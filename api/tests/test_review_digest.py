"""Real PostgreSQL role, synthetic consent/queues, fake SMTP only."""
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
import hashlib
import logging
import secrets
import pytest
from cryptography.fernet import Fernet
from app.config import settings
from app.db import cursor
from app.services import review_digest as digest, account_mail as mail, mfa
from app.routers import review_digest as routes
from test_learning_workflows import learner, official

TICK=digest.tick
DELIVER=digest.deliver
def run(client,fn,*args):return client.portal.call(fn,*args)


@pytest.fixture(autouse=True)
def setup(database,monkeypatch):
    conn=database[1]
    conn.execute('TRUNCATE review_digest_preferences,review_digest_outbox,review_digest_deliveries,account_mail_outbox,account_mail_deliveries')
    @asynccontextmanager
    async def role():
        async with cursor() as cur:
            await cur.execute('SET LOCAL ROLE mpsc');yield cur
    monkeypatch.setattr(digest,'cursor',role);monkeypatch.setattr(routes,'cursor',role);monkeypatch.setattr(mail,'cursor',role)
    monkeypatch.setattr(settings,'mfa_encryption_key',Fernet.generate_key().decode())
    monkeypatch.setattr(settings,'account_mail_enabled',True);monkeypatch.setattr(settings,'review_digest_enabled',True)
    monkeypatch.setattr(settings,'smtp_host','smtp.resend.com');monkeypatch.setattr(settings,'smtp_from','synthetic@example.test')
    monkeypatch.setattr(settings,'smtp_daily_limit',100);monkeypatch.setattr(settings,'smtp_monthly_limit',3000)
    day=conn.execute("SELECT (now() AT TIME ZONE 'Asia/Kolkata')::date").fetchone()[0]
    async def clock(cur):return {'day':day,'hour':18}
    async def background_noop():pass
    monkeypatch.setattr(digest,'clock',clock);monkeypatch.setattr(digest,'tick',background_noop)
    monkeypatch.setattr(digest,'deliver',lambda *a:None)


def account(client,actor,database,due=True,subscribe=True):
    user,h=learner(database,actor);conn=database[1]
    conn.execute('UPDATE users SET email_verified_at=now() WHERE id=%s',(user,))
    q=None
    if due:
        q,_,_=official(database)
        conn.execute("INSERT INTO review_items(user_id,item_type,item_id,canonical_id,box,due_on,last_result) VALUES(%s,'question',%s,%s,1,(now() AT TIME ZONE 'Asia/Kolkata')::date,false)",(user,q,q))
    if subscribe:
        r=save(client,h,user,0,True);assert r.status_code==200,r.text
    return user,h,q


def save(client,h,user,version,enabled):
    return client.post('/api/review-digest/preferences',headers=h,json={'user_id':user,'expected_version':version,'enabled':enabled})


def test_preferences_default_off_private_csrf_cas_verified_and_account_binding(client,actor,database,monkeypatch):
    user,h,_=account(client,actor,database,False,False)
    r=client.get('/api/review-digest/preferences');assert r.status_code==200 and r.headers['cache-control']=='private, no-store'
    assert r.json()['enabled'] is False and r.json()['version']==0 and 'token' not in str(r.json())
    assert save(client,{},user,0,True).status_code==403
    assert save(client,h,'owner',0,True).status_code==409
    database[1].execute('UPDATE users SET email_verified_at=NULL WHERE id=%s',(user,))
    assert save(client,h,user,0,True).status_code==409
    database[1].execute('UPDATE users SET email_verified_at=now() WHERE id=%s',(user,))
    assert save(client,h,user,0,True).json()['version']==1
    assert save(client,h,user,0,False).status_code==409
    monkeypatch.setattr(settings,'review_digest_enabled',False)
    assert save(client,h,user,1,False).json()['enabled'] is False
    assert save(client,h,user,2,True).status_code==409
    client.cookies.clear();assert client.get('/api/review-digest/preferences').status_code==401


def test_empty_silence_window_daily_replay_and_no_economic_writes(client,actor,database,monkeypatch):
    empty,_,_=account(client,actor,database,False);user,_,_=account(client,actor,database)
    sink=[];monkeypatch.setattr(digest,'deliver',lambda *a:sink.append(a))
    original=digest.clock
    async def morning(cur):return {**await original(cur),'hour':17}
    monkeypatch.setattr(digest,'clock',morning);run(client,TICK)
    assert database[1].execute('SELECT count(*) FROM review_digest_outbox').fetchone()[0]==0
    monkeypatch.setattr(digest,'clock',original);run(client,TICK);run(client,TICK)
    assert len(sink)==1 and sink[0][2]==1 and sink[0][3]==0
    assert database[1].execute('SELECT user_id,state FROM review_digest_outbox').fetchall()==[(user,'sent')]
    assert database[1].execute('SELECT count(*) FROM reward_ledger').fetchone()[0]==0
    assert database[1].execute('SELECT count(*) FROM attempts').fetchone()[0]==0


