"""Temporary clearly synthetic share preview, cleaned when stopped."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import conftest,uvicorn
from test_shareable_tests import create,publish
from app.config import settings
prepared=conftest.fresh_database();database=next(prepared)
clients=conftest.client.__wrapped__(database);client=next(clients)
try:
    actor=conftest.actor.__wrapped__(client)
    user,p,row=create(client,actor,database,title='Synthetic shared test preview')
    publish(client,actor,row,user)
    print('Synthetic published test: /api/tests/'+row['id']+'/share',flush=True)
finally:
    try:next(clients)
    except StopIteration:pass
settings.public_origin='http://127.0.0.1:5197'
from app.main import app
try:uvicorn.run(app,host='127.0.0.1',port=8027,log_level='warning')
finally:
    try:next(prepared)
    except StopIteration:pass
