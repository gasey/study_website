#!/usr/bin/env bash
# Narrow paper-import release; drain both paper workers and retain a rollback.
set -euo pipefail
HOST=${ISM_HOST:-ubuntu@152.67.31.231}
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
release="paper-source-import-$(date +%s)"
stage=$(mktemp -d)
trap 'rm -rf "$stage"' EXIT
for file in app/routers/paper_workbench.py app/services/paper_publish.py app/services/paper_targets.py; do
  mkdir -p "$stage/api/$(dirname "$file")"
  cp "$ROOT/api/$file" "$stage/api/$file"
  printf '%s\n' "$file" >> "$stage/api-files.txt"
done
cp "$ROOT/scripts/paper_bank_store.py" "$stage/paper_bank_store.py"
rsync -az -e ssh "$stage/" "$HOST:/tmp/$release/"
ssh "$HOST" bash -s -- "$release" <<'REMOTE'
set -euo pipefail
stage="/tmp/$1"
backup="$stage/backup"
workshop=/srv/study/workshop/india-study-map-app/scripts
mkdir -m 700 "$backup"
sudo env PYTHONPYCACHEPREFIX="$stage/pycache" /srv/api/.venv/bin/python -m compileall -q "$stage/api/app"
sudo env PYTHONPYCACHEPREFIX="$stage/pycache" /srv/api/.venv/bin/python -m py_compile "$stage/paper_bank_store.py"
: > "$backup/existing.txt"
: > "$backup/new.txt"
: > "$backup/active-workers.txt"
while read -r file; do
  if sudo test -f "/srv/api/$file"; then printf '%s\n' "$file" >> "$backup/existing.txt"; else printf '%s\n' "$file" >> "$backup/new.txt"; fi
done < "$stage/api-files.txt"
sudo tar -cf "$backup/api.tar" -C /srv/api -T "$backup/existing.txt"
sudo cp -p "$workshop/paper_bank_store.py" "$backup/paper_bank_store.py"
for unit in ism-paper-documents ism-paper-publisher; do
  if sudo systemctl is-active --quiet "$unit"; then printf '%s\n' "$unit" >> "$backup/active-workers.txt"; fi
done
installed=0
ok=0
restore() {
  local status=$?
  trap - EXIT
  set +e
  if [ "$installed" = 1 ] && [ "$ok" = 0 ]; then
    while read -r unit; do sudo systemctl stop "$unit"; done < "$backup/active-workers.txt"
    sudo tar -xf "$backup/api.tar" -C /srv/api
    while read -r file; do sudo rm -f "/srv/api/$file"; done < "$backup/new.txt"
    sudo cp -p "$backup/paper_bank_store.py" "$workshop/paper_bank_store.py"
    sudo systemctl restart ism-api
    echo 'Paper source import failed; previous API/publisher files restored.' >&2
  fi
  while read -r unit; do sudo systemctl start "$unit" || status=1; done < "$backup/active-workers.txt"
  exit "$status"
}
trap restore EXIT
while read -r unit; do sudo systemctl stop "$unit"; done < "$backup/active-workers.txt"
installed=1
while read -r file; do sudo install -D -m 644 "$stage/api/$file" "/srv/api/$file"; done < "$stage/api-files.txt"
sudo install -m 644 "$stage/paper_bank_store.py" "$workshop/paper_bank_store.py"
sudo systemctl restart ism-api
for n in $(seq 1 20); do
  if curl -fsS --max-time 5 https://study.hawayu.in/api/health > "$stage/health.json"; then
    while read -r unit; do sudo systemctl start "$unit"; sudo systemctl is-active --quiet "$unit"; done < "$backup/active-workers.txt"
    curl -fsS --max-time 15 -o /dev/null https://family.hawayu.in
    ok=1
    cat "$stage/health.json"
    printf '\nPaper source import backup: %s\n' "$backup"
    exit 0
  fi
  sleep 2
done
exit 1
REMOTE
