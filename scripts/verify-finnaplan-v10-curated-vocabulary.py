#!/usr/bin/env python3
"""One read-only real-role snapshot of current publication, learning and integrity."""
import asyncio,json,os,sys,time
from datetime import timedelta
os.chdir('/');sys.path.insert(0,os.environ.get('FINNA_VERIFY_API','/srv/api'))
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool
from app import db
from app.services import review_queue,today,owned_calendar,vocabulary_scheduler,vocabulary_decks,reward_economy,curated_practice,curated_release
from app.services.content_studio import Document
async def verify():
    db._pool=AsyncConnectionPool('dbname='+os.environ.get('FINNA_VERIFY_DB','mpsc'),min_size=1,max_size=1,kwargs={'row_factory':dict_row,'options':'-c role=mpsc -c default_transaction_read_only=on -c jit=off -c statement_timeout=20000'},open=False)
    await db._pool.open(wait=True)
    try:
        async with db.cursor() as cur:
            await cur.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
            await cur.execute("SELECT current_user,current_setting('transaction_read_only') AS readonly");assert await cur.fetchone()=={'current_user':'mpsc','readonly':'on'}
            await cur.execute('SELECT count(*) AS n FROM reward_ledger');before=(await cur.fetchone())['n']
            await cur.execute('SELECT payload FROM material_revisions ORDER BY material_id,revision');revisions=await cur.fetchall()
            for r in revisions:Document.model_validate(r['payload'])
            await cur.execute('SELECT id FROM users WHERE email IS NOT NULL ORDER BY id');users=[r['id'] for r in await cur.fetchall()]
            await cur.execute("SELECT (now() AT TIME ZONE 'Asia/Kolkata')::date AS day");day=(await cur.fetchone())['day']
            checks=0;timings=[]
            for user in users:
                started=time.monotonic()
                queue=await review_queue.queue(cur,user,10000);checks+=1
                assert len({r['item_id'] for r in queue['items']})==len(queue['items'])==queue['scheduled_count']
                legacy=await review_queue.queue(cur,user,10000,include_curated=False);assert not any(r['curated'] for r in legacy['items']);checks+=1
                plan=await today.compose(cur,user);assert plan['due_count']==queue['due_count'] and plan['vocabulary']['target']==5;checks+=1
                bank=await vocabulary_scheduler.overview(cur,user,'all');assert bank['due']+queue['curated_due_count']==queue['vocabulary_due_count'];checks+=1
                catalog=await vocabulary_decks.catalog(cur,user,'all');assert all(0<=r['correct_latest']<=r['attempted']<=r['eligible'] for r in catalog['items']);checks+=1
                words=await curated_practice.catalog(cur,user);checks+=1
                assert all(0<=r['known']<=r['correct_latest']<=r['attempted']<=r['eligible_words'] and r['due']<=r['started']<=r['eligible_cards'] for r in words['items'])
                assert words['known_total']>=0 and words['practice_enabled']
                assert {r['id'] for r in words['items']}=={r['id'] for r in catalog['curated_items']}
                for item in words['items']:
                    own=await review_queue.queue(cur,user,10000,deck=item['id']);assert own['due_count']==item['due'];checks+=1
                forecast,_=await owned_calendar.learning_layers(cur,user,day,day+timedelta(days=40));assert sum(r['count'] for r in forecast)>=queue['due_count'];checks+=1
                timings.append(round((time.monotonic()-started)*1000,3))
            diagnostics=await reward_economy.diagnostics(cur);integrity={k:diagnostics[k] for k in reward_economy.INTEGRITY_FIELDS}
            assert len(integrity)==25 and all(v==0 for v in integrity.values()) and reward_economy.reconciled_release()
            await cur.execute("""SELECT
              (SELECT count(*) FROM posts WHERE accepted AND NOT edit_locked) AS unlocked_accepted,
              (SELECT count(*) FROM posts p WHERE content_version>0 AND NOT EXISTS(SELECT 1 FROM post_revisions r WHERE r.post_id=p.id AND r.version=p.content_version AND r.body=p.body AND r.source_links=p.source_links)) AS missing_current_snapshot,
              (SELECT count(*) FROM posts p WHERE content_version>0 AND NOT EXISTS(SELECT 1 FROM post_revisions r WHERE r.post_id=p.id AND r.version=0)) AS missing_original_snapshot""")
            edits=await cur.fetchone();assert all(v==0 for v in edits.values())
            await cur.execute("SELECT count(*) AS n FROM pg_trigger WHERE tgname LIKE 'community_tier_%' AND tgenabled='O'");assert (await cur.fetchone())['n']==10
            await cur.execute("SELECT count(*) AS n FROM pg_constraint WHERE conname='review_curated_identity' AND convalidated");assert (await cur.fetchone())['n']==1
            await cur.execute('SELECT count(*) AS n FROM reward_ledger');after=(await cur.fetchone())['n'];assert before==after
            assert curated_release.enabled()
            return {'account_users_checked':len(users),'private_read_checks':checks,'batch_ms':timings,'material_revisions_validated':len(revisions),'database_role':'mpsc','transaction_read_only':True,'single_repeatable_read_snapshot':True,'ledger_snapshot_before':before,'ledger_snapshot_after':after,'integrity':integrity,'edit_integrity':edits,'tier_capture_triggers_enabled':10,'economy_reconciled':True,'curated_practice_enabled':True,'workers_started':False,'synthetic_production_activity':False}
    finally:await db._pool.close()
if __name__=='__main__':print(json.dumps(asyncio.run(verify())))
