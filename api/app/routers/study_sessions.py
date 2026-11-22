"""Bounded exam study, using the ordinary question/answer engine and receipts."""
import hashlib
import json
from time import perf_counter
from typing import Annotated, Literal
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, Response, Request
from pydantic import BaseModel, ConfigDict, Field
from psycopg.types.json import Jsonb
from ..db import cursor
from ..deps import current_user
from ..exam_scope import DEFAULT_SCOPE, pool_view
from ..schemas import AnswerSubmission
from ..services.bank_review import protect_answer
from ..services.study_feedback import saved_feedback_changes,presentation_digest
from ..services.question_readiness import reviewed_answer_sql
from ..source_files import figure_image_url
from .questions import list_questions, question_items, _COLS, _answer_question

User = Annotated[str, Depends(current_user)]
router = APIRouter(prefix='/api/study-sessions', tags=['study sessions'])

class Filters(BaseModel):
    model_config = ConfigDict(extra='forbid')
    subject_id: str | None = Field(default=None, min_length=2, max_length=100)
    topic_id: str | None = Field(default=None, min_length=2, max_length=160)
    subtopic_id: str | None = Field(default=None, min_length=2, max_length=160)
    paper_id: str | None = Field(default=None, min_length=1, max_length=500)
    section_path: str | None = Field(default=None, min_length=2, max_length=160)
    year_from: int | None = Field(default=None,ge=1900,le=2100)
    year_to: int | None = Field(default=None,ge=1900,le=2100)
    q: str | None = Field(default=None, min_length=2, max_length=120)
    study_status: Literal['all','unseen','answered','wrong','ever_wrong'] = 'all'
    pool: Literal['practice','scorable'] = 'practice'
    answer_status: Literal['official','verified','needs-review'] | None = None
    order: Literal['repeated','mixed'] = 'repeated'
    seed: str = Field(default='', max_length=64, pattern=r'^[A-Za-z0-9_-]*$')
    offset: int = Field(default=0, ge=0, le=100000)

class Start(BaseModel):
    model_config = ConfigDict(extra='forbid')
    request_key: str = Field(min_length=16, max_length=100)
    size: Literal[10,20] = 10
    collection_id: str = Field(default="udc", min_length=2, max_length=80)
    filters: Filters = Field(default_factory=Filters)
    review_session_id: str | None = Field(default=None, max_length=64)

class Move(BaseModel):
    model_config = ConfigDict(extra='forbid')
    version: int = Field(ge=1)
    position: int = Field(ge=0, le=19)

class Version(BaseModel):
    model_config = ConfigDict(extra='forbid')
    version: int = Field(ge=1)

class Check(Version):
    question_id: str = Field(min_length=1, max_length=100)
    chosen_index: int = Field(ge=0, le=9)
    presentation_hash: str | None = Field(default=None,pattern=r'^[0-9a-f]{64}$')

class Viewed(BaseModel):
    model_config = ConfigDict(extra='forbid')
    question_id: str = Field(min_length=1, max_length=100)


def receipt_key(sid, qid):
    return 'study:'+sid+':'+hashlib.sha256(qid.encode()).hexdigest()[:32]

async def owned(cur, sid, user, lock=False):
    await cur.execute('SELECT * FROM practice_study_sessions WHERE id=%s AND user_id=%s'+(' FOR UPDATE' if lock else ''),(sid,user))
    row = await cur.fetchone()
    if not row:
        raise HTTPException(404,'Study set not found for this account or browser')
    return row

def review_write_guard(row,request):
    from ..services.onboarding import native_guard as checkin_guard
    checkin_guard(row,request)
    from ..services.curated_sessions import native_guard
    native_guard(row,request)
    if row['kind']=='review':
        from ..services.mobile_identity import require_capability
        require_capability(request,'review_answers')

