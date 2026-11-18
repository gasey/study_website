#!/usr/bin/env python3
"""Read-only mpsc verification; optionally load the staged candidate helper."""
import asyncio,importlib.util,json,os,sys,time
os.chdir('/');sys.path.insert(0,'/srv/api')
if len(sys.argv)==2:
    spec=importlib.util.spec_from_file_location('app.services.submissions',sys.argv[1]);module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool
from app import db
from app.services import submissions,reward_economy
async def verify():
    db._pool=AsyncConnectionPool('dbname=mpsc',min_size=1,max_size=2,kwargs={'row_factory':dict_row,'options':'-c role=mpsc -c default_transaction_read_only=on -c jit=off -c statement_timeout=15000'},open=False)
    await db._pool.open(wait=True)
    try:
        async with db.cursor() as cur:
            await cur.execute("SELECT current_user,current_setting('transaction_read_only') AS readonly");assert await cur.fetchone()=={'current_user':'mpsc','readonly':'on'}
            await cur.execute('SELECT id FROM users WHERE email IS NOT NULL ORDER BY id');users=[r['id'] for r in await cur.fetchall()]
            await cur.execute('SELECT count(*) AS n FROM reward_ledger');before=(await cur.fetchone())['n']
        timings=[];checks=0;items=0;route_checks=0
        for user in users:
            for offset in (0,20):
                start=time.monotonic()
                async with db.cursor() as cur:
                    result=await submissions.tracker(cur,user,offset,20)
                    for row in result['items']:
                        table={'bank':'bank_contributions','material':'materials','collection':'learning_catalog'}[row['pipeline']]
                        await cur.execute('SELECT author_id FROM '+table+' WHERE id=%s',(row['id'],));assert (await cur.fetchone())['author_id']==user
                        if row['locked']:assert row['title']=='Linked question details are locked' and row['feedback'] is None
                    assert len(result['items'])<=20 and len(result['review_times'])==3
                    assert all(r['sample_count']>=0 and (r['median_seconds'] is None or r['median_seconds']>=0) for r in result['review_times'])
                    assert result['standing']['post_limit'] in (5,10)
                timings.append(round((time.monotonic()-start)*1000,3));checks+=1;items+=len(result['items'])
            if len(sys.argv)==1:
                from fastapi import Response
                from starlette.requests import Request
                from app.routers.community import my_submissions
                response=Response();request=Request({'type':'http','method':'GET','path':'/api/community/submissions','headers':[]})
                result=await my_submissions(request,response,user,0,20)
                assert response.headers['cache-control']=='private, no-store' and len(result['items'])<=20
                route_checks+=1
        async with db.cursor() as cur:
            await cur.execute('SELECT count(*) AS n FROM reward_ledger');after=(await cur.fetchone())['n']
            d=await reward_economy.diagnostics(cur);integrity={k:d[k] for k in reward_economy.INTEGRITY_FIELDS}
            assert before==after and all(v==0 for v in integrity.values()) and reward_economy.reconciled_release()
        return {'account_users_checked':len(users),'private_tracker_checks':checks,'private_handler_checks':route_checks,'owned_rows_checked':items,'batch_ms':timings,'database_role':'mpsc','transactions_read_only':True,'ledger_before':before,'ledger_after':after,'integrity':integrity,'economy_reconciled':True,'workers_started':False,'synthetic_production_activity':False}
    finally:await db._pool.close()
if __name__=='__main__':print(json.dumps(asyncio.run(verify())))
