"""Hourly bounded cleanup; closed-account study-history deletion is separately gated."""
import asyncio
import logging
from ..db import cursor
from .worker_health import beat,failed

log=logging.getLogger(__name__)


async def sessions(cur,table):
    assert table in ('auth_sessions','mobile_sessions')
    # A mobile credential is unusable when its parent is gone/revoked/expired.
    orphan=""" OR NOT EXISTS(SELECT 1 FROM auth_sessions s WHERE s.token_hash=x.parent_session_hash
      AND s.revoked_at IS NULL AND s.expires_at>now())""" if table=='mobile_sessions' else ''
    await cur.execute('''WITH expired AS (
      SELECT x.token_hash FROM '''+table+''' x WHERE
       (x.expires_at<now()-interval '7 days' OR x.revoked_at<now()-interval '7 days' '''+orphan+''')
       AND x.created_at<now()-interval '7 days'
      ORDER BY x.created_at,x.token_hash LIMIT 500 FOR UPDATE SKIP LOCKED
    ),deleted AS (
      DELETE FROM '''+table+''' x USING expired e WHERE x.token_hash=e.token_hash RETURNING x.user_id,x.created_at
    ),retained AS (
      INSERT INTO account_security_events(user_id,action,created_at,detail)
      SELECT user_id,'session_activity_retained',max(created_at),jsonb_build_object('source',%s::text)
      FROM deleted d GROUP BY user_id HAVING max(created_at)>COALESCE(
       (SELECT max(e.created_at) FROM account_security_events e WHERE e.user_id=d.user_id AND e.action='session_activity_retained'),'-infinity'::timestamptz)
      RETURNING id
    ) SELECT (SELECT count(*)::int FROM deleted) AS removed,(SELECT count(*)::int FROM retained) AS retained''',(table,))
    return await cur.fetchone()


async def sweep(cur):
    await cur.execute("SET LOCAL statement_timeout='5s'")
    await cur.execute("SET LOCAL lock_timeout='1s'")
    await cur.execute("SELECT pg_try_advisory_xact_lock(hashtext('account-retention-v1')) AS claimed")
    if not (await cur.fetchone())['claimed']:return {'claimed':False}
    mobile=await sessions(cur,'mobile_sessions');web=await sessions(cur,'auth_sessions')
    counts={'web':web['removed'],'mobile':mobile['removed'],'activity':web['retained']+mobile['retained']}
    # Request keys here are scoped by server IST date. Removing older dates
    # cannot admit a replay into the current day's budget. Economic receipts,
    # practice_request_receipts, game starts and adoption receipts never expire.
    await cur.execute('''DELETE FROM rate_limits WHERE (user_id,action,ist_date) IN(
      SELECT user_id,action,ist_date FROM rate_limits WHERE ist_date<(now() AT TIME ZONE 'Asia/Kolkata')::date-30
      AND updated_at<now()-interval '30 days' ORDER BY ist_date,user_id,action LIMIT 500 FOR UPDATE SKIP LOCKED)''')
    counts['daily_requests']=cur.rowcount
    await cur.execute('''DELETE FROM account_closure_recovery WHERE user_id IN(
      SELECT user_id FROM account_closure_recovery WHERE expires_at<=clock_timestamp()
      ORDER BY expires_at,user_id LIMIT 500 FOR UPDATE SKIP LOCKED)''')
    counts['closure_recovery_expired']=cur.rowcount
    for table,key,expired in (
        ('review_rate_buckets','bucket',"expires_at<now()-interval '1 day'"),
        ('auth_login_attempts','ctid',"attempted_at<now()-interval '30 days'"),
        ('google_auth_flows','token_hash',"expires_at<now()-interval '7 days'"),
        ('mobile_auth_flows','id',"expires_at<now()-interval '7 days'")):
        # Historical login-attempt rows are append-only to the app: DELETE does
        # not need an UPDATE grant just to claim them. The worker advisory lock
        # already serializes sweeps, and statement/lock limits remain bounded.
        locking='' if table in ('auth_login_attempts','google_auth_flows') else ' FOR UPDATE SKIP LOCKED'
        await cur.execute('DELETE FROM '+table+' WHERE '+expired+' AND '+key+' IN(SELECT '+key+' FROM '+table+' WHERE '+expired+' ORDER BY '+key+' LIMIT 500'+locking+')')
        counts[{'review_rate_buckets':'budgets','auth_login_attempts':'login_attempts','google_auth_flows':'google_flows','mobile_auth_flows':'mobile_flows'}[table]]=cur.rowcount
    await cur.execute('SELECT * FROM sweep_empty_guests(true)');guests=await cur.fetchone()
    counts.update(guests=guests['removed'],guests_scanned=guests['scanned'])
    from ..config import settings
    if settings.study_history_retention_enabled:
        await cur.execute('SELECT sweep_expired_study_history(5,200) AS result')
        study=await cur.fetchone()
        counts.update(study_history=study['result'])
        if settings.private_study_retention_enabled:
            await cur.execute('SELECT sweep_expired_private_study(5,200) AS result')
            private=await cur.fetchone()
            counts['private_study']=private['result']
            if settings.private_preferences_retention_enabled:
                await cur.execute('SELECT sweep_expired_private_preferences(5,200) AS result')
                prefs=await cur.fetchone()
                counts['private_preferences']=prefs['result']
            else:
                counts['private_preferences']='disabled'
        else:
            counts['private_study']='disabled'
            counts['private_preferences']='disabled'
    else:
        counts['study_history']='disabled'
        counts['private_study']='disabled'
        counts['private_preferences']='disabled'
    if settings.audience_gate_enabled:
        await cur.execute('DELETE FROM audience_browser_flows WHERE token_hash IN(SELECT token_hash FROM audience_browser_flows WHERE expires_at<now() ORDER BY expires_at LIMIT 500)')
        counts['audience_flows']=cur.rowcount
    return counts


async def worker():
    while True:
        try:
            async with cursor() as cur:
                counts=await sweep(cur)
                await beat(cur,'account-retention',True,', '.join(f'{k}={v}' for k,v in counts.items()))
        except Exception:
            await failed('account-retention')
            log.warning('Account retention deferred; inspect operational health')
        await asyncio.sleep(3600)
