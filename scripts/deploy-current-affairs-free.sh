#!/usr/bin/env bash
# Initial 0086 release. Exact preimages; never replay over a newer deployment.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOST=${ISM_HOST:-ubuntu@152.67.31.231}
STAGE=$(mktemp -d)
trap 'rm -rf "$STAGE"' EXIT
python3 - "$ROOT" "$STAGE" <<'PY'
from pathlib import Path
import hashlib,json,sys
root,stage=map(Path,sys.argv[1:]);preimages={
'app/services/youtube_current_affairs.py':'79d99bce571419eac4264617da75f3c24fb9da4af77717b8405da2bc5ae1e741',
'app/routers/youtube_current_affairs.py':'aab6ca32586428f8012169a8148d1b51fdbe2f432bb45cc64b548f8daf8eaa92',
'youtube-current-affairs.py':'6e39a769fc348b4ecfae9b42b661d8592b87d679699898c33816183b84dc9ae4',
'app/services/current_affairs_sources.py':None,'app/services/current_affairs_providers.py':None,'migrations/0086_current_affairs_free_sources.sql':None}
files={}
for name,before in preimages.items():
 source=root/'scripts/youtube-current-affairs.py' if name=='youtube-current-affairs.py' else root/'api'/name
 dest=stage/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(source.read_bytes());files[name]={'before':before,'after':hashlib.sha256(dest.read_bytes()).hexdigest()}
(stage/'manifest.json').write_text(json.dumps({'files':files},indent=2)+'\n')
PY
REMOTE="/tmp/finna-free-current-affairs-$(date +%Y%m%d-%H%M%S)"
ssh "$HOST" "mkdir -m 700 '$REMOTE'"
rsync -az -e ssh "$STAGE/" "$HOST:$REMOTE/"
ssh "$HOST" "sudo python3 - '$REMOTE'" <<'PY'
import hashlib,json,os,py_compile,shutil,subprocess,sys,time
from pathlib import Path
stage=Path(sys.argv[1]);root=Path('/srv/api');manifest=json.loads((stage/'manifest.json').read_text());backup=stage/'backup';envfile=Path('/etc/mpsc/youtube-current-affairs.env')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
def sql(db,query):return subprocess.check_output(['sudo','-u','postgres','psql','-X','-q','-A','-t','-v','ON_ERROR_STOP=1','-d',db],input=query,text=True).strip()
for name,item in manifest['files'].items():
 if sha(root/name)!=item['before']:raise SystemExit('Source preimage changed: '+name)
 if sha(stage/name)!=item['after']:raise SystemExit('Staged bytes changed: '+name)
 if name.endswith('.py'):py_compile.compile(str(stage/name),cfile=str(stage/(name.replace('/','_')+'.pyc')),doraise=True)
if not envfile.exists():raise SystemExit('Initial current-affairs private configuration is missing')
if sql('mpsc',"SELECT to_regclass('ca_source_items') IS NOT NULL;")=='t':raise SystemExit('0086 schema already exists; prepare an audited fresh update')
if subprocess.call(['systemctl','is-active','--quiet','ism-youtube-current-affairs.service'])==0:raise SystemExit('Current-affairs worker active; wait for it to finish before replacing code')
fingerprint="SELECT count(*)||':'||md5(string_agg(md5(row(id,type,question,options,answer_text,answer_source,answer_key_ref)::text),',' ORDER BY id)) FROM canonical_questions;"
migration=(stage/'migrations/0086_current_affairs_free_sources.sql').read_text();checksum=sha(stage/'migrations/0086_current_affairs_free_sources.sql')[:16]
clone='ism_free_ca_rehearsal_'+str(int(time.time()));subprocess.run(['sudo','-u','postgres','createdb',clone],check=True)
try:
 with (stage/'clone-restore.log').open('w') as log:
  dump=subprocess.Popen(['sudo','-u','postgres','pg_dump','--no-owner','--no-privileges','mpsc'],stdout=subprocess.PIPE)
  restore=subprocess.run(['sudo','-u','postgres','psql','-X','-q','-v','ON_ERROR_STOP=1','-d',clone],stdin=dump.stdout,stdout=log,stderr=log);dump.stdout.close();dump.wait()
  if dump.returncode or restore.returncode:raise RuntimeError('Disposable database restore failed')
 before=sql(clone,fingerprint);sql(clone,migration);after=sql(clone,fingerprint)
 if before!=after:raise RuntimeError('Question/answer fingerprint changed during rehearsal')
 if sql(clone,"SELECT has_table_privilege('mpsc','ca_source_revisions','INSERT') AND NOT has_table_privilege('mpsc','ca_source_revisions','UPDATE') AND NOT has_table_privilege('mpsc','ca_source_events','DELETE');")!='t':raise RuntimeError('Immutable source/audit grants failed')
 sql(clone,"SET ROLE mpsc; SELECT count(*) FROM ca_source_feeds; SELECT count(*) FROM ca_source_items;")
 manifest['rehearsal']={'bank_before':before,'bank_after':after,'immutable_grants_checked':True}
