BEGIN;
CREATE TABLE bank_paper_intake (
 expectation_id text PRIMARY KEY REFERENCES bank_paper_expectations(id),
 stage text NOT NULL DEFAULT 'discovered' CHECK(stage IN ('discovered','acquired','extracted','review','ready','published')),
 version integer NOT NULL DEFAULT 1,source_sha256 text,artifact jsonb,review_fingerprint text,
 review_note text,reviewed_by text REFERENCES users(id),sync_id bigint REFERENCES sync_log(id),
 last_error text,updated_by text NOT NULL,updated_at timestamptz NOT NULL DEFAULT now(),
 CHECK(source_sha256 IS NULL OR source_sha256 ~ '^[0-9a-f]{64}$')
);
CREATE TABLE learning_checkpoints (
 user_id text NOT NULL REFERENCES users(id),kind text NOT NULL CHECK(kind='practice'),
 route text NOT NULL,question_id text REFERENCES canonical_questions(id),appearance_id text REFERENCES appearances(id),
 version integer NOT NULL DEFAULT 1,updated_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(user_id,kind)
);
CREATE TABLE daily_revision_sessions (
 id text PRIMARY KEY,user_id text NOT NULL REFERENCES users(id),day date NOT NULL,
 exam_scope text NOT NULL CHECK(exam_scope IN ('all','mizoram-recruitment')),
 question_ids text[] NOT NULL,created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(user_id,day,exam_scope)
);
-- Completion is a genuine later attempt, never a client-reported checkbox.
CREATE TABLE daily_revision_completions (
 session_id text NOT NULL REFERENCES daily_revision_sessions(id),question_id text NOT NULL REFERENCES canonical_questions(id),
 attempt_id bigint NOT NULL REFERENCES attempts(id),created_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(session_id,question_id)
);
CREATE FUNCTION record_daily_revision_completion() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN
 IF NEW.context IN ('practice','review') THEN
 INSERT INTO daily_revision_completions(session_id,question_id,attempt_id)
 SELECT s.id,NEW.canonical_id,NEW.id FROM daily_revision_sessions s
 WHERE s.user_id=NEW.user_id AND NEW.canonical_id=ANY(s.question_ids) AND NEW.at>=s.created_at
 ON CONFLICT DO NOTHING;
 END IF; RETURN NEW; END $$;
CREATE TRIGGER daily_revision_answer AFTER INSERT ON attempts FOR EACH ROW EXECUTE FUNCTION record_daily_revision_completion();
CREATE TABLE question_change_events (
 id bigserial PRIMARY KEY,question_id text NOT NULL REFERENCES canonical_questions(id),
 changed_fields text[] NOT NULL,created_at timestamptz NOT NULL DEFAULT now(),
 recipient_cursor text NOT NULL DEFAULT '',finished_at timestamptz,failures integer NOT NULL DEFAULT 0,last_error text
);
CREATE INDEX question_changes_pending ON question_change_events(id) WHERE finished_at IS NULL;
ALTER TABLE review_notifications ADD COLUMN corrected_question_id text REFERENCES canonical_questions(id);
ALTER TABLE review_notifications ADD COLUMN question_change_id bigint REFERENCES question_change_events(id);
CREATE OR REPLACE FUNCTION inbox_notice_defaults() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN
 NEW.category=CASE WHEN NEW.corrected_question_id IS NOT NULL THEN 'scores'
 WHEN NEW.discussion_question_id IS NOT NULL THEN 'discussions'
 WHEN NEW.study_desk_id IS NOT NULL THEN 'desks'
 WHEN NEW.calendar_event_id IS NOT NULL THEN 'calendar'
 WHEN NEW.mock_id IS NOT NULL THEN 'scores'
 WHEN NEW.material_id IS NOT NULL THEN 'materials'
 WHEN NEW.contribution_id IS NOT NULL THEN 'contributions' ELSE 'system' END;
 NEW.silent=COALESCE((SELECT NOT COALESCE((p.in_app->>NEW.category)::boolean,true) FROM inbox_preferences p WHERE p.user_id=NEW.user_id),false);
 RETURN NEW;
