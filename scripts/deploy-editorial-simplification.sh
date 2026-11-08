#!/usr/bin/env bash
# Additive migration must be rehearsed/applied with migrate.sh before this release.
# Ship this feature's files only; preserve the rest of the workshop and API.
set -euo pipefail
HOST=${ISM_HOST:-ubuntu@152.67.31.231}
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RELEASE="editorial-simplification-$(date +%s)"
STAGE=$(mktemp -d)
trap 'rm -rf "$STAGE"' EXIT
mkdir -p "$STAGE/api" "$STAGE/scripts"
for file in app/routers/editorial.py app/routers/bank_workspace.py app/routers/admin_answers.py app/routers/retagging.py app/routers/admin_bank_edits.py app/services/editorial_access.py app/services/bank_review.py app/services/admin_bank_edits.py app/services/bank_publication.py migrations/0073_editorial_simplification.sql; do
  mkdir -p "$STAGE/api/$(dirname "$file")"
  cp "$ROOT/api/$file" "$STAGE/api/$file"
  printf '%s\n' "$file" >> "$STAGE/api-files.txt"
done
cp "$ROOT/scripts/bank-review-worker.py" "$STAGE/scripts/"
cp "$ROOT/scripts/admin_tag_batch.py" "$STAGE/scripts/"
rsync -az -e ssh "$STAGE/" "$HOST:/tmp/$RELEASE/"
ssh "$HOST" bash -s -- "$RELEASE" <<'REMOTE'
set -euo pipefail
stage="/tmp/$1"
backup="$stage/backup"
workshop=/srv/study/workshop/india-study-map-app
mkdir -p "$backup"
chmod 700 "$backup"
# Fail before stopping anything if the expected schema is absent.
test "$(sudo -u postgres psql -d mpsc -qtA -c "SELECT count(*) FROM schema_migrations WHERE version='0073_editorial_simplification'")" = 1
sudo env PYTHONPYCACHEPREFIX="$stage/pycache" /srv/api/.venv/bin/python -m compileall -q "$stage/api/app" "$stage/scripts"
installed=0
released=0
restore() {
  local status=$?
  set +e
  if [ "$installed" = 1 ] && [ "$released" = 0 ]; then
    sudo tar -xf "$backup/api.tar" -C /srv/api
    while read -r file; do
      case "$file" in *.py) sudo rm -f "/srv/api/$file" ;; esac
    done < "$backup/new-files.txt"
    sudo cp "$backup/bank-review-worker.py" "$workshop/scripts/bank-review-worker.py"
    if sudo test -f "$backup/admin_tag_batch.py"; then
      sudo cp "$backup/admin_tag_batch.py" "$workshop/scripts/admin_tag_batch.py"
    else
      sudo rm -f "$workshop/scripts/admin_tag_batch.py"
    fi
    sudo systemctl restart ism-api
    echo 'Editorial release failed; previous API/worker files restored.' >&2
  fi
  if [ -f "$backup/resume-units.txt" ]; then
    while read -r unit; do sudo systemctl start "$unit"; done < "$backup/resume-units.txt"
  fi
  exit "$status"
}
trap restore EXIT
: > "$backup/resume-units.txt"
for unit in ism-oracle-bank-review.timer ism-paper-publisher.service ism-paper-documents.service; do
  if sudo systemctl is-active --quiet "$unit"; then
    printf '%s\n' "$unit" >> "$backup/resume-units.txt"
    sudo systemctl stop "$unit"
  fi
done
for n in $(seq 1 180); do
  if ! sudo systemctl is-active --quiet ism-oracle-bank-review.service; then break; fi
  sleep 2
done
if sudo systemctl is-active --quiet ism-oracle-bank-review.service; then
  echo 'Bank publisher is still running; no files replaced.' >&2
  exit 1
fi
: > "$backup/existing-files.txt"
: > "$backup/new-files.txt"
while read -r file; do
  if sudo test -f "/srv/api/$file"; then
    printf '%s\n' "$file" >> "$backup/existing-files.txt"
  else
    printf '%s\n' "$file" >> "$backup/new-files.txt"
  fi
done < "$stage/api-files.txt"
sudo tar -cf "$backup/api.tar" -C /srv/api -T "$backup/existing-files.txt"
sudo cp "$workshop/scripts/bank-review-worker.py" "$backup/bank-review-worker.py"
if sudo test -f "$workshop/scripts/admin_tag_batch.py"; then sudo cp "$workshop/scripts/admin_tag_batch.py" "$backup/admin_tag_batch.py"; fi
installed=1
sudo rsync -a "$stage/api/" /srv/api/
sudo install -m 755 "$stage/scripts/bank-review-worker.py" "$workshop/scripts/bank-review-worker.py"
sudo install -m 644 "$stage/scripts/admin_tag_batch.py" "$workshop/scripts/admin_tag_batch.py"
sudo systemctl restart ism-api
for n in $(seq 1 20); do
  if curl -fsS --max-time 5 https://study.hawayu.in/api/health > "$stage/health.json"; then
    released=1
    cat "$stage/health.json"
    printf '\nRelease backup: %s\n' "$backup"
    exit 0
  fi
  sleep 2
done
echo 'Editorial API health check did not pass.' >&2
exit 1
REMOTE
