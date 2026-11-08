"""Discovery has real signals, dated editorial control and no answer exposure."""
from datetime import date,timedelta
from uuid import uuid4
import pytest
from psycopg.types.json import Jsonb
from app.services import discovery as d
from test_learning_workflows import official

@pytest.fixture
def source(database,client):
 q,a,p=official(database);c=database[1]
 c.execute("INSERT INTO collection_papers(collection_id,version,paper_id,section_path,as_mock,allow_browse) SELECT 'combined-prelims',live_version,%s,'gs',false,true FROM collections WHERE id='combined-prelims'",(p,))
 c.execute("UPDATE canonical_questions SET question='Discovery source stem',explanation='A source checked explanation.' WHERE id=%s",(q,))
 d.clear_cache();yield q,a,p;d.clear_cache()

def get(client):return client.get('/api/discovery',params={'collection_id':'combined-prelims','limit':6})

def signal(database,q,n=5):
 c=database[1];prefix=uuid4().hex
 for i in range(n):
  user='discovery_'+prefix+str(i)
  c.execute("INSERT INTO users(id,handle,email) VALUES(%s,%s,%s)",(user,user,user+'@learner.invalid'))
  for _ in range(3):c.execute("INSERT INTO attempts(user_id,canonical_id,chosen_text,correct,context) VALUES(%s,%s,'B',true,'practice')",(user,q))

def test_sparse_then_real_distinct_activity_no_answer_or_attempt(client,actor,database,source):
 actor('outsider');q,a,p=source;before=database[1].execute('SELECT count(*) FROM attempts').fetchone()[0]
 r=get(client);assert r.status_code==200,r.text;assert not r.json()['popular']
 assert database[1].execute('SELECT count(*) FROM attempts').fetchone()[0]==before
 signal(database,q,4);d.clear_cache();assert not get(client).json()['popular']
 signal(database,q,1);d.clear_cache();r=get(client);rows=r.json()['popular'];assert len(rows)==1,r.text
 assert rows[0]['score']==10 and rows[0]['participants']==5
 assert rows[0]['appearance_id']==a and rows[0]['paper_id']==p and rows[0]['url'].startswith('/bank/')
 assert 'answer' not in str(rows) and 'explanation' not in str(rows)
 database[1].execute("UPDATE canonical_questions SET status='held' WHERE id=%s",(q,));assert not get(client).json()['popular']

def test_assessment_withheld(client,actor,database,source):
 q,a,p=source;actor('outsider');c=database[1]
 c.execute("INSERT INTO mock_sessions(id,user_id,collection_id,question_ids,duration_seconds) VALUES(%s,'outsider','combined-prelims',%s,600)",('disc_mock_'+uuid4().hex,[q]))
 r=get(client);assert r.status_code==200,r.text;assert r.json()['withheld'] and not r.json()['hot']
 c.execute("DELETE FROM mock_sessions WHERE user_id='outsider' AND submitted_at IS NULL")

def test_owner_pick_lifecycle_and_stale_version(client,actor,database,source):
 q,a,p=source;c=database[1];tid='english:disc_'+uuid4().hex
 c.execute("INSERT INTO review_taxonomy(id,parent_id,level,label,version) VALUES(%s,'english','topic','Discovery topic','test')",(tid,))
 c.execute('UPDATE question_classifications SET topic_id=%s WHERE question_id=%s',(tid,q))
 body={'collection_id':'combined-prelims','taxonomy_id':tid,'title':'A timely study topic','why_now':'A new official syllabus notice makes this topic useful for revision.','sources':[{'url':'https://example.test/official-notice','title':'Synthetic official syllabus notice','published_on':date.today().isoformat(),'checked_on':date.today().isoformat()}],'reason':'Owner checked source and exam relevance in this isolated fixture.'}
 h=actor('outsider');assert client.post('/api/discovery/picks',headers=h,json=body).status_code==403
 h=actor('owner');r=client.post('/api/discovery/picks',headers=h,json=body);assert r.status_code==200,r.text;row=r.json()
 assert not get(client).json()['hot']
 decision={'expected_version':1,'action':'publish','reason':'Inspected source, relevance and dates; no factual answer asserted.'}
 r=client.post('/api/discovery/picks/'+row['id']+'/decision',headers=h,json=decision);assert r.status_code==200,r.text
 r=get(client);assert len(r.json()['hot'])==1,r.text
 assert client.post('/api/discovery/picks/'+row['id']+'/decision',headers=h,json=decision).status_code==409
 c.execute("UPDATE discovery_picks SET expires_at=now()-interval '1 minute' WHERE id=%s",(row['id'],));assert not get(client).json()['hot']

