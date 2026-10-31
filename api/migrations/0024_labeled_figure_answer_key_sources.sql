-- These official-key answers are verified, but the extracted question
-- records do not embed the original figure artwork. Preserve the distinction
-- so learners can open the linked paper before answering.
BEGIN;
UPDATE canonical_questions q
   SET source_defect = 'diagram-not-embedded',
       dispute_note = CASE q.id
         WHEN 'cq_9241abb4c39573bae75b' THEN 'Q7 is keyed A by the final DSWO 2026 Paper-II answer key. The sequence figures are in the linked original paper PDF, not embedded in this question display.'
         WHEN 'cq_7945e0ca075a85eb1df7' THEN 'Q81 is keyed A by the final LDC Commissioner for PwD Paper-II answer key. The mirror-image artwork is in the linked original paper PDF.'
         WHEN 'cq_f0f5eac0ba035db415cb' THEN 'Q85 is keyed C by the final LDC Commissioner for PwD Paper-II answer key. The identity figures are in the linked original paper PDF.'
         WHEN 'cq_f16b180c74eeedebbdd5' THEN 'Q87 is keyed B by the final LDC Commissioner for PwD Paper-II answer key. The missing-number figure is in the linked original paper PDF.'
       END,
       updated_at = now()
 WHERE q.id IN ('cq_9241abb4c39573bae75b','cq_7945e0ca075a85eb1df7',
               'cq_f0f5eac0ba035db415cb','cq_f16b180c74eeedebbdd5')
   AND q.answer_source IN ('official','key')
   AND q.answer_text IS NOT NULL
   AND q.status = 'live'
   AND EXISTS (
     SELECT 1 FROM appearances a
      WHERE a.canonical_id = q.id
        AND (a.has_diagram OR a.figure_image IS NOT NULL)
        AND a.paper_id = CASE q.id
          WHEN 'cq_9241abb4c39573bae75b' THEN 'Old_Questions/Direct_2025-2027/DSWO Paper-II -.pdf'
          WHEN 'cq_7945e0ca075a85eb1df7' THEN 'Old_Questions/Direct_NG_2024-2027/LDC under SW, WCD Paper-II..pdf'
          WHEN 'cq_f0f5eac0ba035db415cb' THEN 'Old_Questions/Direct_NG_2024-2027/LDC under SW, WCD Paper-II..pdf'
          WHEN 'cq_f16b180c74eeedebbdd5' THEN 'Old_Questions/Direct_NG_2024-2027/LDC under SW, WCD Paper-II..pdf'
        END
        AND a.qnum = CASE q.id
          WHEN 'cq_9241abb4c39573bae75b' THEN '7'
          WHEN 'cq_7945e0ca075a85eb1df7' THEN '81'
          WHEN 'cq_f0f5eac0ba035db415cb' THEN '85'
          WHEN 'cq_f16b180c74eeedebbdd5' THEN '87'
        END
   );
COMMIT;
