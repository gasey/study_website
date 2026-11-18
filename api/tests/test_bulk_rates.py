"""Actual mpsc bulk discounts over isolated accounts; no external provider calls."""
import hashlib
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
import pytest
from app.config import settings
from app.routers.auth import _hash_password
from app.services import bulk_rate_release
BASE='/api/billing/bulk'

@pytest.fixture(autouse=True)
def real_role(client,monkeypatch):
    from contextlib import asynccontextmanager
    from app import db
    from app.routers import bulk_rates
    original=db.cursor
    @asynccontextmanager
    async def role_cursor():
        async with original() as cur:
            await cur.execute('SET LOCAL ROLE mpsc');yield cur
    monkeypatch.setattr(bulk_rates,'cursor',role_cursor)


def user(database,verified=True):
    uid='bulk-'+uuid4().hex;email=uid+'@example.test'
    database[1].execute('INSERT INTO users(id,handle,email,email_verified_at,password_hash) VALUES(%s,%s,%s,CASE WHEN %s THEN now() END,%s)',(uid,uid,email,verified,_hash_password('SyntheticPassword123!')))
    database[1].execute("INSERT INTO auth_sessions(token_hash,user_id,expires_at) VALUES(%s,%s,now()+interval '1 day')",(hashlib.sha256(('test-session-'+uid).encode()).hexdigest(),uid))
    return uid,email

def batch(client,h,emails,key=None,preview=None):
    body={'emails':emails,'note':'Synthetic study group'}
    p=client.post(BASE+'/admin/preview',headers=h,json=body);assert p.status_code==200,p.text
    return client.post(BASE+'/admin/emails',headers=h,json={**body,'preview_hash':preview or p.json()['preview_hash'],'request_key':key or uuid4().hex})

def code(client,h,**kwargs):
    r=client.post(BASE+'/admin/codes',headers=h,json={'note':'Synthetic group','request_key':uuid4().hex,**kwargs});assert r.status_code==200,r.text;return r.json()

def claim(client,actor,uid,value,expected=10000):
    return client.post(BASE+'/claim',headers={**actor(uid),'X-Learning-User':uid},json={'code':value,'expected_amount_paise':expected})

def test_owner_boundaries_preview_and_verified_once_application(client,actor,database,monkeypatch):
    uid,email=user(database);h=actor('reviewer1')
    assert client.get(BASE+'/admin',headers=h).status_code==403
    assert client.post(BASE+'/admin/preview',headers=h,json={'emails':[email],'note':'Test'}).status_code==403
    h=actor('owner');assert client.post(BASE+'/admin/preview',json={'emails':[email],'note':'Test'}).status_code==403
    monkeypatch.setattr(settings,'mfa_enforce_staff',True)
    assert client.post(BASE+'/admin/preview',headers=h,json={'emails':[email],'note':'Test'}).status_code==403
    monkeypatch.setattr(settings,'mfa_enforce_staff',False)
    key=uuid4().hex;body={'emails':[email.upper(),' '+email+' '],'note':'Synthetic study group'}
    p=client.post(BASE+'/admin/preview',headers=h,json=body);assert p.json()['total']==1
    payload={**body,'preview_hash':p.json()['preview_hash'],'request_key':key}
    r=client.post(BASE+'/admin/emails',headers=h,json=payload);assert r.status_code==200,r.text
    assert r.json()['added']==r.json()['applied']==1
    assert client.post(BASE+'/admin/emails',headers=h,json=payload).json()==r.json()
    database[1].execute("UPDATE billing_account_rates SET amount_paise=10000 WHERE user_id=%s",(uid,))
    assert client.post(BASE+'/admin/emails',headers=h,json=payload).json()==r.json()
    r=batch(client,h,[email]);assert r.json()['applied']==r.json()['added']==0
    assert database[1].execute('SELECT amount_paise FROM billing_account_rates WHERE user_id=%s',(uid,)).fetchone()[0]==10000
    assert client.get(BASE+'/admin').headers['cache-control']=='private, no-store'
    assert database[1].execute('SELECT count(*) FROM reward_ledger WHERE user_id=%s',(uid,)).fetchone()[0]==0
    assert not database[1].execute('SELECT account_has_pro(%s)',(uid,)).fetchone()[0]


