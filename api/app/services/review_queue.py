"""Shared canonical question/vocabulary Leitner queue; no award writes."""
from datetime import timedelta

INTERVALS = (1,3,7,16,35)


def step(old,day,correct,*,vocab=False,spaced=True):
    """One dated Leitner rule; vocabulary promotions require delayed retrieval."""
    if not correct:return 1,day+timedelta(days=INTERVALS[0])
    if not old:return 1,day+timedelta(days=INTERVALS[0])
    if vocab and old['due_on'] is None:return old['box'],None
    if vocab and (old['due_on']>day or not spaced):
        return old['box'],day+timedelta(days=INTERVALS[old['box']-1])
    box=min(5,old['box']+1)
    return box,None if old['box']==5 else day+timedelta(days=INTERVALS[box-1])


async def attempt_input(cur, attempt):
    await cur.execute('''SELECT a.*,COALESCE(a.scoring_snapshot,sq.snapshot) AS scoring_snapshot,q.id IS NOT NULL AS eligible,
      COALESCE(ma.outcome,aa.payload->>'outcome',CASE WHEN a.correct THEN 'correct' ELSE 'wrong' END) AS outcome
      FROM attempts a LEFT JOIN v_scorable q ON q.id=a.canonical_id
      LEFT JOIN mock_session_questions sq ON sq.mock_id=a.mock_id AND sq.canonical_id=a.canonical_id
      LEFT JOIN LATERAL(SELECT payload FROM attempt_assessments WHERE attempt_id=a.id ORDER BY id DESC LIMIT 1) aa ON true
      LEFT JOIN LATERAL(SELECT x.value->>'outcome' AS outcome FROM mock_assessments m
        CROSS JOIN LATERAL jsonb_array_elements(m.payload->'rows') x(value)
        WHERE m.mock_id=a.mock_id AND x.value->>'question_id'=a.canonical_id
        ORDER BY m.created_at DESC,m.id DESC LIMIT 1) ma ON true
      WHERE a.id=%s''',(attempt,))
    return await cur.fetchone()


async def apply_attempt(cur, attempt):
    a = await attempt_input(cur,attempt)
    if not a or not a['eligible'] or a['outcome'] not in ('correct','wrong'):
        return
    if not a['scoring_snapshot'] or a['scoring_snapshot'].get('answer_source') not in ('official','key'):
        return
    # Guests never acquire a server queue, including through legacy writers.
    await cur.execute('SELECT 1 FROM users WHERE id=%s AND email IS NOT NULL',(a['user_id'],))
    if not await cur.fetchone():
        return
    await cur.execute("SELECT 1 FROM vocabulary_state WHERE user_id=%s AND question_id=%s",(a['user_id'],a['canonical_id']))
    vocab=bool(await cur.fetchone())
    if vocab:
        await cur.execute("SELECT e.score_version,e.appearance_version,e.primary_appearance_id,e.score_version<>s.score_version OR e.appearance_version<>s.appearance_version OR e.primary_appearance_id IS DISTINCT FROM s.appearance_id AS stale FROM v_vocabulary_eligible e JOIN vocabulary_state s ON s.question_id=e.id AND s.user_id=%s WHERE e.id=%s AND e.focus='all'",(a['user_id'],a['canonical_id']))
        source=await cur.fetchone();vocab=bool(source)
    kind='vocab' if vocab else 'question'
    await cur.execute('SELECT * FROM review_items WHERE user_id=%s AND item_type=%s AND item_id=%s FOR UPDATE',(a['user_id'],kind,a['canonical_id']))
    old = await cur.fetchone()
    if old and old['last_attempt_id'] is not None and old['last_attempt_id'] >= attempt:
        return
    correct = a['outcome'] == 'correct'
    if correct and not old and not vocab:
        return  # New correct ordinary questions do not enter the mistake queue.
    await cur.execute("SELECT (%s::timestamptz AT TIME ZONE 'Asia/Kolkata')::date AS day",(a['at'],))
    day=(await cur.fetchone())['day']
    spaced=True
    if vocab and correct and old:
        # Exposure in every answer engine participates in the same delay guard.
        await cur.execute('''SELECT GREATEST(max(at),(SELECT last_exposure_at FROM vocabulary_state WHERE user_id=%s AND question_id=%s)) AS exposed
          FROM attempts WHERE user_id=%s AND canonical_id=%s AND id<>%s AND at<=%s''',(a['user_id'],a['canonical_id'],a['user_id'],a['canonical_id'],attempt,a['at']))
        exposed=(await cur.fetchone())['exposed']
        spaced=not exposed or a['at']-exposed>=timedelta(hours=24)
    # A changed source cannot inherit graduation or a promotion from its old key.
    box,due=step(None if vocab and source['stale'] else old,day,correct,vocab=vocab,spaced=spaced)
    await cur.execute('''INSERT INTO review_items(user_id,item_type,item_id,canonical_id,box,due_on,last_result,last_attempt_id)
      VALUES(%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(user_id,item_type,item_id) DO UPDATE SET
      box=EXCLUDED.box,due_on=EXCLUDED.due_on,last_result=EXCLUDED.last_result,last_attempt_id=EXCLUDED.last_attempt_id,updated_at=clock_timestamp()''',
      (a['user_id'],kind,a['canonical_id'],a['canonical_id'],box,due,correct,attempt))
    if vocab:
        # Invalidate older open recognition presentations after every real answer,
        # including Bank, games and Smart Review. Legacy fields are projections;
        # queue membership and due dates are read exclusively from review_items.
        from ..routers.vocabulary import learning_hash
        await cur.execute('''UPDATE vocabulary_state SET version=version+1,stage=%s,
          due_at=COALESCE(%s::date::timestamp AT TIME ZONE 'Asia/Kolkata',due_at),
          content_hash=%s,score_version=%s,appearance_version=%s,appearance_id=%s
          WHERE user_id=%s AND question_id=%s''',(6 if due is None else box if correct else 0,due,learning_hash(a['scoring_snapshot']),source['score_version'],source['appearance_version'],source['primary_appearance_id'],a['user_id'],a['canonical_id']))


