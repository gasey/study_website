"""Typed structured content, independent of bank corrections and paid billing."""
from typing import Literal
from urllib.parse import urlparse
from pydantic import BaseModel,ConfigDict,Field,model_validator,field_validator
from fastapi import HTTPException
from psycopg.types.json import Jsonb
class Strict(BaseModel):model_config=ConfigDict(extra='forbid')
class Block(Strict):
    id:str=Field(min_length=1,max_length=80,pattern=r'^[a-zA-Z0-9_-]+$')
    type:Literal['heading','paragraph','callout','quote','list','table','image','link','question']
    text:str=Field(default='',max_length=12000)
    items:list[str]=Field(default_factory=list,max_length=50)
    rows:list[list[str]]=Field(default_factory=list,max_length=30)
    url:str=Field(default='',max_length=2000)
    alt:str=Field(default='',max_length=250)
    question_id:str|None=Field(default=None,max_length=150)
    @model_validator(mode='after')
    def bounded(self):
        if any(len(x)>1000 for x in self.items):raise ValueError('List item is too long')
        if any(len(row)>8 or any(len(x)>500 for x in row) for row in self.rows):raise ValueError('Tables allow 8 columns and 500 characters per cell')
        if self.url:
            parsed=urlparse(self.url)
            if parsed.scheme!='https' or not parsed.hostname or parsed.username or parsed.password:raise ValueError('Use a public HTTPS link')
        return self
class Document(Strict):
    title:str=Field(default='',max_length=180)
    summary:str=Field(default='',max_length=600)
    preview:str=Field(default='',max_length=5000)
    kind:Literal['note','article','guide','lesson']='note'
    access:Literal['free','pro','paid-preview']='free'
    price_paise:int=Field(default=0,ge=0,le=10000000)
    tags:list[str]=Field(default_factory=list,max_length=8)
    blocks:list[Block]=Field(default_factory=list,max_length=80)
    collection_id:str|None=Field(default=None,max_length=100)
    subject_id:str|None=Field(default=None,max_length=100)
    @field_validator('tags')
    @classmethod
    def tags_valid(cls,value):
        if any(not t.strip() or len(t)>40 for t in value):raise ValueError('Tags must contain 1–40 characters')
        return list(dict.fromkeys(t.strip() for t in value))
    @model_validator(mode='after')
    def unique_blocks(self):
        if len({b.id for b in self.blocks})!=len(self.blocks):raise ValueError('Each block needs a unique ID')
        return self
async def validate(cur,doc,publish=False):
    if doc.collection_id:
        await cur.execute("SELECT 1 FROM collections WHERE id=%s AND visibility='public'",(doc.collection_id,))
        if not await cur.fetchone():raise HTTPException(422,'Choose an existing public exam')
    if doc.subject_id:
        await cur.execute("SELECT 1 FROM review_taxonomy WHERE id=%s AND level='subject' AND active",(doc.subject_id,))
        if not await cur.fetchone():raise HTTPException(422,'Choose an active subject')
    for block in doc.blocks:
        if block.type=='question' and block.question_id:
            await cur.execute('SELECT 1 FROM canonical_questions WHERE id=%s AND status<>\'merged\'',(block.question_id,))
            if not await cur.fetchone():raise HTTPException(422,'Referenced bank question does not exist')
    if not publish:return
    if len(doc.title.strip())<5 or len(doc.summary.strip())<20 or not doc.blocks:raise HTTPException(422,'Add a title, a useful summary and at least one content block')
    if doc.access!='free' and len(doc.preview.strip())<40:raise HTTPException(422,'Member and paid-preview materials need a useful public excerpt')
    for block in doc.blocks:
        if block.type in {'heading','paragraph','callout','quote'} and not block.text.strip():raise HTTPException(422,'Finish or remove empty text blocks')
        if block.type=='list' and (not block.items or any(not x.strip() for x in block.items)):raise HTTPException(422,'Finish the list items')
        if block.type=='table' and (not block.rows or any(not r for r in block.rows) or len({len(r) for r in block.rows})!=1):raise HTTPException(422,'Tables need nonempty rows with the same column count')
        if block.type in {'image','link'} and (not block.url or (block.type=='image' and not block.alt.strip())):raise HTTPException(422,'Add an HTTPS URL and image alt text')
        if block.type=='question' and not block.question_id:raise HTTPException(422,'Choose a bank question for each question block')
