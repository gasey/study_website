-- The 2021 Informatics Officer General English Paper-II final key conflicts
-- with the sentence classifications derivable from the printed questions.
-- Keep the reviewed answers available in practice, but exclude them from
-- official-key scoring and expose the discrepancy to learners.
BEGIN;
UPDATE canonical_questions q
   SET key_disputed = true,
       dispute_note = CASE q.id
         WHEN 'cq_c85aca9b5328150a' THEN 'Q42: official key C; derived answer A.'
         WHEN 'cq_b0ab85ef027cdcfe' THEN 'Q43: official key A; derived answer C.'
         WHEN 'cq_1aac6dc2a0f673bc' THEN 'Q44: official key C; derived answer B.'
         WHEN 'cq_d71c3470fdb9fcee' THEN 'Q45: official key B; derived answer C.'
         WHEN 'cq_72e3c9bf8578b75b' THEN 'Q47: official key B; derived answer C.'
         WHEN 'cq_440ff2de6f90a50f' THEN 'Q48: official key C; derived answer B.'
         WHEN 'cq_b5fcf396f52a7c79' THEN 'Q49: official key B; derived answer A.'
         WHEN 'cq_da04d6726ea74adc' THEN 'Q50: official key C; derived answer B.'
       END,
       updated_at = now()
 WHERE q.id IN (
   'cq_c85aca9b5328150a','cq_b0ab85ef027cdcfe','cq_1aac6dc2a0f673bc',
   'cq_d71c3470fdb9fcee','cq_72e3c9bf8578b75b','cq_440ff2de6f90a50f',
   'cq_b5fcf396f52a7c79','cq_da04d6726ea74adc'
 )
   AND q.answer_source = 'derived'
   AND q.status = 'live'
   AND EXISTS (
     SELECT 1 FROM appearances a
      WHERE a.canonical_id = q.id
        AND a.paper_id = 'Old_Questions/Direct_2020-2021/Informatics Officer - General English Paper-II.pdf'
        AND a.qnum = CASE q.id
          WHEN 'cq_c85aca9b5328150a' THEN '42'
          WHEN 'cq_b0ab85ef027cdcfe' THEN '43'
          WHEN 'cq_1aac6dc2a0f673bc' THEN '44'
          WHEN 'cq_d71c3470fdb9fcee' THEN '45'
          WHEN 'cq_72e3c9bf8578b75b' THEN '47'
          WHEN 'cq_440ff2de6f90a50f' THEN '48'
          WHEN 'cq_b5fcf396f52a7c79' THEN '49'
          WHEN 'cq_da04d6726ea74adc' THEN '50'
        END
   );
COMMIT;
