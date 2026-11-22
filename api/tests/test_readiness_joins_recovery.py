"""Exercise the bulk reader's own paired recovery and refuse unrelated drift."""
import importlib.util
from pathlib import Path
import pytest
import test_collection_count_recovery as checks
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('bulk_release',ROOT/'scripts/deploy-readiness-joins.py')
release=importlib.util.module_from_spec(spec);spec.loader.exec_module(release)

@pytest.fixture(autouse=True)
def own_operator(monkeypatch):
    monkeypatch.setattr(checks,'release',release)

def test_bulk_restore_preserves_durable_history(tmp_path,monkeypatch):
    checks.test_recovery_restores_three_files_as_pair_preserves_mail_migrations_and_history(tmp_path,monkeypatch)

@pytest.mark.parametrize('changed',['mail','evidence','preimage'])
def test_bulk_restore_refuses_drift(tmp_path,monkeypatch,changed):
    checks.test_recovery_refuses_drift_or_corrupt_preimage_before_stop(tmp_path,monkeypatch,changed)

def test_restore_restarts_api_if_atomic_write_fails(tmp_path,monkeypatch):
    api,backup,scope,calls=checks.setup(tmp_path,monkeypatch)
    helper=release.guard(backup,scope,True)
    def failed(data,path):raise OSError('Synthetic disk failure')
    helper.atomic_bytes=failed
    with pytest.raises(OSError):release.restore(backup,scope)
    assert calls==[['systemctl','stop','ism-api'],['systemctl','start','ism-api']]


def test_restore_refuses_corrupt_helper_preimage(tmp_path,monkeypatch):
    api,backup,scope,calls=checks.setup(tmp_path,monkeypatch)
    (backup/'prior-api/app/services/question_readiness.py').write_text('corrupt')
    with pytest.raises(AssertionError):release.restore(backup,scope)
    assert not calls
