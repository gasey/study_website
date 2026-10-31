from typing import Annotated,Literal
import hashlib,secrets
from fastapi import APIRouter,Depends,HTTPException,Query,Request,Header,Response
from pydantic import Field
from psycopg.types.json import Jsonb
from ..db import cursor
from ..deps import current_user,require_account
from ..services import content_studio as cms
from ..services.review_identity import identity,Actor,require_role
from .rewards import csrf
router=APIRouter(prefix='/api',tags=['content studio'])
User=Annotated[str,Depends(current_user)]
Account=Annotated[str,Depends(require_account)]
Staff=Annotated[Actor,Depends(identity)]
class Save(cms.Strict):
    expected_version:int=Field(ge=1)
    document:cms.Document
class Change(cms.Strict):
    expected_version:int=Field(ge=1)
    reason:str=Field(default='',max_length=2000)
class Review(Change):decision:Literal['publish','changes_requested','archive','restore']
class Reaction(cms.Strict):
    helpful:bool|None=None
    studied:bool|None=None
    saved:bool|None=None
class Report(cms.Strict):
    reason:Literal['incorrect','spam','copyright','other']
    note:str=Field(min_length=10,max_length=2000)
class Resolve(cms.Strict):
    reason:str=Field(min_length=10,max_length=2000)
async def private(response:Response):response.headers['Cache-Control']='private, no-store'
async def write_guard(request,user):
    csrf(request)
    # Atomic per-account budget, independently committed before mutations.
    async with cursor() as cur:
        await cur.execute("INSERT INTO review_rate_buckets(bucket,count,expires_at) VALUES(%s,1,now()+interval '1 minute') ON CONFLICT(bucket) DO UPDATE SET count=CASE WHEN review_rate_buckets.expires_at<=now() THEN 1 ELSE review_rate_buckets.count+1 END,expires_at=CASE WHEN review_rate_buckets.expires_at<=now() THEN now()+interval '1 minute' ELSE review_rate_buckets.expires_at END RETURNING count",('cms:'+user,));n=(await cur.fetchone())['count']
    if n>40:raise HTTPException(429,'Too many content changes. Try again in a minute',headers={'Retry-After':'60'})
SELECT_PUBLIC="""SELECT u.avatar,m.id,m.author_id,m.published_revision,m.published_at,m.lock_version,r.payload,COALESCE(cp.public,false) AS creator_public,
 CASE WHEN m.author_id='team' THEN 'India Study Map' ELSE COALESCE(u.handle,'Contributor') END AS author,
 (SELECT count(*)::int FROM material_votes v WHERE v.material_id=m.id AND v.helpful) AS helpful,
 (SELECT count(*)::int FROM material_votes v WHERE v.material_id=m.id AND v.studied) AS studied
 FROM materials m JOIN material_revisions r ON r.material_id=m.id AND r.revision=m.published_revision
 LEFT JOIN users u ON u.id=m.author_id LEFT JOIN creator_profiles cp ON cp.user_id=m.author_id """
async def published(cur,mid,user):
    await cur.execute(SELECT_PUBLIC+" WHERE m.id=%s AND m.status='published' AND NOT EXISTS(SELECT 1 FROM creator_blocks b WHERE (b.user_id=%s AND b.blocked_id=m.author_id) OR (b.user_id=m.author_id AND b.blocked_id=%s))",(mid,user,user));row=await cur.fetchone()
    if not row:raise HTTPException(404,'Published material not found')
    return row

