from uuid import uuid4
import pytest
from psycopg.types.json import Jsonb
from app.config import settings

@pytest.fixture
def learner(client,actor,database):
    user='reward-'+uuid4().hex[:10];token='token-'+user
    import hashlib
    conn=database[1]
    conn.execute("INSERT INTO users(id,handle,email) VALUES(%s,%s,%s)",(user,user,user+'@example.test'))
    conn.execute("INSERT INTO auth_sessions(token_hash,user_id,expires_at) VALUES(%s,%s,now()+interval '1 day')",(hashlib.sha256(token.encode()).hexdigest(),user))
    client.cookies.clear();client.cookies.set('ism_session',token)
    h={'Origin':settings.public_origin,'X-Review-CSRF':hashlib.sha256(('bank-review:'+token).encode()).hexdigest()}
    return user,h

def attempt(conn,user,qid=None,correct=True,source='official'):
    qid=qid or 'rquestion-'+uuid4().hex
    if not conn.execute('SELECT 1 FROM canonical_questions WHERE id=%s',(qid,)).fetchone():
        conn.execute("INSERT INTO canonical_questions(id,type,question,options,answer_text,answer_source) VALUES(%s,'mcq','Synthetic verified reward question',%s,'B',%s)",(qid,Jsonb(['A','B','C','D']),source))
    conn.execute("INSERT INTO attempts(user_id,canonical_id,correct,chosen_text,context,scoring_snapshot) VALUES(%s,%s,%s,%s,'practice',%s)",(user,qid,correct,'B' if correct else 'A',Jsonb({'answer_source':source,'answer_text':'B'})))
    return qid

def test_rewards_unique_question_cap_guest_and_provenance(client,learner,database):
    user,h=learner;conn=database[1]
    qid=attempt(conn,user);attempt(conn,user,qid)
    attempt(conn,user,source='derived');attempt(conn,user,correct=False)
    wallet=client.get('/api/rewards/me').json();assert wallet['points']==1 and wallet['lifetime_xp']==10
    for _ in range(35):attempt(conn,user)
    wallet=client.get('/api/rewards/me').json();assert wallet['points']==30 and wallet['daily_xp']==300
    guest='dev_01234567-0123-0123-0123-012345678901'
    conn.execute("INSERT INTO users(id,handle) VALUES(%s,%s) ON CONFLICT DO NOTHING",(guest,guest))
    attempt(conn,guest)
    assert conn.execute('SELECT count(*) FROM reward_ledger WHERE user_id=%s',(guest,)).fetchone()[0]==0

def test_visibility_rank_and_no_client_award(client,learner,database):
    user,h=learner;attempt(database[1],user)
    assert not any(r['handle']==user for r in client.get('/api/rewards/leaderboard').json()['items'])
    assert client.post('/api/rewards/visibility',json={'public':True}).status_code==403
    assert client.post('/api/rewards/visibility',headers=h,json={'public':True}).status_code==200
    assert any(r['handle']==user and r['xp']==10 for r in client.get('/api/rewards/leaderboard').json()['items'])
    assert client.post('/api/rewards/award',headers=h,json={'points':99999}).status_code==404
    assert client.post('/api/rewards/visibility',headers=h,json={'public':False}).status_code==200

def test_redemption_disabled_atomic_retry_expiry_and_paid_separation(client,learner,database):
    user,h=learner;conn=database[1];key=uuid4().hex;h={**h,'Idempotency-Key':key}
    body={'catalog_id':'pro-week','version':1}
    assert client.post('/api/rewards/redeem',headers=h,json=body).status_code==409
    # Synthetic points only. Real API has no arbitrary award path.
    conn.execute("INSERT INTO reward_ledger(user_id,event_key,kind,points,xp,note) VALUES(%s,%s,'adjustment',2000,100,'Synthetic reward wallet')",(user,key))
    conn.execute("UPDATE reward_catalog SET enabled=true WHERE id='pro-week'")
    try:
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=2) as pool:res=list(pool.map(lambda _:client.post('/api/rewards/redeem',headers=h,json=body),range(2)))
        assert all(r.status_code==200 for r in res),[r.text for r in res]
        assert res[0].json()['id']==res[1].json()['id']
        wallet=client.get('/api/rewards/me').json();assert wallet['points']==1000 and wallet['lifetime_xp']==100
        assert conn.execute('SELECT account_has_pro(%s)',(user,)).fetchone()[0] is True
        assert client.get('/api/auth/session').json()['plan_code']=='pro'
        billing=client.get('/api/billing/me').json();assert billing['plan_code']=='pro' and billing['plan_status']=='rewarded' and len(billing['reward_access'])==1
        profile=client.get('/api/me/profile').json();assert profile['plan_code']=='pro' and profile['plan_status']=='rewarded'
        assert conn.execute('SELECT plan_code FROM users WHERE id=%s',(user,)).fetchone()[0]=='free'
        assert client.post('/api/rewards/redeem',headers={**h,'Idempotency-Key':uuid4().hex},json=body).status_code==409
        assert client.post('/api/rewards/redeem',headers=h,json={**body,'version':2}).status_code==409
    finally:conn.execute("UPDATE reward_catalog SET enabled=false WHERE id='pro-week'")

