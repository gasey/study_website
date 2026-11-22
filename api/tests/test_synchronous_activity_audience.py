"""Real-role synchronous activity/adoption policy; synthetic isolated databases."""
import asyncio
from contextlib import asynccontextmanager
from types import SimpleNamespace
from uuid import uuid4
import psycopg
from psycopg import sql
import pytest
from fastapi import HTTPException
from app import db
from app.config import settings
from app.services import audience,account_identity,learning_rollups
from test_discussions import database,client
from test_account_privacy import declare
from test_learning_eligibility import wait_for_advisory_wait


@pytest.fixture(scope='module',autouse=True)
def manual_workers():
    from app import main
    from app.services import account_mail,account_retention
    async def idle():await asyncio.Event().wait()
    with pytest.MonkeyPatch.context() as patch:
        for name in ('assessment_worker','learning_worker','game_worker','calendar_worker','desk_retention_worker'):
            patch.setattr(main,name,idle)
        patch.setattr(account_mail,'worker',idle);patch.setattr(account_retention,'worker',idle)
        yield


@asynccontextmanager
async def role():
    async with db.cursor() as cur:
        await cur.execute('SET LOCAL ROLE mpsc')
        yield cur


@pytest.fixture(autouse=True)
def default_policy(client,database,monkeypatch):
    monkeypatch.setattr(settings,'audience_gate_enabled',False)
    monkeypatch.setattr(account_identity,'cursor',role)
    database[1].execute("INSERT INTO account_audience(user_id,category) SELECT id,'adult' FROM users")
    # Production migrations run as postgres, whose 0007 default privileges cover
    # these mutable tables. The disposable runner is a different creating role.
    # The production-dump rehearsal separately verifies these exact privileges.
    database[1].execute('GRANT DELETE ON exam_study_checkpoints,learning_checkpoints TO mpsc')
    database[1].execute('GRANT SELECT,INSERT,UPDATE,DELETE ON module_learning_progress,essay_drafts TO mpsc')


def enable(c,monkeypatch):
    c.execute('UPDATE audience_processing_policy SET enabled=true')
    monkeypatch.setattr(settings,'audience_gate_enabled',True)


def execute(c,query,params=()):
    with c.transaction():
        c.execute('SET LOCAL ROLE mpsc')
        result=c.execute(query,params)
        return result.fetchall() if result.description else None


def insert(c,user='author'):
    return execute(c,"INSERT INTO attempts(user_id,canonical_id,correct,context) VALUES(%s,'cq_test',false,'practice') RETURNING id",(user,))[0][0]


def restrict(c,user,value):
    if value is None:c.execute('DELETE FROM account_audience WHERE user_id=%s',(user,))
    elif value=='closed':c.execute('UPDATE users SET closed_at=now(),email=NULL,password_hash=NULL,name=NULL,avatar=NULL,email_verified_at=NULL,contribution_public=false WHERE id=%s',(user,))
    else:c.execute('UPDATE account_audience SET category=%s WHERE user_id=%s',(value,user))


def activity(c,user='author'):
    return [c.execute('SELECT * FROM '+table+' WHERE user_id=%s ORDER BY 1,2',(user,)).fetchall()
            for table in ('user_activity_daily','user_activity_questions')]


def guest(c):
    user='guest_'+uuid4().hex;token=uuid4().hex
    c.execute('INSERT INTO users(id,handle) VALUES(%s,%s)',(user,user))
    c.execute('INSERT INTO guest_credentials(user_id,token_hash) VALUES(%s,%s)',(user,account_identity.digest(token)))
    c.execute("INSERT INTO account_audience(user_id,category) VALUES(%s,'adult')",(user,))
    return user,token


def transfer(client,token,account='author'):
    return client.portal.call(account_identity.transfer_guest,SimpleNamespace(cookies={'ism_guest':token}),account)


def run(client,fn,*args):
    async def call():
        async with role() as cur:return await fn(cur,*args)
    return client.portal.call(call)


