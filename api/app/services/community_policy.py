"""Posting privileges are derived from real activity, never points or stored vote weights."""
from fastapi import HTTPException

VERSION='community-v2.2'
TIERS=(None,'Helper','Regular','Mentor','Guide')
AUTHOR_TIER="CASE WHEN u.email IS NOT NULL THEN (ARRAY['Helper','Regular','Mentor','Guide'])[community_display_tier_rank(p.author_id)] END"
AUTHOR_PROFILE="CASE WHEN u.email IS NOT NULL AND EXISTS(SELECT 1 FROM creator_profiles cp WHERE cp.user_id=p.author_id AND cp.public) THEN p.author_id END"
DAY_START="(date_trunc('day',now() AT TIME ZONE 'Asia/Kolkata') AT TIME ZONE 'Asia/Kolkata')"
VALID_VOTE="""v.user_id<>p.author_id AND EXISTS(SELECT 1 FROM users voter WHERE voter.id=v.user_id AND voter.email IS NOT NULL)
 AND NOT EXISTS(SELECT 1 FROM creator_blocks b WHERE (b.user_id=v.user_id AND b.blocked_id=p.author_id) OR (b.user_id=p.author_id AND b.blocked_id=v.user_id))"""
HELPFUL_COUNT='(SELECT count(*)::int FROM post_votes v WHERE v.post_id=p.id AND '+VALID_VOTE+')'

async def account_lock(cur,user):
    # Serialize new writes against closure's user-row update. Closure can then
    # anonymize completed history; a write cannot race in after the tombstone.
    await cur.execute('SELECT email FROM users WHERE id=%s FOR SHARE',(user,))
    row=await cur.fetchone()
    if not row or row['email'] is None:raise HTTPException(401,'Sign in to post')

async def standing(cur,user):
    await cur.execute('SELECT community_weighted_helpful(%s)::float AS helpful',(user,))
    return (await cur.fetchone())['helpful']

async def policy(cur,user):
    await cur.execute('''SELECT email IS NOT NULL AS registered,created_at<=now()-interval '3 days' AS old_enough,
      (SELECT count(*)::int FROM (SELECT 1 FROM attempts WHERE user_id=%s AND correct IS NOT NULL AND canonical_id IS NOT NULL LIMIT 50) scored) AS scored_attempts,
      EXISTS(SELECT 1 FROM sanctions WHERE user_id=%s AND kind IN ('mute','suspension') AND lifted_at IS NULL AND starts_at<=now() AND (ends_at IS NULL OR ends_at>now())) AS sanctioned,
      EXISTS(SELECT 1 FROM posts WHERE author_id=%s AND needs_approval AND NOT hidden) AS pending,
      (SELECT count(*) FROM posts WHERE author_id=%s AND NOT needs_approval AND NOT hidden AND NOT before_fix)>=3 AS established,
      (SELECT count(DISTINCT p.id) FROM posts p JOIN abuse_reports ar ON ar.post_id=p.id
        WHERE p.author_id=%s AND ar.status IN ('open','upheld') AND ar.created_at>COALESCE(
          (SELECT max(ma.created_at) FROM mod_actions ma WHERE ma.target_user=%s AND ma.action='approve'),'-infinity'::timestamptz))>=2 AS repeat_flagged
      FROM users WHERE id=%s''',(user,user,user,user,user,user,user))
    row=await cur.fetchone()
    if not row or not row['registered']:
        return {'version':VERSION,'registered':False,'can_create':False,'weighted_helpful':0,'tier':None,'scored_attempts':0,'old_enough':False,'needs_approval':True,'post_limit':5,'reply_limit':30,'posts_remaining':0,'replies_remaining':0}
    helpful=await standing(cur,user)
    await cur.execute('SELECT community_display_tier_rank(%s) AS rank',(user,));display_tier=TIERS[(await cur.fetchone())['rank']]
    restricted=row['pending'] or row['repeat_flagged'] or row['sanctioned']
    tier=next((name for threshold,name in [(150,'Guide'),(50,'Mentor'),(25,'Regular'),(10,'Helper')] if helpful>=threshold),None)
    lifted=not restricted and helpful>=10
    post_limit,reply_limit=(10,60) if not restricted and helpful>=25 else (5,30)
    await cur.execute('''SELECT count(*) FILTER(WHERE parent_id IS NULL)::int AS posts,count(*) FILTER(WHERE parent_id IS NOT NULL)::int AS replies FROM (
      SELECT parent_id FROM posts WHERE author_id=%s AND created_at>='''+DAY_START+'''
      UNION ALL SELECT p.parent_id FROM post_revisions r JOIN posts p ON p.id=r.post_id
      WHERE r.actor_id=%s AND r.version>0 AND r.created_at>='''+DAY_START+''') writes''',(user,user))
    counts=await cur.fetchone()
    return {'version':VERSION,**row,'weighted_helpful':helpful,'tier':tier,'display_tier':display_tier,'mentor_eligible':not restricted and helpful>=50,'privileges_restricted':bool(restricted),
      'can_create':not row['sanctioned'] and (lifted or row['old_enough'] and row['scored_attempts']>=50),
      'needs_approval':not row['established'] or row['repeat_flagged'] or row['pending'],
      'post_limit':post_limit,'reply_limit':reply_limit,'posts_remaining':max(0,post_limit-counts['posts']),
      'replies_remaining':max(0,reply_limit-counts['replies'])}

async def posting_guard(cur,user,*,study=False,reply=False):
    # Same lock as canonical discussion creation: concurrent routes share a budget.
    await cur.execute('SELECT pg_advisory_xact_lock(hashtext(%s))',('discussion:'+user,))
    await account_lock(cur,user)
    state=await policy(cur,user)
    if not state['registered']:raise HTTPException(401,'Sign in to post')
    if state['sanctioned']:raise HTTPException(403,'Your account is currently restricted from posting')
    if study and not state['can_create']:raise HTTPException(403,'Study notes open after 3 days and 50 scored attempts, or Helper standing without a moderation restriction')
    if state['replies_remaining' if reply else 'posts_remaining']==0:
        raise HTTPException(429,'Daily reply limit reached' if reply else 'Daily post limit reached',headers={'Retry-After':'3600'})
    return state
