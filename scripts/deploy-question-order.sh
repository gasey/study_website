#!/usr/bin/env bash
# Bounded question-list release; never ship unrelated API/workshop changes.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOST=${ISM_HOST:-ubuntu@152.67.31.231}
PREIMAGE=d528469c200bd2e8e6eb917a9a6b695d2a56586ab7157246780e864fe776007b
NEXT=$(sha256sum "$ROOT/api/app/routers/questions.py" | cut -d' ' -f1)
STAGE=$(ssh "$HOST" 'mktemp -d /tmp/ism-question-order.XXXXXX')
rsync -az -e ssh "$ROOT/api/app/routers/questions.py" "$HOST:$STAGE/questions.py"
ssh "$HOST" bash -s -- "$STAGE" "$PREIMAGE" "$NEXT" <<'REMOTE'
set -euo pipefail
stage=$1; preimage=$2; next=$3
current=$(sudo sha256sum /srv/api/app/routers/questions.py | cut -d' ' -f1)
if [[ "$current" != "$preimage" && "$current" != "$next" ]]; then
  echo 'Question router changed since review; release stopped before installation.' >&2
  exit 1
fi
[[ $(sha256sum "$stage/questions.py" | cut -d' ' -f1) == "$next" ]]
PYTHONPYCACHEPREFIX="$stage/pycache" /srv/api/.venv/bin/python -m py_compile "$stage/questions.py"
sudo cp /srv/api/app/routers/questions.py "$stage/before.py"
rollback() {
  if [[ $(sudo sha256sum /srv/api/app/routers/questions.py | cut -d' ' -f1) == "$next" ]]; then
    sudo cp "$stage/before.py" /srv/api/app/routers/questions.py
    sudo systemctl restart ism-api
  fi
}
trap rollback ERR
sudo install -m 644 "$stage/questions.py" /srv/api/app/routers/questions.py
sudo systemctl restart ism-api
healthy=false
for attempt in $(seq 1 15); do
  if curl -fsS --max-time 5 https://study.hawayu.in/api/health; then healthy=true; break; fi
  sleep 2
done
[[ "$healthy" == true ]]
curl -fsSL --max-time 15 -o /dev/null https://family.hawayu.in
trap - ERR
echo "Question-order API healthy; rollback copy: $stage/before.py"
REMOTE
