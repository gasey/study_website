"""Built-in account mail: real-role DB reservations with a fake SMTP sink only."""
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
import pytest
from cryptography.fernet import Fernet
from app.config import settings
from app.db import cursor
from app.services import account_mail as mail,mfa
from app.routers.account_recovery import enqueue
from app.routers import account_recovery

@pytest.fixture(autouse=True)
def real_role(monkeypatch,database):
    # Each test owns a provider-wide capacity budget in this disposable DB.
    database[1].execute('TRUNCATE account_mail_deliveries,account_mail_outbox,account_email_tokens')
    @asynccontextmanager
    async def role_cursor():
        async with cursor() as cur:
            await cur.execute('SET LOCAL ROLE mpsc');yield cur
    monkeypatch.setattr(mail,'cursor',role_cursor)
    monkeypatch.setattr(account_recovery,'cursor',role_cursor)
    monkeypatch.setattr(settings,'mfa_encryption_key',Fernet.generate_key().decode())
    monkeypatch.setattr(settings,'account_mail_enabled',True)
    monkeypatch.setattr(settings,'smtp_host','smtp.resend.com')
    monkeypatch.setattr(settings,'smtp_from','synthetic@example.test')
    monkeypatch.setattr(settings,'smtp_daily_limit',100)
    monkeypatch.setattr(settings,'smtp_monthly_limit',3000)


def run(client,fn,*args):return client.portal.call(fn,*args)
def queued(client,database,n=1,purpose='reset'):
    ids=[];conn=database[1]
    async def add(user):
        async with mail.cursor() as cur:await enqueue(cur,user,purpose)
    for _ in range(n):
        user='mail_'+uuid4().hex;conn.execute('INSERT INTO users(id,handle,email) VALUES(%s,%s,%s)',(user,user,user+'@example.test'))
        run(client,add,user);ids.append(conn.execute('SELECT id FROM account_mail_outbox WHERE user_id=%s',(user,)).fetchone()[0])
    return ids


def test_mail_disabled_and_quarantine_do_not_send_or_consume_capacity(client,database,monkeypatch,tmp_path):
    from app.services import account_mail_release
    ids=queued(client,database);sink=[];monkeypatch.setattr(mail,'deliver',lambda *a:sink.append(a))
    monkeypatch.setattr(settings,'account_mail_enabled',False);run(client,mail.tick)
    monkeypatch.setattr(settings,'account_mail_enabled',True)
    flag=tmp_path/'state.json';flag.write_text('{"version":1,"writes_enabled":false}');monkeypatch.setattr(account_mail_release,'STATE_PATH',flag)
    run(client,mail.tick);flag.unlink();run(client,mail.tick)
    assert not sink and database[1].execute('SELECT count(*) FROM account_mail_deliveries').fetchone()[0]==0
    assert database[1].execute('SELECT token_cipher FROM account_mail_outbox WHERE id=%s',(ids[0],)).fetchone()[0]
    assert 'disabled' in database[1].execute("SELECT note FROM worker_heartbeats WHERE worker='account-mail'").fetchone()[0]


def test_success_receipt_is_durable_private_and_worker_replay_does_not_resend(client,database,monkeypatch):
    oid=queued(client,database)[0];sink=[];monkeypatch.setattr(mail,'deliver',lambda *a:sink.append(a))
    run(client,mail.tick);run(client,mail.tick)
    conn=database[1];assert len(sink)==1 and sink[0][1]=='reset' and len(sink[0][2])>32
    assert conn.execute('SELECT attempts,sent_at IS NOT NULL,token_cipher FROM account_mail_outbox WHERE id=%s',(oid,)).fetchone()==(1,True,'')
    assert conn.execute('SELECT state,attempt FROM account_mail_deliveries WHERE outbox_id=%s',(oid,)).fetchone()==('sent',1)
    assert conn.execute('SELECT count(*) FROM reward_ledger').fetchone()[0]==0
    with pytest.raises(Exception):conn.execute("UPDATE account_mail_deliveries SET state='failed' WHERE outbox_id=%s",(oid,))
    cols=[x[0] for x in conn.execute("SELECT column_name FROM information_schema.columns WHERE table_name='account_mail_deliveries'").fetchall()]
    assert not set(cols)&{'email','user_id','token_cipher','token','body'}


def test_concurrent_workers_share_global_daily_budget_before_smtp(client,database,monkeypatch):
    queued(client,database,2);monkeypatch.setattr(settings,'smtp_daily_limit',1);sink=[];monkeypatch.setattr(mail,'deliver',lambda *a:sink.append(a))
    with ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(lambda _:run(client,mail.tick),range(2)))
    conn=database[1];assert len(sink)==1 and conn.execute('SELECT count(*) FROM account_mail_deliveries').fetchone()[0]==1
    assert conn.execute('SELECT sum(attempts) FROM account_mail_outbox').fetchone()[0]==1


def test_monthly_budget_and_legacy_sent_mail_are_counted_without_backfill(client,database,monkeypatch):
    ids=queued(client,database,2);conn=database[1]
    conn.execute('UPDATE account_mail_outbox SET sent_at=now(),token_cipher=%s WHERE id=%s',('',ids[0]))
    monkeypatch.setattr(settings,'smtp_daily_limit',100);monkeypatch.setattr(settings,'smtp_monthly_limit',1)
    sink=[];monkeypatch.setattr(mail,'deliver',lambda *a:sink.append(a));run(client,mail.tick)
    assert not sink and conn.execute('SELECT count(*) FROM account_mail_deliveries').fetchone()[0]==0


