"""Disposable canonical composer preview. Synthetic content only; Ctrl-C drops DB."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import conftest,uvicorn
from test_discussions import question,answer,create,approve
from test_study_posts import ready
from app.routers.auth import _hash_password
from app.config import settings
prepared=conftest.fresh_database();database=next(prepared)
clients=conftest.client.__wrapped__(database);client=next(clients);conn=database[1]
try:
    actor=conftest.actor.__wrapped__(client)
    questions=question.__wrapped__(database);qid,_=next(questions)
    ready(conn,'author',established=False);ready(conn,'outsider',established=False)
    h=answer(client,actor,qid,'outsider')
    r=create(client,h,qid,body='Synthetic **question discussion**: how should we compare these options?\n- Read the original wording\n- Compare `A` and `B`',sources=[{'url':'https://example.test/source','note':'Synthetic source citation'}],context={'paper_id':'paper-test'});assert r.status_code==201,r.text
    pid=r.json()['id'];approve(client,actor,pid)
    h=answer(client,actor,qid,'author')
    r=create(client,h,qid,kind='reply',parent=pid,body='Synthetic **accepted reply**.\n1. Read `B` carefully\n2. Compare the source');assert r.status_code==201,r.text
    rid=r.json()['id'];approve(client,actor,rid)
    h=actor('outsider');assert client.post(f'/api/community/posts/{rid}/accept',headers=h,json={'enabled':True}).status_code==200
    conn.execute("UPDATE users SET password_hash=%s WHERE id='author'",(_hash_password('SyntheticPassword123!'),))
    print('Synthetic question: /bank/'+qid+'?paper=paper-test#discussion',flush=True)
finally:
    try:next(clients)
    except StopIteration:pass
settings.public_origin='http://127.0.0.1:5189'
print('Disposable canonical preview: author@example.test / SyntheticPassword123!',flush=True)
from app.main import app
try:uvicorn.run(app,host='127.0.0.1',port=8019,log_level='warning')
finally:
    try:next(questions)
    except StopIteration:pass
    try:next(prepared)
    except StopIteration:pass
