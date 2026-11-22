"""Static-chapter Atlas lens and staff-only binding curation, without bank writes."""
import re
from typing import Annotated,Literal
from uuid import UUID
from fastapi import APIRouter,Depends,HTTPException,Query,Response
from pydantic import BaseModel,ConfigDict,Field
from ..db import cursor
from ..deps import current_user
from ..exam_scope import DEFAULT_SCOPE,ExamScope,pool_view
from ..services import atlas_bindings as atlas
from ..services.review_identity import Actor,identity,require_role
router=APIRouter(prefix='/api',tags=['Atlas'])
User=Annotated[str,Depends(current_user)]
Staff=Annotated[Actor,Depends(identity)]


async def owner(cur,actor):
    await require_role(cur,actor.id,roles=('owner',))
    from ..services.mfa import staff_required
    if staff_required(actor.id) and not actor.mfa_verified:
        raise HTTPException(403,'Verify your authenticator in Account security before opening Atlas curation')


class Strict(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)


class Binding(Strict):
    chapter_id:str=Field(min_length=1,max_length=100)
    layer_id:str|None=Field(default=None,min_length=1,max_length=100)
    event_id:str|None=Field(default=None,min_length=1,max_length=100)
    subject_id:str=Field(min_length=1,max_length=160)
    topic_id:str=Field(min_length=1,max_length=160)


class Save(Strict):
    expected_version:int=Field(ge=0)
    binding:Binding
    reason:str=Field(min_length=5,max_length=2000)


class Decision(Strict):
    expected_version:int=Field(ge=1)
    action:Literal['publish','hold','rollback']
    revision:int|None=Field(default=None,ge=1)
    reason:str=Field(min_length=5,max_length=2000)


@router.get('/atlas/chapters/{cid}/bindings')
async def public_bindings(cid:str,response:Response):
    response.headers['Cache-Control']='no-store'
    async with cursor() as cur:
        await atlas.current_chapter(cur,cid)
        await cur.execute("SELECT b.id,b.live FROM atlas_topic_bindings b WHERE "+atlas.LIVE+" AND b.live->>'chapter_id'=%(cid)s ORDER BY b.id",{'cid':cid,'atlas_hashes':atlas.HASHES})
        return {'items':[{'id':str(r['id']),**{k:r['live'].get(k) for k in ('chapter_id','layer_id','event_id','subject_id','topic_id')}} for r in await cur.fetchall()]}


@router.get('/atlas/questions/{qid}/links')
async def question_links(qid:str,user:User,response:Response,exam_scope:ExamScope=DEFAULT_SCOPE):
    response.headers['Cache-Control']='private, no-store'
    async with cursor() as cur:
        await cur.execute('SELECT id FROM '+pool_view('all',exam_scope)+' WHERE id=%s',(qid,))
        if not await cur.fetchone():return {'items':[]}
        return {'items':(await atlas.reverse(cur,[qid],user)).get(qid,[])}


@router.get('/admin/atlas/bindings')
async def admin_bindings(actor:Staff,response:Response,offset:int=Query(0,ge=0,le=2000)):
    response.headers['Cache-Control']='private, no-store'
    async with cursor() as cur:
        await owner(cur,actor)
        await cur.execute('SELECT * FROM atlas_topic_bindings ORDER BY updated_at DESC,id LIMIT 50 OFFSET %s',(offset,))
        rows=await cur.fetchall()
        for row in rows:
            await cur.execute('SELECT revision,action,actor_id,payload,reason,created_at FROM atlas_binding_versions WHERE binding_id=%s ORDER BY revision DESC LIMIT 100',(row['id'],))
            row['history']=await cur.fetchall()
        return {'items':rows,'chapters':await studio.catalog(cur),'offset':offset,'limit':50}


