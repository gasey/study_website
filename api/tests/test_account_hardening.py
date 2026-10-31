"""Account boundaries and guest ownership against an isolated PostgreSQL DB."""
import hashlib
from uuid import uuid4
from app.config import settings
from app.services.learning_rewards import level_bounds


def headers(client):
    token=client.cookies.get('ism_session')
    return {'Origin':settings.public_origin,**({'X-Review-CSRF':hashlib.sha256(('bank-review:'+token).encode()).hexdigest()} if token else {})}


def test_device_uuid_cannot_read_or_adopt_legacy_history(client,database,actor):
    conn=database[1];legacy='dev_'+str(uuid4())
    conn.execute('INSERT INTO users(id,handle) VALUES(%s,%s)',(legacy,legacy))
    conn.execute("INSERT INTO attempts(user_id,canonical_id,correct,context) VALUES(%s,'cq_test',false,'practice')",(legacy,))
    client.cookies.clear()
    r=client.get('/api/auth/guest-progress',headers={'X-Device-Id':legacy[4:]})
    assert r.status_code==200 and r.json()['attempts']==0
    proof=client.cookies.get('ism_guest');assert proof
    guest=conn.execute('SELECT user_id FROM guest_credentials WHERE token_hash=%s',(hashlib.sha256(proof.encode()).hexdigest(),)).fetchone()[0]
    assert guest!=legacy
    # Retain guest proof while authenticating as the synthetic owner.
    client.cookies.set('ism_session','test-session-owner')
    h=headers(client)
    assert client.post('/api/auth/guest-progress/save',headers=h,json={}).status_code==200
    assert conn.execute('SELECT user_id FROM attempts WHERE user_id=%s',(legacy,)).fetchone()[0]==legacy


def test_proven_guest_transfer_retry_no_xp_and_cannot_reclaim(client,database):
    conn=database[1];client.cookies.clear();client.get('/api/auth/guest-progress')
    proof=client.cookies.get('ism_guest');guest=conn.execute('SELECT user_id FROM guest_credentials WHERE token_hash=%s',(hashlib.sha256(proof.encode()).hexdigest(),)).fetchone()[0]
    conn.execute("INSERT INTO attempts(user_id,canonical_id,correct,context) VALUES(%s,'cq_test',false,'practice')",(guest,))
    client.cookies.set('ism_session','test-session-owner');h=headers(client)
    r=client.post('/api/auth/guest-progress/save',headers=h,json={});assert r.status_code==200,r.text
    assert r.json()['counts']['attempts']==1
    assert client.post('/api/auth/guest-progress/save',headers=h,json={}).json()==r.json()
    assert conn.execute('SELECT count(*) FROM reward_ledger WHERE event_key LIKE %s',('%'+guest+'%',)).fetchone()[0]==0
    client.cookies.set('ism_session','test-session-outsider')
    assert client.post('/api/auth/guest-progress/save',headers=headers(client),json={}).status_code==409


def test_expired_cookie_does_not_write_as_guest(client,database):
    client.cookies.clear();client.cookies.set('ism_session','expired-synthetic')
    r=client.post('/api/questions/cq_test/answer',headers=headers(client),json={'chosen_index':1})
    assert r.status_code==401,r.text


def test_cookie_mutations_require_origin_and_csrf(client,actor):
    actor('owner')
    assert client.post('/api/auth/sessions/revoke',json={}).status_code==403
    assert client.post('/api/auth/sessions/revoke',headers={**headers(client),'Origin':'https://other.example'},json={}).status_code==403
    assert client.post('/api/auth/sessions/revoke',headers=headers(client),json={'session_id':'nonexistent'}).status_code==200


