import base64,hashlib,io,secrets
from typing import Annotated
from urllib.parse import quote,urlencode
import qrcode
from qrcode.image.svg import SvgPathImage
from fastapi import APIRouter,Depends,HTTPException,Request,Response
from pydantic import BaseModel,ConfigDict,Field
from ..db import cursor
from ..config import settings
from ..services.review_identity import identity,Actor
from ..services import mfa
from .auth import _check_password

async def private(response:Response):response.headers['Cache-Control']='no-store'
router=APIRouter(prefix='/api/auth/mfa',tags=['account security'],dependencies=[Depends(private)])
Account=Annotated[Actor,Depends(identity)]
class PasswordCheck(BaseModel):
    model_config=ConfigDict(extra='forbid')
    password:str=Field(min_length=1,max_length=200)
class Code(BaseModel):
    model_config=ConfigDict(extra='forbid')
    code:str=Field(min_length=6,max_length=64)
class Action(PasswordCheck):code:str=Field(min_length=6,max_length=64)
def session_hash(request):return hashlib.sha256(request.cookies['ism_session'].encode()).hexdigest()
async def password(cur,user,value):
    await cur.execute('SELECT password_hash,email FROM users WHERE id=%s FOR UPDATE',(user,));row=await cur.fetchone()
    if not row or not _check_password(value,row['password_hash']):raise HTTPException(401,'Current password is incorrect')
    return row
async def verified_session(cur,request,user):
    await cur.execute("UPDATE auth_sessions SET mfa_verified_at=now() WHERE token_hash=%s AND user_id=%s AND revoked_at IS NULL AND expires_at>now() RETURNING token_hash",(session_hash(request),user))
    if not await cur.fetchone():raise HTTPException(401,'Your session has expired')

async def event(cur,user,action):await cur.execute('INSERT INTO account_security_events(user_id,action) VALUES (%s,%s)',(user,action))

@router.get('/status')
async def status(actor:Account):
    async with cursor() as cur:
        await cur.execute('SELECT enabled_at FROM account_mfa WHERE user_id=%s',(actor.id,));row=await cur.fetchone()
        await cur.execute('SELECT 1 FROM review_grants WHERE user_id=%s AND revoked_at IS NULL LIMIT 1',(actor.id,));staff=bool(await cur.fetchone())
        await cur.execute('SELECT count(*)::int AS n FROM mfa_recovery_codes WHERE user_id=%s AND used_at IS NULL',(actor.id,));remaining=(await cur.fetchone())['n']
    return {'configured':bool(settings.mfa_encryption_key),'enabled':bool(row and row['enabled_at']),'verified':actor.mfa_verified,'staff_required':staff and settings.mfa_enforce_staff,'recovery_codes_remaining':remaining}

@router.post('/setup')
async def setup(body:PasswordCheck,actor:Account):
    mfa.cipher()
    if not actor.recent:raise HTTPException(403,'Sign in again before setting up an authenticator')
    await mfa.limit(actor.id)
    async with cursor() as cur:
        user=await password(cur,actor.id,body.password)
        await cur.execute('SELECT enabled_at FROM account_mfa WHERE user_id=%s',(actor.id,));old=await cur.fetchone()
        if old and old['enabled_at'] and not actor.mfa_verified:raise HTTPException(403,'Verify the existing authenticator or use a recovery code before replacing it')
        seed=base64.b32encode(secrets.token_bytes(20)).decode().rstrip('=')
        await cur.execute("INSERT INTO account_mfa(user_id,pending_cipher,pending_until) VALUES (%s,%s,now()+interval '10 minutes') ON CONFLICT(user_id) DO UPDATE SET pending_cipher=EXCLUDED.pending_cipher,pending_until=EXCLUDED.pending_until,updated_at=now()",(actor.id,mfa.encrypt(actor.id,seed)))
        await event(cur,actor.id,'mfa_setup_started')
    uri='otpauth://totp/'+quote('India Study Map:'+user['email'],safe='')+'?'+urlencode({'secret':seed,'issuer':'India Study Map','algorithm':'SHA1','digits':6,'period':30})
    image=qrcode.make(uri,image_factory=SvgPathImage);stream=io.BytesIO();image.save(stream)
    return {'setup_key':seed,'qr_data_url':'data:image/svg+xml;base64,'+base64.b64encode(stream.getvalue()).decode(),'expires_in':600}

