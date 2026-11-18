BEGIN;
-- Original and every replacement are immutable snapshots. Anchors never change.
ALTER TABLE posts ADD COLUMN content_version integer NOT NULL DEFAULT 0 CHECK(content_version>=0);
ALTER TABLE posts ADD COLUMN edited_at timestamptz;
ALTER TABLE posts ADD COLUMN edit_locked boolean NOT NULL DEFAULT false;
UPDATE posts p SET edit_locked=true WHERE accepted OR EXISTS(
 SELECT 1 FROM discussion_events e WHERE e.post_id=p.id AND e.action='accepted');
CREATE TABLE post_revisions (
 post_id bigint NOT NULL REFERENCES posts(id), version integer NOT NULL CHECK(version>=0),
 body text NOT NULL, source_links jsonb NOT NULL, actor_id text NOT NULL REFERENCES users(id),
 created_at timestamptz NOT NULL DEFAULT now(), request_key text, request_hash text,
 PRIMARY KEY(post_id,version), UNIQUE(actor_id,request_key)
);
CREATE INDEX post_revisions_actor_day ON post_revisions(actor_id,created_at) WHERE version>0;
CREATE TRIGGER post_revisions_immutable BEFORE UPDATE OR DELETE ON post_revisions
 FOR EACH ROW EXECUTE FUNCTION discussion_events_immutable();
GRANT SELECT ON post_revisions TO mpsc;
CREATE OR REPLACE FUNCTION discussion_post_content_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF ROW(OLD.canonical_id,OLD.parent_id,OLD.kind,OLD.source_context,OLD.created_at,OLD.request_key,OLD.request_hash,OLD.topic_tag,OLD.material_id)
 IS DISTINCT FROM ROW(NEW.canonical_id,NEW.parent_id,NEW.kind,NEW.source_context,NEW.created_at,NEW.request_key,NEW.request_hash,NEW.topic_tag,NEW.material_id)
 THEN RAISE EXCEPTION 'discussion anchors are immutable'; END IF;
 IF OLD.edit_locked AND NOT NEW.edit_locked THEN RAISE EXCEPTION 'accepted reply content is permanently locked'; END IF;
 NEW.edit_locked:=OLD.edit_locked OR OLD.accepted OR NEW.accepted;
 IF ROW(OLD.body,OLD.source_links,OLD.content_version,OLD.edited_at)
 IS DISTINCT FROM ROW(NEW.body,NEW.source_links,NEW.content_version,NEW.edited_at) THEN
  IF OLD.edit_locked OR OLD.accepted OR NEW.accepted THEN RAISE EXCEPTION 'accepted reply content is permanently locked'; END IF;
  IF OLD.hidden OR OLD.before_fix OR NEW.hidden OR NEW.before_fix OR NOT NEW.needs_approval
   OR NEW.content_version<>OLD.content_version+1 OR NEW.edited_at IS DISTINCT FROM now()
   OR NOT EXISTS(SELECT 1 FROM post_revisions r WHERE r.post_id=OLD.id AND r.version=OLD.content_version
    AND r.body=OLD.body AND r.source_links=OLD.source_links)
   OR NOT EXISTS(SELECT 1 FROM post_revisions r WHERE r.post_id=NEW.id AND r.version=NEW.content_version
    AND r.body=NEW.body AND r.source_links=NEW.source_links AND r.created_at=NEW.edited_at AND r.actor_id=OLD.author_id)
  THEN RAISE EXCEPTION 'discussion content is immutable outside a recorded edit'; END IF;
 END IF;
 RETURN NEW;
END $$;
-- Only this function may append snapshots; the app cannot manufacture history.
CREATE FUNCTION community_edit_post(pid bigint,actor text,expected integer,new_body text,new_sources jsonb,retry_key text,retry_hash text)
RETURNS integer LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE p public.posts%ROWTYPE; old public.post_revisions%ROWTYPE;
BEGIN
 SELECT * INTO p FROM public.posts WHERE id=pid FOR UPDATE;
 IF NOT FOUND OR p.author_id<>actor OR p.hidden OR p.before_fix THEN RAISE EXCEPTION 'editable post unavailable'; END IF;
 SELECT * INTO old FROM public.post_revisions WHERE actor_id=actor AND request_key=retry_key;
 IF FOUND THEN
  IF old.post_id<>pid OR old.request_hash<>retry_hash THEN RAISE EXCEPTION 'edit request key conflict'; END IF;
  RETURN old.version;
 END IF;
 IF p.edit_locked OR p.accepted THEN RAISE EXCEPTION 'accepted reply content is permanently locked'; END IF;
 IF p.content_version<>expected THEN RAISE EXCEPTION 'post version changed'; END IF;
 IF char_length(new_body)<10 OR char_length(new_body)>5000 OR jsonb_typeof(new_sources)<>'array'
  OR jsonb_array_length(new_sources)>5 OR retry_key IS NULL OR char_length(retry_key) NOT BETWEEN 16 AND 100
  OR retry_hash IS NULL THEN RAISE EXCEPTION 'invalid edit'; END IF;
 IF p.body=new_body AND p.source_links=new_sources THEN RAISE EXCEPTION 'edit has no changes'; END IF;
 INSERT INTO public.post_revisions(post_id,version,body,source_links,actor_id,created_at)
 VALUES(pid,0,p.body,p.source_links,actor,p.created_at) ON CONFLICT(post_id,version) DO NOTHING;
 INSERT INTO public.post_revisions(post_id,version,body,source_links,actor_id,request_key,request_hash)
 VALUES(pid,p.content_version+1,new_body,new_sources,actor,retry_key,retry_hash);
 UPDATE public.posts SET body=new_body,source_links=new_sources,content_version=content_version+1,
 edited_at=now(),needs_approval=true WHERE id=pid;
 RETURN p.content_version+1;
END $$;
REVOKE ALL ON FUNCTION community_edit_post(bigint,text,integer,text,jsonb,text,text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION community_edit_post(bigint,text,integer,text,jsonb,text,text) TO mpsc;
COMMIT;
