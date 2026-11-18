"""Synthetic signed webhooks only; no network, merchant account or payment."""
import hashlib,hmac,json
from datetime import datetime,timedelta,timezone
from uuid import uuid4
import pytest
from app.config import settings
from app.routers import billing

@pytest.fixture
def provider(monkeypatch,client):
    client.cookies.clear()
    monkeypatch.setattr(settings,'razorpay_key_id','rzp_test_synthetic')
    monkeypatch.setattr(settings,'razorpay_key_secret','synthetic-key-secret')
    monkeypatch.setattr(settings,'razorpay_webhook_secret','synthetic-webhook-secret')
    monkeypatch.setattr(settings,'razorpay_checkout_enabled',False)
    async def no_network(*args):raise AssertionError('No real provider call is allowed')
    monkeypatch.setattr(billing,'_razorpay_async',no_network)

def signed(client,payload,event_id=None):
    raw=json.dumps(payload,separators=(',',':')).encode()
    return client.post('/api/billing/webhook',content=raw,headers={'Content-Type':'application/json',
      'X-Razorpay-Signature':hmac.new(settings.razorpay_webhook_secret.encode(),raw,hashlib.sha256).hexdigest(),
      'X-Razorpay-Event-Id':event_id or uuid4().hex})

def seed(database):
    user='billing-'+uuid4().hex[:10];sid='sub_'+uuid4().hex
    database[1].execute("INSERT INTO users(id,handle,email,razorpay_subscription_id) VALUES(%s,%s,%s,%s)",(user,user,user+'@example.test',sid))
    database[1].execute("INSERT INTO billing_subscriptions(user_id,plan_code,billing_period,amount_paise,razorpay_plan_id,razorpay_subscription_id,status) VALUES(%s,'pro','monthly',10000,'plan_synthetic',%s,'created')",(user,sid))
    return user,sid

def test_deferred_checkout_requires_opt_in_even_with_credentials(client,actor,provider):
    assert client.get('/api/billing/config').json()['enabled'] is False
    r=client.post('/api/billing/checkout',headers=actor('author'),json={'period':'monthly'})
    assert r.status_code==503
    settings.razorpay_checkout_enabled=True
    assert client.get('/api/billing/config').json()['enabled'] is True

def test_bad_signature_never_records_event(client,provider,database):
    eid=uuid4().hex
    r=client.post('/api/billing/webhook',content=b'{}',headers={'X-Razorpay-Signature':'bad','X-Razorpay-Event-Id':eid})
    assert r.status_code==400
    assert not database[1].execute('SELECT 1 FROM billing_webhook_events WHERE event_key=%s',(eid,)).fetchone()

def test_webhook_current_state_duplicate_and_authentication_not_paid(client,provider,database,monkeypatch):
    user,sid=seed(database);end=int((datetime.now(timezone.utc)+timedelta(days=30)).timestamp())
    current={'id':sid,'status':'authenticated','current_end':end}
    async def fetch(method,path,payload=None):assert method=='GET';return current
    monkeypatch.setattr(billing,'_razorpay_async',fetch)
    payload={'event':'subscription.activated','payload':{'subscription':{'entity':{'id':sid,'status':'active'}}}}
    eid=uuid4().hex
    r=signed(client,payload,eid);assert r.status_code==200,r.text
    assert database[1].execute('SELECT plan_code FROM users WHERE id=%s',(user,)).fetchone()[0]=='free'
    assert signed(client,payload,eid).json()['duplicate'] is True
    current['status']='active'
    assert signed(client,payload).status_code==200
    assert database[1].execute('SELECT plan_code FROM users WHERE id=%s',(user,)).fetchone()[0]=='pro'

def test_failed_webhook_transaction_remains_retryable(client,provider,database,monkeypatch):
    user,sid=seed(database);eid=uuid4().hex
    async def fetch(*args):return {'id':sid,'status':'active','current_end':int((datetime.now(timezone.utc)+timedelta(days=1)).timestamp())}
    monkeypatch.setattr(billing,'_razorpay_async',fetch)
    original=billing._apply_subscription
    async def fail(sub,cur=None):
        await cur.execute("UPDATE users SET plan_code='pro' WHERE id=%s",(user,))
        from fastapi import HTTPException
        raise HTTPException(503,'Synthetic transient failure')
    monkeypatch.setattr(billing,'_apply_subscription',fail)
    payload={'event':'subscription.activated','payload':{'subscription':{'entity':{'id':sid}}}}
    assert signed(client,payload,eid).status_code==503
    assert not database[1].execute('SELECT 1 FROM billing_webhook_events WHERE event_key=%s',(eid,)).fetchone()
    assert database[1].execute('SELECT plan_code FROM users WHERE id=%s',(user,)).fetchone()[0]=='free'
    monkeypatch.setattr(billing,'_apply_subscription',original)
    assert signed(client,payload,eid).status_code==200
    assert database[1].execute('SELECT plan_code FROM users WHERE id=%s',(user,)).fetchone()[0]=='pro'

@pytest.fixture
def checkout_account(client,provider,database,monkeypatch):
    user,sid=seed(database)
    token='billing-session-'+uuid4().hex
    database[1].execute("INSERT INTO auth_sessions(token_hash,user_id,expires_at) VALUES(%s,%s,now()+interval '1 hour')",(hashlib.sha256(token.encode()).hexdigest(),user))
    client.cookies.set('ism_session',token)
    response=client.get('/api/review/session')
    assert response.status_code==200,response.text
    headers={'Origin':'https://study.hawayu.in','X-Review-CSRF':response.json()['csrf']}
    monkeypatch.setattr(settings,'razorpay_checkout_enabled',True)
    async def plan(*args):return 'plan_synthetic'
    monkeypatch.setattr(billing,'_get_or_create_plan',plan)
    return user,sid,headers

