"""Synthetic dated editorial claims, exact-source access and historical integrity."""
from datetime import date,timedelta
from uuid import uuid4
import pytest
import psycopg
from psycopg.types.json import Jsonb

@pytest.fixture
def sources(database,client):
 c=database[1];key=uuid4().hex;rows=[]
 for i,year in enumerate((2020,2026)):
  q='ca_q_'+key+str(i);a='ca_a_'+key+str(i);p='ca_p_'+key+str(i)
  c.execute("INSERT INTO papers(id,exam_type,exam_name,year) VALUES(%s,'Direct','Synthetic timeline paper',%s)",(p,year))
  c.execute("INSERT INTO canonical_questions(id,type,question,options,answer_text,answer_source) VALUES(%s,'mcq','Who held the synthetic office at that exam date?',%s,'Historical name','official')",(q,Jsonb(['Earlier name','Historical name','Other name','Another name'])))
  c.execute("INSERT INTO appearances(id,paper_id,canonical_id,is_primary,type,question,options,qnum) VALUES(%s,%s,%s,true,'mcq','Who held this synthetic office?',%s,'1')",(a,p,q,Jsonb(['A','B','C','D'])))
  c.execute("INSERT INTO question_classifications(question_id,subject_id,subject_label,taxonomy_version,source,review_status) VALUES(%s,'english','English','test','manual','approved')",(q,))
  rows.append((q,a,p))
 return rows

def proposal(client,actor,sources,user='reviewer1'):
 h=actor(user);links=[]
 for q,a,p in sources:
  snap=client.get('/api/review/questions/'+q,params={'appearance_id':a});assert snap.status_code==200,snap.text
  links.append({'canonical_id':q,'appearance_id':a,'source_version':snap.json()['baseline_token'],'reference_date':None,'date_basis':'Exact sitting date is unknown; only the source year is recorded.','context':'This is historical context, not a replacement for the printed options.','relation':'same-changing-fact'})
 d=date.today()
 body={'request_key':uuid4().hex,'name':'Synthetic election office '+uuid4().hex,'jurisdiction':'Synthetic jurisdiction','predicate':'officeholder','facts':[{'value':'A separately sourced synthetic later officeholder','effective_on':'2025-01-01','effective_until':None,'source_url':'https://example.test/primary-source','source_title':'Synthetic primary source, page one','source_date':'2025-01-01','checked_on':d.isoformat(),'review_due':(d+timedelta(days=30)).isoformat()}],'links':links,'reason':'Connect historical source questions without changing their keys.'}
 return body,h

def publish(client,actor,body,h):
 r=client.post('/api/current-affairs/proposals',headers=h,json=body);assert r.status_code==201,r.text
 rid=r.json()['id'];owner=actor('owner')
 r=client.post(f'/api/current-affairs/revisions/{rid}/decision',headers=owner,json={'expected_version':0,'action':'publish','reason':'Independently inspected both synthetic source questions and the evidence.'});assert r.status_code==200,r.text
 return rid

def reveal(database,user,qid):
 database[1].execute("INSERT INTO answer_reveals(user_id,canonical_id) VALUES(%s,%s) ON CONFLICT(user_id,canonical_id) DO NOTHING",(user,qid))

def test_publication_preserves_historical_keys_and_requires_reveal(client,actor,sources,database):
 body,h=proposal(client,actor,sources)
 c=database[1];before=c.execute('SELECT id,answer_text,answer_source FROM canonical_questions WHERE id=ANY(%s) ORDER BY id',([s[0] for s in sources],)).fetchall()
 publish(client,actor,body,h)
 h=actor('outsider');q=sources[0][0]
 assert client.post('/api/current-affairs/view',headers=h,json={'canonical_id':q}).status_code==403
 reveal(database,'outsider',q)
 r=client.post('/api/current-affairs/view',headers=h,json={'canonical_id':q,'paper_id':sources[0][2]});assert r.status_code==200,r.text
 assert r.headers['cache-control']=='private, no-store'
 data=r.json()['items'];assert len(data)==1 and len(data[0]['questions'])==2
 assert data[0]['facts'][0]['value']==body['facts'][0]['value']
 assert data[0]['questions'][0]['year']==2026
 assert c.execute('SELECT id,answer_text,answer_source FROM canonical_questions WHERE id=ANY(%s) ORDER BY id',([s[0] for s in sources],)).fetchall()==before
 assert c.execute("SELECT count(*) FROM answer_reveals WHERE user_id='outsider' AND canonical_id=ANY(%s)",([s[0] for s in sources],)).fetchone()[0]==2
 assert c.execute("SELECT count(*) FROM attempts WHERE user_id='outsider' AND canonical_id=ANY(%s)",([s[0] for s in sources],)).fetchone()[0]==0
 assert client.post('/api/current-affairs/view',headers=h,json={'canonical_id':q,'paper_id':'wrong-paper'}).json()['items']==[]

