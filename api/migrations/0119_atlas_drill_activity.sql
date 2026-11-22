-- Display/activity only: no attempts, mastery, streak or award triggers.
BEGIN;
CREATE TABLE atlas_drill_presentations (
 id uuid PRIMARY KEY, user_id text NOT NULL REFERENCES users(id),
 chapter_id text NOT NULL REFERENCES atlas_chapters(id), revision integer NOT NULL,
 body_hash text NOT NULL, drill_id text NOT NULL, request_key uuid NOT NULL,
 snapshot jsonb NOT NULL, created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 expires_at timestamptz NOT NULL DEFAULT clock_timestamp()+interval '30 minutes',
 UNIQUE(user_id,request_key),
 FOREIGN KEY(chapter_id,revision) REFERENCES atlas_chapter_versions(chapter_id,revision)
);
CREATE TABLE atlas_drill_results (
 presentation_id uuid PRIMARY KEY REFERENCES atlas_drill_presentations(id),
 user_id text NOT NULL REFERENCES users(id), chapter_id text NOT NULL,
 body_hash text NOT NULL, drill_id text NOT NULL, correct boolean NOT NULL,
 choice jsonb NOT NULL, result jsonb NOT NULL,
 at timestamptz NOT NULL DEFAULT clock_timestamp()
);
CREATE INDEX atlas_drill_user_day ON atlas_drill_results(user_id,at);
CREATE TABLE atlas_exploration (
 user_id text NOT NULL REFERENCES users(id),chapter_id text NOT NULL REFERENCES atlas_chapters(id),
 body_hash text NOT NULL, viewed_layers text[] NOT NULL DEFAULT '{}',
 updated_at timestamptz NOT NULL DEFAULT clock_timestamp(),PRIMARY KEY(user_id,chapter_id)
);
CREATE TABLE atlas_practice_suggestions (
 user_id text NOT NULL REFERENCES users(id),binding_id uuid NOT NULL REFERENCES atlas_topic_bindings(id),
 source_hash text NOT NULL,created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(user_id,binding_id)
);
CREATE TRIGGER atlas_results_immutable BEFORE UPDATE OR DELETE ON atlas_drill_results
 FOR EACH ROW EXECUTE FUNCTION atlas_chapter_history_immutable();
CREATE TRIGGER atlas_presentations_immutable BEFORE UPDATE OR DELETE ON atlas_drill_presentations
 FOR EACH ROW EXECUTE FUNCTION atlas_chapter_history_immutable();
GRANT SELECT,INSERT ON atlas_drill_presentations,atlas_drill_results TO mpsc;
GRANT SELECT,INSERT,UPDATE ON atlas_exploration,atlas_practice_suggestions TO mpsc;
COMMIT;
