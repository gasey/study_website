#!/usr/bin/env python3
"""Real-role read-only deck checks, optionally against staged candidate modules."""
import asyncio,importlib.util,json,os,sys,time
os.chdir('/');sys.path.insert(0,'/srv/api')
if len(sys.argv)==3:
    for name,path in [('app.services.vocabulary_decks',sys.argv[1]),('app.routers.vocabulary',sys.argv[2])]:
        spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool
from fastapi import Response
from app import db
from app.routers.vocabulary import decks,overview
from app.services.review_identity import Actor
from app.services import vocabulary_decks,reward_economy
async def verify():
    db._pool=AsyncConnectionPool('dbname=mpsc',min_size=1,max_size=2,kwargs={'row_factory':dict_row,'options':'-c role=mpsc -c default_transaction_read_only=on -c jit=off -c statement_timeout=15000'},open=False)
    await db._pool.open(wait=True)
    try:
        async with db.cursor() as cur:
            await cur.execute("SELECT current_user,current_setting('transaction_read_only') AS readonly");assert await cur.fetchone()=={'current_user':'mpsc','readonly':'on'}
            await cur.execute('SELECT id FROM users WHERE email IS NOT NULL ORDER BY id');users=[r['id'] for r in await cur.fetchall()]
            await cur.execute('SELECT count(*) AS n FROM reward_ledger');before=(await cur.fetchone())['n']
        timings=[];checks=0;per_deck=0
        for user in users:
            for scope in ('all','mizoram-recruitment'):
                start=time.monotonic();actor=Actor(user,'',True);response=Response()
                result=await decks(actor,response,scope)
                assert response.headers['cache-control']=='private, no-store' and result['curated_available'] is False
                for item in result['items']:
                    assert 0<=item['correct_latest']<=item['attempted']<=item['eligible']
                    assert 0<=item['started']<=item['eligible'] and 0<=item['due']<=item['eligible']
                    assert item['source']=='bank' and item['state'] in ('exploring','practicing','proficient','mastered')
                    response=Response();summary=await overview(actor,response,scope,item['id'])
                    assert response.headers['cache-control']=='private, no-store' and summary['eligible']==item['eligible'] and summary['due']==item['due']
                    per_deck+=1
                timings.append(round((time.monotonic()-start)*1000,3));checks+=1
        async with db.cursor() as cur:
            await cur.execute('SELECT count(*) AS n FROM reward_ledger');after=(await cur.fetchone())['n']
            d=await reward_economy.diagnostics(cur);integrity={k:d[k] for k in reward_economy.INTEGRITY_FIELDS}
            assert before==after and all(v==0 for v in integrity.values()) and reward_economy.reconciled_release()
        return {'account_users_checked':len(users),'deck_catalog_checks':checks,'deck_overview_checks':per_deck,'batch_ms':timings,'database_role':'mpsc','transactions_read_only':True,'ledger_before':before,'ledger_after':after,'integrity':integrity,'economy_reconciled':True,'workers_started':False,'synthetic_production_activity':False}
    finally:await db._pool.close()
if __name__=='__main__':print(json.dumps(asyncio.run(verify())))
