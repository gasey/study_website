#!/usr/bin/env python3
"""Rehearse staged Desk practice on a fresh Oracle dump clone; never deploy.

Run locally with api/.venv/bin/python scripts/rehearse-desk-practice.py.
Only a temporary clone is migrated. Production workflow rows and API files are
never written. The real-role probe rolls back before all original rows are hashed.
"""
from pathlib import Path
from uuid import uuid4
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
FILES = ('app/routers/study_desks.py', 'app/services/desk_goals.py',
         'app/services/desk_games.py','app/services/game_selection.py','app/services/games.py',
         'app/routers/games.py','app/services/mobile_identity.py','app/services/reward_economy.py',
         'app/data/learning-economy-v2.json',
         'migrations/0111_desk_weekly_goals.sql', 'migrations/0112_desk_review_circle.sql',
         'migrations/0113_desk_practice_sessions.sql')


def run(args, **kwargs):
    result = subprocess.run(args, capture_output=True, text=True, **kwargs)
    if result.returncode:
        raise RuntimeError(result.stderr[-6000:])
    return result.stdout


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def remote(stage):
    os.chdir('/')
    import asyncio
    import psycopg
    from psycopg import sql
    from psycopg.rows import dict_row
    scope = json.loads((stage/'scope.json').read_text())
    assert digest(stage/'rehearse.py') == scope['operator_sha256']
    assert all(digest(stage/'api'/n) == h for n,h in scope['candidate_sha256'].items())
    assert not Path('/srv/api/migrations/0111_desk_weekly_goals.sql').exists(), '0111 already applied/staged on host; inspect first'
    name = 'finna_desk_practice_' + uuid4().hex[:12]
    admin = psycopg.connect('dbname=postgres',autocommit=True)
    created = False
    result = {}

    def fingerprints(conn, definitions):
        output = {}
        for table, columns in definitions:
            sha = hashlib.sha256(); count = 0
            query = sql.SQL('SELECT md5(ROW({})::text) AS h FROM {} ORDER BY h').format(
                sql.SQL(',').join(map(sql.Identifier,columns)),sql.Identifier(table))
            with conn.cursor(name='desk_fp_'+uuid4().hex) as cur:
                cur.execute(query)
                for row in cur:sha.update(row[0].encode());count += 1
            output[table] = {'count':count,'sha256':sha.hexdigest()}
        return output

    try:
        with tempfile.TemporaryDirectory(prefix='finna-desk-practice-clone-') as directory:
            root = Path(directory); dump = root/'workflow.dump'
            with dump.open('wb') as out:
                subprocess.run(['pg_dump','-Fc','-Z1','--no-owner','mpsc'],stdout=out,check=True,timeout=600)
            admin.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(name))); created = True
            subprocess.run(['pg_restore','--exit-on-error','--no-owner','-d',name,str(dump)],check=True,timeout=600,capture_output=True)
            candidate = root/'api'
            shutil.copytree('/srv/api/app',candidate/'app',ignore=shutil.ignore_patterns('__pycache__'))
            shutil.copytree('/srv/api/migrations',candidate/'migrations')
            for n in FILES:shutil.copy2(stage/'api'/n,candidate/n)
            with psycopg.connect('dbname='+name) as conn:
                definitions = conn.execute("SELECT table_name,array_agg(column_name::text ORDER BY ordinal_position) FROM information_schema.columns WHERE table_schema='public' AND table_name IN(SELECT tablename FROM pg_tables WHERE schemaname='public') GROUP BY table_name ORDER BY table_name").fetchall()
                before = fingerprints(conn,definitions); conn.commit()
            with psycopg.connect('dbname='+name,autocommit=True) as conn:
                result['migration_ms'] = {}
                for n in (n for n in FILES if n.startswith('migrations/')):
                    started = time.perf_counter()
                    conn.execute((candidate/n).read_text())
                    result['migration_ms'][n] = round((time.perf_counter()-started)*1000,3)
            sys.path.insert(0,str(candidate))
            from app.services import desk_goals
            async def probe():
                async with await psycopg.AsyncConnection.connect('dbname='+name,row_factory=dict_row) as conn:
                    async with conn.cursor() as cur:
                        await cur.execute('SET LOCAL ROLE mpsc')
                        await cur.execute("SELECT id FROM users WHERE email IS NOT NULL AND closed_at IS NULL AND NOT EXISTS(SELECT 1 FROM game_members gm WHERE gm.user_id=users.id AND gm.released_at IS NULL) ORDER BY id LIMIT 1")
                        user = (await cur.fetchone())['id']
                        did = 'desk_rehearsal_'+uuid4().hex
                        await cur.execute("INSERT INTO study_desks(id,owner_id,name) VALUES(%s,%s,'Disposable rehearsal')",(did,user))
                        period = await desk_goals.clock(cur)
                        await cur.execute('INSERT INTO study_desk_members(desk_id,user_id,joined_at) VALUES(%s,%s,%s)',(did,user,period['start_at']))
                        initial = await desk_goals.summary(cur,did,user,period)
                        assert initial['target'] is None and initial['scored_attempts'] == 0 and initial['sharing_members'] == 0
                        await cur.execute('INSERT INTO study_desk_weekly_goals(desk_id,week_start,target,updated_by) VALUES(%s,%s,300,%s)',(did,period['week_start'],user))
                        await cur.execute("UPDATE study_desk_members SET sharing='{"+'"progress":true'+"}' WHERE desk_id=%s",(did,))
                        started = time.perf_counter(); shared = await desk_goals.summary(cur,did,user,period)
                        elapsed = round((time.perf_counter()-started)*1000,3)
                        assert shared['target'] == 300 and shared['version'] == 1 and shared['sharing_members'] == 1
                        await cur.execute("UPDATE study_desk_members SET sharing='{}' WHERE desk_id=%s",(did,))
                        private = await desk_goals.summary(cur,did,user,period)
                        assert private['scored_attempts'] == 0 and private['sharing_members'] == 0
                        await cur.execute("SELECT has_table_privilege('mpsc','study_desk_weekly_goals','DELETE') AS allowed")
                        assert not (await cur.fetchone())['allowed']
                        from app.config import settings
                        settings.study_desks_private_enabled = True  # this disposable probe process only
                        from app.services import desk_games, games as g, reward_economy
                        assert reward_economy.reconciled_release(), 'Candidate economy evidence differs'
                        await cur.execute('SELECT id FROM v_scorable ORDER BY id LIMIT 1')
                        qid = (await cur.fetchone())['id']
                        iid = 'item_rehearsal_'+uuid4().hex; rid = 'game_rehearsal_'+uuid4().hex
                        await cur.execute("INSERT INTO study_desk_items(id,desk_id,author_id,kind,question_id,request_key,request_hash) VALUES(%s,%s,%s,'question',%s,%s,'rehearsal')",(iid,did,user,qid,uuid4().hex))
                        from psycopg.types.json import Jsonb
                        ctx = {'desk_id':did,'desk_sources':[{'item_id':iid,'question_id':qid}], 'desk_question_ids':[qid]}
                        await cur.execute("INSERT INTO game_rooms(id,owner_id,mode,capacity,questions,round_seconds,request_key,request_hash,selection_context,context_hash,desk_id) VALUES(%s,%s,'party',4,%s,25,%s,'rehearsal',%s,%s,%s)",(rid,user,Jsonb([{'id':qid}]),uuid4().hex,Jsonb(ctx),g.digest(ctx),did))
                        await cur.execute('INSERT INTO game_members(room_id,user_id) VALUES(%s,%s)',(rid,user))
                        game = await g.room(cur,rid)
                        await desk_games.access(cur,game,user)
                        await cur.execute('UPDATE study_desk_items SET deleted_at=clock_timestamp() WHERE id=%s',(iid,))
                        cancelled = await g.advance(cur,game,await g.clock(cur))
                        assert cancelled['state']=='cancelled'
                        await cur.execute('SELECT released_at IS NOT NULL AS freed FROM game_members WHERE room_id=%s',(rid,))
                        assert (await cur.fetchone())['freed']
                        await conn.rollback()
                        return {'real_role':'mpsc','desk_binding_and_withdrawal':True,'candidate_evidence_valid':True,'private_flag_enabled_only_in_probe':True,'consent_revoke_and_empty':True,'goal_read_write':True,
                          'delete_not_granted':True,'rolled_back':True,'single_member_summary_ms':elapsed}
            result['probe'] = asyncio.run(probe())
            # 0112 intentionally adds one defaulted column. Hash the original
            # column lists to prove every pre-existing value is preserved.
            with psycopg.connect('dbname='+name) as conn:
                assert before == fingerprints(conn,definitions), 'Original rows changed'
                assert conn.execute('SELECT count(*) FROM study_desk_weekly_goals').fetchone()[0] == 0
                result |= {'existing_tables_checked':len(before),'all_existing_rows_identical':True,'before':before}
    finally:
        if created:admin.execute(sql.SQL('DROP DATABASE {} WITH (FORCE)').format(sql.Identifier(name)))
        admin.close()
    result |= {'candidate_sha256':scope['candidate_sha256'],'production_database_writes':False,
               'production_api_changed':False,'clone_and_dump_removed':True,'workers_started':False}
    return result


