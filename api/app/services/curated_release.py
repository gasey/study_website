"""Fail-closed availability switch; receipts/history and canonical practice remain."""
import json
from pathlib import Path
from fastapi import HTTPException
STATE_PATH=Path(__file__).resolve().parents[1]/'data/curated-vocabulary-writes.json'
def enabled():
    try:
        state=json.loads(STATE_PATH.read_text())
        return state=={'version':1,'writes_enabled':True} and type(state['version']) is int and state['writes_enabled'] is True
    except (OSError,ValueError,TypeError):return False
def require_writes():
    if not enabled():raise HTTPException(503,'Reviewed word practice is temporarily paused. Your saved grades and reviews are safe.',headers={'Retry-After':'300'})
