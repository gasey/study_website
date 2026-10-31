BEGIN;
CREATE TABLE inbox_preferences (
 user_id TEXT PRIMARY KEY REFERENCES users(id),
 in_app JSONB NOT NULL DEFAULT '{}'::jsonb CHECK(jsonb_typeof(in_app)='object'),
 updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE review_notifications ADD COLUMN category TEXT NOT NULL DEFAULT 'system'
 CHECK(category IN ('discussions','desks','calendar','contributions','materials','scores','system'));
ALTER TABLE review_notifications ADD COLUMN silent BOOLEAN NOT NULL DEFAULT false;
UPDATE review_notifications SET category=CASE
 WHEN discussion_question_id IS NOT NULL THEN 'discussions'
 WHEN study_desk_id IS NOT NULL THEN 'desks'
 WHEN calendar_event_id IS NOT NULL THEN 'calendar'
 WHEN mock_id IS NOT NULL THEN 'scores'
 WHEN material_id IS NOT NULL THEN 'materials'
 WHEN contribution_id IS NOT NULL THEN 'contributions' ELSE 'system' END;
CREATE FUNCTION inbox_notice_defaults() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN
 NEW.category=CASE
 WHEN NEW.discussion_question_id IS NOT NULL THEN 'discussions'
 WHEN NEW.study_desk_id IS NOT NULL THEN 'desks'
 WHEN NEW.calendar_event_id IS NOT NULL THEN 'calendar'
 WHEN NEW.mock_id IS NOT NULL THEN 'scores'
 WHEN NEW.material_id IS NOT NULL THEN 'materials'
 WHEN NEW.contribution_id IS NOT NULL THEN 'contributions' ELSE 'system' END;
 NEW.silent=COALESCE((SELECT NOT COALESCE((p.in_app->>NEW.category)::boolean,true) FROM inbox_preferences p WHERE p.user_id=NEW.user_id),false);
 RETURN NEW;
END $$;
CREATE TRIGGER inbox_notice_defaults BEFORE INSERT ON review_notifications FOR EACH ROW EXECUTE FUNCTION inbox_notice_defaults();
CREATE INDEX inbox_category_cursor ON review_notifications(user_id,category,id DESC);
CREATE INDEX inbox_unread ON review_notifications(user_id,id DESC) WHERE read_at IS NULL AND NOT silent;
CREATE TABLE inbox_desk_reads (
 user_id TEXT NOT NULL REFERENCES users(id),desk_id TEXT NOT NULL REFERENCES study_desks(id),
 last_message_id BIGINT NOT NULL DEFAULT 0 CHECK(last_message_id>=0),updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 PRIMARY KEY(user_id,desk_id)
);
GRANT SELECT,INSERT,UPDATE ON inbox_preferences,inbox_desk_reads TO mpsc;
COMMIT;