async def event(cur,mid,actor,action,detail=None):
    await cur.execute('INSERT INTO material_events(material_id,actor_id,action,detail) VALUES(%s,%s,%s,%s)',(mid,actor,action,Jsonb(detail or {})))
async def owner(cur,user,lock=False):
    await cur.execute("SELECT 1 FROM review_grants WHERE user_id=%s AND role='owner' AND subject_id IS NULL AND revoked_at IS NULL"+(' FOR SHARE' if lock else ''),(user,));return bool(await cur.fetchone())
async def locked(cur,mid,user,version,staff=False):
    await cur.execute('SELECT * FROM materials WHERE id=%s FOR UPDATE',(mid,));row=await cur.fetchone()
    if not row or (row['author_id']!=user and not staff):raise HTTPException(404,'Material not found')
    if row['lock_version']!=version:raise HTTPException(409,'This material changed. Reload before saving')
    return row
async def readable(cur,row,user):
    if row['author_id']==user or (user and await owner(cur,user)):return True
    access=row['payload'].get('access','free')
    if access=='free':return True
    if access=='pro' and user:
        await cur.execute('SELECT account_has_pro(%s) AS pro',(user,));return (await cur.fetchone())['pro']
    return False


async def publication_reward(cur,row,reviewer,doc):
    # One independently reviewed first publication per India calendar day.
    # Self-publication, paid demos and already-published revisions never pay.
    if row['published_revision'] is not None or row['author_id']==reviewer or doc.access=='paid-preview':return
    user=row['author_id']
    await cur.execute('SELECT 1 FROM users WHERE id=%s AND email IS NOT NULL',(user,))
    if not await cur.fetchone():return
    await cur.execute('SELECT pg_advisory_xact_lock(hashtext(%s))',('rewards:'+user,))
    await cur.execute("SELECT 1 FROM material_reward_claims WHERE user_id=%s AND created_at>=(date_trunc('day',now() AT TIME ZONE 'Asia/Kolkata') AT TIME ZONE 'Asia/Kolkata')",(user,))
    if await cur.fetchone():return
    await cur.execute('INSERT INTO material_reward_claims(material_id,user_id,xp,points) VALUES(%s,%s,20,5) ON CONFLICT DO NOTHING RETURNING material_id',(row['id'],user))
    if not await cur.fetchone():return
    await cur.execute('INSERT INTO reward_profiles(user_id) VALUES(%s) ON CONFLICT DO NOTHING',(user,))
    await cur.execute("INSERT INTO reward_ledger(user_id,event_key,kind,xp,points,note) VALUES(%s,%s,'content',20,5,'First independently reviewed material publication')",(user,'cms-published:'+row['id']))

async def reverse_reward(cur,row):
    await cur.execute('SELECT pg_advisory_xact_lock(hashtext(%s))',('rewards:'+row['author_id'],))
    await cur.execute('UPDATE material_reward_claims SET reversed_at=now() WHERE material_id=%s AND reversed_at IS NULL RETURNING *',(row['id'],));claim=await cur.fetchone()
    if claim:await cur.execute("INSERT INTO reward_ledger(user_id,event_key,kind,xp,points,note) VALUES(%s,%s,'content',%s,%s,'Archived material publication reward reversal') ON CONFLICT DO NOTHING",(claim['user_id'],'cms-archived:'+row['id'],-claim['xp'],-claim['points']))
