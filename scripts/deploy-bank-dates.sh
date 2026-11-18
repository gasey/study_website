#!/usr/bin/env bash
# Read-only Important Dates projection; ships only the catalog router and new service.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOST=${ISM_HOST:-ubuntu@152.67.31.231}
PREIMAGE=6cd37631c4a8f496a38e1793447db1622bc1080b72dc6ea6d8ed48c49c862cee
ROUTER_PREIMAGE=7017bdbc596ed7186d7bfa135a98401100e3f54c8d0601dded1515c3930d7bad
SERVICE_PREIMAGE=76a6656ae6075f34538df232a409a6c64f79174a5687599e5627ac9e564a7878
ROUTER=$(sha256sum "$ROOT/api/app/routers/learning_catalog.py" | cut -d' ' -f1)
SERVICE=$(sha256sum "$ROOT/api/app/services/bank_dates.py" | cut -d' ' -f1)
STAGE=$(ssh "$HOST" 'mktemp -d /tmp/ism-bank-dates-release.XXXXXX')
rsync -az -e ssh "$ROOT/api/app/routers/learning_catalog.py" "$ROOT/api/app/services/bank_dates.py" "$HOST:$STAGE/"
ssh "$HOST" bash -s -- "$STAGE" "$PREIMAGE" "$ROUTER" "$SERVICE" "$SERVICE_PREIMAGE" "$ROUTER_PREIMAGE" <<'REMOTE'
set -euo pipefail
stage=$1; preimage=$2; router=$3; service=$4; service_preimage=$5; router_preimage=$6
current=$(sudo sha256sum /srv/api/app/routers/learning_catalog.py | cut -d' ' -f1)
if [[ "$current" != "$preimage" && "$current" != "$router" && "$current" != "$router_preimage" ]]; then
  echo 'Catalog router changed since review; stopped before installation.' >&2; exit 1
fi
if sudo test -f /srv/api/app/services/bank_dates.py; then
  current_service=$(sudo sha256sum /srv/api/app/services/bank_dates.py | cut -d' ' -f1)
  [[ "$current_service" == "$service" || "$current_service" == "$service_preimage" ]] || { echo 'Date service already differs; release stopped.' >&2; exit 1; }
  sudo cp /srv/api/app/services/bank_dates.py "$stage/service.before.py"
fi
[[ $(sha256sum "$stage/learning_catalog.py" | cut -d' ' -f1) == "$router" ]]
[[ $(sha256sum "$stage/bank_dates.py" | cut -d' ' -f1) == "$service" ]]
PYTHONPYCACHEPREFIX="$stage/pycache" /srv/api/.venv/bin/python -m py_compile "$stage/learning_catalog.py" "$stage/bank_dates.py"
sudo cp /srv/api/app/routers/learning_catalog.py "$stage/router.before.py"
rollback() {
 if [[ $(sudo sha256sum /srv/api/app/routers/learning_catalog.py | cut -d' ' -f1) == "$router" ]]; then
  sudo cp "$stage/router.before.py" /srv/api/app/routers/learning_catalog.py
  if sudo test -f "$stage/service.before.py"; then sudo cp "$stage/service.before.py" /srv/api/app/services/bank_dates.py; fi
  sudo systemctl restart ism-api
 fi
}
trap rollback ERR
sudo install -m 644 "$stage/bank_dates.py" /srv/api/app/services/bank_dates.py
sudo install -m 644 "$stage/learning_catalog.py" /srv/api/app/routers/learning_catalog.py
sudo systemctl restart ism-api
healthy=false
for attempt in $(seq 1 15); do
 if curl -fsS --max-time 5 https://study.hawayu.in/api/health; then healthy=true; break; fi
 sleep 2
done
[[ "$healthy" == true ]]
curl -fsSL --max-time 15 -o /dev/null https://family.hawayu.in
trap - ERR
echo "Important Dates API healthy; rollback copy: $stage/router.before.py"
REMOTE
