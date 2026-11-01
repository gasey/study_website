"""Account-owned continuation and daily revision over the existing bank engine."""
import re
from typing import Annotated
from urllib.parse import urlsplit,parse_qsl,urlencode
from uuid import uuid4
from fastapi import APIRouter,Depends,HTTPException,Request,Response,Query
from pydantic import BaseModel,ConfigDict,Field,field_validator
from ..db import cursor
from ..exam_scope import ExamScope,DEFAULT_SCOPE,question_scope
from ..services.review_identity import Actor,inbox_identity
from ..services.bank_review import protect_answer
from .vocabulary import eligible_focus

async def account(request:Request,actor:Annotated[Actor,Depends(inbox_identity)]):
    expected=request.headers.get('x-learning-user')
    if expected!=actor.id:raise HTTPException(409,'Your signed-in account changed. Reload before continuing.')
    return actor
Account=Annotated[Actor,Depends(account)]
def private(response:Response):response.headers['Cache-Control']='private, no-store'
router=APIRouter(prefix='/api/learning',tags=['learning workflows'],dependencies=[Depends(private)])
ALLOWED_KEYS={'study_area','collection','paper','status','answer_status','exam_scope','subject_id','topic_id','subtopic_id','collection_id','section_path','paper_id','pool','offset','limit','view','subject','topic','section','q','year_from','year_to','study_status','tab','paper_label','shelf_id','origin','source','essay_kind','answer_mode'}
def safe_route(value):
    url=urlsplit(value)
    if url.scheme or url.netloc or not re.fullmatch(r'/(?:bank(?:/[A-Za-z0-9_-]+)?|group-b|english|mizo|arithmetic|essay|desk|library/(?:subjects|topics)/[A-Za-z0-9_-]+|exams/[A-Za-z0-9_-]+)',url.path):
        raise ValueError('Choose an internal practice route')
    pairs=parse_qsl(url.query)
    if any(k not in ALLOWED_KEYS or len(v)>600 or any(ord(c)<32 for c in v) for k,v in pairs):raise ValueError('Unsupported practice filter')
    return url.path+('?' + urlencode(pairs) if pairs else '')
class Checkpoint(BaseModel):
    model_config=ConfigDict(extra='forbid')
    route:str=Field(max_length=2000)
    question_id:str|None=Field(default=None,max_length=100)
    appearance_id:str|None=Field(default=None,max_length=600)
    expected_version:int=Field(ge=0)
    @field_validator('route')
    @classmethod
    def valid_route(cls,v):return safe_route(v)

@router.post('/checkpoint')
async def checkpoint(body:Checkpoint,actor:Account):
    async with cursor()as cur:
        await cur.execute('SELECT id FROM users WHERE id=%s FOR UPDATE',(actor.id,))
        await cur.execute("SELECT version FROM learning_checkpoints WHERE user_id=%s AND kind='practice' FOR UPDATE",(actor.id,));old=await cur.fetchone()
        if (old['version'] if old else 0)!=body.expected_version:raise HTTPException(409,'Another tab saved a newer practice position. Reload before saving.')
        if body.question_id:
            await cur.execute("SELECT 1 FROM canonical_questions WHERE id=%s AND status='live'",(body.question_id,))
            if not await cur.fetchone():raise HTTPException(404,'Question unavailable')
        if body.appearance_id:
            await cur.execute('SELECT 1 FROM appearances WHERE id=%s AND canonical_id=%s',(body.appearance_id,body.question_id))
            if not await cur.fetchone():raise HTTPException(422,'The source appearance does not belong to this question')
        await cur.execute('''INSERT INTO learning_checkpoints(user_id,kind,route,question_id,appearance_id) VALUES(%s,'practice',%s,%s,%s)
          ON CONFLICT(user_id,kind) DO UPDATE SET route=EXCLUDED.route,question_id=EXCLUDED.question_id,appearance_id=EXCLUDED.appearance_id,version=learning_checkpoints.version+1,updated_at=now() RETURNING version''',
          (actor.id,body.route,body.question_id,body.appearance_id));return await cur.fetchone()

