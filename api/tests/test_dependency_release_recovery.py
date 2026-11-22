"""Dependency recovery must refuse drift and preserve API/UI/history."""
import importlib.util,shutil
from pathlib import Path
from types import SimpleNamespace
import pytest

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('dependency_release',ROOT/'scripts/deploy-finnaplan-v12-dependencies.py')
release=importlib.util.module_from_spec(spec);spec.loader.exec_module(release)


def test_environment_drift_refuses_recovery_before_service_stop_and_history_survives(tmp_path,monkeypatch):
    api=tmp_path/'api';api.mkdir();backup=tmp_path/'backup';backup.mkdir()
    current=api/'.venv';old=backup/'venv'
    for folder,version in ((current,'new'),(old,'old')):
        (folder/'bin').mkdir(parents=True);(folder/'bin/python').symlink_to('/usr/bin/python3')
        (folder/'VERSION').write_text(version)
    (api/'requirements.txt').write_text('new requirements')
    (backup/'requirements.before.txt').write_text('old requirements')
    (api/'history-sentinel').write_text('real attempts, wallet, retained activity, notices and receipts')
    (api/'app.py').write_text('current API');public=tmp_path/'public';public.mkdir();(public/'index.html').write_text('current UI')
    scope={'environment_after':release.files(current),'environment_before':release.files(old),'requirements_sha256':release.sha(api/'requirements.txt'),'prior_requirements_sha256':release.sha(backup/'requirements.before.txt'),'packages_after':{'fastapi':'new'},'packages_before':{'fastapi':'old'},'maintenance':{'served_web':{'index.html':release.sha(public/'index.html')}}}
    services=[]
    fake=SimpleNamespace(guard=lambda *args:None,guard_collectors=lambda *args:None,guard_extra=lambda *args:None,runtime_mail_guard=lambda:None,inventory=lambda root:{'index.html':release.sha(public/'index.html')},atomic=shutil.copy2)
    monkeypatch.setattr(release,'ROOT',api);monkeypatch.setattr(release,'common',lambda *args:fake)
    monkeypatch.setattr(release,'packages',lambda env:{'fastapi':(env/'VERSION').read_text()})
    monkeypatch.setattr(release,'run',lambda args,**kwargs:services.append(args));monkeypatch.setattr(release,'healthy',lambda:None)
    (current/'unexpected.py').write_text('later package change')
    with pytest.raises(AssertionError,match='environment drift'):release.restore(backup,backup,scope)
    assert services==[] and (old/'VERSION').read_text()=='old'
    (current/'unexpected.py').unlink();release.restore(backup,backup,scope)
    assert services==[['systemctl','stop','ism-api'],['systemctl','start','ism-api']]
    assert (current/'VERSION').read_text()=='old' and (backup/'released-venv/VERSION').read_text()=='new'
    assert (api/'requirements.txt').read_text()=='old requirements'
    assert (api/'history-sentinel').read_text()=='real attempts, wallet, retained activity, notices and receipts'
    assert (api/'app.py').read_text()=='current API' and (public/'index.html').read_text()=='current UI'


def test_changed_or_platform_specific_wheel_refuses_install_before_any_command(tmp_path,monkeypatch):
    stage=tmp_path/'stage';(stage/'wheels').mkdir(parents=True)
    wheel=stage/'wheels/package-1-py3-none-any.whl';wheel.write_bytes(b'original wheel')
    (stage/'requirements.txt').write_text('fixed requirements')
    scope={'wheels':{wheel.name:release.sha(wheel)},'requirements_sha256':release.sha(stage/'requirements.txt')}
    release.wheel_guard(stage,scope)
    wheel.write_bytes(b'drifted wheel')
    monkeypatch.setattr(release,'run',lambda *args,**kwargs:pytest.fail('No install command may run'))
    with pytest.raises(AssertionError):release.prepare(stage,scope,tmp_path/'candidate')
    platform=stage/'wheels/platform-1-cp312-linux_aarch64.whl';wheel.rename(platform)
    scope['wheels']={platform.name:release.sha(platform)}
    with pytest.raises(AssertionError,match='platform-independent'):release.wheel_guard(stage,scope)