@router.get('/materials',dependencies=[Depends(private)])
async def catalog(user:User,q:str=Query('',max_length=160),tag:str=Query('',max_length=40),access:Literal['all','free','pro','paid-preview']='all',sort:Literal['recent','helpful']='recent',collection_id:str|None=None,subject_id:str|None=None,shelf_id:str|None=Query(None,max_length=100),saved:bool=False,creator_id:str|None=Query(None,max_length=100),following:bool=False,offset:int=Query(0,ge=0,le=100000),limit:int=Query(12,ge=1,le=50)):
    async with cursor() as cur:
        if following:
            await cur.execute('SELECT 1 FROM users WHERE id=%s AND email IS NOT NULL',(user,))
            if not await cur.fetchone():raise HTTPException(401,'Sign in to see followed creators')
        where="""m.status='published' AND (%s='' OR r.payload->>'title' ILIKE %s OR r.payload->>'summary' ILIKE %s)
          AND (%s='' OR (r.payload->'tags') ? %s) AND (%s='all' OR r.payload->>'access'=%s)
          AND (%s::text IS NULL OR r.payload->>'collection_id'=%s) AND (%s::text IS NULL OR r.payload->>'subject_id'=%s OR (%s='gk-gs' AND r.payload->>'subject_id' IN ('general-knowledge','general-studies')))
          AND (NOT %s OR EXISTS(SELECT 1 FROM material_bookmarks b WHERE b.material_id=m.id AND b.user_id=%s))
          AND NOT EXISTS(SELECT 1 FROM creator_blocks b WHERE (b.user_id=%s AND b.blocked_id=m.author_id) OR (b.user_id=m.author_id AND b.blocked_id=%s))
          AND (%s::text IS NULL OR (m.author_id=%s AND (m.author_id=%s OR EXISTS(SELECT 1 FROM creator_profiles p WHERE p.user_id=m.author_id AND p.public))))
          AND (NOT %s OR EXISTS(SELECT 1 FROM creator_follows f JOIN creator_profiles p ON p.user_id=f.creator_id AND p.public WHERE f.follower_id=%s AND f.creator_id=m.author_id))"""
        where+=""" AND (%s::text IS NULL OR EXISTS(SELECT 1 FROM library_shelves s WHERE s.id=%s AND s.active AND
          (r.payload->>'subject_id'=ANY(s.match_ids) OR EXISTS(SELECT 1 FROM jsonb_array_elements_text(COALESCE(r.payload->'tags','[]')) tag WHERE lower(tag)=lower(s.title) OR tag=s.id OR tag=ANY(s.match_ids)))))"""
        args=(q,'%'+q+'%','%'+q+'%',tag,tag,access,access,collection_id,collection_id,subject_id,subject_id,subject_id,saved,user,user,user,creator_id,creator_id,user,following,user,shelf_id,shelf_id)
        await cur.execute('SELECT count(*)::int AS n FROM materials m JOIN material_revisions r ON r.material_id=m.id AND r.revision=m.published_revision WHERE '+where,args);total=(await cur.fetchone())['n']
        ordering='helpful DESC,m.published_at DESC,m.id' if sort=='helpful' else 'm.published_at DESC,m.id'
        # Public catalogs never select full bodies, even for their authors.
        sql=SELECT_PUBLIC.replace('r.payload,',"r.payload-'blocks' AS payload,")+" WHERE "+where+' ORDER BY '+ordering+' LIMIT %s OFFSET %s'
        await cur.execute(sql,(*args,limit,offset));rows=await cur.fetchall()
    return {'items':rows,'total':total}

@router.get('/materials/{mid}',dependencies=[Depends(private)])
async def read(mid:str,user:User,preview:bool=False):
    async with cursor() as cur:
        row=await published(cur,mid,user);allowed=not preview and await cms.readable(cur,row,user)
        payload=dict(row.pop('payload'))
        blocks=payload.pop('blocks',[])
        await cur.execute('SELECT helpful,studied FROM material_votes WHERE material_id=%s AND user_id=%s',(mid,user));reaction=await cur.fetchone()
        await cur.execute('SELECT 1 FROM material_bookmarks WHERE material_id=%s AND user_id=%s',(mid,user));saved=bool(await cur.fetchone())
    return {**row,'document':{**payload,'blocks':blocks if allowed else []},'can_read':allowed,'is_author':row['author_id']==user,'reaction':reaction or {'helpful':False,'studied':False},'saved':saved,'payments_enabled':False,'preview_mode':preview}

