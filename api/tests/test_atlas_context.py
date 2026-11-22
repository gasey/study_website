"""Atlas exam order, source-bound dates, private district drafts and provenance."""
from copy import deepcopy
from uuid import uuid4
import pytest
from test_atlas_studio import doc,save,publish,decision

@pytest.fixture(autouse=True)
def real_role(monkeypatch):
    from contextlib import asynccontextmanager
    from app.db import cursor
    from app.routers import atlas
    @asynccontextmanager
    async def role_cursor():
        async with cursor() as cur:
            await cur.execute('SET LOCAL ROLE mpsc');yield cur
    monkeypatch.setattr(atlas,'cursor',role_cursor)


def test_all_district_proposals_valid_private_and_non_overwriting(client,actor,database):
    from app.services.atlas_context import district_proposals,DISTRICTS
    from app.services.atlas_studio import validate
    proposals=district_proposals()['chapters'];assert len(proposals)==11
    assert {d['district'] for d in proposals}==set(DISTRICTS)
    for d in proposals:
        assert validate(deepcopy(d))==d
        assert len(d['layers'])==4 and len(d['sources'])>=3 and not d['drills']
        assert d['layers'][0]['data']['features'][0]['geometry']['type'] in ('Polygon','MultiPolygon')
    url='/api/admin/atlas/district-proposals'
    assert client.get(url,headers=actor('author')).status_code==403
    assert len(client.get(url,headers=actor('owner')).json()['items'])==11
    d=proposals[0];drafturl=url+'/'+d['id']+'/draft'
    before=database[1].execute('SELECT count(*) FROM reward_ledger').fetchone()[0]
    r=client.post(drafturl,headers=actor('owner'),json={});assert r.status_code==200,r.text
    assert r.json()['status']=='draft' and r.json()['body']==d
    assert client.get('/api/atlas/chapters/'+d['id']).status_code==404
    assert client.post(drafturl,headers=actor('owner'),json={}).status_code==409
    assert database[1].execute('SELECT count(*) FROM reward_ledger').fetchone()[0]==before
    assert database[1].execute('SELECT count(*) FROM atlas_topic_bindings').fetchone()[0]==0

@pytest.mark.parametrize('change',[lambda d:d.update(district='Fake district'),lambda d:d.update(sources=[{'title':'Invalid'}]),lambda d:d.update(sources=[{'id':'x','title':'A source','url':'javascript:alert(1)','attribution':'Publisher','note':'Reference','reuse':'reference','checked_on':'2026-01-01'}]),lambda d:d['events'].append({'id':'event','label':'Event','date':'1757','description':'Synthetic','chronicle_entry_id':'date_'+'a'*20})])
def test_provenance_validation_rejects_incomplete_or_unsafe(client,actor,change):
    d=doc();change(d);assert save(client,actor,d).status_code==422


def setup_date(conn):
    conn.execute("UPDATE question_classifications SET subject_id='history',subject_label='History' WHERE question_id='cq_test'")
    conn.execute("UPDATE canonical_questions SET question='When was the Battle of Synthetic fought?',options='[\"1757\",\"1857\",\"1957\",\"2000\"]',answer_text='1757',answer_source='official' WHERE id='cq_test'")
    conn.execute("UPDATE appearances SET question='When was the Battle of Synthetic fought?',options='[\"1757\",\"1857\",\"1957\",\"2000\"]',answer_index=0,answer_source='official' WHERE canonical_id='cq_test'")


def linked_doc(client,actor,conn):
    setup_date(conn);r=client.get('/api/admin/atlas/chronicle-source/cq_test',headers=actor('owner'));assert r.status_code==200,r.text
    ref=r.json();d=doc();d['events']=[{'id':'dated','label':'Synthetic battle','date':'1757','description':'Synthetic source only','chronicle_entry_id':ref['entry']['id'],'chronicle_question_id':'cq_test','chronicle_source_sha256':ref['source_sha256']}]
    return d,ref


