-- Correct two track manifests against source-file identities. Metadata exam
-- labels on these MCS preliminary booklets are inconsistent, so the paper
-- file identity is the authoritative exact match.
BEGIN;

UPDATE collection_sections
   SET query=jsonb_build_object('paper_ids',(
       SELECT COALESCE(array_agg(id ORDER BY year,id),ARRAY[]::text[])
         FROM papers
        WHERE exam_type='Direct'
          AND lower(id) LIKE '%mcs combined%preliminary exam%'
   ))
 WHERE collection_id='combined-prelims' AND version=1 AND path='papers';

-- Assistant Grade direct papers include official title variants. Keep the
-- shared Assistant Grade & UDC sitting in this track; LDE remains excluded.
UPDATE collection_sections
   SET query=jsonb_build_object('paper_ids',(
       SELECT COALESCE(array_agg(id ORDER BY year,id),ARRAY[]::text[])
         FROM papers
        WHERE exam_type IN ('Direct','Direct_NG')
          AND lower(exam_name) NOT LIKE '%limited departmental%'
          AND (lower(exam_name) LIKE '%assistant grade under government of mizoram%'
            OR lower(exam_name) LIKE '%assistant grade under mpsc%'
            OR lower(exam_name) LIKE '%assistant grade & udc%'
            OR lower(exam_name) LIKE '%recruitment to the post of assistant grade%')
   ))
 WHERE collection_id='assistant' AND version=1 AND path='papers';

COMMIT;