END $$;
CREATE FUNCTION record_question_change() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE fields text[]='{}';
BEGIN
 IF OLD.question IS DISTINCT FROM NEW.question THEN fields=array_append(fields,'question'); END IF;
 IF OLD.options IS DISTINCT FROM NEW.options THEN fields=array_append(fields,'options'); END IF;
 IF ROW(OLD.answer_text,OLD.answer_source,OLD.answer_key_ref,OLD.key_disputed) IS DISTINCT FROM ROW(NEW.answer_text,NEW.answer_source,NEW.answer_key_ref,NEW.key_disputed) THEN fields=array_append(fields,'answer or evidence'); END IF;
 IF OLD.explanation IS DISTINCT FROM NEW.explanation THEN fields=array_append(fields,'explanation'); END IF;
 IF ROW(OLD.direction,OLD.passage,OLD.question_markup,OLD.options_markup) IS DISTINCT FROM ROW(NEW.direction,NEW.passage,NEW.question_markup,NEW.options_markup) THEN fields=array_append(fields,'instructions or formatting'); END IF;
 IF ROW(OLD.type,OLD.status,OLD.source_defect) IS DISTINCT FROM ROW(NEW.type,NEW.status,NEW.source_defect) THEN fields=array_append(fields,'availability or scoring eligibility'); END IF;
 IF cardinality(fields)>0 THEN INSERT INTO question_change_events(question_id,changed_fields) VALUES(NEW.id,fields); END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER question_change_notice AFTER UPDATE ON canonical_questions FOR EACH ROW EXECUTE FUNCTION record_question_change();
CREATE FUNCTION record_appearance_change() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN
 IF NEW.canonical_id IS NOT NULL THEN INSERT INTO question_change_events(question_id,changed_fields) VALUES(NEW.canonical_id,ARRAY['source instructions or figure']); END IF; RETURN NEW;
END $$;
CREATE TRIGGER appearance_change_notice AFTER UPDATE ON appearances FOR EACH ROW
 WHEN ((OLD.direction,OLD.passage,OLD.question_markup,OLD.options_markup,OLD.has_diagram,OLD.figure_image) IS DISTINCT FROM (NEW.direction,NEW.passage,NEW.question_markup,NEW.options_markup,NEW.has_diagram,NEW.figure_image)) EXECUTE FUNCTION record_appearance_change();
CREATE FUNCTION record_reviewed_answer_change() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE target text;
BEGIN SELECT canonical_id INTO target FROM bank_contributions WHERE id=NEW.contribution_id;
 IF target IS NOT NULL THEN INSERT INTO question_change_events(question_id,changed_fields) VALUES(target,ARRAY['review publication']); END IF; RETURN NEW; END $$;
CREATE TRIGGER publication_change_notice AFTER UPDATE OF state ON bank_publications FOR EACH ROW WHEN (NEW.state IN ('applied','reverted') AND OLD.state IS DISTINCT FROM NEW.state) EXECUTE FUNCTION record_reviewed_answer_change();
CREATE INDEX attempts_user_question_latest ON attempts(user_id,canonical_id,at DESC,id DESC);
GRANT SELECT,INSERT,UPDATE ON bank_paper_intake,learning_checkpoints TO mpsc;
GRANT SELECT,INSERT ON question_change_events TO mpsc;
GRANT UPDATE(recipient_cursor,finished_at,failures,last_error) ON question_change_events TO mpsc;
GRANT SELECT,INSERT ON daily_revision_sessions,daily_revision_completions TO mpsc;
GRANT USAGE,SELECT ON SEQUENCE question_change_events_id_seq TO mpsc;
COMMIT;
