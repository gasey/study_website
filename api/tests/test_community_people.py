"""Computed standing, immutable display milestones and private public facts."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from uuid import uuid4
import pytest
from psycopg.types.json import Jsonb
from test_discussions import database,client,question,answer,create,approve
from test_study_posts import ready,voters,status,note


def standing_fixture(conn,n=25):
    ready(conn,attempts=0,age=0)
    pid=conn.execute("INSERT INTO posts(kind,author_id,body) VALUES('study','author','Synthetic contributor standing fixture') RETURNING id").fetchone()[0]
    voters(conn,pid,n,qualified=True)
    return pid


def public(conn,user='author',board=True):
    conn.execute('INSERT INTO creator_profiles(user_id,public) VALUES(%s,true) ON CONFLICT(user_id) DO UPDATE SET public=true',(user,))
    conn.execute('INSERT INTO reward_profiles(user_id,board_public) VALUES(%s,%s) ON CONFLICT(user_id) DO UPDATE SET board_public=excluded.board_public',(user,board))


@pytest.mark.parametrize('loss',['unvote','hidden','pending','before_fix','block','closed_voter','attempt_loss'])
def test_display_tier_survives_losses_but_privileges_are_current(client,actor,database,loss):
    _,conn=database;pid=standing_fixture(conn);actor('author');before=status(client)
    assert before['display_tier']==before['tier']=='Regular' and before['post_limit']==10
    voter=conn.execute('SELECT user_id FROM post_votes WHERE post_id=%s LIMIT 1',(pid,)).fetchone()[0]
    if loss=='unvote':conn.execute('DELETE FROM post_votes WHERE post_id=%s AND user_id=%s',(pid,voter))
    elif loss in ('hidden','pending','before_fix'):conn.execute('UPDATE posts SET '+('needs_approval' if loss=='pending' else loss)+'=true WHERE id=%s',(pid,))
    elif loss=='block':conn.execute("INSERT INTO creator_blocks(user_id,blocked_id) VALUES('author',%s)",(voter,))
    elif loss=='closed_voter':conn.execute('UPDATE users SET email=NULL WHERE id=%s',(voter,))
    else:conn.execute('UPDATE attempts SET canonical_id=NULL WHERE id=(SELECT id FROM attempts WHERE user_id=%s LIMIT 1)',(voter,))
    now=status(client);assert now['weighted_helpful']<25 and now['display_tier']=='Regular' and now['post_limit']==5
    assert now['reply_limit']==30
    if loss=='pending':assert now['privileges_restricted'] and not now['can_create']
    assert conn.execute('SELECT community_display_tier_rank(%s)',('author',)).fetchone()[0]==2
    assert conn.execute("SELECT max((detail->>'rank')::int) FROM creator_events WHERE action='community_tier_earned' AND target_id='author'").fetchone()[0]==2
    assert conn.execute('SELECT count(*) FROM reward_ledger').fetchone()[0]==0


def test_voter_maturity_promotes_display_without_stored_weights_or_get_writes(client,actor,database):
    _,conn=database;ready(conn,attempts=0,age=0)
    pid=conn.execute("INSERT INTO posts(kind,author_id,body) VALUES('study','author','Synthetic quarter-weight fixture') RETURNING id").fetchone()[0]
    voters(conn,pid,40);actor('author');assert status(client)['display_tier']=='Helper'
    voters(conn,pid,15,qualified=True);assert status(client)['display_tier']=='Regular'
    assert conn.execute('SELECT min(weight),max(weight) FROM post_votes WHERE post_id=%s',(pid,)).fetchone()==(9999,9999)
    count=conn.execute('SELECT count(*) FROM creator_events').fetchone()[0]
    for _ in range(2):
        r=client.get('/api/community/standing');assert r.status_code==200,r.text
        assert r.headers['cache-control']=='private, no-store' and r.json()['display_tier']=='Regular'
    assert conn.execute('SELECT count(*) FROM creator_events').fetchone()[0]==count


def test_role_audit_cannot_be_forged_rewritten_or_called_directly(client,actor,database,monkeypatch):
    _,conn=database;pid=standing_fixture(conn,10)
    with conn.transaction():
        conn.execute('SET LOCAL ROLE mpsc')
        assert conn.execute('SELECT community_display_tier_rank(%s)',('author',)).fetchone()[0]==1
        for query,args in [
          ("INSERT INTO creator_events(actor_id,action,target_id,detail) VALUES('author','community_tier_earned','author',%s)",(Jsonb({'rank':4}),)),
          ('SELECT community_record_tier(%s)',('author',)),
          ("UPDATE creator_events SET detail='{}' WHERE action='community_tier_earned'",()),
          ("DELETE FROM creator_events WHERE action='community_tier_earned'",())]:
            with pytest.raises(Exception):
                with conn.transaction():conn.execute(query,args)
    # Real role readers also work in read-only transactions.
    from app.routers import community,creators
    original=community.cursor
    @asynccontextmanager
    async def readonly():
        async with original() as cur:
            await cur.execute('SET TRANSACTION READ ONLY');await cur.execute('SET LOCAL ROLE mpsc');yield cur
    monkeypatch.setattr(community,'cursor',readonly);monkeypatch.setattr(creators,'cursor',readonly)
    public(conn);actor('author');assert client.get('/api/community/standing').status_code==200
    actor('outsider');assert client.get('/api/community/guides').status_code==200
    assert client.get('/api/creators/author').status_code==200


def test_post_flair_and_profile_link_require_public_consent(client,actor,database):
    _,conn=database;pid=standing_fixture(conn);actor('outsider')
    r=client.get(f'/api/community/study-posts/{pid}');assert r.status_code==200,r.text
    assert r.json()['author_tier']=='Regular' and r.json()['author_profile_id'] is None
    assert client.get('/api/creators/author').status_code==404
    public(conn)
    r=client.get(f'/api/community/study-posts/{pid}');assert r.json()['author_profile_id']=='author'
    p=client.get('/api/creators/author').json();assert p['community']['helpful_count']==25 and p['community']['accepted_answers']==0
    assert p['community']['display_tier']=='Regular';assert not set(p)&{'email','weighted_helpful','role','plan'}
    feed=client.get('/api/community/feed?content_version=2').json()['items'];assert next(p for p in feed if p['id']==pid)['author_tier']=='Regular'


def test_guides_week_is_dated_opted_in_current_and_moderation_gated(client,actor,database):
    _,conn=database;pid=standing_fixture(conn,150);public(conn);actor('outsider')
    r=client.get('/api/community/guides');assert r.status_code==200,r.text;week=r.json()
    assert r.headers['cache-control']=='private, no-store' and week['as_of'] and week['week_start']<=week['week_end']
    assert [p['id'] for p in week['items']]==['author'] and week['items'][0]['weekly_helpful']==150
    conn.execute("UPDATE post_votes SET created_at=(date_trunc('week',now() AT TIME ZONE 'Asia/Kolkata') AT TIME ZONE 'Asia/Kolkata')-interval '1 second' WHERE post_id=%s",(pid,))
    assert not client.get('/api/community/guides').json()['items']
    conn.execute('UPDATE post_votes SET created_at=now() WHERE post_id=%s',(pid,))
    for table,column in [('creator_profiles','public'),('reward_profiles','board_public')]:
        conn.execute('UPDATE '+table+' SET '+column+"=false WHERE user_id='author'");assert not client.get('/api/community/guides').json()['items']
        conn.execute('UPDATE '+table+' SET '+column+"=true WHERE user_id='author'")
    conn.execute('UPDATE posts SET needs_approval=true WHERE id=%s',(pid,));assert not client.get('/api/community/guides').json()['items']
    conn.execute('UPDATE posts SET needs_approval=false WHERE id=%s',(pid,));assert client.get('/api/community/guides').json()['items']
    action=conn.execute("INSERT INTO mod_actions(actor_id,action,target_user) VALUES('owner','mute','author') RETURNING id").fetchone()[0]
    conn.execute("INSERT INTO sanctions(user_id,kind,step,action_id,starts_at,ends_at) VALUES('author','mute',1,%s,now()-interval '1 minute',now()+interval '1 hour')",(action,))
    assert not client.get('/api/community/guides').json()['items']
    conn.execute("UPDATE sanctions SET lifted_at=now() WHERE user_id='author'")
    voter=conn.execute('SELECT user_id FROM post_votes WHERE post_id=%s LIMIT 1',(pid,)).fetchone()[0]
    conn.execute('DELETE FROM post_votes WHERE post_id=%s AND user_id=%s',(pid,voter))
    assert conn.execute('SELECT community_display_tier_rank(%s)',('author',)).fetchone()[0]==4
    assert not client.get('/api/community/guides').json()['items']
    actor('author');s=client.get('/api/community/standing').json();assert s['display_tier']=='Guide' and s['tier']=='Mentor'
    assert s['mentor_eligible'] and s['post_limit']==10


@pytest.mark.parametrize('pair',[('author','outsider'),('outsider','author')])
def test_new_profile_counts_and_guides_respect_both_blocks(client,actor,database,pair):
    _,conn=database;standing_fixture(conn,150);public(conn);actor('outsider')
    assert client.get('/api/community/guides').json()['items']
    conn.execute('INSERT INTO creator_blocks(user_id,blocked_id) VALUES(%s,%s)',pair)
    assert client.get('/api/creators/author').status_code==404
    assert not client.get('/api/community/guides').json()['items']


def test_profile_counts_preserve_disclosure_parent_and_active_assessment(client,actor,question):
    qid,conn=question;h=answer(client,actor,qid,'outsider');pid=create(client,h,qid).json()['id'];approve(client,actor,pid)
    h=answer(client,actor,qid,'author');rid=create(client,h,qid,kind='reply',parent=pid).json()['id'];approve(client,actor,rid)
    other=actor('outsider');assert client.post(f'/api/community/posts/{rid}/accept',headers=other,json={'enabled':True}).status_code==200
    voters(conn,rid,150,qualified=True);public(conn);actor('owner')
    def counts():
        r=client.get('/api/creators/author');assert r.status_code==200,r.text;return r.json()['community']
    assert counts()['helpful_count']==counts()['accepted_answers']==0
    assert not client.get('/api/community/guides').json()['items']
    h=answer(client,actor,qid,'owner');assert counts()['helpful_count']==150 and counts()['accepted_answers']==1
    assert client.get('/api/community/guides').json()['items'][0]['id']=='author'
    conn.execute("INSERT INTO mock_sessions(id,user_id,collection_id,question_ids,duration_seconds) VALUES('tier-protected','owner','udc',%s,600)",([qid],))
    assert counts()['helpful_count']==counts()['accepted_answers']==0
    assert not client.get('/api/community/guides').json()['items']
    conn.execute("DELETE FROM mock_sessions WHERE id='tier-protected'")
    room='tier-game-'+uuid4().hex
    conn.execute("INSERT INTO game_rooms(id,mode,state,owner_id,capacity,round_seconds,request_key,request_hash,questions) VALUES(%s,'gauntlet','running','owner',1,30,%s,'synthetic',%s)",(room,room,Jsonb([{'id':qid}])))
    conn.execute("INSERT INTO game_members(room_id,user_id) VALUES(%s,'owner')",(room,))
    assert counts()['helpful_count']==counts()['accepted_answers']==0
    assert not client.get('/api/community/guides').json()['items']
    conn.execute("UPDATE game_rooms SET state='finished' WHERE id=%s",(room,))
    conn.execute("UPDATE game_members SET released_at=now() WHERE room_id=%s",(room,))
    assert counts()['helpful_count']==150
    cup='tier-cup-'+uuid4().hex;cup_room=cup+'-room'
    conn.execute("INSERT INTO game_cups(id,opens_at,closes_at,questions) VALUES(%s,now()-interval '1 hour',now()+interval '1 hour',%s)",(cup,Jsonb([{'id':qid}])))
    conn.execute("INSERT INTO game_rooms(id,mode,state,owner_id,capacity,round_seconds,request_key,request_hash,questions,cup_id) VALUES(%s,'cup','finished','owner',1,30,%s,'synthetic',%s,%s)",(cup_room,cup_room,Jsonb([{'id':qid}]),cup))
    conn.execute("INSERT INTO game_members(room_id,user_id) VALUES(%s,'owner')",(cup_room,))
    assert counts()['helpful_count']==counts()['accepted_answers']==0
    assert not client.get('/api/community/guides').json()['items']
    conn.execute('DELETE FROM game_members WHERE room_id=%s',(cup_room,));conn.execute('DELETE FROM game_rooms WHERE id=%s',(cup_room,))
    assert counts()['helpful_count']==150 and counts()['accepted_answers']==1
    conn.execute('UPDATE posts SET hidden=true WHERE id=%s',(pid,));assert counts()['helpful_count']==counts()['accepted_answers']==0


def test_native_new_reads_are_denied(client,actor,database):
    from test_mobile_companion import connect
    native,_=connect(client,actor)
    assert client.get('/api/community/standing',headers=native).status_code==403
    assert client.get('/api/community/guides',headers=native).status_code==403


def test_public_counts_follow_linked_question_disclosure(client,actor,question):
    qid,conn=question;ready(conn);h=answer(client,actor,qid,'author')
    pid=note(client,h,reference={'kind':'question','id':qid}).json()['id'];approve(client,actor,pid);voters(conn,pid,1);public(conn)
    actor('outsider');assert client.get('/api/creators/author').json()['community']['helpful_count']==0
    answer(client,actor,qid,'outsider');assert client.get('/api/creators/author').json()['community']['helpful_count']==1


def test_public_counts_follow_material_publication_and_its_author_block(client,actor,database):
    from test_content_studio import publish,document
    from test_material_shares import share
    _,conn=database;mid=publish(client,actor,document(),user='outsider');ready(conn);h=actor('author')
    pid=share(client,h,mid).json()['id'];approve(client,actor,pid);voters(conn,pid,1);public(conn)
    actor('owner');assert client.get('/api/creators/author').json()['community']['helpful_count']==1
    conn.execute("INSERT INTO creator_blocks(user_id,blocked_id) VALUES('owner','outsider')")
    assert client.get('/api/creators/author').json()['community']['helpful_count']==0
    conn.execute("DELETE FROM creator_blocks WHERE user_id='owner' AND blocked_id='outsider'")
    conn.execute("UPDATE materials SET status='removed' WHERE id=%s",(mid,))
    assert client.get('/api/creators/author').json()['community']['helpful_count']==0


def test_competing_vote_changes_keep_display_and_unique_history(client,actor,database):
    name,conn=database;pid=standing_fixture(conn,24)
    # Two actual vote routes take the normal post lock before tier serialization.
    ready(conn,'outsider');h=actor('outsider')|{'Cookie':'ism_session=test-session-outsider'}
    with ThreadPoolExecutor(max_workers=2) as pool:
        rs=list(pool.map(lambda _:client.post(f'/api/community/study-posts/{pid}/helpful',headers=h,json={'enabled':True}),range(2)))
    assert all(r.status_code==200 for r in rs),[r.text for r in rs]
    assert conn.execute('SELECT community_display_tier_rank(%s)',('author',)).fetchone()[0]==2
    assert client.post(f'/api/community/study-posts/{pid}/helpful',headers=h,json={'enabled':False}).status_code==200
    assert conn.execute('SELECT community_display_tier_rank(%s)',('author',)).fetchone()[0]==2
    assert not conn.execute("SELECT target_id,detail->>'rank' FROM creator_events WHERE action='community_tier_earned' GROUP BY 1,2 HAVING count(*)>1").fetchone()
