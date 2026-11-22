"""Private invitation management. Credit is worker-only, never client callable."""
from typing import Annotated
from fastapi import APIRouter,Depends,Request
from pydantic import BaseModel,ConfigDict,Field
from ..db import cursor
from ..deps import require_account
from ..services import referrals,mfa
from .materials import private,write_guard
router=APIRouter(prefix='/api/referrals',dependencies=[Depends(private)])
Account=Annotated[str,Depends(require_account)]
class Code(BaseModel):
    model_config=ConfigDict(extra='forbid')
    user_id:str=Field(min_length=1,max_length=100)
    expected_version:int=Field(ge=0)
    enabled:bool
@router.get('/invite/{code}')
async def preview(code:str):
    if len(code)!=24:return {'available':False,'days_each':7,'scored_attempts_required':10,'yearly_referrer_cap':5}
    async with cursor() as cur:return await referrals.public(cur,code)
@router.get('/me')
async def me(user:Account):
    async with cursor() as cur:return await referrals.status(cur,user)
@router.post('/code')
async def code(body:Code,request:Request,user:Account):
    from fastapi import HTTPException
    await write_guard(request,user)
    if body.user_id!=user:raise HTTPException(409,'Your account changed. Reload before saving.')
    if body.enabled:await mfa.limit('referral-code:'+user)
    async with cursor() as cur:return await referrals.set_code(cur,user,body.expected_version,body.enabled)
