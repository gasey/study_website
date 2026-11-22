#!/usr/bin/env python3
"""Rehearse only migration0123 on a fresh, disposable production dump clone."""
from pathlib import Path
from uuid import uuid4
import hashlib,json,re,shlex,shutil,subprocess,sys,tempfile,time

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/'reports/finna-game-eligibility-20261120'
MIGRATION='0123_game_audience_marker.sql'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def run(args,**kwargs):
    result=subprocess.run(args,capture_output=True,text=True,**kwargs)
    if result.returncode:raise RuntimeError(result.stderr[-4000:])
    return result.stdout

def remote(stage):
    import os,psycopg
    from psycopg import sql
    os.chdir('/')
    scope=json.loads((stage/'scope.json').read_text())
    assert sha(stage/'rehearsal.py')==scope['operator_sha256']
    assert sha(stage/MIGRATION)==scope['migration_sha256']
    assert shutil.disk_usage('/var/lib/postgresql').free>8*1024**3
    admin=psycopg.connect('dbname=postgres',autocommit=True)
    name='finna_game_age_'+uuid4().hex[:12];created=False
    def fingerprint(conn,definitions):
        result={}
        for table,columns in definitions:
            digest=hashlib.sha256();count=0
            query=sql.SQL('SELECT md5(ROW({})::text) AS h FROM {} ORDER BY h').format(
                sql.SQL(',').join(map(sql.Identifier,columns)),sql.Identifier(table))
            with conn.cursor(name='game_fp_'+uuid4().hex) as cur:
                cur.execute(query)
                for row in cur:digest.update(row[0].encode());count+=1
            result[table]={'count':count,'sha256':digest.hexdigest()}
        return result
    def definitions(conn):
        return conn.execute("SELECT table_name,array_agg(column_name::text ORDER BY ordinal_position) FROM information_schema.columns WHERE table_schema='public' AND table_name IN(SELECT tablename FROM pg_tables WHERE schemaname='public') GROUP BY table_name ORDER BY table_name").fetchall()
    try:
        with tempfile.TemporaryDirectory(prefix='finna-game-age-clone-') as directory:
            dump=Path(directory)/'production.dump'
            with dump.open('wb') as output:
                subprocess.run(['pg_dump','-Fc','-Z1','--no-owner','mpsc'],stdout=output,check=True,timeout=600)
            admin.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(name)));created=True
            subprocess.run(['pg_restore','--exit-on-error','--no-owner','-d',name,str(dump)],capture_output=True,check=True,timeout=600)
            with psycopg.connect('dbname='+name) as conn:
                original=definitions(conn);before=fingerprint(conn,original)
                indexes=conn.execute("SELECT indexname,indexdef FROM pg_indexes WHERE schemaname='public' ORDER BY indexname").fetchall()
                conn.commit()
                started=time.perf_counter();conn.execute((stage/MIGRATION).read_text())
                conn.commit();elapsed=round((time.perf_counter()-started)*1000,3)
                assert original==definitions(conn)
                assert before==fingerprint(conn,original),'Original data changed'
                after=conn.execute("SELECT indexname,indexdef FROM pg_indexes WHERE schemaname='public' ORDER BY indexname").fetchall()
                added=[r for r in after if r not in indexes]
                assert len(added)==1 and added[0][0]=='game_audience_marker_once'
                assert all(r in after for r in indexes),'An existing index changed'
                index=conn.execute("SELECT indisvalid,indisunique,pg_get_expr(indpred,indrelid) FROM pg_index WHERE indexrelid='game_audience_marker_once'::regclass").fetchone()
                assert index[0:2]==(True,True) and 'audience_access_ended' in index[2]
                # Real production data may contain no markers. Generic-plan
                # selection is exercised in the separate populated SQL fixture.
                conn.execute('SET LOCAL ROLE mpsc');conn.execute('SET LOCAL plan_cache_mode=force_generic_plan')
                conn.execute("PREPARE marker_check(text,text) AS SELECT 1 FROM game_events WHERE room_id=$1 AND actor_id=$2 AND action='audience_access_ended'")
                assert conn.execute("EXECUTE marker_check('rehearsal-absent','rehearsal-absent')").fetchall()==[]
    finally:
        if created:admin.execute(sql.SQL('DROP DATABASE {} WITH (FORCE)').format(sql.Identifier(name)))
        assert not admin.execute('SELECT 1 FROM pg_database WHERE datname=%s',(name,)).fetchone()
        admin.close()
    return {'migration':MIGRATION,'migration_sha256':scope['migration_sha256'],
      'operator_sha256':scope['operator_sha256'],'fresh_production_dump':True,
      'existing_tables_checked':len(before),'original_columns_and_values_identical':True,
      'before':before,'migration_ms':elapsed,'new_index':added[0][1],
      'index_valid_and_unique':True,'existing_indexes_preserved':True,
      'application_role_prepared_check':True,'clone_and_dump_removed':True,
      'production_writes':False,'production_migration_applied':False,'workers_started':False}

def main():
    if len(sys.argv)==3 and sys.argv[1]=='--remote':
        result=remote(Path(sys.argv[2]));print(json.dumps(result));return
    assert len(sys.argv)==1
    assert not (REPORT/'validation.json').exists(),'Frozen report'
    assert not (REPORT/'migration-rehearsal.json').exists(),'Use a new rehearsal target'
    with tempfile.TemporaryDirectory(prefix='finna-game-age-package-') as directory:
        package=Path(directory)
        shutil.copy2(__file__,package/'rehearsal.py')
        shutil.copy2(ROOT/'api/migrations'/MIGRATION,package/MIGRATION)
        scope={'operator_sha256':sha(package/'rehearsal.py'),'migration_sha256':sha(package/MIGRATION)}
        (package/'scope.json').write_text(json.dumps(scope))
        host='ubuntu@152.67.31.231'
        stage=run(['ssh',host,'mktemp -d /tmp/finna-game-age-stage.XXXXXX']).strip()
        assert re.fullmatch(r'/tmp/finna-game-age-stage\.[A-Za-z0-9]+',stage)
        (REPORT/'remote-stage.json').write_text(json.dumps({'stage':stage,**scope},indent=2)+'\n')
        timed_out=False
        try:
            run(['rsync','-az',str(package)+'/',host+':'+stage+'/'])
            run(['ssh',host,'sudo chown -R postgres:postgres '+shlex.quote(stage)])
            receipt=json.loads(run(['ssh',host,'sudo -u postgres /srv/api/.venv/bin/python '+shlex.quote(stage+'/rehearsal.py')+' --remote '+shlex.quote(stage)],timeout=1800))
            (REPORT/'migration-rehearsal.json').write_text(json.dumps(receipt,indent=2)+'\n')
            print(json.dumps({k:v for k,v in receipt.items() if k!='before'}))
        except subprocess.TimeoutExpired:
            timed_out=True
            raise RuntimeError('Remote run timed out; retain exact private stage for inspection')
        finally:
            # A completed SSH process has already run the clone's finally block.
            # Only this exact private stage is eligible for filesystem cleanup.
            cleanup="import re,shutil; p="+repr(stage)+"; assert re.fullmatch(r'/tmp/finna-game-age-stage\\.[A-Za-z0-9]+',p); shutil.rmtree(p)"
            if not timed_out:run(['ssh',host,'sudo python3 -c '+shlex.quote(cleanup)])
        (REPORT/'remote-stage-cleanup.json').write_text(json.dumps({'exact_owned_stage_removed':stage})+'\n')

if __name__=='__main__':main()
