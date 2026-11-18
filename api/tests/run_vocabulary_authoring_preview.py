"""Disposable synthetic word-card authoring; never production content."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import conftest,uvicorn
from test_content_studio import create
from test_curated_vocabulary_authoring import deck
from app.routers.auth import _hash_password
from app.config import settings
prepared=conftest.fresh_database();database=next(prepared)
clients=conftest.client.__wrapped__(database);client=next(clients);conn=database[1]
try:
    actor=conftest.actor.__wrapped__(client)
    conn.execute("UPDATE users SET handle='synthetic_author',password_hash=%s WHERE id='author'",(_hash_password('SyntheticPassword123!'),))
    doc=deck();doc['title']='Synthetic word-card authoring preview'
    mid,_,_=create(client,actor,doc)
    print('Synthetic word-card authoring: /studio/'+mid,flush=True)
    print('author@example.test / SyntheticPassword123!',flush=True)
finally:
    try:next(clients)
    except StopIteration:pass
settings.public_origin='http://127.0.0.1:5196'
from app.main import app
try:uvicorn.run(app,host='127.0.0.1',port=8026,log_level='warning')
finally:
    try:next(prepared)
    except StopIteration:pass
