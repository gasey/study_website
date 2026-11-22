import asyncio, hashlib, hmac, json, re
from datetime import datetime, timezone
from urllib.request import Request as UrlRequest, urlopen
from urllib.error import HTTPError, URLError
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from pydantic import BaseModel, Field
from psycopg.types.json import Jsonb

from ..config import settings
from ..db import cursor
from ..deps import require_account
from ..services.account_identity import account_session
from ..services.review_identity import Actor, identity, require_role

router = APIRouter(prefix="/api/billing", tags=["billing"])
PLANS = {"monthly": (10000, 1)}

class CheckoutRequest(BaseModel):
    period: str = Field(pattern="^monthly$")

class VerifyRequest(BaseModel):
    razorpay_payment_id: str
    razorpay_subscription_id: str
    razorpay_signature: str

def credentials_ready():
    return bool(settings.razorpay_key_id and settings.razorpay_key_secret and settings.razorpay_webhook_secret)

def enabled():
    return settings.razorpay_checkout_enabled and credentials_ready()

def _razorpay(method: str, path: str, payload=None):
    body = json.dumps(payload).encode() if payload is not None else None
    req = UrlRequest("https://api.razorpay.com/v1" + path, data=body, method=method,
                     headers={"Authorization": "Basic " + __import__('base64').b64encode(f"{settings.razorpay_key_id}:{settings.razorpay_key_secret}".encode()).decode(),
                              "Content-Type": "application/json"})
    try:
        with urlopen(req, timeout=15) as res: return json.loads(res.read())
    except (HTTPError, URLError, TimeoutError) as exc:
        raise HTTPException(502, "Razorpay could not complete the request. Please try again.") from exc

async def _razorpay_async(method, path, payload=None):
    return await asyncio.to_thread(_razorpay, method, path, payload)

async def _get_or_create_plan(period: str, amount: int, months: int):
    # Prices identify immutable provider-plan versions; retain older references.
    ref_code=f"pro:inr:{amount}:v1"
    async with cursor() as cur:
        await cur.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", ("razorpay:pro:"+period,))
        await cur.execute("SELECT razorpay_plan_id,amount_paise FROM billing_plan_refs WHERE billing_period=%s AND (plan_code=%s OR (plan_code='pro' AND amount_paise=%s)) ORDER BY (plan_code=%s) DESC LIMIT 1", (period,ref_code,amount,ref_code))
        row = await cur.fetchone()
        if row:
            if row['amount_paise']!=amount:raise HTTPException(503,"This plan needs a pricing update before checkout")
            return row["razorpay_plan_id"]
        plan_period, interval = ("monthly", 1) if months == 1 else (("monthly", 6) if months == 6 else ("yearly", 1))
        plan = await _razorpay_async("POST", "/plans", {"period":plan_period, "interval":interval,
                    "item":{"name":f"Finna Pro · {months} month(s)","amount":amount,"currency":"INR"},
                    "notes":{"plan_code":"pro","billing_period":period,"price_version":ref_code}})
        await cur.execute("INSERT INTO billing_plan_refs(plan_code,billing_period,razorpay_plan_id,amount_paise) VALUES (%s,%s,%s,%s)", (ref_code,period,plan["id"],amount))
        return plan["id"]

@router.get("/config")
async def billing_config(request: Request):
    session=await account_session(request)
    amount=await _account_amount(session['user_id']) if session else PLANS['monthly'][0]
    return {"enabled":enabled(),"plans":[{"code":"pro","period":"monthly","amount_paise":amount}],
            "class_plan_available":False}

async def _account_amount(user_id, cur=None):
    if cur is None:
        async with cursor() as transaction:return await _account_amount(user_id,transaction)
    await cur.execute('SELECT amount_paise FROM billing_account_rates WHERE user_id=%s',(user_id,))
    row=await cur.fetchone()
    return row['amount_paise'] if row else PLANS['monthly'][0]

