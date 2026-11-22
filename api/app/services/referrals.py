"""Prospective, launch-gated access grants. Never changes currency or plans."""
import logging,secrets
from fastapi import HTTPException
from psycopg.types.json import Jsonb
from ..config import settings
from ..db import cursor
from . import reward_economy


async def launch_ready(cur):
    # Includes published legal pages, completed delivered recovery, live paid
    # checkout and source-bound/current economy checks. No provider request.
    return (await reward_economy.feature_gates(cur))['catalog_ready']


async def available(cur):
    return settings.referral_rewards_enabled and await launch_ready(cur)


async def clock(cur):
    await cur.execute('SELECT clock_timestamp() AS at')
    return (await cur.fetchone())['at']


async def code_eligible(cur,code):
    await cur.execute('''SELECT c.* FROM referral_codes c JOIN users u ON u.id=c.user_id
      WHERE c.code=%s AND c.enabled AND u.closed_at IS NULL AND u.email IS NOT NULL AND u.email_verified_at IS NOT NULL''',(code,))
    return await cur.fetchone()


async def public(cur,code):
    return {'available':bool(await available(cur) and await code_eligible(cur,code)),
            'days_each':7,'scored_attempts_required':10,'yearly_referrer_cap':5}


async def attempts(cur,user,since):
    from .learning_habit import QUALIFIED
    from ..routers.learning import not_assessed
    await cur.execute('''WITH eligible AS ('''+QUALIFIED+''') SELECT a.id FROM eligible a
      JOIN canonical_questions q ON q.id=a.canonical_id WHERE a.outcome IN ('correct','wrong')
      AND a.at>=%(since)s AND a.at<=clock_timestamp() AND '''+not_assessed('q')+'''
      ORDER BY a.id LIMIT 10''',{'user':user,'since':since})
    return [r['id'] for r in await cur.fetchall()]


async def status(cur,user):
    live=await available(cur)
    await cur.execute('SELECT email_verified_at IS NOT NULL AND email IS NOT NULL AND closed_at IS NULL AS verified FROM users WHERE id=%s',(user,))
    verified=bool((await cur.fetchone() or {}).get('verified'))
    await cur.execute('SELECT code,enabled,version FROM referral_codes WHERE user_id=%s',(user,));code=await cur.fetchone()
    await cur.execute('''SELECT c.created_at,d.state FROM referral_claims c LEFT JOIN referral_decisions d USING(referred_id)
      WHERE c.referred_id=%s''',(user,));claim=await cur.fetchone()
    progress=len(await attempts(cur,user,claim['created_at'])) if claim and not claim['state'] else 10 if claim and claim['state'] in ('credited','capped') else 0
    await cur.execute("SELECT count(*)::int AS n FROM referral_decisions WHERE referrer_id=%s AND state='credited' AND decided_at>clock_timestamp()-interval '1 year'",(user,));credited=(await cur.fetchone())['n']
    return {'user_id':user,'available':live,'verified':verified,'code':code,'credited_this_rolling_year':credited,
            'days_each':7,'scored_attempts_required':10,'yearly_referrer_cap':5,
            'signup_referral':{'state':claim['state'] or 'pending','scored_attempts':progress} if claim else None}


async def set_code(cur,user,version,enabled):
    await cur.execute('SELECT email,email_verified_at,closed_at FROM users WHERE id=%s FOR UPDATE',(user,));owner=await cur.fetchone()
    await cur.execute('SELECT * FROM referral_codes WHERE user_id=%s FOR UPDATE',(user,));old=await cur.fetchone()
    if (old['version'] if old else 0)!=version:raise HTTPException(409,'Your invitation changed. Reload before saving.')
    if enabled and (not await available(cur) or not owner or owner['closed_at'] or not owner['email_verified_at']):raise HTTPException(409,'Invitation rewards are not available for this account yet.')
    if not old and not enabled:return await status(cur,user)
    if old and old['enabled']==enabled:return await status(cur,user)
    await cur.execute('''INSERT INTO referral_codes(user_id,code,enabled) VALUES(%s,%s,true)
      ON CONFLICT(user_id) DO UPDATE SET enabled=%s,version=referral_codes.version+1''',
      (user,old['code'] if old else secrets.token_urlsafe(18),enabled))
    await cur.execute("INSERT INTO account_security_events(user_id,action,detail) VALUES(%s,'referral_invitation_changed',%s)",(user,Jsonb({'enabled':enabled,'version':version+1})))
    return await status(cur,user)


async def attach_signup(cur,user,code):
    if not code:return None
    if not await available(cur):return {'state':'unavailable'}
    # Optional attribution cannot break account creation when a link is revoked
    # concurrently. A savepoint keeps the already-created signup transaction.
    try:
        async with cur.connection.transaction():
            invitation=await code_eligible(cur,code)
            if not invitation or invitation['user_id']==user:return {'state':'unavailable'}
            await cur.execute('''INSERT INTO referral_claims(referred_id,referrer_id,invite_code,invite_version)
              VALUES(%s,%s,%s,%s)''',(user,invitation['user_id'],code,invitation['version']))
            await cur.execute("INSERT INTO account_security_events(user_id,action) VALUES(%s,'referral_attached_at_signup')",(user,))
            return {'state':'pending'}
    except Exception:
        logging.getLogger(__name__).warning('Optional signup referral unavailable; no deferred attribution')
        return {'state':'unavailable'}


