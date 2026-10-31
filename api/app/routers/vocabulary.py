"""Automatic answer-evidence scheduling. Recognition is not a word-mastery claim."""
from datetime import timedelta
from typing import Annotated,Literal
from uuid import uuid4
from fastapi import APIRouter,Depends,HTTPException,Query,Request,Response
from pydantic import BaseModel,ConfigDict,Field
from psycopg.types.json import Jsonb
from ..db import cursor
from ..exam_scope import ExamScope,DEFAULT_SCOPE
from ..services.review_identity import Actor,inbox_identity
from ..services.review_policy import digest
from ..services.bank_review import protect_answer
from ..services.scoring_revisions import capture_mock_questions
from ..source_files import source_pdf_url,figure_image_url

router=APIRouter(prefix='/api/vocabulary',tags=['vocabulary'])
POLICY='vocab-recognition-v1'
DAYS=[0,1,3,7,14,30,60]

def eligible_focus(scope):
    return "e.focus='all'" if scope=='all' else "e.focus='mizoram-recruitment'"

def learning_hash(snapshot):
    return digest({k:snapshot.get(k) for k in ['question','options','answer_text','answer_source','direction','passage','question_markup','options_markup','has_diagram','figure_image']})

async def account(request:Request,actor:Annotated[Actor,Depends(inbox_identity)]):
    expected=request.headers.get('x-vocabulary-user')
    if (expected and expected!=actor.id) or (request.method=='POST' and expected!=actor.id):
        raise HTTPException(409,'Your signed-in account changed. Reload before continuing.')
    return actor
Account=Annotated[Actor,Depends(account)]

class Resume(BaseModel):
    model_config=ConfigDict(extra='forbid')
    resume_id:str|None=Field(default=None,max_length=80)
    question_id:str|None=Field(default=None,max_length=100)

class Answer(BaseModel):
    model_config=ConfigDict(extra='forbid')
    chosen_index:int|None=Field(default=None,ge=0,le=5)
    action:Literal['answer','reveal','defer']='answer'

def private(response):response.headers['Cache-Control']='private, no-store'

def schedule(state,today,now,correct,action):
    stage=state['stage'];credit=state['last_credit_day']
    if action=='defer':return stage,now+timedelta(minutes=10),credit
    if correct is not True:return 0,now+timedelta(minutes=10),credit
    # A short repair is learning, not independent delayed retrieval.
    if stage==0:return 1,now+timedelta(days=1),today
    spaced=state['last_exposure_at'] is not None and now-state['last_exposure_at']>=timedelta(hours=24)
    if spaced and now>=state['due_at'] and credit!=today:stage=min(6,stage+1)
    return stage,now+timedelta(days=DAYS[stage]),today

async def locked_clock(cur,user):
    await cur.execute('SELECT pg_advisory_xact_lock(hashtext(%s))',('learning-session:'+user,))
    await cur.execute("SELECT clock_timestamp() AS now,(clock_timestamp() AT TIME ZONE 'Asia/Kolkata')::date AS today")
    return await cur.fetchone()

async def capture(cur,qid,scope):
    await cur.execute(f'SELECT e.appearance_id,e.score_version,e.appearance_version,e.primary_appearance_id,e.source_version FROM v_vocabulary_eligible e WHERE e.id=%s AND {eligible_focus(scope)}',(qid,))
    eligible=await cur.fetchone()
    if not eligible:return None
    await cur.execute('SELECT id FROM canonical_questions WHERE id=%s FOR SHARE',(qid,))
    rows=await capture_mock_questions(cur,[qid],[eligible['appearance_id']],'official')
    return {**rows[0]['snapshot'],'vocabulary_score_version':eligible['score_version'],'vocabulary_appearance_version':eligible['appearance_version'],'vocabulary_primary_appearance_id':eligible['primary_appearance_id'],'vocabulary_source_version':eligible['source_version']} if rows else None

async def card_payload(cur,card):
    snapshot=card['snapshot']
    await cur.execute('SELECT stage,seen,due_at FROM vocabulary_state WHERE user_id=%s AND question_id=%s',(card['user_id'],card['question_id']))
    state=await cur.fetchone()
    safe={k:snapshot.get(k) for k in ['question','direction','passage','question_markup','options_markup','options','page','answer_source']}
    order=card['display_order'];safe['options']=[snapshot['options'][i] for i in order]
    if safe.get('options_markup') and len(safe['options_markup'])==len(order):safe['options_markup']=[safe['options_markup'][i] for i in order]
    safe.update(figure_image_url=figure_image_url(snapshot.get('figure_image')),source_pdf_url=source_pdf_url(snapshot.get('source_file'),snapshot.get('pdf_url')))
    return {'id':card['id'],'question_id':card['question_id'],'exam_scope':card['exam_scope'],'expires_at':card['expires_at'],
            'question':safe,'stage':state['stage'],'seen':state['seen'],'policy':POLICY}