def test_author_cannot_publish_own_and_outsider_cannot_propose(client,actor,sources):
 body,h=proposal(client,actor,sources,user='owner')
 rid=client.post('/api/current-affairs/proposals',headers=h,json=body).json()['id']
 assert client.post(f'/api/current-affairs/revisions/{rid}/decision',headers=h,json={'expected_version':0,'action':'publish','reason':'I must not publish my own sourced timeline claim.'}).status_code==403
 h=actor('outsider');body['request_key']=uuid4().hex
 assert client.post('/api/current-affairs/proposals',headers=h,json=body).status_code==403
 assert client.get('/api/current-affairs/manage').json()['items']==[]

def test_idempotency_mismatch_and_immutable_history(client,actor,sources,database):
 body,h=proposal(client,actor,sources);r=client.post('/api/current-affairs/proposals',headers=h,json=body);assert r.status_code==201,r.text
 rid=r.json()['id'];assert client.post('/api/current-affairs/proposals',headers=h,json=body).json()['id']==rid
 body['reason']='Different reason must not overwrite immutable submitted content.'
 assert client.post('/api/current-affairs/proposals',headers=h,json=body).status_code==409
 with pytest.raises(psycopg.Error):database[1].execute("UPDATE current_affairs_revisions SET payload='{}'::jsonb WHERE id=%s",(rid,))
 with pytest.raises(psycopg.Error):database[1].execute('DELETE FROM current_affairs_links WHERE revision_id=%s',(rid,))

@pytest.mark.parametrize('invalid',['overlap','future-check','http-source','duplicate-link','bad-interval'])
def test_invalid_fact_context_rejected(client,actor,sources,invalid):
 body,h=proposal(client,actor,sources)
 if invalid=='overlap':body['facts'].append(dict(body['facts'][0]))
 if invalid=='future-check':body['facts'][0]['checked_on']=(date.today()+timedelta(days=1)).isoformat()
 if invalid=='http-source':body['facts'][0]['source_url']='http://example.test/source'
 if invalid=='duplicate-link':body['links'].append(dict(body['links'][0]))
 if invalid=='bad-interval':body['facts'][0]['effective_until']='2024-01-01'
 assert client.post('/api/current-affairs/proposals',headers=h,json=body).status_code==422

def test_stale_source_blocks_submit_publish_and_read(client,actor,sources,database):
 body,h=proposal(client,actor,sources);rid=client.post('/api/current-affairs/proposals',headers=h,json=body).json()['id']
 database[1].execute("UPDATE appearances SET question='A changed synthetic printed source' WHERE id=%s",(sources[0][1],))
 body['request_key']=uuid4().hex
 assert client.post('/api/current-affairs/proposals',headers=h,json=body).status_code==409
 h=actor('owner');assert client.post(f'/api/current-affairs/revisions/{rid}/decision',headers=h,json={'expected_version':0,'action':'publish','reason':'Stale source must fail independent publication checks.'}).status_code==409
 body,h=proposal(client,actor,sources);publish(client,actor,body,h)
 database[1].execute("UPDATE appearances SET question='Another changed synthetic source' WHERE id=%s",(sources[0][1],))
 reveal(database,'outsider',sources[0][0]);h=actor('outsider')
 assert client.post('/api/current-affairs/view',headers=h,json={'canonical_id':sources[0][0]}).json()['items']==[]

