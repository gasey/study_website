BEGIN;
-- Branches cannot duplicate rows: primary flag differs and each source has a
-- unique question/path key. UNION's global deduplication defeats indexed probes.
CREATE OR REPLACE VIEW v_question_paths AS
 SELECT question_id,subject_id,subject_label,topic_id,topic_label,subtopic_id,subtopic_label,true AS is_primary,'approved'::text AS review_status
 FROM question_classifications WHERE review_status='approved'
 UNION ALL
 SELECT question_id,subject_id,subject_label,topic_id,topic_label,subtopic_id,subtopic_label,false,'approved'::text
 FROM question_topic_links WHERE review_status='approved';
COMMIT;
