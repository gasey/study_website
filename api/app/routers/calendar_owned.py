"""Account-owned calendar CRUD and revocable, hash-at-rest subscription URLs."""
import hashlib
import re
import secrets
from datetime import date
from typing import Annotated, Literal
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from ..config import settings
from ..db import cursor
from ..deps import require_account
from ..services import owned_calendar
from .materials import write_guard

router = APIRouter()
Account = Annotated[str, Depends(require_account)]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Entry(Strict):
    expected_version: int = Field(ge=0)
    date: date
    title: str = Field(min_length=1, max_length=180)
    note: str = Field(default='', max_length=3000)
    kind: Literal['personal','progress-test','exam-target'] = 'personal'
    recurrence: Literal[7,14] | None = None
    collection_id: str | None = Field(default=None, min_length=1, max_length=100)

    @field_validator('title','note')
    @classmethod
    def plain_text(cls, value):
        if any(ord(c)<32 and c not in '\r\n\t' for c in value) or '\x7f' in value:
            raise ValueError('Use plain text without control characters')
        return value

    @model_validator(mode='after')
    def valid(self):
        if not date(2000,1,1)<=self.date<=date(2100,12,31):
            raise ValueError('Choose a date between 2000 and 2100')
        if self.kind=='progress-test' and (self.recurrence is None or not self.collection_id):
            raise ValueError('A progress test needs a weekly or fortnightly cadence and an exam')
        if self.kind!='progress-test' and self.recurrence is not None:
            raise ValueError('Only progress tests repeat')
        return self


class Version(Strict):
    expected_version: int = Field(ge=0)


async def owner_lock(cur, user):
    # Serialize quotas, edits and feed rotation for this account, including absent rows.
    await cur.execute('SELECT id FROM users WHERE id=%s FOR UPDATE', (user,))


@router.post('/me/calendar/entries/{eid}')
async def save(eid: UUID, body: Entry, user: Account, request: Request):
    await write_guard(request,user)
    from ..services.v5_release import require_writes
    require_writes()
    async with cursor() as cur:
        await owner_lock(cur,user)
        await cur.execute('SELECT user_id,version FROM calendar_entries WHERE id=%s FOR UPDATE',(eid,))
        old=await cur.fetchone()
        if old and old['user_id']!=user:
            raise HTTPException(404,'Calendar entry not found')
        if (old['version'] if old else 0)!=body.expected_version:
            raise HTTPException(409,'This entry changed. Reload before saving.')
        if body.collection_id:
            await cur.execute("SELECT 1 FROM collections WHERE id=%s AND kind='exam' AND visibility='public'",(body.collection_id,))
            if not await cur.fetchone():
                raise HTTPException(422,'Choose an available public exam')
        await cur.execute("SELECT count(*) AS n,count(*) FILTER(WHERE kind='progress-test' AND id<>%s) AS slots FROM calendar_entries WHERE user_id=%s",(eid,user))
        counts=await cur.fetchone()
        if not old and counts['n']>=500 or body.kind=='progress-test' and counts['slots']>=20:
            raise HTTPException(409,'Calendar supports up to 500 entries and 20 recurring test slots')
        data=(body.date,body.title,body.note,body.kind,body.recurrence,body.collection_id)
        if old:
            await cur.execute('UPDATE calendar_entries SET date=%s,title=%s,note=%s,kind=%s,recurrence=%s,collection_id=%s,version=version+1,updated_at=clock_timestamp() WHERE id=%s AND user_id=%s RETURNING '+owned_calendar.FIELDS,(*data,eid,user))
        else:
            await cur.execute('INSERT INTO calendar_entries(date,title,note,kind,recurrence,collection_id,id,user_id) VALUES(%s,%s,%s,%s,%s,%s,%s,%s) RETURNING '+owned_calendar.FIELDS,(*data,eid,user))
        return await cur.fetchone()


@router.post('/me/calendar/entries/{eid}/delete')
async def delete(eid: UUID, body: Version, user: Account, request: Request):
    await write_guard(request,user)
    async with cursor() as cur:
        await owner_lock(cur,user)
        await cur.execute('SELECT version FROM calendar_entries WHERE id=%s AND user_id=%s FOR UPDATE',(eid,user))
        old=await cur.fetchone()
        if not old: raise HTTPException(404,'Calendar entry not found')
        if old['version']!=body.expected_version: raise HTTPException(409,'This entry changed. Reload before deleting.')
        await cur.execute('DELETE FROM calendar_entries WHERE id=%s AND user_id=%s',(eid,user))
    return {'deleted':True}


@router.get('/me/calendar/feed')
async def status(user: Account):
    async with cursor() as cur:
        await cur.execute('SELECT version,created_at,revoked_at,token_hash IS NOT NULL AS active FROM calendar_feed_tokens WHERE user_id=%s',(user,))
        return await cur.fetchone() or {'version':0,'active':False,'created_at':None,'revoked_at':None}


async def change_feed(cur,user,version,token):
    if token is not None:
        from ..services.v5_release import require_writes
        require_writes()
    await owner_lock(cur,user)
    await cur.execute('SELECT version FROM calendar_feed_tokens WHERE user_id=%s FOR UPDATE',(user,))
    old=await cur.fetchone()
    if (old['version'] if old else 0)!=version:
        raise HTTPException(409,'Calendar subscription changed. Reload before changing it.')
    digest=hashlib.sha256(token.encode()).hexdigest() if token else None
    await cur.execute('''INSERT INTO calendar_feed_tokens(user_id,token_hash,version,revoked_at)
      VALUES(%s,%s,%s,CASE WHEN %s::text IS NULL THEN clock_timestamp() END)
      ON CONFLICT(user_id) DO UPDATE SET token_hash=excluded.token_hash,version=excluded.version,
      created_at=clock_timestamp(),revoked_at=excluded.revoked_at''',(user,digest,version+1,digest))
    return {'version':version+1,'active':token is not None}


@router.post('/me/calendar/feed/rotate')
async def rotate(body: Version, user: Account, request: Request):
    await write_guard(request,user)
    token=secrets.token_urlsafe(32)
    async with cursor() as cur:
        result=await change_feed(cur,user,body.expected_version,token)
    return result | {'url':settings.public_origin.rstrip('/')+'/api/calendar/feed/'+token+'.ics'}


@router.post('/me/calendar/feed/revoke')
async def revoke(body: Version, user: Account, request: Request):
    await write_guard(request,user)
    async with cursor() as cur:
        return await change_feed(cur,user,body.expected_version,None)


@router.get('/calendar/feed/{token}.ics')
async def subscription(token: str):
    headers={'Cache-Control':'private, no-store','Referrer-Policy':'no-referrer',
             'X-Content-Type-Options':'nosniff','Content-Disposition':'inline; filename="finna-private.ics"'}
    if not re.fullmatch(r'[A-Za-z0-9_-]{43}',token):
        raise HTTPException(404,'Calendar feed unavailable',headers=headers)
    async with cursor() as cur:
        await cur.execute('''SELECT t.user_id FROM calendar_feed_tokens t JOIN users u ON u.id=t.user_id
          WHERE token_hash=%s AND revoked_at IS NULL AND u.email IS NOT NULL''',(hashlib.sha256(token.encode()).hexdigest(),))
        row=await cur.fetchone()
        if not row: raise HTTPException(404,'Calendar feed unavailable',headers=headers)
        content=await owned_calendar.subscription(cur,row['user_id'])
    return Response(content,media_type='text/calendar; charset=utf-8',headers=headers)
