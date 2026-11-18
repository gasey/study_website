#!/usr/bin/env python3
"""Private real-role queue/deck/Today/calendar reads; no workers or activity writes."""
import asyncio,json,os,sys,time
from datetime import timedelta
os.chdir('/');sys.path.insert(0,'/srv/api')
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool
from app import db
from app.services import review_queue,today,owned_calendar,vocabulary_scheduler,vocabulary_decks,reward_economy,vocabulary_release
from app.routers.learning import not_assessed
async def verify():
    db._pool=AsyncConnectionPool('dbname=mpsc',min_size=1,max_size=2,kwargs={'row_factory':dict_row,'options':'-c role=mpsc -c default_transaction_read_only=on -c jit=off -c statement_timeout=15000'},open=False)
    await db._pool.open(wait=True)
    try:
        async with db.cursor() as cur:
            await cur.execute("SELECT current_user,current_setting('transaction_read_only') AS readonly");assert await cur.fetchone()=={'current_user':'mpsc','readonly':'on'}
            await cur.execute('SELECT id FROM users WHERE email IS NOT NULL ORDER BY id');users=[r['id'] for r in await cur.fetchall()]
            await cur.execute('SELECT count(*) AS n FROM reward_ledger');before=(await cur.fetchone())['n']
            await cur.execute("SELECT (now() AT TIME ZONE 'Asia/Kolkata')::date AS day");day=(await cur.fetchone())['day']
        checks=0;timings=[]
        for user in users:
            started=time.monotonic()
            async with db.cursor() as cur:
                queue=await review_queue.queue(cur,user,10000);checks+=1
                assert len({r['item_id'] for r in queue['items']})==len(queue['items'])==queue['scheduled_count']
                await cur.execute('''SELECT count(*)::int AS scheduled,count(*) FILTER(WHERE r.due_on<=(now() AT TIME ZONE 'Asia/Kolkata')::date)::int AS due
                  FROM v_bank_review_items r JOIN v_scorable q ON q.id=r.canonical_id WHERE r.user_id=%(user)s AND r.due_on IS NOT NULL AND '''+not_assessed('q'),{'user':user})
                ground=await cur.fetchone();assert ground['scheduled']==queue['scheduled_count'] and ground['due']==queue['due_count'];checks+=1
                plan=await today.compose(cur,user);assert plan['due_count']==queue['due_count'] and plan['vocabulary']['target']==5;checks+=1
                overview=await vocabulary_scheduler.overview(cur,user,'all');assert overview['due']==queue['vocabulary_due_count'];checks+=1
                catalog=await vocabulary_decks.catalog(cur,user,'all');assert all(0<=r['correct_latest']<=r['attempted']<=r['eligible'] and r['due']<=r['started']<=r['eligible'] for r in catalog['items']);checks+=1
                for item in catalog['items']:
                    own=await vocabulary_scheduler.overview(cur,user,'all',item['id']);assert own['eligible']==item['eligible'] and own['due']==item['due'];checks+=1
                forecast,_=await owned_calendar.learning_layers(cur,user,day,day+timedelta(days=40));assert sum(r['count'] for r in forecast)>=queue['due_count'];checks+=1
            timings.append(round((time.monotonic()-started)*1000,3))
        async with db.cursor() as cur:
            await cur.execute('SELECT count(*) AS n FROM reward_ledger');after=(await cur.fetchone())['n']
            diagnostics=await reward_economy.diagnostics(cur);integrity={k:diagnostics[k] for k in reward_economy.INTEGRITY_FIELDS}
            assert before==after and all(v==0 for v in integrity.values()) and reward_economy.reconciled_release()
            await cur.execute("SELECT count(*) AS n FROM pg_constraint WHERE conname='review_vocab_bank_identity' AND convalidated");assert (await cur.fetchone())['n']==1
        assert vocabulary_release.enabled()
        return {'account_users_checked':len(users),'private_read_checks':checks,'batch_ms':timings,'database_role':'mpsc','transactions_read_only':True,'ledger_before':before,'ledger_after':after,'integrity':integrity,'economy_reconciled':True,'recognition_enabled':True,'workers_started':False,'synthetic_production_activity':False}
    finally:await db._pool.close()
if __name__=='__main__':print(json.dumps(asyncio.run(verify())))
