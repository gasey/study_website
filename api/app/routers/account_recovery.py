"""Purpose-bound, single-use recovery; sending remains gated by configuration."""
import re,secrets,hashlib
from typing import Annotated
from fastapi import APIRouter,Depends,HTTPException,Request,Response
from pydantic import BaseModel,Field
from starlette.concurrency import run_in_threadpool
from ..config import settings
from ..db import cursor
from ..deps import require_account
from ..services import mfa
from ..services.account_identity import digest
from ..services.account_mail import configured
from .auth import _same_origin,_check_rate,_hash_password,SESSION_COOKIE,GUEST_COOKIE
router=APIRouter(prefix='/api/auth',tags=['account recovery'])
class EmailRequest(BaseModel):
    email:str=Field(min_length=3,max_length=254)
class Token(BaseModel):
    token:str=Field(min_length=32,max_length=100)
class Reset(Token):
    password:str=Field(min_length=12,max_length=200)
    code:str|None=Field(default=None,max_length=64)

async def enqueue(cur,user,purpose):
    raw=secrets.token_urlsafe(32)
    await cur.execute("UPDATE account_email_tokens SET consumed_at=now() WHERE user_id=%s AND purpose=%s AND consumed_at IS NULL",(user,purpose))
    await cur.execute("INSERT INTO account_email_tokens(token_hash,user_id,purpose,expires_at) VALUES(%s,%s,%s,now()+interval '30 minutes')",(digest(raw),user,purpose))
    await cur.execute('INSERT INTO account_mail_outbox(user_id,purpose,token_cipher) VALUES(%s,%s,%s)',(user,purpose,mfa.encrypt(user,raw)))

@router.get('/recovery/status')
async def status():
    return {'available':configured()}

@router.post('/recovery/request')
async def request_reset(body:EmailRequest,request:Request):
    _same_origin(request)
    if not configured():raise HTTPException(503,'Email recovery is not available yet. Contact site support for access help.')
    email=body.email.strip().lower()
    await _check_rate('reset:'+email,request.client.host if request.client else 'unknown')
    await mfa.limit('reset-account:'+digest(email))
    async with cursor() as cur:
        await cur.execute('SELECT id FROM users WHERE lower(email)=%s FOR UPDATE',(email,));row=await cur.fetchone()
        if row:await enqueue(cur,row['id'],'reset')
    return {'message':'If an account matches, a recovery email will arrive shortly.'}

@router.post('/email/request')
async def request_verification(request:Request,user:Annotated[str,Depends(require_account)]):
    _same_origin(request)
    if not configured():raise HTTPException(503,'Email verification is not available yet.')
    await mfa.limit('verify-email:'+user)
    async with cursor() as cur:
        await cur.execute('SELECT email_verified_at FROM users WHERE id=%s FOR UPDATE',(user,));row=await cur.fetchone()
        if row['email_verified_at']:return {'message':'Your email is already verified.'}
        await enqueue(cur,user,'verify')
    return {'message':'Check your email for a verification link.'}

@router.post('/email/confirm')
async def confirm_email(body:Token,request:Request):
    _same_origin(request)
    async with cursor() as cur:
        await cur.execute("UPDATE account_email_tokens SET consumed_at=now() WHERE token_hash=%s AND purpose='verify' AND consumed_at IS NULL AND expires_at>now() RETURNING user_id",(digest(body.token),));row=await cur.fetchone()
        if not row:raise HTTPException(400,'This link has expired or was already used.')
        await cur.execute('UPDATE users SET email_verified_at=COALESCE(email_verified_at,now()) WHERE id=%s',(row['user_id'],))
        await cur.execute("INSERT INTO account_security_events(user_id,action) VALUES(%s,'email_verified')",(row['user_id'],))
    return {'verified':True}

@router.post('/recovery/complete')
async def complete_reset(body:Reset,request:Request,response:Response):
    _same_origin(request)
    if not re.search(r'[A-Za-z]',body.password) or not re.search(r'\d',body.password):raise HTTPException(422,'Password must include letters and numbers')
    await _check_rate('reset-token:'+digest(body.token),request.client.host if request.client else 'unknown')
    await mfa.limit('reset-token:'+digest(body.token))
    hashed=await run_in_threadpool(_hash_password,body.password)
    async with cursor() as cur:
        # Same lock order as login (user then factor); token consumption is a
        # guarded UPDATE after the user lock, so concurrent use has one winner.
        await cur.execute("SELECT user_id FROM account_email_tokens WHERE token_hash=%s AND purpose='reset' AND consumed_at IS NULL AND expires_at>now()",(digest(body.token),));token=await cur.fetchone()
        if not token:raise HTTPException(400,'This link has expired or was already used.')
        user=token['user_id']
        await cur.execute('SELECT id FROM users WHERE id=%s FOR UPDATE',(user,))
        await cur.execute('SELECT enabled_at FROM account_mfa WHERE user_id=%s',(user,));factor=await cur.fetchone()
        if factor and factor['enabled_at']:
            if not body.code or not await mfa.consume(cur,user,body.code):raise HTTPException(401,'An unused authenticator or recovery code is required.')
        await cur.execute("UPDATE account_email_tokens SET consumed_at=now() WHERE token_hash=%s AND purpose='reset' AND consumed_at IS NULL AND expires_at>now() RETURNING user_id",(digest(body.token),))
        if not await cur.fetchone():raise HTTPException(400,'This link has expired or was already used.')
        await cur.execute('UPDATE users SET password_hash=%s WHERE id=%s',(hashed,user))
        await cur.execute('UPDATE auth_sessions SET revoked_at=now() WHERE user_id=%s AND revoked_at IS NULL',(user,))
        await cur.execute("UPDATE account_email_tokens SET consumed_at=now() WHERE user_id=%s AND purpose='reset' AND consumed_at IS NULL",(user,))
        await cur.execute("INSERT INTO account_security_events(user_id,action) VALUES(%s,'password_recovered')",(user,))
    for cookie in (SESSION_COOKIE,GUEST_COOKIE):response.delete_cookie(cookie,path='/',httponly=True,secure=settings.public_origin.startswith('https://'),samesite='lax')
    return {'changed':True,'message':'Password saved. Sign in again to continue.'}
