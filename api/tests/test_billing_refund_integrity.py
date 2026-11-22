"""Refund ordering and provenance on disposable PostgreSQL using the app role."""
from contextlib import asynccontextmanager
from datetime import datetime,timezone
from uuid import uuid4

import pytest
from psycopg.errors import InsufficientPrivilege

from app.db import cursor
from app.routers import billing
from test_billing_deferred import provider,seed,seed_payment,signed


@pytest.fixture(autouse=True)
def app_role(monkeypatch):
    @asynccontextmanager
    async def real_role():
        async with cursor() as cur:
            await cur.execute('SET LOCAL ROLE mpsc')
            yield cur
    monkeypatch.setattr(billing,'cursor',real_role)


@pytest.fixture
def refund_case(client,provider,database,monkeypatch):
    user,sid=seed(database);pid=seed_payment(database,user,sid);rid='rfnd_'+uuid4().hex
    database[1].execute("UPDATE users SET plan_code='pro',plan_status='active',plan_ends_at=now()+interval '30 days' WHERE id=%s",(user,))
    refund={'id':rid,'payment_id':pid,'amount':10000,'currency':'INR','status':'processed','created_at':int(datetime.now(timezone.utc).timestamp())}
    payment={'id':pid,'amount':10000,'currency':'INR','status':'refunded','captured':True,'amount_refunded':10000,'refund_status':'full'}
    state={'refund':refund,'payment':payment,'items':[refund],'calls':[]}
    async def fetch(method,path,payload=None):
        assert method=='GET'
        state['calls'].append(path)
        if '/refunds?' in path:
            items=state.get('pages',{}).get(path,state['items'])
            return {'count':len(items),'items':items}
        return state['refund'] if path.startswith('/refunds/') else state['payment']
    monkeypatch.setattr(billing,'_razorpay_async',fetch)
    event={'event':'refund.processed','payload':{'refund':{'entity':{'id':rid,'payment_id':pid}}}}
    return user,sid,pid,rid,event,state


@pytest.mark.parametrize('patch',[
    {'amount':9999},{'amount':True},{'currency':'USD'},{'captured':False},
    {'status':'authorized'},{'refund_status':'full','amount_refunded':9999},
    {'status':[]},{'refund_status':{}},
])
def test_payment_provenance_failure_rolls_back_receipt_and_access(client,database,refund_case,patch):
    user,_,pid,rid,event,state=refund_case
    state['payment'].update(patch);eid=uuid4().hex
    response=signed(client,event,eid)
    assert response.status_code==502,response.text
    assert not database[1].execute('SELECT 1 FROM billing_webhook_events WHERE event_key=%s',(eid,)).fetchone()
    assert not database[1].execute('SELECT 1 FROM billing_refunds WHERE razorpay_refund_id=%s',(rid,)).fetchone()
    assert database[1].execute('SELECT account_has_pro(%s)',(user,)).fetchone()[0]
    assert database[1].execute('SELECT amount_refunded_paise FROM billing_payments WHERE razorpay_payment_id=%s',(pid,)).fetchone()[0]==0


def test_pending_portion_of_full_aggregate_does_not_end_access(client,database,refund_case):
    user,sid,_,_,event,state=refund_case
    state['refund']['amount']=2500
    pending={**state['refund'],'id':'rfnd_'+uuid4().hex,'amount':7500,'status':'pending'}
    state['items']=[state['refund'],pending]
    assert signed(client,event).status_code==200
    assert database[1].execute('SELECT access_ended_at FROM billing_subscriptions WHERE razorpay_subscription_id=%s',(sid,)).fetchone()[0] is None
    assert database[1].execute('SELECT account_has_pro(%s)',(user,)).fetchone()[0]
    pending['status']='processed'
    assert signed(client,event).status_code==200
    assert not database[1].execute('SELECT account_has_pro(%s)',(user,)).fetchone()[0]