async def receipts(cur, row):
    keys = [receipt_key(row['id'], qid) for qid in row['question_ids']]
    # Attempts can be explicitly adopted from a proven guest. Ownership follows
    # the attempt, while immutable receipts retain their original identity.
    await cur.execute(f'''SELECT a.canonical_id,a.paper_id,a.chosen_text,a.scoring_snapshot,r.request_key,r.response,
      to_jsonb(q) AS current_question,to_jsonb(src) AS current_appearance,{reviewed_answer_sql('q')} AS current_reviewed
      FROM practice_request_receipts r JOIN attempts a ON a.id=r.attempt_id
      LEFT JOIN canonical_questions q ON q.id=a.canonical_id
      LEFT JOIN appearances src ON src.id=a.scoring_snapshot->>'appearance_id' AND src.canonical_id=a.canonical_id
      WHERE a.user_id=%s AND r.request_key=ANY(%s) AND a.collection_id IS NOT DISTINCT FROM %s
        AND a.context=%s AND a.at>=%s AND (%s::timestamptz IS NULL OR a.at<=%s)''',
      (row['user_id'],keys,row['collection_id'],row['kind'],row['created_at'],row['finished_at'],row['finished_at']))
    result = {}
    for item in await cur.fetchall():
        qid = item['canonical_id']
        if qid not in row['question_ids'] or item['request_key']!=receipt_key(row['id'],qid):
            continue
        if item['paper_id']!=row['paper_ids'][row['question_ids'].index(qid)]:
            continue
        await protect_answer(cur,row['user_id'],qid)
        snapshot = item['scoring_snapshot'] or {}
        options = snapshot.get('options') or []
        chosen = options.index(item['chosen_text']) if item['chosen_text'] in options else None
        result[qid] = {'result':item['response'],'chosen_index':chosen,'snapshot':snapshot,
            'updated_fields':saved_feedback_changes(snapshot,item['response'],
                (item['current_question']|{'reviewed_derived':item['current_reviewed']}) if item['current_question'] else None,item['current_appearance'])}
    from ..services.curated_sessions import receipts as word_receipts
    result.update(await word_receipts(cur,row))
    return result


def summary_for(row, checked):
    correct = sum(bool(item['result']['correct']) for item in checked.values())
    viewed = len(set(row['viewed_ids']) - set(checked))
    return {'correct':correct,'wrong':len(checked)-correct,'viewed':viewed,
            'skipped':len(row['question_ids'])-len(checked)-viewed,
            'unofficial':sum(not item['result']['verified'] and not item['result'].get('curated') for item in checked.values()),
            'total':len(row['question_ids']),
            **({'curated_checked':sum(bool(item['result'].get('curated')) for item in checked.values())}
               if (row.get('filters') or {}).get('has_curated') else {})}


def preview(row):
    return {key:row[key] for key in ('id','kind','collection_id','requested_size','filters','position','version','created_at','updated_at','finished_at','summary')} | {'total':len(row['question_ids'])}