@router.get('/resume')
async def resume(actor:Account,exam_scope:ExamScope=DEFAULT_SCOPE):
    async with cursor()as cur:
        await cur.execute('''SELECT m.id,m.collection_id,m.current_position,m.section_path,m.paper_id,m.started_at,
          GREATEST(0,m.duration_seconds-extract(epoch FROM now()-m.started_at))::int AS seconds_remaining,
          c.title,cardinality(m.question_ids) AS total FROM mock_sessions m JOIN collections c ON c.id=m.collection_id
          WHERE m.user_id=%s AND m.submitted_at IS NULL ORDER BY m.started_at DESC''',(actor.id,));mocks=await cur.fetchall()
        await cur.execute("SELECT c.*,q.question,q.status FROM learning_checkpoints c LEFT JOIN canonical_questions q ON q.id=c.question_id WHERE c.user_id=%s AND kind='practice'",(actor.id,));cp=await cur.fetchone()
        await cur.execute('''SELECT id,exam_scope,issued_at FROM vocabulary_cards WHERE user_id=%s AND answered_at IS NULL
          AND expires_at>now() AND exam_scope=%s ORDER BY issued_at DESC LIMIT 1''',(actor.id,exam_scope));vocab=await cur.fetchone()
        await cur.execute("SELECT id,desk_id,state,created_at,duration_seconds,elapsed_seconds,CASE WHEN resumed_at IS NULL THEN 0 ELSE extract(epoch FROM now()-resumed_at)::int END AS running_seconds FROM study_focus_sessions WHERE user_id=%s AND state IN ('running','paused')",(actor.id,));focus=await cur.fetchone()
        await cur.execute("SELECT document->'tasks' AS tasks FROM personal_desks WHERE user_id=%s",(actor.id,));desk=await cur.fetchone()
    items=[]
    for m in mocks:
        items.append({'kind':'mock','title':m['title'],'detail':f"Question {m['current_position']+1} of {m['total']} · "+('time elapsed; submit your saved work' if m['seconds_remaining']==0 else f"{m['seconds_remaining']//60} minutes remaining"),
          'url':'/exams/'+m['collection_id']+'/mock','updated_at':m['started_at']})
    if cp:
        available=not cp['question_id'] or cp['status']=='live'
        url=cp['route']
        if cp['question_id']:url=cp['route']+('&' if '?' in cp['route'] else '?')+'resume_question='+cp['question_id']+'#question-'+cp['question_id']
        items.append({'kind':'practice','title':'Continue practice','detail':cp['question'] if available and cp['question'] else 'Return to your saved filters' if available else 'This question is unavailable. Choose another question.',
          'url':url if available else '/library','updated_at':cp['updated_at']})
    if vocab:items.append({'kind':'vocabulary','title':'Vocabulary review','detail':'Resume the saved card; its server expiry still applies.','url':'/vocabulary?'+urlencode({'review':vocab['id'],'exam_scope':vocab['exam_scope']}),'updated_at':vocab['issued_at']})
    if focus:
        left=max(0,focus['duration_seconds']-focus['elapsed_seconds']-focus['running_seconds'])
        items.append({'kind':'focus','title':'Focus session','detail':f"{focus['state']} · {left//60} minutes remaining" if left else 'Timer finished; close your saved session.',
          'url':('/desk/'+focus['desk_id'] if focus['desk_id'] else '/desk')+'?tab=focus','updated_at':focus['created_at']})
    tasks=[t for t in (desk or {}).get('tasks') or [] if not t.get('done')]
    if tasks:items.append({'kind':'desk','title':'Your next desk task','detail':tasks[0]['text'],'url':'/desk','updated_at':None})
    return {'items':items,'checkpoint_version':cp['version'] if cp else 0}

