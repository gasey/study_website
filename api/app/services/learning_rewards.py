"""Read-only explanations, league divisions, daily quests and streak helpers."""
from datetime import timedelta
from zoneinfo import ZoneInfo

RULE_VERSION='learning-v1'

SCHOLAR_TITLES=(
    (12,'MPSC Common Core Master'),
    (8,'Secretariat Fellow'),
    (5,'Aizawl Core Scholar'),
    (3,'Chaltlang Cadet'),
    (1,'Foundation Novice'),
)

LEAGUE_DIVISIONS=(
    (2000,'MPSC Topper League','diamond-crest'),
    (1400,'Diamond Ranker','diamond'),
    (700,'Gold Fellow','gold'),
    (300,'Silver Scholar','silver'),
    (0,'Bronze Aspirant','bronze'),
)

DAILY_QUEST_DEFS={
    'warmup_circuit':{
        'key':'warmup_circuit',
        'title':'Ring 1 · Daily Warm-Up Circuit',
        'description':'Complete 1 game run or answer 10 verified questions today',
        'target':10,
        'xp':20,
        'points':2,
    },
    'cross_stream_triad':{
        'key':'cross_stream_triad',
        'title':'Ring 2 · Cross-Stream Triad',
        'description':'Get 6 verified questions right across Foundation pillars today',
        'target':6,
        'xp':30,
        'points':3,
    },
    'mastery_closure':{
        'key':'mastery_closure',
        'title':'Ring 3 · High-Score or Revision Closure',
        'description':'Score 900+ pts in a game or complete 5 practice/revision checks today',
        'target':5,
        'xp':50,
        'points':5,
    },
}

def scholar_title(level:int)->str:
    for floor,title in SCHOLAR_TITLES:
        if level>=floor:return title
    return 'Foundation Novice'

def league_division(weekly_xp:int)->dict:
    xp=max(0,int(weekly_xp or 0))
    for i,(floor,name,tier) in enumerate(LEAGUE_DIVISIONS):
        if xp>=floor:
            next_floor=LEAGUE_DIVISIONS[i-1][0] if i>0 else None
            next_name=LEAGUE_DIVISIONS[i-1][1] if i>0 else None
            return {
                'name':name,
                'tier':tier,
                'floor_xp':floor,
                'next_division':next_name,
                'next_division_xp':next_floor,
                'xp_to_promote':max(0,next_floor-xp) if next_floor is not None else 0,
            }
    return {'name':'Bronze Aspirant','tier':'bronze','floor_xp':0,'next_division':'Silver Scholar','next_division_xp':300,'xp_to_promote':300}

