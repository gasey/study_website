"""30-day closed-account reopening through previously verified email only."""
from contextlib import asynccontextmanager
from uuid import uuid4
import hashlib
import psycopg
import pytest
from cryptography.fernet import Fernet
from app.config import settings
from app.db import cursor
from app.routers import account_tools,account_recovery,auth
from app.services import account_identity,account_mail,mfa
from test_learning_workflows import learner


@pytest.fixture(autouse=True)
def real_role(monkeypatch):
    @asynccontextmanager
    async def role_cursor():
        async with cursor() as cur:
            await cur.execute('SET LOCAL ROLE mpsc')
            yield cur
    for module in (account_tools,account_recovery,auth,account_identity,account_mail):
        monkeypatch.setattr(module,'cursor',role_cursor)
    monkeypatch.setattr(settings,'mfa_encryption_key',Fernet.generate_key().decode())
    monkeypatch.setattr(account_recovery,'configured',lambda:True)
    async def accepting(cur,lock=False):return True
    async def no_rate(*args,**kwargs):return None
    monkeypatch.setattr(account_recovery,'accepting',accepting)
    monkeypatch.setattr(account_recovery,'_check_rate',no_rate)
    monkeypatch.setattr(auth,'_check_rate',no_rate)
    monkeypatch.setattr(mfa,'limit',no_rate)
    monkeypatch.setattr(account_mail,'configured',lambda:True)


def test_reopen_link_restores_identity_and_history_but_not_old_credentials(client,actor,database,monkeypatch):
    conn=database[1]
    user,headers=learner(database,actor)
    email=user+'@example.test'
    conn.execute("UPDATE users SET email=%s,email_verified_at=now(),name='Saved name',avatar='{}'::jsonb WHERE id=%s",(email,user))
    conn.execute("INSERT INTO attempts(user_id,canonical_id,correct,chosen_text,context) VALUES(%s,'cq_test',true,'B','practice')",(user,))
    conn.execute("INSERT INTO google_identities(subject,user_id) VALUES(%s,%s)",('google-'+user,user))

    closed=client.post('/api/me/account-close',headers=headers,json={
        'user_id':user,'expected_version':0,'confirmation':'DELETE MY ACCOUNT'})
    assert closed.status_code==200,closed.text
    assert conn.execute('SELECT email,closed_at FROM users WHERE id=%s',(user,)).fetchone()[0] is None
    escrow=conn.execute('SELECT email_hash,expires_at FROM account_closure_recovery WHERE user_id=%s',(user,)).fetchone()
    assert escrow and escrow[1]
    assert conn.execute('SELECT count(*) FROM attempts WHERE user_id=%s',(user,)).fetchone()[0]==1
    with pytest.raises(psycopg.Error,match='Account is closed'):
        with conn.transaction():
            conn.execute('SET LOCAL ROLE mpsc')
            conn.execute("INSERT INTO account_email_tokens(token_hash,user_id,purpose,expires_at) VALUES(%s,%s,'reopen',now()+interval '5 minutes')",(uuid4().hex,user))

    requested=client.post('/api/auth/recovery/request',headers={'Origin':'https://study.hawayu.in'},json={'email':email})
    assert requested.status_code==200,requested.text
    outbox=conn.execute("SELECT id,token_cipher FROM account_mail_outbox WHERE user_id=%s AND purpose='reopen'",(user,)).fetchone()
    assert outbox and outbox[1]
    raw=mfa.decrypt(user,outbox[1])
    assert conn.execute("SELECT purpose FROM account_email_tokens WHERE token_hash=%s",(hashlib.sha256(raw.encode()).hexdigest(),)).fetchone()==('reopen',)

    sent=[]
    monkeypatch.setattr(account_mail,'deliver',lambda *args:sent.append(args))
    async def tick():
        row=await account_mail.reserve()
        assert row and row['purpose']=='reopen' and row['email']==email
        await account_mail.send_reserved(row)
    client.portal.call(tick)
    assert len(sent)==1 and sent[0][0:2]==(email,'reopen')
    raw=sent[0][2]

    complete=client.post('/api/auth/reopen/complete',headers={'Origin':'https://study.hawayu.in'},json={
        'token':raw,'password':'ReopenedPassword123!'})
    assert complete.status_code==200,complete.text
    account=conn.execute('SELECT closed_at,email,email_verified_at,password_hash,name,avatar,handle FROM users WHERE id=%s',(user,)).fetchone()
    assert account[0] is None and account[1]==email and account[2] is not None
    assert account[3].startswith('scrypt$') and account[4]=='Saved name' and account[5]=={}
    assert account[6].startswith('learn-')
    assert conn.execute('SELECT count(*) FROM account_closure_recovery WHERE user_id=%s',(user,)).fetchone()[0]==0
    assert conn.execute('SELECT count(*) FROM attempts WHERE user_id=%s',(user,)).fetchone()[0]==1
    assert conn.execute('SELECT count(*) FROM auth_sessions WHERE user_id=%s AND revoked_at IS NULL',(user,)).fetchone()[0]==0
    assert conn.execute('SELECT count(*) FROM google_identities WHERE user_id=%s',(user,)).fetchone()[0]==0
    assert conn.execute('SELECT enabled_at,secret_cipher FROM account_mfa WHERE user_id=%s',(user,)).fetchone() is None
    assert conn.execute("SELECT count(*) FROM account_security_events WHERE user_id=%s AND action='account_reopened'",(user,)).fetchone()[0]==1

    again=client.post('/api/auth/reopen/complete',headers={'Origin':'https://study.hawayu.in'},json={
        'token':raw,'password':'AnotherPassword123!'})
    assert again.status_code==400


