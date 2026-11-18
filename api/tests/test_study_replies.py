"""Free-standing replies inherit their parent visibility and existing post budgets."""
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor
import pytest
from psycopg.types.json import Jsonb
from test_discussions import database,client,approve,question,answer,create as discussion
from test_study_posts import ready,note,status,mixed,voters
from test_material_shares import share
from test_content_studio import publish,document


def reply(client,h,pid,body='Synthetic response: compare the original wording before practising.',key=None):
    return client.post(f'/api/community/study-posts/{pid}/replies',headers={**h,'Idempotency-Key':key or uuid4().hex},json={'body':body})


def listed(client,pid,**params):
    r=client.get(f'/api/community/study-posts/{pid}/replies',params=params);assert r.status_code==200,r.text
    assert r.headers['cache-control']=='private, no-store';return r.json()


def root(client,actor,conn,**extra):
    ready(conn);h=actor('author');r=note(client,h,**extra);assert r.status_code==201,r.text
    return r.json()['id']


def test_new_account_reply_moderation_and_actions_without_currency(client,actor,database):
    _,conn=database;pid=root(client,actor,conn);h=actor('outsider')
    assert not status(client)['can_create']
    before=conn.execute('SELECT count(*) FROM reward_ledger').fetchone()[0]
    saved=reply(client,h,pid);assert saved.status_code==201,saved.text;rid=saved.json()['id'];assert saved.json()['needs_approval']
    own=listed(client,pid);assert own['can_reply'] and own['items'][0]['needs_approval']
    actor('author');assert not listed(client,pid)['items']
    assert client.get(f'/api/community/study-posts/{rid}').status_code==404
    approve(client,actor,rid);h=actor('author');assert listed(client,pid)['items'][0]['id']==rid
    assert rid not in mixed(client)
    assert client.post(f'/api/community/study-posts/{rid}/helpful',headers=h,json={'enabled':True}).json()['helpful']==1
    assert client.post(f'/api/community/study-posts/{rid}/report',headers=h,json={'reason':'spam','note':'Synthetic reply conduct details for moderation.'}).status_code==200
    h=actor('outsider');assert client.post(f'/api/community/study-posts/{rid}/helpful',headers=h,json={'enabled':True}).status_code==403
    assert client.post(f'/api/community/study-posts/{rid}/withdraw',headers=h,json={}).status_code==200
    assert not listed(client,pid)['items']
    assert conn.execute('SELECT count(*) FROM reward_ledger').fetchone()[0]==before
    # No question-discussion notification with an unusable null question link.
    assert conn.execute('SELECT count(*) FROM review_notifications WHERE discussion_post_id=%s',(rid,)).fetchone()[0]==0


def test_reply_caps_atomic_independent_and_replay_conflicts(client,actor,database):
    _,conn=database;pid=root(client,actor,conn);ready(conn,'outsider');h=actor('outsider')
    # Twenty-six existing replies; a real concurrent burst can consume only four.
    conn.execute("INSERT INTO posts(kind,parent_id,author_id,body,source_context,topic_tag) SELECT 'study',id,'outsider','Synthetic existing response',source_context,topic_tag FROM posts CROSS JOIN generate_series(1,26) WHERE id=%s",(pid,))
    key=uuid4().hex;first=reply(client,h,pid,key=key);assert first.status_code==201
    with ThreadPoolExecutor(max_workers=7) as pool:results=list(pool.map(lambda i:reply(client,h,pid,body='Synthetic separate reply number '+str(i)),range(7)))
    assert sum(r.status_code==201 for r in results)==3 and sum(r.status_code==429 for r in results)==4
    assert status(client)['replies_remaining']==0 and status(client)['posts_remaining']==5
    assert reply(client,h,pid,key=key).json()['id']==first.json()['id']
    assert reply(client,h,pid,key=key,body='Conflicting synthetic content under the same key.').status_code==409
    assert note(client,h).status_code==201 # Replies do not use top-level slots.
    # Both canonical and free-standing replies spend the same account/day budget.
    parent=conn.execute("SELECT id FROM posts WHERE author_id='outsider' AND canonical_id='cq_test' LIMIT 1").fetchone()[0]
    assert discussion(client,h,'cq_test',kind='reply',parent=parent).status_code==429
    second=conn.execute("SELECT id FROM posts WHERE kind='study' AND parent_id IS NULL AND author_id='outsider' LIMIT 1").fetchone()[0]
    assert reply(client,h,second,key=key).status_code==409


