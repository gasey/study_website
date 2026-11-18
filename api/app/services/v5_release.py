"""Fail-closed switch for the bounded V.5 compatibility recovery bundle.

Recovery keeps the current privacy readers, cosmetic validators and account
tombstones. Only an operator-installed, source-bound artifact enables new writes.
Deletion, feed revocation, sign-out and moderation remain available in recovery.
"""
import json
from pathlib import Path
from fastapi import HTTPException

STATE_PATH = Path(__file__).resolve().parents[1] / 'data/finnaplan-v5-writes.json'


def require_writes():
    try:
        state = json.loads(STATE_PATH.read_text())
        enabled = (state == {'version': 1, 'writes_enabled': True}
                   and type(state['version']) is int and state['writes_enabled'] is True)
    except (OSError, ValueError, TypeError):
        enabled = False
    if not enabled:
        raise HTTPException(503, 'This change is temporarily paused. Please try again later.',
                            headers={'Retry-After': '300'})
