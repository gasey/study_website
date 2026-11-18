"""Owner/MFA boundaries and real isolated-PostgreSQL account aggregates."""
import hashlib
from uuid import uuid4
import pytest
from psycopg.types.json import Jsonb
from app.config import settings
from app.db import cursor
from app.services import account_viewer

BASE='/api/admin/users'

@pytest.fixture(autouse=True)
def policy(monkeypatch):
    monkeypatch.setattr(settings,'mfa_enforce_staff',False)
    monkeypatch.setattr(settings,'staff_mfa_exempt_user_ids','')

@pytest.fixture
def member(database):
    uid='viewer-'+uuid4().hex[:10]
    database[1].execute('INSERT INTO users(id,handle,email) VALUES(%s,%s,%s)',(uid,uid,uid+'@example.test'))
    return uid


def test_owner_mfa_private_and_no_mutation_routes(client,actor,database,member,monkeypatch):
    client.cookies.clear();assert client.get(BASE,params={'q':member}).status_code==401
    for uid in ('author','reviewer1','reviewer2','outsider'):
        actor(uid)
        assert client.get(BASE,params={'q':member}).status_code==403
        assert client.get(BASE+'/'+member).status_code==403
    database[1].execute("INSERT INTO review_grants(user_id,role,subject_id,granted_by,reason) VALUES('outsider','owner','english','test','Synthetic scoped grant')")
    actor('outsider');assert client.get(BASE+'/'+member).status_code==403
    h=actor('owner');monkeypatch.setattr(settings,'mfa_enforce_staff',True)
    assert client.get(BASE,params={'q':member}).status_code==403
    assert client.get(BASE+'/'+member).status_code==403
    monkeypatch.setattr(settings,'staff_mfa_exempt_user_ids','some-owner')
    assert client.get(BASE+'/'+member).status_code==403
    monkeypatch.setattr(settings,'staff_mfa_exempt_user_ids','owner')
    response=client.get(BASE+'/'+member);assert response.status_code==200,response.text
    assert response.headers['cache-control']=='private, no-store'
    monkeypatch.setattr(settings,'staff_mfa_exempt_user_ids','')
    database[1].execute("UPDATE auth_sessions SET mfa_verified_at=now() WHERE user_id='owner'")
    assert client.get(BASE+'/'+member).status_code==200
    assert client.post(BASE+'/'+member,json={},headers=h).status_code==405
    assert client.delete(BASE+'/'+member,headers=h).status_code==405
    assert client.get(BASE+'/missing').status_code==404
    assert client.get(BASE,params={'q':'  '}).status_code==422
    assert client.get(BASE,params={'q':'bad\x00query'}).status_code==422


def test_bounded_literal_handle_and_exact_email_search(client,actor,database,member):
    conn=database[1];actor('owner')
    conn.execute("INSERT INTO users(id,handle,email) SELECT 'viewer-many-'||n,'viewer_many_'||n,'many'||n||'@example.test' FROM generate_series(1,25) n")
    conn.execute("INSERT INTO users(id,handle) VALUES('viewer-guest','viewer-guest')")
    exact=client.get(BASE,params={'q':(' '+member+'@example.test ').upper()});assert exact.status_code==200,exact.text
    assert [r['id'] for r in exact.json()['items']]==[member]
    assert client.get(BASE,params={'q':'many1@'}).json()['items']==[]
    assert client.get(BASE,params={'q':'viewer%'}).json()['items']==[]
    assert client.get(BASE,params={'q':'viewer\\'}).json()['items']==[]
    result=client.get(BASE,params={'q':'viewer_many_'}).json()
    assert len(result['items'])==20 and result['more']
    assert client.get(BASE+'/viewer-guest').status_code==404


def test_read_only_real_role_empty_snapshot_no_private_content(client,actor,database,member):
    conn=database[1];actor('owner')
    tables=['reward_ledger','attempts','account_security_events','billing_account_rates','worker_heartbeats']
    before={t:conn.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in tables}
    async def read():
        async with cursor() as cur:
            await cur.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
            await cur.execute('SET LOCAL ROLE mpsc')
            return await account_viewer.snapshot(cur,member)
    body=client.portal.call(read)
    assert body['read_only'] and body['study']['attempts']==body['study']['verified_correct']==0
    assert body['account']['last_activity_at'] is None and body['account']['roles']==[]
    assert body['study']['streak']['current_streak_days']==0
    assert body['access']['has_pro'] is False and body['access']['amount_paise']==10000
    assert body['economy']['ledger']==[] and body['community']['blocks_given']==0
    response=client.get(BASE+'/'+member)
    for secret in ('password_hash','token_hash','secret_cipher','parent_session_hash','chosen_text','body','blocked_id','event_key','note'):
        assert '"'+secret+'"' not in response.text
    assert {t:conn.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in tables}==before


