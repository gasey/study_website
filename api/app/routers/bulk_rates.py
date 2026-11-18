"""Web-only owner bulk pricing and explicit account group claims."""
import re
from typing import Annotated
from fastapi import APIRouter,Depends,HTTPException,Query
from pydantic import BaseModel,ConfigDict,Field,field_validator
from ..db import cursor
from ..services.review_identity import Actor,identity
from ..services.review_identity import require_role
from ..services import bulk_rates as service
from .learning import Account,private
router=APIRouter(prefix='/bulk',tags=['bulk pricing'],dependencies=[Depends(private)])
Staff=Annotated[Actor,Depends(identity)]

def email(value):
    value=value.strip().lower()
    if len(value)>254 or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',value):raise ValueError('Enter valid email addresses')
    return value

class Body(BaseModel):model_config=ConfigDict(extra='forbid')
class EmailBatch(Body):
    emails:list[str]=Field(min_length=1,max_length=100)
    note:str=Field(min_length=1,max_length=240)
    @field_validator('emails')
    @classmethod
    def normalized(cls,values):return sorted({email(v) for v in values})
    @field_validator('note')
    @classmethod
    def note_text(cls,v):
        if not v.strip():raise ValueError('Add a batch note')
        return v.strip()
class AddBatch(EmailBatch):
    request_key:str=Field(min_length=16,max_length=80,pattern=r'^[A-Za-z0-9_-]+$')
    preview_hash:str=Field(pattern=r'^[0-9a-f]{64}$')
class EmailState(Body):
    email:str
    expected_version:int=Field(ge=1)
    revoked:bool
    @field_validator('email')
    @classmethod
    def normalized(cls,v):return email(v)
class Code(Body):
    note:str=Field(min_length=1,max_length=240)
    max_uses:int=Field(default=100,ge=1,le=1000)
    days:int=Field(default=30,ge=1,le=90)
    request_key:str=Field(min_length=16,max_length=80,pattern=r'^[A-Za-z0-9_-]+$')
    @field_validator('note')
    @classmethod
    def note_text(cls,v):
        if not v.strip():raise ValueError('Add a group note')
        return v.strip()
class Version(Body):expected_version:int=Field(ge=1)
class Claim(Body):
    code:str=Field(min_length=24,max_length=24,pattern=r'^[A-Fa-f0-9]{24}$')
    expected_amount_paise:int=Field(ge=5000,le=10000)
    @field_validator('code')
    @classmethod
    def upper(cls,v):return v.upper()

@router.get('/admin')
async def admin(actor:Staff,q:str=Query(default='',max_length=254)):
    async with cursor() as cur:
        await require_role(cur,actor.id,roles=('owner',));return await service.list_admin(cur,q.strip())
@router.post('/admin/preview')
async def preview(body:EmailBatch,actor:Staff):
    async with cursor() as cur:
        await require_role(cur,actor.id,roles=('owner',));return await service.preview(cur,body.emails,body.note)
@router.post('/admin/emails')
async def add(body:AddBatch,actor:Staff):
    async with cursor() as cur:
        await require_role(cur,actor.id,roles=('owner',));return await service.add_emails(cur,actor.id,body.emails,body.note,body.request_key,body.preview_hash)
@router.post('/admin/email-state')
async def state(body:EmailState,actor:Staff):
    async with cursor() as cur:
        await require_role(cur,actor.id,roles=('owner',));return await service.email_state(cur,actor.id,body.email,body.expected_version,body.revoked)
@router.post('/admin/codes')
async def code(body:Code,actor:Staff):
    async with cursor() as cur:
        await require_role(cur,actor.id,roles=('owner',));return await service.create_code(cur,actor.id,body.note,body.max_uses,body.days,body.request_key)
@router.post('/admin/codes/{code}/revoke')
async def revoke(code:str,body:Version,actor:Staff):
    async with cursor() as cur:
        await require_role(cur,actor.id,roles=('owner',));return await service.revoke_code(cur,actor.id,code,body.expected_version)
@router.get('/me')
async def me(actor:Account):
    async with cursor() as cur:return {'amount_paise':await service.amount(cur,actor.id),'enabled':service.bulk_rate_release.enabled()}
@router.post('/claim')
async def claim(body:Claim,actor:Account):
    async with cursor() as cur:return await service.redeem(cur,actor.id,body.code,body.expected_amount_paise)

@router.get('/admin/codes/{code}/claims')
async def receipts(code:str,actor:Staff,after:str=Query(default='',max_length=100)):
    async with cursor() as cur:
        await require_role(cur,actor.id,roles=('owner',));return await service.claim_receipts(cur,code.upper(),after)
