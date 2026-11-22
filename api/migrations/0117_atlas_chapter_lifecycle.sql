-- Reviewed-content adapter for Atlas. No economic or bank state.
BEGIN;
CREATE TABLE atlas_chapters (
 id text PRIMARY KEY CHECK(id ~ '^[a-z0-9][a-z0-9-]{0,99}$'),
 status text NOT NULL DEFAULT 'draft' CHECK(status IN ('draft','published','held')),
 current_version integer,
 lock_version integer NOT NULL DEFAULT 1 CHECK(lock_version>0),
 position integer NOT NULL DEFAULT 1000,
 updated_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
CREATE TABLE atlas_chapter_versions (
 chapter_id text NOT NULL REFERENCES atlas_chapters(id),
 revision integer NOT NULL CHECK(revision>0),
 body jsonb NOT NULL CHECK(jsonb_typeof(body)='object'),
 body_hash text NOT NULL CHECK(body_hash ~ '^[a-f0-9]{64}$'),
 authored_by text REFERENCES users(id),
 attribution text NOT NULL CHECK(attribution IN ('current-site-content','owner')),
 note text NOT NULL CHECK(length(btrim(note)) BETWEEN 5 AND 2000),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(chapter_id,revision)
);
ALTER TABLE atlas_chapters ADD CONSTRAINT atlas_current_version_fk FOREIGN KEY(id,current_version)
 REFERENCES atlas_chapter_versions(chapter_id,revision) DEFERRABLE INITIALLY DEFERRED;
CREATE TABLE atlas_drafts (
 chapter_id text NOT NULL REFERENCES atlas_chapters(id),
 user_id text NOT NULL REFERENCES users(id),
 body jsonb NOT NULL CHECK(jsonb_typeof(body)='object'),
 version integer NOT NULL DEFAULT 1 CHECK(version>0),
 base_version integer NOT NULL,
 updated_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(chapter_id,user_id)
);
CREATE TABLE atlas_chapter_events (
 id bigserial PRIMARY KEY, chapter_id text NOT NULL REFERENCES atlas_chapters(id),
 action text NOT NULL CHECK(action IN ('seed','save','preview','publish','hold','rollback')),
 actor_id text REFERENCES users(id), revision integer,
 detail jsonb NOT NULL DEFAULT '{}', created_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
CREATE FUNCTION atlas_chapter_history_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'Atlas chapter history is immutable'; END $$;
CREATE TRIGGER atlas_versions_immutable BEFORE UPDATE OR DELETE ON atlas_chapter_versions FOR EACH ROW EXECUTE FUNCTION atlas_chapter_history_immutable();
CREATE TRIGGER atlas_events_immutable BEFORE UPDATE OR DELETE ON atlas_chapter_events FOR EACH ROW EXECUTE FUNCTION atlas_chapter_history_immutable();
GRANT SELECT,INSERT,UPDATE ON atlas_chapters,atlas_drafts TO mpsc;
GRANT SELECT,INSERT ON atlas_chapter_versions,atlas_chapter_events TO mpsc;
GRANT USAGE,SELECT ON SEQUENCE atlas_chapter_events_id_seq TO mpsc;
COMMIT;
