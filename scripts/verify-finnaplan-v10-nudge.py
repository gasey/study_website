#!/usr/bin/env python3
"""Private read-only verification of the deployed study-note release; no workers."""
import asyncio,json,os,sys
os.chdir('/');sys.path.insert(0,'/srv/api')
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool
from fastapi import Response,HTTPException
from app import db
from app.routers import community,study_posts,discussions
from app.services import reward_economy,post_edits
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
            try:await study_posts.replies(-1,user,offset=0,limit=20)
            except HTTPException as error:assert error.status_code==404;checks+=1
            else:raise AssertionError('Missing parent exposed a reply conversation')
            async with db.cursor() as cur:
                try:await post_edits.history(cur,-1,user)
                except HTTPException as error:assert error.status_code==404;checks+=1
                else:raise AssertionError('Missing post exposed revision history')
            async with db.cursor() as cur:
                assert not await discussions.acceptance_nudge_eligible(cur,-1,user);checks+=1
            for version in (1,2):
                for tab in ('for-you','following','questions'):
                    response=Response();result=await community.community_feed(user,response,tab=tab,discussion='all',shelf_id=None,limit=20,offset=0,content_version=version)
                    assert result.available and response.headers['cache-control']=='private, no-store';checks+=1
                    if version==1 or tab=='questions':assert all(p.kind not in {'study','material-share'} for p in result.items)
                    visible_notes+=sum(p.kind=='study' for p in result.items);visible_shares+=sum(p.kind=='material-share' for p in result.items)
        async with db.cursor() as cur:
            await cur.execute('SELECT count(*)::int AS n FROM reward_ledger');after=(await cur.fetchone())['n']
            diagnostics=await reward_economy.diagnostics(cur)
            await cur.execute("""SELECT
              (SELECT count(*) FROM posts WHERE accepted AND NOT edit_locked) AS unlocked_accepted,
              (SELECT count(*) FROM posts p WHERE content_version>0 AND NOT EXISTS(SELECT 1 FROM post_revisions r WHERE r.post_id=p.id AND r.version=p.content_version AND r.body=p.body AND r.source_links=p.source_links)) AS missing_current_snapshot,
              (SELECT count(*) FROM posts p WHERE content_version>0 AND NOT EXISTS(SELECT 1 FROM post_revisions r WHERE r.post_id=p.id AND r.version=0)) AS missing_original_snapshot""")
            edit_integrity=await cur.fetchone();assert all(v==0 for v in edit_integrity.values())
            await cur.execute("SELECT has_function_privilege('mpsc','community_edit_post(bigint,text,integer,text,jsonb,text,text)','EXECUTE') AS enabled")
            assert (await cur.fetchone())['enabled']
            await cur.execute("SELECT indisunique AND indisvalid AS valid FROM pg_index WHERE indexrelid='discussion_acceptance_nudge_once'::regclass")
            assert (await cur.fetchone())['valid']
            await cur.execute("SELECT count(*) AS n FROM discussion_events e JOIN posts p ON p.id=e.post_id WHERE e.action='acceptance_nudged' AND (p.kind<>'doubt' OR p.parent_id IS NOT NULL OR p.author_id<>e.actor_id)")
            assert (await cur.fetchone())['n']==0
        integrity={k:diagnostics[k] for k in reward_economy.INTEGRITY_FIELDS}
        assert before==after and all(v==0 for v in integrity.values()) and reward_economy.reconciled_release()
        return {'database_role':'mpsc','transactions_read_only':True,'account_users_checked':len(users),'private_route_checks':checks,'visible_study_rows':visible_notes,'visible_material_share_rows':visible_shares,'ledger_before':before,'ledger_after':after,'edit_integrity':edit_integrity,'nudge_index_valid':True,'invalid_nudge_events':0,'integrity':integrity,'economy_reconciled':True,'workers_started':False,'synthetic_production_activity':False}
    finally:await db._pool.close()
if __name__=='__main__':print(json.dumps(asyncio.run(verify())))
