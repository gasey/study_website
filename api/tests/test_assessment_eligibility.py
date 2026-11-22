"""Real-role assessment/correction admission; synthetic records only."""
import asyncio
from uuid import uuid4
import pytest
from psycopg.types.json import Jsonb
from app.config import settings
from app.services import scoring_revisions as scoring,correction_notices as notices,assessment_audience as guard,audience,account_tools
from test_learning_eligibility import role_cursor,run,wait_for_advisory_wait
from test_learning_workflows import learner,official
from test_account_privacy import declare


@pytest.fixture(scope='module',autouse=True)
def manual_workers():
    from app import main
    async def idle():await asyncio.Event().wait()
    with pytest.MonkeyPatch.context() as patch:
        for name in ('assessment_worker','learning_worker','game_worker'):patch.setattr(main,name,idle)
        yield


@pytest.fixture(autouse=True)
def independent_queues(database,monkeypatch):
    c=database[1]
    for table in ('assessment_jobs','new_score_jobs','question_change_events'):
        c.execute('UPDATE '+table+' SET finished_at=now() WHERE finished_at IS NULL')
    monkeypatch.setattr(settings,'audience_gate_enabled',False)


def case(database,actor,category='adult',q=None):
    c=database[1];user,h=learner(database,actor)
    if not q:q,_,_=official(database)
    if category:c.execute('INSERT INTO account_audience(user_id,category) VALUES(%s,%s)',(user,category))
    snap={'question':'Synthetic learning question','options':['A','B','C','D'],'answer_text':'B','answer_source':'official','context_basis':'synthetic-frozen'}
    aid=c.execute("INSERT INTO attempts(user_id,canonical_id,correct,chosen_text,context,scoring_snapshot) VALUES(%s,%s,true,'B','practice',%s) RETURNING id",(user,q,Jsonb(snap))).fetchone()[0]
    return user,h,q,aid


def source_job(c,q):
    c.execute("INSERT INTO assessment_jobs(canonical_id,requested_at) VALUES(%s,'1900-01-01') ON CONFLICT(canonical_id) DO UPDATE SET requested_at='1900-01-01',mock_cursor=NULL,attempt_cursor=0,finished_at=NULL,failures=0,last_error=NULL",(q,))
    return {'canonical_id':q,'mock_cursor':None,'attempt_cursor':0}


def correction(c,q):
    c.execute("UPDATE canonical_questions SET explanation=%s WHERE id=%s",('Synthetic correction '+uuid4().hex,q))
    return c.execute('SELECT id FROM question_change_events WHERE question_id=%s ORDER BY id DESC LIMIT 1',(q,)).fetchone()[0]


def outputs(c,user):
    return {'attempts':c.execute('SELECT * FROM attempts WHERE user_id=%s ORDER BY id',(user,)).fetchall(),
      'assessments':c.execute('SELECT x.* FROM attempt_assessments x JOIN attempts a ON a.id=x.attempt_id WHERE a.user_id=%s ORDER BY x.id',(user,)).fetchall(),
      'mocks':c.execute('SELECT x.* FROM mock_assessments x JOIN mock_sessions m ON m.id=x.mock_id WHERE m.user_id=%s ORDER BY x.id',(user,)).fetchall(),
      'notices':c.execute('SELECT * FROM review_notifications WHERE user_id=%s ORDER BY id',(user,)).fetchall(),
      'ledger':c.execute('SELECT * FROM reward_ledger WHERE user_id=%s ORDER BY id',(user,)).fetchall()}


@pytest.mark.parametrize('category',[None,'under18'])
def test_source_batch_preserves_restricted_cursor_and_history(client,actor,database,monkeypatch,category):
    c=database[1];u,_,q,_=case(database,actor,category);job=source_job(c,q)
    before=c.execute('SELECT * FROM assessment_jobs WHERE canonical_id=%s',(q,)).fetchone();saved=outputs(c,u)
    monkeypatch.setattr(settings,'audience_gate_enabled',True)
    assert run(client,scoring.process_job,job) is False
    assert c.execute('SELECT * FROM assessment_jobs WHERE canonical_id=%s',(q,)).fetchone()==before
    assert outputs(c,u)==saved


