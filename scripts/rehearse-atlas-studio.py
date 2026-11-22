#!/usr/bin/env python3
"""Rehearse staged Atlas Studio on a fresh Oracle dump clone; never deploy.

Run locally with api/.venv/bin/python scripts/rehearse-atlas-studio.py.
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
FILES = ('app/services/atlas_studio.py','app/main.py','app/schemas.py','app/routers/questions.py','app/services/browse_allowance.py','app/routers/atlas.py','app/services/atlas_bindings.py','app/data/atlas-static-catalog.json','app/services/desk_calendar.py','app/services/owned_calendar.py','app/routers/calendar_owned.py','app/services/desk_notes.py','app/services/account_tools.py','app/routers/account_tools.py',
         'app/routers/study_desks.py', 'app/services/desk_goals.py',
         'app/services/desk_games.py','app/services/game_selection.py','app/services/games.py',
         'app/routers/games.py','app/services/mobile_identity.py','app/services/reward_economy.py',
         'app/data/learning-economy-v2.json',
         'migrations/0111_desk_weekly_goals.sql', 'migrations/0112_desk_review_circle.sql',
         'migrations/0113_desk_practice_sessions.sql','migrations/0114_desk_note_links.sql','migrations/0115_calendar_desk_view.sql','migrations/0116_atlas_topic_bindings.sql','migrations/0117_atlas_chapter_lifecycle.sql','migrations/0118_atlas_current_site_seed.sql')


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
    name = 'finna_atlas_studio_' + uuid4().hex[:12]
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
        with tempfile.TemporaryDirectory(prefix='finna-atlas-studio-clone-') as directory:
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
                        from app.services import desk_notes
                        noteid = 'item_note_'+uuid4().hex
                        await cur.execute("INSERT INTO study_desk_items(id,desk_id,author_id,kind,question_id,title,body,request_key,request_hash) VALUES(%s,%s,%s,'note',NULL,'Probe note','Disposable note',%s,'probe')",(noteid,did,user,uuid4().hex))
                        shared = await desk_notes.shared(cur,did,noteid,user)
                        assert shared['question_id'] is None
                        await cur.execute("INSERT INTO study_desk_messages(desk_id,author_id,body,note_id,request_key,request_hash) VALUES(%s,%s,'Linked note',%s,%s,'probe')",(did,user,noteid,uuid4().hex))
                        visible = await desk_notes.document(cur,user,{'notes':[{'id':'probe','title':'Probe','body':'Safe text','question_id':qid}]})
                        assert len(visible['notes'])==0, 'Active game must hide its question note'
                        assert '&lt;script&gt;' in desk_notes.printable([{'title':'<script>','body':'Safe text'}],'probe')
                        from app.services import desk_calendar
                        ceid=uuid4()
                        await cur.execute("INSERT INTO calendar_entries(id,user_id,date,title,kind,desk_id,desk_joined_at) SELECT %s,%s,(now() AT TIME ZONE 'Asia/Kolkata')::date+2,'Shared rehearsal date','exam-target',desk_id,joined_at FROM study_desk_members WHERE desk_id=%s AND user_id=%s",(ceid,user,did,user))
                        from datetime import timedelta
                        day=desk_calendar.owned_calendar.india_today()
                        dates=await desk_calendar.view(cur,did,user,day,day+timedelta(days=31))
                        assert any(str(x['id'])==str(ceid) and x['days_until']==2 for x in dates['occurrences'])
                        await cur.execute('UPDATE calendar_entries SET desk_id=NULL,desk_joined_at=NULL WHERE id=%s',(ceid,))
                        assert not (await desk_calendar.view(cur,did,user,day,day+timedelta(days=31)))['occurrences']
                        from app.services import atlas_bindings as atlas
                        await cur.execute('SELECT id FROM v_all_questions ORDER BY id LIMIT 100')
                        sample=[r['id'] for r in await cur.fetchall()]
                        started_at=time.perf_counter()
                        assert not await atlas.reverse(cur,sample,user)
                        result['empty_atlas_reverse_100_ms']=round((time.perf_counter()-started_at)*1000,3)
                        from app.routers.learning import not_assessed
                        await cur.execute("SELECT v.id,p.subject_id,p.topic_id FROM v_all_questions v JOIN v_question_paths p ON p.question_id=v.id JOIN review_taxonomy t ON t.id=p.topic_id AND t.active AND t.level='topic' JOIN review_taxonomy sub ON sub.id=t.parent_id AND sub.id=p.subject_id AND sub.active WHERE "+not_assessed('v')+' ORDER BY v.id LIMIT 1',{'user':user})
                        target=await cur.fetchone();assert target
                        binding_id=uuid4()
                        draft={'chapter_id':atlas.CATALOG['chapters'][0]['id'],'layer_id':None,'event_id':None,'subject_id':target['subject_id'],'topic_id':target['topic_id']}
                        await atlas.save(cur,binding_id,0,draft,user,'Synthetic clone fixture only; never live curation')
                        assert not await atlas.reverse(cur,[target['id']],user)
                        await atlas.decide(cur,binding_id,1,'publish',user,'Synthetic clone fixture only; rolled back')
                        assert (await atlas.reverse(cur,[target['id']],user))[target['id']]
                        await atlas.decide(cur,binding_id,2,'hold',user,'Synthetic clone fixture withdrawal')
                        assert not await atlas.reverse(cur,[target['id']],user)
                        from app.services import atlas_studio as studio
                        assert len(await studio.catalog(cur))==26
                        seed=await studio.published(cur,'rivers-of-india');doc=seed['body'].copy()
                        doc['id']='synthetic-studio-'+uuid4().hex[:12];doc['title']='Synthetic clone-only studio fixture'
                        draftrow=await studio.save(cur,doc['id'],user,0,0,doc)
                        h=studio.digest(doc)
                        await studio.event(cur,doc['id'],user,'preview',detail={'body_hash':h,'draft_version':1,'base_version':1})
                        published=await studio.decide(cur,doc['id'],user,1,'publish','Synthetic clone fixture only; rolled back',1,None,h)
                        assert (await studio.published(cur,doc['id']))['body']==doc
                        await studio.decide(cur,doc['id'],user,2,'hold','Synthetic clone fixture only; rolled back')
                        await studio.decide(cur,doc['id'],user,3,'rollback','Synthetic clone fixture only; rolled back',revision=1)
                        await desk_games.access(cur,game,user)
                        await cur.execute('UPDATE study_desk_items SET deleted_at=clock_timestamp() WHERE id=%s',(iid,))
                        cancelled = await g.advance(cur,game,await g.clock(cur))
                        assert cancelled['state']=='cancelled'
                        await cur.execute('SELECT released_at IS NOT NULL AS freed FROM game_members WHERE room_id=%s',(rid,))
                        assert (await cur.fetchone())['freed']
                        await conn.rollback()
                        return {'chapter_seed_count':26,'studio_publish_hold_restore_rolled_back':True,'real_role':'mpsc','synthetic_atlas_binding_publish_hold_rolled_back':True,'central_calendar_share_withdrawal':True,'note_link_same_room_and_disclosure':True,'print_escaping':True,'desk_binding_and_withdrawal':True,'candidate_evidence_valid':True,'private_flag_enabled_only_in_probe':True,'consent_revoke_and_empty':True,'goal_read_write':True,
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
    report = ROOT/'reports/finna-atlas-studio-staged-20261118'; report.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='finna-atlas-studio-package-') as directory:
        package = Path(directory)
        for n in FILES:
            target = package/'api'/n; target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(ROOT/'api'/n,target)
        shutil.copy2(__file__,package/'rehearse.py')
        scope = {'candidate_sha256':{n:digest(package/'api'/n) for n in FILES},'operator_sha256':digest(package/'rehearse.py')}
        (package/'scope.json').write_text(json.dumps(scope))
        (package/'result.json').touch()
        host = 'ubuntu@152.67.31.231'
        stage = run(['ssh',host,'mktemp -d /tmp/finna-atlas-studio-stage.XXXXXX']).strip()
        assert re.fullmatch(r'/tmp/finna-atlas-studio-stage\.[A-Za-z0-9]+',stage)
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
