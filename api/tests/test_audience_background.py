"""Age restrictions outside authenticated requests; synthetic PG and fake mail."""
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
import hashlib
import secrets
from uuid import uuid4

import pytest
from fastapi import HTTPException
from app.config import settings
from app.db import cursor
from app.services import audience, calendar_reminders, review_digest, weekly_boards
from app.routers import account_privacy, calendar_owned
from test_account_privacy import declare
from test_review_digest import setup as digest_setup, account, run, TICK
from test_weekly_boards import profile, game


@pytest.fixture(autouse=True)
def app_role(monkeypatch):
    @asynccontextmanager
    async def role():
        async with cursor() as cur:
            await cur.execute('SET LOCAL ROLE mpsc')
            yield cur
    for module in (audience, account_privacy, calendar_owned):
        monkeypatch.setattr(module,'cursor',role)


def category(conn,user,value):
    conn.execute('DELETE FROM account_audience WHERE user_id=%s',(user,))
    if value:conn.execute('INSERT INTO account_audience(user_id,category) VALUES(%s,%s)',(user,value))


def calendar_setup(conn,user):
    eid='audience-event-'+uuid4().hex
    conn.execute("""INSERT INTO exam_calendar_events(id,title,kind,state,starts_on,
      source_url,source_reference,verification_note,verified_on,published_at)
      VALUES(%s,'Synthetic audience notice','exam','published',
      (now() AT TIME ZONE 'Asia/Kolkata')::date+1,'https://mpsc.mizoram.gov.in/synthetic',
      'Synthetic source','Synthetic fixture only',current_date,now())""",(eid,))
    conn.execute('INSERT INTO user_calendar_saved(user_id,event_id) VALUES(%s,%s)',(user,eid))
    conn.execute('INSERT INTO user_calendar_preferences(user_id,reminders) VALUES(%s,true) ON CONFLICT(user_id) DO UPDATE SET reminders=true',(user,))
    return eid


def feed_setup(conn,user):
    raw=secrets.token_urlsafe(32)
    conn.execute('INSERT INTO calendar_feed_tokens(user_id,token_hash,version) VALUES(%s,%s,1)',(user,hashlib.sha256(raw.encode()).hexdigest()))
    conn.execute("INSERT INTO calendar_entries(id,user_id,date,title,note,kind) VALUES(%s,%s,current_date,'Private fixture','Do not disclose','personal')",(uuid4(),user))
    return raw


@pytest.mark.parametrize('blocked_category',[None,'under18'])
def test_schedule_does_not_read_restricted_due_queue(client,actor,database,monkeypatch,blocked_category):
    blocked,_,_=account(client,actor,database)
    adult,_,_=account(client,actor,database)
    conn=database[1];category(conn,blocked,blocked_category);category(conn,adult,'adult')
    original=review_digest.due;examined=[];sent=[]
    async def due(cur,user):
        examined.append(user);assert user==adult
        return await original(cur,user)
    monkeypatch.setattr(review_digest,'due',due)
    monkeypatch.setattr(review_digest,'deliver',lambda *args:sent.append(args))
    monkeypatch.setattr(settings,'audience_gate_enabled',True)
    run(client,TICK);run(client,TICK)
    assert examined==[adult,adult] and len(sent)==1
    assert conn.execute('SELECT user_id,state FROM review_digest_outbox').fetchall()==[(adult,'sent')]
    assert conn.execute('SELECT last_checked_day FROM review_digest_preferences WHERE user_id=%s',(blocked,)).fetchone()==(None,)


@pytest.mark.parametrize('blocked_category',[None,'under18'])
def test_reserved_delivery_rechecks_age_before_due_or_smtp(client,actor,database,monkeypatch,blocked_category):
    user,_,_=account(client,actor,database);run(client,review_digest.schedule)
    row=run(client,review_digest.reserve);assert row
    category(database[1],user,blocked_category)
    monkeypatch.setattr(settings,'audience_gate_enabled',True)
    async def forbidden(*args):raise AssertionError('Restricted study queue was processed')
    monkeypatch.setattr(review_digest,'due',forbidden)
    monkeypatch.setattr(review_digest,'deliver',lambda *args:pytest.fail('Restricted reminder sent'))
    run(client,review_digest.send_reserved,row)
    assert database[1].execute('SELECT state FROM review_digest_deliveries').fetchall()==[('cancelled',)]


