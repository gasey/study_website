"""Five connected workflows, synthetic records only."""
import asyncio,hashlib
from uuid import uuid4
from psycopg.types.json import Jsonb
from test_admin_workbench import workbench
from test_exam_inventory import create,body
from app.services.correction_notices import process

def learner(database,actor):
 conn=database[1];uid='learn-'+uuid4().hex
 conn.execute('INSERT INTO users(id,handle,email) VALUES(%s,%s,%s)',(uid,uid,uid+'@example.test'))
 token='test-session-'+uid
 conn.execute("INSERT INTO auth_sessions(token_hash,user_id,expires_at) VALUES(%s,%s,now()+interval '1 day')",(hashlib.sha256(token.encode()).hexdigest(),uid))
 h=actor(uid);h['X-Learning-User']=uid
 return uid,h

def official(database):
 conn=database[1];tag=uuid4().hex;q='learn-q-'+tag;a='learn-a-'+tag;p='learn-p-'+tag
 conn.execute("INSERT INTO papers(id,exam_type,exam_name,source_file,year) VALUES(%s,'Direct','Synthetic learning workflow','Old_Questions/test.pdf',2020)",(p,))
 conn.execute("INSERT INTO canonical_questions(id,type,question,options,answer_text,answer_source) VALUES(%s,'mcq','Synthetic learning question',%s,'B','official')",(q,Jsonb(['A','B','C','D'])))
 conn.execute("INSERT INTO appearances(id,paper_id,type,question,options,answer_index,answer_source,canonical_id,is_primary,qnum,page) VALUES(%s,%s,'mcq','Synthetic learning question',%s,1,'official',%s,true,'1',1)",(a,p,Jsonb(['A','B','C','D']),q))
 conn.execute("INSERT INTO question_classifications(question_id,subject_id,subject_label,taxonomy_version,source,review_status) VALUES(%s,'english','English','test','manual','approved')",(q,))
 return q,a,p

def attempt(conn,user,q,correct=False,chosen='A'):
 return conn.execute("INSERT INTO attempts(user_id,canonical_id,correct,chosen_text,context) VALUES(%s,%s,%s,%s,'practice') RETURNING id",(user,q,correct,chosen)).fetchone()[0]

def test_resume_bound_routes_and_conflicts(client,actor,database):
 user,h=learner(database,actor);q,a,p=official(database)
 assert client.get('/api/learning/resume').status_code==409
 r=client.get('/api/learning/resume',headers=h);assert r.status_code==200 and r.headers['cache-control']=='private, no-store'
 payload={'route':'/english?view=practice&exam_scope=all','question_id':q,'appearance_id':a,'expected_version':0}
 r=client.post('/api/learning/checkpoint',headers=h,json=payload);assert r.status_code==200,r.text
 assert client.post('/api/learning/checkpoint',headers=h,json=payload).status_code==409
 r=client.get('/api/learning/resume',headers=h);assert '/english?' in r.json()['items'][0]['url'] and '#question-'+q in r.json()['items'][0]['url']
 for route in ['https://evil.test/bank','//evil.test','/bank?token=secret','/admin/bank','/bank?exam_scope=all%0A']:
  assert client.post('/api/learning/checkpoint',headers=h,json={**payload,'route':route,'expected_version':1}).status_code==422
 assert client.post('/api/learning/checkpoint',headers={**h,'X-Learning-User':'owner'},json={**payload,'expected_version':1}).status_code==409
 assert client.post('/api/learning/checkpoint',headers={'X-Learning-User':user},json={**payload,'expected_version':1}).status_code==403
 assert client.post('/api/learning/checkpoint',headers=h,json={**payload,'appearance_id':'appearance-test','expected_version':1}).status_code==422

def test_daily_dedup_genuine_completion_and_account_isolation(client,actor,database):
 user,h=learner(database,actor);q,a,p=official(database);conn=database[1]
 attempt(conn,user,q)
 conn.execute('INSERT INTO personal_desks(user_id,document) VALUES(%s,%s)',(user,Jsonb({'saved':[q]})))
 r=client.get('/api/learning/revision',headers=h);assert r.status_code==200,r.text
 assert r.json()['available']==1 and r.json()['mistakes']==1 and r.json()['saved']==1
 s=client.post('/api/learning/revision/start',headers=h,json={});assert s.status_code==200,s.text
 sid=s.json()['id'];assert client.post('/api/learning/revision/start',headers=h,json={}).json()['id']==sid
 data=client.get('/api/learning/revision/'+sid,headers=h).json();assert len(data['items'])==1 and data['items'][0]['state']=='ready'
 latest=attempt(conn,user,q,True,'B')
 data=client.get('/api/learning/revision/'+sid,headers=h).json();assert data['items'][0]['state']=='completed'
 client.get('/api/learning/revision/'+sid,headers=h)
 assert conn.execute('SELECT count(*) FROM daily_revision_completions WHERE session_id=%s',(sid,)).fetchone()[0]==1
 assert conn.execute('SELECT attempt_id FROM daily_revision_completions WHERE session_id=%s',(sid,)).fetchone()[0]==latest
 assert client.get('/api/learning/revision',headers=h).json()['mistakes']==0
 other,oh=learner(database,actor)
 assert client.get('/api/learning/revision/'+sid,headers=oh).status_code==404
 assert client.post('/api/learning/revision/start',headers=oh,json={}).json()['id']!=sid

