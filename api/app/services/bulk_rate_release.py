"""Pausing bulk assignment retains every assigned price and receipt."""
import json
from pathlib import Path
from fastapi import HTTPException
STATE_PATH=Path(__file__).resolve().parents[1]/'data/bulk-rate-writes.json'
def enabled():
    try:
        value=json.loads(STATE_PATH.read_text())
        return value=={'version':1,'writes_enabled':True} and type(value['version']) is int and value['writes_enabled'] is True
    except (OSError,ValueError,TypeError):return False
def require_writes():
    if not enabled():raise HTTPException(503,'Bulk price assignments are temporarily paused. Existing prices remain in place.',headers={'Retry-After':'300'})