def test_reopen_window_expiry_and_email_reservation(client,actor,database):
    conn=database[1];user,headers=learner(database,actor);email=user+'@example.test'
    conn.execute('UPDATE users SET email=%s,email_verified_at=now() WHERE id=%s',(email,user))
    assert client.post('/api/me/account-close',headers=headers,json={
        'user_id':user,'expected_version':0,'confirmation':'DELETE MY ACCOUNT'}).status_code==200
    escrow=conn.execute('SELECT identity_cipher FROM account_closure_recovery WHERE user_id=%s',(user,)).fetchone()[0]
    assert escrow
    # New password/Google registration cannot claim the address while recovery is available.
    blocked=client.post('/api/auth/register',headers={'Origin':'https://study.hawayu.in'},json={
        'email':email,'password':'AnotherStrongPassword123!'})
    assert blocked.status_code==409
    conn.execute("UPDATE account_closure_recovery SET expires_at=now()-interval '1 second' WHERE user_id=%s",(user,))
    requested=client.post('/api/auth/recovery/request',headers={'Origin':'https://study.hawayu.in'},json={'email':email})
    assert requested.status_code==200
    assert conn.execute("SELECT count(*) FROM account_email_tokens WHERE user_id=%s AND purpose='reopen'",(user,)).fetchone()[0]==0
    assert conn.execute('SELECT email,closed_at IS NOT NULL FROM users WHERE id=%s',(user,)).fetchone()==(None,True)


def test_unverified_closed_email_has_no_reopen_envelope(client,actor,database):
    conn=database[1];user,headers=learner(database,actor)
    assert client.post('/api/me/account-close',headers=headers,json={
        'user_id':user,'expected_version':0,'confirmation':'DELETE MY ACCOUNT'}).status_code==200
    assert conn.execute('SELECT count(*) FROM account_closure_recovery WHERE user_id=%s',(user,)).fetchone()[0]==0


def test_expired_identity_escrow_is_purged_by_bounded_retention_worker(client,actor,database):
    from app.services import account_retention
    conn=database[1];user,headers=learner(database,actor)
    conn.execute('UPDATE users SET email=%s,email_verified_at=now() WHERE id=%s',(user+'@example.test',user))
    assert client.post('/api/me/account-close',headers=headers,json={
        'user_id':user,'expected_version':0,'confirmation':'DELETE MY ACCOUNT'}).status_code==200
    conn.execute("UPDATE account_closure_recovery SET expires_at=now()-interval '1 second' WHERE user_id=%s",(user,))
    async def sweep():
        async with account_retention.cursor() as cur:
            await cur.execute('SET LOCAL ROLE mpsc')
            return await account_retention.sweep(cur)
    result=client.portal.call(sweep)
    assert result['closure_recovery_expired']>=1
    assert conn.execute('SELECT count(*) FROM account_closure_recovery WHERE user_id=%s',(user,)).fetchone()[0]==0
