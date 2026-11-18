"""Account-owned submission metadata over existing review lifecycles; no writes."""
from .community_policy import policy

# Never select draft bodies, baselines, reviewer identities or another author's
# title. Pagination happens before per-item feedback/assessment checks.
OWN="""
 SELECT 'bank' AS pipeline,id,title,kind,state,revision,updated_at,subject_id,
   ARRAY[canonical_id]::text[] AS questions,NULL::integer AS published_revision
 FROM bank_contributions WHERE author_id=%(user)s
 UNION ALL
 SELECT 'material',id,title,'material',workflow_state,revision,updated_at,NULL,
   ARRAY[]::text[],published_revision FROM materials WHERE author_id=%(user)s
 UNION ALL
 SELECT 'collection',id,payload->>'title',CASE WHEN payload->'test_config' IS NOT NULL AND payload->'test_config'<>'null'::jsonb THEN 'test' ELSE kind END,
   state,version,updated_at,payload->>'subject_id',
   ARRAY(SELECT jsonb_array_elements_text(COALESCE(payload->'question_ids','[]'::jsonb))),
   CASE WHEN live_payload IS NOT NULL THEN live_test_version END
 FROM learning_catalog WHERE author_id=%(user)s
"""
PAIR="""NOT EXISTS(SELECT 1 FROM creator_blocks b WHERE
 (b.user_id=%(user)s AND b.blocked_id={actor}) OR (b.user_id={actor} AND b.blocked_id=%(user)s))"""

async def protected(cur,questions,user):
    questions=[q for q in questions if q]
    if not questions:return False
    await cur.execute("""SELECT EXISTS(SELECT 1 FROM unnest(%s::text[]) q(id) WHERE
      NOT EXISTS(SELECT 1 FROM attempts a WHERE a.user_id=%s AND a.canonical_id=q.id)
      AND NOT EXISTS(SELECT 1 FROM answer_reveals r WHERE r.user_id=%s AND r.canonical_id=q.id)
      AND NOT EXISTS(SELECT 1 FROM discussion_disclosures d JOIN canonical_questions c ON c.id=d.canonical_id
        WHERE d.user_id=%s AND c.id=q.id AND (c.status='held' OR c.source_defect IN ('duplicate-options','unresolved-source')
          OR c.type<>'mcq' OR c.answer_text IS NULL OR
          (SELECT count(*) FROM jsonb_array_elements_text(COALESCE(c.options,'[]'::jsonb)) opt WHERE opt=c.answer_text)<>1)))
      OR EXISTS(SELECT 1 FROM mock_sessions m WHERE m.user_id=%s AND m.submitted_at IS NULL AND m.question_ids && %s::text[])
      OR EXISTS(SELECT 1 FROM game_members gm JOIN game_rooms gr ON gr.id=gm.room_id LEFT JOIN game_cups cup ON cup.id=gr.cup_id
        WHERE gm.user_id=%s AND ((gm.released_at IS NULL AND gr.state IN ('waiting','running')) OR cup.closes_at>now())
        AND EXISTS(SELECT 1 FROM unnest(%s::text[]) q(id) WHERE gr.questions @> jsonb_build_array(jsonb_build_object('id',q.id)))) AS locked""",
      (questions,user,user,user,user,questions,user,questions))
    return (await cur.fetchone())['locked']

async def feedback(cur,row,user):
    args={'user':user,'id':row['id']}
    queries={
      'bank':"SELECT rationale AS note,revision,created_at FROM contribution_decisions WHERE contribution_id=%(id)s AND decision IN ('request_changes','reject') AND "+PAIR.format(actor='reviewer_id')+" ORDER BY id DESC LIMIT 1",
      'material':"SELECT detail->>'reason' AS note,detail->>'revision' AS revision,created_at FROM material_events WHERE material_id=%(id)s AND action IN ('changes_requested','archive') AND "+PAIR.format(actor='actor_id')+" ORDER BY id DESC LIMIT 1",
      'collection':"SELECT reason AS note,version AS revision,created_at FROM learning_catalog_history WHERE entry_id=%(id)s AND action IN ('request_changes','reject') AND "+PAIR.format(actor='actor_id')+" ORDER BY id DESC LIMIT 1"}
    await cur.execute(queries[row['pipeline']],args)
    return await cur.fetchone()

async def position(cur,row,user):
    if row['state'] not in ('submitted','in_review'):return None
    # Counts are a dated oldest-submitted ordering, not a promise of FIFO review.
    # No other account's title, identity, contents or reviewer is returned.
    if row['pipeline']=='bank':
        query="""WITH queue AS (SELECT c.id,COALESCE((SELECT max(created_at) FROM contribution_events e
          WHERE e.contribution_id=c.id AND e.action='submitted'),c.created_at) AS queued
          FROM bank_contributions c WHERE state IN ('submitted','in_review') AND subject_id=%(subject)s
          AND """+PAIR.format(actor='c.author_id')+""")
          SELECT count(*)::int AS position FROM queue WHERE (queued,id)<=(SELECT queued,id FROM queue WHERE id=%(id)s)"""
    elif row['pipeline']=='material':
        query="""WITH queue AS (SELECT m.id,COALESCE((SELECT max(created_at) FROM material_events e
          WHERE e.material_id=m.id AND e.action='submitted' AND e.detail->>'revision'=m.revision::text),m.updated_at) AS queued
          FROM materials m WHERE workflow_state='submitted' AND """+PAIR.format(actor='m.author_id')+""")
          SELECT count(*)::int AS position FROM queue WHERE (queued,id)<=(SELECT queued,id FROM queue WHERE id=%(id)s)"""
    else:
        query="""WITH queue AS (SELECT c.id,COALESCE((SELECT max(created_at) FROM learning_catalog_history h
          WHERE h.entry_id=c.id AND h.action='submit'),c.updated_at) AS queued
          FROM learning_catalog c WHERE state='submitted' AND kind=%(kind)s AND """+PAIR.format(actor='c.author_id')+""")
          SELECT count(*)::int AS position FROM queue WHERE (queued,id)<=(SELECT queued,id FROM queue WHERE id=%(id)s)"""
    await cur.execute(query,{'user':user,'id':row['id'],'subject':row['subject_id'],'kind':'practice' if row['kind']=='test' else row['kind']})
    value=(await cur.fetchone())['position']
    return value or None

