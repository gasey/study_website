#!/usr/bin/env bash
# Bounded mobile learner release. No bank, schema, publisher or Caddy writes.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOST=${ISM_HOST:-ubuntu@152.67.31.231}
RELEASE_MODE=${1:-initial}
RECEIPT_FILE=receipt.json
if [[ "$RELEASE_MODE" == credit ]]; then RECEIPT_FILE=credit-followup.json; fi
STAGE=$(mktemp -d)
trap 'rm -rf "$STAGE"' EXIT
python3 - "$ROOT" "$STAGE" "$RELEASE_MODE" <<'PY'
import hashlib,json,sys
from pathlib import Path
root=Path(sys.argv[1]);stage=Path(sys.argv[2])
preimages={
 'app/services/mobile_identity.py':'46bdd8147de128b9fa650904e626a240009f6218fe8e8b75ddcc63afdc48be1e',
 'app/services/review_identity.py':'1046e83446201919eb24715d3222008462a5b63f6c60b555a80413cce584875f',
 'app/routers/mobile.py':'f96169b7bc190b0f6e02b131efcf4fe3200923f734bcb50a392fca019887f547',
 'app/routers/mobile_authoring.py':None,
 'app/config.py':'ca3ccf7c7c66e8cb4b76fe952e04f4456dd0764c2e55c4ab31904f7c01116f88',
 'app/routers/billing.py':'ed2a635fd31d2bbf46ff0c45d3767407df19c5d962ac79da9961feb3a8a4d0cc',
}
if sys.argv[3]=='credit':
 preimages={'app/routers/mobile_authoring.py':'fe612f1ae8806eeab8f5abf8f9b7d9a228efef7a70791f8d09e6f71fa6e820af'}
files={}
for name,old in preimages.items():
 data=(root/'api'/name).read_bytes();target=stage/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
 files[name]={'before':old,'after':hashlib.sha256(data).hexdigest()}
(stage/'manifest.json').write_text(json.dumps({'files':files},indent=2)+'\n')
PY
REMOTE="/tmp/finna-mobile-release-$(date +%Y%m%d-%H%M%S)"
ssh "$HOST" "mkdir -m 700 '$REMOTE'"
rsync -az -e ssh "$STAGE/" "$HOST:$REMOTE/"
ssh "$HOST" "sudo python3 - '$REMOTE'" <<'PY'
import hashlib,json,os,py_compile,shutil,subprocess,sys
from pathlib import Path
stage=Path(sys.argv[1]);root=Path('/srv/api');manifest=json.loads((stage/'manifest.json').read_text());backup=stage/'backup'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
for name,entry in manifest['files'].items():
 if sha(root/name)!=entry['before']:raise SystemExit('Preimage changed; stopped before modifying '+name)
 if sha(stage/name)!=entry['after']:raise SystemExit('Staged hash mismatch: '+name)
 py_compile.compile(str(stage/name),cfile=str(stage/(name.replace('/','_')+'.pyc')),doraise=True)
for name,entry in manifest['files'].items():
 if entry['before'] is not None:
  target=backup/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(root/name,target)
installed=False
try:
 installed=True
 for name in manifest['files']:
  shutil.copyfile(stage/name,root/name);os.chmod(root/name,0o644)
 subprocess.run(['/srv/api/.venv/bin/python','-c',"from app.main import app; assert any(r.path == '/api/mobile/learning' for r in app.routes)"],cwd=root,env={**os.environ,'PYTHONPATH':str(root),'PYTHONPYCACHEPREFIX':str(stage/'cache')},check=True)
 subprocess.run(['systemctl','restart','ism-api'],check=True)
 for url in ['https://study.hawayu.in/api/health','https://family.hawayu.in']:
  subprocess.run(['curl','--retry','8','--retry-connrefused','--retry-delay','2','-fsS','--max-time','10','-o','/dev/null',url],check=True)
 config=json.loads(subprocess.check_output(['curl','-fsS','--max-time','10','https://study.hawayu.in/api/billing/config'],text=True))
 if config['enabled']:raise RuntimeError('Deferred checkout must remain disabled')
 for name,entry in manifest['files'].items():
  if sha(root/name)!=entry['after']:raise RuntimeError('Installed hash mismatch: '+name)
except BaseException:
 if installed:
  for name,entry in manifest['files'].items():
   if entry['before'] is None:(root/name).unlink(missing_ok=True)
   else:shutil.copy2(backup/name,root/name)
  subprocess.run(['systemctl','restart','ism-api'],check=True)
 raise
manifest['both_sites_healthy']=True;manifest['schema_changed']=False;manifest['checkout_activation_requested']=False
(stage/'receipt.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(f"Installed and verified {len(manifest['files'])} mobile/billing files. Both sites healthy. Checkout activation stays disabled by configuration.")
print('Rollback files: '+str(backup))
PY
mkdir -p "$ROOT/reports/mobile-release-20261115"
scp -q "$HOST:$REMOTE/receipt.json" "$ROOT/reports/mobile-release-20261115/$RECEIPT_FILE"
