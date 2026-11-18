-- Prospective completion receipts and once-ever mastery milestones. No awards
-- are minted by this migration; old tiers are recorded as unpaid baselines.
BEGIN;
CREATE TABLE game_completion_rewards (
 room_id text NOT NULL REFERENCES game_rooms(id), user_id text NOT NULL REFERENCES users(id),
 day date NOT NULL, ledger_id bigint NOT NULL UNIQUE REFERENCES reward_ledger(id),
 PRIMARY KEY(room_id,user_id)
);
CREATE TABLE mock_completion_rewards (
 mock_id text PRIMARY KEY REFERENCES mock_sessions(id), user_id text NOT NULL REFERENCES users(id),
 day date NOT NULL, ledger_id bigint NOT NULL UNIQUE REFERENCES reward_ledger(id)
);
CREATE TABLE mastery_milestones (
 user_id text NOT NULL REFERENCES users(id), subject_id text NOT NULL, topic text NOT NULL,
 tier text NOT NULL CHECK(tier IN ('proficient','mastered')),
 origin text NOT NULL CHECK(origin IN ('baseline','activity')),
 ledger_id bigint UNIQUE REFERENCES reward_ledger(id), source_attempt_id bigint REFERENCES attempts(id),
 review_session_id text REFERENCES practice_study_sessions(id),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(), PRIMARY KEY(user_id,topic,tier),
 CHECK((origin='baseline' AND ledger_id IS NULL AND source_attempt_id IS NULL AND review_session_id IS NULL)
   OR (origin='activity' AND ledger_id IS NOT NULL AND source_attempt_id IS NOT NULL))
);
INSERT INTO mastery_milestones(user_id,subject_id,topic,tier,origin)
 SELECT DISTINCT ON(user_id,topic,tier) user_id,subject_id,topic,tier,'baseline' FROM (
   SELECT user_id,subject_id,topic,'proficient' AS tier FROM user_topic_mastery WHERE state IN ('proficient','mastered')
   UNION ALL SELECT user_id,subject_id,topic,'mastered' FROM user_topic_mastery WHERE state='mastered'
 ) historical ORDER BY user_id,topic,tier,subject_id;
CREATE TRIGGER immutable_game_completion_reward BEFORE UPDATE OR DELETE ON game_completion_rewards FOR EACH ROW EXECUTE FUNCTION review_immutable();
CREATE TRIGGER immutable_mock_completion_reward BEFORE UPDATE OR DELETE ON mock_completion_rewards FOR EACH ROW EXECUTE FUNCTION review_immutable();
CREATE TRIGGER immutable_mastery_milestone BEFORE UPDATE OR DELETE ON mastery_milestones FOR EACH ROW EXECUTE FUNCTION review_immutable();
GRANT SELECT,INSERT ON game_completion_rewards,mock_completion_rewards,mastery_milestones TO mpsc;
-- Daily admission writes these under the application role, including the first
-- request after midnight. Do not depend on migration-owner default privileges.
GRANT SELECT,INSERT ON game_dailies,game_daily_entries TO mpsc;

CREATE FUNCTION reward_game_completion() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE m game_members%ROWTYPE; d date; checks integer; timed boolean; total integer; daily boolean;
 event text; receipt bigint;
