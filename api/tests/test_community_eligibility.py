"""Eligibility of public/shared subjects; no history erasure or real recipients."""
import asyncio
from contextlib import asynccontextmanager
from uuid import uuid4
import pytest
from psycopg.types.json import Jsonb
from app.config import settings
from app.db import cursor
from app.services import audience,community_audience,games,desk_games
from test_discussions import database,client,question,answer,create,approve
from test_creator_profiles import opt_in
from test_content_studio import publish
from test_study_desks import desk_setup,room,join
from test_owned_calendar import save as calendar_save
from test_learning_eligibility import wait_for_advisory_wait
from test_account_privacy import declare
from test_games_search import game_case
from test_game_eligibility import room_case


@pytest.fixture(scope='module',autouse=True)
def manual_workers():
    from app import main
    async def idle():await asyncio.Event().wait()
    with pytest.MonkeyPatch.context() as patch:
        for n in ('assessment_worker','learning_worker','game_worker'):patch.setattr(main,n,idle)
        yield


@asynccontextmanager
async def role():
    async with cursor() as cur:
        await cur.execute('SET LOCAL ROLE mpsc')
        yield cur


@pytest.fixture(autouse=True)
def original_flag_and_real_readers(client,database,monkeypatch):
    from app.routers import community,creators,discussions,study_posts,materials,study_desks,search,inbox,games as game_routes
    monkeypatch.setattr(settings,'audience_gate_enabled',False)
    for module in (community,creators,discussions,study_posts,materials,study_desks,search,inbox,game_routes):monkeypatch.setattr(module,'cursor',role)
    database[1].execute("INSERT INTO account_audience(user_id,category) SELECT id,'adult' FROM users ON CONFLICT(user_id) DO UPDATE SET category='adult'")


def run(client,fn,*args):
    async def call():
        async with role() as cur:return await fn(cur,*args)
    return client.portal.call(call)


def restrict(c,user,category):
    if category=='closed':
        c.execute('UPDATE users SET closed_at=now(),email=NULL,password_hash=NULL,name=NULL,avatar=NULL,email_verified_at=NULL,contribution_public=false WHERE id=%s',(user,))
        return
    if category is None:c.execute('DELETE FROM account_audience WHERE user_id=%s',(user,))
    else:c.execute('UPDATE account_audience SET category=%s WHERE user_id=%s',(category,user))


def post(c,user='author',kind='study',parent=None,qid=None,accepted=False):
    return c.execute('INSERT INTO posts(author_id,kind,body,parent_id,canonical_id,accepted) VALUES(%s,%s,%s,%s,%s,%s) RETURNING id',
      (user,kind,'Synthetic subject content '+uuid4().hex,parent,qid,accepted)).fetchone()[0]


def feed(client,**kw):
    r=client.get('/api/community/feed',params={'content_version':2,**kw});assert r.status_code==200,r.text
    return r.json()


@pytest.mark.parametrize('category',[None,'under18','closed'])
def test_creator_discovery_profile_search_follow_and_history(client,actor,database,monkeypatch,category):
    c=database[1];opt_in(client,actor);h=actor('outsider')
    assert client.post('/api/creators/author/follow',headers=h,json={'enabled':True}).status_code==200
    original=c.execute("SELECT * FROM creator_profiles WHERE user_id='author'").fetchone()
    restrict(c,'author',category);monkeypatch.setattr(settings,'audience_gate_enabled',True)
    assert client.get('/api/creators/author').status_code==404
    r=client.get('/api/creators?q=author');assert r.status_code==200 and r.json()['items']==[] and r.json()['total']==0
    r=client.get('/api/search?q=author&category=people');assert r.status_code==200 and '"id":"author"' not in r.text
    assert client.post('/api/creators/author/follow',headers=h,json={'enabled':True}).status_code==404
    assert client.post('/api/creators/author/follow',headers=h,json={'enabled':False}).status_code==200
    assert c.execute("SELECT * FROM creator_profiles WHERE user_id='author'").fetchone()==original


