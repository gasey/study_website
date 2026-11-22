"""Durable learning admission and restriction races on isolated PostgreSQL."""
import asyncio
from contextlib import asynccontextmanager

import pytest
from app.config import settings
from app.db import cursor
from app.services import audience, learning_rollups, account_tools
from test_account_privacy import declare
from test_learning_loop import questions, attempt
from test_learning_workflows import learner


@pytest.fixture(scope='module',autouse=True)
def no_automatic_reconciler():
    from app import main
    async def idle():await asyncio.Event().wait()
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(main,'learning_worker',idle)
        yield


@pytest.fixture(autouse=True)
def independent_jobs(database,monkeypatch):
    conn=database[1]
    # Independent synthetic cases only; production code never deletes jobs.
    conn.execute('DELETE FROM learning_rollup_jobs')
    conn.execute("UPDATE account_audience SET category='under18'")
    conn.execute("DELETE FROM worker_heartbeats WHERE worker IN ('mastery-nightly','mastery-reconciler')")
    monkeypatch.setattr(settings,'audience_gate_enabled',False)


@asynccontextmanager
async def role_cursor():
    async with cursor() as cur:
        await cur.execute('SET LOCAL ROLE mpsc')
        yield cur


def run(client,fn,*args):
    async def call():
        async with role_cursor() as cur:return await fn(cur,*args)
    return client.portal.call(call)


def case(database,actor,category='adult'):
    conn=database[1];user,h=learner(database,actor);_,ids=questions(database,1)
    aid=attempt(conn,user,ids[0],False)
    if category:conn.execute('INSERT INTO account_audience(user_id,category) VALUES(%s,%s)',(user,category))
    return user,h,aid


def snapshot(conn,user):
    return {table:conn.execute('SELECT * FROM '+table+' WHERE user_id=%s ORDER BY 1,2',(user,)).fetchall()
            for table in ('learning_rollup_jobs','review_items','user_topic_mastery','user_activity_daily',
                          'user_activity_questions','reward_ledger')}


async def wait_for_advisory_wait(cur,task):
    for _ in range(100):
        await cur.execute("SELECT EXISTS(SELECT 1 FROM pg_locks WHERE locktype='advisory' AND NOT granted AND pid<>pg_backend_pid() AND database=(SELECT oid FROM pg_database WHERE datname=current_database())) AS waiting")
        if (await cur.fetchone())['waiting']:return
        if task.done():
            await task
            raise AssertionError('Operation bypassed the held processing lease')
        await asyncio.sleep(.01)
    raise AssertionError('Operation did not wait on the processing lease')


@pytest.mark.parametrize('value',[None,'under18'])
def test_restricted_job_remains_byte_for_byte_pending(client,actor,database,monkeypatch,value):
    user,_,_=case(database,actor,value);conn=database[1];before=snapshot(conn,user)
    monkeypatch.setattr(settings,'audience_gate_enabled',True)
    assert run(client,learning_rollups.process_one) is False
    assert snapshot(conn,user)==before


def test_adult_confirmation_resumes_original_pending_work_once(client,actor,database,monkeypatch):
    user,h,aid=case(database,actor,None);conn=database[1]
    original=conn.execute('SELECT requested_version FROM learning_rollup_jobs WHERE user_id=%s',(user,)).fetchone()[0]
    monkeypatch.setattr(settings,'audience_gate_enabled',True)
    assert run(client,learning_rollups.process_one) is False
    assert declare(client,'adult',headers=h,user_id=user).status_code==200
    assert client.post('/api/account-privacy/confirm-adult',headers=h,json={'user_id':user,'expected_version':0}).status_code==200
    assert run(client,learning_rollups.process_one) is True
    after=snapshot(conn,user)
    assert conn.execute('SELECT requested_version,processed_version,attempt_cursor FROM learning_rollup_jobs WHERE user_id=%s',(user,)).fetchone()==(original,original,aid)
    assert len(after['review_items'])==len(after['user_topic_mastery'])==1
    assert not after['reward_ledger']
    assert run(client,learning_rollups.process_one) is False
    assert snapshot(conn,user)==after


def test_flag_off_preserves_existing_unknown_age_processing(client,actor,database):
    user,_,_=case(database,actor,None)
    assert run(client,learning_rollups.process_one) is True
    assert database[1].execute('SELECT processed_version=requested_version FROM learning_rollup_jobs WHERE user_id=%s',(user,)).fetchone()==(True,)


def test_restricted_oldest_job_does_not_starve_adult(client,actor,database,monkeypatch):
    minor,_,_=case(database,actor,'under18');adult,_,_=case(database,actor)
    conn=database[1];before=snapshot(conn,minor)
    monkeypatch.setattr(settings,'audience_gate_enabled',True)
    assert run(client,learning_rollups.process_one) is True
    assert snapshot(conn,minor)==before
    assert conn.execute('SELECT processed_version=requested_version FROM learning_rollup_jobs WHERE user_id=%s',(adult,)).fetchone()==(True,)


def test_busy_restriction_skipped_without_blocking_another_account(client,actor,database,monkeypatch):
    busy,_,_=case(database,actor);adult,_,_=case(database,actor);conn=database[1]
    before=snapshot(conn,busy);monkeypatch.setattr(settings,'audience_gate_enabled',True)
    async def scenario():
        async with role_cursor() as cur:
            await audience.learning_processing_lock(cur,busy,restricting=True)
            async def worker():
                async with role_cursor() as other:return await learning_rollups.process_one(other)
            assert await asyncio.wait_for(worker(),5) is True
    client.portal.call(scenario)
    assert snapshot(conn,busy)==before
    assert conn.execute('SELECT processed_version=requested_version FROM learning_rollup_jobs WHERE user_id=%s',(adult,)).fetchone()==(True,)


