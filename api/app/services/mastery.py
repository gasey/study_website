"""Private verified-key rollups and explicitly prospective mastery milestones."""
from datetime import timedelta

RULE_VERSION = 'topic-mastery-v1'

# Match score-summary's latest append-only assessment, rather than rewriting an
# original attempt. Original provenance and today's eligibility are both gates.
VERIFIED_ACTIVITY = """
 SELECT a.*,
   COALESCE(ma.outcome,aa.payload->>'outcome',CASE WHEN a.correct THEN 'correct' ELSE 'wrong' END) AS outcome
 FROM attempts a JOIN v_scorable q ON q.id=a.canonical_id
 LEFT JOIN mock_session_questions sq ON sq.mock_id=a.mock_id AND sq.canonical_id=a.canonical_id
 LEFT JOIN LATERAL(SELECT payload FROM attempt_assessments WHERE attempt_id=a.id ORDER BY id DESC LIMIT 1) aa ON true
 LEFT JOIN LATERAL(SELECT x.value->>'outcome' AS outcome FROM mock_assessments m
   CROSS JOIN LATERAL jsonb_array_elements(m.payload->'rows') x(value)
   WHERE m.mock_id=a.mock_id AND x.value->>'question_id'=a.canonical_id
   ORDER BY m.created_at DESC,m.id DESC LIMIT 1) ma ON true
 WHERE a.user_id=%(user)s AND COALESCE(a.scoring_snapshot,sq.snapshot)->>'answer_source' IN ('official','key')
   AND a.chosen_text IS NOT NULL
"""
VERIFIED_ATTEMPTS = '''SELECT e.*,qc.subject_id,qc.topic_id AS topic FROM ('''+VERIFIED_ACTIVITY+''') e
 JOIN question_classifications qc ON qc.question_id=e.canonical_id
 WHERE qc.review_status='approved' AND qc.topic_id IS NOT NULL'''


async def account(cur, user):
    await cur.execute('SELECT email IS NOT NULL AS account FROM users WHERE id=%s', (user,))
    row = await cur.fetchone()
    return bool(row and row['account'])


def tier(attempted, correct, review_completed=False):
    if attempted >= 20 and correct * 100 >= attempted * 85 and review_completed:
        return 'mastered'
    if attempted >= 10 and correct * 100 >= attempted * 70:
        return 'proficient'
    return 'practicing' if attempted >= 5 else 'exploring'


async def prepare(cur,user,question_ids=None):
    """Refresh/latch the pre-activity baseline while owning the shared job lock."""
    if not await account(cur,user):return
    await cur.execute('SELECT learning_habit_lock(%s)',(user,))
    await refresh(cur,user,question_ids)