@router.post('/materials/{mid}/reaction')
async def react(mid:str,body:Reaction,request:Request,user:Account):
    await write_guard(request,user)
    async with cursor() as cur:
        row=await published(cur,mid,user)
        if body.helpful is not None or body.studied is not None:
            if row['author_id']==user:raise HTTPException(403,'Authors cannot upvote or mark their own material studied')
            if not await cms.readable(cur,row,user):raise HTTPException(403,'Full material access is needed before voting or marking studied')
            await cur.execute('INSERT INTO material_votes(material_id,user_id,helpful,studied,studied_at) VALUES(%s,%s,COALESCE(%s,false),COALESCE(%s,false),CASE WHEN %s THEN now() END) ON CONFLICT(material_id,user_id) DO UPDATE SET helpful=COALESCE(%s,material_votes.helpful),studied=COALESCE(%s,material_votes.studied),studied_at=CASE WHEN %s=true THEN COALESCE(material_votes.studied_at,now()) WHEN %s=false THEN NULL ELSE material_votes.studied_at END',(mid,user,body.helpful,body.studied,body.studied,body.helpful,body.studied,body.studied,body.studied))
        if body.saved is True:await cur.execute('INSERT INTO material_bookmarks(material_id,user_id) VALUES(%s,%s) ON CONFLICT DO NOTHING',(mid,user))
        elif body.saved is False:await cur.execute('DELETE FROM material_bookmarks WHERE material_id=%s AND user_id=%s',(mid,user))
    return {'saved':True}

@router.post('/materials/{mid}/report')
async def report(mid:str,body:Report,request:Request,user:Account):
    await write_guard(request,user)
    async with cursor() as cur:
        await published(cur,mid,user)
        await cur.execute('INSERT INTO material_reports(material_id,user_id,reason,note) VALUES(%s,%s,%s,%s) ON CONFLICT(material_id,user_id) DO UPDATE SET reason=EXCLUDED.reason,note=EXCLUDED.note,state=\'open\',resolution=NULL RETURNING id',(mid,user,body.reason,body.note));row=await cur.fetchone()
        await cms.event(cur,mid,user,'reported',{'report_id':row['id']})
    return row

@router.get('/studio/materials',dependencies=[Depends(private)])
async def mine(user:Account,offset:int=Query(0,ge=0,le=100000),limit:int=Query(20,ge=1,le=50)):
    async with cursor() as cur:
        await cur.execute('SELECT id,title,status,workflow_state,revision,lock_version,published_revision,updated_at,count(*) OVER()::int AS total FROM materials WHERE author_id=%s ORDER BY updated_at DESC,id LIMIT %s OFFSET %s',(user,limit,offset));rows=await cur.fetchall()
    return {'items':rows,'total':rows[0]['total'] if rows else 0}

@router.post('/studio/materials',status_code=201)
async def create(doc:cms.Document,request:Request,user:Account,idempotency_key:Annotated[str,Header(min_length=16,max_length=100)]):
    await write_guard(request,user)
    # Deterministic account/key identity avoids a second draft on retry.
    mid='mat_'+hashlib.sha256((user+':'+idempotency_key).encode()).hexdigest()[:32]
    async with cursor() as cur:
        await cur.execute('SELECT pg_advisory_xact_lock(hashtext(%s))',('cms-create:'+mid,))
        await cur.execute('SELECT id,lock_version FROM materials WHERE id=%s AND author_id=%s',(mid,user));existing=await cur.fetchone()
        if existing:
            await cur.execute('SELECT payload FROM material_revisions WHERE material_id=%s AND revision=1',(mid,));original=await cur.fetchone()
            if original['payload']!=doc.model_dump():raise HTTPException(409,'This save key was used for another draft. Reopen your saved draft')
            return existing
        await cms.validate(cur,doc)
        await cur.execute('INSERT INTO materials(id,author_id,title,tags,blocks) VALUES(%s,%s,%s,%s,%s)',(mid,user,doc.title,doc.tags,Jsonb([b.model_dump() for b in doc.blocks])))
        await cur.execute('INSERT INTO material_revisions(material_id,revision,payload,created_by) VALUES(%s,1,%s,%s)',(mid,Jsonb(doc.model_dump()),user));await cms.event(cur,mid,user,'created')
    return {'id':mid,'lock_version':1}