BEGIN
 IF NEW.state<>'finished' OR OLD.state<>'running' OR NEW.finished_at IS NULL
   OR (NEW.finished_at AT TIME ZONE 'Asia/Kolkata')::date<>(now() AT TIME ZONE 'Asia/Kolkata')::date
   OR NEW.finished_at>clock_timestamp() THEN RETURN NEW; END IF;
 daily:=NEW.mode='daily'; d:=(now() AT TIME ZONE 'Asia/Kolkata')::date;
 FOR m IN SELECT * FROM game_members WHERE room_id=NEW.id AND left_at IS NULL ORDER BY user_id LOOP
   IF NOT EXISTS(SELECT 1 FROM users WHERE id=m.user_id AND email IS NOT NULL) THEN CONTINUE; END IF;
   -- Frozen room identity was rechecked under canonical SHARE locks by finish().
   -- Require the server-bound scored attempt for every answered, non-excluded item.
   SELECT count(*),COALESCE(bool_and(COALESCE(a.elapsed_ms>=3000 AND t.id IS NOT NULL
      AND t.user_id=m.user_id AND t.context='game' AND t.canonical_id=NEW.questions->a.position->>'id'
      AND t.chosen_text=NEW.questions->a.position->'options'->>a.chosen_index
      AND t.correct=a.correct AND COALESCE(NEW.questions->a.position->>'answer_source','') IN ('official','key'),false)),false)
    INTO checks,timed FROM game_answers a LEFT JOIN attempts t ON t.id=a.attempt_id
    WHERE a.room_id=NEW.id AND a.user_id=m.user_id AND NOT a.excluded AND a.chosen_index IS NOT NULL;
   total:=jsonb_array_length(NEW.questions)-m.excluded;
   IF checks=0 OR NOT timed OR total<=0 THEN CONTINUE; END IF;
   IF daily THEN
     IF NEW.daily_id IS DISTINCT FROM d::text OR NOT EXISTS(SELECT 1 FROM game_daily_entries e
       WHERE e.room_id=NEW.id AND e.user_id=m.user_id AND e.daily_id=NEW.daily_id) THEN CONTINUE; END IF;
     event:='daily:'||m.user_id||':'||NEW.daily_id;
   ELSE
     IF NEW.mode NOT IN ('gauntlet','speed','duel','party','cup','trail') OR m.correct*100<60*total THEN CONTINUE; END IF;
     event:='game:'||m.user_id||':'||NEW.id;
   END IF;
   PERFORM learning_habit_lock(m.user_id);
   INSERT INTO reward_profiles(user_id) VALUES(m.user_id) ON CONFLICT DO NOTHING;
   INSERT INTO reward_ledger(user_id,event_key,kind,xp,points,note,rule_version)
    VALUES(m.user_id,event,'game',CASE WHEN daily THEN 10 ELSE 15 END,CASE WHEN daily THEN 1 ELSE 2 END,
      CASE WHEN daily THEN 'Completed Daily Five' ELSE 'Completed verified game at 60% accuracy' END,'learning-v2')
    ON CONFLICT DO NOTHING RETURNING id INTO receipt;
   IF receipt IS NOT NULL THEN INSERT INTO game_completion_rewards(room_id,user_id,day,ledger_id)
     VALUES(NEW.id,m.user_id,d,receipt); END IF;
 END LOOP;
 RETURN NEW;
END $$;
CREATE TRIGGER award_game_completion AFTER UPDATE OF state ON game_rooms FOR EACH ROW EXECUTE FUNCTION reward_game_completion();

CREATE FUNCTION reward_mock_completion() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE n integer; valid integer; receipt bigint;
BEGIN
 IF NEW.submitted_at IS NULL OR OLD.submitted_at IS NOT NULL OR NEW.late OR NEW.answer_mode<>'official'
   OR NOT EXISTS(SELECT 1 FROM users WHERE id=NEW.user_id AND email IS NOT NULL)
   OR (NEW.submitted_at AT TIME ZONE 'Asia/Kolkata')::date<>(now() AT TIME ZONE 'Asia/Kolkata')::date
   OR NEW.submitted_at>clock_timestamp() THEN RETURN NEW; END IF;
 n:=cardinality(NEW.question_ids);
 -- Full means the entire frozen test was answered, including custom verified
 -- tests; it does not require the separate original-paper simulation mode.
 IF n<1 OR NEW.submitted_at<NEW.started_at+make_interval(secs=>3*n) THEN RETURN NEW; END IF;
 SELECT count(DISTINCT sq.canonical_id) INTO valid FROM mock_session_questions sq
  JOIN v_scorable q ON q.id=sq.canonical_id AND q.answer_text=sq.snapshot->>'answer_text'
  WHERE sq.mock_id=NEW.id AND sq.canonical_id=ANY(NEW.question_ids)
   AND COALESCE(sq.snapshot->>'answer_source','') IN ('official','key')
   AND EXISTS(SELECT 1 FROM attempts a WHERE a.mock_id=NEW.id AND a.user_id=NEW.user_id
     AND a.context='mock' AND a.canonical_id=sq.canonical_id AND a.chosen_text IS NOT NULL
     AND a.correct IS NOT NULL AND a.at>=NEW.started_at AND a.at<=NEW.submitted_at);
 IF valid<>n THEN RETURN NEW; END IF;
 PERFORM learning_habit_lock(NEW.user_id);
 INSERT INTO reward_profiles(user_id) VALUES(NEW.user_id) ON CONFLICT DO NOTHING;
 INSERT INTO reward_ledger(user_id,event_key,kind,xp,points,note,rule_version)
   VALUES(NEW.user_id,'mock:'||NEW.user_id||':'||NEW.id,'study',30,3,'Completed full verified mock','learning-v2')
   ON CONFLICT DO NOTHING RETURNING id INTO receipt;
 IF receipt IS NOT NULL THEN INSERT INTO mock_completion_rewards(mock_id,user_id,day,ledger_id)
   VALUES(NEW.id,NEW.user_id,(now() AT TIME ZONE 'Asia/Kolkata')::date,receipt); END IF;
 RETURN NEW;
END $$;
-- Existing question-discovery awards settle before the completion bonus.
CREATE TRIGGER yy_mock_completion AFTER UPDATE OF submitted_at ON mock_sessions FOR EACH ROW EXECUTE FUNCTION reward_mock_completion();
COMMIT;
