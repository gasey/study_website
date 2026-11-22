-- Manual, versioned Atlas/topic links. No chapter or question is reclassified.
BEGIN;
CREATE TABLE atlas_topic_bindings (
 id uuid PRIMARY KEY,
 draft jsonb NOT NULL CHECK(jsonb_typeof(draft)='object'),
 live jsonb CHECK(live IS NULL OR jsonb_typeof(live)='object'),
 version integer NOT NULL DEFAULT 1 CHECK(version>0),
 updated_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
CREATE INDEX atlas_bindings_live_chapter ON atlas_topic_bindings((live->>'chapter_id')) WHERE live IS NOT NULL;
CREATE INDEX atlas_bindings_live_topic ON atlas_topic_bindings((live->>'topic_id')) WHERE live IS NOT NULL;
CREATE UNIQUE INDEX atlas_bindings_live_identity ON atlas_topic_bindings
 ((live->>'chapter_id'),(COALESCE(live->>'layer_id','')),(COALESCE(live->>'event_id','')),
  (live->>'subject_id'),(live->>'topic_id')) WHERE live IS NOT NULL;
CREATE TABLE atlas_binding_versions (
 id bigserial PRIMARY KEY,
 binding_id uuid NOT NULL REFERENCES atlas_topic_bindings(id),
 revision integer NOT NULL,
 action text NOT NULL CHECK(action IN ('save','publish','hold','rollback')),
 actor_id text NOT NULL REFERENCES users(id),
 payload jsonb,
 reason text NOT NULL CHECK(length(btrim(reason)) BETWEEN 5 AND 2000),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 UNIQUE(binding_id,revision)
);
CREATE FUNCTION atlas_binding_history_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'Atlas binding history is immutable'; END $$;
CREATE TRIGGER atlas_binding_history_immutable BEFORE UPDATE OR DELETE ON atlas_binding_versions
 FOR EACH ROW EXECUTE FUNCTION atlas_binding_history_immutable();
GRANT SELECT,INSERT,UPDATE ON atlas_topic_bindings TO mpsc;
GRANT SELECT,INSERT ON atlas_binding_versions TO mpsc;
GRANT USAGE,SELECT ON SEQUENCE atlas_binding_versions_id_seq TO mpsc;
COMMIT;