def test_unverified_signup_waits_for_real_email_confirmation(client,actor,database):
    email='future-'+uuid4().hex+'@example.test';h=actor('owner')
    r=batch(client,h,[email]);assert r.json()['added']==1 and r.json()['applied']==0
    client.cookies.clear();r=client.post('/api/auth/register',headers={'Origin':settings.public_origin},json={'email':email,'password':'SyntheticPassword123!'})
    assert r.status_code==200,r.text
    uid=database[1].execute('SELECT id FROM users WHERE email=%s',(email,)).fetchone()[0]
    assert not database[1].execute('SELECT 1 FROM billing_account_rates WHERE user_id=%s',(uid,)).fetchone()
    raw=uuid4().hex+uuid4().hex
    database[1].execute("INSERT INTO account_email_tokens(token_hash,user_id,purpose,expires_at) VALUES(%s,%s,'verify',now()+interval '1 hour')",(hashlib.sha256(raw.encode()).hexdigest(),uid))
    assert client.post('/api/auth/email/confirm',headers={'Origin':settings.public_origin},json={'token':raw}).status_code==200
    assert database[1].execute('SELECT amount_paise FROM billing_account_rates WHERE user_id=%s',(uid,)).fetchone()[0]==5000
    database[1].execute('UPDATE billing_account_rates SET amount_paise=10000 WHERE user_id=%s',(uid,))
    client.cookies.clear();r=client.post('/api/auth/login',headers={'Origin':settings.public_origin},json={'email':email,'password':'SyntheticPassword123!'})
    assert r.status_code==200,r.text
    assert database[1].execute('SELECT amount_paise FROM billing_account_rates WHERE user_id=%s',(uid,)).fetchone()[0]==10000


def test_preview_drift_revoke_pending_and_exact_versions(client,actor,database):
    uid,email=user(database);h=actor('owner');body={'emails':[email],'note':'Synthetic study group'}
    p=client.post(BASE+'/admin/preview',headers=h,json=body).json()
    database[1].execute("INSERT INTO billing_account_rates(user_id,amount_paise,updated_by) VALUES(%s,5000,'owner')",(uid,))
    assert batch(client,h,[email],preview=p['preview_hash']).status_code==409
    pending='pending-'+uuid4().hex+'@example.test';assert batch(client,h,[pending]).status_code==200
    r=client.post(BASE+'/admin/email-state',headers=h,json={'email':pending,'expected_version':1,'revoked':True});assert r.status_code==200
    assert client.post(BASE+'/admin/email-state',headers=h,json={'email':pending,'expected_version':1,'revoked':False}).status_code==409
    client.cookies.clear();assert client.post('/api/auth/register',headers={'Origin':settings.public_origin},json={'email':pending,'password':'SyntheticPassword123!'}).status_code==200
    assert database[1].execute('SELECT applied_user_id FROM billing_rate_allowlist WHERE email_normalized=%s',(pending,)).fetchone()[0] is None


def test_code_replay_cap_revocation_and_unchanged_access(client,actor,database):
    uid,_=user(database);other,_=user(database);h=actor('owner');row=code(client,h,max_uses=1)
    first=claim(client,actor,uid,row['code']);assert first.status_code==200,first.text
    assert first.json()['saved'] and first.json()['amount_paise']==5000
    database[1].execute('UPDATE billing_account_rates SET amount_paise=10000 WHERE user_id=%s',(uid,))
    replay=claim(client,actor,uid,row['code']);assert replay.json()['already_redeemed'] and replay.json()['amount_paise']==10000
    assert claim(client,actor,other,row['code']).status_code==404
    h=actor('owner');current=next(c for c in client.get(BASE+'/admin').json()['codes'] if c['code']==row['code'])
    assert current['uses']==1 and current['version']==2
    assert client.post(BASE+'/admin/codes/'+row['code']+'/revoke',headers=h,json={'expected_version':1}).status_code==409
    assert client.post(BASE+'/admin/codes/'+row['code']+'/revoke',headers=h,json={'expected_version':2}).status_code==200
    assert claim(client,actor,uid,row['code']).json()['already_redeemed']
    assert not database[1].execute('SELECT account_has_pro(%s)',(uid,)).fetchone()[0]
    for table in ('reward_ledger','billing_payments','billing_access_grants','billing_subscriptions'):
        assert database[1].execute('SELECT count(*) FROM '+table+' WHERE user_id=%s',(uid,)).fetchone()[0]==0


def test_code_creation_retry_expiry_and_payload_guards(client,actor,database):
    h=actor('owner');key=uuid4().hex;row=code(client,h,request_key=key)
    assert code(client,h,request_key=key)['code']==row['code']
    assert client.post(BASE+'/admin/codes',headers=h,json={'note':'Changed','request_key':key}).status_code==409
    assert client.post(BASE+'/admin/codes',headers=h,json={'note':'Test','request_key':uuid4().hex,'max_uses':1001}).status_code==422
    assert client.post(BASE+'/admin/preview',headers=h,json={'emails':['bad'],'note':'Test'}).status_code==422
    # Synthetic expiry via insertion, not by weakening the immutable code guard.
    value=uuid4().hex[:24].upper()
    database[1].execute("INSERT INTO billing_rate_codes(code,created_by,note,created_at,expires_at,request_key,request_hash) VALUES(%s,'owner','Expired synthetic',now()-interval '2 days',now()-interval '1 day',%s,'synthetic')",(value,uuid4().hex))
    uid,_=user(database);assert claim(client,actor,uid,value).status_code==404
    h=actor(uid);assert client.post(BASE+'/claim',headers={**h,'X-Learning-User':'other'},json={'code':row['code'],'expected_amount_paise':10000}).status_code==409


