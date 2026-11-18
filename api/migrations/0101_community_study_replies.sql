BEGIN;
-- Free-standing replies reuse study rows and existing immutable post history.
-- Existing canonical replies keep their established anchor and reader contract.
ALTER TABLE posts DROP CONSTRAINT post_reply_has_parent;
ALTER TABLE posts ADD CONSTRAINT post_reply_has_parent CHECK(
 (kind='reply' AND parent_id IS NOT NULL) OR kind='study'
 OR (kind NOT IN ('reply','study') AND parent_id IS NULL));
CREATE FUNCTION community_study_reply_anchor() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE root posts%ROWTYPE;
BEGIN
 IF NEW.kind='study' AND NEW.parent_id IS NOT NULL THEN
  SELECT * INTO root FROM posts WHERE id=NEW.parent_id FOR SHARE;
  IF NOT FOUND OR root.kind NOT IN ('study','material-share') OR root.parent_id IS NOT NULL
     OR NEW.source_context IS DISTINCT FROM root.source_context
     OR NEW.topic_tag IS DISTINCT FROM root.topic_tag THEN
   RAISE EXCEPTION 'study reply must inherit a top-level study or material anchor';
  END IF;
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER community_study_reply_anchor BEFORE INSERT ON posts
FOR EACH ROW EXECUTE FUNCTION community_study_reply_anchor();
COMMIT;