async def vocabulary_exposure(cur,user,qid,action,day):
    await cur.execute("SELECT * FROM review_items WHERE user_id=%s AND item_type='vocab' AND item_id=%s FOR UPDATE",(user,qid))
    old=await cur.fetchone();box=old['box'] if old and action=='defer' else 1
    due=max(old['due_on'],day+timedelta(days=1)) if old and old['due_on'] and action=='defer' else day+timedelta(days=1)
    correct=bool(old and old['last_result'] and action=='defer')
    await cur.execute('''INSERT INTO review_items(user_id,item_type,item_id,canonical_id,box,due_on,last_result)
      VALUES(%s,'vocab',%s,%s,%s,%s,%s) ON CONFLICT(user_id,item_type,item_id) DO UPDATE SET
      box=EXCLUDED.box,due_on=EXCLUDED.due_on,last_result=EXCLUDED.last_result,updated_at=clock_timestamp()''',(user,qid,qid,box,due,correct))
    return {'box':box,'due_on':due,'last_result':correct}


async def seed(cur,user):
    """Only latest eligible mistakes; historical retries never earn promotions."""
    from .mastery import account
    if not await account(cur,user):
        return
    await cur.execute('''WITH latest AS (SELECT DISTINCT ON(canonical_id) * FROM attempts
      WHERE user_id=%s AND canonical_id IS NOT NULL ORDER BY canonical_id,at DESC,id DESC)
      SELECT a.id,a.canonical_id FROM latest a JOIN v_scorable q ON q.id=a.canonical_id
      LEFT JOIN LATERAL(SELECT payload FROM attempt_assessments WHERE attempt_id=a.id ORDER BY id DESC LIMIT 1) aa ON true
      LEFT JOIN LATERAL(SELECT x.value->>'outcome' AS outcome FROM mock_assessments m
        CROSS JOIN LATERAL jsonb_array_elements(m.payload->'rows') x(value)
        WHERE m.mock_id=a.mock_id AND x.value->>'question_id'=a.canonical_id
        ORDER BY m.created_at DESC,m.id DESC LIMIT 1) ma ON true
      WHERE COALESCE(ma.outcome,CASE WHEN aa.payload->>'reason'='legacy_unversioned' THEN NULL ELSE aa.payload->>'outcome' END,
        CASE WHEN a.correct THEN 'correct' ELSE 'wrong' END)='wrong' ORDER BY a.id''',(user,))
    for a in await cur.fetchall():
        await cur.execute('''INSERT INTO review_items(user_id,item_type,item_id,canonical_id,box,due_on,last_result,last_attempt_id)
          VALUES(%s,'question',%s,%s,1,(now() AT TIME ZONE 'Asia/Kolkata')::date+1,false,%s)
          ON CONFLICT DO NOTHING''',(user,a['canonical_id'],a['canonical_id'],a['id']))


async def reconcile(cur,user):
    """Corrections can reset an incorrect schedule, never supply a promotion."""
    await cur.execute("SELECT * FROM review_items WHERE user_id=%s AND canonical_id IS NOT NULL ORDER BY item_type,item_id FOR UPDATE",(user,))
    for item in await cur.fetchall():
        a = await attempt_input(cur,item['last_attempt_id'])
        if not a or not a['eligible'] or a['outcome'] not in ('correct','wrong'):
            continue  # Current eligibility also gates every read/compose.
        correct = a['outcome'] == 'correct'
        if correct == item['last_result']:
            continue
        if correct:
            await cur.execute("UPDATE review_items SET last_result=true,updated_at=clock_timestamp() WHERE user_id=%s AND item_type=%s AND item_id=%s",(user,item['item_type'],item['item_id']))
        else:
            await cur.execute("UPDATE review_items SET box=1,due_on=(now() AT TIME ZONE 'Asia/Kolkata')::date+1,last_result=false,updated_at=clock_timestamp() WHERE user_id=%s AND item_type=%s AND item_id=%s",(user,item['item_type'],item['item_id']))


