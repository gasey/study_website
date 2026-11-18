"""Disposable synthetic profile/shop UI fixture. Ctrl-C drops its database."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import conftest,uvicorn
from uuid import uuid4

databases=conftest.fresh_database();database=next(databases)
clients=conftest.client.__wrapped__(database);client=next(clients)
conn=database[1]
from app.config import settings
settings.public_origin='http://127.0.0.1:5189'
from app.routers.auth import _hash_password
for user in ('author','owner'):
 conn.execute('UPDATE users SET password_hash=%s WHERE id=%s',(_hash_password('SyntheticPassword123!'),user))
conn.execute("INSERT INTO reward_ledger(user_id,event_key,kind,points,note) VALUES('author',%s,'adjustment',200,'Synthetic UI test wallet only')",(uuid4().hex,))
print('Synthetic local profile/shop preview: author@example.test / SyntheticPassword123!. No production data.',flush=True)
from app.main import app
try:next(clients)
except StopIteration:pass
try:uvicorn.run(app,host='127.0.0.1',port=8019,log_level='warning')
finally:
 try:next(databases)
 except StopIteration:pass
