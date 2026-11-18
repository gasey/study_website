"""Pausing new check-ins preserves existing ordinary practice and receipts."""
import json
from pathlib import Path
from fastapi import HTTPException
STATE_PATH=Path(__file__).resolve().parents[1]/'data/onboarding-writes.json'
def enabled():
    try:
        value=json.loads(STATE_PATH.read_text())
        return value=={'version':1,'writes_enabled':True} and type(value['version']) is int and value['writes_enabled'] is True
    except (OSError,ValueError,TypeError):return False
def require_writes():
    if not enabled():raise HTTPException(503,'New exam check-ins are temporarily paused. Your saved set and answers remain available.',headers={'Retry-After':'300'})