def test_sessions_are_private_and_revocation_is_account_bound(client,actor,database):
    actor('owner');r=client.get('/api/auth/sessions');assert r.status_code==200
    assert 'no-store' in r.headers['cache-control']
    assert all('token_hash' not in x for x in r.json()['items'])
    other=database[1].execute("SELECT public_id FROM auth_sessions WHERE user_id='outsider' AND token_hash=%s",(hashlib.sha256(b'test-session-outsider').hexdigest(),)).fetchone()[0]
    assert client.post('/api/auth/sessions/revoke',headers=headers(client),json={'session_id':other}).json()['revoked']==0
    client.cookies.set('ism_session','test-session-outsider')
    assert client.get('/api/auth/session').json()['authenticated']


def test_board_total_survives_empty_page_and_private_placement(client,actor,database):
    conn=database[1];u='board_'+uuid4().hex
    conn.execute('INSERT INTO users(id,handle,email) VALUES(%s,%s,%s)',(u,u,u+'@example.test'))
    conn.execute('INSERT INTO reward_profiles(user_id,board_public) VALUES(%s,true)',(u,))
    conn.execute("INSERT INTO reward_ledger(user_id,event_key,kind,xp,note) VALUES(%s,%s,'adjustment',100,'Synthetic board')",(u,u))
    actor('owner');a=client.get('/api/rewards/leaderboard?period=month').json();b=client.get('/api/rewards/leaderboard?period=month&offset=10000').json()
    assert a['total']==b['total'] and a['total']>0 and b['items']==[]
    assert a['period_start'] and a['period_end'] and a['as_of']
    assert all(set(x)=={'handle','avatar','rank','xp'} for x in a['items'])


def test_level_boundaries():
    for xp,level in [(0,1),(39,1),(40,1),(159,1),(160,2),(359,2),(360,3)]:
        b=level_bounds(xp);assert b['level']==level
        assert b['level_floor_xp']<=xp<b['next_level_xp']


def test_simultaneous_awards_share_cap_and_metadata(client,database):
    import psycopg
    from concurrent.futures import ThreadPoolExecutor
    from psycopg.types.json import Jsonb
    conn=database[1];user='cap_'+uuid4().hex
    conn.execute('INSERT INTO users(id,handle,email) VALUES(%s,%s,%s)',(user,user,user+'@example.test'))
    conn.execute("INSERT INTO reward_ledger(user_id,event_key,kind,xp,note) VALUES(%s,%s,'study',290,'Synthetic cap baseline')",(user,user))
    ids=['capq_'+uuid4().hex for _ in range(10)]
    for q in ids:conn.execute("INSERT INTO canonical_questions(id,type,question,options,answer_text,answer_source) VALUES(%s,'mcq','Synthetic cap question','[\"A\",\"B\"]','B','official')",(q,))
    def write(q):
        with psycopg.connect('dbname='+database[0]) as c:
            c.execute('SET LOCAL ROLE mpsc')
            c.execute("INSERT INTO attempts(user_id,canonical_id,correct,chosen_text,context,scoring_snapshot) VALUES(%s,%s,true,'B','practice',%s)",(user,q,Jsonb({'answer_source':'official','answer_text':'B'})))
    with ThreadPoolExecutor(max_workers=10) as pool:list(pool.map(write,ids))
    assert conn.execute('SELECT sum(xp) FROM reward_ledger WHERE user_id=%s',(user,)).fetchone()[0]==300
    rows=conn.execute('SELECT source_attempt_id,rule_version FROM reward_ledger WHERE user_id=%s AND source_attempt_id IS NOT NULL',(user,)).fetchall()
    assert len(rows)==1 and rows[0][1]=='learning-v1'
    assert conn.execute('SELECT count(*) FROM reward_question_claims WHERE user_id=%s',(user,)).fetchone()[0]==1


