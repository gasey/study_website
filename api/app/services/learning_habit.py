"""Prospective habit receipts. No backfill and no client-controlled awards."""
from datetime import timedelta
from psycopg.types.json import Jsonb
from .mastery import VERIFIED_ACTIVITY,account

from .reward_economy import RULE_VERSION
QUALIFIED=VERIFIED_ACTIVITY+""" AND a.context IN ('practice','review','game','mock')
 AND (a.context<>'mock' OR EXISTS(SELECT 1 FROM mock_sessions m WHERE m.id=a.mock_id
   AND m.user_id=a.user_id AND m.submitted_at IS NOT NULL AND NOT m.late))"""


async def clock(cur):
    await cur.execute("SELECT (now() AT TIME ZONE 'Asia/Kolkata')::date AS day")
    return (await cur.fetchone())['day']


async def streak(cur,user):
    day=await clock(cur)
    await cur.execute('SELECT current_streak_days,longest_streak_days,last_active_ist_date,streak_shields FROM reward_profiles WHERE user_id=%s',(user,))
    row=await cur.fetchone() or {'current_streak_days':0,'longest_streak_days':0,'last_active_ist_date':None,'streak_shields':0}
    last=row['last_active_ist_date']
    if not last or last<day-timedelta(days=1 if not row['streak_shields'] else 2):row['current_streak_days']=0
    return row


async def capture_plan(cur,user):
    if not await account(cur,user):return
    # Same order as every account attempt and review finish, before any writes.
    await cur.execute('SELECT learning_habit_lock(%s)',(user,))
    day=await clock(cur)
    await cur.execute('SELECT 1 FROM daily_learning_plans WHERE user_id=%s AND day=%s',(user,day))
    if await cur.fetchone():return
    from .today import saved_exam,weak_target,exam_preparation,taper
    from ..routers.learning import not_assessed
    exam=await saved_exam(cur,user)
    preparation=await exam_preparation(cur,user,exam,day)
    target=taper(await weak_target(cur,user,exam),preparation)
    from .review_queue import selection_sql
    await cur.execute('WITH items AS ('+selection_sql()+''') SELECT item_id,curated,content_hash FROM items
      WHERE due_on<=%(day)s AND (NOT curated OR reward_due) ORDER BY item_id''',{'user':user,'day':day,'include_curated':True})
    scheduled=await cur.fetchall();due=[r['item_id'] for r in scheduled];word_hashes={r['item_id']:r['content_hash'] for r in scheduled if r['curated']};pool=[]
    if target:
        await cur.execute('''SELECT q.id FROM v_scorable q JOIN question_classifications qc ON qc.question_id=q.id
          AND qc.review_status='approved' AND qc.subject_id=%(subject)s AND qc.topic_id=%(topic)s
          WHERE EXISTS(SELECT 1 FROM appearances a JOIN collection_papers cp ON cp.paper_id=a.paper_id
            JOIN collections c ON c.id=cp.collection_id AND c.live_version=cp.version AND c.visibility='public'
            WHERE a.canonical_id=q.id AND c.id=%(exam)s)
          AND NOT EXISTS(SELECT 1 FROM user_activity_questions x WHERE x.user_id=%(user)s AND x.canonical_id=q.id)
          AND '''+not_assessed('q')+' ORDER BY q.id',{'user':user,'subject':target['subject_id'],'topic':target['topic'],'exam':exam['id']})
        pool=[r['id'] for r in await cur.fetchall()]
    snapshot={'curated_due_hashes':word_hashes,'exam_preparation':preparation,'exam':exam,'new_target':target,'new_pool':pool,'due_ids':due}
    # Serialize dates/decimals from otherwise public plan inputs.
    import json
    snapshot=json.loads(json.dumps(snapshot,default=str))
    await cur.execute('INSERT INTO daily_learning_plans(user_id,day,snapshot) VALUES(%s,%s,%s) ON CONFLICT DO NOTHING',(user,day,Jsonb(snapshot)))