@pytest.mark.parametrize('category',[None,'under18','closed'])
def test_mixed_feed_and_direct_study_read_hide_subject_before_pagination(client,actor,database,monkeypatch,category):
    c=database[1];visible=post(c,'reviewer1');hidden=post(c);saved=c.execute('SELECT * FROM posts ORDER BY id').fetchall()
    restrict(c,'author',category);actor('outsider');monkeypatch.setattr(settings,'audience_gate_enabled',True)
    r=feed(client,limit=1);assert [x['id'] for x in r['items']]==[visible] and not r['has_more']
    assert client.get(f'/api/community/study-posts/{hidden}').status_code==404
    assert c.execute('SELECT * FROM posts ORDER BY id').fetchall()==saved


def test_study_reply_pages_hide_restricted_child_and_parent(client,actor,database,monkeypatch):
    c=database[1];parent=post(c,'reviewer1');good=post(c,'reviewer2',parent=parent);bad=post(c,'author',parent=parent)
    other=post(c,'author');child=post(c,'reviewer2',parent=other)
    restrict(c,'author','under18');actor('outsider');monkeypatch.setattr(settings,'audience_gate_enabled',True)
    r=client.get(f'/api/community/study-posts/{parent}/replies?limit=1');assert r.status_code==200,r.text
    assert [x['id'] for x in r.json()['items']]==[good] and not r.json()['has_more']
    assert client.get(f'/api/community/study-posts/{bad}').status_code==404
    assert client.get(f'/api/community/study-posts/{child}').status_code==404


@pytest.mark.parametrize('category',[None,'under18','closed'])
def test_question_threads_feed_accepted_snippet_and_unanswered(client,actor,question,monkeypatch,category):
    q,c=question;answer(client,actor,q,'outsider');parent=post(c,'reviewer1','doubt',qid=q)
    accepted=post(c,'author','reply',parent=parent,qid=q,accepted=True)
    own=post(c,'author','doubt',qid=q);restrict(c,'author',category)
    monkeypatch.setattr(settings,'audience_gate_enabled',True)
    r=client.get(f'/api/community/questions/{q}/discussion');assert r.status_code==200,r.text
    assert [x['id'] for x in r.json()['items']]==[parent]
    assert client.get(f'/api/community/posts/{own}/replies').status_code==404
    r=client.get(f'/api/community/posts/{parent}/replies');assert r.status_code==200 and r.json()['items']==[]
    card=next(x for x in feed(client)['items'] if x['id']==parent);assert card['accepted_answer'] is None
    assert parent in [x['id'] for x in feed(client,discussion='unanswered')['items']]
    assert c.execute('SELECT accepted FROM posts WHERE id=%s',(accepted,)).fetchone()==(True,)


@pytest.mark.parametrize('reverse',[False,True])
def test_age_enabled_discussions_keep_both_blocks_and_disclosure_gate(client,actor,question,monkeypatch,reverse):
    q,c=question;pid=post(c,'author','doubt',qid=q)
    actor('outsider');monkeypatch.setattr(settings,'audience_gate_enabled',True)
    assert client.get(f'/api/community/questions/{q}/discussion').json()['items']==[]
    monkeypatch.setattr(settings,'audience_gate_enabled',False);answer(client,actor,q,'outsider')
    monkeypatch.setattr(settings,'audience_gate_enabled',True)
    assert pid in [x['id'] for x in feed(client)['items']]
    a,b=('author','outsider') if reverse else ('outsider','author')
    c.execute('INSERT INTO creator_blocks(user_id,blocked_id) VALUES(%s,%s)',(a,b))
    assert client.get(f'/api/community/questions/{q}/discussion').json()['items']==[]
    assert pid not in [x['id'] for x in feed(client)['items']]