def test_restricted_pending_outbox_does_not_consume_reservation(client,actor,database,monkeypatch):
    user,_,_=account(client,actor,database);run(client,review_digest.schedule)
    monkeypatch.setattr(settings,'audience_gate_enabled',True)
    assert run(client,review_digest.reserve) is None
    assert database[1].execute('SELECT count(*) FROM review_digest_deliveries').fetchone()==(0,)


def test_delivery_waits_for_account_restriction_before_checking_age(client,actor,database,monkeypatch):
    user,_,_=account(client,actor,database);run(client,review_digest.schedule)
    row=run(client,review_digest.reserve);category(database[1],user,'adult')
    monkeypatch.setattr(settings,'audience_gate_enabled',True)
    monkeypatch.setattr(review_digest,'deliver',lambda *args:pytest.fail('Restricted reminder sent'))
    async def scenario():
        async with audience.cursor() as cur:
            await cur.execute('SELECT id FROM users WHERE id=%s FOR UPDATE',(user,))
            task=asyncio.create_task(review_digest.send_reserved(row))
            try:
                done,_=await asyncio.wait({task},timeout=.1)
                assert not done,'Delivery bypassed account restriction lock'
                await cur.execute("UPDATE account_audience SET category='under18' WHERE user_id=%s",(user,))
            except BaseException:
                task.cancel();await asyncio.gather(task,return_exceptions=True);raise
        await asyncio.wait_for(task,5)
    run(client,scenario)
    assert database[1].execute('SELECT state FROM review_digest_deliveries').fetchall()==[('cancelled',)]


def test_direct_service_cannot_subscribe_unknown_age_but_can_withdraw(client,actor,database,monkeypatch):
    user,_,_=account(client,actor,database)
    monkeypatch.setattr(settings,'audience_gate_enabled',True)
    async def consent(enabled,version):
        async with audience.cursor() as cur:return await review_digest.consent(cur,user,version,enabled)
    assert run(client,consent,False,1)['enabled'] is False
    with pytest.raises(HTTPException) as exc:run(client,consent,True,2)
    assert exc.value.status_code==403


def test_declaration_cancels_pending_work_and_revokes_feed_without_deleting_entries(client,actor,database,monkeypatch):
    conn=database[1];user,h,_=account(client,actor,database)
    eid=calendar_setup(conn,user);raw=feed_setup(conn,user)
    run(client,review_digest.schedule);row=run(client,review_digest.reserve);assert row
    monkeypatch.setattr(settings,'audience_gate_enabled',True)
    response=declare(client,'under18',headers=h,user_id=user)
    assert response.status_code==200,response.text
    assert conn.execute('SELECT enabled,token_cipher FROM review_digest_preferences WHERE user_id=%s',(user,)).fetchone()==(False,'')
    assert conn.execute('SELECT state FROM review_digest_outbox WHERE user_id=%s',(user,)).fetchone()==('cancelled',)
    assert conn.execute('SELECT reminders FROM user_calendar_preferences WHERE user_id=%s',(user,)).fetchone()==(False,)
    assert conn.execute('SELECT token_hash,version,revoked_at IS NOT NULL FROM calendar_feed_tokens WHERE user_id=%s',(user,)).fetchone()==(None,2,True)
    assert conn.execute('SELECT count(*) FROM calendar_entries WHERE user_id=%s',(user,)).fetchone()==(1,)
    run(client,review_digest.send_reserved,row)
    async def sweep():
        async with audience.cursor() as cur:return await calendar_reminders.sweep(cur)
    run(client,sweep)
    assert conn.execute('SELECT count(*) FROM review_notifications WHERE calendar_event_id=%s',(eid,)).fetchone()==(0,)
    client.cookies.clear();assert client.get('/api/calendar/feed/'+raw+'.ics').status_code==404


@pytest.mark.parametrize('value',[None,'under18','adult'])
def test_calendar_notifications_filter_existing_preferences(client,actor,database,monkeypatch,value):
    conn=database[1];user,_,_=account(client,actor,database,False,False)
    eid=calendar_setup(conn,user);category(conn,user,value)
    monkeypatch.setattr(settings,'audience_gate_enabled',True)
    async def sweep():
        async with audience.cursor() as cur:await calendar_reminders.sweep(cur)
    run(client,sweep);run(client,sweep)
    count=conn.execute('SELECT count(*) FROM review_notifications WHERE calendar_event_id=%s',(eid,)).fetchone()[0]
    assert count==(2 if value=='adult' else 0)


