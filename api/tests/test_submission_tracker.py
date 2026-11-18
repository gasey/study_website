"""Private submission reads: real SQL role, existing histories and disclosure guards."""
from contextlib import asynccontextmanager
from uuid import uuid4
from psycopg.types.json import Jsonb


def bank(conn,owner='author',state='draft',qid=None,subject='english'):
    uid='tracker-'+uuid4().hex
    conn.execute("INSERT INTO bank_contributions(id,author_id,kind,subject_id,title,state,idempotency_key,request_hash,canonical_id) VALUES(%s,%s,'explanation',%s,%s,%s,%s,'synthetic',%s)",(uid,owner,subject,'Synthetic bank '+uid,state,uid,qid))
    conn.execute("INSERT INTO contribution_revisions(contribution_id,revision,payload,baseline,baseline_hash,actor_id,created_at) VALUES(%s,1,'{}','{}','synthetic',%s,now()-interval '10 days')",(uid,owner))
    return uid

def material(conn,owner='author',state='draft'):
    uid='tracker-'+uuid4().hex
    conn.execute("INSERT INTO materials(id,author_id,title,workflow_state,blocks) VALUES(%s,%s,%s,%s,'[]')",(uid,owner,'Synthetic material '+uid,state))
    return uid

def collection(conn,owner='author',state='draft',questions=None):
    uid='tracker-'+uuid4().hex
    conn.execute("INSERT INTO learning_catalog(id,author_id,kind,state,payload) VALUES(%s,%s,'practice',%s,%s)",(uid,owner,state,Jsonb({'title':'Synthetic collection '+uid,'subject_id':'english','question_ids':questions or []})))
    return uid


def get(client,**params):
    response=client.get('/api/community/submissions',params={'limit':50,**params})
    assert response.status_code==200,response.text
    assert response.headers['cache-control']=='private, no-store'
    return response.json()


def test_tracker_is_owned_paginated_and_read_only_under_real_role(client,actor,database,monkeypatch):
    conn=database[1];own=[bank(conn),material(conn),collection(conn)];others=[bank(conn,'outsider'),material(conn,'outsider'),collection(conn,'outsider')]
    actor('author')
    from app.routers import community
    original=community.cursor
    @asynccontextmanager
    async def readonly():
        async with original() as cur:
            await cur.execute('SET TRANSACTION READ ONLY');await cur.execute('SET LOCAL ROLE mpsc');yield cur
    monkeypatch.setattr(community,'cursor',readonly)
    before=conn.execute('SELECT (SELECT count(*) FROM contribution_events),(SELECT count(*) FROM material_events),(SELECT count(*) FROM reward_ledger),(SELECT count(*) FROM creator_events)').fetchone()
    data=get(client,user='outsider');ids={x['id'] for x in data['items']};assert set(own)<=ids and not set(others)&ids
    assert all(x['sample_count']==0 and x['median_seconds'] is None for x in data['review_times'])
    assert not any(key in str(data['items']) for key in ('baseline_hash','reviewer_id','lease_user','author_id','request_hash','payload','question_ids'))
    page=get(client,limit=1);assert len(page['items'])==1 and page['has_more']
    next_page=get(client,limit=1,offset=1);assert page['items'][0]['id']!=next_page['items'][0]['id']
    assert get(client,offset=10000)['items']==[]
    after=conn.execute('SELECT (SELECT count(*) FROM contribution_events),(SELECT count(*) FROM material_events),(SELECT count(*) FROM reward_ledger),(SELECT count(*) FROM creator_events)').fetchone();assert before==after


def test_feedback_and_review_time_use_real_paired_history_and_honor_blocks(client,actor,database):
    conn=database[1];bid=bank(conn,state='changes_requested');mid=material(conn,state='changes_requested');cid=collection(conn,state='changes_requested')
    conn.execute("INSERT INTO contribution_events(contribution_id,actor_id,action,created_at) VALUES(%s,'author','submitted',now()-interval '6 days')",(bid,))
    conn.execute("INSERT INTO contribution_decisions(contribution_id,revision,reviewer_id,decision,rationale,created_at) VALUES(%s,1,'reviewer1','request_changes','Synthetic return: name the printed source.',now()-interval '4 days')",(bid,))
    conn.execute("INSERT INTO material_events(material_id,actor_id,action,detail,created_at) VALUES(%s,'author','submitted','{\"revision\":1}',now()-interval '6 days'),(%s,'reviewer1','changes_requested','{\"revision\":1,\"reason\":\"Synthetic return: explain the quotation.\"}',now()-interval '4 days')",(mid,mid))
    conn.execute("INSERT INTO learning_catalog_history(entry_id,version,actor_id,action,payload,reason,created_at) VALUES(%s,1,'author','submit','{}','',now()-interval '6 days'),(%s,2,'reviewer1','request_changes','{}','Synthetic return: inspect the linked pool.',now()-interval '4 days')",(cid,cid))
    actor('author');data=get(client);rows={x['id']:x for x in data['items']}
    for uid in (bid,mid,cid):assert rows[uid]['feedback']['note'].startswith('Synthetic return:') and rows[uid]['state']=='changes_requested'
    for metric in data['review_times']:assert metric['sample_count']>=1 and abs(metric['median_seconds']-172800)<1
    conn.execute("INSERT INTO creator_blocks(user_id,blocked_id) VALUES('reviewer1','author')")
    blocked=get(client);rows={x['id']:x for x in blocked['items']}
    assert all(rows[uid]['feedback'] is None for uid in (bid,mid,cid))
    assert all(metric['sample_count']==0 and metric['median_seconds'] is None for metric in blocked['review_times'])
    conn.execute("DELETE FROM creator_blocks WHERE user_id='reviewer1' AND blocked_id='author'")


