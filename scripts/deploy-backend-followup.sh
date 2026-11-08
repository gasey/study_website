#!/usr/bin/env bash
# Two-file follow-up, exact preimages, no settings/schema/content mutation.
set -euo pipefail
HOST=${ISM_HOST:-ubuntu@152.67.31.231}
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RELEASE="backend-followup-$(date +%s)"
STAGE=$(mktemp -d)
trap 'rm -rf "$STAGE"' EXIT
cp "$ROOT/scripts/releases/backend-followup-20261107.json" "$STAGE/expected.json"
cp "$ROOT/api/app/services/bank_publication.py" "$ROOT/scripts/bank-review-worker.py" "$STAGE/"
rsync -az "$STAGE/" "$HOST:/tmp/$RELEASE/"
ssh "$HOST" bash -s -- "$RELEASE" <<'REMOTE'
set -euo pipefail
stage="/tmp/$1"
mkdir -p "$stage/backup"
chmod 700 "$stage/backup"
python3 - "$stage" <<'PY'
import json,subprocess,sys
from pathlib import Path
stage=Path(sys.argv[1]);expected=json.loads((stage/'expected.json').read_text())
for target,value in expected.items():
 if subprocess.check_output(['sudo','sha256sum',target],text=True).split()[0]!=value:raise SystemExit('Deployed preimage changed: '+target)
(stage/'file-list').write_text('\n'.join(p.lstrip('/') for p in expected)+'\n')
PY
sudo env PYTHONPYCACHEPREFIX="$stage/pycache" /srv/api/.venv/bin/python -m py_compile "$stage/bank_publication.py" "$stage/bank-review-worker.py"
timer_active=0
if sudo systemctl is-active --quiet ism-oracle-bank-review.timer;then timer_active=1;fi
sudo systemctl stop ism-oracle-bank-review.timer
installed=0
success=0
restore(){
 status=$?
 if [ "$installed" = 1 ] && [ "$success" = 0 ];then
  sudo tar -xf "$stage/backup/files.tar" -C /
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
if sudo systemctl is-active --quiet ism-oracle-bank-review.service;then echo 'Publisher active; deferred before files changed.' >&2;exit 1;fi
sudo tar -cf "$stage/backup/files.tar" -C / -T "$stage/file-list"
installed=1
sudo install -m 644 "$stage/bank_publication.py" /srv/api/app/services/bank_publication.py
sudo install -m 644 "$stage/bank-review-worker.py" /srv/study/workshop/india-study-map-app/scripts/bank-review-worker.py
sudo systemctl restart ism-api
healthy=0
for n in $(seq 1 20);do
 if curl -fsS --max-time 5 https://study.hawayu.in/api/health > "$stage/health.json";then healthy=1;break;fi
 sleep 1
done
test "$healthy" = 1
(cd /srv/api && sudo -u postgres env PUBLICATION_SERIAL_QUEUE=false ISM_DB_TRANSPORT=local /srv/api/.venv/bin/python /srv/api/promote-publication-queue.py --database mpsc) > "$stage/helper-smoke.json"
python3 - "$stage/helper-smoke.json" <<'PY'
import json,sys
assert json.load(open(sys.argv[1]))['state']=='disabled'
PY
curl -fsS --max-time 15 https://family.hawayu.in/ > /dev/null
success=1
echo "Follow-up release complete; rollback: $stage"
REMOTE
