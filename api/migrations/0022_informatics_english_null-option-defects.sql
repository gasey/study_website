-- These two 2021 Informatics Officer questions have three distinct printed
-- choices and an empty fourth JSON slot. The old duplicate detector counted
-- JSON null as a repeated option and wrongly removed valid keyed questions
-- from strict scoring. Clear that false positive only for these exact rows.
BEGIN;
UPDATE canonical_questions q
   SET source_defect = NULL,
       updated_at = now()
 WHERE q.id IN ('cq_6b3c45d0ca395fe3','cq_ffadf851a1db62c7')
   AND q.answer_source = 'official'
   AND q.answer_text = 'Simple sentence'
   AND q.options = '["Simple sentence","Complex Sentence","Compound sentence",null]'::jsonb
   AND q.source_defect = 'duplicate-options'
   AND EXISTS (
     SELECT 1 FROM appearances a
      WHERE a.canonical_id = q.id
        AND a.paper_id = 'Old_Questions/Direct_2020-2021/Informatics Officer - General English Paper-II.pdf'
        AND a.qnum = CASE q.id
          WHEN 'cq_6b3c45d0ca395fe3' THEN '41'
          WHEN 'cq_ffadf851a1db62c7' THEN '46'
        END
   );
COMMIT;
