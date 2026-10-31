from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor
import copy
import pytest
from psycopg.types.json import Jsonb
from pydantic import ValidationError
from app.services.content_studio import Document

def document(access='free'):
    return {'title':'A useful synthetic study guide','summary':'A clearly labelled synthetic guide for content workflow testing.','preview':'This public excerpt describes the guide without exposing the protected lesson body.','kind':'guide','access':access,'price_paise':4900 if access=='paid-preview' else 0,'tags':['Test'],'blocks':[{'id':'intro','type':'heading','text':'PRIVATE_BODY_MARKER'},{'id':'body','type':'paragraph','text':'<script>alert("literal text only")</script> A synthetic lesson.'}],'collection_id':None,'subject_id':None}

def create(client,actor,doc=None,user='author'):
    h=actor(user);key=uuid4().hex
    r=client.post('/api/studio/materials',headers={**h,'Idempotency-Key':key},json=doc or document());assert r.status_code==201,r.text
    return r.json()['id'],h,key

def publish(client,actor,doc=None,user='author'):
    mid,h,key=create(client,actor,doc,user)
    r=client.post('/api/studio/materials/'+mid+'/submit',headers=h,json={'expected_version':1});assert r.status_code==200,r.text
    h=actor('owner');r=client.post('/api/admin/bank/content/'+mid+'/review',headers=h,json={'expected_version':2,'decision':'publish','reason':'Synthetic exact revision CMS approval'});assert r.status_code==200,r.text
    return mid

def test_typed_blocks_incomplete_draft_and_publish_validation(client,actor):
    mid,h,key=create(client,actor,{'title':'','blocks':[]})
    assert client.post('/api/studio/materials/'+mid+'/submit',headers=h,json={'expected_version':1}).status_code==422
    invalid=document();invalid['blocks'][0]['type']='raw-html'
    assert client.post('/api/studio/materials',headers={**h,'Idempotency-Key':uuid4().hex},json=invalid).status_code==422
    for url in ['javascript:alert(1)','data:text/html,hello','http://unsafe.test','https://user:pass@example.test/path']:
        invalid=document();invalid['blocks']=[{'id':'a','type':'link','url':url}]
        with pytest.raises(ValidationError):Document.model_validate(invalid)
    invalid=document();invalid['blocks']*=2
    with pytest.raises(ValidationError):Document.model_validate(invalid)
    # A draft may be incomplete, but URLs and block contracts stay constrained.
    assert client.post('/api/studio/materials',json=document(),headers={'Idempotency-Key':uuid4().hex}).status_code==403

def test_create_retry_ownership_and_optimistic_save(client,actor):
    mid,h,key=create(client,actor)
    response=client.post('/api/studio/materials',headers={**h,'Idempotency-Key':key},json=document());assert response.json()['id']==mid
    other=document();other['title']='Changed payload under same retry key'
    assert client.post('/api/studio/materials',headers={**h,'Idempotency-Key':key},json=other).status_code==409
    actor('outsider');assert client.get('/api/studio/materials/'+mid).status_code==404
    assert client.get('/api/studio/materials/'+mid+'/revisions/1').status_code==404
    assert client.get('/api/materials/'+mid).status_code==404
    h=actor('author')
    def save(_):return client.post('/api/studio/materials/'+mid+'/save',headers=h,json={'expected_version':1,'document':other})
    with ThreadPoolExecutor(max_workers=2) as pool:r=list(pool.map(save,range(2)))
    assert sorted(x.status_code for x in r)==[200,409]
    draft=client.get('/api/studio/materials/'+mid).json();assert draft['revision']==2
    assert client.get('/api/studio/materials/'+mid+'/revisions/1').json()['title']==document()['title']

