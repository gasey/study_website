"""Disposable synthetic quiz preview; all data is removed when stopped."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import conftest,uvicorn
from test_onboarding import setup
from app.routers.auth import _hash_password
from app.config import settings
prepared=conftest.fresh_database();database=next(prepared)
clients=conftest.client.__wrapped__(database);client=next(clients)
try:
    actor=conftest.actor.__wrapped__(client)
    user,h,exam,ids,paper=setup(client,actor,database)
    database[1].execute("UPDATE users SET email='synthetic_checkin@example.test',handle='synthetic_checkin',password_hash=%s WHERE id=%s",(_hash_password('SyntheticPassword123!'),user))
    print('Synthetic check-in: /onboarding; synthetic_checkin@example.test / SyntheticPassword123!',flush=True)
finally:
    try:next(clients)
    except StopIteration:pass
settings.public_origin='http://127.0.0.1:5197'
from app.main import app
try:uvicorn.run(app,host='127.0.0.1',port=8027,log_level='warning')
finally:
    try:next(prepared)
    except StopIteration:pass