def test_dated_links_two_way_fresh_source_hold_and_no_rewards(client,actor,database):
    conn=database[1];d,ref=linked_doc(client,actor,conn);row=publish(client,actor,save(client,actor,d).json())
    forward='/api/atlas/chapters/'+d['id']+'/chronicle';reverse='/api/atlas/chronicle/'+ref['entry']['id']+'/links'
    r=client.get(forward);assert r.status_code==200,r.text
    assert r.json()['items'][0]['entry_id']==ref['entry']['id']
    assert client.get(reverse).json()['items'][0]['event_id']=='dated'
    assert r.headers['cache-control']=='private, no-store'
    conn.execute("UPDATE canonical_questions SET question=question||' Source edited.' WHERE id='cq_test'")
    assert not client.get(forward).json()['items'] and not client.get(reverse).json()['items']
    held=decision(client,actor,row,'hold');assert held.status_code==200
    assert client.get(forward).status_code==404
    assert not client.get(reverse).json()['items']
    assert decision(client,actor,held.json(),'rollback',revision=1).status_code==409


def test_stale_chronicle_publication_refused_and_assessment_guard(client,actor,database):
    conn=database[1];d,ref=linked_doc(client,actor,conn);row=save(client,actor,d).json()
    conn.execute("UPDATE canonical_questions SET status='held' WHERE id='cq_test'")
    from test_atlas_studio import preview
    p=preview(client,actor,row);assert p.status_code==200
    assert decision(client,actor,row,preview_hash=p.json()['body_hash']).status_code==409
    conn.execute("UPDATE canonical_questions SET status='live' WHERE id='cq_test'")
    row=publish(client,actor,row)
    conn.execute("INSERT INTO mock_sessions(id,user_id,collection_id,question_ids,duration_seconds) VALUES('atlas-context-mock','owner','udc',ARRAY['cq_test'],600)")
    assert client.get('/api/atlas/chapters/'+d['id']+'/chronicle').status_code==409
    assert client.get('/api/atlas/chronicle/'+ref['entry']['id']+'/links').status_code==409


def test_exam_order_uses_live_sections_bindings_and_retains_full_catalog(client,actor,database):
    from psycopg.types.json import Jsonb
    conn=database[1];catalog_before={x['id'] for x in client.get('/api/atlas/chapters').json()['items']};d=doc();row=publish(client,actor,save(client,actor,d).json());bid=str(uuid4())
    conn.execute("INSERT INTO review_taxonomy(id,label,parent_id,level,version) VALUES('english/atlas-context','Synthetic Atlas context','english','topic','synthetic')")
    binding={'chapter_id':d['id'],'subject_id':'english','topic_id':'english/atlas-context'}
    u='/api/admin/atlas/bindings/'+bid
    r=client.post(u,headers=actor('owner'),json={'expected_version':0,'binding':binding,'reason':'Synthetic fixture only'});assert r.status_code==200,r.text
    assert client.post(u+'/decision',headers=actor('owner'),json={'expected_version':1,'action':'publish','reason':'Synthetic fixture only'}).status_code==200
    conn.execute("INSERT INTO collections(id,title,kind,visibility,live_version) VALUES('atlas-context-exam','Synthetic exam','exam','public',1)")
    conn.execute("INSERT INTO collection_sections(collection_id,version,path,title,position,query) VALUES('atlas-context-exam',1,'synthetic','Synthetic topic',0,%s)",(Jsonb({'subject_id':'english','topic_id':'english/atlas-context'}),))
    conn.execute("INSERT INTO user_exam_bookmarks(user_id,collection_id,is_primary) VALUES('owner','atlas-context-exam',true)")
    h=actor('owner')|{'x-learning-user':'owner'};r=client.get('/api/atlas/me/index',headers=h);assert r.status_code==200,r.text
    assert r.json()['exam']['id']=='atlas-context-exam' and {x['id'] for x in r.json()['items']}==catalog_before|{d['id']}
    assert next(x for x in r.json()['items'] if x['id']==d['id'])['exam_relevant']
    conn.execute("UPDATE collections SET live_version=2 WHERE id='atlas-context-exam'")
    assert not any(x['exam_relevant'] for x in client.get('/api/atlas/me/index',headers=h).json()['items'])
    assert client.get('/api/atlas/me/index',headers=actor('owner')|{'x-learning-user':'u1'}).status_code==409