def main():
    if len(sys.argv) == 3 and sys.argv[1] == '--remote':
        stage = Path(sys.argv[2])
        receipt = json.dumps(remote(stage))
        (stage/'result.json').write_text(receipt+'\n')
        print(receipt);return
    assert len(sys.argv) == 1
    report = ROOT/'reports/finna-desk-practice-staged-20261118'; report.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='finna-desk-practice-package-') as directory:
        package = Path(directory)
        for n in FILES:
            target = package/'api'/n; target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(ROOT/'api'/n,target)
        shutil.copy2(__file__,package/'rehearse.py')
        scope = {'candidate_sha256':{n:digest(package/'api'/n) for n in FILES},'operator_sha256':digest(package/'rehearse.py')}
        (package/'scope.json').write_text(json.dumps(scope))
        (package/'result.json').touch()
        host = 'ubuntu@152.67.31.231'
        stage = run(['ssh',host,'mktemp -d /tmp/finna-desk-practice-stage.XXXXXX']).strip()
        assert re.fullmatch(r'/tmp/finna-desk-practice-stage\.[A-Za-z0-9]+',stage)
        try:
            run(['rsync','-az',str(package)+'/',host+':'+stage+'/'])
            run(['ssh',host,'chmod -R a+rX '+shlex.quote(stage)+' && chmod a+w '+shlex.quote(stage+'/result.json')])
            receipt = run(['ssh',host,'sudo -u postgres /srv/api/.venv/bin/python '+shlex.quote(stage+'/rehearse.py')+' --remote '+shlex.quote(stage)],timeout=1500)
            parsed = json.loads(receipt)
            (report/'clone.json').write_text(json.dumps(parsed,indent=2)+'\n')
            print(json.dumps({k:v for k,v in parsed.items() if k != 'before'}))
        finally:
            run(['ssh',host,'sudo rm -rf -- '+shlex.quote(stage)])


if __name__ == '__main__':main()
