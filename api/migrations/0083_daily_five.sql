-- Daily Five: one shared five-question set per IST day, drawn from the
-- non-technical core (gk_gs / english / everyday_math pillars). Deliberately
-- mirrors the weekly cup in 0043 -- game_dailies is game_cups, and
-- game_daily_entries is game_cup_entries -- so the room lifecycle, answer
-- submission, scoring and review paths are reused rather than duplicated.
BEGIN;

CREATE TABLE game_dailies(
  id TEXT PRIMARY KEY,                       -- IST calendar date, ISO yyyy-mm-dd
  opens_at TIMESTAMPTZ NOT NULL,
  closes_at TIMESTAMPTZ NOT NULL,
  questions JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK(closes_at>opens_at)
);

-- 0067 replaced the original 0043 constraint to add 'trail'; keep every
-- existing mode and add 'daily'.
ALTER TABLE game_rooms DROP CONSTRAINT game_rooms_mode_check;
ALTER TABLE game_rooms ADD CONSTRAINT game_rooms_mode_check
  CHECK(mode IN ('gauntlet','speed','duel','party','cup','trail','daily'));
ALTER TABLE game_rooms ADD COLUMN daily_id TEXT REFERENCES game_dailies(id);

-- PRIMARY KEY(daily_id,user_id) is what enforces one attempt per day; the
-- router's pre-check is a friendly error, this is the guarantee.
CREATE TABLE game_daily_entries(
  daily_id TEXT NOT NULL REFERENCES game_dailies(id),
  user_id TEXT NOT NULL REFERENCES users(id),
  room_id TEXT NOT NULL UNIQUE REFERENCES game_rooms(id),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY(daily_id,user_id)
);
-- Drives the per-user game streak and "your recent dailies".
CREATE INDEX game_daily_entries_user ON game_daily_entries(user_id,daily_id DESC);

-- District is optional. Learners without one still play and still rank on the
-- players board; they are simply absent from the district league.
ALTER TABLE reward_profiles ADD COLUMN district TEXT;
ALTER TABLE reward_profiles ADD CONSTRAINT reward_profiles_district_check
  CHECK(district IS NULL OR district IN (
    'Aizawl','Champhai','Hnahthial','Khawzawl','Kolasib','Lawngtlai',
    'Lunglei','Mamit','Saitual','Serchhip','Siaha'));
CREATE INDEX reward_profiles_district ON reward_profiles(district) WHERE district IS NOT NULL;

COMMIT;