def test_revision_publishing_draft_isolation_reports_archive_restore(client,actor):
    mid=publish(client,actor)
    h=actor('author');draft=client.get('/api/studio/materials/'+mid).json();version=draft['lock_version']
    revised=document();revised['title']='UNAPPROVED_TITLE';revised['blocks'][0]['text']='UNAPPROVED_BODY'
    assert client.post('/api/studio/materials/'+mid+'/save',headers=h,json={'expected_version':version,'document':revised}).status_code==200
    actor('outsider');public=client.get('/api/materials/'+mid).json()
    assert public['document']['title']==document()['title'] and 'UNAPPROVED_BODY' not in str(public)
    h=actor('author');assert client.post('/api/studio/materials/'+mid+'/submit',headers=h,json={'expected_version':version+1}).status_code==200
    h=actor('reviewer1');assert client.get('/api/admin/bank/content').status_code==403
    assert client.post('/api/admin/bank/content/'+mid+'/review',headers=h,json={'expected_version':version+2,'decision':'publish'}).status_code==403
    h=actor('owner');assert client.post('/api/admin/bank/content/'+mid+'/review',headers=h,json={'expected_version':version+1,'decision':'publish'}).status_code==409
    assert client.post('/api/admin/bank/content/'+mid+'/review',headers=h,json={'expected_version':version+2,'decision':'publish'}).status_code==200
    h=actor('outsider');report=client.post('/api/materials/'+mid+'/report',headers=h,json={'reason':'incorrect','note':'Synthetic source mismatch needs review.'});assert report.status_code==200
    h=actor('owner');assert client.post('/api/admin/bank/content/'+mid+'/review',headers=h,json={'expected_version':version+3,'decision':'archive','reason':'Synthetic report investigation'}).status_code==200
    assert client.get('/api/materials/'+mid).status_code==404
    assert client.post('/api/admin/bank/content/'+mid+'/review',headers=h,json={'expected_version':version+4,'decision':'restore','reason':'Synthetic restoration after investigation'}).status_code==200
    assert client.get('/api/materials/'+mid).json()['document']['title']=='UNAPPROVED_TITLE'
    assert client.post('/api/admin/bank/content/reports/'+str(report.json()['id'])+'/resolve',headers=h,json={'reason':'Synthetic issue investigated and corrected.'}).status_code==200

def test_paid_body_redaction_catalog_and_pro_entitlement(client,actor,database):
    mid=publish(client,actor,document('paid-preview'))
    actor('outsider');r=client.get('/api/materials/'+mid);assert r.status_code==200
    assert r.headers['cache-control']=='private, no-store'
    body=r.json();assert body['can_read'] is False and body['document']['blocks']==[] and body['payments_enabled'] is False
    assert 'PRIVATE_BODY_MARKER' not in r.text
    catalog=client.get('/api/materials').json();assert 'PRIVATE_BODY_MARKER' not in str(catalog) and all('blocks' not in m['payload'] for m in catalog['items'])
    h=actor('outsider');assert client.post('/api/materials/'+mid+'/reaction',headers=h,json={'helpful':True}).status_code==403
    assert client.post('/api/materials/'+mid+'/reaction',headers=h,json={'saved':True}).status_code==200
    actor('author');assert client.get('/api/materials/'+mid).json()['can_read'] is True
    pro=publish(client,actor,document('pro'));actor('outsider')
    database[1].execute("UPDATE users SET plan_code='free',plan_status='free',plan_ends_at=NULL WHERE id='outsider'")
    assert client.get('/api/materials/'+pro).json()['can_read'] is False
    database[1].execute("INSERT INTO reward_redemptions(id,user_id,idempotency_key,catalog_id,catalog_version,points,starts_at,ends_at) VALUES(%s,'outsider',%s,'pro-week',1,1000,now(),now()+interval '1 day')",(uuid4().hex,uuid4().hex))
    assert client.get('/api/materials/'+pro).json()['can_read'] is True

