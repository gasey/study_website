"""Source-bound manual Atlas curation; ordinary question browse/scoring stays authoritative."""
from contextlib import asynccontextmanager
from uuid import uuid4
from pathlib import Path
import subprocess
import pytest
from psycopg.types.json import Jsonb


@pytest.fixture(autouse=True)
def case(database,client,monkeypatch):
    from app.db import cursor
    from app.routers import atlas,questions
    @asynccontextmanager
    async def role_cursor():
        async with cursor() as cur:
            await cur.execute('SET LOCAL ROLE mpsc');yield cur
    monkeypatch.setattr(atlas,'cursor',role_cursor);monkeypatch.setattr(questions,'cursor',role_cursor)
    conn=database[1];topic='english/atlas-'+uuid4().hex
    conn.execute('UPDATE atlas_topic_bindings SET live=NULL')
    conn.execute("INSERT INTO review_taxonomy(id,label,parent_id,level,version) VALUES(%s,'Synthetic Atlas test topic','english','topic','atlas-test')",(topic,))
    conn.execute("UPDATE question_classifications SET topic_id=%s,topic_label='Synthetic Atlas topic',review_status='approved' WHERE question_id='cq_test'",(topic,))
    return conn,topic


def binding(topic,**patch):return {'chapter_id':'rivers-of-india','layer_id':None,'event_id':None,'subject_id':'english','topic_id':topic,**patch}
def save(client,actor,payload,bid=None,version=0):
    bid=bid or str(uuid4());r=client.post('/api/admin/atlas/bindings/'+bid,headers=actor('owner'),json={'expected_version':version,'binding':payload,'reason':'Synthetic fixture curation only'});return bid,r

def decide(client,actor,bid,version,action='publish',**kw):return client.post('/api/admin/atlas/bindings/'+bid+'/decision',headers=actor('owner'),json={'expected_version':version,'action':action,'reason':'Synthetic owner test decision',**kw})
def questions(client,**patch):return client.get('/api/questions',params={'atlas_chapter':'rivers-of-india',**patch})
def reverse(client):return client.get('/api/atlas/questions/cq_test/links')


def test_draft_publish_bidirectional_question_contract_hold_and_rollback(client,actor,case):
    conn,topic=case;before=conn.execute('SELECT count(*) FROM reward_ledger').fetchone()[0]
    bid,r=save(client,actor,binding(topic));assert r.status_code==200,r.text
    assert questions(client).json()['total']==0 and reverse(client).json()['items']==[]
    assert decide(client,actor,bid,1).status_code==200
    duplicate,r=save(client,actor,binding(topic));assert r.status_code==200
    assert decide(client,actor,duplicate,1).status_code==409
    result=questions(client);assert result.status_code==200,result.text
    assert result.json()['total']==1
    q=result.json()['items'][0];assert q['id']=='cq_test' and q['source_appearance']['paper_id']=='paper-test' and q['answer_status']=='needs-review'
    assert not {'answer_text','answer_index','explanation'} & q.keys()
    assert q['atlas_links'][0]['chapter_id']=='rivers-of-india' and reverse(client).json()['items'][0]['chapter_id']=='rivers-of-india'
    assert decide(client,actor,bid,1,'hold').status_code==409
    assert decide(client,actor,bid,2,'hold').status_code==200
    assert questions(client).json()['total']==0 and reverse(client).json()['items']==[]
    assert decide(client,actor,bid,3,'rollback',revision=1).status_code==422
    assert decide(client,actor,bid,3,'rollback',revision=2).status_code==200
    assert questions(client).json()['total']==1
    rows=conn.execute('SELECT revision,action,actor_id FROM atlas_binding_versions WHERE binding_id=%s ORDER BY revision',(bid,)).fetchall()
    assert rows==[(1,'save','owner'),(2,'publish','owner'),(3,'hold','owner'),(4,'rollback','owner')]
    assert conn.execute('SELECT count(*) FROM reward_ledger').fetchone()[0]==before


def test_layer_validation_draft_edits_keep_live_and_registry_drift_hides_both(client,actor,case):
    from app.services.atlas_bindings import CHAPTERS
    conn,topic=case;layer=CHAPTERS['rivers-of-india']['layers'][0]['id']
    bid,r=save(client,actor,binding(topic,layer_id=layer));assert r.status_code==200,r.text
    assert decide(client,actor,bid,1).status_code==200
    assert questions(client,atlas_layer=layer).json()['total']==1
    other=CHAPTERS['rivers-of-india']['layers'][1]['id']
    assert questions(client,atlas_layer=other).json()['total']==0
    _,r=save(client,actor,binding(topic,chapter_id='mountains-and-passes'),bid,2);assert r.status_code==200
    assert questions(client).json()['total']==1
    assert decide(client,actor,bid,3).status_code==200
    assert questions(client).json()['total']==0
    assert questions(client,atlas_chapter='mountains-and-passes').json()['total']==1
    conn.execute("UPDATE review_taxonomy SET version='retired-review' WHERE id=%s",(topic,))
    assert questions(client,atlas_chapter='mountains-and-passes').json()['total']==0 and reverse(client).json()['items']==[]
    assert decide(client,actor,bid,4).status_code==409
    _,r=save(client,actor,binding(topic,chapter_id='mountains-and-passes'),bid,4);assert r.status_code==200
    assert decide(client,actor,bid,5).status_code==200
    conn.execute('UPDATE review_taxonomy SET active=false WHERE id=%s',(topic,))
    assert questions(client,atlas_chapter='mountains-and-passes').json()['total']==0


