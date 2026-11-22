"""Real-role bounded retention and preservation of every kind of linked guest."""
import asyncio,hashlib
from uuid import uuid4
import pytest
from app.db import cursor
from app.services import account_retention,worker_health


def run(client,fn,*args):
    async def invoke():
        async with cursor() as cur:
            await cur.execute('SET LOCAL ROLE mpsc')
            return await fn(cur,*args)
    return client.portal.call(invoke)


@pytest.fixture(autouse=True)
def startup(client):
    async def ready():
        async with asyncio.timeout(3):
            while True:
                async with cursor() as cur:
                    await cur.execute("SELECT 1 FROM worker_heartbeats WHERE worker='account-retention'")
                    if await cur.fetchone():return
                await asyncio.sleep(.01)
    client.portal.call(ready)


def guest(conn,*,expires='19 months',adopted=False):
    uid='guest_'+uuid4().hex
    conn.execute("INSERT INTO users(id,handle,created_at) VALUES(%s,%s,now()-interval '25 months')",(uid,'guest-'+uid[6:22]))
    conn.execute("INSERT INTO guest_credentials(user_id,token_hash,created_at,expires_at,adopted_by,adopted_at) VALUES(%s,%s,now()-interval '25 months',now()-%s::interval,%s,CASE WHEN %s THEN now() ELSE NULL END)",(uid,hashlib.sha256(uid.encode()).hexdigest(),expires,'author' if adopted else None,adopted))
    return uid


def test_expired_sessions_retain_real_activity_and_keep_current_credentials(client,database):
    conn=database[1];uid='retention-'+uuid4().hex
    conn.execute('INSERT INTO users(id,handle,email) VALUES(%s,%s,%s)',(uid,uid,uid+'@example.test'))
    for key,created,expires,revoked in [('old','40 days','-9 days',None),('revoked','60 days','9 days','8 days'),('recent','3 days','-2 days',None),('live','2 days','9 days',None)]:
        conn.execute("INSERT INTO auth_sessions(token_hash,user_id,created_at,expires_at,revoked_at) VALUES(%s,%s,now()-%s::interval,now()+%s::interval,CASE WHEN %s::text IS NULL THEN NULL ELSE now()-%s::interval END)",(uid+key,uid,created,expires,revoked,revoked))
    conn.execute("INSERT INTO mobile_sessions(token_hash,public_id,user_id,parent_session_hash,created_at,expires_at) VALUES(%s,%s,%s,%s,now()-interval '20 days',now()+interval '1 day')",(uid+'mobile',uid+'mobile',uid,uid+'old'))
    expected=conn.execute('SELECT created_at FROM mobile_sessions WHERE user_id=%s',(uid,)).fetchone()[0]
    result=run(client,account_retention.sweep);assert result['web']==2 and result['mobile']==1
    assert conn.execute('SELECT count(*) FROM auth_sessions WHERE user_id=%s',(uid,)).fetchone()[0]==2
    retained=conn.execute("SELECT created_at,detail FROM account_security_events WHERE user_id=%s AND action='session_activity_retained' ORDER BY created_at DESC",(uid,)).fetchall()
    assert retained[0][0]==expected and retained[0][1]=={'source':'mobile_sessions'}
    assert 'token' not in str(retained)
    before=len(retained);assert run(client,account_retention.sweep)['web']==0
    assert conn.execute("SELECT count(*) FROM account_security_events WHERE user_id=%s AND action='session_activity_retained'",(uid,)).fetchone()[0]==before


