#!/usr/bin/env bash
# Narrow read-only overview release; no content, account or schema mutation.
set -euo pipefail
HOST=${ISM_HOST:-ubuntu@152.67.31.231}
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAGE="/tmp/bank-overview-$(date +%s)"
EXPECTED=$(sha256sum "$ROOT/reports/bank-overview-20261107/preimages/bank_workspace.py" | cut -d ' ' -f 1)
ssh "$HOST" "mkdir -p '$STAGE'"
rsync -az "$ROOT/api/app/routers/bank_workspace.py" "$ROOT/api/app/services/bank_overview.py" "$HOST:$STAGE/"
ssh "$HOST" bash -s -- "$STAGE" "$EXPECTED" <<'REMOTE'
set -euo pipefail
stage=$1
actual=$(sudo sha256sum /srv/api/app/routers/bank_workspace.py | cut -d ' ' -f 1)
test "$actual" = "$2"
sudo test ! -e /srv/api/app/services/bank_overview.py
sudo cp /srv/api/app/routers/bank_workspace.py "$stage/router-before.py"
sudo env PYTHONPYCACHEPREFIX="$stage/pycache" /srv/api/.venv/bin/python -m py_compile "$stage/bank_workspace.py" "$stage/bank_overview.py"
success=0
restore(){
 if [ "$success" = 0 ]; then
  sudo cp "$stage/router-before.py" /srv/api/app/routers/bank_workspace.py
  sudo rm -f /srv/api/app/services/bank_overview.py
  sudo systemctl restart ism-api
 fi
}
trap restore EXIT
sudo install -m 644 "$stage/bank_workspace.py" /srv/api/app/routers/bank_workspace.py
sudo install -m 644 "$stage/bank_overview.py" /srv/api/app/services/bank_overview.py
sudo systemctl restart ism-api
for n in $(seq 1 20); do
 if curl -fsS --max-time 5 https://study.hawayu.in/api/health > "$stage/health.json"; then success=1; break; fi
 sleep 1
done
test "$success" = 1
curl -fsS --max-time 15 https://family.hawayu.in/ > /dev/null
echo "Overview API released; backup: $stage"
REMOTE