def test_active_assessment_pending_paths_source_scope_and_allowance(client,actor,case):
    conn,topic=case;bid,r=save(client,actor,binding(topic));assert decide(client,actor,bid,1).status_code==200
    h=actor('author');mid=uuid4().hex
    conn.execute("INSERT INTO mock_sessions(id,user_id,collection_id,question_ids,duration_seconds) VALUES(%s,'author','udc',%s,600)",(mid,['cq_test']))
    assert questions(client).json()['total']==0 and reverse(client).json()['items']==[]
    actor('outsider');assert questions(client).json()['total']==1
    conn.execute('UPDATE mock_sessions SET submitted_at=now(),elapsed_seconds=0,score=0,n_correct=0,n_wrong=0,n_skipped=1 WHERE id=%s',(mid,))
    actor('author');assert questions(client).json()['total']==1
    conn.execute("UPDATE question_classifications SET review_status='pending' WHERE question_id='cq_test'")
    assert questions(client).json()['total']==0 and reverse(client).json()['items']==[]
    conn.execute("UPDATE question_classifications SET review_status='approved' WHERE question_id='cq_test'")
    conn.execute("UPDATE papers SET exam_scope_id='outside-mizoram' WHERE id='paper-test'")
    assert questions(client).json()['total']==0 and reverse(client).json()['items']==[]
    assert client.get('/api/atlas/questions/cq_test/links?exam_scope=all').json()['items']
    client.cookies.clear();assert questions(client,exam_scope='all').status_code==401
    from app.services.browse_allowance import power_filter,query_key
    assert power_filter({'atlas_chapter':'rivers-of-india','year_from':2020})
    assert query_key({'atlas_chapter':'rivers-of-india'})!=query_key({'atlas_chapter':'mountains-and-passes'})
    conn.execute("UPDATE papers SET exam_scope_id='mizoram-recruitment' WHERE id='paper-test'")


def test_permissions_mfa_csrf_native_and_invalid_references(client,actor,case,monkeypatch):
    conn,topic=case
    for user in ('author','reviewer1','reviewer2'):
        assert client.get('/api/admin/atlas/bindings',headers=actor(user)).status_code==403
    owner=actor('owner')
    assert client.post('/api/admin/atlas/bindings/'+str(uuid4()),json={'expected_version':0,'binding':binding(topic),'reason':'Synthetic only'}).status_code==403
    for patch in ({'chapter_id':'missing'},{'layer_id':'missing'},{'event_id':'missing'},{'subject_id':'mizo'},{'topic_id':'missing'}):
        _,r=save(client,actor,binding(topic,**patch));assert r.status_code==422,r.text
    assert client.get('/api/questions?atlas_layer=missing').status_code==422
    options=client.get('/api/admin/atlas/topics?subject_id=english&q=Synthetic',headers=actor('owner'));assert topic in options.text
    r=client.post('/api/admin/atlas/binding-preview',headers=actor('owner'),json=binding(topic));assert r.status_code==200 and r.json()['count']==1
    from app.config import settings
    h=actor('owner');monkeypatch.setattr(settings,'mfa_enforce_staff',True)
    assert client.get('/api/admin/atlas/bindings').status_code==403
    assert client.post('/api/admin/atlas/binding-preview',headers=h,json=binding(topic)).status_code==403
    monkeypatch.setattr(settings,'staff_mfa_exempt_user_ids','some-other-owner')
    assert client.get('/api/admin/atlas/bindings').status_code==403
    monkeypatch.setattr(settings,'staff_mfa_exempt_user_ids','owner')
    assert client.get('/api/admin/atlas/bindings').status_code==200
    monkeypatch.setattr(settings,'staff_mfa_exempt_user_ids','')
    conn.execute("UPDATE auth_sessions SET mfa_verified_at=now() WHERE user_id='owner'")
    assert client.get('/api/admin/atlas/bindings').status_code==200
    monkeypatch.setattr(settings,'mfa_enforce_staff',False)
    from test_mobile_companion import connect
    mobile,_=connect(client,actor)
    for path in ('/api/admin/atlas/bindings','/api/atlas/chapters/rivers-of-india/bindings','/api/atlas/questions/cq_test/links','/api/questions?atlas_chapter=rivers-of-india'):
        assert client.get(path,headers=mobile).status_code==403,path


def test_catalog_matches_exact_26_chapters_and_history_is_immutable(client,actor,case):
    import psycopg
    conn,topic=case;root=Path(__file__).resolve().parents[2]
    subprocess.run(['node','scripts/export-atlas-catalog.cjs','--check'],cwd=root,check=True,capture_output=True)
    from app.services.atlas_bindings import CHAPTERS
    assert len(CHAPTERS)==26
    bid,r=save(client,actor,binding(topic));assert r.status_code==200
    with pytest.raises(psycopg.errors.RaiseException):conn.execute("UPDATE atlas_binding_versions SET reason='Changed history' WHERE binding_id=%s",(bid,))
    with pytest.raises(psycopg.errors.RaiseException):conn.execute('DELETE FROM atlas_binding_versions WHERE binding_id=%s',(bid,))
