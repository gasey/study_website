import asyncio, hashlib, hmac, json
from datetime import datetime, timezone
from urllib.request import Request as UrlRequest, urlopen
from urllib.error import HTTPError, URLError
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from ..config import settings
from ..db import cursor
from ..deps import require_account

router = APIRouter(prefix="/api/billing", tags=["billing"])
PLANS = {"monthly": (9900, 1), "six_months": (44900, 6), "yearly": (79900, 12)}

class CheckoutRequest(BaseModel):
    period: str = Field(pattern="^(monthly|six_months|yearly)$")

class VerifyRequest(BaseModel):
    razorpay_payment_id: str
    razorpay_subscription_id: str
    razorpay_signature: str

def enabled():
    return bool(settings.razorpay_key_id and settings.razorpay_key_secret and settings.razorpay_webhook_secret)

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
    async with cursor() as cur:
        await cur.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", ("razorpay:pro:"+period,))
        await cur.execute("SELECT razorpay_plan_id FROM billing_plan_refs WHERE plan_code='pro' AND billing_period=%s", (period,))
        row = await cur.fetchone()
        if row: return row["razorpay_plan_id"]
        plan_period, interval = ("monthly", 1) if months == 1 else (("monthly", 6) if months == 6 else ("yearly", 1))
        plan = await _razorpay_async("POST", "/plans", {"period":plan_period, "interval":interval,
                    "item":{"name":f"India Study Map Pro · {months} month(s)","amount":amount,"currency":"INR"},
                    "notes":{"plan_code":"pro","billing_period":period}})
        await cur.execute("INSERT INTO billing_plan_refs(plan_code,billing_period,razorpay_plan_id,amount_paise) VALUES ('pro',%s,%s,%s) ON CONFLICT (plan_code,billing_period) DO NOTHING", (period,plan["id"],amount))
        return plan["id"]

@router.get("/config")
async def billing_config():
    return {"enabled":enabled(),"plans":[{"code":"pro","period":p,"amount_paise":a} for p,(a,_) in PLANS.items()],
            "class_plan_available":False}

@router.get("/me")
async def billing_me(user_id: Annotated[str, Depends(require_account)]):
    async with cursor() as cur:
        await cur.execute("SELECT email,CASE WHEN account_has_pro(id) THEN 'pro' ELSE 'free' END AS plan_code,CASE WHEN EXISTS(SELECT 1 FROM reward_redemptions rr WHERE rr.user_id=users.id AND rr.starts_at<=now() AND rr.ends_at>now()) THEN 'rewarded' WHEN NOT account_has_pro(id) THEN 'free' ELSE plan_status END AS plan_status,trial_ends_at,plan_ends_at,razorpay_subscription_id FROM users WHERE id=%s", (user_id,))
        user=await cur.fetchone()
        await cur.execute("SELECT plan_code,billing_period,status,current_start,current_end,created_at FROM billing_subscriptions WHERE user_id=%s ORDER BY created_at DESC LIMIT 1", (user_id,))
        sub=await cur.fetchone()
    async with cursor() as cur:
        await cur.execute('SELECT starts_at,ends_at FROM reward_redemptions WHERE user_id=%s AND ends_at>now() ORDER BY starts_at',(user_id,))
        rewards=await cur.fetchall()
    return {**user,"subscription":sub,"enabled":enabled(),"reward_access":rewards}

@router.post("/checkout")
async def checkout(body: CheckoutRequest, request: Request, user_id: Annotated[str, Depends(require_account)]):
    origin=request.headers.get("origin")
    if origin and origin.rstrip("/") != settings.public_origin.rstrip("/"): raise HTTPException(403,"Request origin is not allowed")
    if not enabled(): raise HTTPException(503,"Razorpay checkout is not configured yet")
    amount,months=PLANS[body.period]
    plan_id=await _get_or_create_plan(body.period,amount,months)
    async with cursor() as cur:
        await cur.execute("SELECT email,razorpay_subscription_id FROM users WHERE id=%s", (user_id,))
        user=await cur.fetchone()
    if user.get("razorpay_subscription_id"):
        raise HTTPException(409,"Manage or cancel your current subscription before changing plans")
    sub=await _razorpay_async("POST","/subscriptions",{"plan_id":plan_id,"total_count":120,"quantity":1,"customer_notify":0,
             "notes":{"user_id":user_id,"plan_code":"pro","billing_period":body.period}})
    async with cursor() as cur:
        await cur.execute("INSERT INTO billing_subscriptions(user_id,plan_code,billing_period,amount_paise,razorpay_plan_id,razorpay_subscription_id,status) VALUES (%s,'pro',%s,%s,%s,%s,%s)",
                          (user_id,body.period,amount,plan_id,sub["id"],sub.get("status","created")))
        await cur.execute("UPDATE users SET razorpay_subscription_id=%s WHERE id=%s",(sub["id"],user_id))
    return {"key_id":settings.razorpay_key_id,"subscription_id":sub["id"],"email":user["email"],"amount_paise":amount,"period":body.period,
            "name":"India Study Map Pro","description":f"Pro subscription · {body.period.replace('_',' ')}"}

