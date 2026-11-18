"""Real, read-only ops snapshots. Missing collection is never a healthy result."""
from datetime import datetime, timedelta
import json
from ..routers.billing import enabled as checkout_enabled
from .restore_health import observation as restore_observation

# Thresholds allow several normal cycles; desk retention runs hourly.
WORKERS = (
    ('score-reassessment', 'Assessment queue', 90),
    ('desk-retention', 'Private desk retention', 10800),
    ('account-retention', 'Account & transient receipt retention', 10800),
    ('calendar-reminders', 'Calendar reminders', 180),
    ('game-lifecycle', 'Game lifecycle', 30),
    ('account-mail', 'Account mail', 60),
    ('mastery-reconciler', 'Mastery reconciliation', 90),
    ('mastery-nightly', 'Nightly reconciliation enqueue', 90000),
)
TIMERS = (
    ('ism-oracle-bank-review', 'Bank review publication', 300),
    ('ism-workshop-backup', 'Paired recovery backup', 172800),
    ('ism-stats-refresh', 'Statistics refresh', 172800),
    ('finna-ops-host', 'Host evidence collection', 900),
)


def collected(row, now, kind):
    result={'state':'unknown','note':'Awaiting the first actual host collection.',
            'last_beat':None,'last_ok':None}
    if row is None:return result
    result.update(last_beat=row['last_beat'],last_ok=row['last_ok'])
    try:
        data=json.loads(row['note'] or '')
        if data.get('schema')!=1 or data.get('state') not in {'healthy','attention','unknown'}:
            raise ValueError('Invalid collection schema')
        result.update(state=data['state'],note=str(data['note'])[:280])
        if data['state']=='healthy' and (row['last_ok'] is None or (row['last_ok']-now).total_seconds()>30):
            raise ValueError('Missing or future successful collection')
        if kind=='disk' and data['state']=='healthy':
            free,total=data['free_bytes'],data['total_bytes']
            if type(free) is not int or type(total) is not int or not 0<=free<=total or total==0:
                raise ValueError('Invalid disk measurement')
            result.update(free_bytes=free,total_bytes=total)
            if free<10*1024**3:result['state']='attention'
        elif kind=='disk' and data['state']=='attention' and 'free_bytes' in data:
            free,total=data['free_bytes'],data['total_bytes']
            if type(free) is not int or type(total) is not int or not 0<=free<=total or total==0:
                raise ValueError('Invalid disk measurement')
            result.update(free_bytes=free,total_bytes=total)
        if kind=='backup' and data['state']=='healthy':
            stamp=datetime.fromisoformat(data['backup_at'])
            if stamp.tzinfo is None or stamp!=row['last_ok'] or data['verification']!='sha256_pair_and_dump_index':
                raise ValueError('Invalid verified backup receipt')
            result['backup_at']=stamp
            age=(now-stamp).total_seconds()
            if age < -30:result['state']='unknown'
            elif age>172800:result['state']='stale'
        age=(now-row['last_beat']).total_seconds()
        if age < -30:result['state']='unknown'
        elif age>900:result['state']='stale'
    except (TypeError,ValueError,KeyError,AttributeError):
        result.update(state='unknown',note='Invalid collection receipt; inspect host collector.')
    return result


def heartbeat(key, label, seconds, row, now):
    result = {'id': key, 'label': label, 'stale_after_seconds': seconds,
              'last_beat': None, 'last_ok': None, 'note': None, 'state': 'unknown'}
    if row is None:
        return result
    result.update({k: row[k] for k in ('last_beat', 'last_ok', 'note')})
    age = (now - row['last_beat']).total_seconds()
    # Clock skew is unknown; a future timestamp must not make a worker green.
    if age < -30 or (row['last_ok'] and (row['last_ok']-now).total_seconds()>30):
        result['state'] = 'unknown'
    elif age > seconds:
        result['state'] = 'stale'
    elif (row['note'] or '').startswith('failed:') or row['last_ok'] is None or row['last_ok'] < row['last_beat'] - timedelta(milliseconds=100):
        result['state'] = 'attention'
    else:
        result['state'] = 'healthy'
    return result


