#!/usr/bin/env bash
# Initial bounded release. Frozen entry-point preimage prevents stale replays.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOST=${ISM_HOST:-ubuntu@152.67.31.231}
STAGE=$(mktemp -d)
trap 'rm -rf "$STAGE"' EXIT
ssh "$HOST" 'cat /srv/api/app/main.py' > "$STAGE/main-before.py"
python3 - "$ROOT" "$STAGE" <<'PY'
from pathlib import Path
import hashlib,json,sys
root,stage=map(Path,sys.argv[1:]);before=(stage/'main-before.py').read_bytes()
expected='f2e30fe1261e8f1b01fe3f7df75c9bf776b9db589a858c6d95d7d2920b609a3d'
if hashlib.sha256(before).hexdigest()!=expected:raise SystemExit('API entry point changed; prepare a fresh reviewed release')
names=['app/services/youtube_current_affairs.py','app/routers/youtube_current_affairs.py','migrations/0085_youtube_current_affairs.sql']
files={'app/main.py':{'before':expected}}
for name in names:
 dest=stage/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((root/'api'/name).read_bytes());files[name]={'before':None}
main=stage/'app/main.py';main.write_text(before.decode()+'\nfrom .routers import youtube_current_affairs\napp.include_router(youtube_current_affairs.router)\napp.add_middleware(youtube_current_affairs.YouTubeBodyLimit)\n')
for src,name in [('youtube-current-affairs.py','youtube-current-affairs.py'),('youtube-current-affairs-requirements.txt','youtube-current-affairs-requirements.txt')]:
 (stage/name).write_bytes((root/'scripts'/src).read_bytes());files[name]={'before':None}
for name in files:files[name]['after']=hashlib.sha256((stage/name).read_bytes()).hexdigest()
for name in ['ism-youtube-current-affairs.service','ism-youtube-current-affairs.timer']:(stage/name).write_bytes((root/'scripts/systemd'/name).read_bytes())
# Binary was downloaded using the official v2 installer's npm package and verified
# against its SHA512 integrity field. Never install the desktop x64 binary on ARM.
arm=Path('/tmp/finna-opencode-arm64');receipt=json.loads((arm/'receipt.json').read_text())
if receipt['version']!='2.0.32' or hashlib.sha256((arm/'opencode').read_bytes()).hexdigest()!=receipt['binary_sha256']:raise SystemExit('Missing verified ARM binary')
(stage/'opencode').write_bytes((arm/'opencode').read_bytes())
(stage/'manifest.json').write_text(json.dumps({'files':files,'opencode':receipt},indent=2)+'\n')
PY
REMOTE="/tmp/finna-youtube-release-$(date +%Y%m%d-%H%M%S)"
ssh "$HOST" "mkdir -m 700 '$REMOTE'"
rsync -az -e ssh "$STAGE/" "$HOST:$REMOTE/"
ssh "$HOST" "sudo python3 - '$REMOTE'" <<'PY'
import hashlib,json,os,py_compile,shutil,subprocess,sys,time
from pathlib import Path
stage=Path(sys.argv[1]);root=Path('/srv/api');manifest=json.loads((stage/'manifest.json').read_text());backup=stage/'backup'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
def sql(db,query):return subprocess.check_output(['sudo','-u','postgres','psql','-X','-q','-A','-t','-v','ON_ERROR_STOP=1','-d',db],input=query,text=True).strip()
for name,entry in manifest['files'].items():
 if sha(root/name)!=entry['before']:raise SystemExit('Source preimage changed: '+name)
 if sha(stage/name)!=entry['after']:raise SystemExit('Staged hash mismatch: '+name)
 if name.endswith('.py'):py_compile.compile(str(stage/name),cfile=str(stage/(name.replace('/','_')+'.pyc')),doraise=True)
units=['ism-youtube-current-affairs.service','ism-youtube-current-affairs.timer'];envfile=Path('/etc/mpsc/youtube-current-affairs.env');binary=Path('/opt/finna-opencode/2.0.32/opencode')
if envfile.exists() or binary.exists() or any(Path('/etc/systemd/system',n).exists() for n in units):raise SystemExit('Existing automation installation requires a new bounded update')
if sha(stage/'opencode')!=manifest['opencode']['binary_sha256']:raise SystemExit('OpenCode binary hash changed')
if sql('mpsc',"SELECT to_regclass('ca_youtube_videos') IS NOT NULL;")=='t':raise SystemExit('Schema exists; do not replay this initial migration')
fingerprint="SELECT count(*)||':'||md5(string_agg(md5(row(id,type,question,options,answer_text,answer_source,answer_key_ref)::text),',' ORDER BY id)) FROM canonical_questions;"
migration=(stage/'migrations/0085_youtube_current_affairs.sql').read_text();checksum=sha(stage/'migrations/0085_youtube_current_affairs.sql')[:16]
clone='ism_youtube_rehearsal_'+str(int(time.time()));subprocess.run(['sudo','-u','postgres','createdb',clone],check=True)
try:
 with (stage/'clone-restore.log').open('w') as log:
  dump=subprocess.Popen(['sudo','-u','postgres','pg_dump','--no-owner','--no-privileges','mpsc'],stdout=subprocess.PIPE)
  restore=subprocess.run(['sudo','-u','postgres','psql','-X','-q','-v','ON_ERROR_STOP=1','-d',clone],stdin=dump.stdout,stdout=log,stderr=log);dump.stdout.close();dump.wait()
  if dump.returncode or restore.returncode:raise RuntimeError('Disposable production clone failed to restore')
 before=sql(clone,fingerprint);sql(clone,migration);after=sql(clone,fingerprint)
 if before!=after:raise RuntimeError('Question/answer fingerprint changed during rehearsal')
 sql(clone,"SET ROLE mpsc; SELECT count(*) FROM ca_youtube_videos; SELECT count(*) FROM ca_youtube_transcripts;")
 grants=sql(clone,"SELECT has_table_privilege('mpsc','ca_youtube_transcripts','INSERT') AND NOT has_table_privilege('mpsc','ca_youtube_transcripts','UPDATE') AND NOT has_table_privilege('mpsc','ca_youtube_events','DELETE');")
 if grants!='t':raise RuntimeError('Immutable source/audit grants failed')
 manifest['rehearsal']={'bank_fingerprint_before':before,'bank_fingerprint_after':after,'immutable_grants_checked':True}
