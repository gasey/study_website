"""Bounded opt-in standings. Public rows contain identity, score and rank only."""
from .learning_rewards import league_division
from . import audience


async def window(cur,as_of=None):
    await cur.execute("""SELECT t AS as_of,date_trunc('week',t AT TIME ZONE 'Asia/Kolkata') AT TIME ZONE 'Asia/Kolkata' AS start_at,
      (date_trunc('week',t AT TIME ZONE 'Asia/Kolkata')+interval '1 week') AT TIME ZONE 'Asia/Kolkata' AS end_at
      FROM (SELECT COALESCE(%s::timestamptz,clock_timestamp()) AS t) x""",(as_of,))
    return await cur.fetchone()


async def project(cur,scores,params,user,clock):
    # Rank public accounts first. A private viewer's hypothetical placement
    # must not move anybody else's rank or insert their identity into the list.
    await cur.execute('''WITH scores AS ('''+scores+'''), ranked AS (
      SELECT *,dense_rank() OVER(ORDER BY score DESC)::int AS rank FROM scores WHERE public AND score>0
    ), viewer AS (
      SELECT s.score,s.public,1+(SELECT count(DISTINCT p.score)::int FROM ranked p WHERE p.score>s.score) AS rank
      FROM scores s WHERE s.user_id=%(viewer)s AND s.score>0
    ), top AS (SELECT * FROM ranked ORDER BY rank,handle,user_id LIMIT 10),
    neighbors AS (SELECT * FROM ranked WHERE rank BETWEEN (SELECT rank-2 FROM viewer) AND (SELECT rank+2 FROM viewer)),
    nearby AS (SELECT * FROM neighbors ORDER BY (user_id=%(viewer)s) DESC,rank,handle,user_id LIMIT 25),
    shown AS (SELECT * FROM top UNION SELECT * FROM nearby),
    enriched AS (
      SELECT s.user_id, s.handle, s.score, s.rank,
        u.avatar,
        COALESCE(cp.public, false) AS profile_public,
        CASE WHEN COALESCE(cp.public, false) OR s.user_id=%(viewer)s THEN s.user_id ELSE NULL END AS public_user_id,
        GREATEST(1, floor(sqrt(GREATEST(0, COALESCE((SELECT sum(rl.xp) FROM reward_ledger rl WHERE rl.user_id=s.user_id), 0)) / 40.0)))::int AS level
      FROM shown s
      JOIN users u ON u.id=s.user_id
      LEFT JOIN creator_profiles cp ON cp.user_id=s.user_id
    )
    SELECT (SELECT count(*)::int FROM ranked) AS total,
      COALESCE((SELECT jsonb_agg(jsonb_build_object('handle',e.handle,'score',e.score,'rank',e.rank,'avatar',e.avatar,'level',e.level,'profile_public',e.profile_public,'user_id',e.public_user_id) ORDER BY e.rank,e.handle,e.user_id) FROM top t JOIN enriched e ON e.user_id=t.user_id),'[]') AS top,
      COALESCE((SELECT jsonb_agg(jsonb_build_object('handle',e.handle,'score',e.score,'rank',e.rank,'avatar',e.avatar,'level',e.level,'profile_public',e.profile_public,'user_id',e.public_user_id) ORDER BY e.rank,e.handle,e.user_id) FROM nearby n JOIN enriched e ON e.user_id=n.user_id),'[]') AS nearby,
      COALESCE((SELECT jsonb_agg(jsonb_build_object('handle',e.handle,'score',e.score,'rank',e.rank,'avatar',e.avatar,'level',e.level,'profile_public',e.profile_public,'user_id',e.public_user_id) ORDER BY e.rank,e.handle,e.user_id) FROM enriched e),'[]') AS items,
      (SELECT jsonb_build_object('score',score,'rank',rank,'public',public) FROM viewer) AS placement,
      (SELECT count(*)>25 FROM neighbors) AS neighborhood_truncated''',params|{'viewer':user})
    return dict(await cur.fetchone())|{'period':'week','timezone':'Asia/Kolkata',
      'period_start':clock['start_at'],'period_end':clock['end_at'],'as_of':clock['as_of'],'has_more':False}


BLOCKS="""NOT EXISTS(SELECT 1 FROM creator_blocks cb WHERE
 (cb.user_id=%(viewer)s AND cb.blocked_id=u.id) OR (cb.user_id=u.id AND cb.blocked_id=%(viewer)s))"""


