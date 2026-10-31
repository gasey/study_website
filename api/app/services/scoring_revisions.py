"""Append-only reassessments. Never rewrite original attempts or mock results."""
import asyncio
import logging
import unicodedata
from uuid import uuid4
from fastapi import HTTPException
from psycopg.types.json import Jsonb
from ..db import cursor
from .review_policy import digest

POLICY='adjusted-score-v1'
log=logging.getLogger(__name__)
CONTEXT_KEYS=('direction','passage','question_markup','options_markup','has_diagram','figure_image')


def identity(text):
    # Preserve case and mathematical signs. Only canonical Unicode/whitespace.
    return ' '.join(unicodedata.normalize('NFC',text or '').split())


def evaluate(snapshot,current,chosen,mode):
    if not snapshot:return {'outcome':'excluded','reason':'legacy_unversioned','answer_text':None}
    if not current:return {'outcome':'excluded','reason':'question_unavailable','answer_text':None}
    reason=None
    if current.get('type')!='mcq':reason='not_mcq'
    elif current.get('status')!='live':reason='question_held'
    elif current.get('key_disputed'):reason='disputed_key'
    elif current.get('source_defect') in {'duplicate-options','unresolved-source'}:reason='source_defect'
    elif not current.get('answer_text'):reason='answer_unavailable'
    elif current.get('answer_source') not in {'official','key','derived'}:reason='unverified_answer'
    elif current.get('answer_source')=='derived' and mode=='official':reason='not_official_key'
    elif current.get('answer_source')=='derived' and not current.get('reviewed_eligible'):reason='derived_review_missing'
    elif identity(snapshot.get('question'))!=identity(current.get('question')):reason='question_text_changed'
    old_context={k:snapshot.get(k) for k in CONTEXT_KEYS}
    new_context=current.get('presentation') or {k:current.get(k) for k in CONTEXT_KEYS}
    if not reason:
        if current.get('context_unavailable') and any(old_context.values()):reason='presentation_snapshot_missing'
        elif any((old_context[k] or None)!=(new_context.get(k) or None) for k in CONTEXT_KEYS):reason='question_context_changed'
    old=[identity(o) for o in snapshot.get('options',[]) if o is not None]
    new=[identity(o) for o in current.get('options',[]) if o is not None]
    if not reason and (not old or any(not o for o in old) or any(not o for o in new) or len(old)!=len(snapshot.get('options',[])) or len(new)!=len(current.get('options',[])) or len(set(old))!=len(old) or len(set(new))!=len(new) or set(old)!=set(new)):
        reason='options_unmappable'
    key=identity(current.get('answer_text'))
    if not reason and key not in new:reason='answer_unmappable'
    if not reason and chosen is not None and identity(chosen) not in old:reason='choice_unmappable'
    if reason:return {'outcome':'excluded','reason':reason,'answer_text':current.get('answer_text')}
    outcome='skipped' if chosen is None else 'correct' if identity(chosen)==key else 'wrong'
    return {'outcome':outcome,'reason':'key_corrected' if snapshot.get('answer_text')!=current.get('answer_text') else 'provenance_changed' if snapshot.get('answer_source')!=current.get('answer_source') else 'unchanged','answer_text':current.get('answer_text')}


def totals(rows,marks_correct,marks_wrong):
    counts={k:sum(r['outcome']==k for r in rows) for k in ['correct','wrong','skipped','excluded']}
    included=len(rows)-counts['excluded']
    return {'n_correct':counts['correct'],'n_wrong':counts['wrong'],'n_skipped':counts['skipped'],'n_excluded':counts['excluded'],'scorable_total':included,
            'score':round(counts['correct']*float(marks_correct)-counts['wrong']*float(marks_wrong),6) if included else None,
            'maximum':round(included*float(marks_correct),6),'accuracy':round(100*counts['correct']/included,2) if included else None}


CURRENT_COLUMNS="""COALESCE((SELECT version FROM question_score_versions sv WHERE sv.canonical_id=q.id),0) AS score_version,q.id,q.type,q.question,q.options,q.answer_text,q.answer_source,q.key_disputed,q.source_defect,q.status,
 EXISTS(SELECT 1 FROM v_mock_practice v WHERE v.id=q.id) AS reviewed_eligible"""

CONTEXT_SELECT="""src.context_revision AS appearance_score_version,jsonb_build_object('direction',COALESCE(src.direction,q.direction),
 'passage',COALESCE(src.passage,q.passage),'question_markup',COALESCE(src.question_markup,q.question_markup),
 'options_markup',COALESCE(src.options_markup,q.options_markup),'has_diagram',src.has_diagram,'figure_image',src.figure_image) AS presentation"""