@router.get('/studio/materials/{mid}',dependencies=[Depends(private)])
async def draft(mid:str,user:Account):
    async with cursor() as cur:
        staff=await cms.owner(cur,user)
        await cur.execute('SELECT * FROM materials WHERE id=%s AND (author_id=%s OR %s)',(mid,user,staff));row=await cur.fetchone()
        if not row:raise HTTPException(404,'Material not found')
        await cur.execute('SELECT payload FROM material_revisions WHERE material_id=%s AND revision=%s',(mid,row['revision']));doc=(await cur.fetchone())['payload']
        await cur.execute('SELECT revision,created_at FROM material_revisions WHERE material_id=%s ORDER BY revision DESC LIMIT 30',(mid,));revisions=await cur.fetchall()
        await cur.execute('SELECT action,detail,created_at FROM material_events WHERE material_id=%s AND action<>\'reported\' ORDER BY id DESC LIMIT 30',(mid,));events=await cur.fetchall()
        await cur.execute("SELECT action,detail,created_at FROM material_events WHERE material_id=%s AND action IN ('publish','changes_requested','archive','restore') ORDER BY id DESC LIMIT 1",(mid,));feedback=await cur.fetchone()
    return {'feedback':feedback,'id':mid,'author_id':row['author_id'],'workflow_state':row['workflow_state'],'published_revision':row['published_revision'],'lock_version':row['lock_version'],'revision':row['revision'],'document':doc,'revisions':revisions,'events':events}

@router.get('/studio/materials/{mid}/revisions/{revision}',dependencies=[Depends(private)])
async def revision(mid:str,revision:int,user:Account):
    async with cursor() as cur:
        staff=await cms.owner(cur,user)
        await cur.execute('SELECT 1 FROM materials WHERE id=%s AND (author_id=%s OR %s)',(mid,user,staff))
        if not await cur.fetchone():raise HTTPException(404,'Material not found')
        await cur.execute('SELECT payload FROM material_revisions WHERE material_id=%s AND revision=%s',(mid,revision));row=await cur.fetchone()
        if not row:raise HTTPException(404,'Revision not found')
    return row['payload']

@router.post('/studio/materials/{mid}/save')
async def save(mid:str,body:Save,request:Request,user:Account):
    await write_guard(request,user)
    async with cursor() as cur:
        row=await cms.locked(cur,mid,user,body.expected_version,await cms.owner(cur,user,True))
        if row['workflow_state']=='archived':raise HTTPException(409,'Ask the CMS owner to restore archived material before editing')
        await cms.validate(cur,body.document)
        number=row['revision']+1
        await cur.execute('INSERT INTO material_revisions(material_id,revision,payload,created_by) VALUES(%s,%s,%s,%s)',(mid,number,Jsonb(body.document.model_dump()),user))
        await cur.execute('UPDATE materials SET title=%s,tags=%s,blocks=%s,revision=%s,lock_version=lock_version+1,workflow_state=\'draft\',updated_at=now() WHERE id=%s',(body.document.title,body.document.tags,Jsonb([b.model_dump() for b in body.document.blocks]),number,mid));await cms.event(cur,mid,user,'draft_saved',{'revision':number})
    return {'id':mid,'lock_version':body.expected_version+1,'revision':number}

@router.post('/studio/materials/{mid}/submit')
async def submit(mid:str,body:Change,request:Request,user:Account):
    await write_guard(request,user)
    async with cursor() as cur:
        row=await cms.locked(cur,mid,user,body.expected_version,await cms.owner(cur,user,True))
        if row['workflow_state'] not in {'draft','changes_requested'}:raise HTTPException(409,'Only a draft can be submitted')
        await cur.execute('SELECT payload FROM material_revisions WHERE material_id=%s AND revision=%s',(mid,row['revision']));doc=cms.Document.model_validate((await cur.fetchone())['payload']);await cms.validate(cur,doc,True)
        await cur.execute("UPDATE materials SET workflow_state='submitted',lock_version=lock_version+1,updated_at=now() WHERE id=%s",(mid,));await cms.event(cur,mid,user,'submitted',{'revision':row['revision']})
    return {'submitted':True,'lock_version':body.expected_version+1}