def test_reopening_unpaid_checkout_reuses_subscription(client,database,checkout_account,monkeypatch):
    user,sid,headers=checkout_account
    async def fetch(method,path,payload=None):
        assert (method,path)==('GET','/subscriptions/'+sid)
        return {'id':sid,'status':'created'}
    monkeypatch.setattr(billing,'_razorpay_async',fetch)
    for _ in range(2):
        response=client.post('/api/billing/checkout',headers=headers,json={'period':'monthly'})
        assert response.status_code==200,response.text
        assert response.json()['subscription_id']==sid
    assert database[1].execute('SELECT count(*) FROM billing_subscriptions WHERE user_id=%s',(user,)).fetchone()[0]==1

@pytest.mark.parametrize('status',['cancelled','completed','expired'])
def test_terminal_subscription_allows_new_purchase_and_old_events_cannot_revoke_it(client,database,checkout_account,monkeypatch,status):
    user,sid,headers=checkout_account;new_sid='sub_'+uuid4().hex
    end=int((datetime.now(timezone.utc)+timedelta(days=30)).timestamp())
    async def provider_call(method,path,payload=None):
        if method=='GET':return {'id':sid,'status':status}
        assert path=='/subscriptions'
        assert payload['total_count']==120
        return {'id':new_sid,'status':'created'}
    monkeypatch.setattr(billing,'_razorpay_async',provider_call)
    response=client.post('/api/billing/checkout',headers=headers,json={'period':'monthly'})
    assert response.status_code==200,response.text
    assert response.json()['subscription_id']==new_sid
    database[1].execute("UPDATE users SET plan_code='pro',plan_status='active',plan_ends_at=to_timestamp(%s) WHERE id=%s",(end,user))
    event={'event':'subscription.'+status,'payload':{'subscription':{'entity':{'id':sid}}}}
    client.cookies.clear()  # Provider deliveries have no signed-in browser session.
    assert signed(client,event).status_code==200
    row=database[1].execute('SELECT razorpay_subscription_id,plan_code,plan_status FROM users WHERE id=%s',(user,)).fetchone()
    assert row==(new_sid,'pro','active')

@pytest.mark.parametrize('status',['active','authenticated','pending','halted'])
def test_nonterminal_subscription_prevents_second_mandate(client,checkout_account,monkeypatch,status):
    user,sid,headers=checkout_account
    async def fetch(method,path,payload=None):
        assert method=='GET'
        return {'id':sid,'status':status}
    monkeypatch.setattr(billing,'_razorpay_async',fetch)
    assert client.post('/api/billing/checkout',headers=headers,json={'period':'monthly'}).status_code==409

def test_concurrent_checkout_creates_one_provider_subscription(client,database,checkout_account,monkeypatch):
    import asyncio
    from concurrent.futures import ThreadPoolExecutor
    user,sid,headers=checkout_account;new_sid='sub_'+uuid4().hex;created=[]
    database[1].execute('UPDATE users SET razorpay_subscription_id=NULL WHERE id=%s',(user,))
    async def provider_call(method,path,payload=None):
        if method=='GET':return {'id':new_sid,'status':'created'}
        assert path=='/subscriptions'
        created.append(payload)
        await asyncio.sleep(0.05)
        return {'id':new_sid,'status':'created'}
    monkeypatch.setattr(billing,'_razorpay_async',provider_call)
    def purchase(_):return client.post('/api/billing/checkout',headers=headers,json={'period':'monthly'})
    with ThreadPoolExecutor(max_workers=2) as executor:responses=list(executor.map(purchase,range(2)))
    assert [r.status_code for r in responses]==[200,200],[r.text for r in responses]
    assert {r.json()['subscription_id'] for r in responses}=={new_sid}
    assert len(created)==1

def test_price_change_creates_new_plan_without_reusing_old_price(client,provider,database,actor,monkeypatch):
    old_plan='plan_old_'+uuid4().hex;new_plan='plan_new_'+uuid4().hex;sid='sub_'+uuid4().hex;calls=[]
    database[1].execute("INSERT INTO billing_plan_refs(plan_code,billing_period,razorpay_plan_id,amount_paise) VALUES('pro','monthly',%s,9900)",(old_plan,))
    monkeypatch.setattr(settings,'razorpay_checkout_enabled',True)
    async def provider_call(method,path,payload=None):
        calls.append((method,path,payload))
        if path=='/plans':
            assert payload['item']['amount']==10000
            return {'id':new_plan}
        if method=='POST':
            assert payload['plan_id']==new_plan
            return {'id':sid,'status':'created'}
        return {'id':sid,'status':'created'}
    monkeypatch.setattr(billing,'_razorpay_async',provider_call)
    headers=actor('author')
    for _ in range(2):
        response=client.post('/api/billing/checkout',headers=headers,json={'period':'monthly'})
        assert response.status_code==200,response.text
        assert response.json()['amount_paise']==10000
    assert len([c for c in calls if c[:2]==('POST','/plans')])==1
    assert database[1].execute("SELECT razorpay_plan_id,amount_paise FROM billing_plan_refs WHERE plan_code='pro' AND billing_period='monthly'").fetchone()==(old_plan,9900)
    assert database[1].execute("SELECT razorpay_plan_id,amount_paise FROM billing_plan_refs WHERE plan_code='pro:inr:10000:v1' AND billing_period='monthly'").fetchone()==(new_plan,10000)
