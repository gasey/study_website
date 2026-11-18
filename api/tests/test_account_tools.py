"""Disposable real-role account self-service: ownership, portability and tombstones."""
from contextlib import asynccontextmanager
from datetime import timedelta
from uuid import uuid4
import hashlib,json
from concurrent.futures import ThreadPoolExecutor
import psycopg
import pytest
from app.db import cursor
from app.routers import account_tools,auth
from app.services import account_tools as tools
from test_learning_workflows import learner
from test_learning_loop import questions,attempt,run
from test_owned_calendar import save

@pytest.fixture(autouse=True)
def mpsc(monkeypatch):
    @asynccontextmanager
    async def app_cursor():
        async with cursor() as cur:
            await cur.execute('SET LOCAL ROLE mpsc')
            yield cur
    monkeypatch.setattr(account_tools,'cursor',app_cursor)


def close(client,h,user,**patch):
    return client.post('/api/me/account-close',headers=h,json={'user_id':user,'expected_version':0,'confirmation':'DELETE MY ACCOUNT',**patch})


def test_private_tools_guest_native_and_account_binding(client,actor,database):
    client.cookies.clear();assert client.get('/api/me/account-tools').status_code==401
    user,h=learner(database,actor)
    r=client.get('/api/me/account-tools',headers=h)
    assert r.status_code==200,r.text
    assert r.headers['cache-control']=='private, no-store' and 'etag' not in r.headers
    assert r.json()['user_id']==user and r.json()['closure_blockers']==[] and r.json()['recent']
    assert client.get('/api/me/data-export?user_id=owner',headers=h).status_code==409
    assert close(client,{},user).status_code==403
    assert close(client,h,'owner').status_code==409
    assert close(client,h,user,confirmation='delete').status_code==422
    from test_mobile_companion import connect
    mobile,_=connect(client,actor,user)
    for path in ('account-tools','data-export?user_id='+user):
        assert client.get('/api/me/'+path,headers=mobile).status_code==403
    for path in ('account-close','account-signout-all'):
        assert client.post('/api/me/'+path,headers=mobile,json={}).status_code==403


def test_export_snapshot_all_batches_owned_fields_and_assessment_guards(client,actor,database):
    conn=database[1];user,h=learner(database,actor);_,ids=questions(database,2)
    attempt(conn,user,ids[0],True);attempt(conn,user,ids[1],False)
    # The immutable scoring snapshot already contains the correct answer; export must omit it.
    for _ in range(205):conn.execute("INSERT INTO posts(canonical_id,kind,author_id,body) VALUES(%s,'doubt',%s,'Owned export note')",(ids[0],user))
    conn.execute("INSERT INTO posts(canonical_id,kind,author_id,body) VALUES(%s,'doubt','outsider','OTHER_ACCOUNT_SECRET')",(ids[0],))
    conn.execute("INSERT INTO personal_desks(user_id,document) VALUES(%s,%s)",(user,psycopg.types.json.Jsonb({'notes':[{'body':'My private note'}]})))
    assert save(client,h,date='2026-11-19',title='My private calendar').status_code==200
    before=conn.execute('SELECT count(*) FROM reward_ledger').fetchone()[0]
    result=client.get('/api/me/data-export',params={'user_id':user},headers=h)
    assert result.status_code==200,result.text
    body=result.json()
    assert len(body['attempts'])==2 and len(body['posts'])==205 and len({r['id'] for r in body['posts']})==205
    assert body['private_desk'][0]['document']['notes'][0]['body']=='My private note'
    assert body['calendar'][0]['title']=='My private calendar'
    for forbidden in ('OTHER_ACCOUNT_SECRET','NEVER_EXPORT_KEY','password_hash','secret_cipher','token_hash','request_hash','scoring_snapshot'):
        assert forbidden not in result.text
    assert result.headers['content-disposition']=='attachment; filename="finna-data.json"'
    assert result.headers['cache-control']=='private, no-store' and result.headers['x-content-type-options']=='nosniff'
    # A held mock question must not become an export-based reveal route.
    from test_learning_loop import due
    due(conn,user,ids)
    conn.execute("INSERT INTO mock_sessions(id,user_id,collection_id,question_ids,duration_seconds) VALUES(%s,%s,'udc',%s,60)",(uuid4().hex,user,ids))
    guarded=client.get('/api/me/data-export',params={'user_id':user},headers=h)
    assert guarded.status_code==200,guarded.text
    assert guarded.json()['attempts']==[] and guarded.json()['posts']==[] and guarded.json()['review_schedule']==[]
    assert conn.execute('SELECT count(*) FROM reward_ledger').fetchone()[0]==before


