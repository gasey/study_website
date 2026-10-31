from datetime import datetime, timedelta, timezone
import hashlib, hmac, re, secrets
from psycopg.types.json import Jsonb
from starlette.concurrency import run_in_threadpool
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response
from pydantic import BaseModel, Field, field_validator

from ..config import settings
from ..db import cursor
from ..deps import require_account
from ..services.account_identity import guest_identity, transfer_guest, GUEST_COOKIE, account_session, csrf_token

router = APIRouter(prefix="/api/auth", tags=["account"])
SESSION_COOKIE = "ism_session"
SESSION_DAYS = 30

class Credentials(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(min_length=12, max_length=200)
    @field_validator("email")
    @classmethod
    def valid_email(cls, value):
        value = value.strip().lower()
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value): raise ValueError("Enter a valid email address")
        return value

class LoginCredentials(BaseModel):
    code: str | None = Field(default=None,max_length=64)
    email: str = Field(max_length=254)
    password: str = Field(min_length=1, max_length=200)
    @field_validator("email")
    @classmethod
    def valid_email(cls, value):
        value = value.strip().lower()
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value): raise ValueError("Enter a valid email address")
        return value

def _hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    derived = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1, dklen=64)
    return f"scrypt${salt.hex()}${derived.hex()}"

def _check_password(password: str, encoded: str | None) -> bool:
    if not encoded:
        return False
    try:
        kind, salt, expected = encoded.split("$")
        return kind == "scrypt" and hmac.compare_digest(_hash_password(password, bytes.fromhex(salt)).split("$")[-1], expected)
    except (ValueError, TypeError):
        return False

_DUMMY_HASH = _hash_password('TimingOnlyNotAnAccount123!')

def _set_session(response: Response, token: str) -> None:
    response.set_cookie(SESSION_COOKIE, token, max_age=SESSION_DAYS*86400, httponly=True,
                        secure=settings.public_origin.startswith("https://"), samesite="lax", path="/")

def _same_origin(request: Request) -> None:
    origin = request.headers.get("origin")
    if not origin or origin.rstrip("/") != settings.public_origin.rstrip("/"):
        raise HTTPException(403, "Request origin is not allowed")

async def _new_session(user_id: str, response: Response, mfa_verified=False, cur=None) -> None:
    token=secrets.token_urlsafe(32)
    async def persist(c):
        await c.execute("DELETE FROM auth_sessions WHERE expires_at<now() OR revoked_at IS NOT NULL")
        await c.execute("INSERT INTO auth_sessions(token_hash,user_id,expires_at,mfa_verified_at) VALUES (%s,%s,now()+interval '30 days',CASE WHEN %s THEN now() ELSE NULL END)",(hashlib.sha256(token.encode()).hexdigest(),user_id,mfa_verified))
    if cur is not None:await persist(cur)
    else:
        async with cursor() as c:await persist(c)
    _set_session(response,token)

@router.post("/register")
async def register(body: Credentials, request: Request, response: Response,
                   x_device_id: Annotated[str | None, Header(alias="X-Device-Id")] = None):
    _same_origin(request)
    email = str(body.email).strip().lower()
    await _check_rate(email, request.client.host if request.client else "unknown")
    if not re.search(r"[A-Za-z]", body.password) or not re.search(r"\d", body.password):
        raise HTTPException(422, "Password must include letters and numbers")
    user_id = "usr_" + secrets.token_urlsafe(18)
    handle = "learner-" + secrets.token_hex(4)
    hashed = await run_in_threadpool(_hash_password,body.password)
    try:
        async with cursor() as cur:
            await cur.execute("INSERT INTO users(id,handle,email,password_hash,role,plan_code,plan_status,trial_ends_at) VALUES (%s,%s,%s,%s,'learner','pro','trial',now()+interval '7 days')",
                              (user_id, handle, email, hashed))
    except Exception as exc:
        if "idx_users_email_lower" in str(exc) or "duplicate key" in str(exc).lower():
            raise HTTPException(409, "An account with this email already exists") from exc
        raise
    await _new_session(user_id, response)
    return {"authenticated": True, "email": email, "plan_code": "pro", "plan_status": "trial", "trial_ends_at": (datetime.now(timezone.utc)+timedelta(days=7)).isoformat()}

