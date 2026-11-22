"""Static recovery refuses runtime/backup drift and retains open-tab chunks."""
import importlib.util,shutil
from pathlib import Path
from types import SimpleNamespace
import pytest
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('build_dependency_release',ROOT/'scripts/deploy-finnaplan-v12-build-dependencies.py')
release=importlib.util.module_from_spec(spec);spec.loader.exec_module(release)


def setup(tmp_path,monkeypatch):
    public=tmp_path/'public';public.mkdir();backup=tmp_path/'backup';(backup/'public').mkdir(parents=True)
    for folder in (public,backup/'public'):(folder/'old.js').write_text('old immutable chunk')
    (public/'index.html').write_text('new index');(public/'new.js').write_text('new immutable chunk')
    (backup/'public/index.html').write_text('old index')
    history=tmp_path/'history';history.write_text('real learner receipts')
    runtime=tmp_path/'api.py';runtime.write_text('current API/environment/configuration')
    prior=release.inventory(backup/'public');served=release.inventory(public)
    scope={'prior_web':prior,'served_web':served,'restored_web':{**served,**prior},'dependencies':{}}
    calls=[];original=release.run
    def guard(stage,scope,expected):
        assert runtime.read_text()=='current API/environment/configuration','Runtime drift'
        assert release.inventory(public)==expected,'Static drift'
        return SimpleNamespace(common=lambda *args:SimpleNamespace(atomic=shutil.copy2))
    def run(args,**kwargs):
        calls.append(args)
        if args[0]=='chown':return ''
        return original(args,**kwargs)
    monkeypatch.setattr(release,'PUBLIC',public);monkeypatch.setattr(release,'guard',guard);monkeypatch.setattr(release,'run',run)
    return public,backup,history,runtime,scope,calls


def test_recovery_refuses_runtime_drift_and_keeps_new_chunks_and_history(tmp_path,monkeypatch):
    public,backup,history,runtime,scope,calls=setup(tmp_path,monkeypatch)
    runtime.write_text('later runtime')
    with pytest.raises(AssertionError,match='Runtime drift'):release.restore(backup,scope)
    assert calls==[] and (public/'index.html').read_text()=='new index'
    runtime.write_text('current API/environment/configuration');result=release.restore(backup,scope)
    assert result['new_chunks_retained'] and result['runtime_and_history_unchanged']
    assert release.inventory(public)==scope['restored_web']
    assert (public/'index.html').read_text()=='old index' and (public/'new.js').read_text()=='new immutable chunk'
    assert history.read_text()=='real learner receipts'
    assert not any(args[0] in ('systemctl','psql','pip') for args in calls)


def test_corrupt_backup_refuses_before_any_installed_file_changes(tmp_path,monkeypatch):
    public,backup,history,runtime,scope,calls=setup(tmp_path,monkeypatch)
    (backup/'public/old.js').write_text('corrupt backup')
    with pytest.raises(AssertionError):release.restore(backup,scope)
    assert calls==[] and release.inventory(public)==scope['served_web']
