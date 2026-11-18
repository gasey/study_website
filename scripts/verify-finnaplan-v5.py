#!/usr/bin/env python3
"""Read-only V.5 release readback as mpsc; no workers, sessions or learner writes.

Run on Oracle via sudo -u postgres /srv/api/.venv/bin/python. Identity is
provided only inside this separate verifier process. Live HTTP authentication
is not bypassed or changed; its boundaries are tested in the isolated suite.
"""
import asyncio
from datetime import date,timedelta
import json
import os
os.chdir('/')  # Avoid reading an operator home or production dotenv file.
import sys
sys.path.insert(0,'/srv/api')
from contextlib import asynccontextmanager
from types import SimpleNamespace
from urllib.parse import urlsplit
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool
from app import db
from app.main import app
from app.deps import current_user


class ReadClient:
    async def request(self,path,body=None):
        target=urlsplit(path);messages=[];received=False
        payload=json.dumps(body).encode() if body is not None else b''
        async def receive():
            nonlocal received
            if not received:
                received=True
                return {'type':'http.request','body':payload,'more_body':False}
            await asyncio.Event().wait()
        async def send(message):messages.append(message)
        headers=[(b'host',b'study.hawayu.in'),(b'origin',b'https://study.hawayu.in')]
        if body is not None:headers.extend([(b'content-type',b'application/json'),(b'content-length',str(len(payload)).encode())])
        await app({'type':'http','asgi':{'version':'3.0'},'http_version':'1.1','method':'POST' if body is not None else 'GET',
          'scheme':'https','path':target.path,'raw_path':target.path.encode(),'query_string':target.query.encode(),
          'root_path':'','headers':headers,'server':('study.hawayu.in',443),'client':('127.0.0.1',0)},receive,send)
        start=next(m for m in messages if m['type']=='http.response.start')
        data=json.loads(b''.join(m.get('body',b'') for m in messages if m['type']=='http.response.body'))
        return SimpleNamespace(status_code=start['status'],headers={k.decode():v.decode() for k,v in start['headers']},json=lambda:data)
    async def get(self,path):return await self.request(path)
    async def post(self,path,**kwargs):return await self.request(path,kwargs['json'])


@asynccontextmanager
async def read_client():
    yield ReadClient()