async def state(cur, row, include_items=False):
    checked = await receipts(cur,row)
    result = preview(row) | {'viewed_ids':row['viewed_ids'],
        'results':{qid:{k:v for k,v in value.items() if k!='snapshot'} for qid,value in checked.items()},
        'summary':row['summary'] or summary_for(row,checked)}
    if include_items:
        # Read the exact saved IDs/sources, not a moving unseen/wrong queue.
        # Current holds still apply. Withdrawn/missing items become skipped slots.
        await cur.execute(f'''SELECT {_COLS},src.figure_image,COALESCE(src.has_diagram,false) AS has_diagram,
          src.paper_id AS source_paper_id,src.year AS source_year,src.exam AS source_exam,
          src.paper AS source_paper,src.qnum AS source_qnum,src.page AS source_page,
          src.series AS source_series,src.source_file,src.pdf_url
          FROM unnest(%(ids)s::text[],%(papers)s::text[]) WITH ORDINALITY chosen(selected_id,selected_paper,ord)
          JOIN v_all_questions v ON v.id=chosen.selected_id
          LEFT JOIN question_classifications qc ON qc.question_id=v.id AND qc.review_status='approved'
          JOIN LATERAL (
            SELECT a.figure_image,a.has_diagram,a.paper_id,a.qnum,a.page,a.series,
              p.year,p.exam_name AS exam,p.paper_number AS paper,p.source_file,p.pdf_url
            FROM appearances a JOIN papers p ON p.id=a.paper_id
            WHERE a.canonical_id=v.id AND a.paper_id=chosen.selected_paper
              AND (%(review)s OR EXISTS(SELECT 1 FROM collection_papers cp JOIN collections c
                ON c.id=cp.collection_id AND c.live_version=cp.version AND c.visibility='public'
                WHERE cp.paper_id=p.id AND cp.collection_id=%(collection)s))
            ORDER BY a.is_primary DESC,a.id LIMIT 1
          ) src ON TRUE ORDER BY chosen.ord''',{'ids':row['question_ids'],'papers':row['paper_ids'],'collection':row['collection_id'],'review':row['kind']=='review'})
        items = await question_items(cur,await cur.fetchall())
        items = [item.model_copy(update={'presentation_hash':presentation_digest(item.model_dump(mode='json'))}) for item in items]
        by_id = {item.id:item for item in items}
        for qid, answer in checked.items():
            item = by_id.get(qid)
            if item is None:
                continue
            snap = answer['snapshot']
            fields = {k:snap[k] for k in ('question','options','direction','passage','question_markup','options_markup') if k in snap}
            fields.update(answer_source=answer['result']['answer_source'],verified=answer['result']['verified'])
            # An older snapshot cannot inherit today's independent review badge.
            fields.update(answer_status=snap.get('answer_status') or ('official' if answer['result']['verified'] else 'needs-review'),
                          reviewed_derived=bool(snap.get('reviewed_derived',False)))
            if 'figure_image' in snap:
                fields['figure_image_url']=figure_image_url(snap['figure_image'])
            if 'has_diagram' in snap:
                fields['has_diagram']=bool(snap['has_diagram'])
            by_id[qid] = item.model_copy(update=fields)
        from ..services.curated_sessions import questions as word_questions
        by_id.update({q['id']:q for q in await word_questions(cur,row)})
        result['question_ids'] = row['question_ids']
        result['items'] = [by_id[qid] for qid in row['question_ids'] if qid in by_id]
    return result

async def candidates(body, user):
    # Explicit values are required when reusing a FastAPI handler: Query defaults
    # are parameter declarations, not usable Python default arguments.
    f = body.filters
    return await list_questions(pool=f.pool,answer_status=f.answer_status,q=f.q,
      year_from=f.year_from,year_to=f.year_to,source=None,subject_id=f.subject_id,topic_id=f.topic_id,
      study_area=None,shelf_id=None,learning_entry=None,subtopic_id=f.subtopic_id,collection_id=body.collection_id,
      section_path=f.section_path,paper_id=f.paper_id,essay_kind=None,
      study_status=f.study_status,order=f.order,seed=f.seed,repeats_only=False,origin='paper',
      limit=body.size,offset=f.offset,user_id=user,exam_scope=DEFAULT_SCOPE)

