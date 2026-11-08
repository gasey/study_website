from datetime import date
from app.routers.learning_catalog import next_date
from test_learning_workflows import official

def content(q):
 return dict(kind='day',title='Synthetic observance',description='Synthetic verified day for this isolated test only.',subject_id='english',question_ids=[q],sources=[dict(title='Synthetic source',url='https://example.test/day',checked_on='2026-01-01')],month=6,day=5)

def test_catalog_review_source_reuse_and_revision(client,actor,database):
 q,_,_=official(database)
 h=actor('author');r=client.post('/api/learning-catalog',headers=h,json={'content':content(q),'reason':'Prepare a synthetic reviewed collection.'});assert r.status_code==200,r.text
 item=r.json();eid=item['id']
 assert not any(x['id']==eid for x in client.get('/api/learning-catalog').json()['items'])
 def decision(who,version,action):
  return client.post('/api/learning-catalog/'+eid+'/decision',headers=actor(who),json={'expected_version':version,'action':action,'reason':'Inspected source and exact related question in this fixture.'})
 assert decision('author',1,'submit').status_code==200
 assert decision('author',2,'publish').status_code==403
 assert decision('reviewer1',2,'publish').status_code==200
 r=client.get('/api/learning-catalog');assert any(x['id']==eid and x['available']==1 for x in r.json()['items']),r.text
 r=client.get('/api/questions',params={'learning_entry':eid,'origin':'all','exam_scope':'all'});assert r.status_code==200,r.text
 assert [x['id'] for x in r.json()['items']]==[q]
 assert decision('reviewer1',2,'publish').status_code==409
 h=actor('author');p=content(q);p['title']='Unpublished replacement'
 r=client.post('/api/learning-catalog',headers=h,json={'id':eid,'expected_version':3,'content':p,'reason':'Revise the synthetic entry.'});assert r.status_code==200,r.text
 assert next(x for x in client.get('/api/learning-catalog').json()['items'] if x['id']==eid)['content']['title']=='Synthetic observance'
 assert decision('owner',4,'withdraw').status_code==200
 assert not any(x['id']==eid for x in client.get('/api/learning-catalog').json()['items'])
 assert client.get('/api/questions',params={'learning_entry':eid,'origin':'all','exam_scope':'all'}).json()['total']==0

def test_catalog_private_draft_validation_and_assessment(client,actor,database):
 q,_,_=official(database);h=actor('author');p=content(q);p['day']=31;p['month']=2
 assert client.post('/api/learning-catalog',headers=h,json={'content':p,'reason':'An invalid day must not save.'}).status_code==422
 p=content(q);p['question_ids']=['missing']
 assert client.post('/api/learning-catalog',headers=h,json={'content':p,'reason':'Missing references must fail.'}).status_code==422
 p=content(q);r=client.post('/api/learning-catalog',headers=h,json={'content':p,'reason':'Private draft ownership test.'});eid=r.json()['id']
 actor('outsider');assert not any(x['id']==eid for x in client.get('/api/learning-catalog/manage').json()['items'])
 h=actor('outsider');assert client.post('/api/learning-catalog',headers=h,json={'id':eid,'expected_version':1,'content':p,'reason':'Cannot edit another author.'}).status_code==403
 database[1].execute("INSERT INTO mock_sessions(id,user_id,collection_id,question_ids,duration_seconds) VALUES ('catalog-active','outsider','combined-prelims',%s,600)",([q],))
 try:
  assert client.get('/api/learning-catalog').status_code==409
  assert client.get('/api/questions',params={'learning_entry':eid}).status_code==409
 finally:database[1].execute("DELETE FROM mock_sessions WHERE id='catalog-active'")

def test_next_date_leap_year_rollover_and_variable():
 assert next_date({'month':2,'day':29},date(2026,11,3))==date(2028,2,29)
 assert next_date({'month':1,'day':1},date(2026,11,3))==date(2027,1,1)
 assert next_date({'occurrences':['2026-01-01']},date(2026,11,3)) is None
 assert next_date({'month':6,'day':5},date(2026,6,5))==date(2026,6,5)

def test_weekly_overview_actual_counts_and_private_cache(client,actor,database):
 actor('outsider');r=client.get('/api/learning-catalog/overview');assert r.status_code==200,r.text
 assert r.headers['cache-control']=='private, no-store'
 assert r.json()['activity']['answered']==database[1].execute("SELECT count(*) FROM attempts WHERE user_id='outsider' AND at>=now()-interval '7 days'").fetchone()[0]
