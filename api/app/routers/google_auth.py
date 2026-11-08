"""Google OIDC authorization-code/PKCE with explicit account linking and MFA."""
import base64
import hashlib
import hmac
import secrets
from typing import Literal
from urllib.parse import urlencode
import requests
from google.oauth2 import id_token
from google.auth.transport.requests import Request as GoogleRequest
from fastapi import APIRouter, Request, Response, HTTPException
from pydantic import BaseModel,Field
from starlette.responses import RedirectResponse
from starlette.concurrency import run_in_threadpool
from ..config import settings
from ..db import cursor
from ..services.account_identity import account_session
from ..services import mfa
from .auth import _same_origin, _new_session, _check_rate

router=APIRouter(prefix='/api/auth/google',tags=['Google sign-in'])
STATE_COOKIE='ism_google_state'
PENDING_COOKIE='ism_google_pending'

def hashed(value):return hashlib.sha256(value.encode()).hexdigest()
def enabled():return bool(settings.google_client_id and settings.google_client_secret)
def callback_url():return settings.public_origin.rstrip('/')+'/api/auth/google/callback'
def cookie(response,name,value):
    response.set_cookie(name,value,max_age=600,httponly=True,secure=settings.public_origin.startswith('https://'),samesite='lax',path='/api/auth/google')
def private(response):response.headers['Cache-Control']='private, no-store'

async def link_session(request,user_id,session_hash):
    row=await account_session(request)
    if not row or row['user_id']!=user_id or not row['recent'] or hashed(request.cookies.get('ism_session',''))!=session_hash:
        raise HTTPException(403,'Sign in again before linking Google')
    async with cursor() as cur:
        await cur.execute('SELECT enabled_at FROM account_mfa WHERE user_id=%s',(user_id,));factor=await cur.fetchone()
        if factor and factor['enabled_at'] and not row['mfa_verified']:raise HTTPException(403,'Verify your authenticator before linking Google')

class Start(BaseModel):
    action:Literal['login','link']='login'
class Finish(BaseModel):
    code:str=Field(default='',max_length=64)

@router.get('/config')
async def config(response:Response):
    private(response);return {'enabled':enabled()}

@router.post('/start')
async def start(body:Start,request:Request,response:Response):
    private(response);_same_origin(request)
    if not enabled():raise HTTPException(503,'Google sign-in is not configured')
    await _check_rate('google-start',request.client.host if request.client else 'unknown')
    row=await account_session(request)
    user=None;session_hash=None
    if body.action=='link':
        if not row:raise HTTPException(401,'Sign in before linking Google')
        user=row['user_id'];session_hash=hashed(request.cookies.get('ism_session',''))
        await link_session(request,user,session_hash)
    elif row:raise HTTPException(409,'Use Link Google in Account security while signed in')
    token=secrets.token_urlsafe(32);verifier=secrets.token_urlsafe(48);nonce=secrets.token_urlsafe(32)
    async with cursor() as cur:
        await cur.execute('DELETE FROM google_auth_flows WHERE expires_at<now()')
        await cur.execute("INSERT INTO google_auth_flows(token_hash,stage,verifier,nonce,link_user_id,session_hash) VALUES(%s,'authorize',%s,%s,%s,%s)",(hashed(token),verifier,nonce,user,session_hash))
    cookie(response,STATE_COOKIE,token)
    challenge=base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip('=')
    return {'url':'https://accounts.google.com/o/oauth2/v2/auth?'+urlencode(dict(client_id=settings.google_client_id,redirect_uri=callback_url(),response_type='code',scope='openid email',state=token,nonce=nonce,code_challenge=challenge,code_challenge_method='S256',prompt='select_account'))}

class BoundedGoogleRequest(GoogleRequest):
    def __call__(self,*args,**kwargs):
        kwargs['timeout']=10
        return super().__call__(*args,**kwargs)

def exchange(code,flow):
    # Never accept an ID token supplied by the browser or log provider bodies.
    try:
        with requests.Session() as session:
            response=session.post('https://oauth2.googleapis.com/token',data=dict(code=code,client_id=settings.google_client_id,client_secret=settings.google_client_secret,redirect_uri=callback_url(),grant_type='authorization_code',code_verifier=flow['verifier']),timeout=10,allow_redirects=False)
            response.raise_for_status()
            claims=id_token.verify_oauth2_token(response.json()['id_token'],BoundedGoogleRequest(session=session),settings.google_client_id)
        if claims.get('nonce')!=flow['nonce'] or claims.get('email_verified') is not True or not claims.get('sub') or not claims.get('email'):
            raise ValueError('Invalid identity claims')
        if claims.get('azp',settings.google_client_id)!=settings.google_client_id:raise ValueError('Invalid authorized party')
        if len(claims['sub'])>255 or len(claims['email'])>254:raise ValueError('Invalid identity length')
        return claims
    except Exception:
        raise HTTPException(401,'Google sign-in could not be verified. Please start again.') from None

