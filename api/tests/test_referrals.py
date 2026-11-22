"""Prospective access grants against disposable PostgreSQL; no provider calls."""
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
import pytest
from app.config import settings
from app.db import cursor
from app.services import referrals as service, mfa
from app.routers import referrals as routes, auth, google_auth as google
from test_learning_workflows import learner
from test_learning_loop import questions,attempt,run

TICK=service.tick

@pytest.fixture(autouse=True)
def setup(client,database,monkeypatch):
    # Legacy auth tables predate per-migration ACLs. Match their existing live
    # mpsc CRUD grants (read-only ACL check, 19 Nov); no new referral privileges.
    database[1].execute('GRANT SELECT,INSERT,UPDATE,DELETE ON users,auth_login_attempts,auth_sessions,google_auth_flows,google_identities TO mpsc')
    @asynccontextmanager
    async def role():
        async with cursor() as cur:
            await cur.execute('SET LOCAL ROLE mpsc');yield cur
    for module in (service,routes,auth,google):monkeypatch.setattr(module,'cursor',role)
    async def ready(cur):return True
    async def noop():pass
    monkeypatch.setattr(service,'launch_ready',ready)
    monkeypatch.setattr(service,'tick',noop)
    monkeypatch.setattr(settings,'referral_rewards_enabled',True)


def invitation(client,actor,database):
    user,h=learner(database,actor)
    database[1].execute('UPDATE users SET email_verified_at=now() WHERE id=%s',(user,))
    r=save(client,h,user,0,True);assert r.status_code==200,r.text
    return user,h,r.json()['code']['code']


def save(client,h,user,version,enabled):
    return client.post('/api/referrals/code',headers=h,json={'user_id':user,'expected_version':version,'enabled':enabled})


def signup(client,database,code,verified=True):
    email='referral-'+uuid4().hex+'@example.test';client.cookies.clear()
    r=client.post('/api/auth/register',headers={'Origin':settings.public_origin},json={'email':email,'password':'SyntheticPassword123!','referral_code':code})
    assert r.status_code==200,r.text
    user=database[1].execute('SELECT id FROM users WHERE email=%s',(email,)).fetchone()[0]
    if verified:database[1].execute('UPDATE users SET email_verified_at=now() WHERE id=%s',(user,))
    return user


def qualify(database,user,n=10,**kwargs):
    _,ids=questions(database,n)
    for q in ids:attempt(database[1],user,q,**kwargs)
    return ids


def decision(client,database,user):
    async def invoke(cur):
        await cur.execute('SELECT * FROM referral_claims WHERE referred_id=%s FOR UPDATE',(user,))
        return await service.decide(cur,await cur.fetchone())
    return run(client,invoke)


def test_private_default_csrf_version_account_verified_and_paused_withdrawal(client,actor,database,monkeypatch):
    user,h=learner(database,actor)
    r=client.get('/api/referrals/me');assert r.status_code==200 and r.headers['cache-control']=='private, no-store'
    assert r.json()['code'] is None and r.json()['verified'] is False
    assert save(client,h,user,0,True).status_code==409
    database[1].execute('UPDATE users SET email_verified_at=now() WHERE id=%s',(user,))
    assert save(client,{},user,0,True).status_code==403
    assert save(client,h,'owner',0,True).status_code==409
    r=save(client,h,user,0,True);assert r.status_code==200,r.text
    code=r.json()['code']['code'];assert len(code)==24
    assert save(client,h,user,0,False).status_code==409
    async def limited(*args):raise Exception('Withdrawal must bypass subscription limits')
    monkeypatch.setattr(mfa,'limit',limited);monkeypatch.setattr(settings,'referral_rewards_enabled',False)
    r=save(client,h,user,1,False);assert r.status_code==200 and r.json()['code']['enabled'] is False
    client.cookies.clear();assert client.get('/api/referrals/me').status_code==401
    assert client.get('/api/referrals/invite/'+code).json()['available'] is False
    assert client.post('/api/referrals/award',json={}).status_code==404


