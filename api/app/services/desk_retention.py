"""Bounded cleanup of resolved report evidence and closed private desk content."""

import asyncio
import logging
from ..db import cursor
from .worker_health import beat, failed

log = logging.getLogger(__name__)


async def sweep(cur):
    await cur.execute(
        """UPDATE study_desk_reports SET snapshot='{}',reason='Retention period elapsed',resolution='Retained review metadata only'
      WHERE id IN(SELECT id FROM study_desk_reports WHERE state='resolved' AND retain_until<now() AND snapshot<>'{}'::jsonb ORDER BY id LIMIT 500 FOR UPDATE SKIP LOCKED)"""
    )
    counts = {'report_snapshots': cur.rowcount}
    for table in ["study_desk_items", "study_desk_messages"]:
        await cur.execute(
            "DELETE FROM "
            + table
            + " WHERE id IN(SELECT x.id FROM "
            + table
            + " x JOIN study_desks d ON d.id=x.desk_id WHERE d.closed_at<now()-interval '30 days' ORDER BY x.id LIMIT 500)"
        )
        counts[table] = cur.rowcount
    return counts


async def worker():
    while True:
        try:
            async with cursor() as cur:
                counts = await sweep(cur)
                await beat(cur, 'desk-retention', True, ', '.join(f'{k}={v}' for k,v in counts.items()))
        except Exception:
            await failed('desk-retention')
            log.warning(
                "Private desk retention sweep deferred; database availability should be checked"
            )
        await asyncio.sleep(3600)
