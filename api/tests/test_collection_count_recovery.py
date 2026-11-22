"""Count-reader recovery preserves source/evidence pairing and durable history."""
import importlib.util,shutil
from pathlib import Path
from types import SimpleNamespace
import pytest
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('count_release',ROOT/'scripts/deploy-collection-counts.py')
release=importlib.util.module_from_spec(spec);spec.loader.exec_module(release)


def setup(tmp_path,monkeypatch):
    api=tmp_path/'api';backup=tmp_path/'backup';api.mkdir();backup.mkdir();calls=[]
    for name in release.CHANGES:
        for base,prefix in ((api,'new '),(backup/'prior-api','old ')):
            p=base/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(prefix+name)
    (api/'durable-history').write_text('attempts ledger grants consent recovery audit')
    (api/'mail-writer.py').write_text('current security mail and digest writers')
    (api/'0120.sql').write_text('applied immutable migration')
    scope={'api':{n:release.sha(api/n) for n in release.CHANGES},'prior_api':{n:release.sha(backup/'prior-api'/n) for n in release.CHANGES}}
    def atomic(data,path):path.write_bytes(data)
    helper=SimpleNamespace(run=lambda command:calls.append(command),atomic_bytes=atomic,health=lambda:{'healthy':True})
    def guard(stage,scope,released=False):
        assert (api/'mail-writer.py').read_text()=='current security mail and digest writers','Other writer drift'
        assert {n:release.sha(api/n) for n in release.CHANGES}==scope['api' if released else 'prior_api'],'Reader or evidence drift'
        return helper
    monkeypatch.setattr(release,'ROOT',api);monkeypatch.setattr(release,'guard',guard)
    return api,backup,scope,calls


def test_recovery_restores_three_files_as_pair_preserves_mail_migrations_and_history(tmp_path,monkeypatch):
    api,backup,scope,calls=setup(tmp_path,monkeypatch)
    result=release.restore(backup,scope)
    assert result['prior_reader_and_evidence_restored']
    assert {n:release.sha(api/n) for n in release.CHANGES}==scope['prior_api']
    assert (api/'durable-history').read_text()=='attempts ledger grants consent recovery audit'
    assert (api/'0120.sql').read_text()=='applied immutable migration'
    assert calls==[['systemctl','stop','ism-api'],['systemctl','start','ism-api']]


@pytest.mark.parametrize('changed',['mail','evidence','preimage'])
def test_recovery_refuses_drift_or_corrupt_preimage_before_stop(tmp_path,monkeypatch,changed):
    api,backup,scope,calls=setup(tmp_path,monkeypatch)
    if changed=='mail':(api/'mail-writer.py').write_text('newer unrelated writer')
    elif changed=='evidence':(api/'app/data/learning-economy-v2.json').write_text('later evidence')
    else:(backup/'prior-api/app/data/learning-economy-v2.json').write_text('damaged backup')
    before={n:release.sha(api/n) for n in release.CHANGES}
    with pytest.raises(AssertionError):release.restore(backup,scope)
    assert not calls and before=={n:release.sha(api/n) for n in release.CHANGES}
