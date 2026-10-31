-- Efficient date-range reads for the private per-user study progress view.
BEGIN;
CREATE INDEX IF NOT EXISTS idx_attempts_user_at ON attempts(user_id, at DESC);
COMMIT;