def test_mixed_batch_rolls_back_earlier_adult_and_resumes_once_after_confirmation(client,actor,database,monkeypatch):
    c=database[1];u,_,q,aid=case(database,actor);v,_,_,bid=case(database,actor,None,q)
    job=source_job(c,q);original=c.execute('SELECT * FROM assessment_jobs WHERE canonical_id=%s',(q,)).fetchone()
    monkeypatch.setattr(settings,'audience_gate_enabled',True)
    assert run(client,scoring.process_job,job) is False
    assert c.execute('SELECT count(*) FROM attempt_assessments WHERE attempt_id=ANY(%s)',([aid,bid],)).fetchone()==(0,)
    assert c.execute('SELECT * FROM assessment_jobs WHERE canonical_id=%s',(q,)).fetchone()==original
    c.execute("INSERT INTO account_audience(user_id,category) VALUES(%s,'adult')",(v,))
    assert run(client,scoring.process_job,job) is True
    assert c.execute('SELECT count(*) FROM attempt_assessments WHERE attempt_id=ANY(%s)',([aid,bid],)).fetchone()==(2,)
    saved=[outputs(c,x) for x in (u,v)]
    assert run(client,scoring.process_job,job) is False
    assert [outputs(c,x) for x in (u,v)]==saved


def test_actual_pending_worker_looks_past_restricted_source_job(client,actor,database,monkeypatch):
    c=database[1];_,_,q,aid=case(database,actor,'under18');source_job(c,q)
    _,_,other,bid=case(database,actor);source_job(c,other)
    c.execute("UPDATE assessment_jobs SET requested_at='1901-01-01' WHERE canonical_id=%s",(other,))
    monkeypatch.setattr(settings,'audience_gate_enabled',True)
    assert run(client,scoring.process_pending) is True
    assert c.execute('SELECT count(*) FROM attempt_assessments WHERE attempt_id=%s',(aid,)).fetchone()==(0,)
    assert c.execute('SELECT count(*) FROM attempt_assessments WHERE attempt_id=%s',(bid,)).fetchone()==(1,)
    assert c.execute('SELECT finished_at FROM assessment_jobs WHERE canonical_id=%s',(q,)).fetchone()==(None,)


@pytest.mark.parametrize('category',[None,'under18'])
def test_individual_queue_is_not_acknowledged_or_failed(client,actor,database,monkeypatch,category):
    c=database[1];u,_,_,aid=case(database,actor,category)
    before=c.execute('SELECT * FROM new_score_jobs WHERE attempt_id=%s',(aid,)).fetchone();saved=outputs(c,u)
    monkeypatch.setattr(settings,'audience_gate_enabled',True);run(client,scoring.process_new_jobs)
    assert c.execute('SELECT * FROM new_score_jobs WHERE attempt_id=%s',(aid,)).fetchone()==before
    assert outputs(c,u)==saved


def test_appearance_integrity_invalidation_continues_and_other_individual_runs(client,actor,database,monkeypatch):
    c=database[1];_,_,q,aid=case(database,actor,'under18');_,_,_,bid=case(database,actor)
    source_job(c,q);c.execute("UPDATE assessment_jobs SET mock_cursor='retained',attempt_cursor=999,finished_at=now() WHERE canonical_id=%s",(q,))
    app=c.execute('SELECT id FROM appearances WHERE canonical_id=%s',(q,)).fetchone()[0]
    c.execute('INSERT INTO new_score_jobs(appearance_id) VALUES(%s) ON CONFLICT(appearance_id) DO UPDATE SET finished_at=NULL',(app,))
    monkeypatch.setattr(settings,'audience_gate_enabled',True);run(client,scoring.process_new_jobs)
    assert c.execute('SELECT mock_cursor,attempt_cursor,finished_at FROM assessment_jobs WHERE canonical_id=%s',(q,)).fetchone()==(None,0,None)
    assert c.execute('SELECT finished_at IS NOT NULL FROM new_score_jobs WHERE appearance_id=%s',(app,)).fetchone()==(True,)
    assert c.execute('SELECT count(*) FROM attempt_assessments WHERE attempt_id=%s',(aid,)).fetchone()==(0,)
    assert c.execute('SELECT count(*) FROM attempt_assessments WHERE attempt_id=%s',(bid,)).fetchone()==(1,)


@pytest.mark.parametrize('category',[None,'under18'])
def test_notice_page_retains_cursor_and_creates_no_notice(client,actor,database,monkeypatch,category):
    c=database[1];u,_,q,_=case(database,actor,category);eid=correction(c,q)
    before=c.execute('SELECT * FROM question_change_events WHERE id=%s',(eid,)).fetchone();saved=outputs(c,u)
    monkeypatch.setattr(settings,'audience_gate_enabled',True)
    assert run(client,notices._process,eid) is False
    assert c.execute('SELECT * FROM question_change_events WHERE id=%s',(eid,)).fetchone()==before
    assert outputs(c,u)==saved


