"""Encrypted durable outbox; no sending until explicitly configured/enabled."""
import asyncio,smtplib,ssl
from email.message import EmailMessage
from starlette.concurrency import run_in_threadpool
from ..config import settings
from ..db import cursor
from . import mfa

def configured():
    if not (settings.account_mail_enabled and settings.smtp_host and settings.smtp_from):return False
    try:mfa.cipher()
    except Exception:return False
    return True

def deliver(email,purpose,token):
    message=EmailMessage();message['From']=settings.smtp_from;message['To']=email
    message['Subject']='Reset your Study Map password' if purpose=='reset' else 'Verify your Study Map email'
    action='reset' if purpose=='reset' else 'verify'
    link=settings.public_origin+'/account/recovery#'+action+'='+token
    message.set_content('Open this link to '+('reset your password' if purpose=='reset' else 'verify your email')+':\n\n'+link+'\n\nThis link expires after 30 minutes and works once. If you did not request it, you can ignore this email.')
    with smtplib.SMTP(settings.smtp_host,settings.smtp_port,timeout=10) as smtp:
        smtp.ehlo();smtp.starttls(context=ssl.create_default_context());smtp.ehlo()
        if settings.smtp_username:smtp.login(settings.smtp_username,settings.smtp_password)
        smtp.send_message(message)

async def tick():
    if not configured():return
    async with cursor() as cur:
        await cur.execute("SELECT o.*,u.email FROM account_mail_outbox o JOIN users u ON u.id=o.user_id WHERE o.sent_at IS NULL AND o.attempts<5 AND o.next_attempt_at<=now() AND o.created_at>now()-interval '30 minutes' ORDER BY o.id FOR UPDATE OF o SKIP LOCKED LIMIT 1")
        row=await cur.fetchone()
        if not row:return
        try:await run_in_threadpool(deliver,row['email'],row['purpose'],mfa.decrypt(row['user_id'],row['token_cipher']))
        except Exception as error:
            await cur.execute("UPDATE account_mail_outbox SET attempts=attempts+1,last_error=%s,next_attempt_at=now()+interval '2 minutes' WHERE id=%s",(type(error).__name__,row['id']))
        else:
            await cur.execute("UPDATE account_mail_outbox SET attempts=attempts+1,sent_at=now(),token_cipher='',last_error=NULL WHERE id=%s",(row['id'],))

async def worker():
    while True:
        await asyncio.sleep(10)
        try:await tick()
        except Exception:pass  # Retry next tick; transaction rolls back. No secrets logged.