def test_closure_revokes_credentials_feeds_entitlements_and_keeps_history(client,actor,database):
    from test_mobile_companion import connect
    conn=database[1];user,h=learner(database,actor);_,ids=questions(database,1)
    aid=attempt(conn,user,ids[0],True)
    conn.execute("INSERT INTO posts(canonical_id,kind,author_id,body) VALUES(%s,'doubt',%s,'Retained immutable discussion')",(ids[0],user))
    assert save(client,h,title='Private plan to remove').status_code==200
    feed=client.post('/api/me/calendar/feed/rotate',headers=h,json={'expected_version':0}).json()['url']
    conn.execute("INSERT INTO personal_desks(user_id,document) VALUES(%s,'{}')",(user,))
    conn.execute("INSERT INTO creator_profiles(user_id,public,bio) VALUES(%s,true,'Remove this bio')",(user,))
    conn.execute("INSERT INTO reward_profiles(user_id,board_public) VALUES(%s,true) ON CONFLICT(user_id) DO UPDATE SET board_public=true",(user,))
    conn.execute("UPDATE users SET plan_code='pro',plan_status='active' WHERE id=%s",(user,))
    conn.execute("INSERT INTO google_identities(subject,user_id) VALUES(%s,%s)",('google-'+user,user))
    conn.execute("INSERT INTO account_email_tokens(token_hash,user_id,purpose,expires_at) VALUES(%s,%s,'reset',now()+interval '1 hour')",('t'*64,user))
    conn.execute("INSERT INTO account_mail_outbox(user_id,purpose,token_cipher) VALUES(%s,'reset','Sensitive pending token')",(user,))
    mobile,_=connect(client,actor,user)
    h=actor(user);before=conn.execute('SELECT count(*) FROM reward_ledger').fetchone()[0]
    assert conn.execute('SELECT account_has_pro(%s)',(user,)).fetchone()[0]
    r=close(client,h,user);assert r.status_code==200,r.text
    assert r.json()=={'closed':True} and 'Max-Age=0' in r.headers['set-cookie']
    row=conn.execute('SELECT closed_at,email,name,avatar,password_hash,handle,contribution_public FROM users WHERE id=%s',(user,)).fetchone()
    assert row[0] and row[1:5]==(None,None,None,None) and row[5].startswith('deleted-') and not row[6]
    assert not conn.execute('SELECT account_has_pro(%s)',(user,)).fetchone()[0]
    assert conn.execute('SELECT id FROM attempts WHERE id=%s',(aid,)).fetchone()
    assert conn.execute('SELECT body FROM posts WHERE author_id=%s',(user,)).fetchone()[0]=='Retained immutable discussion'
    assert conn.execute('SELECT count(*) FROM reward_ledger').fetchone()[0]==before
    assert conn.execute('SELECT count(*) FROM calendar_entries WHERE user_id=%s',(user,)).fetchone()[0]==0
    assert conn.execute('SELECT count(*) FROM personal_desks WHERE user_id=%s',(user,)).fetchone()[0]==0
    assert conn.execute('SELECT count(*) FROM google_identities WHERE user_id=%s',(user,)).fetchone()[0]==0
    assert conn.execute('SELECT count(*) FROM account_mail_outbox WHERE user_id=%s',(user,)).fetchone()[0]==0
    assert conn.execute('SELECT public,bio FROM creator_profiles WHERE user_id=%s',(user,)).fetchone()==(False,'')
    assert client.get(feed).status_code==404
    client.cookies.clear()
    assert client.get('/api/me/profile',headers=mobile).status_code==401
    assert client.get('/api/me/identity',headers={'Cookie':'ism_session=test-session-'+user}).status_code==401
    assert conn.execute("SELECT count(*) FROM account_security_events WHERE user_id=%s AND action='account_closed'",(user,)).fetchone()[0]==1


def test_closure_recent_mfa_version_staff_desk_and_billing_blockers(client,actor,database):
    user,h=learner(database,actor);conn=database[1]
    conn.execute("UPDATE auth_sessions SET created_at=now()-interval '16 minutes' WHERE user_id=%s",(user,))
    assert close(client,h,user).status_code==403
    conn.execute('UPDATE auth_sessions SET created_at=now() WHERE user_id=%s',(user,))
    assert close(client,h,user,expected_version=1).status_code==409
    conn.execute('INSERT INTO account_mfa(user_id,enabled_at) VALUES(%s,now())',(user,))
    assert close(client,h,user).status_code==403
    conn.execute('UPDATE auth_sessions SET mfa_verified_at=now() WHERE user_id=%s',(user,))
    conn.execute("INSERT INTO study_desks(id,owner_id,name) VALUES(%s,%s,'Owned desk')",(user,user))
    assert close(client,h,user).status_code==409
    conn.execute('UPDATE study_desks SET closed_at=now() WHERE id=%s',(user,))
    conn.execute("UPDATE users SET razorpay_subscription_id='Unconfirmed billing' WHERE id=%s",(user,))
    assert close(client,h,user).status_code==409
    conn.execute('UPDATE users SET razorpay_subscription_id=NULL WHERE id=%s',(user,))
    conn.execute("UPDATE users SET role='staff' WHERE id=%s",(user,))
    assert close(client,h,user).status_code==409
    conn.execute("UPDATE users SET role='learner' WHERE id=%s",(user,))
    assert close(client,h,user).status_code==200