async def _check_rate(email: str, ip: str) -> None:
    key = hashlib.sha256(f"{email}|{ip}".encode()).hexdigest()
    async with cursor() as cur:
        await cur.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", ("login-rate:"+key,))
        await cur.execute("DELETE FROM auth_login_attempts WHERE attempted_at < now()-interval '1 day'")
        await cur.execute("SELECT count(*)::int AS n FROM auth_login_attempts WHERE identifier_hash=%s AND attempted_at>now()-interval '15 minutes'", (key,))
        if (await cur.fetchone())["n"] >= 10:
            raise HTTPException(429, "Too many attempts. Try again in 15 minutes.")
        await cur.execute("INSERT INTO auth_login_attempts(identifier_hash) VALUES (%s)", (key,))

@router.post("/login")
async def login(body: LoginCredentials, request: Request, response: Response,
                x_device_id: Annotated[str | None, Header(alias="X-Device-Id")] = None):
    _same_origin(request)
    email = str(body.email).strip().lower()
    await _check_rate(email, request.client.host if request.client else "unknown")
    from ..services import mfa
    await mfa.limit('login:'+hashlib.sha256(email.encode()).hexdigest())
    async with cursor() as cur:
        await cur.execute("SELECT id,password_hash,email,plan_code,plan_status,trial_ends_at FROM users WHERE lower(email)=%s FOR UPDATE",(email,))
        user=await cur.fetchone()
        valid=await run_in_threadpool(_check_password,body.password,user['password_hash'] if user else _DUMMY_HASH)
        if not user or not valid:raise HTTPException(401,'Email or password is incorrect')
        await cur.execute('SELECT enabled_at FROM account_mfa WHERE user_id=%s',(user['id'],));factor=await cur.fetchone()
        enabled=bool(factor and factor['enabled_at'])
        if enabled:
            if not body.code:raise HTTPException(401,'Authenticator code required')
            if not await mfa.consume(cur,user['id'],body.code):raise HTTPException(401,'Authenticator or recovery code is incorrect or already used')
        await _new_session(user['id'],response,mfa_verified=enabled,cur=cur)
    return {"authenticated": True, "email": user["email"], "plan_code": user["plan_code"], "plan_status": user["plan_status"], "trial_ends_at": user["trial_ends_at"]}

@router.get("/session")
async def session(request: Request, response: Response):
    response.headers["Cache-Control"]="private, no-store"
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        await guest_identity(request,response)
        return {"authenticated": False,"state":"guest"}
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    async with cursor() as cur:
        await cur.execute("SELECT u.avatar,u.avatar_version,u.email,u.email_verified_at,CASE WHEN account_has_pro(u.id) THEN 'pro' ELSE 'free' END AS plan_code,CASE WHEN EXISTS(SELECT 1 FROM reward_redemptions rr WHERE rr.user_id=u.id AND rr.starts_at<=now() AND rr.ends_at>now()) THEN 'rewarded' WHEN NOT account_has_pro(u.id) THEN 'free' ELSE u.plan_status END AS plan_status,u.trial_ends_at,u.plan_ends_at FROM auth_sessions s JOIN users u ON u.id=s.user_id WHERE s.token_hash=%s AND s.revoked_at IS NULL AND s.expires_at>now()", (token_hash,))
        row = await cur.fetchone()
    session_info = await account_session(request) if row else None
    return {"authenticated": bool(row), "state":"authenticated" if row else "expired",
            "csrf":csrf_token(token),
            "expires_at":session_info['expires_at'] if session_info else None,
            "mfa_verified":bool(session_info and session_info['mfa_verified']), **(row or {})}

@router.post("/logout")
async def logout(request: Request, response: Response):
    _same_origin(request)
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        async with cursor() as cur:
            await cur.execute("UPDATE auth_sessions SET revoked_at=now() WHERE token_hash=%s", (hashlib.sha256(token.encode()).hexdigest(),))
    response.delete_cookie(GUEST_COOKIE, path='/', httponly=True, secure=settings.public_origin.startswith('https://'), samesite='lax')
    response.delete_cookie(SESSION_COOKIE, path="/", httponly=True, secure=settings.public_origin.startswith("https://"), samesite="lax")
    return {"authenticated": False}

