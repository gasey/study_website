#!/usr/bin/env python3
"""Fresh production-dump clone; candidate public readers under mpsc, no migration."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'reports/finnaplan-v12-ops-20261118'
FILES=('app/main.py','app/db.py','app/routers/ops.py','app/services/ops.py')
SOURCES={n:(ROOT/'api'/n).read_text() for n in FILES}
REMOTE=r'''
import hashlib,json,os,shutil,subprocess,tempfile
from pathlib import Path
from uuid import uuid4
import psycopg
from psycopg import sql

def fingerprint(conn,table,columns):
    query=sql.SQL('SELECT md5(ROW({})::text) AS h FROM {} ORDER BY h').format(sql.SQL(',').join(map(sql.Identifier,columns)),sql.Identifier(table))
    digest=hashlib.sha256();count=0
    with conn.cursor(name='share_fp_'+uuid4().hex) as cur:
        cur.execute(query)
        for row in cur:digest.update(row[0].encode());count+=1
    return {'count':count,'sha256':digest.hexdigest()}
assert shutil.disk_usage('/var/lib/postgresql').free>8*1024**3
name='finna_ops_rehearsal_'+uuid4().hex[:12];created=False
admin=psycopg.connect('dbname=postgres',autocommit=True)
pre={n:hashlib.sha256((Path('/srv/api')/n).read_bytes()).hexdigest() if (Path('/srv/api')/n).is_file() else None for n in SOURCES}
try:
    with tempfile.TemporaryDirectory(prefix='finna-ops-private-') as directory:
        stage=Path(directory);dump=stage/'production.dump'
        with dump.open('wb') as output:subprocess.run(['pg_dump','-Fc','-Z1','--no-owner','mpsc'],stdout=output,check=True,timeout=600)
        admin.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(name)));created=True
        subprocess.run(['pg_restore','--exit-on-error','--no-owner','-d',name,str(dump)],check=True,timeout=600)
        root=stage/'api';shutil.copytree('/srv/api/app',root/'app',ignore=shutil.ignore_patterns('__pycache__'));shutil.copytree('/srv/api/migrations',root/'migrations')
        for n,s in SOURCES.items():p=root/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s)
        (stage/'verify.py').write_text(VERIFIER)
        with psycopg.connect('dbname='+name) as conn:
            defs=conn.execute("SELECT table_name,array_agg(column_name::text ORDER BY ordinal_position) FROM information_schema.columns WHERE table_schema='public' AND table_name IN(SELECT tablename FROM pg_tables WHERE schemaname='public') GROUP BY table_name ORDER BY table_name").fetchall()
            before={t:fingerprint(conn,t,c) for t,c in defs};conn.commit()
            env=os.environ.copy();env.update(FINNA_VERIFY_API=str(root),FINNA_VERIFY_DB=name)
            result=subprocess.run(['/srv/api/.venv/bin/python',str(stage/'verify.py')],env=env,text=True,capture_output=True,check=True,timeout=300)
            verification=json.loads(result.stdout)
            assert before=={t:fingerprint(conn,t,c) for t,c in defs}
        assert pre=={n:hashlib.sha256((Path('/srv/api')/n).read_bytes()).hexdigest() if (Path('/srv/api')/n).is_file() else None for n in SOURCES}
finally:
    if created:admin.execute(sql.SQL('DROP DATABASE {} WITH (FORCE)').format(sql.Identifier(name)))
    admin.close()
print(json.dumps({'existing_tables_checked':len(before),'before':before,'all_existing_rows_identical':True,'verification':verification,'candidate_sha256':{n:hashlib.sha256(s.encode()).hexdigest() for n,s in SOURCES.items()},'live_preimages':pre,'migration_changes':False,'database_writes':False,'live_files_or_services_changed':False,'clone_and_dump_removed':True}))
'''
if __name__=='__main__':
    verifier=(ROOT/'scripts/verify-finnaplan-v12-ops.py').read_text()
    result=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','ubuntu@152.67.31.231','sudo -u postgres /srv/api/.venv/bin/python -'],input=('SOURCES='+repr(SOURCES)+'\nVERIFIER='+repr(verifier)+'\n'+REMOTE).encode(),capture_output=True,timeout=1200)
    if result.returncode:raise SystemExit(result.stderr.decode(errors='replace')[-4000:])
    report=json.loads(result.stdout);(R/'read-rehearsal.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('before','live_preimages','candidate_sha256')},indent=2))
