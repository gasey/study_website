#!/usr/bin/env python3
"""Read-only count-query parity/timing on a fresh production dump clone."""
from pathlib import Path
from uuid import uuid4
import hashlib,json,re,shlex,shutil,subprocess,sys,tempfile,time
ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/'reports/finna-empty-pins-20261120'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def run(args,**kwargs):
    result=subprocess.run(args,capture_output=True,text=True,**kwargs)
    if result.returncode:raise RuntimeError(result.stderr[-4000:])
    return result.stdout

def remote(stage):
    import os,psycopg
    from psycopg import sql
    from psycopg.rows import dict_row
    os.chdir('/')
    scope=json.loads((stage/'scope.json').read_text())
    assert sha(stage/'benchmark.py')==scope['operator_sha256']
    assert sha(stage/'queries.json')==scope['queries_sha256']
    queries=json.loads((stage/'queries.json').read_text())
    assert shutil.disk_usage('/var/lib/postgresql').free>8*1024**3
    admin=psycopg.connect('dbname=postgres',autocommit=True);name='finna_pins_'+uuid4().hex[:12];created=False
    timings=[];checks=[];plans=[]
    def fingerprint(conn,definitions):
        result={}
        for table,columns in definitions:
            digest=hashlib.sha256();count=0
            query=sql.SQL('SELECT md5(ROW({})::text) AS h FROM {} ORDER BY h').format(sql.SQL(',').join(map(sql.Identifier,columns)),sql.Identifier(table))
            with conn.cursor(name='counts_fp_'+uuid4().hex) as cur:
                cur.execute(query)
                for row in cur:digest.update(row[0].encode());count+=1
            result[table]={'count':count,'sha256':digest.hexdigest()}
        return result
    try:
        with tempfile.TemporaryDirectory(prefix='finna-pins-clone-') as directory:
            dump=Path(directory)/'workflow.dump'
            with dump.open('wb') as output:subprocess.run(['pg_dump','-Fc','-Z1','--no-owner','mpsc'],stdout=output,check=True,timeout=600)
            admin.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(name)));created=True
            subprocess.run(['pg_restore','--exit-on-error','--no-owner','-d',name,str(dump)],capture_output=True,check=True,timeout=600)
            # pg_dump excludes planner statistics. Settle them explicitly instead
            # of timing restore defaults or racing automatic ANALYZE in the clone.
            with psycopg.connect('dbname='+name,autocommit=True) as prepared:
                prepared.execute('ANALYZE')
            with psycopg.connect('dbname='+name) as root:
                definitions=root.execute("SELECT table_name,array_agg(column_name::text ORDER BY ordinal_position) FROM information_schema.columns WHERE table_schema='public' AND table_name IN(SELECT tablename FROM pg_tables WHERE schemaname='public') GROUP BY table_name ORDER BY table_name").fetchall()
                before=fingerprint(root,definitions)
                collections=root.execute("SELECT id,live_version FROM collections WHERE visibility='public' ORDER BY id").fetchall()
                with psycopg.connect('dbname='+name,row_factory=dict_row,prepare_threshold=None) as conn:
                    conn.execute('SET ROLE mpsc');conn.execute('SET TRANSACTION READ ONLY');conn.execute("SET LOCAL statement_timeout='120s'")
                    for jit in ('off',):
                        conn.execute('SET LOCAL jit='+jit)
                        for scope_name,variants in queries.items():
                            for kind in ('sections','detail'):
                                cases=[(None,None),*collections] if kind=='sections' else collections
                                for collection,version in cases:
                                    outputs={}
                                    for variant,typed in (list(variants.items()) if len(checks)%2==0 else list(reversed(variants.items()))):
                                        settings=typed.get('_settings',{}).get(kind,{})
                                        assert set(settings)<=set(['join_collapse_limit','collection_ids']) and settings.get('join_collapse_limit',8) in (1,8)
                                        chosen=1 if kind=='detail' and collection=='subject-wise-practice' else 8
                                        conn.execute('SET LOCAL join_collapse_limit='+str(chosen))
                                        query=typed[kind]
                                        params={'collection_id':collection}
                                        started=time.perf_counter();rows=conn.execute(query,params).fetchall();elapsed=round((time.perf_counter()-started)*1000,3)
                                        outputs[variant]=sorted(json.dumps(r,sort_keys=True,default=str) for r in rows)
                                        plan=conn.execute('EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) '+query,params).fetchone()['QUERY PLAN'][0]
                                        if kind=='detail' and collection=='subject-wise-practice' and scope_name=='mizoram-recruitment' and jit=='off':plans.append({'variant':variant,'plan':plan})
                                        timings.append({'scope':scope_name,'kind':kind,'collection':collection,'variant':variant,'join_collapse_limit':chosen,'jit':jit,'rows':len(rows),'elapsed_ms':elapsed,'planning_ms':plan['Planning Time'],'execution_ms':plan['Execution Time'],'cost':plan['Plan']['Total Cost'],'jit_used':'JIT' in plan,'shared_hit_blocks':plan['Plan'].get('Shared Hit Blocks'),'temp_written_blocks':plan['Plan'].get('Temp Written Blocks')})
                                    (stage/'progress.json').write_text(json.dumps({'completed_runs':len(timings),'last':timings[-1]}))
                                    assert all(value==outputs['before'] for value in outputs.values()),(kind,collection,scope_name,jit)
                                    checks.append({'scope':scope_name,'kind':kind,'collection':collection,'jit':jit,'all_variants_identical':True})
                    # Warm repeated samples alternate the baseline/candidate order.
                    # Re-read every public collection, both source scopes and both readers.
                    conn.execute('SET LOCAL jit=off')
                    for repeat in range(4):
                        for scope_name,variants in queries.items():
                            for kind in ('sections','detail'):
                                for collection,version in ([(None,None),*collections] if kind=='sections' else collections):
                                    conn.execute('SET LOCAL join_collapse_limit='+str(1 if kind=='detail' and collection=='subject-wise-practice' else 8))
                                    outputs={}
                                    for variant in (list(variants) if repeat%2==0 else list(reversed(variants))):
                                        query=variants[variant][kind]
                                        params={'collection_id':collection}
                                        started=time.perf_counter();rows=conn.execute(query,params).fetchall();elapsed=round((time.perf_counter()-started)*1000,3)
                                        outputs[variant]=sorted(json.dumps(r,sort_keys=True,default=str) for r in rows)
                                        timings.append({'scope':scope_name,'kind':kind,'collection':collection,'variant':variant,'jit':'off','rows':len(rows),'elapsed_ms':elapsed,'repeat':repeat})
                                    assert all(value==outputs['before'] for value in outputs.values()),(kind,collection,scope_name,repeat)
                                    checks.append({'scope':scope_name,'kind':kind,'collection':collection,'repeat':repeat,'all_variants_identical':True})
                                    (stage/'progress.json').write_text(json.dumps({'completed_runs':len(timings),'last':timings[-1]}))
                assert before==fingerprint(root,definitions),'Original data changed'
    finally:
        if created:admin.execute(sql.SQL('DROP DATABASE {} WITH (FORCE)').format(sql.Identifier(name)))
        admin.close()
    return {'driver_auto_prepare':False,'read_only':True,'role':'mpsc','clone_analyzed_before_timing':True,'existing_tables_checked':len(before),'all_original_values_identical':True,'before':before,'checks':checks,'plans':plans,'timings':timings,'query_sha256':scope['queries_sha256'],'operator_sha256':scope['operator_sha256'],'production_writes':False,'workers_started':False,'clone_and_dump_removed':True}

