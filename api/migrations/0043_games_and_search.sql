BEGIN;
ALTER TABLE attempts DROP CONSTRAINT attempts_context_check;
ALTER TABLE attempts ADD CONSTRAINT attempts_context_check CHECK(context IN ('practice','mock','mock-derived','duel','cup','review','material','game'));
CREATE TABLE game_cups(id TEXT PRIMARY KEY,opens_at TIMESTAMPTZ NOT NULL,closes_at TIMESTAMPTZ NOT NULL,questions JSONB NOT NULL,created_at TIMESTAMPTZ NOT NULL DEFAULT now(),CHECK(closes_at>opens_at));
CREATE TABLE game_rooms(
 id TEXT PRIMARY KEY,owner_id TEXT NOT NULL REFERENCES users(id),mode TEXT NOT NULL CHECK(mode IN ('gauntlet','speed','duel','party','cup')),
 state TEXT NOT NULL DEFAULT 'waiting' CHECK(state IN ('waiting','running','finished','cancelled')),
 subject_id TEXT,capacity INTEGER NOT NULL CHECK(capacity BETWEEN 1 AND 4),join_code TEXT UNIQUE,
 matchmaking BOOLEAN NOT NULL DEFAULT false,cup_id TEXT REFERENCES game_cups(id),
 questions JSONB NOT NULL,current_position INTEGER NOT NULL DEFAULT 0,round_seconds INTEGER NOT NULL CHECK(round_seconds BETWEEN 5 AND 60),
 round_started_at TIMESTAMPTZ,round_ends_at TIMESTAMPTZ,deadline TIMESTAMPTZ,version INTEGER NOT NULL DEFAULT 1,
 created_at TIMESTAMPTZ NOT NULL DEFAULT now(),finished_at TIMESTAMPTZ,request_key TEXT NOT NULL,request_hash TEXT NOT NULL,UNIQUE(owner_id,request_key)
);
CREATE INDEX game_room_work ON game_rooms(round_ends_at,id) WHERE state='running';
CREATE INDEX game_room_queue ON game_rooms(mode,subject_id,created_at) WHERE state='waiting' AND matchmaking;
CREATE TABLE game_start_requests(user_id TEXT NOT NULL REFERENCES users(id),request_key TEXT NOT NULL,room_id TEXT NOT NULL REFERENCES game_rooms(id),request_hash TEXT NOT NULL,PRIMARY KEY(user_id,request_key));
GRANT SELECT,INSERT ON game_start_requests TO mpsc;
CREATE TABLE game_members(room_id TEXT NOT NULL REFERENCES game_rooms(id),user_id TEXT NOT NULL REFERENCES users(id),
 joined_at TIMESTAMPTZ NOT NULL DEFAULT now(),left_at TIMESTAMPTZ,released_at TIMESTAMPTZ,score INTEGER NOT NULL DEFAULT 0,
 correct INTEGER NOT NULL DEFAULT 0,wrong INTEGER NOT NULL DEFAULT 0,skipped INTEGER NOT NULL DEFAULT 0,excluded INTEGER NOT NULL DEFAULT 0,
 elapsed_ms INTEGER NOT NULL DEFAULT 0,lives INTEGER NOT NULL DEFAULT 3,streak INTEGER NOT NULL DEFAULT 0,distance INTEGER NOT NULL DEFAULT 0,
 public_result BOOLEAN NOT NULL DEFAULT false,PRIMARY KEY(room_id,user_id));
CREATE UNIQUE INDEX game_one_active ON game_members(user_id) WHERE released_at IS NULL;
CREATE INDEX game_member_history ON game_members(user_id,joined_at DESC);
CREATE TABLE game_answers(room_id TEXT NOT NULL,user_id TEXT NOT NULL,position INTEGER NOT NULL CHECK(position>=0),chosen_index INTEGER,correct BOOLEAN NOT NULL,elapsed_ms INTEGER NOT NULL CHECK(elapsed_ms>=0),attempt_id BIGINT REFERENCES attempts(id),excluded BOOLEAN NOT NULL DEFAULT false,created_at TIMESTAMPTZ NOT NULL DEFAULT now(),PRIMARY KEY(room_id,user_id,position),FOREIGN KEY(room_id,user_id) REFERENCES game_members(room_id,user_id));
CREATE FUNCTION game_answer_immutable() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN
 IF ROW(OLD.room_id,OLD.user_id,OLD.position,OLD.chosen_index,OLD.correct,OLD.elapsed_ms,OLD.created_at) IS DISTINCT FROM ROW(NEW.room_id,NEW.user_id,NEW.position,NEW.chosen_index,NEW.correct,NEW.elapsed_ms,NEW.created_at) THEN RAISE EXCEPTION 'recorded game choices are immutable'; END IF; RETURN NEW; END $$;
