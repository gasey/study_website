BEGIN;
-- Configuration only: source content and frozen assignments are not changed.
CREATE TABLE module_composition_drafts (
 collection_id text PRIMARY KEY REFERENCES collections(id),
 revision integer NOT NULL DEFAULT 1,
 base_version integer,
 payload jsonb NOT NULL,
 actor_id text NOT NULL REFERENCES users(id),
 updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE module_composition_history (
 id bigserial PRIMARY KEY,
 collection_id text NOT NULL REFERENCES collections(id),
 version integer NOT NULL,
 actor_id text NOT NULL REFERENCES users(id),
 reason text NOT NULL CHECK(length(btrim(reason))>=15),
 payload jsonb NOT NULL,
 preview_hash text NOT NULL,
 request_key text NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(collection_id,version), UNIQUE(actor_id,request_key)
);
CREATE TRIGGER module_composition_history_immutable BEFORE UPDATE OR DELETE ON module_composition_history
 FOR EACH ROW EXECUTE FUNCTION editorial_checks_immutable();
GRANT SELECT,INSERT,UPDATE ON module_composition_drafts TO mpsc;
GRANT SELECT,INSERT ON module_composition_history TO mpsc;
GRANT USAGE,SELECT ON SEQUENCE module_composition_history_id_seq TO mpsc;
GRANT SELECT,INSERT,UPDATE ON collections TO mpsc;
GRANT SELECT,INSERT ON collection_sections,collection_papers TO mpsc;
COMMIT;
