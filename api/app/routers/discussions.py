"""One canonical question thread, immutable posts and ordinary correction citations."""
from typing import Annotated, Literal
import hashlib
import json
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator
from psycopg.types.json import Jsonb
from ..db import cursor
from ..deps import current_user, require_account
from ..services.bank_review import protect_answer
from ..services.review_identity import Actor, identity, require_role
from ..services.review_policy import safe_url
from .materials import write_guard
from .moderation import queue_items, moderate_post
from ..schemas import ModerationActionRequest

router = APIRouter(prefix='/api/community', tags=['question discussions'])
User = Annotated[str, Depends(current_user)]
Account = Annotated[str, Depends(require_account)]
Staff = Annotated[Actor, Depends(identity)]

class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
class Source(Strict):
    url: str = Field(max_length=2000)
    note: str = Field(min_length=3, max_length=1000)
    @field_validator('url')
    @classmethod
    def url_valid(cls, value):
        return safe_url(value)
class Context(Strict):
    paper_id: str | None = Field(default=None,max_length=500)
    collection_id: str | None = Field(default=None,max_length=100)
class Post(Strict):
    kind: Literal['doubt','explanation','reply']
    body: str = Field(min_length=10,max_length=5000)
    parent_id: int | None = Field(default=None,gt=0)
    context: Context = Field(default_factory=Context)
    sources: list[Source] = Field(default_factory=list,max_length=5)
class Toggle(Strict):
    enabled: bool
class Report(Strict):
    reason: Literal['spam','harassment','answer_leak','copyright','other']
    note: str = Field(min_length=10,max_length=2000)
class Lock(Strict):
    enabled: bool
    reason: str = Field(min_length=10,max_length=1000)

async def private(response: Response):
    response.headers['Cache-Control']='private, no-store'

async def event(cur,qid,user,action,pid=None,detail=None):
    await cur.execute('INSERT INTO discussion_events(canonical_id,post_id,actor_id,action,detail) VALUES(%s,%s,%s,%s,%s)',(qid,pid,user,action,Jsonb(detail or {})))

async def access(cur,qid,user,write=False):
    await protect_answer(cur,user,qid)
    await cur.execute("SELECT type,answer_text,options,status,source_defect FROM canonical_questions WHERE id=%s AND status IN ('live','held')",(qid,))
    q=await cur.fetchone()
    if not q: raise HTTPException(404,'Question not found')
    await cur.execute('SELECT 1 FROM attempts WHERE user_id=%s AND canonical_id=%s LIMIT 1',(user,qid));answered=bool(await cur.fetchone())
    exceptional=q['status']=='held' or q['source_defect'] in ('duplicate-options','unresolved-source') or q['type']!='mcq' or not q['answer_text'] or (q['options'] or []).count(q['answer_text'])!=1
    await cur.execute('SELECT 1 FROM discussion_disclosures WHERE user_id=%s AND canonical_id=%s',(user,qid));disclosed=bool(await cur.fetchone())
    allowed=answered or (exceptional and disclosed)
    await cur.execute('SELECT reason FROM thread_locks WHERE canonical_id=%s AND (until IS NULL OR until>now())',(qid,));lock=await cur.fetchone()
    if write:
        if not allowed:raise HTTPException(403,'Answer this question before joining its discussion, or open discussion for an unscored question')
        if lock:raise HTTPException(409,'Discussion is locked: '+(lock['reason'] or 'moderation review'))
        await cur.execute("SELECT 1 FROM sanctions WHERE user_id=%s AND kind IN ('mute','suspension') AND lifted_at IS NULL AND starts_at<=now() AND (ends_at IS NULL OR ends_at>now())",(user,))
        if await cur.fetchone():raise HTTPException(403,'Your account is currently restricted from discussion changes')
    return {'allowed':allowed,'can_disclose':exceptional and not allowed,'locked':bool(lock),'lock_reason':lock['reason'] if lock else None}

VISIBLE="""NOT p.hidden AND NOT p.before_fix AND (NOT p.needs_approval OR p.author_id=%s)
 AND NOT EXISTS(SELECT 1 FROM creator_blocks b WHERE (b.user_id=%s AND b.blocked_id=p.author_id) OR (b.user_id=p.author_id AND b.blocked_id=%s))"""
SELECT="""SELECT u.avatar,p.id,p.canonical_id,p.kind,p.parent_id,p.body,p.pinned,p.accepted,p.needs_approval,
 p.source_context,p.source_links,p.created_at,p.author_id,p.author_id=%s AS is_author,
 CASE WHEN p.author_id='team' THEN 'India Study Map' ELSE COALESCE(u.handle,'Learner') END AS author,
 (SELECT count(*)::int FROM post_votes v WHERE v.post_id=p.id) AS helpful,
 EXISTS(SELECT 1 FROM post_votes v WHERE v.post_id=p.id AND v.user_id=%s) AS voted
 FROM posts p LEFT JOIN users u ON u.id=p.author_id """