def test_retraction_version_and_independent_replacement(client,actor,sources,database):
 body,h=proposal(client,actor,sources);rid=publish(client,actor,body,h)
 h=actor('reviewer1');row=next(r for r in client.get('/api/current-affairs/manage').json()['items'] if r['id']==rid)
 body.update(entity_id=row['entity_id'],base_version=1,request_key=uuid4().hex)
 rid2=client.post('/api/current-affairs/proposals',headers=h,json=body).json()['id']
 h=actor('owner');assert client.post(f'/api/current-affairs/revisions/{rid2}/decision',headers=h,json={'expected_version':0,'action':'publish','reason':'An outdated entity version is rejected rather than overwritten.'}).status_code==409
 assert client.post(f'/api/current-affairs/revisions/{rid2}/decision',headers=h,json={'expected_version':1,'action':'publish','reason':'Independent source inspection supports the replacement revision.'}).status_code==200
 c=database[1];assert c.execute('SELECT state FROM current_affairs_revisions WHERE id=%s',(rid,)).fetchone()[0]=='superseded'
 assert client.post(f'/api/current-affairs/revisions/{rid2}/decision',headers=h,json={'expected_version':2,'action':'retract','reason':'Withdraw this timeline pending further primary source checks.'}).status_code==200
 reveal(database,'outsider',sources[0][0]);h=actor('outsider')
 assert client.post('/api/current-affairs/view',headers=h,json={'canonical_id':sources[0][0]}).json()['items']==[]

def test_all_new_paths_withheld_during_unrelated_mock(client,actor,sources,database):
 body,h=proposal(client,actor,sources);c=database[1];mid=uuid4().hex
 c.execute("INSERT INTO mock_sessions(id,user_id,collection_id,question_ids,duration_seconds) VALUES(%s,'reviewer1','ldc',ARRAY['unrelated-question'],600)",(mid,))
 try:
  assert client.get('/api/current-affairs/manage').status_code==409
  assert client.post('/api/current-affairs/proposals',headers=h,json=body).status_code==409
  assert client.post('/api/current-affairs/view',headers=h,json={'canonical_id':sources[0][0]}).status_code==409
 finally:c.execute('DELETE FROM mock_sessions WHERE id=%s',(mid,))

def test_finished_cup_still_withholds_context(client,actor,sources,database):
 import hashlib
 c=database[1];cup='ca_cup_'+uuid4().hex;room='ca_room_'+uuid4().hex;user='ca_cup_user_'+uuid4().hex
 c.execute("INSERT INTO users(id,handle,email,role) VALUES(%s,%s,%s,'learner')",(user,user,user+'@example.test'))
 c.execute("INSERT INTO auth_sessions(token_hash,user_id,expires_at) VALUES(%s,%s,now()+interval '1 day')",(hashlib.sha256(('test-session-'+user).encode()).hexdigest(),user))
 c.execute("INSERT INTO game_cups(id,opens_at,closes_at,questions) VALUES(%s,now()-interval '1 hour',now()+interval '1 hour','[]')",(cup,))
 c.execute("INSERT INTO game_rooms(id,owner_id,mode,state,capacity,cup_id,questions,round_seconds,request_key,request_hash) VALUES(%s,%s,'cup','finished',1,%s,'[]',30,%s,'test')",(room,user,cup,uuid4().hex))
 c.execute("INSERT INTO game_members(room_id,user_id,released_at) VALUES(%s,%s,now())",(room,user))
 h=actor(user)
 assert client.get('/api/current-affairs/manage').status_code==409
 assert client.post('/api/current-affairs/view',headers=h,json={'canonical_id':sources[0][0]}).status_code==409

def test_revoked_author_scope_blocks_publication(client,actor,sources,database):
 body,h=proposal(client,actor,sources);rid=client.post('/api/current-affairs/proposals',headers=h,json=body).json()['id'];c=database[1]
 c.execute("UPDATE review_grants SET revoked_at=now() WHERE user_id='reviewer1' AND revoked_at IS NULL")
 try:
  h=actor('owner');assert client.post(f'/api/current-affairs/revisions/{rid}/decision',headers=h,json={'expected_version':0,'action':'publish','reason':'Former author access must be checked again before publication.'}).status_code==403
 finally:c.execute("UPDATE review_grants SET revoked_at=NULL WHERE user_id='reviewer1'")