def test_mixed_notice_page_rolls_back_then_resumes_and_deduplicates(client,actor,database,monkeypatch):
    c=database[1];u,_,q,_=case(database,actor);v,_,_,_=case(database,actor,None,q);eid=correction(c,q)
    first,last=sorted((u,v))
    c.execute('DELETE FROM account_audience WHERE user_id=ANY(%s)',([u,v],))
    c.execute("INSERT INTO account_audience(user_id,category) VALUES(%s,'adult')",(first,))
    v=last
    monkeypatch.setattr(settings,'audience_gate_enabled',True)
    assert run(client,notices._process,eid) is False
    assert c.execute('SELECT count(*) FROM review_notifications WHERE question_change_id=%s',(eid,)).fetchone()==(0,)
    c.execute("INSERT INTO account_audience(user_id,category) VALUES(%s,'adult')",(v,))
    assert run(client,notices._process,eid) is True
    assert c.execute('SELECT count(*) FROM review_notifications WHERE question_change_id=%s',(eid,)).fetchone()==(2,)
    c.execute("UPDATE question_change_events SET recipient_cursor='',finished_at=NULL WHERE id=%s",(eid,))
    assert run(client,notices._process,eid) is True
    assert c.execute('SELECT count(*) FROM review_notifications WHERE question_change_id=%s',(eid,)).fetchone()==(2,)


def test_actual_notice_worker_looks_past_restricted_event(client,actor,database,monkeypatch):
    c=database[1];_,_,q,_=case(database,actor,'under18');blocked=correction(c,q)
    _,_,q2,_=case(database,actor);eligible=correction(c,q2)
    monkeypatch.setattr(settings,'audience_gate_enabled',True)
    assert run(client,notices.process) is True
    assert c.execute('SELECT finished_at FROM question_change_events WHERE id=%s',(blocked,)).fetchone()==(None,)
    assert c.execute('SELECT count(*) FROM review_notifications WHERE question_change_id=%s',(eligible,)).fetchone()==(1,)


@pytest.mark.parametrize('kind',['source','notice','individual'])
def test_busy_lease_defers_and_releases_queue_and_earlier_account_locks(client,actor,database,monkeypatch,kind):
    c=database[1];u,_,q,_=case(database,actor);v,_,_,bid=case(database,actor,'adult',q)
    job=source_job(c,q);eid=correction(c,q)
    individual=c.execute('SELECT id FROM new_score_jobs WHERE attempt_id=%s',(bid,)).fetchone()[0]
    if kind=='notice':u,v=sorted((u,v))
    monkeypatch.setattr(settings,'audience_gate_enabled',True)
    async def scenario():
        async with role_cursor() as exclusive:
            await audience.learning_processing_lock(exclusive,v,restricting=True)
            async with role_cursor() as worker:
                if kind=='individual':
                    await asyncio.wait_for(scoring.process_new_jobs(worker),5)
                    await exclusive.execute('SELECT 1 FROM new_score_jobs WHERE id=%s FOR UPDATE NOWAIT',(individual,))
                    return
                fn=scoring.process_job if kind=='source' else notices._process
                assert await asyncio.wait_for(fn(worker,job if kind=='source' else eid),5) is False
                await exclusive.execute('SELECT pg_try_advisory_xact_lock(hashtextextended(%s,0)) AS claimed',('audience-learning-processing-v1:'+u,))
                assert (await exclusive.fetchone())['claimed']
                table='assessment_jobs' if kind=='source' else 'question_change_events'
                field='canonical_id' if kind=='source' else 'id'
                await exclusive.execute('SELECT 1 FROM '+table+' WHERE '+field+'=%s FOR UPDATE NOWAIT',(q if kind=='source' else eid,))
    client.portal.call(scenario)


