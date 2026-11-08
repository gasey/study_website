"""Server timing, frozen narrow sources, one-use boosts and reward replay."""
from uuid import uuid4
import pytest
from psycopg.types.json import Jsonb
from test_games_search import game_case

@pytest.fixture
def trail_case(client,actor,database,game_case):
 c,subject,users,headers,ids=game_case
 topic=subject+'/short-topic'
 c.execute("INSERT INTO review_taxonomy(id,label,parent_id,level,version) VALUES(%s,'Synthetic short topic',%s,'topic','test')",(topic,subject))
 c.execute('UPDATE question_classifications SET topic_id=%s,topic_label=%s WHERE question_id=ANY(%s)',(topic,'Synthetic short topic',ids))
 c.execute("INSERT INTO collection_papers(collection_id,version,paper_id,allow_browse) SELECT 'udc',live_version,'paper-test',true FROM collections WHERE id='udc' ON CONFLICT DO NOTHING")
 h=actor('owner');r=client.post('/api/topic-trail/packs',headers=h,json={'title':'Synthetic short topic trail','collection_id':'udc','taxonomy_id':topic,'reason':'Synthetic exact source and topic membership checked for this isolated test.'});assert r.status_code==200,r.text
 p=r.json();client.cookies.clear()
 yield c,users[0],headers[0],p,ids
 c.execute('UPDATE topic_trail_packs SET active=false WHERE id=%s',(p['id'],))
 c.execute("DELETE FROM collection_papers WHERE collection_id='udc' AND paper_id='paper-test'")

def start(client,h,p,key=None):
 r=client.post('/api/topic-trail/start',headers=h,json={'pack_id':p['id'],'context_hash':p['context_hash'],'request_key':key or uuid4().hex});assert r.status_code==200,r.text
 return r.json()
def begin(client,h,r,double=False):return client.post('/api/topic-trail/'+r['id']+'/begin',headers=h,json={'position':r['position']+(r['trail_phase']=='feedback'),'double':double})
def answer(client,h,r,choice=1):return client.post('/api/games/rooms/'+r['id']+'/answer',headers=h,json={'position':r['position'],'chosen_index':choice})

def test_full_run_score_boost_pause_and_exactly_once(client,trail_case):
 c,user,h,p,ids=trail_case;key=uuid4().hex;r=start(client,h,p,key)
 assert r['question'] is None and r['trail_phase']=='ready'
 assert start(client,h,p,key)['id']==r['id']
 assert answer(client,h,r).status_code==409
 for i in range(10):
  response=begin(client,h,r,double=i==0);assert response.status_code==200,response.text;r=response.json()
  assert r['question'] and 'answer_index' not in r['question'] and 'answer_text' not in r['question']
  if i==0:assert client.post('/api/topic-trail/'+r['id']+'/begin',headers=h,json={'position':i,'double':False}).status_code==409
  response=answer(client,h,r);assert response.status_code==200,response.text;r=response.json()
  assert r['trail_phase']=='feedback' and r['feedback']['correct']
  assert (c.execute('SELECT round_ends_at=deadline FROM game_rooms WHERE id=%s',(r['id'],)).fetchone())[0]
  if i==0:assert answer(client,h,r).json()['position']==i
 r=begin(client,h,r).json();assert r['state']=='finished' and r['trail_score']==1100 and r['trail_label']=='Perfect trail'
 assert r['players'][0]['correct']==10 and len(r['review'])==10
 before=c.execute('SELECT count(*) FROM attempts WHERE user_id=%s',(user,)).fetchone()[0]
 client.get('/api/games/rooms/'+r['id'],headers=h)
 assert c.execute('SELECT count(*) FROM attempts WHERE user_id=%s',(user,)).fetchone()[0]==before==10
 assert c.execute('SELECT count(*) FROM answer_reveals WHERE user_id=%s',(user,)).fetchone()[0]==10

