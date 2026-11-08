BEGIN;
CREATE TABLE current_affairs_entities (
 id text PRIMARY KEY,
 name text NOT NULL,
 jurisdiction text NOT NULL,
 predicate text NOT NULL,
 created_by text NOT NULL REFERENCES users(id),
 live_revision bigint,
 version integer NOT NULL DEFAULT 0,
 UNIQUE(name,jurisdiction,predicate)
);
CREATE TABLE current_affairs_revisions (
 id bigserial PRIMARY KEY,
 entity_id text NOT NULL REFERENCES current_affairs_entities(id),
 author_id text NOT NULL REFERENCES users(id),
 request_key text NOT NULL,
 base_version integer NOT NULL,
 payload jsonb NOT NULL,
 state text NOT NULL DEFAULT 'pending' CHECK(state IN ('pending','published','superseded','rejected','retracted')),
 reviewer_id text REFERENCES users(id),
 decision_reason text,
 created_at timestamptz NOT NULL DEFAULT now(),
 decided_at timestamptz,
 UNIQUE(author_id,request_key),
 CHECK(state NOT IN ('published','superseded') OR reviewer_id IS NOT NULL AND reviewer_id<>author_id)
);
ALTER TABLE current_affairs_entities ADD CONSTRAINT current_affairs_live_revision_fk FOREIGN KEY(live_revision) REFERENCES current_affairs_revisions(id);
CREATE TABLE current_affairs_links (
 revision_id bigint NOT NULL REFERENCES current_affairs_revisions(id),
 appearance_id text NOT NULL REFERENCES appearances(id),
 canonical_id text NOT NULL REFERENCES canonical_questions(id),
 PRIMARY KEY(revision_id,appearance_id)
);
CREATE INDEX current_affairs_question_links ON current_affairs_links(canonical_id,revision_id);
CREATE FUNCTION current_affairs_revision_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF TG_OP='DELETE' THEN RAISE EXCEPTION 'Current affairs history cannot be deleted'; END IF;
 IF (NEW.id,NEW.entity_id,NEW.author_id,NEW.request_key,NEW.base_version,NEW.payload,NEW.created_at)
 IS DISTINCT FROM (OLD.id,OLD.entity_id,OLD.author_id,OLD.request_key,OLD.base_version,OLD.payload,OLD.created_at)
 THEN RAISE EXCEPTION 'Current affairs revision content is immutable'; END IF;
 IF NOT ((OLD.state='pending' AND NEW.state IN ('published','rejected')) OR (OLD.state='published' AND NEW.state IN ('superseded','retracted')))
 THEN RAISE EXCEPTION 'Invalid current affairs transition'; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER current_affairs_revision_guard BEFORE UPDATE OR DELETE ON current_affairs_revisions FOR EACH ROW EXECUTE FUNCTION current_affairs_revision_guard();
CREATE TRIGGER current_affairs_links_immutable BEFORE UPDATE OR DELETE ON current_affairs_links FOR EACH ROW EXECUTE FUNCTION editorial_checks_immutable();
GRANT SELECT,INSERT,UPDATE ON current_affairs_entities,current_affairs_revisions TO mpsc;
GRANT SELECT,INSERT ON current_affairs_links TO mpsc;
GRANT USAGE,SELECT ON SEQUENCE current_affairs_revisions_id_seq TO mpsc;
COMMIT;