async def grant(cur,user,key,stamp):
    await cur.execute('''SELECT GREATEST(%s::timestamptz,
      CASE WHEN plan_code='pro' THEN plan_ends_at END,
      CASE WHEN plan_status='trial' THEN trial_ends_at END,
      (SELECT max(ends_at) FROM billing_access_grants WHERE user_id=u.id),
      (SELECT max(ends_at) FROM reward_redemptions WHERE user_id=u.id)) AS starts
      FROM users u WHERE id=%s''',(stamp,user))
    start=(await cur.fetchone())['starts']
    await cur.execute('''INSERT INTO billing_access_grants(user_id,granted_by,idempotency_key,days,starts_at,ends_at,source)
      VALUES(%s,NULL,%s,7,%s,%s+interval '7 days','referral') RETURNING id''',(user,key,start,start))
    return (await cur.fetchone())['id']


async def decide(cur,claim):
    if not await available(cur):return False
    inviter=claim['referrer_id'];friend=claim['referred_id'];stamp=await clock(cur)
    await cur.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s,0))",('referral-cap:'+inviter,))
    # Same access stacking locks as owner grants/checkout, with both IDs sorted.
    for prefix in ('billing-checkout:','rewards:'):
        for user in sorted((inviter,friend)):await cur.execute('SELECT pg_advisory_xact_lock(hashtext(%s))',(prefix+user,))
    await cur.execute('SELECT id,email,email_verified_at,closed_at FROM users WHERE id=ANY(%s) ORDER BY id FOR SHARE',([inviter,friend],));users=await cur.fetchall()
    await cur.execute('SELECT 1 FROM referral_decisions WHERE referred_id=%s',(friend,))
    if await cur.fetchone():return False
    if len(users)!=2 or any(not u['email'] or u['closed_at'] for u in users):
        await cur.execute("INSERT INTO referral_decisions(referred_id,referrer_id,state,decided_at) VALUES(%s,%s,'closed',%s)",(friend,inviter,stamp));return True
    if any(not u['email_verified_at'] for u in users):return False
    ids=await attempts(cur,friend,claim['created_at'])
    if len(ids)<10:return False
    await cur.execute("SELECT count(*)::int AS n FROM referral_decisions WHERE referrer_id=%s AND state='credited' AND decided_at>%s::timestamptz-interval '1 year'",(inviter,stamp))
    if (await cur.fetchone())['n']>=5:
        await cur.execute("INSERT INTO referral_decisions(referred_id,referrer_id,state,decided_at,attempt_ids) VALUES(%s,%s,'capped',%s,%s)",(friend,inviter,stamp,ids));return True
    giver=await grant(cur,inviter,'referral:'+friend+':referrer',stamp)
    receiver=await grant(cur,friend,'referral:'+friend+':referred',stamp)
    await cur.execute("""INSERT INTO referral_decisions(referred_id,referrer_id,state,decided_at,attempt_ids,referrer_grant_id,referred_grant_id)
      VALUES(%s,%s,'credited',%s,%s,%s,%s)""",(friend,inviter,stamp,ids,giver,receiver))
    for user in (inviter,friend):
        await cur.execute("INSERT INTO account_security_events(user_id,action,detail) VALUES(%s,'referral_pro_days_granted',%s)",(user,Jsonb({'days':7,'source':'referral'})))
        await cur.execute("INSERT INTO review_notifications(user_id,event_key,message,category) VALUES(%s,%s,'A qualified invitation added 7 Pro days. View Plan & billing for your access dates.','system') ON CONFLICT(event_key) DO NOTHING",(user,'referral:'+friend+':'+user))
    return True


async def tick():
    if not settings.referral_rewards_enabled:return
    async with cursor() as cur:
        if not await available(cur):return
        await cur.execute('''SELECT c.referred_id FROM referral_claims c WHERE NOT EXISTS(
          SELECT 1 FROM referral_decisions d WHERE d.referred_id=c.referred_id)
          ORDER BY last_checked_at NULLS FIRST,created_at,referred_id LIMIT 25''')
        candidates=await cur.fetchall()
    # One transaction per claim. A batch must never accumulate cap/access locks
    # for unrelated inviters in a different order from another worker's batch.
    for row in candidates:
        async with cursor() as cur:
            await cur.execute("SET LOCAL statement_timeout='10s'")
            await cur.execute('''SELECT c.* FROM referral_claims c WHERE referred_id=%s AND NOT EXISTS(
              SELECT 1 FROM referral_decisions d WHERE d.referred_id=c.referred_id)
              FOR UPDATE OF c SKIP LOCKED''',(row['referred_id'],))
            claim=await cur.fetchone()
            if not claim:continue
            await decide(cur,claim)
            await cur.execute('UPDATE referral_claims SET last_checked_at=clock_timestamp() WHERE referred_id=%s',(claim['referred_id'],))
