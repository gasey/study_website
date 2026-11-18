"""Disposable contributor UI preview. Synthetic content only; Ctrl-C drops DB."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import conftest,uvicorn
from test_community_people import standing_fixture,public
from test_discussions import question,answer,create,approve
from test_study_posts import voters
from app.routers.auth import _hash_password
from app.config import settings

prepared=conftest.fresh_database();database=next(prepared)
clients=conftest.client.__wrapped__(database);client=next(clients);conn=database[1]
try:
    actor=conftest.actor.__wrapped__(client)
    pid=standing_fixture(conn,150);public(conn)
    conn.execute("UPDATE users SET handle='synthetic_guide',password_hash=%s WHERE id='author'",(_hash_password('SyntheticPassword123!'),))
    questions=question.__wrapped__(database);qid,_=next(questions)
    other=answer(client,actor,qid,'outsider');parent=create(client,other,qid,body='Synthetic question: how do we compare the wording with its source?').json()['id'];approve(client,actor,parent)
    h=answer(client,actor,qid,'author');rid=create(client,h,qid,kind='reply',parent=parent,body='Synthetic **source-based method**: compare the wording before choosing an option.').json()['id'];approve(client,actor,rid)
    other=actor('outsider');assert client.post(f'/api/community/posts/{rid}/accept',headers=other,json={'enabled':True}).status_code==200
    voters(conn,rid,1,qualified=True)
    print('Synthetic tier note: /community?study='+str(pid),flush=True)
    print('Synthetic discussion: /bank/'+qid+'?paper=paper-test#discussion',flush=True)
finally:
    try:next(clients)
    except StopIteration:pass
settings.public_origin='http://127.0.0.1:5189'
print('Synthetic contributor preview: author@example.test / SyntheticPassword123!',flush=True)
from app.main import app
try:uvicorn.run(app,host='127.0.0.1',port=8019,log_level='warning')
finally:
    try:next(questions)
    except StopIteration:pass
    try:next(prepared)
    except StopIteration:pass
