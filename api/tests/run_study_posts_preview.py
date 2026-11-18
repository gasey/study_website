"""Disposable V.10 study-note UI preview. All activity is synthetic; Ctrl-C drops DB."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import conftest,uvicorn
from test_study_posts import ready,note
from test_discussions import approve
from app.routers.auth import _hash_password
from app.config import settings

prepared=conftest.fresh_database();database=next(prepared)
clients=conftest.client.__wrapped__(database);client=next(clients);conn=database[1]
try:
    actor=conftest.actor.__wrapped__(client)
    ready(conn,'author',established=False);h=actor('author')
    result=note(client,h,body='Synthetic preview: practise a little every day, then revisit the questions you missed.',topic_tag='english')
    assert result.status_code==201,result.text;approve(client,actor,result.json()['id'])
    ready(conn,'outsider');h=actor('outsider')
    result=note(client,h,body='Synthetic preview: compare the wording in the original question before choosing an answer.',topic_tag='english',reference={'kind':'question','id':'cq_test'})
    assert result.status_code==201,result.text
    conn.execute("INSERT INTO creator_profiles(user_id,public) VALUES('outsider',true)")
    h=actor('author');assert client.post('/api/creators/outsider/follow',headers=h,json={'enabled':True}).status_code==200
    conn.execute("UPDATE users SET password_hash=%s WHERE id='author'",(_hash_password('SyntheticPassword123!'),))
finally:
    try:next(clients)
    except StopIteration:pass
settings.public_origin='http://127.0.0.1:5189'
print('Disposable study-note preview: author@example.test / SyntheticPassword123!; no production activity.',flush=True)
from app.main import app
try:uvicorn.run(app,host='127.0.0.1',port=8019,log_level='warning')
finally:
    try:next(prepared)
    except StopIteration:pass
