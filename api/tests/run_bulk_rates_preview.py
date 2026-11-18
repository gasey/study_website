"""Disposable synthetic quiz preview; all data is removed when stopped."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import conftest,uvicorn
from app.routers.auth import _hash_password
from app.config import settings
prepared=conftest.fresh_database();database=next(prepared)
clients=conftest.client.__wrapped__(database);client=next(clients)
try:
    actor=conftest.actor.__wrapped__(client)
    database[1].execute("UPDATE users SET email='synthetic_owner@example.test',password_hash=%s WHERE id='owner'",(_hash_password('SyntheticPassword123!'),))
    database[1].execute("UPDATE users SET email='synthetic_member@example.test',email_verified_at=now(),password_hash=%s WHERE id='author'",(_hash_password('SyntheticPassword123!'),))
    from test_bulk_rates import code,claim
    row=code(client,actor('owner'),note='Synthetic receipt preview')
    assert claim(client,actor,'author',row['code']).status_code==200
    print('Synthetic bulk preview: synthetic_owner@example.test and synthetic_member@example.test / SyntheticPassword123!',flush=True)

finally:
    try:next(clients)
    except StopIteration:pass
settings.public_origin='http://127.0.0.1:5197'
from app.main import app
try:uvicorn.run(app,host='127.0.0.1',port=8027,log_level='warning')
finally:
    try:next(prepared)
    except StopIteration:pass
