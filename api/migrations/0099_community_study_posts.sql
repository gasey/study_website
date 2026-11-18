BEGIN;
-- Free-standing notes use the existing moderation/report/vote lifecycle.
-- Canonical threads keep their non-null question anchor through the new check.
ALTER TABLE posts ALTER COLUMN canonical_id DROP NOT NULL;
ALTER TABLE posts DROP CONSTRAINT posts_kind_check;
ALTER TABLE posts ADD CONSTRAINT posts_kind_check CHECK(kind IN ('doubt','explanation','reply','study'));
ALTER TABLE posts ADD CONSTRAINT posts_anchor_kind CHECK((kind='study')=(canonical_id IS NULL));
ALTER TABLE posts ADD COLUMN topic_tag text REFERENCES review_taxonomy(id);
ALTER TABLE posts ADD CONSTRAINT posts_study_tag CHECK(topic_tag IS NULL OR kind='study');
ALTER TABLE discussion_events ALTER COLUMN canonical_id DROP NOT NULL;
CREATE OR REPLACE FUNCTION discussion_post_content_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF ROW(OLD.canonical_id,OLD.parent_id,OLD.kind,OLD.body,OLD.source_context,OLD.source_links,OLD.created_at,OLD.request_key,OLD.request_hash,OLD.topic_tag)
 IS DISTINCT FROM ROW(NEW.canonical_id,NEW.parent_id,NEW.kind,NEW.body,NEW.source_context,NEW.source_links,NEW.created_at,NEW.request_key,NEW.request_hash,NEW.topic_tag)
 THEN RAISE EXCEPTION 'discussion content is immutable; withdraw and post a clarification'; END IF;
 RETURN NEW;
END $$;
CREATE INDEX posts_author_daily ON posts(author_id,created_at,parent_id);
CREATE INDEX post_votes_by_voter ON post_votes(user_id,post_id);
COMMIT;
