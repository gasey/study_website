"""Bounded, read-only calendar projections. Scheduling never creates study activity."""
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import logging
import re


class RedactFeedAccess(logging.Filter):
    """Keep calendar bearer credentials out of Uvicorn access-log records."""
    def filter(self, record):
        if isinstance(record.args, tuple):
            record.args = tuple(re.sub(r"/api/calendar/feed/[^ ?]+", "/api/calendar/feed/[redacted].ics", arg)
                                if isinstance(arg,str) else arg for arg in record.args)
        return True


_access_logger = logging.getLogger('uvicorn.access')
if not any(isinstance(f,RedactFeedAccess) for f in _access_logger.filters):
    _access_logger.addFilter(RedactFeedAccess())

FIELDS = 'id,date,title,note,kind,recurrence,collection_id,version,created_at,updated_at'


def india_today():
    return datetime.now(ZoneInfo('Asia/Kolkata')).date()


def occurrences(entries, start: date, end: date, today: date):
    """Expand upcoming slots only; missed slots disappear without a database write."""
    result = []
    for row in entries:
        day = row['date']
        cadence = row['recurrence']
        if cadence:
            floor = max(start, today)
            day += timedelta(days=max(0, (floor-day).days + cadence-1)//cadence*cadence)
        while start <= day <= end:
            result.append({'id': str(row['id']), 'day': day, 'title': row['title'],
                           'note': row['note'], 'kind': row['kind'],
                           'collection_id': row['collection_id'], 'version': row['version']})
            if not cadence:
                break
            day += timedelta(days=cadence)
    return sorted(result, key=lambda r: (r['day'], r['id']))


async def entries(cur, user):
    await cur.execute('SELECT '+FIELDS+' FROM calendar_entries WHERE user_id=%s ORDER BY date,id LIMIT 500', (user,))
    return await cur.fetchall()


async def layers(cur, user, start, end):
    rows = await entries(cur, user)
    return {'entries': rows, 'occurrences': occurrences(rows, start, end, india_today())}


def text(value):
    # Normalize every newline before escaping; user text can never add properties.
    return value.replace('\\', '\\\\').replace('\r\n', '\n').replace('\r', '\n').replace('\n', '\\n').replace(';', '\\;').replace(',', '\\,')


def fold(line):
    parts = []; part = ''; size = 0
    for char in line:
        length = len(char.encode('utf-8'))
        if size+length > 75:
            parts.append(part); part = ' '; size = 1
        part += char; size += length
    return '\r\n'.join(parts+[part])


def feed(rows, today):
    """RFC5545 all-day events, stable per-occurrence UIDs, private user entries only.

    Export all one-off entries and one year of future recurring suggestions.
    No RRULE: past missed suggestions must not reappear in subscribed calendars.
    Review projections/verified history use aggregate counts with stable daily UIDs.
    """
    projected = occurrences(rows, date(2000,1,1), today+timedelta(days=366), today)
    # Keep future one-off targets, even beyond the rolling recurring window.
    projected += occurrences([r for r in rows if not r['recurrence'] and r['date']>today+timedelta(days=366)],
                             today+timedelta(days=367), date(2100,12,31), today)
    lines = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//Finna//Private calendar//EN', 'CALSCALE:GREGORIAN']
    by_id = {str(r['id']): r for r in rows}
    for item in projected:
        row = by_id[item['id']]; day = item['day']
        stamp = row['updated_at'].astimezone(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        lines += ['BEGIN:VEVENT', f"UID:{item['id']}-{day:%Y%m%d}@calendar.finna",
                  f"SEQUENCE:{row['version']}", 'DTSTAMP:'+stamp, 'LAST-MODIFIED:'+stamp,
                  f'DTSTART;VALUE=DATE:{day:%Y%m%d}', f'DTEND;VALUE=DATE:{day+timedelta(days=1):%Y%m%d}',
                  'SUMMARY:'+text(item['title']), 'DESCRIPTION:'+text(item['note']),
                  'CLASS:PRIVATE', 'TRANSP:TRANSPARENT', 'END:VEVENT']
    return '\r\n'.join(map(fold, lines+['END:VCALENDAR']))+'\r\n'


async def learning_layers(cur, user, start, end):
    # Reuse the exact in-app eligibility policy; export never reveals questions.
    from . import mastery
    from ..routers.learning import not_assessed
    args={'user':user,'start':start,'end':end}
    from .review_queue import selection_sql
    await cur.execute('WITH items AS ('+selection_sql()+''') SELECT GREATEST(due_on,(now() AT TIME ZONE 'Asia/Kolkata')::date) AS day,count(*)::int AS count
      FROM items WHERE GREATEST(due_on,(now() AT TIME ZONE 'Asia/Kolkata')::date) BETWEEN %(start)s AND %(end)s
      GROUP BY day ORDER BY day''',{**args,'include_curated':True})
    forecast=await cur.fetchall()
    await cur.execute('''SELECT (e.at AT TIME ZONE 'Asia/Kolkata')::date AS day,count(*)::int AS count
      FROM ('''+mastery.VERIFIED_ACTIVITY+''' AND (a.at AT TIME ZONE 'Asia/Kolkata')::date BETWEEN %(start)s AND %(end)s) e
      WHERE e.outcome IN ('correct','wrong') AND e.at<=now() GROUP BY day ORDER BY day''',args)
    return forecast, await cur.fetchall()


async def subscription(cur, user):
    import hashlib
    today=india_today()
    rows=await entries(cur,user)
    forecast,habit=await learning_layers(cur,user,today-timedelta(days=366),today+timedelta(days=366))
    key=hashlib.sha256(user.encode()).hexdigest()
    stamp=datetime.now(timezone.utc)
    for kind,values in [('forecast',forecast),('habit',habit)]:
        for item in values:
            rows.append({'id':f"{key}-{kind}-{item['day']:%Y%m%d}",'date':item['day'],
              'title':f"{item['count']} projected reviews" if kind=='forecast' else f"{item['count']} verified checks",
              'note':'Projection only; dates shift as you answer. Overdue reviews appear today.' if kind=='forecast' else 'Past eligible activity. Display only.',
              'kind':'personal','recurrence':None,'collection_id':None,'version':0,'updated_at':stamp})
    return feed(rows,today)
