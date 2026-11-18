"""Disposable synthetic author-work tracker, never a production fixture."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import conftest,uvicorn
from psycopg.types.json import Jsonb
from test_submission_tracker import bank,material,collection
from app.routers.auth import _hash_password
from app.config import settings
prepared=conftest.fresh_database();database=next(prepared)
clients=conftest.client.__wrapped__(database);client=next(clients);conn=database[1]
try:
    conn.execute("UPDATE users SET handle='synthetic_author',password_hash=%s WHERE id='author'",(_hash_password('SyntheticPassword123!'),))
    bid=bank(conn,state='submitted');mid=material(conn,state='changes_requested');cid=collection(conn,state='draft')
    payload={'kind':'practice','title':'Synthetic linked collection','description':'A synthetic private collection for the tracker preview.','subject_id':'english','question_ids':[],'sources':[],'month':None,'day':None,'occurrences':[],'themes':[],'suggested_minutes':10,'test_config':None}
    conn.execute('UPDATE learning_catalog SET payload=%s WHERE id=%s',(Jsonb(payload),cid))
    doc={'title':'Synthetic returned material','summary':'A synthetic private material for inspecting reviewer feedback.','preview':'','kind':'note','access':'free','price_paise':0,'tags':[],'blocks':[],'collection_id':None,'subject_id':None}
    conn.execute("INSERT INTO material_revisions(material_id,revision,payload,created_by) VALUES(%s,1,%s,'author')",(mid,Jsonb(doc)))
    conn.execute("INSERT INTO material_events(material_id,actor_id,action,detail) VALUES(%s,'owner','changes_requested','{\"revision\":1,\"reason\":\"Synthetic return note: name the source and explain which passages are your own work.\"}')",(mid,))
    print('Synthetic tracker: author@example.test / SyntheticPassword123!',flush=True)
finally:
    try:next(clients)
    except StopIteration:pass
settings.public_origin='http://127.0.0.1:5191'
from app.main import app
try:uvicorn.run(app,host='127.0.0.1',port=8021,log_level='warning')
finally:
    try:next(prepared)
    except StopIteration:pass