async def review_times(cur,user):
    # Real independently recorded decisions from the last30days, paired with
    # their latest preceding submission. Missing history is not an elapsed time.
    await cur.execute("""
      WITH durations AS (
        SELECT 'bank' AS pipeline,extract(epoch FROM d.created_at-s.created_at) AS seconds
        FROM contribution_decisions d JOIN bank_contributions c ON c.id=d.contribution_id
        JOIN contribution_revisions r ON r.contribution_id=d.contribution_id AND r.revision=d.revision
        JOIN LATERAL (SELECT max(e.created_at) AS created_at FROM contribution_events e WHERE e.contribution_id=c.id
          AND e.action='submitted' AND e.created_at>=r.created_at AND e.created_at<=d.created_at) s ON s.created_at IS NOT NULL
        WHERE d.created_at>=now()-interval '30 days' AND d.created_at<=now() AND d.reviewer_id<>c.author_id AND """+PAIR.format(actor='c.author_id')+" AND "+PAIR.format(actor='d.reviewer_id')+"""
        UNION ALL
        SELECT 'material',extract(epoch FROM e.created_at-s.created_at)
        FROM material_events e JOIN materials m ON m.id=e.material_id
        JOIN LATERAL (SELECT max(t.created_at) AS created_at FROM material_events t WHERE t.material_id=m.id
          AND t.action='submitted' AND t.detail->>'revision'=e.detail->>'revision' AND t.created_at<=e.created_at) s ON s.created_at IS NOT NULL
        WHERE e.action IN ('publish','changes_requested') AND e.created_at>=now()-interval '30 days' AND e.created_at<=now()
          AND e.actor_id<>m.author_id AND """+PAIR.format(actor='m.author_id')+" AND "+PAIR.format(actor='e.actor_id')+"""
        UNION ALL
        SELECT 'collection',extract(epoch FROM h.created_at-s.created_at)
        FROM learning_catalog_history h JOIN learning_catalog c ON c.id=h.entry_id
        JOIN LATERAL (SELECT max(t.created_at) AS created_at FROM learning_catalog_history t WHERE t.entry_id=c.id
          AND t.action='submit' AND t.version<h.version AND t.created_at<=h.created_at
          AND NOT EXISTS(SELECT 1 FROM learning_catalog_history saved WHERE saved.entry_id=c.id
            AND saved.version>t.version AND saved.version<h.version AND saved.action='save')) s ON s.created_at IS NOT NULL
        WHERE h.action IN ('publish','request_changes','reject') AND h.created_at>=now()-interval '30 days' AND h.created_at<=now()
          AND h.actor_id<>c.author_id AND """+PAIR.format(actor='c.author_id')+" AND "+PAIR.format(actor='h.actor_id')+"""
      ) SELECT pipeline,count(*)::int AS sample_count,percentile_cont(0.5) WITHIN GROUP(ORDER BY seconds)::float AS median_seconds
      FROM durations WHERE seconds>=0 GROUP BY pipeline""",{'user':user})
    rows={r['pipeline']:r for r in await cur.fetchall()}
    return [rows.get(k,{'pipeline':k,'sample_count':0,'median_seconds':None}) for k in ('bank','material','collection')]

async def tracker(cur,user,offset=0,limit=20):
    await cur.execute('SELECT * FROM ('+OWN+') own ORDER BY updated_at DESC,pipeline,id LIMIT %(limit)s OFFSET %(offset)s',{'user':user,'offset':offset,'limit':limit+1})
    rows=await cur.fetchall();items=[]
    for row in rows[:limit]:
        locked=await protected(cur,row['questions'],user)
        items.append({**{k:row[k] for k in ('pipeline','id','kind','state','revision','updated_at','published_revision')},
          'title':'Linked question details are locked' if locked else row['title'],
          'locked':locked,'feedback':None if locked else await feedback(cur,row,user),'queue_position':await position(cur,row,user)})
    state=await policy(cur,user)
    return {'items':items,'has_more':len(rows)>limit,'offset':offset,'review_times':await review_times(cur,user),
      'standing':{k:state.get(k) for k in ('display_tier','tier','can_create','post_limit','reply_limit','posts_remaining','replies_remaining','privileges_restricted','mentor_eligible')},
      'as_of':(await _now(cur)),'queue_scope':'Oldest submission first in the same review queue; blocked accounts excluded. Reviewers may choose a different order.'}

async def _now(cur):
    await cur.execute('SELECT now() AS time');return (await cur.fetchone())['time']
