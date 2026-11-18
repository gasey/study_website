"""Web identity editing. Existing native display-name editing remains compatible."""
from typing import Annotated
from fastapi import APIRouter,Depends,HTTPException,Request
from pydantic import BaseModel,ConfigDict,Field,field_validator
from ..db import cursor
from ..deps import require_account
from ..services import profile_identity
from .materials import private,write_guard

router=APIRouter(dependencies=[Depends(private)])
Account=Annotated[str,Depends(require_account)]
class Edit(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)
    user_id:str=Field(min_length=1,max_length=100)
    expected_version:int=Field(ge=0)
    name:str=Field(default='',max_length=60)
    handle:str=Field(min_length=1,max_length=100)
    bio:str=Field(default='',max_length=600) # Existing longer bios may be preserved unchanged.
    @field_validator('name','handle','bio')
    @classmethod
    def plain(cls,v,info):
        if any((ord(c)<32 and not (info.field_name=='bio' and c in '\n\t')) or ord(c)==127 for c in v):raise ValueError('Use plain text without control characters')
        return v

@router.get('/identity')
async def get(user:Account):
    async with cursor() as cur:return await profile_identity.read(cur,user)

@router.post('/identity')
async def save(body:Edit,request:Request,user:Account):
    await write_guard(request,user)
    if body.user_id!=user:raise HTTPException(409,'Your account changed. Reload before saving.')
    async with cursor() as cur:return await profile_identity.save(cur,user,body)