finally:subprocess.run(['sudo','-u','postgres','dropdb','--force',clone],check=True)
print('Production dump-clone migration rehearsal passed.',flush=True)
# Install the isolated downloader, leaving existing dependencies untouched.
subprocess.run(['/srv/api/.venv/bin/python','-m','pip','install','--no-deps','-q','-r',str(stage/'youtube-current-affairs-requirements.txt')],check=True)
production_before=sql('mpsc',fingerprint)
if not migration.rstrip().endswith('COMMIT;'):raise RuntimeError('Unexpected migration transaction marker')
sql('mpsc',migration.rstrip()[:-7]+"INSERT INTO schema_migrations(version,checksum) VALUES('0085_youtube_current_affairs','"+checksum+"');\nCOMMIT;")
manifest['migration']={'version':'0085_youtube_current_affairs','checksum':checksum}
for name,entry in manifest['files'].items():
 if entry['before'] is not None:
  dest=backup/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(root/name,dest)
try:
 for name in manifest['files']:
  dest=root/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(stage/name,dest);os.chmod(dest,0o644)
 binary.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(stage/'opencode',binary);os.chmod(binary,0o755)
 version=subprocess.check_output([str(binary),'--version'],text=True).strip()
 if '2.0.32' not in version:raise RuntimeError('Unexpected OpenCode version')
 envfile.write_text('CA_LLM_PROVIDER=opencode\nCA_GENERATION_ENABLED=1\nCA_OPENCODE_MODEL=opencode/deepseek-v4.1-flash-free\nCA_OPENCODE_BIN='+str(binary)+'\nCA_DAILY_CALL_LIMIT=6\n');os.chmod(envfile,0o600)
 subprocess.run(['/srv/api/.venv/bin/python','-c',"from app.main import app; assert any(r.path=='/api/current-affairs/automation' for r in app.routes)"],cwd=root,env={**os.environ,'PYTHONPATH':str(root),'PYTHONPYCACHEPREFIX':str(stage/'cache')},check=True)
 subprocess.run(['systemctl','restart','ism-api'],check=True)
 for name in units:
  dest=Path('/etc/systemd/system',name);shutil.copyfile(stage/name,dest);os.chmod(dest,0o644)
 subprocess.run(['systemctl','daemon-reload'],check=True)
 subprocess.run(['systemctl','enable','--now','ism-youtube-current-affairs.timer'],check=True)
 for url in ['https://study.hawayu.in/api/health','https://family.hawayu.in']:
  subprocess.run(['curl','--retry','8','--retry-connrefused','--retry-delay','2','-fsSL','--max-time','15','-o','/dev/null',url],check=True)
 if sql('mpsc',fingerprint)!=production_before:raise RuntimeError('Production question/answer fingerprint changed')
 for name,entry in manifest['files'].items():
  if sha(root/name)!=entry['after']:raise RuntimeError('Installed hash changed: '+name)
except BaseException:
 subprocess.run(['systemctl','disable','--now','ism-youtube-current-affairs.timer'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 subprocess.run(['systemctl','stop','ism-youtube-current-affairs.service'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 for name,entry in manifest['files'].items():
  if entry['before'] is None:(root/name).unlink(missing_ok=True)
  else:shutil.copy2(backup/name,root/name)
 envfile.unlink(missing_ok=True)
 for name in units:Path('/etc/systemd/system',name).unlink(missing_ok=True)
 subprocess.run(['systemctl','daemon-reload'],check=True);subprocess.run(['systemctl','restart','ism-api'],check=True)
 # Additive schema and any immutable records remain for recovery; no ledger rewrite.
 raise
manifest.update({'bank_fingerprint_after':production_before,'both_sites_healthy':True,'timer_enabled':True,'private_drafts_only':True,'backup':str(backup)})
(stage/'receipt.json').write_text(json.dumps(manifest,indent=2)+'\n');print('Owner API and bounded free-model worker installed; no content published.',flush=True)
PY
mkdir -p "$ROOT/reports/youtube-current-affairs-20261115"
scp -q "$HOST:$REMOTE/receipt.json" "$ROOT/reports/youtube-current-affairs-20261115/release.json"
printf 'Release evidence: %s\n' "$REMOTE"
