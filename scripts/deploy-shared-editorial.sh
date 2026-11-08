#!/usr/bin/env bash
# Narrow API-only release; rehearse/apply 0074–0075 through migrate.sh first.
set -euo pipefail
HOST=${ISM_HOST:-ubuntu@152.67.31.231}
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RELEASE="shared-editorial-$(date +%s)"
STAGE=$(mktemp -d)
trap 'rm -rf "$STAGE"' EXIT
for file in app/routers/editorial.py app/routers/editorial_shared.py app/services/editorial_status.py app/services/review_scope.py app/routers/module_composition.py app/services/module_composition.py migrations/0074_shared_editorial.sql migrations/0075_module_composition.sql; do
  mkdir -p "$STAGE/$(dirname "$file")"
  cp "$ROOT/api/$file" "$STAGE/$file"
  printf '%s\n' "$file" >> "$STAGE/files.txt"
done
rsync -az -e ssh "$STAGE/" "$HOST:/tmp/$RELEASE/"
ssh "$HOST" bash -s -- "$RELEASE" <<'REMOTE'
set -euo pipefail
stage="/tmp/$1"
backup="$stage/backup"
mkdir -m 700 "$backup"
test "$(sudo -u postgres psql -d mpsc -qtA -c "SELECT count(*) FROM schema_migrations WHERE version='0075_module_composition'")" = 1
sudo env PYTHONPYCACHEPREFIX="$stage/pycache" /srv/api/.venv/bin/python -m compileall -q "$stage/app"
: > "$backup/existing.txt"
: > "$backup/new.txt"
while read -r file; do
  if sudo test -f "/srv/api/$file"; then printf '%s\n' "$file" >> "$backup/existing.txt"; else printf '%s\n' "$file" >> "$backup/new.txt"; fi
done < "$stage/files.txt"
sudo tar -cf "$backup/api.tar" -C /srv/api -T "$backup/existing.txt"
installed=0
ok=0
restore() {
  local status=$?
  if [ "$installed" = 1 ] && [ "$ok" = 0 ]; then
    sudo tar -xf "$backup/api.tar" -C /srv/api
    while read -r file; do sudo rm -f "/srv/api/$file"; done < "$backup/new.txt"
    sudo systemctl restart ism-api
    echo 'Shared editorial API failed; previous files restored.' >&2
  fi
  exit "$status"
}
trap restore EXIT
installed=1
while read -r file; do sudo install -D -m 644 "$stage/$file" "/srv/api/$file"; done < "$stage/files.txt"
sudo systemctl restart ism-api
for n in $(seq 1 20); do
  if curl -fsS --max-time 5 https://study.hawayu.in/api/health > "$stage/health.json"; then
    ok=1
    cat "$stage/health.json"
    printf '\nRelease backup: %s\n' "$backup"
    exit 0
  fi
  sleep 2
done
exit 1
REMOTE
curl -fsS --max-time 15 -o /dev/null https://family.hawayu.in
