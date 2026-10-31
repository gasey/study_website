BEGIN;
ALTER TABLE users ADD COLUMN avatar JSONB;
ALTER TABLE users ADD COLUMN avatar_version INTEGER NOT NULL DEFAULT 0 CHECK(avatar_version>=0);
ALTER TABLE users ADD CONSTRAINT avatar_object CHECK(avatar IS NULL OR (jsonb_typeof(avatar)='object' AND octet_length(avatar::text)<=2048));
CREATE TABLE user_avatar_items (
 user_id TEXT NOT NULL REFERENCES users(id),item_id TEXT NOT NULL,
 level_at_claim INTEGER NOT NULL CHECK(level_at_claim>=1),created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 PRIMARY KEY(user_id,item_id)
);
CREATE TABLE avatar_events (
 id BIGSERIAL PRIMARY KEY,user_id TEXT NOT NULL REFERENCES users(id),
 action TEXT NOT NULL CHECK(action IN ('saved','reset')),version INTEGER NOT NULL,
 detail JSONB NOT NULL DEFAULT '{}',created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 UNIQUE(user_id,version)
);
CREATE FUNCTION avatar_events_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'avatar events are append-only'; END $$;
CREATE TRIGGER avatar_events_immutable BEFORE UPDATE OR DELETE ON avatar_events FOR EACH ROW EXECUTE FUNCTION avatar_events_immutable();
GRANT SELECT,INSERT ON user_avatar_items,avatar_events TO mpsc;
GRANT USAGE,SELECT ON SEQUENCE avatar_events_id_seq TO mpsc;
COMMIT;
