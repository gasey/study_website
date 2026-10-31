import base64,hashlib,time
from uuid import uuid4
import pytest
from cryptography.fernet import Fernet
from fastapi import HTTPException
from app.config import settings
from app.services import mfa
from app.routers.auth import _hash_password

@pytest.fixture
def account(client,database,monkeypatch):
    monkeypatch.setattr(settings,'mfa_encryption_key',Fernet.generate_key().decode())
    suffix=uuid4().hex[:10];user='mfa_'+suffix;email=user+'@example.test';password='SyntheticPassword123!';token='mfa-session-'+suffix
    conn=database[1]
    conn.execute("INSERT INTO users(id,handle,email,password_hash) VALUES (%s,%s,%s,%s)",(user,user,email,_hash_password(password)))
    conn.execute("INSERT INTO auth_sessions(token_hash,user_id,expires_at) VALUES (%s,%s,now()+interval '1 day')",(hashlib.sha256(token.encode()).hexdigest(),user))
    client.cookies.clear();client.cookies.set('ism_session',token)
    h={'Origin':settings.public_origin,'X-Review-CSRF':hashlib.sha256(('bank-review:'+token).encode()).hexdigest()}
    return user,email,password,h

def enroll(client,account):
    user,email,password,h=account
    response=client.post('/api/auth/mfa/setup',headers=h,json={'password':password});assert response.status_code==200,response.text
    setup=response.json();seed=setup['setup_key']
    assert response.headers['cache-control']=='no-store' and setup['qr_data_url'].startswith('data:image/svg+xml;base64,')
    response=client.post('/api/auth/mfa/confirm',headers=h,json={'code':mfa.totp(seed,int(time.time())//30)});assert response.status_code==200,response.text
    return seed,response.json()['recovery_codes']


def test_rfc_vector_cipher_binding_and_code_validation(monkeypatch):
    seed=base64.b32encode(b'12345678901234567890').decode().rstrip('=')
    assert mfa.totp(seed,59//30,8)=='94287082'
    assert mfa.matching_counter(seed,mfa.totp(seed,2),now=59)==2
    assert mfa.matching_counter(seed,'abcdef',now=59) is None
    monkeypatch.setattr(settings,'mfa_encryption_key',Fernet.generate_key().decode())
    encrypted=mfa.encrypt('test-user',seed);assert seed not in encrypted
    assert mfa.decrypt('test-user',encrypted)==seed
    with pytest.raises(HTTPException):mfa.decrypt('another-user',encrypted)


def test_enroll_login_requires_factor_and_recovery_is_one_use(client,account,database):
    user,email,password,h=account;seed,codes=enroll(client,account);conn=database[1]
    assert len(codes)==10 and len(set(codes))==10
    assert conn.execute('SELECT secret_cipher FROM account_mfa WHERE user_id=%s',(user,)).fetchone()[0]!=seed
    stored=conn.execute('SELECT code_hash FROM mfa_recovery_codes WHERE user_id=%s',(user,)).fetchall()
    assert all(code not in [v[0] for v in stored] for code in codes)
    # Enrollment consumes its own TOTP; replay cannot verify again.
    assert client.post('/api/auth/mfa/verify',headers=h,json={'code':mfa.totp(seed,int(time.time())//30)}).status_code==401
    client.cookies.clear()
    response=client.post('/api/auth/login',headers={'Origin':settings.public_origin},json={'email':email,'password':password})
    assert response.status_code==401 and not client.cookies.get('ism_session')
    response=client.post('/api/auth/login',headers={'Origin':settings.public_origin},json={'email':email,'password':password,'code':codes[0]});assert response.status_code==200,response.text
    assert client.get('/api/auth/mfa/status').json()['verified'] is True
    assert client.get('/api/auth/mfa/status').json()['recovery_codes_remaining']==9
    client.cookies.clear()
    assert client.post('/api/auth/login',headers={'Origin':settings.public_origin},json={'email':email,'password':password,'code':codes[0]}).status_code==401


def test_staff_mutation_requires_enrollment_then_verified_session(client,account,database,monkeypatch):
    user,email,password,h=account;conn=database[1]
    conn.execute("INSERT INTO review_grants(user_id,role,granted_by,reason) VALUES (%s,'owner','test','Synthetic MFA role check')",(user,))
    monkeypatch.setattr(settings,'mfa_enforce_staff',True)
    assert client.get('/api/review/session').json()['mfa_required'] is True
    assert client.post('/api/admin/bank/assessments/retry',headers=h,json={'reason':'Synthetic staff test before enrollment.'}).status_code==403
    seed,codes=enroll(client,account)
    assert client.post('/api/admin/bank/assessments/retry',headers=h,json={'reason':'Synthetic staff test after enrollment.'}).status_code==200
    conn.execute("UPDATE auth_sessions SET mfa_verified_at=now()-interval '16 minutes' WHERE user_id=%s",(user,))
    assert client.post('/api/admin/bank/assessments/retry',headers=h,json={'reason':'Synthetic stale MFA session test.'}).status_code==403
    assert client.post('/api/auth/mfa/verify',headers=h,json={'code':codes[1]}).status_code==200
    assert client.post('/api/admin/bank/assessments/retry',headers=h,json={'reason':'Synthetic refreshed MFA session test.'}).status_code==200
    assert client.post('/api/auth/mfa/disable',headers=h,json={'password':password,'code':codes[2]}).status_code==409


def test_setup_password_csrf_and_replacement_guards(client,account,database):
    user,email,password,h=account
    assert client.post('/api/auth/mfa/setup',json={'password':password}).status_code==403
    assert client.post('/api/auth/mfa/setup',headers=h,json={'password':'WrongPassword123!'}).status_code==401
    seed,codes=enroll(client,account)
    database[1].execute("UPDATE auth_sessions SET mfa_verified_at=now()-interval '16 minutes' WHERE user_id=%s",(user,))
    assert client.post('/api/auth/mfa/setup',headers=h,json={'password':password}).status_code==403
    assert client.post('/api/auth/mfa/verify',headers=h,json={'code':codes[0]}).status_code==200
    response=client.post('/api/auth/mfa/setup',headers=h,json={'password':password});assert response.status_code==200,response.text
    assert database[1].execute('SELECT enabled_at IS NOT NULL FROM account_mfa WHERE user_id=%s',(user,)).fetchone()[0] is True


def test_second_factor_replay_under_concurrency(client,account):
    from concurrent.futures import ThreadPoolExecutor
    user,email,password,h=account;seed,codes=enroll(client,account)
    def verify(_):return client.post('/api/auth/mfa/verify',headers=h,json={'code':codes[0]})
    with ThreadPoolExecutor(max_workers=2) as pool:responses=list(pool.map(verify,range(2)))
    assert sorted(r.status_code for r in responses)==[200,401]


def test_expired_setup_unconfigured_and_rate_limit(client,account,database,monkeypatch):
    user,email,password,h=account
    assert client.post('/api/auth/mfa/setup',headers=h,json={'password':password}).status_code==200
    database[1].execute("UPDATE account_mfa SET pending_until=now()-interval '1 second' WHERE user_id=%s",(user,))
    assert client.post('/api/auth/mfa/confirm',headers=h,json={'code':'123456'}).status_code==409
    monkeypatch.setattr(settings,'mfa_encryption_key','')
    assert client.post('/api/auth/mfa/setup',headers=h,json={'password':password}).status_code==503
    assert client.get('/api/auth/mfa/status').json()['configured'] is False
    for _ in range(8):
        assert client.post('/api/auth/mfa/verify',headers=h,json={'code':'123456'}).status_code==401
    response=client.post('/api/auth/mfa/verify',headers=h,json={'code':'123456'})
    assert response.status_code==429 and response.headers['retry-after']=='300'
    assert database[1].execute('SELECT count FROM review_rate_buckets WHERE bucket=%s',('mfa:'+user,)).fetchone()[0]==11


def test_rotate_disable_and_revoked_session(client,account,database):
    user,email,password,h=account;seed,codes=enroll(client,account)
    response=client.post('/api/auth/mfa/recovery-codes',headers=h,json={'password':password,'code':codes[0]})
    assert response.status_code==200,response.text
    fresh=response.json()['recovery_codes'];assert len(fresh)==10
    assert client.post('/api/auth/mfa/verify',headers=h,json={'code':codes[1]}).status_code==401
    response=client.post('/api/auth/mfa/disable',headers=h,json={'password':password,'code':fresh[0]})
    assert response.status_code==200,response.text
    assert client.get('/api/auth/mfa/status').json()['enabled'] is False
    assert client.get('/api/auth/mfa/status').json()['recovery_codes_remaining']==0
    database[1].execute('UPDATE auth_sessions SET revoked_at=now() WHERE user_id=%s',(user,))
    assert client.post('/api/auth/mfa/setup',headers=h,json={'password':password}).status_code==401