def test_skipped_job_row_lock_releases_its_processing_lease(client,actor,database,monkeypatch):
    busy,_,_=case(database,actor);adult,_,_=case(database,actor)
    monkeypatch.setattr(settings,'audience_gate_enabled',True)
    async def scenario():
        async with role_cursor() as cur:
            await cur.execute('SELECT user_id FROM learning_rollup_jobs WHERE user_id=%s FOR UPDATE',(busy,))
            async with role_cursor() as other:
                assert await asyncio.wait_for(learning_rollups.process_one(other),5) is True
                await cur.execute('SELECT pg_try_advisory_xact_lock(hashtextextended(%s,0)) AS claimed',('audience-learning-processing-v1:'+busy,))
                assert (await cur.fetchone())['claimed'],'Skipped candidate retained a shared lease'
    client.portal.call(scenario)
    assert database[1].execute('SELECT processed_version=requested_version FROM learning_rollup_jobs WHERE user_id=%s',(adult,)).fetchone()==(True,)


def test_declaration_waits_for_already_admitted_learning_then_parks_later_work(client,actor,database,monkeypatch):
    user,h,_=case(database,actor);monkeypatch.setattr(settings,'audience_gate_enabled',True)
    async def scenario():
        async with role_cursor() as cur:
            assert await learning_rollups.process_one(cur) is True
            task=asyncio.create_task(asyncio.to_thread(declare,client,'under18',headers=h,user_id=user,expected_version=1))
            try:await wait_for_advisory_wait(cur,task)
            except BaseException:
                task.cancel();raise
        response=await asyncio.wait_for(task,5)
        assert response.status_code==200,response.text
    client.portal.call(scenario)
    conn=database[1]
    assert conn.execute('SELECT category FROM account_audience WHERE user_id=%s',(user,)).fetchone()==('under18',)
    conn.execute('UPDATE learning_rollup_jobs SET requested_version=requested_version+1 WHERE user_id=%s',(user,))
    before=snapshot(conn,user)
    assert run(client,learning_rollups.process_one) is False
    assert snapshot(conn,user)==before


def test_candidate_rechecks_category_after_selection(client,actor,database,monkeypatch):
    user,_,_=case(database,actor);conn=database[1];before=snapshot(conn,user)
    original=audience.learning_processing_lock
    async def restrict_before_claim(cur,target,**kwargs):
        if target==user and not kwargs.get('restricting'):
            conn.execute("UPDATE account_audience SET category='under18',version=version+1 WHERE user_id=%s",(user,))
        return await original(cur,target,**kwargs)
    monkeypatch.setattr(settings,'audience_gate_enabled',True)
    monkeypatch.setattr(audience,'learning_processing_lock',restrict_before_claim)
    assert run(client,learning_rollups.process_one) is False
    assert snapshot(conn,user)==before


def test_close_waits_for_learning_and_closed_job_is_not_processed(client,actor,database,monkeypatch):
    user,_,_=case(database,actor);monkeypatch.setattr(settings,'audience_gate_enabled',True)
    async def scenario():
        async with role_cursor() as cur:
            assert await learning_rollups.process_one(cur) is True
            async def close():
                async with role_cursor() as other:await account_tools.close(other,user,0)
            task=asyncio.create_task(close())
            try:await wait_for_advisory_wait(cur,task)
            except BaseException:
                task.cancel();await asyncio.gather(task,return_exceptions=True);raise
        await asyncio.wait_for(task,5)
    client.portal.call(scenario)
    conn=database[1];assert conn.execute('SELECT closed_at IS NOT NULL FROM users WHERE id=%s',(user,)).fetchone()==(True,)
    conn.execute('UPDATE learning_rollup_jobs SET requested_version=requested_version+1 WHERE user_id=%s',(user,))
    before=snapshot(conn,user)
    assert run(client,learning_rollups.process_one) is False
    assert snapshot(conn,user)==before


def test_processing_failure_keeps_pending_work_and_records_failure(client,actor,database,monkeypatch):
    user,_,_=case(database,actor);conn=database[1]
    monkeypatch.setattr(settings,'audience_gate_enabled',True)
    async def fail(cur,target):
        await cur.execute("INSERT INTO personal_desks(user_id,document) VALUES(%s,'{}')",(target,))
        raise RuntimeError('Synthetic reconciliation failure')
    monkeypatch.setattr(learning_rollups.review_queue,'seed',fail)
    async def scenario():
        async with role_cursor() as cur:
            with pytest.raises(RuntimeError):await learning_rollups.process_one(cur)
    client.portal.call(scenario)
    assert conn.execute('SELECT failures,processed_version<requested_version,initialized_at FROM learning_rollup_jobs WHERE user_id=%s',(user,)).fetchone()==(1,True,None)
    assert conn.execute('SELECT count(*) FROM personal_desks WHERE user_id=%s',(user,)).fetchone()==(0,)


def test_nightly_enqueue_filters_restrictions_and_reports_pending_jobs(client,actor,database,monkeypatch):
    minor,_,_=case(database,actor,'under18');unknown,_,_=case(database,actor,None);adult,_,_=case(database,actor)
    conn=database[1];before={u:snapshot(conn,u) for u in (minor,unknown)}
    monkeypatch.setattr(settings,'audience_gate_enabled',True)
    run(client,learning_rollups.cycle)
    assert all(snapshot(conn,u)==before[u] for u in before)
    assert conn.execute('SELECT processed_version=requested_version FROM learning_rollup_jobs WHERE user_id=%s',(adult,)).fetchone()==(True,)
    note=conn.execute("SELECT note FROM worker_heartbeats WHERE worker='mastery-reconciler'").fetchone()[0]
    assert '2 age-restricted jobs remain pending' in note
