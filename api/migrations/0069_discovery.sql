BEGIN;
CREATE TABLE discovery_picks (
 id text PRIMARY KEY,
 collection_id text NOT NULL REFERENCES collections(id),
 taxonomy_id text NOT NULL REFERENCES review_taxonomy(id),
 title text NOT NULL,
 why_now text NOT NULL,
 sources jsonb NOT NULL CHECK(jsonb_typeof(sources)='array'),
 fact_revision_id bigint REFERENCES current_affairs_revisions(id),
 state text NOT NULL DEFAULT 'draft' CHECK(state IN ('draft','published','retired')),
 expires_at timestamptz NOT NULL,
 version integer NOT NULL DEFAULT 1,
 created_by text NOT NULL REFERENCES users(id),
 published_at timestamptz,
 updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE discovery_pick_history (
 id bigserial PRIMARY KEY,
 pick_id text NOT NULL REFERENCES discovery_picks(id),
 actor_id text NOT NULL REFERENCES users(id),
 payload jsonb NOT NULL,
 reason text NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TRIGGER discovery_history_immutable BEFORE UPDATE OR DELETE ON discovery_pick_history
 FOR EACH ROW EXECUTE FUNCTION editorial_checks_immutable();
CREATE INDEX discovery_active ON discovery_picks(collection_id,expires_at) WHERE state='published';
CREATE INDEX attempts_discovery_recent ON attempts(at,canonical_id,user_id) WHERE context='practice';
CREATE INDEX posts_discovery_recent ON posts(created_at,canonical_id,author_id) WHERE NOT hidden AND NOT needs_approval AND NOT before_fix;
GRANT SELECT,INSERT,UPDATE ON discovery_picks TO mpsc;
GRANT SELECT,INSERT ON discovery_pick_history TO mpsc;
GRANT USAGE,SELECT ON SEQUENCE discovery_pick_history_id_seq TO mpsc;
COMMIT;