def test_catalog_owner_only_and_stale_price(client,actor):
    h=actor('reviewer1');assert client.get('/api/admin/bank/rewards').status_code==403
    h=actor('owner');row=client.get('/api/admin/bank/rewards').json()[0]
    response=client.post('/api/admin/bank/rewards/pro-week',headers=h,json={'version':row['version'],'points':1000,'enabled':False,'reason':'Synthetic policy review only'})
    assert response.status_code==200
    assert client.post('/api/admin/bank/rewards/pro-week',headers=h,json={'version':row['version'],'points':1000,'enabled':True,'reason':'Synthetic stale catalog change'}).status_code==409

def test_distinct_redemptions_cannot_double_spend_and_expiry(client,learner,database):
    from concurrent.futures import ThreadPoolExecutor
    user,h=learner;conn=database[1];offer='test-redeem-'+uuid4().hex
    conn.execute('INSERT INTO reward_catalog(id,title,points,pro_days,enabled) VALUES(%s,\'Synthetic reward\',1000,1,true)',(offer,))
    conn.execute("INSERT INTO reward_ledger(user_id,event_key,kind,points,note) VALUES(%s,%s,'adjustment',1000,'Synthetic test only')",(user,uuid4().hex))
    def run(_):return client.post('/api/rewards/redeem',headers={**h,'Idempotency-Key':uuid4().hex},json={'catalog_id':offer,'version':1})
    with ThreadPoolExecutor(max_workers=2) as pool:responses=list(pool.map(run,range(2)))
    assert sorted(r.status_code for r in responses)==[200,409]
    assert client.get('/api/rewards/me').json()['points']==0
    assert conn.execute("SELECT count(*) FROM reward_redemptions WHERE user_id=%s",(user,)).fetchone()[0]==1
    # Use a separate expired synthetic receipt, preserving immutable history.
    other='expired-'+uuid4().hex
    conn.execute('INSERT INTO users(id,handle,email) VALUES(%s,%s,%s)',(other,other,other+'@example.test'))
    conn.execute("INSERT INTO reward_redemptions(id,user_id,idempotency_key,catalog_id,catalog_version,points,starts_at,ends_at) VALUES(%s,%s,%s,%s,1,1000,now()-interval '2 days',now()-interval '1 day')",(uuid4().hex,other,uuid4().hex,offer))
    assert conn.execute('SELECT account_has_pro(%s)',(other,)).fetchone()[0] is False
    conn.execute('UPDATE reward_catalog SET enabled=false WHERE id=%s',(offer,))

def test_checkpoint_scope_and_journey(client,learner,database):
    user,h=learner;conn=database[1];cid='journey-'+uuid4().hex
    conn.execute("INSERT INTO collections(id,title,kind) VALUES(%s,'Synthetic exam journey','exam')",(cid,))
    body={'pool':'scorable','status':'wrong','q':'synthetic','offset':20}
    assert client.post('/api/me/exam-checkpoint/'+cid,json=body).status_code==403
    assert client.post('/api/me/exam-checkpoint/'+cid,headers=h,json=body).status_code==200
    journey=client.get('/api/me/exam-journey/'+cid).json()
    assert journey['checkpoint']['state']['offset']==20
    assert journey['checkpoint']['state']['status']=='wrong'
    assert journey['active_mock'] is None
    assert client.post('/api/me/exam-checkpoint/'+cid,headers=h,json={**body,'paper':'not-in-this-exam'}).status_code==422
    assert client.post('/api/me/exam-checkpoint/'+cid,headers=h,json={**body,'offset':-1}).status_code==422

def test_mock_rewards_and_subscription_view_share_entitlement(client,actor,database):
    from test_scoring_revisions import start_and_finish
    qid,cid,mid,h,result=start_and_finish(client,actor,database)
    conn=database[1]
    assert conn.execute('SELECT count(*) FROM reward_question_claims WHERE user_id=\'owner\' AND canonical_id=%s',(qid,)).fetchone()[0]==1
    # Replaying a submitted mock cannot create another award.
    assert client.post('/api/mocks/'+mid+'/submit',headers=h,json={'answers':[]}).status_code==409
    assert conn.execute('SELECT count(*) FROM reward_question_claims WHERE user_id=\'owner\' AND canonical_id=%s',(qid,)).fetchone()[0]==1

def test_award_trigger_runs_with_actual_app_role(client,learner,database):
    user,h=learner;conn=database[1];qid='role-reward-'+uuid4().hex
    conn.execute("INSERT INTO canonical_questions(id,type,question,options,answer_text,answer_source) VALUES(%s,'mcq','Synthetic app-role reward','[\"A\",\"B\",\"C\",\"D\"]','B','official')",(qid,))
    with conn.transaction():
        conn.execute('SET LOCAL ROLE mpsc')
        conn.execute("INSERT INTO attempts(user_id,canonical_id,correct,chosen_text,context,scoring_snapshot) VALUES(%s,%s,true,'B','practice',%s)",(user,qid,Jsonb({'answer_source':'official','answer_text':'B'})))
    assert client.get('/api/rewards/me').json()['points']==1
