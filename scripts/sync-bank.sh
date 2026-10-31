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
TAXONOMY=${ISM_TAXONOMY:-$ROOT/../mpsc-question-bankv2/taxonomies/question-bank-v2.json}
DRY=${1:-}
case "$DRY" in
  ''|--check|--dry-run|--classifications-only) ;;
  *) echo "usage: $0 [--check|--dry-run|--classifications-only]" >&2; exit 2 ;;
esac
[ "$#" -le 1 ] || { echo "Only one sync mode is allowed" >&2; exit 2; }

# Shared with the bank publication worker. A worker can pass its held lock.
if [ "${ISM_BANK_LOCK_HELD:-}" != "1" ]; then
  exec 9>"${BANK}.lock"
  flock -x 9
fi

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
  LOCAL_CLASS=$(python3 - "$BANK" <<'PY'
import collections, json, sys
data=json.load(open(sys.argv[1]))
c=collections.Counter(claim.get('review_status') for q in data.get('questions', [])
                      for claim in q.get('classifications', []) if claim.get('is_primary'))
print(f"{sum(c.values())}|{c['approved']}|{c['pending']}|{c['rejected']}")
PY
)
  REMOTE_CLASS=$(ssh "$HOST" "sudo -u postgres psql -qtA -F'|' -d $DB -c \"
    SELECT COUNT(*),COUNT(*) FILTER (WHERE review_status='approved'),
           COUNT(*) FILTER (WHERE review_status='pending'),
           COUNT(*) FILTER (WHERE review_status='rejected')
      FROM question_classifications;\"" 2>/dev/null)
  IFS='|' read -r LC_N LC_A LC_P LC_R <<<"$LOCAL_CLASS"
  IFS='|' read -r RC_N RC_A RC_P RC_R <<<"$REMOTE_CLASS"
  echo "local taxonomy : ${LC_N} rows (${LC_A} approved · ${LC_P} pending · ${LC_R} rejected)"
  echo "server taxonomy: ${RC_N} rows (${RC_A} approved · ${RC_P} pending · ${RC_R} rejected)"
  if [ "${REMOTE_SUM:-x}" = "$LOCAL" ]; then
    echo "status      : IN SYNC"
  else
    echo "status      : SERVER IS BEHIND — run ./scripts/sync-bank.sh"
  fi
  [ "${FEEDBACK:-0}" != "0" ] && echo "feedback    : ${FEEDBACK} open proposal(s) from the server — export before editing the bank"
  exit 0
fi

# Taxonomy can be published independently of paper/question text. This path
# touches only the bank-owned classification table; it is useful while the
# legacy bank sync is under audit and never reads or writes learner tables.
if [ "$DRY" = "--classifications-only" ]; then
  TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
  python3 "$ROOT/scripts/bank_to_csv.py" "$BANK" "$TMP/csv" "$TAXONOMY" >/dev/null
  echo "==> publishing taxonomy classifications from $BANK"
  ssh "$HOST" 'rm -rf /tmp/bank-classifications && mkdir -p /tmp/bank-classifications'
  rsync -az -e ssh "$TMP/csv/question_classifications.csv" "$TMP/csv/question_topic_links.csv" "$HOST:/tmp/bank-classifications/"
  ssh "$HOST" 'chmod 755 /tmp/bank-classifications && chmod 644 /tmp/bank-classifications/*.csv'
  ssh "$HOST" "sudo -u postgres psql -v ON_ERROR_STOP=1 -d $DB" <<'SQL'
BEGIN;
CREATE TEMP TABLE s_classifications (question_id TEXT, subject_id TEXT, subject_label TEXT,
    topic_id TEXT, topic_label TEXT, subtopic_id TEXT, subtopic_label TEXT,
    taxonomy_version TEXT, source TEXT, review_status TEXT, confidence NUMERIC,
    evidence TEXT, is_primary BOOL) ON COMMIT DROP;
\copy s_classifications FROM '/tmp/bank-classifications/question_classifications.csv' CSV HEADER
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM s_classifications s
              LEFT JOIN appearances a ON a.id=s.question_id
              LEFT JOIN canonical_questions q ON q.id=a.canonical_id WHERE q.id IS NULL) THEN
    RAISE EXCEPTION 'classification sync contains question IDs absent from canonical_questions';
  END IF;
