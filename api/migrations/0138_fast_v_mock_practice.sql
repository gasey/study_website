BEGIN;

-- Rewrite v_mock_practice and v_bank_answer_status from `id IN (SELECT ...)`
-- to correlated `EXISTS (SELECT 1 FROM ...)` so PostgreSQL pushes point-lookup
-- predicates (`WHERE id = $1`, `EXISTS(SELECT 1 FROM v_mock_practice WHERE id = q.id)`)
-- directly into index scans instead of materializing all 13k rows of v_scorable
-- and all 59k rows of v_reviewed_answer_publications (~4.7s per derived answer click).
-- Result set is 100% identical because canonical_questions.id is NOT NULL.

CREATE OR REPLACE VIEW v_mock_practice AS
SELECT c.*
FROM canonical_questions c
WHERE EXISTS (SELECT 1 FROM v_scorable s WHERE s.id = c.id)
   OR EXISTS (SELECT 1 FROM v_reviewed_answer_publications r WHERE r.canonical_id = c.id);

CREATE OR REPLACE VIEW v_bank_answer_status AS
SELECT q.id,
  CASE
    WHEN q.type <> 'mcq' THEN 'written'
    WHEN q.status = 'held'
      OR q.key_disputed
      OR q.source_defect = ANY (ARRAY['duplicate-options', 'unresolved-source']) THEN 'needs-review'
    WHEN q.answer_text IS NULL THEN 'unsolved'
    WHEN q.answer_source = ANY (ARRAY['official', 'key']) THEN
      CASE
        WHEN valid_scoring_options(q.options) THEN 'official'
        ELSE 'needs-review'
      END
    WHEN q.answer_source = 'derived'
      AND EXISTS (SELECT 1 FROM v_reviewed_answer_publications r WHERE r.canonical_id = q.id) THEN 'verified'
    ELSE 'needs-review'
  END AS answer_status
FROM canonical_questions q;

COMMIT;