async def plan_status(cur,user):
    day=await clock(cur)
    await cur.execute('SELECT * FROM daily_learning_plans WHERE user_id=%s AND day=%s',(user,day))
    plan=await cur.fetchone()
    if not plan:return {'started':False,'completed':False,'progress':0,'target':1,'tasks':[],'new_target':None}
    snapshot=plan['snapshot'];tasks=[]
    if snapshot['due_ids']:
        await cur.execute('''SELECT count(*)::int AS target,count(*) FILTER(WHERE EXISTS(
          SELECT 1 FROM review_item_completions e WHERE e.user_id=%(user)s AND e.canonical_id=q.id AND e.completed_on=%(day)s))::int AS progress
          FROM v_scorable q WHERE q.id=ANY(%(ids)s)''',{'user':user,'day':day,'ids':snapshot['due_ids']})
        row=await cur.fetchone()
        hashes=snapshot.get('curated_due_hashes',{})
        if hashes:
            from .curated_practice import ACCESS
            await cur.execute('''SELECT count(*)::int AS target,count(*) FILTER(WHERE EXISTS(
              SELECT 1 FROM vocab_review_completions c JOIN vocab_attempts a ON a.id=c.attempt_id AND a.content_hash=frozen.hash
              WHERE c.user_id=%(user)s AND c.card_id=e.id AND c.completed_on=%(day)s))::int AS progress
              FROM unnest(%(ids)s::text[],%(hashes)s::text[]) frozen(id,hash)
              JOIN v_curated_vocabulary e ON e.id=frozen.id AND e.content_hash=frozen.hash WHERE '''+ACCESS,
              {'user':user,'day':day,'ids':list(hashes),'hashes':list(hashes.values())})
            words=await cur.fetchone()
            for key in ('target','progress'):row[key]+=words[key]
        if row['target']:tasks.append({'key':'reviews',**row})
    target=snapshot['new_target']
    if target:
        await cur.execute('SELECT count(*)::int AS n FROM v_scorable WHERE id=ANY(%s)',(snapshot['new_pool'],))
        needed=min(int(target['target']),(await cur.fetchone())['n'])
        await cur.execute('SELECT count(DISTINCT e.canonical_id)::int AS n FROM ('+QUALIFIED+''') e
          WHERE e.outcome IN ('correct','wrong') AND e.at>=%(started)s AND e.at<=clock_timestamp()
          AND e.canonical_id=ANY(%(ids)s)''',{'user':user,'started':plan['started_at'],'ids':snapshot['new_pool']})
        done=(await cur.fetchone())['n']
        target={**target,'target':needed,'completed':done>=needed,'progress':min(done,needed),'exam_title':snapshot['exam']['title']}
        if needed:tasks.append({'key':'new_questions','progress':min(done,needed),'target':needed})
        else:target=None
    await cur.execute('''SELECT EXISTS(SELECT 1 FROM game_daily_entries e JOIN game_rooms r ON r.id=e.room_id
      JOIN game_members m ON m.room_id=r.id AND m.user_id=e.user_id
      WHERE e.user_id=%s AND e.daily_id=%s AND r.state='finished' AND m.left_at IS NULL AND m.correct+m.wrong>0) AS done''',(user,day.isoformat()))
    done=(await cur.fetchone())['done'];tasks.append({'key':'daily_five','progress':int(done),'target':1})
    completed=sum(t['progress']>=t['target'] for t in tasks)
    return {'exam_preparation':snapshot.get('exam_preparation'),'started':True,'completed':completed==len(tasks),'progress':completed,'target':len(tasks),'tasks':tasks,'new_target':target}