@pytest.mark.parametrize('category',[None,'under18','closed'])
def test_material_catalog_search_direct_and_cross_author_reference(client,actor,database,monkeypatch,category):
    c=database[1];mid=publish(client,actor,user='author')
    pid=c.execute("INSERT INTO posts(kind,author_id,body,material_id,source_context) VALUES('material-share','reviewer1','Synthetic shared material',%s,%s) RETURNING id",(mid,Jsonb({'study_reference':{'kind':'material','id':mid}}))).fetchone()[0]
    original=c.execute('SELECT * FROM material_revisions WHERE material_id=%s ORDER BY revision',(mid,)).fetchall()
    restrict(c,'author',category);actor('outsider');monkeypatch.setattr(settings,'audience_gate_enabled',True)
    assert client.get('/api/materials/'+mid).status_code==404
    listing=client.get('/api/materials');assert listing.status_code==200 and mid not in [x['id'] for x in listing.json()['items']]
    assert client.get(f'/api/community/study-posts/{pid}').status_code==404
    assert pid not in [x['id'] for x in feed(client)['items']]
    r=client.get('/api/search?q=Synthetic&category=notes');assert r.status_code==200 and mid not in r.text
    assert c.execute('SELECT * FROM material_revisions WHERE material_id=%s ORDER BY revision',(mid,)).fetchall()==original


def test_restricted_follower_is_not_counted_and_flag_off_restores_original_view(client,actor,database,monkeypatch):
    c=database[1];opt_in(client,actor);c.execute("INSERT INTO creator_follows(follower_id,creator_id) VALUES('reviewer1','author')")
    actor('outsider');restrict(c,'reviewer1','under18');monkeypatch.setattr(settings,'audience_gate_enabled',True)
    assert client.get('/api/creators/author').json()['followers']==0
    monkeypatch.setattr(settings,'audience_gate_enabled',False)
    assert client.get('/api/creators/author').json()['followers']==1


def test_reserved_team_attribution_remains_visible_without_inferred_learner_age(client,actor,database,monkeypatch):
    c=database[1];pid=post(c,'team');actor('outsider');monkeypatch.setattr(settings,'audience_gate_enabled',True)
    assert pid in [x['id'] for x in feed(client)['items']]
    assert client.get(f'/api/community/study-posts/{pid}').status_code==200
    assert c.execute("SELECT count(*) FROM account_audience WHERE user_id='team'").fetchone()==(0,)


@pytest.mark.parametrize('category',[None,'under18','closed'])
def test_desk_member_shares_messages_calendar_and_counts_are_withheld(client,actor,database,desk_setup,monkeypatch,category):
    c=database[1];did=room(client,actor);join(client,actor,did);join(client,actor,did,'reviewer1')
    h=actor('outsider')
    iid=client.post(f'/api/desk/rooms/{did}/items',headers={**h,'Idempotency-Key':uuid4().hex},json={'kind':'note','title':'Restricted subject note','body':'SUBJECT_PRIVATE_MARKER','question_id':'cq_test'}).json()['id']
    assert client.post(f'/api/desk/rooms/{did}/messages',headers={**h,'Idempotency-Key':uuid4().hex},json={'body':'SUBJECT_MESSAGE_MARKER','note_id':iid}).status_code==201
    assert calendar_save(client,h,desk_id=did,title='SUBJECT_CALENDAR_MARKER').status_code==200
    saved=c.execute('SELECT * FROM study_desk_items WHERE id=%s',(iid,)).fetchone()
    restrict(c,'outsider',category);actor('reviewer1');monkeypatch.setattr(settings,'audience_gate_enabled',True)
    r=client.get(f'/api/desk/rooms/{did}');assert r.status_code==200,r.text
    assert 'outsider' not in [m['user_id'] for m in r.json()['members']]
    assert client.get('/api/desk/rooms').json()['items'][0]['members']==2
    assert client.get(f'/api/desk/rooms/{did}/items').json()['items']==[]
    assert client.get(f'/api/desk/rooms/{did}/messages').json()['items']==[]
    thread=client.get('/api/inbox/threads');assert thread.status_code==200,thread.text
    assert thread.json()['items'][0]['last_message'] is None and thread.json()['items'][0]['unread']==0
    assert client.get(f'/api/desk/rooms/{did}/notes/{iid}').status_code==404
    cal=client.get(f'/api/desk/rooms/{did}/calendar?start=2026-11-01&end=2026-12-01');assert cal.status_code==200 and cal.json()['occurrences']==[]
    assert c.execute('SELECT * FROM study_desk_items WHERE id=%s',(iid,)).fetchone()==saved


