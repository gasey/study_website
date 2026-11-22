#!/usr/bin/env python3
"""Rehearse community tier eligibility on a fresh disposable production dump."""
from pathlib import Path
from uuid import uuid4
import hashlib,json,re,shlex,shutil,subprocess,sys,tempfile,time

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/'reports/finna-tier-eligibility-20261120/resilient-rehearsal'
MIGRATIONS=('0122_privacy_requests_and_audience.sql','0124_synchronous_activity_audience.sql','0125_activity_admitted_owner.sql','0126_publication_reward_audience.sql','0127_community_tier_audience.sql','0128_community_tier_lookup_path.sql')

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def run(args,**kwargs):
    if args[0]=='ssh':args=[args[0],'-o','ConnectTimeout=20','-o','ServerAliveInterval=20','-o','ServerAliveCountMax=6',*args[1:]]
    result=subprocess.run(args,capture_output=True,text=True,**kwargs)
    if result.returncode:raise RuntimeError(result.stderr[-4000:])
    return result.stdout

def remote(stage):
    import os,psycopg
    from psycopg import sql
    os.chdir('/')
    scope=json.loads((stage/'scope.json').read_text())
    assert sha(stage/'rehearsal.py')==scope['operator_sha256']
    for name in MIGRATIONS:assert sha(stage/name)==scope['migration_sha256'][name]
    assert shutil.disk_usage('/var/lib/postgresql').free>8*1024**3
    admin=psycopg.connect('dbname=postgres',autocommit=True)
    name='finna_tier_resilient_'+uuid4().hex[:12];created=False
    def fingerprint(conn,definitions):
        result={}
        for table,columns in definitions:
            digest=hashlib.sha256();count=0
            query=sql.SQL('SELECT md5(ROW({})::text) AS h FROM {} ORDER BY h').format(
                sql.SQL(',').join(map(sql.Identifier,columns)),sql.Identifier(table))
            with conn.cursor(name='tier_fp_'+uuid4().hex) as cur:
                cur.execute(query)
                for row in cur:digest.update(row[0].encode());count+=1
            result[table]={'count':count,'sha256':digest.hexdigest()}
        return result
    def definitions(conn):
        return conn.execute("SELECT table_name,array_agg(column_name::text ORDER BY ordinal_position) FROM information_schema.columns WHERE table_schema='public' AND table_name IN(SELECT tablename FROM pg_tables WHERE schemaname='public') GROUP BY table_name ORDER BY table_name").fetchall()
    try:
        with tempfile.TemporaryDirectory(prefix='finna-tier-resilient-clone-') as directory:
            dump=Path(directory)/'production.dump'
            with dump.open('wb') as output:
                subprocess.run(['pg_dump','-Fc','-Z1','--no-owner','mpsc'],stdout=output,check=True,timeout=600)
            admin.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(name)));created=True
            subprocess.run(['pg_restore','--exit-on-error','--no-owner','-d',name,str(dump)],capture_output=True,check=True,timeout=600)
            with psycopg.connect('dbname='+name) as conn:
                original=definitions(conn);before=fingerprint(conn,original)
                indexes=conn.execute("SELECT indexname,indexdef FROM pg_indexes WHERE schemaname='public' ORDER BY indexname").fetchall()
                function_names=('community_weighted_helpful(text)','community_record_tier(text)','community_tier_change()','community_display_tier_rank(text)')
                original_functions={n:conn.execute('SELECT prosrc,proowner,proacl FROM pg_proc WHERE oid=%s::regprocedure',(n,)).fetchone() for n in function_names}
                original_guard=conn.execute("SELECT prosrc,proowner,proacl FROM pg_proc WHERE oid='community_tier_event_guard()'::regprocedure").fetchone()
                conn.commit()
                applied={}
                for migration in MIGRATIONS:
                    started=time.perf_counter();conn.execute((stage/migration).read_text());conn.commit()
                    applied[migration]=round((time.perf_counter()-started)*1000,3)
                after_definitions=dict(definitions(conn))
                assert all(after_definitions.get(table)==columns for table,columns in original)
                assert before==fingerprint(conn,original),'Original data changed'
                after=conn.execute("SELECT indexname,indexdef FROM pg_indexes WHERE schemaname='public' ORDER BY indexname").fetchall()
                assert all(row in after for row in indexes),'An existing index changed'
                new_tables=sorted(set(after_definitions)-{table for table,_ in original})
                assert new_tables==['account_audience','audience_browser_flows','audience_processing_policy','privacy_request_events','privacy_requests']
                functions={n:conn.execute('SELECT prosrc,proowner,proacl FROM pg_proc WHERE oid=%s::regprocedure',(n,)).fetchone() for n in function_names}
                tier_source=(stage/'0127_community_tier_audience.sql').read_text()
                for n in function_names[:-1]:
                    body=tier_source.split('CREATE OR REPLACE FUNCTION '+n.split('(')[0],1)[1].split('$$')[1]
                    assert functions[n][0]==body and functions[n][0]!=original_functions[n][0],n
                    assert functions[n][1:]==original_functions[n][1:],n
                assert functions[function_names[-1]]==original_functions[function_names[-1]]
                assert conn.execute("SELECT prosrc,proowner,proacl FROM pg_proc WHERE oid='community_tier_event_guard()'::regprocedure").fetchone()==original_guard
                for n in (*function_names,'community_tier_event_guard()'):
                    assert conn.execute('SELECT proconfig FROM pg_proc WHERE oid=%s::regprocedure',(n,)).fetchone()==(['search_path=pg_catalog, public, pg_temp'],),n
                assert not conn.execute("SELECT has_function_privilege('mpsc','community_record_tier(text)','EXECUTE')").fetchone()[0]
                triggers=conn.execute("SELECT tgname FROM pg_trigger WHERE starts_with(tgname,'community_tier_') AND NOT tgisinternal ORDER BY tgname").fetchall()
                assert len(triggers)==12,triggers
                assert conn.execute('SELECT enabled FROM audience_processing_policy').fetchall()==[(False,)]
                # Verify the precise postgres default privileges which our local
                # non-postgres migration runner must explicitly simulate.
                mutable=('exam_study_checkpoints','learning_checkpoints','module_learning_progress','essay_drafts')
                privileges={table:{priv:conn.execute('SELECT has_table_privilege(%s,%s,%s)',('mpsc',table,priv)).fetchone()[0]
                    for priv in ('SELECT','INSERT','UPDATE','DELETE')} for table in mutable}
                assert all(all(values.values()) for values in privileges.values()),privileges
                policy_privileges={priv:conn.execute('SELECT has_table_privilege(%s,%s,%s)',('mpsc','audience_processing_policy',priv)).fetchone()[0]
                    for priv in ('SELECT','INSERT','UPDATE','DELETE')}
                assert policy_privileges=={'SELECT':True,'INSERT':False,'UPDATE':False,'DELETE':False}
                conn.commit()
                conn.execute('SET LOCAL ROLE mpsc')
                assert conn.execute('SELECT audience_database_gate_enabled()').fetchone()==(False,)
                assert conn.execute("SELECT audience_processing_admit('rehearsal-absent')").fetchone()==(True,)
                conn.execute('SELECT record_learning_activity(-1)');conn.rollback()
                conn.execute('SET TRANSACTION READ ONLY');conn.execute('SET LOCAL ROLE mpsc')
                assert conn.execute("SELECT community_weighted_helpful('rehearsal-absent'),community_display_tier_rank('rehearsal-absent')").fetchone()==(0,0)
                conn.rollback()
                # Only the new policy row is temporarily changed in this clone.
                # It is reset to off before the final fingerprint. No cloned learner records, rewards or notices are written.
                conn.execute('UPDATE audience_processing_policy SET enabled=true')
                conn.execute('SET LOCAL ROLE mpsc')
                conn.execute("SET LOCAL finna.audience_gate_enabled='off'")
                assert conn.execute("SELECT audience_processing_admit('rehearsal-absent')").fetchone()==(False,)
                conn.rollback()
                conn.execute('UPDATE audience_processing_policy SET enabled=true');conn.commit()
                conn.execute('SET TRANSACTION READ ONLY');conn.execute('SET LOCAL ROLE mpsc')
                conn.execute("SET LOCAL finna.audience_gate_enabled='off'")
                assert conn.execute("SELECT community_weighted_helpful('rehearsal-absent'),community_display_tier_rank('rehearsal-absent')").fetchone()==(0,0)
                conn.rollback()
                conn.execute('UPDATE audience_processing_policy SET enabled=false');conn.commit()
                assert conn.execute('SELECT enabled FROM audience_processing_policy').fetchall()==[(False,)]
                assert before==fingerprint(conn,original),'Read checks changed original data'

    finally:
        if created:admin.execute(sql.SQL('DROP DATABASE {} WITH (FORCE)').format(sql.Identifier(name)))
        assert not admin.execute('SELECT 1 FROM pg_database WHERE datname=%s',(name,)).fetchone()
        admin.close()
    return {'migrations':MIGRATIONS,'migration_sha256':scope['migration_sha256'],
      'operator_sha256':scope['operator_sha256'],'fresh_production_dump':True,
      'existing_tables_checked':len(before),'original_columns_and_values_identical':True,
      'before':before,'migration_ms':applied,'new_tables':new_tables,
      'existing_indexes_preserved':True,'database_policy_default_off':True,
      'tier_functions_match_exact_migration':True,'tier_functions_owner_and_acl_preserved':True,
      'display_function_body_owner_acl_unchanged':True,'event_guard_body_owner_acl_unchanged':True,
      'explicit_public_before_temp_lookup':True,'server_owned_record_function_not_client_callable':True,
      'community_tier_triggers':len(triggers),'read_only_real_role_policy_off_and_on':True,
      'mutable_transfer_privileges':privileges,'application_policy_privileges':policy_privileges,
      'application_role_default_off_and_enabled_checks':True,'no_session_guc_bypass':True,
      'clone_and_dump_removed':True,'production_writes':False,
      'production_migration_applied':False,'workers_started':False}

