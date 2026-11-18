"""Web-only study-note authoring; existing post moderation owns publication."""
import hashlib,json
from typing import Annotated,Literal
from fastapi import APIRouter,Depends,Header,HTTPException,Query,Request,Response
from pydantic import BaseModel,ConfigDict,Field,field_validator,model_validator
from psycopg.types.json import Jsonb
from ..db import cursor
from ..deps import current_user,require_account
from ..services import study_posts as notes
from ..services.community_policy import policy,posting_guard,account_lock,HELPFUL_COUNT
from .materials import write_guard
from .discussions import Report,Toggle,event

router=APIRouter(prefix='/study-posts',tags=['study posts'])
User=Annotated[str,Depends(current_user)]
Account=Annotated[str,Depends(require_account)]
class Strict(BaseModel):model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)
class Reference(Strict):
    kind:Literal['question','material','paper','exam']
    id:str=Field(min_length=1,max_length=500)
class Note(Strict):
    kind:Literal['study','material-share']='study'
    body:str=Field(min_length=10,max_length=5000)
    topic_tag:str|None=Field(default=None,min_length=1,max_length=200)
    reference:Reference|None=None
    @model_validator(mode='after')
    def reviewed_material(self):
        if self.kind=='material-share' and (not self.reference or self.reference.kind!='material'):
            raise ValueError('A material share requires a published material link')
        return self
    @field_validator('body')
    @classmethod
    def text_only(cls,value):return notes.clean_body(value)
class Reply(Strict):
    body:str=Field(min_length=10,max_length=5000)
    @field_validator('body')
    @classmethod
    def text_only(cls,value):return notes.clean_body(value)
async def private(response:Response):response.headers['Cache-Control']='private, no-store'

@router.get('/status',dependencies=[Depends(private)])
async def status(user:User):
    async with cursor() as cur:
        state=await policy(cur,user)
        await cur.execute("SELECT id,label FROM review_taxonomy WHERE active AND level='subject' ORDER BY label,id")
        subjects=await cur.fetchall()
    return {**state,'subjects':subjects}

@router.post('',status_code=201,dependencies=[Depends(private)])
async def create(body:Note,request:Request,user:Account,idempotency_key:Annotated[str,Header(min_length=16,max_length=100)]):
    await write_guard(request,user)
    payload=body.model_dump()
    # Existing study retries retain the exact pre-share request hash contract.
    if body.kind=='study':payload.pop('kind')
    digest=hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()
    async with cursor() as cur:
        await cur.execute('SELECT pg_advisory_xact_lock(hashtext(%s))',('discussion:'+user,))
        await cur.execute('SELECT id,kind,request_hash,needs_approval FROM posts WHERE author_id=%s AND request_key=%s',(user,idempotency_key))
        old=await cur.fetchone()
        if old:
            if old['kind']!=body.kind or old['request_hash']!=digest:raise HTTPException(409,'This request key belongs to a different post')
            return {'id':old['id'],'needs_approval':old['needs_approval'],'replayed':True}
        state=await posting_guard(cur,user,study=True)
        if body.topic_tag:
            await cur.execute('SELECT 1 FROM review_taxonomy WHERE id=%s AND active',(body.topic_tag,))
            if not await cur.fetchone():raise HTTPException(422,'Choose an active subject or topic')
        link=body.reference.model_dump() if body.reference else None
        resolved=await notes.reference(cur,link,user)
        if resolved:link={'kind':resolved['kind'],'id':resolved['id']}
        context={'study_reference':link} if link else {}
        await cur.execute("INSERT INTO posts(kind,author_id,body,topic_tag,source_context,needs_approval,request_key,request_hash,material_id) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id",(body.kind,user,body.body,body.topic_tag,Jsonb(context),state['needs_approval'],idempotency_key,digest,link['id'] if body.kind=='material-share' else None))
        pid=(await cur.fetchone())['id']
        await event(cur,None,user,'material_shared' if body.kind=='material-share' else 'study_created',pid,{'needs_approval':state['needs_approval']})
    return {'id':pid,'needs_approval':state['needs_approval'],'replayed':False}

@router.get('/{pid}',dependencies=[Depends(private)])
async def read(pid:int,user:User):
    async with cursor() as cur:
        row=await notes.visible(cur,pid,user)
        await cur.execute('SELECT email IS NOT NULL AS registered FROM users WHERE id=%s',(user,))
        row['registered']=(await cur.fetchone())['registered']
    return row

@router.post('/{pid}/helpful',dependencies=[Depends(private)])
async def helpful(pid:int,body:Toggle,request:Request,user:Account):
    await write_guard(request,user)
    async with cursor() as cur:
        await account_lock(cur,user)
        p=await notes.visible(cur,pid,user)
        state=await policy(cur,user)
        if state['sanctioned']:raise HTTPException(403,'Your account is currently restricted from posting')
        if p['is_author']:raise HTTPException(403,'You cannot vote on your own post')
        await cur.execute('SELECT id,needs_approval,hidden FROM posts WHERE id=%s FOR UPDATE',(pid,));latest=await cur.fetchone()
        if latest['needs_approval'] or latest['hidden']:raise HTTPException(409,'This post is unavailable for voting')
        if body.enabled:await cur.execute('INSERT INTO post_votes(post_id,user_id,weight) VALUES(%s,%s,1) ON CONFLICT DO NOTHING',(pid,user))
        else:await cur.execute('DELETE FROM post_votes WHERE post_id=%s AND user_id=%s',(pid,user))
        await cur.execute('SELECT '+HELPFUL_COUNT+' AS n FROM posts p WHERE p.id=%s',(pid,))
        count=(await cur.fetchone())['n']
    return {'helpful':count,'voted':body.enabled}

