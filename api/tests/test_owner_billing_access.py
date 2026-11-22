"""Owner-selected rates and complimentary access use synthetic accounts only."""
import hashlib,hmac,json
from datetime import datetime,timedelta,timezone
from uuid import uuid4
import pytest
from app.config import settings
from app.routers import billing

@pytest.fixture
def account(database):
    user='pricing-'+uuid4().hex[:12];token='pricing-session-'+uuid4().hex
    database[1].execute("INSERT INTO users(id,handle,email) VALUES(%s,%s,%s)",(user,user,user+'@example.test'))
    database[1].execute("INSERT INTO auth_sessions(token_hash,user_id,expires_at) VALUES(%s,%s,now()+interval '1 day')",(hashlib.sha256(token.encode()).hexdigest(),user))
    return user,token

def sign_in(client,token):
    client.cookies.clear();client.cookies.set('ism_session',token)
    session=client.get('/api/review/session');assert session.status_code==200,session.text
    return {'Origin':'https://study.hawayu.in','X-Review-CSRF':session.json()['csrf']}

def test_owner_only_rates_csrf_mfa_and_audited_account_price(client,actor,database,account,monkeypatch):
    user,token=account;route='/api/billing/admin/account/'+user+'/rate'
    h=actor('reviewer1')
    assert client.get('/api/billing/admin/account',params={'email':user+'@example.test'}).status_code==403
    assert client.post(route,headers=h,json={'amount_paise':5000,'expected_amount_paise':10000}).status_code==403
    h=actor('owner')
    assert client.post(route,json={'amount_paise':5000,'expected_amount_paise':10000}).status_code==403
    monkeypatch.setattr(settings,'mfa_enforce_staff',True)
    assert client.post(route,headers=h,json={'amount_paise':5000,'expected_amount_paise':10000}).status_code==403
    monkeypatch.setattr(settings,'mfa_enforce_staff',False)
    assert client.post(route,headers=h,json={'amount_paise':5000,'expected_amount_paise':10000}).status_code==200
    assert client.post(route,headers=h,json={'amount_paise':10000,'expected_amount_paise':10000}).status_code==409
    assert client.post(route,headers=h,json={'amount_paise':1,'expected_amount_paise':5000}).status_code==422
    audit=database[1].execute("SELECT detail FROM account_security_events WHERE user_id=%s AND action='owner_billing_rate_changed'",(user,)).fetchone()[0]
    assert audit['actor_id']=='owner' and audit['amount_paise']==5000
    sign_in(client,token)
    assert client.get('/api/billing/config').json()['plans']==[{'code':'pro','period':'monthly','amount_paise':5000}]
    actor('outsider')
    assert client.get('/api/billing/config').json()['plans'][0]['amount_paise']==10000
    client.cookies.clear()
    assert client.get('/api/billing/config').json()['plans'][0]['amount_paise']==10000

def test_owner_billing_account_view_includes_refund_reconciliation(client,actor,database,account):
    user,_=account
    payment_id='pay_'+uuid4().hex;refund_id='rfnd_'+uuid4().hex;sid='sub_'+uuid4().hex
    database[1].execute("INSERT INTO billing_subscriptions(user_id,plan_code,billing_period,amount_paise,razorpay_plan_id,razorpay_subscription_id,status) VALUES(%s,'pro','monthly',10000,'plan_synthetic',%s,'active')",(user,sid))
    database[1].execute("INSERT INTO billing_payments(razorpay_payment_id,razorpay_subscription_id,user_id,amount_paise,currency,status,paid_at,amount_refunded_paise,refund_status) VALUES(%s,%s,%s,10000,'INR','captured',now(),2500,'partial')",(payment_id,sid,user))
    database[1].execute("INSERT INTO billing_refunds(razorpay_refund_id,razorpay_payment_id,amount_paise,currency,status,provider_created_at) VALUES(%s,%s,2500,'INR','pending',now())",(refund_id,payment_id))
    headers=actor('owner')
    response=client.get('/api/billing/admin/account',headers=headers,params={'email':user+'@example.test'})
    assert response.status_code==200,response.text
    payload=response.json()
    assert payload['subscription']['access_end_reason'] is None
    assert payload['payments'][0]['razorpay_payment_id']==payment_id
    assert payload['payments'][0]['amount_refunded_paise']==2500
    assert payload['payments'][0]['refund_status']=='partial'
    assert payload['refunds'][0]['razorpay_refund_id']==refund_id
    assert payload['refunds'][0]['status']=='pending'

def test_checkout_uses_assigned_price_and_cannot_choose_arbitrary_amount(client,actor,database,account,monkeypatch):
    user,token=account
    database[1].execute("INSERT INTO billing_account_rates(user_id,amount_paise,updated_by) VALUES(%s,5000,'owner')",(user,))
    monkeypatch.setattr(settings,'razorpay_checkout_enabled',True)
    monkeypatch.setattr(settings,'razorpay_key_id','rzp_test_synthetic')
    monkeypatch.setattr(settings,'razorpay_key_secret','synthetic')
    monkeypatch.setattr(settings,'razorpay_webhook_secret','synthetic')
    async def plan(period,amount,months):
        assert amount==5000 and period=='monthly' and months==1
        return 'plan_discount_'+user
    async def create(method,path,payload=None):
        assert method=='POST' and path=='/subscriptions'
        assert payload['plan_id']=='plan_discount_'+user
        return {'id':'sub_'+user,'status':'created'}
    monkeypatch.setattr(billing,'_get_or_create_plan',plan)
    monkeypatch.setattr(billing,'_razorpay_async',create)
    h=sign_in(client,token)
    r=client.post('/api/billing/checkout',headers=h,json={'period':'monthly','amount_paise':1})
    assert r.status_code==200,r.text
    assert r.json()['amount_paise']==5000
    assert database[1].execute('SELECT amount_paise FROM billing_subscriptions WHERE user_id=%s',(user,)).fetchone()[0]==5000
    assert client.post('/api/billing/checkout',headers=h,json={'period':'yearly'}).status_code==422