def test_invalid_dates_and_scope(client,actor,source):
 actor('outsider');assert client.get('/api/discovery?collection_id=unknown').status_code==422
 assert client.get('/api/discovery?collection_id=udc&limit=100').status_code==422
 assert client.get('/api/discovery/manage').status_code==403

def test_booklet_activity_counts_each_learner_once(client,actor,database):
 c=database[1];tag=uuid4().hex;qs=[]
 for letter in ('A','B'):
  pid='Old_Questions/Discovery-'+tag+' Series '+letter+'.pdf';qid='booklet_'+tag+letter;aid='booklet_a_'+tag+letter;qs.append(qid)
  c.execute("INSERT INTO papers(id,exam_type,exam_name,year) VALUES(%s,'Direct','Synthetic same sitting',2023)",(pid,))
  c.execute("INSERT INTO canonical_questions(id,type,question,options,answer_text,answer_source) VALUES(%s,'mcq','Identical booklet practice item',%s,'B','official')",(qid,Jsonb(['A','B','C','D'])))
  c.execute("INSERT INTO appearances(id,paper_id,canonical_id,is_primary,type,question,options,answer_index,answer_source) VALUES(%s,%s,%s,true,'mcq','Identical booklet practice item',%s,1,'official')",(aid,pid,qid,Jsonb(['A','B','C','D'])))
  c.execute("INSERT INTO collection_papers(collection_id,version,paper_id,section_path,as_mock) SELECT 'combined-prelims',live_version,%s,'gs',false FROM collections WHERE id='combined-prelims'",(pid,))
 users=[]
 for i in range(5):
  user='group_'+tag+str(i);users.append(user);c.execute('INSERT INTO users(id,handle,email) VALUES(%s,%s,%s)',(user,user,user+'@learner.invalid'))
  for qid in qs:c.execute("INSERT INTO attempts(user_id,canonical_id,chosen_text,correct,context) VALUES(%s,%s,'B',true,'practice')",(user,qid))
 actor('outsider');d.clear_cache();r=get(client);assert r.status_code==200,r.text
 rows=[x for x in r.json()['popular'] if x['id'] in qs];assert len(rows)==1,r.text
 assert rows[0]['participants']==5 and rows[0]['score']==10
 c.execute("UPDATE canonical_questions SET explanation='Different solution: do not group this source' WHERE id=%s",(qs[1],));d.clear_cache()
 assert len([x for x in get(client).json()['popular'] if x['id'] in qs])==2

def test_unpublished_and_expired_fact_support_is_not_current(client,database):
 async def run(rid):
  from app.db import cursor
  async with cursor() as cur:return await d.fact_current(cur,rid)
 assert client.portal.call(run,None)
 assert not client.portal.call(run,999999999)

def test_hot_pick_disappears_when_supporting_source_changes(client,actor,database,source):
 from test_current_affairs import proposal,publish
 q,a,p=source;c=database[1];tid='english:dated_'+uuid4().hex
 c.execute("INSERT INTO review_taxonomy(id,parent_id,level,label,version) VALUES(%s,'english','topic','Dated discovery topic','test')",(tid,))
 c.execute('UPDATE question_classifications SET topic_id=%s WHERE question_id=%s',(tid,q))
 body,h=proposal(client,actor,[(q,a,p)]);rid=publish(client,actor,body,h)
 h=actor('owner');pick={'collection_id':'combined-prelims','taxonomy_id':tid,'title':'A sourced timely pick','why_now':'This isolated fixture tests a dated, independently reviewed factual connection.','fact_revision_id':rid,'sources':[{'url':'https://example.test/source','title':'Synthetic primary evidence','published_on':date.today().isoformat(),'checked_on':date.today().isoformat()}],'reason':'Owner reviewed independent factual support and exam relevance.'}
 r=client.post('/api/discovery/picks',headers=h,json=pick);assert r.status_code==200,r.text
 pid=r.json()['id'];r=client.post('/api/discovery/picks/'+pid+'/decision',headers=h,json={'expected_version':1,'action':'publish','reason':'Owner checked dated evidence and independently published connection.'});assert r.status_code==200,r.text
 assert any(x['id']==pid for x in get(client).json()['hot'])
 c.execute("UPDATE canonical_questions SET explanation='A human changed the supporting question context.' WHERE id=%s",(q,))
 assert not any(x['id']==pid for x in get(client).json()['hot'])