@router.get('/overview')
async def overview(actor:Account,response:Response,exam_scope:ExamScope=DEFAULT_SCOPE):
    private(response)
    async with cursor() as cur:
        await cur.execute(f'''SELECT count(*)::int AS eligible,
          count(*) FILTER(WHERE s.seen>0)::int AS started,
          count(*) FILTER(WHERE s.seen>0 AND (s.due_at<=now() OR s.score_version<>e.score_version OR s.appearance_version<>e.appearance_version OR s.appearance_id IS DISTINCT FROM e.primary_appearance_id))::int AS due,
          count(*) FILTER(WHERE s.stage>=5 AND s.score_version=e.score_version AND s.appearance_version=e.appearance_version AND s.appearance_id=e.primary_appearance_id)::int AS retaining,
          COALESCE(sum(s.graded),0)::int AS graded,COALESCE(sum(s.correct),0)::int AS correct,
          min(s.due_at) FILTER(WHERE s.seen>0 AND s.due_at>now()) AS next_due
          FROM v_vocabulary_eligible e LEFT JOIN vocabulary_state s ON s.question_id=e.id AND s.user_id=%s
          WHERE {eligible_focus(exam_scope)}''',(actor.id,))
        data=await cur.fetchone()
    return {**data,'policy':POLICY,'new_daily_target':10,'recognition_only':True}

@router.post('/card')
async def next_card(body:Resume,actor:Account,response:Response,exam_scope:ExamScope=DEFAULT_SCOPE):
    private(response)
    async with cursor() as cur:
        clock=await locked_clock(cur,actor.id)
        if body.resume_id:
            await cur.execute('SELECT * FROM vocabulary_cards WHERE id=%s AND user_id=%s AND exam_scope=%s',(body.resume_id,actor.id,exam_scope))
            saved=await cur.fetchone()
            if saved and saved['answered_at']:
                await protect_answer(cur,actor.id,saved['question_id'])
                return {'card':await card_payload(cur,saved),'result':saved['result'],'restored':True}
        await cur.execute('''SELECT * FROM vocabulary_cards WHERE user_id=%s AND exam_scope=%s
          AND answered_at IS NULL AND expires_at>%s ORDER BY issued_at DESC LIMIT 1 FOR UPDATE''',(actor.id,exam_scope,clock['now']))
        existing=await cur.fetchone()
        if existing:
            await protect_answer(cur,actor.id,existing['question_id'])
            current=await capture(cur,existing['question_id'],exam_scope)
            await cur.execute('SELECT version FROM vocabulary_state WHERE user_id=%s AND question_id=%s',(actor.id,existing['question_id']))
            version=await cur.fetchone()
            if current and digest(current)==existing['content_hash'] and version and version['version']==existing['state_version']:
                return {'card':await card_payload(cur,existing)}
            await cur.execute('UPDATE vocabulary_cards SET expires_at=%s WHERE id=%s',(clock['now'],existing['id']))
        await cur.execute("SELECT count(*)::int AS n FROM vocabulary_state WHERE user_id=%s AND (first_review_at AT TIME ZONE 'Asia/Kolkata')::date=%s",(actor.id,clock['today']))
        new_today=(await cur.fetchone())['n']
        await cur.execute(f'''SELECT e.id FROM v_vocabulary_eligible e LEFT JOIN vocabulary_state s ON s.question_id=e.id AND s.user_id=%s
          WHERE {eligible_focus(exam_scope)} AND (%s::text IS NULL OR e.id=%s) AND (s.question_id IS NULL OR s.due_at<=%s OR s.score_version<>e.score_version OR s.appearance_version<>e.appearance_version OR s.appearance_id IS DISTINCT FROM e.primary_appearance_id)
          AND (s.seen>0 OR %s<10)
          ORDER BY CASE WHEN s.seen>0 THEN 0 ELSE 1 END,s.due_at NULLS LAST,e.id LIMIT 30''',(actor.id,body.question_id,body.question_id,clock['now'],new_today))
        candidates=await cur.fetchall()
        for row in candidates:
            await protect_answer(cur,actor.id,row['id'])
            snapshot=await capture(cur,row['id'],exam_scope)
            if not snapshot:continue
            fingerprint=digest(snapshot)
            learned=learning_hash(snapshot)
            await cur.execute('''INSERT INTO vocabulary_state(user_id,question_id,content_hash,score_version,appearance_version,appearance_id) VALUES(%s,%s,%s,%s,%s,%s)
              ON CONFLICT(user_id,question_id) DO NOTHING''',(actor.id,row['id'],learned,snapshot['vocabulary_score_version'],snapshot['vocabulary_appearance_version'],snapshot['vocabulary_primary_appearance_id']))
            await cur.execute('SELECT * FROM vocabulary_state WHERE user_id=%s AND question_id=%s FOR UPDATE',(actor.id,row['id']))
            state=await cur.fetchone()
            if state['content_hash']!=learned:
                await cur.execute('''UPDATE vocabulary_state SET content_hash=%s,stage=0,due_at=%s,score_version=%s,appearance_version=%s,appearance_id=%s,version=version+1
                  WHERE user_id=%s AND question_id=%s RETURNING *''',(learned,clock['now'],snapshot['vocabulary_score_version'],snapshot['vocabulary_appearance_version'],snapshot['vocabulary_primary_appearance_id'],actor.id,row['id']))
                state=await cur.fetchone()
            await cur.execute('UPDATE vocabulary_state SET score_version=%s,appearance_version=%s,appearance_id=%s WHERE user_id=%s AND question_id=%s',
                (snapshot['vocabulary_score_version'],snapshot['vocabulary_appearance_version'],snapshot['vocabulary_primary_appearance_id'],actor.id,row['id']))
            cid='vcr_'+uuid4().hex
            order=list(range(len(snapshot['options'])))
            await cur.execute('''INSERT INTO vocabulary_cards(id,user_id,question_id,exam_scope,snapshot,display_order,content_hash,state_version)
              VALUES(%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *''',(cid,actor.id,row['id'],exam_scope,Jsonb(snapshot),order,fingerprint,state['version']))
            return {'card':await card_payload(cur,await cur.fetchone())}
    return {'card':None,'message':'No reviews are due in this focus. Your daily new-card target may already be complete.'}