def test_days_stack_preserve_trial_and_paid_state_and_retry_once(client,actor,database,account):
    user,token=account;h=actor('owner');route='/api/billing/admin/account/'+user+'/days'
    database[1].execute("UPDATE users SET plan_code='pro',plan_status='trial',trial_ends_at=now()+interval '7 days' WHERE id=%s",(user,))
    key=uuid4().hex
    first=client.post(route,headers=h,json={'days':7,'idempotency_key':key})
    assert first.status_code==200,first.text
    assert client.post(route,headers=h,json={'days':7,'idempotency_key':key}).json()==first.json()
    assert client.post(route,headers=h,json={'days':8,'idempotency_key':key}).status_code==409
    second=client.post(route,headers=h,json={'days':3,'idempotency_key':uuid4().hex})
    assert second.status_code==200,second.text
    assert second.json()['starts_at']==first.json()['ends_at']
    assert database[1].execute('SELECT count(*) FROM billing_access_grants WHERE user_id=%s',(user,)).fetchone()[0]==2
    assert database[1].execute("SELECT plan_status FROM users WHERE id=%s",(user,)).fetchone()[0]=='trial'
    assert database[1].execute('SELECT count(*) FROM billing_payments WHERE user_id=%s',(user,)).fetchone()[0]==0
    assert database[1].execute("SELECT count(*) FROM account_security_events WHERE user_id=%s AND action='owner_pro_days_granted'",(user,)).fetchone()[0]==2
    sign_in(client,token)
    assert len(client.get('/api/billing/me').json()['granted_access'])==2

def test_manual_access_survives_cancelled_webhook_and_expires(client,actor,database,account,monkeypatch):
    user,token=account;h=actor('owner')
    r=client.post('/api/billing/admin/account/'+user+'/days',headers=h,json={'days':7,'idempotency_key':uuid4().hex})
    assert r.status_code==200,r.text
    sid='sub_'+user
    database[1].execute('UPDATE users SET razorpay_subscription_id=%s WHERE id=%s',(sid,user))
    database[1].execute("INSERT INTO billing_subscriptions(user_id,plan_code,billing_period,amount_paise,razorpay_plan_id,razorpay_subscription_id,status) VALUES(%s,'pro','monthly',10000,'plan_synthetic',%s,'created')",(user,sid))
    async def fetch(*args):return {'id':sid,'status':'cancelled'}
    monkeypatch.setattr(billing,'_razorpay_async',fetch)
    monkeypatch.setattr(settings,'razorpay_webhook_secret','synthetic')
    raw=json.dumps({'event':'subscription.cancelled','payload':{'subscription':{'entity':{'id':sid}}}}).encode()
    client.cookies.clear()
    r=client.post('/api/billing/webhook',content=raw,headers={'X-Razorpay-Signature':hmac.new(b'synthetic',raw,hashlib.sha256).hexdigest()})
    assert r.status_code==200,r.text
    sign_in(client,token)
    me=client.get('/api/billing/me').json();assert me['plan_code']=='pro' and me['plan_status']=='granted'
    assert client.get('/api/auth/session').json()['plan_status']=='granted'
    assert client.get('/api/me/profile').json()['plan_status']=='granted'
    expired='expired-'+uuid4().hex[:12]
    database[1].execute('INSERT INTO users(id,handle,email) VALUES(%s,%s,%s)',(expired,expired,expired+'@example.test'))
    database[1].execute("INSERT INTO billing_access_grants(user_id,granted_by,idempotency_key,days,starts_at,ends_at) VALUES(%s,'owner',%s,1,now()-interval '2 days',now()-interval '1 day')",(expired,uuid4().hex))
    assert database[1].execute('SELECT account_has_pro(%s)',(expired,)).fetchone()[0] is False

def test_reward_access_starts_after_owner_grant(client,actor,database,account,monkeypatch):
    from app.services import reward_economy
    async def launched(cur):return {'catalog_ready':True}
    monkeypatch.setattr(reward_economy,'feature_gates',launched)
    user,token=account;h=actor('owner')
    grant=client.post('/api/billing/admin/account/'+user+'/days',headers=h,json={'days':7,'idempotency_key':uuid4().hex})
    assert grant.status_code==200,grant.text
    database[1].execute("INSERT INTO reward_ledger(user_id,event_key,kind,points,note) VALUES(%s,%s,'adjustment',10000,'Synthetic test wallet')",(user,uuid4().hex))
    offer=database[1].execute("UPDATE reward_catalog SET enabled=true WHERE id='pro-week' RETURNING version").fetchone()
    try:
        h=sign_in(client,token)
        r=client.post('/api/rewards/redeem',headers={**h,'Idempotency-Key':uuid4().hex},json={'catalog_id':'pro-week','version':offer[0]})
        assert r.status_code==200,r.text
        assert r.json()['starts_at']==grant.json()['ends_at']
    finally:database[1].execute("UPDATE reward_catalog SET enabled=false WHERE id='pro-week'")
