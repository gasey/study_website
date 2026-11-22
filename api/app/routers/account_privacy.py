"""Owned privacy request receipts and a disabled-by-default age boundary."""
import secrets
import hmac
from typing import Literal
from fastapi import APIRouter, Request, Response, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from ..config import settings
from ..db import cursor
from ..services import audience, mfa
from ..services.account_identity import account_session, digest, csrf_token
from ..services.review_identity import identity, require_role
from .auth import _same_origin
from .materials import write_guard

router = APIRouter(prefix='/api/account-privacy')


class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid')


class Declaration(Strict):
    category: Literal['adult','under18']
    user_id: str | None = Field(default=None,max_length=100)
    expected_version: int = Field(default=0,ge=0)


class Owned(Strict):
    user_id: str = Field(min_length=1,max_length=100)


class Confirm(Owned):
    expected_version: int = Field(ge=0)


class NewRequest(Owned):
    kind: Literal['access','correction','erasure','guardian']
    request_key: str = Field(min_length=16,max_length=80,pattern=r'^[A-Za-z0-9_-]+$')


class Transition(Owned):
    expected_version: int = Field(ge=1)
    state: Literal['in_review','completed','declined','withdrawn']


class AudienceCorrection(Owned):
    request_id: str = Field(min_length=1,max_length=100)
    expected_audience_version: int = Field(ge=0)
    new_category: Literal['adult','under18']


async def _restrict_under18_channels(cur, user, keep_session_hash=None):
    await cur.execute('UPDATE mobile_sessions SET revoked_at=now() WHERE user_id=%s AND revoked_at IS NULL',(user,))
    if keep_session_hash is not None:
        await cur.execute('UPDATE auth_sessions SET revoked_at=now() WHERE user_id=%s AND token_hash<>%s AND revoked_at IS NULL',(user,keep_session_hash))
    else:
        await cur.execute('UPDATE auth_sessions SET revoked_at=now() WHERE user_id=%s AND revoked_at IS NULL',(user,))
    await cur.execute("UPDATE review_digest_preferences SET enabled=false,version=version+1,token_cipher='',updated_at=clock_timestamp() WHERE user_id=%s",(user,))
    await cur.execute("UPDATE review_digest_outbox SET state='cancelled' WHERE user_id=%s AND state='pending'",(user,))
    await cur.execute('UPDATE user_calendar_preferences SET reminders=false WHERE user_id=%s',(user,))
    await cur.execute("UPDATE calendar_feed_tokens SET token_hash=NULL,version=version+1,revoked_at=clock_timestamp() WHERE user_id=%s AND token_hash IS NOT NULL",(user,))


async def owner(request):
    # Deliberately avoid current_user: this tool must not create guest identities
    # and must remain available to an account whose study access is restricted.
    session = await account_session(request)
    if not session:raise HTTPException(401,'Sign in to manage privacy requests')
    return session


@router.get('/status')
async def status(request:Request,response:Response):
    response.headers['Cache-Control']='private, no-store'
    session=await account_session(request)
    category=None;version=0
    if session:
        async with cursor() as cur:
            await cur.execute('SELECT category,version FROM account_audience WHERE user_id=%s',(session['user_id'],))
            row=await cur.fetchone()
            if row:category=row['category'];version=row['version']
    return {'user_id':session['user_id'] if session else None,'category':category,
            'version':version,'browser_category':await audience.browser_category(request),
            'age_check_enabled':settings.audience_gate_enabled,
            'guardian_enrollment_available':False,'support_email':'hruaitluangasailo20@gmail.com'}


