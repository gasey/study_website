import importlib.util
from pathlib import Path
from types import SimpleNamespace
import pytest

SPEC=importlib.util.spec_from_file_location('owner_coordination',Path(__file__).resolve().parents[2]/'scripts/owner-bank-maintenance.py')
OWNER=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(OWNER)


@pytest.mark.parametrize('state',['active','activating','reloading'])
def test_live_single_item_worker_prevents_new_batch_exports(monkeypatch,state):
    monkeypatch.setattr(OWNER.subprocess,'run',lambda *a,**k:SimpleNamespace(stdout=state))
    with pytest.raises(ValueError,match='Pause ism-bank-review.timer'):
        OWNER.require_batch_worker_idle({'operation':'answer-batch','repairs':[{'mode':'official'}]*2})
    with pytest.raises(ValueError):OWNER.require_batch_worker_idle({'operation':'source-batch'})


def test_holds_do_not_create_exports_and_paused_worker_allows_batches(monkeypatch):
    monkeypatch.setattr(OWNER.subprocess,'run',lambda *a,**k:SimpleNamespace(stdout='active'))
    OWNER.require_batch_worker_idle({'operation':'answer-batch','repairs':[{'mode':'needs-review'}]*18})
    monkeypatch.setattr(OWNER.subprocess,'run',lambda *a,**k:SimpleNamespace(stdout='inactive'))
    OWNER.require_batch_worker_idle({'operation':'answer-batch','repairs':[{'mode':'official'}]*2})
