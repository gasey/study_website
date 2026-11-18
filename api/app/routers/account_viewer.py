"""Owner account support: authenticated web sessions, existing MFA policy, reads only."""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query
from ..db import cursor
from ..services import account_viewer, mfa
from ..services.review_identity import Actor, identity, require_role
from .learning import private

router=APIRouter(prefix='/api/admin/users',tags=['account support'],dependencies=[Depends(private)])
Owner=Annotated[Actor,Depends(identity)]


async def guard(cur,actor):
    await cur.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
    await cur.execute("SET LOCAL statement_timeout='5s'")
    await require_role(cur,actor.id,roles=('owner',),lock=False)
    if mfa.staff_required(actor.id) and not actor.mfa_verified:
        raise HTTPException(403,'Verify your authenticator in Account security before viewing accounts')


@router.get('')
async def search(actor:Owner,q:str=Query(min_length=3,max_length=254,pattern=r'^[^\x00-\x1f\x7f]+$')):
    async with cursor() as cur:
        await guard(cur,actor)
        return await account_viewer.search(cur,q)


@router.get('/{user_id}')
async def account(user_id:str,actor:Owner):
    if len(user_id)>200 or any(ord(c)<32 or ord(c)==127 for c in user_id):
        raise HTTPException(404,'Registered account not found')
    async with cursor() as cur:
        await guard(cur,actor)
        return await account_viewer.snapshot(cur,user_id)
