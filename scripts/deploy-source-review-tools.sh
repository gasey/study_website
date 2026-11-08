#!/usr/bin/env bash
# Narrow operator-tool/shared-verifier update; no bank content or permissions changed.
set -euo pipefail
HOST=${ISM_HOST:-ubuntu@152.67.31.231}
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
release="source-review-tools-$(date +%s)"
stage=$(mktemp -d)
trap 'rm -rf "$stage"' EXIT
for file in publish-owner-review-batch.py; do cp "$ROOT/scripts/$file" "$stage/$file"; done
cp "$ROOT/api/app/services/publication_verification.py" "$stage/publication_verification.py"
rsync -az -e ssh "$stage/" "$HOST:/tmp/$release/"
ssh "$HOST" bash -s -- "$release" <<'REMOTE'
set -euo pipefail
stage="/tmp/$1"
workshop=/srv/study/workshop/india-study-map-app/scripts
mkdir -m 700 "$stage/backup"
sudo env PYTHONPYCACHEPREFIX="$stage/pycache" /srv/api/.venv/bin/python -m py_compile "$stage/publish-owner-review-batch.py"
sudo env PYTHONPYCACHEPREFIX="$stage/pycache" /srv/api/.venv/bin/python -m py_compile "$stage/publication_verification.py"
sudo cp -p /srv/api/app/services/publication_verification.py "$stage/backup/publication_verification.py"
sudo cp -p "$workshop/publish-owner-review-batch.py" "$stage/backup/"
sudo install -m 755 "$stage/publish-owner-review-batch.py" "$workshop/publish-owner-review-batch.py"
sudo install -m 644 "$stage/publication_verification.py" /srv/api/app/services/publication_verification.py
sudo systemctl restart ism-api
healthy=0
for n in $(seq 1 20); do
  if curl -fsS --max-time 5 https://study.hawayu.in/api/health >/dev/null; then healthy=1; break; fi
  sleep 2
done
if [ "$healthy" != 1 ]; then
  sudo cp -p "$stage/backup/publication_verification.py" /srv/api/app/services/publication_verification.py
  sudo cp -p "$stage/backup/publish-owner-review-batch.py" "$workshop/publish-owner-review-batch.py"
  sudo systemctl restart ism-api
  echo 'Health failed; restored previous source review tools and verifier.' >&2
  exit 1
fi
printf 'Source review tools backup: %s/backup\n' "$stage"
REMOTE
