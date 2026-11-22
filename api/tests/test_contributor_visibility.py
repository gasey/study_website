"""Real-role public reads; stored bank, credits, votes and milestones stay intact."""
from contextlib import asynccontextmanager
import pytest
from psycopg.types.json import Jsonb
from app.config import settings
from app.db import cursor
from app.services import community_people
from test_discussions import database,client,question,answer
from test_community_eligibility import restrict,post,manual_workers
from test_contribution_rewards_v2 import publication,credit


@asynccontextmanager
async def role():
    async with cursor() as cur:
        await cur.execute('SET LOCAL ROLE mpsc')
        yield cur


@pytest.fixture(autouse=True)
def real_readers(client,database,monkeypatch):
    from app.routers import bank_workspace,community,discussions,study_posts
    for module in (bank_workspace,community,discussions,study_posts):monkeypatch.setattr(module,'cursor',role)
    monkeypatch.setattr(settings,'audience_gate_enabled',False)
    database[1].execute("INSERT INTO account_audience(user_id,category) SELECT id,'adult' FROM users ON CONFLICT DO NOTHING")


def restriction(c,user,category):
    if category=='email_missing':c.execute('UPDATE users SET email=NULL WHERE id=%s',(user,))
    else:restrict(c,user,category)


def contribution(c,user='author',*,points=10,age=0):
    cid,pid=publication(c,user,reviewers=())
    credit(c,user,cid,pid,amount=points)
    c.execute("UPDATE bank_contributions SET updated_at=now()-make_interval(days=>%s) WHERE id=%s",(age,cid))
    return cid


def board(client,**params):
    r=client.get('/api/community/contributors',params=params)
    assert r.status_code==200,r.text
    assert r.headers['cache-control']=='private, no-store'
    return r.json()


def published(client,**params):
    r=client.get('/api/community/contributions',params=params)
    assert r.status_code==200,r.text
    assert r.headers['cache-control']=='private, no-store'
    return r.json()


@pytest.mark.parametrize('category',[None,'under18','closed','email_missing'])
@pytest.mark.parametrize('period',['week','month','all'])
def test_rank_filter_precedes_dense_rank_and_limit_and_retains_history(client,actor,database,monkeypatch,category,period):
    c=database[1];contribution(c,points=20);good=contribution(c,'reviewer1')
    before=c.execute('SELECT * FROM contribution_credit ORDER BY id').fetchall()
    bank=c.execute('SELECT * FROM canonical_questions ORDER BY id').fetchall()
    restriction(c,'author',category);actor('outsider');monkeypatch.setattr(settings,'audience_gate_enabled',True)
    rows=board(client,period=period,limit=1,subject_id='english')
    assert len(rows)==1 and rows[0]['id']=='reviewer1' and rows[0]['rank']==1 and rows[0]['credit']==10
    assert board(client,period=period,subject_id='mizo')==[]
    assert c.execute('SELECT * FROM contribution_credit ORDER BY id').fetchall()==before
    assert c.execute('SELECT * FROM canonical_questions ORDER BY id').fetchall()==bank
    assert c.execute('SELECT state FROM bank_contributions WHERE id=%s',(good,)).fetchone()==('published',)
    monkeypatch.setattr(settings,'audience_gate_enabled',False)
    assert board(client,period=period,limit=1)[0]['id']==('reviewer1' if category=='closed' else 'author')


@pytest.mark.parametrize('reverse',[False,True])
def test_rank_blocks_are_proved_viewer_specific_and_anonymous_read_creates_nothing(client,actor,database,monkeypatch,reverse):
    c=database[1];contribution(c,points=20);contribution(c,'reviewer1')
    a,b=('author','outsider') if reverse else ('outsider','author')
    c.execute('INSERT INTO creator_blocks(user_id,blocked_id) VALUES(%s,%s)',(a,b))
    actor('outsider');monkeypatch.setattr(settings,'audience_gate_enabled',True)
    assert [r['id'] for r in board(client,limit=1)]==['reviewer1']
    client.cookies.clear();before=c.execute('SELECT count(*) FROM users').fetchone()
    r=client.get('/api/community/contributors',headers={'X-Device-Id':'outsider'})
    assert r.status_code==200 and r.json()[0]['id']=='author' and 'set-cookie' not in r.headers
    assert c.execute('SELECT count(*) FROM users').fetchone()==before


