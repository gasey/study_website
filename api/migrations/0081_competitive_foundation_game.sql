BEGIN;

ALTER TABLE reward_profiles
  ADD COLUMN IF NOT EXISTS stream_cohort TEXT NOT NULL DEFAULT 'balanced-core'
    CHECK (stream_cohort IN ('arts-comfort','science-bridge','balanced-core','commerce-core','single-pillar')),
  ADD COLUMN IF NOT EXISTS current_streak_days INTEGER NOT NULL DEFAULT 0
    CHECK (current_streak_days >= 0),
  ADD COLUMN IF NOT EXISTS longest_streak_days INTEGER NOT NULL DEFAULT 0
    CHECK (longest_streak_days >= 0),
  ADD COLUMN IF NOT EXISTS last_active_ist_date DATE,
  ADD COLUMN IF NOT EXISTS streak_shields INTEGER NOT NULL DEFAULT 0
    CHECK (streak_shields BETWEEN 0 AND 2);

CREATE TABLE IF NOT EXISTS daily_quest_claims (
  id BIGSERIAL PRIMARY KEY,
  user_id TEXT NOT NULL REFERENCES users(id),
  ist_date DATE NOT NULL,
  quest_key TEXT NOT NULL CHECK (quest_key IN ('warmup_circuit','cross_stream_triad','mastery_closure','streak_day3','streak_day7')),
  xp_awarded INTEGER NOT NULL DEFAULT 0 CHECK (xp_awarded >= 0),
  points_awarded INTEGER NOT NULL DEFAULT 0 CHECK (points_awarded >= 0),
  ledger_id BIGINT NOT NULL REFERENCES reward_ledger(id),
  claimed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (user_id, ist_date, quest_key)
);

CREATE INDEX IF NOT EXISTS daily_quest_claims_user_date
  ON daily_quest_claims (user_id, ist_date DESC);

CREATE TRIGGER immutable_daily_quest_claims
  BEFORE UPDATE OR DELETE ON daily_quest_claims
  FOR EACH ROW EXECUTE FUNCTION review_immutable();

GRANT SELECT, INSERT ON daily_quest_claims TO mpsc;
GRANT USAGE, SELECT ON SEQUENCE daily_quest_claims_id_seq TO mpsc;

ALTER TABLE game_members
  ADD COLUMN IF NOT EXISTS pace_bonus INTEGER NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS streak_bonus INTEGER NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS courage_bonus INTEGER NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS best_streak INTEGER NOT NULL DEFAULT 0;

CREATE INDEX IF NOT EXISTS game_rooms_competitive_finished
  ON game_rooms (mode, finished_at DESC)
  WHERE state = 'finished';

COMMIT;