def selection_sql():
    """One private, typed due projection; source/entitlement checks precede counts."""
    from ..routers.learning import not_assessed
    from .curated_practice import ACCESS
    return '''SELECT r.item_id,r.item_type,r.canonical_id,r.box,r.due_on,q.question,qc.subject_id,qc.topic_id,
      COALESCE(qc.subject_label,'Unclassified') AS subject_label,qc.topic_label,
      EXISTS(SELECT 1 FROM user_focus_subjects f JOIN review_taxonomy s ON s.id=f.subject_id AND s.active AND s.level='subject'
        WHERE f.user_id=r.user_id AND f.subject_id=qc.subject_id) AS focused,
      false AS curated,NULL::text AS deck_id,NULL::text AS content_hash,true AS reward_due
      FROM v_bank_review_items r JOIN v_scorable q ON q.id=r.canonical_id
      LEFT JOIN question_classifications qc ON qc.question_id=q.id AND qc.review_status='approved'
      WHERE r.user_id=%(user)s AND r.due_on IS NOT NULL AND '''+not_assessed('q')+'''
      UNION ALL
      SELECT r.item_id,r.item_type,NULL::text AS canonical_id,
      CASE WHEN r.vocab_content_hash IS DISTINCT FROM e.content_hash THEN 1 ELSE r.box END AS box,
      CASE WHEN r.vocab_content_hash IS DISTINCT FROM e.content_hash THEN (now() AT TIME ZONE 'Asia/Kolkata')::date ELSE r.due_on END AS due_on,
      e.payload->>'word' AS question,e.subject_id,NULL::text AS topic_id,t.label AS subject_label,
      'Reviewed word cards'::text AS topic_label,
      EXISTS(SELECT 1 FROM user_focus_subjects f JOIN review_taxonomy s ON s.id=f.subject_id AND s.active AND s.level='subject'
        WHERE f.user_id=r.user_id AND f.subject_id=e.subject_id) AS focused,
      true AS curated,e.deck_id,e.content_hash,r.vocab_content_hash=e.content_hash AS reward_due
      FROM review_items r JOIN v_curated_vocabulary e ON e.id=r.vocab_card_id
      JOIN review_taxonomy t ON t.id=e.subject_id AND t.active AND t.level='subject'
      WHERE %(include_curated)s AND r.user_id=%(user)s AND (r.due_on IS NOT NULL OR r.vocab_content_hash IS DISTINCT FROM e.content_hash)
      AND '''+ACCESS


async def selection(cur,user,size,focused=False,through=None,item_type='all',deck=None,include_curated=True):
    await cur.execute('WITH items AS ('+selection_sql()+''') SELECT * FROM items
      WHERE due_on<=COALESCE(%(through)s::date,(now() AT TIME ZONE 'Asia/Kolkata')::date)
      AND (NOT %(focused)s OR focused) AND (%(kind)s='all' OR item_type=%(kind)s)
      AND (%(deck)s::text IS NULL OR deck_id=%(deck)s) ORDER BY due_on,item_id LIMIT %(limit)s''',
      {'user':user,'include_curated':include_curated,'focused':focused,'through':through,'kind':item_type,'deck':deck,'limit':size})
    return await cur.fetchall()


async def queue(cur,user,limit=50,offset=0,include_curated=True,deck=None):
    args={'user':user,'include_curated':include_curated,'limit':limit,'offset':offset,'deck':deck}
    base='SELECT * FROM ('+selection_sql()+') eligible WHERE (%(deck)s::text IS NULL OR deck_id=%(deck)s)'
    await cur.execute('WITH items AS ('+base+') SELECT * FROM items ORDER BY due_on,item_id LIMIT %(limit)s OFFSET %(offset)s',args)
    items=await cur.fetchall()
    await cur.execute('WITH items AS ('+base+''') SELECT
      count(*) FILTER(WHERE due_on<=(now() AT TIME ZONE 'Asia/Kolkata')::date)::int AS due_count,
      count(*)::int AS scheduled_count,
      count(*) FILTER(WHERE item_type='vocab' AND due_on<=(now() AT TIME ZONE 'Asia/Kolkata')::date)::int AS vocabulary_due_count,
      count(*) FILTER(WHERE item_type='vocab')::int AS vocabulary_scheduled_count,
      count(*) FILTER(WHERE curated AND due_on<=(now() AT TIME ZONE 'Asia/Kolkata')::date)::int AS curated_due_count,
      count(*) FILTER(WHERE curated)::int AS curated_scheduled_count FROM items''',args)
    counts=await cur.fetchone()
    from .curated_release import enabled
    return {**counts,'curated_writes_enabled':enabled(),'items':items,'has_more':offset+len(items)<counts['scheduled_count'],'interval_days':list(INTERVALS),'max_session_size':20}