@router.get('/admin/atlas/topics')
async def topics(actor:Staff,response:Response,q:str=Query('',max_length=100),subject_id:str|None=Query(None,max_length=160)):
    response.headers['Cache-Control']='private, no-store'
    async with cursor() as cur:
        await owner(cur,actor)
        await cur.execute("SELECT id,label FROM review_taxonomy WHERE active AND level='subject' ORDER BY label,id")
        subjects=await cur.fetchall()
        await cur.execute("SELECT t.id,t.label,t.parent_id FROM review_taxonomy t JOIN review_taxonomy s ON s.id=t.parent_id AND s.active AND s.level='subject' WHERE t.active AND t.level='topic' AND (%s::text IS NULL OR t.parent_id=%s) AND (t.label ILIKE %s OR t.id ILIKE %s) ORDER BY t.label,t.id LIMIT 100",(subject_id,subject_id,'%'+q+'%','%'+q+'%'))
        return {'subjects':subjects,'topics':await cur.fetchall(),'limit':100}


@router.post('/admin/atlas/bindings/{bid}')
async def save_binding(bid:UUID,body:Save,actor:Staff):
    async with cursor() as cur:
        await owner(cur,actor)
        return await atlas.save(cur,bid,body.expected_version,body.binding.model_dump(),actor.id,body.reason)


@router.post('/admin/atlas/bindings/{bid}/decision')
async def decide_binding(bid:UUID,body:Decision,actor:Staff):
    async with cursor() as cur:
        await owner(cur,actor)
        return await atlas.decide(cur,bid,body.expected_version,body.action,actor.id,body.reason,body.revision)


@router.post('/admin/atlas/binding-preview')
async def preview_binding(body:Binding,actor:Staff):
    async with cursor() as cur:
        await owner(cur,actor)
        await atlas.validate(cur,body.model_dump(),fresh=True)
        await cur.execute('SELECT count(*)::int AS count FROM '+pool_view('all',DEFAULT_SCOPE)+" v WHERE EXISTS(SELECT 1 FROM v_question_paths p WHERE p.question_id=v.id AND p.subject_id=%s AND p.topic_id=%s)",(body.subject_id,body.topic_id))
        return {'count':(await cur.fetchone())['count'],'exam_scope':DEFAULT_SCOPE,'basis':'Approved live question paths; ordinary browse and assessment guards apply to learner results.'}

# Atlas uses the reviewed-content lifecycle without material rewards or paid access.
from ..services import atlas_studio as studio

class ChapterSave(Strict):
    expected_version:int=Field(ge=0)
    base_version:int=Field(ge=0)
    chapter:dict

class ChapterDecision(Strict):
    expected_version:int=Field(ge=1)
    action:Literal['publish','hold','rollback']
    draft_version:int|None=Field(default=None,ge=1)
    revision:int|None=Field(default=None,ge=1)
    preview_hash:str|None=Field(default=None,pattern=r'^[a-f0-9]{64}$')
    reason:str=Field(min_length=5,max_length=2000)

class ChapterPreview(Strict):
    expected_version:int=Field(ge=1)
    draft_version:int=Field(ge=1)

@router.get('/atlas/chapters')
async def chapters(response:Response):
    response.headers['Cache-Control']='no-store'
    async with cursor() as cur:
        return {'items':await studio.catalog(cur)}

@router.get('/atlas/chapters/{cid}')
async def chapter(cid:str,response:Response):
    response.headers['Cache-Control']='no-store'
    async with cursor() as cur:return await studio.published(cur,cid)

@router.get('/admin/atlas/chapters')
async def chapter_queue(actor:Staff,response:Response):
    response.headers['Cache-Control']='private, no-store'
    async with cursor() as cur:
        await owner(cur,actor)
        await cur.execute('''SELECT c.*,v.body->>'title' AS title,d.body->>'title' AS draft_title,
         d.version AS draft_version FROM atlas_chapters c LEFT JOIN atlas_chapter_versions v
         ON v.chapter_id=c.id AND v.revision=c.current_version LEFT JOIN atlas_drafts d
         ON d.chapter_id=c.id AND d.user_id=%s ORDER BY c.position,c.id LIMIT 500''',(actor.id,))
        return {'items':await cur.fetchall()}