def test_votes_are_unique_not_rewards_and_not_self_votes(client,actor,database):
    mid=publish(client,actor)
    h=actor('author');assert client.post('/api/materials/'+mid+'/reaction',headers=h,json={'helpful':True}).status_code==403
    h=actor('outsider');conn=database[1]
    before=conn.execute("SELECT COALESCE(sum(points),0) FROM reward_ledger WHERE user_id='outsider'").fetchone()[0]
    def vote(_):return client.post('/api/materials/'+mid+'/reaction',headers=h,json={'helpful':True,'studied':True})
    with ThreadPoolExecutor(max_workers=2) as pool:r=list(pool.map(vote,range(2)))
    assert all(v.status_code==200 for v in r)
    assert client.get('/api/materials/'+mid).json()['helpful']==1
    assert client.get('/api/materials/'+mid).json()['studied']==1
    assert conn.execute("SELECT COALESCE(sum(points),0) FROM reward_ledger WHERE user_id='outsider'").fetchone()[0]==before
    assert client.post('/api/materials/'+mid+'/reaction',headers=h,json={'helpful':False}).status_code==200
    assert client.get('/api/materials/'+mid).json()['helpful']==0
    assert client.get('/api/materials/'+mid).json()['studied']==1

def test_bank_question_reference_and_history_are_guarded(client,actor,database):
    doc=document();doc['blocks']=[{'id':'bank','type':'question','question_id':'cq_test'}]
    mid,h,key=create(client,actor,doc)
    assert client.post('/api/studio/materials/'+mid+'/submit',headers=h,json={'expected_version':1}).status_code==200
    bad=copy.deepcopy(doc);bad['blocks'][0]['question_id']='missing-bank-id'
    assert client.post('/api/studio/materials/'+mid+'/save',headers=h,json={'expected_version':2,'document':bad}).status_code==422
    with pytest.raises(Exception,match='append-only'):database[1].execute('DELETE FROM material_revisions WHERE material_id=%s',(mid,))


def test_publication_reward_independent_daily_cap_reversal_and_notices(client,actor,database):
    import hashlib
    conn=database[1];user='cms-author-'+uuid4().hex
    conn.execute('INSERT INTO users(id,handle,email) VALUES(%s,%s,%s)',(user,user,user+'@example.test'))
    conn.execute("INSERT INTO auth_sessions(token_hash,user_id,expires_at) VALUES(%s,%s,now()+interval '1 day')",(hashlib.sha256(('test-session-'+user).encode()).hexdigest(),user))
    mid=publish(client,actor,user=user)
    assert conn.execute('SELECT sum(points),sum(xp) FROM reward_ledger WHERE user_id=%s',(user,)).fetchone()==(5,20)
    actor(user);notices=client.get('/api/review/notifications').json()
    assert any(n['material_id']==mid for n in notices)
    h=actor('owner')
    assert client.post('/api/admin/bank/content/'+mid+'/review',headers=h,json={'expected_version':3,'decision':'archive','reason':'Synthetic content removed after review'}).status_code==200
    assert client.post('/api/admin/bank/content/'+mid+'/review',headers=h,json={'expected_version':4,'decision':'restore','reason':'Synthetic restored without a new reward'}).status_code==200
    assert conn.execute('SELECT sum(points),sum(xp) FROM reward_ledger WHERE user_id=%s',(user,)).fetchone()==(0,0)
    publish(client,actor,user=user)
    assert conn.execute('SELECT count(*) FROM material_reward_claims WHERE user_id=%s',(user,)).fetchone()[0]==1
    own=publish(client,actor,user='owner')
    assert conn.execute('SELECT count(*) FROM material_reward_claims WHERE material_id=%s',(own,)).fetchone()[0]==0


def test_owner_can_preview_locked_demo_and_app_role_permissions(client,actor,database):
    actor('owner')
    assert client.get('/api/materials/cms-paid-demo').json()['can_read'] is True
    response=client.get('/api/materials/cms-paid-demo?preview=true')
    assert response.json()['can_read'] is False and response.json()['document']['blocks']==[]
    mid,h,key=create(client,actor)
    conn=database[1]
    with conn.transaction():
        conn.execute('SET LOCAL ROLE mpsc')
        conn.execute("INSERT INTO material_events(material_id,actor_id,action) VALUES(%s,'author','Synthetic app role write')",(mid,))
        conn.execute("INSERT INTO material_votes(material_id,user_id,helpful) VALUES(%s,'outsider',true)",(mid,))
        assert conn.execute('SELECT payload FROM material_revisions WHERE material_id=%s',(mid,)).fetchone()