async def post_visible(cur,pid,user):
    await cur.execute(SELECT+' WHERE p.id=%s AND '+VISIBLE,(user,user,pid,user,user,user));p=await cur.fetchone()
    if not p:raise HTTPException(404,'Discussion post not found')
    a=await access(cur,p['canonical_id'],user)
    if not a['allowed']:raise HTTPException(403,'Answer the question before reading this discussion')
    if p['parent_id']:
        await cur.execute('SELECT 1 FROM posts p WHERE p.id=%s AND '+VISIBLE,(p['parent_id'],user,user,user))
        if not await cur.fetchone():raise HTTPException(404,'Discussion is unavailable')
    return p

@router.get('/questions/{qid}/discussion',dependencies=[Depends(private)])
async def thread(qid:str,user:User,focus:int|None=Query(None,gt=0),offset:int=Query(0,ge=0,le=100000),limit:int=Query(20,ge=1,le=50)):
    async with cursor() as cur:
        state=await access(cur,qid,user)
        await cur.execute('SELECT email IS NOT NULL AS registered FROM users WHERE id=%s',(user,));state['registered']=(await cur.fetchone())['registered']
        if not state['allowed']:return {**state,'items':[],'has_more':False}
        await cur.execute(SELECT+' WHERE p.canonical_id=%s AND p.parent_id IS NULL AND '+VISIBLE+' ORDER BY p.pinned DESC,p.created_at DESC,p.id DESC LIMIT %s OFFSET %s',(user,user,qid,user,user,user,limit+1,offset));rows=await cur.fetchall()
        focused=None
        if focus:
            post=await post_visible(cur,focus,user)
            if post['canonical_id']!=qid:raise HTTPException(404,'Post is not in this question discussion')
            focused=await post_visible(cur,post['parent_id'],user) if post['parent_id'] else post
    return {**state,'items':rows[:limit],'has_more':len(rows)>limit,'focused':focused}

@router.post('/questions/{qid}/discussion/open')
async def disclose(qid:str,request:Request,user:Account):
    await write_guard(request,user)
    async with cursor() as cur:
        state=await access(cur,qid,user)
        if not state['can_disclose'] and not state['allowed']:raise HTTPException(403,'Answer this question before opening its discussion')
        if state['can_disclose']:
            await cur.execute('INSERT INTO discussion_disclosures(user_id,canonical_id) VALUES(%s,%s) ON CONFLICT DO NOTHING',(user,qid))
    return {'opened':True}

async def source_context(cur,qid,ctx):
    result={}
    if ctx.paper_id:
        await cur.execute('SELECT a.id AS appearance_id,a.paper_id,a.qnum,a.page,p.exam_name,p.year FROM appearances a JOIN papers p ON p.id=a.paper_id WHERE a.canonical_id=%s AND a.paper_id=%s ORDER BY a.is_primary DESC,a.id LIMIT 1',(qid,ctx.paper_id));result=await cur.fetchone()
        if not result:raise HTTPException(422,'Source paper does not contain this question')
    if ctx.collection_id:
        await cur.execute("SELECT 1 FROM collections WHERE id=%s AND visibility='public'",(ctx.collection_id,))
        if not await cur.fetchone():raise HTTPException(422,'Exam context is unavailable')
        # A paper context is required to make the exam association verifiable.
        await cur.execute('SELECT 1 FROM collection_papers cp JOIN collections c ON c.id=cp.collection_id AND c.live_version=cp.version WHERE cp.collection_id=%s AND cp.paper_id=%s',(ctx.collection_id,ctx.paper_id))
        if not await cur.fetchone():raise HTTPException(422,'Paper is not part of this exam')
        result['collection_id']=ctx.collection_id
    return result

