#!/usr/bin/env python3
"""Rehearse V.5 account self-service draft0097; no production install."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FILES=('app/routers/calendar.py', 'app/routers/calendar_owned.py', 'app/routers/learning_loop.py', 'app/services/owned_calendar.py', 'app/routers/rewards.py', 'app/routers/me.py', 'app/routers/profile_identity.py', 'app/routers/avatars.py', 'app/routers/creators.py', 'app/routers/search.py', 'app/services/profile_identity.py', 'app/services/avatars.py', 'app/services/cosmetic_shop.py', 'app/data/avatar_catalog.json')
FILES+=('app/services/today.py','app/services/learning_habit.py','app/services/weekly_boards.py','app/services/weekly_recap.py','app/services/calendar_schedule.py','app/routers/games.py')
FILES+=('app/routers/account_tools.py','app/services/account_tools.py','app/routers/auth.py')
SOURCES={name:(ROOT/'api'/name).read_text() for name in FILES}
MIGRATION=(ROOT/'api/migrations/0097_owned_calendar.sql').read_text()
REMOTE=r'''
import asyncio,hashlib,json,os,shutil,subprocess,sys,tempfile,time
from datetime import timedelta
from pathlib import Path
from urllib.request import urlopen
from uuid import uuid4
import psycopg
from psycopg import sql
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

def fingerprint(conn,table,columns):
    fields=sql.SQL(',').join(map(sql.Identifier,columns))
    query=sql.SQL('SELECT md5(ROW({})::text) AS h FROM {} ORDER BY h').format(fields,sql.Identifier(table))
    digest=hashlib.sha256();count=0
    with conn.cursor(name='calendar_fp_'+uuid4().hex) as cur:
        cur.execute(query)
        for row in cur:digest.update(row[0].encode());count+=1
    return {'count':count,'sha256':digest.hexdigest()}

assert shutil.disk_usage('/var/lib/postgresql').free>8*1024**3
name='finna_calendar_rehearsal_'+uuid4().hex[:12]
admin=psycopg.connect('dbname=postgres',autocommit=True);created=False
try:
    with tempfile.TemporaryDirectory(prefix='finna-calendar-private-') as directory:
        dump=Path(directory)/'production.dump'
        with dump.open('wb') as output:
            subprocess.run(['pg_dump','-Fc','-Z1','--no-owner','mpsc'],stdout=output,check=True,timeout=600)
        admin.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(name)));created=True
        subprocess.run(['pg_restore','--exit-on-error','--no-owner','-d',name,str(dump)],check=True,timeout=600)
        with psycopg.connect('dbname='+name) as conn:
            definitions=conn.execute("SELECT table_name,array_agg(column_name::text ORDER BY ordinal_position) FROM information_schema.columns WHERE table_schema='public' AND table_name IN (SELECT tablename FROM pg_tables WHERE schemaname='public') GROUP BY table_name ORDER BY table_name").fetchall()
            before={t:fingerprint(conn,t,c) for t,c in definitions};conn.commit()
            started=time.perf_counter();conn.execute(MIGRATION);conn.commit()
            apply_ms=round((time.perf_counter()-started)*1000,3)
            after={t:fingerprint(conn,t,c) for t,c in definitions};assert before==after;conn.commit()
            user=conn.execute('SELECT id FROM users WHERE email IS NOT NULL ORDER BY id LIMIT 1').fetchone()[0];conn.commit()
            # Verify grants without retaining any synthetic workflow record.
            with conn.transaction():
                conn.execute('SET LOCAL ROLE mpsc')
                eid=uuid4()
                conn.execute("INSERT INTO calendar_entries(id,user_id,date,title,kind) VALUES(%s,%s,'2026-11-17','Synthetic rolled-back permission probe','personal')",(eid,user))
                conn.execute('UPDATE calendar_entries SET version=version+1 WHERE id=%s',(eid,))
                conn.execute('DELETE FROM calendar_entries WHERE id=%s',(eid,))
                conn.execute("INSERT INTO calendar_feed_tokens(user_id,token_hash,version) VALUES(%s,%s,1)",(user,'a'*64))
                conn.execute('UPDATE calendar_feed_tokens SET token_hash=NULL,revoked_at=clock_timestamp(),version=2 WHERE user_id=%s',(user,))
                raise psycopg.Rollback()
            code=Path(directory)/'candidate';code.mkdir()
            shutil.copytree('/srv/api/app',code/'app',ignore=shutil.ignore_patterns('data','__pycache__'))
            (code/'app/data').mkdir()
            for child in Path('/srv/api/app/data').iterdir():
                if child.name!='avatar_catalog.json':(code/'app/data'/child.name).symlink_to(child,target_is_directory=child.is_dir())
            preimages={}
            for relative,source in SOURCES.items():
                live=Path('/srv/api')/relative
                preimages[relative]=hashlib.sha256(live.read_bytes()).hexdigest() if live.exists() else None
                (code/relative).write_text(source)
            os.chdir('/');sys.path.insert(0,str(code))
            from app import db
            from app.routers import learning_loop,calendar_owned
            from app.services import owned_calendar,profile_identity,avatars,cosmetic_shop,today,weekly_boards,account_tools
            from types import SimpleNamespace
            async def probes():
                db._pool=AsyncConnectionPool('dbname='+name,min_size=1,max_size=1,kwargs={'row_factory':dict_row,'options':'-c role=mpsc -c jit=off'},open=False)
                await db._pool.open(wait=True)
                try:
                    async with db.cursor() as cur:
                        identity=await profile_identity.read(cur,user)
                        edited=await profile_identity.save(cur,user,SimpleNamespace(expected_version=identity['identity_version'],name=identity['name'] or '',handle=identity['handle'],bio='Synthetic rolled-back rehearsal bio'))
                        assert edited['identity_version']==identity['identity_version']+1
                        await cur.execute("INSERT INTO reward_ledger(user_id,event_key,kind,points,note) VALUES(%s,%s,'adjustment',200,'Synthetic rolled-back wallet fixture')",(user,'rehearsal:'+uuid4().hex))
                        bought=await cosmetic_shop.purchase(cur,user,'top-plum',avatars.CATALOG_SHA256,25)
                        assert bought['points_spent']==25
                        again=await cosmetic_shop.purchase(cur,user,'top-plum',avatars.CATALOG_SHA256,25)
                        assert again['replayed'] and again['points_spent']==0
                        assert all(n==0 for n in (await cosmetic_shop.diagnostics(cur)).values())
                        await cur.connection.rollback()
                    async with db.cursor() as cur:
                        synthetic='close-rehearsal-'+uuid4().hex
                        await cur.execute("INSERT INTO users(id,handle,email,plan_code,plan_status) VALUES(%s,%s,%s,'pro','active')",(synthetic,synthetic,synthetic+'@example.test'))
                        await cur.execute("INSERT INTO calendar_entries(id,user_id,date,title,kind) VALUES(%s,%s,'2026-11-17','Synthetic closure plan','personal')",(uuid4(),synthetic))
                        assert await account_tools.close(cur,synthetic,0)=={'closed':True}
                        await cur.execute('SELECT email,closed_at,account_has_pro(id) AS pro FROM users WHERE id=%s',(synthetic,))
                        ended=await cur.fetchone();assert ended['email'] is None and ended['closed_at'] and not ended['pro']
                        await cur.execute('SELECT count(*) AS n FROM calendar_entries WHERE user_id=%s',(synthetic,))
                        assert (await cur.fetchone())['n']==0
                        await cur.connection.rollback()
                finally:await db._pool.close()
            asyncio.run(probes())
            async def verify():
                db._pool=AsyncConnectionPool('dbname='+name,min_size=1,max_size=2,
                  kwargs={'row_factory':dict_row,'options':'-c role=mpsc -c default_transaction_read_only=on -c jit=off'},open=False)
                await db._pool.open(wait=True)
                try:
                    async with db.cursor() as cur:
                        await cur.execute("SELECT current_user,current_setting('transaction_read_only') AS readonly")
                        assert await cur.fetchone()=={'current_user':'mpsc','readonly':'on'}
                        await cur.execute('SELECT DISTINCT u.id FROM users u JOIN attempts a ON a.user_id=u.id WHERE u.email IS NOT NULL ORDER BY u.id')
                        users=[r['id'] for r in await cur.fetchall()]
                        await cur.execute('SELECT count(*) AS n FROM reward_ledger');ledger_before=(await cur.fetchone())['n']
                    checks=[];day=owned_calendar.india_today()
                    for user in users:
                        start=time.perf_counter()
                        result=await learning_loop.calendar_layers(day,day+timedelta(days=30),user)
                        assert result['registered'] and result['entries']==[] and result['occurrences']==[]
                        async with db.cursor() as cur:
                            identity=await profile_identity.read(cur,user)
                            avatar=await avatars.account(cur,user)
                            inventory=await avatars.inventory(cur,avatar)
                            assert len(inventory)==29 and len([i for i in inventory if i.get('price_points')])==3
                            assert identity['user_id']==user
                        async with db.cursor() as cur:
                            exported=json.loads(''.join([part async for part in account_tools.export(cur,user)]))
                            assert exported['account']['id']==user
                            assert 'password_hash' not in exported['account']
                            assert all('scoring_snapshot' not in r for r in exported['attempts'])
                            plan=await today.compose(cur,user)
                            assert plan['account'] and not plan['plan_status']['started']
                            board=await weekly_boards.xp(cur,user)
                            assert board['period']=='week' and len(board['items'])<=35
                            assert all(set(r)=={'handle','xp','rank'} for r in board['items'])
                            assert all(r['kind']=='cup' for r in result['community'])
                            assert all(n==0 for n in (await cosmetic_shop.diagnostics(cur)).values())
                        assert await calendar_owned.status(user)=={'version':0,'active':False,'created_at':None,'revoked_at':None}
                        async with db.cursor() as cur:content=await owned_calendar.subscription(cur,user)
                        assert content.startswith('BEGIN:VCALENDAR'+chr(13)+chr(10))
                        assert 'ATTENDEE:' not in content and 'ORGANIZER:' not in content
                        checks.append({'ms':round((time.perf_counter()-start)*1000,3),'export_bytes':len(content.encode())})
                    async with db.cursor() as cur:
                        await cur.execute('SELECT count(*) AS n FROM reward_ledger');ledger_after=(await cur.fetchone())['n']
                    return {'account_users_checked':len(users),'reads':checks,'database_role':'mpsc','transactions_read_only':True,
                      'ledger_rows_before':ledger_before,'ledger_rows_after':ledger_after,'live_auth_overrides':False,'workers_started':False}
                finally:await db._pool.close()
            verification=asyncio.run(verify())
            assert before=={t:fingerprint(conn,t,c) for t,c in definitions}
            for table in ('calendar_entries','calendar_feed_tokens'):
                assert conn.execute(sql.SQL('SELECT count(*) FROM {}').format(sql.Identifier(table))).fetchone()[0]==0
            for relative,digest in preimages.items():
                live=Path('/srv/api')/relative
                assert (hashlib.sha256(live.read_bytes()).hexdigest() if live.exists() else None)==digest
            report={'migration':'0097_owned_calendar.sql','migration_sha256':hashlib.sha256(MIGRATION.encode()).hexdigest(),
              'apply_ms':apply_ms,'existing_tables_checked':len(before),'all_existing_columns_and_rows_preserved':True,
              'application_role_crud_and_token_grants':True,'identity_and_shop_probes_rolled_back':True,'synthetic_closure_probe_rolled_back':True,'owned_export_read_only':True,'permission_probes_rolled_back':True,'new_calendar_rows':0,
              'read_only_flow':verification,'production_mutations':False,'live_code_installed':False,
              'candidate_sha256':{n:hashlib.sha256(s.encode()).hexdigest() for n,s in SOURCES.items()},'live_preimages':preimages}
finally:
    if created:admin.execute(sql.SQL('DROP DATABASE {} WITH (FORCE)').format(sql.Identifier(name)))
    admin.close()
health={}
for host in ('study.hawayu.in','family.hawayu.in'):
    with urlopen('https://'+host,timeout=30) as response:health[host]=response.status;assert response.status==200
print(json.dumps(report|{'clone_and_dump_removed':True,'both_site_health':health}))
'''
if __name__=='__main__':
    result=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','ubuntu@152.67.31.231','sudo -u postgres /srv/api/.venv/bin/python -'],
      input=('SOURCES='+repr(SOURCES)+'\nMIGRATION='+repr(MIGRATION)+'\n'+REMOTE).encode(),capture_output=True,timeout=1200)
    if result.returncode:raise SystemExit(result.stderr.decode(errors='replace')[-4000:])
    report=json.loads(result.stdout)
    target=ROOT/'reports/finnaplan-v5-account-20261117/migration-rehearsal.json'
    target.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
