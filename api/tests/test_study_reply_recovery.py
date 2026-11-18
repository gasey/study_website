"""Recovery must retain privacy readers for saved replies, even with old authoring."""
import importlib.util
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('replies_deploy',ROOT/'scripts/deploy-finnaplan-v10-replies.py')
release=importlib.util.module_from_spec(spec);spec.loader.exec_module(release)


def test_reply_recovery_retains_schema_history_parent_readers_and_refuses_drift(tmp_path,monkeypatch):
    root,public,backup=[tmp_path/n for n in ('api','public','backup')]
    authoring='app/routers/study_posts.py';unchanged='app/db.py';names={authoring,*release.RETAINED}
    for n in [*names,unchanged]:
        p=root/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('Prior '+n)
    prior={n:release.sha(root/n) for n in [*names,unchanged]};prior[release.MIGRATION]=None
    for n in names:
        p=backup/'api'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((root/n).read_bytes());(root/n).write_text('Released '+n)
    public.mkdir();(public/'index.html').write_text('prior web');(backup/'public').mkdir();(backup/'public/index.html').write_text('prior web')
    prior_web=release.inventory(public);(public/'index.html').write_text('released web');(public/'replies.js').write_text('reply component')
    (root/release.MIGRATION).parent.mkdir();(root/release.MIGRATION).write_text('Applied0101 reply-anchor guard')
    history=root/'private-reply-history';history.write_text('Replies and their moderation/vote history')
    scope={'prior_api':prior,'api':{n:release.sha(root/n) for n in names},'migration_sha256':release.sha(root/release.MIGRATION),'prior_web':prior_web,'served_web':release.inventory(public)}
    original=release.run;services=[]
    def run(args,**kwargs):
        if args[0]=='systemctl':services.append(args);return
        return original(args,**kwargs)
    monkeypatch.setattr(release,'run',run);monkeypatch.setattr(release,'health',lambda:None)
    (root/unchanged).write_text('newer runtime')
    with pytest.raises(AssertionError,match='drift'):release.restore_artifacts(backup,scope,root,public)
    (root/unchanged).write_text('Prior '+unchanged);(public/'index.html').write_text('newer web')
    with pytest.raises(AssertionError,match='Newer static'):release.restore_artifacts(backup,scope,root,public)
    assert not services
    (public/'index.html').write_text('released web');release.restore_artifacts(backup,scope,root,public)
    assert (root/authoring).read_text()=='Prior '+authoring
    assert all((root/n).read_text()=='Released '+n for n in release.RETAINED)
    assert release.sha(root/release.MIGRATION)==scope['migration_sha256']
    assert history.read_text()=='Replies and their moderation/vote history'
    assert release.inventory(public)==prior_web
    assert services==[['systemctl','stop','ism-api'],['systemctl','start','ism-api']]
    with pytest.raises(AssertionError,match='drift'):release.restore_artifacts(backup,scope,root,public)