def test_queue_positions_are_live_and_blocked_accounts_do_not_count(client,actor,database):
    conn=database[1];earlier=material(conn,'outsider',state='submitted');own=material(conn,state='submitted')
    conn.execute("INSERT INTO material_events(material_id,actor_id,action,detail,created_at) VALUES(%s,'outsider','submitted','{\"revision\":1}',now()-interval '2 days'),(%s,'author','submitted','{\"revision\":1}',now()-interval '1 day')",(earlier,own))
    actor('author');before=next(x for x in get(client)['items'] if x['id']==own)['queue_position'];assert before>=2
    conn.execute("INSERT INTO creator_blocks(user_id,blocked_id) VALUES('author','outsider')")
    after=next(x for x in get(client)['items'] if x['id']==own)['queue_position'];assert after==before-1
    conn.execute("DELETE FROM creator_blocks WHERE user_id='author' AND blocked_id='outsider'")
    conn.execute("UPDATE materials SET workflow_state='draft' WHERE id=%s",(own,));assert next(x for x in get(client)['items'] if x['id']==own)['queue_position'] is None


def test_tracker_redacts_question_titles_and_feedback_for_disclosure_and_assessments(client,actor,database):
    conn=database[1];qid='cq_test';bid=bank(conn,qid=qid);cid=collection(conn,questions=[qid]);actor('author')
    def locked():
        rows={r['id']:r for r in get(client)['items']};return all(rows[uid]['locked'] and rows[uid]['title']=='Linked question details are locked' and rows[uid]['feedback'] is None for uid in (bid,cid))
    assert locked()
    conn.execute("UPDATE canonical_questions SET source_defect='unresolved-source' WHERE id=%s",(qid,))
    conn.execute("INSERT INTO discussion_disclosures(user_id,canonical_id) VALUES('author',%s)",(qid,))
    assert not locked()
    conn.execute('UPDATE canonical_questions SET source_defect=NULL WHERE id=%s',(qid,))
    assert locked()
    conn.execute("INSERT INTO attempts(user_id,canonical_id,context,correct,chosen_text) VALUES('author',%s,'practice',false,'A')",(qid,))
    assert not locked()
    mock='tracker-'+uuid4().hex
    conn.execute("INSERT INTO mock_sessions(id,user_id,collection_id,question_ids,duration_seconds) VALUES(%s,'author','udc',%s,600)",(mock,[qid]));assert locked()
    conn.execute('DELETE FROM mock_sessions WHERE id=%s',(mock,));assert not locked()
    room='tracker-'+uuid4().hex
    conn.execute("INSERT INTO game_rooms(id,mode,state,owner_id,capacity,round_seconds,request_key,request_hash,questions) VALUES(%s,'gauntlet','running','author',1,30,%s,'synthetic',%s)",(room,room,Jsonb([{'id':qid}])))
    conn.execute("INSERT INTO game_members(room_id,user_id) VALUES(%s,'author')",(room,));assert locked()
    conn.execute("UPDATE game_rooms SET state='finished' WHERE id=%s",(room,));conn.execute('UPDATE game_members SET released_at=now() WHERE room_id=%s',(room,));assert not locked()
    cup='tracker-'+uuid4().hex;cup_room=cup+'-room'
    conn.execute("INSERT INTO game_cups(id,opens_at,closes_at,questions) VALUES(%s,now()-interval '1 hour',now()+interval '1 hour',%s)",(cup,Jsonb([{'id':qid}])))
    conn.execute("INSERT INTO game_rooms(id,mode,state,owner_id,capacity,round_seconds,request_key,request_hash,questions,cup_id) VALUES(%s,'cup','finished','author',1,30,%s,'synthetic',%s,%s)",(cup_room,cup_room,Jsonb([{'id':qid}]),cup))
    conn.execute("INSERT INTO game_members(room_id,user_id) VALUES(%s,'author')",(cup_room,));assert locked()
    conn.execute('DELETE FROM game_members WHERE room_id=%s',(cup_room,));conn.execute('DELETE FROM game_rooms WHERE id=%s',(cup_room,));assert not locked()


def test_tracker_has_no_fabricated_review_times_and_enforces_guest_native_bounds(client,actor,database):
    actor('outsider');data=get(client)
    assert len(data['review_times'])==3 and 'as_of' in data
    assert client.get('/api/community/submissions?limit=51').status_code==422
    client.cookies.clear();assert client.get('/api/community/submissions').status_code in (401,403)
    from test_mobile_companion import connect
    native,_=connect(client,actor)
    assert client.get('/api/community/submissions',headers=native).status_code==403
