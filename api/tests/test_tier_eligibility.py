"""Database policy, immutable tiers and complete voter admission; isolated real roles."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from uuid import uuid4
import psycopg
import pytest
from psycopg.types.json import Jsonb
from app.config import settings
from app.services import audience
from test_discussions import database,client
from test_synchronous_activity_audience import manual_workers,role,execute,restrict
from test_account_privacy import declare
from test_learning_eligibility import wait_for_advisory_wait
from test_community_people import public


@pytest.fixture(autouse=True)
def enabled_policy(client,database,monkeypatch):
    c=database[1]
    c.execute("INSERT INTO account_audience(user_id,category) SELECT id,'adult' FROM users ON CONFLICT DO NOTHING")
    c.execute('UPDATE audience_processing_policy SET enabled=true')
    monkeypatch.setattr(settings,'audience_gate_enabled',True)
    from app.routers import community,creators
    for module in (community,creators):monkeypatch.setattr(module,'cursor',role)
    yield
    c.execute('UPDATE audience_processing_policy SET enabled=false')


def new_voter(c,prefix='tier-voter-',category='adult'):
    u=prefix+uuid4().hex
    c.execute('INSERT INTO users(id,handle,email) VALUES(%s,%s,%s)',(u,u,u+'@example.test'))
    if category:c.execute('INSERT INTO account_audience(user_id,category) VALUES(%s,%s)',(u,category))
    return u


def vote(c,pid,user):
    execute(c,'INSERT INTO post_votes(post_id,user_id,weight) VALUES(%s,%s,9999) ON CONFLICT DO NOTHING',(pid,user))


def graph(c,n=39,user='author'):
    pid=c.execute("INSERT INTO posts(kind,author_id,body) VALUES('study',%s,'Synthetic tier admission fixture') RETURNING id",(user,)).fetchone()[0]
    voters=[]
    for _ in range(n):
        u=new_voter(c);vote(c,pid,u);voters.append(u)
    return pid,voters


def score(c,user='author'):
    return float(execute(c,'SELECT community_weighted_helpful(%s)',(user,))[0][0])


def events(c):
    return c.execute("SELECT * FROM creator_events WHERE action='community_tier_earned' ORDER BY id").fetchall()


def rank(c,user='author'):
    return execute(c,'SELECT community_display_tier_rank(%s)',(user,))[0][0]


def lock(c,user):
    c.execute("SELECT pg_advisory_xact_lock(hashtextextended('audience-learning-processing-v1:'||%s,0))",(user,))


def unknown_or_closed(c,user,value):
    if value=='email_missing':c.execute('UPDATE users SET email=NULL WHERE id=%s',(user,))
    else:restrict(c,user,value)


@pytest.mark.parametrize('value',[None,'under18','closed','email_missing'])
def test_restricted_target_current_weight_is_zero_and_source_votes_do_not_award(client,database,value):
    c=database[1];unknown_or_closed(c,'author',value);pid,users=graph(c,40)
    assert score(c)==0 and rank(c)==0 and events(c)==[]
    assert c.execute('SELECT count(*) FROM post_votes WHERE post_id=%s',(pid,)).fetchone()==(40,)
    assert c.execute('SELECT count(*) FROM reward_ledger').fetchone()==(0,)


@pytest.mark.parametrize('value',[None,'under18','closed','email_missing'])
def test_restricted_voter_is_excluded_and_existing_milestones_remain(client,database,value):
    c=database[1];pid,users=graph(c,40);original=events(c)
    assert score(c)==10 and rank(c)==1 and len(original)==1
    unknown_or_closed(c,users[0],value)
    assert score(c)==9.75 and rank(c)==1 and events(c)==original
    assert c.execute('SELECT count(*) FROM post_votes WHERE post_id=%s',(pid,)).fetchone()==(40,)


@pytest.mark.parametrize('n,expected',[(40,1),(100,2),(200,3),(600,4)])
def test_live_thresholds_replay_and_maximum_label_have_unique_monotonic_history(client,database,n,expected):
    c=database[1];pid,users=graph(c,n)
    assert score(c)==n/4 and rank(c)==expected
    before=events(c)
    vote(c,pid,users[-1])
    execute(c,'UPDATE post_votes SET weight=12345 WHERE post_id=%s',(pid,))
    assert events(c)==before
    assert c.execute("SELECT count(DISTINCT detail->>'rank'),count(*) FROM creator_events WHERE action='community_tier_earned' AND target_id='author'").fetchone()==(expected,expected)
    assert c.execute('SELECT count(*) FROM reward_ledger').fetchone()==(0,)


@pytest.mark.parametrize('value',[None,'under18'])
def test_policy_off_retains_legacy_weights_and_default_trigger_behavior(client,database,monkeypatch,value):
    c=database[1];c.execute('UPDATE audience_processing_policy SET enabled=false');monkeypatch.setattr(settings,'audience_gate_enabled',False)
    unknown_or_closed(c,'author',value);pid,users=graph(c,40)
    unknown_or_closed(c,users[0],value)
    assert score(c)==10 and rank(c)==1 and len(events(c))==1


def test_busy_target_does_not_wait_for_tier_mutex_or_block_source(client,database):
    name,c=database;pid,users=graph(c);last=new_voter(c)
    with psycopg.connect('dbname='+name) as held:
        lock(held,'author');held.execute("SELECT pg_advisory_xact_lock(hashtextextended('community-tier:author',0))")
        c.execute("SET statement_timeout='3s'")
        try:vote(c,pid,last)
        finally:c.execute('RESET statement_timeout')
    assert score(c)==10 and rank(c)==1 and events(c)==[]


def test_busy_voter_suppresses_whole_capture_and_releases_new_partial_leases(client,database):
    name,c=database;pid,users=graph(c);last=new_voter(c)
    first,last_busy=sorted(users)[0],sorted(users)[-1]
    with psycopg.connect('dbname='+name) as busy:
        lock(busy,last_busy)
        with psycopg.connect('dbname='+name) as writer:
            writer.execute('SET LOCAL ROLE mpsc')
            writer.execute('INSERT INTO post_votes(post_id,user_id,weight) VALUES(%s,%s,9999)',(pid,last))
            assert events(writer)==[]
            with psycopg.connect('dbname='+name) as probe:
                assert probe.execute("SELECT pg_try_advisory_xact_lock(hashtextextended('audience-learning-processing-v1:'||%s,0))",(first,)).fetchone()==(True,)
    assert score(c)==10 and events(c)==[]
    # A read may display current standing; it must not persist a delayed award.
    assert rank(c)==1 and events(c)==[]
    execute(c,'DELETE FROM post_votes WHERE post_id=%s AND user_id=%s',(pid,last))
    assert score(c)==9.75 and rank(c)==1 and len(events(c))==1


@pytest.mark.parametrize('loss',['unvote','hidden','pending','before_fix','block','closed_voter','under18_voter','missing_voter','under18_author','missing_author','closed_author'])
def test_before_loss_capture_retains_previously_unrecorded_eligible_label(client,database,loss):
    name,c=database;pid,users=graph(c);last=new_voter(c)
    with psycopg.connect('dbname='+name) as busy:
        lock(busy,users[0]);vote(c,pid,last)
    assert score(c)==10 and events(c)==[]
    if loss=='unvote':execute(c,'DELETE FROM post_votes WHERE post_id=%s AND user_id=%s',(pid,last))
    elif loss in ('hidden','pending','before_fix'):execute(c,'UPDATE posts SET '+('needs_approval' if loss=='pending' else loss)+'=true WHERE id=%s',(pid,))
    elif loss=='block':execute(c,"INSERT INTO creator_blocks(user_id,blocked_id) VALUES('author',%s)",(last,))
    else:
        who='author' if loss.endswith('author') else last
        value='closed' if loss.startswith('closed') else None if loss.startswith('missing') else 'under18'
        unknown_or_closed(c,who,value)
    assert score(c)<10 and rank(c)==1 and len(events(c))==1


@pytest.mark.parametrize('loss',['delete','canonical','correct'])
def test_maturity_gain_and_loss_use_actual_attempts_not_stored_weight(client,database,loss):
    c=database[1];pid,users=graph(c)
    u=users[0]
    c.execute("INSERT INTO attempts(user_id,canonical_id,correct,context) SELECT %s,'cq_test',false,'practice' FROM generate_series(1,49)",(u,))
    assert score(c)==9.75 and events(c)==[]
    aid=execute(c,"INSERT INTO attempts(user_id,canonical_id,correct,context) VALUES(%s,'cq_test',false,'practice') RETURNING id",(u,))[0][0]
    assert score(c)==10.5 and rank(c)==1
    old=events(c)
    if loss=='canonical':
        execute(c,'UPDATE attempts SET canonical_id=NULL WHERE id=%s',(aid,))
        assert score(c)==9.75
    elif loss=='delete':
        # The app role cannot delete study roots; the definer sweeper owns that path.
        with pytest.raises(psycopg.errors.InsufficientPrivilege):execute(c,'DELETE FROM attempts WHERE id=%s',(aid,))
        assert score(c)==10.5
    else:
        with pytest.raises(psycopg.errors.NotNullViolation):execute(c,'UPDATE attempts SET correct=NULL WHERE id=%s',(aid,))
        assert score(c)==10.5
    assert rank(c)==1 and events(c)==old


@pytest.mark.parametrize('who',['author','voter'])
def test_admitted_milestone_prevents_raw_restriction_until_commit(client,database,who):
    name,c=database;pid,users=graph(c);last=new_voter(c)
    with psycopg.connect('dbname='+name) as writer:
        writer.execute('SET LOCAL ROLE mpsc');writer.execute('INSERT INTO post_votes(post_id,user_id,weight) VALUES(%s,%s,1)',(pid,last))
        with pytest.raises(psycopg.errors.LockNotAvailable):restrict(c,'author' if who=='author' else users[0],'under18')
    restrict(c,'author' if who=='author' else users[0],'under18')
    assert rank(c)==1 and len(events(c))==1


def test_admitted_capture_serializes_api_voter_restriction_before_rows(client,database,actor):
    c=database[1];pid,users=graph(c,38);vote(c,pid,'outsider');last=new_voter(c);h=actor('outsider')
    async def scenario():
        async with role() as held:
            await held.execute('INSERT INTO post_votes(post_id,user_id,weight) VALUES(%s,%s,1)',(pid,last))
            task=asyncio.create_task(asyncio.to_thread(declare,client,'under18',headers=h,user_id='outsider',expected_version=1))
            try:await wait_for_advisory_wait(held,task)
            except BaseException:task.cancel();await asyncio.gather(task,return_exceptions=True);raise
        response=await asyncio.wait_for(task,5);assert response.status_code==200,response.text
    client.portal.call(scenario)
    assert score(c)==9.75 and rank(c)==1 and len(events(c))==1


def test_independent_sql_votes_serialize_milestones_without_duplicate_labels(client,database):
    name,c=database;pid,users=graph(c,38);more=[new_voter(c) for _ in range(4)]
    def writer(u):
        with psycopg.connect('dbname='+name) as conn:
            conn.execute('SET LOCAL ROLE mpsc');conn.execute('INSERT INTO post_votes(post_id,user_id,weight) VALUES(%s,%s,1)',(pid,u))
    with ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(writer,more))
    assert score(c)==10.5 and rank(c)==1 and len(events(c))==1


def test_policy_is_database_wide_missing_fails_closed_and_session_guc_cannot_bypass(client,database):
    c=database[1];pid,users=graph(c,40);restrict(c,users[0],'under18')
    with c.transaction():
        c.execute('SET LOCAL ROLE mpsc');c.execute("SET LOCAL finna.audience_gate_enabled='off'")
        assert float(c.execute("SELECT community_weighted_helpful('author')").fetchone()[0])==9.75
    c.execute('DELETE FROM audience_processing_policy')
    with pytest.raises(psycopg.errors.RaiseException,match='policy is missing'):score(c)
    with pytest.raises(psycopg.errors.RaiseException,match='policy is missing'):vote(c,pid,new_voter(c))
    c.execute('INSERT INTO audience_processing_policy(singleton,enabled) VALUES(true,true)')


def test_read_only_standing_guides_profiles_preserve_history_and_filter_current_weight(client,database,actor,monkeypatch):
    from app.db import cursor
    from app.routers import community,creators
    c=database[1];pid,users=graph(c,600);public(c);actor('outsider')
    @asynccontextmanager
    async def readonly():
        async with cursor() as cur:
            await cur.execute('SET TRANSACTION READ ONLY');await cur.execute('SET LOCAL ROLE mpsc');yield cur
    for module in (community,creators):monkeypatch.setattr(module,'cursor',readonly)
    original=events(c)
    assert client.get('/api/community/guides').json()['items'][0]['id']=='author'
    restrict(c,users[0],'under18')
    assert client.get('/api/community/guides').json()['items']==[]
    assert client.get('/api/creators/author').json()['community']['display_tier']=='Guide'
    actor('author');r=client.get('/api/community/standing');assert r.status_code==200,r.text
    assert r.json()['weighted_helpful']==149.75 and r.json()['display_tier']=='Guide' and r.json()['tier']=='Mentor'
    assert events(c)==original


def test_real_role_cannot_forge_call_or_rewrite_milestones(client,database):
    c=database[1];graph(c,40)
    for query,args in [('SELECT community_record_tier(%s)',('author',)),
      ("INSERT INTO creator_events(actor_id,action,target_id,detail) VALUES('author','community_tier_earned','author',%s)",(Jsonb({'rank':4}),)),
      ("DELETE FROM creator_events WHERE action='community_tier_earned'",()),
      ("UPDATE creator_events SET detail='{}' WHERE action='community_tier_earned'",())]:
        with pytest.raises(psycopg.errors.InsufficientPrivilege):execute(c,query,args)


def test_application_temp_relations_cannot_forge_server_owned_tier(client,database):
    c=database[1];pid,users=graph(c);last=new_voter(c)
    with c.transaction():
        c.execute('SET LOCAL ROLE mpsc')
        c.execute('CREATE TEMP TABLE post_votes AS SELECT * FROM public.post_votes WITH NO DATA')
        c.execute('INSERT INTO pg_temp.post_votes SELECT v.* FROM public.post_votes v CROSS JOIN generate_series(1,1000) WHERE v.user_id=%s',(users[0],))
        c.execute('INSERT INTO public.post_votes(post_id,user_id,weight) VALUES(%s,%s,1)',(pid,last))
        result=c.execute("SELECT max((detail->>'rank')::int) FROM public.creator_events WHERE action='community_tier_earned' AND target_id='author'").fetchone()[0]
        assert result==1,'A temporary vote table must not turn a real Helper threshold into a forged higher tier'


@pytest.mark.parametrize('who',['author','voter'])
def test_admitted_capture_requires_direct_closure_to_retry_without_tier_deadlock(client,database,who):
    name,c=database;pid,users=graph(c);last=new_voter(c);target='author' if who=='author' else users[0]
    with psycopg.connect('dbname='+name) as writer:
        writer.execute('SET LOCAL ROLE mpsc');writer.execute('INSERT INTO post_votes(post_id,user_id,weight) VALUES(%s,%s,1)',(pid,last))
        c.execute("SET statement_timeout='3s'")
        try:
            with pytest.raises(psycopg.errors.LockNotAvailable):restrict(c,target,'closed')
        finally:c.execute('RESET statement_timeout')
    restrict(c,target,'closed')
    assert rank(c)==1 and len(events(c))==1


@pytest.mark.parametrize('target',['author','outsider'])
def test_admitted_capture_serializes_full_account_closure(client,database,target):
    from app.services import account_tools
    c=database[1];pid,users=graph(c,38);vote(c,pid,'outsider');last=new_voter(c)
    version=c.execute('SELECT identity_version FROM users WHERE id=%s',(target,)).fetchone()[0]
    async def closing():
        async with role() as other:return await account_tools.close(other,target,version)
    async def scenario():
        async with role() as held:
            await held.execute('INSERT INTO post_votes(post_id,user_id,weight) VALUES(%s,%s,1)',(pid,last))
            task=asyncio.create_task(closing())
            try:await wait_for_advisory_wait(held,task)
            except BaseException:task.cancel();await asyncio.gather(task,return_exceptions=True);raise
        assert await asyncio.wait_for(task,5)=={'closed':True}
    client.portal.call(scenario)
    assert c.execute('SELECT closed_at IS NOT NULL FROM users WHERE id=%s',(target,)).fetchone()==(True,)
    assert rank(c)==1 and len(events(c))==1


@pytest.mark.parametrize('category',['under18',None])
def test_restricted_voter_maturity_change_cannot_add_target_milestone(client,database,category):
    c=database[1];pid,users=graph(c);u=users[0];restrict(c,u,category)
    c.execute("INSERT INTO attempts(user_id,canonical_id,correct,context) SELECT %s,'cq_test',false,'practice' FROM generate_series(1,50)",(u,))
    assert score(c)==9.5 and events(c)==[]


def test_busy_maturity_subject_does_not_wait_for_author_tier_lock(client,database):
    name,c=database;pid,users=graph(c);u=users[0]
    c.execute("INSERT INTO attempts(user_id,canonical_id,correct,context) SELECT %s,'cq_test',false,'practice' FROM generate_series(1,49)",(u,))
    with psycopg.connect('dbname='+name) as held:
        lock(held,u);held.execute("SELECT pg_advisory_xact_lock(hashtextextended('community-tier:author',0))")
        c.execute("SET statement_timeout='3s'")
        try:execute(c,"INSERT INTO attempts(user_id,canonical_id,correct,context) VALUES(%s,'cq_test',false,'practice')",(u,))
        finally:c.execute('RESET statement_timeout')
    assert score(c)==10.5 and events(c)==[]
