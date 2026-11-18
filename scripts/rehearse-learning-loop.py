#!/usr/bin/env python3
"""Rehearse draft 0092 on a fresh disposable production-dump clone.

The dump and disposable clone stay on Oracle, avoiding a large network copy.
No background workers, synthetic study activity or production mutations run.
One deterministic worker cycle runs only on the disposable clone. The
private dump and clone are removed in finally; both sites are checked afterward.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import shutil
import tempfile
import time
import sys
from urllib.request import urlopen
from uuid import uuid4
import psycopg
from psycopg import sql

ROOT=Path(__file__).resolve().parents[1]
MIGRATION=ROOT/'api/migrations/0092_learning_loop.sql'


def fingerprint(conn,table,columns):
    fields=sql.SQL(',').join(map(sql.Identifier,columns))
    query=sql.SQL('SELECT md5(ROW({})::text) AS h FROM {} ORDER BY h').format(fields,sql.Identifier(table))
    digest=hashlib.sha256();count=0
    with conn.cursor(name='fingerprint_'+uuid4().hex) as cur:
        cur.execute(query)
        for row in cur:
            digest.update(row[0].encode());count+=1
    return {'count':count,'sha256':digest.hexdigest()}


def remote(migration_text,prerequisites,api_sources,verifier_text):
    assert shutil.disk_usage('/var/lib/postgresql').free>8*1024**3,'Insufficient rehearsal disk headroom'
    migration_bytes=migration_text.encode()
    name='finna_learning_rehearsal_'+uuid4().hex[:12]
    admin=psycopg.connect('dbname=postgres',autocommit=True)
    created=False
    try:
        with tempfile.TemporaryDirectory(prefix='finna-learning-private-') as directory:
            dump=Path(directory)/'production.dump'
            with dump.open('wb') as output:
                subprocess.run(['pg_dump','-Fc','-Z1','--no-owner','mpsc'],stdout=output,check=True,timeout=600)
            admin.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(name)));created=True
            subprocess.run(['pg_restore','--exit-on-error','--no-owner','-d',name,str(dump)],check=True,timeout=600)
            with psycopg.connect('dbname='+name) as conn:
                definitions=conn.execute("SELECT table_name,array_agg(column_name::text ORDER BY ordinal_position) FROM information_schema.columns WHERE table_schema='public' AND table_name IN (SELECT tablename FROM pg_tables WHERE schemaname='public') GROUP BY table_name ORDER BY table_name").fetchall()
                before={table:fingerprint(conn,table,columns) for table,columns in definitions}
                conn.commit()
                dependency_results=[]
                for filename,source in prerequisites:
                    checksum=hashlib.sha256(source.encode()).hexdigest()
                    prior=conn.execute('SELECT checksum FROM schema_migrations WHERE version=%s',(filename.removesuffix('.sql'),)).fetchone()
                    if prior:
                        assert prior[0][:16]==checksum[:16],'Prerequisite checksum differs: '+filename
                        dependency_results.append({'file':filename,'already_applied':True,'sha256':checksum})
                    else:
                        started=time.perf_counter();conn.execute(source);conn.commit()
                        dependency_results.append({'file':filename,'already_applied':False,'sha256':checksum,'apply_ms':round((time.perf_counter()-started)*1000,3)})
                started=time.perf_counter();conn.execute(migration_bytes.decode());conn.commit()
                elapsed=round((time.perf_counter()-started)*1000,3)
                after={table:fingerprint(conn,table,columns) for table,columns in definitions}
                assert before==after,'Existing data changed'
                account_users=conn.execute('SELECT count(DISTINCT a.user_id) FROM attempts a JOIN users u ON u.id=a.user_id WHERE u.email IS NOT NULL').fetchone()[0]
                jobs=conn.execute('SELECT count(*) FROM learning_rollup_jobs').fetchone()[0]
                assert account_users==jobs
                assert conn.execute('SELECT count(*) FROM user_topic_mastery').fetchone()[0]==0
                assert conn.execute('SELECT count(*) FROM review_items').fetchone()[0]==0
                conn.execute('SET LOCAL ROLE mpsc')
                for table in ('user_topic_mastery','review_items','user_focus_subjects','worker_heartbeats','learning_rollup_jobs','question_classifications','mock_session_questions','user_activity_daily','user_activity_questions','auth_login_backoff'):
                    conn.execute(sql.SQL('SELECT 1 FROM {} LIMIT 1').format(sql.Identifier(table)))
                # Rehearse the exact candidate worker against the real restored
                # ACLs, then run read-only routes. The live app never sees this DB.
                code=Path(directory)/'candidate';code.mkdir()
                shutil.copytree('/srv/api/app',code/'app',ignore=shutil.ignore_patterns('__pycache__','data'))
                (code/'app/data').symlink_to('/srv/api/app/data',target_is_directory=True)
                for relative,source in api_sources.items():
                    target=code/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(source)
                os.chdir(code)
                sys.path.insert(0,str(code))
                import asyncio
                from psycopg.rows import dict_row
                from psycopg_pool import AsyncConnectionPool
                from app import db
                from app.services.learning_rollups import cycle
                async def seed():
                    db._pool=AsyncConnectionPool('dbname='+name,min_size=1,max_size=3,
                      kwargs={'row_factory':dict_row,'options':'-c role=mpsc -c jit=off'},open=False)
                    await db._pool.open(wait=True)
                    try:
                        async with db.cursor() as cur:await cycle(cur)
                    finally:await db._pool.close()
                asyncio.run(seed())
                conn.commit()
                assert conn.execute('SELECT count(*) FROM learning_rollup_jobs WHERE processed_version<requested_version OR failures>0').fetchone()[0]==0
                verifier={"__name__":"clone_verifier"}
                exec(compile(verifier_text.replace("sys.path.insert(0,'/srv/api')","sys.path.insert(0,"+repr(str(code))+")"),'clone_verifier','exec'),verifier)
                readback=asyncio.run(verifier['verify'](name))
                after_worker={table:fingerprint(conn,table,columns) for table,columns in definitions}
                assert before==after_worker,'Seed changed pre-existing columns/rows, including ledger'
                seed_counts={table:conn.execute(sql.SQL('SELECT count(*) FROM {}').format(sql.Identifier(table))).fetchone()[0]
                  for table in ('user_topic_mastery','review_items')}
                report={'migration':'0092_learning_loop.sql','sha256':hashlib.sha256(migration_bytes).hexdigest(),
                  'prerequisites':dependency_results,
                  'apply_ms':elapsed,'existing_tables_checked':len(before),'all_existing_columns_and_rows_preserved':True,
                  'account_jobs_enqueued':jobs,'account_users_with_attempts':account_users,'mastery_rows':0,'review_rows':0,
                  'application_role_reads':True,'workers_started':False,'production_mutations':False,
                  'clone_worker_seed':seed_counts,'read_only_flow':readback,'seed_preserves_all_existing_rows':True,'cloned_acls_preserved':True}
    finally:
        if created:
            admin.execute(sql.SQL('DROP DATABASE {} WITH (FORCE)').format(sql.Identifier(name)))
        admin.close()
    health={}
    for host in ('study.hawayu.in','family.hawayu.in'):
        with urlopen('https://'+host,timeout=30) as response:
            health[host]=response.status
            assert response.status==200
    return report | {'both_site_health':health,'clone_and_dump_removed':True,'location':'Oracle disposable database; no app points at it'}


def main():
    # Feed exact Python source and draft migration through stdin. No shell
    # interpolation, credentials, persisted remote helper or public staging path.
    source=Path(__file__).read_text().rsplit('\nif __name__==',1)[0]
    dependencies=[('0083_daily_five.sql',(ROOT/'api/migrations/0083_daily_five.sql').read_text())]
    candidate=['app/main.py','app/routers/account_recovery.py','app/routers/auth.py','app/routers/games.py','app/routers/me.py','app/routers/mobile.py','app/routers/questions.py','app/routers/study_sessions.py','app/services/game_selection.py','app/services/games.py','app/services/mobile_identity.py','app/services/scoring_revisions.py','app/routers/learning_loop.py','app/services/activity_progress.py','app/services/learning_rollups.py','app/services/login_backoff.py','app/services/mastery.py','app/services/review_queue.py','app/services/today.py']
    api_sources={name:(ROOT/'api'/name).read_text() for name in candidate}
    verifier=(ROOT/'scripts/verify-learning-loop.py').read_text()
    code=source+'\nprint(json.dumps(remote('+repr(MIGRATION.read_text())+','+repr(dependencies)+','+repr(api_sources)+','+repr(verifier)+')))\n'
    try:
        result=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','ubuntu@152.67.31.231',
          'sudo -u postgres /srv/api/.venv/bin/python -'],input=code.encode(),capture_output=True,check=True,timeout=1200)
    except subprocess.CalledProcessError as error:
        print(error.stderr.decode(errors='replace')[-3000:],file=sys.stderr)
        raise
    report=json.loads(result.stdout)
    target=ROOT/'reports/finnaplan-v2-today-20261117'
    target.mkdir(parents=True,exist_ok=True)
    (target/'migration-rehearsal.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
