#!/usr/bin/env bash
# Bounded workflow release; guarded bank store and immutable history remain intact.
set -euo pipefail
HOST=${ISM_HOST:-ubuntu@152.67.31.231}
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RELEASE="backend-audit-$(date +%s)"
STAGE=$(mktemp -d)
trap 'rm -rf "$STAGE"' EXIT
cp "$ROOT/scripts/releases/backend-audit-20261107.json" "$STAGE/expected.json"
python3 - "$ROOT" "$STAGE" <<'PY'
import json,sys,shutil
from pathlib import Path
root,stage=map(Path,sys.argv[1:])
for target in json.loads((stage/'expected.json').read_text()):
 rel=target.removeprefix('/srv/api/') if target.startswith('/srv/api/') else 'scripts/bank-review-worker.py'
 source=root/'api'/rel if target.startswith('/srv/api/') else root/rel
 output=stage/'files'/target.lstrip('/');output.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,output)
shutil.copyfile(root/'scripts/promote-publication-queue.py',stage/'files/srv/api/promote-publication-queue.py')
PY
rsync -az "$STAGE/" "$HOST:/tmp/$RELEASE/"
ssh "$HOST" bash -s -- "$RELEASE" <<'REMOTE'
set -euo pipefail
stage="/tmp/$1"
backup="$stage/backup"
api_policy=/etc/systemd/system/ism-api.service.d/publication-queue.conf
worker_policy=/etc/systemd/system/ism-oracle-bank-review.service.d/publication-queue.conf
mkdir -p "$backup"
chmod 700 "$backup"
python3 - "$stage" <<'PY'
import json,subprocess,sys
from pathlib import Path
stage=Path(sys.argv[1]);expected=json.loads((stage/'expected.json').read_text())
for target,value in expected.items():
 actual=subprocess.check_output(['sudo','sha256sum',target],text=True).split()[0]
 if actual!=value:raise SystemExit('Deployed preimage changed: '+target)
(stage/'existing-files.txt').write_text('\n'.join(target.lstrip('/') for target in expected)+'\n')
PY
sudo test ! -e /srv/api/promote-publication-queue.py
sudo env PYTHONPYCACHEPREFIX="$stage/pycache" /srv/api/.venv/bin/python -m compileall -q "$stage/files"
timer_active=0
if sudo systemctl is-active --quiet ism-oracle-bank-review.timer; then timer_active=1; fi
sudo systemctl stop ism-oracle-bank-review.timer
installed=0
success=0
restore(){
 status=$?
 if [ "$installed" = 1 ] && [ "$success" = 0 ]; then
  sudo tar -xf "$backup/files.tar" -C /
  sudo rm -f /srv/api/promote-publication-queue.py
  if sudo test -f "$backup/api-policy"; then sudo cp "$backup/api-policy" "$api_policy"; else sudo rm -f "$api_policy"; fi
  if sudo test -f "$backup/worker-policy"; then sudo cp "$backup/worker-policy" "$worker_policy"; else sudo rm -f "$worker_policy"; fi
  sudo systemctl daemon-reload
  sudo systemctl restart ism-api
  echo 'Restored previous API, worker and queue settings.' >&2
 fi
 if [ "$timer_active" = 1 ]; then sudo systemctl start ism-oracle-bank-review.timer; fi
 exit "$status"
}
trap restore EXIT
for n in $(seq 1 45); do
 if ! sudo systemctl is-active --quiet ism-oracle-bank-review.service; then break; fi
 sleep 1
done
if sudo systemctl is-active --quiet ism-oracle-bank-review.service; then echo 'Publisher is still active; release deferred before files changed.' >&2;exit 1;fi
sudo tar -cf "$backup/files.tar" -C / -T "$stage/existing-files.txt"
if sudo test -f "$api_policy"; then sudo cp "$api_policy" "$backup/api-policy"; fi
if sudo test -f "$worker_policy"; then sudo cp "$worker_policy" "$backup/worker-policy"; fi
installed=1
python3 - "$stage" <<'PYINSTALL'
import json,subprocess,sys
from pathlib import Path
stage=Path(sys.argv[1]);targets=[*json.loads((stage/'expected.json').read_text()),'/srv/api/promote-publication-queue.py']
for target in targets:
 subprocess.run(['sudo','install','-m','644',str(stage/'files'/target.lstrip('/')),target],check=True)
PYINSTALL
printf '%s\n' '[Service]' 'Environment=PUBLICATION_SERIAL_QUEUE=true' > "$stage/queue.conf"
sudo mkdir -p /etc/systemd/system/ism-api.service.d /etc/systemd/system/ism-oracle-bank-review.service.d
sudo install -m 600 "$stage/queue.conf" "$api_policy"
sudo install -m 600 "$stage/queue.conf" "$worker_policy"
sudo systemctl daemon-reload
sudo systemctl restart ism-api
healthy=0
for n in $(seq 1 20); do
 if curl -fsS --max-time 5 https://study.hawayu.in/api/health > "$stage/health.json"; then healthy=1;break;fi
 sleep 1
done
test "$healthy" = 1
# Import/DB-access smoke as the actual helper user; disabled mode performs no writes.
(cd /srv/api && sudo -u postgres env PUBLICATION_SERIAL_QUEUE=false ISM_DB_TRANSPORT=local /srv/api/.venv/bin/python /srv/api/promote-publication-queue.py --database mpsc) > "$stage/helper-smoke.json"
python3 - "$stage/helper-smoke.json" <<'PY'
import json,sys
assert json.load(open(sys.argv[1]))['state']=='disabled'
PY
curl -fsS --max-time 15 https://family.hawayu.in/ > /dev/null
success=1
echo "Backend queue audit release completed; rollback: $stage"
REMOTE
