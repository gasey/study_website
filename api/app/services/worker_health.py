"""Small cycle receipts; success commits with work, failure follows rollback."""
import asyncio
import logging
from ..db import cursor

log = logging.getLogger(__name__)
WORKERS = {'score-reassessment','desk-retention','calendar-reminders','game-lifecycle','mastery-reconciler','account-retention'}


async def beat(cur, worker, ok, note):
    if worker not in WORKERS:
        raise ValueError('Unregistered worker')
    note = ('ok: ' if ok else 'failed: ') + note[:280]
    await cur.execute('''INSERT INTO worker_heartbeats(worker,last_beat,last_ok,note)
      VALUES(%s,clock_timestamp(),CASE WHEN %s THEN clock_timestamp() END,%s)
      ON CONFLICT(worker) DO UPDATE SET last_beat=clock_timestamp(),
        last_ok=CASE WHEN %s THEN clock_timestamp() ELSE worker_heartbeats.last_ok END,note=EXCLUDED.note''',
      (worker,ok,note,ok))


async def failed(worker, note='Cycle rolled back; inspect worker logs'):
    # No exception payloads, account identifiers or private job contents. A DB
    # outage leaves a stale receipt; do not make failure reporting unbounded.
    try:
        async with asyncio.timeout(2):
            async with cursor() as cur:
                await beat(cur, worker, False, note)
    except asyncio.CancelledError:
        raise
    except Exception:
        log.warning('Worker failure receipt unavailable; inspect heartbeat freshness')
