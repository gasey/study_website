import asyncio, hashlib, hmac, json
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
        await cur.execute('SELECT starts_at,ends_at,days FROM billing_access_grants WHERE user_id=%s AND ends_at>now() ORDER BY starts_at',(user_id,))
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
    await cur.execute("SELECT user_id FROM billing_subscriptions WHERE razorpay_subscription_id=%s FOR UPDATE",(sid,))
    row=await cur.fetchone()
    if not row: return
    await cur.execute("UPDATE billing_subscriptions SET status=%s,current_start=%s,current_end=%s,updated_at=now() WHERE razorpay_subscription_id=%s",(status,start,end,sid))
    # A mandate authentication is not an active paid subscription period.
    active=status=="active" and end is not None and end>datetime.now(timezone.utc)
    # A delayed event for an older subscription cannot overwrite a newer link.
    await cur.execute("UPDATE users SET plan_code=%s,plan_status=%s,plan_ends_at=%s WHERE id=%s AND razorpay_subscription_id=%s",
        ("pro" if active else "free",status,end,row["user_id"],sid))

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
    except (ValueError,TypeError):
        raise HTTPException(400,"Invalid webhook payload")
    event_id=request.headers.get("x-razorpay-event-id") or hashlib.sha256(raw).hexdigest()
    entity=event.get("payload",{}).get("subscription",{}).get("entity")
    payment=event.get("payload",{}).get("payment",{}).get("entity")
    sid=(entity or {}).get('id') or (payment or {}).get('subscription_id')
    # Read the provider's current state to tolerate out-of-order deliveries.
    # Unrecognised subscriptions cannot grant access or cause provider lookups.
    async with cursor() as cur:
        if sid:
            # Serialize each provider subscription before reading its current
            # state, so delayed concurrent deliveries cannot reverse it.
            await cur.execute('SELECT pg_advisory_xact_lock(hashtext(%s))',('billing-subscription:'+sid,))
        await cur.execute('SELECT 1 FROM billing_webhook_events WHERE event_key=%s',(event_id,))
        if await cur.fetchone():return {"received":True,"duplicate":True}
        current=None
        if sid:
            await cur.execute("SELECT 1 FROM billing_subscriptions WHERE razorpay_subscription_id=%s",(sid,))
            if await cur.fetchone():current=await _razorpay_async("GET",f"/subscriptions/{sid}")
        # Receipt and effects commit together; failures remain retryable.
        await cur.execute("INSERT INTO billing_webhook_events(event_key,event_name) VALUES (%s,%s) ON CONFLICT DO NOTHING RETURNING event_key",(event_id,event.get("event","unknown")))
        if not await cur.fetchone():return {"received":True,"duplicate":True}
        if current:await _apply_subscription(current,cur)
        if payment and sid:
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
        await cur.execute('SELECT amount_paise,status,billing_period FROM billing_subscriptions WHERE user_id=%s ORDER BY id DESC LIMIT 1',(user['id'],))
        user['subscription']=await cur.fetchone()
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