finally:subprocess.run(['sudo','-u','postgres','dropdb','--force',clone],check=True)
print('0086 dump-clone rehearsal passed.',flush=True)
subprocess.run(['systemctl','stop','ism-youtube-current-affairs.timer'],check=True)
try:
 if subprocess.call(['systemctl','is-active','--quiet','ism-youtube-current-affairs.service'])==0:raise RuntimeError('Worker began during rehearsal; installation deferred')
 for name,item in manifest['files'].items():
  if sha(root/name)!=item['before']:raise RuntimeError('Source changed during rehearsal: '+name)
 production_before=sql('mpsc',fingerprint)
 if not migration.rstrip().endswith('COMMIT;'):raise RuntimeError('Migration transaction marker changed')
 sql('mpsc',migration.rstrip()[:-7]+"INSERT INTO schema_migrations(version,checksum) VALUES('0086_current_affairs_free_sources','"+checksum+"');\nCOMMIT;")
 backup.mkdir(exist_ok=True);shutil.copy2(envfile,backup/'provider.env')
 for name,item in manifest['files'].items():
  if item['before'] is not None:
   dest=backup/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(root/name,dest)
 installed=True
 try:
  for name in manifest['files']:
   dest=root/name;dest.parent.mkdir(parents=True,exist_ok=True);temporary=dest.with_name(dest.name+'.next');shutil.copyfile(stage/name,temporary);os.chmod(temporary,0o644);os.replace(temporary,dest)
  # User chose to configure keys later: collection on, new generation/captions paused.
  # Preserve any private key lines and unrelated settings without printing them.
  updates={'CA_LLM_PROVIDER':'gemini','CA_GENERATION_ENABLED':'0','CA_GEMINI_MODEL':'gemini-3.8-flash','CA_GEMINI_FREE_PROJECT':'0','CA_CAPTION_PROVIDER':'supadata','CA_VIDEO_INPUT':'captions','CA_SOURCE_GENERATION_ENABLED':'0','CA_SUPADATA_MONTHLY_LIMIT':'90'}
  lines=[line for line in envfile.read_text().splitlines() if line.split('=',1)[0].strip() not in updates]
  envfile.write_text('\n'.join(lines+[k+'='+v for k,v in updates.items()])+'\n');os.chmod(envfile,0o600)
  subprocess.run(['/srv/api/.venv/bin/python','-c',"from app.main import app; assert any(r.path=='/api/current-affairs/automation/sources' for r in app.routes)"],cwd=root,env={**os.environ,'PYTHONPATH':str(root),'PYTHONPYCACHEPREFIX':str(stage/'cache')},check=True)
  subprocess.run(['systemctl','restart','ism-api'],check=True)
  for url in ['https://study.hawayu.in/api/health','https://family.hawayu.in']:
   subprocess.run(['curl','--retry','8','--retry-connrefused','--retry-delay','2','-fsSL','--max-time','15','-o','/dev/null',url],check=True)
  if sql('mpsc',fingerprint)!=production_before:raise RuntimeError('Production question/answer fingerprint changed')
  for name,item in manifest['files'].items():
   if sha(root/name)!=item['after']:raise RuntimeError('Installed source hash changed: '+name)
 except BaseException:
  for name,item in manifest['files'].items():
   if item['before'] is None:(root/name).unlink(missing_ok=True)
   else:shutil.copy2(backup/name,root/name)
  shutil.copy2(backup/'provider.env',envfile);subprocess.run(['systemctl','restart','ism-api'],check=True)
  # Retain additive DDL and immutable evidence/checksum on source rollback.
  raise
 manifest.update({'migration':'0086_current_affairs_free_sources','checksum':checksum,'bank_fingerprint_after':production_before,'both_sites_healthy':True,'generation_enabled':False,'supadata_without_key':True,'backup':str(backup)})
 (stage/'receipt.json').write_text(json.dumps(manifest,indent=2)+'\n');print('Free-only integrations installed; AI and native-caption provider await keys.',flush=True)
finally:subprocess.run(['systemctl','start','ism-youtube-current-affairs.timer'],check=True)
PY
mkdir -p "$ROOT/reports/current-affairs-free-release-20261116"
scp -q "$HOST:$REMOTE/receipt.json" "$ROOT/reports/current-affairs-free-release-20261116/release.json"
printf 'Release stage: %s\n' "$REMOTE"
