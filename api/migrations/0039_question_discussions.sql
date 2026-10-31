BEGIN;
ALTER TABLE posts ADD COLUMN request_key TEXT;
ALTER TABLE posts ADD COLUMN request_hash TEXT;
ALTER TABLE posts ADD COLUMN source_context JSONB NOT NULL DEFAULT '{}';
ALTER TABLE posts ADD COLUMN source_links JSONB NOT NULL DEFAULT '[]';
ALTER TABLE abuse_reports ADD COLUMN note TEXT;
CREATE UNIQUE INDEX posts_author_request ON posts(author_id,request_key) WHERE request_key IS NOT NULL;
CREATE INDEX posts_parent_visible ON posts(parent_id,accepted DESC,created_at,id);
CREATE INDEX posts_author_moderation ON posts(author_id,created_at) WHERE NOT hidden;
CREATE FUNCTION discussion_post_content_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF ROW(OLD.canonical_id,OLD.parent_id,OLD.kind,OLD.body,OLD.source_context,OLD.source_links,OLD.created_at,OLD.request_key,OLD.request_hash)
 IS DISTINCT FROM ROW(NEW.canonical_id,NEW.parent_id,NEW.kind,NEW.body,NEW.source_context,NEW.source_links,NEW.created_at,NEW.request_key,NEW.request_hash)
 THEN RAISE EXCEPTION 'discussion content is immutable; withdraw and post a clarification'; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER discussion_content_immutable BEFORE UPDATE ON posts FOR EACH ROW EXECUTE FUNCTION discussion_post_content_immutable();
CREATE INDEX posts_question_roots ON posts(canonical_id,pinned DESC,created_at DESC,id DESC) WHERE parent_id IS NULL AND NOT hidden AND NOT before_fix;
CREATE INDEX posts_feed_published ON posts(pinned DESC,created_at DESC,id DESC) WHERE parent_id IS NULL AND NOT hidden AND NOT needs_approval AND NOT before_fix;
CREATE TABLE discussion_disclosures (
 user_id TEXT NOT NULL REFERENCES users(id), canonical_id TEXT NOT NULL REFERENCES canonical_questions(id),
 created_at TIMESTAMPTZ NOT NULL DEFAULT now(), PRIMARY KEY(user_id,canonical_id)
);
CREATE TABLE discussion_events (
 id BIGSERIAL PRIMARY KEY, canonical_id TEXT NOT NULL REFERENCES canonical_questions(id),
 post_id BIGINT REFERENCES posts(id), actor_id TEXT NOT NULL REFERENCES users(id),
 action TEXT NOT NULL, detail JSONB NOT NULL DEFAULT '{}', created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE FUNCTION discussion_events_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'discussion events are append-only'; END $$;
CREATE TRIGGER discussion_events_immutable BEFORE UPDATE OR DELETE ON discussion_events FOR EACH ROW EXECUTE FUNCTION discussion_events_immutable();
GRANT SELECT,INSERT ON discussion_events TO mpsc;
GRANT SELECT,INSERT,DELETE ON discussion_disclosures TO mpsc;
GRANT USAGE,SELECT ON SEQUENCE discussion_events_id_seq TO mpsc;
ALTER TABLE review_notifications ADD COLUMN discussion_post_id BIGINT REFERENCES posts(id);
ALTER TABLE review_notifications ADD COLUMN discussion_question_id TEXT REFERENCES canonical_questions(id);
COMMIT;
