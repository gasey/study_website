BEGIN;
-- Editorial collections reference bank IDs; bank questions remain bank-owned.
CREATE TABLE learning_catalog (
 id text PRIMARY KEY,
 kind text NOT NULL CHECK(kind IN ('day','practice')),
 author_id text NOT NULL REFERENCES users(id),
 version integer NOT NULL DEFAULT 1,
 state text NOT NULL DEFAULT 'draft' CHECK(state IN ('draft','submitted','changes_requested','rejected','published','withdrawn')),
 payload jsonb NOT NULL,
 live_payload jsonb,
 updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX learning_catalog_state ON learning_catalog(state,updated_at DESC);
CREATE TABLE learning_catalog_history (
 id bigserial PRIMARY KEY,
 entry_id text NOT NULL REFERENCES learning_catalog(id),
 version integer NOT NULL,
 actor_id text NOT NULL REFERENCES users(id),
 action text NOT NULL,
 payload jsonb NOT NULL,
 reason text NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(entry_id,version)
);
CREATE TRIGGER learning_catalog_history_immutable BEFORE UPDATE OR DELETE ON learning_catalog_history
 FOR EACH ROW EXECUTE FUNCTION editorial_checks_immutable();
GRANT SELECT,INSERT,UPDATE ON learning_catalog TO mpsc;
GRANT SELECT,INSERT ON learning_catalog_history TO mpsc;
GRANT USAGE,SELECT ON SEQUENCE learning_catalog_history_id_seq TO mpsc;
COMMIT;
