"""Vocabulary adapters over the shared canonical Leitner queue; no awards."""
from datetime import datetime,time
from zoneinfo import ZoneInfo
from .vocabulary_decks import DECK_FILTER

DAILY_NEW=5
INDIA=ZoneInfo('Asia/Kolkata')
STALE="(s.score_version<>e.score_version OR s.appearance_version<>e.appearance_version OR s.appearance_id IS DISTINCT FROM e.primary_appearance_id)"

def due_time(day):
    return datetime.combine(day,time.min,INDIA) if day else None

def stage(row):
    return 6 if row and row['due_on'] is None else row['box'] if row and row['last_result'] else 0

async def schedule(cur,user,qid):
    await cur.execute("SELECT * FROM review_items WHERE user_id=%s AND item_type='vocab' AND item_id=%s",(user,qid))
    return await cur.fetchone()

async def overview(cur,user,scope,deck=None):
    from ..routers.learning import not_assessed
    await cur.execute('SET LOCAL jit=off')
    await cur.execute('''SELECT count(*)::int AS eligible,
      count(*) FILTER(WHERE r.item_id IS NOT NULL)::int AS started,
      count(*) FILTER(WHERE r.item_id IS NOT NULL AND (r.due_on<=(now() AT TIME ZONE 'Asia/Kolkata')::date OR '''+STALE+'''))::int AS due,
      count(*) FILTER(WHERE r.box=5 AND r.last_result AND NOT '''+STALE+''')::int AS retaining,
      count(*) FILTER(WHERE r.item_id IS NOT NULL AND r.due_on IS NULL AND NOT '''+STALE+''')::int AS graduated,
      COALESCE(sum(s.graded),0)::int AS graded,COALESCE(sum(s.correct),0)::int AS correct,
      min(r.due_on) FILTER(WHERE r.due_on>(now() AT TIME ZONE 'Asia/Kolkata')::date) AS next_day
      FROM v_vocabulary_eligible e LEFT JOIN vocabulary_state s ON s.question_id=e.id AND s.user_id=%(user)s
      LEFT JOIN review_items r ON r.user_id=%(user)s AND r.item_type='vocab' AND r.item_id=e.id
      WHERE e.focus=%(scope)s AND '''+DECK_FILTER+' AND '+not_assessed('e'),{'user':user,'scope':scope,'deck':deck})
    row=await cur.fetchone();next_due=due_time(row.pop('next_day'))
    return {**row,'next_due':next_due,'new_daily_target':DAILY_NEW,'recognition_only':True}

async def candidates(cur,user,scope,deck,question,now,new_today):
    from ..routers.learning import not_assessed
    await cur.execute('''SELECT e.id FROM v_vocabulary_eligible e
      LEFT JOIN vocabulary_state s ON s.question_id=e.id AND s.user_id=%(user)s
      LEFT JOIN review_items r ON r.user_id=%(user)s AND r.item_type='vocab' AND r.item_id=e.id
      WHERE e.focus=%(scope)s AND '''+DECK_FILTER+' AND '+not_assessed('e')+'''
      AND (%(question)s::text IS NULL OR e.id=%(question)s)
      AND (r.item_id IS NULL OR r.due_on<=(%(now)s::timestamptz AT TIME ZONE 'Asia/Kolkata')::date OR '''+STALE+''')
      AND (r.item_id IS NOT NULL OR %(new_today)s<%(target)s)
      ORDER BY CASE WHEN r.item_id IS NOT NULL THEN 0 ELSE 1 END,r.due_on NULLS LAST,e.id LIMIT 30''',
      {'user':user,'scope':scope,'deck':deck,'question':question,'now':now,'new_today':new_today,'target':DAILY_NEW})
    return await cur.fetchall()

async def reset_source(cur,user,qid,day):
    # Source/key changes reset a derived schedule, never a result or receipt.
    await cur.execute("UPDATE review_items SET box=1,due_on=%s,last_result=false,updated_at=clock_timestamp() WHERE user_id=%s AND item_type='vocab' AND item_id=%s",(day,user,qid))

async def today(cur,user,include_curated=True):
    summary=await overview(cur,user,'all')
    from .curated_practice import new_today,ACCESS,STALE
    introduced=await new_today(cur,user)
    if include_curated:
        await cur.execute('''SELECT count(*)::int AS eligible,count(r.item_id)::int AS started,
          count(*) FILTER(WHERE r.item_id IS NOT NULL AND (r.due_on<=(now() AT TIME ZONE 'Asia/Kolkata')::date OR '''+STALE+'''))::int AS due
          FROM v_curated_vocabulary e LEFT JOIN review_items r ON r.user_id=%(user)s AND r.vocab_card_id=e.id
          WHERE '''+ACCESS,{'user':user})
        words=await cur.fetchone()
        for name in ('eligible','started','due'):summary[name]+=words[name]
    return {'target':DAILY_NEW,'introduced':introduced,'remaining':max(0,min(DAILY_NEW-introduced,summary['eligible']-summary['started'])),
      'due':summary['due'],'eligible':summary['eligible'],
      'url':'/revise?item_type=vocab' if summary['due'] else '/revise?tab=vocabulary&exam_scope=all'}