def test_two_accounts_cannot_simultaneously_claim_guest(client,database):
    from concurrent.futures import ThreadPoolExecutor
    conn=database[1];client.cookies.clear();client.get('/api/auth/guest-progress');proof=client.cookies.get('ism_guest')
    guest=conn.execute('SELECT user_id FROM guest_credentials WHERE token_hash=%s',(hashlib.sha256(proof.encode()).hexdigest(),)).fetchone()[0]
    def claim(user):
        token='test-session-'+user
        h={'Origin':settings.public_origin,'X-Review-CSRF':hashlib.sha256(('bank-review:'+token).encode()).hexdigest(),'Cookie':'ism_session='+token+'; ism_guest='+proof}
        return client.post('/api/auth/guest-progress/save',headers=h,json={}).status_code
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(claim,['owner','outsider']))
    assert sorted(results)==[200,409]
    assert conn.execute('SELECT count(*) FROM guest_transfer_receipts WHERE guest_id=%s',(guest,)).fetchone()[0]==1


def test_recovery_disabled_and_tokens_single_use_purpose_bound(client,database,monkeypatch):
    from app.routers.auth import _hash_password,_check_password
    from app.routers.account_recovery import enqueue
    from cryptography.fernet import Fernet
    from app.services.account_identity import digest
    conn=database[1];client.cookies.clear();h={'Origin':settings.public_origin}
    monkeypatch.setattr(settings,'account_mail_enabled',False)
    assert client.get('/api/auth/recovery/status').json()=={'available':False}
    assert client.post('/api/auth/recovery/request',headers=h,json={'email':'unknown@example.test'}).status_code==503
    user='reset_'+uuid4().hex;raw='test-token-'+uuid4().hex;password='SyntheticResetPassword123!'
    conn.execute('INSERT INTO users(id,handle,email,password_hash) VALUES(%s,%s,%s,%s)',(user,user,user+'@example.test',_hash_password('OriginalPassword123!')))
    conn.execute("INSERT INTO auth_sessions(token_hash,user_id,expires_at) VALUES(%s,%s,now()+interval '1 day')",(digest(user),user))
    conn.execute("INSERT INTO account_email_tokens(token_hash,user_id,purpose,expires_at) VALUES(%s,%s,'reset',now()+interval '30 minutes')",(digest(raw),user))
    assert client.post('/api/auth/email/confirm',headers=h,json={'token':raw}).status_code==400
    r=client.post('/api/auth/recovery/complete',headers=h,json={'token':raw,'password':password});assert r.status_code==200,r.text
    assert _check_password(password,conn.execute('SELECT password_hash FROM users WHERE id=%s',(user,)).fetchone()[0])
    assert conn.execute('SELECT revoked_at IS NOT NULL FROM auth_sessions WHERE user_id=%s',(user,)).fetchone()[0]
    assert client.post('/api/auth/recovery/complete',headers=h,json={'token':raw,'password':password}).status_code==400
    # Expired tokens never modify an account.
    expired='expired-'+uuid4().hex
    conn.execute("INSERT INTO account_email_tokens(token_hash,user_id,purpose,expires_at) VALUES(%s,%s,'reset',now()-interval '1 minute')",(digest(expired),user))
    assert client.post('/api/auth/recovery/complete',headers=h,json={'token':expired,'password':password}).status_code==400


def test_reset_does_not_bypass_mfa(client,database,monkeypatch):
    from app.services import mfa
    from cryptography.fernet import Fernet
    from app.services.account_identity import digest
    monkeypatch.setattr(settings,'mfa_encryption_key',Fernet.generate_key().decode())
    conn=database[1];user='resetmfa_'+uuid4().hex;raw='reset-token-'+uuid4().hex
    conn.execute('INSERT INTO users(id,handle,email) VALUES(%s,%s,%s)',(user,user,user+'@example.test'))
    conn.execute('INSERT INTO account_mfa(user_id,secret_cipher,enabled_at) VALUES(%s,%s,now())',(user,mfa.encrypt(user,'JBSWY3DPEHPK3PXP')))
    conn.execute("INSERT INTO account_email_tokens(token_hash,user_id,purpose,expires_at) VALUES(%s,%s,'reset',now()+interval '30 minutes')",(digest(raw),user))
    client.cookies.clear();r=client.post('/api/auth/recovery/complete',headers={'Origin':settings.public_origin},json={'token':raw,'password':'AnotherNewPassword123!'})
    assert r.status_code==401
    assert conn.execute('SELECT consumed_at FROM account_email_tokens WHERE token_hash=%s',(digest(raw),)).fetchone()[0] is None


