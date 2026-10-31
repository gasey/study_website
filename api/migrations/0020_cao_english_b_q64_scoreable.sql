-- Q64 has one omitted distractor on the scanned booklet, not duplicate option
-- text. The final key unambiguously marks the printed option “between”. The
-- v3 preflight counted JSON null as a duplicate because it compared the
-- distinct non-null option values to the four-slot array length. Clear only
-- this source defect after asserting the exact paper, choices and official key.
BEGIN;
UPDATE canonical_questions q
   SET source_defect = NULL, updated_at = now()
 WHERE q.id = 'cq_1181d6983db9f6da'
   AND q.type = 'mcq'
   AND q.answer_text = 'between'
   AND q.options = '["among","between","across",null]'::jsonb
   AND q.source_defect = 'duplicate-options'
   AND EXISTS (
       SELECT 1 FROM appearances a
        WHERE a.canonical_id = q.id
          AND a.paper_id = 'Old_Questions/Direct_2025-2027/CAO March-2026 General English (Series B)..pdf'
          AND a.qnum = '64'
   );
COMMIT;