END $$;
INSERT INTO question_classifications (question_id,subject_id,subject_label,topic_id,topic_label,
    subtopic_id,subtopic_label,taxonomy_version,source,review_status,confidence,evidence,is_primary)
SELECT a.canonical_id,s.subject_id,s.subject_label,s.topic_id,s.topic_label,s.subtopic_id,s.subtopic_label,
       s.taxonomy_version,s.source,s.review_status,s.confidence,s.evidence,s.is_primary
  FROM s_classifications s JOIN appearances a ON a.id=s.question_id
ON CONFLICT (question_id) DO UPDATE SET
    subject_id=EXCLUDED.subject_id, subject_label=EXCLUDED.subject_label,
    topic_id=EXCLUDED.topic_id, topic_label=EXCLUDED.topic_label,
    subtopic_id=EXCLUDED.subtopic_id, subtopic_label=EXCLUDED.subtopic_label,
    taxonomy_version=EXCLUDED.taxonomy_version, source=EXCLUDED.source,
    review_status=EXCLUDED.review_status, confidence=EXCLUDED.confidence,
    evidence=EXCLUDED.evidence, is_primary=EXCLUDED.is_primary, updated_at=now()
WHERE (question_classifications.subject_id,question_classifications.subject_label,question_classifications.topic_id,question_classifications.topic_label,question_classifications.subtopic_id,question_classifications.subtopic_label,question_classifications.taxonomy_version,question_classifications.source,question_classifications.review_status,question_classifications.confidence,question_classifications.evidence,question_classifications.is_primary)
 IS DISTINCT FROM (EXCLUDED.subject_id,EXCLUDED.subject_label,EXCLUDED.topic_id,EXCLUDED.topic_label,EXCLUDED.subtopic_id,EXCLUDED.subtopic_label,EXCLUDED.taxonomy_version,EXCLUDED.source,EXCLUDED.review_status,EXCLUDED.confidence,EXCLUDED.evidence,EXCLUDED.is_primary);
DELETE FROM question_classifications qc
 WHERE NOT EXISTS (SELECT 1 FROM s_classifications s JOIN appearances a ON a.id=s.question_id
                    WHERE a.canonical_id=qc.question_id);

CREATE TEMP TABLE s_links (question_id TEXT,path_id TEXT,subject_id TEXT,subject_label TEXT,topic_id TEXT,topic_label TEXT,subtopic_id TEXT,subtopic_label TEXT,taxonomy_version TEXT,source TEXT,review_status TEXT,evidence TEXT) ON COMMIT DROP;
\copy s_links FROM '/tmp/bank-classifications/question_topic_links.csv' CSV HEADER
DO $$ BEGIN
 IF EXISTS(SELECT 1 FROM s_links l LEFT JOIN appearances a ON a.id=l.question_id WHERE a.canonical_id IS NULL) THEN RAISE EXCEPTION 'Related link target missing'; END IF;
END $$;
INSERT INTO question_topic_links
 SELECT DISTINCT ON (a.canonical_id,l.path_id) a.canonical_id,l.path_id,l.subject_id,l.subject_label,l.topic_id,l.topic_label,l.subtopic_id,l.subtopic_label,l.taxonomy_version,l.source,l.review_status,l.evidence
 FROM s_links l JOIN appearances a ON a.id=l.question_id
 ORDER BY a.canonical_id,l.path_id,a.is_primary DESC,a.id
 ON CONFLICT(question_id,path_id) DO UPDATE SET subject_id=EXCLUDED.subject_id,subject_label=EXCLUDED.subject_label,topic_id=EXCLUDED.topic_id,topic_label=EXCLUDED.topic_label,subtopic_id=EXCLUDED.subtopic_id,subtopic_label=EXCLUDED.subtopic_label,taxonomy_version=EXCLUDED.taxonomy_version,source=EXCLUDED.source,review_status=EXCLUDED.review_status,evidence=EXCLUDED.evidence;
