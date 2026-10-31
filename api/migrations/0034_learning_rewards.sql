BEGIN;
CREATE TABLE reward_profiles(user_id TEXT PRIMARY KEY REFERENCES users(id),board_public BOOLEAN NOT NULL DEFAULT false,created_at TIMESTAMPTZ NOT NULL DEFAULT now());
CREATE TABLE reward_ledger(id BIGSERIAL PRIMARY KEY,user_id TEXT NOT NULL REFERENCES users(id),event_key TEXT NOT NULL UNIQUE,kind TEXT NOT NULL CHECK(kind IN ('study','game','contribution','redemption','adjustment')),xp INTEGER NOT NULL DEFAULT 0,points INTEGER NOT NULL DEFAULT 0,note TEXT NOT NULL,created_at TIMESTAMPTZ NOT NULL DEFAULT now());
CREATE INDEX reward_ledger_user_time ON reward_ledger(user_id,created_at DESC,id DESC);
CREATE INDEX reward_ledger_board ON reward_ledger(created_at,user_id) WHERE xp<>0;
CREATE TRIGGER immutable_reward_ledger BEFORE UPDATE OR DELETE ON reward_ledger FOR EACH ROW EXECUTE FUNCTION review_immutable();
CREATE TABLE reward_question_claims(user_id TEXT NOT NULL REFERENCES users(id),canonical_id TEXT NOT NULL REFERENCES canonical_questions(id),attempt_id BIGINT NOT NULL REFERENCES attempts(id),PRIMARY KEY(user_id,canonical_id));
CREATE TABLE reward_catalog(id TEXT PRIMARY KEY,title TEXT NOT NULL,points INTEGER NOT NULL CHECK(points>0),pro_days INTEGER NOT NULL CHECK(pro_days BETWEEN 1 AND 30),enabled BOOLEAN NOT NULL DEFAULT false,version INTEGER NOT NULL DEFAULT 1,updated_at TIMESTAMPTZ NOT NULL DEFAULT now());
INSERT INTO reward_catalog(id,title,points,pro_days) VALUES('pro-week','7 days of Pro',1000,7);
CREATE TABLE reward_redemptions(id TEXT PRIMARY KEY,user_id TEXT NOT NULL REFERENCES users(id),idempotency_key TEXT NOT NULL,catalog_id TEXT NOT NULL REFERENCES reward_catalog(id),catalog_version INTEGER NOT NULL,points INTEGER NOT NULL CHECK(points>0),starts_at TIMESTAMPTZ NOT NULL,ends_at TIMESTAMPTZ NOT NULL,created_at TIMESTAMPTZ NOT NULL DEFAULT now(),UNIQUE(user_id,idempotency_key),CHECK(ends_at>starts_at));
CREATE INDEX reward_redemptions_user ON reward_redemptions(user_id,ends_at DESC);
CREATE TRIGGER immutable_reward_redemption BEFORE UPDATE OR DELETE ON reward_redemptions FOR EACH ROW EXECUTE FUNCTION review_immutable();
CREATE FUNCTION account_has_pro(uid TEXT) RETURNS BOOLEAN LANGUAGE sql STABLE AS $$
 SELECT EXISTS(SELECT 1 FROM users WHERE id=uid AND plan_code='pro' AND ((plan_status IN ('active','authenticated') AND (plan_ends_at IS NULL OR plan_ends_at>now())) OR (plan_status='trial' AND trial_ends_at>now()) OR plan_ends_at>now()))
 OR EXISTS(SELECT 1 FROM reward_redemptions WHERE user_id=uid AND starts_at<=now() AND ends_at>now());
$$;
CREATE FUNCTION reward_study_attempt(aid BIGINT) RETURNS void LANGUAGE plpgsql AS $$
DECLARE a attempts%ROWTYPE; claimed TEXT; earned INTEGER; proof JSONB;
BEGIN
 SELECT * INTO a FROM attempts WHERE id=aid;
 IF NOT FOUND OR NOT a.correct OR a.canonical_id IS NULL OR a.context NOT IN ('practice','mock') THEN RETURN; END IF;
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
 INSERT INTO reward_ledger(user_id,event_key,kind,xp,points,note) VALUES(a.user_id,'question:'||a.user_id||':'||a.canonical_id,'study',10,1,'First correct verified-key question');
END;$$;
CREATE FUNCTION reward_attempt_insert() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN IF NEW.context='practice' THEN PERFORM reward_study_attempt(NEW.id); END IF; RETURN NEW; END;$$;
CREATE TRIGGER award_practice_rewards AFTER INSERT ON attempts FOR EACH ROW EXECUTE FUNCTION reward_attempt_insert();
CREATE FUNCTION reward_mock_submit() RETURNS trigger LANGUAGE plpgsql AS $$ DECLARE aid BIGINT; BEGIN IF NEW.submitted_at IS NOT NULL AND OLD.submitted_at IS NULL THEN FOR aid IN SELECT id FROM attempts WHERE mock_id=NEW.id ORDER BY position,id LOOP PERFORM reward_study_attempt(aid); END LOOP; END IF; RETURN NEW; END;$$;
CREATE TRIGGER award_mock_rewards AFTER UPDATE ON mock_sessions FOR EACH ROW EXECUTE FUNCTION reward_mock_submit();
CREATE FUNCTION reward_contribution_credit() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN
 IF NOT EXISTS(SELECT 1 FROM users WHERE id=NEW.user_id AND email IS NOT NULL) THEN RETURN NEW; END IF;
 PERFORM pg_advisory_xact_lock(hashtext('rewards:'||NEW.user_id));
 INSERT INTO reward_profiles(user_id) VALUES(NEW.user_id) ON CONFLICT DO NOTHING;
 INSERT INTO reward_ledger(user_id,event_key,kind,xp,points,note) VALUES(NEW.user_id,'contribution-credit:'||NEW.id,'contribution',NEW.amount,NEW.amount,'Published contribution credit or reversal') ON CONFLICT DO NOTHING;
 RETURN NEW; END;$$;
CREATE TRIGGER award_contribution_rewards AFTER INSERT ON contribution_credit FOR EACH ROW EXECUTE FUNCTION reward_contribution_credit();
GRANT SELECT,INSERT,UPDATE ON reward_profiles,reward_catalog TO mpsc;
GRANT SELECT,INSERT ON reward_ledger,reward_question_claims,reward_redemptions TO mpsc;
GRANT USAGE,SELECT ON ALL SEQUENCES IN SCHEMA public TO mpsc;
CREATE TABLE exam_study_checkpoints(user_id TEXT NOT NULL REFERENCES users(id),collection_id TEXT NOT NULL REFERENCES collections(id),state JSONB NOT NULL,updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),PRIMARY KEY(user_id,collection_id));
GRANT SELECT,INSERT,UPDATE ON exam_study_checkpoints TO mpsc;
COMMIT;