def test_restricted_desk_owner_hides_room_search_and_invite_but_member_can_leave(client,actor,database,desk_setup,monkeypatch):
    c=database[1];did=room(client,actor);join(client,actor,did);h=actor('author')
    invitation=client.post(f'/api/desk/rooms/{did}/invite',headers=h,json={'handle':'reviewer1'}).json()['id']
    restrict(c,'author','under18');h=actor('outsider');monkeypatch.setattr(settings,'audience_gate_enabled',True)
    assert client.get('/api/desk/rooms').json()['items']==[]
    assert client.get(f'/api/desk/rooms/{did}').status_code==404
    assert did not in client.get('/api/search?q=Synthetic&category=desks').text
    assert client.get('/api/inbox/threads').json()['items']==[]
    actor('reviewer1');assert client.get('/api/desk/rooms').json()['invitations']==[]
    assert client.post('/api/desk/invites/'+invitation,headers=actor('reviewer1'),json={'decision':'accept'}).status_code==409
    assert client.post('/api/desk/invites/'+invitation,headers=actor('reviewer1'),json={'decision':'decline'}).status_code==200
    assert client.post(f'/api/desk/rooms/{did}/leave',headers=actor('outsider')).status_code==200


def test_new_desk_invitation_cannot_target_restricted_handle(client,actor,database,desk_setup,monkeypatch):
    c=database[1];did=room(client,actor);h=actor('author');restrict(c,'outsider','under18')
    monkeypatch.setattr(settings,'audience_gate_enabled',True)
    r=client.post(f'/api/desk/rooms/{did}/invite',headers=h,json={'handle':'outsider'});assert r.status_code==404,r.text
    assert c.execute('SELECT count(*) FROM study_desk_invites WHERE desk_id=%s',(did,)).fetchone()==(0,)


@pytest.mark.parametrize('category',[None,'under18','closed'])
def test_immediate_notices_are_suppressed_without_history_replay(client,actor,database,monkeypatch,category):
    c=database[1];restrict(c,'author',category);monkeypatch.setattr(settings,'audience_gate_enabled',True)
    key='prospective:'+uuid4().hex
    sql="INSERT INTO review_notifications(user_id,event_key,message) VALUES(%s,%s,'Synthetic prospective study notice') ON CONFLICT DO NOTHING"
    assert run(client,community_audience.notify,'author',sql,('author',key)) is False
    assert c.execute('SELECT count(*) FROM review_notifications WHERE event_key=%s',(key,)).fetchone()==(0,)
    c.execute("INSERT INTO account_audience(user_id,category) VALUES('author','adult') ON CONFLICT(user_id) DO UPDATE SET category='adult'")
    assert c.execute('SELECT count(*) FROM review_notifications WHERE event_key=%s',(key,)).fetchone()==(0,)


def test_busy_notice_releases_temporary_lease_without_blocking(client,actor,database,monkeypatch):
    monkeypatch.setattr(settings,'audience_gate_enabled',True)
    async def scenario():
        async with role() as locker:
            await audience.learning_processing_lock(locker,'author',restricting=True)
            async with role() as publisher:
                assert not await asyncio.wait_for(community_audience.notify(publisher,'author',"SELECT 1",()),5)
    client.portal.call(scenario)


def test_restriction_waits_for_admitted_immediate_notice(client,actor,database,monkeypatch):
    h=actor('author');monkeypatch.setattr(settings,'audience_gate_enabled',True)
    async def scenario():
        async with role() as publisher:
            assert await community_audience.notify(publisher,'author',"INSERT INTO review_notifications(user_id,event_key,message) VALUES('author',%s,'Synthetic notice')",('lease:'+uuid4().hex,))
            task=asyncio.create_task(asyncio.to_thread(declare,client,'under18',headers=h,user_id='author',expected_version=1))
            try:await wait_for_advisory_wait(publisher,task)
            except BaseException:task.cancel();raise
        r=await asyncio.wait_for(task,5);assert r.status_code==200,r.text
    client.portal.call(scenario)