def source_join(target):
    return """ LEFT JOIN LATERAL (SELECT sx.* FROM appearances sx WHERE sx.canonical_id=q.id
      AND (("""+target+""") IS NOT NULL AND sx.id=("""+target+""") OR ("""+target+""") IS NULL AND sx.is_primary)
      ORDER BY sx.id LIMIT 1) src ON TRUE """

def current_record(row):
    if not row['id']:return None
    result={k:row[k] for k in ['id','type','question','options','answer_text','answer_source','key_disputed','source_defect','status','reviewed_eligible','presentation']}
    snap=row.get('snapshot') or row.get('scoring_snapshot') or {}
    result['context_unavailable']=not snap.get('appearance_id') and not snap.get('context_basis')
    return result


async def mock_inputs(cur,mock_id,user=None):
    await cur.execute('SELECT * FROM mock_sessions WHERE id=%s AND (%s::text IS NULL OR user_id=%s)',(mock_id,user,user))
    session=await cur.fetchone()
    if not session:raise HTTPException(404,'Mock not found')
    if session['submitted_at'] is None:raise HTTPException(409,'Finish this mock before viewing reassessments')
    if user:
        await cur.execute('SELECT 1 FROM mock_sessions WHERE user_id=%s AND submitted_at IS NULL AND question_ids && %s::text[]',(user,session['question_ids']))
        if await cur.fetchone():raise HTTPException(409,'Finish your active mock before viewing updated answers')
    await cur.execute('''SELECT u.id AS question_id,u.ord-1 AS position,sq.snapshot,sq.options AS presented_options,
      a.chosen_text,a.correct AS original_correct,'''+CURRENT_COLUMNS+','+CONTEXT_SELECT+'''
      FROM unnest(%s::text[]) WITH ORDINALITY u(id,ord)
      LEFT JOIN mock_session_questions sq ON sq.mock_id=%s AND sq.canonical_id=u.id
      LEFT JOIN attempts a ON a.mock_id=%s AND a.canonical_id=u.id
      LEFT JOIN canonical_questions q ON q.id=u.id '''+source_join("COALESCE(sq.snapshot->>'appearance_id',sq.appearance_id)")+''' ORDER BY u.ord''',(session['question_ids'],mock_id,mock_id))
    return session,await cur.fetchall()

def input_fingerprint(session,inputs):
    return digest({'inputs':inputs,'mode':session['answer_mode'],'marks_correct':session['marks_correct'],'marks_wrong':session['marks_wrong']})


async def assess_mock(cur,mock_id,user=None):
    session,inputs=await mock_inputs(cur,mock_id,user)
    adjusted=[];original=[]
    for row in inputs:
        current=current_record(row)
        snapshot=row['snapshot'];chosen=row['chosen_text']
        verdict=evaluate(snapshot,current,chosen,session['answer_mode'])
        original_outcome='skipped' if chosen is None else 'correct' if row['original_correct'] else 'wrong'
        original.append({'outcome':original_outcome,'answer_source':snapshot.get('answer_source') if snapshot else None})
        adjusted.append({'question_id':row['question_id'],'position':int(row['position']),'question':snapshot.get('question') if snapshot else row.get('question'),
         'chosen_text':chosen,'original_answer':snapshot.get('answer_text') if snapshot else None,'original_outcome':original_outcome,
         'answer_source':current.get('answer_source') if current else None,**verdict})
    # Hash actual inputs, not a global sync timestamp, so unrelated bank writes
    # do not create duplicate assessments. Marking rules are part of identity.
    fingerprint=input_fingerprint(session,inputs)
    official=[r for r in adjusted if r['answer_source'] in {'official','key'} and r['outcome']!='excluded']
    original_official=[r for r in original if r['answer_source'] in {'official','key'}]
    payload={**totals(adjusted,session['marks_correct'],session['marks_wrong']),
      'original_score':float(session['score']),'original_total':len(inputs),'legacy_unversioned':any(not r['snapshot'] for r in inputs),
      'changed_questions':sum(r['outcome']!=r['original_outcome'] or r['reason']!='unchanged' for r in adjusted),
      'marking':{'correct':float(session['marks_correct']),'wrong_penalty':float(session['marks_wrong'])},
      'official_subset':totals(official,session['marks_correct'],session['marks_wrong']),
      'original_official_subset':totals(original_official,session['marks_correct'],session['marks_wrong']),
      'rows':adjusted,'policy_version':POLICY}
    await cur.execute('''INSERT INTO mock_assessments(id,mock_id,input_hash,policy_version,payload)
      VALUES (%s,%s,%s,%s,%s) ON CONFLICT(mock_id,input_hash,policy_version) DO NOTHING''',('asm_'+uuid4().hex,mock_id,fingerprint,POLICY,Jsonb(payload)))
    await cur.execute('SELECT id,created_at,payload FROM mock_assessments WHERE mock_id=%s AND input_hash=%s AND policy_version=%s',(mock_id,fingerprint,POLICY))
    row=await cur.fetchone()
    if payload['changed_questions'] and not payload['legacy_unversioned']:
        await cur.execute("INSERT INTO review_notifications(user_id,mock_id,event_key,message) VALUES (%s,%s,%s,'Your saved mock has an adjusted assessment. Your original result is unchanged.') ON CONFLICT(event_key) DO NOTHING",(session['user_id'],mock_id,row['id']+':assessment'))
    return {**row['payload'],'id':row['id'],'computed_at':row['created_at']}

