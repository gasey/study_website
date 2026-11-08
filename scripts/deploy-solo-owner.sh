#!/usr/bin/env bash
# Bounded release. Rehearse only 0080 on a fresh dump clone; preserve unrelated source.
set -euo pipefail
HOST=${ISM_HOST:-ubuntu@152.67.31.231}
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RELEASE="solo-owner-$(date +%s)"
STAGE=$(mktemp -d)
trap 'rm -rf "$STAGE"' EXIT
mkdir -p "$STAGE/api/app" "$STAGE/scripts"
for file in app/routers/admin_bank_edits.py app/routers/retagging.py app/routers/bank_workspace.py app/routers/paper_workbench.py app/routers/learning_catalog.py app/services/owner_workflow.py app/services/database_map.py app/services/paper_approval.py app/services/paper_publish.py migrations/0080_owner_paper_decisions.sql; do
  mkdir -p "$STAGE/api/$(dirname "$file")"
  cp "$ROOT/api/$file" "$STAGE/api/$file"
  printf '%s\n' "$file" >> "$STAGE/api-files.txt"
done
cp "$ROOT/scripts/releases/solo-owner-20261106.json" "$STAGE/expected.json"
cp "$ROOT/scripts/paper_bank_store.py" "$STAGE/scripts/paper_bank_store.py"
rsync -az -e ssh "$STAGE/" "$HOST:/tmp/$RELEASE/"
ssh "$HOST" bash -s -- "$RELEASE" <<'REMOTE'
set -euo pipefail
stage="/tmp/$1"
backup="$stage/backup"
workshop=/srv/study/workshop/india-study-map-app
clone="ism_soloowner_rehearsal_${1##*-}"
chmod 755 "$stage"
mkdir -p "$backup"
chmod 700 "$backup"
python3 - "$stage" <<'PY'
from pathlib import Path
import hashlib,json,subprocess,sys
r=Path(sys.argv[1]);expected=json.loads((r/'expected.json').read_text())['api_preimages']
for rel in (r/'api-files.txt').read_text().splitlines():
 p=r/'api'/rel;live=Path('/srv/api')/rel
 current=subprocess.run(['sudo','sha256sum',str(live)],capture_output=True,text=True)
 if current.returncode:
  if rel in expected:raise SystemExit('Expected deployed file missing: '+rel)
  continue
 sha=current.stdout.split()[0]
 prior=expected.get(rel,[])
 allowed=set(prior if isinstance(prior,list) else [prior])|{hashlib.sha256(p.read_bytes()).hexdigest()}
 if sha not in allowed:raise SystemExit('Deployed source changed; inspect before replacing: '+rel)
for rel,prior in json.loads((r/'expected.json').read_text())['script_preimages'].items():
 live=Path('/srv/study/workshop/india-study-map-app/scripts')/rel
 current=subprocess.run(['sudo','sha256sum',str(live)],check=True,capture_output=True,text=True).stdout.split()[0]
 if current not in {prior,hashlib.sha256((r/'scripts'/rel).read_bytes()).hexdigest()}:raise SystemExit('Deployed bank script changed; inspect before replacing: '+rel)