@router.post('/cards/{cid}/answer')
async def answer(cid:str,body:Answer,actor:Account,response:Response):
    private(response)
    if (body.action=='answer') != (body.chosen_index is not None):raise HTTPException(422,'Choose an answer, reveal or defer')
    async with cursor() as cur:
        clock=await locked_clock(cur,actor.id)
        await cur.execute('SELECT * FROM vocabulary_cards WHERE id=%s AND user_id=%s FOR UPDATE',(cid,actor.id))
        card=await cur.fetchone()
        if not card:raise HTTPException(404,'Review card not found')
        await protect_answer(cur,actor.id,card['question_id'])
        if card['answered_at']:
            if card['chosen_index']!=body.chosen_index or card['action']!=body.action:raise HTTPException(409,'This card was already answered with another choice')
            return card['result']
        if card['expires_at']<=clock['now']:raise HTTPException(409,'This review expired. Load the next card; no result was recorded.')
        snapshot=await capture(cur,card['question_id'],card['exam_scope'])
        if not snapshot or digest(snapshot)!=card['content_hash']:
            raise HTTPException(409,'The source or key changed. Reload the review; no result was recorded.')
        await cur.execute('SELECT * FROM vocabulary_state WHERE user_id=%s AND question_id=%s FOR UPDATE',(actor.id,card['question_id']))
        state=await cur.fetchone()
        if not state or state['version']!=card['state_version']:raise HTTPException(409,'Another tab updated this review. Load your next card.')
        if body.chosen_index is not None and body.chosen_index>=len(snapshot['options']):raise HTTPException(422,'Choice is not one of the displayed options')
        chosen=None if body.chosen_index is None else snapshot['options'][card['display_order'][body.chosen_index]]
        correct=None if chosen is None else chosen==snapshot['answer_text']
        await cur.execute('SELECT max(at) AS recent FROM attempts WHERE user_id=%s AND canonical_id=%s',(actor.id,card['question_id']))
        recent=(await cur.fetchone())['recent']
        if recent and (state['last_exposure_at'] is None or recent>state['last_exposure_at']):state['last_exposure_at']=recent
        stage,due,credit=schedule(state,clock['today'],clock['now'],correct,body.action)
        attempt=None
        if chosen is not None:
            await cur.execute('''INSERT INTO attempts(user_id,canonical_id,correct,chosen_text,context,scoring_snapshot)
              VALUES(%s,%s,%s,%s,'review',%s) RETURNING id''',(actor.id,card['question_id'],correct,chosen,Jsonb(snapshot)))
            attempt=(await cur.fetchone())['id']
        await cur.execute('''UPDATE vocabulary_state SET stage=%s,due_at=%s,last_credit_day=%s,version=version+1,
          seen=seen+1,graded=graded+%s,correct=correct+%s,lapses=lapses+%s,last_review_at=%s,last_exposure_at=CASE WHEN %s THEN last_exposure_at ELSE %s END,first_review_at=COALESCE(first_review_at,%s)
          WHERE user_id=%s AND question_id=%s''',(stage,due,credit,int(chosen is not None),int(correct is True),int(correct is False),clock['now'],body.action=='defer',clock['now'],clock['now'],actor.id,card['question_id']))
        result={'correct':correct,'outcome':body.action if chosen is None else 'correct' if correct else 'wrong',
          'answer_text':None if body.action=='defer' else snapshot['answer_text'],'explanation':None if body.action=='defer' else snapshot.get('explanation'),'answer_source':snapshot['answer_source'],
          'next_due':due,'stage':stage,'policy':POLICY,'message':'Scheduled automatically from this answer. No confidence rating is needed.'}
        # JSONB round-trip gives the exact same response shape for every retry.
        result={**result,'next_due':due.isoformat()}
        await cur.execute('''UPDATE vocabulary_cards SET answered_at=%s,action=%s,chosen_index=%s,attempt_id=%s,result=%s WHERE id=%s''',
          (clock['now'],body.action,body.chosen_index,attempt,Jsonb(result),cid))
    return result
