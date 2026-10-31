BEGIN;
CREATE TABLE exam_calendar_events (
 id TEXT PRIMARY KEY, collection_id TEXT REFERENCES collections(id), title TEXT NOT NULL CHECK(length(title) BETWEEN 3 AND 180),
 kind TEXT NOT NULL CHECK(kind IN ('notification','deadline','admit_card','exam','answer_key','result')),
 starts_on DATE, ends_on DATE, summary TEXT NOT NULL DEFAULT '', source_url TEXT NOT NULL,
 source_reference TEXT NOT NULL, verification_note TEXT NOT NULL, verified_on DATE NOT NULL,
 state TEXT NOT NULL DEFAULT 'draft' CHECK(state IN ('draft','published','archived')),
 version INTEGER NOT NULL DEFAULT 1 CHECK(version>0),
 created_by TEXT REFERENCES users(id), updated_by TEXT REFERENCES users(id),
 created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now(), published_at TIMESTAMPTZ,
 CHECK(ends_on IS NULL OR (starts_on IS NOT NULL AND ends_on>=starts_on)),
 CHECK(kind='notification' OR starts_on IS NOT NULL),CHECK(octet_length(summary)<=12000)
);
CREATE INDEX calendar_public_dates ON exam_calendar_events(starts_on,id) WHERE state='published';
CREATE INDEX calendar_public_notices ON exam_calendar_events(published_at DESC,id) WHERE state='published';
CREATE TABLE user_calendar_saved(user_id TEXT NOT NULL REFERENCES users(id),event_id TEXT NOT NULL REFERENCES exam_calendar_events(id),created_at TIMESTAMPTZ NOT NULL DEFAULT now(),PRIMARY KEY(user_id,event_id));
CREATE INDEX calendar_event_savers ON user_calendar_saved(event_id,user_id);
CREATE TABLE user_calendar_preferences(user_id TEXT PRIMARY KEY REFERENCES users(id),reminders BOOLEAN NOT NULL DEFAULT false,updated_at TIMESTAMPTZ NOT NULL DEFAULT now());
CREATE TABLE calendar_history(id BIGSERIAL PRIMARY KEY,event_id TEXT NOT NULL REFERENCES exam_calendar_events(id),actor_id TEXT REFERENCES users(id),version INTEGER NOT NULL,reason TEXT NOT NULL,snapshot JSONB NOT NULL,created_at TIMESTAMPTZ NOT NULL DEFAULT now(),UNIQUE(event_id,version));
CREATE FUNCTION calendar_history_immutable() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'calendar history is append-only'; END $$;
CREATE TRIGGER calendar_history_immutable BEFORE UPDATE OR DELETE ON calendar_history FOR EACH ROW EXECUTE FUNCTION calendar_history_immutable();
ALTER TABLE review_notifications ADD COLUMN calendar_event_id TEXT REFERENCES exam_calendar_events(id);
GRANT SELECT,INSERT,UPDATE ON exam_calendar_events,user_calendar_preferences TO mpsc;
GRANT SELECT,INSERT,DELETE ON user_calendar_saved TO mpsc;
GRANT SELECT,INSERT ON calendar_history TO mpsc;
GRANT USAGE,SELECT ON SEQUENCE calendar_history_id_seq TO mpsc;
COMMIT;
