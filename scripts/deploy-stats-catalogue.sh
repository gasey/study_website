#!/usr/bin/env bash
# Bounded follow-up: Survey catalogue/edition checks and source-link parsing.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOST=${ISM_HOST:-ubuntu@152.67.31.231}
RELEASE_MODE=${1:-catalogue}
RECEIPT_FILE=catalogue-followup.json
if [[ "$RELEASE_MODE" == read ]]; then RECEIPT_FILE=read-followup.json; fi
if [[ "$RELEASE_MODE" == retry ]]; then RECEIPT_FILE=refresh-followup.json; fi
STAGE=$(mktemp -d)
trap 'rm -rf "$STAGE"' EXIT
python3 - "$ROOT" "$STAGE" "$RELEASE_MODE" <<'PY'
import hashlib,json,sys
from pathlib import Path
root=Path(sys.argv[1]);stage=Path(sys.argv[2]);prior=json.loads((root/'reports/stats-release-20261115/receipt.json').read_text())['files'];files={}
names=['app/services/stats_catalog.py','app/services/stats_connectors.py','app/routers/stats.py','app/data/stats/survey-2025-26-tables.json']
if sys.argv[3] in {'read','retry'}:
 prior.update(json.loads((root/'reports/stats-release-20261115/catalogue-followup.json').read_text())['files'])
 names=['app/services/stats.py','app/routers/stats.py'] if sys.argv[3]=='read' else ['app/services/stats_connectors.py']
for name in names:
 data=(root/'api'/name).read_bytes();p=stage/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
 files[name]={'before':prior[name]['after'] if name in prior else None,'after':hashlib.sha256(data).hexdigest()}
(stage/'manifest.json').write_text(json.dumps({'files':files},indent=2)+'\n')
PY
REMOTE="/tmp/finna-stats-catalogue-$(date +%Y%m%d-%H%M%S)"
ssh "$HOST" "mkdir -m 700 '$REMOTE'"
rsync -az -e ssh "$STAGE/" "$HOST:$REMOTE/"
ssh "$HOST" "sudo python3 - '$REMOTE'" <<'PY'
import hashlib,json,os,shutil,subprocess,sys,py_compile
from pathlib import Path
stage=Path(sys.argv[1]);root=Path('/srv/api');manifest=json.loads((stage/'manifest.json').read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
for name,item in manifest['files'].items():
 if sha(root/name)!=item['before'] or sha(stage/name)!=item['after']:raise SystemExit('Changed preimage or stage: '+name)
 if name.endswith('.py'):py_compile.compile(str(stage/name),cfile=str(stage/(name.replace('/','_')+'.pyc')),doraise=True)
for name,item in manifest['files'].items():
 if item['before']:
  p=stage/'backup'/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(root/name,p)
try:
 for name in manifest['files']:
  p=root/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(stage/name,p);os.chmod(p,0o644)
 subprocess.run(['/srv/api/.venv/bin/python','-c',"from app.main import app; from app.services.stats_catalog import SURVEYS; assert len(SURVEYS[0]['tables'])==107"],cwd=root,env={**os.environ,'PYTHONPATH':str(root),'PYTHONPYCACHEPREFIX':str(stage/'cache')},check=True)
 subprocess.run(['systemctl','restart','ism-api'],check=True)
 for url in ['https://study.hawayu.in/api/health','https://family.hawayu.in']:
  subprocess.run(['curl','--retry','8','--retry-connrefused','--retry-delay','2','-fsSL','--max-time','15','-o','/dev/null',url],check=True)
 for name,item in manifest['files'].items():
  if sha(root/name)!=item['after']:raise RuntimeError('Installed hash mismatch')
except BaseException:
 for name,item in manifest['files'].items():
  if item['before']:shutil.copy2(stage/'backup'/name,root/name)
  else:(root/name).unlink(missing_ok=True)
 subprocess.run(['systemctl','restart','ism-api'],check=True)
 raise
manifest['both_sites_healthy']=True;manifest['schema_changed']=False
(stage/'receipt.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Stats Survey catalogue and source checks installed; both sites healthy.')
PY
scp -q "$HOST:$REMOTE/receipt.json" "$ROOT/reports/stats-release-20261115/$RECEIPT_FILE"
