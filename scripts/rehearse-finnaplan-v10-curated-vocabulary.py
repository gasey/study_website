#!/usr/bin/env python3
"""Fresh private dump clone; additive queue migration and real-role read/write probe."""
import json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];REPORT=ROOT/'reports/finnaplan-v10-curated-vocabulary-20261118'
FILES=('app/services/review_queue.py', 'app/routers/vocabulary.py', 'app/services/vocabulary_decks.py', 'app/services/vocabulary_scheduler.py', 'app/routers/learning_loop.py', 'app/routers/study_sessions.py', 'app/services/learning_habit.py', 'app/services/today.py', 'app/services/owned_calendar.py', 'app/services/reward_economy.py', 'app/services/curated_vocabulary.py', 'app/services/curated_practice.py', 'app/services/curated_sessions.py', 'app/services/curated_release.py', 'app/data/learning-economy-v2.json', 'app/data/curated-vocabulary-writes.json')
SOURCES={n:(ROOT/'api'/n).read_text() for n in FILES};MIGRATION=(ROOT/'api/migrations/0106_curated_vocabulary.sql').read_text()
REMOTE=r'''
import asyncio,hashlib,json,os,shutil,subprocess,sys,tempfile,time
from pathlib import Path
from uuid import uuid4
from urllib.request import urlopen
import psycopg
from psycopg import sql
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from psycopg_pool import AsyncConnectionPool

def fingerprint(conn,table,columns):
    fields=sql.SQL(',').join(map(sql.Identifier,columns))
    where=''
    query=sql.SQL('SELECT md5(ROW({})::text) AS h FROM {}'+where+' ORDER BY h').format(fields,sql.Identifier(table))
    digest=hashlib.sha256();count=0
    with conn.cursor(name='vocab_fp_'+uuid4().hex) as cur:
        cur.execute(query)
        for row in cur:digest.update(row[0].encode());count+=1
    return {'count':count,'sha256':digest.hexdigest()}
assert shutil.disk_usage('/var/lib/postgresql').free>8*1024**3
name='finna_vocab_rehearsal_'+uuid4().hex[:12];created=False
admin=psycopg.connect('dbname=postgres',autocommit=True)
try:
    with tempfile.TemporaryDirectory(prefix='finna-vocab-private-') as directory:
        dump=Path(directory)/'production.dump'
        with dump.open('wb') as output:subprocess.run(['pg_dump','-Fc','-Z1','--no-owner','mpsc'],stdout=output,check=True,timeout=600)
        admin.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(name)));created=True
        subprocess.run(['pg_restore','--exit-on-error','--no-owner','-d',name,str(dump)],check=True,timeout=600)
        with psycopg.connect('dbname='+name) as conn:
            conn.execute('CREATE TEMP TABLE rehearsal_original_review_keys ON COMMIT PRESERVE ROWS AS SELECT user_id,item_type,item_id FROM review_items')
            definitions=conn.execute("SELECT table_name,array_agg(column_name::text ORDER BY ordinal_position) FROM information_schema.columns WHERE table_schema='public' AND table_name IN(SELECT tablename FROM pg_tables WHERE schemaname='public') GROUP BY table_name ORDER BY table_name").fetchall()
            before={t:fingerprint(conn,t,c) for t,c in definitions};conn.commit()
            started=time.perf_counter();conn.execute(MIGRATION);conn.commit();apply_ms=round((time.perf_counter()-started)*1000,3)
            assert before=={t:fingerprint(conn,t,c) for t,c in definitions};conn.commit()
            added=conn.execute("SELECT count(*) FROM vocab_cards").fetchone()[0];conn.commit()
            code=Path(directory)/'candidate';code.mkdir()
            shutil.copytree('/srv/api/app',code/'app',ignore=shutil.ignore_patterns('__pycache__'))
            shutil.copytree('/srv/api/migrations',code/'migrations')
            (code/'migrations/0106_curated_vocabulary.sql').write_text(MIGRATION)
            preimages={}
            for relative,source in SOURCES.items():
                live=Path('/srv/api')/relative;preimages[relative]=hashlib.sha256(live.read_bytes()).hexdigest() if live.is_file() else None
                target=code/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(source)
            os.chdir('/');sys.path.insert(0,str(code))
            from app import db
            from app.services import review_queue,today,vocabulary_scheduler,vocabulary_decks,owned_calendar,reward_economy,curated_practice,curated_sessions
            from app.routers.vocabulary import capture,learning_hash
            async def verify():
                db._pool=AsyncConnectionPool('dbname='+name,min_size=1,max_size=2,kwargs={'row_factory':dict_row,'options':'-c role=mpsc -c jit=off -c statement_timeout=20000'},open=False)
                await db._pool.open(wait=True)
                try:
                    async with db.cursor() as cur:
                        await cur.execute('SELECT current_user');assert (await cur.fetchone())['current_user']=='mpsc'
                        await cur.execute('SELECT id FROM users WHERE email IS NOT NULL ORDER BY id');users=[r['id'] for r in await cur.fetchall()]
                        await cur.execute('SELECT count(*) AS n FROM reward_ledger');ledger_before=(await cur.fetchone())['n']
                    checks=0;durations=[]
                    for user in users:
                        started=time.perf_counter()
                        async with db.cursor() as cur:
                            await cur.execute('SET TRANSACTION READ ONLY')
                            queue=await review_queue.queue(cur,user);checks+=1
                            assert len({r['item_id'] for r in queue['items']})==len(queue['items'])
                            plan=await today.compose(cur,user);assert plan['due_count']==queue['due_count'] and plan['vocabulary']['target']==5;checks+=1
                            overview=await vocabulary_scheduler.overview(cur,user,'all');assert overview['due']+queue['curated_due_count']==queue['vocabulary_due_count'];checks+=1
                            catalog=await vocabulary_decks.catalog(cur,user,'all');assert all(x['attempted']<=x['eligible'] for x in catalog['items']);checks+=1
                            await cur.execute("SELECT (now() AT TIME ZONE 'Asia/Kolkata')::date AS day");day=(await cur.fetchone())['day']
                            from datetime import timedelta
                            await owned_calendar.learning_layers(cur,user,day,day+timedelta(days=40));checks+=1
                        durations.append(round((time.perf_counter()-started)*1000,3))
                    # A synthetic probe exists only in this private clone and is
                    # fully rolled back. No server workers or auth overrides run.
                    async with db.cursor() as cur:
                        async with cur.connection.transaction():
                            uid='vocab_probe_'+uuid4().hex
                            await cur.execute('INSERT INTO users(id,handle,email) VALUES(%s,%s,%s)',(uid,uid,uid+'@example.invalid'))
                            mid='synthetic_private_clone_'+uuid4().hex
                            await cur.execute("SELECT id FROM collections WHERE kind='exam' AND visibility='public' ORDER BY id LIMIT 1");exam=(await cur.fetchone())['id']
                            await cur.execute("SELECT id FROM review_taxonomy WHERE level='subject' AND active ORDER BY id LIMIT 1");subject=(await cur.fetchone())['id']
                            card={'language':'mizo-english','word':'synthetic','meaning':'Disposable test fixture','usage':'Only a synthetic fixture.','mizo_gloss':'Not a real language claim','source_note':'Private clone only; rolled back.','recognition_options':['Disposable test fixture','Other meaning'],'cloze_sentence':'Use {{word}} here.','cloze_options':['synthetic','other'],'mizo_options':['Not a real language claim','Other gloss']}
                            doc={'title':'Private clone synthetic reviewed deck','summary':'Disposable database integration probe only.','kind':'vocabulary-deck','access':'free','collection_id':exam,'subject_id':subject,'blocks':[{'id':'word','type':'vocabulary','vocabulary':card}]}
                            await cur.execute("INSERT INTO materials(id,author_id,title,blocks) VALUES(%s,%s,%s,%s)",(mid,uid,doc['title'],Jsonb(doc['blocks'])))
                            await cur.execute('INSERT INTO material_revisions(material_id,revision,payload,created_by) VALUES(%s,1,%s,%s)',(mid,Jsonb(doc),uid))
                            await cur.execute("UPDATE materials SET status='published',workflow_state='published',published_revision=1 WHERE id=%s",(mid,))
                            shown=(await curated_practice.next_card(cur,uid,mid,'english-to-mizo'))['card'];assert shown
                            result=await curated_practice.grade(cur,uid,shown['id'],'answer',0);assert result['correct'] and result['points']==result['xp']==0
                            assert await curated_practice.grade(cur,uid,shown['id'],'answer',0)==result
                            await cur.execute('SELECT count(*) AS n FROM attempts WHERE user_id=%s',(uid,));assert (await cur.fetchone())['n']==0
                            await cur.execute('SELECT count(*) AS n FROM reward_ledger WHERE user_id=%s',(uid,));assert (await cur.fetchone())['n']==0
                            await cur.execute("UPDATE review_items SET due_on=(now() AT TIME ZONE 'Asia/Kolkata')::date WHERE user_id=%s",(uid,))
                            queue=await review_queue.queue(cur,uid);assert queue['curated_due_count']==1
                            sid=uuid4().hex;cid=shown['card_id']
                            await cur.execute("INSERT INTO practice_study_sessions(id,user_id,kind,collection_id,request_key,request_hash,requested_size,question_ids,paper_ids,filters) VALUES(%s,%s,'review',NULL,%s,%s,10,%s,%s,%s) RETURNING *",(sid,uid,uuid4().hex,'synthetic', [cid],[None],Jsonb({'has_curated':True})))
                            saved=await cur.fetchone();await curated_sessions.freeze(cur,uid,sid,queue['items'][0],True)
                            assert await curated_sessions.check(cur,saved,cid,0)
                            assert cid in await curated_sessions.receipts(cur,saved)
                            await cur.execute('UPDATE practice_study_sessions SET finished_at=clock_timestamp() WHERE id=%s RETURNING *',(sid,));saved=await cur.fetchone()
                            frozen_checks=await curated_sessions.finish_checks(cur,saved);assert len(frozen_checks)==1 and frozen_checks[0]['was_due']
                            diagnostics=await reward_economy.diagnostics(cur);assert all(diagnostics[k]==0 for k in reward_economy.INTEGRITY_FIELDS)
                            raise psycopg.Rollback()
                    async with db.cursor() as cur:
                        await cur.execute('SET TRANSACTION READ ONLY')
                        await cur.execute('SELECT count(*) AS n FROM reward_ledger');ledger_after=(await cur.fetchone())['n']
                        diagnostics=await reward_economy.diagnostics(cur)
                    integrity={k:diagnostics[k] for k in reward_economy.INTEGRITY_FIELDS}
                    assert ledger_before==ledger_after and all(v==0 for v in integrity.values()) and reward_economy.reconciled_release()
                    return {'account_users_checked':len(users),'private_read_checks':checks,'read_batch_ms':durations,'database_role':'mpsc','read_transactions_read_only':True,'synthetic_write_probe_rolled_back':True,'ledger_before':ledger_before,'ledger_after':ledger_after,'integrity':integrity,'economy_reconciled':True,'workers_started':False}
                finally:await db._pool.close()
            verification=asyncio.run(verify())
            assert before=={t:fingerprint(conn,t,c) for t,c in definitions};conn.commit()
            for relative,digest in preimages.items():
                live=Path('/srv/api')/relative;assert (hashlib.sha256(live.read_bytes()).hexdigest() if live.is_file() else None)==digest
            report={'existing_tables_checked':len(before),'before':before,'all_existing_rows_identical':True,'reviewed_cards_projected':added,'migration_apply_ms':apply_ms,'migration_sha256':hashlib.sha256(MIGRATION.encode()).hexdigest(),'verification':verification,'candidate_sha256':{n:hashlib.sha256(s.encode()).hexdigest() for n,s in SOURCES.items()},'live_preimages':preimages}
finally:
    if created:admin.execute(sql.SQL('DROP DATABASE {} WITH (FORCE)').format(sql.Identifier(name)))
    admin.close()
health={}
for host in ('study.hawayu.in','family.hawayu.in'):
    with urlopen('https://'+host,timeout=30) as response:assert response.status==200;health[host]=response.status
print(json.dumps(report|{'clone_and_dump_removed':True,'both_site_health':health}))
'''
if __name__=='__main__':
    result=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','ubuntu@152.67.31.231','sudo -u postgres /srv/api/.venv/bin/python -'],input=('SOURCES='+repr(SOURCES)+'\nMIGRATION='+repr(MIGRATION)+'\n'+REMOTE).encode(),capture_output=True,timeout=1200)
    if result.returncode:raise SystemExit(result.stderr.decode(errors='replace')[-4000:])
    report=json.loads(result.stdout);(REPORT/'migration-rehearsal.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('existing_tables_checked','all_existing_rows_identical','reviewed_cards_projected','migration_apply_ms','verification','clone_and_dump_removed','both_site_health')},indent=2))