@router.post('/declare')
async def declare(body:Declaration,request:Request,response:Response):
    _same_origin(request)
    if not settings.audience_gate_enabled:raise HTTPException(409,'Age-category enrollment is not enabled yet')
    session=await account_session(request)
    if (session['user_id'] if session else None)!=body.user_id:
        raise HTTPException(409,'Your account changed. Reload before saving.')
    if session and not hmac.compare_digest(request.headers.get('x-review-csrf',''),csrf_token(request.cookies['ism_session'])):
        raise HTTPException(403,'Refresh the page before saving')
    # Minimal browser flow only; no child name, date of birth, email or account.
    await mfa.limit('audience:'+digest(request.client.host if request.client else 'unknown'))
    token=secrets.token_urlsafe(32)
    async with cursor() as cur:
        if session and body.category=='under18':
            await audience.calendar_publication_lock(cur,restricting=True)
            await audience.learning_processing_lock(cur,session['user_id'],restricting=True)
        if session:
            user=session['user_id']
            await cur.execute('SELECT id FROM users WHERE id=%s FOR UPDATE',(user,))
            await cur.execute('SELECT category,version FROM account_audience WHERE user_id=%s FOR UPDATE',(user,))
            old=await cur.fetchone()
            if (old['version'] if old else 0)!=body.expected_version:raise HTTPException(409,'Your age declaration changed. Reload before saving.')
            if body.category=='adult' and old and old['category']=='under18':
                raise HTTPException(409,'Contact support to review an existing under-18 declaration.')
            if body.category=='under18':
                prev=old['category'] if old else None
                await cur.execute("INSERT INTO account_audience(user_id,category) VALUES(%s,'under18') ON CONFLICT(user_id) DO UPDATE SET category='under18',version=account_audience.version+1,declared_at=clock_timestamp()",(user,))
                await _restrict_under18_channels(cur,user,keep_session_hash=digest(request.cookies['ism_session']))
                await cur.execute("INSERT INTO account_audience_events(user_id,actor_id,previous_category,new_category,reason_code) VALUES(%s,%s,%s,'under18','self_declaration')",(user,user,prev))
        await cur.execute('DELETE FROM audience_browser_flows WHERE token_hash IN(SELECT token_hash FROM audience_browser_flows WHERE expires_at<now() ORDER BY expires_at LIMIT 500)')
        await cur.execute('INSERT INTO audience_browser_flows(token_hash,category) VALUES(%s,%s)',(digest(token),body.category))
        old=request.cookies.get(audience.COOKIE)
        if old:await cur.execute('DELETE FROM audience_browser_flows WHERE token_hash=%s',(digest(old),))
    response.set_cookie(audience.COOKIE,token,max_age=86400,httponly=True,secure=settings.public_origin.startswith('https://'),samesite='lax',path='/')
    response.headers['Cache-Control']='private, no-store'
    return {'category':body.category,'guardian_enrollment_available':False,
            'message':('Finna is for people aged 18 or over. '+('Study access is unavailable for this account.' if session else 'No learner account was created.')) if body.category=='under18' else 'Age category saved for this browser for one day.'}


@router.post('/confirm-adult')
async def confirm(body:Confirm,request:Request):
    session=await owner(request);await write_guard(request,session['user_id'])
    if body.user_id!=session['user_id']:raise HTTPException(409,'Your account changed. Reload before saving.')
    if not settings.audience_gate_enabled:raise HTTPException(409,'Age-category enrollment is not enabled yet')
    await audience.require_browser(request)
    async with cursor() as cur:
        await cur.execute('SELECT id FROM users WHERE id=%s FOR UPDATE',(session['user_id'],))
        await cur.execute('SELECT category,version FROM account_audience WHERE user_id=%s FOR UPDATE',(session['user_id'],))
        old=await cur.fetchone()
        if (old['version'] if old else 0)!=body.expected_version:raise HTTPException(409,'Your age declaration changed. Reload before saving.')
        await audience.bind_adult(cur,session['user_id'])
        if not old:
            await cur.execute("INSERT INTO account_audience_events(user_id,actor_id,previous_category,new_category,reason_code) VALUES(%s,%s,NULL,'adult','self_declaration')",(session['user_id'],session['user_id']))
    return {'category':'adult'}


