"""Reviewed taxonomy decks over canonical vocabulary; no content or award writes."""
from fastapi import HTTPException
from .mastery import VERIFIED_ACTIVITY,tier

ROOT='english/vocabulary'
# The approved path is the classification authority. Do not infer a deck from
# wording, retag a question, or multiply a canonical question across appearances.
MEMBERSHIP="""EXISTS(SELECT 1 FROM v_question_paths vp JOIN review_taxonomy rt
 ON rt.id=vp.subtopic_id AND rt.active AND rt.parent_id='english/vocabulary' AND rt.level='subtopic'
 WHERE vp.question_id=e.id AND vp.subject_id='english' AND vp.topic_id='english/vocabulary' AND rt.id=%(deck)s)"""
HAS_SUBTOPIC=MEMBERSHIP.replace(' AND rt.id=%(deck)s','')
DECK_FILTER="(%(deck)s::text IS NULL OR (CASE WHEN %(deck)s='english/vocabulary' THEN NOT "+HAS_SUBTOPIC+' ELSE '+MEMBERSHIP+' END))'

async def validate(cur,deck):
    if deck is None:return
    await cur.execute("SELECT 1 FROM review_taxonomy WHERE active AND (id=%s AND id='english/vocabulary' OR id=%s AND parent_id='english/vocabulary' AND level='subtopic')",(deck,deck))
    if not await cur.fetchone():raise HTTPException(422,'Choose a current vocabulary deck')

async def contains(cur,qid,scope,deck):
    await cur.execute('SELECT 1 FROM v_vocabulary_eligible e WHERE e.id=%(id)s AND e.focus=%(scope)s AND '+DECK_FILTER,{'id':qid,'scope':scope,'deck':deck})
    return bool(await cur.fetchone())

async def catalog(cur,user,scope):
    from ..routers.learning import not_assessed
    await cur.execute('SET LOCAL jit=off')
    await cur.execute("SELECT id,label FROM review_taxonomy WHERE active AND parent_id='english/vocabulary' AND level='subtopic' ORDER BY label,id")
    definitions=await cur.fetchall()
    definitions.append({'id':ROOT,'label':'Other vocabulary'})
    # Only the learner's latest independently scored response contributes.
    # Repeated correct tries cannot inflate progress; current assessments win.
    await cur.execute('''WITH verified AS MATERIALIZED ('''+VERIFIED_ACTIVITY+'''),
      latest AS MATERIALIZED (SELECT DISTINCT ON(canonical_id)
        canonical_id,outcome,at FROM verified ORDER BY canonical_id,at DESC,id DESC),
      reviewed AS MATERIALIZED (
        SELECT DISTINCT e.canonical_id FROM verified e
        JOIN question_classifications qc ON qc.question_id=e.canonical_id AND qc.review_status='approved'
          AND qc.subject_id='english' AND qc.topic_id='english/vocabulary'
        JOIN user_topic_mastery mt ON mt.user_id=%(user)s AND mt.subject_id=qc.subject_id AND mt.topic=qc.topic_id
        JOIN practice_request_receipts r ON r.user_id=%(user)s AND r.attempt_id=e.id
        JOIN practice_study_sessions ps ON ps.user_id=%(user)s AND ps.kind='review'
          AND r.request_key='study:'||ps.id||':'||left(encode(sha256(convert_to(e.canonical_id,'UTF8')),'hex'),32)
        WHERE ps.finished_at IS NOT NULL AND mt.proficient_at IS NOT NULL
          AND ps.finished_at>=mt.proficient_at+interval '14 days'
          AND e.at>=mt.proficient_at+interval '14 days'
          AND e.context='review' AND e.outcome IN ('correct','wrong') AND e.collection_id IS NULL
          AND e.canonical_id=ANY(ps.question_ids)
          AND e.paper_id=ps.paper_ids[array_position(ps.question_ids,e.canonical_id)]
          AND e.at>=ps.created_at AND e.at<=ps.finished_at),
      members AS MATERIALIZED (
      SELECT DISTINCT e.id,e.score_version,e.appearance_version,e.primary_appearance_id,COALESCE(rt.id,'english/vocabulary') AS deck_id
      FROM v_vocabulary_eligible e LEFT JOIN v_question_paths vp
       ON vp.question_id=e.id AND vp.subject_id='english' AND vp.topic_id='english/vocabulary'
      LEFT JOIN review_taxonomy rt ON rt.id=vp.subtopic_id AND rt.active
       AND rt.parent_id='english/vocabulary' AND rt.level='subtopic'
      WHERE e.focus=%(scope)s AND '''+not_assessed('e')+'''),
      eligible AS (SELECT m.* FROM members m WHERE m.deck_id<>'english/vocabulary'
        OR NOT EXISTS(SELECT 1 FROM members specific WHERE specific.id=m.id AND specific.deck_id<>'english/vocabulary'))
      SELECT m.deck_id,count(*)::int AS eligible,
        count(*) FILTER(WHERE r.item_id IS NOT NULL)::int AS started,
        count(*) FILTER(WHERE l.outcome IN ('correct','wrong'))::int AS attempted,
        count(*) FILTER(WHERE l.outcome='correct')::int AS correct_latest,
        max(l.at) FILTER(WHERE l.outcome IN ('correct','wrong')) AS last_activity,
        count(*) FILTER(WHERE r.item_id IS NOT NULL AND (r.due_on<=(now() AT TIME ZONE 'Asia/Kolkata')::date OR s.score_version<>m.score_version OR s.appearance_version<>m.appearance_version OR s.appearance_id IS DISTINCT FROM m.primary_appearance_id))::int AS due,
        bool_or(reviewed.canonical_id IS NOT NULL) AS reviewed
      FROM eligible m LEFT JOIN vocabulary_state s ON s.question_id=m.id AND s.user_id=%(user)s
      LEFT JOIN review_items r ON r.user_id=%(user)s AND r.item_type='vocab' AND r.item_id=m.id
      LEFT JOIN latest l ON l.canonical_id=m.id LEFT JOIN reviewed ON reviewed.canonical_id=m.id GROUP BY m.deck_id''',{'user':user,'scope':scope})
    stats={r['deck_id']:r for r in await cur.fetchall()}
    await cur.execute('SELECT now() AS now');now=(await cur.fetchone())['now']
    items=[]
    for definition in definitions:
        row=stats.get(definition['id'],{})
        attempted=row.get('attempted',0);correct=row.get('correct_latest',0)
        state=tier(attempted,correct,row.get('reviewed',False))
        last=row.get('last_activity')
        items.append({**definition,'source':'bank','eligible':row.get('eligible',0),'started':row.get('started',0),
          'attempted':attempted,'correct_latest':correct,'due':row.get('due',0),
          'state':state,'rusty':bool(state in ('proficient','mastered') and last and (now-last).days>=45),
          'last_activity':last})
    from .curated_practice import catalog as curated_catalog
    curated=await curated_catalog(cur,user,scope)
    return {'curated_items':curated['items'],'curated_known_total':curated['known_total'],'curated_practice_enabled':curated['practice_enabled'],'items':items,'basis':'Latest verified-key answers to canonical questions; not a count of unique words mastered.',
      'curated_available':bool(curated['items']),'curated_message':'No reviewed word or Mizo–English decks are available for this account in this scope.'}
