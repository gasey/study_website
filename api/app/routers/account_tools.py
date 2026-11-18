"""Cookie-owned account self-service. Native destructive operations stay closed."""
from typing import Annotated,Literal
from fastapi import APIRouter,Depends,HTTPException,Request,Response
from starlette.responses import StreamingResponse
from pydantic import BaseModel,ConfigDict,Field
from ..db import cursor
from ..deps import require_account
from ..services import account_tools,mfa
from ..services.account_identity import account_session
from .materials import private,write_guard
router=APIRouter(dependencies=[Depends(private)])
Account=Annotated[str,Depends(require_account)]

@router.get('/account-tools')
async def status(request:Request,user:Account):
    session=await account_session(request)
    async with cursor() as cur:
        await cur.execute('SELECT id AS user_id,identity_version FROM users WHERE id=%s',(user,));row=await cur.fetchone()
        await cur.execute('SELECT enabled_at IS NOT NULL AS enabled FROM account_mfa WHERE user_id=%s',(user,));factor=await cur.fetchone()
        await cur.execute('SELECT EXISTS(SELECT 1 FROM creator_profiles WHERE user_id=%s AND public) AS public',(user,));creator=await cur.fetchone()
        await cur.execute('SELECT COALESCE(sum(points),0)::int AS points,COALESCE((SELECT board_public FROM reward_profiles WHERE user_id=%s),false) AS public FROM reward_ledger WHERE user_id=%s',(user,user));wallet=await cur.fetchone()
        return row|{'recent':bool(session and session['recent']),'mfa_enabled':bool(factor and factor['enabled']),
                    'creator_public':creator['public'],'points':wallet['points'],'board_public':wallet['public'],
                    'closure_blockers':await account_tools.blockers(cur,user)}

@router.get('/data-export')
async def export(user_id:str, user:Account):
    if user_id!=user:raise HTTPException(409,'Your account changed. Reload before exporting.')
    await mfa.limit('data-export:'+user)
    async def content():
        async with cursor() as cur:
            async for part in account_tools.export(cur,user):yield part
    return StreamingResponse(content(),media_type='application/json',headers={
        'Cache-Control':'private, no-store','Content-Disposition':'attachment; filename="finna-data.json"',
        'X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer'})

class Close(BaseModel):
    model_config=ConfigDict(extra='forbid')
    user_id:str=Field(min_length=1,max_length=100)
    expected_version:int=Field(ge=0)
    confirmation:Literal['DELETE MY ACCOUNT']

@router.post('/account-close')
async def close(body:Close,request:Request,response:Response,user:Account):
    await write_guard(request,user)
    if body.user_id!=user:raise HTTPException(409,'Your account changed. Reload before closing.')
    session=await account_session(request)
    if not session or not session['recent']:raise HTTPException(403,'Sign in again, then close your account within 15 minutes.')
    await mfa.limit('account-close:'+user)
    async with cursor() as cur:
        await cur.execute('SELECT enabled_at FROM account_mfa WHERE user_id=%s',(user,));factor=await cur.fetchone()
        if factor and factor['enabled_at'] and not session['mfa_verified']:raise HTTPException(403,'Verify your authenticator in Account security before closing your account.')
        result=await account_tools.close(cur,user,body.expected_version,session['mfa_verified'])
    from .auth import SESSION_COOKIE,GUEST_COOKIE
    from ..config import settings
    for cookie in (SESSION_COOKIE,GUEST_COOKIE):response.delete_cookie(cookie,path='/',httponly=True,secure=settings.public_origin.startswith('https://'),samesite='lax')
    return result


class Owner(BaseModel):
    model_config=ConfigDict(extra='forbid')
    user_id:str=Field(min_length=1,max_length=100)

@router.post('/account-signout-all')
async def signout(body:Owner,request:Request,response:Response,user:Account):
    await write_guard(request,user)
    if body.user_id!=user:raise HTTPException(409,'Your account changed. Reload before signing out.')
    async with cursor() as cur:
        await cur.execute('SELECT id FROM users WHERE id=%s FOR UPDATE',(user,))
        await cur.execute('UPDATE auth_sessions SET revoked_at=now() WHERE user_id=%s AND revoked_at IS NULL',(user,))
        await cur.execute('UPDATE mobile_sessions SET revoked_at=now() WHERE user_id=%s AND revoked_at IS NULL',(user,))
        await cur.execute("INSERT INTO account_security_events(user_id,action) VALUES(%s,'signed_out_everywhere')",(user,))
    from .auth import SESSION_COOKIE,GUEST_COOKIE
    from ..config import settings
    for cookie in (SESSION_COOKIE,GUEST_COOKIE):response.delete_cookie(cookie,path='/',httponly=True,secure=settings.public_origin.startswith('https://'),samesite='lax')
    return {'signed_out':True}
