#!/usr/bin/env python3
"""Real-role, read-only community verification. Never opens workers or creates users."""
import asyncio, importlib.util, json, os, sys
from pathlib import Path
os.chdir('/')
sys.path.insert(0, '/srv/api')
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool
from fastapi import Response
from app import db

async def verify(candidate=None):
    if candidate:
        spec=importlib.util.spec_from_file_location('app.routers.community_candidate',candidate)
        reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader)
    else:
        from app.routers import community as reader
    db._pool=AsyncConnectionPool('dbname=mpsc',min_size=1,max_size=2,
        kwargs={'row_factory':dict_row,'options':'-c role=mpsc -c default_transaction_read_only=on -c jit=off'},open=False)
    await db._pool.open(wait=True)
    try:
        async with db.cursor() as cur:
            await cur.execute("SELECT current_user,current_setting('transaction_read_only') AS readonly")
            assert await cur.fetchone()=={'current_user':'mpsc','readonly':'on'}
            await cur.execute('SELECT DISTINCT u.id FROM users u JOIN attempts a ON a.user_id=u.id WHERE u.email IS NOT NULL ORDER BY u.id LIMIT 10')
            users=[row['id'] for row in await cur.fetchall()]
            await cur.execute('SELECT count(*)::int AS n FROM reward_ledger');before=(await cur.fetchone())['n']
        checks=0;rows=0
        for user in users:
            for scope in ('mizoram-recruitment','all'):
                for tab,discussion in [('following','all'),('following','unanswered'),('for-you','all'),('questions','doubts')]:
                    response=Response()
                    result=await reader.community_feed(user,response,tab=tab,discussion=discussion,shelf_id=None,limit=20,offset=0,exam_scope=scope)
                    assert result.available and response.headers['cache-control']=='private, no-store'
                    rows+=len(result.items);checks+=1
                    if tab=='following':
                        assert [r.created_at for r in result.items]==sorted([r.created_at for r in result.items],reverse=True)
                    for item in result.items:
                        async with db.cursor() as cur:
                            await cur.execute('''SELECT NOT p.hidden AND NOT p.needs_approval AND NOT p.before_fix
                              AND NOT EXISTS(SELECT 1 FROM creator_blocks b WHERE (b.user_id=%s AND b.blocked_id=p.author_id) OR (b.user_id=p.author_id AND b.blocked_id=%s))
                              AND (NOT %s OR EXISTS(SELECT 1 FROM creator_follows f JOIN creator_profiles cp ON cp.user_id=f.creator_id AND cp.public WHERE f.follower_id=%s AND f.creator_id=p.author_id)) AS visible
                              FROM posts p WHERE p.id=%s''',(user,user,tab=='following',user,item.id))
                            assert (await cur.fetchone())['visible']
        async with db.cursor() as cur:
            await cur.execute('SELECT count(*)::int AS n FROM reward_ledger');after=(await cur.fetchone())['n']
        assert before==after
        return {'database_role':'mpsc','transactions_read_only':True,'account_users_checked':len(users),
            'community_route_checks':checks,'visible_rows_checked':rows,'ledger_before':before,'ledger_after':after,
            'workers_started':False,'synthetic_production_activity':False,'candidate_reader':bool(candidate)}
    finally:
        await db._pool.close()
if __name__=='__main__':
    print(json.dumps(asyncio.run(verify(sys.argv[1] if len(sys.argv)>1 else None))))
