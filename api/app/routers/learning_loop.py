"""Account-only reads and server-composed Smart Review sets."""
import hashlib
import json
from datetime import date
from typing import Annotated,Literal
from uuid import uuid4
from fastapi import APIRouter,Depends,HTTPException,Query,Request
from pydantic import BaseModel,ConfigDict,Field
from psycopg.types.json import Jsonb
from ..db import cursor
from ..deps import require_account,current_user
from ..services import mastery,review_queue
from .learning import not_assessed
from .study_sessions import state

router = APIRouter(tags=['learning loop'])
Account = Annotated[str,Depends(require_account)]


class Focus(BaseModel):
    model_config = ConfigDict(extra='forbid')
    subject_ids: list[str] = Field(max_length=5)


class ReviewStart(BaseModel):
    model_config = ConfigDict(extra='forbid')
    request_key: str = Field(min_length=16,max_length=100)
    size: int = Field(default=20,ge=1,le=20)
    focus_only: bool = False
    through: date | None = None
    item_type: Literal['all','question','vocab'] = 'all'
    deck_id: str|None = Field(default=None,max_length=100)


async def focus(cur,user):
    await cur.execute('''SELECT f.subject_id,s.label FROM user_focus_subjects f
      JOIN review_taxonomy s ON s.id=f.subject_id AND s.active AND s.level='subject'
      WHERE user_id=%s ORDER BY position''',(user,))
    return {'items':await cur.fetchall(),'limit':5}


@router.get('/api/me/mastery')
async def my_mastery(user:Account):
    async with cursor() as cur:
        return await mastery.snapshot(cur,user)


@router.get('/api/me/review-queue')
async def my_review_queue(user:Account,request:Request,limit:int=Query(50,ge=1,le=100),offset:int=Query(0,ge=0,le=100000),deck_id:str|None=Query(None,max_length=100)):
    from ..services.curated_sessions import supports_words
    from ..services import curated_release
    native=bool(getattr(request.state,'mobile_session',None))
    if deck_id and not supports_words(request):raise HTTPException(403,'This word-card queue needs the updated website')
    if deck_id and not curated_release.enabled():curated_release.require_writes()
    if native and deck_id:raise HTTPException(403,'Word-card queues are available on the website')
    async with cursor() as cur:
        return await review_queue.queue(cur,user,limit,offset,include_curated=supports_words(request) and curated_release.enabled(),deck=deck_id)


@router.get('/api/me/focus-subjects')
async def my_focus(user:Account):
    async with cursor() as cur:
        from ..services.today import focus_subjects,saved_exam
        return await focus_subjects(cur,user,await saved_exam(cur,user))


@router.get('/api/me/today')
async def my_today(user:Annotated[str,Depends(current_user)],request:Request):
    from ..services.today import compose
    from ..services.curated_sessions import supports_words
    from ..services.curated_release import enabled
    async with cursor() as cur:
        return await compose(cur,user,include_curated=supports_words(request) and enabled())


@router.patch('/api/me/focus-subjects')
async def save_focus(body:Focus,user:Account,request:Request):
    from ..services.mobile_identity import require_capability
    require_capability(request,'focus_subjects_write')
    if len(set(body.subject_ids)) != len(body.subject_ids):
        raise HTTPException(422,'Choose each subject once')
    async with cursor() as cur:
        await cur.execute('SELECT id FROM users WHERE id=%s FOR UPDATE',(user,))
        await cur.execute("SELECT id FROM review_taxonomy WHERE id=ANY(%s) AND active AND level='subject' FOR SHARE",(body.subject_ids,))
        if {r['id'] for r in await cur.fetchall()} != set(body.subject_ids):
            raise HTTPException(422,'Choose active subjects from the registry')
        await cur.execute('DELETE FROM user_focus_subjects WHERE user_id=%s',(user,))
        for position,subject in enumerate(body.subject_ids):
            await cur.execute('INSERT INTO user_focus_subjects(user_id,subject_id,position) VALUES(%s,%s,%s)',(user,subject,position))
        return await focus(cur,user)


