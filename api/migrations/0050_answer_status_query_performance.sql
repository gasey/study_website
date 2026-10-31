BEGIN;
-- Same classification, but compute the reviewed set once, and validate options
-- only for official/key candidates. Unreviewed derived answers already need review.
CREATE OR REPLACE VIEW v_bank_answer_status AS SELECT q.id,
 CASE WHEN q.type<>'mcq' THEN 'written'
 WHEN q.status='held' OR q.key_disputed OR q.source_defect IN ('duplicate-options','unresolved-source') THEN 'needs-review'
 WHEN q.answer_text IS NULL THEN 'unsolved'
 WHEN q.answer_source IN ('official','key') THEN CASE WHEN valid_scoring_options(q.options) THEN 'official' ELSE 'needs-review' END
 WHEN q.answer_source='derived' AND q.id IN (SELECT r.canonical_id FROM v_reviewed_answer_publications r) THEN 'verified'
 ELSE 'needs-review' END AS answer_status FROM canonical_questions q;
COMMIT;
