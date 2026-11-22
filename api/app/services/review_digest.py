"""Prospective opt-in reminders. Reuse the private due queue and mail capacity."""
import secrets
import smtplib
from email.message import EmailMessage
from fastapi import HTTPException
from psycopg.types.json import Jsonb
from starlette.concurrency import run_in_threadpool
from ..config import settings
from ..db import cursor
from . import account_mail, mfa, review_queue, learning_habit, audience
from .account_identity import digest


def available():
    return settings.review_digest_enabled and account_mail.configured()


async def clock(cur):
    await cur.execute("SELECT (now() AT TIME ZONE 'Asia/Kolkata')::date AS day,extract(hour FROM now() AT TIME ZONE 'Asia/Kolkata')::int AS hour")
    return await cur.fetchone()


def evening(stamp):
    return 18 <= stamp['hour'] < 22


async def status(cur, user):
    await cur.execute('''SELECT u.id AS user_id,u.email_verified_at IS NOT NULL AS verified,
      COALESCE(p.enabled,false) AS enabled,COALESCE(p.version,0) AS version
      FROM users u LEFT JOIN review_digest_preferences p ON p.user_id=u.id WHERE u.id=%s''', (user,))
    row = await cur.fetchone()
    return {**row, 'available': available(), 'time_zone': 'Asia/Kolkata', 'window': '18:00–22:00', 'max_per_day': 1}


async def consent(cur, user, version, enabled):
    # Same user -> preference -> outbox lock order as closure and delivery.
    await cur.execute('SELECT email,email_verified_at,closed_at FROM users WHERE id=%s FOR UPDATE', (user,))
    owner = await cur.fetchone()
    if not owner or owner['closed_at'] or not owner['email']:raise HTTPException(403, 'Sign in to manage email preferences.')
    if enabled and not await audience.eligible(cur,user):raise HTTPException(403,audience.MESSAGE)
    await cur.execute('SELECT * FROM review_digest_preferences WHERE user_id=%s FOR UPDATE', (user,))
    old = await cur.fetchone()
    if (old['version'] if old else 0) != version:raise HTTPException(409, 'Email preferences changed. Reload before saving.')
    if enabled and (not available() or not owner['email_verified_at']):
        raise HTTPException(409, 'Verify your email and wait for reminder availability before subscribing.')
    address = digest(owner['email'].strip().casefold())
    if old and old['enabled'] == enabled and (not enabled or old['email_hash']==address):return await status(cur, user)
    raw = secrets.token_urlsafe(32) if enabled else None
    token_hash = digest(raw) if raw else old['token_hash'] if old else None
    await cur.execute('''INSERT INTO review_digest_preferences(user_id,enabled,version,token_hash,token_cipher,email_hash)
      VALUES(%s,%s,%s,%s,%s,%s) ON CONFLICT(user_id) DO UPDATE SET enabled=EXCLUDED.enabled,
      version=EXCLUDED.version,token_hash=EXCLUDED.token_hash,token_cipher=EXCLUDED.token_cipher,
      email_hash=EXCLUDED.email_hash,updated_at=clock_timestamp()''',
      (user, enabled, version+1, token_hash, mfa.encrypt(user, raw) if raw else '', address if enabled else None))
    await cur.execute("UPDATE review_digest_outbox SET state='cancelled' WHERE user_id=%s AND state='pending'", (user,))
    await cur.execute("INSERT INTO account_security_events(user_id,action,detail) VALUES(%s,'review_digest_consent',%s)",
                      (user, Jsonb({'enabled': enabled, 'version': version+1})))
    return await status(cur, user)


async def unsubscribe(cur, token):
    await cur.execute('SELECT user_id FROM review_digest_preferences WHERE token_hash=%s', (digest(token),))
    row = await cur.fetchone()
    if not row:return
    user = row['user_id']
    await cur.execute('SELECT id FROM users WHERE id=%s FOR UPDATE', (user,))
    await cur.execute('SELECT enabled,version FROM review_digest_preferences WHERE user_id=%s AND token_hash=%s FOR UPDATE', (user, digest(token)))
    pref = await cur.fetchone()
    if not pref or not pref['enabled']:return
    await cur.execute("UPDATE review_digest_preferences SET enabled=false,version=version+1,token_cipher='',updated_at=clock_timestamp() WHERE user_id=%s", (user,))
    await cur.execute("UPDATE review_digest_outbox SET state='cancelled' WHERE user_id=%s AND state='pending'", (user,))
    await cur.execute("INSERT INTO account_security_events(user_id,action,detail) VALUES(%s,'review_digest_unsubscribed',%s)", (user, Jsonb({'version': pref['version']+1})))


