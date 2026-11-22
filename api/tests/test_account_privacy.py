"""Synthetic PostgreSQL cases; no real identity provider, email or payment calls."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from uuid import uuid4
import pytest
from app.config import settings
from app.db import cursor
from app.routers import account_privacy as privacy
from app.services import audience
from test_learning_workflows import learner


@pytest.fixture(autouse=True)
def real_role(monkeypatch):
    @asynccontextmanager
    async def role_cursor():
        async with cursor() as cur:
            await cur.execute('SET LOCAL ROLE mpsc')
            yield cur
    monkeypatch.setattr(privacy,'cursor',role_cursor)
    monkeypatch.setattr(audience,'cursor',role_cursor)


def payload(user,kind='erasure',key=None):
    return {'user_id':user,'kind':kind,'request_key':key or uuid4().hex}


def test_request_ownership_idempotency_and_no_erasure_side_effect(client,actor,database):
    user,h=learner(database,actor);c=database[1];body=payload(user)
    assert client.post('/api/account-privacy/requests',json=body).status_code==403
    assert client.post('/api/account-privacy/requests',headers=h,json={**body,'user_id':'outsider'}).status_code==409
    with ThreadPoolExecutor(2) as pool:
        results=list(pool.map(lambda _:client.post('/api/account-privacy/requests',headers=h,json=body),range(2)))
    assert [r.status_code for r in results]==[200,200]
    rid=results[0].json()['id'];assert results[1].json()['id']==rid
    assert c.execute('SELECT count(*) FROM privacy_request_events WHERE request_id=%s',(rid,)).fetchone()[0]==1
    assert c.execute('SELECT email,closed_at FROM users WHERE id=%s',(user,)).fetchone()==(user+'@example.test',None)
    assert client.post('/api/account-privacy/requests',headers=h,json={**body,'kind':'access'}).status_code==409
    own=client.get('/api/account-privacy/requests');assert own.headers['cache-control']=='private, no-store'
    assert own.json()['items'][0]['state']=='received' and 'request_key' not in own.text
    _,other=learner(database,actor)
    assert client.get('/api/account-privacy/requests').json()['items']==[]
    assert client.post('/api/account-privacy/requests/'+rid+'/withdraw',headers=other,json={'user_id':client.get('/api/account-privacy/status').json()['user_id'],'expected_version':1,'state':'withdrawn'}).status_code==404


def test_versions_terminal_states_owner_permissions_and_audit(client,actor,database,monkeypatch):
    user,h=learner(database,actor)
    rid=client.post('/api/account-privacy/requests',headers=h,json=payload(user)).json()['id']
    body={'user_id':user,'expected_version':1,'state':'completed'}
    assert client.post('/api/account-privacy/admin/requests/'+rid,headers=h,json=body).status_code==403
    oh=actor('owner')
    assert client.get('/api/account-privacy/admin/requests').status_code==200
    monkeypatch.setattr(settings,'mfa_enforce_staff',True)
    assert client.post('/api/account-privacy/admin/requests/'+rid,headers=oh,json=body).status_code==403
    monkeypatch.setattr(settings,'mfa_enforce_staff',False)
    r=client.post('/api/account-privacy/admin/requests/'+rid,headers=oh,json={**body,'state':'in_review'})
    assert r.status_code==200 and r.json()['version']==2
    assert client.post('/api/account-privacy/admin/requests/'+rid,headers=oh,json=body).status_code==409
    h=actor(user);withdraw={'user_id':user,'expected_version':2,'state':'withdrawn'}
    assert client.post('/api/account-privacy/requests/'+rid+'/withdraw',headers=h,json=withdraw).status_code==200
    assert client.post('/api/account-privacy/requests/'+rid+'/withdraw',headers=h,json={**withdraw,'expected_version':3}).status_code==409
    assert database[1].execute('SELECT state FROM privacy_request_events WHERE request_id=%s ORDER BY id',(rid,)).fetchall()==[('received',),('in_review',),('withdrawn',)]


def test_no_guest_creation_no_capability_leak_and_open_limit(client,actor,database):
    c=database[1];client.cookies.clear();before=c.execute('SELECT count(*) FROM users').fetchone()[0]
    assert client.get('/api/account-privacy/requests').status_code==401
    assert client.get('/api/account-privacy/status').json()['guardian_enrollment_available'] is False
    assert c.execute('SELECT count(*) FROM users').fetchone()[0]==before
    user,h=learner(database,actor)
    for _ in range(5):assert client.post('/api/account-privacy/requests',headers=h,json=payload(user)).status_code==200
    assert client.post('/api/account-privacy/requests',headers=h,json=payload(user)).status_code==409
    assert client.post('/api/account-privacy/requests',headers=h,json={**payload(user),'child_name':'SHOULD_NOT_STORE'}).status_code==422
    assert client.post('/api/account-privacy/requests',headers=h,json={**payload(user),'extra':'x'*70000}).status_code==413
    exported=client.get('/api/me/data-export',params={'user_id':user})
    assert exported.status_code==200 and len(exported.json()['privacy_requests'])==5
    assert 'request_key' not in exported.text


def declare(client,category='adult',**kw):
    return client.post('/api/account-privacy/declare',headers={'Origin':settings.public_origin,**kw.pop('headers',{})},json={'category':category,**kw})


def test_disabled_gate_preserves_compatibility(client,actor,monkeypatch):
    monkeypatch.setattr(settings,'audience_gate_enabled',False);client.cookies.clear()
    assert client.get('/api/account-privacy/status').json()['age_check_enabled'] is False
    assert declare(client).status_code==409
    assert client.get('/api/me/profile').status_code==200


def test_minor_and_missing_declaration_cannot_create_guest_or_account(client,database,monkeypatch):
    monkeypatch.setattr(settings,'audience_gate_enabled',True);client.cookies.clear();c=database[1]
    before=c.execute('SELECT count(*) FROM users').fetchone()[0]
    assert client.get('/api/me/profile').status_code==403
    r=declare(client,'under18');assert r.status_code==200,r.text
    assert r.json()['guardian_enrollment_available'] is False
    assert 'HttpOnly' in r.headers['set-cookie'] and 'Secure' in r.headers['set-cookie']
    assert client.get('/api/me/profile').status_code==403
    email=uuid4().hex+'@example.test'
    reg={'email':email,'password':'SyntheticPassword123!'}
    assert client.post('/api/auth/register',headers={'Origin':settings.public_origin},json=reg).status_code==403
    assert c.execute('SELECT count(*) FROM users').fetchone()[0]==before
    assert declare(client,'adult').status_code==200
    r=client.post('/api/auth/register',headers={'Origin':settings.public_origin},json=reg)
    assert r.status_code==200,r.text
    assert client.get('/api/me/profile').status_code==200
    assert c.execute('SELECT category FROM account_audience WHERE user_id=(SELECT id FROM users WHERE email=%s)',(email,)).fetchone()==('adult',)


def test_existing_minor_cannot_self_upgrade_or_use_old_native_session(client,actor,database,monkeypatch):
    from test_mobile_companion import connect
    user,h=learner(database,actor);mobile,_=connect(client,actor,user);h=actor(user)
    monkeypatch.setattr(settings,'audience_gate_enabled',True)
    assert client.get('/api/me/profile').status_code==403
    client.cookies.clear()
    assert client.get('/api/me/profile',headers=mobile).status_code==403
    h=actor(user)
    s=client.get('/api/account-privacy/status').json()
    r=declare(client,'under18',headers=h,user_id=user,expected_version=s['version']);assert r.status_code==200,r.text
    assert declare(client,'adult',headers=h,user_id=user,expected_version=1).status_code==409
    assert client.get('/api/me/profile').status_code==403
    client.cookies.clear()
    assert client.get('/api/me/profile',headers=mobile).status_code==401
    h=actor(user)
    # Restricted accounts retain request/export/recovery access.
    assert client.post('/api/account-privacy/requests',headers=h,json=payload(user,'erasure')).status_code==200
    assert client.get('/api/me/data-export',params={'user_id':user}).status_code==200
    assert client.post('/api/mobile-auth/authorize',headers=h,json={'flow':'a'*43}).status_code==403


def test_expiry_account_switch_and_google_start_guard(client,actor,database,monkeypatch):
    from app.routers import google_auth
    monkeypatch.setattr(settings,'audience_gate_enabled',True)
    monkeypatch.setattr(settings,'google_client_id','synthetic');monkeypatch.setattr(settings,'google_client_secret','synthetic')
    client.cookies.clear()
    assert client.post('/api/auth/google/start',headers={'Origin':settings.public_origin},json={}).status_code==403
    assert declare(client).status_code==200
    assert client.post('/api/auth/google/start',headers={'Origin':settings.public_origin},json={}).status_code==200
    database[1].execute("UPDATE audience_browser_flows SET expires_at=now()-interval '1 second'")
    assert client.get('/api/me/profile').status_code==403
    user,h=learner(database,actor)
    assert declare(client,'adult',headers=h,user_id='outsider').status_code==409
    assert declare(client,'adult',headers=h,user_id=user).status_code==200
    assert client.post('/api/account-privacy/confirm-adult',headers=h,json={'user_id':user,'expected_version':0}).status_code==200
    assert client.get('/api/me/profile').status_code==200


def test_google_callback_cannot_provision_after_age_choice_expires(client,actor,database,monkeypatch):
    from app.routers import google_auth as google
    from test_google_auth import begin,callback,finish
    monkeypatch.setattr(settings,'google_client_id','synthetic');monkeypatch.setattr(settings,'google_client_secret','synthetic')
    monkeypatch.setattr(settings,'audience_gate_enabled',True)
    client.cookies.clear();assert declare(client).status_code==200
    email=uuid4().hex+'@example.test'
    state,_=begin(client,monkeypatch,email);callback(client,state)
    database[1].execute("UPDATE audience_browser_flows SET expires_at=now()-interval '1 second'")
    assert finish(client).status_code==403
    assert database[1].execute('SELECT count(*) FROM users WHERE email=%s',(email,)).fetchone()[0]==0
    assert declare(client).status_code==200
    r=finish(client);assert r.status_code==200,r.text
    assert database[1].execute('SELECT category FROM account_audience WHERE user_id=(SELECT id FROM users WHERE email=%s)',(email,)).fetchone()==('adult',)


def test_transaction_rechecks_restriction_and_rolls_back_stale_write(client,actor,database,monkeypatch):
    from fastapi import HTTPException
    user,h=learner(database,actor);c=database[1]
    c.execute("INSERT INTO account_audience(user_id,category) VALUES(%s,'adult')",(user,))
    monkeypatch.setattr(settings,'audience_gate_enabled',True)
    async def race():
        # Execute in the TestClient loop: avoid replacing its active pool.
        token=audience.mutation_actor.set(user)
        try:
            async with cursor() as cur:
                await cur.execute('INSERT INTO personal_desks(user_id,document) VALUES(%s,\'{}\')',(user,))
                c.execute("UPDATE account_audience SET category='under18',version=version+1 WHERE user_id=%s",(user,))
        finally:audience.mutation_actor.reset(token)
    with pytest.raises(HTTPException) as exc:client.portal.call(race)
    assert exc.value.status_code==403
    assert c.execute('SELECT count(*) FROM personal_desks WHERE user_id=%s',(user,)).fetchone()[0]==0


def test_api_does_not_offer_native_guardian_approval_or_identity_upload(client,actor,database):
    from test_mobile_companion import connect
    user,h=learner(database,actor);mobile,_=connect(client,actor,user);client.cookies.clear()
    assert client.get('/api/account-privacy/status',headers=mobile).status_code==403
    assert client.post('/api/account-privacy/admin/verify-guardian',headers=mobile,json={'verified':True}).status_code==403


def test_stale_cookie_does_not_trap_anonymous_age_declaration(client,actor,monkeypatch):
    monkeypatch.setattr(settings,'audience_gate_enabled',True)
    client.cookies.clear();client.cookies.set('ism_session','expired-local-preview-cookie')
    assert declare(client,'under18').status_code==200
    assert client.post('/api/account-privacy/declare',headers={'Origin':'https://evil.test'},json={'category':'adult'}).status_code==403
    h=actor('author')
    assert declare(client,'adult',user_id='author').status_code==403
    assert declare(client,'adult',headers=h,user_id='author').status_code==200


def test_expired_browser_cleanup_is_bounded_and_audit_is_append_only(client,actor,database,monkeypatch):
    import psycopg
    from app.services.account_retention import sweep
    user,h=learner(database,actor);c=database[1]
    rid=client.post('/api/account-privacy/requests',headers=h,json=payload(user)).json()['id']
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        with c.transaction():
            c.execute('SET LOCAL ROLE mpsc')
            c.execute('DELETE FROM privacy_request_events WHERE request_id=%s',(rid,))
    monkeypatch.setattr(settings,'audience_gate_enabled',True)
    c.execute("INSERT INTO audience_browser_flows(token_hash,category,expires_at) SELECT md5('cleanup-'||n::text)||md5('cleanup2-'||n::text),'under18',now()-interval '1 hour' FROM generate_series(1,502) n")
    before=c.execute('SELECT count(*) FROM audience_browser_flows WHERE expires_at<now()').fetchone()[0]
    async def cleanup():
        async with cursor() as cur:
            await cur.execute('SET LOCAL ROLE mpsc')
            return await sweep(cur)
    result=client.portal.call(cleanup)
    assert result['audience_flows']==500
    assert c.execute('SELECT count(*) FROM audience_browser_flows WHERE expires_at<now()').fetchone()[0]==before-500


def test_adult_only_rejects_new_guardian_requests_preserves_historical_retry_and_withdrawal(client,actor,database):
    user,h=learner(database,actor);c=database[1];body=payload(user,'guardian')
    before=c.execute('SELECT count(*) FROM privacy_request_events').fetchone()[0]
    rejected=client.post('/api/account-privacy/requests',headers=h,json=body)
    assert rejected.status_code==422 and '18 or over' in rejected.json()['detail']
    assert c.execute('SELECT count(*) FROM privacy_requests WHERE user_id=%s',(user,)).fetchone()[0]==0
    assert c.execute('SELECT count(*) FROM privacy_request_events').fetchone()[0]==before
    rid='historical-'+uuid4().hex
    c.execute("INSERT INTO privacy_requests(id,user_id,kind,request_key) VALUES(%s,%s,'guardian',%s)",(rid,user,body['request_key']))
    c.execute("INSERT INTO privacy_request_events(request_id,actor_id,state) VALUES(%s,%s,'received')",(rid,user))
    replay=client.post('/api/account-privacy/requests',headers=h,json=body)
    assert replay.status_code==200 and replay.json()['id']==rid
    assert c.execute('SELECT count(*) FROM privacy_request_events WHERE request_id=%s',(rid,)).fetchone()[0]==1
    assert client.post('/api/account-privacy/requests/'+rid+'/withdraw',headers=h,json={'user_id':user,'expected_version':1,'state':'withdrawn'}).status_code==200
    assert c.execute('SELECT state FROM privacy_request_events WHERE request_id=%s ORDER BY id',(rid,)).fetchall()==[('received',),('withdrawn',)]