def test_exact_assigned_editor_can_propose_without_global_grants(client,actor,sources,database):
 c=database[1];aid='ca_assignment_'+uuid4().hex
 c.execute("INSERT INTO editorial_assignments(id,email,collection_id,user_id,state,created_by,reason) VALUES(%s,'outsider@example.test','udc','outsider','active','owner','Synthetic exact-source timeline author permission')",(aid,))
 c.execute('INSERT INTO editorial_assignment_papers(assignment_id,paper_id) VALUES(%s,%s)',(aid,sources[0][2]))
 try:
  body,h=proposal(client,actor,sources[:1],user='outsider')
  r=client.post('/api/current-affairs/proposals',headers=h,json=body);assert r.status_code==201,r.text
  assert client.post('/api/current-affairs/proposals',headers=h,json={**body,'request_key':uuid4().hex,'links':[{**body['links'][0],'canonical_id':sources[1][0],'appearance_id':sources[1][1]}]}).status_code==403
 finally:c.execute("UPDATE editorial_assignments SET state='revoked',version=version+1 WHERE id=%s",(aid,))

def test_source_search_is_answer_free_and_permission_scoped(client,actor,sources,database):
 marker='unique search '+uuid4().hex
 database[1].execute('UPDATE appearances SET question=%s WHERE id=%s',(marker,sources[0][1]))
 actor('reviewer1');r=client.get('/api/current-affairs/sources',params={'q':marker});assert r.status_code==200,r.text
 assert sources[0][1] in {x['appearance_id'] for x in r.json()['items']}
 assert 'answer' not in r.text and 'source_version' not in r.text
 actor('outsider');assert client.get('/api/current-affairs/sources',params={'q':'synthetic office'}).json()['items']==[]

def test_published_connections_survive_identical_sync_but_not_real_change(client,actor,sources,database):
 body,h=proposal(client,actor,sources);publish(client,actor,body,h)
 c=database[1]
 # Sync can rewrite identical values and bump row transaction IDs.
 c.execute('UPDATE appearances SET question=question WHERE id=%s',(sources[0][1],))
 c.execute('UPDATE canonical_questions SET updated_at=now() WHERE id=%s',(sources[0][0],))
 c.execute('UPDATE question_classifications SET subject_id=subject_id WHERE question_id=%s',(sources[0][0],))
 reveal(database,'outsider',sources[0][0]);h=actor('outsider')
 r=client.post('/api/current-affairs/view',headers=h,json={'canonical_id':sources[0][0]});assert r.status_code==200 and len(r.json()['items'])==1,r.text
 c.execute("UPDATE canonical_questions SET answer_text='Earlier name' WHERE id=%s",(sources[0][0],))
 assert client.post('/api/current-affairs/view',headers=h,json={'canonical_id':sources[0][0]}).json()['items']==[]


def measured_proposal(client,actor,sources,kind='trade-ranking'):
 body,h=proposal(client,actor,sources)
 body['name']='Synthetic iron ore export-volume series '+uuid4().hex
 body['predicate']='largest exporter'
 body['jurisdiction']='Worldwide'
 body['comparison']={'kind':kind,'subject':'Iron ore, synthetic commodity definition','metric':'Largest exporter by annual exported quantity','basis':'volume','unit':'metric tonnes','population':'Countries worldwide','source_series':'Synthetic trade statistics series','methodology':'Same commodity code; export tonnage, not value or production; calendar-year basis.'}
 f=body['facts'][0]
 f.update(value='Synthetic Country A led the 2023 export-volume ranking.',period_label='Calendar year 2023',period_kind='calendar-year',period_start='2023-01-01',period_end='2023-12-31')
 body['facts'].append({**f,'value':'Synthetic Country B led the 2024 export-volume ranking.','period_label':'Calendar year 2024','period_start':'2024-01-01','period_end':'2024-12-31'})
 for l in body['links']:l.update(period_label='Calendar year 2023',comparison_status='comparable',comparison_note='Original question means the same iron ore export tonnage and worldwide country population.')
 return body,h


def test_trade_reporting_years_coexist_without_expiry_and_show_measure(client,actor,sources,database):
 body,h=measured_proposal(client,actor,sources)
 # Both annual reports may be checked/published at the same time. Their
 # reporting periods, not invented officeholder expiry dates, distinguish them.
 body['facts'][1]['effective_on']=body['facts'][0]['effective_on']
 publish(client,actor,body,h)
 reveal(database,'outsider',sources[0][0]);h=actor('outsider')
 r=client.post('/api/current-affairs/view',headers=h,json={'canonical_id':sources[0][0]});assert r.status_code==200,r.text
 item=r.json()['items'][0]
 assert item['comparison']['basis']=='volume' and item['comparison']['unit']=='metric tonnes'
 assert [f['period_label'] for f in item['facts']]==['Calendar year 2024','Calendar year 2023']
 assert item['questions'][0]['comparison_status']=='comparable'


