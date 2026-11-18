"""Bounded ops-reader recovery retains current mail/review writers and history."""
import importlib.util
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('share_deploy',ROOT/'scripts/deploy-finnaplan-v12-users.py');release=importlib.util.module_from_spec(spec);spec.loader.exec_module(release)

def test_account_viewer_recovery_restores_pair_and_refuses_drift(tmp_path,monkeypatch):
    root,public,backup=[tmp_path/n for n in ('api','public','backup')]
    changed='app/main.py';new='app/services/ops.py';writer='app/services/account_mail.py';migration='migrations/0107_account_mail_delivery.sql'
    for n in (changed,new,writer,migration):
        p=root/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('current '+n)
    p=backup/'api'/changed;p.parent.mkdir(parents=True);p.write_text('prior reader')
    (backup/'public').mkdir();(backup/'public/index.html').write_text('prior static')
    public.mkdir();(public/'index.html').write_text('current static');(public/'new.js').write_text('new chunk')
    scope={'prior_api':{changed:release.sha(backup/'api'/changed),new:None,writer:release.sha(root/writer),migration:release.sha(root/migration)},'api':{n:release.sha(root/n) for n in (changed,new)},'prior_web':release.inventory(backup/'public'),'served_web':release.inventory(public)}
    history=root/'history';history.write_text('All existing attempts, grades, mail capacity and learner history')
    monkeypatch.setattr(release,'guard_collectors',lambda scope:None)
    original=release.run;services=[]
    def run(args,**kwargs):
        if args[0]=='systemctl':services.append(args);return
        return original(args,**kwargs)
    monkeypatch.setattr(release,'run',run);monkeypatch.setattr(release,'health',lambda:None)
    (root/writer).write_text('newer writer')
    with pytest.raises(AssertionError,match='drift'):release.restore_pair(backup,scope,root,public)
    (root/writer).write_text('current '+writer);(public/'index.html').write_text('newer static')
    with pytest.raises(AssertionError,match='Newer static'):release.restore_pair(backup,scope,root,public)
    (public/'index.html').write_text('current static');assert not services
    release.restore_pair(backup,scope,root,public)
    assert services==[['systemctl','stop','ism-api'],['systemctl','start','ism-api']]
    assert (root/changed).read_text()=='prior reader' and not (root/new).exists()
    assert release.inventory(public)==scope['prior_web']
    for n in (writer,migration):assert release.sha(root/n)==scope['prior_api'][n]
    assert history.read_text()=='All existing attempts, grades, mail capacity and learner history'
    release.guard(scope,root=root)


def test_installed_collectors_are_guarded(tmp_path):
    p=tmp_path/'collector.py';p.write_text('unchanged')
    scope={'protected_host_files':{str(p):release.sha(p)}}
    p.write_text('newer collector')
    with pytest.raises(AssertionError,match='Collector/unit drift'):release.guard_collectors(scope)
