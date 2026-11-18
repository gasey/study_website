#!/usr/bin/env bash
# Bounded Stats release; existing API entry/boundary get only the Stats additions.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOST=${ISM_HOST:-ubuntu@152.67.31.231}
RELEASE_MODE=${1:-initial}
STAGE=$(mktemp -d)
trap 'rm -rf "$STAGE"' EXIT
ssh "$HOST" 'cat /srv/api/app/main.py' > "$STAGE/main-before.py"
ssh "$HOST" 'cat /srv/api/app/services/mobile_identity.py' > "$STAGE/mobile-before.py"
python3 - "$ROOT" "$STAGE" <<'PY'
from pathlib import Path
import hashlib,json,sys
root=Path(sys.argv[1]);stage=Path(sys.argv[2])
preimages={'app/main.py':'3f14db8f8d33259a813ba9d18266992f6932b2e9847936b46575dea6905e6189','app/services/mobile_identity.py':'eb6b38f61cee5916ad21826c67245f200636f0e7ced889364c12f5514b1d6e81'}
for name,src in [('app/main.py','main-before.py'),('app/services/mobile_identity.py','mobile-before.py')]:
 data=(stage/src).read_bytes()
 if hashlib.sha256(data).hexdigest()!=preimages[name]:raise SystemExit('Existing source changed: '+name)
 text=data.decode()
 if name.endswith('main.py'):text+='\nfrom .routers import stats\napp.include_router(stats.router)\napp.add_middleware(stats.StatsBodyLimit)\n'
 else:
  if text.count('READ = (')!=1:raise SystemExit('Mobile boundary marker changed')
  text=text.replace('READ = (',"READ = (\n    # Public Stats reads only; owner publication is deliberately absent.\n    r'/api/stats/(?:overview|sources|surveys(?:/[^/]+)?|metrics/[^/]+(?:/(?:releases|rankings))?)',",1)
 target=stage/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(text)
new=['app/services/stats.py','app/services/stats_catalog.py','app/services/stats_connectors.py','app/services/stats_bootstrap.py','app/routers/stats.py','app/data/stats/hdi-hdr2025.json','app/data/stats/state-health-round-iv.json','migrations/0084_stats.sql']
for name in new:
 target=stage/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((root/'api'/name).read_bytes());preimages[name]=None
for source,name in [(root/'scripts/refresh-stats.py','refresh-stats.py'),(Path('/tmp/finna-stats-initial-wdi.json'),'app/data/stats/initial-wdi.json')]:
 target=stage/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(source.read_bytes());preimages[name]=None
for name in ['ism-stats-refresh.service','ism-stats-refresh.timer']:(stage/name).write_bytes((root/'scripts/systemd'/name).read_bytes())
manifest={name:{'before':old,'after':hashlib.sha256((stage/name).read_bytes()).hexdigest()} for name,old in preimages.items()}
(stage/'manifest.json').write_text(json.dumps({'files':manifest},indent=2)+'\n')
PY
REMOTE="/tmp/finna-stats-release-$(date +%Y%m%d-%H%M%S)"
ssh "$HOST" "mkdir -m 700 '$REMOTE'"
rsync -az -e ssh "$STAGE/" "$HOST:$REMOTE/"
ssh "$HOST" "sudo python3 - '$REMOTE' '$RELEASE_MODE'" <<'PY'
import hashlib,json,os,shutil,subprocess,sys,py_compile,time
from pathlib import Path
stage=Path(sys.argv[1]);root=Path('/srv/api');manifest=json.loads((stage/'manifest.json').read_text());backup=stage/'backup'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
def sql(db,text):return subprocess.check_output(['sudo','-u','postgres','psql','-X','-q','-A','-t','-v','ON_ERROR_STOP=1','-d',db],input=text,text=True).strip()
for name,entry in manifest['files'].items():
 if sha(root/name)!=entry['before']:raise SystemExit('Preimage changed: '+name)
 if sha(stage/name)!=entry['after']:raise SystemExit('Staged hash mismatch: '+name)
 if name.endswith('.py'):py_compile.compile(str(stage/name),cfile=str(stage/(name.replace('/','_')+'.pyc')),doraise=True)
for name in ('ism-stats-refresh.service','ism-stats-refresh.timer'):
 if Path('/etc/systemd/system',name).exists():raise SystemExit('Stats scheduler already exists; needs a fresh release')
migration=(stage/'migrations/0084_stats.sql').read_text();checksum=sha(stage/'migrations/0084_stats.sql')[:16]
fingerprint="SELECT count(*)||':'||md5(string_agg(id,',' ORDER BY id)) FROM canonical_questions;"
exists=sql('mpsc',"SELECT to_regclass('public.stats_releases') IS NOT NULL;")=='t'
if exists:
 if len(sys.argv)<3 or sys.argv[2]!='resume':raise SystemExit('Stats schema exists. An audited resume is required.')
 if sql('mpsc',"SELECT checksum FROM schema_migrations WHERE version='0084_stats';")!=checksum:raise SystemExit('Applied Stats migration checksum changed')
 original=Path('/tmp/finna-stats-release-20261115-223632')
 if not (original/'clone-restore.log').exists() or sha(original/'migrations/0084_stats.sql')[:16]!=checksum:raise SystemExit('Original rehearsal evidence missing')
 manifest['rehearsal']={'completed_in':'/tmp/finna-stats-release-20261115-223632','note':'Initial clone rehearsal passed; source rollback followed a libpq environment mismatch. Same additive migration retained; no repeat DDL.'}
