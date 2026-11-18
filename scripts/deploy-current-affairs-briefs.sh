#!/usr/bin/env bash
# Frozen 0088 source/page/brief release; never replay over a newer deployment.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOST=${ISM_HOST:-ubuntu@152.67.31.231}
STAGE=$(mktemp -d)
trap 'rm -rf "$STAGE"' EXIT
python3 - "$ROOT" "$STAGE" <<'PY'
from pathlib import Path
import hashlib,json,sys
root,stage=map(Path,sys.argv[1:]);before={
 'app/services/youtube_current_affairs.py':'3a665fb0455a7419354621a605160e8dbf53a4a76fd7acd7377477e2ba59a382',
 'app/services/current_affairs_sources.py':'f4cce5118221d8e2a8c39df9ecb46321454e8b3974913b2d7c80fa6fa0f2a419',
 'app/routers/youtube_current_affairs.py':'88f5f9e510bc4ca1615c0fcdffd2e21b41c640c8051e86d284ed8a53153a7a34',
 'youtube-current-affairs.py':'460dcdfb3ac6e780da09991fe6dbd0649ae08a4f0197d2fc25bfb4f95b116473',
 'app/services/current_affairs_pages.py':None,'app/services/current_affairs_briefs.py':None,'migrations/0088_current_affairs_briefs.sql':None}
files={}
for name,digest in before.items():
 source=root/'scripts'/name if name=='youtube-current-affairs.py' else root/'api'/name
 target=stage/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(source.read_bytes());files[name]={'before':digest,'after':hashlib.sha256(target.read_bytes()).hexdigest()}
(stage/'manifest.json').write_text(json.dumps({'files':files},indent=2)+'\n')
PY
REMOTE="/tmp/finna-ca-briefs-$(date +%Y%m%d-%H%M%S)"
ssh "$HOST" "mkdir -m 700 '$REMOTE'"
rsync -az -e ssh "$STAGE/" "$HOST:$REMOTE/"
ssh "$HOST" "sudo python3 - '$REMOTE'" <<'PY'
import hashlib,json,os,py_compile,shutil,subprocess,sys,time
from pathlib import Path
stage=Path(sys.argv[1]);root=Path('/srv/api');manifest=json.loads((stage/'manifest.json').read_text());backup=stage/'backup'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None
def sql(db,query):return subprocess.check_output(['sudo','-u','postgres','psql','-X','-qAt','-v','ON_ERROR_STOP=1','-d',db],input=query,text=True).strip()
fingerprint="SELECT count(*)||':'||md5(string_agg(md5(row(id,type,question,options,answer_text,answer_source,answer_key_ref)::text),',' ORDER BY id)) FROM canonical_questions;"
permissions="SELECT NOT has_table_privilege('mpsc','ca_brief_inputs','UPDATE') AND NOT has_table_privilege('mpsc','ca_brief_inputs','DELETE') AND NOT has_table_privilege('mpsc','ca_brief_inputs','TRUNCATE') AND has_table_privilege('mpsc','ca_brief_inputs','INSERT') AND has_column_privilege('mpsc','ca_brief_drafts','status','UPDATE') AND NOT has_column_privilege('mpsc','ca_brief_drafts','payload','UPDATE');"
for name,item in manifest['files'].items():
 if sha(root/name)!=item['before'] or sha(stage/name)!=item['after']:raise SystemExit('Frozen source preimage changed: '+name)
 if name.endswith('.py'):py_compile.compile(str(stage/name),cfile=str(stage/(name.replace('/','_')+'.pyc')),doraise=True)
if sql('mpsc',"SELECT EXISTS(SELECT 1 FROM schema_migrations WHERE version='0088_current_affairs_briefs');")=='t':raise SystemExit('0088 already applied; prepare a fresh bounded update')
if subprocess.call(['systemctl','is-active','--quiet','ism-youtube-current-affairs.service'])==0:raise SystemExit('Current-affairs worker is active; wait before replacing it')
migration=(stage/'migrations/0088_current_affairs_briefs.sql').read_text();checksum=sha(stage/'migrations/0088_current_affairs_briefs.sql')[:16]
clone='ism_ca_brief_rehearsal_'+str(int(time.time()));subprocess.run(['sudo','-u','postgres','createdb',clone],check=True)
try:
 with (stage/'clone-restore.log').open('w') as log:
  dump=subprocess.Popen(['sudo','-u','postgres','pg_dump','--no-owner','mpsc'],stdout=subprocess.PIPE)
  restore=subprocess.run(['sudo','-u','postgres','psql','-X','-q','-v','ON_ERROR_STOP=1','-d',clone],stdin=dump.stdout,stdout=log,stderr=log);dump.stdout.close();dump.wait()
  if dump.returncode or restore.returncode:raise RuntimeError('ACL-preserving clone restore failed')
 before=sql(clone,fingerprint);sql(clone,migration)
 if sql(clone,fingerprint)!=before or sql(clone,permissions)!='t':raise RuntimeError('Clone integrity or runtime grants failed')
 sql(clone,"SET ROLE mpsc; INSERT INTO ca_briefs(id,cadence,period_start,period_end,current_hash) VALUES('synthetic-clone','daily',current_date,current_date,'synthetic'); INSERT INTO ca_brief_inputs(brief_id,content_hash,payload) VALUES('synthetic-clone','synthetic','{}');")
 manifest['rehearsal']={'acl_preserved':True,'bank_before':before,'bank_after':sql(clone,fingerprint),'runtime_append_only':True}