@router.post('/api/review-sessions')
async def start_review(body:ReviewStart,user:Account,request:Request):
    from ..services.mobile_identity import require_capability
    require_capability(request,'review_sessions')
    payload=body.model_dump(mode='json')
    if body.deck_id is None:payload.pop('deck_id')
    native=bool(getattr(request.state,'mobile_session',None))
    from ..services.curated_sessions import supports_words
    if body.deck_id and not supports_words(request):raise HTTPException(403,'Word-card sessions need the updated website')
    if native and body.deck_id is not None:raise HTTPException(403,'Reviewed word-card sessions are available on the website')
    if body.item_type=='all':payload.pop('item_type')  # Preserve old start-request fingerprints.
    fingerprint = hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()
    async with cursor() as cur:
        await cur.execute('SELECT pg_advisory_xact_lock(hashtext(%s))',('study-start:'+user+':'+body.request_key,))
        await cur.execute('SELECT * FROM practice_study_sessions WHERE user_id=%s AND request_key=%s',(user,body.request_key))
        prior = await cur.fetchone()
        if prior:
            if prior['kind']!='review' or prior['request_hash']!=fingerprint:
                raise HTTPException(409,'This start request was already used for another study set')
            from ..services.curated_sessions import native_guard
            native_guard(prior,request)
            return await state(cur,prior,True)
        from ..services.learning_habit import capture_plan
        await capture_plan(cur,user)
        from ..services import curated_release
        if body.deck_id and not curated_release.enabled():curated_release.require_writes()
        rows=await review_queue.selection(cur,user,body.size,body.focus_only,body.through,body.item_type,body.deck_id,include_curated=supports_words(request) and curated_release.enabled())
        for item in rows:
            if item['curated']:item['paper_id']=None
            else:
                await cur.execute('SELECT paper_id FROM appearances WHERE canonical_id=%s ORDER BY is_primary DESC,id LIMIT 1',(item['item_id'],))
                item['paper_id']=(await cur.fetchone())['paper_id']
        if not rows:
            raise HTTPException(422,'No due questions are available for this review. Your full queue is still available.')
        await cur.execute('''INSERT INTO practice_study_sessions(id,user_id,collection_id,kind,request_key,request_hash,
          requested_size,question_ids,paper_ids,filters) VALUES(%s,%s,NULL,'review',%s,%s,%s,%s,%s,%s) RETURNING *''',
          (uuid4().hex,user,body.request_key,fingerprint,20 if body.size>10 else 10,
           [r['item_id'] for r in rows],[r['paper_id'] for r in rows],Jsonb({'focus_only':body.focus_only,'through':body.through.isoformat() if body.through else None,'item_type':body.item_type,'deck_id':body.deck_id,'has_curated':any(r['curated'] for r in rows)})))
        session=await cur.fetchone()
        for i,item in enumerate(rows):
            if item['curated']:
                from ..services.curated_sessions import freeze
                await freeze(cur,user,session['id'],item,i==0)
                continue
            await cur.execute('''INSERT INTO review_session_items(session_id,canonical_id,due_on,opened_at)
              VALUES(%s,%s,%s,CASE WHEN %s THEN clock_timestamp() ELSE NULL END)''',
              (session['id'],item['item_id'],item['due_on'],i==0))
        return await state(cur,session,True)


@router.get('/api/me/calendar-layers')
async def calendar_layers(start:date,end:date,user:Annotated[str,Depends(current_user)]):
    from .calendar import span,PUBLIC,JOIN
    span(start,end)
    async with cursor() as cur:
        await cur.execute('SELECT '+PUBLIC+JOIN+''' WHERE e.state='published'
          AND (e.collection_id IS NULL OR c.visibility='public') AND e.starts_on<=%s
          AND COALESCE(e.ends_on,e.starts_on)>=%s ORDER BY e.starts_on,e.id LIMIT 500''',(end,start))
        official=await cur.fetchall()
        forecast=[];habit=[];community=[];owned={"entries":[],"occurrences":[]}
        registered=await mastery.account(cur,user)
        if registered:
            from ..services import owned_calendar
            from ..services.calendar_schedule import community as schedule
            community=schedule(start,end)
            owned=await owned_calendar.layers(cur,user,start,end)
            forecast,habit=await owned_calendar.learning_layers(cur,user,start,end)
        return {'official':official,'forecast':forecast,'habit':habit,'community':community,
          'desk_schedule_available':False,'registered':registered,**owned,
          'forecast_basis':'Projected question reviews; dates shift as you answer. Overdue items are shown today.'}


from .learning import Account as OnboardingAccount

class OnboardingStart(BaseModel):
    model_config=ConfigDict(extra='forbid')
    request_key:str=Field(min_length=16,max_length=100)
    collection_id:str=Field(min_length=2,max_length=80)


def onboarding_account(request,user):
    if getattr(request.state,'mobile_session',None):raise HTTPException(403,'Exam check-ins are available on the website')
    if request.headers.get('x-learning-user')!=user:raise HTTPException(409,'Your signed-in account changed. Reload before continuing.')


@router.get('/api/me/onboarding')
async def onboarding_status(actor:OnboardingAccount,request:Request):
    user=actor.id
    from ..services import onboarding
    onboarding_account(request,user)
    async with cursor() as cur:return await onboarding.status(cur,user)


@router.post('/api/me/onboarding')
async def onboarding_start(body:OnboardingStart,actor:OnboardingAccount,request:Request):
    user=actor.id
    from ..services import onboarding
    onboarding_account(request,user)
    async with cursor() as cur:return await onboarding.start(cur,user,body.collection_id,body.request_key)


@router.get('/api/me/onboarding/{sid}/summary')
async def onboarding_summary(sid:str,actor:OnboardingAccount,request:Request):
    user=actor.id
    from ..services import onboarding
    onboarding_account(request,user)
    async with cursor() as cur:return await onboarding.summary(cur,user,sid)
