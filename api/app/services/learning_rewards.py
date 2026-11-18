"""Read-only explanations, league divisions, daily quests and streak helpers."""
from datetime import timedelta
from zoneinfo import ZoneInfo

from .reward_economy import RULE_VERSION

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
    'review_ring':{'key':'review_ring','title':'Ring 2 · Review','description':'Clear 8 scheduled due items in completed Smart Review sets','target':8,'xp':30,'points':3},
    'plan_ring':{'key':'plan_ring','title':'Ring 3 · Today’s plan','description':'Finish your fixed daily review, new-question and Daily Five targets','target':1,'xp':50,'points':5},
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
    # Legacy game callers cannot qualify a day with a view, claim or empty run.
    from .learning_habit import QUALIFIED,clock,streak
    day=await clock(cur)
    await cur.execute('SELECT id FROM ('+QUALIFIED+" AND (a.at AT TIME ZONE 'Asia/Kolkata')::date=%(day)s AND a.at<=clock_timestamp()) e WHERE outcome IN ('correct','wrong') LIMIT 1",{'user':user,'day':day})
    if await cur.fetchone():await cur.execute('SELECT touch_learning_streak(%s,%s)',(user,day))
    return await streak(cur,user)


async def daily_quests_status(cur,user:str)->dict:
    from .learning_habit import QUALIFIED,clock,plan_status
    today=await clock(cur)
    await cur.execute('SELECT count(*)::int AS n FROM ('+QUALIFIED+" AND (a.at AT TIME ZONE 'Asia/Kolkata')::date=%(day)s AND a.at<=clock_timestamp()) e WHERE outcome IN ('correct','wrong')",{'user':user,'day':today})
    attempts=(await cur.fetchone())['n']
    await cur.execute('''SELECT count(*)::int AS n FROM game_members m JOIN game_rooms r ON r.id=m.room_id
      WHERE m.user_id=%s AND m.left_at IS NULL AND r.state='finished' AND m.correct+m.wrong>0
      AND (r.finished_at AT TIME ZONE 'Asia/Kolkata')::date=%s''',(user,today))
    games=(await cur.fetchone())['n']
    await cur.execute('SELECT count(*)::int AS n FROM review_item_completions WHERE user_id=%s AND completed_on=%s',(user,today))
    cleared=(await cur.fetchone())['n']
    plan=await plan_status(cur,user)
    await cur.execute('SELECT quest_key,xp_awarded,points_awarded FROM daily_quest_claims WHERE user_id=%s AND ist_date=%s',(user,today))
    claimed={r['quest_key']:r for r in await cur.fetchall()}
    progress={'warmup_circuit':min(10,max(attempts,10 if games else 0)),'review_ring':min(8,cleared),'plan_ring':int(plan['completed'])}
    quests=[]
    # On cutover day an old ring receipt settles its replacement too. Old rows
    # remain immutable and cannot be replayed into a second same-slot payment.
    for key,old in [('warmup_circuit',None),('review_ring','cross_stream_triad'),('plan_ring','mastery_closure')]:
        definition=DAILY_QUEST_DEFS[key];receipt=claimed.get(key) or claimed.get(old)
        quests.append({'key':key,'title':definition['title'],'description':definition['description'],'subtitle':definition['description'],
          'progress':progress[key],'target':definition['target'],'completed':progress[key]>=definition['target'],
          'claimed':bool(receipt),'settled_by':receipt['quest_key'] if receipt else None,
          'xp_reward':definition['xp'],'points_reward':definition['points'],
          'xp_awarded':receipt['xp_awarded'] if receipt else None,'points_awarded':receipt['points_awarded'] if receipt else None})
    monday=today-timedelta(days=today.weekday())
    await cur.execute('SELECT day FROM user_learning_days WHERE user_id=%s AND day BETWEEN %s AND %s',(user,monday,today))
    days={r['day'] for r in await cur.fetchall()}
    strip=[{'day':label,'label':label,'date':(monday+timedelta(days=i)).isoformat(),
      'active':monday+timedelta(days=i) in days,'is_today':monday+timedelta(days=i)==today} for i,label in enumerate(['Mon','Tue','Wed','Thu','Fri','Sat','Sun'])]
    return {'ist_date':today.isoformat(),'quests':quests,'week_strip':strip,'plan':plan}

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
