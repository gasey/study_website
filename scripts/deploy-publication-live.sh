#!/usr/bin/env bash
# Commit-only wakeup of the existing guarded publisher; no bank/schema changes.
set -euo pipefail
HOST=${ISM_HOST:-ubuntu@152.67.31.231}
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RELEASE="publication-live-$(date +%s)"
STAGE=$(mktemp -d)
trap 'rm -rf "$STAGE"' EXIT
cp "$ROOT/scripts/releases/publication-live-20261107.json" "$STAGE/expected.json"
python3 - "$ROOT" "$STAGE" <<'PY'
import json,shutil,sys
from pathlib import Path
root,stage=map(Path,sys.argv[1:])
for target in json.loads((stage/'expected.json').read_text()):
 output=stage/'files'/target.lstrip('/');output.parent.mkdir(parents=True,exist_ok=True)
 shutil.copyfile(root/'api'/target.removeprefix('/srv/api/'),output)
shutil.copyfile(root/'scripts/publication-wakeup.py',stage/'files/srv/api/publication-wakeup.py')
shutil.copyfile(root/'scripts/systemd/ism-publication-wakeup.service',stage/'wakeup.service')
PY
rsync -az "$STAGE/" "$HOST:/tmp/$RELEASE/"
ssh "$HOST" bash -s -- "$RELEASE" <<'REMOTE'
set -euo pipefail
stage="/tmp/$1"
unit=/etc/systemd/system/ism-publication-wakeup.service
script=/srv/api/publication-wakeup.py
mkdir -p "$stage/backup"
chmod 700 "$stage/backup"
python3 - "$stage" <<'PY'
import json,subprocess,sys
from pathlib import Path
stage=Path(sys.argv[1]);expected=json.loads((stage/'expected.json').read_text())
for target,value in expected.items():
 if subprocess.check_output(['sudo','sha256sum',target],text=True).split()[0]!=value:raise SystemExit('Deployed preimage changed: '+target)
(stage/'file-list').write_text('\n'.join(p.lstrip('/')for p in expected)+'\n')
PY
sudo test ! -e "$unit"
sudo test ! -e "$script"
sudo env PYTHONPYCACHEPREFIX="$stage/pycache" /srv/api/.venv/bin/python -m compileall -q "$stage/files"
timer_active=0
if sudo systemctl is-active --quiet ism-oracle-bank-review.timer;then timer_active=1;fi
sudo systemctl stop ism-oracle-bank-review.timer
installed=0
success=0
restore(){
 status=$?
 if [ "$installed" = 1 ] && [ "$success" = 0 ];then
  sudo systemctl disable --now ism-publication-wakeup.service || true
  sudo tar -xf "$stage/backup/files.tar" -C /
  sudo rm -f "$unit" "$script"
  sudo systemctl daemon-reload
  sudo systemctl restart ism-api
 fi
 if [ "$timer_active" = 1 ];then sudo systemctl start ism-oracle-bank-review.timer;fi
 exit "$status"
}
trap restore EXIT
for n in $(seq 1 45);do
 if ! sudo systemctl is-active --quiet ism-oracle-bank-review.service;then break;fi
 sleep 1
done
if sudo systemctl is-active --quiet ism-oracle-bank-review.service;then echo 'Publisher active; deferred before install.' >&2;exit 1;fi
sudo tar -cf "$stage/backup/files.tar" -C / -T "$stage/file-list"
installed=1
python3 - "$stage" <<'PY'
import json,subprocess,sys
from pathlib import Path
stage=Path(sys.argv[1]);targets=[*json.loads((stage/'expected.json').read_text()),'/srv/api/publication-wakeup.py']
for target in targets:subprocess.run(['sudo','install','-m','644',str(stage/'files'/target.lstrip('/')),target],check=True)
PY
sudo install -m 644 "$stage/wakeup.service" "$unit"
sudo systemd-analyze verify "$unit"
sudo systemctl daemon-reload
sudo systemctl restart ism-api
healthy=0
for n in $(seq 1 20);do
 if curl -fsS --max-time 5 https://study.hawayu.in/api/health > "$stage/health.json";then healthy=1;break;fi
 sleep 1
done
test "$healthy" = 1
sudo systemctl enable --now ism-publication-wakeup.service
# A committed wake signal is safe: the worker still checks the authoritative queue.
sleep 2
sudo systemctl is-active --quiet ism-publication-wakeup.service
sudo -u postgres psql -X -q -d mpsc -c "SELECT pg_notify('ism_bank_publication','');" > /dev/null
sleep 2
sudo systemctl is-active --quiet ism-publication-wakeup.service
sudo journalctl -u ism-publication-wakeup.service --since '1 minute ago' --no-pager > "$stage/listener.log"
python3 - "$stage/listener.log" <<'PYCHECK'
from pathlib import Path
import sys
assert 'Publisher wake requested' in Path(sys.argv[1]).read_text()
PYCHECK
curl -fsS --max-time 15 https://family.hawayu.in/ > /dev/null
success=1
echo "Publication wake-up release complete; rollback: $stage"
REMOTE
