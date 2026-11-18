-- Prospective habit events only. No historical awards or profile rewrites.
BEGIN;
CREATE TABLE user_learning_days (
 user_id text NOT NULL REFERENCES users(id), day date NOT NULL,
 PRIMARY KEY(user_id,day)
);
CREATE TABLE daily_learning_plans (
 user_id text NOT NULL REFERENCES users(id), day date NOT NULL,
 snapshot jsonb NOT NULL, started_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(user_id,day)
);
CREATE TRIGGER immutable_daily_learning_plan BEFORE UPDATE OR DELETE ON daily_learning_plans
 FOR EACH ROW EXECUTE FUNCTION review_immutable();
CREATE TABLE review_session_items (
 session_id text NOT NULL REFERENCES practice_study_sessions(id),
 canonical_id text NOT NULL REFERENCES canonical_questions(id), due_on date NOT NULL,
 opened_at timestamptz, attempt_id bigint UNIQUE REFERENCES attempts(id),
 PRIMARY KEY(session_id,canonical_id)
);
CREATE TABLE review_item_completions (
 user_id text NOT NULL REFERENCES users(id), canonical_id text NOT NULL REFERENCES canonical_questions(id),
 scheduled_due date NOT NULL, session_id text NOT NULL REFERENCES practice_study_sessions(id),
 attempt_id bigint NOT NULL UNIQUE REFERENCES attempts(id), correct boolean NOT NULL,
 completed_on date NOT NULL, PRIMARY KEY(user_id,canonical_id,scheduled_due)
);
CREATE INDEX review_completions_user_day ON review_item_completions(user_id,completed_on);
CREATE TRIGGER immutable_review_item_completion BEFORE UPDATE OR DELETE ON review_item_completions
 FOR EACH ROW EXECUTE FUNCTION review_immutable();
CREATE TABLE review_session_rewards (
 session_id text PRIMARY KEY REFERENCES practice_study_sessions(id),
 user_id text NOT NULL REFERENCES users(id), day date NOT NULL,
 slot integer NOT NULL CHECK(slot BETWEEN 1 AND 2), ledger_id bigint NOT NULL UNIQUE REFERENCES reward_ledger(id),
 UNIQUE(user_id,day,slot)
);
CREATE TRIGGER immutable_review_session_reward BEFORE UPDATE OR DELETE ON review_session_rewards
 FOR EACH ROW EXECUTE FUNCTION review_immutable();
ALTER TABLE daily_quest_claims DROP CONSTRAINT daily_quest_claims_quest_key_check;
ALTER TABLE daily_quest_claims ADD CONSTRAINT daily_quest_claims_quest_key_check
 CHECK(quest_key IN ('warmup_circuit','cross_stream_triad','mastery_closure','streak_day3','streak_day7','review_ring','plan_ring'));

CREATE FUNCTION touch_learning_streak(uid text, active_day date) RETURNS void LANGUAGE plpgsql AS $$
DECLARE p reward_profiles%ROWTYPE; days integer; shields integer;
BEGIN
 IF active_day IS DISTINCT FROM (now() AT TIME ZONE 'Asia/Kolkata')::date
   OR NOT EXISTS(SELECT 1 FROM users WHERE id=uid AND email IS NOT NULL) THEN RETURN; END IF;
 PERFORM pg_advisory_xact_lock(hashtext('rewards:'||uid));
 INSERT INTO reward_profiles(user_id) VALUES(uid) ON CONFLICT DO NOTHING;
 SELECT * INTO p FROM reward_profiles WHERE user_id=uid FOR UPDATE;
 INSERT INTO user_learning_days(user_id,day) VALUES(uid,active_day) ON CONFLICT DO NOTHING;
 IF p.last_active_ist_date>=active_day THEN RETURN; END IF;
 days:=1; shields:=p.streak_shields;
 IF p.last_active_ist_date=active_day-1 THEN days:=p.current_streak_days+1;
 ELSIF p.last_active_ist_date=active_day-2 AND shields>0 THEN
   days:=p.current_streak_days+1; shields:=shields-1;
 END IF;
 UPDATE reward_profiles SET current_streak_days=days,longest_streak_days=GREATEST(longest_streak_days,days),
   last_active_ist_date=active_day,streak_shields=shields WHERE user_id=uid;
END $$;
CREATE FUNCTION qualify_learning_attempt(aid bigint) RETURNS void LANGUAGE plpgsql AS $$
DECLARE a attempts%ROWTYPE; proof jsonb;
BEGIN
 SELECT * INTO a FROM attempts WHERE id=aid;
 IF NOT FOUND OR a.chosen_text IS NULL OR a.correct IS NULL OR a.canonical_id IS NULL
   OR a.context NOT IN ('practice','review','game','mock')
   OR (a.at AT TIME ZONE 'Asia/Kolkata')::date<>(now() AT TIME ZONE 'Asia/Kolkata')::date
   OR a.at>clock_timestamp() OR NOT EXISTS(SELECT 1 FROM v_scorable WHERE id=a.canonical_id) THEN RETURN; END IF;
 IF a.context='mock' THEN
   SELECT sq.snapshot INTO proof FROM mock_session_questions sq JOIN mock_sessions m ON m.id=sq.mock_id
    WHERE sq.mock_id=a.mock_id AND sq.canonical_id=a.canonical_id AND m.user_id=a.user_id
      AND m.submitted_at IS NOT NULL AND NOT m.late;
 ELSE proof:=a.scoring_snapshot; END IF;
 IF proof IS NULL OR COALESCE(proof->>'answer_source','') NOT IN ('official','key') THEN RETURN; END IF;
 PERFORM touch_learning_streak(a.user_id,(a.at AT TIME ZONE 'Asia/Kolkata')::date);
