#!/usr/bin/env python3
"""Read-only count-query parity/timing on a fresh production dump clone."""
from pathlib import Path
from uuid import uuid4
import hashlib,json,re,shlex,shutil,subprocess,sys,tempfile,time
ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/'reports/finna-section-count-flat-20261119'
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
    admin=psycopg.connect('dbname=postgres',autocommit=True);name='finna_counts_'+uuid4().hex[:12];created=False
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
        with tempfile.TemporaryDirectory(prefix='finna-counts-clone-') as directory:
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
                    baseline={}
                    conn.execute('SET LOCAL jit=off')
                    for scope_name,variants in queries.items():
                        for collection in (None,*[c[0] for c in collections]):
                            for variant,typed in variants.items():
                                query=typed['sections'];params={'collection_id':collection} if collection else {}
                                if collection:query=query.replace("WHERE c.visibility='public' AND", "WHERE c.visibility='public' AND c.id=%(collection_id)s AND",1)
                                started=time.perf_counter();rows=conn.execute(query,params).fetchall();elapsed=round((time.perf_counter()-started)*1000,3)
                                output=sorted(json.dumps(row,sort_keys=True,default=str) for row in rows);key=(scope_name,collection)
                                if variant=='before':baseline[key]=output
                                else:assert output==baseline[key],(variant,key)
                                plan=conn.execute('EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) '+query,params).fetchone()['QUERY PLAN'][0]
                                timings.append({'scope':scope_name,'collection':collection,'variant':variant,'elapsed_ms':elapsed,'execution_ms':plan['Execution Time'],'planning_ms':plan['Planning Time'],'rows':len(rows),'shared_hit_blocks':plan['Plan'].get('Shared Hit Blocks'),'temp_written_blocks':plan['Plan'].get('Temp Written Blocks')})
                                plans.append({'scope':scope_name,'collection':collection,'variant':variant,'plan':plan})
                                checks.append({'scope':scope_name,'collection':collection,'variant':variant,'identical':True})
                                (stage/'progress.json').write_text(json.dumps({'last':timings[-1],'completed':len(timings)}))
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
    with tempfile.TemporaryDirectory(prefix='finna-counts-package-') as directory:
        package=Path(directory);shutil.copy2(__file__,package/'benchmark.py');shutil.copy2(REPORT/'queries.json',package/'queries.json')
        (package/'scope.json').write_text(json.dumps({'operator_sha256':sha(package/'benchmark.py'),'queries_sha256':sha(package/'queries.json')}));(package/'result.json').touch()
        host='ubuntu@152.67.31.231';stage=run(['ssh',host,'mktemp -d /tmp/finna-counts-stage.XXXXXX']).strip();assert re.fullmatch(r'/tmp/finna-counts-stage\.[A-Za-z0-9]+',stage)
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