DELETE FROM question_topic_links l WHERE NOT EXISTS(SELECT 1 FROM s_links s JOIN appearances a ON a.id=s.question_id WHERE a.canonical_id=l.question_id AND s.path_id=l.path_id);

SELECT review_status,COUNT(*) FROM question_classifications GROUP BY review_status ORDER BY review_status;
INSERT INTO collections (id,title,kind,route,visibility,position,live_version)
VALUES ('subject-wise-practice','Subject-wise practice','practice','/exams/subject-wise-practice','public',99,1)
ON CONFLICT (id) DO UPDATE SET title=EXCLUDED.title,kind=EXCLUDED.kind,route=EXCLUDED.route,
    visibility=EXCLUDED.visibility,position=EXCLUDED.position,live_version=EXCLUDED.live_version,
    updated_at=now();
DELETE FROM collection_sections WHERE collection_id='subject-wise-practice' AND version=1;
INSERT INTO collection_sections (collection_id,version,path,title,position,formats,query)
SELECT 'subject-wise-practice',1,'subject/'||subjects.subject_id,subjects.subject_label,
       row_number() OVER (ORDER BY subjects.subject_label)::int-1,'{}',
       jsonb_build_object('subject_id',subjects.subject_id)
  FROM (SELECT DISTINCT qc.subject_id,qc.subject_label
          FROM question_classifications qc JOIN v_scorable v ON v.id=qc.question_id
         WHERE qc.review_status='approved') AS subjects;
COMMIT;
SQL
  ssh "$HOST" 'rm -rf /tmp/bank-classifications'
  echo "==> classifications synchronized; no question text, answers, attempts, or accounts changed"
  exit 0
fi

echo "==> source: $BANK ($(du -h "$BANK" | cut -f1))"
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
python3 "$ROOT/scripts/bank_to_csv.py" "$BANK" "$TMP/csv" "$TAXONOMY"

echo "==> uploading"
ssh "$HOST" 'rm -rf /tmp/bank-csv && mkdir -p /tmp/bank-csv'
rsync -az -e ssh "$TMP/csv/" "$HOST:/tmp/bank-csv/"
# The scheduled worker uses umask 077. PostgreSQL must traverse the staging
# directory as well as read these public question-bank CSVs.
ssh "$HOST" 'chmod 755 /tmp/bank-csv && chmod 644 /tmp/bank-csv/*.csv'

