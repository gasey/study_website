"""Review-circle membership, consent and per-viewer answer-reveal boundaries."""
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
import pytest
from psycopg.types.json import Jsonb
from test_study_desks import desk_setup, room, join


def add(client,actor,did,kind='question'):
    h=actor('author')
    response=client.post(f'/api/desk/rooms/{did}/items',headers={**h,'Idempotency-Key':uuid4().hex},
                        json={'kind':kind,'question_id':'cq_test','body':'Synthetic discussion context'})
    assert response.status_code==201,response.text
    return response.json()['id']


def url(did,iid):return f'/api/desk/rooms/{did}/items/{iid}/discussion'
def listed(client,did,filter='all'):
    response=client.get(f'/api/desk/rooms/{did}/items?discussion={filter}')
    assert response.status_code==200,response.text
    assert response.headers['cache-control']=='private, no-store'
    return response.json()['items']


def test_lifecycle_concurrent_version_replay_and_no_economy(client,actor,database):
    conn=database[1];did=room(client,actor);join(client,actor,did)
    iid=add(client,actor,did);h=actor('outsider')
    before={t:conn.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in ('attempts','reward_ledger','reward_question_claims','calendar_entries')}
    assert listed(client,did)[0]['discussion_state']=='none'
    assert not listed(client,did,'needed')
    assert client.post(url(did,iid),headers=h,json={'expected_version':1,'state':'resolved'}).status_code==409
    data={'expected_version':1,'state':'needed'}
    assert client.post(url(did,iid),json=data).status_code==403
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses=list(pool.map(lambda _:client.post(url(did,iid),headers=h,json=data),range(2)))
    assert sorted(r.status_code for r in responses)==[200,409]
    row=listed(client,did,'needed')[0]
    assert row['id']==iid and row['version']==2
    assert client.post(url(did,iid),headers=h,json=data).status_code==409
    assert client.post(url(did,iid),headers=h,json={'expected_version':2,'state':'needed'}).json()['version']==2
    assert client.post(url(did,iid),headers=h,json={'expected_version':2,'state':'resolved'}).json()['version']==3
    assert not listed(client,did,'needed')
    assert listed(client,did,'resolved')[0]['discussion_state']=='resolved'
    assert client.post(url(did,iid),headers=h,json={'expected_version':3,'state':'needed'}).json()['version']==4
    assert conn.execute("SELECT count(*) FROM study_desk_events WHERE desk_id=%s AND action LIKE 'discussion_%%'",(did,)).fetchone()[0]==3
    assert {t:conn.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in before}==before


@pytest.mark.parametrize('reverse',[False,True])
def test_blocks_consent_departure_deletion_and_nonmembers(client,actor,database,reverse):
    conn=database[1];did=room(client,actor);join(client,actor,did)
    h=actor('author');assert client.post(f'/api/desk/rooms/{did}/sharing',headers=h,json={'mistakes':True}).status_code==200
    iid=add(client,actor,did,'mistake');h=actor('outsider');data={'expected_version':1,'state':'needed'}
    assert client.post(url(did,iid),headers=h,json=data).status_code==200
    a,b=('outsider','author') if reverse else ('author','outsider')
    conn.execute('INSERT INTO creator_blocks(user_id,blocked_id) VALUES(%s,%s)',(a,b))
    assert not listed(client,did,'needed')
    assert client.post(url(did,iid),headers=h,json={'expected_version':2,'state':'resolved'}).status_code==404
    conn.execute('DELETE FROM creator_blocks WHERE user_id=%s AND blocked_id=%s',(a,b))
    conn.execute("UPDATE study_desk_members SET sharing='{}' WHERE desk_id=%s AND user_id='author'",(did,))
    assert not listed(client,did,'needed')
    assert client.post(url(did,iid),headers=h,json={'expected_version':2,'state':'resolved'}).status_code==404
    conn.execute("UPDATE study_desk_members SET sharing='{"+'"mistakes":true'+"}' WHERE desk_id=%s AND user_id='author'",(did,))
    assert listed(client,did,'needed')
    conn.execute("UPDATE study_desk_members SET left_at=now() WHERE desk_id=%s AND user_id='author'",(did,))
    assert not listed(client,did,'needed')
    actor('reviewer1');assert client.get(f'/api/desk/rooms/{did}/items?discussion=needed').status_code==404
    assert client.post(url(did,iid),headers=actor('reviewer1'),json=data).status_code==404
    actor('outsider');conn.execute('UPDATE study_desk_items SET deleted_at=now() WHERE id=%s',(iid,))
    assert client.post(url(did,iid),headers=actor('outsider'),json=data).status_code==404


@pytest.mark.parametrize('assessment',['mock','game'])
def test_assessment_reveal_gate_is_per_member_for_filter_and_update(client,actor,database,assessment):
    conn=database[1];did=room(client,actor);join(client,actor,did);iid=add(client,actor,did)
    h=actor('author');assert client.post(url(did,iid),headers=h,json={'expected_version':1,'state':'needed'}).status_code==200
    testid='circle_'+uuid4().hex
    if assessment=='mock':
        conn.execute("INSERT INTO mock_sessions(id,user_id,collection_id,question_ids,duration_seconds) VALUES(%s,'outsider','udc',%s,600)",(testid,['cq_test']))
    else:
        conn.execute("INSERT INTO game_rooms(id,owner_id,mode,capacity,round_seconds,questions,request_key,request_hash) VALUES(%s,'outsider','party',4,30,%s,%s,'synthetic')",(testid,Jsonb([{'id':'cq_test'}]),uuid4().hex))
        conn.execute("INSERT INTO game_members(room_id,user_id) VALUES(%s,'outsider')",(testid,))
    h=actor('outsider')
    assert not listed(client,did,'needed')
    assert client.post(url(did,iid),headers=h,json={'expected_version':2,'state':'resolved'}).status_code==409
    actor('author');assert listed(client,did,'needed')[0]['id']==iid
    if assessment=='mock':
        conn.execute('UPDATE mock_sessions SET submitted_at=now(),elapsed_seconds=0,score=0,n_correct=0,n_wrong=0,n_skipped=1 WHERE id=%s',(testid,))
    else:
        conn.execute("UPDATE game_rooms SET state='finished' WHERE id=%s",(testid,))
        conn.execute('UPDATE game_members SET released_at=now() WHERE room_id=%s',(testid,))
    h=actor('outsider');assert listed(client,did,'needed')
    assert client.post(url(did,iid),headers=h,json={'expected_version':2,'state':'resolved'}).status_code==200


def test_flag_validation_content_version_and_feature_gate(client,actor,database,monkeypatch):
    from app.config import settings
    did=room(client,actor);iid=add(client,actor,did);h=actor('author')
    data={'expected_version':1,'state':'needed'}
    for change in ({'state':'anything'},{'expected_version':0},{'question_id':'cq_test'}):
        assert client.post(url(did,iid),headers=h,json=data|change).status_code==422
    # A content edit and a circle update share the same version lock.
    assert client.post(f'/api/desk/rooms/{did}/items/{iid}',headers=h,json={'expected_version':1,'title':'','body':'New synthetic context'}).status_code==200
    assert client.post(url(did,iid),headers=h,json=data).status_code==409
    note=add(client,actor,did,'note')
    assert client.post(url(did,note),headers=h,json=data).status_code==404
    assert client.get(f'/api/desk/rooms/{did}/items?discussion=unknown').status_code==422
    monkeypatch.setattr(settings,'study_desks_private_enabled',False)
    assert client.post(url(did,iid),headers=h,json=data).status_code==409