@router.get('/callback')
async def callback(request:Request,state:str='',code:str='',error:str=''):
    supplied=request.cookies.get(STATE_COOKIE,'')
    if not enabled() or not supplied or not hmac.compare_digest(supplied,state):raise HTTPException(400,'Google sign-in state expired or did not match')
    async with cursor() as cur:
        await cur.execute("DELETE FROM google_auth_flows WHERE token_hash=%s AND stage='authorize' AND expires_at>now() RETURNING *",(hashed(state),));flow=await cur.fetchone()
    if not flow:raise HTTPException(400,'Google sign-in was already used or expired')
    if error or not code:
        response=RedirectResponse('/login?google_error=cancelled',status_code=303);private(response);response.delete_cookie(STATE_COOKIE,path='/api/auth/google');return response
    claims=await run_in_threadpool(exchange,code,flow)
    if flow['link_user_id']:await link_session(request,flow['link_user_id'],flow['session_hash'])
    token=secrets.token_urlsafe(32)
    async with cursor() as cur:
        await cur.execute("INSERT INTO google_auth_flows(token_hash,stage,subject,email,link_user_id,session_hash) VALUES(%s,'complete',%s,%s,%s,%s)",(hashed(token),claims['sub'],claims['email'].lower(),flow['link_user_id'],flow['session_hash']))
    response=RedirectResponse('/google/finish',status_code=303);private(response);cookie(response,PENDING_COOKIE,token);response.delete_cookie(STATE_COOKIE,path='/api/auth/google');return response

async def pending(cur,request,lock=False):
    await cur.execute("SELECT * FROM google_auth_flows WHERE token_hash=%s AND stage='complete' AND expires_at>now()"+(' FOR UPDATE' if lock else ''),(hashed(request.cookies.get(PENDING_COOKIE,'')),))
    row=await cur.fetchone()
    if not row:raise HTTPException(401,'Google sign-in expired. Start again.')
    return row

@router.get('/pending')
async def status(request:Request,response:Response):
    private(response)
    async with cursor() as cur:
        p=await pending(cur,request)
        await cur.execute('SELECT m.enabled_at FROM google_identities g LEFT JOIN account_mfa m ON m.user_id=g.user_id WHERE g.subject=%s',(p['subject'],));row=await cur.fetchone()
        return {'linking':bool(p['link_user_id']),'mfa_required':bool(row and row['enabled_at'] and not p['link_user_id'])}

@router.post('/finish')
async def finish(body:Finish,request:Request,response:Response):
    private(response);_same_origin(request)
    await _check_rate('google-finish',request.client.host if request.client else 'unknown')
    async with cursor() as cur:
        p=await pending(cur,request,True)
        await cur.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))',('google:'+p['subject'],))
        await cur.execute('SELECT user_id FROM google_identities WHERE subject=%s',(p['subject'],));linked=await cur.fetchone()
        if p['link_user_id']:
            await link_session(request,p['link_user_id'],p['session_hash']);user=p['link_user_id']
            if linked and linked['user_id']!=user:raise HTTPException(409,'This Google identity is already linked to another account')
            await cur.execute('SELECT subject FROM google_identities WHERE user_id=%s',(user,));existing=await cur.fetchone()
            if existing and existing['subject']!=p['subject']:raise HTTPException(409,'This account already has a different Google identity')
            await cur.execute('INSERT INTO google_identities(subject,user_id) VALUES(%s,%s) ON CONFLICT(subject) DO NOTHING',(p['subject'],user))
            destination='/account/security'
        else:
            if await account_session(request):raise HTTPException(409,'Your account changed during Google sign-in. Start again.')
            if linked:user=linked['user_id']
            else:
                await cur.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))',('google-email:'+p['email'],))
                await cur.execute('SELECT id FROM users WHERE lower(email)=%s',(p['email'],))
                if await cur.fetchone():raise HTTPException(409,'An account already uses this email. Sign in with your existing method, then link Google in Account security.')
                user='usr_'+secrets.token_urlsafe(18)
                await cur.execute("INSERT INTO users(id,handle,email,email_verified_at,role,plan_code,plan_status,trial_ends_at) VALUES(%s,%s,%s,now(),'learner','pro','trial',now()+interval '7 days')",(user,'learner-'+secrets.token_hex(4),p['email']))
                await cur.execute('INSERT INTO google_identities(subject,user_id) VALUES(%s,%s)',(p['subject'],user))
            await cur.execute('SELECT enabled_at FROM account_mfa WHERE user_id=%s',(user,));factor=await cur.fetchone();has_mfa=bool(factor and factor['enabled_at'])
            if has_mfa:
                await mfa.limit(user)
                if not body.code or not await mfa.consume(cur,user,body.code):raise HTTPException(401,'Enter a valid authenticator or recovery code')
            await _new_session(user,response,mfa_verified=has_mfa,cur=cur);destination='/feed'
        await cur.execute('DELETE FROM google_auth_flows WHERE token_hash=%s',(p['token_hash'],))
    response.delete_cookie(PENDING_COOKIE,path='/api/auth/google')
    return {'next':destination}
