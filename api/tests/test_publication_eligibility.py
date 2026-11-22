"""Publication reward admission and integrity reversals; isolated real-role SQL."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
import importlib.util
from pathlib import Path
from uuid import uuid4
import psycopg
from psycopg.types.json import Jsonb
import pytest
from app.config import settings
from app.services import audience
from test_discussions import database,client
from test_contribution_rewards_v2 import publication,credit
from test_synchronous_activity_audience import manual_workers,role,execute,restrict
from test_account_privacy import declare
from test_learning_eligibility import wait_for_advisory_wait


@pytest.fixture(autouse=True)
def enabled_policy(client,database,monkeypatch):
    c=database[1]
    c.execute("INSERT INTO account_audience(user_id,category) SELECT id,'adult' FROM users")
    c.execute('UPDATE audience_processing_policy SET enabled=true')
    monkeypatch.setattr(settings,'audience_gate_enabled',True)


def award(c,user,cid,pid,**kw):
    with c.transaction():
        c.execute('SET LOCAL ROLE mpsc')
        return credit(c,user,cid,pid,**kw)


def independent_award(name,user,pair,**kw):
    with psycopg.connect('dbname='+name) as c:
        c.execute('SET LOCAL ROLE mpsc')
        return credit(c,user,*pair,**kw)


def ledger(c,user='author'):
    return c.execute('SELECT * FROM reward_ledger WHERE user_id=%s ORDER BY id',(user,)).fetchall()


def reversal(c,cid,pid):
    rid='reversal-'+uuid4().hex
    revision=c.execute('SELECT max(revision)+1 FROM bank_publications WHERE contribution_id=%s',(cid,)).fetchone()[0]
    c.execute("INSERT INTO bank_publications(id,contribution_id,revision,manifest,manifest_hash,exported_by) VALUES(%s,%s,%s,%s,%s,'owner')",(rid,cid,revision,Jsonb({'payload':{'reverts_publication':pid}}),'f'*64))
    return rid


def paid(c,legacy=False):
    cid,pid=publication(c,'author',reviewers=() if legacy else ('reviewer1',))
    cc=award(c,'author',cid,pid)[0]
    if legacy:
        c.execute("INSERT INTO reward_ledger(user_id,event_key,kind,xp,points,note,rule_version) VALUES('author',%s,'contribution',13,7,'Synthetic v1 source receipt','learning-v1')",('contribution-credit:'+str(cc),))
    original=c.execute('SELECT id,xp,points FROM reward_ledger WHERE event_key=%s',('contribution-credit:'+str(cc),)).fetchone()
    return cid,pid,original


def acknowledgement(c,cid,pid):
    # Generate the real trusted worker's SQL without calling SSH, publication,
    # sync, email or file writers. Execute it only against this disposable DB.
    spec=importlib.util.spec_from_file_location('audience_publication_worker',Path(__file__).resolve().parents[2]/'scripts/bank-review-worker.py')
    worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)
    receipt=c.execute('SELECT receipt FROM bank_publications WHERE id=%s',(pid,)).fetchone()[0]
    c.execute("UPDATE bank_publications SET state='exported',finished_at=NULL WHERE id=%s",(pid,))
    c.execute("UPDATE bank_contributions SET state='publishing' WHERE id=%s",(cid,))
    return worker.acknowledge({'id':pid,'contribution_id':cid},receipt,sql_only=True).replace('BEGIN;','BEGIN; SET LOCAL ROLE mpsc;',1)


@pytest.mark.parametrize('value',[None,'under18','closed'])
def test_real_publisher_acknowledgement_preserves_source_when_positive_reward_is_suppressed(client,database,value):
    c=database[1];cid,pid=publication(c,'author');statement=acknowledgement(c,cid,pid)
    restrict(c,'author',value);c.execute(statement);c.execute(statement)
    assert c.execute('SELECT state FROM bank_publications WHERE id=%s',(pid,)).fetchone()==('applied',)
    assert c.execute('SELECT state FROM bank_contributions WHERE id=%s',(cid,)).fetchone()==('published',)
    assert c.execute('SELECT count(*) FROM contribution_credit WHERE publication_id=%s',(pid,)).fetchone()==(1,)
    assert c.execute("SELECT count(*) FROM contribution_events WHERE contribution_id=%s AND action='published'",(cid,)).fetchone()==(1,)
    # Source publication/audit remain; optional recipient workflow notice is suppressed.
    assert c.execute('SELECT count(*) FROM review_notifications WHERE contribution_id=%s',(cid,)).fetchone()==(0,)
    assert ledger(c)==[]
    assert c.execute('SELECT count(*) FROM contribution_reward_claims').fetchone()==(0,)
    assert c.execute("SELECT count(*) FROM reward_profiles WHERE user_id='author'").fetchone()==(0,)


@pytest.mark.parametrize('value',[None,'under18'])
def test_default_off_retains_registered_publication_reward_and_replay(client,database,monkeypatch,value):
    c=database[1];c.execute('UPDATE audience_processing_policy SET enabled=false')
    monkeypatch.setattr(settings,'audience_gate_enabled',False);restrict(c,'author',value)
    cid,pid=publication(c,'author');cc=award(c,'author',cid,pid)[0]
    assert c.execute('SELECT xp,points FROM reward_ledger WHERE event_key=%s',('contribution-credit:'+str(cc),)).fetchone()==(20,5)
    saved=ledger(c);assert award(c,'author',cid,pid) is None and ledger(c)==saved


@pytest.mark.parametrize('kind,reviewers,expected',[
    ('explanation',('reviewer1',),(20,5)),('answer',('reviewer1','reviewer2'),(40,10))])
def test_enabled_adult_tariffs_replay_and_source_receipts(client,database,kind,reviewers,expected):
    c=database[1];cid,pid=publication(c,'author',kind,reviewers);cc=award(c,'author',cid,pid)[0]
    assert c.execute('SELECT xp,points FROM reward_ledger WHERE event_key=%s',('contribution-credit:'+str(cc),)).fetchone()==expected
    saved=ledger(c);assert award(c,'author',cid,pid) is None and ledger(c)==saved
    assert c.execute('SELECT credit_id,publication_id FROM contribution_reward_claims').fetchall()==[(cc,pid)]


def test_enabled_concurrent_cap_and_reversal_does_not_restore_a_daily_slot(client,database):
    name,c=database;pairs=[publication(c,'author') for _ in range(6)]
    with ThreadPoolExecutor(6) as pool:list(pool.map(lambda pair:independent_award(name,'author',pair),pairs))
    assert c.execute("SELECT count(*),sum(xp),sum(points) FROM reward_ledger WHERE user_id='author'").fetchone()==(3,60,15)
    pid=c.execute('SELECT publication_id FROM contribution_reward_claims ORDER BY credit_id LIMIT 1').fetchone()[0]
    cid=next(cid for cid,p in pairs if p==pid);rid=reversal(c,cid,pid)
    award(c,'author',cid,rid,key=rid+':reversal:'+pid,amount=-10)
    later=publication(c,'author');award(c,'author',*later)
    assert c.execute("SELECT count(*) FROM reward_ledger WHERE user_id='author' AND points>0").fetchone()==(3,)
    assert c.execute("SELECT sum(xp),sum(points) FROM reward_ledger WHERE user_id='author'").fetchone()==(40,10)


def test_busy_account_does_not_abort_publisher_or_wait_on_processing_lease(client,database):
    name,c=database;cid,pid=publication(c,'author');statement=acknowledgement(c,cid,pid)
    def acknowledge():
        with psycopg.connect('dbname='+name,autocommit=True) as other:other.execute(statement)
    async def scenario():
        async with role() as held:
            await audience.learning_processing_lock(held,'author',restricting=True)
            await asyncio.wait_for(asyncio.to_thread(acknowledge),5)
    client.portal.call(scenario)
    assert c.execute('SELECT state FROM bank_publications WHERE id=%s',(pid,)).fetchone()==('applied',)
    assert c.execute('SELECT count(*) FROM contribution_credit WHERE publication_id=%s',(pid,)).fetchone()==(1,)
    assert ledger(c)==[]


def test_restricted_positive_returns_before_reward_mutex(client,database):
    name,c=database;pair=publication(c,'author');restrict(c,'author','under18')
    async def scenario():
        async with role() as held:
            await held.execute("SELECT pg_advisory_xact_lock(hashtext('rewards:author'))")
            await asyncio.wait_for(asyncio.to_thread(independent_award,name,'author',pair),5)
    client.portal.call(scenario);assert ledger(c)==[]


def test_accepted_positive_lease_serializes_api_restriction(client,database,actor):
    c=database[1];pair=publication(c,'author');h=actor('author')
    async def scenario():
        async with role() as held:
            await held.execute("INSERT INTO contribution_credit(user_id,contribution_id,publication_id,amount,event_key,reason,subject_id) VALUES('author',%s,%s,10,%s,'Synthetic lease boundary','english')",(*pair,pair[1]+':credit'))
            task=asyncio.create_task(asyncio.to_thread(declare,client,'under18',headers=h,user_id='author',expected_version=1))
            try:await wait_for_advisory_wait(held,task)
            except BaseException:task.cancel();await asyncio.gather(task,return_exceptions=True);raise
        response=await asyncio.wait_for(task,5);assert response.status_code==200,response.text
    client.portal.call(scenario)
    saved=ledger(c);assert len(saved)==1
    next_pair=publication(c,'author');award(c,'author',*next_pair);assert ledger(c)==saved


def test_direct_sql_restriction_must_retry_while_positive_is_admitted(client,database):
    c=database[1];cid,pid=publication(c,'author')
    async def scenario():
        async with role() as held:
            await held.execute("INSERT INTO contribution_credit(user_id,contribution_id,publication_id,amount,event_key,reason,subject_id) VALUES('author',%s,%s,10,%s,'Synthetic restriction race','english')",(cid,pid,pid+':credit'))
            with pytest.raises(psycopg.errors.LockNotAvailable):restrict(c,'author','under18')
    client.portal.call(scenario);restrict(c,'author','under18')
    assert len(ledger(c))==1


def test_direct_closure_can_wait_for_foreign_key_then_finish_without_deadlock(client,database):
    c=database[1];cid,pid=publication(c,'author');backend={}
    async def close_sql():
        async with role() as other:
            await other.execute('SELECT pg_backend_pid() AS pid');backend['pid']=(await other.fetchone())['pid']
            await other.execute('''UPDATE users SET closed_at=now(),email=NULL,password_hash=NULL,name=NULL,
              avatar=NULL,email_verified_at=NULL,contribution_public=false WHERE id='author' ''')
    async def scenario():
        async with role() as held:
            await held.execute("INSERT INTO contribution_credit(user_id,contribution_id,publication_id,amount,event_key,reason,subject_id) VALUES('author',%s,%s,10,%s,'Synthetic closure race','english')",(cid,pid,pid+':credit'))
            task=asyncio.create_task(close_sql())
            try:
                for _ in range(100):
                    await held.execute("SELECT EXISTS(SELECT 1 FROM pg_locks WHERE pid=%s AND locktype IN ('transactionid','tuple') AND NOT granted) AS waiting",(backend.get('pid'),))
                    if (await held.fetchone())['waiting']:break
                    if task.done():await task;raise AssertionError('Closure skipped the held foreign-key row lock')
                    await asyncio.sleep(.01)
                else:raise AssertionError('Closure did not wait for the admitted source credit')
            except BaseException:task.cancel();await asyncio.gather(task,return_exceptions=True);raise
        await asyncio.wait_for(task,5)
    client.portal.call(scenario)
    assert c.execute("SELECT closed_at IS NOT NULL FROM users WHERE id='author'").fetchone()==(True,)
    saved=ledger(c);assert len(saved)==1
    award(c,'author',*publication(c,'author'));assert ledger(c)==saved


@pytest.mark.parametrize('legacy',[False,True])
@pytest.mark.parametrize('value',[None,'under18','closed','adult'])
def test_restricted_or_closed_reversal_negates_exact_receipt_once(client,database,actor,legacy,value):
    c=database[1];cid,pid,original=paid(c,legacy);positive=ledger(c)[0]
    restrict(c,'author',value);rid=reversal(c,cid,pid)
    cc=award(c,'author',cid,rid,key=rid+':reversal:'+pid,amount=-10)[0]
    assert c.execute('SELECT xp,points,reverses_id FROM reward_ledger WHERE event_key=%s',('contribution-credit:'+str(cc),)).fetchone()==(-original[1],-original[2],original[0])
    assert award(c,'author',cid,rid,key=rid+':reversal:'+pid,amount=-10) is None
    other=reversal(c,cid,pid);award(c,'author',cid,other,key=other+':reversal:'+pid,amount=-10)
    assert ledger(c)[0]==positive
    assert c.execute("SELECT sum(xp),sum(points) FROM reward_ledger WHERE user_id='author'").fetchone()==(0,0)
    assert c.execute('SELECT count(*) FROM contribution_reward_reversals WHERE original_ledger_id=%s',(original[0],)).fetchone()==(1,)
    actor('owner');diagnostic=client.get('/api/admin/bank/reward-diagnostics')
    assert diagnostic.status_code==200,diagnostic.text
    from app.services.reward_economy import INTEGRITY_FIELDS
    assert all(diagnostic.json()[field]==0 for field in INTEGRITY_FIELDS)


def test_closed_reversal_integrity_also_applies_when_policy_is_off(client,database,monkeypatch):
    c=database[1];cid,pid,original=paid(c);restrict(c,'author','closed')
    c.execute('UPDATE audience_processing_policy SET enabled=false');monkeypatch.setattr(settings,'audience_gate_enabled',False)
    rid=reversal(c,cid,pid);award(c,'author',cid,rid,key=rid+':reversal:'+pid,amount=-10)
    assert c.execute('SELECT count(*) FROM contribution_reward_reversals WHERE original_ledger_id=%s',(original[0],)).fetchone()==(1,)
    assert c.execute("SELECT sum(xp),sum(points) FROM reward_ledger WHERE user_id='author'").fetchone()==(0,0)


def test_valid_reversal_does_not_wait_for_eligibility_lease(client,database):
    name,c=database;cid,pid,original=paid(c);rid=reversal(c,cid,pid)
    async def scenario():
        async with role() as held:
            await audience.learning_processing_lock(held,'author',restricting=True)
            await asyncio.wait_for(asyncio.to_thread(independent_award,name,'author',(cid,rid),key=rid+':reversal:'+pid,amount=-10),5)
    client.portal.call(scenario)
    assert c.execute('SELECT count(*) FROM contribution_reward_reversals WHERE original_ledger_id=%s',(original[0],)).fetchone()==(1,)


def test_missing_policy_blocks_positive_but_does_not_block_exact_reversal(client,database):
    c=database[1];cid,pid,original=paid(c);other=publication(c,'author');rid=reversal(c,cid,pid)
    c.execute('DELETE FROM audience_processing_policy')
    with pytest.raises(psycopg.errors.RaiseException,match='policy is missing'):award(c,'author',*other)
    award(c,'author',cid,rid,key=rid+':reversal:'+pid,amount=-10)
    assert c.execute('SELECT count(*) FROM contribution_reward_reversals WHERE original_ledger_id=%s',(original[0],)).fetchone()==(1,)
    assert c.execute('SELECT count(*) FROM contribution_credit WHERE publication_id=%s',(other[1],)).fetchone()==(0,)


@pytest.mark.parametrize('bad',['wrong_amount','wrong_event','wrong_contribution','no_original_receipt'])
def test_restricted_invalid_reversal_has_no_ledger_or_reversal_receipt(client,database,bad):
    c=database[1]
    if bad=='no_original_receipt':cid,pid=publication(c,'author',reviewers=());award(c,'author',cid,pid)
    else:cid,pid,_=paid(c)
    saved=ledger(c);rid=reversal(c,cid,pid);restrict(c,'author','under18')
    if bad=='wrong_contribution':cid=publication(c,'author')[0]
    award(c,'author',cid,rid,key='invalid-'+rid if bad=='wrong_event' else rid+':reversal:'+pid,amount=-9 if bad=='wrong_amount' else -10)
    assert ledger(c)==saved
    assert c.execute('SELECT count(*) FROM contribution_reward_reversals').fetchone()==(0,)


def test_suppressed_original_event_does_not_replay_on_confirmation_or_flag_off(client,database,monkeypatch):
    c=database[1];cid,pid=publication(c,'author');restrict(c,'author','under18');cc=award(c,'author',cid,pid)[0]
    assert ledger(c)==[]
    c.execute("UPDATE account_audience SET category='adult' WHERE user_id='author'")
    assert award(c,'author',cid,pid) is None and ledger(c)==[]
    c.execute('UPDATE audience_processing_policy SET enabled=false');monkeypatch.setattr(settings,'audience_gate_enabled',False)
    assert award(c,'author',cid,pid) is None and ledger(c)==[]
    with pytest.raises(psycopg.errors.RaiseException,match='append-only'):
        c.execute('UPDATE contribution_credit SET amount=amount WHERE id=%s',(cc,))


def test_session_guc_cannot_disable_positive_admission(client,database):
    c=database[1];pair=publication(c,'author');restrict(c,'author','under18')
    with c.transaction():
        c.execute('SET LOCAL ROLE mpsc');c.execute("SET LOCAL finna.audience_gate_enabled='off'")
        credit(c,'author',*pair)
    assert ledger(c)==[]


def test_real_publisher_closed_reversal_and_zero_credit_finish_once(client,database):
    c=database[1];cid,pid,original=paid(c);rid=reversal(c,cid,pid)
    receipt={'publication_id':rid,'manifest_hash':'f'*64,'output_sha256':'b'*64,'after':{'id':'appearance-test'}}
    c.execute('UPDATE bank_publications SET receipt=%s WHERE id=%s',(Jsonb(receipt),rid))
    statement=acknowledgement(c,cid,rid);restrict(c,'author','closed')
    c.execute(statement);saved=ledger(c);c.execute(statement)
    assert ledger(c)==saved and len(saved)==2
    assert c.execute('SELECT state FROM bank_publications WHERE id=%s',(rid,)).fetchone()==('applied',)
    assert c.execute('SELECT state FROM bank_publications WHERE id=%s',(pid,)).fetchone()==('reverted',)
    assert c.execute('SELECT state FROM bank_contributions WHERE id=%s',(cid,)).fetchone()==('reverted',)
    assert c.execute('SELECT amount FROM contribution_credit WHERE publication_id=%s ORDER BY amount',(rid,)).fetchall()==[(-10,),(0,)]
    assert c.execute('SELECT count(*) FROM contribution_reward_reversals WHERE original_ledger_id=%s',(original[0],)).fetchone()==(1,)
    assert c.execute("SELECT sum(xp),sum(points) FROM reward_ledger WHERE user_id='author'").fetchone()==(0,0)
