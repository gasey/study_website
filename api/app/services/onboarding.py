"""Optional primary-exam check-in using ordinary saved practice and grading."""
import hashlib,json
from uuid import uuid4
from fastapi import HTTPException
from psycopg.types.json import Jsonb
from . import onboarding_release
from .repeat_selection import distinct_candidates
from .mastery import VERIFIED_ATTEMPTS

MARKER={'onboarding_version':1}


def is_checkin(row):
    return (row.get('filters') or {}).get('onboarding_version')==1


def native_guard(row,request):
    if is_checkin(row) and getattr(request.state,'mobile_session',None):
        raise HTTPException(403,'Exam check-ins are available on the website')


async def primary(cur,user,lock=False):
    await cur.execute('''SELECT c.id,c.title,c.live_version FROM user_exam_bookmarks b
      JOIN collections c ON c.id=b.collection_id AND c.visibility='public' AND c.kind='exam'
      WHERE b.user_id=%s AND b.is_primary'''+(' FOR SHARE OF c,b' if lock else ''),(user,))
    return await cur.fetchone()


async def prior(cur,user,exam):
    await cur.execute('''SELECT * FROM practice_study_sessions WHERE user_id=%s
      AND collection_id=%s AND filters @> %s''',(user,exam,Jsonb(MARKER)))
    return await cur.fetchone()


async def selection(cur,user,exam,seed):
    # Bounded candidate sample, round-robin by current approved subject. The
    # count is explicitly a sample, not the exam's full inventory. No random().
    from ..routers.learning import not_assessed
    await cur.execute('SET LOCAL jit=off')
    await cur.execute('''WITH sources AS MATERIALIZED (
      SELECT q.id,qc.subject_id,src.paper_id FROM v_scorable q
      JOIN question_classifications qc ON qc.question_id=q.id AND qc.review_status='approved'
      JOIN review_taxonomy s ON s.id=qc.subject_id AND s.active AND s.level='subject'
      JOIN review_taxonomy t ON t.id=qc.topic_id AND t.active AND t.level='topic'
      JOIN LATERAL(SELECT a.paper_id FROM appearances a JOIN collection_papers cp ON cp.paper_id=a.paper_id
        JOIN collections c ON c.id=cp.collection_id AND c.live_version=cp.version AND c.visibility='public'
        WHERE a.canonical_id=q.id AND c.id=%(exam)s AND (NOT a.has_diagram OR a.figure_image IS NOT NULL)
        ORDER BY a.is_primary DESC,a.paper_id,a.id LIMIT 1) src ON TRUE
      WHERE q.type='mcq' AND '''+not_assessed()+'''), ranked AS (
      SELECT *,row_number() OVER(PARTITION BY subject_id ORDER BY md5(id||%(seed)s),id) AS rank
      FROM sources)
      SELECT id,subject_id,paper_id FROM ranked WHERE rank<=30
      ORDER BY rank,md5(subject_id||%(seed)s),id LIMIT 500''',{'user':user,'exam':exam,'seed':seed})
    rows=await cur.fetchall()
    distinct=set(await distinct_candidates(cur,[r['id'] for r in rows]))
    return [r for r in rows if r['id'] in distinct][:10]


async def status(cur,user):
    from ..routers.study_sessions import preview
    exam=await primary(cur,user)
    if not exam:return {'exam':None,'session':None,'available':False,'reason':'Choose a primary exam to take an optional check-in.'}
    saved=await prior(cur,user,exam['id'])
    if saved:return {'exam':exam,'session':{**preview(saved),'summary':None},'available':False,'reason':None}
    if not onboarding_release.enabled():return {'exam':exam,'session':None,'available':False,'reason':'New exam check-ins are temporarily paused.'}
    rows=await selection(cur,user,exam['id'],'onboarding-availability-v1')
    return {'exam':exam,'session':None,'available':len(rows)==10,
            'reason':None if len(rows)==10 else 'Ten distinct official-key questions with approved active subjects and topics are not available for this check-in.'}


