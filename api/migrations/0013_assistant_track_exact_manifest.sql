-- Source-reviewed direct recruitment Assistant papers include archived title
-- variants such as "Assistant under MPSC". Restrict by exact exam-title
-- phrase and exclude specialist Assistant posts and departmental promotion.
BEGIN;
UPDATE collection_sections
   SET query=jsonb_build_object('paper_ids',(
       SELECT COALESCE(array_agg(id ORDER BY year,id),ARRAY[]::text[])
         FROM papers
        WHERE exam_type IN ('Direct','Direct_NG')
          AND lower(coalesce(exam_name,'')) ~ 'competitive examinations? for recruitment to the post of assistant( grade)?'
          AND lower(exam_name) !~ 'assistant (sub|public|divisional|director|engineer|controller|tourist|architect|jailor|auditor|treasury|labour|accounts)'
   ))
 WHERE collection_id='assistant' AND version=1 AND path='papers';
COMMIT;