def test_qualification_tenth_answer_two_grants_once_no_currency_or_plan_changes(client,actor,database):
    conn=database[1];inviter,_,code=invitation(client,actor,database);friend=signup(client,database,code)
    before=conn.execute('SELECT id,plan_code,plan_status,plan_ends_at,trial_ends_at FROM users WHERE id=ANY(%s) ORDER BY id',([inviter,friend],)).fetchall()
    assert not decision(client,database,friend);qualify(database,friend,9)
    assert not decision(client,database,friend);qualify(database,friend,1)
    wallet=conn.execute('SELECT count(*) FROM reward_ledger').fetchone()[0]
    with ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(lambda _:decision(client,database,friend),range(3)))
    assert sum(results)==1
    assert conn.execute('SELECT id,plan_code,plan_status,plan_ends_at,trial_ends_at FROM users WHERE id=ANY(%s) ORDER BY id',([inviter,friend],)).fetchall()==before
    assert conn.execute('SELECT count(*) FROM reward_ledger').fetchone()[0]==wallet
    grants=conn.execute("SELECT user_id,days,granted_by,source,ends_at-starts_at FROM billing_access_grants WHERE user_id=ANY(%s) ORDER BY user_id",([inviter,friend],)).fetchall()
    assert len(grants)==2 and all(g[1:4]==(7,None,'referral') and g[4].days==7 for g in grants)
    trial=next(r[4] for r in before if r[0]==friend)
    assert conn.execute('SELECT starts_at FROM billing_access_grants WHERE user_id=%s',(friend,)).fetchone()[0]>=trial
    assert conn.execute("SELECT count(*) FROM review_notifications WHERE event_key LIKE %s",('referral:'+friend+':%',)).fetchone()[0]==2
    data=client.get('/api/referrals/me').json()
    assert data['signup_referral']=={'state':'credited','scored_attempts':10}
    assert inviter not in str(data) and 'attempt_ids' not in str(data) and 'email' not in str(data)
    billing=client.get('/api/billing/me');assert billing.status_code==200,billing.text
    assert billing.json()['granted_access'][0]['source']=='referral'


@pytest.mark.parametrize('reason',['unverified','inviter_unverified','closed','held','inferred','derived','assessment','old','future','skipped','mock'])
def test_ineligible_attempts_accounts_or_active_assessments_do_not_credit(client,actor,database,reason):
    conn=database[1];inviter,_,code=invitation(client,actor,database);friend=signup(client,database,code,verified=reason!='unverified')
    kwargs={}
    if reason in ('inferred','derived'):kwargs['source']=reason
    if reason=='old':kwargs['at']='2000-01-01T00:00:00Z'
    if reason=='future':kwargs['at']='2100-01-01T00:00:00Z'
    if reason=='mock':kwargs['context']='mock'
    ids=qualify(database,friend,**kwargs)
    if reason=='inviter_unverified':conn.execute('UPDATE users SET email_verified_at=NULL WHERE id=%s',(inviter,))
    if reason=='closed':
        from app.services.account_tools import close
        run(client,close,friend,0)
    if reason=='held':conn.execute("UPDATE canonical_questions SET status='held' WHERE id=ANY(%s)",(ids,))
    if reason=='skipped':conn.execute('UPDATE attempts SET chosen_text=NULL WHERE user_id=%s',(friend,))
    if reason=='assessment':conn.execute("INSERT INTO mock_sessions(id,user_id,collection_id,question_ids,duration_seconds) VALUES(%s,%s,'udc',%s,1200)",('ref-'+uuid4().hex,friend,ids))
    assert decision(client,database,friend)==(reason=='closed')
    assert not conn.execute("SELECT 1 FROM billing_access_grants WHERE user_id=%s",(friend,)).fetchone()