def level_bounds(xp):
    from math import isqrt
    level=max(1,isqrt(max(0,xp)//40))
    return {'level':level,'level_floor_xp':0 if level==1 else 40*level**2,'next_level_xp':40*(level+1)**2,'title':scholar_title(level)}

async def touch_daily_streak(cur,user:str):
    await cur.execute("SELECT email IS NOT NULL AS account FROM users WHERE id=%s",(user,))
    row=await cur.fetchone()
    if not row or not row['account']:return None
    await cur.execute("SELECT (now() AT TIME ZONE 'Asia/Kolkata')::date AS today")
    today=(await cur.fetchone())['today']
    await cur.execute("INSERT INTO reward_profiles(user_id) VALUES(%s) ON CONFLICT DO NOTHING",(user,))
    await cur.execute("SELECT current_streak_days,longest_streak_days,last_active_ist_date,streak_shields FROM reward_profiles WHERE user_id=%s FOR UPDATE",(user,))
    prof=await cur.fetchone()
    cur_streak=prof['current_streak_days'] or 0
    longest=prof['longest_streak_days'] or 0
    last_date=prof['last_active_ist_date']
    shields=prof['streak_shields'] or 0
    if last_date==today:
        return {'current_streak_days':cur_streak,'longest_streak_days':longest,'streak_shields':shields,'last_active_ist_date':today}
    if last_date is None:
        cur_streak=1
    else:
        gap=(today-last_date).days
        if gap==1:
            cur_streak+=1
        elif gap==2 and shields>0:
            shields-=1
            cur_streak+=1
        else:
            cur_streak=1
    longest=max(longest,cur_streak)
    await cur.execute(
        "UPDATE reward_profiles SET current_streak_days=%s,longest_streak_days=%s,last_active_ist_date=%s,streak_shields=%s WHERE user_id=%s",
        (cur_streak,longest,today,shields,user),
    )
    return {'current_streak_days':cur_streak,'longest_streak_days':longest,'streak_shields':shields,'last_active_ist_date':today}

async def daily_quests_status(cur,user:str)->dict:
    await cur.execute("SELECT (now() AT TIME ZONE 'Asia/Kolkata')::date AS today, (date_trunc('day',now() AT TIME ZONE 'Asia/Kolkata') AT TIME ZONE 'Asia/Kolkata') AS day_start")
    t_row=await cur.fetchone()
    today=t_row['today']
    day_start=t_row['day_start']

    await cur.execute(
        """SELECT
          count(*)::int AS total_attempts,
          count(*) FILTER (WHERE correct)::int AS correct_attempts,
          count(*) FILTER (WHERE context IN ('practice','review'))::int AS practice_attempts
        FROM attempts WHERE user_id=%s AND at>=%s""",
        (user,day_start),
    )
    att=await cur.fetchone()

    await cur.execute(
        """SELECT
          count(*)::int AS games_finished,
          COALESCE(max(m.score),0)::int AS max_score
        FROM game_members m JOIN game_rooms r ON r.id=m.room_id
        WHERE m.user_id=%s AND m.left_at IS NULL AND r.state='finished' AND r.finished_at>=%s""",
        (user,day_start),
    )
    gms=await cur.fetchone()

    await cur.execute(
        "SELECT quest_key,xp_awarded,points_awarded,claimed_at FROM daily_quest_claims WHERE user_id=%s AND ist_date=%s",
        (user,today),
    )
    claimed_map={r['quest_key']:r for r in await cur.fetchall()}

    warmup_prog=min(10,max(10 if gms['games_finished']>=1 else 0,att['total_attempts']))
    triad_prog=min(6,att['correct_attempts'])
    mastery_prog=5 if gms['max_score']>=900 else min(5,max(att['practice_attempts'],att['correct_attempts']//2))

    progress_by_key={
        'warmup_circuit':warmup_prog,
        'cross_stream_triad':triad_prog,
        'mastery_closure':mastery_prog,
    }

    quests=[]
    for q_key in ('warmup_circuit','cross_stream_triad','mastery_closure'):
        d=DAILY_QUEST_DEFS[q_key]
        prog=progress_by_key[q_key]
        c_row=claimed_map.get(q_key)
        quests.append({
            'key':q_key,
            'title':d['title'],
            'description':d['description'],
            'progress':prog,
            'target':d['target'],
            'completed':prog>=d['target'],
            'claimed':c_row is not None,
            'xp_reward':d['xp'],
            'points_reward':d['points'],
            'xp_awarded':c_row['xp_awarded'] if c_row else None,
            'points_awarded':c_row['points_awarded'] if c_row else None,
        })

    # Build 7-day Mon..Sun IST activity strip for current week
    monday=today-timedelta(days=today.weekday())
    await cur.execute(
        """SELECT DISTINCT (at AT TIME ZONE 'Asia/Kolkata')::date AS d
           FROM attempts WHERE user_id=%s AND at >= (%s::timestamp AT TIME ZONE 'Asia/Kolkata')""",
        (user,monday.isoformat()),
    )
    active_days={r['d'] for r in await cur.fetchall()}
    labels=['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
    week_strip=[]
    for i in range(7):
        d=monday+timedelta(days=i)
        week_strip.append({
            'day':labels[i],
            'date':d.isoformat(),
            'active':d in active_days or (d==today and (warmup_prog>0 or len(claimed_map)>0)),
            'is_today':d==today,
        })

    return {'ist_date':today.isoformat(),'quests':quests,'week_strip':week_strip}

async def attempt_reward(cur,user,question,attempt,correct,source,context):
    await cur.execute('SELECT email IS NOT NULL AS account FROM users WHERE id=%s',(user,))
    account=(await cur.fetchone())['account']
    reason='guest' if not account else 'incorrect' if not correct else 'unofficial' if source not in ('official','key') else 'ineligible'
    await cur.execute('''SELECT c.attempt_id,l.id,l.xp,l.points,l.rule_version FROM reward_question_claims c
      JOIN reward_ledger l ON l.event_key='question:'||c.user_id||':'||c.canonical_id
      WHERE c.user_id=%s AND c.canonical_id=%s''',(user,question))
    receipt=await cur.fetchone()
    if receipt and receipt['attempt_id']==attempt:
        return {'status':'awarded','xp':receipt['xp'],'points':receipt['points'],'receipt_id':receipt['id'],'rule_version':receipt['rule_version']}
    if account and correct and source in ('official','key'):
        if receipt:reason='already_rewarded'
        elif context=='practice':
            await cur.execute("SELECT COALESCE(sum(xp),0)::int AS n FROM reward_ledger WHERE user_id=%s AND kind IN ('study','game') AND created_at>=(date_trunc('day',now() AT TIME ZONE 'Asia/Kolkata') AT TIME ZONE 'Asia/Kolkata')",(user,))
            if (await cur.fetchone())['n']>=300:reason='daily_cap'
    return {'status':reason,'xp':0,'points':0,'receipt_id':receipt['id'] if receipt else None,'rule_version':RULE_VERSION}
