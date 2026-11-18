"""Exercise the paired recovery against disposable files; no real service changes."""
import importlib.util
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('following_deploy', ROOT/'scripts/deploy-finnaplan-v10-following.py')
release=importlib.util.module_from_spec(spec);spec.loader.exec_module(release)


def test_paired_recovery_and_newer_release_guards(tmp_path, monkeypatch):
    root, public, backup = [tmp_path / name for name in ('api','public','backup')]
    reader = root / release.READER
    reader.parent.mkdir(parents=True)
    reader.write_text('prior reader')
    dependency = root / 'app/db.py';dependency.write_text('unchanged dependency')
    old = {release.READER:release.sha(reader),'app/db.py':release.sha(dependency)}
    public.mkdir();(public/'index.html').write_text('prior static')
    (backup/'public').mkdir(parents=True);(backup/'public/index.html').write_text('prior static')
    (backup/'community.py').write_text('prior reader')
    scope={'prior_api':old,'prior_web':release.inventory(public)}
    reader.write_text('released reader');scope['reader_sha256']=release.sha(reader)
    (public/'index.html').write_text('released static');(public/'new.js').write_text('new chunk')
    scope['served_web']=release.inventory(public)
    original=release.run;services=[]
    def run(args,**kwargs):
        if args[0]=='systemctl':services.append(args);return
        return original(args,**kwargs)
    monkeypatch.setattr(release,'run',run);monkeypatch.setattr(release,'health',lambda:None)
    # Drift must fail before touching either artifact or restarting a service.
    dependency.write_text('newer dependency')
    with pytest.raises(AssertionError,match='drift'):release.restore_pair(backup,scope,root,public)
    dependency.write_text('unchanged dependency')
    (public/'index.html').write_text('newer static')
    with pytest.raises(AssertionError,match='Newer static'):release.restore_pair(backup,scope,root,public)
    assert reader.read_text()=='released reader' and not services
    (public/'index.html').write_text('released static')
    release.restore_pair(backup,scope,root,public)
    assert release.api_inventory(root,scope)==old
    assert release.inventory(public)==scope['prior_web']
    assert services==[['systemctl','restart','ism-api']]
    with pytest.raises(AssertionError,match='drift'):release.restore_pair(backup,scope,root,public)