async def due(cur, user):
    # No seeding, rollup, rewards, historical activity or new entitlement grants.
    await cur.execute('WITH items AS ('+review_queue.selection_sql()+''') SELECT count(*)::int AS n FROM items
      WHERE due_on<=(now() AT TIME ZONE 'Asia/Kolkata')::date''', {'user': user, 'include_curated': True})
    return (await cur.fetchone())['n']


async def schedule():
    if not available():return
    async with cursor() as cur:
        stamp = await clock(cur)
        if not evening(stamp):return
        await cur.execute("SET LOCAL statement_timeout='5s'")
        await cur.execute("SELECT pg_try_advisory_xact_lock(hashtext('review-digest-schedule-v1')) AS claimed")
        if not (await cur.fetchone())['claimed']:return
        # Bounded fair daily sweep; empty queues produce no outbox or email.
        await cur.execute('''SELECT p.user_id FROM review_digest_preferences p JOIN users u ON u.id=p.user_id
          WHERE p.enabled AND u.email_verified_at IS NOT NULL AND u.email IS NOT NULL AND u.closed_at IS NULL
          AND '''+audience.eligible_sql('u.id')+'''
          AND (p.last_checked_day IS NULL OR p.last_checked_day<%s)
          ORDER BY p.last_checked_day NULLS FIRST,p.user_id LIMIT 25''', (stamp['day'],))
        for candidate in await cur.fetchall():
            user = candidate['user_id']
            await cur.execute('SELECT email_verified_at,email,closed_at FROM users WHERE id=%s FOR UPDATE', (user,))
            owner = await cur.fetchone()
            if not owner or not await audience.eligible(cur,user):continue
            await cur.execute('SELECT * FROM review_digest_preferences WHERE user_id=%s FOR UPDATE', (user,))
            pref = await cur.fetchone()
            if not pref or not pref['enabled'] or owner['closed_at'] or not owner['email_verified_at'] or not owner['email']:continue
            if pref['email_hash']!=digest(owner['email'].strip().casefold()):continue
            if pref['last_checked_day'] and pref['last_checked_day']>=stamp['day']:continue
            await cur.execute('UPDATE review_digest_preferences SET last_checked_day=%s WHERE user_id=%s', (stamp['day'], user))
            if await due(cur, user):
                await cur.execute('''INSERT INTO review_digest_outbox(user_id,day,consent_version) VALUES(%s,%s,%s)
                  ON CONFLICT(user_id,day) DO NOTHING''', (user, stamp['day'], pref['version']))