@router.post('/questions/{qid}/discussion',status_code=201)
async def create(qid:str,body:Post,request:Request,user:Account,idempotency_key:Annotated[str,Header(min_length=16,max_length=100)]):
    await write_guard(request,user)
    if (body.kind=='reply') != (body.parent_id is not None):raise HTTPException(422,'Replies require a parent; doubts and explanations start a topic')
    sha=hashlib.sha256(json.dumps({'qid':qid,**body.model_dump()},sort_keys=True).encode()).hexdigest()
    async with cursor() as cur:
        await cur.execute('SELECT pg_advisory_xact_lock(hashtext(%s))',('discussion:'+user,))
        await access(cur,qid,user,write=True)
        await cur.execute('SELECT id,request_hash,needs_approval FROM posts WHERE author_id=%s AND request_key=%s',(user,idempotency_key));old=await cur.fetchone()
        if old:
            if old['request_hash']!=sha:raise HTTPException(409,'This request key belongs to a different post')
            return {'id':old['id'],'needs_approval':old['needs_approval'],'replayed':True}
        context=await source_context(cur,qid,body.context)
        if body.parent_id:
            parent=await post_visible(cur,body.parent_id,user)
            if parent['canonical_id']!=qid or parent['parent_id'] or parent['needs_approval']:raise HTTPException(422,'Reply to a published top-level topic for this question')
            context=parent['source_context']
        await cur.execute("SELECT count(*)::int AS n FROM posts WHERE author_id=%s AND created_at>now()-interval '1 day'",(user,))
        if (await cur.fetchone())['n']>=30:raise HTTPException(429,'Daily discussion limit reached',headers={'Retry-After':'3600'})
        await cur.execute('SELECT count(*)::int AS n FROM posts WHERE author_id=%s AND NOT needs_approval AND NOT hidden',(user,));pending=(await cur.fetchone())['n']<3
        await cur.execute('INSERT INTO posts(canonical_id,kind,parent_id,author_id,body,needs_approval,request_key,request_hash,source_context,source_links) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id',(qid,body.kind,body.parent_id,user,body.body,pending,idempotency_key,sha,Jsonb(context),Jsonb([s.model_dump() for s in body.sources])));pid=(await cur.fetchone())['id']
        await event(cur,qid,user,'created',pid,{'needs_approval':pending})
        if not pending:await notify_reply(cur,pid)
    return {'id':pid,'needs_approval':pending,'replayed':False}

@router.get('/posts/{pid}/replies',dependencies=[Depends(private)])
async def replies(pid:int,user:User,focus:int|None=Query(None,gt=0),offset:int=Query(0,ge=0,le=100000),limit:int=Query(20,ge=1,le=50)):
    async with cursor() as cur:
        await post_visible(cur,pid,user)
        await cur.execute(SELECT+' WHERE p.parent_id=%s AND '+VISIBLE+' ORDER BY p.accepted DESC,p.created_at,p.id LIMIT %s OFFSET %s',(user,user,pid,user,user,user,limit+1,offset));rows=await cur.fetchall()
        focused=None
        if focus:
            focused=await post_visible(cur,focus,user)
            if focused['parent_id']!=pid:raise HTTPException(404,'Reply is not in this discussion topic')
    return {'items':rows[:limit],'has_more':len(rows)>limit,'focused':focused}

@router.post('/posts/{pid}/helpful')
async def helpful(pid:int,body:Toggle,request:Request,user:Account):
    await write_guard(request,user)
    async with cursor() as cur:
        p=await post_visible(cur,pid,user);await access(cur,p['canonical_id'],user,write=True)
        await cur.execute('SELECT id FROM posts WHERE id=%s FOR UPDATE',(pid,))
        if p['is_author']:raise HTTPException(403,'You cannot vote on your own post')
        if p['needs_approval']:raise HTTPException(409,'This post is awaiting moderation')
        if body.enabled:await cur.execute('INSERT INTO post_votes(post_id,user_id,weight) VALUES(%s,%s,1) ON CONFLICT DO NOTHING',(pid,user))
        else:await cur.execute('DELETE FROM post_votes WHERE post_id=%s AND user_id=%s',(pid,user))
        await cur.execute('SELECT count(*)::int AS n FROM post_votes WHERE post_id=%s',(pid,));n=(await cur.fetchone())['n']
        await cur.execute('UPDATE posts SET helpful=%s,helpful_w=%s WHERE id=%s',(n,n,pid))
    return {'helpful':n,'voted':body.enabled}

@router.post('/posts/{pid}/accept')
async def accept(pid:int,body:Toggle,request:Request,user:Account):
    await write_guard(request,user)
    async with cursor() as cur:
        p=await post_visible(cur,pid,user);await access(cur,p['canonical_id'],user,write=True)
        if not p['parent_id'] or p['needs_approval']:raise HTTPException(422,'Only a published reply can be accepted')
        await cur.execute('SELECT author_id,kind FROM posts WHERE id=%s FOR UPDATE',(p['parent_id'],));parent=await cur.fetchone()
        if parent['author_id']!=user or parent['kind']!='doubt' or p['is_author']:raise HTTPException(403,'Only the doubt author can accept another person’s reply')
        await cur.execute('SELECT accepted FROM posts WHERE id=%s',(pid,))
        if (await cur.fetchone())['accepted']==body.enabled:return {'accepted':body.enabled}
        if body.enabled:
            await cur.execute('UPDATE posts SET accepted=false WHERE parent_id=%s AND accepted',(p['parent_id'],))
        await cur.execute('UPDATE posts SET accepted=%s WHERE id=%s',(body.enabled,pid))
        if body.enabled:
            await cur.execute("INSERT INTO review_notifications(user_id,event_key,message,discussion_post_id,discussion_question_id) VALUES(%s,%s,'Your reply was accepted by the person who asked the doubt',%s,%s) ON CONFLICT DO NOTHING",(p['author_id'],'discussion-accepted:'+str(pid),pid,p['canonical_id']))
        await event(cur,p['canonical_id'],user,'accepted' if body.enabled else 'unaccepted',pid)
    return {'accepted':body.enabled}

