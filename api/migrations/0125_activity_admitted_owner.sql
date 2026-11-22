BEGIN;
-- A direct function call can race with ownership transfer between its reads.
-- Derive activity only for the exact subject whose processing lease was admitted;
-- the transfer already preserves a durable reconciliation hint for the new owner.
CREATE OR REPLACE FUNCTION record_learning_activity(target bigint) RETURNS void
LANGUAGE plpgsql SET search_path=pg_catalog,public AS $$
DECLARE d record; uid text;
BEGIN
 SELECT user_id INTO uid FROM attempts WHERE id=target;
 IF NOT FOUND OR NOT public.audience_processing_admit(uid) THEN RETURN; END IF;
 SELECT a.*,COALESCE(qc.subject_id,'') AS subject_key,COALESCE(qc.subject_label,'') AS subject_label INTO d
 FROM attempts a JOIN users u ON u.id=a.user_id AND u.email IS NOT NULL
 LEFT JOIN question_classifications qc ON qc.question_id=a.canonical_id AND qc.review_status='approved'
 WHERE a.id=target AND a.user_id=uid;
 IF NOT FOUND THEN RETURN; END IF;
 INSERT INTO user_activity_daily(user_id,collection_key,section_key,subject_key,subject_label,day,answered,correct,last_active_at)
 VALUES(d.user_id,COALESCE(d.collection_id,''),COALESCE(d.section_path,''),d.subject_key,d.subject_label,
   (d.at AT TIME ZONE 'Asia/Kolkata')::date,1,d.correct::int,d.at)
 ON CONFLICT(user_id,collection_key,section_key,subject_key,day) DO UPDATE SET
   answered=user_activity_daily.answered+1,correct=user_activity_daily.correct+EXCLUDED.correct,
   subject_label=EXCLUDED.subject_label,last_active_at=GREATEST(user_activity_daily.last_active_at,EXCLUDED.last_active_at);
 IF d.canonical_id IS NOT NULL THEN
  INSERT INTO user_activity_questions VALUES(d.user_id,COALESCE(d.collection_id,''),COALESCE(d.section_path,''),d.subject_key,d.canonical_id)
  ON CONFLICT DO NOTHING;
 END IF;
END $$;

COMMIT;