@router.post('')
async def start(body:Start,user:User,request:Request):
    async with cursor() as cur:
        await cur.execute("SELECT 1 FROM collections WHERE id=%s AND visibility='public' AND exam_scope_id=%s",(body.collection_id,DEFAULT_SCOPE))
        if not await cur.fetchone():
            raise HTTPException(404,"Published exam not found")
    # Keep legacy UDC request hashes stable for interrupted website requests.
    request_data = body.model_dump()
    if body.collection_id == "udc":
        request_data.pop("collection_id")
    for field in ("year_from","year_to"):
        if request_data["filters"].get(field) is None:
            request_data["filters"].pop(field,None)
    request_hash = hashlib.sha256(json.dumps(request_data,sort_keys=True).encode()).hexdigest()
    filters = body.filters.model_dump()
    if body.review_session_id:
        async with cursor() as cur:
            parent = await owned(cur,body.review_session_id,user)
            from ..services.onboarding import native_guard as checkin_guard
            checkin_guard(parent,request)
            if parent['collection_id'] != body.collection_id:
                raise HTTPException(422,'Review set belongs to another exam')
            checked = await receipts(cur,parent)
            await cur.execute(f'SELECT id FROM {pool_view("practice",DEFAULT_SCOPE)} WHERE id=ANY(%s)',(parent['question_ids'],))
            eligible = {r['id'] for r in await cur.fetchall()}
        ids = [qid for qid in parent['question_ids'] if qid in eligible and qid in checked and not checked[qid]['result']['correct']][:body.size]
        papers = [parent['paper_ids'][parent['question_ids'].index(qid)] for qid in ids]
        filters = {**parent['filters'],'study_status':'all','offset':0,'review_session_id':parent['id']}
        filters.pop('onboarding_version',None);filters.pop('exam_title',None)
    else:
        page = await candidates(body,user)
        items = [item for item in page.items if item.type=='mcq' and item.source_appearance]
        ids = [item.id for item in items]
        papers = [item.source_appearance.paper_id for item in items]
    async with cursor() as cur:
        await cur.execute('SELECT pg_advisory_xact_lock(hashtext(%s))',('study-start:'+user+':'+body.request_key,))
        await cur.execute('SELECT * FROM practice_study_sessions WHERE user_id=%s AND request_key=%s',(user,body.request_key))
        prior = await cur.fetchone()
        if prior:
            if prior['request_hash']!=request_hash:
                raise HTTPException(409,'This start request was already used for another study set')
            return await state(cur,prior,True)
        if not ids:
            raise HTTPException(422,'No answerable questions match this set. Change the subject or filters, or start from the beginning.')
        sid = uuid4().hex
        await cur.execute('''INSERT INTO practice_study_sessions(id,user_id,collection_id,request_key,request_hash,
          requested_size,question_ids,paper_ids,filters) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *''',
          (sid,user,body.collection_id,body.request_key,request_hash,body.size,ids,papers,Jsonb(filters)))
        return await state(cur,await cur.fetchone(),True)

@router.get('')
async def recent(user:User,collection_id:str="udc"):
    async with cursor() as cur:
        await cur.execute("(SELECT * FROM practice_study_sessions WHERE user_id=%s AND collection_id=%s AND NOT filters @> '{\"onboarding_version\":1}'::jsonb AND finished_at IS NULL ORDER BY updated_at DESC LIMIT 3) UNION ALL (SELECT * FROM practice_study_sessions WHERE user_id=%s AND collection_id=%s AND NOT filters @> '{\"onboarding_version\":1}'::jsonb AND finished_at IS NOT NULL ORDER BY updated_at DESC LIMIT 5) ORDER BY updated_at DESC",(user,collection_id,user,collection_id))
        return {'items':[preview(row) for row in await cur.fetchall()]}

@router.get('/{sid}')
async def read(sid:str,user:User,response:Response,request:Request):
    response.headers['Cache-Control']='private, no-store'
    async with cursor() as cur:
        row=await owned(cur,sid,user)
        from ..services.onboarding import native_guard as checkin_guard
        checkin_guard(row,request)
        from ..services.curated_sessions import native_guard
        native_guard(row,request)
        return await state(cur,row,True)

@router.post('/{sid}/position')
async def move(sid:str,body:Move,user:User,request:Request):
    async with cursor() as cur:
        row = await owned(cur,sid,user,True)
        review_write_guard(row,request)
        if row['finished_at'] or row['version']!=body.version:
            raise HTTPException(409,'This set changed in another tab. Reload its saved position.')
        if body.position>=len(row['question_ids']):
            raise HTTPException(422,'Choose a question in this set')
        if row['kind']=='review':
            from ..services.curated_sessions import position as word_position
            await word_position(cur,sid,row['question_ids'][body.position])
            await cur.execute('UPDATE review_session_items SET opened_at=clock_timestamp() WHERE session_id=%s AND canonical_id=%s AND attempt_id IS NULL',(sid,row['question_ids'][body.position]))
        await cur.execute('UPDATE practice_study_sessions SET position=%s,version=version+1,updated_at=clock_timestamp() WHERE id=%s RETURNING *',(body.position,sid))
        return await state(cur,await cur.fetchone())

