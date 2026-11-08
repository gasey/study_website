BEGIN;
ALTER TABLE game_rooms DROP CONSTRAINT game_rooms_mode_check;
ALTER TABLE game_rooms ADD CONSTRAINT game_rooms_mode_check CHECK(mode IN ('gauntlet','speed','duel','party','cup','trail'));
ALTER TABLE game_rooms ADD COLUMN trail_phase text NOT NULL DEFAULT 'ready' CHECK(trail_phase IN ('ready','question','feedback'));
ALTER TABLE game_rooms ADD COLUMN trail_boost_position integer;
CREATE TABLE topic_trail_packs(
 id text PRIMARY KEY,title text NOT NULL,collection_id text NOT NULL REFERENCES collections(id),
 taxonomy_id text NOT NULL REFERENCES review_taxonomy(id),active boolean NOT NULL DEFAULT true,
 version integer NOT NULL DEFAULT 1,created_by text NOT NULL REFERENCES users(id),updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE topic_trail_pack_history(id bigserial PRIMARY KEY,pack_id text NOT NULL REFERENCES topic_trail_packs(id),actor_id text NOT NULL REFERENCES users(id),payload jsonb NOT NULL,reason text NOT NULL,created_at timestamptz NOT NULL DEFAULT now());
CREATE TRIGGER topic_trail_pack_history_immutable BEFORE UPDATE OR DELETE ON topic_trail_pack_history FOR EACH ROW EXECUTE FUNCTION review_immutable();
GRANT SELECT,INSERT,UPDATE ON topic_trail_packs TO mpsc;
GRANT SELECT,INSERT ON topic_trail_pack_history TO mpsc;
GRANT USAGE,SELECT ON SEQUENCE topic_trail_pack_history_id_seq TO mpsc;
COMMIT;