class PasswordChange(BaseModel):
    current_password: str = Field(min_length=1, max_length=200)
    new_password: str = Field(min_length=12, max_length=200)

@router.post("/password")
async def change_password(body: PasswordChange, user_id: Annotated[str, Depends(require_account)], request: Request, response: Response,
                          x_device_id: Annotated[str | None, Header(alias="X-Device-Id")] = None):
    _same_origin(request)
    if not re.search(r"[A-Za-z]",body.new_password) or not re.search(r"\d",body.new_password):
        raise HTTPException(422,"Password must include letters and numbers")
    async with cursor() as cur:
        await cur.execute("SELECT password_hash FROM users WHERE id=%s FOR UPDATE",(user_id,)); row=await cur.fetchone()
        if not row or not await run_in_threadpool(_check_password,body.current_password,row["password_hash"]): raise HTTPException(400,"Current password is incorrect")
        await cur.execute('SELECT enabled_at FROM account_mfa WHERE user_id=%s',(user_id,));factor=await cur.fetchone()
        if factor and factor['enabled_at']:
            token=request.cookies.get(SESSION_COOKIE)
            await cur.execute("SELECT 1 FROM auth_sessions WHERE token_hash=%s AND mfa_verified_at>now()-interval '15 minutes'",(hashlib.sha256((token or '').encode()).hexdigest(),))
            if not await cur.fetchone():raise HTTPException(403,'Verify your authenticator in Account security before changing your password')
        await cur.execute("UPDATE users SET password_hash=%s WHERE id=%s",(await run_in_threadpool(_hash_password,body.new_password),user_id))
        token=request.cookies.get(SESSION_COOKIE)
        await cur.execute("UPDATE auth_sessions SET revoked_at=now() WHERE user_id=%s AND token_hash<>%s",(user_id,hashlib.sha256(token.encode()).hexdigest() if token else ""))
        await cur.execute("UPDATE auth_sessions SET revoked_at=now() WHERE user_id=%s",(user_id,))
        await _new_session(user_id,response,mfa_verified=bool(factor and factor['enabled_at']),cur=cur)
        await cur.execute("INSERT INTO account_security_events(user_id,action) VALUES(%s,'password_changed')",(user_id,))
    return {"changed":True}


@router.get('/guest-progress')
async def guest_progress(request:Request,response:Response):
    response.headers['Cache-Control']='private, no-store'
    guest=await guest_identity(request,response)
    async with cursor() as cur:
        await cur.execute('SELECT count(*)::int AS attempts FROM attempts WHERE user_id=%s',(guest,))
        counts=await cur.fetchone()
    return counts

@router.post('/guest-progress/save')
async def save_guest_progress(request:Request,response:Response,user:Annotated[str,Depends(require_account)]):
    _same_origin(request)
    return await transfer_guest(request,user)

@router.get('/sessions')
async def sessions(request:Request,response:Response,user:Annotated[str,Depends(require_account)]):
    response.headers['Cache-Control']='private, no-store'
    async with cursor() as cur:
        await cur.execute("SELECT public_id AS id,created_at,expires_at,token_hash=%s AS current FROM auth_sessions WHERE user_id=%s AND revoked_at IS NULL AND expires_at>now() ORDER BY created_at DESC",(hashlib.sha256(request.cookies['ism_session'].encode()).hexdigest(),user))
        return {'items':await cur.fetchall()}

class RevokeSessions(BaseModel):
    session_id:str|None=Field(default=None,max_length=64)

@router.post('/sessions/revoke')
async def revoke_sessions(body:RevokeSessions,request:Request,user:Annotated[str,Depends(require_account)]):
    _same_origin(request)
    async with cursor() as cur:
        await cur.execute("UPDATE auth_sessions SET revoked_at=now() WHERE user_id=%s AND revoked_at IS NULL AND ((%s::text IS NULL AND token_hash<>%s) OR public_id=%s)",(user,body.session_id,hashlib.sha256(request.cookies['ism_session'].encode()).hexdigest(),body.session_id))
        count=cur.rowcount
        await cur.execute("INSERT INTO account_security_events(user_id,action,detail) VALUES(%s,'sessions_revoked',%s)",(user,Jsonb({'count':count})))
    return {'revoked':count}