def test_refund_before_payment_can_retry_after_charge_arrives(client,database,refund_case):
    user,sid,pid,_,event,_=refund_case;eid=uuid4().hex
    database[1].execute('DELETE FROM billing_payments WHERE razorpay_payment_id=%s',(pid,))
    assert signed(client,event,eid).status_code==503
    database[1].execute("INSERT INTO billing_payments(razorpay_payment_id,razorpay_subscription_id,user_id,amount_paise,currency,status) VALUES(%s,%s,%s,10000,'INR','captured')",(pid,sid,user))
    assert signed(client,event,eid).status_code==200
    assert not database[1].execute('SELECT account_has_pro(%s)',(user,)).fetchone()[0]


def test_refund_for_old_subscription_preserves_new_subscription(client,database,refund_case):
    user,sid,_,_,event,_=refund_case;new_sid='sub_'+uuid4().hex
    database[1].execute("INSERT INTO billing_subscriptions(user_id,plan_code,billing_period,amount_paise,razorpay_plan_id,razorpay_subscription_id,status) VALUES(%s,'pro','monthly',10000,'plan_synthetic',%s,'active')",(user,new_sid))
    database[1].execute('UPDATE users SET razorpay_subscription_id=%s WHERE id=%s',(new_sid,user))
    assert signed(client,event).status_code==200
    assert database[1].execute('SELECT access_end_reason FROM billing_subscriptions WHERE razorpay_subscription_id=%s',(sid,)).fetchone()[0]=='full_refund'
    assert database[1].execute('SELECT access_ended_at FROM billing_subscriptions WHERE razorpay_subscription_id=%s',(new_sid,)).fetchone()[0] is None
    assert database[1].execute('SELECT account_has_pro(%s)',(user,)).fetchone()[0]


@pytest.mark.parametrize('field,value',[('amount',5000),('currency','USD'),('created_at',1),('status','pending')])
def test_processed_refund_history_cannot_be_rewritten(client,database,refund_case,field,value):
    _,_,_,rid,event,state=refund_case
    assert signed(client,event).status_code==200
    state['refund'][field]=value;eid=uuid4().hex
    assert signed(client,event,eid).status_code==502
    assert not database[1].execute('SELECT 1 FROM billing_webhook_events WHERE event_key=%s',(eid,)).fetchone()
    assert database[1].execute('SELECT amount_paise,currency,status FROM billing_refunds WHERE razorpay_refund_id=%s',(rid,)).fetchone()==(10000,'INR','processed')


@pytest.mark.parametrize('payload',[
    {},
    {'refund':[]},{'refund':{'entity':[]}},{'payment':{'entity':None}},
    {'refund':{'entity':{'id':'rfnd_ok','payment_id':'pay_bad/other'}}},
    {'refund':{'entity':{'id':'rfnd_ok','payment_id':'pay_one'}},'payment':{'entity':{'id':'pay_other'}}},
])
def test_malformed_signed_payload_is_rejected_without_provider_calls(client,provider,database,monkeypatch,payload):
    eid=uuid4().hex
    assert signed(client,{'event':'refund.processed','payload':payload},eid).status_code==400
    assert not database[1].execute('SELECT 1 FROM billing_webhook_events WHERE event_key=%s',(eid,)).fetchone()


def test_duplicate_refund_ids_in_provider_list_cannot_end_access(client,database,refund_case):
    user,_,_,_,event,state=refund_case
    state['items']=[state['refund'],state['refund']]
    assert signed(client,event).status_code==502
    assert database[1].execute('SELECT account_has_pro(%s)',(user,)).fetchone()[0]


def test_full_refund_list_is_read_across_pages(client,database,refund_case):
    user,_,pid,_,event,state=refund_case
    state['refund']['amount']=100
    first=[{**state['refund'],'id':'rfnd_'+uuid4().hex,'amount':99} for _ in range(100)]
    state['pages']={f'/payments/{pid}/refunds?count=100&skip=0':first,
        f'/payments/{pid}/refunds?count=100&skip=100':[state['refund']]}
    assert signed(client,event).status_code==200
    assert state['calls'][-1].endswith('skip=100')
    assert not database[1].execute('SELECT account_has_pro(%s)',(user,)).fetchone()[0]