def test_concurrent_workers_once_per_ist_day_and_shared_budget(client,actor,database,monkeypatch):
    account(client,actor,database);sink=[];monkeypatch.setattr(digest,'deliver',lambda *a:sink.append(a))
    with ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(lambda _:run(client,TICK),range(3)))
    assert len(sink)==1
    async def capacity():
        async with digest.cursor() as cur:return await mail.capacity(cur)
    assert run(client,capacity)['day_used']==1
    assert database[1].execute('SELECT count(*) FROM review_digest_deliveries').fetchone()[0]==1


@pytest.mark.parametrize('reason',['unsubscribe','closed','address','unverified','empty','held','assessment','paused','late'])
def test_send_rechecks_consent_account_queue_and_window(client,actor,database,monkeypatch,reason):
    user,h,q=account(client,actor,database);conn=database[1];run(client,digest.schedule);row=run(client,digest.reserve);assert row
    if reason=='unsubscribe':assert save(client,h,user,1,False).status_code==200
    elif reason=='closed':
        from app.services.account_tools import close
        async def close_user():
            async with digest.cursor() as cur:await close(cur,user,0)
        run(client,close_user)
    elif reason=='address':conn.execute("UPDATE users SET email='changed@example.test' WHERE id=%s",(user,))
    elif reason=='unverified':conn.execute('UPDATE users SET email_verified_at=NULL WHERE id=%s',(user,))
    elif reason=='empty':conn.execute('UPDATE review_items SET due_on=due_on+1 WHERE user_id=%s',(user,))
    elif reason=='held':conn.execute("UPDATE canonical_questions SET status='held' WHERE id=%s",(q,))
    elif reason=='assessment':conn.execute("INSERT INTO mock_sessions(id,user_id,collection_id,question_ids,duration_seconds) VALUES(%s,%s,'udc',%s,1200)",('digest-mock-'+user,user,[q]))
    elif reason=='paused':monkeypatch.setattr(settings,'review_digest_enabled',False)
    elif reason=='late':
        original=digest.clock
        async def late(cur):return {**await original(cur),'hour':22}
        monkeypatch.setattr(digest,'clock',late)
    sink=[];monkeypatch.setattr(digest,'deliver',lambda *a:sink.append(a));run(client,digest.send_reserved,row)
    assert not sink and conn.execute('SELECT state FROM review_digest_deliveries').fetchone()[0]=='cancelled'
    if reason=='closed':
        assert conn.execute('SELECT count(*) FROM review_digest_preferences WHERE user_id=%s',(user,)).fetchone()[0]==0
        assert conn.execute('SELECT count(*) FROM review_digest_outbox WHERE user_id=%s',(user,)).fetchone()[0]==0


def test_pending_recovery_priority_and_reserved_daily_monthly_headroom(client,actor,database,monkeypatch):
    user,_,_=account(client,actor,database);conn=database[1];run(client,digest.schedule)
    conn.execute("INSERT INTO account_mail_outbox(user_id,purpose,token_cipher) VALUES(%s,'reset','synthetic')",(user,))
    assert run(client,digest.reserve) is None
    conn.execute('DELETE FROM account_mail_outbox')
    monkeypatch.setattr(settings,'smtp_daily_limit',1);assert run(client,digest.reserve) is None
    monkeypatch.setattr(settings,'smtp_daily_limit',100);monkeypatch.setattr(settings,'smtp_monthly_limit',1)
    assert run(client,digest.reserve) is None


def test_uncertain_send_is_not_retried_and_receipts_stay_immutable(client,actor,database,monkeypatch):
    account(client,actor,database);sink=[];conn=database[1]
    def timeout(*args):sink.append(args);raise TimeoutError('SECRET ADDRESS/TOKEN must not be recorded')
    monkeypatch.setattr(digest,'deliver',timeout)
    for _ in range(6):
        run(client,TICK);conn.execute("UPDATE review_digest_outbox SET next_attempt_at=now()-interval '1 second'")
    assert len(sink)==1
    assert conn.execute('SELECT DISTINCT state,error_type FROM review_digest_deliveries').fetchall()==[('uncertain','TimeoutError')]
    with pytest.raises(Exception):conn.execute("DELETE FROM review_digest_deliveries")