async def verify(database_name='mpsc'):
    db._pool=AsyncConnectionPool('dbname='+database_name,min_size=1,max_size=3,
      kwargs={'row_factory':dict_row,'options':'-c role=mpsc -c default_transaction_read_only=on -c jit=off'},open=False)
    await db._pool.open(wait=True)
    try:
        async with db.cursor() as cur:
            await cur.execute("SELECT current_user,current_setting('transaction_read_only') AS readonly")
            assert await cur.fetchone()=={'current_user':'mpsc','readonly':'on'}
            await cur.execute('SELECT DISTINCT u.id FROM users u JOIN attempts a ON a.user_id=u.id WHERE u.email IS NOT NULL ORDER BY u.id')
            users=[r['id'] for r in await cur.fetchall()]
        checks=0
        async with read_client() as client:
            for user in users:
                app.dependency_overrides[current_user]=lambda:user
                async with db.cursor() as cur:
                    await cur.execute('SELECT count(*)::int AS answered,count(*) FILTER(WHERE correct)::int AS correct,count(DISTINCT canonical_id)::int AS unique_questions FROM attempts WHERE user_id=%s',(user,))
                    actual=await cur.fetchone()
                    await cur.execute("SELECT (now() AT TIME ZONE 'Asia/Kolkata')::date AS day")
                    day=(await cur.fetchone())['day']
                reads={}
                paths=['/api/me/progress?detail=true','/api/me/mastery','/api/me/review-queue','/api/me/focus-subjects','/api/me/today',
                  '/api/rewards/me','/api/me/calendar-layers?start='+day.isoformat()+'&end='+(day+timedelta(days=30)).isoformat(),'/api/games']
                for path in paths:
                    response=await client.get(path)
                    assert response.status_code==200,(path,response.status_code)
                    assert response.headers.get('cache-control')=='private, no-store',path
                    reads[path.split('?')[0]]=response.json();checks+=1
                progress=reads['/api/me/progress']
                assert {k:progress[k] for k in actual}==actual,'Activity rollup differs from original attempts'
                today=reads['/api/me/today'];queue=reads['/api/me/review-queue']
                assert today['account'] and today['due_count']==queue['due_count']
                budget=reads['/api/rewards/me']['point_budget']
                assert budget['cap']==25 and budget['remaining']==max(0,25-budget['earned'])
                assert {p['key']:p['cap'] for p in budget['pillars']}=={'learn':12,'revise':4,'prove':3,'play':4,'daily':1,'habit':10}
                assert reads['/api/rewards/me']['rule_version']=='learning-v2'
                assert progress['streak_basis']=='account learning'
                assert progress['current_streak']==reads['/api/rewards/me']['current_streak_days']
                assert {q['key'] for q in today['quests']}=={'warmup_circuit','review_ring','plan_ring'}
                assert isinstance(today['plan_status']['started'],bool)
                assert today['daily_five']['url'].startswith('/games')
                assert reads['/api/games']['daily']['id']==day.isoformat()
                preview=await client.post('/api/games/preview',headers={'Origin':'https://study.hawayu.in'},json={'mode':'daily','selection':{'kind':'mixed','excluded_areas':[]}})
                assert preview.status_code==200,preview.status_code
                assert preview.json()['required']==5
                checks+=1
                v5={}
                for path in ('/api/me/identity','/api/me/account-tools','/api/me/avatar?catalog_version=2',
                    '/api/me/avatar','/api/me/calendar/feed','/api/rewards/leaderboard?contract=2',
                    '/api/games/leaderboard?mode=speed&contract=2'):
                    response=await client.get(path)
                    assert response.status_code==200,(path,response.status_code)
                    assert response.headers.get('cache-control')=='private, no-store' and not response.headers.get('etag'),path
                    v5[path]=response.json();checks+=1
                assert v5['/api/me/identity']['user_id']==user
                assert v5['/api/me/account-tools']['user_id']==user
                assert len(v5['/api/me/avatar']['catalog'])==26
                assert len(v5['/api/me/avatar?catalog_version=2']['catalog'])==29
                for path,fields in (('/api/rewards/leaderboard?contract=2',{'handle','xp','rank'}),
                    ('/api/games/leaderboard?mode=speed&contract=2',{'handle','score','rank'})):
                    assert v5[path]['period']=='week' and len(v5[path]['items'])<=35
                    assert all(set(row)==fields for row in v5[path]['items'])
                from app.services import account_tools
                async with db.cursor() as cur:
                    exported=json.loads(''.join([part async for part in account_tools.export(cur,user)]))
                    assert exported['account']['id']==user
                    assert all('scoring_snapshot' not in row for row in exported['attempts'])
                    assert not {'password_hash','token_hash','secret_cipher'}&set(exported['account'])
                checks+=1
            # Existing actual owner grant, separate verifier process only. No
            # live credential/session or MFA assertion is created for this read.
            from app.services.review_identity import identity,Actor
            async with db.cursor() as cur:
                await cur.execute("SELECT user_id FROM review_grants WHERE role='owner' AND subject_id IS NULL AND revoked_at IS NULL ORDER BY user_id LIMIT 1")
                owner=(await cur.fetchone())['user_id']
            app.dependency_overrides[identity]=lambda:Actor(owner,'',False,False)
            diagnostics=await client.get('/api/admin/bank/reward-diagnostics')
            assert diagnostics.status_code==200,diagnostics.status_code
            diagnostic_fields=('claims_without_receipts','receipts_without_claims','wallets_in_debt','over_cap_days',
              'review_receipt_mismatches','orphan_review_receipts','review_over_cap_days','duplicate_quest_slots',
              'daily_counter_mismatches','missing_daily_counters','v2_point_over_cap_days','v2_pillar_over_cap_days','game_completion_mismatches','mock_completion_mismatches',
              'mastery_receipt_mismatches','orphan_completion_receipts','contribution_receipt_mismatches',
              'contribution_reversal_mismatches','contribution_over_cap_days',
              'cosmetic_ledger_mismatches','cosmetic_audit_mismatches','duplicate_cosmetic_purchases')
            diagnostics={k:diagnostics.json()[k] for k in diagnostic_fields}
            checks+=1
            assert all(v==0 for v in diagnostics.values()),diagnostics
            gates=await client.get('/api/admin/bank/reward-feature-gates')
            assert gates.status_code==200 and not gates.json()['catalog_ready']
            assert {c['key'] for c in gates.json()['checks']}=={'legal_pages','email_recovery','paid_checkout','economy_reconciliation'}
            launch={c['key']:c['ready'] for c in gates.json()['checks']}
            assert launch['economy_reconciliation'] and not launch['paid_checkout'] and not launch['legal_pages'],launch
            checks+=1
        return {'account_users_checked':len(users),'private_route_checks':checks,'activity_ground_truth_matches':True,
          'streak_surfaces_agree':True,'new_quest_keys':True,'point_limits_visible':True,'catalog_launch_blocked':True,'economy_reconciled':True,'feature_gates':launch,'reward_diagnostics':diagnostics,'today_due_matches_full_queue':True,'daily_preview_reads':True,'database_role':'mpsc','transactions_read_only':True,
          'workers_started':False,'authentication_overrides':'separate verifier process only; no live API/session changes'}
    finally:
        app.dependency_overrides.clear()
        await db._pool.close()


if __name__=='__main__':
    print(json.dumps(asyncio.run(verify())))