@router.get('/requests')
async def requests(request:Request,response:Response):
    response.headers['Cache-Control']='private, no-store';session=await owner(request)
    async with cursor() as cur:
        await cur.execute('SELECT id,kind,state,version,created_at,updated_at FROM privacy_requests WHERE user_id=%s ORDER BY created_at DESC,id DESC LIMIT 50',(session['user_id'],))
        rows=await cur.fetchall()
    return {'user_id':session['user_id'],'items':rows,'limit':50}


@router.post('/requests')
async def create(body:NewRequest,request:Request):
    session=await owner(request);user=session['user_id'];await write_guard(request,user)
    if body.user_id!=user:raise HTTPException(409,'Your account changed. Reload before saving.')
    async with cursor() as cur:
        await cur.execute('SELECT id FROM users WHERE id=%s AND closed_at IS NULL FOR UPDATE',(user,))
        if not await cur.fetchone():raise HTTPException(409,'This account is closed')
        await cur.execute('SELECT id,kind,state,version FROM privacy_requests WHERE user_id=%s AND request_key=%s',(user,body.request_key))
        existing=await cur.fetchone()
        if existing:
            if existing['kind']!=body.kind:raise HTTPException(409,'This request key was already used for a different request')
            return existing
        # Preserve old receipts and their retry keys without offering new minor enrollment.
        if body.kind=='guardian':
            raise HTTPException(422,'Finna is for people aged 18 or over. Under-18 enrollment is not supported. Contact support about an age declaration or existing data.')
        await cur.execute("SELECT count(*) AS n FROM privacy_requests WHERE user_id=%s AND state IN ('received','in_review')",(user,))
        if (await cur.fetchone())['n']>=5:raise HTTPException(409,'You already have five open requests. Review those requests or contact support.')
        rid=secrets.token_urlsafe(18)
        await cur.execute('INSERT INTO privacy_requests(id,user_id,kind,request_key) VALUES(%s,%s,%s,%s) RETURNING id,kind,state,version',(rid,user,body.kind,body.request_key))
        row=await cur.fetchone()
        await cur.execute("INSERT INTO privacy_request_events(request_id,actor_id,state) VALUES(%s,%s,'received')",(rid,user))
    return row


@router.post('/requests/{rid}/withdraw')
async def withdraw(rid:str,body:Transition,request:Request):
    session=await owner(request);user=session['user_id'];await write_guard(request,user)
    if body.user_id!=user or body.state!='withdrawn':raise HTTPException(409,'Reload before withdrawing this request.')
    async with cursor() as cur:
        return await change(cur,rid,user,user,body.expected_version,'withdrawn')


async def change(cur,rid,subject,actor,version,state):
    await cur.execute('SELECT id,state,version FROM privacy_requests WHERE id=%s AND user_id=%s FOR UPDATE',(rid,subject))
    row=await cur.fetchone()
    if not row:raise HTTPException(404,'Request not found')
    if row['version']!=version or row['state'] not in ('received','in_review'):
        raise HTTPException(409,'The request changed or is already closed. Reload before updating.')
    if row['state']=='in_review' and state=='in_review':raise HTTPException(409,'The request is already in review')
    await cur.execute('UPDATE privacy_requests SET state=%s,version=version+1,updated_at=clock_timestamp() WHERE id=%s RETURNING id,state,version',(state,rid))
    result=await cur.fetchone()
    await cur.execute('INSERT INTO privacy_request_events(request_id,actor_id,state) VALUES(%s,%s,%s)',(rid,actor,state))
    return result


@router.get('/admin/requests')
async def queue(request:Request,response:Response):
    response.headers['Cache-Control']='private, no-store';actor=await identity(request)
    async with cursor() as cur:
        await require_role(cur,actor.id,roles=('owner',))
        await cur.execute("SELECT id,user_id,kind,state,version,created_at,updated_at FROM privacy_requests WHERE state IN ('received','in_review') ORDER BY created_at,id LIMIT 100")
        return {'items':await cur.fetchall(),'limit':100}


