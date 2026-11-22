"""Display-only private room goals, using the existing verified scoring policy."""
from datetime import timedelta
from zoneinfo import ZoneInfo

from . import audience
from .mastery import VERIFIED_ACTIVITY
from .weekly_boards import window

IST = ZoneInfo('Asia/Kolkata')


async def clock(cur, *, as_of=None):
    period = await window(cur, as_of)
    return period | {'week_start': period['start_at'].astimezone(IST).date()}


async def summary(cur, did, viewer, period):
    """Caller owns membership and a consistent transaction snapshot.

    Current consent, membership and either-direction blocks apply even to the
    viewer's own contribution. Rejoining cannot reveal pre-membership activity.
    This is an attempt total, not a distinct-question count or a leaderboard.
    """
    await cur.execute('''SELECT target,version FROM study_desk_weekly_goals
      WHERE desk_id=%s AND week_start=%s''', (did, period['week_start']))
    goal = await cur.fetchone()
    await cur.execute('''SELECT m.user_id,m.joined_at FROM study_desk_members m
      JOIN users u ON u.id=m.user_id AND u.email IS NOT NULL AND u.closed_at IS NULL
      WHERE m.desk_id=%s AND m.left_at IS NULL AND m.sharing->>'progress'='true'
      AND NOT EXISTS(SELECT 1 FROM creator_blocks b WHERE
        (b.user_id=%s AND b.blocked_id=m.user_id) OR
        (b.user_id=m.user_id AND b.blocked_id=%s))
      AND '''+audience.subject_sql('m.user_id')+''' ORDER BY m.user_id''', (did, viewer, viewer))
    members = await cur.fetchall()
    total = 0
    for member in members:
        await cur.execute('''SELECT count(DISTINCT e.id)::int AS total FROM ('''
          + VERIFIED_ACTIVITY + ''') e WHERE e.at>=%(start)s AND e.at<%(end)s
          AND e.at<=%(as_of)s AND e.outcome IN ('correct','wrong')''', {
            'user': member['user_id'],
            'start': max(period['start_at'], member['joined_at']),
            'end': period['end_at'], 'as_of': period['as_of'],
          })
        total += (await cur.fetchone())['total']
    return {
        'week_start': period['week_start'],
        'week_end': period['week_start'] + timedelta(days=6),
        'resets_at': period['end_at'], 'as_of': period['as_of'],
        'timezone': 'Asia/Kolkata', 'target': goal['target'] if goal else None,
        'version': goal['version'] if goal else 0,
        'scored_attempts': total, 'sharing_members': len(members),
        'completed': bool(goal and total >= goal['target']),
    }
