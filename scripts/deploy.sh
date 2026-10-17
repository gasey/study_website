#!/usr/bin/env bash
# Build locally, ship artifacts. The server never compiles frontend code —
# one Ampere core makes `npm run build` slow and it competes with the running
# site. See docs/DECISIONS.md #4.
#
#   ./scripts/deploy.sh          # web + api
#   ./scripts/deploy.sh web      # just the frontend
#   ./scripts/deploy.sh api      # just the backend
set -euo pipefail

HOST=${ISM_HOST:-ubuntu@152.67.31.231}
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WHAT=${1:-all}

deploy_web() {
  echo "==> building web"
  (cd "$ROOT/web" && npm run build)
  echo "==> shipping to /srv/study/public"
  rsync -az --delete -e ssh "$ROOT/web/dist/" "$HOST:/tmp/web-stage/"
  ssh "$HOST" 'sudo rsync -a --delete /tmp/web-stage/ /srv/study/public/ && sudo chown -R caddy:caddy /srv/study'
}

deploy_api() {
  echo "==> shipping api"
  rsync -az --delete --exclude .venv --exclude __pycache__ -e ssh "$ROOT/api/" "$HOST:/tmp/api-stage/"
  ssh "$HOST" '
    set -e
    sudo rsync -a --delete --exclude .venv /tmp/api-stage/ /srv/api/
    cd /srv/api
    [ -d .venv ] || sudo python3 -m venv .venv
    sudo .venv/bin/pip install -q -r requirements.txt
    sudo systemctl restart ism-api
  '
  echo "==> waiting for health"
  for i in $(seq 1 15); do
    if curl -fsS --max-time 5 https://study.hawayu.in/api/health >/dev/null 2>&1; then
      curl -s https://study.hawayu.in/api/health; echo; return 0
    fi
    sleep 2
  done
  echo "API did not come back healthy" >&2
  ssh "$HOST" 'sudo journalctl -u ism-api -n 30 --no-pager' >&2
  return 1
}

case "$WHAT" in
  web) deploy_web ;;
  api) deploy_api ;;
  all) deploy_web; deploy_api ;;
  *) echo "usage: $0 [web|api|all]" >&2; exit 2 ;;
esac
echo "==> done: https://study.hawayu.in"