@router.post("/verify")
async def verify(body: VerifyRequest, user_id: Annotated[str, Depends(require_account)]):
    if not enabled(): raise HTTPException(503,"Razorpay checkout is not configured yet")
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

async def _apply_subscription(sub):
    sid=sub.get("id")
    if not sid: return
    status=sub.get("status","created")
    start=datetime.fromtimestamp(sub["current_start"],timezone.utc) if sub.get("current_start") else None
    end=datetime.fromtimestamp(sub["current_end"],timezone.utc) if sub.get("current_end") else None
    async with cursor() as cur:
        await cur.execute("SELECT user_id FROM billing_subscriptions WHERE razorpay_subscription_id=%s",(sid,))
        row=await cur.fetchone()
        if not row: return
        await cur.execute("UPDATE billing_subscriptions SET status=%s,current_start=%s,current_end=%s,updated_at=now() WHERE razorpay_subscription_id=%s",(status,start,end,sid))
        active=status in ("active","authenticated")
        await cur.execute("UPDATE users SET plan_code=%s,plan_status=%s,plan_ends_at=%s WHERE id=%s",
                          ("pro" if active else "free",status,end,row["user_id"]))

@router.post("/webhook")
async def webhook(request: Request):
    raw=await request.body()
    signature=request.headers.get("x-razorpay-signature","")
    if not settings.razorpay_webhook_secret: raise HTTPException(503,"Webhook is not configured")
    expected=hmac.new(settings.razorpay_webhook_secret.encode(),raw,hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected,signature): raise HTTPException(400,"Invalid webhook signature")
    event=json.loads(raw)
    event_id=request.headers.get("x-razorpay-event-id") or hashlib.sha256(raw).hexdigest()
    async with cursor() as cur:
        await cur.execute("INSERT INTO billing_webhook_events(event_key,event_name) VALUES (%s,%s) ON CONFLICT DO NOTHING RETURNING event_key",(event_id,event.get("event","unknown")))
        if not await cur.fetchone(): return {"received":True,"duplicate":True}
    entity=event.get("payload",{}).get("subscription",{}).get("entity")
    if entity: await _apply_subscription(entity)
    payment=event.get("payload",{}).get("payment",{}).get("entity")
    if payment and payment.get("subscription_id"):
        async with cursor() as cur:
            await cur.execute("SELECT user_id FROM billing_subscriptions WHERE razorpay_subscription_id=%s",(payment["subscription_id"],))
            user=await cur.fetchone()
            if user:
                await cur.execute("INSERT INTO billing_payments(razorpay_payment_id,razorpay_subscription_id,user_id,amount_paise,currency,status,paid_at) VALUES (%s,%s,%s,%s,%s,%s,CASE WHEN %s='captured' THEN now() END) ON CONFLICT DO NOTHING",
                    (payment["id"],payment["subscription_id"],user["user_id"],payment.get("amount",0),payment.get("currency","INR"),payment.get("status","created"),payment.get("status")))
    return {"received":True}

@router.post("/cancel")
async def cancel(user_id: Annotated[str, Depends(require_account)]):
    if not enabled(): raise HTTPException(503,"Razorpay is not configured")
    async with cursor() as cur:
        await cur.execute("SELECT razorpay_subscription_id FROM users WHERE id=%s",(user_id,)); row=await cur.fetchone()
    if not row or not row["razorpay_subscription_id"]: raise HTTPException(404,"No subscription to cancel")
    result=await _razorpay_async("POST",f"/subscriptions/{row['razorpay_subscription_id']}/cancel",{"cancel_at_cycle_end":1})
    await _apply_subscription(result)
    return {"cancelled":True,"status":result.get("status")}