@pytest.mark.parametrize('category',[None,'under18','closed','email_missing'])
def test_published_author_filter_precedes_cursor_and_keeps_anonymous_consent(client,actor,database,monkeypatch,category):
    c=database[1];older=contribution(c,'reviewer1',age=2);newer=contribution(c,'reviewer2',age=1);hidden=contribution(c)
    c.execute("UPDATE users SET contribution_public=false WHERE id='reviewer1'")
    saved=c.execute('SELECT * FROM bank_contributions ORDER BY id').fetchall()
    restriction(c,'author',category);actor('outsider');monkeypatch.setattr(settings,'audience_gate_enabled',True)
    page=published(client,limit=1);assert [x['id'] for x in page['items']]==[newer] and page['next_cursor']==newer
    page=published(client,limit=1,before=newer)
    assert [x['id'] for x in page['items']]==[older] and page['next_cursor'] is None
    assert page['items'][0]['author']=='Anonymous contributor'
    assert hidden not in [r['id'] for r in published(client)['items']]
    assert c.execute('SELECT * FROM bank_contributions ORDER BY id').fetchall()==saved
    assert client.get('/api/questions/cq_test').status_code==200


@pytest.mark.parametrize('reverse',[False,True])
def test_published_blocks_hide_work_and_reject_new_vote_but_allow_own_unvote(client,actor,database,monkeypatch,reverse):
    c=database[1];cid=contribution(c)
    c.execute("INSERT INTO contribution_votes(user_id,contribution_id) VALUES('outsider',%s)",(cid,))
    a,b=('author','outsider') if reverse else ('outsider','author')
    c.execute('INSERT INTO creator_blocks(user_id,blocked_id) VALUES(%s,%s)',(a,b))
    h=actor('outsider');monkeypatch.setattr(settings,'audience_gate_enabled',True)
    assert published(client)['items']==[]
    assert client.post(f'/api/contributions/{cid}/vote',headers=h).status_code==404
    assert client.post(f'/api/contributions/{cid}/unvote',headers=h).status_code==200
    assert c.execute('SELECT count(*) FROM contribution_votes WHERE contribution_id=%s',(cid,)).fetchone()==(0,)


@pytest.mark.parametrize('category',[None,'under18','closed','email_missing'])
def test_legacy_votes_exclude_restricted_subject_and_preserve_own_vote_state(client,actor,database,monkeypatch,category):
    c=database[1];cid=contribution(c)
    for u in ('reviewer1','reviewer2','outsider'):c.execute('INSERT INTO contribution_votes(user_id,contribution_id) VALUES(%s,%s)',(u,cid))
    original=c.execute('SELECT * FROM contribution_votes ORDER BY user_id').fetchall()
    restriction(c,'reviewer1',category);actor('outsider');monkeypatch.setattr(settings,'audience_gate_enabled',True)
    row=published(client)['items'][0];assert row['helpful']==2 and row['voted']
    assert c.execute('SELECT * FROM contribution_votes ORDER BY user_id').fetchall()==original
    monkeypatch.setattr(settings,'audience_gate_enabled',False)
    assert published(client)['items'][0]['helpful']==3


@pytest.mark.parametrize('reverse',[False,True])
def test_legacy_vote_counts_keep_author_voter_blocks(client,actor,database,monkeypatch,reverse):
    c=database[1];cid=contribution(c)
    for u in ('reviewer1','reviewer2'):c.execute('INSERT INTO contribution_votes(user_id,contribution_id) VALUES(%s,%s)',(u,cid))
    a,b=('author','reviewer1') if reverse else ('reviewer1','author')
    c.execute('INSERT INTO creator_blocks(user_id,blocked_id) VALUES(%s,%s)',(a,b))
    actor('outsider');monkeypatch.setattr(settings,'audience_gate_enabled',True)
    assert published(client)['items'][0]['helpful']==1


@pytest.mark.parametrize('category',[None,'under18','closed','email_missing'])
def test_new_legacy_vote_rejects_restricted_author_and_old_unvote_remains(client,actor,database,monkeypatch,category):
    c=database[1];cid=contribution(c)
    c.execute("INSERT INTO contribution_votes(user_id,contribution_id) VALUES('outsider',%s)",(cid,))
    restriction(c,'author',category);h=actor('outsider');monkeypatch.setattr(settings,'audience_gate_enabled',True)
    assert client.post(f'/api/contributions/{cid}/vote',headers=h).status_code==404
    assert client.post(f'/api/contributions/{cid}/unvote',headers=h).status_code==200