@router.post('/confirm')
async def confirm(body:Code,request:Request,actor:Account):
    if not actor.recent:raise HTTPException(403,'Sign in again before confirming authenticator setup')
    await mfa.limit(actor.id)
    async with cursor() as cur:
        await cur.execute('SELECT id FROM users WHERE id=%s FOR UPDATE',(actor.id,));await cur.fetchone()
        await cur.execute('SELECT * FROM account_mfa WHERE user_id=%s AND pending_until>now() FOR UPDATE',(actor.id,));row=await cur.fetchone()
        if not row or not row['pending_cipher']:raise HTTPException(409,'Setup expired. Start authenticator setup again')
        if row['enabled_at'] and not actor.mfa_verified:raise HTTPException(403,'Verify the existing authenticator before replacing it')
        counter=mfa.matching_counter(mfa.decrypt(actor.id,row['pending_cipher']),body.code)
        if counter is None:raise HTTPException(401,'Authenticator code is incorrect')
        await cur.execute('UPDATE account_mfa SET secret_cipher=pending_cipher,pending_cipher=NULL,pending_until=NULL,enabled_at=now(),last_counter=%s,updated_at=now() WHERE user_id=%s',(counter,actor.id))
        codes=await mfa.recovery(cur,actor.id)
        await cur.execute('UPDATE auth_sessions SET revoked_at=now() WHERE user_id=%s AND token_hash<>%s',(actor.id,session_hash(request)))
        await verified_session(cur,request,actor.id)
        await event(cur,actor.id,'mfa_enabled')
    return {'enabled':True,'recovery_codes':codes}

@router.post('/verify')
async def verify(body:Code,request:Request,actor:Account):
    await mfa.limit(actor.id)
    async with cursor() as cur:
        await cur.execute('SELECT id FROM users WHERE id=%s FOR UPDATE',(actor.id,));await cur.fetchone()
        if not await mfa.consume(cur,actor.id,body.code):raise HTTPException(401,'Code is incorrect or already used. Wait for the next code or use a recovery code')
        await verified_session(cur,request,actor.id)
        await event(cur,actor.id,'mfa_session_verified')
    return {'verified':True}

@router.post('/recovery-codes')
async def rotate_recovery(body:Action,request:Request,actor:Account):
    await mfa.limit(actor.id)
    async with cursor() as cur:
        await password(cur,actor.id,body.password)
        if not await mfa.consume(cur,actor.id,body.code):raise HTTPException(401,'Authenticator or recovery code is incorrect or already used')
        codes=await mfa.recovery(cur,actor.id)
        await verified_session(cur,request,actor.id)
        await event(cur,actor.id,'mfa_recovery_rotated')
    return {'recovery_codes':codes}

@router.post('/disable')
async def disable(body:Action,request:Request,actor:Account):
    await mfa.limit(actor.id)
    async with cursor() as cur:
        await password(cur,actor.id,body.password)
        await cur.execute('SELECT 1 FROM review_grants WHERE user_id=%s AND revoked_at IS NULL LIMIT 1',(actor.id,))
        if settings.mfa_enforce_staff and await cur.fetchone():raise HTTPException(409,'Staff accounts must replace their authenticator rather than disable MFA')
        if not await mfa.consume(cur,actor.id,body.code):raise HTTPException(401,'Authenticator or recovery code is incorrect or already used')
        await cur.execute('UPDATE account_mfa SET secret_cipher=NULL,pending_cipher=NULL,pending_until=NULL,enabled_at=NULL,last_counter=-1 WHERE user_id=%s',(actor.id,))
        await cur.execute('UPDATE mfa_recovery_codes SET used_at=COALESCE(used_at,now()) WHERE user_id=%s',(actor.id,))
        await cur.execute('UPDATE auth_sessions SET revoked_at=now() WHERE user_id=%s AND token_hash<>%s',(actor.id,session_hash(request)))
        await cur.execute('UPDATE auth_sessions SET mfa_verified_at=NULL WHERE token_hash=%s',(session_hash(request),));await event(cur,actor.id,'mfa_disabled')
    return {'enabled':False}
