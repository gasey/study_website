"""Disposable synthetic quiz preview; all data is removed when stopped."""
from pathlib import Path
import sys,signal
signal.signal(signal.SIGTERM,lambda *_:sys.exit(0))
sys.path.insert(0,str(Path(__file__).resolve().parent))
import conftest,uvicorn
from app.routers.auth import _hash_password
from app.config import settings
prepared=conftest.fresh_database();database=next(prepared)
Path('/tmp/finna-users-preview-db.txt').write_text(database[0])
clients=conftest.client.__wrapped__(database);client=next(clients)
try:
    actor=conftest.actor.__wrapped__(client)
    database[1].execute("UPDATE users SET email='synthetic_owner@example.test',password_hash=%s WHERE id='owner'",(_hash_password('SyntheticPassword123!'),))
    database[1].execute("UPDATE users SET email='synthetic_member@example.test',email_verified_at=now(),password_hash=%s WHERE id='author'",(_hash_password('SyntheticPassword123!'),))
    database[1].execute("INSERT INTO billing_account_rates(user_id,amount_paise,updated_by) VALUES('author',5000,'owner')")
    database[1].execute("INSERT INTO billing_access_grants(user_id,granted_by,idempotency_key,days,starts_at,ends_at) VALUES('author','owner','synthetic-preview',7,now(),now()+interval '7 days')")
    database[1].execute("INSERT INTO reward_ledger(user_id,event_key,kind,xp,points,note) VALUES('author','synthetic:preview','adjustment',15,3,'Synthetic preview only')")
    database[1].execute("INSERT INTO creator_blocks(user_id,blocked_id) VALUES('author','outsider')")
    print('Synthetic account viewer preview ready',flush=True)

finally:
    try:next(clients)
    except StopIteration:pass
settings.public_origin='http://127.0.0.1:5197'
from app.main import app
try:uvicorn.run(app,host='127.0.0.1',port=8027,log_level='warning')
finally:
    try:next(prepared)
    except StopIteration:pass