@router.get('/admin/atlas/chapters/{cid}')
async def chapter_workspace(cid:str,actor:Staff,response:Response):
    response.headers['Cache-Control']='private, no-store'
    async with cursor() as cur:
        await owner(cur,actor);return await studio.workspace(cur,cid,actor.id)

@router.get('/admin/atlas/chapters/{cid}/versions/{revision}')
async def chapter_version(cid:str,revision:int,actor:Staff,response:Response):
    response.headers['Cache-Control']='private, no-store'
    async with cursor() as cur:
        await owner(cur,actor)
        await cur.execute('SELECT body FROM atlas_chapter_versions WHERE chapter_id=%s AND revision=%s',(cid,revision));row=await cur.fetchone()
        if not row:raise HTTPException(404,'Atlas revision not found')
        return row

@router.post('/admin/atlas/chapters/{cid}/draft')
async def chapter_save(cid:str,body:ChapterSave,actor:Staff):
    async with cursor() as cur:
        await owner(cur,actor);return await studio.save(cur,cid,actor.id,body.expected_version,body.base_version,body.chapter)

@router.post('/admin/atlas/chapters/{cid}/preview')
async def chapter_preview(cid:str,body:ChapterPreview,actor:Staff):
    async with cursor() as cur:
        await owner(cur,actor);row=await studio.workspace(cur,cid,actor.id)
        if row['lock_version']!=body.expected_version or row['draft_base']!=body.expected_version or row['draft_version']!=body.draft_version:raise HTTPException(409,'Save your current draft and resolve publication changes first')
        doc=studio.validate(row['body']);h=studio.digest(doc)
        await studio.event(cur,cid,actor.id,'preview',detail={'body_hash':h,'draft_version':body.draft_version,'base_version':body.expected_version})
        return {'body':doc,'body_hash':h,'draft_version':body.draft_version}

@router.post('/admin/atlas/chapters/{cid}/decision')
async def chapter_decision(cid:str,body:ChapterDecision,actor:Staff):
    async with cursor() as cur:
        await owner(cur,actor);return await studio.decide(cur,cid,actor.id,body.expected_version,body.action,body.reason,body.draft_version,body.revision,body.preview_hash)


from .learning import Account as DrillAccount
from ..services import atlas_drills as activity
from ..services import atlas_context as context

@router.get('/atlas/me/index')
async def atlas_exam_index(actor:DrillAccount,response:Response):
    response.headers['Cache-Control']='private, no-store'
    async with cursor() as cur:return await context.exam_catalog(cur,actor.id)

@router.get('/atlas/chapters/{cid}/chronicle')
async def atlas_chronicle(cid:str,user:User,response:Response):
    response.headers['Cache-Control']='private, no-store'
    async with cursor() as cur:return await context.chapter_chronicle(cur,user,cid)

@router.get('/atlas/chronicle/{eid}/links')
async def chronicle_atlas(eid:str,user:User,response:Response):
    response.headers['Cache-Control']='private, no-store'
    if not re.fullmatch(r'date_[0-9a-f]{20}',eid):raise HTTPException(422,'Choose a dated Chronicle entry')
    async with cursor() as cur:return await context.chronicle_chapters(cur,user,eid)

@router.get('/admin/atlas/chronicle-source/{qid}')
async def chronicle_snapshot(qid:str,actor:Staff,response:Response):
    response.headers['Cache-Control']='private, no-store'
    from .current_affairs import no_assessment
    async with cursor() as cur:
        await owner(cur,actor);await no_assessment(cur,actor.id)
        rows=await context.anchors(cur,[qid])
        if qid not in rows:raise HTTPException(404,'Choose an available dated Chronicle entry')
        return rows[qid]

@router.get('/admin/atlas/district-proposals')
async def district_proposals(actor:Staff,response:Response):
    response.headers['Cache-Control']='private, no-store'
    async with cursor() as cur:await owner(cur,actor)
    return {'items':[{'id':d['id'],'title':d['title'],'district':d['district']} for d in context.district_proposals()['chapters']]}

