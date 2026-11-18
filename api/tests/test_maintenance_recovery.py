"""Current history/readers and0110 survive bounded maintenance recovery."""
import importlib.util
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('maintenance_release',ROOT/'scripts/deploy-finnaplan-v12-maintenance.py')
release=importlib.util.module_from_spec(spec);spec.loader.exec_module(release)


def test_recovery_preserves_activity_reader_schema_and_all_history(tmp_path,monkeypatch):
    root,public,backup=[tmp_path/n for n in ('api','public','backup')]
    changed='app/main.py';reader=release.KEEP_READERS[0];new='app/services/account_retention.py';writer='app/routers/questions.py';migration=release.MIGRATION
    for n in (changed,reader,new,writer,migration):
        p=root/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('current '+n)
    for n in (changed,reader):
        p=backup/'api'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('prior '+n)
    p=backup/'released-api'/reader;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('current '+reader)
    (backup/'public').mkdir();(backup/'public/index.html').write_text('prior UI')
    public.mkdir();(public/'index.html').write_text('current UI');(public/'new.js').write_text('new chunk')
    tool=tmp_path/'restore-rehearsal.py';tool.write_text('verified restore tool')
    extra=backup/'released-extra'/str(tool).lstrip('/');extra.parent.mkdir(parents=True);extra.write_text(tool.read_text())
    scope={'prior_api':{changed:release.sha(backup/'api'/changed),reader:release.sha(backup/'api'/reader),new:None,writer:release.sha(root/writer),migration:None},'api':{n:release.sha(root/n) for n in (changed,reader,new)},'migration_sha256':release.sha(root/migration),'prior_web':release.inventory(backup/'public'),'served_web':release.inventory(public),'extra':{str(tool):release.sha(tool)}}
    history=root/'history';history.write_text('attempts, wallets, notices, audits, retained activity and adoption receipts')
    services=[];original=release.run
    def run(args,**kwargs):
        if args[0]=='systemctl':services.append(args);return
        return original(args,**kwargs)
    monkeypatch.setattr(release,'run',run);monkeypatch.setattr(release,'health',lambda:None)
    monkeypatch.setattr(release,'guard_collectors',lambda scope:None);monkeypatch.setattr(release,'migration_applied',lambda scope:True)
    (root/writer).write_text('newer writer')
    with pytest.raises(AssertionError,match='drift'):release.restore_pair(backup,scope,root,public)
    (root/writer).write_text('current '+writer);(public/'index.html').write_text('unrelated UI')
    with pytest.raises(AssertionError,match='Newer static'):release.restore_pair(backup,scope,root,public)
    assert not services
    (public/'index.html').write_text('current UI');release.restore_pair(backup,scope,root,public)
    assert services==[['systemctl','stop','ism-api'],['systemctl','start','ism-api']]
    assert (root/changed).read_text()=='prior '+changed and not (root/new).exists()
    assert (root/reader).read_text()=='current '+reader
    assert (root/migration).is_file() and release.sha(root/migration)==scope['migration_sha256']
    assert release.inventory(public)==scope['prior_web']
    assert history.read_text()=='attempts, wallets, notices, audits, retained activity and adoption receipts'
    release.guard(scope,restored=True,root=root)


def test_restore_tool_and_registry_drift_refuse_recovery(tmp_path,monkeypatch):
    tool=tmp_path/'restore.py';tool.write_text('verified')
    scope={'extra':{str(tool):release.sha(tool)},'migration_sha256':'a'*64}
    tool.write_text('unrelated newer tool')
    with pytest.raises(AssertionError,match='Restore tool drift'):release.guard_extra(scope,True)
    monkeypatch.setattr(release,'sql',lambda query:'b'*64)
    with pytest.raises(AssertionError,match='Migration registry drift'):release.migration_applied(scope)