@router.post('/admin/requests/{rid}')
async def resolve(rid:str,body:Transition,request:Request):
    actor=await identity(request)
    if not actor.recent:raise HTTPException(403,'Sign in again before managing privacy requests')
    if body.state=='withdrawn':raise HTTPException(422,'Only the requesting account can withdraw a request')
    async with cursor() as cur:
        await require_role(cur,actor.id,roles=('owner',))
        return await change(cur,rid,body.user_id,actor.id,body.expected_version,body.state)


@router.post('/admin/audience-correction')
async def correct_audience(body:AudienceCorrection,request:Request):
    """Owner-reviewed correction of an existing age declaration.

    Requires an explicit in-review 'correction' privacy request, recent owner
    authentication (and MFA when enforced), and exact audience version.
    Never automatically grandfathers an account with no prior declaration to adult.
    """
    if not settings.audience_gate_enabled:
        raise HTTPException(409,'Age-category enrollment is not enabled yet')
    actor=await identity(request)
    if not actor.recent:
        raise HTTPException(403,'Sign in again before correcting an age declaration')
    async with cursor() as cur:
        await require_role(cur,actor.id,roles=('owner',))
        if body.new_category=='under18':
            await audience.calendar_publication_lock(cur,restricting=True)
            await audience.learning_processing_lock(cur,body.user_id,restricting=True)
        await cur.execute('SELECT id,closed_at FROM users WHERE id=%s FOR UPDATE',(body.user_id,))
        target=await cur.fetchone()
        if not target:raise HTTPException(404,'Account not found')
        if target['closed_at'] is not None:raise HTTPException(409,'Cannot correct age declaration on a closed account')
        await cur.execute('SELECT id,kind,state FROM privacy_requests WHERE id=%s AND user_id=%s FOR UPDATE',(body.request_id,body.user_id))
        req=await cur.fetchone()
        if not req:raise HTTPException(404,'Linked correction request not found')
        if req['kind']!='correction' or req['state']!='in_review':
            raise HTTPException(409,'An in-review correction privacy request is required before changing an age declaration.')
        await cur.execute('SELECT category,version FROM account_audience WHERE user_id=%s FOR UPDATE',(body.user_id,))
        old=await cur.fetchone()
        if (old['version'] if old else 0)!=body.expected_audience_version:
            raise HTTPException(409,'The account age declaration changed. Reload before saving.')
        if not old and body.new_category=='adult':
            raise HTTPException(409,'Existing accounts without a declaration must confirm their own age category.')
        if old and old['category']==body.new_category:
            raise HTTPException(409,'The account already has that age category.')
        prev=old['category'] if old else None
        if old:
            await cur.execute('UPDATE account_audience SET category=%s,version=version+1,declared_at=clock_timestamp() WHERE user_id=%s RETURNING category,version',(body.new_category,body.user_id))
        else:
            await cur.execute('INSERT INTO account_audience(user_id,category) VALUES(%s,%s) RETURNING category,version',(body.user_id,body.new_category))
        updated=await cur.fetchone()
        if body.new_category=='under18':
            await _restrict_under18_channels(cur,body.user_id,keep_session_hash=None)
        await cur.execute("INSERT INTO account_audience_events(user_id,actor_id,previous_category,new_category,request_id,reason_code) VALUES(%s,%s,%s,%s,%s,'owner_verified_correction')",(body.user_id,actor.id,prev,body.new_category,body.request_id))
        await cur.execute("INSERT INTO account_security_events(user_id,action,detail) VALUES(%s,'audience_category_corrected',jsonb_build_object('from',%s::text,'to',%s::text,'request_id',%s::text))",(body.user_id,prev,body.new_category,body.request_id))
    return {'user_id':body.user_id,'category':updated['category'],'version':updated['version'],'request_id':body.request_id}
