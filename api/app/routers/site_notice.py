from datetime import datetime
from typing import Annotated
from fastapi import APIRouter,Depends,HTTPException,Response
from pydantic import BaseModel,ConfigDict,Field,field_validator
from ..db import cursor
from ..services import site_notice,mfa
from ..services.review_identity import Actor,identity,require_role

router=APIRouter(prefix='/api',tags=['site notice'])
Owner=Annotated[Actor,Depends(identity)]


class Notice(BaseModel):
    model_config=ConfigDict(extra='forbid')
    message:str=Field(max_length=500)
    expires_at:datetime|None=None
    expected_version:int=Field(ge=1,strict=True)

    @field_validator('message')
    @classmethod
    def text_only(cls,value):
        if any(ord(c)<32 and c not in '\n\t' or ord(c)==127 for c in value):raise ValueError('Use plain readable text')
        return value

    @field_validator('expires_at')
    @classmethod
    def timezone_required(cls,value):
        if value and value.tzinfo is None:raise ValueError('Expiry needs a timezone')
        return value


async def owner(cur,actor,*,read=False):
    if read:
        await cur.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
        await cur.execute("SET LOCAL statement_timeout='5s'")
    await require_role(cur,actor.id,roles=('owner',),lock=not read)
    if mfa.staff_required(actor.id) and not actor.mfa_verified:
        raise HTTPException(403,'Verify your authenticator in Account security before managing the site notice')


@router.get('/site-notice')
async def public(response:Response):
    response.headers['Cache-Control']='no-store'
    async with cursor() as cur:
        return await site_notice.public(cur)


@router.get('/admin/ops/notice')
async def setting(actor:Owner,response:Response):
    response.headers['Cache-Control']='private, no-store'
    async with cursor() as cur:
        await owner(cur,actor,read=True)
        return await site_notice.setting(cur)


@router.post('/admin/ops/notice')
async def save(body:Notice,actor:Owner,response:Response):
    response.headers['Cache-Control']='private, no-store'
    async with cursor() as cur:
        await owner(cur,actor)
        return await site_notice.save(cur,actor.id,body)
