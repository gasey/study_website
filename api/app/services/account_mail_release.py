"""Fail-closed mail pause; queued ciphertext and completed account links remain."""
import json
from pathlib import Path
STATE_PATH=Path(__file__).resolve().parents[1]/'data/account-mail-writes.json'
def enabled():
    try:
        state=json.loads(STATE_PATH.read_text())
        return state=={'version':1,'writes_enabled':True} and type(state['version']) is int and state['writes_enabled'] is True
    except (OSError,ValueError,TypeError):return False
