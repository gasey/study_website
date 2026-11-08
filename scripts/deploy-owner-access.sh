#!/usr/bin/env bash
# Explicit owner-requested account policy; no schema/content/role changes.
set -euo pipefail
HOST=${ISM_HOST:-ubuntu@152.67.31.231}
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RELEASE="owner-access-$(date +%s)"
STAGE=$(mktemp -d)
trap 'rm -rf "$STAGE"' EXIT
cp "$ROOT/scripts/releases/owner-access-20261107.json" "$STAGE/expected.json"
python3 - "$ROOT" "$STAGE" <<'PY'
import json,sys,shutil
from pathlib import Path
root,stage=map(Path,sys.argv[1:])
files=json.loads((stage/'expected.json').read_text())
for rel in files:
 target=stage/'api'/rel;target.parent.mkdir(parents=True,exist_ok=True)
 shutil.copyfile(root/'api'/rel,target)
(stage/'api-files.txt').write_text('\n'.join(files)+'\n')
PY
rsync -az -e ssh "$STAGE/" "$HOST:/tmp/$RELEASE/"
ssh "$HOST" bash -s -- "$RELEASE" <<'REMOTE'
set -euo pipefail
stage="/tmp/$1"
policy=/etc/systemd/system/ism-api.service.d/owner-mfa-policy.conf
backup="$stage/backup"
mkdir -p "$backup"
chmod 700 "$backup"
python3 - "$stage" <<'PY'
import hashlib,json,subprocess,sys
from pathlib import Path
stage=Path(sys.argv[1])
for rel,expected in json.loads((stage/'expected.json').read_text()).items():
 actual=subprocess.check_output(['sudo','sha256sum','/srv/api/'+rel],text=True).split()[0]
 if actual!=expected:raise SystemExit('Deployed preimage changed: '+rel)
PY
# Check the exact user and unfinished enrollment; never silently remove an active factor.
test "$(sudo -u postgres psql -X -qtA -d mpsc -c "SELECT count(*) FROM users u LEFT JOIN account_mfa m ON m.user_id=u.id WHERE u.id='usr_3Xw_h0yauFwLL4Xel8myStcO' AND lower(u.email)='hruaitluangasailo20@gmail.com' AND m.enabled_at IS NULL AND EXISTS(SELECT 1 FROM review_grants g WHERE g.user_id=u.id AND g.role='owner' AND g.revoked_at IS NULL)")" = 1
sudo env PYTHONPYCACHEPREFIX="$stage/pycache" /srv/api/.venv/bin/python -m compileall -q "$stage/api/app"
sudo tar -cf "$backup/api.tar" -C /srv/api -T "$stage/api-files.txt"
if sudo test -f "$policy"; then sudo cp "$policy" "$backup/policy.conf"; fi
sudo sha256sum /srv/study/workshop/mpsc-question-bankv2/bank/mpsc_bank_v2.json > "$stage/bank-before.txt"
installed=0
success=0
restore() {
 status=$?
 if [ "$installed" = 1 ] && [ "$success" = 0 ]; then
  sudo tar -xf "$backup/api.tar" -C /srv/api
  if sudo test -f "$backup/policy.conf"; then sudo cp "$backup/policy.conf" "$policy"; else sudo rm -f "$policy"; fi
  sudo systemctl daemon-reload
  sudo systemctl restart ism-api
  echo 'Restored API and previous account policy after failed release.' >&2
 fi
 exit "$status"
}
trap restore EXIT
installed=1
sudo rsync -a "$stage/api/" /srv/api/
printf '%s\n' '[Service]' 'Environment=STAFF_MFA_EXEMPT_USER_IDS=usr_3Xw_h0yauFwLL4Xel8myStcO' > "$stage/policy.conf"
sudo install -m 600 "$stage/policy.conf" "$policy"
sudo systemctl daemon-reload
sudo systemctl restart ism-api
healthy=0
for n in $(seq 1 20); do
 if curl -fsS --max-time 5 https://study.hawayu.in/api/health > "$stage/health.json"; then healthy=1; break; fi
 sleep 1
done
test "$healthy" = 1
# Clear only the unfinished setup and record the direct owner instruction.
sudo -u postgres psql -X -v ON_ERROR_STOP=1 -d mpsc > "$stage/account-policy-receipt.txt" <<'SQL'
BEGIN;
SELECT id FROM users WHERE id='usr_3Xw_h0yauFwLL4Xel8myStcO' AND lower(email)='hruaitluangasailo20@gmail.com' FOR UPDATE;
UPDATE account_mfa SET pending_cipher=NULL,pending_until=NULL,updated_at=now()
 WHERE user_id='usr_3Xw_h0yauFwLL4Xel8myStcO' AND enabled_at IS NULL;
INSERT INTO account_security_events(user_id,action,detail)
 VALUES ('usr_3Xw_h0yauFwLL4Xel8myStcO','owner_requested_optional_staff_mfa',
 '{"authorization":"Owner explicitly requested simpler access or removal in Codex on 2026-11-07","scope":"Exact immutable account ID only","active_factor_removed":false,"unfinished_setup_cleared":true,"mfa_verified_asserted":false}');
COMMIT;
SQL
sudo sha256sum /srv/study/workshop/mpsc-question-bankv2/bank/mpsc_bank_v2.json > "$stage/bank-after.txt"
cmp "$stage/bank-before.txt" "$stage/bank-after.txt"
curl -fsS --max-time 15 https://family.hawayu.in/ > /dev/null
success=1
echo "Released narrow account policy and Assistant/UDC draft template: $stage"
REMOTE