@router.get("/me")
async def billing_me(user_id: Annotated[str, Depends(require_account)]):
    async with cursor() as cur:
        await cur.execute("SELECT email,CASE WHEN account_has_pro(id) THEN 'pro' ELSE 'free' END AS plan_code,CASE WHEN EXISTS(SELECT 1 FROM reward_redemptions rr WHERE rr.user_id=users.id AND rr.starts_at<=now() AND rr.ends_at>now()) THEN 'rewarded' WHEN EXISTS(SELECT 1 FROM billing_access_grants bg WHERE bg.user_id=users.id AND bg.starts_at<=now() AND bg.ends_at>now()) THEN 'granted' WHEN NOT account_has_pro(id) THEN 'free' ELSE plan_status END AS plan_status,trial_ends_at,plan_ends_at,razorpay_subscription_id FROM users WHERE id=%s", (user_id,))
        user=await cur.fetchone()
        await cur.execute("SELECT plan_code,billing_period,status,current_start,current_end,created_at FROM billing_subscriptions WHERE user_id=%s ORDER BY created_at DESC LIMIT 1", (user_id,))
        sub=await cur.fetchone()
    async with cursor() as cur:
        await cur.execute('SELECT starts_at,ends_at FROM reward_redemptions WHERE user_id=%s AND ends_at>now() ORDER BY starts_at',(user_id,))
        rewards=await cur.fetchall()
    async with cursor() as cur:
        await cur.execute('SELECT starts_at,ends_at,days,source FROM billing_access_grants WHERE user_id=%s AND ends_at>now() ORDER BY starts_at',(user_id,))
        grants=await cur.fetchall()
    return {**user,"subscription":sub,"enabled":enabled(),"reward_access":rewards,"granted_access":grants}

