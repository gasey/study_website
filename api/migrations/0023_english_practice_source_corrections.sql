-- Store user-facing provenance for explicit English practice corrections.
-- The bank has clearly labeled supplemental options where the paper's choices
-- contain no correct answer. The Geologist figure artwork remains in its PDF.
BEGIN;
ALTER TABLE canonical_questions
  DROP CONSTRAINT IF EXISTS canonical_questions_source_defect_check;
ALTER TABLE canonical_questions
  ADD CONSTRAINT canonical_questions_source_defect_check CHECK (
    source_defect IN ('duplicate-options','hand-transcribed-matching-table',
                      'correct-option-added','diagram-not-embedded')
  );
UPDATE canonical_questions q
   SET source_defect = CASE q.id
         WHEN 'cq_bcbd65c36346a9bd' THEN 'correct-option-added'
         WHEN 'cq_593a85bf4293080a' THEN 'correct-option-added'
         WHEN 'cq_04d17b292766eb03' THEN 'correct-option-added'
         WHEN 'cq_274ae8f11fc9264d' THEN 'correct-option-added'
         WHEN 'cq_b592387c54fa34e0' THEN 'diagram-not-embedded'
       END,
       dispute_note = CASE q.id
         WHEN 'cq_bcbd65c36346a9bd' THEN 'The paper choices omit the synonym of apathy; the appended answer is an explicit practice correction.'
         WHEN 'cq_593a85bf4293080a' THEN 'The paper choices omit the synonym of puerility; the appended answer is an explicit practice correction.'
         WHEN 'cq_04d17b292766eb03' THEN 'The paper choices omit the meaning of judicious; the appended answer is an explicit practice correction.'
         WHEN 'cq_274ae8f11fc9264d' THEN 'The paper choices omit “preposition”; the appended answer is an explicit practice correction.'
         WHEN 'cq_b592387c54fa34e0' THEN 'The figure artwork is available in the original paper PDF but was not embedded in the question extraction.'
       END,
       updated_at = now()
 WHERE q.id IN (
   'cq_bcbd65c36346a9bd','cq_593a85bf4293080a','cq_04d17b292766eb03',
   'cq_274ae8f11fc9264d','cq_b592387c54fa34e0'
   )
   AND q.answer_source = 'derived'
   AND q.answer_text IS NOT NULL
   AND q.status = 'live'
   AND EXISTS (
     SELECT 1 FROM appearances a
      WHERE a.canonical_id = q.id
        AND a.paper_id = CASE q.id
          WHEN 'cq_bcbd65c36346a9bd' THEN 'Old_Questions/Direct_2019-2020/Chemist-II General Englsih.pdf'
          WHEN 'cq_593a85bf4293080a' THEN 'Old_Questions/Direct_2019-2020/General English (JE).pdf'
          WHEN 'cq_04d17b292766eb03' THEN 'Old_Questions/Direct_2019-2020/General English (JE).pdf'
          WHEN 'cq_274ae8f11fc9264d' THEN 'Old_Questions/Direct_NG_2024-2027/JE under Agri&Farmer Welfare March-2026 Paper-I (Gen. English)..pdf'
          WHEN 'cq_b592387c54fa34e0' THEN 'Old_Questions/Direct_2019-2020/Geologist Junior General English Paper-III.pdf'
        END
        AND a.qnum = CASE q.id
          WHEN 'cq_bcbd65c36346a9bd' THEN '73'
          WHEN 'cq_593a85bf4293080a' THEN '75'
          WHEN 'cq_04d17b292766eb03' THEN '76'
          WHEN 'cq_274ae8f11fc9264d' THEN '12'
          WHEN 'cq_b592387c54fa34e0' THEN '91'
        END
   );
COMMIT;
