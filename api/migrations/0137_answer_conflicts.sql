BEGIN;

-- Phase V.17 (§VII.6.2, §VII.6.3): Key-versus-solution conflicts materialised view.
-- Mirrors `services/answer_comparison.py` `published_comparison()`.
-- Shape B ('key-won'): official/key stands in canonical_questions.answer_text while
-- an applied mode='verified' + preserve_official_key publication disagrees with it.
-- Shape A ('solution-won'): derived answer stands in canonical_questions.answer_text
-- while an applied official-key publication exists in history with a different answer.
--
-- Per §VII.6.3 Step 5 (owner-locked 22 Nov 2026): this migration ships the matview
-- and read-only ops/triage visibility first, WITHOUT subtracting from `v_scorable`
-- until the live clone Shape B count and >5-per-paper cluster gate are inspected.

CREATE MATERIALIZED VIEW IF NOT EXISTS v_answer_conflicts AS
SELECT c.id AS canonical_id,
       a.paper_id,
       a.qnum,
       'key-won'::text AS shape,
       c.answer_text AS official_answer,
       p.manifest->'admin_decision'->>'solution_answer_text' AS solution_answer,
       p.id AS solution_publication_id,
       p.finished_at AS detected_from
  FROM canonical_questions c
  JOIN bank_contributions b ON b.canonical_id = c.id
  JOIN bank_publications p ON p.contribution_id = b.id
  JOIN appearances a ON a.id = b.appearance_id AND a.is_primary
 WHERE c.status = 'live'
   AND c.type = 'mcq'
   AND c.answer_source IN ('official', 'key')
   AND NOT c.key_disputed
   AND b.state = 'published'
   AND p.state = 'applied'
   AND p.manifest->'admin_decision'->>'mode' = 'verified'
   AND COALESCE((p.manifest->'admin_decision'->>'preserve_official_key')::boolean, false)
   AND p.manifest->'admin_decision'->>'solution_answer_text' IS NOT NULL
   AND p.manifest->'admin_decision'->>'solution_answer_text' IS DISTINCT FROM c.answer_text
   AND p.receipt->'after'->>'question' = c.question
   AND p.receipt->'after'->'options' = c.options
UNION ALL
SELECT c.id AS canonical_id,
       a.paper_id,
       a.qnum,
       'solution-won'::text AS shape,
       p.receipt->'after'->'options'->>((p.receipt->'after'->>'answerIndex')::int) AS official_answer,
       c.answer_text AS solution_answer,
       p.id AS solution_publication_id,
       p.finished_at AS detected_from
  FROM canonical_questions c
  JOIN bank_contributions b ON b.canonical_id = c.id
  JOIN bank_publications p ON p.contribution_id = b.id
  JOIN appearances a ON a.id = b.appearance_id AND a.is_primary
 WHERE c.status = 'live'
   AND c.type = 'mcq'
   AND c.answer_source = 'derived'
   AND b.state = 'published'
   AND p.state = 'applied'
   AND p.manifest->'admin_decision'->>'mode' = 'official'
   AND jsonb_typeof(p.receipt->'after'->'answerIndex') = 'number'
   AND p.receipt->'after'->>'question' = c.question
   AND p.receipt->'after'->'options' = c.options
   AND (p.receipt->'after'->'options'->>((p.receipt->'after'->>'answerIndex')::int))
       IS DISTINCT FROM c.answer_text;

CREATE UNIQUE INDEX IF NOT EXISTS idx_v_answer_conflicts_pk
  ON v_answer_conflicts (canonical_id, solution_publication_id, shape);

CREATE INDEX IF NOT EXISTS idx_v_answer_conflicts_paper
  ON v_answer_conflicts (paper_id, shape);

GRANT SELECT ON v_answer_conflicts TO mpsc;

COMMIT;