# Everything below runs in ONE transaction: it fully applies or not at all.
SQL=$(cat <<'EOSQL'
BEGIN;

CREATE TEMP TABLE s_sittings (id TEXT, exam_name TEXT, exam_type TEXT, year INT, month TEXT) ON COMMIT DROP;
CREATE TEMP TABLE s_papers (id TEXT, exam_type TEXT, exam_name TEXT, post TEXT, paper_number TEXT,
    paper_subject TEXT, year INT, month TEXT, kind TEXT, source_file TEXT, pdf_path TEXT, sitting_id TEXT, exam_scope_id TEXT) ON COMMIT DROP;
CREATE TEMP TABLE s_fg (id TEXT, paper_id TEXT, page INT) ON COMMIT DROP;
CREATE TEMP TABLE s_pg (id TEXT, passage TEXT) ON COMMIT DROP;
CREATE TEMP TABLE s_q (id TEXT, paper_id TEXT, type TEXT, qnum TEXT, qnum_seq INT, page INT,
    question TEXT, direction TEXT, question_markup TEXT, options_markup JSONB,
    source_context_ref TEXT, options JSONB, answer_index INT, answer_source TEXT, answer_key_ref TEXT,
    subject TEXT, topic TEXT, topic_label TEXT, difficulty TEXT, explanation TEXT, marks NUMERIC,
    has_diagram BOOL, used_vision BOOL, figure_group_id TEXT, figure_image TEXT, passage TEXT,
    passage_id TEXT, essay_kind TEXT, review_metadata JSONB) ON COMMIT DROP;
CREATE TEMP TABLE s_classifications (question_id TEXT, subject_id TEXT, subject_label TEXT,
    topic_id TEXT, topic_label TEXT, subtopic_id TEXT, subtopic_label TEXT,
    taxonomy_version TEXT, source TEXT, review_status TEXT, confidence NUMERIC,
    evidence TEXT, is_primary BOOL) ON COMMIT DROP;

\copy s_sittings FROM '/tmp/bank-csv/sittings.csv' CSV HEADER
\copy s_papers   FROM '/tmp/bank-csv/papers.csv' CSV HEADER
\copy s_fg       FROM '/tmp/bank-csv/figure_groups.csv' CSV HEADER
\copy s_pg       FROM '/tmp/bank-csv/passage_groups.csv' CSV HEADER
\copy s_q        FROM '/tmp/bank-csv/questions.csv' CSV HEADER
\copy s_classifications FROM '/tmp/bank-csv/question_classifications.csv' CSV HEADER
CREATE TEMP TABLE s_links (question_id TEXT,path_id TEXT,subject_id TEXT,subject_label TEXT,topic_id TEXT,topic_label TEXT,subtopic_id TEXT,subtopic_label TEXT,taxonomy_version TEXT,source TEXT,review_status TEXT,evidence TEXT) ON COMMIT DROP;
\copy s_links FROM '/tmp/bank-csv/question_topic_links.csv' CSV HEADER


\echo '--- incoming ---'
SELECT (SELECT COUNT(*) FROM s_papers) AS papers, (SELECT COUNT(*) FROM s_q) AS questions;
SELECT COUNT(*) AS taxonomy_classifications FROM s_classifications;
\echo '--- new / changed appearances ---'
SELECT COUNT(*) FILTER (WHERE a.id IS NULL) AS new,
       COUNT(*) FILTER (WHERE a.id IS NOT NULL AND
             (a.question IS DISTINCT FROM s.question
           OR a.direction IS DISTINCT FROM s.direction
           OR a.question_markup IS DISTINCT FROM s.question_markup
           OR a.options_markup IS DISTINCT FROM s.options_markup
           OR a.passage IS DISTINCT FROM s.passage
           OR a.source_context_ref IS DISTINCT FROM s.source_context_ref
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

INSERT INTO papers (id,exam_type,exam_name,post,paper_number,paper_subject,year,month,kind,source_file,pdf_path,sitting_id,exam_scope_id)
  SELECT * FROM s_papers
  ON CONFLICT (id) DO UPDATE SET exam_type=EXCLUDED.exam_type, exam_name=EXCLUDED.exam_name,
    post=EXCLUDED.post, paper_number=EXCLUDED.paper_number, paper_subject=EXCLUDED.paper_subject,
    year=EXCLUDED.year, month=EXCLUDED.month, kind=EXCLUDED.kind,
    source_file=EXCLUDED.source_file, pdf_path=EXCLUDED.pdf_path, sitting_id=EXCLUDED.sitting_id,
    exam_scope_id=COALESCE(EXCLUDED.exam_scope_id,papers.exam_scope_id);

INSERT INTO figure_groups SELECT * FROM s_fg ON CONFLICT (id) DO UPDATE
  SET paper_id=EXCLUDED.paper_id, page=EXCLUDED.page;
INSERT INTO passage_groups SELECT * FROM s_pg ON CONFLICT (id) DO UPDATE
  SET passage=EXCLUDED.passage;

ALTER TABLE appearances DISABLE TRIGGER app_counts;

-- A canonical row must exist BEFORE its appearance: appearances.canonical_id
-- is NOT NULL with an FK, and ON CONFLICT DO UPDATE does not rescue a NOT
-- NULL violation — the proposed row is validated before the conflict is
-- detected. So new canonicals are created first, from staging.
INSERT INTO canonical_questions (id, type, question, direction, question_markup, options_markup,
                                 passage, source_context_ref, options, answer_text, answer_source,
                                 answer_key_ref, status, stem_norm)
SELECT 'cq_' || substr(md5(s.id), 1, 16), s.type, s.question, s.direction, s.question_markup,
       s.options_markup, s.passage, s.source_context_ref, s.options,
       CASE WHEN s.answer_index IS NOT NULL THEN s.options ->> s.answer_index END,
       COALESCE(s.answer_source, 'none'), s.answer_key_ref, 'live', norm_stem(s.question)
  FROM s_q s
 WHERE NOT EXISTS (SELECT 1 FROM appearances a WHERE a.id = s.id)
ON CONFLICT (id) DO NOTHING;

-- Bank-owned columns only. canonical_id is set for NEW rows and deliberately
-- left out of the DO UPDATE list, so a row the dedupe job has since merged
-- keeps pointing at its merge target. option_order / is_primary / bbox are
-- likewise migration- and dedupe-owned, not sourced from the JSON.
INSERT INTO appearances (id,paper_id,type,qnum,qnum_seq,page,question,direction,question_markup,
    options_markup,source_context_ref,options,answer_index,
    answer_source,answer_key_ref,subject,topic,difficulty,explanation,marks,has_diagram,
    used_vision,figure_group_id,figure_image,passage,passage_id,essay_kind,
    canonical_id,option_order,is_primary)
  SELECT id,paper_id,type,qnum,qnum_seq,page,question,direction,question_markup,
         options_markup,source_context_ref,options,answer_index,answer_source,
         answer_key_ref,subject,topic,difficulty,explanation,marks,has_diagram,used_vision,
         figure_group_id,figure_image,passage,passage_id,essay_kind,
         'cq_' || substr(md5(id), 1, 16),
         CASE WHEN jsonb_array_length(options) > 0
              THEN ARRAY(SELECT generate_series(0, jsonb_array_length(options) - 1)) END,
         true
    FROM s_q
  ON CONFLICT (id) DO UPDATE SET
    paper_id=EXCLUDED.paper_id, type=EXCLUDED.type, qnum=EXCLUDED.qnum, qnum_seq=EXCLUDED.qnum_seq,
    page=EXCLUDED.page, question=EXCLUDED.question, direction=EXCLUDED.direction,
    question_markup=EXCLUDED.question_markup, options_markup=EXCLUDED.options_markup,
    source_context_ref=EXCLUDED.source_context_ref,
    options=EXCLUDED.options,
    option_order=CASE
      WHEN appearances.option_order IS NOT NULL
       AND array_length(appearances.option_order,1) IS DISTINCT FROM jsonb_array_length(EXCLUDED.options)
      THEN CASE WHEN jsonb_array_length(EXCLUDED.options)>0
                THEN ARRAY(SELECT generate_series(0,jsonb_array_length(EXCLUDED.options)-1))
                ELSE NULL END
      ELSE appearances.option_order
    END,
    difficulty=EXCLUDED.difficulty,
    answer_index=EXCLUDED.answer_index, answer_source=EXCLUDED.answer_source,
    answer_key_ref=EXCLUDED.answer_key_ref, explanation=EXCLUDED.explanation, marks=EXCLUDED.marks,
    has_diagram=EXCLUDED.has_diagram, used_vision=EXCLUDED.used_vision,
    figure_group_id=EXCLUDED.figure_group_id, figure_image=EXCLUDED.figure_image,
    passage=EXCLUDED.passage, passage_id=EXCLUDED.passage_id, essay_kind=EXCLUDED.essay_kind
  WHERE (appearances.paper_id,appearances.type,appearances.qnum,appearances.qnum_seq,appearances.page,appearances.question,appearances.direction,appearances.question_markup,appearances.options_markup,appearances.source_context_ref,appearances.options,appearances.difficulty,appearances.answer_index,appearances.answer_source,appearances.answer_key_ref,appearances.explanation,appearances.marks,appearances.has_diagram,appearances.used_vision,appearances.figure_group_id,appearances.figure_image,appearances.passage,appearances.passage_id,appearances.essay_kind)
    IS DISTINCT FROM (EXCLUDED.paper_id,EXCLUDED.type,EXCLUDED.qnum,EXCLUDED.qnum_seq,EXCLUDED.page,EXCLUDED.question,EXCLUDED.direction,EXCLUDED.question_markup,EXCLUDED.options_markup,EXCLUDED.source_context_ref,EXCLUDED.options,EXCLUDED.difficulty,EXCLUDED.answer_index,EXCLUDED.answer_source,EXCLUDED.answer_key_ref,EXCLUDED.explanation,EXCLUDED.marks,EXCLUDED.has_diagram,EXCLUDED.used_vision,EXCLUDED.figure_group_id,EXCLUDED.figure_image,EXCLUDED.passage,EXCLUDED.passage_id,EXCLUDED.essay_kind)
     OR (appearances.option_order IS NOT NULL
         AND array_length(appearances.option_order,1) IS DISTINCT FROM jsonb_array_length(EXCLUDED.options));

-- Propagate edited text/options/keys from the primary printing. This is what
-- makes local authoritative: a typo fixed in the JSON reaches the canonical
-- row. It also overwrites any server-side edit to the same columns, which is
-- the documented trade-off in DECISIONS.md #5.
UPDATE canonical_questions c SET
    question = a.question,
    direction = a.direction,
    question_markup = a.question_markup,
    options_markup = a.options_markup,
    passage = a.passage,
    source_context_ref = a.source_context_ref,
    options = a.options,
    answer_text = CASE WHEN a.answer_index IS NOT NULL AND c.status <> 'withdrawn'
                       THEN a.options ->> a.answer_index END,
    answer_source = COALESCE(a.answer_source, 'none'),
    answer_key_ref = a.answer_key_ref,
    -- explanation was missing here, which cost a whole harvest: 43,018
    -- explanations landed in appearances and 18 reached canonical, so the
    -- API — which reads canonical — showed none of them. Any bank-owned
    -- column added to the appearances upsert above must also be listed
    -- here AND in the change-detection below, or it silently stops halfway.
    explanation = NULLIF(a.explanation, ''),
    -- Retired learner difficulty must not be reintroduced from raw archive metadata.
    difficulty = NULL,
    stem_norm = norm_stem(a.question),
    updated_at = now()
  FROM appearances a
 WHERE a.canonical_id = c.id AND a.is_primary
   AND (c.question IS DISTINCT FROM a.question OR c.options IS DISTINCT FROM a.options
     OR c.direction IS DISTINCT FROM a.direction
     OR c.question_markup IS DISTINCT FROM a.question_markup
     OR c.options_markup IS DISTINCT FROM a.options_markup
     OR c.passage IS DISTINCT FROM a.passage
     OR c.source_context_ref IS DISTINCT FROM a.source_context_ref
     OR c.answer_text IS DISTINCT FROM (CASE WHEN a.answer_index IS NOT NULL AND c.status <> 'withdrawn' THEN a.options ->> a.answer_index END)
     OR c.answer_source IS DISTINCT FROM COALESCE(a.answer_source, 'none')
     OR c.answer_key_ref IS DISTINCT FROM a.answer_key_ref
     OR c.difficulty IS NOT NULL
     OR c.explanation IS DISTINCT FROM NULLIF(a.explanation, ''));

-- Explicit publication metadata only; absent JSON keys preserve prior reviewed defects.
UPDATE canonical_questions c SET
    source_defect=CASE WHEN s.review_metadata ? 'sourceDefect' THEN s.review_metadata->>'sourceDefect' ELSE c.source_defect END,
    dispute_note=CASE WHEN s.review_metadata ? 'disputeNote' THEN s.review_metadata->>'disputeNote' ELSE c.dispute_note END,
    updated_at=now()
  FROM appearances a JOIN s_q s ON s.id=a.id
 WHERE a.canonical_id=c.id AND a.is_primary
   AND ((s.review_metadata ? 'sourceDefect' AND c.source_defect IS DISTINCT FROM s.review_metadata->>'sourceDefect')
     OR (s.review_metadata ? 'disputeNote' AND c.dispute_note IS DISTINCT FROM s.review_metadata->>'disputeNote'));

UPDATE canonical_questions c SET times_asked = GREATEST(1, s.n), first_year = s.y0,
       last_year = s.y1, updated_at = now()
  FROM (SELECT a.canonical_id AS cid, COUNT(DISTINCT COALESCE(p.sitting_id, p.id)) AS n,
               MIN(p.year) AS y0, MAX(p.year) AS y1
          FROM appearances a JOIN papers p ON p.id = a.paper_id
         WHERE a.canonical_id IS NOT NULL GROUP BY a.canonical_id) s
 WHERE c.id = s.cid AND (c.times_asked, c.first_year, c.last_year)
       IS DISTINCT FROM (GREATEST(1, s.n), s.y0, s.y1);

ALTER TABLE appearances ENABLE TRIGGER app_counts;

-- Taxonomy-v2 is separate from the legacy subject/topic columns. The full
-- selected path and its review provenance are synchronized as bank data.
INSERT INTO question_classifications (question_id,subject_id,subject_label,topic_id,topic_label,
    subtopic_id,subtopic_label,taxonomy_version,source,review_status,confidence,evidence,is_primary)
SELECT a.canonical_id,s.subject_id,s.subject_label,s.topic_id,s.topic_label,s.subtopic_id,s.subtopic_label,
       s.taxonomy_version,s.source,s.review_status,s.confidence,s.evidence,s.is_primary
  FROM s_classifications s JOIN appearances a ON a.id=s.question_id
ON CONFLICT (question_id) DO UPDATE SET
    subject_id=EXCLUDED.subject_id, subject_label=EXCLUDED.subject_label,
    topic_id=EXCLUDED.topic_id, topic_label=EXCLUDED.topic_label,
    subtopic_id=EXCLUDED.subtopic_id, subtopic_label=EXCLUDED.subtopic_label,
    taxonomy_version=EXCLUDED.taxonomy_version, source=EXCLUDED.source,
    review_status=EXCLUDED.review_status, confidence=EXCLUDED.confidence,
    evidence=EXCLUDED.evidence, is_primary=EXCLUDED.is_primary, updated_at=now()
WHERE (question_classifications.subject_id,question_classifications.subject_label,question_classifications.topic_id,question_classifications.topic_label,question_classifications.subtopic_id,question_classifications.subtopic_label,question_classifications.taxonomy_version,question_classifications.source,question_classifications.review_status,question_classifications.confidence,question_classifications.evidence,question_classifications.is_primary)
 IS DISTINCT FROM (EXCLUDED.subject_id,EXCLUDED.subject_label,EXCLUDED.topic_id,EXCLUDED.topic_label,EXCLUDED.subtopic_id,EXCLUDED.subtopic_label,EXCLUDED.taxonomy_version,EXCLUDED.source,EXCLUDED.review_status,EXCLUDED.confidence,EXCLUDED.evidence,EXCLUDED.is_primary);

DELETE FROM question_classifications qc
 WHERE NOT EXISTS (SELECT 1 FROM s_classifications s JOIN appearances a ON a.id=s.question_id
                    WHERE a.canonical_id=qc.question_id);
DO $$ BEGIN
 IF EXISTS(SELECT 1 FROM s_links l LEFT JOIN appearances a ON a.id=l.question_id WHERE a.canonical_id IS NULL) THEN RAISE EXCEPTION 'Related link target missing'; END IF;
END $$;
INSERT INTO question_topic_links
 SELECT DISTINCT ON (a.canonical_id,l.path_id) a.canonical_id,l.path_id,l.subject_id,l.subject_label,l.topic_id,l.topic_label,l.subtopic_id,l.subtopic_label,l.taxonomy_version,l.source,l.review_status,l.evidence
 FROM s_links l JOIN appearances a ON a.id=l.question_id
 ORDER BY a.canonical_id,l.path_id,a.is_primary DESC,a.id
 ON CONFLICT(question_id,path_id) DO UPDATE SET subject_id=EXCLUDED.subject_id,subject_label=EXCLUDED.subject_label,topic_id=EXCLUDED.topic_id,topic_label=EXCLUDED.topic_label,subtopic_id=EXCLUDED.subtopic_id,subtopic_label=EXCLUDED.subtopic_label,taxonomy_version=EXCLUDED.taxonomy_version,source=EXCLUDED.source,review_status=EXCLUDED.review_status,evidence=EXCLUDED.evidence;
DELETE FROM question_topic_links l WHERE NOT EXISTS(SELECT 1 FROM s_links s JOIN appearances a ON a.id=s.question_id WHERE a.canonical_id=l.question_id AND s.path_id=l.path_id);

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

UPDATE canonical_questions c SET status='held',held_reason=h.reason
 FROM review_holds h WHERE h.canonical_id=c.id AND h.released_at IS NULL AND c.status='live';

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