@pytest.mark.parametrize('value',[None,'under18','closed'])
def test_raw_insert_keeps_source_and_queue_without_restricted_activity(client,database,monkeypatch,value):
    c=database[1];first=insert(c);old=activity(c)
    restrict(c,'author',value);enable(c,monkeypatch);aid=insert(c)
    assert activity(c)==old
    assert c.execute('SELECT id FROM attempts WHERE user_id=\'author\' ORDER BY id').fetchall()==[(first,),(aid,)]
    assert c.execute("SELECT requested_version>processed_version FROM learning_rollup_jobs WHERE user_id='author'").fetchone()==(True,)
    execute(c,'SELECT record_learning_activity(%s)',(aid,));assert activity(c)==old


def test_default_off_preserves_unknown_activity_and_ownership(client,database):
    c=database[1];restrict(c,'author',None);aid=insert(c)
    assert c.execute("SELECT sum(answered) FROM user_activity_daily WHERE user_id='author'").fetchone()==(1,)
    execute(c,"UPDATE attempts SET user_id='outsider' WHERE id=%s",(aid,))
    assert c.execute('SELECT user_id FROM attempts WHERE id=%s',(aid,)).fetchone()==('outsider',)


def test_enabled_registered_adult_activity_and_distinct_question_membership(client,database,monkeypatch):
    c=database[1];enable(c,monkeypatch);insert(c);insert(c)
    assert c.execute("SELECT sum(answered),sum(correct) FROM user_activity_daily WHERE user_id='author'").fetchone()==(2,0)
    assert c.execute("SELECT count(*) FROM user_activity_questions WHERE user_id='author'").fetchone()==(1,)


def test_busy_account_defers_activity_without_losing_source_or_pending_job(client,database,monkeypatch):
    c=database[1];enable(c,monkeypatch)
    async def scenario():
        async with role() as held:
            await audience.learning_processing_lock(held,'author',restricting=True)
            async with role() as other:
                await asyncio.wait_for(other.execute("INSERT INTO attempts(user_id,canonical_id,correct,context) VALUES('author','cq_test',false,'practice') RETURNING id"),5)
                return (await other.fetchone())['id']
    aid=client.portal.call(scenario);assert activity(c)==[[],[]]
    assert c.execute('SELECT user_id FROM attempts WHERE id=%s',(aid,)).fetchone()==('author',)
    assert run(client,learning_rollups.process_one) is True
    assert c.execute("SELECT sum(answered) FROM user_activity_daily WHERE user_id='author'").fetchone()==(1,)
    saved=activity(c);assert run(client,learning_rollups.process_one) is False;assert activity(c)==saved


def test_pending_unknown_activity_resumes_only_through_admitted_reconciliation(client,database,monkeypatch):
    c=database[1];restrict(c,'author',None);enable(c,monkeypatch);insert(c)
    assert run(client,learning_rollups.process_one) is False and activity(c)==[[],[]]
    c.execute("INSERT INTO account_audience(user_id,category) VALUES('author','adult')")
    assert run(client,learning_rollups.process_one) is True
    saved=activity(c);assert saved[0][0][6]==1
    assert run(client,learning_rollups.process_one) is False and activity(c)==saved
    assert c.execute("SELECT count(*) FROM reward_ledger WHERE user_id='author'").fetchone()==(0,)


@pytest.mark.parametrize('side',['source','target'])
@pytest.mark.parametrize('value',[None,'under18','closed'])
def test_raw_ownership_transfer_rejects_either_restricted_subject(client,database,monkeypatch,side,value):
    c=database[1];source,token=guest(c);aid=insert(c,source);saved=c.execute('SELECT * FROM attempts WHERE id=%s',(aid,)).fetchone()
    restrict(c,source if side=='source' else 'author',value);enable(c,monkeypatch)
    with pytest.raises(psycopg.errors.ObjectNotInPrerequisiteState):
        execute(c,"UPDATE attempts SET user_id='author' WHERE id=%s",(aid,))
    assert c.execute('SELECT * FROM attempts WHERE id=%s',(aid,)).fetchone()==saved
    assert activity(c)==[[],[]]