@router.post("/checkout")
async def checkout(body: CheckoutRequest, request: Request, user_id: Annotated[str, Depends(require_account)]):
    origin=request.headers.get("origin")
    if origin and origin.rstrip("/") != settings.public_origin.rstrip("/"): raise HTTPException(403,"Request origin is not allowed")
    if not enabled(): raise HTTPException(503,"Razorpay checkout is not configured yet")
    _,months=PLANS[body.period]
    amount=await _account_amount(user_id)
    plan_id=await _get_or_create_plan(body.period,amount,months)
    async with cursor() as cur:
        # Repeated clicks and reopening checkout must share one pending mandate.
        await cur.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", ('billing-checkout:'+user_id,))
        if await _account_amount(user_id,cur)!=amount:raise HTTPException(409,"Your price changed. Refresh before checkout")
        await cur.execute("SELECT email,razorpay_subscription_id FROM users WHERE id=%s", (user_id,))
        user=await cur.fetchone()
        sub=None
        if user.get("razorpay_subscription_id"):
            sid=user['razorpay_subscription_id']
            await cur.execute("SELECT billing_period,amount_paise FROM billing_subscriptions WHERE user_id=%s AND razorpay_subscription_id=%s",(user_id,sid))
            previous=await cur.fetchone()
            if not previous:raise HTTPException(409,"Your subscription needs support before starting another checkout")
            current=await _razorpay_async("GET",f"/subscriptions/{sid}")
            if current.get('id')!=sid:raise HTTPException(502,"Razorpay returned an unexpected subscription")
            if current.get('status')=='created' and previous['billing_period']==body.period and previous['amount_paise']==amount:
                sub=current
            elif current.get('status') not in {'cancelled','completed','expired'}:
                raise HTTPException(409,"Manage or cancel your current subscription before changing plans")
        if sub is None:
            # Razorpay limits a subscription to 100 years, including yearly plans.
            sub=await _razorpay_async("POST","/subscriptions",{"plan_id":plan_id,"total_count":min(120,1200//months),"quantity":1,"customer_notify":0,
                     "notes":{"user_id":user_id,"plan_code":"pro","billing_period":body.period}})
            await cur.execute("INSERT INTO billing_subscriptions(user_id,plan_code,billing_period,amount_paise,razorpay_plan_id,razorpay_subscription_id,status) VALUES (%s,'pro',%s,%s,%s,%s,%s)",
                              (user_id,body.period,amount,plan_id,sub["id"],sub.get("status","created")))
            await cur.execute("UPDATE users SET razorpay_subscription_id=%s WHERE id=%s",(sub["id"],user_id))
    return {"key_id":settings.razorpay_key_id,"subscription_id":sub["id"],"email":user["email"],"amount_paise":amount,"period":body.period,
            "name":"Finna Pro","description":f"Pro subscription · {body.period.replace('_',' ')}"}

@router.post("/verify")
async def verify(body: VerifyRequest, user_id: Annotated[str, Depends(require_account)]):
    if not credentials_ready(): raise HTTPException(503,"Razorpay checkout is not configured yet")
    async with cursor() as cur:
        await cur.execute("SELECT razorpay_subscription_id FROM billing_subscriptions WHERE user_id=%s AND razorpay_subscription_id=%s", (user_id,body.razorpay_subscription_id))
        row=await cur.fetchone()
    if not row: raise HTTPException(403,"Subscription does not belong to this account")
    expected=hmac.new(settings.razorpay_key_secret.encode(),f"{body.razorpay_payment_id}|{row['razorpay_subscription_id']}".encode(),hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected,body.razorpay_signature): raise HTTPException(400,"Payment verification failed")
    # Verify with Razorpay itself before granting access. Webhook remains authoritative.
    sub=await _razorpay_async("GET",f"/subscriptions/{row['razorpay_subscription_id']}")
    if not isinstance(sub,dict) or sub.get('id')!=row['razorpay_subscription_id']:
        raise HTTPException(502,"Razorpay returned an unexpected subscription")
    await _apply_subscription(sub)
    return {"verified":True,"status":sub.get("status")}

async def _apply_subscription(sub, cur=None):
    sid=sub.get("id")
    if not sid: return
    if cur is None:
        async with cursor() as transaction:
            return await _apply_subscription(sub, transaction)
    status=sub.get("status","created")
    start=datetime.fromtimestamp(sub["current_start"],timezone.utc) if sub.get("current_start") else None
    end=datetime.fromtimestamp(sub["current_end"],timezone.utc) if sub.get("current_end") else None
    await cur.execute("SELECT user_id,access_ended_at FROM billing_subscriptions WHERE razorpay_subscription_id=%s FOR UPDATE",(sid,))
    row=await cur.fetchone()
    if not row: return
    await cur.execute("UPDATE billing_subscriptions SET status=%s,current_start=%s,current_end=%s,updated_at=now() WHERE razorpay_subscription_id=%s",(status,start,end,sid))
    # A mandate authentication is not an active paid subscription period.
    active=(not row['access_ended_at'] and status=="active" and end is not None and end>datetime.now(timezone.utc))
    # A delayed event for an older subscription cannot overwrite a newer link.
    effective_status='refunded' if row['access_ended_at'] else status
    effective_end=row['access_ended_at'] or end
    await cur.execute("UPDATE users SET plan_code=%s,plan_status=%s,plan_ends_at=%s WHERE id=%s AND razorpay_subscription_id=%s",
        ("pro" if active else "free",effective_status,effective_end,row["user_id"],sid))

async def _reconcile_refund(refund_id, payment_id, cur):
    """Record Razorpay's current refund/payment state for a known payment only."""
    await cur.execute("SELECT amount_paise,currency,user_id,razorpay_subscription_id FROM billing_payments WHERE razorpay_payment_id=%s FOR UPDATE",(payment_id,))
    payment_row=await cur.fetchone()
    if not payment_row:
        # Refund delivery can precede the charge delivery. Do not permanently
        # acknowledge it before the owned payment record is available.
        raise HTTPException(503,"The payment must be reconciled before its refund")
    refund=await _razorpay_async("GET",f"/refunds/{refund_id}")
    payment=await _razorpay_async("GET",f"/payments/{payment_id}")
    if (not isinstance(refund,dict) or not isinstance(payment,dict)
        or refund.get('id')!=refund_id or refund.get('payment_id')!=payment_id or payment.get('id')!=payment_id):
        raise HTTPException(502,"Razorpay returned a refund for a different payment")
    status=refund.get('status')
    amount=refund.get('amount')
    currency=refund.get('currency')
    created=refund.get('created_at')
    total_refunded=payment.get('amount_refunded')
    refund_status=payment.get('refund_status')
    if (not isinstance(status,str) or status not in {'pending','processed','failed'} or isinstance(amount,bool) or not isinstance(amount,int)
        or amount<=0 or amount>payment_row['amount_paise'] or currency!=payment_row['currency']
        or type(payment.get('amount')) is not int or payment['amount']!=payment_row['amount_paise']
        or payment.get('currency')!=payment_row['currency']
        or not isinstance(payment.get('status'),str) or payment['status'] not in {'captured','refunded'} or payment.get('captured') is not True
        or isinstance(total_refunded,bool) or not isinstance(total_refunded,int)
        or total_refunded<0 or total_refunded>payment_row['amount_paise']
        or (refund_status is not None and (not isinstance(refund_status,str) or refund_status not in {'partial','full'}))
        or (refund_status=='full' and total_refunded!=payment_row['amount_paise'])
        or (refund_status=='partial' and not 0<total_refunded<payment_row['amount_paise'])
        or (refund_status is None and total_refunded!=0)
        or (status=='processed' and total_refunded<amount)
        or isinstance(created,bool) or not isinstance(created,int)):
        raise HTTPException(502,"Razorpay returned invalid refund details")
    try:created_at=datetime.fromtimestamp(created,timezone.utc)
    except (ValueError,OverflowError,OSError):
        raise HTTPException(502,"Razorpay returned an invalid refund timestamp") from None
    await cur.execute("SELECT razorpay_payment_id,amount_paise,currency,provider_created_at,status FROM billing_refunds WHERE razorpay_refund_id=%s FOR UPDATE",(refund_id,))
    previous=await cur.fetchone()
    if previous and (previous['razorpay_payment_id']!=payment_id or previous['amount_paise']!=amount
        or previous['currency']!=currency or previous['provider_created_at']!=created_at
        or (previous['status']=='processed' and status!='processed')):
        raise HTTPException(502,"Razorpay returned inconsistent refund history")
    full_processed=False
    if status=='processed' and refund_status=='full':
        full_processed=await _fully_processed_refunds(payment_id,payment_row,refund)
    await cur.execute("""UPDATE billing_payments
      SET status=%s,amount_refunded_paise=%s,refund_status=%s,updated_at=now()
      WHERE razorpay_payment_id=%s""",
      (payment.get('status','captured'),total_refunded,refund_status,payment_id))
    await cur.execute("""INSERT INTO billing_refunds
      (razorpay_refund_id,razorpay_payment_id,amount_paise,currency,status,provider_created_at)
      VALUES(%s,%s,%s,%s,%s,%s)
      ON CONFLICT(razorpay_refund_id) DO UPDATE SET
        amount_paise=EXCLUDED.amount_paise,currency=EXCLUDED.currency,
        status=EXCLUDED.status,provider_created_at=EXCLUDED.provider_created_at,updated_at=now()""",
      (refund_id,payment_id,amount,currency,status,created_at))
    if full_processed:
        # Apply the owner's full-refund rule only after current provider state is
        # confirmed. Preserve earned/owner grants; renewal cancellation stays a
        # separate provider operation and is not attempted from a webhook.
        sid=payment_row['razorpay_subscription_id']
        await cur.execute("""UPDATE billing_subscriptions SET
          access_ended_at=COALESCE(access_ended_at,now()),access_end_reason='full_refund',updated_at=now()
          WHERE razorpay_subscription_id=%s""",(sid,))
        await cur.execute("""UPDATE users SET plan_code='free',plan_status='refunded',plan_ends_at=now()
          WHERE id=%s AND razorpay_subscription_id=%s""",(payment_row['user_id'],sid))

async def _fully_processed_refunds(payment_id, payment_row, current_refund):
    """Bounded read: a full aggregate can include refunds still pending."""
    seen=set();processed=0;current_seen=False
    for page in range(10):
        collection=await _razorpay_async("GET",f"/payments/{payment_id}/refunds?count=100&skip={page*100}")
        items=collection.get('items') if isinstance(collection,dict) else None
        if (not isinstance(items,list) or len(items)>100 or type(collection.get('count')) is not int
            or collection['count']!=len(items)):
            raise HTTPException(502,"Razorpay returned an invalid refund list")
        for item in items:
            if (not isinstance(item,dict) or not _provider_id(item.get('id'),'rfnd')
                or item['id'] in seen or item.get('payment_id')!=payment_id
                or item.get('currency')!=payment_row['currency']
                or type(item.get('amount')) is not int or not 0<item['amount']<=payment_row['amount_paise']
                or not isinstance(item.get('status'),str) or item['status'] not in {'pending','processed','failed'}):
                raise HTTPException(502,"Razorpay returned inconsistent payment refunds")
            seen.add(item['id'])
            if item['id']==current_refund['id']:
                if any(item.get(key)!=current_refund.get(key) for key in ('amount','status','created_at')):
                    raise HTTPException(502,"Razorpay refund state changed during reconciliation")
                current_seen=True
            if item['status']=='processed':processed+=item['amount']
        if processed>payment_row['amount_paise']:
            raise HTTPException(502,"Razorpay returned excessive processed refunds")
        if len(items)<100:
            if not current_seen:raise HTTPException(502,"Razorpay omitted the current refund")
            return processed==payment_row['amount_paise']
    raise HTTPException(503,"This payment needs manual refund reconciliation")

def _provider_id(value, prefix):
    return isinstance(value,str) and re.fullmatch(prefix+r'_[A-Za-z0-9_-]{1,100}',value) is not None

@router.post("/webhook")
async def webhook(request: Request):
    raw=await request.body()
    signature=request.headers.get("x-razorpay-signature","")
    if not settings.razorpay_webhook_secret: raise HTTPException(503,"Webhook is not configured")
    expected=hmac.new(settings.razorpay_webhook_secret.encode(),raw,hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected,signature): raise HTTPException(400,"Invalid webhook signature")
    try:
        event=json.loads(raw)
        if not isinstance(event,dict) or not isinstance(event.get('payload',{}),dict):raise ValueError()
        if not isinstance(event.get('event','unknown'),str):raise ValueError()
        for name in ('subscription','payment','refund'):
            wrapper=event.get('payload',{}).get(name,{})
            if not isinstance(wrapper,dict) or not isinstance(wrapper.get('entity',{}),dict):raise ValueError()
    except (ValueError,TypeError):
        raise HTTPException(400,"Invalid webhook payload")
    event_id=request.headers.get("x-razorpay-event-id") or hashlib.sha256(raw).hexdigest()
    entity=event.get("payload",{}).get("subscription",{}).get("entity")
    payment=event.get("payload",{}).get("payment",{}).get("entity")
    refund=event.get("payload",{}).get("refund",{}).get("entity")
    sid=(entity or {}).get('id') or (payment or {}).get('subscription_id')
    refund_id=(refund or {}).get('id')
    payment_id=(refund or {}).get('payment_id') or (payment or {}).get('id')
    if event.get('event','').startswith('refund.') and not refund:
        raise HTTPException(400,"Missing webhook refund details")
    if (sid is not None and not _provider_id(sid,'sub')) or (refund is not None and
        (not _provider_id(refund_id,'rfnd') or not _provider_id(payment_id,'pay'))):
        raise HTTPException(400,"Invalid webhook identifiers")
    if refund_id and payment and payment.get('id')!=payment_id:
        raise HTTPException(400,"Conflicting webhook payment identifiers")
    # Read the provider's current state to tolerate out-of-order deliveries.
    # Unrecognised subscriptions cannot grant access or cause provider lookups.
    async with cursor() as cur:
        if sid and not refund_id:
            # Serialize each provider subscription before reading its current
            # state, so delayed concurrent deliveries cannot reverse it.
            await cur.execute('SELECT pg_advisory_xact_lock(hashtext(%s))',('billing-subscription:'+sid,))
        if refund_id and payment_id:
            await cur.execute('SELECT pg_advisory_xact_lock(hashtext(%s))',('billing-payment:'+payment_id,))
        await cur.execute('SELECT 1 FROM billing_webhook_events WHERE event_key=%s',(event_id,))
        if await cur.fetchone():return {"received":True,"duplicate":True}
        # Reserve the event before applying effects, including when simultaneous
        # deliveries disagree about the payment ID. The receipt rolls back on failure.
        await cur.execute("INSERT INTO billing_webhook_events(event_key,event_name) VALUES (%s,%s) ON CONFLICT DO NOTHING RETURNING event_key",(event_id,event.get("event","unknown")))
        if not await cur.fetchone():return {"received":True,"duplicate":True}
        current=None
        if sid and not refund_id:
            await cur.execute("SELECT 1 FROM billing_subscriptions WHERE razorpay_subscription_id=%s",(sid,))
            if await cur.fetchone():
                current=await _razorpay_async("GET",f"/subscriptions/{sid}")
                if not isinstance(current,dict) or current.get('id')!=sid:
                    raise HTTPException(502,"Razorpay returned an unexpected subscription")
        if refund_id and payment_id:
            await _reconcile_refund(refund_id,payment_id,cur)
        if current and not refund_id:await _apply_subscription(current,cur)
        if payment and sid and not refund_id:
            await cur.execute("SELECT user_id FROM billing_subscriptions WHERE razorpay_subscription_id=%s",(sid,))
            user=await cur.fetchone()
            if user:
                await cur.execute("INSERT INTO billing_payments(razorpay_payment_id,razorpay_subscription_id,user_id,amount_paise,currency,status,paid_at) VALUES (%s,%s,%s,%s,%s,%s,CASE WHEN %s='captured' THEN now() END) ON CONFLICT DO NOTHING",
                    (payment["id"],sid,user["user_id"],payment.get("amount",0),payment.get("currency","INR"),payment.get("status","created"),payment.get("status")))
    return {"received":True}

@router.post("/cancel")
async def cancel(user_id: Annotated[str, Depends(require_account)]):
    if not credentials_ready(): raise HTTPException(503,"Razorpay is not configured")
    async with cursor() as cur:
        await cur.execute("SELECT razorpay_subscription_id FROM users WHERE id=%s",(user_id,)); row=await cur.fetchone()
    if not row or not row["razorpay_subscription_id"]: raise HTTPException(404,"No subscription to cancel")
    result=await _razorpay_async("POST",f"/subscriptions/{row['razorpay_subscription_id']}/cancel",{"cancel_at_cycle_end":1})
    if not isinstance(result,dict) or result.get('id')!=row['razorpay_subscription_id']:
        raise HTTPException(502,"Razorpay returned an unexpected subscription")
    await _apply_subscription(result)
    return {"cancelled":True,"status":result.get("status")}

# These controls use the existing staff session, CSRF, MFA and global-owner grant.
class RateUpdate(BaseModel):
    amount_paise: Literal[5000,10000]
    expected_amount_paise: Literal[5000,10000]

class AccessGrant(BaseModel):
    days: int = Field(ge=1,le=3650)
    idempotency_key: str = Field(min_length=16,max_length=80,pattern=r'^[A-Za-z0-9_-]+$')

Staff = Annotated[Actor,Depends(identity)]

@router.get('/admin/account')
async def admin_account(actor:Staff,email:str=Query(min_length=3,max_length=254)):
    async with cursor() as cur:
        await require_role(cur,actor.id,roles=('owner',))
        await cur.execute('SELECT id,email,handle,plan_ends_at,trial_ends_at FROM users WHERE lower(email)=%s',(email.strip().lower(),))
        user=await cur.fetchone()
        if not user:raise HTTPException(404,'No registered account has that email')
        user['amount_paise']=await _account_amount(user['id'],cur)
        await cur.execute('SELECT days,starts_at,ends_at,created_at FROM billing_access_grants WHERE user_id=%s ORDER BY id DESC LIMIT 20',(user['id'],))
        user['granted_access']=await cur.fetchall()
        await cur.execute('SELECT amount_paise,status,billing_period,access_ended_at,access_end_reason FROM billing_subscriptions WHERE user_id=%s ORDER BY id DESC LIMIT 1',(user['id'],))
        user['subscription']=await cur.fetchone()
        await cur.execute('''SELECT razorpay_payment_id,razorpay_subscription_id,amount_paise,
            amount_refunded_paise,currency,status,refund_status,paid_at,created_at
            FROM billing_payments WHERE user_id=%s ORDER BY created_at DESC LIMIT 20''',(user['id'],))
        user['payments']=await cur.fetchall()
        await cur.execute('''SELECT r.razorpay_refund_id,r.razorpay_payment_id,r.amount_paise,
            r.currency,r.status,r.provider_created_at,r.created_at,r.updated_at
            FROM billing_refunds r JOIN billing_payments p USING(razorpay_payment_id)
            WHERE p.user_id=%s ORDER BY r.provider_created_at DESC NULLS LAST,r.created_at DESC LIMIT 50''',(user['id'],))
        user['refunds']=await cur.fetchall()
        return user

@router.post('/admin/account/{user_id}/rate')
async def admin_rate(user_id:str,body:RateUpdate,actor:Staff):
    async with cursor() as cur:
        await require_role(cur,actor.id,roles=('owner',))
        await cur.execute('SELECT pg_advisory_xact_lock(hashtext(%s))',('billing-checkout:'+user_id,))
        await cur.execute('SELECT 1 FROM users WHERE id=%s AND email IS NOT NULL',(user_id,))
        if not await cur.fetchone():raise HTTPException(404,'Account not found')
        old=await _account_amount(user_id,cur)
        if old!=body.expected_amount_paise:raise HTTPException(409,'Account price changed. Reload before saving')
        await cur.execute('INSERT INTO billing_account_rates(user_id,amount_paise,updated_by) VALUES(%s,%s,%s) ON CONFLICT(user_id) DO UPDATE SET amount_paise=EXCLUDED.amount_paise,updated_by=EXCLUDED.updated_by,updated_at=now()', (user_id,body.amount_paise,actor.id))
        await cur.execute("INSERT INTO account_security_events(user_id,action,detail) VALUES(%s,'owner_billing_rate_changed',%s)",(user_id,Jsonb({'actor_id':actor.id,'before_paise':old,'amount_paise':body.amount_paise})))
    return {'saved':True,'amount_paise':body.amount_paise}

@router.post('/admin/account/{user_id}/days')
async def admin_days(user_id:str,body:AccessGrant,actor:Staff):
    async with cursor() as cur:
        await require_role(cur,actor.id,roles=('owner',))
        await cur.execute('SELECT pg_advisory_xact_lock(hashtext(%s))',('billing-checkout:'+user_id,))
        await cur.execute('SELECT pg_advisory_xact_lock(hashtext(%s))',('rewards:'+user_id,))
        await cur.execute('SELECT days,starts_at,ends_at FROM billing_access_grants WHERE user_id=%s AND idempotency_key=%s',(user_id,body.idempotency_key))
        existing=await cur.fetchone()
        if existing:
            if existing['days']!=body.days:raise HTTPException(409,'This request already granted a different number of days')
            return {'saved':True,**existing}
        await cur.execute('SELECT plan_code,plan_status,plan_ends_at,trial_ends_at,razorpay_subscription_id FROM users WHERE id=%s AND email IS NOT NULL',(user_id,))
        user=await cur.fetchone()
        if not user:raise HTTPException(404,'Account not found')
        if user['plan_code']=='pro' and user['plan_status']=='active' and user['plan_ends_at'] is None and not user['razorpay_subscription_id']:
            raise HTTPException(409,'This account already has unlimited Pro access')
        await cur.execute('''SELECT GREATEST(now(),%s::timestamptz,%s::timestamptz,
          (SELECT max(ends_at) FROM reward_redemptions WHERE user_id=%s),
          (SELECT max(ends_at) FROM billing_access_grants WHERE user_id=%s)) AS starts''',
          (user['plan_ends_at'] if user['plan_code']=='pro' else None,user['trial_ends_at'] if user['plan_status']=='trial' else None,user_id,user_id))
        starts=(await cur.fetchone())['starts']
        await cur.execute('INSERT INTO billing_access_grants(user_id,granted_by,idempotency_key,days,starts_at,ends_at) VALUES(%s,%s,%s,%s,%s,%s+make_interval(days=>%s)) RETURNING days,starts_at,ends_at', (user_id,actor.id,body.idempotency_key,body.days,starts,starts,body.days))
        grant=await cur.fetchone()
        await cur.execute("INSERT INTO account_security_events(user_id,action,detail) VALUES(%s,'owner_pro_days_granted',%s)",(user_id,Jsonb({'actor_id':actor.id,'days':body.days,'starts_at':starts.isoformat(),'ends_at':grant['ends_at'].isoformat()})))
        return {'saved':True,**grant}

# Bulk discounts share the existing billing/account boundaries.
from .bulk_rates import router as bulk_rate_router
router.include_router(bulk_rate_router)