def test_closed_identity_and_credentials_cannot_resurrect_even_after_provider_updates(client,actor,database):
    user,h=learner(database,actor);conn=database[1]
    assert close(client,h,user).status_code==200
    for query,params in [
      ('UPDATE users SET email=%s WHERE id=%s',('resurrect@example.test',user)),
      ('INSERT INTO auth_sessions(token_hash,user_id,expires_at) VALUES(%s,%s,now()+interval \'1 day\')',(uuid4().hex,user)),
      ('INSERT INTO google_identities(subject,user_id) VALUES(%s,%s)',(uuid4().hex,user)),
      ('INSERT INTO account_mfa(user_id,enabled_at) VALUES(%s,now())',(user,))]:
        with pytest.raises(psycopg.Error):
            with conn.transaction():conn.execute(query,params)
    conn.execute("UPDATE users SET plan_code='pro',plan_status='active',plan_ends_at=now()+interval '30 days' WHERE id=%s",(user,))
    assert not conn.execute('SELECT account_has_pro(%s)',(user,)).fetchone()[0]


def test_sign_out_everywhere_revokes_web_and_mobile_without_closing(client,actor,database):
    from test_mobile_companion import connect
    user,h=learner(database,actor);conn=database[1]
    mobile,_=connect(client,actor,user);h=actor(user)
    assert client.post('/api/me/account-signout-all',headers=h,json={'user_id':'owner'}).status_code==409
    r=client.post('/api/me/account-signout-all',headers=h,json={'user_id':user})
    assert r.status_code==200,r.text
    client.cookies.clear()
    assert client.get('/api/me/profile',headers=mobile).status_code==401
    assert not conn.execute('SELECT closed_at IS NOT NULL FROM users WHERE id=%s',(user,)).fetchone()[0]
    assert conn.execute('SELECT count(*) FROM auth_sessions WHERE user_id=%s AND revoked_at IS NULL',(user,)).fetchone()[0]==0


def test_concurrent_close_has_one_receipt_and_new_sessions_are_denied(client,actor,database):
    from fastapi import Response,HTTPException
    user,h=learner(database,actor)
    headers=h|{'Cookie':'ism_session=test-session-'+user}
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(lambda _:close(client,headers,user),range(2)))
    assert sorted(r.status_code for r in results)[0]==200
    assert sum(r.status_code==200 for r in results)==1
    assert all(r.status_code in (200,401,409) for r in results)
    assert database[1].execute("SELECT count(*) FROM account_security_events WHERE user_id=%s AND action='account_closed'",(user,)).fetchone()[0]==1
    async def mint(cur):
        await auth._new_session(user,Response(),cur=cur)
    with pytest.raises(HTTPException) as rejected:run(client,mint)
    assert rejected.value.status_code==401


def test_credential_creation_waits_for_closure_and_cannot_restore_a_tombstone(client,actor,database):
    from threading import Event
    user,h=learner(database,actor);conn=database[1];started=Event()
    def issue():
        with psycopg.connect('dbname='+database[0]) as contender:
            contender.execute('SET LOCAL ROLE mpsc')
            started.set()
            # An existing credential update takes the same owner lock as creation.
            contender.execute('UPDATE auth_sessions SET expires_at=now()+interval \'30 days\' WHERE user_id=%s',(user,))
    with conn.transaction():
        conn.execute('SELECT id FROM users WHERE id=%s FOR UPDATE',(user,))
        with ThreadPoolExecutor(max_workers=1) as pool:
            future=pool.submit(issue);assert started.wait(5)
            conn.execute("UPDATE users SET closed_at=now(),email=NULL,password_hash=NULL,name=NULL,avatar=NULL,email_verified_at=NULL,contribution_public=false WHERE id=%s",(user,))
            # Release the owner lock so the waiting credential check sees closure.
            conn.execute('COMMIT')
            with pytest.raises(psycopg.Error,match='Account is closed'):future.result(timeout=10)