@pytest.mark.parametrize('protection',['mock','game','cup'])
def test_legacy_titles_keep_mock_and_game_disclosure_protection(client,actor,database,monkeypatch,protection):
    c=database[1];contribution(c);actor('outsider');monkeypatch.setattr(settings,'audience_gate_enabled',True)
    assert len(published(client)['items'])==1
    if protection=='mock':
        c.execute("INSERT INTO collections(id,title,kind,visibility) VALUES('protect','Synthetic mock','exam','public')")
        c.execute("INSERT INTO mock_sessions(id,user_id,collection_id,question_ids,duration_seconds) VALUES('protect','outsider','protect',ARRAY['cq_test'],600)")
    else:
        cup='protect-cup' if protection=='cup' else None
        if cup:c.execute("INSERT INTO game_cups(id,opens_at,closes_at,questions) VALUES(%s,now()-interval '1 hour',now()+interval '1 hour',%s)",(cup,Jsonb([{'id':'cq_test'}])))
        c.execute("INSERT INTO game_rooms(id,owner_id,mode,capacity,questions,round_seconds,request_key,request_hash,cup_id) VALUES('protect','outsider',%s,1,%s,30,'protect','fixture',%s)",('cup' if cup else 'gauntlet',Jsonb([{'id':'cq_test'}]),cup))
        c.execute("INSERT INTO game_members(room_id,user_id,released_at) VALUES('protect','outsider',CASE WHEN %s THEN now() END)",(bool(cup),))
    assert published(client)['items']==[]


@pytest.mark.parametrize('category',[None,'under18','closed','email_missing'])
def test_post_vote_counts_use_fresh_flag_across_feed_direct_thread_and_public_stats(client,actor,question,monkeypatch,category):
    q,c=question;sid=post(c);did=post(c,kind='doubt',qid=q)
    for pid in (sid,did):
        for u in ('reviewer1','reviewer2'):c.execute('INSERT INTO post_votes(post_id,user_id,weight) VALUES(%s,%s,9999)',(pid,u))
    answer(client,actor,q,'outsider');original=c.execute('SELECT * FROM post_votes ORDER BY post_id,user_id').fetchall()
    restriction(c,'reviewer1',category);monkeypatch.setattr(settings,'audience_gate_enabled',True)
    for _ in range(2):
        feed=client.get('/api/community/feed?content_version=2').json()['items']
        assert {r['id']:r['helpful'] for r in feed if r['id'] in (sid,did)}=={sid:1,did:1}
        assert client.get(f'/api/community/study-posts/{sid}').json()['helpful']==1
        thread=client.get(f'/api/community/questions/{q}/discussion').json()['items'];assert thread[0]['helpful']==1
        async def stats():
            async with role() as cur:return await community_people.visible_stats(cur,['author'],'outsider')
        assert client.portal.call(stats)['author']['helpful_count']==2
    assert c.execute('SELECT * FROM post_votes ORDER BY post_id,user_id').fetchall()==original
    monkeypatch.setattr(settings,'audience_gate_enabled',False)
    expected=1 if category in ('closed','email_missing') else 2
    assert client.get(f'/api/community/study-posts/{sid}').json()['helpful']==expected


def test_visible_weight_ignores_restricted_mature_voter_without_changing_milestones(client,actor,database,monkeypatch):
    c=database[1];sid=post(c)
    for u in ('reviewer1','reviewer2'):c.execute('INSERT INTO post_votes(post_id,user_id,weight) VALUES(%s,%s,9999)',(sid,u))
    c.execute("INSERT INTO attempts(user_id,canonical_id,chosen_text,correct,context) SELECT 'reviewer1','cq_test','A',false,'practice' FROM generate_series(1,50)")
    restriction(c,'reviewer1','under18');actor('outsider');monkeypatch.setattr(settings,'audience_gate_enabled',True)
    before=c.execute('SELECT * FROM creator_events ORDER BY id').fetchall()
    async def stats():
        async with role() as cur:return await community_people.visible_stats(cur,['author'],'outsider')
    row=client.portal.call(stats)['author'];assert row['weekly_weighted']==.25 and row['helpful_count']==row['weekly_helpful']==1
    assert c.execute('SELECT * FROM creator_events ORDER BY id').fetchall()==before


def test_read_only_real_role_readers_and_http_gets_write_no_history(client,actor,database,monkeypatch):
    from app.routers import bank_workspace,community,study_posts
    c=database[1];cid=contribution(c);sid=post(c);actor('outsider');monkeypatch.setattr(settings,'audience_gate_enabled',True)
    @asynccontextmanager
    async def read_only():
        async with cursor() as cur:
            await cur.execute('SET TRANSACTION READ ONLY');await cur.execute('SET LOCAL ROLE mpsc');yield cur
    for module in (bank_workspace,community,study_posts):monkeypatch.setattr(module,'cursor',read_only)
    before=c.execute('SELECT * FROM creator_events ORDER BY id').fetchall()
    assert board(client)[0]['id']=='author'
    assert published(client)['items'][0]['id']==cid
    assert client.get(f'/api/community/study-posts/{sid}').status_code==200
    assert client.get('/api/community/feed?content_version=2').status_code==200
    assert c.execute('SELECT * FROM creator_events ORDER BY id').fetchall()==before
