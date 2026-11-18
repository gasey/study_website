BEGIN;
CREATE TABLE user_topic_mastery (
 user_id text NOT NULL REFERENCES users(id), subject_id text NOT NULL, topic text NOT NULL,
 state text NOT NULL CHECK(state IN ('exploring','practicing','proficient','mastered')),
 distinct_attempted integer NOT NULL CHECK(distinct_attempted>0),
 distinct_correct_latest integer NOT NULL CHECK(distinct_correct_latest BETWEEN 0 AND distinct_attempted),
 last_verified_activity_at timestamptz NOT NULL, proficient_at timestamptz, mastered_at timestamptz,
 rule_version text NOT NULL, updated_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(user_id,subject_id,topic)
);
CREATE TABLE review_items (
 user_id text NOT NULL REFERENCES users(id), item_type text NOT NULL CHECK(item_type IN ('question','vocab')),
 item_id text NOT NULL, canonical_id text REFERENCES canonical_questions(id),
 box integer NOT NULL CHECK(box BETWEEN 1 AND 5), due_on date, last_result boolean NOT NULL,
 last_attempt_id bigint REFERENCES attempts(id), updated_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(user_id,item_type,item_id),
 CHECK(item_type<>'question' OR canonical_id IS NOT NULL AND canonical_id=item_id)
);
-- Date comparisons belong in queries: current_date is not immutable and cannot
-- legally be a PostgreSQL partial-index predicate. NULL means graduated.
CREATE INDEX review_items_due ON review_items(user_id,due_on,item_id)
 WHERE item_type='question' AND due_on IS NOT NULL;
CREATE TABLE user_focus_subjects (
 user_id text NOT NULL REFERENCES users(id), subject_id text NOT NULL REFERENCES review_taxonomy(id),
 position integer NOT NULL CHECK(position BETWEEN 0 AND 4),
 PRIMARY KEY(user_id,subject_id), UNIQUE(user_id,position)
);
CREATE TABLE worker_heartbeats (
 worker text PRIMARY KEY, last_beat timestamptz NOT NULL DEFAULT now(), last_ok timestamptz, note text
);
-- One durable, versioned job per learner. Changes arriving during a cycle cannot
-- be lost; failed work remains observable and can be retried without awards.
CREATE TABLE learning_rollup_jobs (
 user_id text PRIMARY KEY REFERENCES users(id), requested_version bigint NOT NULL DEFAULT 1,
 processed_version bigint NOT NULL DEFAULT 0, requested_at timestamptz NOT NULL DEFAULT now(),
 initialized_at timestamptz, attempt_cursor bigint NOT NULL DEFAULT 0,
 failures integer NOT NULL DEFAULT 0, last_error text
);
CREATE INDEX learning_rollup_pending ON learning_rollup_jobs(requested_at,user_id)
 WHERE processed_version<requested_version;
CREATE INDEX attempts_question_learning_users ON attempts(canonical_id,user_id);
CREATE FUNCTION enqueue_learning_user(target text) RETURNS void LANGUAGE sql AS $$
 INSERT INTO learning_rollup_jobs(user_id) SELECT id FROM users WHERE id=target AND email IS NOT NULL
 ON CONFLICT(user_id) DO UPDATE SET requested_version=learning_rollup_jobs.requested_version+1,
 requested_at=clock_timestamp(),failures=0,last_error=NULL
$$;
CREATE FUNCTION enqueue_learning_attempt() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF TG_OP='UPDATE' THEN PERFORM enqueue_learning_user(OLD.user_id); END IF;
 PERFORM enqueue_learning_user(NEW.user_id); RETURN NEW;
END $$;
CREATE TRIGGER learning_attempt_pending AFTER INSERT ON attempts FOR EACH ROW EXECUTE FUNCTION enqueue_learning_attempt();
CREATE TRIGGER learning_attempt_adopted AFTER UPDATE OF user_id ON attempts FOR EACH ROW
 WHEN(OLD.user_id IS DISTINCT FROM NEW.user_id) EXECUTE FUNCTION enqueue_learning_attempt();