@pytest.mark.parametrize('side',['source','target'])
@pytest.mark.parametrize('value',[None,'under18','closed'])
def test_service_transfer_rechecks_both_subjects_without_mutating_history(client,database,monkeypatch,side,value):
    c=database[1];source,token=guest(c);aid=insert(c,source)
    c.execute("INSERT INTO attempt_assessments(attempt_id,input_hash,policy_version,payload) VALUES(%s,%s,'synthetic','{}')",(aid,uuid4().hex))
    saved=c.execute('SELECT * FROM attempts WHERE id=%s',(aid,)).fetchone()
    assessments=c.execute('SELECT * FROM attempt_assessments WHERE attempt_id=%s',(aid,)).fetchall()
    restrict(c,source if side=='source' else 'author',value);enable(c,monkeypatch)
    with pytest.raises(HTTPException) as exc:transfer(client,token)
    assert exc.value.status_code==403
    assert c.execute('SELECT * FROM attempts WHERE id=%s',(aid,)).fetchone()==saved
    assert c.execute('SELECT * FROM attempt_assessments WHERE attempt_id=%s',(aid,)).fetchall()==assessments
    assert c.execute('SELECT adopted_by FROM guest_credentials WHERE user_id=%s',(source,)).fetchone()==(None,)
    assert c.execute('SELECT count(*) FROM guest_transfer_receipts').fetchone()==(0,)


def test_proven_adult_guest_transfer_replay_preserves_assessments_and_no_awards(client,database,monkeypatch):
    c=database[1];source,token=guest(c);aid=insert(c,source)
    before=c.execute('SELECT id,at,canonical_id,scoring_snapshot FROM attempts WHERE id=%s',(aid,)).fetchone()
    c.execute("INSERT INTO attempt_assessments(attempt_id,input_hash,policy_version,payload) VALUES(%s,%s,'synthetic','{}')",(aid,uuid4().hex))
    assessments=c.execute('SELECT * FROM attempt_assessments WHERE attempt_id=%s',(aid,)).fetchall()
    enable(c,monkeypatch);result=transfer(client,token)
    assert result['counts']['attempts']==1 and transfer(client,token)==result
    assert c.execute('SELECT id,at,canonical_id,scoring_snapshot FROM attempts WHERE id=%s',(aid,)).fetchone()==before
    assert c.execute('SELECT * FROM attempt_assessments WHERE attempt_id=%s',(aid,)).fetchall()==assessments
    assert c.execute("SELECT sum(answered) FROM user_activity_daily WHERE user_id='author'").fetchone()==(1,)
    assert c.execute('SELECT count(*) FROM guest_transfer_receipts').fetchone()==(1,)
    assert c.execute('SELECT count(*) FROM reward_ledger').fetchone()==(0,)
    with pytest.raises(HTTPException) as exc:transfer(client,token,'outsider')
    assert exc.value.status_code==409


@pytest.mark.parametrize('side',['source','target'])
def test_busy_transfer_fails_before_credentials_or_ownership_locks(client,database,monkeypatch,side):
    c=database[1];source,token=guest(c);aid=insert(c,source);enable(c,monkeypatch)
    async def scenario():
        async with role() as held:
            await audience.learning_processing_lock(held,source if side=='source' else 'author',restricting=True)
            with pytest.raises(HTTPException) as exc:
                await asyncio.wait_for(account_identity.transfer_guest(SimpleNamespace(cookies={'ism_guest':token}),'author'),5)
            assert exc.value.status_code==409
            await held.execute('SELECT token_hash FROM guest_credentials WHERE user_id=%s FOR UPDATE NOWAIT',(source,))
            await held.execute("SELECT id FROM users WHERE id='author' FOR UPDATE NOWAIT")
    client.portal.call(scenario)
    assert c.execute('SELECT user_id FROM attempts WHERE id=%s',(aid,)).fetchone()==(source,)


