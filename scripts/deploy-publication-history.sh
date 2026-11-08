#!/usr/bin/env bash
# Add read-only history routes to the exact running router; preserve unrelated work.
set -euo pipefail
HOST=${ISM_HOST:-ubuntu@152.67.31.231}
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOCAL_STAGE=$(mktemp -d)
RELEASE="/tmp/publication-history-$(date +%s)"
trap 'rm -rf "$LOCAL_STAGE"' EXIT
ssh "$HOST" 'sudo cat /srv/api/app/routers/bank_workspace.py' > "$LOCAL_STAGE/bank_workspace.py"
EXPECTED=$(sha256sum "$LOCAL_STAGE/bank_workspace.py" | cut -d ' ' -f 1)
python3 - "$ROOT" "$LOCAL_STAGE" <<'PY'
from pathlib import Path
import sys
root,stage=map(Path,sys.argv[1:])
router=stage/'bank_workspace.py'
source=router.read_text()
marker="@router.get('/api/admin/bank/publication-history')"
if marker in source:raise SystemExit('History routes already installed; inspect before updating.')
fragment=(root/'api/app/routers/bank_workspace.py').read_text().split(marker,1)[1]
router.write_text(source+'\n\n'+marker+fragment)
PY
cp "$ROOT/api/app/services/publication_history.py" "$LOCAL_STAGE/publication_history.py"
ssh "$HOST" "mkdir -p '$RELEASE'"
rsync -az "$LOCAL_STAGE/" "$HOST:$RELEASE/"
ssh "$HOST" bash -s -- "$RELEASE" "$EXPECTED" <<'REMOTE'
set -euo pipefail
stage=$1
actual=$(sudo sha256sum /srv/api/app/routers/bank_workspace.py | cut -d ' ' -f 1)
test "$actual" = "$2"
sudo cp /srv/api/app/routers/bank_workspace.py "$stage/router-before.py"
service_existed=0
if sudo test -f /srv/api/app/services/publication_history.py; then service_existed=1; sudo cp /srv/api/app/services/publication_history.py "$stage/service-before.py"; fi
sudo env PYTHONPYCACHEPREFIX="$stage/pycache" /srv/api/.venv/bin/python -m py_compile "$stage/bank_workspace.py" "$stage/publication_history.py"
success=0
restore(){
 if [ "$success" = 0 ]; then
  sudo cp "$stage/router-before.py" /srv/api/app/routers/bank_workspace.py
  if [ "$service_existed" = 1 ];then sudo cp "$stage/service-before.py" /srv/api/app/services/publication_history.py;else sudo rm -f /srv/api/app/services/publication_history.py;fi
  sudo systemctl restart ism-api
 fi
}
trap restore EXIT
sudo install -m 644 "$stage/publication_history.py" /srv/api/app/services/publication_history.py
sudo install -m 644 "$stage/bank_workspace.py" /srv/api/app/routers/bank_workspace.py
sudo systemctl restart ism-api
healthy=0
for n in $(seq 1 20);do
 if curl -fsS --max-time 5 https://study.hawayu.in/api/health > "$stage/health.json";then healthy=1;break;fi
 sleep 1
done
test "$healthy" = 1
# Anonymous requests must remain blocked.
test "$(curl -s -o /dev/null -w '%{http_code}' https://study.hawayu.in/api/admin/bank/publication-history)" = 401
curl -fsS --max-time 15 https://family.hawayu.in/ > /dev/null
success=1
printf 'Publication history API released; rollback copy: %s\n' "$stage"
REMOTE