def test_refund_timestamp_overflow_is_retryable_provider_error(client,database,refund_case):
    user,_,_,_,event,state=refund_case;eid=uuid4().hex
    state['refund']['created_at']=10**100
    assert signed(client,event,eid).status_code==502
    assert not database[1].execute('SELECT 1 FROM billing_webhook_events WHERE event_key=%s',(eid,)).fetchone()
    assert database[1].execute('SELECT account_has_pro(%s)',(user,)).fetchone()[0]


def test_refund_list_limit_keeps_access_and_receipt_retryable(client,database,refund_case):
    user,_,pid,_,event,state=refund_case;eid=uuid4().hex
    state['pages']={f'/payments/{pid}/refunds?count=100&skip={page*100}':[
        {**state['refund'],'id':'rfnd_'+uuid4().hex,'amount':1} for _ in range(100)] for page in range(10)}
    assert signed(client,event,eid).status_code==503
    assert len([p for p in state['calls'] if '/refunds?' in p])==10
    assert not database[1].execute('SELECT 1 FROM billing_webhook_events WHERE event_key=%s',(eid,)).fetchone()
    assert database[1].execute('SELECT account_has_pro(%s)',(user,)).fetchone()[0]


def test_app_role_cannot_rewrite_charge_or_payment_ownership(database,refund_case):
    _,_,pid,_,_,_=refund_case;conn=database[1]
    with conn.transaction():
        conn.execute('SET LOCAL ROLE mpsc')
        for statement in ('UPDATE billing_payments SET amount_paise=1 WHERE razorpay_payment_id=%s',
                          "UPDATE billing_payments SET user_id='outsider' WHERE razorpay_payment_id=%s"):
            with pytest.raises(InsufficientPrivilege),conn.transaction():
                conn.execute(statement,(pid,))


def test_simultaneous_same_event_id_for_different_payments_applies_once(client,provider,database,monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    refunds={};payments={};events=[];users=[];calls=[]
    for _ in range(2):
        user,sid=seed(database);pid=seed_payment(database,user,sid);rid='rfnd_'+uuid4().hex
        users.append(user)
        database[1].execute("UPDATE users SET plan_code='pro',plan_status='active',plan_ends_at=now()+interval '30 days' WHERE id=%s",(user,))
        refunds[rid]={'id':rid,'payment_id':pid,'amount':10000,'currency':'INR','status':'processed','created_at':int(datetime.now(timezone.utc).timestamp())}
        payments[pid]={'id':pid,'amount':10000,'currency':'INR','status':'refunded','captured':True,'amount_refunded':10000,'refund_status':'full'}
        events.append({'event':'refund.processed','payload':{'refund':{'entity':{'id':rid,'payment_id':pid}}}})
    async def fetch(method,path,payload=None):
        calls.append(path)
        if path.startswith('/refunds/'):return refunds[path.split('/')[-1]]
        pid=path.split('/')[2]
        if '/refunds?' in path:
            return {'count':1,'items':[row for row in refunds.values() if row['payment_id']==pid]}
        return payments[pid]
    monkeypatch.setattr(billing,'_razorpay_async',fetch)
    eid=uuid4().hex
    with ThreadPoolExecutor(max_workers=2) as executor:
        responses=list(executor.map(lambda event:signed(client,event,eid),events))
    assert [r.status_code for r in responses]==[200,200]
    assert sum(bool(r.json().get('duplicate')) for r in responses)==1
    assert len(calls)==3
    assert sum(database[1].execute("SELECT plan_status='refunded' FROM users WHERE id=%s",(user,)).fetchone()[0] for user in users)==1
