#!/usr/bin/env python3
"""Private read-only verification of the deployed study-note release; no workers."""
import asyncio,json,os,sys
os.chdir('/');sys.path.insert(0,'/srv/api')
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool
from fastapi import Response
from app import db
from app.routers import community,study_posts
from app.services import reward_economy
async def verify():
    db._pool=AsyncConnectionPool('dbname=mpsc',min_size=1,max_size=2,kwargs={'row_factory':dict_row,'options':'-c role=mpsc -c default_transaction_read_only=on -c jit=off'},open=False)
    await db._pool.open(wait=True)
    try:
        async with db.cursor() as cur:
            await cur.execute("SELECT current_user,current_setting('transaction_read_only') AS readonly")
            assert await cur.fetchone()=={'current_user':'mpsc','readonly':'on'}
            await cur.execute('SELECT id FROM users WHERE email IS NOT NULL ORDER BY id');users=[r['id'] for r in await cur.fetchall()]
            await cur.execute('SELECT count(*)::int AS n FROM reward_ledger');before=(await cur.fetchone())['n']
        checks=0;visible_notes=0;visible_shares=0
        for user in users:
            state=await study_posts.status(user);assert state['registered'] and state['post_limit'] in (5,10);checks+=1
            for version in (1,2):
                for tab in ('for-you','following','questions'):
                    response=Response();result=await community.community_feed(user,response,tab=tab,discussion='all',shelf_id=None,limit=20,offset=0,content_version=version)
                    assert result.available and response.headers['cache-control']=='private, no-store';checks+=1
                    if version==1 or tab=='questions':assert all(p.kind not in {'study','material-share'} for p in result.items)
                    visible_notes+=sum(p.kind=='study' for p in result.items);visible_shares+=sum(p.kind=='material-share' for p in result.items)
        async with db.cursor() as cur:
            await cur.execute('SELECT count(*)::int AS n FROM reward_ledger');after=(await cur.fetchone())['n']
            diagnostics=await reward_economy.diagnostics(cur)
        integrity={k:diagnostics[k] for k in reward_economy.INTEGRITY_FIELDS}
        assert before==after and all(v==0 for v in integrity.values()) and reward_economy.reconciled_release()
        return {'database_role':'mpsc','transactions_read_only':True,'account_users_checked':len(users),'private_route_checks':checks,'visible_study_rows':visible_notes,'visible_material_share_rows':visible_shares,'ledger_before':before,'ledger_after':after,'integrity':integrity,'economy_reconciled':True,'workers_started':False,'synthetic_production_activity':False}
    finally:await db._pool.close()
if __name__=='__main__':print(json.dumps(asyncio.run(verify())))