def test_outbox_request_generic_and_token_encrypted(client,database,monkeypatch):
    from cryptography.fernet import Fernet
    from app.services import mfa
    monkeypatch.setattr(settings,'mfa_encryption_key',Fernet.generate_key().decode())
    monkeypatch.setattr(settings,'account_mail_enabled',True)
    monkeypatch.setattr(settings,'smtp_host','localhost')
    monkeypatch.setattr(settings,'smtp_from','synthetic@example.test')
    user='mail_'+uuid4().hex;conn=database[1]
    conn.execute('INSERT INTO users(id,handle,email) VALUES(%s,%s,%s)',(user,user,user+'@example.test'))
    client.cookies.clear();h={'Origin':settings.public_origin}
    yes=client.post('/api/auth/recovery/request',headers=h,json={'email':user+'@example.test'})
    no=client.post('/api/auth/recovery/request',headers=h,json={'email':'absent-'+user+'@example.test'})
    assert yes.status_code==no.status_code==200 and yes.json()==no.json()
    row=conn.execute('SELECT token_cipher FROM account_mail_outbox WHERE user_id=%s',(user,)).fetchone()
    raw=mfa.decrypt(user,row[0]);assert raw not in row[0] and len(raw)>32


def test_answer_receipt_replay_conflict_and_unofficial_reason(client,actor,database):
    conn=database[1];h=actor('owner');key=uuid4().hex;q='receipt_'+uuid4().hex
    conn.execute("INSERT INTO canonical_questions(id,type,question,options,answer_text,answer_source) VALUES(%s,'mcq','Synthetic receipt','[\"A\",\"B\"]','B','official')",(q,))
    conn.execute("INSERT INTO appearances(id,paper_id,type,question,options,answer_index,answer_source,canonical_id,is_primary) VALUES(%s,'paper-test','mcq','Synthetic receipt','[\"A\",\"B\"]',1,'official',%s,true)",('a_'+q,q))
    r=client.post('/api/questions/'+q+'/answer',headers={**h,'Idempotency-Key':key},json={'chosen_index':1});assert r.status_code==200,r.text
    assert r.json()['reward']['status'] in ('awarded','daily_cap')
    assert client.post('/api/questions/'+q+'/answer',headers={**h,'Idempotency-Key':key},json={'chosen_index':1}).json()==r.json()
    assert conn.execute("SELECT count(*) FROM attempts WHERE user_id='owner' AND canonical_id=%s",(q,)).fetchone()[0]==1
    assert client.post('/api/questions/'+q+'/answer',headers={**h,'Idempotency-Key':key},json={'chosen_index':0}).status_code==409
    # A later key change cannot rewrite a frozen request receipt.
    conn.execute("UPDATE canonical_questions SET answer_text='A' WHERE id=%s",(q,))
    assert client.post('/api/questions/'+q+'/answer',headers={**h,'Idempotency-Key':key},json={'chosen_index':1}).json()==r.json()


def test_diagnostics_owner_only_and_read_only(client,actor,database):
    actor('outsider');assert client.get('/api/admin/bank/reward-diagnostics').status_code==403
    actor('owner');before=database[1].execute('SELECT count(*),sum(xp),sum(points) FROM reward_ledger').fetchone()
    r=client.get('/api/admin/bank/reward-diagnostics?email=owner@example.test');assert r.status_code==200,r.text
    assert 'claims_without_receipts' in r.json() and 'security_events' in r.json()['account']
    assert database[1].execute('SELECT count(*),sum(xp),sum(points) FROM reward_ledger').fetchone()==before


