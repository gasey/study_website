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
marker=Path('/tmp/finna-atlas-depth-preview.json')
prepared=conftest.fresh_database();database=next(prepared)
clients=conftest.client.__wrapped__(database);client=next(clients)
try:
 conn=database[1]
 conn.execute("UPDATE users SET email='synthetic_drills@example.test',password_hash=%s,plan_code='pro',plan_status='trial',trial_ends_at=now()+interval '7 days' WHERE id='owner'",(_hash_password('SyntheticPassword123!'),))
 conn.execute("INSERT INTO review_taxonomy(id,label,level,version) VALUES('geography','Geography','subject','synthetic') ON CONFLICT DO NOTHING")
 conn.execute("INSERT INTO review_taxonomy(id,label,parent_id,level,version) VALUES('geography/synthetic-drill-qa','Synthetic drill QA topic','geography','topic','synthetic')")
 conn.execute("INSERT INTO canonical_questions(id,type,question,options,answer_text,answer_source) VALUES('synthetic_atlas_drill_q','mcq','When was the Battle of Synthetic fought?',%s,'1757','official')",(Jsonb(['1757','1857','1957','2000']),))
 conn.execute("INSERT INTO appearances(id,paper_id,type,question,options,answer_index,answer_source,canonical_id,is_primary,qnum,page) VALUES('synthetic_atlas_drill_app','paper-test','mcq','When was the Battle of Synthetic fought?',%s,0,'official','synthetic_atlas_drill_q',true,'2',1)",(Jsonb(['1757','1857','1957','2000']),))
 conn.execute("INSERT INTO question_classifications(question_id,subject_id,subject_label,topic_id,topic_label,taxonomy_version,source,review_status) VALUES('synthetic_atlas_drill_q','geography','Geography','geography/synthetic-drill-qa','Synthetic drill QA topic','synthetic','manual','approved')")
 conn.execute("INSERT INTO user_exam_bookmarks(user_id,collection_id,is_primary) VALUES('owner','udc',true)")
 conn.execute("INSERT INTO collection_sections(collection_id,version,path,title,position,query) SELECT 'udc',live_version,'synthetic-atlas','Synthetic Atlas syllabus fixture',50,%s FROM collections WHERE id='udc'",(Jsonb({'subject_id':'geography','topic_id':'geography/synthetic-drill-qa'}),))
 marker.write_text(json.dumps({'database':database[0],'seeded_chapters':26}))
 print('Synthetic drill preview ready; existing 26 chapters attributed as current-site content.',flush=True)
finally:
 try:next(clients)
 except StopIteration:pass
settings.public_origin='http://localhost:5198'
from app.main import app
try:uvicorn.run(app,host='127.0.0.1',port=8028,log_level='warning')
finally:
 try:next(prepared)
 except StopIteration:pass
 marker.unlink(missing_ok=True)