CREATE FUNCTION enqueue_learning_assessment() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE target text;
BEGIN
 SELECT user_id INTO target FROM attempts WHERE id=NEW.attempt_id;
 PERFORM enqueue_learning_user(target); RETURN NEW;
END $$;
CREATE TRIGGER learning_assessment_pending AFTER INSERT ON attempt_assessments FOR EACH ROW EXECUTE FUNCTION enqueue_learning_assessment();
CREATE FUNCTION enqueue_learning_question() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE qid text; target text;
BEGIN
 IF TG_TABLE_NAME='question_classifications' THEN
  IF TG_OP='UPDATE' AND (OLD.subject_id,OLD.topic_id,OLD.review_status)
    IS NOT DISTINCT FROM (NEW.subject_id,NEW.topic_id,NEW.review_status) THEN RETURN NULL; END IF;
  qid=CASE WHEN TG_OP='DELETE' THEN OLD.question_id ELSE NEW.question_id END;
 ELSE qid=NEW.id; END IF;
 FOR target IN SELECT DISTINCT user_id FROM attempts WHERE canonical_id=qid ORDER BY user_id
 LOOP PERFORM enqueue_learning_user(target); END LOOP;
 RETURN NULL;
END $$;
CREATE TRIGGER learning_taxonomy_pending AFTER INSERT OR UPDATE OR DELETE ON question_classifications
 FOR EACH ROW EXECUTE FUNCTION enqueue_learning_question();
CREATE TRIGGER learning_question_pending AFTER UPDATE ON canonical_questions FOR EACH ROW
 WHEN ((OLD.answer_text,OLD.answer_source,OLD.key_disputed,OLD.source_defect,OLD.status)
 IS DISTINCT FROM (NEW.answer_text,NEW.answer_source,NEW.key_disputed,NEW.source_defect,NEW.status))
 EXECUTE FUNCTION enqueue_learning_question();
ALTER TABLE practice_study_sessions ADD COLUMN kind text NOT NULL DEFAULT 'practice' CHECK(kind IN ('practice','review'));
ALTER TABLE practice_study_sessions ALTER COLUMN collection_id DROP NOT NULL;
ALTER TABLE practice_study_sessions ADD CONSTRAINT study_collection_required CHECK(kind='review' OR collection_id IS NOT NULL);
CREATE OR REPLACE FUNCTION enqueue_attempt_reassessment() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF NEW.context IN ('practice','review','game') THEN
  INSERT INTO new_score_jobs(attempt_id) VALUES(NEW.id) ON CONFLICT DO NOTHING;
 END IF;
 RETURN NEW;
END $$;
CREATE FUNCTION enqueue_learning_mock_assessment() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE target text;
BEGIN
 SELECT user_id INTO target FROM mock_sessions WHERE id=NEW.mock_id;
 PERFORM enqueue_learning_user(target); RETURN NEW;
END $$;
CREATE TRIGGER learning_mock_assessment_pending AFTER INSERT ON mock_assessments FOR EACH ROW EXECUTE FUNCTION enqueue_learning_mock_assessment();
INSERT INTO learning_rollup_jobs(user_id) SELECT DISTINCT a.user_id FROM attempts a JOIN users u ON u.id=a.user_id WHERE u.email IS NOT NULL;
GRANT SELECT,INSERT,UPDATE,DELETE ON user_topic_mastery,review_items,user_focus_subjects TO mpsc;
GRANT SELECT,INSERT,UPDATE ON worker_heartbeats,learning_rollup_jobs TO mpsc;
GRANT SELECT ON question_classifications,mock_session_questions TO mpsc;

