from uuid import uuid4
from psycopg.types.json import Jsonb
from test_content_studio import create,publish,document

def test_owner_only_work_dashboard_and_filters(client,actor,database):
    _,conn=database
    unique='Queue-'+uuid4().hex[:10]
    doc=document();doc['title']=unique+' material'
    mid,h,_=create(client,actor,doc)
    assert client.post('/api/studio/materials/'+mid+'/submit',headers=h,json={'expected_version':1}).status_code==200
    cid='queue-'+uuid4().hex
    conn.execute("INSERT INTO bank_contributions(id,author_id,subject_id,title,state,kind,idempotency_key,request_hash) VALUES(%s,'author','english',%s,'publication_failed','answer',%s,'test')",(cid,unique+' failed correction',cid))
    rid=conn.execute("INSERT INTO content_reports(canonical_id,kind,reporter_id,note) VALUES('cq_test','outdated',%s,'Synthetic outdated source report') RETURNING id",(unique,)).fetchone()[0]
    actor('outsider');assert client.get('/api/admin/bank/work').status_code==403
    actor('reviewer1');assert client.get('/api/admin/bank/work').status_code==403
    actor('owner');r=client.get('/api/admin/bank/work?q='+unique);assert r.status_code==200,r.text
    data=r.json();assert data['total']==2 and data['items'][0]['id']==cid and data['items'][0]['priority']==0
    assert r.headers['cache-control']=='private, no-store'
    assert client.get('/api/admin/bank/work?q='+unique+'&kind=material').json()['items'][0]['id']==mid
    assert client.get('/api/admin/bank/work?q='+unique+'&stage=failed&priority=urgent').json()['total']==1
    assert client.get('/api/admin/bank/work?q='+unique+'&offset=1000').json()['total']==2
    assert not client.get('/api/admin/bank/work?q='+unique+'&offset=1000').json()['items']
    report=client.get('/api/admin/bank/reports?report_id='+str(rid));assert len(report.json())==1 and report.json()[0]['id']==rid
    assert client.get('/api/admin/bank/work?kind=invalid').status_code==422
    assert client.get('/api/admin/bank/work?limit=51').status_code==422

def test_material_review_feedback_survives_long_draft_history(client,actor,database):
    _,conn=database;mid,h,_=create(client,actor)
    client.post('/api/studio/materials/'+mid+'/submit',headers=h,json={'expected_version':1})
    h=actor('owner');note='Add a dated source and explain the example before resubmitting.'
    r=client.post('/api/admin/bank/content/'+mid+'/review',headers=h,json={'expected_version':2,'decision':'changes_requested','reason':note});assert r.status_code==200,r.text
    for n in range(35):conn.execute("INSERT INTO material_events(material_id,actor_id,action,detail) VALUES(%s,'author','draft_saved',%s)",(mid,Jsonb({'revision':1,'synthetic':n})))
    actor('author');r=client.get('/api/studio/materials/'+mid);assert r.json()['feedback']['detail']['reason']==note
    assert r.json()['feedback']['detail']['revision']==1 and len(r.json()['events'])==30
    notices=client.get('/api/review/notifications').json();assert any(n.get('material_id')==mid for n in notices)
    unread=client.get('/api/review/notifications/unread');assert unread.status_code==200 and unread.headers['cache-control']=='private, no-store'
    n=next(n for n in notices if n.get('material_id')==mid);before=unread.json()['unread']
    client.post('/api/review/notifications/'+str(n['id'])+'/read',headers=actor('author'),json={})
    assert client.get('/api/review/notifications/unread').json()['unread']==before-1
    actor('outsider');assert client.get('/api/studio/materials/'+mid).status_code==404
    assert client.get('/api/studio/materials/'+mid+'/revisions/1').status_code==404

def test_revision_sources_exact_links_and_empty_page_total(client,actor,database):
    _,conn=database
    doc=document();doc['title']='Comparison-'+uuid4().hex
    mid=publish(client,actor,doc)
    h=actor('author');draft=client.get('/api/studio/materials/'+mid).json();revised=document();revised['title']=doc['title']+' revised';revised['blocks'][0]['text']='A reviewed replacement heading'
    r=client.post('/api/studio/materials/'+mid+'/save',headers=h,json={'expected_version':draft['lock_version'],'document':revised});assert r.status_code==200,r.text
    v=r.json()['lock_version'];client.post('/api/studio/materials/'+mid+'/submit',headers=h,json={'expected_version':v})
    actor('owner');detail=client.get('/api/studio/materials/'+mid).json();assert detail['published_revision']==1 and detail['revision']==2
    assert client.get('/api/studio/materials/'+mid+'/revisions/1').json()['title']==doc['title']
    assert client.get('/api/studio/materials/'+mid+'/revisions/2').json()['title']==revised['title']
    assert client.get('/api/admin/bank/content?q='+doc['title']+'&offset=1000').json()['total']==1
    r=client.get('/api/admin/bank/work?kind=material&q='+doc['title']);assert r.status_code==200,r.text
    assert 'material='+mid in r.json()['items'][0]['url']
    actor('outsider');report=client.post('/api/materials/'+mid+'/report',headers=actor('outsider'),json={'reason':'copyright','note':'Synthetic copyright report for dashboard verification.'});assert report.status_code==200
    rid=conn.execute('SELECT id FROM material_reports WHERE material_id=%s',(mid,)).fetchone()[0]
    actor('owner');reports=client.get('/api/admin/bank/content?material_report='+str(rid)).json()['reports'];assert len(reports)==1
    assert client.get('/api/materials/'+mid).json()['document']['title']==doc['title']

def test_creator_report_dashboard_target_scope(client,actor,database):
    _,conn=database
    h=actor('outsider');r=client.post('/api/creators/author/report',headers=h,json={'reason':'harassment','note':'Synthetic creator safety report for owner review.'});assert r.status_code==200
    rid=conn.execute("SELECT id FROM creator_reports WHERE reporter_id='outsider' AND creator_id='author'").fetchone()[0]
    actor('owner');queue=client.get('/api/admin/bank/work?kind=creator-report');assert queue.status_code==200,queue.text
    assert any('creator_report='+str(rid) in row['url'] and row['priority']==1 for row in queue.json()['items'])
    exact=client.get('/api/admin/bank/creator-reports?report_id='+str(rid)).json();assert len(exact['items'])==1
