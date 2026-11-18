"""Retain applied additive schema and history during paired API/static recovery."""
import importlib.util
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('materials_deploy',ROOT/'scripts/deploy-finnaplan-v10-materials.py')
release=importlib.util.module_from_spec(spec);spec.loader.exec_module(release)


def test_material_share_recovery_retains_schema_history_and_refuses_drift(tmp_path,monkeypatch):
    root,public,backup=[tmp_path/n for n in ('api','public','backup')]
    compat='app/routers/discussions.py'
    old_name='app/routers/community.py';new_name='app/services/study_posts.py';unchanged='app/db.py'
    for n,body in [(old_name,'prior reader'),(unchanged,'unchanged runtime'),(compat,'prior native reader')]:
        p=root/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(body)
    prior={compat:release.sha(root/compat),old_name:release.sha(root/old_name),new_name:None,unchanged:release.sha(root/unchanged),release.MIGRATION:None}
    (backup/'api/app/routers').mkdir(parents=True);(backup/'api'/old_name).write_text('prior reader')
    public.mkdir();(public/'index.html').write_text('prior web');(backup/'public').mkdir();(backup/'public/index.html').write_text('prior web')
    prior_web=release.inventory(public)
    (backup/'api'/compat).write_text('prior native reader');(root/compat).write_text('Retained material-share isolation guard')
    (root/old_name).write_text('released reader');(root/new_name).parent.mkdir(parents=True);(root/new_name).write_text('new note reader')
    (root/release.MIGRATION).parent.mkdir();(root/release.MIGRATION).write_text('applied additive0100')
    (public/'index.html').write_text('released web');(public/'new.js').write_text('new chunk')
    history=root/'private-study-history';history.write_text('Saved notes, moderation events and vote evidence')
    scope={'prior_api':prior,'api':{n:release.sha(root/n) for n in (old_name,new_name,compat)},'migration_sha256':release.sha(root/release.MIGRATION),'prior_web':prior_web,'served_web':release.inventory(public)}
    original=release.run;services=[]
    def run(args,**kwargs):
        if args[0]=='systemctl':services.append(args);return
        return original(args,**kwargs)
    monkeypatch.setattr(release,'run',run);monkeypatch.setattr(release,'health',lambda:None)
    (root/unchanged).write_text('newer runtime')
    with pytest.raises(AssertionError,match='drift'):release.restore_artifacts(backup,scope,root,public)
    (root/unchanged).write_text('unchanged runtime');(public/'index.html').write_text('newer web')
    with pytest.raises(AssertionError,match='Newer static'):release.restore_artifacts(backup,scope,root,public)
    assert not services
    (public/'index.html').write_text('released web');release.restore_artifacts(backup,scope,root,public)
    assert (root/old_name).read_text()=='prior reader' and not (root/new_name).exists()
    assert release.sha(root/release.MIGRATION)==scope['migration_sha256']
    assert (root/compat).read_text()=='Retained material-share isolation guard'
    assert history.read_text()=='Saved notes, moderation events and vote evidence'
    assert release.inventory(public)==prior_web
    assert services==[['systemctl','stop','ism-api'],['systemctl','start','ism-api']]
    with pytest.raises(AssertionError,match='drift'):release.restore_artifacts(backup,scope,root,public)