async def reserve():
    async with cursor() as cur:
        if not available():return
        stamp = await clock(cur)
        if not evening(stamp):return
        await cur.execute("SELECT pg_advisory_xact_lock(hashtext('account-mail-capacity-v1'))")
        budget = await account_mail.capacity(cur)
        # Preserve headroom for security mail that arrives later in the day/month.
        daily_floor = min(10, max(1, budget['daily_limit']//10))
        monthly_floor = min(100, max(1, budget['monthly_limit']//10))
        if budget['day_remaining']<=daily_floor or budget['month_remaining']<=monthly_floor:return
        await cur.execute('''SELECT 1 FROM account_mail_outbox WHERE sent_at IS NULL AND token_cipher<>''
          AND attempts<5 AND created_at>now()-interval '30 minutes' LIMIT 1''')
        if await cur.fetchone():return
        await cur.execute('''UPDATE review_digest_outbox SET state='cancelled' WHERE state='pending' AND day<%s''', (stamp['day'],))
        # A crash may follow SMTP acceptance. Reminders never retry an uncertain
        # transmission: one committed attempt per IST day, then try a future day.
        await cur.execute("UPDATE review_digest_deliveries SET state='uncertain',finished_at=clock_timestamp(),error_type='LeaseExpired' WHERE state='reserved' AND outbox_id IN (SELECT id FROM review_digest_outbox WHERE attempts>0 AND next_attempt_at<=now())")
        await cur.execute("UPDATE review_digest_outbox SET state='cancelled' WHERE state='pending' AND attempts>0 AND next_attempt_at<=now()")
        await cur.execute('''SELECT o.* FROM review_digest_outbox o WHERE state='pending' AND day=%s
          AND '''+audience.eligible_sql('o.user_id')+'''
          AND attempts=0 AND next_attempt_at<=now() ORDER BY id FOR UPDATE SKIP LOCKED LIMIT 1''', (stamp['day'],))
        row = await cur.fetchone()
        if not row:return
        await cur.execute("UPDATE review_digest_deliveries SET state='uncertain',finished_at=clock_timestamp(),error_type='LeaseExpired' WHERE outbox_id=%s AND state='reserved'", (row['id'],))
        await cur.execute("UPDATE review_digest_outbox SET attempts=attempts+1,next_attempt_at=clock_timestamp()+interval '5 minutes',last_error=NULL WHERE id=%s RETURNING attempts", (row['id'],))
        row['attempts'] = (await cur.fetchone())['attempts']
        await cur.execute('INSERT INTO review_digest_deliveries(outbox_id,attempt) VALUES(%s,%s) RETURNING id', (row['id'], row['attempts']))
        row['delivery_id'] = (await cur.fetchone())['id']
        return row


def deliver(email, token, count, streak, key, created_at):
    message = EmailMessage()
    message['From'] = settings.smtp_from;message['To'] = email
    message['Subject'] = 'Your Finna reviews are ready'
    unsubscribe_url = settings.public_origin+'/api/review-digest/unsubscribe?token='+token
    message['List-Unsubscribe'] = '<'+unsubscribe_url+'>'
    message['List-Unsubscribe-Post'] = 'List-Unsubscribe=One-Click'
    message.set_content(f'{count} reviews are due. Your current study streak is {streak} days.\n\n'
                        +'Open Smart Review: '+settings.public_origin+'/revise?tab=review\n\n'
                        +'You chose evening review reminders. Unsubscribe without signing in: '
                        +unsubscribe_url)
    account_mail.send_message(message, key, created_at)


async def send_reserved(row):
    async with cursor() as cur:
        await cur.execute('SELECT email,email_verified_at,closed_at FROM users WHERE id=%s FOR UPDATE', (row['user_id'],))
        owner = await cur.fetchone()
        await cur.execute('SELECT * FROM review_digest_preferences WHERE user_id=%s FOR UPDATE', (row['user_id'],))
        pref = await cur.fetchone()
        await cur.execute('SELECT * FROM review_digest_outbox WHERE id=%s FOR UPDATE', (row['id'],))
        own = await cur.fetchone()
        await cur.execute('SELECT state FROM review_digest_deliveries WHERE id=%s FOR UPDATE', (row['delivery_id'],))
        attempt = await cur.fetchone()
        if not attempt or attempt['state']!='reserved':return
        stamp = await clock(cur)
        paused = not available()
        allowed = await audience.eligible(cur,row['user_id'])
        cancel = (paused or not allowed or not evening(stamp) or stamp['day']!=row['day'] or not owner or owner['closed_at']
                  or not owner['email'] or not owner['email_verified_at'] or not pref or not pref['enabled']
                  or pref['version']!=row['consent_version'] or not own or own['state']!='pending' or own['attempts']!=row['attempts'])
        if not cancel and pref['email_hash']!=digest(owner['email'].strip().casefold()):cancel=True
        count = 0 if cancel else await due(cur, row['user_id'])
        if cancel or not count:
            await cur.execute("UPDATE review_digest_deliveries SET state='cancelled',finished_at=clock_timestamp(),error_type='NotDeliverable' WHERE id=%s", (row['delivery_id'],))
            if own:await cur.execute("UPDATE review_digest_outbox SET state='cancelled' WHERE id=%s", (row['id'],))
            return
        try:
            raw = mfa.decrypt(row['user_id'], pref['token_cipher'])
            if digest(raw)!=pref['token_hash']:raise ValueError('Reminder token mismatch')
            streak = (await learning_habit.streak(cur, row['user_id']))['current_streak_days']
            key = 'review-digest-'+str(row['id'])
            await run_in_threadpool(deliver, owner['email'], raw, count, streak, key, row['created_at'])
        except Exception as error:
            kind = type(error).__name__[:80]
            state = 'failed' if isinstance(error, (smtplib.SMTPResponseException, smtplib.SMTPRecipientsRefused, ValueError, TypeError)) else 'uncertain'
            await cur.execute('UPDATE review_digest_deliveries SET state=%s,finished_at=clock_timestamp(),error_type=%s WHERE id=%s', (state, kind, row['delivery_id']))
            await cur.execute("UPDATE review_digest_outbox SET state='cancelled',last_error=%s WHERE id=%s", (kind, row['id']))
        else:
            await cur.execute("UPDATE review_digest_deliveries SET state='sent',finished_at=clock_timestamp() WHERE id=%s", (row['delivery_id'],))
            await cur.execute("UPDATE review_digest_outbox SET state='sent',sent_at=clock_timestamp(),last_error=NULL WHERE id=%s", (row['id'],))


async def tick():
    await schedule()
    row = await reserve()
    if row:await send_reserved(row)