@router.post('/admin/atlas/district-proposals/{cid}/draft')
async def district_draft(cid:str,actor:Staff):
    doc=next((d for d in context.district_proposals()['chapters'] if d['id']==cid),None)
    if not doc:raise HTTPException(404,'District proposal unavailable')
    async with cursor() as cur:
        await owner(cur,actor)
        return await studio.save(cur,cid,actor.id,0,0,doc)

class Viewed(Strict):
    body_hash:str=Field(pattern=r'^[a-f0-9]{64}$')
    layers:list[str]=Field(max_length=80)

class DrillStart(Strict):
    body_hash:str=Field(pattern=r'^[a-f0-9]{64}$')
    drill_id:str=Field(min_length=1,max_length=320)
    request_key:UUID

class MapChoice(Strict):
    lat:float=Field(ge=-90,le=90,allow_inf_nan=False)
    lng:float=Field(ge=-180,le=180,allow_inf_nan=False)

@router.get('/atlas/me/progress')
async def atlas_progress(actor:DrillAccount,response:Response):
    response.headers['Cache-Control']='private, no-store'
    async with cursor() as cur:return await activity.progress(cur,actor.id)

@router.get('/atlas/me/suggestions')
async def atlas_suggestions(actor:DrillAccount,response:Response):
    response.headers['Cache-Control']='private, no-store'
    from ..services.today import saved_exam
    async with cursor() as cur:return {'items':await activity.suggestions(cur,actor.id,await saved_exam(cur,actor.id))}

@router.get('/atlas/chapters/{cid}/activity')
async def atlas_activity(cid:str,actor:DrillAccount,response:Response):
    response.headers['Cache-Control']='private, no-store'
    async with cursor() as cur:return await activity.state(cur,actor.id,cid)

@router.post('/atlas/chapters/{cid}/viewed')
async def atlas_viewed(cid:str,body:Viewed,actor:DrillAccount):
    async with cursor() as cur:return await activity.view(cur,actor.id,cid,body.body_hash,body.layers)

@router.post('/atlas/chapters/{cid}/drills')
async def atlas_drill_start(cid:str,body:DrillStart,actor:DrillAccount):
    async with cursor() as cur:return await activity.start(cur,actor.id,cid,body.drill_id,body.body_hash,body.request_key)

@router.post('/atlas/drills/{pid}/answer')
async def atlas_drill_answer(pid:UUID,body:MapChoice,actor:DrillAccount):
    async with cursor() as cur:return await activity.answer(cur,actor.id,pid,body.model_dump())

@router.get('/atlas/questions/{qid}/context')
async def question_map_context(qid:str,user:User,response:Response,exam_scope:ExamScope=DEFAULT_SCOPE):
    response.headers['Cache-Control']='private, no-store'
    from ..services.question_readiness import answer_status_sql
    from .learning import not_assessed
    async with cursor() as cur:
        await cur.execute('''SELECT DISTINCT av.body,b.live->>'layer_id' AS layer_id,b.live->>'event_id' AS event_id
          FROM canonical_questions q JOIN v_question_paths p ON p.question_id=q.id
          JOIN atlas_topic_bindings b ON p.subject_id=b.live->>'subject_id' AND p.topic_id=b.live->>'topic_id'
          JOIN atlas_chapters ac ON ac.id=b.live->>'chapter_id'
          JOIN atlas_chapter_versions av ON av.chapter_id=ac.id AND av.revision=ac.current_version
          WHERE q.id=%(qid)s AND q.id IN(SELECT id FROM '''+pool_view('all',exam_scope)+''')
          AND av.body->>'subject'='geography' AND '''+answer_status_sql('q')+''' IN ('official','verified')
          AND '''+not_assessed('q')+' AND '+atlas.LIVE+''' ORDER BY av.body LIMIT 3''',{'qid':qid,'user':user})
        return {'items':await cur.fetchall(),'basis':'Map context only; the original question and ordinary scoring remain authoritative.'}
