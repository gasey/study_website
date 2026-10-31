BEGIN;
ALTER TABLE game_rooms ADD COLUMN selection_context jsonb;
ALTER TABLE game_rooms ADD COLUMN context_hash text;
ALTER TABLE game_rooms ADD CONSTRAINT game_context_pair CHECK((selection_context IS NULL)=(context_hash IS NULL));
CREATE INDEX game_queue_context ON game_rooms(context_hash,created_at) WHERE state='waiting' AND matchmaking;
ALTER TABLE game_members ADD COLUMN ready boolean NOT NULL DEFAULT false;
CREATE TABLE game_preferences(user_id text PRIMARY KEY REFERENCES users(id),selection jsonb NOT NULL,updated_at timestamptz NOT NULL DEFAULT now());
GRANT SELECT,INSERT,UPDATE ON game_preferences TO mpsc;
CREATE FUNCTION game_context_immutable() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN
 IF OLD.selection_context IS DISTINCT FROM NEW.selection_context OR OLD.context_hash IS DISTINCT FROM NEW.context_hash THEN
 RAISE EXCEPTION 'game selection context is immutable'; END IF; RETURN NEW; END $$;
CREATE TRIGGER game_context_fixed BEFORE UPDATE ON game_rooms FOR EACH ROW EXECUTE FUNCTION game_context_immutable();
COMMIT;
