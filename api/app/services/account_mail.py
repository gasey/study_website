"""Built-in encrypted mail automation; durable conservative capacity reservations."""
import asyncio,hashlib,logging,smtplib,ssl
from email.message import EmailMessage
from email.utils import format_datetime
from urllib.parse import urlparse
from starlette.concurrency import run_in_threadpool
from ..config import settings
from ..db import cursor
from . import mfa,account_mail_release
from .account_identity import digest
log=logging.getLogger(__name__)


def configured():
    if not (account_mail_release.enabled() and settings.account_mail_enabled and settings.smtp_host and settings.smtp_from):return False
    try:mfa.cipher()
    except Exception:return False
    return True


def deliver(email,purpose,token,delivery_key=None,created_at=None):
    message=EmailMessage();message['From']=settings.smtp_from;message['To']=email
    message['Subject']='Reset your Study Map password' if purpose=='reset' else 'Verify your Study Map email'
    action='reset' if purpose=='reset' else 'verify'
    link=settings.public_origin+'/account/recovery#'+action+'='+token
    message.set_content('Open this link to '+('reset your password' if purpose=='reset' else 'verify your email')+':\n\n'+link+'\n\nThis link expires after 30 minutes and works once. If you did not request it, you can ignore this email.')
    if delivery_key:
        message['Message-ID']='<'+delivery_key+'@'+(urlparse(settings.public_origin).hostname or 'finna.invalid')+'>'
        if created_at:message['Date']=format_datetime(created_at)
        if settings.smtp_host.casefold()=='smtp.resend.com':message['Resend-Idempotency-Key']=delivery_key
    with smtplib.SMTP(settings.smtp_host,settings.smtp_port,timeout=10) as smtp:
        smtp.ehlo();smtp.starttls(context=ssl.create_default_context());smtp.ehlo()
        if settings.smtp_username:smtp.login(settings.smtp_username,settings.smtp_password)
        smtp.send_message(message)


async def beat(cur,note):
    await cur.execute("""INSERT INTO worker_heartbeats(worker,last_ok,note) VALUES('account-mail',clock_timestamp(),%s)
      ON CONFLICT(worker) DO UPDATE SET last_beat=clock_timestamp(),last_ok=clock_timestamp(),note=EXCLUDED.note""",(note,))


async def capacity(cur):
    # Count every committed reservation, even failed/uncertain SMTP outcomes.
    # Use the provider UTC day and a conservative31-day window, independent of
    # its account billing date. Include old sent mail once, without backfill.
    await cur.execute("""WITH bounds AS(SELECT
       date_trunc('day',statement_timestamp() AT TIME ZONE 'UTC') AT TIME ZONE 'UTC' AS day,
       statement_timestamp()-interval '31 days' AS month),
      usage AS(SELECT reserved_at AS at FROM account_mail_deliveries
       UNION ALL SELECT o.sent_at FROM account_mail_outbox o WHERE o.sent_at IS NOT NULL
         AND NOT EXISTS(SELECT 1 FROM account_mail_deliveries d WHERE d.outbox_id=o.id))
      SELECT count(*) FILTER(WHERE at>=bounds.day)::int AS day_used,
       count(*) FILTER(WHERE at>=bounds.month)::int AS month_used FROM bounds LEFT JOIN usage ON at>=bounds.month""")
    counts=await cur.fetchone()
    return {**counts,'daily_window':'utc_calendar_day','monthly_window':'rolling_31_days','daily_limit':settings.smtp_daily_limit,'monthly_limit':settings.smtp_monthly_limit,
            'day_remaining':max(0,settings.smtp_daily_limit-counts['day_used']),
            'month_remaining':max(0,settings.smtp_monthly_limit-counts['month_used'])}


async def accepting(cur,lock=False):
    if not configured():return False
    if lock:await cur.execute("SELECT pg_advisory_xact_lock(hashtext('account-mail-capacity-v1'))")
    budget=await capacity(cur)
    await cur.execute("""SELECT count(*)::int AS n FROM account_mail_outbox o JOIN users u ON u.id=o.user_id
      WHERE o.sent_at IS NULL AND o.token_cipher<>'' AND o.attempts<5 AND o.created_at>statement_timestamp()-interval '30 minutes'
        AND u.email IS NOT NULL AND u.closed_at IS NULL""")
    pending=(await cur.fetchone())['n']
    return pending<min(budget['day_remaining'],budget['month_remaining'])