else:
 clone='ism_stats_rehearsal_'+str(int(time.time()))
 subprocess.run(['sudo','-u','postgres','createdb',clone],check=True)
 try:
  with (stage/'clone-restore.log').open('w') as log:
   dump=subprocess.Popen(['sudo','-u','postgres','pg_dump','--no-owner','--no-privileges','mpsc'],stdout=subprocess.PIPE)
   restore=subprocess.run(['sudo','-u','postgres','psql','-X','-q','-v','ON_ERROR_STOP=1','-d',clone],stdin=dump.stdout,stdout=log,stderr=log)
   dump.stdout.close();dump.wait()
   if dump.returncode or restore.returncode:raise RuntimeError('Clone restore failed; see private restore log')
  before=sql(clone,fingerprint);sql(clone,migration);after=sql(clone,fingerprint)
  if before!=after:raise RuntimeError('Bank identity changed in rehearsal')
  sql(clone,"SET ROLE mpsc; INSERT INTO stats_import_runs(metric_id,status) VALUES('rehearsal','running'); SELECT count(*) FROM stats_releases;")
  manifest['rehearsal']={'bank_fingerprint_before':before,'bank_fingerprint_after':after,'runtime_grants_checked':True}
 finally:subprocess.run(['sudo','-u','postgres','dropdb','--force',clone],check=True)
 print('Fresh dump-clone migration rehearsal passed.',flush=True)
 ledger="INSERT INTO schema_migrations(version,checksum) VALUES('0084_stats','"+checksum+"');\nCOMMIT;"
 if not migration.rstrip().endswith('COMMIT;'):raise RuntimeError('Migration transaction marker changed')
 sql('mpsc',migration.rstrip()[:-7]+ledger)
production_before=sql('mpsc',fingerprint)
manifest['migration']={'version':'0084_stats','checksum':checksum}
for name,entry in manifest['files'].items():
 if entry['before'] is not None:
  dest=backup/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(root/name,dest)
installed=False
try:
 installed=True
 for name in manifest['files']:
  dest=root/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(stage/name,dest);os.chmod(dest,0o644)
 subprocess.run(['/srv/api/.venv/bin/python','-c',"from app.main import app; import requests; assert any(r.path=='/api/stats/overview' for r in app.routes)"],cwd=root,env={**os.environ,'PYTHONPATH':str(root),'PYTHONPYCACHEPREFIX':str(stage/'cache')},check=True)
 subprocess.run(['systemctl','restart','ism-api'],check=True)
 for url in ['https://study.hawayu.in/api/health','https://family.hawayu.in']:
  subprocess.run(['curl','--retry','8','--retry-connrefused','--retry-delay','2','-fsSL','--max-time','15','-o','/dev/null',url],check=True)
 result=subprocess.check_output(['systemd-run','--quiet','--wait','--collect','--pipe','--uid=www-data','--property=EnvironmentFile=/etc/mpsc/db.env','--property=WorkingDirectory=/srv/api','/srv/api/.venv/bin/python','/srv/api/refresh-stats.py','--initial-bundle','/srv/api/app/data/stats/initial-wdi.json','--bootstrap'],text=True)
 manifest['initial_imports']=json.loads(result.strip().splitlines()[-1])
 if any(x['status']!='published' for x in manifest['initial_imports']):raise RuntimeError('Initial imports did not publish')
 for name in ('ism-stats-refresh.service','ism-stats-refresh.timer'):
  shutil.copyfile(stage/name,Path('/etc/systemd/system',name));os.chmod(Path('/etc/systemd/system',name),0o644)
 subprocess.run(['systemctl','daemon-reload'],check=True)
 subprocess.run(['systemctl','enable','--now','ism-stats-refresh.timer'],check=True)
 if sql('mpsc',fingerprint)!=production_before:raise RuntimeError('Bank identity fingerprint changed')
 for name,entry in manifest['files'].items():
  if sha(root/name)!=entry['after']:raise RuntimeError('Installed hash changed: '+name)
except BaseException:
 subprocess.run(['systemctl','disable','--now','ism-stats-refresh.timer'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 if installed:
  for name,entry in manifest['files'].items():
   if entry['before'] is None:(root/name).unlink(missing_ok=True)
   else:shutil.copy2(backup/name,root/name)
  subprocess.run(['systemctl','restart','ism-api'],check=True)
 # The additive Stats tables/immutable receipts are retained for recovery.
 raise
manifest['bank_fingerprint_after']=production_before;manifest['both_sites_healthy']=True;manifest['timer_enabled']=True
(stage/'receipt.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Stats API, nine initial statistical releases and daily timer installed.',flush=True)
print('Rollback source files: '+str(backup),flush=True)
PY
mkdir -p "$ROOT/reports/stats-release-20261115"
scp -q "$HOST:$REMOTE/receipt.json" "$ROOT/reports/stats-release-20261115/receipt.json"