def test_old_daily_request_keys_expire_but_current_budget_and_durable_receipts_survive(client,database):
    conn=database[1]
    conn.execute("INSERT INTO rate_limits(user_id,action,ist_date,request_keys,updated_at) VALUES('author','old',(now() AT TIME ZONE 'Asia/Kolkata')::date-31,ARRAY['old-key'],now()-interval '31 days'),('author','recent-change',(now() AT TIME ZONE 'Asia/Kolkata')::date-31,ARRAY['keep-key'],now()),('author','boundary',(now() AT TIME ZONE 'Asia/Kolkata')::date-30,ARRAY['keep-key'],now()-interval '31 days'),('author','today',(now() AT TIME ZONE 'Asia/Kolkata')::date,ARRAY['keep-key'],now())")
    aid=conn.execute("INSERT INTO attempts(user_id,canonical_id,correct,chosen_text,context) VALUES('author','cq_test',true,'B','practice') RETURNING id").fetchone()[0]
    conn.execute("INSERT INTO practice_request_receipts(user_id,request_key,request_hash,attempt_id,response,created_at) VALUES('author','durable-key','synthetic',%s,'{}',now()-interval '2 years')",(aid,))
    result=run(client,account_retention.sweep);assert result['daily_requests']==1
    assert set(r[0] for r in conn.execute("SELECT action FROM rate_limits WHERE user_id='author'"))=={'recent-change','boundary','today'}
    assert conn.execute("SELECT count(*) FROM practice_request_receipts WHERE request_key='durable-key'").fetchone()[0]==1
    assert conn.execute('SELECT 1 FROM attempts WHERE id=%s',(aid,)).fetchone()


def test_guests_with_any_progress_history_or_recent_possible_use_stay(client,database):
    conn=database[1];empty=guest(conn);attempted=guest(conn);ledger=guest(conn);adopted=guest(conn,adopted=True);recent=guest(conn,expires='11 months');post=guest(conn)
    conn.execute("INSERT INTO attempts(user_id,canonical_id,correct,chosen_text,context) VALUES(%s,'cq_test',true,'B','practice')",(attempted,))
    conn.execute("INSERT INTO reward_ledger(user_id,event_key,kind,points,note) VALUES(%s,%s,'adjustment',1,'Preserved synthetic receipt')",(ledger,ledger))
    conn.execute("INSERT INTO posts(canonical_id,author_id,kind,body) VALUES('cq_test',%s,'doubt','Preserve legacy unlinked author')",(post,))
    result=run(client,account_retention.sweep);assert result['guests']==1
    assert conn.execute('SELECT 1 FROM users WHERE id=%s',(empty,)).fetchone() is None
    for uid in (attempted,ledger,adopted,recent,post):assert conn.execute('SELECT 1 FROM users WHERE id=%s',(uid,)).fetchone()
    assert conn.execute('SELECT adopted_by FROM guest_credentials WHERE user_id=%s',(adopted,)).fetchone()[0]=='author'


def test_future_foreign_keys_and_legacy_text_references_fail_closed(client,database):
    conn=database[1];fk=guest(conn);legacy=guest(conn)
    conn.execute('CREATE TABLE future_guest_progress(user_id text REFERENCES users(id) ON DELETE CASCADE)')
    conn.execute('CREATE TABLE future_guest_notes(owner_id text)')
    conn.execute('INSERT INTO future_guest_progress VALUES(%s)',(fk,));conn.execute('INSERT INTO future_guest_notes VALUES(%s)',(legacy,))
    result=run(client,account_retention.sweep);assert result['guests']==0
    assert conn.execute('SELECT 1 FROM users WHERE id=%s',(fk,)).fetchone()
    assert conn.execute('SELECT 1 FROM users WHERE id=%s',(legacy,)).fetchone()
    assert conn.execute('SELECT count(*) FROM future_guest_progress').fetchone()[0]==1


def test_dry_run_is_read_only_and_batches_are_bounded(client,database):
    conn=database[1];ids=[guest(conn,expires='23 months') for _ in range(23)]
    async def dry(cur):
        await cur.execute('SET TRANSACTION READ ONLY')
        await cur.execute('SELECT * FROM sweep_empty_guests(false)');return await cur.fetchone()
    preview=run(client,dry);assert preview=={'scanned':20,'eligible':20,'removed':0}
    first=run(client,account_retention.sweep);assert first['guests']==20 and first['guests_scanned']==20
    assert conn.execute('SELECT count(*) FROM users WHERE id=ANY(%s)',(ids,)).fetchone()[0]==3
    assert run(client,account_retention.sweep)['guests']==3