async def assess_attempt(cur,attempt_id):
    await cur.execute('SELECT a.id AS attempt_id,a.scoring_snapshot,a.chosen_text,a.correct,'+CURRENT_COLUMNS+','+CONTEXT_SELECT+' FROM attempts a LEFT JOIN canonical_questions q ON q.id=a.canonical_id '+source_join("a.scoring_snapshot->>'appearance_id'")+' WHERE a.id=%s AND a.context=\'practice\'',(attempt_id,))
    row=await cur.fetchone()
    if not row:return
    current=current_record(row)
    verdict=evaluate(row['scoring_snapshot'],current,row['chosen_text'],'derived-practice')
    payload={**verdict,'original_correct':row['correct'],'legacy_unversioned':not bool(row['scoring_snapshot'])}
    await cur.execute('''INSERT INTO attempt_assessments(attempt_id,input_hash,policy_version,payload) VALUES (%s,%s,%s,%s)
      ON CONFLICT(attempt_id,input_hash,policy_version) DO NOTHING''',(attempt_id,digest(row),POLICY,Jsonb(payload)))

async def process_job(cur,job=None):
    if job is None:
        await cur.execute('SELECT * FROM assessment_jobs WHERE finished_at IS NULL AND failures<5 ORDER BY requested_at LIMIT 1 FOR UPDATE SKIP LOCKED')
        job=await cur.fetchone()
    if not job:return False
    await cur.execute('''SELECT id FROM mock_sessions WHERE submitted_at IS NOT NULL AND question_ids @> ARRAY[%s]::text[]
      AND (%s::text IS NULL OR id>%s) ORDER BY id LIMIT 10''',(job['canonical_id'],job['mock_cursor'],job['mock_cursor']))
    mocks=await cur.fetchall()
    for mock in mocks:await assess_mock(cur,mock['id'])
    await cur.execute("SELECT id FROM attempts WHERE canonical_id=%s AND context='practice' AND id>%s ORDER BY id LIMIT 100",(job['canonical_id'],job['attempt_cursor']))
    attempts=await cur.fetchall()
    for attempt in attempts:await assess_attempt(cur,attempt['id'])
    await cur.execute('''UPDATE assessment_jobs SET mock_cursor=%s,attempt_cursor=%s,
       finished_at=CASE WHEN %s THEN now() ELSE NULL END,last_error=NULL WHERE canonical_id=%s''',
       (mocks[-1]['id'] if mocks else job['mock_cursor'],attempts[-1]['id'] if attempts else job['attempt_cursor'],len(mocks)<10 and len(attempts)<100,job['canonical_id']))
    return True

async def process_new_jobs(cur):
    await cur.execute('SELECT * FROM new_score_jobs WHERE finished_at IS NULL AND failures<5 ORDER BY id LIMIT 10 FOR UPDATE SKIP LOCKED')
    jobs=await cur.fetchall()
    for job in jobs:
        try:
            async with cur.connection.transaction():
                if job['mock_id']:await assess_mock(cur,job['mock_id'])
                elif job['attempt_id']:await assess_attempt(cur,job['attempt_id'])
                else:
                    await cur.execute("SELECT canonical_id FROM appearances WHERE id=%s",(job['appearance_id'],))
                    source=await cur.fetchone()
                    if source and source['canonical_id']:
                        await cur.execute("INSERT INTO assessment_jobs(canonical_id) VALUES (%s) ON CONFLICT(canonical_id) DO UPDATE SET requested_at=now(),mock_cursor=NULL,attempt_cursor=0,finished_at=NULL,failures=0,last_error=NULL",(source['canonical_id'],))
            await cur.execute('UPDATE new_score_jobs SET finished_at=now(),last_error=NULL WHERE id=%s',(job['id'],))
        except Exception:
            await cur.execute("UPDATE new_score_jobs SET failures=failures+1,last_error='Assessment failed; operator investigation required' WHERE id=%s",(job['id'],))
    return len(jobs)