finally:subprocess.run(['sudo','-u','postgres','dropdb','--force',clone],check=True)
print('0088 ACL-preserving clone rehearsal passed.',flush=True)
subprocess.run(['systemctl','stop','ism-youtube-current-affairs.timer'],check=True)
try:
 if subprocess.call(['systemctl','is-active','--quiet','ism-youtube-current-affairs.service'])==0:raise RuntimeError('Worker started during rehearsal; defer installation')
 for name,item in manifest['files'].items():
  if sha(root/name)!=item['before']:raise RuntimeError('Source changed during rehearsal: '+name)
 backup.mkdir(exist_ok=True)
 for name,item in manifest['files'].items():
  if item['before'] is not None:
   target=backup/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(root/name,target)
 production_before=sql('mpsc',fingerprint)
 if not migration.rstrip().endswith('COMMIT;'):raise RuntimeError('Migration transaction marker changed')
 sql('mpsc',migration.rstrip()[:-7]+"INSERT INTO schema_migrations(version,checksum) VALUES('0088_current_affairs_briefs','"+checksum+"');\nCOMMIT;")
 try:
  for name in manifest['files']:
   target=root/name;target.parent.mkdir(parents=True,exist_ok=True);temporary=target.with_name(target.name+'.next');shutil.copyfile(stage/name,temporary);os.chmod(temporary,0o644);os.replace(temporary,target)
  subprocess.run(['/srv/api/.venv/bin/python','-c',"from app.main import app; assert any(r.path=='/api/current-affairs/automation/briefs' for r in app.routes)"],cwd=root,env={**os.environ,'PYTHONPATH':str(root),'PYTHONPYCACHEPREFIX':str(stage/'cache')},check=True)
  subprocess.run(['systemctl','restart','ism-api'],check=True)
  for url in ['https://study.hawayu.in/api/health','https://family.hawayu.in']:
   subprocess.run(['curl','--retry','8','--retry-connrefused','--retry-delay','2','-fsSL','--max-time','15','-o','/dev/null',url],check=True)
  if sql('mpsc',permissions)!='t':raise RuntimeError('Production runtime grants failed')
  for name,item in manifest['files'].items():
   if sha(root/name)!=item['after']:raise RuntimeError('Installed source hash changed: '+name)
 except BaseException:
  # Keep the compatible fixed-feed mapping/pages adapter after additive DDL,
  # so the old router can still list new (paused) feed rows on source rollback.
  sql('mpsc',"UPDATE ca_source_feeds SET enabled=false WHERE id IN ('pib-releases','mizoram-dipr');")
  for name,item in manifest['files'].items():
   if name in {'app/services/current_affairs_sources.py','app/services/current_affairs_pages.py'} or name.startswith('migrations/'):continue
   if item['before'] is None:(root/name).unlink(missing_ok=True)
   else:shutil.copy2(backup/name,root/name)
  subprocess.run(['systemctl','restart','ism-api'],check=True);raise
 after=sql('mpsc',fingerprint)
 if after!=production_before:raise RuntimeError('Bank fingerprint changed; investigate concurrent bank work before claiming preservation')
 manifest.update({'migration':'0088_current_affairs_briefs','checksum':checksum,'bank_before':production_before,'bank_after':after,'both_sites_healthy':True,'backup':str(backup),'provider_config_unchanged':True})
 (stage/'receipt.json').write_text(json.dumps(manifest,indent=2)+'\n');print('Official-page and daily/weekly brief integrations installed.',flush=True)
finally:subprocess.run(['systemctl','start','ism-youtube-current-affairs.timer'],check=True)
PY
mkdir -p "$ROOT/reports/current-affairs-plan-completion-20261116"
scp -q "$HOST:$REMOTE/receipt.json" "$ROOT/reports/current-affairs-plan-completion-20261116/release.json"
printf 'Release stage: %s\n' "$REMOTE"
