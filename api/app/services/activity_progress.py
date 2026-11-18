"""Recorded account activity from sparse rollups; verified mastery is separate."""
from datetime import timedelta
from ..schemas import Progress,DailyActivity,SubjectProgress,ScopeProgress


async def reconcile(cur,user):
    # The caller owns the user's durable job row, including when an answer is
    # being inserted concurrently. Rebuilds repair adoption/classification drift.
    await cur.execute('DELETE FROM user_activity_daily WHERE user_id=%s',(user,))
    await cur.execute('DELETE FROM user_activity_questions WHERE user_id=%s',(user,))
    await cur.execute('''INSERT INTO user_activity_daily
      SELECT a.user_id,COALESCE(a.collection_id,''),COALESCE(a.section_path,''),COALESCE(qc.subject_id,''),
        max(COALESCE(qc.subject_label,'')),(a.at AT TIME ZONE 'Asia/Kolkata')::date,
        count(*)::int,count(*) FILTER(WHERE a.correct)::int,max(a.at)
      FROM attempts a JOIN users u ON u.id=a.user_id AND u.email IS NOT NULL
      LEFT JOIN question_classifications qc ON qc.question_id=a.canonical_id AND qc.review_status='approved'
      WHERE a.user_id=%s GROUP BY a.user_id,a.collection_id,a.section_path,qc.subject_id,(a.at AT TIME ZONE 'Asia/Kolkata')::date''',(user,))
    await cur.execute('''INSERT INTO user_activity_questions
      SELECT DISTINCT a.user_id,COALESCE(a.collection_id,''),COALESCE(a.section_path,''),COALESCE(qc.subject_id,''),a.canonical_id
      FROM attempts a JOIN users u ON u.id=a.user_id AND u.email IS NOT NULL
      LEFT JOIN question_classifications qc ON qc.question_id=a.canonical_id AND qc.review_status='approved'
      WHERE a.user_id=%s AND a.canonical_id IS NOT NULL''',(user,))


async def read(cur,user,detail=False,collection_id=None,section_path=None):
    where='user_id=%(user)s AND (%(collection)s::text IS NULL OR collection_key=%(collection)s) AND (%(section)s::text IS NULL OR section_key=%(section)s)'
    params={'user':user,'collection':collection_id,'section':section_path}
    await cur.execute('''SELECT COALESCE(sum(answered),0)::int AS answered,COALESCE(sum(correct),0)::int AS correct,
      max(last_active_at) AS last_active_at,(now() AT TIME ZONE 'Asia/Kolkata')::date AS today,
      (SELECT count(DISTINCT canonical_id)::int FROM user_activity_questions WHERE '''+where+''') AS unique_questions
      FROM user_activity_daily WHERE '''+where,params)
    totals=await cur.fetchone()
    result=Progress(answered=totals['answered'],correct=totals['correct'],unique_questions=totals['unique_questions'],
      accuracy=round(100*totals['correct']/totals['answered'],1) if totals['answered'] else 0,
      last_active_at=totals['last_active_at'])
    from .learning_habit import streak
    result.current_streak=(await streak(cur,user))['current_streak_days']
    result.streak_basis='account learning'
    if not detail:
        return result
    await cur.execute('''SELECT day,sum(answered)::int AS answered,sum(correct)::int AS correct
      FROM user_activity_daily WHERE '''+where+''' AND day>=(now() AT TIME ZONE 'Asia/Kolkata')::date-29
      GROUP BY day ORDER BY day''',params)
    result.daily_activity=[DailyActivity(day=r['day'].isoformat(),answered=r['answered'],correct=r['correct']) for r in await cur.fetchall()]
    active={r.day for r in result.daily_activity};today=totals['today']
    result.active_days_30=len(active)
    await cur.execute('''WITH totals AS (SELECT subject_key,max(subject_label) AS subject,sum(answered)::int AS answered,
      sum(correct)::int AS correct FROM user_activity_daily WHERE '''+where+''' AND subject_key<>'' GROUP BY subject_key),
      questions AS (SELECT subject_key,count(DISTINCT canonical_id)::int AS unique_questions FROM user_activity_questions
        WHERE '''+where+''' GROUP BY subject_key)
      SELECT t.subject_key AS subject_id,t.subject,t.answered,t.correct,COALESCE(q.unique_questions,0) AS unique_questions
      FROM totals t LEFT JOIN questions q USING(subject_key) ORDER BY t.answered DESC,t.subject''',params)
    result.subjects=[SubjectProgress(**r) for r in await cur.fetchall()]
    dimension='section_key' if collection_id else 'collection_key'
    await cur.execute('''WITH totals AS (SELECT '''+dimension+''' AS key,sum(answered)::int AS answered,sum(correct)::int AS correct
      FROM user_activity_daily WHERE '''+where+''' GROUP BY '''+dimension+'''), questions AS (
      SELECT '''+dimension+''' AS key,count(DISTINCT canonical_id)::int AS unique_questions
      FROM user_activity_questions WHERE '''+where+''' GROUP BY '''+dimension+''')
      SELECT t.*,COALESCE(q.unique_questions,0) AS unique_questions,
        CASE WHEN %(collection)s::text IS NULL THEN COALESCE(c.title,'General study') ELSE COALESCE(cs.title,'Other module practice') END AS label
      FROM totals t LEFT JOIN questions q USING(key)
      LEFT JOIN collections c ON c.id=CASE WHEN %(collection)s::text IS NULL THEN t.key ELSE %(collection)s END
      LEFT JOIN collection_sections cs ON %(collection)s::text IS NOT NULL AND cs.collection_id=c.id AND cs.version=c.live_version AND cs.path=t.key
      ORDER BY t.answered DESC,label''',params)
    scoped=[ScopeProgress(scope_id=r['key'] or ('unsectioned' if collection_id else 'general'),label=r['label'],
      answered=r['answered'],correct=r['correct'],unique_questions=r['unique_questions'],
      accuracy=round(100*r['correct']/r['answered'],1)) for r in await cur.fetchall()]
    if collection_id:result.sections=scoped
    else:result.collections=scoped
    return result