@pytest.mark.parametrize('field',['subject','metric','basis','unit','population','source_series','methodology'])
def test_measurement_definition_required_for_ranking(client,actor,sources,field):
 body,h=measured_proposal(client,actor,sources);body['comparison'][field]=None
 r=client.post('/api/current-affairs/proposals',headers=h,json=body);assert r.status_code==422,r.text


@pytest.mark.parametrize('change',['basis','commodity','methodology','population'])
def test_different_measure_cannot_replace_same_connection(client,actor,sources,change):
 body,h=measured_proposal(client,actor,sources);rid=publish(client,actor,body,h)
 h=actor('reviewer1');row=next(r for r in client.get('/api/current-affairs/manage').json()['items'] if r['id']==rid)
 body.update(entity_id=row['entity_id'],base_version=1,request_key=uuid4().hex)
 if change=='basis':body['comparison'].update(basis='value',unit='USD at current prices')
 if change=='commodity':body['comparison']['subject']='Iron and steel, a different commodity group'
 if change=='methodology':body['comparison']['methodology']='A different methodology now counts re-exports and changes coverage.'
 if change=='population':body['comparison']['population']='Only Indian states, not countries worldwide'
 r=client.post('/api/current-affairs/proposals',headers=h,json=body);assert r.status_code==422 and 'Comparison identity differs' in r.text,r.text


@pytest.mark.parametrize('change',['missing-period','duplicate-period','backwards-period','missing-link-note','comparable-without-period'])
def test_period_and_question_comparability_validation(client,actor,sources,change):
 body,h=measured_proposal(client,actor,sources)
 if change=='missing-period':body['facts'][0]['period_label']=None
 if change=='duplicate-period':body['facts'][1]['period_label']=body['facts'][0]['period_label']
 if change=='backwards-period':body['facts'][0]['period_end']='2022-01-01'
 if change=='missing-link-note':body['links'][0]['comparison_note']=None
 if change=='comparable-without-period':body['links'][0]['period_label']=None
 assert client.post('/api/current-affairs/proposals',headers=h,json=body).status_code==422


def test_unknown_question_measure_remains_related_only(client,actor,sources,database):
 body,h=measured_proposal(client,actor,sources)
 body['links'][0].update(comparison_status='related-only',period_label=None,comparison_note='The old stem says iron without a commodity code or value/volume basis; direct comparison is unsupported.')
 publish(client,actor,body,h);reveal(database,'outsider',sources[0][0]);h=actor('outsider')
 item=client.post('/api/current-affairs/view',headers=h,json={'canonical_id':sources[0][0]}).json()['items'][0]
 question=next(q for q in item['questions'] if q['canonical_id']==sources[0][0])
 assert question['comparison_status']=='related-only' and question['period_label'] is None


@pytest.mark.parametrize('kind',['officeholder','production-ranking','statistic','report-ranking','scheme','award','record','event'])
def test_other_current_affairs_categories_submit(client,actor,sources,kind):
 body,h=measured_proposal(client,actor,sources,kind)
 if kind in {'officeholder','scheme'}:
  body['facts']=body['facts'][:1]
 if kind=='award':
  for i,f in enumerate(body['facts']):f.update(period_kind='event-edition',edition=str(2023+i))
 r=client.post('/api/current-affairs/proposals',headers=h,json=body);assert r.status_code==201,r.text


def test_legacy_successful_request_replays_with_new_optional_defaults(client,actor,sources,database):
 body,h=proposal(client,actor,sources);c=database[1];entity='legacy_ca_'+uuid4().hex
 c.execute('INSERT INTO current_affairs_entities(id,name,jurisdiction,predicate,created_by) VALUES(%s,%s,%s,%s,%s)',(entity,body['name'],body['jurisdiction'],body['predicate'],'reviewer1'))
 rid=c.execute('INSERT INTO current_affairs_revisions(entity_id,author_id,request_key,base_version,payload) VALUES(%s,%s,%s,0,%s) RETURNING id',(entity,'reviewer1',body['request_key'],Jsonb(body))).fetchone()[0]
 r=client.post('/api/current-affairs/proposals',headers=h,json=body)
 assert r.status_code==201 and r.json()=={'id':rid,'replayed':True},r.text
