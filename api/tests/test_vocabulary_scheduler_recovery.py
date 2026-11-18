"""0105 recovery quarantines recognition and retains compatible shared writers."""
import importlib.util
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('scheduler_deploy',ROOT/'scripts/deploy-finnaplan-v10-vocabulary-scheduler.py');release=importlib.util.module_from_spec(spec);spec.loader.exec_module(release)
def test_recovery_guards_drift_and_keeps_shared_writers_and_migration(tmp_path,monkeypatch):
    root,public,backup=[tmp_path/n for n in ('api','public','backup')]
    writer='app/services/review_queue.py';evidence='app/data/learning-economy-v2.json'
    for n in (writer,evidence,release.FLAG,release.MIGRATION):
        p=root/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('candidate '+n)
    (root/release.FLAG).write_text('{"version":1,"writes_enabled":true}\n')
    api={n:release.sha(root/n) for n in (writer,evidence,release.FLAG)}
    public.mkdir();(public/'index.html').write_text('candidate web');(public/'new.js').write_text('candidate chunk')
    (backup/'public').mkdir(parents=True);(backup/'public/index.html').write_text('prior web')
    scope={'prior_api':{writer:'prior',evidence:'prior',release.FLAG:None,release.MIGRATION:None},'api':api,'migration_sha256':release.sha(root/release.MIGRATION),'prior_web':release.inventory(backup/'public'),'served_web':release.inventory(public)}
    history=root/'learner-history';history.write_text('Immutable attempts and earned receipts')
    original=release.run;services=[]
    def run(args,**kwargs):
        if args[0]=='systemctl':services.append(args);return
        return original(args,**kwargs)
    monkeypatch.setattr(release,'run',run);monkeypatch.setattr(release,'health',lambda:None)
    (root/writer).write_text('newer writer')
    with pytest.raises(AssertionError,match='drift'):release.restore_artifacts(backup,scope,root,public)
    (root/writer).write_text('candidate '+writer);(public/'index.html').write_text('newer web')
    with pytest.raises(AssertionError,match='Newer static'):release.restore_artifacts(backup,scope,root,public)
    (public/'index.html').write_text('candidate web');extra=root/'app/services/unknown.py';extra.write_text('new dependency')
    with pytest.raises(AssertionError,match='drift'):release.restore_artifacts(backup,scope,root,public)
    extra.unlink();assert not services
    release.restore_artifacts(backup,scope,root,public)
    assert services==[['systemctl','stop','ism-api'],['systemctl','start','ism-api']]
    assert (root/release.FLAG).read_bytes()==release.PAUSED
    for n in (writer,evidence):assert release.sha(root/n)==api[n]
    assert release.sha(root/release.MIGRATION)==scope['migration_sha256']
    assert release.inventory(public)==scope['prior_web']
    assert history.read_text()=='Immutable attempts and earned receipts'
    release.guard(scope,paused=True,root=root)
    with pytest.raises(AssertionError):release.guard(scope,True,root=root)