def test_reply_regular_lift_and_sanctions(client,actor,database):
    _,conn=database;pid=root(client,actor,conn);ready(conn,'outsider');parent=conn.execute("SELECT id FROM posts WHERE author_id='outsider' LIMIT 1").fetchone()[0]
    voters(conn,parent,25,qualified=True);h=actor('outsider');assert listed(client,pid)['reply_limit']==60
    conn.execute("INSERT INTO posts(kind,parent_id,author_id,body,source_context,topic_tag) SELECT 'study',id,'outsider','Synthetic prior regular response',source_context,topic_tag FROM posts CROSS JOIN generate_series(1,30) WHERE id=%s",(pid,))
    assert reply(client,h,pid).status_code==201
    action=conn.execute("INSERT INTO mod_actions(actor_id,action,target_user,note) VALUES('owner','mute','outsider','Synthetic restriction') RETURNING id").fetchone()[0]
    conn.execute("INSERT INTO sanctions(user_id,kind,step,ends_at,action_id) VALUES('outsider','mute',1,now()+interval '1 day',%s)",(action,))
    assert not listed(client,pid)['can_reply']
    assert reply(client,h,pid).status_code==403


def test_parent_and_reply_blocks_before_pagination_and_withdrawal(client,actor,database):
    _,conn=database;pid=root(client,actor,conn);ready(conn,'outsider');h=actor('outsider');rid=reply(client,h,pid).json()['id'];actor('owner')
    for a,b in [('owner','author'),('author','owner')]:
        conn.execute('INSERT INTO creator_blocks(user_id,blocked_id) VALUES(%s,%s)',(a,b))
        assert client.get(f'/api/community/study-posts/{pid}/replies').status_code==404
        assert client.get(f'/api/community/study-posts/{rid}').status_code==404
        conn.execute('DELETE FROM creator_blocks WHERE user_id=%s AND blocked_id=%s',(a,b))
    for a,b in [('owner','outsider'),('outsider','owner')]:
        conn.execute('INSERT INTO creator_blocks(user_id,blocked_id) VALUES(%s,%s)',(a,b))
        assert not listed(client,pid,limit=1)['items'] and not listed(client,pid,limit=1)['has_more']
        assert client.get(f'/api/community/study-posts/{rid}').status_code==404
        conn.execute('DELETE FROM creator_blocks WHERE user_id=%s AND blocked_id=%s',(a,b))
    assert listed(client,pid)['items'][0]['id']==rid
    h=actor('author');assert client.post(f'/api/community/study-posts/{pid}/withdraw',headers=h,json={}).status_code==200
    h=actor('outsider');assert client.get(f'/api/community/study-posts/{rid}').status_code==404
    assert reply(client,h,pid).status_code==404
    assert client.post(f'/api/community/study-posts/{rid}/withdraw',headers=h,json={}).status_code==200


def test_replies_inherit_question_disclosure_and_all_assessment_gates(client,actor,database,question):
    _,conn=database;qid=question[0];ready(conn);h=actor('author');answer(client,actor,qid,'author')
    pid=note(client,h,reference={'kind':'question','id':qid}).json()['id'];ready(conn,'outsider');h=actor('outsider')
    assert client.get(f'/api/community/study-posts/{pid}/replies').status_code==403
    assert reply(client,h,pid).status_code==403
    h=answer(client,actor,qid,'outsider');rid=reply(client,h,pid).json()['id'];assert listed(client,pid)['items'][0]['id']==rid
    mock='mock_'+uuid4().hex
    conn.execute("INSERT INTO mock_sessions(id,user_id,collection_id,question_ids,duration_seconds) VALUES(%s,'outsider','udc',%s,600)",(mock,[qid]))
    assert client.get(f'/api/community/study-posts/{pid}/replies').status_code==409
    assert client.get(f'/api/community/study-posts/{rid}').status_code==409
    assert reply(client,h,pid).status_code==409
    conn.execute('DELETE FROM mock_sessions WHERE id=%s',(mock,))
    room='reply_game_'+uuid4().hex
    conn.execute("INSERT INTO game_rooms(id,mode,state,owner_id,capacity,round_seconds,request_key,request_hash,questions) VALUES(%s,'gauntlet','running','outsider',1,30,%s,'synthetic',%s)",(room,room,Jsonb([{'id':qid}])))
    conn.execute("INSERT INTO game_members(room_id,user_id) VALUES(%s,'outsider')",(room,))
    assert client.get(f'/api/community/study-posts/{pid}/replies').status_code==409
    conn.execute("UPDATE game_rooms SET state='finished' WHERE id=%s",(room,))
    conn.execute('DELETE FROM game_members WHERE room_id=%s',(room,));conn.execute('DELETE FROM game_rooms WHERE id=%s',(room,))
    room='reply_cup_room_'+uuid4().hex
    cup='reply_cup_'+uuid4().hex
    conn.execute("INSERT INTO game_cups(id,opens_at,closes_at,questions) VALUES(%s,now()-interval '1 hour',now()+interval '1 hour',%s)",(cup,Jsonb([{'id':qid}])))
    conn.execute("INSERT INTO game_rooms(id,mode,state,owner_id,capacity,round_seconds,request_key,request_hash,questions,cup_id) VALUES(%s,'cup','finished','outsider',1,30,%s,'synthetic',%s,%s)",(room,room,Jsonb([{'id':qid}]),cup))
    conn.execute("INSERT INTO game_members(room_id,user_id) VALUES(%s,'outsider')",(room,))
    assert client.get(f'/api/community/study-posts/{rid}').status_code==409
    h=actor('owner');conn.execute('UPDATE posts SET needs_approval=true WHERE id=%s',(rid,))
    conn.execute("INSERT INTO mock_sessions(id,user_id,collection_id,question_ids,duration_seconds) VALUES(%s,'owner','udc',%s,600)",(mock+'_owner',[qid]))
    assert rid not in [p['post_id'] for p in client.get('/api/community/admin/queue?tab=New%20users').json()['items']]
    assert client.post(f'/api/community/admin/posts/{rid}/action',headers=h,json={'action':'approve'}).status_code==409


