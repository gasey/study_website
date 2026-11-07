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
  ssh "$HOST" 'sudo rsync -a --delete /tmp/web-stage/ /srv/study/public/ && sudo chown -R caddy:caddy /srv/study/public'
}

resume_oracle_workers() {
  ssh "$HOST" 'if sudo test -f /etc/systemd/system/ism-paper-documents.service; then sudo systemctl start ism-paper-documents.service ism-paper-publisher.service ism-oracle-bank-review.timer; fi'
}
deploy_api() {
  trap 'resume_oracle_workers || true' EXIT
  echo "==> draining Oracle publishers before deployment"
  ssh "$HOST" '
    set -e
    if sudo test -f /etc/systemd/system/ism-paper-documents.service; then
      sudo systemctl stop ism-paper-documents.service ism-paper-publisher.service
      sudo systemctl stop ism-oracle-bank-review.timer
      for i in $(seq 1 180); do
        if ! sudo systemctl is-active --quiet ism-oracle-bank-review.service; then break; fi
        sleep 2
      done
      if sudo systemctl is-active --quiet ism-oracle-bank-review.service; then
        sudo systemctl start ism-paper-documents.service ism-paper-publisher.service ism-oracle-bank-review.timer
        echo "Publisher is still running; deployment deferred before files changed" >&2
        exit 1
      fi
    fi
  '
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
  if ssh "$HOST" 'sudo test -d /srv/study/workshop/india-study-map-app/scripts'; then
    rsync -az --delete --exclude __pycache__ --exclude bank-authority-policy.json -e ssh "$ROOT/scripts/" "$HOST:/tmp/ism-workshop-scripts/"
    ssh "$HOST" 'sudo rsync -a --delete --exclude bank-authority-policy.json /tmp/ism-workshop-scripts/ /srv/study/workshop/india-study-map-app/scripts/'
  fi
  ssh "$HOST" '
    if sudo test -f /etc/systemd/system/ism-paper-documents.service; then
      sudo cp /srv/study/workshop/india-study-map-app/scripts/systemd/ism-paper-documents.service /srv/study/workshop/india-study-map-app/scripts/systemd/ism-paper-publisher.service /etc/systemd/system/
      sudo systemctl daemon-reload
      sudo systemctl start ism-paper-documents.service ism-paper-publisher.service ism-oracle-bank-review.timer
    fi
  '
  trap - EXIT
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

# Targeted learning release: do not replace unrelated workshop/worker changes.
deploy_learning_api() {
  local stage
  stage=$(mktemp -d)
  chmod 755 "$stage"
  for file in app/main.py app/config.py app/schemas.py app/routers/questions.py app/routers/mocks.py app/routers/learning_catalog.py app/routers/google_auth.py requirements.txt migrations/0070_learning_catalog.sql migrations/0071_google_identity.sql; do
    mkdir -p "$stage/$(dirname "$file")"
    cp "$ROOT/api/$file" "$stage/$file"
  done
  rsync -az -e ssh "$stage/" "$HOST:/tmp/learning-api-stage/"
  ssh "$HOST" 'set -e; sudo rsync -a /tmp/learning-api-stage/ /srv/api/; cd /srv/api; sudo .venv/bin/pip install -q -r requirements.txt; sudo systemctl restart ism-api'
  for i in $(seq 1 15); do
    if curl -fsS --max-time 5 https://study.hawayu.in/api/health; then return 0; fi
    sleep 2
  done
  echo "Learning API release did not become healthy" >&2
  return 1
}

# Editorial workspace release: only its router/helper and additive migration file.
# Apply/rehearse pending migrations separately with scripts/migrate.sh first.
deploy_editorial_api() {
  local backup_name="editorial-workspace-$(date +%s)"
  ssh "$HOST" "sudo mkdir -p /tmp/$backup_name && sudo cp /srv/api/app/routers/editorial.py /tmp/$backup_name/router.py && sudo cp /srv/api/app/services/editorial_access.py /tmp/$backup_name/access.py"
  rsync -az -e ssh "$ROOT/api/app/routers/editorial.py" "$HOST:/tmp/editorial-workspace-router.py"
  rsync -az -e ssh "$ROOT/api/app/services/editorial_access.py" "$HOST:/tmp/editorial-workspace-access.py"
  rsync -az -e ssh "$ROOT/api/migrations/0072_editorial_workspace.sql" "$HOST:/tmp/editorial-workspace-migration.sql"
  ssh "$HOST" 'set -e; PYTHONPYCACHEPREFIX=/tmp/ism-editorial-pycache /srv/api/.venv/bin/python -m py_compile /tmp/editorial-workspace-router.py /tmp/editorial-workspace-access.py; sudo install -m 644 /tmp/editorial-workspace-router.py /srv/api/app/routers/editorial.py; sudo install -m 644 /tmp/editorial-workspace-access.py /srv/api/app/services/editorial_access.py; sudo install -m 644 /tmp/editorial-workspace-migration.sql /srv/api/migrations/0072_editorial_workspace.sql; sudo systemctl restart ism-api'
  for i in $(seq 1 15); do
    if curl -fsS --max-time 5 https://study.hawayu.in/api/health; then return 0; fi
    sleep 2
  done
  ssh "$HOST" "sudo cp /tmp/$backup_name/router.py /srv/api/app/routers/editorial.py && sudo cp /tmp/$backup_name/access.py /srv/api/app/services/editorial_access.py && sudo systemctl restart ism-api"
  echo "Editorial API health check failed; restored previous router/helper" >&2
  return 1
}

case "$WHAT" in
  publication-live) bash "$ROOT/scripts/deploy-publication-live.sh" ;;
  backend-followup) bash "$ROOT/scripts/deploy-backend-followup.sh" ;;
  backend-audit) bash "$ROOT/scripts/deploy-backend-audit.sh" ;;
  review-queue) bash "$ROOT/scripts/deploy-review-queue.sh" ;;
  publication-refresh) bash "$ROOT/scripts/deploy-publication-refresh.sh" ;;
  bank-overview) bash "$ROOT/scripts/deploy-bank-overview.sh" ;;
  owner-access) bash "$ROOT/scripts/deploy-owner-access.sh" ;;
  solo-owner) bash "$ROOT/scripts/deploy-solo-owner.sh" ;;
  shareable-tests) bash "$ROOT/scripts/deploy-shareable-tests.sh" ;;
  bank-organization) bash "$ROOT/scripts/deploy-bank-organization.sh" ;;
  pdf-library) bash "$ROOT/scripts/deploy-pdf-library.sh" ;;
  gazetted-review) bash "$ROOT/scripts/deploy-gazetted-review.sh" ;;
  paper-source-import) bash "$ROOT/scripts/deploy-paper-source-import.sh" ;;
  source-review-tools) bash "$ROOT/scripts/deploy-source-review-tools.sh" ;;
  shared-editorial) bash "$ROOT/scripts/deploy-shared-editorial.sh" ;;
  editorial-simplification) bash "$ROOT/scripts/deploy-editorial-simplification.sh" ;;
  editorial-api) deploy_editorial_api ;;
  learning-api) deploy_learning_api ;;
  web) deploy_web ;;
  api) deploy_api ;;
  all) deploy_api; deploy_web ;;
  *) echo "usage: $0 [web|api|solo-owner|shareable-tests|bank-organization|pdf-library|gazetted-review|paper-source-import|source-review-tools|editorial-api|editorial-simplification|shared-editorial|learning-api|all]" >&2; exit 2 ;;
esac
curl -fsS --max-time 15 -o /dev/null https://family.hawayu.in
echo "==> done: https://study.hawayu.in; shared family site healthy"