@pytest.mark.parametrize('kind',['attempt','notice'])
def test_under18_declaration_waits_for_admitted_processing(client,actor,database,monkeypatch,kind):
    c=database[1];u,h,q,aid=case(database,actor);eid=correction(c,q)
    monkeypatch.setattr(settings,'audience_gate_enabled',True)
    async def scenario():
        async with role_cursor() as worker:
            if kind=='attempt':await scoring.assess_attempt(worker,aid)
            else:assert await notices._process(worker,eid)
            task=asyncio.create_task(asyncio.to_thread(declare,client,'under18',headers=h,user_id=u,expected_version=1))
            try:await wait_for_advisory_wait(worker,task)
            except BaseException:task.cancel();raise
        response=await asyncio.wait_for(task,5);assert response.status_code==200,response.text
    client.portal.call(scenario)
    before=outputs(c,u)
    with pytest.raises(guard.Paused):run(client,scoring.assess_attempt,aid)
    assert outputs(c,u)==before


def test_closed_account_is_parked_without_deleting_originals(client,actor,database,monkeypatch):
    c=database[1];u,_,q,aid=case(database,actor);job=source_job(c,q);eid=correction(c,q)
    monkeypatch.setattr(settings,'audience_gate_enabled',True);run(client,account_tools.close,u,0)
    before=outputs(c,u)
    assert run(client,scoring.process_job,job) is False
    # Closure removes the email: the original recipient query excludes it.
    # An empty fanout can finish without creating a notice or assessment.
    assert run(client,notices._process,eid) is True
    assert outputs(c,u)==before


def test_flag_off_preserves_unknown_age_processing(client,actor,database):
    c=database[1];u,_,q,aid=case(database,actor,None);job=source_job(c,q);eid=correction(c,q)
    assert run(client,scoring.process_job,job) is True
    assert run(client,notices._process,eid) is True
    assert c.execute('SELECT count(*) FROM attempt_assessments WHERE attempt_id=%s',(aid,)).fetchone()==(1,)
    assert c.execute('SELECT count(*) FROM review_notifications WHERE question_change_id=%s',(eid,)).fetchone()==(1,)


def test_health_reports_pending_without_marking_restriction_a_failure(client,actor,database,monkeypatch):
    c=database[1];_,_,q,_=case(database,actor,'under18');source_job(c,q)
    monkeypatch.setattr(settings,'audience_gate_enabled',True);run(client,scoring.assessment_health)
    row=c.execute("SELECT last_ok IS NOT NULL,note FROM worker_heartbeats WHERE worker='score-reassessment'").fetchone()
    assert row[0] and 'pending queues=' in row[1] and 'retain cursors' in row[1]


def mock_case(c,u,q):
    mid='audience-mock-'+uuid4().hex
    c.execute("INSERT INTO mock_sessions(id,user_id,collection_id,question_ids,duration_seconds,submitted_at,elapsed_seconds,n_correct,n_wrong,n_skipped,score) VALUES(%s,%s,'ldc',ARRAY[%s],60,now(),10,0,0,1,0)",(mid,u,q))
    snap={'question':'Synthetic learning question','options':['A','B','C','D'],'answer_text':'A','answer_source':'official','context_basis':'synthetic-frozen'}
    c.execute('INSERT INTO mock_session_questions(mock_id,position,canonical_id,options,snapshot) VALUES(%s,0,%s,%s,%s)',(mid,q,Jsonb(snap['options']),Jsonb(snap)))
    c.execute('INSERT INTO new_score_jobs(mock_id) VALUES(%s) ON CONFLICT DO NOTHING',(mid,))
    return mid


@pytest.mark.parametrize('category',[None,'under18'])
def test_mock_assessment_and_its_notice_are_parked_then_resume_once(client,actor,database,monkeypatch,category):
    c=database[1];u,_,q,_=case(database,actor,category);mid=mock_case(c,u,q)
    before=outputs(c,u);original=c.execute('SELECT * FROM mock_sessions WHERE id=%s',(mid,)).fetchone()
    job=c.execute('SELECT * FROM new_score_jobs WHERE mock_id=%s',(mid,)).fetchone()
    monkeypatch.setattr(settings,'audience_gate_enabled',True)
    with pytest.raises(guard.Paused):run(client,scoring.assess_mock,mid)
    run(client,scoring.process_new_jobs)
    assert outputs(c,u)==before
    assert c.execute('SELECT * FROM new_score_jobs WHERE mock_id=%s',(mid,)).fetchone()==job
    if category:
        # Fixture-only category adjustment: real under18 self-upgrades remain denied.
        c.execute("UPDATE account_audience SET category='adult' WHERE user_id=%s",(u,))
    else:c.execute("INSERT INTO account_audience(user_id,category) VALUES(%s,'adult')",(u,))
    run(client,scoring.process_new_jobs);saved=outputs(c,u)
    assert len(saved['mocks'])==1 and len(saved['notices'])==1
    run(client,scoring.assess_mock,mid)
    assert outputs(c,u)==saved
    assert c.execute('SELECT * FROM mock_sessions WHERE id=%s',(mid,)).fetchone()==original


