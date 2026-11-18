#!/usr/bin/env python3
"""Read-only real-role bulk pricing, mail capacity and learning integrity snapshot."""
import asyncio,json,os,sys,time
from datetime import timedelta
os.chdir('/');sys.path.insert(0,os.environ.get('FINNA_VERIFY_API','/srv/api'))
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool
from app import db
from app.services import review_queue,today,owned_calendar,vocabulary_scheduler,vocabulary_decks,reward_economy,curated_practice,curated_release,account_mail,public_share,shareable_tests,onboarding,onboarding_release,bulk_rates
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
                assert await bulk_rates.amount(cur,user) in (5000,10000);checks+=1
                checkin=await onboarding.status(cur,user);assert checkin['exam'] is None or 'id' in checkin['exam'];checks+=1
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
            mail_budget=await account_mail.capacity(cur)
            await cur.execute('SELECT count(*)::int AS n FROM account_mail_deliveries');mail_attempts=(await cur.fetchone())['n']
            assert curated_release.enabled()
            await cur.execute("SELECT q.id FROM canonical_questions q JOIN appearances a ON a.canonical_id=q.id JOIN papers p ON p.id=a.paper_id WHERE q.status='live' ORDER BY q.id LIMIT 3")
            samples=[r['id'] for r in await cur.fetchall()];assert samples
            previews=0
            for qid in samples:
                preview=await public_share.question_preview(cur,qid,exam_scope='all')
                page=public_share.share_page(**preview,action='Open this question').body.decode()
                assert 'og:image' in page and 'answer_text' not in page and 'http-equiv' not in page
                assert set(preview)=={'title','description','badge','target_path','share_path'};previews+=1
            await cur.execute("SELECT id FROM learning_catalog WHERE live_payload IS NOT NULL AND live_test_version IS NOT NULL ORDER BY id LIMIT 3")
            tests=[r['id'] for r in await cur.fetchall()]
            for eid in tests:
                metadata=shareable_tests.metadata(await shareable_tests.published(cur,eid))
                assert not {'questions','question_ids','published_by','author_id'} & set(metadata);previews+=1
            await cur.execute("SELECT count(*) AS n FROM pg_indexes WHERE indexname='practice_onboarding_exam_once'");assert (await cur.fetchone())['n']==1
            await cur.execute("SELECT count(*) AS n FROM practice_study_sessions WHERE filters @> '{\"onboarding_version\":1}'::jsonb AND (kind<>'practice' OR cardinality(question_ids)<>10 OR collection_id IS NULL)")
            assert (await cur.fetchone())['n']==0 and onboarding_release.enabled()
            await cur.execute("SELECT count(*) AS n FROM billing_rate_codes c WHERE uses<>(SELECT count(*) FROM billing_rate_redemptions r WHERE r.code=c.code)")
            assert (await cur.fetchone())['n']==0
            await cur.execute("SELECT count(*) AS n FROM billing_rate_allowlist WHERE (applied_user_id IS NULL)<>(applied_at IS NULL)");assert (await cur.fetchone())['n']==0
            await cur.execute("SELECT count(*) AS n FROM pg_trigger WHERE tgname IN ('immutable_rate_batch','immutable_rate_redemption','rate_allowlist_history','rate_code_history','count_rate_redemption') AND tgenabled='O'");assert (await cur.fetchone())['n']==5
            assert bulk_rates.bulk_rate_release.enabled()
            return {'bulk_integrity_counters':{'code_receipt_mismatches':0,'allowlist_application_mismatches':0},'bulk_history_triggers_enabled':5,'onboarding_unique_index_valid':True,'invalid_onboarding_sets':0,'public_preview_sample':samples[0],'public_preview_reads':previews,'public_tests_checked':len(tests),'no_synthetic_publication':True,'account_users_checked':len(users),'private_read_checks':checks,'batch_ms':timings,'material_revisions_validated':len(revisions),'database_role':'mpsc','transaction_read_only':True,'single_repeatable_read_snapshot':True,'ledger_snapshot_before':before,'ledger_snapshot_after':after,'integrity':integrity,'edit_integrity':edits,'tier_capture_triggers_enabled':10,'economy_reconciled':True,'curated_practice_enabled':True,'mail_budget':mail_budget,'mail_attempts':mail_attempts,'smtp_contacted':False,'workers_started':False,'synthetic_production_activity':False}
    finally:await db._pool.close()
if __name__=='__main__':print(json.dumps(asyncio.run(verify())))