# No answer-bearing payload is returned by queue discovery. Exclude concurrent
# assessed questions so their very presence cannot leak through review metadata.
def not_assessed(alias='q'):
    return f'''NOT EXISTS(SELECT 1 FROM mock_sessions ms WHERE ms.user_id=%(user)s AND ms.submitted_at IS NULL AND {alias}.id=ANY(ms.question_ids))
      AND NOT EXISTS(SELECT 1 FROM game_members gm JOIN game_rooms gr ON gr.id=gm.room_id LEFT JOIN game_cups cup ON cup.id=gr.cup_id
       WHERE gm.user_id=%(user)s AND ((gm.released_at IS NULL AND gr.state IN ('waiting','running')) OR cup.closes_at>now())
       AND gr.questions @> jsonb_build_array(jsonb_build_object('id',{alias}.id)))'''

async def candidates(cur,user,scope):
    # Small personal sets do not benefit from LLVM compilation of expanded
    # eligibility views. This setting is local to the current transaction.
    await cur.execute('SET LOCAL jit=off')
    await cur.execute(f'''WITH latest AS MATERIALIZED (
      SELECT DISTINCT ON(a.canonical_id) a.* FROM attempts a WHERE a.user_id=%(user)s AND a.canonical_id IS NOT NULL
      ORDER BY a.canonical_id,a.at DESC,a.id DESC),
      mistakes AS MATERIALIZED (SELECT l.canonical_id FROM latest l
       LEFT JOIN LATERAL(SELECT payload->>'outcome' AS outcome FROM attempt_assessments aa WHERE aa.attempt_id=l.id ORDER BY aa.id DESC LIMIT 1) aa ON true
       LEFT JOIN LATERAL(SELECT x.value->>'outcome' AS outcome FROM mock_assessments ma CROSS JOIN LATERAL jsonb_array_elements(ma.payload->'rows') x(value)
         WHERE ma.mock_id=l.mock_id AND x.value->>'question_id'=l.canonical_id ORDER BY ma.created_at DESC,ma.id DESC LIMIT 1) ma ON true
       WHERE COALESCE(aa.outcome,ma.outcome,CASE WHEN l.correct THEN 'correct' ELSE 'wrong' END)='wrong'),
      saved AS MATERIALIZED (SELECT jsonb_array_elements_text(COALESCE(document->'saved','[]'::jsonb)) AS id FROM personal_desks WHERE user_id=%(user)s),
      due AS MATERIALIZED (SELECT vs.question_id AS id FROM vocabulary_state vs JOIN v_vocabulary_eligible e ON e.id=vs.question_id AND e.focus=%(scope)s
       WHERE vs.user_id=%(user)s AND vs.seen>0 AND (vs.due_at<=now() OR vs.score_version<>e.score_version OR vs.appearance_version<>e.appearance_version OR vs.appearance_id IS DISTINCT FROM e.primary_appearance_id)),
      selected_ids AS MATERIALIZED (SELECT canonical_id AS id FROM mistakes UNION SELECT id FROM saved UNION SELECT id FROM due)
      SELECT q.id,q.question,qc.subject_label,
       EXISTS(SELECT 1 FROM mistakes m WHERE m.canonical_id=q.id) AS mistake,
       EXISTS(SELECT 1 FROM saved s WHERE s.id=q.id) AS saved,
       EXISTS(SELECT 1 FROM due d WHERE d.id=q.id) AS vocabulary
      FROM selected_ids ids JOIN v_mock_practice q ON q.id=ids.id
      LEFT JOIN question_classifications qc ON qc.question_id=q.id AND qc.review_status='approved'
      WHERE {question_scope('q',scope)} AND {not_assessed()}
      AND NOT EXISTS(SELECT 1 FROM answer_reveals ar WHERE ar.user_id=%(user)s AND ar.canonical_id=q.id AND ar.revealed_at>clock_timestamp()-interval '30 minutes')
      ORDER BY vocabulary DESC,mistake DESC,saved DESC,q.id''',{'user':user,'scope':scope})
    return await cur.fetchall()