@pytest.mark.parametrize('change',['category','delete','close'])
def test_direct_sql_restriction_fails_fast_while_processing_is_admitted(client,database,monkeypatch,change):
    c=database[1];enable(c,monkeypatch)
    async def scenario():
        async with role() as held:
            await held.execute("SELECT audience_processing_admit('author') AS admitted")
            assert (await held.fetchone())['admitted']
            async def restrict_now():
                async with role() as other:
                    if change=='category':await other.execute("UPDATE account_audience SET category='under18' WHERE user_id='author'")
                    elif change=='delete':
                        # App-role DELETE is intentionally denied by 0122. An
                        # operator's deletion still must obey the lease guard.
                        await other.execute('RESET ROLE')
                        await other.execute("DELETE FROM account_audience WHERE user_id='author'")
                    else:await other.execute("UPDATE users SET closed_at=now(),email=NULL,password_hash=NULL,name=NULL,avatar=NULL,email_verified_at=NULL,contribution_public=false WHERE id='author'")
            with pytest.raises(psycopg.errors.LockNotAvailable):await asyncio.wait_for(restrict_now(),5)
    client.portal.call(scenario)
    restrict(c,'author',{'category':'under18','delete':None,'close':'closed'}[change])
    insert(c);assert activity(c)==[[],[]]


def test_api_restriction_waits_for_sql_activity_then_blocks_later_activity(client,database,actor,monkeypatch):
    c=database[1];h=actor('author');enable(c,monkeypatch)
    async def scenario():
        async with role() as held:
            await held.execute("INSERT INTO attempts(user_id,canonical_id,correct,context) VALUES('author','cq_test',false,'practice')")
            task=asyncio.create_task(asyncio.to_thread(declare,client,'under18',headers=h,user_id='author',expected_version=1))
            try:await wait_for_advisory_wait(held,task)
            except BaseException:task.cancel();raise
        response=await asyncio.wait_for(task,5);assert response.status_code==200,response.text
    client.portal.call(scenario);saved=activity(c);insert(c);assert activity(c)==saved


@pytest.mark.parametrize('gate,app_flag',[(False,True),(True,False)])
def test_real_pool_startup_rejects_policy_mismatch_and_closes_new_pool(client,database,monkeypatch,gate,app_flag):
    c=database[1];c.execute('UPDATE audience_processing_policy SET enabled=%s',(gate,))
    monkeypatch.setattr(settings,'audience_gate_enabled',app_flag)
    async def scenario():
        original=db._pool
        try:
            with pytest.raises(RuntimeError,match='policies differ'):await db.open_pool()
            assert db._pool.closed
        finally:db._pool=original
    client.portal.call(scenario)


def test_application_cannot_change_or_remove_database_policy_or_spoof_guc(client,database,monkeypatch):
    c=database[1];restrict(c,'author','under18');enable(c,monkeypatch)
    for query in ('UPDATE audience_processing_policy SET enabled=false','DELETE FROM audience_processing_policy',"SELECT audience_restriction_guard()"):
        with pytest.raises(psycopg.errors.InsufficientPrivilege):execute(c,query)
    with c.transaction():
        c.execute('SET LOCAL ROLE mpsc');c.execute("SET LOCAL finna.audience_gate_enabled='off'")
        assert c.execute("SELECT audience_processing_admit('author')").fetchone()==(False,)
    insert(c);assert activity(c)==[[],[]]


def test_missing_policy_fails_closed(client,database):
    c=database[1];c.execute('DELETE FROM audience_processing_policy')
    with pytest.raises(psycopg.errors.RaiseException,match='policy is missing'):insert(c)
    assert c.execute('SELECT count(*) FROM attempts').fetchone()==(0,)


