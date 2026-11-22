"""Withdrawal keeps shared mail capacity and credentials under drift guards."""
import importlib.util,json,shutil
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('digest_release',ROOT/'scripts/deploy-review-digest.py')
release=importlib.util.module_from_spec(spec);spec.loader.exec_module(release)


def test_withdrawal_refuses_drift_and_retains_capacity_schema_and_security_mail(tmp_path,monkeypatch):
    api=tmp_path/'api';public=tmp_path/'public';backup=tmp_path/'backup';env=tmp_path/'db.env'
    for n in ('app/services/account_mail.py','migrations/0120_review_digest.sql'):
        p=api/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('compatible '+n)
    public.mkdir();(public/'index.html').write_text('new');(public/'chunk.js').write_text('new chunk')
    (backup/'public').mkdir(parents=True);(backup/'public/index.html').write_text('prior')
    before=b'SMTP_PASSWORD=synthetic-secret\nACCOUNT_MAIL_ENABLED=true\n'
    (backup/'db.env.before').write_bytes(before);env.write_bytes(release.env_value(before,True))
    scope={'prior_api':{},'api':release.inventory(api),'prior_web':release.inventory(backup/'public'),'served_web':release.inventory(public)}
    calls=[]
    def run(args,**kw):
        calls.append(args)
        if args[0]=='rsync':
            for f in public.iterdir():f.unlink()
            shutil.copytree(backup/'public',public,dirs_exist_ok=True)
    monkeypatch.setattr(release,'ROOT',api);monkeypatch.setattr(release,'PUBLIC',public);monkeypatch.setattr(release,'ENV',env)
    monkeypatch.setattr(release,'run',run);monkeypatch.setattr(release,'health',lambda:[])
    ownership=[]
    monkeypatch.setattr(release.os,'fchown',lambda fd,uid,gid:ownership.append((uid,gid)))
    writer=api/'app/services/account_mail.py';original=writer.read_bytes();writer.write_text('newer capacity writer')
    with pytest.raises(AssertionError,match='drift'):release.restore(backup,scope)
    assert not calls;writer.write_bytes(original)
    env.write_bytes(env.read_bytes()+b'NEW_CREDENTIAL=synthetic-new\n')
    with pytest.raises(AssertionError,match='environment drift'):release.restore(backup,scope)
    assert not calls;env.write_bytes(release.env_value(before,True))
    result=release.restore(backup,scope)
    assert result['compatible_api_and_capacity_retained']
    assert release.inventory(api)==scope['api'] and release.inventory(public)==scope['prior_web']
    assert env.read_bytes()==release.env_value(before,False) and b'SMTP_PASSWORD=synthetic-secret' in env.read_bytes()
    assert env.stat().st_mode&0o777==0o600
    assert ownership and ownership[0][0]==0
    assert calls[0]==['systemctl','stop','ism-api'] and calls[-1]==['systemctl','start','ism-api']
