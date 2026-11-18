"""Commit/rollback and durable failure evidence using real PostgreSQL roles."""
import pytest
from app.db import cursor
from app.services import worker_health
from app.services.scoring_revisions import assessment_health


def run(client, fn, *args):return client.portal.call(fn,*args)


def test_actual_startup_cycles_log_counts_without_creating_rewards(client,database):
    async def startup_receipts():
        import asyncio
        async with asyncio.timeout(2):
            while True:
                async with cursor() as cur:
                    await cur.execute("SELECT worker,note FROM worker_heartbeats WHERE worker IN('desk-retention','calendar-reminders','game-lifecycle')")
                    rows={r['worker']:r['note'] for r in await cur.fetchall()}
                if len(rows)==3:return rows
                await asyncio.sleep(.01)
    rows=run(client,startup_receipts)
    assert len(rows)==3 and all(n.startswith('ok:') for n in rows.values())
    assert 'report_snapshots=' in rows['desk-retention'] and 'notifications inserted=' in rows['calendar-reminders']
    assert database[1].execute('SELECT count(*) FROM reward_ledger').fetchone()[0]==0



def test_failure_preserves_success_and_rollback_never_claims_a_cycle(client,database):
    async def scenario():
        async with cursor() as cur:
            await cur.execute('SET LOCAL ROLE mpsc')
            await worker_health.beat(cur,'desk-retention',True,'Completed synthetic cycle')
        async with cursor() as cur:
            await cur.execute("SELECT last_ok FROM worker_heartbeats WHERE worker='desk-retention'")
            prior=(await cur.fetchone())['last_ok']
        with pytest.raises(RuntimeError):
            async with cursor() as cur:
                await cur.execute('SET LOCAL ROLE mpsc')
                await worker_health.beat(cur,'desk-retention',True,'Must roll back')
                raise RuntimeError('Private synthetic exception body must not be saved')
        await worker_health.failed('desk-retention')
        async with cursor() as cur:
            await cur.execute("SELECT * FROM worker_heartbeats WHERE worker='desk-retention'")
            row=await cur.fetchone()
            assert row['last_ok']==prior and row['last_beat']>=prior
            assert row['note'].startswith('failed:') and 'Private' not in row['note']
            from app.services.ops import heartbeat
            assert heartbeat('x','x',3600,row,row['last_beat'])['state']=='attention'
    run(client,scenario)



def test_pending_failed_assessment_never_appears_healthy(client,database):
    conn=database[1]
    conn.execute("INSERT INTO assessment_jobs(canonical_id,failures) VALUES('cq_test',1) ON CONFLICT(canonical_id) DO UPDATE SET failures=1,finished_at=NULL")
    async def check():
        async with cursor() as cur:
            await cur.execute('SET LOCAL ROLE mpsc');await assessment_health(cur)
    run(client,check)
    assert conn.execute("SELECT note FROM worker_heartbeats WHERE worker='score-reassessment'").fetchone()[0].startswith('failed:')
    conn.execute("UPDATE assessment_jobs SET finished_at=now() WHERE canonical_id='cq_test'")
    run(client,check)
    assert conn.execute("SELECT note FROM worker_heartbeats WHERE worker='score-reassessment'").fetchone()[0].startswith('ok:')


def test_failure_reporting_is_bounded_and_cancellation_is_not_swallowed(client,monkeypatch):
    from contextlib import asynccontextmanager
    import asyncio
    @asynccontextmanager
    async def unavailable():
        raise RuntimeError('database unavailable')
        yield
    monkeypatch.setattr(worker_health,'cursor',unavailable)
    run(client,worker_health.failed,'desk-retention')
    @asynccontextmanager
    async def cancelled():
        raise asyncio.CancelledError()
        yield
    monkeypatch.setattr(worker_health,'cursor',cancelled)
    async def check():
        with pytest.raises(asyncio.CancelledError):await worker_health.failed('desk-retention')
    run(client,check)