async def reserve():
    # This transaction commits BEFORE SMTP, so process loss cannot return capacity.
    async with cursor() as cur:
        if not configured():await beat(cur,'disabled; delivery not configured or paused');return None
        await cur.execute("SELECT pg_advisory_xact_lock(hashtext('account-mail-capacity-v1'))")
        budget=await capacity(cur)
        if not budget['day_remaining'] or not budget['month_remaining']:
            await beat(cur,'sending budget exhausted; pending links keep their original expiry');return None
        await cur.execute("""SELECT o.*,u.email FROM account_mail_outbox o JOIN users u ON u.id=o.user_id
          WHERE o.sent_at IS NULL AND o.token_cipher<>'' AND o.attempts<5 AND o.next_attempt_at<=statement_timestamp()
            AND o.created_at>statement_timestamp()-interval '30 minutes' AND u.email IS NOT NULL AND u.closed_at IS NULL
          ORDER BY (o.purpose='reset') DESC,o.id FOR UPDATE OF o SKIP LOCKED LIMIT 1""")
        row=await cur.fetchone()
        if not row:await beat(cur,'idle; no deliverable account links');return None
        await cur.execute("""UPDATE account_mail_deliveries SET state='uncertain',finished_at=clock_timestamp(),error_type='LeaseExpired'
          WHERE outbox_id=%s AND state='reserved'""",(row['id'],))
        await cur.execute("""UPDATE account_mail_outbox SET attempts=attempts+1,next_attempt_at=clock_timestamp()+interval '5 minutes',last_error=NULL
          WHERE id=%s RETURNING attempts""",(row['id'],));row['attempts']=(await cur.fetchone())['attempts']
        await cur.execute('INSERT INTO account_mail_deliveries(outbox_id,attempt) VALUES(%s,%s) RETURNING id',(row['id'],row['attempts']))
        row['delivery_id']=(await cur.fetchone())['id']
        await beat(cur,'reserved account delivery capacity')
        return row


async def send_reserved(row):
    async with cursor() as cur:
        # Match closure/reset lock order: user before outbox. A closure can delete
        # the pending ciphertext between reservation and delivery; never send it.
        await cur.execute('SELECT email,closed_at FROM users WHERE id=%s FOR SHARE',(row['user_id'],));user=await cur.fetchone()
        await cur.execute('SELECT * FROM account_mail_outbox WHERE id=%s FOR UPDATE',(row['id'],));own=await cur.fetchone()
        await cur.execute('SELECT state FROM account_mail_deliveries WHERE id=%s FOR UPDATE',(row['delivery_id'],));attempt=await cur.fetchone()
        if not attempt or attempt['state']!='reserved':return
        paused=not configured()
        cancel=paused or not user or user['closed_at'] or not user['email'] or user['email']!=row['email'] or not own or own['sent_at'] or own['attempts']!=row['attempts'] or not own['token_cipher']
        if not cancel:
            try:raw=mfa.decrypt(row['user_id'],own['token_cipher'])
            except Exception:raw=None
            if raw:
                await cur.execute('''SELECT 1 FROM account_email_tokens WHERE token_hash=%s AND user_id=%s AND purpose=%s
                  AND consumed_at IS NULL AND expires_at>statement_timestamp()''',(digest(raw),row['user_id'],own['purpose']))
                cancel=not bool(await cur.fetchone())
            else:cancel=True
        if cancel:
            await cur.execute("UPDATE account_mail_deliveries SET state='cancelled',finished_at=clock_timestamp(),error_type='NotDeliverable' WHERE id=%s",(row['delivery_id'],))
            if own and not own['sent_at'] and own['attempts']==row['attempts'] and not paused:
                await cur.execute("UPDATE account_mail_outbox SET token_cipher='',last_error='Cancelled' WHERE id=%s",(row['id'],))
            await beat(cur,'cancelled unavailable or expired account link');return
        key='finna-account-'+hashlib.sha256((settings.public_origin+'|'+str(row['id'])+'|'+row['created_at'].isoformat()).encode()).hexdigest()
        try:await run_in_threadpool(deliver,user['email'],own['purpose'],raw,key,row['created_at'])
        except Exception as error:
            # An SMTP timeout can follow acceptance. Keep its capacity consumed and
            # the same provider idempotency key; never claim exactly-once delivery.
            kind=type(error).__name__[:100]
            state='failed' if isinstance(error,(smtplib.SMTPResponseException,smtplib.SMTPRecipientsRefused,ValueError,TypeError)) else 'uncertain'
            await cur.execute("UPDATE account_mail_deliveries SET state=%s,finished_at=clock_timestamp(),error_type=%s WHERE id=%s",(state,kind,row['delivery_id']))
            await cur.execute('UPDATE account_mail_outbox SET last_error=%s WHERE id=%s',(kind,row['id']))
            await beat(cur,'SMTP delivery failed; bounded retry retained')
        else:
            await cur.execute("UPDATE account_mail_deliveries SET state='sent',finished_at=clock_timestamp() WHERE id=%s",(row['delivery_id'],))
            await cur.execute("UPDATE account_mail_outbox SET sent_at=clock_timestamp(),token_cipher='',last_error=NULL WHERE id=%s",(row['id'],))
            await beat(cur,'account email accepted by SMTP; inbox delivery not certified')


async def tick():
    row=await reserve()
    if row:await send_reserved(row)


async def worker():
    while True:
        await asyncio.sleep(10)
        try:await tick()
        except asyncio.CancelledError:raise
        except Exception:
            # No exception body/recipient/token/credential is logged.
            log.warning('Account mail worker unavailable; durable queue retained')
            try:
                async with cursor() as cur:
                    await cur.execute("""INSERT INTO worker_heartbeats(worker,note) VALUES('account-mail','worker unavailable; inspect durable queue')
                      ON CONFLICT(worker) DO UPDATE SET last_beat=clock_timestamp(),note=EXCLUDED.note""")
            except Exception:pass  # DB unavailability is visible as a stale heartbeat.