def test_cleanup_rollback_and_sign_in_do_not_sweep_other_accounts(client,database):
    from app.routers.auth import _new_session
    from fastapi import Response
    conn=database[1];token='old-'+uuid4().hex
    conn.execute("INSERT INTO auth_sessions(token_hash,user_id,created_at,expires_at) VALUES(%s,'author',now()-interval '40 days',now()-interval '10 days')",(token,))
    async def fail():
        async with cursor() as cur:
            await cur.execute('SET LOCAL ROLE mpsc');await account_retention.sweep(cur)
            raise RuntimeError('Synthetic transaction failure')
    with pytest.raises(RuntimeError):client.portal.call(fail)
    assert conn.execute('SELECT 1 FROM auth_sessions WHERE token_hash=%s',(token,)).fetchone()
    client.portal.call(_new_session,'owner',Response())
    assert conn.execute('SELECT 1 FROM auth_sessions WHERE token_hash=%s',(token,)).fetchone()


def test_protected_old_guests_do_not_starve_empty_candidates(client,database):
    conn=database[1]
    for _ in range(21):
        uid=guest(conn,expires='24 months')
        conn.execute("INSERT INTO posts(canonical_id,author_id,kind,body) VALUES('cq_test',%s,'doubt','Preserve older guest data')",(uid,))
    empty=guest(conn,expires='21 months')
    assert run(client,account_retention.sweep)['guests']==1
    assert not conn.execute('SELECT 1 FROM users WHERE id=%s',(empty,)).fetchone()


def test_non_id_and_composite_user_foreign_keys_preserve_exact_accounts(client,database):
    conn=database[1];by_handle=guest(conn);composite=guest(conn);empty=guest(conn)
    conn.execute('CREATE TABLE future_guest_handles(author_handle text REFERENCES users(handle) ON DELETE CASCADE)')
    conn.execute('INSERT INTO future_guest_handles SELECT handle FROM users WHERE id=%s',(by_handle,))
    conn.execute('ALTER TABLE users ADD UNIQUE(id,identity_version)')
    conn.execute('CREATE TABLE future_guest_versions(uid text,v integer,FOREIGN KEY(uid,v) REFERENCES users(id,identity_version) ON DELETE CASCADE)')
    conn.execute('INSERT INTO future_guest_versions SELECT id,identity_version FROM users WHERE id=%s',(composite,))
    assert run(client,account_retention.sweep)['guests']==1
    assert not conn.execute('SELECT 1 FROM users WHERE id=%s',(empty,)).fetchone()
    for uid in (by_handle,composite):assert conn.execute('SELECT 1 FROM users WHERE id=%s',(uid,)).fetchone()


@pytest.mark.parametrize('field,value',[
 ('plan_code',"'pro'"),('plan_status',"'active'"),('trial_ends_at',"now()-interval '2 years'"),
 ('plan_ends_at',"now()-interval '2 years'"),('razorpay_subscription_id',"'legacy-provider-reference'"),
 ('password_hash',"'legacy-credential'"),('email_verified_at',"now()-interval '2 years'"),
 ('name',"'Saved guest name'"),('avatar',"'{}'::jsonb"),('level','2'),('avatar_version','1'),('identity_version','1')])
def test_inline_financial_credential_and_profile_state_is_not_empty(client,database,field,value):
    conn=database[1];uid=guest(conn)
    # Identifiers/values are a fixed test matrix, never request-supplied SQL.
    conn.execute('UPDATE users SET '+field+'='+value+' WHERE id=%s',(uid,))
    run(client,account_retention.sweep)
    assert conn.execute('SELECT 1 FROM users WHERE id=%s',(uid,)).fetchone()
