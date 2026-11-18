"""Recovery pauses tier capture before restoring prior API and economy evidence."""
import importlib.util
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('tier_deploy',ROOT/'scripts/deploy-finnaplan-v10-tiers.py')
release=importlib.util.module_from_spec(spec);spec.loader.exec_module(release)


def test_tier_recovery_pauses_capture_and_retains_history_refusing_drift(tmp_path,monkeypatch):
    root,public,backup=[tmp_path/n for n in ('api','public','backup')]
    authoring='app/routers/discussions.py';unchanged='app/db.py';evidence='app/data/learning-economy-v2.json';helper='app/services/community_people.py';names={authoring,evidence,*release.RETAINED}
    for n in [*names,unchanged]:
        p=root/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('Prior '+n)
    prior={n:release.sha(root/n) for n in [*names,unchanged]};prior[release.MIGRATION]=None;prior[helper]=None
    for n in names:
        p=backup/'api'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((root/n).read_bytes());(root/n).write_text('Released '+n)
    (root/helper).parent.mkdir(parents=True,exist_ok=True);(root/helper).write_text('Released helper');names.add(helper)
    public.mkdir();(public/'index.html').write_text('prior web');(backup/'public').mkdir();(backup/'public/index.html').write_text('prior web')
    prior_web=release.inventory(public);(public/'index.html').write_text('released web');(public/'replies.js').write_text('reply component')
    (root/release.MIGRATION).parent.mkdir();(root/release.MIGRATION).write_text('Applied0104 tier hooks and unique audit index')
    history=root/'private-prompt-history';history.write_text('Earned tier labels and immutable moderation history')
    scope={'prior_api':prior,'api':{n:release.sha(root/n) for n in names},'migration_sha256':release.sha(root/release.MIGRATION),'prior_web':prior_web,'served_web':release.inventory(public)}
    original=release.run;services=[]
    def run(args,**kwargs):
        if args[0]=='systemctl':services.append(args);return
        return original(args,**kwargs)
    paused=[];monkeypatch.setattr(release,'pause_tier_capture',lambda:paused.append(True));monkeypatch.setattr(release,'run',run);monkeypatch.setattr(release,'health',lambda:None)
    (root/unchanged).write_text('newer runtime')
    with pytest.raises(AssertionError,match='drift'):release.restore_artifacts(backup,scope,root,public)
    (root/unchanged).write_text('Prior '+unchanged);(public/'index.html').write_text('newer web')
    with pytest.raises(AssertionError,match='Newer static'):release.restore_artifacts(backup,scope,root,public)
    assert not services
    (public/'index.html').write_text('released web')
    def fail_pause():raise RuntimeError('Synthetic lock timeout before pausing')
    monkeypatch.setattr(release,'pause_tier_capture',fail_pause)
    with pytest.raises(RuntimeError,match='lock timeout'):release.restore_artifacts(backup,scope,root,public)
    assert services==[['systemctl','stop','ism-api'],['systemctl','start','ism-api']]
    assert release.inventory(public)==scope['served_web'] and (root/helper).is_file()
    services.clear();monkeypatch.setattr(release,'pause_tier_capture',lambda:paused.append(True))
    release.restore_artifacts(backup,scope,root,public)
    assert paused==[True]
    assert not (root/helper).exists() and (root/evidence).read_text()=='Prior '+evidence
    assert (root/authoring).read_text()=='Prior '+authoring
    assert all((root/n).read_text()=='Released '+n for n in release.RETAINED)
    assert release.sha(root/release.MIGRATION)==scope['migration_sha256']
    assert history.read_text()=='Earned tier labels and immutable moderation history'
    assert release.inventory(public)==prior_web
    assert services==[['systemctl','stop','ism-api'],['systemctl','start','ism-api']]
    with pytest.raises(AssertionError,match='drift'):release.restore_artifacts(backup,scope,root,public)