def test_launch_disabled_or_failed_gate_attaches_nothing_and_never_backfills(client,actor,database,monkeypatch):
    inviter,_,code=invitation(client,actor,database)
    async def not_ready(cur):return False
    monkeypatch.setattr(service,'launch_ready',not_ready)
    friend=signup(client,database,code)
    assert not database[1].execute('SELECT 1 FROM referral_claims WHERE referred_id=%s',(friend,)).fetchone()
    assert client.get('/api/referrals/invite/'+code).json()['available'] is False
    async def ready(cur):return True
    monkeypatch.setattr(service,'launch_ready',ready)
    assert run(client,service.attach_signup,friend,code)=={'state':'unavailable'}
    assert not database[1].execute('SELECT 1 FROM referral_claims WHERE referred_id=%s',(friend,)).fetchone()
    monkeypatch.setattr(settings,'referral_rewards_enabled',False)
    assert run(client,service.attach_signup,friend,code)=={'state':'unavailable'}


def test_revoked_or_unknown_link_signup_succeeds_without_claim(client,actor,database):
    inviter,h,code=invitation(client,actor,database)
    assert save(client,h,inviter,1,False).status_code==200
    for value in (code,'A'*24):
        friend=signup(client,database,value)
        assert not database[1].execute('SELECT 1 FROM referral_claims WHERE referred_id=%s',(friend,)).fetchone()


def test_concurrent_referrer_cap_five_rolling_year_and_terminal_replay(client,actor,database):
    conn=database[1];inviter,_,code=invitation(client,actor,database)
    friends=[signup(client,database,code) for _ in range(6)]
    for friend in friends:qualify(database,friend)
    with ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(lambda u:decision(client,database,u),friends))
    states=conn.execute('SELECT referred_id,state FROM referral_decisions WHERE referrer_id=%s',(inviter,)).fetchall()
    assert sum(s=='credited' for _,s in states)==5 and sum(s=='capped' for _,s in states)==1
    assert conn.execute('SELECT count(*) FROM billing_access_grants WHERE user_id=%s',(inviter,)).fetchone()[0]==5
    assert client.portal.call(TICK) is None
    assert all(not decision(client,database,f) for f in friends)
    capped=next(u for u,s in states if s=='capped')
    # Explicit synthetic historical receipt: only the disposable admin can bypass
    # immutability for this clock-boundary fixture, never an application endpoint.
    conn.execute('ALTER TABLE referral_decisions DISABLE TRIGGER immutable_referral_decision')
    try:conn.execute("UPDATE referral_decisions SET decided_at=now()-interval '1 year 1 day' WHERE referrer_id=%s AND state='credited'",(inviter,))
    finally:conn.execute('ALTER TABLE referral_decisions ENABLE TRIGGER immutable_referral_decision')
    newer=signup(client,database,code);qualify(database,newer);assert decision(client,database,newer)
    assert not decision(client,database,capped)
    assert conn.execute("SELECT count(*) FROM referral_decisions WHERE referrer_id=%s AND state='credited' AND decided_at>now()-interval '1 year'",(inviter,)).fetchone()[0]==1


def test_closed_account_disables_link_exports_private_fields_and_preserves_receipts(client,actor,database):
    from app.services import account_tools
    inviter,h,code=invitation(client,actor,database);friend=signup(client,database,code);qualify(database,friend)
    assert decision(client,database,friend)
    async def exported(cur):return ''.join([chunk async for chunk in account_tools.export(cur,friend)])
    data=run(client,exported)
    assert 'referral_result' in data and 'credited' in data and 'referral' in data
    assert inviter not in data and 'attempt_ids' not in data and 'invite_code' not in data
    run(client,account_tools.close,inviter,0)
    assert client.get('/api/referrals/invite/'+code).json()['available'] is False
    assert database[1].execute('SELECT enabled FROM referral_codes WHERE user_id=%s',(inviter,)).fetchone()==(False,)
    assert not decision(client,database,friend)


