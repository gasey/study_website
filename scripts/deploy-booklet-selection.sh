#!/usr/bin/env bash
# Read-only selection change; never rewrites questions or publication history.
set -euo pipefail
HOST=${ISM_HOST:-ubuntu@152.67.31.231}
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOCAL_STAGE=$(mktemp -d)
RELEASE="/tmp/booklet-selection-$(date +%s)"
trap 'rm -rf "$LOCAL_STAGE"' EXIT
ssh "$HOST" 'sudo cat /srv/api/app/services/repeat_selection.py' > "$LOCAL_STAGE/repeat_selection.py"
EXPECTED=$(sha256sum "$LOCAL_STAGE/repeat_selection.py" | cut -d ' ' -f 1)
python3 - "$LOCAL_STAGE/repeat_selection.py" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]);s=p.read_text();needle='    if len(ids)<2:return ids\n'
if 'distinct_booklet_candidates' in s:raise SystemExit(0)
if needle not in s:raise SystemExit('Selection preimage does not match')
s=s.replace(needle,needle+'    from .booklet_selection import distinct_booklet_candidates\n    ids=await distinct_booklet_candidates(cur,ids)\n    if len(ids)<2:return ids\n',1);p.write_text(s)
PY
cp "$ROOT/api/app/services/booklet_selection.py" "$LOCAL_STAGE/booklet_selection.py"
ssh "$HOST" "mkdir -p '$RELEASE'"
rsync -az "$LOCAL_STAGE/" "$HOST:$RELEASE/"
ssh "$HOST" bash -s -- "$RELEASE" "$EXPECTED" <<'REMOTE'
set -euo pipefail
stage=$1
test "$(sudo sha256sum /srv/api/app/services/repeat_selection.py | cut -d ' ' -f 1)" = "$2"
sudo cp /srv/api/app/services/repeat_selection.py "$stage/repeat-before.py"
service_existed=0
if sudo test -f /srv/api/app/services/booklet_selection.py;then service_existed=1;sudo cp /srv/api/app/services/booklet_selection.py "$stage/booklet-before.py";fi
sudo env PYTHONPYCACHEPREFIX="$stage/pycache" /srv/api/.venv/bin/python -m py_compile "$stage/repeat_selection.py" "$stage/booklet_selection.py"
success=0
restore(){
 if [ "$success" = 0 ];then
  sudo cp "$stage/repeat-before.py" /srv/api/app/services/repeat_selection.py
  if [ "$service_existed" = 1 ];then sudo cp "$stage/booklet-before.py" /srv/api/app/services/booklet_selection.py;else sudo rm -f /srv/api/app/services/booklet_selection.py;fi
  sudo systemctl restart ism-api
 fi
}
trap restore EXIT
sudo install -m 644 "$stage/booklet_selection.py" /srv/api/app/services/booklet_selection.py
sudo install -m 644 "$stage/repeat_selection.py" /srv/api/app/services/repeat_selection.py
sudo systemctl restart ism-api
healthy=0
for n in $(seq 1 20);do
 if curl -fsS --max-time 5 https://study.hawayu.in/api/health > "$stage/health.json";then healthy=1;break;fi
 sleep 1
done
test "$healthy" = 1
curl -fsS --max-time 15 https://family.hawayu.in/ > /dev/null
success=1
printf 'Booklet selection released; rollback copy: %s\n' "$stage"
REMOTE