def test_expired_cookie_can_explicitly_logout_without_account_write(client):
    client.cookies.clear();client.cookies.set('ism_session','expired-browser-cookie')
    session=client.get('/api/auth/session');assert session.json()['state']=='expired'
    assert session.json()['csrf']
    r=client.post('/api/auth/logout',headers={'Origin':settings.public_origin,'X-Review-CSRF':session.json()['csrf']},json={})
    assert r.status_code==200 and not r.json()['authenticated']
    # TestClient's manually unscoped cookie can coexist with deleted host cookie;
    # inspect the actual response's expiry directives instead.
    assert any('ism_session=' in c and 'Max-Age=0' in c for c in r.headers.get_list('set-cookie'))


def test_board_ties_own_placement_opt_out_and_india_boundary(client,database):
    from datetime import datetime
    from zoneinfo import ZoneInfo
    conn=database[1];users=['tied_'+uuid4().hex for _ in range(2)]
    for u in users:
        conn.execute('INSERT INTO users(id,handle,email) VALUES(%s,%s,%s)',(u,u,u+'@example.test'))
        conn.execute('INSERT INTO reward_profiles(user_id,board_public) VALUES(%s,true)',(u,))
        conn.execute("INSERT INTO reward_ledger(user_id,event_key,kind,xp,note) VALUES(%s,%s,'adjustment',50000,'Synthetic tie')",(u,u))
    token='tie-session-'+uuid4().hex
    conn.execute("INSERT INTO auth_sessions(token_hash,user_id,expires_at) VALUES(%s,%s,now()+interval '1 day')",(hashlib.sha256(token.encode()).hexdigest(),users[0]))
    client.cookies.clear();client.cookies.set('ism_session',token)
    r=client.get('/api/rewards/leaderboard?limit=100').json()
    tied=[x for x in r['items']if x['handle']in users];assert len(tied)==2 and tied[0]['rank']==tied[1]['rank']
    assert r['placement']['rank']==tied[0]['rank'] and r['placement']['xp']==50000
    start=datetime.fromisoformat(r['period_start']).astimezone(ZoneInfo('Asia/Kolkata'))
    assert start.day==1 and start.hour==0 and start.minute==0
    assert client.post('/api/rewards/visibility',headers=headers(client),json={'public':False}).status_code==200
    out=client.get('/api/rewards/leaderboard?limit=100').json()
    assert out['placement']is None and users[0]not in [x['handle']for x in out['items']]


def test_password_change_rotates_cookie_and_keeps_new_session_usable(client,database):
    from app.routers.auth import _hash_password
    from app.services.account_identity import digest
    conn=database[1];user='password_'+uuid4().hex;token='password-session-'+uuid4().hex
    conn.execute('INSERT INTO users(id,handle,email,password_hash) VALUES(%s,%s,%s,%s)',(user,user,user+'@example.test',_hash_password('OriginalPassword123!')))
    conn.execute("INSERT INTO auth_sessions(token_hash,user_id,expires_at) VALUES(%s,%s,now()+interval '1 day')",(digest(token),user))
    client.cookies.clear();client.cookies.set('ism_session',token,domain='study.hawayu.in',path='/')
    r=client.post('/api/auth/password',headers=headers(client),json={'current_password':'OriginalPassword123!','new_password':'ChangedPassword123!'})
    assert r.status_code==200,r.text
    assert client.cookies.get('ism_session')!=token
    assert client.get('/api/auth/session').json()['authenticated']
    assert client.post('/api/auth/sessions/revoke',headers=headers(client),json={'session_id':'nonexistent'}).status_code==200
    client.cookies.clear();client.cookies.set('ism_session',token)
    assert not client.get('/api/auth/session').json()['authenticated']