-- Activity preserves original recorded results, independently of verified-key
-- mastery. Sparse day buckets and distinct-question membership serve progress
-- without expanding a learner's repeated attempt history on every GET.
CREATE TABLE user_activity_daily (
 user_id text NOT NULL REFERENCES users(id), collection_key text NOT NULL, section_key text NOT NULL,
 subject_key text NOT NULL, subject_label text NOT NULL, day date NOT NULL,
 answered integer NOT NULL CHECK(answered>0), correct integer NOT NULL CHECK(correct BETWEEN 0 AND answered),
 last_active_at timestamptz NOT NULL,
 PRIMARY KEY(user_id,collection_key,section_key,subject_key,day)
);
CREATE TABLE user_activity_questions (
 user_id text NOT NULL REFERENCES users(id), collection_key text NOT NULL, section_key text NOT NULL,
 subject_key text NOT NULL, canonical_id text NOT NULL,
 PRIMARY KEY(user_id,collection_key,section_key,subject_key,canonical_id)
);
CREATE FUNCTION record_learning_activity(target bigint) RETURNS void LANGUAGE plpgsql AS $$
DECLARE d record;
BEGIN
 SELECT a.*,COALESCE(qc.subject_id,'') AS subject_key,COALESCE(qc.subject_label,'') AS subject_label INTO d
 FROM attempts a JOIN users u ON u.id=a.user_id AND u.email IS NOT NULL
 LEFT JOIN question_classifications qc ON qc.question_id=a.canonical_id AND qc.review_status='approved'
 WHERE a.id=target;
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
-- Own the durable user job before touching activity rows: the reconciler uses
-- this same lock order. Adoption into an account records its existing attempts.
CREATE OR REPLACE FUNCTION enqueue_learning_attempt() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF TG_OP='UPDATE' THEN PERFORM enqueue_learning_user(OLD.user_id); END IF;
 PERFORM enqueue_learning_user(NEW.user_id);
 PERFORM record_learning_activity(NEW.id);
 RETURN NEW;
END $$;
INSERT INTO user_activity_daily
 SELECT a.user_id,COALESCE(a.collection_id,''),COALESCE(a.section_path,''),COALESCE(qc.subject_id,''),
 max(COALESCE(qc.subject_label,'')),(a.at AT TIME ZONE 'Asia/Kolkata')::date,
 count(*)::int,count(*) FILTER(WHERE a.correct)::int,max(a.at)
 FROM attempts a JOIN users u ON u.id=a.user_id AND u.email IS NOT NULL
 LEFT JOIN question_classifications qc ON qc.question_id=a.canonical_id AND qc.review_status='approved'
 GROUP BY a.user_id,a.collection_id,a.section_path,qc.subject_id,(a.at AT TIME ZONE 'Asia/Kolkata')::date;
INSERT INTO user_activity_questions
 SELECT DISTINCT a.user_id,COALESCE(a.collection_id,''),COALESCE(a.section_path,''),COALESCE(qc.subject_id,''),a.canonical_id
 FROM attempts a JOIN users u ON u.id=a.user_id AND u.email IS NOT NULL
 LEFT JOIN question_classifications qc ON qc.question_id=a.canonical_id AND qc.review_status='approved'
 WHERE a.canonical_id IS NOT NULL;
GRANT SELECT,INSERT,UPDATE,DELETE ON user_activity_daily,user_activity_questions TO mpsc;
ALTER TABLE user_exam_bookmarks ADD COLUMN is_primary boolean NOT NULL DEFAULT false;
CREATE UNIQUE INDEX user_one_primary_exam ON user_exam_bookmarks(user_id) WHERE is_primary;
CREATE INDEX activity_user_question ON user_activity_questions(user_id,canonical_id);
CREATE INDEX activity_user_day ON user_activity_daily(user_id,day);
CREATE TABLE auth_login_backoff (
 bucket text PRIMARY KEY, failures integer NOT NULL DEFAULT 0 CHECK(failures>=0),
 last_failed_at timestamptz NOT NULL DEFAULT now(), blocked_until timestamptz NOT NULL DEFAULT now()
);
GRANT SELECT,INSERT,UPDATE,DELETE ON auth_login_backoff TO mpsc;
-- Explicit dependencies also support rehearsals run by an operator other than
-- postgres (whose default privileges already cover the production tables).
GRANT SELECT,INSERT,UPDATE,DELETE ON user_exam_bookmarks TO mpsc;
GRANT SELECT ON game_dailies,game_daily_entries,game_rooms,game_members,game_cups,daily_quest_claims,review_rate_buckets,auth_login_attempts TO mpsc;
COMMIT;
