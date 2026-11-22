-- Draft: bind the existing party engine to private Desk membership.
BEGIN;
ALTER TABLE game_rooms ADD COLUMN desk_id text REFERENCES study_desks(id);
ALTER TABLE game_rooms ADD CONSTRAINT desk_party_only CHECK (
 desk_id IS NULL OR (mode='party' AND capacity=4 AND NOT matchmaking
 AND join_code IS NULL AND cup_id IS NULL AND daily_id IS NULL
 AND selection_context IS NOT NULL AND context_hash IS NOT NULL
 AND (selection_context->>'desk_id') IS NOT DISTINCT FROM desk_id));
CREATE INDEX game_desk_recent ON game_rooms(desk_id,created_at DESC) WHERE desk_id IS NOT NULL;
CREATE FUNCTION desk_game_binding_immutable() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN
 IF OLD.desk_id IS DISTINCT FROM NEW.desk_id THEN
 RAISE EXCEPTION 'game Desk binding is immutable'; END IF; RETURN NEW; END $$;
CREATE TRIGGER desk_game_binding_fixed BEFORE UPDATE OF desk_id ON game_rooms
 FOR EACH ROW EXECUTE FUNCTION desk_game_binding_immutable();
COMMIT;