def main():
    if len(sys.argv)==3 and sys.argv[1]=='--remote':
        stage=Path(sys.argv[2])
        try:
            receipt=remote(stage);(stage/'result.json').write_text(json.dumps(receipt)+'\n');print('Clone parity, timing and preservation complete.')
        except Exception:
            (stage/'failed').touch();raise
        return
    assert len(sys.argv)==1
    with tempfile.TemporaryDirectory(prefix='finna-pins-package-') as directory:
        package=Path(directory);shutil.copy2(__file__,package/'benchmark.py');shutil.copy2(REPORT/'queries.json',package/'queries.json')
        (package/'scope.json').write_text(json.dumps({'operator_sha256':sha(package/'benchmark.py'),'queries_sha256':sha(package/'queries.json')}));(package/'result.json').touch()
        host='ubuntu@152.67.31.231';stage=run(['ssh',host,'mktemp -d /tmp/finna-pins-stage.XXXXXX']).strip();assert re.fullmatch(r'/tmp/finna-pins-stage\.[A-Za-z0-9]+',stage)
        (REPORT/'remote-stage.json').write_text(json.dumps({'stage':stage})+'\n')
        try:
            run(['rsync','-az',str(package)+'/',host+':'+stage+'/']);run(['ssh',host,'chmod -R a+rX '+shlex.quote(stage)+' && chmod a+w '+shlex.quote(stage)+' '+shlex.quote(stage+'/result.json')])
            run(['ssh',host,'nohup sudo -u postgres /srv/api/.venv/bin/python '+shlex.quote(stage+'/benchmark.py')+' --remote '+shlex.quote(stage)+' > '+shlex.quote(stage+'/remote.log')+' 2>&1 < /dev/null &'])
            for _ in range(100):
                done=run(['ssh',host,'if test -s '+shlex.quote(stage+'/result.json')+'; then echo complete; elif test -e '+shlex.quote(stage+'/failed')+'; then echo failed; fi']).strip()
                if done:
                    if done=='failed':raise RuntimeError(run(['ssh',host,'cat '+shlex.quote(stage+'/remote.log')]))
                    receipt=json.loads(run(['ssh',host,'cat '+shlex.quote(stage+'/result.json')]))
                    (REPORT/'benchmark.json').write_text(json.dumps(receipt,indent=2)+'\n')
                    print(json.dumps({k:v for k,v in receipt.items() if k not in ('before','timings','checks','plans')}));break
                time.sleep(15)
            else:raise RuntimeError('Timed out; inspect exact recorded stage before cleanup')
        finally:
            # Completed/failing remote operators remove their clone in finally.
            # A timeout must retain its private stage for diagnosis, not race it.
            if 'done' in locals() and done:run(['ssh',host,'sudo rm -rf -- '+shlex.quote(stage)])
if __name__=='__main__':main()