def test_two_accounts_race_last_use_and_price_drift(client,actor,database):
    # Each worker has its own cookie jar; use the actual ASGI application.
    users=[user(database)[0] for _ in range(2)];h=actor('owner');row=code(client,h,max_uses=1)
    sessions=[]
    for uid in users:
        token='race-'+uuid4().hex;database[1].execute("INSERT INTO auth_sessions(token_hash,user_id,expires_at) VALUES(%s,%s,now()+interval '1 day')",(hashlib.sha256(token.encode()).hexdigest(),uid));sessions.append((uid,token))
    def submit(pair):
        uid,token=pair
        return client.post(BASE+'/claim',headers={'Cookie':'ism_session='+token,'Origin':settings.public_origin,'X-Review-CSRF':hashlib.sha256(('bank-review:'+token).encode()).hexdigest(),'X-Learning-User':uid},json={'code':row['code'],'expected_amount_paise':10000}).status_code
    with ThreadPoolExecutor(max_workers=2) as pool:assert sorted(pool.map(submit,sessions))==[200,404]
    assert database[1].execute('SELECT uses FROM billing_rate_codes WHERE code=%s',(row['code'],)).fetchone()[0]==1


def test_pause_history_and_mobile_boundary(client,actor,database,monkeypatch,tmp_path):
    from test_mobile_companion import connect
    uid,_=user(database);row=code(client,actor('owner'));headers,_=connect(client,actor,uid)
    assert client.get(BASE+'/me',headers=headers).status_code==403
    assert client.post(BASE+'/claim',headers=headers,json={'code':row['code'],'expected_amount_paise':10000}).status_code==403
    flag=tmp_path/'paused.json';flag.write_text('{"version":1,"writes_enabled":false}')
    monkeypatch.setattr(bulk_rate_release,'STATE_PATH',flag)
    assert claim(client,actor,uid,row['code']).status_code==503
    assert client.get(BASE+'/admin',headers=actor('owner')).status_code==200
    conn=database[1]
    with pytest.raises(Exception):conn.execute('UPDATE billing_rate_codes SET uses=uses+1,version=version+1 WHERE code=%s',(row['code'],))
    with pytest.raises(Exception):conn.execute('DELETE FROM billing_rate_codes WHERE code=%s',(row['code'],))


def test_unclaimed_revocation_price_drift_and_receipt_history(client,actor,database):
    uid,email=user(database);h=actor('owner');row=code(client,h)
    assert claim(client,actor,uid,row['code'],5000).status_code==409
    h=actor('owner')
    assert client.post(BASE+'/admin/codes/'+row['code']+'/revoke',headers=h,json={'expected_version':1}).status_code==200
    assert claim(client,actor,uid,row['code']).status_code==404
    h=actor('owner');assert batch(client,h,[email]).json()['applied']==1
    entry=next(e for e in client.get(BASE+'/admin').json()['emails'] if e['email_normalized']==email)
    assert client.post(BASE+'/admin/email-state',headers=h,json={'email':email,'expected_version':entry['version'],'revoked':True}).status_code==200
    assert database[1].execute('SELECT amount_paise FROM billing_account_rates WHERE user_id=%s',(uid,)).fetchone()[0]==5000
    with pytest.raises(Exception):database[1].execute('DELETE FROM billing_rate_batches')
    with pytest.raises(Exception):database[1].execute('UPDATE billing_rate_allowlist SET applied_user_id=NULL,applied_at=NULL,version=version+1 WHERE email_normalized=%s',(email,))


def test_optional_failure_never_blocks_sign_in_and_verified_login_applies(client,actor,database,monkeypatch):
    from app.services import bulk_rates
    uid,email=user(database);h=actor('owner');future='verified-login-'+uuid4().hex+'@example.test'
    assert batch(client,h,[future]).status_code==200
    database[1].execute('UPDATE users SET email=%s WHERE id=%s',(future,uid))
    client.cookies.clear();r=client.post('/api/auth/login',headers={'Origin':settings.public_origin},json={'email':future,'password':'SyntheticPassword123!'})
    assert r.status_code==200 and database[1].execute('SELECT amount_paise FROM billing_account_rates WHERE user_id=%s',(uid,)).fetchone()[0]==5000
    async def failed(*args):raise RuntimeError('Synthetic optional failure')
    monkeypatch.setattr(bulk_rates,'apply_email',failed)
    client.cookies.clear();assert client.post('/api/auth/login',headers={'Origin':settings.public_origin},json={'email':future,'password':'SyntheticPassword123!'}).status_code==200


def test_owner_search_finds_older_retained_entries(client,actor,database):
    uid,email=user(database);h=actor('owner');assert batch(client,h,[email]).status_code==200
    row=code(client,h,note='Unique searchable group '+uid)
    result=client.get(BASE+'/admin',headers=h,params={'q':email}).json()
    assert [e['email_normalized'] for e in result['emails']]==[email] and result['codes']==[]
    result=client.get(BASE+'/admin',headers=h,params={'q':row['code'].lower()}).json()
    assert [c['code'] for c in result['codes']]==[row['code']]
