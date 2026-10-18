#!/usr/bin/env bash
# Apply pending schema migrations.
#
# The schema is expected to keep changing as features land. That only stays
# safe if every change is a numbered file in api/migrations/ that is applied
# exactly once and never edited afterwards.
#
#   ./scripts/migrate.sh --status     # what is applied, what is pending
#   ./scripts/migrate.sh --dry-run    # apply inside a transaction, roll back
#   ./scripts/migrate.sh              # apply pending, for real
#
# Rules this enforces:
#   * each migration runs in ONE transaction — half-applied is impossible
#   * applied migrations are checksummed; editing one afterwards is an error
#     rather than a silent divergence between repo and server
#   * migrations run in filename order, so name them NNNN_what_it_does.sql
set -euo pipefail

HOST=${ISM_HOST:-ubuntu@152.67.31.231}
DB=${ISM_DB:-mpsc}
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIR="$ROOT/api/migrations"
MODE=${1:-apply}

psql_remote() { ssh "$HOST" "sudo -u postgres psql -v ON_ERROR_STOP=1 -qtA -d $DB" ; }

# Ledger. Created on first run; harmless thereafter.
psql_remote <<'SQL' >/dev/null
CREATE TABLE IF NOT EXISTS schema_migrations (
    version     TEXT PRIMARY KEY,
    checksum    TEXT NOT NULL,
    applied_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
SQL

applied=$(psql_remote <<<"SELECT version||' '||checksum FROM schema_migrations;" || true)

pending=()
drift=()
for f in "$DIR"/[0-9]*.sql; do
  v=$(basename "$f" .sql)
  sum=$(sha256sum "$f" | cut -c1-16)
  prev=$(grep -E "^$v " <<<"$applied" | awk '{print $2}' || true)
  if [ -z "$prev" ]; then pending+=("$v")
  elif [ "$prev" != "$sum" ]; then drift+=("$v (recorded $prev, now $sum)")
  fi
done

if [ ${#drift[@]} -gt 0 ]; then
  echo "ERROR: these migrations were edited after being applied:" >&2
  printf '  %s\n' "${drift[@]}" >&2
  echo "Write a NEW migration instead; never edit an applied one." >&2
  exit 1
fi

if [ "$MODE" = "--status" ]; then
  echo "applied:"; [ -n "$applied" ] && sed 's/^/  /' <<<"$applied" || echo "  (none)"
  echo "pending:"; [ ${#pending[@]} -gt 0 ] && printf '  %s\n' "${pending[@]}" || echo "  (none)"
  exit 0
fi

if [ ${#pending[@]} -eq 0 ]; then echo "nothing pending"; exit 0; fi
echo "pending: ${pending[*]}"

# A migration owns its own transactions (0002 has two BEGIN/COMMIT pairs),
# so there is no outer transaction to roll back — a "dry run" against the
# real database would simply apply it. Dry runs therefore go against a
# throwaway clone, which is the only way to rehearse honestly.
TARGET="$DB"
if [ "$MODE" = "--dry-run" ]; then
  TARGET="${DB}_migtest"
  # `createdb -T` needs exclusive access to the template, and the API's
  # connection pool holds connections to $DB. Taking the API down to
  # rehearse a migration is the wrong trade, so dump and restore instead.
  # Slower (~30s on the current 282 MB), but the site stays up and the
  # rehearsal includes real data — which matters for migrations that
  # backfill, where a schema-only clone would pass trivially.
  echo "==> cloning $DB → $TARGET via dump (API stays up)"
  ssh "$HOST" "
    sudo -u postgres dropdb --if-exists $TARGET
    sudo -u postgres createdb $TARGET
    sudo -u postgres pg_dump --no-owner --no-privileges $DB \
      | sudo -u postgres psql -q --set ON_ERROR_STOP=1 -d $TARGET >/dev/null"
fi

for v in "${pending[@]}"; do
  f="$DIR/$v.sql"
  sum=$(sha256sum "$f" | cut -c1-16)
  echo "==> $v"
  scp -q "$f" "$HOST:/tmp/mig.sql"
  ssh "$HOST" "sudo -u postgres psql -v ON_ERROR_STOP=1 -q -d $TARGET -f /tmp/mig.sql"
  if [ "$MODE" = "--dry-run" ]; then
    echo "    applies cleanly (on the clone)"
  else
    psql_remote <<<"INSERT INTO schema_migrations(version,checksum) VALUES ('$v','$sum');" >/dev/null
    echo "    applied"
  fi
done

if [ "$MODE" = "--dry-run" ]; then
  ssh "$HOST" "sudo -u postgres dropdb --if-exists $TARGET"
  echo "==> clone dropped; $DB untouched"
fi
echo "==> done"