@pytest.mark.parametrize('category',[None,'under18','closed'])
def test_game_view_removes_restricted_player_and_owner_attribution(client,database,game_case,monkeypatch,category):
    c,rid,users,_,_=room_case(client,game_case,'duel',2)
    restrict(c,users[0],category);monkeypatch.setattr(settings,'audience_gate_enabled',True)
    before=c.execute('SELECT * FROM game_members WHERE room_id=%s ORDER BY user_id',(rid,)).fetchall()
    async def view(cur):return await games.view(cur,await games.room(cur,rid),users[1],await games.clock(cur))
    result=run(client,view)
    assert [p['user_id'] for p in result['players']]==[users[1]]
    assert result['owner_id']=='' and isinstance(result['owner_id'],str)
    assert c.execute('SELECT * FROM game_members WHERE room_id=%s ORDER BY user_id',(rid,)).fetchall()==before


def test_subject_predicate_rejects_unqualified_correlation(monkeypatch):
    monkeypatch.setattr(settings,'audience_gate_enabled',True)
    with pytest.raises(ValueError,match='qualified'):audience.subject_sql('id')


def test_desk_weekly_projection_excludes_restricted_sharing_member(client,actor,database,desk_setup,monkeypatch):
    c=database[1];did=room(client,actor);join(client,actor,did)
    c.execute("UPDATE study_desk_members SET sharing='{"+'"progress":true'+"}' WHERE desk_id=%s",(did,))
    restrict(c,'outsider','under18');actor('author');monkeypatch.setattr(settings,'audience_gate_enabled',True)
    r=client.get(f'/api/desk/rooms/{did}/weekly-goal');assert r.status_code==200,r.text
    assert r.json()['sharing_members']==1


def test_desk_note_subject_still_obeys_reverse_block_and_assessment(client,actor,database,desk_setup,monkeypatch):
    c=database[1];did=room(client,actor);join(client,actor,did);h=actor('author')
    r=client.post(f'/api/desk/rooms/{did}/items',headers={**h,'Idempotency-Key':uuid4().hex},json={'kind':'note','title':'Synthetic visible note','body':'Synthetic shared note body','question_id':'cq_test'})
    assert r.status_code==201,r.text;iid=r.json()['id'];actor('outsider')
    monkeypatch.setattr(settings,'audience_gate_enabled',True)
    assert client.get(f'/api/desk/rooms/{did}/notes/{iid}').status_code==200
    c.execute("INSERT INTO creator_blocks(user_id,blocked_id) VALUES('author','outsider')")
    assert client.get(f'/api/desk/rooms/{did}/notes/{iid}').status_code==404
    c.execute("DELETE FROM creator_blocks WHERE user_id='author'")
    c.execute("INSERT INTO mock_sessions(id,user_id,collection_id,question_ids,duration_seconds) VALUES(%s,'outsider','udc',ARRAY['cq_test'],600)",('age-desk-mock-'+uuid4().hex,))
    assert client.get(f'/api/desk/rooms/{did}/notes/{iid}').status_code==409


def test_actual_desk_notice_writer_omits_restricted_recipient(client,actor,database,desk_setup,monkeypatch):
    from app.routers import study_desks
    c=database[1];did=room(client,actor);join(client,actor,did);restrict(c,'outsider','under18')
    monkeypatch.setattr(settings,'audience_gate_enabled',True);key='desk-age-notice:'+uuid4().hex
    run(client,study_desks.notify,'outsider',key,'Synthetic shared notice',did)
    assert c.execute('SELECT count(*) FROM review_notifications WHERE event_key=%s',(key,)).fetchone()==(0,)


