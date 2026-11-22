"""Prospective CMS rewards/workflow notices; source and integrity records stay."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
import psycopg
from psycopg.types.json import Jsonb
import pytest
from app.config import settings
from app.services import content_studio as cms,audience,bank_review,account_tools
from test_discussions import database,client
from test_content_studio import create,document
from test_synchronous_activity_audience import manual_workers,role,execute,restrict
from test_account_privacy import declare
from test_learning_eligibility import wait_for_advisory_wait
from test_publication_eligibility import acknowledgement,paid,reversal
from test_contribution_rewards_v2 import publication


@pytest.fixture(autouse=True)
def enabled_policy(client,database,monkeypatch):
    from app.routers import materials,bank_workspace
    c=database[1];c.execute("INSERT INTO account_audience(user_id,category) SELECT id,'adult' FROM users")
    c.execute('UPDATE audience_processing_policy SET enabled=true')
    monkeypatch.setattr(settings,'audience_gate_enabled',True)
    monkeypatch.setattr(materials,'cursor',role);monkeypatch.setattr(bank_workspace,'cursor',role)
    yield
    c.execute('UPDATE audience_processing_policy SET enabled=false')


def submitted(client,actor,doc=None,user='author'):
    mid,h,_=create(client,actor,doc,user)
    r=client.post('/api/studio/materials/'+mid+'/submit',headers=h,json={'expected_version':1});assert r.status_code==200,r.text
    return mid


def decision(client,h,mid,kind='publish',version=2):
    r=client.post('/api/admin/bank/content/'+mid+'/review',headers=h,json={'expected_version':version,'decision':kind,'reason':'Synthetic exact revision workflow test'})
    assert r.status_code==200,r.text
    return r


def ledger(c):return c.execute("SELECT * FROM reward_ledger WHERE user_id='author' ORDER BY id").fetchall()
def notices(c):return c.execute("SELECT * FROM review_notifications WHERE user_id='author' ORDER BY id").fetchall()


def direct_notice(c,kind,entity,key=None,user='author'):
    column='material_id' if kind=='material' else 'contribution_id'
    return execute(c,'INSERT INTO review_notifications(user_id,'+column+',event_key,message) VALUES(%s,%s,%s,%s) RETURNING id',
      (user,entity,key or uuid4().hex,'Synthetic optional workflow notice'))


def entity(client,actor,c,kind):
    return submitted(client,actor) if kind=='material' else publication(c,'author',reviewers=())[0]


def run(client,fn,*args):
    async def call():
        async with role() as cur:return await fn(cur,*args)
    return client.portal.call(call)


@pytest.mark.parametrize('value',[None,'under18','closed'])
def test_restricted_cms_publication_keeps_source_and_audit_without_reward_or_notice(client,actor,database,value):
    c=database[1];mid=submitted(client,actor);history=c.execute('SELECT * FROM material_revisions WHERE material_id=%s',(mid,)).fetchall()
    restrict(c,'author',value);h=actor('owner');decision(client,h,mid)
    assert c.execute('SELECT status,workflow_state,published_revision,lock_version FROM materials WHERE id=%s',(mid,)).fetchone()==('published','published',1,3)
    assert c.execute('SELECT * FROM material_revisions WHERE material_id=%s',(mid,)).fetchall()==history
    assert c.execute("SELECT count(*) FROM material_events WHERE material_id=%s AND action='publish'",(mid,)).fetchone()==(1,)
    assert c.execute('SELECT count(*) FROM material_reward_claims WHERE material_id=%s',(mid,)).fetchone()==(0,)
    assert ledger(c)==[] and notices(c)==[]
    assert client.get('/api/materials/'+mid).status_code==404
    # Authorized governance access remains; recipient visibility is separate.
    assert any(x['id']==mid for x in client.get('/api/admin/bank/content?state=all').json()['items'])


@pytest.mark.parametrize('value',[None,'under18'])
def test_skipped_cms_first_publication_cannot_replay_after_confirmation_or_flag_off(client,actor,database,monkeypatch,value):
    c=database[1];mid=submitted(client,actor);restrict(c,'author',value);h=actor('owner');decision(client,h,mid)
    c.execute("INSERT INTO account_audience(user_id,category) VALUES('author','adult') ON CONFLICT(user_id) DO UPDATE SET category='adult'")
    assert client.post('/api/admin/bank/content/'+mid+'/review',headers=h,json={'expected_version':2,'decision':'publish'}).status_code==409
    # A genuine later revision may publish, but it is not a first publication.
    h=actor('author');assert client.post('/api/studio/materials/'+mid+'/save',headers=h,json={'expected_version':3,'document':document()}).status_code==200
    assert client.post('/api/studio/materials/'+mid+'/submit',headers=h,json={'expected_version':4}).status_code==200
    h=actor('owner');decision(client,h,mid,version=5)
    assert ledger(c)==[] and c.execute('SELECT count(*) FROM material_reward_claims WHERE material_id=%s',(mid,)).fetchone()==(0,)
    c.execute('UPDATE audience_processing_policy SET enabled=false');monkeypatch.setattr(settings,'audience_gate_enabled',False)
    assert client.post('/api/admin/bank/content/'+mid+'/review',headers=h,json={'expected_version':2,'decision':'publish'}).status_code==409
    assert len(notices(c))==1 # Only the genuine later source event delivered a notice.


def test_busy_cms_recipient_finishes_publication_without_waiting_on_reward_mutex(client,actor,database):
    c=database[1];mid=submitted(client,actor);h=actor('owner')
    async def scenario():
        async with role() as held:
            await audience.learning_processing_lock(held,'author',restricting=True)
            await held.execute("SELECT pg_advisory_xact_lock(hashtext('rewards:author'))")
            await asyncio.wait_for(asyncio.to_thread(decision,client,h,mid),5)
    client.portal.call(scenario)
    assert c.execute('SELECT status FROM materials WHERE id=%s',(mid,)).fetchone()==('published',)
    assert ledger(c)==[] and notices(c)==[]


def test_restricted_cms_returns_before_reward_mutex(client,actor,database):
    c=database[1];mid=submitted(client,actor);restrict(c,'author','under18');h=actor('owner')
    async def scenario():
        async with role() as held:
            await held.execute("SELECT pg_advisory_xact_lock(hashtext('rewards:author'))")
            await asyncio.wait_for(asyncio.to_thread(decision,client,h,mid),5)
    client.portal.call(scenario);assert ledger(c)==[]


def test_cms_daily_cap_survives_concurrency_archive_restore_and_new_publication(client,actor,database):
    c=database[1];mids=[submitted(client,actor) for _ in range(5)];h=actor('owner')
    with ThreadPoolExecutor(max_workers=5) as pool:list(pool.map(lambda mid:decision(client,h,mid),mids))
    claims=c.execute("SELECT material_id FROM material_reward_claims WHERE user_id='author'").fetchall();assert len(claims)==1
    assert c.execute("SELECT sum(xp),sum(points) FROM reward_ledger WHERE user_id='author'").fetchone()==(20,5)
    mid=claims[0][0];decision(client,h,mid,'archive',3);decision(client,h,mid,'restore',4)
    other=submitted(client,actor);h=actor('owner');decision(client,h,other)
    assert c.execute("SELECT count(*) FROM material_reward_claims WHERE user_id='author'").fetchone()==(1,)
    assert c.execute("SELECT sum(xp),sum(points) FROM reward_ledger WHERE user_id='author'").fetchone()==(0,0)


@pytest.mark.parametrize('excluded',['self','paid-preview','already_published'])
def test_existing_cms_exclusions_never_create_claims(client,actor,database,excluded):
    c=database[1]
    mid=submitted(client,actor,document('paid-preview' if excluded=='paid-preview' else 'free'),user='owner' if excluded=='self' else 'author')
    h=actor('owner')
    if excluded=='already_published':
        c.execute('UPDATE materials SET published_revision=1 WHERE id=%s',(mid,))
    decision(client,h,mid)
    assert c.execute('SELECT count(*) FROM material_reward_claims WHERE material_id=%s',(mid,)).fetchone()==(0,)


@pytest.mark.parametrize('value',[None,'under18','closed'])
@pytest.mark.parametrize('off',[False,True])
def test_cms_archive_reverses_existing_claim_exactly_once_while_restricted(client,actor,database,monkeypatch,value,off):
    c=database[1];mid=submitted(client,actor);h=actor('owner');decision(client,h,mid);original=ledger(c)[0]
    restrict(c,'author',value)
    if off:c.execute('UPDATE audience_processing_policy SET enabled=false');monkeypatch.setattr(settings,'audience_gate_enabled',False)
    decision(client,h,mid,'archive',3);decision(client,h,mid,'restore',4);decision(client,h,mid,'archive',5)
    assert ledger(c)[0]==original and len(ledger(c))==2
    assert c.execute("SELECT sum(xp),sum(points) FROM reward_ledger WHERE user_id='author'").fetchone()==(0,0)
    assert c.execute('SELECT xp,points,reversed_at IS NOT NULL FROM material_reward_claims WHERE material_id=%s',(mid,)).fetchone()==(20,5,True)


def test_cms_historical_claim_amounts_reverse_without_eligibility_lease(client,actor,database):
    c=database[1];mid=submitted(client,actor)
    # A synthetic historical receipt with its recorded amounts, not a new tariff.
    c.execute('INSERT INTO material_reward_claims(material_id,user_id,xp,points) VALUES(%s,\'author\',13,7)',(mid,))
    c.execute("INSERT INTO reward_ledger(user_id,event_key,kind,xp,points,note) VALUES('author',%s,'content',13,7,'Synthetic historical CMS receipt')",('cms-published:'+mid,))
    c.execute("UPDATE materials SET status='published',workflow_state='published',published_revision=1,lock_version=3 WHERE id=%s",(mid,))
    h=actor('owner')
    async def scenario():
        async with role() as held:
            await audience.learning_processing_lock(held,'author',restricting=True)
            await asyncio.wait_for(asyncio.to_thread(decision,client,h,mid,'archive',3),5)
    client.portal.call(scenario)
    assert c.execute("SELECT sum(xp),sum(points) FROM reward_ledger WHERE user_id='author'").fetchone()==(0,0)
    assert len(ledger(c))==2


def test_missing_policy_suppresses_archive_notice_without_losing_integrity_reversal(client,actor,database):
    c=database[1];mid=submitted(client,actor);h=actor('owner');decision(client,h,mid);before=notices(c)
    c.execute('DELETE FROM audience_processing_policy')
    try:decision(client,h,mid,'archive',3)
    finally:c.execute('INSERT INTO audience_processing_policy(singleton,enabled) VALUES(true,true)')
    assert notices(c)==before
    assert c.execute("SELECT sum(xp),sum(points) FROM reward_ledger WHERE user_id='author'").fetchone()==(0,0)


def test_missing_policy_stops_new_positive_cms_derivation(client,actor,database):
    c=database[1];mid=submitted(client,actor);c.execute('DELETE FROM audience_processing_policy')
    async def call():
        async with role() as cur:
            row=await cms.locked(cur,mid,'owner',2,True)
            await cms.publication_reward(cur,row,'owner',cms.Document.model_validate(document()))
    try:
        with pytest.raises(psycopg.errors.RaiseException,match='policy is missing'):client.portal.call(call)
    finally:c.execute('INSERT INTO audience_processing_policy(singleton,enabled) VALUES(true,true)')
    assert ledger(c)==[]


@pytest.mark.parametrize('kind',['material','contribution'])
@pytest.mark.parametrize('value',[None,'under18','closed'])
def test_independent_sql_notice_admission_preserves_history_and_read_controls(client,actor,database,kind,value):
    c=database[1];item=entity(client,actor,c,kind);old=direct_notice(c,kind,item)[0][0];before=notices(c)
    restrict(c,'author',value)
    assert direct_notice(c,kind,item)==[] and notices(c)==before
    execute(c,'UPDATE review_notifications SET read_at=now() WHERE id=%s',(old,))
    assert c.execute('SELECT read_at IS NOT NULL FROM review_notifications WHERE id=%s',(old,)).fetchone()==(True,)


@pytest.mark.parametrize('kind',['material','contribution'])
def test_busy_notice_is_optional_and_does_not_block_source_transaction(client,actor,database,kind):
    name,c=database;item=entity(client,actor,c,kind)
    with psycopg.connect('dbname='+name) as held:
        held.execute("SELECT pg_advisory_xact_lock(hashtextextended('audience-learning-processing-v1:author',0))")
        c.execute("SET statement_timeout='3s'")
        try:assert direct_notice(c,kind,item)==[]
        finally:c.execute('RESET statement_timeout')
    assert notices(c)==[]


@pytest.mark.parametrize('kind',['material','contribution'])
def test_policy_off_preserves_legacy_notice_and_preferences(client,actor,database,monkeypatch,kind):
    c=database[1];item=entity(client,actor,c,kind);restrict(c,'author','under18')
    c.execute('UPDATE audience_processing_policy SET enabled=false');monkeypatch.setattr(settings,'audience_gate_enabled',False)
    c.execute("INSERT INTO inbox_preferences(user_id,in_app) VALUES('author',%s)",(Jsonb({'materials':False,'contributions':False}),))
    assert direct_notice(c,kind,item)
    row=c.execute("SELECT category,silent FROM review_notifications WHERE user_id='author'").fetchone()
    assert row==('materials' if kind=='material' else 'contributions',True)


@pytest.mark.parametrize('kind',['material','contribution'])
def test_missing_notice_policy_suppresses_only_optional_workflow_copy(client,actor,database,kind):
    c=database[1];item=entity(client,actor,c,kind);c.execute('DELETE FROM audience_processing_policy')
    try:
        assert direct_notice(c,kind,item)==[]
        assert execute(c,"INSERT INTO review_notifications(user_id,event_key,message) VALUES('author',%s,'Synthetic account control notice') RETURNING id",(uuid4().hex,))
    finally:c.execute('INSERT INTO audience_processing_policy(singleton,enabled) VALUES(true,true)')


def test_session_guc_and_http_flag_cannot_bypass_database_notice_or_cms_admission(client,actor,database,monkeypatch):
    c=database[1];mid=submitted(client,actor);restrict(c,'author','under18');monkeypatch.setattr(settings,'audience_gate_enabled',False)
    with c.transaction():
        c.execute('SET LOCAL ROLE mpsc');c.execute("SET LOCAL finna.audience_gate_enabled='off'")
        assert c.execute("INSERT INTO review_notifications(user_id,material_id,event_key,message) VALUES('author',%s,%s,'Synthetic flag guard') RETURNING id",(mid,uuid4().hex)).fetchall()==[]
    decision(client,actor('owner'),mid);assert ledger(c)==[] and notices(c)==[]


def test_admitted_cms_reward_and_notice_serialize_api_restriction(client,actor,database):
    c=database[1];mid=submitted(client,actor);h=actor('author')
    async def scenario():
        async with role() as held:
            row=await cms.locked(held,mid,'owner',2,True)
            await cms.publication_reward(held,row,'owner',cms.Document.model_validate(document()))
            task=asyncio.create_task(asyncio.to_thread(declare,client,'under18',headers=h,user_id='author',expected_version=1))
            try:await wait_for_advisory_wait(held,task)
            except BaseException:task.cancel();await asyncio.gather(task,return_exceptions=True);raise
        response=await asyncio.wait_for(task,5);assert response.status_code==200,response.text
    client.portal.call(scenario)
    assert len(ledger(c))==1


@pytest.mark.parametrize('kind',['material','contribution'])
def test_admitted_independent_notice_restriction_must_retry_until_commit(client,actor,database,kind):
    name,c=database;item=entity(client,actor,c,kind)
    column='material_id' if kind=='material' else 'contribution_id'
    with psycopg.connect('dbname='+name) as writer:
        writer.execute('SET LOCAL ROLE mpsc');writer.execute('INSERT INTO review_notifications(user_id,'+column+",event_key,message) VALUES('author',%s,%s,'Synthetic held notice')",(item,uuid4().hex))
        with pytest.raises(psycopg.errors.LockNotAvailable):restrict(c,'author','under18')
    restrict(c,'author','under18');assert len(notices(c))==1


@pytest.mark.parametrize('value',[None,'under18','closed','busy'])
def test_trusted_publisher_retry_never_backfills_suppressed_original_notice(client,actor,database,monkeypatch,value):
    name,c=database;cid,pid=publication(c,'author');sql=acknowledgement(c,cid,pid)
    if value=='busy':
        with psycopg.connect('dbname='+name) as held:
            held.execute("SELECT pg_advisory_xact_lock(hashtextextended('audience-learning-processing-v1:author',0))")
            c.execute(sql)
    else:restrict(c,'author',value);c.execute(sql)
    assert notices(c)==[]
    if value!='closed':c.execute("INSERT INTO account_audience(user_id,category) VALUES('author','adult') ON CONFLICT(user_id) DO UPDATE SET category='adult'")
    c.execute(sql)
    c.execute('UPDATE audience_processing_policy SET enabled=false');monkeypatch.setattr(settings,'audience_gate_enabled',False);c.execute(sql)
    assert notices(c)==[]
    assert c.execute('SELECT count(*) FROM contribution_credit WHERE publication_id=%s',(pid,)).fetchone()==(1,)
    assert c.execute("SELECT count(*) FROM contribution_events WHERE contribution_id=%s AND action='published'",(cid,)).fetchone()==(1,)


def test_trusted_publisher_keeps_exact_negative_and_zero_credit_when_notice_policy_missing(client,database):
    c=database[1];cid,pid,original=paid(c);rid=reversal(c,cid,pid)
    c.execute('UPDATE bank_publications SET receipt=%s WHERE id=%s',(Jsonb({'publication_id':rid,'manifest_hash':'f'*64,'output_sha256':'b'*64,'after':{'id':'appearance-test'}}),rid))
    sql=acknowledgement(c,cid,rid);restrict(c,'author','closed');c.execute('DELETE FROM audience_processing_policy')
    try:c.execute(sql);c.execute(sql)
    finally:c.execute('INSERT INTO audience_processing_policy(singleton,enabled) VALUES(true,true)')
    assert notices(c)==[]
    assert c.execute('SELECT amount FROM contribution_credit WHERE publication_id=%s ORDER BY amount',(rid,)).fetchall()==[(-10,),(0,)]
    assert c.execute("SELECT sum(xp),sum(points) FROM reward_ledger WHERE user_id='author'").fetchone()==(0,0)


def test_contribution_state_audit_is_preserved_when_private_notice_is_suppressed(client,database):
    c=database[1];cid,_=publication(c,'author',reviewers=());restrict(c,'author','under18')
    async def change():
        async with role() as cur:
            await cur.execute('SELECT * FROM bank_contributions WHERE id=%s FOR UPDATE',(cid,));row=await cur.fetchone()
            return await bank_review.update_state(cur,row,'owner','rejected',{'reason':'Synthetic retained decision audit'})
    assert client.portal.call(change)['state']=='rejected'
    assert notices(c)==[]
    assert c.execute("SELECT count(*) FROM contribution_events WHERE contribution_id=%s AND action='rejected'",(cid,)).fetchone()==(1,)


def test_adult_notice_reads_remain_private_owned_and_read_only(client,actor,database,monkeypatch):
    from contextlib import asynccontextmanager
    from app.db import cursor
    from app.routers import bank_workspace
    c=database[1];cid=publication(c,'author',reviewers=())[0];direct_notice(c,'contribution',cid)
    @asynccontextmanager
    async def readonly():
        async with cursor() as cur:
            await cur.execute('SET TRANSACTION READ ONLY');await cur.execute('SET LOCAL ROLE mpsc');yield cur
    monkeypatch.setattr(bank_workspace,'cursor',readonly)
    actor('author');r=client.get('/api/review/notifications');assert r.status_code==200 and len(r.json())==1
    assert r.headers['cache-control']=='private, no-store'
    actor('outsider');assert client.get('/api/review/notifications').json()==[]
    actor('owner');r=client.get('/api/admin/bank/reward-diagnostics');assert r.status_code==200,r.text
    from app.services.reward_economy import INTEGRITY_FIELDS
    assert all(r.json()[key]==0 for key in INTEGRITY_FIELDS)


@pytest.mark.parametrize('kind',['cms_reward','notice'])
def test_admitted_recipient_processing_serializes_full_account_closure(client,actor,database,kind):
    c=database[1];mid=submitted(client,actor)
    version=c.execute("SELECT identity_version FROM users WHERE id='author'").fetchone()[0]
    async def closing():
        async with role() as other:return await account_tools.close(other,'author',version)
    async def scenario():
        async with role() as held:
            if kind=='cms_reward':
                row=await cms.locked(held,mid,'owner',2,True)
                await cms.publication_reward(held,row,'owner',cms.Document.model_validate(document()))
            else:
                await held.execute("INSERT INTO review_notifications(user_id,material_id,event_key,message) VALUES('author',%s,%s,'Synthetic admitted workflow notice')",(mid,uuid4().hex))
            task=asyncio.create_task(closing())
            try:await wait_for_advisory_wait(held,task)
            except BaseException:task.cancel();await asyncio.gather(task,return_exceptions=True);raise
        assert await asyncio.wait_for(task,5)=={'closed':True}
    client.portal.call(scenario)
    assert c.execute("SELECT closed_at IS NOT NULL FROM users WHERE id='author'").fetchone()==(True,)
    assert (len(ledger(c)),len(notices(c)))==((1,0) if kind=='cms_reward' else (0,1))


@pytest.mark.parametrize('reverse',[False,True])
def test_adult_private_workflow_notices_keep_authorized_governance_independent_of_social_blocks(client,actor,database,reverse):
    c=database[1];mid=submitted(client,actor)
    a,b=('author','owner') if reverse else ('owner','author')
    c.execute('INSERT INTO creator_blocks(user_id,blocked_id) VALUES(%s,%s)',(a,b))
    decision(client,actor('owner'),mid)
    assert len(notices(c))==1 and len(ledger(c))==1
    assert c.execute("SELECT actor_id FROM material_events WHERE material_id=%s AND action='publish'",(mid,)).fetchone()==('owner',)


def test_nonworkflow_account_control_notice_is_not_suppressed_for_restricted_subject(client,database):
    c=database[1];restrict(c,'author','under18')
    assert execute(c,"INSERT INTO review_notifications(user_id,event_key,message) VALUES('author',%s,'Synthetic account control notice') RETURNING id",(uuid4().hex,))
    assert c.execute("SELECT category FROM review_notifications WHERE user_id='author'").fetchone()==('system',)


def test_flag_off_unknown_age_retains_existing_cms_first_publication_reward(client,actor,database,monkeypatch):
    c=database[1];mid=submitted(client,actor);restrict(c,'author',None)
    c.execute('UPDATE audience_processing_policy SET enabled=false');monkeypatch.setattr(settings,'audience_gate_enabled',False)
    decision(client,actor('owner'),mid)
    assert c.execute("SELECT sum(xp),sum(points) FROM reward_ledger WHERE user_id='author'").fetchone()==(20,5)
    assert len(notices(c))==1


def test_application_role_cannot_replace_disable_or_call_notice_guard(client,database):
    c=database[1]
    for query in ['SELECT audience_review_notice_recipient()',
      'ALTER TABLE review_notifications DISABLE TRIGGER audience_review_notice_recipient',
      'DROP FUNCTION audience_review_notice_recipient() CASCADE']:
        with pytest.raises(psycopg.errors.InsufficientPrivilege):execute(c,query)
