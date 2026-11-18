#!/usr/bin/env python3
"""Read-only V.5 candidate queries against Oracle ACLs; no live code install."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FILES=('app/routers/rewards.py','app/routers/games.py','app/routers/mobile.py','app/services/today.py',
       'app/services/weekly_boards.py','app/services/weekly_recap.py')
SOURCES={name:(ROOT/'api'/name).read_text() for name in FILES}
REMOTE='''
import asyncio,hashlib,json,os,shutil,sys,tempfile,time
from pathlib import Path
with tempfile.TemporaryDirectory(prefix='finna-weekly-readonly-') as directory:
    code=Path(directory)
    shutil.copytree('/srv/api/app',code/'app',ignore=shutil.ignore_patterns('data','__pycache__'))
    (code/'app/data').symlink_to('/srv/api/app/data',target_is_directory=True)
    for name,source in SOURCES.items():(code/name).write_text(source)
    os.chdir('/')
    sys.path.insert(0,str(code))
    from psycopg.rows import dict_row
    from psycopg_pool import AsyncConnectionPool
    from app import db
    from app.services import weekly_boards,weekly_recap
    async def check():
        db._pool=AsyncConnectionPool('dbname=mpsc',min_size=1,max_size=2,
          kwargs={'row_factory':dict_row,'options':'-c role=mpsc -c default_transaction_read_only=on -c jit=off'},open=False)
        await db._pool.open(wait=True)
        try:
            async with db.cursor() as cur:
                await cur.execute("SELECT current_user,current_setting('transaction_read_only') AS readonly")
                assert await cur.fetchone()=={'current_user':'mpsc','readonly':'on'}
                await cur.execute('SELECT DISTINCT u.id FROM users u JOIN attempts a ON a.user_id=u.id WHERE u.email IS NOT NULL ORDER BY u.id')
                users=[r['id'] for r in await cur.fetchall()]
                await cur.execute('SELECT count(*) AS n FROM reward_ledger');before=(await cur.fetchone())['n']
                checks=[]
                for user in users:
                    for mode in ('xp','gauntlet','speed','duel','daily'):
                        started=time.perf_counter()
                        result=await weekly_boards.xp(cur,user) if mode=='xp' else await weekly_boards.games(cur,user,mode)
                        elapsed=round((time.perf_counter()-started)*1000,3)
                        assert len(result['items'])<=35 and len(result['top'])<=10 and len(result['nearby'])<=25
                        fields={'handle','rank','xp' if mode=='xp' else 'score'}
                        assert all(set(r)==fields for r in result['items'])
                        checks.append({'mode':mode,'ms':elapsed,'public_rows':len(result['items'])})
                    assert await weekly_recap.compose(cur,user) is None # Current actual IST Tuesday.
                await cur.execute('SELECT count(*) AS n FROM reward_ledger');after=(await cur.fetchone())['n']
                return {'account_users_checked':len(users),'board_queries':checks,'monday_only_verified_on_actual_tuesday':True,
                  'database_role':'mpsc','transactions_read_only':True,'workers_started':False,'live_auth_overrides':False,
                  'ledger_rows_before':before,'ledger_rows_after':after}
        finally:await db._pool.close()
    report=asyncio.run(check())
print(json.dumps(report|{'private_candidate_removed':True,'live_code_installed':False,
 'candidate_sha256':{n:hashlib.sha256(s.encode()).hexdigest() for n,s in SOURCES.items()}}))
'''
result=subprocess.run(['ssh','-o','BatchMode=yes','ubuntu@152.67.31.231','sudo -u postgres /srv/api/.venv/bin/python -'],
 input=('SOURCES='+repr(SOURCES)+'\n'+REMOTE).encode(),capture_output=True,check=True,timeout=180)
report=json.loads(result.stdout)
target=ROOT/'reports/finnaplan-v5-boards-20261117/read-only-rehearsal.json'
target.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
