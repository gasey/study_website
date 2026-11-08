#!/usr/bin/env bash
# Bounded PDF CMS release, with source preimages and an additive schema migration.
set -euo pipefail
HOST=${ISM_HOST:-ubuntu@152.67.31.231}
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
release="pdf-library-$(date +%s)"
stage=$(mktemp -d)
trap 'rm -rf "$stage"' EXIT
files=(app/main.py app/config.py app/routers/paper_workbench.py app/routers/pdf_library.py app/services/pdf_library.py app/services/pdf_library_scan.py migrations/0077_pdf_library.sql)
for file in "${files[@]}"; do
  mkdir -p "$stage/api/$(dirname "$file")"
  cp "$ROOT/api/$file" "$stage/api/$file"
  printf '%s\n' "$file" >> "$stage/api-files.txt"
done
mkdir "$stage/systemd"
cp "$ROOT"/scripts/systemd/ism-pdf-library* "$stage/systemd/"
cp "$ROOT/scripts/systemd/ism-api-pdf-library.conf" "$stage/systemd/"
cat > "$stage/preimages.txt" <<'HASHES'
9cf5eacbe8919ba9a103cac108dedc8889f7e6e7f1c3f9fd6229c3cad45221ec app/main.py
31ed0cd60f28a2eaf4b2f5a51a36dda4d0f8456239aa5543a3af5842c182546e app/config.py
cc2a644f65500849772de1bc59874b60b32a8c5dee457063485225a7eb3f15f8 app/routers/paper_workbench.py
HASHES
rsync -az -e ssh "$stage/" "$HOST:/tmp/$release/"
ssh "$HOST" bash -s -- "$release" <<'REMOTE'
set -euo pipefail
stage="/tmp/$1"
backup="$stage/backup"
mkdir -m 700 "$backup"
while read -r expected file; do
  current=$(sudo sha256sum "/srv/api/$file" | cut -d' ' -f1)
  incoming=$(sha256sum "$stage/api/$file" | cut -d' ' -f1)
  if [ "$current" != "$expected" ] && [ "$current" != "$incoming" ]; then
    echo "Live source changed; inspect before deploying: $file" >&2
    exit 1
  fi
done < "$stage/preimages.txt"
sudo env PYTHONPYCACHEPREFIX="$stage/pycache" /srv/api/.venv/bin/python -m compileall -q "$stage/api/app"
sudo systemd-analyze verify "$stage"/systemd/*.service "$stage"/systemd/*.timer
: > "$backup/existing.txt"
: > "$backup/new.txt"
while read -r file; do
  if sudo test -f "/srv/api/$file"; then printf '%s\n' "$file" >> "$backup/existing.txt"; else printf '%s\n' "$file" >> "$backup/new.txt"; fi
done < "$stage/api-files.txt"
sudo tar -cf "$backup/api.tar" -C /srv/api -T "$backup/existing.txt"
: > "$backup/systemd-existing.txt"
for file in "$stage"/systemd/*; do
  name=$(basename "$file")
  target="/etc/systemd/system/$name"
  if [ "$name" = ism-api-pdf-library.conf ]; then target=/etc/systemd/system/ism-api.service.d/pdf-library.conf; fi
  if sudo test -f "$target"; then sudo cp -p "$target" "$backup/$name"; printf '%s\n' "$name" >> "$backup/systemd-existing.txt"; fi
done
sudo stat -c '%u:%g %a' /srv/study/private/paper-workbench/sources > "$backup/upload-permissions.txt"
installed=0
ok=0
restore() {
  status=$?
  trap - EXIT
  set +e
  if [ "$installed" = 1 ] && [ "$ok" = 0 ]; then
    sudo systemctl disable --now ism-pdf-library.timer ism-pdf-library-refresh.timer
    sudo systemctl stop ism-pdf-library.service ism-pdf-library-refresh.service
    sudo tar -xf "$backup/api.tar" -C /srv/api
    while read -r file; do sudo rm -f "/srv/api/$file"; done < "$backup/new.txt"
    for file in "$stage"/systemd/*; do
      name=$(basename "$file"); target="/etc/systemd/system/$name"
      if [ "$name" = ism-api-pdf-library.conf ]; then target=/etc/systemd/system/ism-api.service.d/pdf-library.conf; fi
      if test -f "$backup/$name"; then sudo cp -p "$backup/$name" "$target"; else sudo rm -f "$target"; fi
    done
    read -r ownership mode < "$backup/upload-permissions.txt"
    sudo chown "$ownership" /srv/study/private/paper-workbench/sources
    sudo chmod "$mode" /srv/study/private/paper-workbench/sources
    sudo systemctl daemon-reload
    sudo systemctl restart ism-api
    echo "PDF Library deployment failed; API and service files restored. Additive index tables retained. Backup: $backup" >&2
  fi
  exit "$status"
}
trap restore EXIT
migration=0077_pdf_library
sum=$(sha256sum "$stage/api/migrations/$migration.sql" | cut -d' ' -f1)
applied=$(sudo -u postgres psql -qtA -d mpsc -c "SELECT checksum FROM schema_migrations WHERE version='$migration'")
if [ -n "$applied" ] && [ "$applied" != "$sum" ]; then echo 'Migration checksum mismatch' >&2; exit 1; fi
if [ -z "$applied" ]; then
  {
    echo 'BEGIN;'
    sed '/^BEGIN;$/d; /^COMMIT;$/d' "$stage/api/migrations/$migration.sql"
    printf "INSERT INTO schema_migrations(version,checksum) VALUES('%s','%s');\n" "$migration" "$sum"
    echo 'COMMIT;'
  } | sudo -u postgres psql -v ON_ERROR_STOP=1 -q -d mpsc
fi
installed=1
while read -r file; do sudo install -D -m 644 "$stage/api/$file" "/srv/api/$file"; done < "$stage/api-files.txt"
sudo install -d -m 750 -o root -g www-data /srv/study/private/pdf-library
sudo install -d -m 755 /srv/study/private/pdf-library/archive
sudo chgrp www-data /srv/study/private/paper-workbench/sources
sudo chmod 2770 /srv/study/private/paper-workbench/sources
for file in "$stage"/systemd/*; do
  name=$(basename "$file"); target="/etc/systemd/system/$name"
  if [ "$name" = ism-api-pdf-library.conf ]; then target=/etc/systemd/system/ism-api.service.d/pdf-library.conf; fi
  sudo install -D -m 644 "$file" "$target"
done
sudo systemctl daemon-reload
sudo systemctl restart ism-api
for n in $(seq 1 20); do
  if curl -fsS --max-time 5 https://study.hawayu.in/api/health > "$stage/health.json"; then break; fi
  sleep 2
done
curl -fsS --max-time 10 https://study.hawayu.in/api/health
curl -fsS --max-time 15 -o /dev/null https://family.hawayu.in
sudo systemctl enable --now ism-pdf-library.timer ism-pdf-library-refresh.timer
sudo systemctl start ism-pdf-library-refresh.service
sudo systemctl is-active --quiet ism-api ism-paper-documents ism-paper-publisher ism-pdf-library.timer ism-pdf-library-refresh.timer
ok=1
echo "PDF Library deployed. Backup: $backup"
REMOTE
