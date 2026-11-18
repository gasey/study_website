"""Static-only recovery keeps API/history untouched and refuses newer inventory."""
import importlib.util
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('submission_checklists_static_deploy',ROOT/'scripts/deploy-finnaplan-v10-checklists.py')
release=importlib.util.module_from_spec(spec);spec.loader.exec_module(release)


def test_submission_checklists_static_recovery_and_exact_api_inventory(tmp_path):
    api,public,backup=[tmp_path/n for n in ('api','public','backup')]
    (api/'app').mkdir(parents=True);(api/'migrations').mkdir();(api/'app/db.py').write_text('unchanged runtime');(api/'migrations/0101.sql').write_text('applied schema')
    compatibility={p.relative_to(api).as_posix():release.sha(p) for p in api.rglob('*') if p.is_file()}
    public.mkdir();(public/'index.html').write_text('prior web');(backup/'public').mkdir(parents=True);(backup/'public/index.html').write_text('prior web')
    prior=release.inventory(public);(public/'index.html').write_text('composer web');(public/'composer.js').write_text('new component');served=release.inventory(public)
    scope={'api_compatibility':compatibility,'prior_web':prior,'served_web':served}
    release.compatible(scope,root=api)
    (api/'app/newer.py').write_text('new runtime')
    with pytest.raises(AssertionError,match='inventory'):release.compatible(scope,root=api)
    (api/'app/newer.py').unlink();(public/'index.html').write_text('newer web')
    with pytest.raises(AssertionError,match='Newer static'):release.restore_files(backup,public,scope)
    (public/'index.html').write_text('composer web');release.restore_files(backup,public,scope)
    assert release.inventory(public)==prior
    assert {p.relative_to(api).as_posix():release.sha(p) for p in api.rglob('*') if p.is_file()}==compatibility