PY
test "$(sudo -u postgres psql -X -qtA -d mpsc -c "SELECT count(*) FROM schema_migrations WHERE version='0079_shareable_tests'")" = 1
sudo env PYTHONPYCACHEPREFIX="$stage/pycache" /srv/api/.venv/bin/python -m compileall -q "$stage/api/app" "$stage/scripts"
installed=0
released=0
clone_created=0
restore() {
  local status=$?
  set +e
  if [ "$clone_created" = 1 ]; then sudo -u postgres dropdb "$clone"; fi
  if [ "$installed" = 1 ] && [ "$released" = 0 ]; then
    sudo tar -xf "$backup/api.tar" -C /srv/api
    sudo tar -xf "$backup/scripts.tar" -C "$workshop/scripts"
    while read -r file; do sudo rm -f "/srv/api/$file"; done < "$backup/new-files.txt"
    sudo systemctl restart ism-api
    echo 'Restored previous API files; additive configuration schema is retained.' >&2
  fi
  if [ -f "$backup/resume-units.txt" ]; then
    while read -r unit; do sudo systemctl start "$unit"; done < "$backup/resume-units.txt"
  fi
  exit "$status"
}
trap restore EXIT
echo 'Rehearsing 0080 on a disposable production dump clone'
sudo -u postgres createdb "$clone"
clone_created=1
sudo -u postgres pg_dump --no-owner --no-privileges mpsc | sudo -u postgres psql -X -q -v ON_ERROR_STOP=1 -d "$clone" > "$stage/clone-restore.log"
fingerprint() {
  sudo -u postgres psql -X -qtA -v ON_ERROR_STOP=1 -d "$1" <<'SQL'
SELECT 'questions',count(*),md5(string_agg(md5(row_to_json(t)::text),'' ORDER BY id)) FROM canonical_questions t;
SELECT 'appearances',count(*),md5(string_agg(md5(row_to_json(t)::text),'' ORDER BY id)) FROM appearances t;
SELECT 'papers',count(*),md5(string_agg(md5(row_to_json(t)::text),'' ORDER BY id)) FROM papers t;
SELECT 'classifications',count(*),md5(string_agg(md5(row_to_json(t)::text),'' ORDER BY question_id)) FROM question_classifications t;
SELECT 'attempts',count(*),md5(string_agg(md5(row_to_json(t)::text),'' ORDER BY id)) FROM attempts t;
SELECT 'assignments',count(*),md5(string_agg(md5(row_to_json(t)::text),'' ORDER BY id)) FROM editorial_assignments t;
SELECT 'grants',count(*),md5(string_agg(md5(row_to_json(t)::text),'' ORDER BY id)) FROM review_grants t;
SELECT 'learning_catalog',count(*),md5(string_agg(md5((to_jsonb(t)-'live_test_version')::text),'' ORDER BY id)) FROM learning_catalog t;
SELECT 'learning_history',count(*),md5(string_agg(md5(row_to_json(t)::text),'' ORDER BY id)) FROM learning_catalog_history t;
SELECT 'paper_drafts',count(*),md5(string_agg(md5(row_to_json(t)::text),'' ORDER BY id)) FROM paper_workbench_drafts t;
SELECT 'paper_reviews',count(*),md5(string_agg(md5(row_to_json(t)::text),'' ORDER BY id)) FROM paper_workbench_reviews t;
SELECT 'paper_history',count(*),md5(string_agg(md5(row_to_json(t)::text),'' ORDER BY id)) FROM paper_workbench_history t;
SELECT 'paper_jobs',count(*),md5(string_agg(md5(row_to_json(t)::text),'' ORDER BY id)) FROM paper_workbench_jobs t;
SELECT 'mock_sessions',count(*),md5(string_agg(md5((to_jsonb(t)-'learning_test_id'-'learning_test_version'-'learning_test_title')::text),'' ORDER BY id)) FROM mock_sessions t;
SQL
}
fingerprint "$clone" > "$stage/rehearsal-before.txt"
applied=$(sudo -u postgres psql -X -qtA -d mpsc -c "SELECT checksum FROM schema_migrations WHERE version='0080_owner_paper_decisions'")
checksum=$(sha256sum "$stage/api/migrations/0080_owner_paper_decisions.sql" | cut -c1-16)
if [ -z "$applied" ]; then
  sudo -u postgres psql -X -q -v ON_ERROR_STOP=1 -d "$clone" -f "$stage/api/migrations/0080_owner_paper_decisions.sql"
elif [ "$applied" != "$checksum" ]; then
  echo 'Applied 0080 checksum differs; never rewrite an applied migration' >&2
  exit 1
fi
fingerprint "$clone" > "$stage/rehearsal-after.txt"
cmp "$stage/rehearsal-before.txt" "$stage/rehearsal-after.txt"
sudo -u postgres dropdb "$clone"
clone_created=0
echo 'Migration rehearsal passed; source records, attempts and permissions are unchanged'
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
if sudo systemctl is-active --quiet ism-oracle-bank-review.service; then echo 'Publisher has not drained; no release installed' >&2; exit 1; fi
sudo sha256sum /srv/study/workshop/mpsc-question-bankv2/bank/mpsc_bank_v2.json > "$stage/bank-before.txt"
if [ -z "$applied" ]; then
  python3 - "$stage" "$checksum" <<'PY'
from pathlib import Path
import sys
r=Path(sys.argv[1]);s=(r/'api/migrations/0080_owner_paper_decisions.sql').read_text()
s=s.replace('COMMIT;',"INSERT INTO schema_migrations(version,checksum) VALUES('0080_owner_paper_decisions','"+sys.argv[2]+"');\nCOMMIT;")
(r/'apply.sql').write_text(s)
PY
  sudo -u postgres psql -X -q -v ON_ERROR_STOP=1 -d mpsc -f "$stage/apply.sql"
fi
: > "$backup/existing-files.txt"
: > "$backup/new-files.txt"
while read -r file; do
  if sudo test -f "/srv/api/$file"; then printf '%s\n' "$file" >> "$backup/existing-files.txt"; else printf '%s\n' "$file" >> "$backup/new-files.txt"; fi
done < "$stage/api-files.txt"
sudo tar -cf "$backup/api.tar" -C /srv/api -T "$backup/existing-files.txt"
sudo tar -cf "$backup/scripts.tar" -C "$workshop/scripts" paper_bank_store.py
installed=1
sudo rsync -a "$stage/api/" /srv/api/
sudo install -m 644 "$stage/scripts/paper_bank_store.py" "$workshop/scripts/paper_bank_store.py"
sudo sha256sum /srv/study/workshop/mpsc-question-bankv2/bank/mpsc_bank_v2.json > "$stage/bank-after.txt"
cmp "$stage/bank-before.txt" "$stage/bank-after.txt"
sudo systemctl restart ism-api
for n in $(seq 1 20); do
  if curl -fsS --max-time 5 https://study.hawayu.in/api/health > "$stage/health.json"; then
    curl -fsS --max-time 10 https://study.hawayu.in/api/tests > "$stage/tests-directory.json"
    test "$(curl -Ls -o /dev/null -w '%{http_code}' --max-time 10 https://family.hawayu.in)" = 200
    released=1
    cat "$stage/health.json"
    printf '\nRelease evidence and rollback: %s\n' "$stage"
    exit 0
  fi
  sleep 2
done
echo 'API health check failed' >&2
exit 1
REMOTE
