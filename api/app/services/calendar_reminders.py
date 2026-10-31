"""Bounded, retry-safe in-app reminders. No email or external push delivery."""

import asyncio
import logging
from ..db import cursor

log = logging.getLogger(__name__)


async def sweep(cur):
    # Receipt and inbox item are the same unique row: multiple workers/retries
    # cannot deliver twice. Follows and saved events form a deduplicated audience.
    await cur.execute("""WITH audience AS (
      SELECT s.user_id,s.event_id FROM user_calendar_saved s
      UNION SELECT b.user_id,e.id FROM user_exam_bookmarks b JOIN exam_calendar_events e ON e.collection_id=b.collection_id
    ), candidates AS (
      SELECT a.user_id,e.id,e.version,e.title,e.state,
       CASE WHEN e.state='archived' THEN 'withdrawn'
         WHEN e.updated_at>now()-interval '7 days' THEN 'update'
         WHEN e.starts_on=(now() AT TIME ZONE 'Asia/Kolkata')::date THEN 'today'
         WHEN e.starts_on=(now() AT TIME ZONE 'Asia/Kolkata')::date+1 THEN 'tomorrow'
         WHEN e.starts_on=(now() AT TIME ZONE 'Asia/Kolkata')::date+7 THEN 'week' END AS phase
      FROM audience a JOIN exam_calendar_events e ON e.id=a.event_id
      JOIN user_calendar_preferences p ON p.user_id=a.user_id AND p.reminders
      JOIN users u ON u.id=a.user_id AND u.email IS NOT NULL
      LEFT JOIN collections c ON c.id=e.collection_id
      WHERE (e.collection_id IS NULL OR c.visibility='public') AND e.published_at IS NOT NULL
       AND ((e.state='published' AND (e.starts_on IS NULL OR COALESCE(e.ends_on,e.starts_on)>=(now() AT TIME ZONE 'Asia/Kolkata')::date))
         OR (e.state='archived' AND e.updated_at>now()-interval '7 days'))
    ), deliveries AS (
      SELECT *, 'calendar:'||id||':'||version||':'||phase||':'||user_id AS key FROM candidates WHERE phase IS NOT NULL
    ) INSERT INTO review_notifications(user_id,calendar_event_id,event_key,message)
      SELECT user_id,id,key,
       CASE phase WHEN 'withdrawn' THEN 'Official calendar entry withdrawn: '
        WHEN 'today' THEN 'Calendar reminder · today: '
        WHEN 'tomorrow' THEN 'Calendar reminder · tomorrow: '
        WHEN 'week' THEN 'Calendar reminder · in 7 days: '
        ELSE 'New or updated official notice: ' END||title||'. Open the notice and confirm the official source.'
      FROM deliveries d WHERE NOT EXISTS(SELECT 1 FROM review_notifications n WHERE n.event_key=d.key)
      ORDER BY id,user_id LIMIT 500 ON CONFLICT(event_key) DO NOTHING""")
    # Date reminders also run for recently updated rows, independently from
    # update receipts, so an update cannot suppress a due-day reminder.
    await cur.execute("""WITH audience AS (
      SELECT user_id,event_id FROM user_calendar_saved
      UNION SELECT b.user_id,e.id FROM user_exam_bookmarks b JOIN exam_calendar_events e ON e.collection_id=b.collection_id
    ), due AS (
      SELECT a.user_id,e.id,e.version,e.title,e.starts_on-(now() AT TIME ZONE 'Asia/Kolkata')::date AS days
      FROM audience a JOIN exam_calendar_events e ON e.id=a.event_id
      JOIN user_calendar_preferences p ON p.user_id=a.user_id AND p.reminders
      JOIN users u ON u.id=a.user_id AND u.email IS NOT NULL
      LEFT JOIN collections c ON c.id=e.collection_id
      WHERE e.state='published' AND (e.collection_id IS NULL OR c.visibility='public')
       AND e.starts_on IN ((now() AT TIME ZONE 'Asia/Kolkata')::date,(now() AT TIME ZONE 'Asia/Kolkata')::date+1,(now() AT TIME ZONE 'Asia/Kolkata')::date+7)
    ), deliveries AS (
      SELECT *,'calendar:'||id||':'||version||':'||CASE days WHEN 0 THEN 'today' WHEN 1 THEN 'tomorrow' ELSE 'week' END||':'||user_id AS key FROM due
    ) INSERT INTO review_notifications(user_id,calendar_event_id,event_key,message)
      SELECT user_id,id,key,'Calendar reminder · '||CASE days WHEN 0 THEN 'today' WHEN 1 THEN 'tomorrow' ELSE 'in 7 days' END||': '||title||'. Confirm the latest official source.'
      FROM deliveries d WHERE NOT EXISTS(SELECT 1 FROM review_notifications n WHERE n.event_key=d.key)
      ORDER BY id,user_id LIMIT 500 ON CONFLICT(event_key) DO NOTHING""")


async def worker():
    while True:
        try:
            async with cursor() as cur:
                await sweep(cur)
        except Exception:
            log.exception("Calendar reminder sweep deferred")
        await asyncio.sleep(60)