def test_actual_reply_notice_writer_omits_restricted_parent(client,actor,question,monkeypatch):
    from app.routers import discussions
    q,c=question;parent=post(c,'author','doubt',qid=q);rid=post(c,'reviewer1','reply',parent=parent,qid=q)
    restrict(c,'author','under18');monkeypatch.setattr(settings,'audience_gate_enabled',True)
    run(client,discussions.notify_reply,rid)
    assert c.execute('SELECT count(*) FROM review_notifications WHERE event_key=%s',('discussion-reply:'+str(rid),)).fetchone()==(0,)


def test_restricted_accounts_keep_privacy_export_and_staff_moderation(client,actor,database,monkeypatch):
    c=database[1];pid=post(c);c.execute('UPDATE posts SET needs_approval=true WHERE id=%s',(pid,))
    restrict(c,'author','under18');actor('author');monkeypatch.setattr(settings,'audience_gate_enabled',True)
    r=client.get('/api/me/data-export?user_id=author');assert r.status_code==200,r.text
    assert str(pid) in r.text
    actor('owner');r=client.get('/api/community/admin/queue');assert r.status_code==200,r.text
    assert 'post:'+str(pid) in [x['id'] for x in r.json()['items']]


@pytest.mark.parametrize('reverse',[False,True])
def test_age_enabled_creator_and_material_readers_keep_both_block_pairs(client,actor,database,monkeypatch,reverse):
    c=database[1];mid=publish(client,actor,user='author');opt_in(client,actor)
    actor('outsider');monkeypatch.setattr(settings,'audience_gate_enabled',True)
    assert client.get('/api/creators/author').status_code==200
    assert client.get('/api/materials/'+mid).status_code==200
    a,b=('author','outsider') if reverse else ('outsider','author')
    c.execute('INSERT INTO creator_blocks(user_id,blocked_id) VALUES(%s,%s)',(a,b))
    assert client.get('/api/creators/author').status_code==404
    assert client.get('/api/materials/'+mid).status_code==404
    assert '"id":"author"' not in client.get('/api/creators?q=author').text
    assert mid not in client.get('/api/materials').text


def test_unknown_subject_confirmation_resumes_read_visibility_without_new_records(client,actor,database,monkeypatch):
    c=database[1];pid=post(c);original=c.execute('SELECT * FROM posts WHERE id=%s',(pid,)).fetchone()
    restrict(c,'author',None);actor('outsider');monkeypatch.setattr(settings,'audience_gate_enabled',True)
    assert client.get(f'/api/community/study-posts/{pid}').status_code==404
    c.execute("INSERT INTO account_audience(user_id,category) VALUES('author','adult')")
    assert client.get(f'/api/community/study-posts/{pid}').status_code==200
    assert c.execute('SELECT * FROM posts WHERE id=%s',(pid,)).fetchone()==original


def test_guides_candidates_and_visible_counts_exclude_restricted_author(client,actor,database,monkeypatch):
    from test_community_people import standing_fixture,public
    from app.services import community_people
    c=database[1];pid=standing_fixture(c,150);public(c)
    # These synthetic eligible voters are created after the baseline declaration fixture.
    c.execute("INSERT INTO account_audience(user_id,category) SELECT user_id,'adult' FROM post_votes WHERE post_id=%s ON CONFLICT DO NOTHING",(pid,))
    actor('outsider');monkeypatch.setattr(settings,'audience_gate_enabled',True)
    assert [x['id'] for x in client.get('/api/community/guides').json()['items']]==['author']
    restrict(c,'author','under18')
    assert client.get('/api/community/guides').json()['items']==[]
    assert run(client,community_people.visible_stats,['author'],'outsider')=={}