def test_daily_active_mock_and_unreviewed_answers_excluded(client,actor,database):
 user,h=learner(database,actor);q,a,p=official(database);conn=database[1]
 attempt(conn,user,q)
 cid='blocked-'+uuid4().hex
 conn.execute("INSERT INTO mock_sessions(id,user_id,collection_id,question_ids,duration_seconds) VALUES(%s,%s,'ldc',%s,60)",(cid,user,[q]))
 assert client.get('/api/learning/revision',headers=h).json()['available']==0
 conn.execute('DELETE FROM mock_sessions WHERE id=%s',(cid,))
 assert client.get('/api/learning/revision',headers=h).json()['available']==1
 conn.execute("UPDATE canonical_questions SET answer_source='derived' WHERE id=%s",(q,))
 assert client.get('/api/learning/revision',headers=h).json()['available']==0

def test_correction_notice_fanout_retry_preferences_and_answer_gate(client,actor,database):
 conn=database[1];user,h=learner(database,actor);q,a,p=official(database)
 aid=attempt(conn,user,q);conn.execute('INSERT INTO personal_desks(user_id,document) VALUES(%s,%s)',(user,Jsonb({'saved':[q]})))
 conn.execute('INSERT INTO inbox_preferences(user_id,in_app) VALUES(%s,%s)',(user,Jsonb({'scores':False})))
 before=conn.execute('SELECT correct,chosen_text FROM attempts WHERE id=%s',(aid,)).fetchone()
 conn.execute("UPDATE canonical_questions SET explanation='Synthetic explanation, no answer change' WHERE id=%s",(q,))
 eid=conn.execute('SELECT id FROM question_change_events WHERE question_id=%s ORDER BY id DESC LIMIT 1',(q,)).fetchone()[0]
 # Use API pool and its real transaction boundary; worker consumes one event per batch.
 async def drain():
  from app.db import cursor
  async with cursor() as cur:
   for _ in range(200):
    if not await process(cur):break
 client.portal.call(drain)
 notices=conn.execute('SELECT message,silent FROM review_notifications WHERE user_id=%s AND question_change_id=%s',(user,eid)).fetchall()
 assert len(notices)==1 and notices[0][1] is True and 'B' not in notices[0][0]
 conn.execute('UPDATE question_change_events SET finished_at=NULL,recipient_cursor=\'\' WHERE id=%s',(eid,));client.portal.call(drain)
 assert conn.execute('SELECT count(*) FROM review_notifications WHERE user_id=%s AND question_change_id=%s',(user,eid)).fetchone()[0]==1
 assert conn.execute('SELECT correct,chosen_text FROM attempts WHERE id=%s',(aid,)).fetchone()==before
 r=client.get('/api/learning/changes/'+str(eid),headers=h);assert r.status_code==200 and r.json()['changed_fields']==['explanation']
 cid='notice-mock-'+uuid4().hex;conn.execute("INSERT INTO mock_sessions(id,user_id,collection_id,question_ids,duration_seconds) VALUES(%s,%s,'ldc',%s,60)",(cid,user,[q]))
 assert client.get('/api/learning/changes/'+str(eid),headers=h).status_code==409
 conn.execute('DELETE FROM mock_sessions WHERE id=%s',(cid,))
 conn.execute('UPDATE canonical_questions SET explanation=explanation WHERE id=%s',(q,))
 assert conn.execute('SELECT count(*) FROM question_change_events WHERE question_id=%s',(q,)).fetchone()[0]==1
 other,oh=learner(database,actor);assert client.get('/api/learning/changes/'+str(eid),headers=oh).status_code==404

def test_quality_counts_match_filters_and_subject_scope(client,actor,workbench,database):
 ids,paper,alt=workbench;conn=database[1];eid,h=create(client,actor)
 client.post('/api/admin/bank/inventory/exams/'+eid+'/papers',headers=h,json={'paper_id':paper,'reason':'Synthetic quality scope association'})
 conn.execute('UPDATE canonical_questions SET key_disputed=true WHERE id=%s',(ids['keyed'],))
 conn.execute("UPDATE appearances SET has_diagram=true,figure_image=NULL WHERE id=%s",('app-'+ids['missing'],))
 for user in ['owner','reviewer1']:
  actor(user);r=client.get('/api/admin/bank/quality',params={'exam_id':eid,'year':2020});assert r.status_code==200,r.text;counts=r.json()
  for key,issue in [('missing','missing'),('disputed','disputed'),('missing_explanation','missing-explanation'),('missing_figure','missing-figure'),('missing_context','missing-context')]:
   r=client.get('/api/admin/bank/questions',params={'exam_id':eid,'year':2020,'issue':issue});assert r.status_code==200,r.text;assert r.json()['total']==counts[key]
 learner(database,actor);assert client.get('/api/admin/bank/quality').status_code==403