@router.get('/admin/bank/content',dependencies=[Depends(private)])
async def cms_queue(actor:Staff,state:Literal['all','submitted','published','draft','archived','changes_requested']='submitted',q:str=Query('',max_length=160),offset:int=Query(0,ge=0,le=100000),limit:int=Query(20,ge=1,le=50),order:Literal['oldest','newest']='oldest',material_report:int|None=Query(None,ge=1)):
    async with cursor() as cur:
        await require_role(cur,actor.id,roles=('owner',))
        where="(%s='all' OR m.workflow_state=%s) AND (%s='' OR m.title ILIKE %s OR m.id ILIKE %s OR u.handle ILIKE %s)"
        args=(state,state,q,'%'+q+'%','%'+q+'%','%'+q+'%')
        await cur.execute('SELECT count(*)::int AS n FROM materials m LEFT JOIN users u ON u.id=m.author_id WHERE '+where,args);total=(await cur.fetchone())['n']
        sorting='m.updated_at,m.id' if order=='oldest' else 'm.updated_at DESC,m.id'
        await cur.execute("SELECT m.id,m.title,m.author_id,m.workflow_state,m.published_revision,m.revision,m.lock_version,m.updated_at,COALESCE(u.handle,'India Study Map') AS author FROM materials m LEFT JOIN users u ON u.id=m.author_id WHERE "+where+' ORDER BY '+sorting+' LIMIT %s OFFSET %s',(*args,limit,offset));rows=await cur.fetchall()
        await cur.execute("SELECT r.id,r.material_id,r.reason,r.note,r.created_at,m.title FROM material_reports r JOIN materials m ON m.id=r.material_id WHERE r.state='open' AND (%s::bigint IS NULL OR r.id=%s) ORDER BY r.id LIMIT 50",(material_report,material_report));reports=await cur.fetchall()
    return {'items':rows,'total':total,'reports':reports}

@router.post('/admin/bank/content/{mid}/review')
async def review(mid:str,body:Review,actor:Staff):
    async with cursor() as cur:
        await require_role(cur,actor.id,roles=('owner',));row=await cms.locked(cur,mid,actor.id,body.expected_version,True)
        if body.decision=='publish':
            if row['workflow_state']!='submitted':raise HTTPException(409,'Review the submitted revision before publishing')
            await cur.execute('SELECT payload FROM material_revisions WHERE material_id=%s AND revision=%s',(mid,row['revision']));doc=cms.Document.model_validate((await cur.fetchone())['payload']);await cms.validate(cur,doc,True)
            await cur.execute("UPDATE materials SET status='published',workflow_state='published',published_revision=revision,published_at=now(),updated_at=now(),lock_version=lock_version+1 WHERE id=%s",(mid,))
            await cms.publication_reward(cur,row,actor.id,doc)
        else:
            if len(body.reason.strip())<10:raise HTTPException(422,'Explain this CMS decision')
            if body.decision=='changes_requested':
                if row['workflow_state']!='submitted':raise HTTPException(409,'This revision is not awaiting review')
                await cur.execute("UPDATE materials SET workflow_state='changes_requested',updated_at=now(),lock_version=lock_version+1 WHERE id=%s",(mid,))
            elif body.decision=='archive':
                await cur.execute("UPDATE materials SET status='removed',workflow_state='archived',updated_at=now(),lock_version=lock_version+1 WHERE id=%s",(mid,))
                await cms.reverse_reward(cur,row)
            else:
                if row['workflow_state']!='archived':raise HTTPException(409,'Only archived materials can be restored')
                await cur.execute("UPDATE materials SET status=CASE WHEN published_revision IS NULL THEN 'draft' ELSE 'published' END,workflow_state=CASE WHEN published_revision IS NULL THEN 'draft' ELSE 'published' END,updated_at=now(),lock_version=lock_version+1 WHERE id=%s",(mid,))
        await cms.event(cur,mid,actor.id,body.decision,{'reason':body.reason,'revision':row['revision']})
        await cur.execute("INSERT INTO review_notifications(user_id,material_id,event_key,message) SELECT id,%s,%s,%s FROM users WHERE id=%s AND id<>%s ON CONFLICT(event_key) DO NOTHING",(mid,'cms:'+mid+':'+str(body.expected_version)+':'+body.decision,'Your material received a CMS decision: '+body.decision.replace('_',' ')+'. Open the studio for the review notes.',row['author_id'],actor.id))
    return {'id':mid,'lock_version':body.expected_version+1}

@router.post('/admin/bank/content/reports/{rid}/resolve')
async def resolve(rid:int,body:Resolve,actor:Staff):
    async with cursor() as cur:
        await require_role(cur,actor.id,roles=('owner',))
        await cur.execute("UPDATE material_reports SET state='resolved',resolution=%s WHERE id=%s AND state='open' RETURNING material_id",(body.reason,rid));row=await cur.fetchone()
        if not row:raise HTTPException(409,'Report already resolved or missing')
        await cms.event(cur,row['material_id'],actor.id,'report_resolved',{'report':rid,'reason':body.reason})
    return {'resolved':True}
