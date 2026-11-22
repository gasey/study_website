-- Persistent participation endings must remain cheap to check and once-only.
-- Existing game choices, results, events and rewards are retained unchanged.
BEGIN;
CREATE UNIQUE INDEX game_audience_marker_once ON game_events(room_id,actor_id)
 WHERE action='audience_access_ended';
COMMIT;