@router.post('/posts/{pid}/report')
async def report(pid:int,body:Report,request:Request,user:Account):
    await write_guard(request,user)
    async with cursor() as cur:
        p=await post_visible(cur,pid,user)
        if p['is_author']:raise HTTPException(403,'Withdraw your own post instead')
        await cur.execute('INSERT INTO abuse_reports(post_id,reason,reporter_id,weight,note) VALUES(%s,%s,%s,1,%s) ON CONFLICT(post_id,reporter_id) DO NOTHING',(pid,body.reason,user,body.note))
    return {'reported':True}

@router.post('/posts/{pid}/withdraw')
async def withdraw(pid:int,request:Request,user:Account):
    await write_guard(request,user)
    async with cursor() as cur:
        await cur.execute('SELECT * FROM posts WHERE id=%s AND author_id=%s FOR UPDATE',(pid,user));p=await cur.fetchone()
        if not p:raise HTTPException(404,'Your post was not found')
        await protect_answer(cur,user,p['canonical_id'])
        if not p['hidden']:
            await cur.execute("UPDATE posts SET hidden=true,hidden_by=%s,hidden_reason='Withdrawn by author' WHERE id=%s",(user,pid))
            await event(cur,p['canonical_id'],user,'withdrawn',pid)
    return {'withdrawn':True}

@router.get('/posts/{pid}/evidence',dependencies=[Depends(private)])
async def evidence(pid:int,user:Account):
    async with cursor() as cur:
        p=await post_visible(cur,pid,user)
        if p['needs_approval']:raise HTTPException(409,'Wait for discussion moderation before citing this post')
    return {**p,'citation_note':'Community discussion by '+p['author']+': '+p['body'],'citation_path':'/bank/'+p['canonical_id']+'?post='+str(pid)+'#discussion'}

async def notify_reply(cur,pid):
    await cur.execute("""SELECT r.canonical_id,p.author_id FROM posts r JOIN posts p ON p.id=r.parent_id
      WHERE r.id=%s AND NOT r.hidden AND NOT r.needs_approval AND NOT p.hidden
      AND r.author_id<>p.author_id AND NOT EXISTS(SELECT 1 FROM creator_blocks b
      WHERE (b.user_id=r.author_id AND b.blocked_id=p.author_id) OR (b.user_id=p.author_id AND b.blocked_id=r.author_id))""",(pid,))
    row=await cur.fetchone()
    if row:await cur.execute("INSERT INTO review_notifications(user_id,event_key,message,discussion_post_id,discussion_question_id) VALUES(%s,%s,'Someone replied to your question discussion',%s,%s) ON CONFLICT DO NOTHING",(row['author_id'],'discussion-reply:'+str(pid),pid,row['canonical_id']))

@router.get('/admin/queue',dependencies=[Depends(private)])
async def queue(staff:Staff,tab:Literal['Reported','New users','My actions']='New users'):
    async with cursor() as cur:
        await require_role(cur,staff.id,roles=('owner',))
        result=await queue_items(cur,staff.id,tab,40)
        await cur.execute('SELECT unnest(question_ids) AS qid FROM mock_sessions WHERE user_id=%s AND submitted_at IS NULL',(staff.id,))
        protected={r['qid'] for r in await cur.fetchall()}
        result.items=[item for item in result.items if item.canonical_id not in protected]
    return result

@router.post('/admin/posts/{pid}/action')
async def moderate(pid:int,body:ModerationActionRequest,staff:Staff):
    return await moderate_post(pid,body,staff.id,session_owner=True)


@router.post('/admin/questions/{qid}/lock')
async def lock(qid:str,body:Lock,staff:Staff):
    async with cursor() as cur:
        await require_role(cur,staff.id,roles=('owner',))
        await cur.execute('SELECT id FROM canonical_questions WHERE id=%s FOR SHARE',(qid,))
        if not await cur.fetchone():raise HTTPException(404,'Question not found')
        if body.enabled:await cur.execute('INSERT INTO thread_locks(canonical_id,locked_by,reason) VALUES(%s,%s,%s) ON CONFLICT(canonical_id) DO UPDATE SET locked_by=EXCLUDED.locked_by,reason=EXCLUDED.reason,until=NULL',(qid,staff.id,body.reason))
        else:await cur.execute('DELETE FROM thread_locks WHERE canonical_id=%s',(qid,))
        await event(cur,qid,staff.id,'locked' if body.enabled else 'unlocked',detail={'reason':body.reason})
    return {'locked':body.enabled}