def test_crash_reservation_survives_and_expired_lease_retries_with_same_key(client,database,monkeypatch):
    oid=queued(client,database)[0];conn=database[1]
    row=run(client,mail.reserve);assert row and conn.execute('SELECT state FROM account_mail_deliveries').fetchone()[0]=='reserved'
    assert run(client,mail.reserve) is None
    conn.execute("UPDATE account_mail_outbox SET next_attempt_at=now()-interval '1 second' WHERE id=%s",(oid,))
    sink=[];monkeypatch.setattr(mail,'deliver',lambda *a:sink.append(a));run(client,mail.tick)
    assert conn.execute('SELECT state FROM account_mail_deliveries ORDER BY id').fetchall()==[('uncertain',),('sent',)]
    assert len(sink)==1
    run(client,mail.send_reserved,row);assert len(sink)==1


def test_timeout_keeps_capacity_and_retry_key_and_bounds_attempts(client,database,monkeypatch):
    oid=queued(client,database)[0];conn=database[1];sink=[]
    def timeout(*args):sink.append(args);raise TimeoutError('SECRET RECIPIENT/TOKEN MUST NOT BE RECORDED')
    monkeypatch.setattr(mail,'deliver',timeout)
    for _ in range(6):
        run(client,mail.tick);conn.execute("UPDATE account_mail_outbox SET next_attempt_at=now()-interval '1 second' WHERE id=%s",(oid,))
    assert len(sink)==5 and len({a[3] for a in sink})==1
    assert conn.execute('SELECT count(*) FROM account_mail_deliveries').fetchone()[0]==5
    assert conn.execute('SELECT DISTINCT state,error_type FROM account_mail_deliveries').fetchall()==[('uncertain','TimeoutError')]
    assert conn.execute('SELECT attempts,last_error FROM account_mail_outbox').fetchone()==(5,'TimeoutError')


def test_reserved_mail_rechecks_closed_account_and_consumed_tokens(client,database,monkeypatch):
    sink=[];monkeypatch.setattr(mail,'deliver',lambda *a:sink.append(a));conn=database[1]
    for reason in ('closed','consumed'):
        oid=queued(client,database)[0];row=run(client,mail.reserve)
        if reason=='closed':
            from app.services.account_tools import close
            async def close_account():
                async with mail.cursor() as cur:return await close(cur,row['user_id'],0)
            assert run(client,close_account)['closed']
        else:conn.execute('UPDATE account_email_tokens SET consumed_at=now() WHERE user_id=%s',(row['user_id'],))
        run(client,mail.send_reserved,row)
    assert not sink and conn.execute('SELECT DISTINCT state FROM account_mail_deliveries').fetchall()==[('cancelled',)]


def test_pausing_after_reservation_preserves_pending_ciphertext(client,database,monkeypatch):
    oid=queued(client,database)[0];row=run(client,mail.reserve);sink=[];monkeypatch.setattr(mail,'deliver',lambda *a:sink.append(a))
    monkeypatch.setattr(settings,'account_mail_enabled',False);run(client,mail.send_reserved,row)
    assert not sink and database[1].execute('SELECT token_cipher FROM account_mail_outbox WHERE id=%s',(oid,)).fetchone()[0]


def test_resend_transport_uses_tls_and_stable_provider_key_without_secret_headers(monkeypatch):
    from datetime import datetime,timezone
    calls=[]
    class SMTP:
        def __init__(self,*args,**kwargs):calls.append(('connection',args,kwargs))
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def ehlo(self):calls.append(('ehlo',))
        def starttls(self,**kwargs):assert kwargs['context'].check_hostname;calls.append(('tls',))
        def login(self,*args):calls.append(('login',))
        def send_message(self,msg):calls.append(('message',msg))
    monkeypatch.setattr(mail.smtplib,'SMTP',SMTP);monkeypatch.setattr(settings,'smtp_username','resend');monkeypatch.setattr(settings,'smtp_password','private-key')
    mail.deliver('fixture@example.test','reset','private-token','stable-id',datetime(2026,11,18,tzinfo=timezone.utc))
    msg=next(c[1] for c in calls if c[0]=='message')
    assert msg['Resend-Idempotency-Key']=='stable-id' and msg['Message-ID'].startswith('<stable-id@')
    assert 'private-key' not in str(msg) and calls.index(('tls',))<calls.index(('login',))


def test_full_queue_rejects_known_and_unknown_requests_identically(client,database,monkeypatch):
    monkeypatch.setattr(settings,'smtp_daily_limit',1)
    queued(client,database)
    h={'Origin':settings.public_origin};client.cookies.clear()
    assert client.get('/api/auth/recovery/status').json()=={'available':False}
    responses=[client.post('/api/auth/recovery/request',headers=h,json={'email':e}) for e in ['owner@example.test','missing@example.test']]
    assert [r.status_code for r in responses]==[503,503] and responses[0].json()==responses[1].json()
    assert all(r.headers['retry-after']=='300' for r in responses)


def test_utc_day_and_conservative_month_budget_use_actual_server_boundaries(client,database):
    conn=database[1]
    conn.execute("""INSERT INTO account_mail_deliveries(outbox_id,attempt,reserved_at)
      VALUES(-100,1,date_trunc('day',now() AT TIME ZONE 'UTC') AT TIME ZONE 'UTC'),
            (-101,1,(date_trunc('day',now() AT TIME ZONE 'UTC') AT TIME ZONE 'UTC')-interval '1 second')""")
    async def check():
        async with mail.cursor() as cur:return await mail.capacity(cur)
    counts=run(client,check)
    assert counts['day_used']==1
    expected=conn.execute("SELECT count(*) FROM account_mail_deliveries WHERE reserved_at>=now()-interval '31 days'").fetchone()[0]
    assert counts['month_used']==expected
