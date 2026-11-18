BEGIN;
-- One optional, resumable normal-practice check-in per account/exam.
-- No new attempt, mastery, reward, answer or account-preference store.
CREATE UNIQUE INDEX practice_onboarding_exam_once ON practice_study_sessions(user_id,collection_id)
 WHERE filters @> '{"onboarding_version":1}'::jsonb;
COMMIT;
