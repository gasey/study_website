"""Disposable local Atlas curation/browser fixture; never a real reviewed binding."""
from pathlib import Path
from uuid import uuid4
import json,signal,sys
signal.signal(signal.SIGTERM,lambda *_:sys.exit(0))
sys.path.insert(0,str(Path(__file__).resolve().parent))
import conftest,uvicorn
from app.config import settings
from app.routers.auth import _hash_password
from psycopg.types.json import Jsonb
from app.services.atlas_bindings import CHAPTERS
marker=Path('/tmp/finna-atlas-bindings-preview.json')
prepared=conftest.fresh_database();database=next(prepared)
clients=conftest.client.__wrapped__(database);client=next(clients)
try:
 conn=database[1];topic='english/atlas-synthetic-qa'
 conn.execute("UPDATE users SET email='synthetic_atlas@example.test',password_hash=%s,plan_code='pro',plan_status='trial',trial_ends_at=now()+interval '7 days' WHERE id='owner'",(_hash_password('SyntheticPassword123!'),))
 conn.execute("INSERT INTO review_taxonomy(id,label,parent_id,level,version) VALUES(%s,'Synthetic Atlas QA topic','english','topic','synthetic')",(topic,))
 for n in range(8):
  qid='atlas_qa_'+uuid4().hex
  conn.execute("INSERT INTO canonical_questions(id,type,question,options,answer_text,answer_source) VALUES(%s,'mcq',%s,%s,'B','official')",(qid,'Synthetic Atlas QA '+str(n+1)+': choose option B. This is disposable test content.',Jsonb(['A','B','C','D'])))
  conn.execute("INSERT INTO appearances(id,paper_id,type,question,options,answer_index,answer_source,canonical_id,is_primary,qnum,page) VALUES(%s,'paper-test','mcq',%s,%s,1,'official',%s,true,%s,1)",('atlas_app_'+uuid4().hex,'Synthetic Atlas QA '+str(n+1)+': choose option B. This is disposable test content.',Jsonb(['A','B','C','D']),qid,str(n+2)))
  conn.execute("INSERT INTO question_classifications(question_id,subject_id,subject_label,topic_id,topic_label,taxonomy_version,source,review_status) VALUES(%s,'english','English',%s,'Synthetic Atlas QA topic','synthetic','manual','approved')",(qid,topic))
 marker.write_text(json.dumps({'database':database[0],'chapter_id':'rivers-of-india','layer_id':CHAPTERS['rivers-of-india']['layers'][0]['id'],'topic_id':topic}))
 print('Synthetic Atlas preview ready; no binding published.',flush=True)
finally:
 try:next(clients)
 except StopIteration:pass
settings.public_origin='http://localhost:5197'
from app.main import app
try:uvicorn.run(app,host='127.0.0.1',port=8027,log_level='warning')
finally:
 try:next(prepared)
 except StopIteration:pass
 marker.unlink(missing_ok=True)