def test_timeout_consumes_double_and_resume_original_question(client,trail_case):
 c,user,h,p,ids=trail_case;r=start(client,h,p);r=begin(client,h,r,True).json();qid=r['question']['id']
 assert client.get('/api/games/rooms/'+r['id'],headers=h).json()['question']['id']==qid
 c.execute("UPDATE game_rooms SET round_ends_at=now()-interval '1 second' WHERE id=%s",(r['id'],))
 r=client.get('/api/games/rooms/'+r['id'],headers=h).json();assert r['trail_phase']=='feedback' and not r['feedback']['correct'] and r['boost_used']
 assert begin(client,h,r,True).status_code==409
 assert begin(client,h,r).status_code==200

def test_changed_source_excluded_and_other_assessment_blocked(client,trail_case):
 c,user,h,p,ids=trail_case;r=start(client,h,p);r=begin(client,h,r).json();qid=r['question']['id']
 assert client.post('/api/topic-trail/start',headers=h,json={'pack_id':p['id'],'context_hash':p['context_hash'],'request_key':uuid4().hex}).status_code==409
 c.execute("UPDATE canonical_questions SET answer_text='C' WHERE id=%s",(qid,))
 r=answer(client,h,r).json();assert r['feedback']['excluded'] and r['feedback']['answer_index'] is None
 client.post('/api/games/rooms/'+r['id']+'/leave',headers=h,json={})
 r=client.get('/api/games/rooms/'+r['id'],headers=h).json()
 assert r['players'][0]['excluded']==1 and r['trail_score']==0
 assert c.execute('SELECT count(*) FROM attempts WHERE user_id=%s',(user,)).fetchone()[0]==0

def test_stale_pack_rejects_start(client,trail_case):
 c,user,h,p,ids=trail_case;c.execute('UPDATE topic_trail_packs SET version=version+1 WHERE id=%s',(p['id'],))
 r=client.post('/api/topic-trail/start',headers=h,json={'pack_id':p['id'],'context_hash':p['context_hash'],'request_key':uuid4().hex});assert r.status_code==409

def test_duplicate_booklets_do_not_inflate_pool(client,actor,trail_case):
 c,user,h,p,ids=trail_case
 # A second canonical ID with identical printed text/options must not create
 # a second stepping stone in the same run.
 duplicate='cq_duplicate_'+uuid4().hex
 c.execute('INSERT INTO canonical_questions(id,type,question,options,answer_text,answer_source) SELECT %s,type,question,options,answer_text,answer_source FROM canonical_questions WHERE id=%s',(duplicate,ids[0]))
 c.execute('INSERT INTO appearances(id,paper_id,type,question,options,answer_index,answer_source,canonical_id,is_primary) SELECT %s,paper_id,type,question,options,answer_index,answer_source,%s,true FROM appearances WHERE canonical_id=%s LIMIT 1',('a_'+duplicate,duplicate,ids[0]))
 c.execute('INSERT INTO question_classifications(question_id,subject_id,subject_label,topic_id,topic_label,taxonomy_version,source,review_status) SELECT %s,subject_id,subject_label,topic_id,topic_label,taxonomy_version,source,review_status FROM question_classifications WHERE question_id=%s',(duplicate,ids[0]))
 packs=client.get('/api/topic-trail',headers=h).json()['packs'];latest=next(x for x in packs if x['id']==p['id'])
 assert latest['available']==40

def test_explicit_sources_enforce_exact_pool_and_owner_access(client,actor,trail_case):
 c,user,h,p,ids=trail_case;owner=actor('owner')
 body={'id':p['id'],'expected_version':1,'title':'Synthetic exact source trail','collection_id':'udc','taxonomy_id':p['taxonomy_id'],'canonical_ids':ids[:10],'reason':'Exact synthetic source membership inspected for a bounded trail.'}
 r=client.post('/api/topic-trail/packs',headers=owner,json=body);assert r.status_code==200,r.text;assert r.json()['available']==10
 body.update(expected_version=2,canonical_ids=ids[:9]+['outside-pool'])
 assert client.post('/api/topic-trail/packs',headers=owner,json=body).status_code==422
 client.cookies.clear();assert client.get('/api/topic-trail/pool',headers=h,params={'collection_id':'udc','taxonomy_id':p['taxonomy_id']}).status_code==403