@router.post('/{pid}/report',dependencies=[Depends(private)])
async def report(pid:int,body:Report,request:Request,user:Account):
    await write_guard(request,user)
    async with cursor() as cur:
        await account_lock(cur,user)
        p=await notes.visible(cur,pid,user)
        if p['is_author']:raise HTTPException(403,'Withdraw your own post instead')
        await cur.execute('INSERT INTO abuse_reports(post_id,reason,reporter_id,weight,note) VALUES(%s,%s,%s,1,%s) ON CONFLICT(post_id,reporter_id) DO NOTHING',(pid,body.reason,user,body.note))
    return {'reported':True}

@router.post('/{pid}/withdraw',dependencies=[Depends(private)])
async def withdraw(pid:int,request:Request,user:Account):
    await write_guard(request,user)
    async with cursor() as cur:
        await account_lock(cur,user)
        await cur.execute("SELECT id,hidden FROM posts WHERE id=%s AND author_id=%s AND kind IN ('study','material-share') FOR UPDATE",(pid,user))
        row=await cur.fetchone()
        if not row:raise HTTPException(404,'Your study note was not found')
        if not row['hidden']:
            await cur.execute("UPDATE posts SET hidden=true,hidden_by=%s,hidden_reason='Withdrawn by author' WHERE id=%s",(user,pid))
            await event(cur,None,user,'study_withdrawn',pid)
    return {'withdrawn':True}


@router.get('/{pid}/replies',dependencies=[Depends(private)])
async def replies(pid:int,user:User,offset:int=Query(0,ge=0,le=100000),limit:int=Query(20,ge=1,le=50)):
    async with cursor() as cur:
        await notes.conversation(cur,pid,user)
        await cur.execute('''SELECT p.id FROM posts p WHERE p.parent_id=%s AND p.kind='study'
          AND NOT p.hidden AND NOT p.before_fix AND (NOT p.needs_approval OR p.author_id=%s)
          AND NOT EXISTS(SELECT 1 FROM creator_blocks b WHERE (b.user_id=%s AND b.blocked_id=p.author_id)
            OR (b.user_id=p.author_id AND b.blocked_id=%s))
          ORDER BY p.created_at,p.id LIMIT %s OFFSET %s''',(pid,user,user,user,limit+1,offset))
        ids=await cur.fetchall()
        items=[await notes.visible(cur,row['id'],user) for row in ids[:limit]]
        state=await policy(cur,user)
    return {'items':items,'has_more':len(ids)>limit,'registered':state['registered'],
      'can_reply':state['registered'] and not state.get('sanctioned',False),
      'replies_remaining':state['replies_remaining'],'reply_limit':state['reply_limit']}

@router.post('/{pid}/replies',status_code=201,dependencies=[Depends(private)])
async def reply(pid:int,body:Reply,request:Request,user:Account,idempotency_key:Annotated[str,Header(min_length=16,max_length=100)]):
    await write_guard(request,user)
    digest=hashlib.sha256(json.dumps({'parent_id':pid,'body':body.body},sort_keys=True).encode()).hexdigest()
    async with cursor() as cur:
        await cur.execute('SELECT pg_advisory_xact_lock(hashtext(%s))',('discussion:'+user,))
        await account_lock(cur,user)
        parent=await notes.conversation(cur,pid,user,lock=True)
        await cur.execute('SELECT id,kind,parent_id,request_hash,needs_approval FROM posts WHERE author_id=%s AND request_key=%s',(user,idempotency_key))
        old=await cur.fetchone()
        if old:
            if old['kind']!='study' or old['parent_id']!=pid or old['request_hash']!=digest:
                raise HTTPException(409,'This request key belongs to a different post')
            return {'id':old['id'],'needs_approval':old['needs_approval'],'replayed':True}
        state=await posting_guard(cur,user,reply=True)
        await cur.execute('SELECT source_context,topic_tag FROM posts WHERE id=%s',(pid,));anchor=await cur.fetchone()
        await cur.execute('''INSERT INTO posts(kind,parent_id,author_id,body,source_context,topic_tag,needs_approval,request_key,request_hash)
          VALUES('study',%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id''',(pid,user,body.body,Jsonb(anchor['source_context']),anchor['topic_tag'],state['needs_approval'],idempotency_key,digest))
        rid=(await cur.fetchone())['id']
        await event(cur,None,user,'study_reply_created',rid,{'parent_id':pid,'needs_approval':state['needs_approval']})
    return {'id':rid,'needs_approval':state['needs_approval'],'replayed':False}
