BEGIN;
-- Reviewed materials remain the source; a share owns only its commentary.
ALTER TABLE posts ADD COLUMN material_id text REFERENCES materials(id);
ALTER TABLE posts DROP CONSTRAINT posts_kind_check;
ALTER TABLE posts ADD CONSTRAINT posts_kind_check CHECK(kind IN ('doubt','explanation','reply','study','material-share'));
ALTER TABLE posts DROP CONSTRAINT posts_anchor_kind;
ALTER TABLE posts ADD CONSTRAINT posts_anchor_kind CHECK((kind IN ('study','material-share'))=(canonical_id IS NULL));
ALTER TABLE posts DROP CONSTRAINT posts_study_tag;
ALTER TABLE posts ADD CONSTRAINT posts_study_tag CHECK(topic_tag IS NULL OR kind IN ('study','material-share'));
ALTER TABLE posts ADD CONSTRAINT posts_material_anchor CHECK(
 (kind='material-share' AND material_id IS NOT NULL AND parent_id IS NULL
  AND COALESCE(source_context->'study_reference'->>'kind'='material'
      AND source_context->'study_reference'->>'id'=material_id,false))
 OR (kind<>'material-share' AND material_id IS NULL));
CREATE OR REPLACE FUNCTION discussion_post_content_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF ROW(OLD.canonical_id,OLD.parent_id,OLD.kind,OLD.body,OLD.source_context,OLD.source_links,OLD.created_at,OLD.request_key,OLD.request_hash,OLD.topic_tag,OLD.material_id)
 IS DISTINCT FROM ROW(NEW.canonical_id,NEW.parent_id,NEW.kind,NEW.body,NEW.source_context,NEW.source_links,NEW.created_at,NEW.request_key,NEW.request_hash,NEW.topic_tag,NEW.material_id)
 THEN RAISE EXCEPTION 'discussion content is immutable; withdraw and post a clarification'; END IF;
 RETURN NEW;
END $$;
CREATE INDEX posts_material_shares ON posts(material_id) WHERE kind='material-share';
COMMIT;