async def snapshot(cur, pool):
    await cur.execute("SELECT statement_timestamp() AS now, (now() AT TIME ZONE 'Asia/Kolkata')::date-1 AS yesterday")
    clock = await cur.fetchone()
    now, day = clock['now'], clock['yesterday']
    keys = [w[0] for w in WORKERS] + ['timer:' + t[0] for t in TIMERS] + ['probe:disk','probe:backup','restore-rehearsal']
    await cur.execute('SELECT worker,last_beat,last_ok,note FROM worker_heartbeats WHERE worker=ANY(%s)', (keys,))
    rows = {r['worker']: r for r in await cur.fetchall()}
    workers = [heartbeat(k, label, seconds, rows.get(k), now) for k, label, seconds in WORKERS]
    # Older reassessment health proves only its reported transaction, not a new
    # standardized successful-cycle receipt. Keep it separate and labelled.
    await cur.execute("SELECT seen_at,status FROM review_worker_health WHERE worker_id='score-reassessment'")
    assessment = await cur.fetchone()
    if not workers[0]['last_beat']:workers[0]['legacy_observation'] = assessment
    timers=[]
    for k,label,seconds in TIMERS:
        row=rows.get('timer:'+k)
        item=heartbeat('timer:'+k,label,seconds,row,now)
        if row:
            try:
                data=json.loads(row['note'] or '')
                if data.get('schema')!=1 or data.get('state') not in {'healthy','attention','unknown'}:raise ValueError()
                item['note']=str(data['note'])[:280]
                # Collector event time precedes its peer-DB write. Its structured
                # outcome, not the in-process100ms stamp tolerance, proves success.
                if item['state'] not in {'unknown','stale'}:
                    item['state']=data['state'] if data['state']!='healthy' or row['last_ok'] is not None else 'attention'
            except (ValueError,TypeError,KeyError,AttributeError):
                item.update(state='unknown',note='Invalid outcome receipt; inspect collector.')
        else:item['note']='Collector installed; awaiting the next actual job outcome.'
        timers.append(item)
    await cur.execute('''SELECT COALESCE(sum(GREATEST(points,0)),0)::bigint AS minted_points,
      COALESCE(sum(GREATEST(xp,0)),0)::bigint AS minted_xp, count(*)::int AS receipts
      FROM reward_ledger WHERE created_at >= %s::date::timestamp AT TIME ZONE 'Asia/Kolkata'
       AND created_at < (%s::date+1)::timestamp AT TIME ZONE 'Asia/Kolkata' ''', (day, day))
    economy = await cur.fetchone()
    await cur.execute('''SELECT count(*)::int AS redemptions,COALESCE(sum(points),0)::bigint AS redeemed_points
      FROM reward_redemptions WHERE created_at >= %s::date::timestamp AT TIME ZONE 'Asia/Kolkata'
       AND created_at < (%s::date+1)::timestamp AT TIME ZONE 'Asia/Kolkata' ''', (day, day))
    economy.update(await cur.fetchone())
    await cur.execute('''SELECT count(*)::int AS cap_accounts FROM reward_daily_counters
      WHERE day=%s AND (xp>=300 OR points>=25)''', (day,))
    economy.update(await cur.fetchone())
    await cur.execute('''SELECT user_id,count(*)::int AS days FROM reward_daily_counters
      WHERE day BETWEEN %s::date-6 AND %s AND (xp>=300 OR points>=25)
      GROUP BY user_id HAVING count(*)=7 ORDER BY user_id LIMIT 51''', (day, day))
    cap = await cur.fetchall()
    await cur.execute('''SELECT c.user_id,c.points,c.xp FROM reward_daily_counters c JOIN users u ON u.id=c.user_id
      WHERE c.day=%s AND c.points>=20 AND u.closed_at IS NULL
       AND (u.created_at AT TIME ZONE 'Asia/Kolkata')::date BETWEEN %s::date-6 AND %s
      ORDER BY c.points DESC,c.xp DESC,c.user_id LIMIT 51''', (day, day, day))
    velocity = await cur.fetchall()
    economy.update({'day': day, 'cap_streaks': cap[:50], 'cap_streaks_more': len(cap)>50,
                    'new_account_velocity': velocity[:50], 'new_account_velocity_more': len(velocity)>50,
                    'velocity_rule': 'At least 20 points yesterday; account created within the seven IST calendar days ending yesterday.',
                    'cap_rule': 'At least 25 points or 300 XP in the recorded learning daily counter. Streaks end yesterday.',
                    'mint_rule': 'Positive ledger amounts across all reward kinds; adjustments included. No netting against spending.'})
    await cur.execute('''WITH reports AS (
      SELECT 'questions' AS queue,created_at FROM content_reports WHERE status IN ('open','confirmed')
      UNION ALL SELECT 'discussions',created_at FROM abuse_reports WHERE status='open'
      UNION ALL SELECT 'materials',created_at FROM material_reports WHERE state='open'
      UNION ALL SELECT 'creators',created_at FROM creator_reports WHERE state='open'
      UNION ALL SELECT 'private desks',created_at FROM study_desk_reports WHERE state='open'
    ) SELECT queue,count(*)::int AS open,
      percentile_cont(.5) WITHIN GROUP(ORDER BY EXTRACT(epoch FROM (statement_timestamp()-created_at))/3600) AS median_hours,
      count(*) FILTER(WHERE created_at<statement_timestamp()-interval '48 hours')::int AS over_48h
      FROM reports GROUP BY queue ORDER BY queue''')
    moderation = await cur.fetchall()
    by_queue = {r['queue']: r for r in moderation}
    moderation = [by_queue.get(q, {'queue':q,'open':0,'median_hours':None,'over_48h':0})
                  for q in ('questions','discussions','materials','creators','private desks')]
    probes = {'api': 'responding', 'database': 'query succeeded', 'pool': pool,
              'pool_scope': 'This API process; the snapshot request holds one connection.',
              'disk': collected(rows.get('probe:disk'),now,'disk'),
              'backup': collected(rows.get('probe:backup'),now,'backup'),
              'webhooks': {'state':'not_collected' if checkout_enabled() else 'disabled', 'count_24h':None}}
    return {'observed_at':now, 'workers':workers, 'timers':timers, 'probes':probes,
            'economy':economy, 'moderation':moderation, 'read_only':True,
            'restore_rehearsal':restore_observation(rows.get('restore-rehearsal'),now)}