def test_abandoned_reservation_cannot_send_after_lease_or_on_next_ist_day(client,actor,database,monkeypatch):
    account(client,actor,database);conn=database[1];run(client,digest.schedule);abandoned=run(client,digest.reserve)
    conn.execute("UPDATE review_digest_outbox SET next_attempt_at=now()-interval '1 second'")
    assert run(client,digest.reserve) is None
    sink=[];monkeypatch.setattr(digest,'deliver',lambda *a:sink.append(a));run(client,digest.send_reserved,abandoned)
    assert not sink and conn.execute('SELECT state FROM review_digest_deliveries').fetchone()[0]=='uncertain'
    original=digest.clock
    async def tomorrow(cur):return {**await original(cur),'day':(await original(cur))['day']+timedelta(days=1)}
    monkeypatch.setattr(digest,'clock',tomorrow);run(client,TICK);run(client,TICK)
    assert len(sink)==1 and conn.execute('SELECT count(*) FROM review_digest_outbox').fetchone()[0]==2


def test_native_surface_is_not_widened(client,actor,database):
    user,_,_=account(client,actor,database)
    from test_mobile_companion import connect
    mobile,_=connect(client,actor,user)
    assert client.get('/api/review-digest/preferences',headers=mobile).status_code==403
    assert client.post('/api/review-digest/preferences',headers=mobile,json={}).status_code==403


def test_consent_throttle_never_blocks_withdrawal(client,actor,database,monkeypatch):
    from fastapi import HTTPException
    user,h,_=account(client,actor,database)
    async def limited(*args):raise HTTPException(429,'Synthetic consent throttle')
    monkeypatch.setattr(routes.mfa,'limit',limited)
    assert save(client,h,user,1,False).json()['enabled'] is False
    assert save(client,h,user,2,True).status_code==429


def test_public_unsubscribe_get_inert_post_idempotent_and_old_link_cannot_cancel_new_consent(client,actor,database):
    user,h,_=account(client,actor,database);conn=database[1]
    raw=mfa.decrypt(user,conn.execute('SELECT token_cipher FROM review_digest_preferences WHERE user_id=%s',(user,)).fetchone()[0])
    url='/api/review-digest/unsubscribe?token='+raw
    client.cookies.clear();r=client.get(url)
    assert r.status_code==200 and raw not in r.text and 'no-referrer' in r.headers['referrer-policy']
    assert conn.execute('SELECT enabled FROM review_digest_preferences WHERE user_id=%s',(user,)).fetchone()[0]
    for _ in range(2):assert client.post(url,data={'List-Unsubscribe':'One-Click'}).json()['unsubscribed']
    assert conn.execute('SELECT enabled,version FROM review_digest_preferences WHERE user_id=%s',(user,)).fetchone()==(False,2)
    h=actor(user);assert save(client,h,user,2,True).json()['version']==3
    client.cookies.clear();assert client.post(url,data={'List-Unsubscribe':'One-Click'}).status_code==200
    assert conn.execute('SELECT enabled FROM review_digest_preferences WHERE user_id=%s',(user,)).fetchone()[0]
    assert client.post('/api/review-digest/unsubscribe',json={'token':secrets.token_urlsafe(32)}).json()['unsubscribed']
    assert client.post(url,data={'List-Unsubscribe':'bad'}).status_code==400


def test_transport_unsubscribe_headers_and_access_log_redaction(monkeypatch):
    sink=[];monkeypatch.setattr(mail,'send_message',lambda *a:sink.append(a))
    DELIVER('synthetic@example.test','private-token',2,3,'digest-stable-key',None)
    message=sink[0][0]
    assert message['List-Unsubscribe-Post']=='List-Unsubscribe=One-Click'
    assert message['List-Unsubscribe'].startswith('<https://study.hawayu.in/api/review-digest/unsubscribe?token=')
    assert '/revise?tab=review' in message.get_content() and '2 reviews' in message.get_content()
    assert '/api/review-digest/unsubscribe?token=private-token' in message.get_content()
    record=logging.LogRecord('uvicorn.access',20,'',0,'%s %s %s %s %s',('client','POST','/api/review-digest/unsubscribe?token=private-token','1.1',200),None)
    assert routes.UnsubscribeAccessFilter().filter(record)
    assert 'private-token' not in record.getMessage()
