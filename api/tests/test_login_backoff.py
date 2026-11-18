from uuid import uuid4
from app.services import login_backoff
from app.routers.auth import _hash_password
from app.services.account_identity import digest
from test_learning_loop import run
from test_learning_workflows import learner

ORIGIN={'Origin':'https://study.hawayu.in'}


def test_failed_login_persists_account_backoff_success_clears_only_account(client,database):
    conn=database[1];email='backoff-'+uuid4().hex+'@example.test';password='SyntheticPassword123!'
    user='backoff-'+uuid4().hex
    conn.execute('INSERT INTO users(id,handle,email,password_hash) VALUES(%s,%s,%s,%s)',(user,user,email,_hash_password(password)))
    client.cookies.clear()
    for _ in range(5):
        r=client.post('/api/auth/login',headers=ORIGIN,json={'email':email,'password':'wrong'})
        assert r.status_code==401,r.text
    r=client.post('/api/auth/login',headers=ORIGIN,json={'email':email,'password':password})
    assert r.status_code==429 and int(r.headers['retry-after'])>=1
    key=login_backoff.bucket('account',email)
    assert conn.execute('SELECT failures FROM auth_login_backoff WHERE bucket=%s',(key,)).fetchone()[0]==5
    conn.execute('UPDATE auth_login_backoff SET blocked_until=now()-interval \'1 second\'')
    r=client.post('/api/auth/login',headers=ORIGIN,json={'email':email,'password':password})
    assert r.status_code==200,r.text
    assert conn.execute('SELECT count(*) FROM auth_login_backoff WHERE bucket=%s',(key,)).fetchone()[0]==0
    assert conn.execute("SELECT count(*) FROM auth_login_backoff WHERE bucket LIKE 'ip:%%'").fetchone()[0]>=1


def test_account_and_ip_backoff_are_independent_and_recovery_unlocks(client,actor,database):
    conn=database[1];user,h=learner(database,actor);email=conn.execute('SELECT email FROM users WHERE id=%s',(user,)).fetchone()[0]
    for i in range(20):client.portal.call(login_backoff.failed,'unknown-'+str(i)+'@example.test','synthetic-ip')
    ipkey=login_backoff.bucket('ip','synthetic-ip')
    assert conn.execute('SELECT blocked_until>now() FROM auth_login_backoff WHERE bucket=%s',(ipkey,)).fetchone()[0]
    for i in range(5):client.portal.call(login_backoff.failed,email,'other-ip-'+str(i))
    key=login_backoff.bucket('account',email)
    assert conn.execute('SELECT blocked_until>now() FROM auth_login_backoff WHERE bucket=%s',(key,)).fetchone()[0]
    raw='synthetic-reset-'+uuid4().hex
    conn.execute("INSERT INTO account_email_tokens(token_hash,user_id,purpose,expires_at) VALUES(%s,%s,'reset',now()+interval '1 hour')",(digest(raw),user))
    client.cookies.clear()
    r=client.post('/api/auth/recovery/complete',headers=ORIGIN,json={'token':raw,'password':'NewSyntheticPassword123!'})
    assert r.status_code==200,r.text
    assert conn.execute('SELECT count(*) FROM auth_login_backoff WHERE bucket=%s',(key,)).fetchone()[0]==0
    assert conn.execute('SELECT count(*) FROM auth_login_backoff WHERE bucket=%s',(ipkey,)).fetchone()[0]==1
    assert client.post('/api/auth/recovery/complete',headers=ORIGIN,json={'token':raw,'password':'AnotherPassword123!'}).status_code==400