def main():
    if len(sys.argv)==3 and sys.argv[1]=='--remote':
        stage=Path(sys.argv[2]);result=remote(stage)
        (stage/'completed-rehearsal.json').write_text(json.dumps(result))
        print(json.dumps(result));return
    assert len(sys.argv)==1
    REPORT.mkdir(exist_ok=False)
    assert not (REPORT/'validation.json').exists(),'Frozen report'
    assert not (REPORT/'migration-rehearsal.json').exists(),'Use a new rehearsal target'
    with tempfile.TemporaryDirectory(prefix='finna-tier-resilient-package-') as directory:
        package=Path(directory)
        shutil.copy2(__file__,package/'rehearsal.py')
        for name in MIGRATIONS:shutil.copy2(ROOT/'api/migrations'/name,package/name)
        scope={'operator_sha256':sha(package/'rehearsal.py'),'migration_sha256':{name:sha(package/name) for name in MIGRATIONS}}
        (package/'scope.json').write_text(json.dumps(scope))
        host='ubuntu@152.67.31.231'
        stage=run(['ssh',host,'mktemp -d /tmp/finna-tier-resilient-stage.XXXXXX']).strip()
        assert re.fullmatch(r'/tmp/finna-tier-resilient-stage\.[A-Za-z0-9]+',stage)
        (REPORT/'remote-stage.json').write_text(json.dumps({'stage':stage,**scope},indent=2)+'\n')
        timed_out=False;completed=False
        try:
            run(['rsync','-az',str(package)+'/',host+':'+stage+'/'])
            run(['ssh',host,'sudo chown -R postgres:postgres '+shlex.quote(stage)])
            receipt=json.loads(run(['ssh',host,'sudo -u postgres /srv/api/.venv/bin/python '+shlex.quote(stage+'/rehearsal.py')+' --remote '+shlex.quote(stage)],timeout=1800))
            completed=True
            (REPORT/'migration-rehearsal.json').write_text(json.dumps(receipt,indent=2)+'\n')
            print(json.dumps({k:v for k,v in receipt.items() if k!='before'}))
        except subprocess.TimeoutExpired:
            timed_out=True
            raise RuntimeError('Remote run timed out; retain exact private stage for inspection')
        finally:
            # A completed SSH process has already run the clone's finally block.
            # Only this exact private stage is eligible for filesystem cleanup.
            cleanup="import re,shutil; p="+repr(stage)+"; assert re.fullmatch(r'/tmp/finna-tier-resilient-stage\\.[A-Za-z0-9]+',p); shutil.rmtree(p)"
            if completed and not timed_out:run(['ssh',host,'sudo python3 -c '+shlex.quote(cleanup)])
        assert completed
        (REPORT/'remote-stage-cleanup.json').write_text(json.dumps({'exact_owned_stage_removed':stage})+'\n')

if __name__=='__main__':main()