def test_service_rechecks_target_after_early_http_age_check(client,database,monkeypatch):
    c=database[1];source,token=guest(c);aid=insert(c,source);enable(c,monkeypatch)
    original=audience.require_learner
    async def check_then_restrict(user):
        await original(user)
        restrict(c,user,'under18')
    monkeypatch.setattr(audience,'require_learner',check_then_restrict)
    with pytest.raises(HTTPException) as exc:transfer(client,token)
    assert exc.value.status_code==403
    assert c.execute('SELECT user_id FROM attempts WHERE id=%s',(aid,)).fetchone()==(source,)


def test_unproved_or_expired_guest_cannot_transfer(client,database,monkeypatch):
    c=database[1];source,token=guest(c);aid=insert(c,source);enable(c,monkeypatch)
    for proof in ('unknown-synthetic-token',token):
        if proof==token:c.execute('UPDATE guest_credentials SET expires_at=now()-interval \'1 second\' WHERE user_id=%s',(source,))
        with pytest.raises(HTTPException) as exc:transfer(client,proof)
        assert exc.value.status_code==409
    with pytest.raises(psycopg.errors.ObjectNotInPrerequisiteState):
        execute(c,"UPDATE attempts SET user_id='author' WHERE id=%s",(aid,))
    assert c.execute('SELECT user_id FROM attempts WHERE id=%s',(aid,)).fetchone()==(source,)


def test_matching_enabled_policy_contract_validates(client,database,monkeypatch):
    from app.services.audience_database import validate_policy
    enable(database[1],monkeypatch)
    assert run(client,validate_policy) is None


def test_guest_cannot_be_used_as_registered_transfer_target(client,database,monkeypatch):
    c=database[1];source,token=guest(c);insert(c,source);enable(c,monkeypatch)
    with pytest.raises(HTTPException) as exc:transfer(client,token,source)
    assert exc.value.status_code==403
    assert c.execute('SELECT count(*) FROM guest_transfer_receipts').fetchone()==(0,)


def test_direct_activity_function_rechecks_the_admitted_owner_after_transfer(client,database,monkeypatch):
    c=database[1];aid=insert(c);enable(c,monkeypatch);barrier='synthetic-activity-owner:'+uuid4().hex
    async def scenario():
        async with role() as processor:
            await processor.execute('SELECT pg_backend_pid() AS pid');pid=(await processor.fetchone())['pid']
            # Instrument only this disposable DB/backend, between the first
            # ownership read and admission. Other SQL sessions run normally.
            c.execute('ALTER FUNCTION audience_processing_admit(text,boolean) RENAME TO audience_processing_admit_actual')
            c.execute(sql.SQL('''CREATE FUNCTION audience_processing_admit(uid text,allow_guest boolean DEFAULT false) RETURNS boolean
              LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $body$
              BEGIN
                IF pg_backend_pid()={} THEN PERFORM pg_advisory_xact_lock(hashtextextended({},0)); END IF;
                RETURN public.audience_processing_admit_actual(uid,allow_guest);
              END $body$''').format(sql.Literal(pid),sql.Literal(barrier)))
            c.execute('GRANT EXECUTE ON FUNCTION audience_processing_admit(text,boolean) TO mpsc')
            async with role() as held:
                await held.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))',(barrier,))
                task=asyncio.create_task(processor.execute('SELECT record_learning_activity(%s)',(aid,)))
                try:
                    await wait_for_advisory_wait(held,task)
                    execute(c,"UPDATE attempts SET user_id='outsider' WHERE id=%s",(aid,))
                    restrict(c,'outsider','under18')
                except BaseException:
                    task.cancel();await asyncio.gather(task,return_exceptions=True);raise
            await asyncio.wait_for(task,5)
    client.portal.call(scenario)
    assert c.execute("SELECT sum(answered) FROM user_activity_daily WHERE user_id='outsider'").fetchone()==(1,)
    assert c.execute('SELECT user_id FROM attempts WHERE id=%s',(aid,)).fetchone()==('outsider',)