def test_assessment_failure_rolls_back_batch_and_keeps_original_cursor(client,actor,database,monkeypatch):
    c=database[1];u,_,q,aid=case(database,actor);job=source_job(c,q)
    before=c.execute('SELECT * FROM assessment_jobs WHERE canonical_id=%s',(q,)).fetchone()
    original=scoring._assess_attempt
    async def fail_after_write(cur,attempt_id):
        await original(cur,attempt_id)
        raise RuntimeError('Synthetic assessment failure after write')
    monkeypatch.setattr(scoring,'_assess_attempt',fail_after_write)
    monkeypatch.setattr(settings,'audience_gate_enabled',True)
    with pytest.raises(RuntimeError,match='Synthetic'):run(client,scoring.process_job,job)
    assert c.execute('SELECT * FROM assessment_jobs WHERE canonical_id=%s',(q,)).fetchone()==before
    assert c.execute('SELECT count(*) FROM attempt_assessments WHERE attempt_id=%s',(aid,)).fetchone()==(0,)
    assert run(client,scoring.process_pending) is False
    assert c.execute('SELECT mock_cursor,attempt_cursor,failures FROM assessment_jobs WHERE canonical_id=%s',(q,)).fetchone()==(None,0,1)


def test_closure_waits_for_admitted_assessment(client,actor,database,monkeypatch):
    c=database[1];u,_,_,aid=case(database,actor)
    monkeypatch.setattr(settings,'audience_gate_enabled',True)
    async def close():
        async with role_cursor() as other:await account_tools.close(other,u,0)
    async def scenario():
        async with role_cursor() as worker:
            await scoring.assess_attempt(worker,aid)
            task=asyncio.create_task(close())
            try:await wait_for_advisory_wait(worker,task)
            except BaseException:task.cancel();raise
        await asyncio.wait_for(task,5)
    client.portal.call(scenario)
    assert c.execute('SELECT closed_at IS NOT NULL FROM users WHERE id=%s',(u,)).fetchone()==(True,)
    with pytest.raises(guard.Paused):run(client,scoring.assess_attempt,aid)


def test_restriction_winning_after_target_selection_is_observed(client,actor,database,monkeypatch):
    c=database[1];u,h,_,aid=case(database,actor);before=outputs(c,u)
    original=audience.learning_processing_lock
    monkeypatch.setattr(settings,'audience_gate_enabled',True)
    async def scenario():
        selected=asyncio.Event();resume=asyncio.Event()
        async def delayed(cur,user,*,restricting=False):
            if user==u and not restricting:
                selected.set();await resume.wait()
            return await original(cur,user,restricting=restricting)
        monkeypatch.setattr(audience,'learning_processing_lock',delayed)
        async def assess():
            async with role_cursor() as cur:await scoring.assess_attempt(cur,aid)
        task=asyncio.create_task(assess())
        await asyncio.wait_for(selected.wait(),5)
        try:
            response=await asyncio.to_thread(declare,client,'under18',headers=h,user_id=u,expected_version=1)
            assert response.status_code==200,response.text
        finally:resume.set()
        with pytest.raises(guard.Paused):await asyncio.wait_for(task,5)
    client.portal.call(scenario)
    assert outputs(c,u)==before


def test_flag_off_worker_still_skips_locked_oldest_job(client,actor,database):
    c=database[1];_,_,q,_=case(database,actor,None);source_job(c,q)
    _,_,other,bid=case(database,actor,None);source_job(c,other)
    c.execute("UPDATE assessment_jobs SET requested_at='1901-01-01' WHERE canonical_id=%s",(other,))
    async def scenario():
        async with role_cursor() as locker:
            await locker.execute('SELECT 1 FROM assessment_jobs WHERE canonical_id=%s FOR UPDATE',(q,))
            async with role_cursor() as worker:assert await scoring.process_pending(worker) is True
    client.portal.call(scenario)
    assert c.execute('SELECT count(*) FROM attempt_assessments WHERE attempt_id=%s',(bid,)).fetchone()==(1,)