def test_material_reply_reference_withdrawal_blocks_and_moderator_context(client,actor,database):
    _,conn=database;mid=publish(client,actor,document('paid-preview'),user='outsider');ready(conn);h=actor('author');pid=share(client,h,mid).json()['id']
    h=actor('owner');rid=reply(client,h,pid).json()['id'];h=actor('author');assert 'PRIVATE_BODY_MARKER' not in str(listed(client,pid))
    actor('owner');queued=next(p for p in client.get('/api/community/admin/queue?tab=New%20users').json()['items'] if p['post_id']==rid);assert queued['material']['id']==mid
    h=actor('author');assert client.post(f'/api/community/admin/posts/{rid}/action',headers=h,json={'action':'approve'}).status_code==403
    for a,b in [('author','outsider'),('outsider','author')]:
        conn.execute('INSERT INTO creator_blocks(user_id,blocked_id) VALUES(%s,%s)',(a,b))
        assert client.get(f'/api/community/study-posts/{pid}/replies').status_code==404
        conn.execute('DELETE FROM creator_blocks WHERE user_id=%s AND blocked_id=%s',(a,b))
    conn.execute("UPDATE materials SET status='removed' WHERE id=%s",(mid,));assert client.get(f'/api/community/study-posts/{pid}/replies').status_code==404


def test_pending_parent_invalid_anchor_text_guests_and_native_boundaries(client,actor,database):
    _,conn=database;ready(conn,established=False);h=actor('author');pid=note(client,h).json()['id']
    assert reply(client,h,pid).status_code==409
    approve(client,actor,pid);h=actor('author');rid=reply(client,h,pid).json()['id']
    assert reply(client,h,rid).status_code==409
    assert reply(client,h,pid,body='Read https://external.test for a shortcut.').status_code==422
    assert reply(client,{},pid).status_code==403
    assert conn.execute('SELECT canonical_id FROM posts WHERE id=%s',(rid,)).fetchone()[0] is None
    with conn.transaction():conn.execute('SET LOCAL ROLE mpsc');assert conn.execute('SELECT parent_id FROM posts WHERE id=%s',(rid,)).fetchone()[0]==pid
    with pytest.raises(Exception,match='inherit'):
        with conn.transaction():conn.execute("INSERT INTO posts(kind,parent_id,author_id,body,source_context) VALUES('study',%s,'author','Synthetic context mismatch','{\"wrong\":true}')",(pid,))
    with pytest.raises(Exception,match='inherit'):
        with conn.transaction():conn.execute("INSERT INTO posts(kind,parent_id,author_id,body) VALUES('study',%s,'author','Synthetic nested reply')",(rid,))
    client.cookies.clear();page=listed(client,pid);assert not page['registered'] and not page['can_reply']
    assert reply(client,{},pid).status_code==401
    from test_mobile_companion import connect
    native,_=connect(client,actor,'author')
    assert client.get(f'/api/community/study-posts/{pid}/replies',headers=native).status_code==403
    assert reply(client,native,pid).status_code==403
    assert client.get(f'/api/community/posts/{rid}/replies',headers=native).status_code==404
    assert client.post(f'/api/community/posts/{rid}/withdraw',headers=native,json={}).status_code==404