def test_intake_gates_stale_review_failures_and_actual_archive(client,actor,workbench,database,tmp_path,monkeypatch):
 ids,paper,alt=workbench;eid,h=create(client,actor);payload=body(eid,paper);payload['expected_questions']=8
 x=client.post('/api/admin/bank/inventory/expectations',headers=h,json=payload).json()['id']
 base='/api/admin/bank/intake/'+x
 note='Synthetic source and extraction evidence for the full intake flow'
 sha=hashlib.sha256(b'%PDF synthetic source').hexdigest()
 def step(stage,version,**extra):return client.post(base,headers=h,json={'stage':stage,'expected_version':version,'reason':note,**extra})
 assert step('published',0).status_code==409
 assert step('acquired',0).status_code==422
 r=step('acquired',0,source_sha256=sha);assert r.status_code==200,r.text
 assert step('acquired',0,source_sha256=sha).status_code==409
 assert step('extracted',1).status_code==422
 artifact={'source_sha256':sha,'text_sha256':'a'*64,'pages':2,'characters':500,'tool':'pdftotext','note':note}
 assert step('extracted',1,artifact={**artifact,'source_sha256':'b'*64}).status_code==422
 r=step('extracted',1,artifact=artifact);assert r.status_code==200,r.text
 assert step('review',2,retry_error='Source extraction needs repair').status_code==422
 assert step('extracted',2,retry_error='Source extraction needs repair').status_code==200
 r=step('review',3);assert r.status_code==200,r.text
 assert step('ready',4).status_code==409
 from app.config import settings
 monkeypatch.setattr(settings,'paper_archive_root',str(tmp_path));(tmp_path/'Old_Questions').mkdir();(tmp_path/'Old_Questions/test.pdf').write_bytes(b'%PDF synthetic source')
 r=step('ready',4);assert r.status_code==200,r.text
 database[1].execute("UPDATE appearances SET direction='Source context changed' WHERE paper_id=%s",(paper,))
 assert step('published',5).status_code==409
 assert step('review',5).status_code==200
 payload.update(expected_version=1,note=note)
 assert client.post('/api/admin/bank/inventory/expectations/'+x,headers=h,json=payload).status_code==200
 assert step('ready',6).status_code==200
 r=step('published',7);assert r.status_code==200 and r.json()['sync_id'] is not None,r.text
 assert client.get('/api/admin/bank/intake').status_code==200
 actor('reviewer1');assert client.get('/api/admin/bank/intake').status_code==403
 actor('outsider');assert client.get('/api/admin/bank/intake').status_code==403


def test_daily_selection_reserves_a_mix_and_deduplicates():
 from app.routers.learning import choose_daily
 rows=[{'id':'v'+str(i),'vocabulary':True,'mistake':False,'saved':False}for i in range(30)]
 rows +=[{'id':'m'+str(i),'vocabulary':False,'mistake':True,'saved':False}for i in range(10)]
 rows +=[{'id':'s'+str(i),'vocabulary':False,'mistake':False,'saved':True}for i in range(10)]
 chosen=choose_daily(rows)
 assert len(chosen)==len(set(chosen))==20
 assert sum(x.startswith('v')for x in chosen)==8
 assert sum(x.startswith('m')for x in chosen)==8
 assert sum(x.startswith('s')for x in chosen)==4
 assert choose_daily(rows[:3])==['v0','v1','v2']


def test_target_vocabulary_reuses_current_card_then_reviews_requested_question(client,actor,database):
 from test_vocabulary import seed,pick
 user,h=learner(database,actor);h['X-Vocabulary-User']=user
 ids=seed(database[1],2)
 r=client.post('/api/vocabulary/card',headers=h,json={'question_id':ids[0]});assert r.status_code==200,r.text
 first=r.json()['card'];assert first['question_id']==ids[0]
 r=client.post('/api/vocabulary/card',headers=h,json={'question_id':ids[1]});assert r.json()['card']['id']==first['id']
 assert pick(client,h,first).status_code==200
 r=client.post('/api/vocabulary/card',headers=h,json={'question_id':ids[1]});assert r.status_code==200,r.text
 second=r.json()['card'];assert second['question_id']==ids[1] and second['id']!=first['id']
 assert pick(client,h,second).status_code==200
 assert client.post('/api/vocabulary/card',headers=h,json={'question_id':ids[1]}).json()['card'] is None