END $$;
-- Every writer uses job -> rewards -> profile lock order, including games and
-- mock finalization. This precedes the existing first-correct award trigger.
CREATE FUNCTION learning_habit_lock(uid text) RETURNS void LANGUAGE plpgsql AS $$
BEGIN
 IF NOT EXISTS(SELECT 1 FROM users WHERE id=uid AND email IS NOT NULL) THEN RETURN; END IF;
 INSERT INTO learning_rollup_jobs(user_id) VALUES(uid) ON CONFLICT DO NOTHING;
 PERFORM 1 FROM learning_rollup_jobs WHERE user_id=uid FOR UPDATE;
 PERFORM pg_advisory_xact_lock(hashtext('rewards:'||uid));
END $$;
CREATE FUNCTION habit_attempt_before() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN PERFORM learning_habit_lock(NEW.user_id); RETURN NEW; END $$;
CREATE TRIGGER aa_habit_attempt_lock BEFORE INSERT ON attempts FOR EACH ROW EXECUTE FUNCTION habit_attempt_before();
CREATE FUNCTION habit_attempt_after() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN PERFORM qualify_learning_attempt(NEW.id); RETURN NEW; END $$;
CREATE TRIGGER zz_habit_attempt AFTER INSERT ON attempts FOR EACH ROW EXECUTE FUNCTION habit_attempt_after();
CREATE FUNCTION habit_mock_before() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF NEW.submitted_at IS NOT NULL AND OLD.submitted_at IS NULL THEN PERFORM learning_habit_lock(NEW.user_id); END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER aa_habit_mock_lock BEFORE UPDATE OF submitted_at ON mock_sessions FOR EACH ROW EXECUTE FUNCTION habit_mock_before();
CREATE FUNCTION habit_mock_after() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE aid bigint;
BEGIN
 IF NEW.submitted_at IS NOT NULL AND OLD.submitted_at IS NULL THEN
   FOR aid IN SELECT id FROM attempts WHERE mock_id=NEW.id ORDER BY id LOOP PERFORM qualify_learning_attempt(aid); END LOOP;
 END IF; RETURN NEW;
END $$;
CREATE TRIGGER zz_habit_mock AFTER UPDATE OF submitted_at ON mock_sessions FOR EACH ROW EXECUTE FUNCTION habit_mock_after();

-- Review/quest awards can leave a partial XP budget. Preserve the v1 discovery
-- rule while clamping the final award to the remaining shared 300 XP.
CREATE OR REPLACE FUNCTION reward_study_attempt(aid BIGINT) RETURNS void LANGUAGE plpgsql AS $$
DECLARE a attempts%ROWTYPE; claimed TEXT; earned INTEGER; proof JSONB;
BEGIN
 SELECT * INTO a FROM attempts WHERE id=aid;
 IF NOT FOUND OR NOT a.correct OR a.canonical_id IS NULL OR a.context NOT IN ('practice','mock','game') THEN RETURN; END IF;
 IF NOT EXISTS(SELECT 1 FROM users WHERE id=a.user_id AND email IS NOT NULL) THEN RETURN; END IF;
 IF a.context='mock' THEN
   SELECT sq.snapshot INTO proof FROM mock_session_questions sq JOIN mock_sessions m ON m.id=sq.mock_id WHERE sq.mock_id=a.mock_id AND sq.canonical_id=a.canonical_id AND m.submitted_at IS NOT NULL AND NOT m.late AND m.user_id=a.user_id;
 ELSE proof:=a.scoring_snapshot; END IF;
 IF proof IS NULL OR COALESCE(proof->>'answer_source','') NOT IN ('official','key') OR proof->>'answer_text' IS DISTINCT FROM a.chosen_text THEN RETURN; END IF;
 IF NOT EXISTS(SELECT 1 FROM v_scorable WHERE id=a.canonical_id AND answer_text=a.chosen_text) THEN RETURN; END IF;
 PERFORM pg_advisory_xact_lock(hashtext('rewards:'||a.user_id));
 SELECT COALESCE(sum(xp),0) INTO earned FROM reward_ledger WHERE user_id=a.user_id AND kind IN ('study','game') AND created_at >= (date_trunc('day',now() AT TIME ZONE 'Asia/Kolkata') AT TIME ZONE 'Asia/Kolkata');
 IF earned>=300 THEN RETURN; END IF;
 INSERT INTO reward_question_claims(user_id,canonical_id,attempt_id) VALUES(a.user_id,a.canonical_id,a.id) ON CONFLICT DO NOTHING RETURNING canonical_id INTO claimed;
 IF claimed IS NULL THEN RETURN; END IF;
 INSERT INTO reward_profiles(user_id) VALUES(a.user_id) ON CONFLICT DO NOTHING;
 INSERT INTO reward_ledger(user_id,event_key,kind,xp,points,note) VALUES(a.user_id,'question:'||a.user_id||':'||a.canonical_id,CASE WHEN a.context='game' THEN 'game' ELSE 'study' END,LEAST(10,300-earned),1,'First correct verified-key question');
END;$$;
GRANT SELECT,INSERT ON user_learning_days,daily_learning_plans,review_item_completions,review_session_rewards TO mpsc;
GRANT SELECT,INSERT,UPDATE ON review_session_items TO mpsc;
COMMIT;
