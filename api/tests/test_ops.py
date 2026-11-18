"""Real isolated PostgreSQL owner/privacy, freshness and IST aggregation checks."""
from datetime import datetime,timedelta,timezone
from app.services.ops import heartbeat

BASE='/api/admin/ops'


def test_heartbeat_boundaries_do_not_infer_success():
    now=datetime.now(timezone.utc)
    def state(age,ok):
        return heartbeat('x','Test',60,{'last_beat':now-timedelta(seconds=age),'last_ok':ok,'note':'test'},now)['state']
    assert heartbeat('x','Test',60,None,now)['state']=='unknown'
    assert state(0,None)=='attention'
    assert state(10,now-timedelta(seconds=10))=='healthy'
    assert state(61,now)=='stale'
    assert state(-60,now+timedelta(seconds=60))=='unknown'
    assert state(0,now-timedelta(seconds=20))=='attention'


def test_owner_only_private_read_without_side_effects(client,actor,database):
    client.cookies.clear();assert client.get(BASE).status_code==401
    for user in ('outsider','author','reviewer1','reviewer2'):
        assert client.get(BASE,headers=actor(user)).status_code==403
    conn=database[1]
    tables=['reward_ledger','worker_heartbeats','reward_daily_counters','account_security_events','account_mail_deliveries']
    before={t:conn.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in tables}
    r=client.get(BASE,headers=actor('owner'));assert r.status_code==200,r.text
    body=r.json();assert body['read_only'] and r.headers['cache-control']=='private, no-store'
    assert 0<=body['probes']['pool']['available']<=body['probes']['pool']['size']<=body['probes']['pool']['max']
    assert body['probes']['backup']['state']=='unknown' and body['probes']['webhooks']['count_24h'] is None
    assert all(x['state']=='unknown' for x in body['timers'])
    assert all(x['last_ok'] for x in body['workers'] if x['id'] in ('desk-retention','calendar-reminders','game-lifecycle'))
    assert {t:conn.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in tables}==before
    assert not any(word in r.text for word in ('password_hash','token_cipher','smtp_password','database_url','@example.test'))
    assert client.post(BASE,json={},headers=actor('owner')).status_code==405


def test_real_fresh_stale_failed_and_legacy_observations(client,actor,database):
    conn=database[1]
    conn.execute("INSERT INTO worker_heartbeats(worker,last_beat,last_ok,note) VALUES('calendar-reminders',now(),now(),'cycle complete'),('desk-retention',now()-interval '4 hours',now()-interval '4 hours','done'),('game-lifecycle',now(),now()-interval '1 hour','failed') ON CONFLICT(worker) DO UPDATE SET last_beat=EXCLUDED.last_beat,last_ok=EXCLUDED.last_ok,note=EXCLUDED.note")
    conn.execute("INSERT INTO review_worker_health(worker_id,status) VALUES('score-reassessment','online') ON CONFLICT(worker_id) DO UPDATE SET status='online',seen_at=now()")
    r=client.get(BASE,headers=actor('owner'));assert r.status_code==200,r.text
    rows={w['id']:w for w in r.json()['workers']}
    assert rows['calendar-reminders']['state']=='healthy' and rows['desk-retention']['state']=='stale'
    assert rows['game-lifecycle']['state']=='attention'
    assert rows['score-reassessment']['state']=='unknown' and rows['score-reassessment']['legacy_observation']['status']=='online'


def test_ist_yesterday_totals_streaks_and_moderation(client,actor,database):
    conn=database[1];conn.execute("INSERT INTO users(id,handle,created_at) VALUES('ops-capped','ops-capped',now()-interval '2 days'),('ops-not-capped','ops-not-capped',now()-interval '1 day')")
    # Seven actual daily records ending yesterday, with one below-cap account.
    conn.execute("INSERT INTO reward_daily_counters(user_id,day,xp,points) SELECT 'ops-capped',(now() AT TIME ZONE 'Asia/Kolkata')::date-n,300,25 FROM generate_series(1,7) n")
    conn.execute("INSERT INTO reward_daily_counters(user_id,day,xp,points) VALUES('ops-not-capped',(now() AT TIME ZONE 'Asia/Kolkata')::date-1,20,4)")
    # Adjustment events don't mutate learning counters. Boundary receipt is the
    # first instant of yesterday in IST; today's receipt must stay outside totals.
    conn.execute("INSERT INTO reward_ledger(user_id,event_key,kind,xp,points,note,created_at) VALUES('ops-capped','ops:old','adjustment',7,11,'synthetic',(now() AT TIME ZONE 'Asia/Kolkata')::date::timestamp AT TIME ZONE 'Asia/Kolkata'-interval '1 day'),('ops-capped','ops:today','adjustment',999,999,'synthetic',(now() AT TIME ZONE 'Asia/Kolkata')::date::timestamp AT TIME ZONE 'Asia/Kolkata')")
    conn.execute("INSERT INTO content_reports(canonical_id,kind,reporter_id,note,status,created_at) VALUES('cq_test','typo_ocr','ops-capped','synthetic','confirmed',now()-interval '49 hours'),('cq_test','typo_ocr','ops-not-capped','synthetic','open',now()-interval '1 hour')")
    r=client.get(BASE,headers=actor('owner'));assert r.status_code==200,r.text
    e=r.json()['economy'];assert (e['minted_xp'],e['minted_points'],e['cap_accounts'])==(7,11,1)
    assert e['cap_streaks']==[{'user_id':'ops-capped','days':7}]
    assert [x['user_id'] for x in e['new_account_velocity']]==['ops-capped']
    m=next(x for x in r.json()['moderation'] if x['queue']=='questions')
    assert m['open']==2 and m['over_48h']==1 and 24.9<m['median_hours']<25.1


def test_query_failure_propagates_instead_of_zero(client,actor,monkeypatch):
    from app.services import ops
    async def fail(*args):raise RuntimeError('synthetic outage')
    monkeypatch.setattr(ops,'snapshot',fail)
    import pytest
    with pytest.raises(RuntimeError,match='synthetic outage'):
        client.get(BASE,headers=actor('owner'))


def test_native_owner_bearer_cannot_read_ops(client,actor):
    from test_mobile_companion import connect
    headers,_=connect(client,actor,'owner')
    assert client.get(BASE,headers=headers).status_code==403