async def worker():
    while True:
        await asyncio.sleep(15)
        try:
            async with cursor() as cur:
                await cur.execute("INSERT INTO review_worker_health(worker_id,status) VALUES ('score-reassessment','online') ON CONFLICT(worker_id) DO UPDATE SET seen_at=now(),status='online'")
                from .correction_notices import process as process_notices
                for _ in range(10):
                    if not await process_notices(cur):break
                await process_new_jobs(cur)
                await cur.execute('SELECT * FROM assessment_jobs WHERE finished_at IS NULL AND failures<5 ORDER BY requested_at LIMIT 1 FOR UPDATE SKIP LOCKED')
                job=await cur.fetchone()
                if not job:continue
                try:
                    async with cur.connection.transaction():
                        await process_job(cur,job)
                except Exception:
                    await cur.execute("UPDATE assessment_jobs SET failures=failures+1,last_error='Reassessment batch failed; operator investigation required' WHERE canonical_id=%s",(job['canonical_id'],))
                    await cur.execute("UPDATE review_worker_health SET status='batch failed' WHERE worker_id='score-reassessment'")
                    log.error('Score reassessment batch failed; persisted job retained')
        except asyncio.CancelledError:raise
        except Exception:
            log.error('Score reassessment worker unavailable; jobs retained')


def original_breakdown(rows,marks_correct,marks_wrong):
    official=[{'outcome':'skipped' if r.chosen_text is None else 'correct' if r.correct else 'wrong'} for r in rows if r.answer_source in {'official','key'}]
    return {'official_subset':totals(official,marks_correct,marks_wrong),'maximum':round(len(rows)*float(marks_correct),6)}


async def capture_mock_questions(cur,ids,appearance_ids,mode):
    """Read eligibility and the exact presented content in one MVCC statement.

    Canonical rows are already share-locked by the caller. Appearance-only
    writes after this statement cannot alter the captured immutable payload.
    Random mocks use the primary source; paper mocks must map to that content.
    """
    view='v_mock_practice' if mode=='derived-practice' else 'v_scorable'
    primary_context=CONTEXT_SELECT.replace('src.','prim.').replace('AS appearance_score_version','AS primary_score_version').replace('AS presentation','AS expected_presentation')
    query='''SELECT q.id,q.question,q.options AS canonical_options,q.answer_text,q.answer_source,q.explanation,
      q.answer_key_ref,(SELECT publication_id FROM v_reviewed_answer_publications rp WHERE rp.canonical_id=q.id LIMIT 1) AS review_publication_id,src.id AS appearance_id,src.options AS source_options,src.page,p.source_file,p.pdf_url,'''+CONTEXT_SELECT+','+primary_context+'''
      FROM unnest(%s::text[],%s::text[]) WITH ORDINALITY u(id,desired_id,position)
      JOIN canonical_questions q ON q.id=u.id JOIN '''+view+''' eligible ON eligible.id=q.id
      '''+source_join('u.desired_id')+source_join('NULL::text').replace('src ON TRUE','prim ON TRUE')+'''
      LEFT JOIN papers p ON p.id=src.paper_id ORDER BY u.position'''
    await cur.execute(query,(ids,appearance_ids))
    rows=await cur.fetchall();result=[]
    for row in rows:
        # Recover desired by question ID because an ineligible row can be absent.
        desired=appearance_ids[ids.index(row['id'])]
        opts=row['source_options'] if desired else row['canonical_options']
        old=[identity(o) for o in row['canonical_options']]
        new=[identity(o) for o in opts or []]
        context=row['presentation'];expected=row['expected_presentation']
        if set(old)!=set(new) or len(old)!=len(new) or len(set(new))!=len(new) or any(not o for o in new):continue
        if any((context.get(k) or None)!=(expected.get(k) or None) for k in CONTEXT_KEYS):continue
        if desired and row['appearance_id']!=desired:continue
        snap={k:row[k] for k in ['question','answer_text','answer_source','answer_key_ref','review_publication_id','explanation','appearance_id','page','source_file','pdf_url']}
        snap.update(context);snap.update(options=opts,policy_version='mock-snapshot-v2')
        result.append({'id':row['id'],'appearance_id':row['appearance_id'],'snapshot':snap})
    return result