@router.post('/{sid}/viewed')
async def viewed(sid:str,body:Viewed,user:User,request:Request):
    async with cursor() as cur:
        row = await owned(cur,sid,user,True)
        review_write_guard(row,request)
        if body.question_id not in row['question_ids']:
            raise HTTPException(422,'Question is not in this study set')
        if not row['finished_at'] and body.question_id not in row['viewed_ids']:
            from ..services import curated_sessions
            if await curated_sessions.is_card(cur,sid,body.question_id):
                if not await curated_sessions.was_revealed(cur,row,body.question_id):raise HTTPException(409,'Open the word-card answer before marking it as viewed')
            else:
                await protect_answer(cur,user,body.question_id)
                await cur.execute('SELECT 1 FROM answer_reveals WHERE user_id=%s AND canonical_id=%s',(user,body.question_id))
                if not await cur.fetchone():raise HTTPException(409,'Open the answer before marking it as viewed')
            await cur.execute('UPDATE practice_study_sessions SET viewed_ids=array_append(viewed_ids,%s),version=version+1,updated_at=clock_timestamp() WHERE id=%s RETURNING *',(body.question_id,sid))
            row = await cur.fetchone()
        return await state(cur,row)

@router.post('/{sid}/answer')
async def check(sid:str,body:Check,user:User,request:Request,response:Response):
    started=perf_counter()
    try:
        return await _check_answer(sid,body,user,request)
    finally:
        response.headers['Server-Timing']=f"answer;dur={(perf_counter()-started)*1000:.1f}"

async def _check_answer(sid:str,body:Check,user:User,request:Request):
    async with cursor() as cur:
        row = await owned(cur,sid,user,True)
        review_write_guard(row,request)
        if row['kind']=='review' and getattr(request.state,'mobile_session',None) and not body.presentation_hash:
            raise HTTPException(422,'Reload this review question before sending its saved choice')
        if body.question_id not in row['question_ids']:
            raise HTTPException(422,'Question is not in this study set')
        prior = (await receipts(cur,row)).get(body.question_id)
        if prior:
            if prior['chosen_index']!=body.chosen_index:
                raise HTTPException(409,'This question was already checked. Review its saved feedback.')
            return await state(cur,row)
        if row['finished_at'] or row['version']!=body.version or row['question_ids'][row['position']]!=body.question_id:
            raise HTTPException(409,'This set changed in another tab. Reload its saved position.')
        from ..services import curated_sessions
        if row['kind']=='review' and await curated_sessions.check(cur,row,body.question_id,body.chosen_index):
            await cur.execute('UPDATE practice_study_sessions SET version=version+1,updated_at=clock_timestamp() WHERE id=%s RETURNING *',(sid,))
            return await state(cur,await cur.fetchone())
        index = row['question_ids'].index(body.question_id)
        if body.presentation_hash:
            # Keep the displayed content stable through grading. Old clients
            # retain their API contract; the current UI always sends this token.
            await cur.execute('''SELECT a.id FROM appearances a JOIN canonical_questions q ON q.id=a.canonical_id
              WHERE q.id=%s AND a.paper_id=%s ORDER BY a.id FOR SHARE OF a,q''',
              (body.question_id,row['paper_ids'][index]))
            await cur.fetchall()
            current=await state(cur,row,True)
            question=next((q for q in current['items'] if not isinstance(q,dict) and q.id==body.question_id),None)
            if question is None or question.presentation_hash!=body.presentation_hash:
                raise HTTPException(409,'This question was edited after you opened it. Reload the set and choose again; no attempt was recorded.')
        await _answer_question(body.question_id,AnswerSubmission(chosen_index=body.chosen_index,
          collection_id=row['collection_id'],paper_id=row['paper_ids'][index],context=row['kind']),user,
          idempotency_key=receipt_key(sid,body.question_id),exam_scope='all' if row['kind']=='review' or (row.get('filters') or {}).get('onboarding_version')==1 else DEFAULT_SCOPE,_cur=cur)
        if row['kind']=='review':
            await cur.execute('''UPDATE review_session_items i SET attempt_id=r.attempt_id FROM practice_request_receipts r
              WHERE i.session_id=%s AND i.canonical_id=%s AND r.user_id=%s AND r.request_key=%s''',
              (sid,body.question_id,user,receipt_key(sid,body.question_id)))
        await cur.execute('UPDATE practice_study_sessions SET version=version+1,updated_at=clock_timestamp() WHERE id=%s RETURNING *',(sid,))
        return await state(cur,await cur.fetchone())