async def review_finish(cur,row):
    user=row['user_id'];day=await clock(cur)
    await cur.execute('SELECT learning_habit_lock(%s)',(user,))
    if not await account(cur,user):return {'status':'guest','xp':0,'points':0}
    # Match the frozen session's server-issued attempt receipt, paper and context.
    await cur.execute('''SELECT e.id,e.canonical_id,e.outcome,i.due_on,
      e.at>=i.opened_at+interval '3 seconds' AS timed,
      i.due_on<=(s.created_at AT TIME ZONE 'Asia/Kolkata')::date AS was_due
      FROM practice_study_sessions s JOIN review_session_items i ON i.session_id=s.id
      JOIN ('''+QUALIFIED+''') e ON e.id=i.attempt_id AND e.canonical_id=i.canonical_id
      JOIN practice_request_receipts r ON r.attempt_id=e.id AND r.user_id=s.user_id
        AND r.request_key='study:'||s.id||':'||left(encode(sha256(convert_to(e.canonical_id,'UTF8')),'hex'),32)
      WHERE s.id=%(sid)s AND s.user_id=%(user)s AND s.kind='review' AND s.finished_at IS NOT NULL
      AND e.context='review' AND e.collection_id IS NULL AND e.outcome IN ('correct','wrong')
      AND e.paper_id=s.paper_ids[array_position(s.question_ids,e.canonical_id)]
      AND e.at>=s.created_at AND e.at<=s.finished_at AND i.opened_at IS NOT NULL''',{'user':user,'sid':row['id']})
    checks=[{**c,'curated':False} for c in await cur.fetchall()]
    from . import curated_sessions
    checks.extend(await curated_sessions.finish_checks(cur,row))
    if checks:await cur.execute('SELECT touch_learning_streak(%s,%s)',(user,day))
    due=[c for c in checks if c['was_due']]
    fresh=[]
    for c in due:
        if not c['timed']:continue
        if c['curated']:
            await cur.execute('''INSERT INTO vocab_review_completions(user_id,card_id,scheduled_due,session_id,attempt_id,correct,completed_on)
              VALUES(%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING RETURNING card_id''',
              (user,c['canonical_id'],c['due_on'],row['id'],c['id'],c['outcome']=='correct',day))
        else:
            await cur.execute('''INSERT INTO review_item_completions(user_id,canonical_id,scheduled_due,session_id,attempt_id,correct,completed_on)
              VALUES(%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING RETURNING canonical_id''',
              (user,c['canonical_id'],c['due_on'],row['id'],c['id'],c['outcome']=='correct',day))
        if await cur.fetchone():fresh.append(c)
    await cur.execute('''SELECT count(*)::int AS n FROM review_session_items i JOIN v_scorable q ON q.id=i.canonical_id
      JOIN practice_study_sessions s ON s.id=i.session_id WHERE s.id=%s
      AND i.due_on<=(s.created_at AT TIME ZONE 'Asia/Kolkata')::date''',(row['id'],))
    total=(await cur.fetchone())['n']+await curated_sessions.total_due(cur,row)
    eligible=len(fresh)>=8 and all(c['timed'] for c in due) and sum(c['outcome']=='correct' for c in fresh)*100>=60*total
    if not eligible:return {'status':'not_eligible','xp':0,'points':0,'due_checked':len(fresh),'minimum_due':8,'minimum_seconds':3}
    await cur.execute('SELECT count(*)::int AS n FROM review_session_rewards WHERE user_id=%s AND day=%s',(user,day))
    slot=(await cur.fetchone())['n']+1
    if slot>2:return {'status':'daily_cap','xp':0,'points':0}
    await cur.execute("SELECT COALESCE(sum(xp),0)::int AS xp FROM reward_ledger WHERE user_id=%s AND kind IN ('study','game') AND (created_at AT TIME ZONE 'Asia/Kolkata')::date=%s",(user,day))
    xp=min(20,max(0,300-(await cur.fetchone())['xp']))
    await cur.execute('''INSERT INTO reward_ledger(user_id,event_key,kind,xp,points,note,rule_version)
      VALUES(%s,%s,'study',%s,2,'Completed scheduled Smart Review',%s) RETURNING id,xp,points''',
      (user,f'review:{user}:{day.isoformat()}:{slot}',xp,RULE_VERSION))
    receipt=await cur.fetchone();ledger=receipt['id']
    await cur.execute('INSERT INTO review_session_rewards(session_id,user_id,day,slot,ledger_id) VALUES(%s,%s,%s,%s,%s)',(row['id'],user,day,slot,ledger))
    return {'status':'awarded','xp':receipt['xp'],'points':receipt['points'],'receipt_id':ledger,'rule_version':RULE_VERSION}
