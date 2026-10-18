#!/usr/bin/env bash
# Push the locally-authored question bank to the server.
#
# Local is the source of truth for BANK data; the server database is a
# derived artifact (docs/DECISIONS.md #5). This script is one-way and
# re-runnable.
#
# It touches ONLY: sittings, papers, figure_groups, passage_groups,
# appearances, canonical_questions.
# It never touches: users, attempts, posts, post_votes, content_reports,
# abuse_reports, materials, moderators, mod_actions, sanctions, appeals.
# Those exist only on the server and cannot be restored from anywhere.
#
#   ./scripts/sync-bank.sh --dry-run   # report what would change
#   ./scripts/sync-bank.sh             # apply
set -euo pipefail

HOST=${ISM_HOST:-ubuntu@152.67.31.231}
DB=${ISM_DB:-mpsc}
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BANK=${ISM_BANK:-$ROOT/../mpsc-question-bankv2/bank/mpsc_bank_v2.json}
DRY=${1:-}

[ -f "$BANK" ] || { echo "bank not found: $BANK" >&2; exit 1; }

# --check answers the question parallel work actually raises: is the server
# running the bank I have in front of me, and has it anything to send back?
if [ "$DRY" = "--check" ]; then
  LOCAL=$(sha256sum "$BANK" | cut -c1-64)
  # Pipe-separated. Not space (the timestamp contains one, which silently
  # shifted every later field) and not \t (it survives the quoting as a
  # literal backslash-t, so nothing splits at all).
  IFS='|' read -r REMOTE_SUM REMOTE_N REMOTE_AT FEEDBACK <<<"$(ssh "$HOST" \
    "sudo -u postgres psql -qtA -F'|' -d $DB -c \"
       SELECT COALESCE(bank_checksum,'none'), COALESCE(questions_in,0),
              COALESCE(to_char(finished_at,'YYYY-MM-DD HH24:MI'),'never'),
              COALESCE(open_feedback,0)
         FROM v_sync_state;\"" 2>/dev/null)"
  echo "local  bank : ${LOCAL:0:12}…  $(python3 -c "import json,sys;print(len(json.load(open(sys.argv[1]))['questions']))" "$BANK") questions"
  echo "server bank : ${REMOTE_SUM:0:12}…  ${REMOTE_N:-?} questions  (last sync ${REMOTE_AT:-?})"
  if [ "${REMOTE_SUM:-x}" = "$LOCAL" ]; then
    echo "status      : IN SYNC"
  else
    echo "status      : SERVER IS BEHIND — run ./scripts/sync-bank.sh"
  fi
  [ "${FEEDBACK:-0}" != "0" ] && echo "feedback    : ${FEEDBACK} open proposal(s) from the server — export before editing the bank"
  exit 0
fi

echo "==> source: $BANK ($(du -h "$BANK" | cut -f1))"
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
python3 "$ROOT/scripts/bank_to_csv.py" "$BANK" "$TMP/csv"

echo "==> uploading"
ssh "$HOST" 'rm -rf /tmp/bank-csv && mkdir -p /tmp/bank-csv'
rsync -az -e ssh "$TMP/csv/" "$HOST:/tmp/bank-csv/"
ssh "$HOST" 'chmod 644 /tmp/bank-csv/*.csv'

# Everything below runs in ONE transaction: it fully applies or not at all.
SQL=$(cat <<'EOSQL'
BEGIN;

CREATE TEMP TABLE s_sittings (id TEXT, exam_name TEXT, exam_type TEXT, year INT, month TEXT) ON COMMIT DROP;
CREATE TEMP TABLE s_papers (id TEXT, exam_type TEXT, exam_name TEXT, post TEXT, paper_number TEXT,
    paper_subject TEXT, year INT, month TEXT, kind TEXT, source_file TEXT, pdf_path TEXT, sitting_id TEXT) ON COMMIT DROP;
CREATE TEMP TABLE s_fg (id TEXT, paper_id TEXT, page INT) ON COMMIT DROP;
CREATE TEMP TABLE s_pg (id TEXT, passage TEXT) ON COMMIT DROP;
CREATE TEMP TABLE s_q (id TEXT, paper_id TEXT, type TEXT, qnum TEXT, qnum_seq INT, page INT,
    question TEXT, options JSONB, answer_index INT, answer_source TEXT, answer_key_ref TEXT,
    subject TEXT, topic TEXT, topic_label TEXT, difficulty TEXT, explanation TEXT, marks NUMERIC,
    has_diagram BOOL, used_vision BOOL, figure_group_id TEXT, figure_image TEXT, passage TEXT,
    passage_id TEXT, essay_kind TEXT) ON COMMIT DROP;

\copy s_sittings FROM '/tmp/bank-csv/sittings.csv' CSV HEADER
\copy s_papers   FROM '/tmp/bank-csv/papers.csv' CSV HEADER
\copy s_fg       FROM '/tmp/bank-csv/figure_groups.csv' CSV HEADER
\copy s_pg       FROM '/tmp/bank-csv/passage_groups.csv' CSV HEADER
\copy s_q        FROM '/tmp/bank-csv/questions.csv' CSV HEADER

\echo '--- incoming ---'
SELECT (SELECT COUNT(*) FROM s_papers) AS papers, (SELECT COUNT(*) FROM s_q) AS questions;
\echo '--- new / changed appearances ---'
SELECT COUNT(*) FILTER (WHERE a.id IS NULL) AS new,
       COUNT(*) FILTER (WHERE a.id IS NOT NULL AND
             (a.question IS DISTINCT FROM s.question
           OR a.options  IS DISTINCT FROM s.options
           OR a.answer_index IS DISTINCT FROM s.answer_index
           OR a.answer_source IS DISTINCT FROM s.answer_source)) AS changed
  FROM s_q s LEFT JOIN appearances a ON a.id = s.id;
\echo '--- user data that must survive ---'
SELECT (SELECT COUNT(*) FROM attempts) AS attempts, (SELECT COUNT(*) FROM users) AS users;
EOSQL
)