async def refresh(cur, user, question_id=None, *, award_attempt_ids=(), award_review_session=None):
    """Rebuild affected topics; full rebuilds also remove stale classifications.

    Locking is shared by immediate answers and the durable worker. Callers first
    own this user's job row, matching the insert-trigger lock order.
    """
    if not await account(cur, user):
        return
    await cur.execute('SELECT pg_advisory_xact_lock(hashtext(%s))', ('learning:'+user,))
    topic_filter = ''
    question_ids=([question_id] if isinstance(question_id,str) else question_id) or None
    params = {'user': user, 'questions': question_ids}
    if question_id:
        topic_filter = ''' AND (qc.subject_id,qc.topic_id) IN
          (SELECT subject_id,topic_id FROM question_classifications WHERE question_id=ANY(%(questions)s) AND review_status='approved')'''
    await cur.execute('''WITH eligible AS ('''+VERIFIED_ATTEMPTS+topic_filter+'''), latest AS (
       SELECT DISTINCT ON(canonical_id) * FROM eligible ORDER BY canonical_id,at DESC,id DESC)
       SELECT subject_id,topic,count(*)::int AS attempted,
         count(*) FILTER(WHERE outcome='correct')::int AS correct,max(at) AS last_activity
       FROM latest WHERE outcome IN ('correct','wrong') GROUP BY subject_id,topic''', params)
    rows = await cur.fetchall()
    # Compare to the same latest-attempt aggregation above. An older valid
    # attempt cannot keep a topic alive after its latest assessment is excluded.
    await cur.execute('''SELECT subject_id,topic FROM user_topic_mastery WHERE user_id=%(user)s
      AND (%(questions)s::text[] IS NULL OR (subject_id,topic) IN
        (SELECT subject_id,topic_id FROM question_classifications WHERE question_id=ANY(%(questions)s)))''',params)
    stale = {(r['subject_id'],r['topic']) for r in await cur.fetchall()} - {(r['subject_id'],r['topic']) for r in rows}
    for subject, topic in stale:
        await cur.execute('DELETE FROM user_topic_mastery WHERE user_id=%s AND subject_id=%s AND topic=%s', (user,subject,topic))
    await cur.execute('SELECT clock_timestamp() AS now')
    now = (await cur.fetchone())['now']
    from .mastery_rewards import evidence,settle
    causes=await evidence(cur,user,award_attempt_ids,award_review_session)
    for row in rows:
        key = (user,row['subject_id'],row['topic'])
        await cur.execute('SELECT state,proficient_at,mastered_at FROM user_topic_mastery WHERE user_id=%s AND subject_id=%s AND topic=%s', key)
        old = await cur.fetchone() or {}
        proficient = row['attempted'] >= 10 and row['correct'] * 100 >= row['attempted'] * 70
        proficient_at = (old.get('proficient_at') or now) if proficient else None
        reviewed = False
        if proficient_at:
            # Finishing a set of viewed/skipped cards is not a completed review.
            # At least one currently eligible, scored answer must touch the topic.
            await cur.execute('''SELECT EXISTS(SELECT 1 FROM practice_study_sessions s
              JOIN practice_request_receipts r ON r.user_id=s.user_id
                AND r.request_key LIKE 'study:'||s.id||':%%'
              JOIN ('''+VERIFIED_ATTEMPTS+''') e ON e.id=r.attempt_id
              WHERE s.user_id=%(user)s AND s.kind='review' AND s.finished_at IS NOT NULL
                AND e.context='review' AND e.outcome IN ('correct','wrong')
                AND e.canonical_id=ANY(s.question_ids) AND e.collection_id IS NULL
                AND e.paper_id=s.paper_ids[array_position(s.question_ids,e.canonical_id)]
                AND r.request_key='study:'||s.id||':'||left(encode(sha256(convert_to(e.canonical_id,'UTF8')),'hex'),32)
                AND e.at>=s.created_at AND e.at<=s.finished_at
                AND e.subject_id=%(subject)s AND e.topic=%(topic)s
                AND s.finished_at>=%(after)s AND e.at>=%(after)s) AS reviewed''',
              params | {'subject':row['subject_id'],'topic':row['topic'],'after':proficient_at+timedelta(days=14)})
            reviewed = (await cur.fetchone())['reviewed']
        state = tier(row['attempted'],row['correct'],reviewed)
        mastered_at = (old.get('mastered_at') or now) if state == 'mastered' else None
        await cur.execute('''INSERT INTO user_topic_mastery(user_id,subject_id,topic,state,distinct_attempted,
          distinct_correct_latest,last_verified_activity_at,proficient_at,mastered_at,rule_version)
          VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(user_id,subject_id,topic) DO UPDATE SET
          state=EXCLUDED.state,distinct_attempted=EXCLUDED.distinct_attempted,distinct_correct_latest=EXCLUDED.distinct_correct_latest,
          last_verified_activity_at=EXCLUDED.last_verified_activity_at,proficient_at=EXCLUDED.proficient_at,
          mastered_at=EXCLUDED.mastered_at,rule_version=EXCLUDED.rule_version,updated_at=clock_timestamp()''',
          (*key,state,row['attempted'],row['correct'],row['last_activity'],proficient_at,mastered_at,RULE_VERSION))
        await settle(cur,user,row['subject_id'],row['topic'],old.get('state'),state,causes.get((row['subject_id'],row['topic'])))


async def snapshot(cur, user):
    from .today import saved_exam
    exam=await saved_exam(cur,user)
    await cur.execute('''SELECT m.*,COALESCE(s.label,m.subject_id) AS subject_label,COALESCE(t.label,m.topic) AS topic_label,
      round(100.0*distinct_correct_latest/distinct_attempted,1)::float AS accuracy,
      state IN ('proficient','mastered') AND last_verified_activity_at<=now()-interval '45 days' AS rusty,
      EXISTS(SELECT 1 FROM user_focus_subjects f JOIN review_taxonomy r ON r.id=f.subject_id AND r.active
        WHERE f.user_id=m.user_id AND f.subject_id=m.subject_id) AS focused,
      (%(exam)s::text IS NULL OR EXISTS(SELECT 1 FROM question_classifications qc
        JOIN appearances a ON a.canonical_id=qc.question_id JOIN collection_papers cp ON cp.paper_id=a.paper_id
        JOIN collections c ON c.id=cp.collection_id AND c.live_version=cp.version AND c.visibility='public'
        WHERE c.id=%(exam)s AND qc.review_status='approved' AND qc.subject_id=m.subject_id AND qc.topic_id=m.topic)) AS in_primary_exam
      FROM user_topic_mastery m LEFT JOIN review_taxonomy s ON s.id=m.subject_id
      LEFT JOIN review_taxonomy t ON t.id=m.topic WHERE user_id=%(user)s
      ORDER BY focused DESC,in_primary_exam DESC,subject_label,topic_label,m.topic''',{'user':user,'exam':exam['id'] if exam else None})
    return {'items':await cur.fetchall(),'rule_version':RULE_VERSION,'exam':exam,
            'basis':'Verified-key study activity. A study aid, not an exam-readiness certification.'}