@router.get('/revision')
async def revision(actor:Account,exam_scope:ExamScope=DEFAULT_SCOPE):
    async with cursor()as cur:
        rows=await candidates(cur,actor.id,exam_scope)
        await cur.execute("SELECT (clock_timestamp() AT TIME ZONE 'Asia/Kolkata')::date AS day");day=(await cur.fetchone())['day']
        await cur.execute('SELECT id FROM daily_revision_sessions WHERE user_id=%s AND day=%s AND exam_scope=%s',(actor.id,day,exam_scope));session=await cur.fetchone()
    return {'day':day,'available':len(rows),'mistakes':sum(r['mistake'] for r in rows),'saved':sum(r['saved'] for r in rows),'vocabulary':sum(r['vocabulary'] for r in rows),'session_id':session['id'] if session else None,'daily_limit':20}

def choose_daily(rows,limit=20):
    selected=[]
    for category,budget in [('vocabulary',8),('mistake',8),('saved',4)]:
        choices=[r['id'] for r in rows if r[category] and r['id'] not in selected]
        selected.extend(choices[:budget])
    selected.extend(r['id'] for r in rows if r['id'] not in selected)
    return selected[:limit]

@router.post('/revision/start')
async def start_revision(actor:Account,exam_scope:ExamScope=DEFAULT_SCOPE):
    async with cursor()as cur:
        await cur.execute('SELECT pg_advisory_xact_lock(hashtext(%s))',('daily-revision:'+actor.id,))
        await cur.execute("SELECT (clock_timestamp() AT TIME ZONE 'Asia/Kolkata')::date AS day");day=(await cur.fetchone())['day']
        await cur.execute('SELECT id FROM daily_revision_sessions WHERE user_id=%s AND day=%s AND exam_scope=%s',(actor.id,day,exam_scope));existing=await cur.fetchone()
        if existing:return existing
        ids=choose_daily(await candidates(cur,actor.id,exam_scope))
        sid='rev_'+uuid4().hex
        await cur.execute('INSERT INTO daily_revision_sessions(id,user_id,day,exam_scope,question_ids) VALUES(%s,%s,%s,%s,%s)',(sid,actor.id,day,exam_scope,ids))
    return {'id':sid}

@router.get('/revision/{sid}')
async def session_revision(sid:str,actor:Account):
    async with cursor()as cur:
        await cur.execute('SELECT * FROM daily_revision_sessions WHERE id=%s AND user_id=%s',(sid,actor.id));session=await cur.fetchone()
        if not session:raise HTTPException(404,'Revision session not found')
        # Re-evaluate eligibility on every refresh, including current exam focus.
        rows={r['id']:r for r in await candidates(cur,actor.id,session['exam_scope'])}
        await cur.execute('SELECT question_id FROM daily_revision_completions WHERE session_id=%s',(sid,));done={r['question_id'] for r in await cur.fetchall()}
        items=[]
        for qid in session['question_ids']:
            r=rows.get(qid)
            items.append({'id':qid,'question':r['question'] if r else None,'subject':r['subject_label'] if r else None,
              'reasons':[k for k in ('vocabulary','mistake','saved') if r and r[k]],
              'state':'completed' if qid in done else 'ready' if r else 'unavailable'})
    return {'id':sid,'day':session['day'],'exam_scope':session['exam_scope'],'items':items}

@router.get('/changes/{eid}')
async def change_detail(eid:int,actor:Account):
    async with cursor()as cur:
        await cur.execute('''SELECT e.id,e.question_id,e.changed_fields,e.created_at FROM question_change_events e
          WHERE e.id=%s AND EXISTS(SELECT 1 FROM review_notifications n WHERE n.user_id=%s AND n.question_change_id=e.id)''',(eid,actor.id));event=await cur.fetchone()
        if not event:raise HTTPException(404,'Question update not found')
        await protect_answer(cur,actor.id,event['question_id'])
        await cur.execute('''SELECT DISTINCT m.id,c.title FROM mock_sessions m JOIN collections c ON c.id=m.collection_id
          WHERE m.user_id=%s AND m.submitted_at IS NOT NULL AND %s=ANY(m.question_ids) ORDER BY m.id LIMIT 20''',(actor.id,event['question_id']));mocks=await cur.fetchall()
    return {**event,'mocks':mocks,'message':'Original answers and mock results are unchanged. Current answers require the normal answer check; adjusted assessments are separate.'}