APPLY=$(cat <<'EOSQL'
INSERT INTO sittings SELECT * FROM s_sittings
  ON CONFLICT (id) DO UPDATE SET exam_name=EXCLUDED.exam_name, exam_type=EXCLUDED.exam_type,
    year=EXCLUDED.year, month=EXCLUDED.month;

INSERT INTO papers (id,exam_type,exam_name,post,paper_number,paper_subject,year,month,kind,source_file,pdf_path,sitting_id)
  SELECT * FROM s_papers
  ON CONFLICT (id) DO UPDATE SET exam_type=EXCLUDED.exam_type, exam_name=EXCLUDED.exam_name,
    post=EXCLUDED.post, paper_number=EXCLUDED.paper_number, paper_subject=EXCLUDED.paper_subject,
    year=EXCLUDED.year, month=EXCLUDED.month, kind=EXCLUDED.kind,
    source_file=EXCLUDED.source_file, pdf_path=EXCLUDED.pdf_path, sitting_id=EXCLUDED.sitting_id;

INSERT INTO figure_groups SELECT * FROM s_fg ON CONFLICT (id) DO UPDATE
  SET paper_id=EXCLUDED.paper_id, page=EXCLUDED.page;
INSERT INTO passage_groups SELECT * FROM s_pg ON CONFLICT (id) DO UPDATE
  SET passage=EXCLUDED.passage;

ALTER TABLE appearances DISABLE TRIGGER app_counts;

-- A canonical row must exist BEFORE its appearance: appearances.canonical_id
-- is NOT NULL with an FK, and ON CONFLICT DO UPDATE does not rescue a NOT
-- NULL violation — the proposed row is validated before the conflict is
-- detected. So new canonicals are created first, from staging.
INSERT INTO canonical_questions (id, type, question, options, answer_text, answer_source,
                                 answer_key_ref, status, stem_norm)
SELECT 'cq_' || substr(md5(s.id), 1, 16), s.type, s.question, s.options,
       CASE WHEN s.answer_index IS NOT NULL THEN s.options ->> s.answer_index END,
       COALESCE(s.answer_source, 'none'), s.answer_key_ref, 'live', norm_stem(s.question)
  FROM s_q s
 WHERE NOT EXISTS (SELECT 1 FROM appearances a WHERE a.id = s.id)
ON CONFLICT (id) DO NOTHING;

-- Bank-owned columns only. canonical_id is set for NEW rows and deliberately
-- left out of the DO UPDATE list, so a row the dedupe job has since merged
-- keeps pointing at its merge target. option_order / is_primary / bbox are
-- likewise migration- and dedupe-owned, not sourced from the JSON.
INSERT INTO appearances (id,paper_id,type,qnum,qnum_seq,page,question,options,answer_index,
    answer_source,answer_key_ref,subject,topic,difficulty,explanation,marks,has_diagram,
    used_vision,figure_group_id,figure_image,passage,passage_id,essay_kind,
    canonical_id,option_order,is_primary)
  SELECT id,paper_id,type,qnum,qnum_seq,page,question,options,answer_index,answer_source,
         answer_key_ref,subject,topic,difficulty,explanation,marks,has_diagram,used_vision,
         figure_group_id,figure_image,passage,passage_id,essay_kind,
         'cq_' || substr(md5(id), 1, 16),
         CASE WHEN jsonb_array_length(options) > 0
              THEN ARRAY(SELECT generate_series(0, jsonb_array_length(options) - 1)) END,
         true
    FROM s_q
  ON CONFLICT (id) DO UPDATE SET
    paper_id=EXCLUDED.paper_id, type=EXCLUDED.type, qnum=EXCLUDED.qnum, qnum_seq=EXCLUDED.qnum_seq,
    page=EXCLUDED.page, question=EXCLUDED.question, options=EXCLUDED.options,
    answer_index=EXCLUDED.answer_index, answer_source=EXCLUDED.answer_source,
    answer_key_ref=EXCLUDED.answer_key_ref, explanation=EXCLUDED.explanation, marks=EXCLUDED.marks,
    has_diagram=EXCLUDED.has_diagram, used_vision=EXCLUDED.used_vision,
    figure_group_id=EXCLUDED.figure_group_id, figure_image=EXCLUDED.figure_image,
    passage=EXCLUDED.passage, passage_id=EXCLUDED.passage_id, essay_kind=EXCLUDED.essay_kind;

-- Propagate edited text/options/keys from the primary printing. This is what
-- makes local authoritative: a typo fixed in the JSON reaches the canonical
-- row. It also overwrites any server-side edit to the same columns, which is
-- the documented trade-off in DECISIONS.md #5.
UPDATE canonical_questions c SET
    question = a.question,
    options = a.options,
    answer_text = CASE WHEN a.answer_index IS NOT NULL AND c.status <> 'withdrawn'
                       THEN a.options ->> a.answer_index END,
    answer_source = COALESCE(a.answer_source, 'none'),
    stem_norm = norm_stem(a.question),
    updated_at = now()
  FROM appearances a
 WHERE a.canonical_id = c.id AND a.is_primary
   AND (c.question IS DISTINCT FROM a.question OR c.options IS DISTINCT FROM a.options
     OR c.answer_source IS DISTINCT FROM COALESCE(a.answer_source, 'none'));

UPDATE canonical_questions c SET times_asked = GREATEST(1, s.n), first_year = s.y0,
       last_year = s.y1, updated_at = now()
  FROM (SELECT a.canonical_id AS cid, COUNT(DISTINCT COALESCE(p.sitting_id, p.id)) AS n,
               MIN(p.year) AS y0, MAX(p.year) AS y1
          FROM appearances a JOIN papers p ON p.id = a.paper_id
         WHERE a.canonical_id IS NOT NULL GROUP BY a.canonical_id) s
 WHERE c.id = s.cid AND (c.times_asked, c.first_year, c.last_year)
       IS DISTINCT FROM (GREATEST(1, s.n), s.y0, s.y1);

ALTER TABLE appearances ENABLE TRIGGER app_counts;
EOSQL
)