class WordReveal(Version):
    question_id:str=Field(min_length=1,max_length=150)

@router.post('/{sid}/word-reveal')
async def word_reveal(sid:str,body:WordReveal,user:User,request:Request):
    from ..services import curated_sessions
    async with cursor() as cur:
        row=await owned(cur,sid,user,True);review_write_guard(row,request)
        if row['kind']!='review' or row['finished_at'] or row['version']!=body.version or row['question_ids'][row['position']]!=body.question_id:
            raise HTTPException(409,'This saved set changed. Reload its current card.')
        await curated_sessions.reveal(cur,row,body.question_id)
        await cur.execute('UPDATE practice_study_sessions SET viewed_ids=CASE WHEN %s=ANY(viewed_ids) THEN viewed_ids ELSE array_append(viewed_ids,%s) END,version=version+1,updated_at=clock_timestamp() WHERE id=%s RETURNING *',(body.question_id,body.question_id,sid))
        return await state(cur,await cur.fetchone(),True)


@router.post('/{sid}/finish')
async def finish(sid:str,body:Version,user:User,request:Request):
    async with cursor() as cur:
        row = await owned(cur,sid,user,True)
        review_write_guard(row,request)
        if row['finished_at']:
            return await state(cur,row)
        if row['version']!=body.version:
            raise HTTPException(409,'This set changed in another tab. Reload before finishing.')
        # A reveal can succeed even if its UI acknowledgement is interrupted.
        # Reconcile server-recorded views before freezing the finish summary.
        await cur.execute('SELECT canonical_id FROM answer_reveals WHERE user_id=%s AND canonical_id=ANY(%s) AND revealed_at>=%s',(user,row['question_ids'],row['created_at']))
        row['viewed_ids']=list(dict.fromkeys([*row['viewed_ids'],*(r['canonical_id'] for r in await cur.fetchall())]))
        summary = summary_for(row,await receipts(cur,row))
        if row['kind']=='review':
            from ..services.mastery import prepare
            await prepare(cur,user,row['question_ids'])
        await cur.execute('UPDATE practice_study_sessions SET finished_at=clock_timestamp(),summary=%s,viewed_ids=%s,version=version+1,updated_at=clock_timestamp() WHERE id=%s RETURNING *',(Jsonb(summary),row['viewed_ids'],sid))
        row = await cur.fetchone()
        if row['kind']=='review':
            from ..services.learning_habit import review_finish
            summary['reward']=await review_finish(cur,row)
            await cur.execute('UPDATE practice_study_sessions SET summary=%s WHERE id=%s',(Jsonb(summary),sid))
            row['summary']=summary
            from ..services.mastery import refresh
            await cur.execute('SELECT user_id FROM learning_rollup_jobs WHERE user_id=%s FOR UPDATE',(user,))
            await refresh(cur,user,row['question_ids'],award_review_session=sid)
        return await state(cur,row)
