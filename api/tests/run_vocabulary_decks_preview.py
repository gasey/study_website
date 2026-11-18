"""Disposable synthetic vocabulary deck preview, no production questions/users."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import conftest,uvicorn
from test_vocabulary_decks import prepare
from app.routers.auth import _hash_password
from app.config import settings
prepared=conftest.fresh_database();database=next(prepared)
clients=conftest.client.__wrapped__(database);client=next(clients);conn=database[1]
try:
    prepare(conn)
    conn.execute("UPDATE users SET handle='synthetic_author',password_hash=%s WHERE id='author'",(_hash_password('SyntheticPassword123!'),))
    print('Synthetic vocabulary decks: author@example.test / SyntheticPassword123!',flush=True)
finally:
    try:next(clients)
    except StopIteration:pass
settings.public_origin='http://127.0.0.1:5194'
from app.main import app
try:uvicorn.run(app,host='127.0.0.1',port=8024,log_level='warning')
finally:
    try:next(prepared)
    except StopIteration:pass