def test_desk_game_source_access_rejects_restricted_sharer(client,actor,database,desk_setup,monkeypatch):
    from fastapi import HTTPException
    c=database[1];did=room(client,actor);join(client,actor,did)
    h=actor('outsider');r=client.post(f'/api/desk/rooms/{did}/items',headers={**h,'Idempotency-Key':uuid4().hex},json={'kind':'question','question_id':'cq_test','title':'Synthetic source share','body':'Synthetic reason for sharing this question'})
    assert r.status_code==201,r.text;iid=r.json()['id']
    synthetic={'desk_id':did,'id':'no-members-synthetic','selection_context':{'desk_sources':[{'item_id':iid,'question_id':'cq_test'}]}}
    run(client,desk_games.access,synthetic,'author')
    restrict(c,'outsider','under18');monkeypatch.setattr(settings,'audience_gate_enabled',True)
    with pytest.raises(HTTPException) as error:run(client,desk_games.access,synthetic,'author')
    assert error.value.status_code==404


def test_inbox_preview_rechecks_linked_note_subject_without_leaking_reference(client,actor,database,desk_setup,monkeypatch):
    c=database[1];did=room(client,actor);join(client,actor,did);join(client,actor,did,'reviewer1')
    r=client.post(f'/api/desk/rooms/{did}/items',headers={**actor('outsider'),'Idempotency-Key':uuid4().hex},json={'kind':'note','title':'Restricted shared source','body':'Synthetic restricted note body','question_id':'cq_test'})
    assert r.status_code==201,r.text;iid=r.json()['id']
    r=client.post(f'/api/desk/rooms/{did}/messages',headers={**actor('reviewer1'),'Idempotency-Key':uuid4().hex},json={'body':'LINKED_PREVIEW_MARKER','note_id':iid})
    assert r.status_code==201,r.text
    restrict(c,'outsider','under18');actor('author');monkeypatch.setattr(settings,'audience_gate_enabled',True)
    r=client.get('/api/inbox/threads');assert r.status_code==200,r.text
    assert 'LINKED_PREVIEW_MARKER' not in r.text and '_note_id' not in r.text
    assert r.json()['items'][0]['last_message']=='Linked note is unavailable or assessment-locked.'


@pytest.mark.parametrize('category',[None,'under18','closed'])
def test_both_cup_boards_filter_subject_before_ranking_without_rewriting_results(client,actor,database,game_case,monkeypatch,category):
    from datetime import datetime,timezone
    c,rid,users,headers,rows=room_case(client,game_case,'cup')
    cid,opens,closes=games.cup_window(datetime.now(timezone.utc))
    c.execute('INSERT INTO game_cups(id,opens_at,closes_at,questions) VALUES(%s,%s,%s,%s)',(cid,opens,closes,Jsonb(rows)))
    finished='cup-visibility-'+uuid4().hex
    c.execute("INSERT INTO game_rooms(id,owner_id,mode,capacity,cup_id,questions,round_seconds,request_key,request_hash,state,finished_at) SELECT %s,owner_id,mode,capacity,%s,questions,round_seconds,%s,request_hash,'finished',now() FROM game_rooms WHERE id=%s",(finished,cid,finished,rid))
    c.execute('INSERT INTO game_members(room_id,user_id,score,correct,elapsed_ms,public_result,released_at) VALUES(%s,%s,100,5,5000,true,now())',(finished,users[0]))
    c.execute('INSERT INTO game_cup_entries(cup_id,user_id,room_id) VALUES(%s,%s,%s)',(cid,users[0],finished))
    c.execute("INSERT INTO account_audience(user_id,category) VALUES(%s,'adult')",(users[1],))
    client.cookies.clear();monkeypatch.setattr(settings,'audience_gate_enabled',True)
    paths=['/api/games/cup/board?cup_id='+cid,'/api/games/leaderboard?track=cup']
    for path in paths:
        r=client.get(path,headers=headers[1]);assert r.status_code==200,r.text
        assert len(r.json()['items'])==1
    saved=c.execute('SELECT * FROM game_members WHERE room_id=%s',(finished,)).fetchone()
    restrict(c,users[0],category)
    for path in paths:
        r=client.get(path,headers=headers[1]);assert r.status_code==200,r.text
        assert r.json()['items']==[]
    assert c.execute('SELECT * FROM game_members WHERE room_id=%s',(finished,)).fetchone()==saved