def test_access_wallet_cap_window_activity_and_sessions(client,actor,database,member):
    conn=database[1];actor('owner')
    conn.execute("INSERT INTO billing_account_rates(user_id,amount_paise,updated_by) VALUES(%s,5000,'owner')",(member,))
    conn.execute("INSERT INTO billing_access_grants(user_id,granted_by,idempotency_key,days,starts_at,ends_at) VALUES(%s,'owner','synthetic-grant',7,now()-interval '1 day',now()+interval '6 days')",(member,))
    conn.execute("INSERT INTO reward_ledger(user_id,event_key,kind,xp,points,note,created_at) SELECT %s,%s||n,'adjustment',n,n,'PRIVATE STUDY ITEM',now()-n*interval '1 minute' FROM generate_series(1,25) n",(member,member))
    conn.execute("INSERT INTO reward_daily_counters(user_id,day,xp,points) SELECT %s,(now() AT TIME ZONE 'Asia/Kolkata')::date-n,CASE WHEN n=1 THEN 299 ELSE 300 END,0 FROM generate_series(0,31) n",(member,))
    conn.execute("INSERT INTO auth_sessions(token_hash,user_id,created_at,expires_at,revoked_at) VALUES(%s,%s,now()-interval '2 hours',now()+interval '1 day',NULL),(%s,%s,now()-interval '3 hours',now()-interval '1 day',NULL),(%s,%s,now()-interval '4 hours',now()+interval '1 day',now())",(member+'live',member,member+'old',member,member+'revoked',member))
    conn.execute("INSERT INTO mobile_sessions(token_hash,public_id,user_id,parent_session_hash) VALUES(%s,%s,%s,%s),(%s,%s,%s,%s)",(member+'mobile',member+'mobile',member,member+'live',member+'orphan',member+'orphan',member,member+'revoked'))
    # An owner pricing action must not manufacture learner activity.
    conn.execute("INSERT INTO account_security_events(user_id,action) VALUES(%s,'owner_billing_rate_changed')",(member,))
    r=client.get(BASE+'/'+member);assert r.status_code==200,r.text
    b=r.json();assert b['access']['has_pro'] and b['access']['status']=='granted'
    assert b['access']['amount_paise']==5000 and b['access']['grants'][0]['active']
    assert b['account']['web_sessions']==b['account']['mobile_sessions']==1
    assert len(b['economy']['ledger'])==20 and b['economy']['ledger'][0]['xp']==1
    assert b['economy']['points']==325 and b['economy']['cap_days']==29
    assert 'PRIVATE STUDY ITEM' not in r.text
    conn.execute("UPDATE users SET plan_code='pro',plan_status='active',plan_ends_at=now()-interval '1 day' WHERE id=%s",(member,))
    # Still Pro through the immutable grant, regardless of expired paid plan.
    assert client.get(BASE+'/'+member).json()['access']['has_pro']


def test_verified_attempts_respect_latest_assessment_and_current_holds(client,actor,database,member):
    from test_learning_loop import questions,attempt
    conn=database[1];_,ids=questions(database,3)
    a=attempt(conn,member,ids[0]);attempt(conn,member,ids[1],source='inferred');attempt(conn,member,ids[2])
    actor('owner');b=client.get(BASE+'/'+member).json()
    assert b['study']['attempts']==3 and b['study']['verified_correct']==2
    conn.execute("INSERT INTO attempt_assessments(attempt_id,input_hash,policy_version,payload) VALUES(%s,%s,'synthetic',%s)",(a,uuid4().hex,Jsonb({'outcome':'wrong'})))
    assert client.get(BASE+'/'+member).json()['study']['verified_correct']==1
    conn.execute("UPDATE canonical_questions SET status='held' WHERE id=%s",(ids[2],))
    b=client.get(BASE+'/'+member).json();assert b['study']['verified_correct']==0
    assert b['account']['last_activity_at'] is not None


def test_community_counts_and_blocks_hide_identities(client,actor,database,member):
    conn=database[1]
    post=conn.execute("INSERT INTO posts(canonical_id,author_id,kind,body) VALUES('cq_test',%s,'doubt','PRIVATE POST BODY') RETURNING id",(member,)).fetchone()[0]
    conn.execute("INSERT INTO posts(canonical_id,author_id,kind,parent_id,body) VALUES('cq_test',%s,'reply',%s,'PRIVATE REPLY BODY')",(member,post))
    conn.execute("INSERT INTO post_votes(post_id,user_id) VALUES(%s,'author'),(%s,'outsider')",(post,post))
    conn.execute("INSERT INTO creator_blocks(user_id,blocked_id) VALUES(%s,'outsider'),('reviewer1',%s)",(member,member))
    conn.execute("INSERT INTO abuse_reports(post_id,reason,reporter_id) VALUES(%s,'other','author')",(post,))
    actor('owner');r=client.get(BASE+'/'+member);assert r.status_code==200,r.text
    c=r.json()['community'];assert c['posts']==c['replies']==1
    assert c['helpful_received']==1 and c['blocks_given']==c['blocks_received']==1
    assert c['post_reports']==1 and c['needs_approval']
    assert not any(s in r.text for s in ('PRIVATE POST','PRIVATE REPLY','reviewer1','outsider'))


def test_outage_is_not_an_empty_account(client,actor,member,monkeypatch):
    actor('owner')
    async def fail(*args):raise RuntimeError('Synthetic database outage')
    monkeypatch.setattr(account_viewer,'snapshot',fail)
    with pytest.raises(RuntimeError,match='Synthetic database outage'):
        client.get(BASE+'/'+member)


def test_native_owner_and_revoked_global_grant_denied(client,actor,database):
    from test_mobile_companion import connect
    headers,_=connect(client,actor,'owner')
    assert client.get(BASE,params={'q':'author'},headers=headers).status_code==403
    actor('owner');database[1].execute("UPDATE review_grants SET revoked_at=now() WHERE user_id='owner'")
    assert client.get(BASE,params={'q':'author'}).status_code==403