async def xp(cur,user,*,as_of=None):
    clock=await window(cur,as_of)
    params={'viewer':user,'start':clock['start_at'],'end':clock['end_at'],'as_of':clock['as_of']}
    await cur.execute('''SELECT COALESCE(sum(xp),0)::int AS xp FROM reward_ledger
      WHERE user_id=%(viewer)s AND created_at>=%(start)s AND created_at<%(end)s AND created_at<=%(as_of)s''',params)
    own=(await cur.fetchone())['xp'];league=league_division(own)
    params|={'floor':league['floor_xp'],'ceiling':league['next_division_xp']}
    scores='''SELECT l.user_id,u.handle,COALESCE(p.board_public,false) AS public,sum(l.xp)::int AS score
      FROM reward_ledger l JOIN users u ON u.id=l.user_id AND u.email IS NOT NULL
      LEFT JOIN reward_profiles p ON p.user_id=u.id
      WHERE (p.board_public OR u.id=%(viewer)s) AND l.created_at>=%(start)s AND l.created_at<%(end)s AND l.created_at<=%(as_of)s
      AND '''+BLOCKS+''' AND '''+audience.eligible_sql('u.id')+''' GROUP BY l.user_id,u.handle,p.board_public
      HAVING sum(l.xp)>0 AND sum(l.xp)>=%(floor)s AND (%(ceiling)s::int IS NULL OR sum(l.xp)<%(ceiling)s)'''
    result=await project(cur,scores,params,user,clock)
    # Preserve the established XP field name for existing board readers.
    for key in ('items','top','nearby'):
        for row in result[key]:row['xp']=row.pop('score')
    if result['placement']:result['placement']['xp']=result['placement'].pop('score')
    return result|{'league':{'name':league['name'],'floor_xp':league['floor_xp'],'next_xp':league['next_division_xp']}}


async def games(cur,user,mode,*,as_of=None):
    clock=await window(cur,as_of)
    params={'viewer':user,'mode':mode,'start':clock['start_at'],'end':clock['end_at'],'as_of':clock['as_of']}
    if mode=='daily':
        # Consecutive completed entry days inside this IST week. The running
        # streak is evaluated from real entry dates, not an editable profile.
        scores='''WITH days AS (
          SELECT DISTINCT m.user_id,u.handle,COALESCE(p.board_public,false) AS public,
            (r.finished_at AT TIME ZONE 'Asia/Kolkata')::date AS day
          FROM game_daily_entries e JOIN game_rooms r ON r.id=e.room_id AND r.daily_id=e.daily_id AND r.mode='daily'
          JOIN game_members m ON m.room_id=r.id AND m.user_id=e.user_id AND m.left_at IS NULL
          JOIN users u ON u.id=m.user_id AND u.email IS NOT NULL LEFT JOIN reward_profiles p ON p.user_id=u.id
          WHERE r.state='finished' AND r.finished_at>=%(start)s AND r.finished_at<%(end)s AND r.finished_at<=%(as_of)s
            AND e.daily_id=(r.finished_at AT TIME ZONE 'Asia/Kolkata')::date::text
            AND m.correct+m.wrong>0 AND (p.board_public OR u.id=%(viewer)s) AND '''+BLOCKS+''' AND '''+audience.eligible_sql('u.id')+'''
        ), runs AS (SELECT *,day-(row_number() OVER(PARTITION BY user_id ORDER BY day))::int AS island FROM days),
        lengths AS (SELECT user_id,handle,public,count(*)::int AS score FROM runs GROUP BY user_id,handle,public,island)
        SELECT user_id,handle,public,max(score)::int AS score FROM lengths GROUP BY user_id,handle,public'''
    else:
        score="""count(*) FILTER(WHERE EXISTS(SELECT 1 FROM game_members opponent
          WHERE opponent.room_id=r.id AND opponent.user_id<>m.user_id AND opponent.left_at IS NULL
            AND opponent.correct+opponent.wrong>0)
          AND NOT EXISTS(SELECT 1 FROM game_members opponent WHERE opponent.room_id=r.id
            AND opponent.user_id<>m.user_id AND opponent.left_at IS NULL AND opponent.score>=m.score))::int""" if mode=='duel' else 'max(m.score)::int'
        scores='''SELECT m.user_id,u.handle,COALESCE(p.board_public,false) AS public,'''+score+''' AS score
          FROM game_members m JOIN game_rooms r ON r.id=m.room_id
          JOIN users u ON u.id=m.user_id AND u.email IS NOT NULL LEFT JOIN reward_profiles p ON p.user_id=u.id
          WHERE r.mode=%(mode)s AND r.state='finished' AND r.finished_at>=%(start)s AND r.finished_at<%(end)s AND r.finished_at<=%(as_of)s
            AND m.left_at IS NULL AND m.correct+m.wrong>0 AND (p.board_public OR u.id=%(viewer)s) AND '''+BLOCKS+''' AND '''+audience.eligible_sql('u.id')+'''
          GROUP BY m.user_id,u.handle,p.board_public'''
    return await project(cur,scores,params,user,clock)


def retired(period,cohort='all',track=None):
    """Old selectors stay readable without mislabelling a weekly score as monthly."""
    return {'items':[],'top':[],'nearby':[],'total':0,'placement':None,
            'period':period,'cohort':cohort,'has_more':False,'timezone':'Asia/Kolkata',
            'period_start':None,'period_end':None,'retired':True,
            'message':'Standings now use the current India week. Open the weekly board on the website.',
            **({'track':track} if track else {})}
