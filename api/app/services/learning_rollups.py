"""Durable learning jobs, incremental answer updates and nightly reconciliation."""
import asyncio
import logging
from ..db import cursor
from . import mastery, review_queue, audience
from ..config import settings
from .worker_health import beat, failed

log = logging.getLogger(__name__)


async def record(cur,user,attempt):
    if not await mastery.account(cur,user):
        return
    # The attempt trigger already owns this row; preserve that lock order.
    await cur.execute('SELECT * FROM learning_rollup_jobs WHERE user_id=%s FOR UPDATE',(user,))
    job = await cur.fetchone()
    if job['initialized_at'] is None:
        await review_queue.seed(cur,user)
        await cur.execute('UPDATE learning_rollup_jobs SET initialized_at=clock_timestamp() WHERE user_id=%s',(user,))
    await review_queue.apply_attempt(cur,attempt)
    await cur.execute('SELECT canonical_id FROM attempts WHERE id=%s',(attempt,))
    await mastery.refresh(cur,user,(await cur.fetchone())['canonical_id'],award_attempt_ids=[attempt])


class _SkipCandidate(Exception):
    pass


async def claim_job(cur):
    if not settings.audience_gate_enabled:
        await cur.execute('''SELECT * FROM learning_rollup_jobs WHERE processed_version<requested_version AND failures<5
          ORDER BY requested_at,user_id LIMIT 1 FOR UPDATE SKIP LOCKED''')
        return await cur.fetchone()
    # Do not lock the job before the account's processing lease: restrictions
    # acquire that lease before their user lock, while answer triggers own jobs.
    # A bounded lookahead keeps a busy oldest account from blocking its peers.
    await cur.execute('''SELECT j.user_id FROM learning_rollup_jobs j JOIN users u ON u.id=j.user_id
      WHERE j.processed_version<j.requested_version AND j.failures<5
       AND u.email IS NOT NULL AND u.closed_at IS NULL AND '''+audience.eligible_sql('j.user_id')+'''
      ORDER BY j.requested_at,j.user_id LIMIT 10''')
    for candidate in await cur.fetchall():
        user=candidate['user_id']
        try:
            async with cur.connection.transaction():
                if not await audience.learning_processing_lock(cur,user):raise _SkipCandidate
                # Fresh snapshot after the lease. A declaration may have won
                # between candidate selection and lease acquisition.
                await cur.execute('''SELECT j.* FROM learning_rollup_jobs j JOIN users u ON u.id=j.user_id
                  WHERE j.user_id=%s AND j.processed_version<j.requested_version AND j.failures<5
                   AND u.email IS NOT NULL AND u.closed_at IS NULL AND '''+audience.eligible_sql('j.user_id')+'''
                  FOR UPDATE OF j SKIP LOCKED''',(user,))
                job=await cur.fetchone()
                if not job:raise _SkipCandidate
                return job
        except _SkipCandidate:
            # Rollback releases locks from a skipped candidate; none is held
            # until outer commit merely because another worker owns its job.
            continue
    return None


async def process_one(cur):
    job = await claim_job(cur)
    if not job:
        return False
    user = job['user_id']
    try:
        async with cur.connection.transaction():
            if job['initialized_at'] is None:
                await review_queue.seed(cur,user)
            else:
                await cur.execute('SELECT id FROM attempts WHERE user_id=%s AND id>%s ORDER BY id',(user,job['attempt_cursor']))
                for a in await cur.fetchall():
                    await review_queue.apply_attempt(cur,a['id'])
            await review_queue.reconcile(cur,user)
            await mastery.refresh(cur,user)
            from .activity_progress import reconcile
            await reconcile(cur,user)
            await cur.execute('''UPDATE learning_rollup_jobs SET initialized_at=COALESCE(initialized_at,clock_timestamp()),
              attempt_cursor=COALESCE((SELECT max(id) FROM attempts WHERE user_id=%s),0),
              processed_version=%s,failures=0,last_error=NULL WHERE user_id=%s''',(user,job['requested_version'],user))
    except Exception:
        await cur.execute("UPDATE learning_rollup_jobs SET failures=failures+1,last_error='Learning reconciliation failed; operator investigation required' WHERE user_id=%s",(user,))
        raise
    return True


async def cycle(cur):
    await cur.execute("INSERT INTO worker_heartbeats(worker,note) VALUES('mastery-reconciler','processing') ON CONFLICT(worker) DO UPDATE SET last_beat=clock_timestamp(),note='processing'")
    # One enqueue per IST day, serialized across API processes. Each user's job
    # remains small and independently retryable; no unbounded nightly transaction.
    await cur.execute("SELECT pg_try_advisory_xact_lock(hashtext('mastery-nightly')) AS locked")
    if (await cur.fetchone())['locked']:
        await cur.execute("SELECT last_ok FROM worker_heartbeats WHERE worker='mastery-nightly' AND (last_ok AT TIME ZONE 'Asia/Kolkata')::date=(now() AT TIME ZONE 'Asia/Kolkata')::date")
        if not await cur.fetchone():
            await cur.execute('''INSERT INTO learning_rollup_jobs(user_id) SELECT id FROM users WHERE email IS NOT NULL
              AND '''+audience.eligible_sql('users.id')+'''
              AND (EXISTS(SELECT 1 FROM attempts a WHERE a.user_id=users.id)
                OR EXISTS(SELECT 1 FROM user_topic_mastery m WHERE m.user_id=users.id))
              ORDER BY id ON CONFLICT(user_id) DO UPDATE SET requested_version=learning_rollup_jobs.requested_version+1,
              requested_at=clock_timestamp(),failures=0,last_error=NULL''')
            await cur.execute("INSERT INTO worker_heartbeats(worker,last_ok,note) VALUES('mastery-nightly',clock_timestamp(),'Reconciliation enqueued') ON CONFLICT(worker) DO UPDATE SET last_beat=clock_timestamp(),last_ok=clock_timestamp(),note=EXCLUDED.note")
    for _ in range(10):
        if not await process_one(cur):
            break
    note='Reconciliation cycle complete'
    if settings.audience_gate_enabled:
        await cur.execute('''SELECT count(*)::int AS n FROM learning_rollup_jobs j JOIN users u ON u.id=j.user_id
          WHERE j.processed_version<j.requested_version AND u.email IS NOT NULL AND u.closed_at IS NULL
          AND NOT '''+audience.eligible_sql('j.user_id'))
        paused=(await cur.fetchone())['n']
        if paused:note+=f'; {paused} age-restricted jobs remain pending'
    await beat(cur, 'mastery-reconciler', True, note)


async def worker():
    while True:
        await asyncio.sleep(15)
        try:
            async with cursor() as cur:
                # Persist failures and the beat even when a job's savepoint fails.
                try:
                    await cycle(cur)
                except Exception:
                    await beat(cur, 'mastery-reconciler', False, 'Learning job failed; inspect learning_rollup_jobs')
                    log.exception('Learning reconciliation failed')
        except asyncio.CancelledError:
            raise
        except Exception:
            await failed('mastery-reconciler')
            log.exception('Learning reconciler unavailable; durable jobs retained')
