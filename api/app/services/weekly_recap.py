"""Monday's private growth recap. No jobs, stored summaries or awards."""
from datetime import timedelta
from . import mastery,weekly_boards


async def compose(cur,user,*,as_of=None):
    if not await mastery.account(cur,user):return None
    clock=await weekly_boards.window(cur,as_of)
    await cur.execute("SELECT (%s AT TIME ZONE 'Asia/Kolkata')::date AS day",(clock['as_of'],))
    day=(await cur.fetchone())['day']
    if day.weekday()!=0:return None
    end=clock['start_at'];start=end-timedelta(days=7)
    params={'user':user,'start':start,'end':end,'first':day-timedelta(days=7),'last':day}
    await cur.execute('''SELECT
      (SELECT COALESCE(sum(xp),0)::int FROM reward_ledger WHERE user_id=%(user)s AND created_at>=%(start)s AND created_at<%(end)s) AS xp,
      (SELECT count(*)::int FROM review_item_completions WHERE user_id=%(user)s AND completed_on>=%(first)s AND completed_on<%(last)s) AS reviews_cleared,
      (SELECT count(*)::int FROM user_learning_days WHERE user_id=%(user)s AND day>=%(first)s AND day<%(last)s) AS active_days,
      (SELECT COALESCE(sum(LEAST(duration_seconds,elapsed_seconds)),0)::int FROM study_focus_sessions
        WHERE user_id=%(user)s AND state IN ('completed','cancelled') AND ended_at>=%(start)s AND ended_at<%(end)s) AS focus_seconds''',params)
    result=await cur.fetchone()
    await cur.execute('''SELECT m.topic,COALESCE(t.label,m.topic) AS topic_label,m.tier
      FROM mastery_milestones m LEFT JOIN review_taxonomy t ON t.id=m.topic
      WHERE m.user_id=%(user)s AND m.origin='activity' AND m.created_at>=%(start)s AND m.created_at<%(end)s
      ORDER BY m.created_at,m.topic,m.tier LIMIT 51''',params)
    topics=await cur.fetchall()
    return result|{'week_start':day-timedelta(days=7),'week_end':day-timedelta(days=1),
      'streak_kept':result['active_days']==7,'topics':topics[:50],'more_topics':len(topics)>50,
      'topic_basis':'First qualifying topic milestones recorded last week; historical tiers are not inferred.',
      'focus_basis':'Server-timed focus sessions ended last week.','timezone':'Asia/Kolkata'}
