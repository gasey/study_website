"""Reader/economy source pair rolls back together; all data and other code stay."""
import importlib.util,shutil
from pathlib import Path
from types import SimpleNamespace
import pytest
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('detail_performance_release',ROOT/'scripts/deploy-finnaplan-v12-query-performance.py')
release=importlib.util.module_from_spec(spec);spec.loader.exec_module(release)


def setup(tmp_path,monkeypatch):
    api=tmp_path/'api';api.mkdir();backup=tmp_path/'backup';backup.mkdir()
    names=('app/routers/questions.py','app/services/reward_economy.py','app/data/learning-economy-v2.json')
    for n in names:
        for base,prefix in ((api,'new '),(backup/'api','old ')):
            p=base/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(prefix+n)
    (api/'migrations').mkdir();(api/'migrations/0110_site_maintenance.sql').write_text('applied immutable migration')
    (api/'history').write_text('attempts, ledger, activity, credentials, audits and adoption receipts')
    (api/'other-writer.py').write_text('current other writer')
    scope={'api':{n:release.sha(api/n) for n in names},'prior_api':{n:release.sha(backup/'api'/n) for n in names},'dependencies':{}}
    calls=[]
    def guard(stage,scope,released=False):
        assert (api/'other-writer.py').read_text()=='current other writer','Unrelated writer drift'
        assert {n:release.sha(api/n) for n in names}==scope['api' if released else 'prior_api'],'Reader/evidence drift'
        return SimpleNamespace(common=lambda *args:SimpleNamespace(atomic=shutil.copy2))
    monkeypatch.setattr(release,'ROOT',api);monkeypatch.setattr(release,'guard',guard)
    monkeypatch.setattr(release,'run',lambda args,**kwargs:calls.append(args));monkeypatch.setattr(release,'healthy',lambda:None)
    return api,backup,scope,calls


def test_recovery_refuses_newer_writer_then_restores_complete_pair_without_history_reset(tmp_path,monkeypatch):
    api,backup,scope,calls=setup(tmp_path,monkeypatch)
    (api/'other-writer.py').write_text('later writer')
    with pytest.raises(AssertionError,match='writer drift'):release.restore(backup,scope)
    assert calls==[]
    (api/'other-writer.py').write_text('current other writer');result=release.restore(backup,scope)
    assert result['prior_reader_evidence_pair_restored']
    assert {n:release.sha(api/n) for n in scope['api']}==scope['prior_api']
    assert (api/'history').read_text()=='attempts, ledger, activity, credentials, audits and adoption receipts'
    assert (api/'migrations/0110_site_maintenance.sql').read_text()=='applied immutable migration'
    assert calls==[['systemctl','stop','ism-api'],['systemctl','start','ism-api']]


def test_corrupt_prior_evidence_refuses_before_stopping_or_replacing_reader(tmp_path,monkeypatch):
    api,backup,scope,calls=setup(tmp_path,monkeypatch)
    (backup/'api/app/data/learning-economy-v2.json').write_text('corrupt prior evidence')
    with pytest.raises(AssertionError):release.restore(backup,scope)
    assert calls==[] and {n:release.sha(api/n) for n in scope['api']}==scope['api']
