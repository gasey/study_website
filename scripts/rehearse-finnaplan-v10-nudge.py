#!/usr/bin/env python3
"""Rehearse study-note schema/readers on a fresh private production-dump clone."""
import json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/'reports/finnaplan-v10-nudge-20261117'
FILES=('app/routers/discussions.py',)
SOURCES={name:(ROOT/'api'/name).read_text() for name in FILES}
MIGRATION=(ROOT/'api/migrations/0103_acceptance_nudge.sql').read_text()
REMOTE=r'''
import asyncio,hashlib,json,os,shutil,subprocess,sys,tempfile,time
from pathlib import Path
from uuid import uuid4
from urllib.request import urlopen
import psycopg
from psycopg import sql
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

def fingerprint(conn,table,columns):
    fields=sql.SQL(',').join(map(sql.Identifier,columns))
    query=sql.SQL('SELECT md5(ROW({})::text) AS h FROM {} ORDER BY h').format(fields,sql.Identifier(table))
    digest=hashlib.sha256();count=0
    with conn.cursor(name='study_fp_'+uuid4().hex) as cur:
        cur.execute(query)
        for row in cur:digest.update(row[0].encode());count+=1
    return {'count':count,'sha256':digest.hexdigest()}

assert shutil.disk_usage('/var/lib/postgresql').free>8*1024**3
name='finna_study_rehearsal_'+uuid4().hex[:12]
admin=psycopg.connect('dbname=postgres',autocommit=True);created=False
try:
    with tempfile.TemporaryDirectory(prefix='finna-study-private-') as directory:
        dump=Path(directory)/'production.dump'
        with dump.open('wb') as output:subprocess.run(['pg_dump','-Fc','-Z1','--no-owner','mpsc'],stdout=output,check=True,timeout=600)
        admin.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(name)));created=True
        subprocess.run(['pg_restore','--exit-on-error','--no-owner','-d',name,str(dump)],check=True,timeout=600)
        with psycopg.connect('dbname='+name) as conn:
            definitions=conn.execute("SELECT table_name,array_agg(column_name::text ORDER BY ordinal_position) FROM information_schema.columns WHERE table_schema='public' AND table_name IN (SELECT tablename FROM pg_tables WHERE schemaname='public') GROUP BY table_name ORDER BY table_name").fetchall()
            before={t:fingerprint(conn,t,c) for t,c in definitions};conn.commit()
            started=time.perf_counter();conn.execute(MIGRATION);conn.commit();apply_ms=round((time.perf_counter()-started)*1000,3)
            assert before=={t:fingerprint(conn,t,c) for t,c in definitions};conn.commit()
            user=conn.execute('SELECT id FROM users WHERE email IS NOT NULL ORDER BY id LIMIT 1').fetchone()[0];conn.commit()
            # Exercise the unique claim index under the real app role, rolled back.
            with conn.transaction():
                conn.execute('SET LOCAL ROLE mpsc')
                qid=conn.execute('SELECT id FROM canonical_questions LIMIT 1').fetchone()[0]
                pid=conn.execute("INSERT INTO posts(canonical_id,kind,author_id,body) VALUES(%s,'doubt',%s,'Synthetic rolled-back acceptance reminder probe') RETURNING id",(qid,user)).fetchone()[0]
                claim="INSERT INTO discussion_events(canonical_id,post_id,actor_id,action) VALUES(%s,%s,%s,'acceptance_nudged') ON CONFLICT(post_id) WHERE action='acceptance_nudged' DO NOTHING RETURNING id"
                assert conn.execute(claim,(qid,pid,user)).fetchone()
                assert conn.execute(claim,(qid,pid,user)).fetchone() is None
                raise psycopg.Rollback()
            code=Path(directory)/'candidate';code.mkdir()
            shutil.copytree('/srv/api/app',code/'app',ignore=shutil.ignore_patterns('data','__pycache__'))
            (code/'app/data').symlink_to('/srv/api/app/data',target_is_directory=True)
            (code/'migrations').symlink_to('/srv/api/migrations',target_is_directory=True)
            preimages={}
            for relative,source in SOURCES.items():
                live=Path('/srv/api')/relative
                preimages[relative]=hashlib.sha256(live.read_bytes()).hexdigest() if live.is_file() else None
                target=code/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(source)
            os.chdir('/');sys.path.insert(0,str(code))
            from app import db
            from app.routers import community,study_posts,discussions
            from app.services import community_policy,reward_economy
            from fastapi import Response
            async def verify():
                db._pool=AsyncConnectionPool('dbname='+name,min_size=1,max_size=2,
                  kwargs={'row_factory':dict_row,'options':'-c role=mpsc -c default_transaction_read_only=on -c jit=off'},open=False)
                await db._pool.open(wait=True)
                try:
                    async with db.cursor() as cur:
                        await cur.execute("SELECT current_user,current_setting('transaction_read_only') AS readonly")
                        assert await cur.fetchone()=={'current_user':'mpsc','readonly':'on'}
                        await cur.execute('SELECT id FROM users WHERE email IS NOT NULL ORDER BY id');users=[r['id'] for r in await cur.fetchall()]
                        await cur.execute('SELECT count(*) AS n FROM reward_ledger');ledger_before=(await cur.fetchone())['n']
                    checks=0;durations=[]
                    for user in users:
                        started=time.perf_counter()
                        state=await study_posts.status(user);assert state['registered'] and state['post_limit'] in (5,10);checks+=1
                        async with db.cursor() as cur:
                            assert not await discussions.acceptance_nudge_eligible(cur,-1,user);checks+=1
                        for version in (1,2):
                            for tab in ('for-you','following','questions'):
                                response=Response();result=await community.community_feed(user,response,tab=tab,discussion='all',shelf_id=None,limit=20,offset=0,content_version=version)
                                assert result.available and response.headers['cache-control']=='private, no-store'
                                if version==1 or tab=='questions':assert all(p.kind not in {'study','material-share'} for p in result.items)
                                checks+=1
                        durations.append(round((time.perf_counter()-started)*1000,3))
                    async with db.cursor() as cur:
                        await cur.execute('SELECT count(*) AS n FROM reward_ledger');ledger_after=(await cur.fetchone())['n']
                        diagnostics=await reward_economy.diagnostics(cur)
                    assert ledger_before==ledger_after
                    integrity={k:diagnostics[k] for k in reward_economy.INTEGRITY_FIELDS};assert all(v==0 for v in integrity.values())
                    assert reward_economy.reconciled_release()
                    return {'account_users_checked':len(users),'private_read_checks':checks,'read_batch_ms':durations,
                      'database_role':'mpsc','transactions_read_only':True,'ledger_before':ledger_before,'ledger_after':ledger_after,
                      'integrity':integrity,'economy_reconciled':True,'workers_started':False}
                finally:await db._pool.close()
            verification=asyncio.run(verify())
            assert before=={t:fingerprint(conn,t,c) for t,c in definitions}

            for relative,digest in preimages.items():
                live=Path('/srv/api')/relative
                assert (hashlib.sha256(live.read_bytes()).hexdigest() if live.is_file() else None)==digest
            report={'existing_tables_checked':len(before),'before':before,'after_identical':True,'migration_apply_ms':apply_ms,
              'migration_sha256':hashlib.sha256(MIGRATION.encode()).hexdigest(),'verification':verification,
              'candidate_sha256':{n:hashlib.sha256(s.encode()).hexdigest() for n,s in SOURCES.items()},'live_preimages':preimages}
finally:
    if created:admin.execute(sql.SQL('DROP DATABASE {} WITH (FORCE)').format(sql.Identifier(name)))
    admin.close()
health={}
for host in ('study.hawayu.in','family.hawayu.in'):
    with urlopen('https://'+host,timeout=30) as response:assert response.status==200;health[host]=response.status
print(json.dumps(report|{'clone_and_dump_removed':True,'both_site_health':health}))
'''
if __name__=='__main__':
    result=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','ubuntu@152.67.31.231','sudo -u postgres /srv/api/.venv/bin/python -'],
        input=('SOURCES='+repr(SOURCES)+'\nMIGRATION='+repr(MIGRATION)+'\n'+REMOTE).encode(),capture_output=True,timeout=1200)
    if result.returncode:raise SystemExit(result.stderr.decode(errors='replace')[-4000:])
    report=json.loads(result.stdout);(REPORT/'migration-rehearsal.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('existing_tables_checked','after_identical','migration_apply_ms','verification','clone_and_dump_removed','both_site_health')},indent=2))
