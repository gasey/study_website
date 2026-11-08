#!/usr/bin/env bash
# Bounded release. Rehearse only 0078 on a fresh dump clone; preserve unrelated source.
set -euo pipefail
HOST=${ISM_HOST:-ubuntu@152.67.31.231}
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RELEASE="bank-organization-$(date +%s)"
STAGE=$(mktemp -d)
trap 'rm -rf "$STAGE"' EXIT
mkdir -p "$STAGE/api/app" "$STAGE/scripts"
for file in app/schemas.py app/routers/mocks.py app/routers/collections.py app/routers/admin_bank_edits.py app/routers/bank_organization.py app/services/bank_organization.py app/services/repeat_selection.py app/services/learning_taxonomy.py app/data/learning-topic-aliases.json app/data/exam-scheme-templates.json migrations/0078_bank_organization.sql; do
  mkdir -p "$STAGE/api/$(dirname "$file")"
  cp "$ROOT/api/$file" "$STAGE/api/$file"
  printf '%s\n' "$file" >> "$STAGE/api-files.txt"
done
cp "$ROOT/scripts/extend-writing-taxonomy.py" "$STAGE/scripts/"
cp "$ROOT/scripts/releases/bank-organization-20261106.json" "$STAGE/expected.json"
# Patch the inspected deployed entry point only; local route-order work is unrelated.
ssh "$HOST" 'sudo cat /srv/api/app/main.py' > "$STAGE/api/app/main.py"
python3 - "$STAGE" <<'PY'
from pathlib import Path
import hashlib,json,sys
r=Path(sys.argv[1]);p=r/'api/app/main.py';s=p.read_text();expected=json.loads((r/'expected.json').read_text())['api_preimages']['app/main.py']
addition='\nfrom .routers import bank_organization\napp.include_router(bank_organization.router)\napp.include_router(bank_organization.public_router)\n'
if hashlib.sha256(p.read_bytes()).hexdigest()==expected:s+=addition
elif addition not in s:raise SystemExit('Deployed entry point changed; inspect its new source before releasing')
p.write_text(s)
PY
printf '%s\n' app/main.py >> "$STAGE/api-files.txt"
rsync -az -e ssh "$STAGE/" "$HOST:/tmp/$RELEASE/"
ssh "$HOST" bash -s -- "$RELEASE" <<'REMOTE'
set -euo pipefail
stage="/tmp/$1"
backup="$stage/backup"
workshop=/srv/study/workshop/india-study-map-app
clone="ism_organization_rehearsal_${1##*-}"
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
PY
test "$(sudo -u postgres psql -X -qtA -d mpsc -c "SELECT count(*) FROM schema_migrations WHERE version='0077_pdf_library'")" = 1
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
echo 'Rehearsing 0078 on a disposable production dump clone'
sudo -u postgres createdb "$clone"
clone_created=1
sudo -u postgres pg_dump --no-owner --no-privileges mpsc | sudo -u postgres psql -X -q -v ON_ERROR_STOP=1 -d "$clone" > "$stage/clone-restore.log"
fingerprint() {
  sudo -u postgres psql -X -qtA -d "$1" <<'SQL'
SELECT 'questions',count(*),md5(string_agg(md5(row_to_json(t)::text),'' ORDER BY id)) FROM canonical_questions t;
SELECT 'appearances',count(*),md5(string_agg(md5(row_to_json(t)::text),'' ORDER BY id)) FROM appearances t;
SELECT 'papers',count(*),md5(string_agg(md5(row_to_json(t)::text),'' ORDER BY id)) FROM papers t;
SELECT 'classifications',count(*),md5(string_agg(md5(row_to_json(t)::text),'' ORDER BY question_id)) FROM question_classifications t;
SELECT 'attempts',count(*),md5(string_agg(md5(row_to_json(t)::text),'' ORDER BY id)) FROM attempts t;
SELECT 'assignments',count(*),md5(string_agg(md5(row_to_json(t)::text),'' ORDER BY id)) FROM editorial_assignments t;
SELECT 'grants',count(*),md5(string_agg(md5(row_to_json(t)::text),'' ORDER BY id)) FROM review_grants t;
SQL
}
fingerprint "$clone" > "$stage/rehearsal-before.txt"
applied=$(sudo -u postgres psql -X -qtA -d mpsc -c "SELECT checksum FROM schema_migrations WHERE version='0078_bank_organization'")
checksum=$(sha256sum "$stage/api/migrations/0078_bank_organization.sql" | cut -c1-16)
if [ -z "$applied" ]; then
  sudo -u postgres psql -X -q -v ON_ERROR_STOP=1 -d "$clone" -f "$stage/api/migrations/0078_bank_organization.sql"
elif [ "$applied" != "$checksum" ]; then
  echo 'Applied 0078 checksum differs; never rewrite an applied migration' >&2
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
r=Path(sys.argv[1]);s=(r/'api/migrations/0078_bank_organization.sql').read_text()
s=s.replace('COMMIT;',"INSERT INTO schema_migrations(version,checksum) VALUES('0078_bank_organization','"+sys.argv[2]+"');\nCOMMIT;")
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
installed=1
sudo rsync -a "$stage/api/" /srv/api/
sudo install -m 644 "$stage/scripts/extend-writing-taxonomy.py" "$workshop/scripts/extend-writing-taxonomy.py"
sudo bash -c "cd '$workshop'; python3 scripts/extend-writing-taxonomy.py --apply"
sudo sha256sum /srv/study/workshop/mpsc-question-bankv2/bank/mpsc_bank_v2.json > "$stage/bank-after.txt"
cmp "$stage/bank-before.txt" "$stage/bank-after.txt"
sudo systemctl restart ism-api
for n in $(seq 1 20); do
  if curl -fsS --max-time 5 https://study.hawayu.in/api/health > "$stage/health.json"; then
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
