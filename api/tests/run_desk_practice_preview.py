"""Synthetic local-only Desk preview; database and marker removed on exit."""
from pathlib import Path
from uuid import uuid4
import json
import signal
import sys

signal.signal(signal.SIGTERM, lambda *_:sys.exit(0))
sys.path.insert(0,str(Path(__file__).resolve().parent))
import conftest
import uvicorn
from app.config import settings
from app.routers.auth import _hash_password
from psycopg.types.json import Jsonb
from test_desk_goals import question

marker = Path('/tmp/finna-desk-practice-preview.json')
prepared = conftest.fresh_database(); database = next(prepared)
clients = conftest.client.__wrapped__(database); client = next(clients)
did = 'desk_'+uuid4().hex
try:
    conn = database[1]
    settings.study_desks_private_enabled = True
    conn.execute("UPDATE users SET email='synthetic_desk@example.test',password_hash=%s WHERE id='author'",(_hash_password('SyntheticPassword123!'),))
    conn.execute("UPDATE users SET plan_code='pro',plan_status='trial',trial_ends_at=now()+interval '7 days' WHERE id='author'")
    conn.execute("INSERT INTO study_desks(id,owner_id,name,goal) VALUES(%s,'author','Synthetic Practice QA','Disposable fixture for layout and interaction checks')",(did,))
    conn.execute("INSERT INTO study_desk_members(desk_id,user_id,sharing) VALUES(%s,'author',%s),(%s,'outsider',%s)", (did,Jsonb({'progress':True,'times':False,'mistakes':False}),did,Jsonb({'progress':True,'times':False,'mistakes':False})))
    for n in range(10):
        qid = question(conn)
        conn.execute('UPDATE canonical_questions SET question=%s WHERE id=%s',('Synthetic practice question '+str(n+1)+': choose option B',qid))
        conn.execute("INSERT INTO appearances(id,paper_id,type,question,options,answer_index,answer_source,canonical_id,is_primary,qnum,page) SELECT %s,'paper-test',type,question,options,1,answer_source,id,true,%s,1 FROM canonical_questions WHERE id=%s",('appearance_'+uuid4().hex,str(n+2),qid))
        conn.execute("INSERT INTO question_classifications(question_id,subject_id,subject_label,taxonomy_version,source,review_status) VALUES(%s,'english','English','synthetic','manual','approved')",(qid,))
        conn.execute("INSERT INTO study_desk_items(id,desk_id,author_id,kind,question_id,body,request_key,request_hash) VALUES(%s,%s,'author','question',%s,'Synthetic shared question for practice QA',%s,'synthetic')",('item_'+uuid4().hex,did,qid,uuid4().hex))
    conn.execute("INSERT INTO study_desk_weekly_goals(desk_id,week_start,target,updated_by) VALUES(%s,(date_trunc('week',now() AT TIME ZONE 'Asia/Kolkata'))::date,10,'author')",(did,))
    marker.write_text(json.dumps({'database':database[0],'desk_id':did}))
    print('Synthetic local Desk preview ready',flush=True)
finally:
    try:next(clients)
    except StopIteration:pass
settings.public_origin = 'http://127.0.0.1:5197'
from app.main import app
try:
    uvicorn.run(app,host='127.0.0.1',port=8027,log_level='warning')
finally:
    try:next(prepared)
    except StopIteration:pass
    marker.unlink(missing_ok=True)
