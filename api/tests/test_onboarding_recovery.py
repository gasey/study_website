"""0108 recovery quarantines check-in creation and retains compatible shared writers."""
import importlib.util
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('scheduler_deploy',ROOT/'scripts/deploy-finnaplan-v11-onboarding.py');release=importlib.util.module_from_spec(spec);spec.loader.exec_module(release)
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


def test_pause_keeps_source_bound_economy_reconciled(tmp_path,monkeypatch):
    import json
    from app.services import reward_economy as economy
    evidence=json.loads((ROOT/'api/app/data/learning-economy-v2.json').read_text())
    hashes={}
    for name in economy.RELEASE_FILES:
        path=tmp_path/name;path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes((ROOT/'api'/name).read_bytes());hashes[name]=release.sha(path)
    evidence['source_sha256']=hashes
    target=tmp_path/'evidence.json';target.write_text(json.dumps(evidence))
    monkeypatch.setattr(economy,'_API_ROOT',tmp_path)
    monkeypatch.setattr(economy,'_EVIDENCE_PATH',target)
    flag=tmp_path/release.FLAG;flag.parent.mkdir(parents=True,exist_ok=True)
    flag.write_text('{"version":1,"writes_enabled":true}\n')
    assert economy.reconciled_release()
    flag.write_bytes(release.PAUSED)
    assert economy.reconciled_release()
    (tmp_path/'app/services/onboarding.py').write_text('changed writer')
    assert not economy.reconciled_release()