def test_calendar_sweep_waits_for_restriction_then_uses_fresh_snapshot(client,actor,database,monkeypatch):
    conn=database[1];user,_,_=account(client,actor,database,False,False)
    eid=calendar_setup(conn,user);category(conn,user,'adult')
    monkeypatch.setattr(settings,'audience_gate_enabled',True)
    async def scenario():
        started=asyncio.Event()
        async def sweep():
            async with audience.cursor() as cur:
                started.set()
                await calendar_reminders.sweep(cur)
        async with audience.cursor() as cur:
            await audience.calendar_publication_lock(cur,restricting=True)
            task=asyncio.create_task(sweep())
            try:
                await started.wait()
                done,_=await asyncio.wait({task},timeout=.1)
                assert not done,'Calendar publication bypassed restriction lock'
                await cur.execute("UPDATE account_audience SET category='under18' WHERE user_id=%s",(user,))
            except BaseException:
                task.cancel();await asyncio.gather(task,return_exceptions=True);raise
        await asyncio.wait_for(task,5)
    run(client,scenario)
    assert conn.execute('SELECT count(*) FROM review_notifications WHERE calendar_event_id=%s',(eid,)).fetchone()==(0,)


def test_feed_age_check_ignores_cookie_and_rechecks_after_user_lock(client,actor,database,monkeypatch):
    conn=database[1];user,_,_=account(client,actor,database,False,False);raw=feed_setup(conn,user)
    client.cookies.clear();url='/api/calendar/feed/'+raw+'.ics'
    assert client.get(url).status_code==200  # default-off compatibility
    monkeypatch.setattr(settings,'audience_gate_enabled',True)
    response=client.get(url)
    assert response.status_code==404 and 'Do not disclose' not in response.text
    assert response.headers['cache-control']=='private, no-store'
    category(conn,user,'adult');assert client.get(url).status_code==200
    async def scenario():
        async with audience.cursor() as cur:
            await cur.execute('SELECT id FROM users WHERE id=%s FOR UPDATE',(user,))
            task=asyncio.create_task(calendar_owned.subscription(raw))
            try:
                done,_=await asyncio.wait({task},timeout=.1)
                assert not done,'Feed did not serialize with account restriction'
                await cur.execute("UPDATE account_audience SET category='under18' WHERE user_id=%s",(user,))
            except BaseException:
                task.cancel();await asyncio.gather(task,return_exceptions=True);raise
        with pytest.raises(HTTPException) as exc:await asyncio.wait_for(task,5)
        assert exc.value.status_code==404
    run(client,scenario)


@pytest.mark.parametrize('mode',['xp','speed','duel','daily'])
def test_standings_remove_missing_and_under18_categories_before_ranking(client,database,monkeypatch,mode):
    at=datetime(2030,1,8,10,tzinfo=timezone.utc)
    conn=database[1];users=[profile(conn,10,at=at) for _ in range(3)]
    adult,minor,unknown=users;category(conn,adult,'adult');category(conn,minor,'under18')
    for user in users:
        if mode!='xp':
            rid=game(conn,user,100,mode,at=at)
            if mode=='daily':
                day=at.date().isoformat()
                conn.execute("INSERT INTO game_dailies(id,opens_at,closes_at,questions) VALUES(%s,%s,%s,'[]') ON CONFLICT DO NOTHING",(day,at,at+timedelta(days=1)))
                conn.execute('UPDATE game_rooms SET daily_id=%s WHERE id=%s',(day,rid))
                conn.execute('INSERT INTO game_daily_entries(daily_id,user_id,room_id) VALUES(%s,%s,%s)',(day,user,rid))
            elif mode=='duel':
                conn.execute('INSERT INTO game_members(room_id,user_id,score,correct,released_at) VALUES(%s,%s,50,1,now())',(rid,users[(users.index(user)+1)%3]))
    monkeypatch.setattr(settings,'audience_gate_enabled',True)
    async def board():
        async with audience.cursor() as cur:
            return await weekly_boards.xp(cur,adult,as_of=at) if mode=='xp' else await weekly_boards.games(cur,adult,mode,as_of=at)
    result=run(client,board)
    assert result['total']==1 and result['items'][0]['handle']==adult and result['items'][0]['rank']==1
    assert minor not in str(result) and unknown not in str(result)