async def start(cur,user,exam_id,request_key):
    from ..routers.study_sessions import state
    await cur.execute('SELECT id FROM users WHERE id=%s FOR UPDATE',(user,))
    exam=await primary(cur,user,True)
    if not exam or exam['id']!=exam_id:raise HTTPException(409,'Your primary exam changed. Reload before starting its check-in.')
    fingerprint=hashlib.sha256(json.dumps({'kind':'onboarding-v1','collection_id':exam_id},sort_keys=True).encode()).hexdigest()
    await cur.execute('SELECT * FROM practice_study_sessions WHERE user_id=%s AND request_key=%s',(user,request_key))
    replay=await cur.fetchone()
    if replay:
        if replay['request_hash']!=fingerprint or not is_checkin(replay):raise HTTPException(409,'This start request was already used for another study set')
        return await state(cur,replay,True)
    saved=await prior(cur,user,exam_id)
    if saved:return await state(cur,saved,True)
    onboarding_release.require_writes()
    rows=await selection(cur,user,exam_id,uuid4().hex)
    if len(rows)!=10:raise HTTPException(422,'Ten eligible distinct questions are not available. Your normal practice and reviews remain available.')
    # The shared state reader selects no keys. Original presentation hashes,
    # grading, exclusions, discovery caps and mastery hooks remain authoritative.
    filters={**MARKER,'exam_title':exam['title'],'pool':'scorable','order':'mixed'}
    await cur.execute('''INSERT INTO practice_study_sessions(id,user_id,collection_id,request_key,request_hash,
      requested_size,question_ids,paper_ids,filters) VALUES(%s,%s,%s,%s,%s,10,%s,%s,%s) RETURNING *''',
      (uuid4().hex,user,exam_id,request_key,fingerprint,[r['id'] for r in rows],[r['paper_id'] for r in rows],Jsonb(filters)))
    return await state(cur,await cur.fetchone(),True)


async def summary(cur,user,sid):
    from ..routers.study_sessions import owned,receipts
    row=await owned(cur,sid,user)
    if not is_checkin(row):raise HTTPException(404,'Exam check-in not found')
    # Gate even aggregate suggestions during protected assessments.
    await receipts(cur,row)
    if not row['finished_at']:return {'finished':False,'subjects':[],'suggested_subject_ids':[]}
    await cur.execute('''SELECT e.subject_id,s.label,count(*)::int AS checked,
      count(*) FILTER(WHERE e.outcome='correct')::int AS correct FROM ('''+VERIFIED_ATTEMPTS+''') e
      JOIN practice_request_receipts r ON r.attempt_id=e.id AND r.user_id=%(user)s
      JOIN review_taxonomy s ON s.id=e.subject_id AND s.active AND s.level='subject'
      JOIN review_taxonomy t ON t.id=e.topic AND t.active AND t.level='topic'
      WHERE e.context='practice' AND e.collection_id=%(exam)s AND e.at>=%(started)s AND e.at<=%(finished)s
        AND e.canonical_id=ANY(%(ids)s) AND e.paper_id=(%(papers)s::text[])[array_position(%(ids)s::text[],e.canonical_id)] AND e.outcome IN ('correct','wrong')
        AND r.request_key='study:'||%(sid)s||':'||substr(encode(sha256(convert_to(e.canonical_id,'UTF8')),'hex'),1,32)
      GROUP BY e.subject_id,s.label ORDER BY 1.0*count(*) FILTER(WHERE e.outcome='correct')/count(*),count(*) DESC,e.subject_id''',
      {'user':user,'exam':row['collection_id'],'started':row['created_at'],'finished':row['finished_at'],'ids':row['question_ids'],'papers':row['paper_ids'],'sid':sid})
    subjects=await cur.fetchall()
    return {'finished':True,'subjects':subjects,'suggested_subject_ids':[s['subject_id'] for s in subjects if s['correct']<s['checked']][:5],
            'basis':'A small practice sample, not an exam-readiness estimate. Viewed, skipped, excluded or currently ineligible answers are not evidence. Choose any focus changes yourself.'}