CREATE TRIGGER game_choice_immutable BEFORE UPDATE ON game_answers FOR EACH ROW EXECUTE FUNCTION game_answer_immutable();
CREATE TABLE game_cup_entries(cup_id TEXT NOT NULL REFERENCES game_cups(id),user_id TEXT NOT NULL REFERENCES users(id),room_id TEXT NOT NULL UNIQUE REFERENCES game_rooms(id),PRIMARY KEY(cup_id,user_id));
CREATE TABLE game_events(id BIGSERIAL PRIMARY KEY,room_id TEXT NOT NULL REFERENCES game_rooms(id),actor_id TEXT REFERENCES users(id),action TEXT NOT NULL,detail JSONB NOT NULL DEFAULT '{}',created_at TIMESTAMPTZ NOT NULL DEFAULT now());
CREATE TRIGGER game_event_immutable BEFORE UPDATE OR DELETE ON game_events FOR EACH ROW EXECUTE FUNCTION review_immutable();
CREATE FUNCTION game_snapshot_immutable() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN
 IF OLD.questions IS DISTINCT FROM NEW.questions OR OLD.mode<>NEW.mode OR OLD.cup_id IS DISTINCT FROM NEW.cup_id THEN RAISE EXCEPTION 'game question snapshots are immutable'; END IF; RETURN NEW; END $$;
CREATE TRIGGER game_snapshot BEFORE UPDATE ON game_rooms FOR EACH ROW EXECUTE FUNCTION game_snapshot_immutable();
CREATE TRIGGER cup_snapshot BEFORE UPDATE OR DELETE ON game_cups FOR EACH ROW EXECUTE FUNCTION review_immutable();
GRANT SELECT,INSERT,UPDATE ON game_rooms,game_members,game_answers TO mpsc;
GRANT SELECT,INSERT ON game_cups,game_cup_entries,game_events TO mpsc;
GRANT USAGE,SELECT ON SEQUENCE game_events_id_seq TO mpsc;
CREATE OR REPLACE FUNCTION reward_study_attempt(aid BIGINT) RETURNS void LANGUAGE plpgsql AS $$
DECLARE a attempts%ROWTYPE; claimed TEXT; earned INTEGER; proof JSONB;
BEGIN
 SELECT * INTO a FROM attempts WHERE id=aid;
 IF NOT FOUND OR NOT a.correct OR a.canonical_id IS NULL OR a.context NOT IN ('practice','mock','game') THEN RETURN; END IF;
 IF NOT EXISTS(SELECT 1 FROM users WHERE id=a.user_id AND email IS NOT NULL) THEN RETURN; END IF;
 IF a.context='mock' THEN
   SELECT sq.snapshot INTO proof FROM mock_session_questions sq JOIN mock_sessions m ON m.id=sq.mock_id WHERE sq.mock_id=a.mock_id AND sq.canonical_id=a.canonical_id AND m.submitted_at IS NOT NULL AND NOT m.late AND m.user_id=a.user_id;
 ELSE proof:=a.scoring_snapshot; END IF;
 IF proof IS NULL OR proof->>'answer_source' NOT IN ('official','key') OR proof->>'answer_text' IS DISTINCT FROM a.chosen_text THEN RETURN; END IF;
 IF NOT EXISTS(SELECT 1 FROM v_scorable WHERE id=a.canonical_id AND answer_text=a.chosen_text) THEN RETURN; END IF;
 PERFORM pg_advisory_xact_lock(hashtext('rewards:'||a.user_id));
 SELECT COALESCE(sum(xp),0) INTO earned FROM reward_ledger WHERE user_id=a.user_id AND kind IN ('study','game') AND created_at >= (date_trunc('day',now() AT TIME ZONE 'Asia/Kolkata') AT TIME ZONE 'Asia/Kolkata');
 IF earned>=300 THEN RETURN; END IF;
 INSERT INTO reward_question_claims(user_id,canonical_id,attempt_id) VALUES(a.user_id,a.canonical_id,a.id) ON CONFLICT DO NOTHING RETURNING canonical_id INTO claimed;
 IF claimed IS NULL THEN RETURN; END IF;
 INSERT INTO reward_profiles(user_id) VALUES(a.user_id) ON CONFLICT DO NOTHING;
 INSERT INTO reward_ledger(user_id,event_key,kind,xp,points,note) VALUES(a.user_id,'question:'||a.user_id||':'||a.canonical_id,CASE WHEN a.context='game' THEN 'game' ELSE 'study' END,10,1,'First correct verified-key question');
END;$$;
COMMIT;