def test_google_new_signup_carries_code_existing_signin_and_link_do_not_attach(client,actor,database,monkeypatch):
    from urllib.parse import parse_qs,urlparse
    inviter,_,code=invitation(client,actor,database)
    monkeypatch.setattr(settings,'google_client_id','synthetic-client');monkeypatch.setattr(settings,'google_client_secret','synthetic-secret')
    sub=uuid4().hex;email=uuid4().hex+'@example.test'
    monkeypatch.setattr(google,'exchange',lambda *args:dict(sub=sub,email=email,email_verified=True))
    def flow(action='login'):
        headers={'Origin':settings.public_origin,'X-Review-CSRF':client.get('/api/auth/session').json().get('csrf','')}
        r=client.post('/api/auth/google/start',headers=headers,json={'action':action,'referral_code':code});assert r.status_code==200,r.text
        state=parse_qs(urlparse(r.json()['url']).query)['state'][0]
        r=client.get('/api/auth/google/callback',params={'state':state,'code':'synthetic'},follow_redirects=False);assert r.status_code==303,r.text
        r=client.post('/api/auth/google/finish',headers=headers,json={});assert r.status_code==200,r.text
    client.cookies.clear();flow()
    friend=database[1].execute('SELECT user_id FROM google_identities WHERE subject=%s',(sub,)).fetchone()[0]
    assert database[1].execute('SELECT referrer_id FROM referral_claims WHERE referred_id=%s',(friend,)).fetchone()==(inviter,)
    client.cookies.clear();flow()
    assert database[1].execute('SELECT count(*) FROM referral_claims WHERE referred_id=%s',(friend,)).fetchone()[0]==1
    user,h=learner(database,actor);sub=uuid4().hex;flow('link')
    assert not database[1].execute('SELECT 1 FROM referral_claims WHERE referred_id=%s',(user,)).fetchone()


def test_native_paths_remain_closed_and_real_launch_gate_is_not_faked(client,database):
    from app.services.mobile_identity import allowed,capabilities
    for method,path in [('GET','/api/referrals/me'),('POST','/api/referrals/code')]:assert not allowed(method,path)
    assert 'referrals' not in capabilities()
    assert run(client,service.reward_economy.feature_gates)['catalog_ready'] is False


def test_worker_waits_for_verification_then_credits_once_and_partial_grant_failure_rolls_back(client,actor,database,monkeypatch):
    inviter,_,code=invitation(client,actor,database);friend=signup(client,database,code,verified=False);qualify(database,friend)
    client.portal.call(TICK)
    assert not database[1].execute('SELECT 1 FROM referral_decisions WHERE referred_id=%s',(friend,)).fetchone()
    database[1].execute('UPDATE users SET email_verified_at=now() WHERE id=%s',(friend,))
    original=service.grant
    async def interrupted(cur,user,key,stamp):
        if key.endswith(':referred'):raise RuntimeError('Synthetic interruption before second grant')
        return await original(cur,user,key,stamp)
    monkeypatch.setattr(service,'grant',interrupted)
    with pytest.raises(RuntimeError):decision(client,database,friend)
    assert not database[1].execute('SELECT 1 FROM billing_access_grants WHERE user_id=ANY(%s)',([inviter,friend],)).fetchone()
    monkeypatch.setattr(service,'grant',original)
    with ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(lambda _:client.portal.call(TICK),range(2)))
    assert database[1].execute('SELECT state FROM referral_decisions WHERE referred_id=%s',(friend,)).fetchone()==('credited',)
    assert database[1].execute('SELECT count(*) FROM billing_access_grants WHERE user_id=ANY(%s)',([inviter,friend],)).fetchone()[0]==2


def test_attribution_receipts_and_access_grants_immutable_with_least_privileges(client,actor,database):
    import psycopg
    inviter,_,code=invitation(client,actor,database);friend=signup(client,database,code);qualify(database,friend);assert decision(client,database,friend)
    async def mutate(cur,query):await cur.execute(query,(friend,))
    for query in ["UPDATE referral_claims SET created_at=created_at-interval '1 day' WHERE referred_id=%s",
                  "UPDATE referral_decisions SET state='closed' WHERE referred_id=%s",
                  'DELETE FROM referral_decisions WHERE referred_id=%s',
                  'DELETE FROM referral_claims WHERE referred_id=%s',
                  'DELETE FROM billing_access_grants WHERE user_id=%s']:
        with pytest.raises(psycopg.Error):run(client,mutate,query)