if [ "$DRY" = "--dry-run" ]; then
  echo "==> DRY RUN (nothing is written)"
  ssh "$HOST" "sudo -u postgres psql -v ON_ERROR_STOP=1 -d $DB" <<< "$SQL
ROLLBACK;"
else
  # Record which bank version this sync carries. Without it nobody can
  # answer "is the server running the bank in front of me?", and parallel
  # work drifts silently.
  SUM=$(sha256sum "$BANK" | cut -c1-64)
  BYTES=$(stat -c%s "$BANK")
  NQ=$(python3 -c "import json,sys;print(len(json.load(open(sys.argv[1]))['questions']))" "$BANK")
  WHO="${USER:-unknown}@$(hostname -s)"
  echo "==> bank ${SUM:0:12}… · ${NQ} questions"

  echo "==> applying"
  ssh "$HOST" "sudo -u postgres psql -v ON_ERROR_STOP=1 -d $DB" <<< "$SQL
-- Capture the before-counts as psql variables so the deltas recorded below
-- are real deltas, not totals wearing a delta's name.
SELECT COUNT(*) AS cq_before FROM canonical_questions \gset
SELECT COUNT(*) AS ap_before FROM appearances \gset
SELECT COUNT(*) AS at_before FROM attempts \gset

INSERT INTO sync_log (bank_checksum, bank_bytes, questions_in, attempts_before, ran_by)
VALUES ('$SUM', $BYTES, $NQ, :at_before, '$WHO');

$APPLY

UPDATE sync_log SET
    finished_at     = now(),
    attempts_after  = (SELECT COUNT(*) FROM attempts),
    canonical_new   = (SELECT COUNT(*) FROM canonical_questions) - :cq_before,
    canonical_upd   = (SELECT COUNT(*) FROM canonical_questions
                        WHERE updated_at > now() - interval '5 minutes'),
    appearances_new = (SELECT COUNT(*) FROM appearances) - :ap_before
  WHERE id = (SELECT MAX(id) FROM sync_log);
COMMIT;"
  echo "==> after"
  ssh "$HOST" "sudo -u postgres psql -tA -d $DB -c \"
    SELECT 'canonical='||COUNT(*) FROM canonical_questions
    UNION ALL SELECT 'scorable='||COUNT(*) FROM v_scorable
    UNION ALL SELECT 'attempts='||COUNT(*) FROM attempts;\""
fi
echo "==> done"
