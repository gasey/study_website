-- Learner progress is still keyed to canonical questions, but now carries
-- optional module/paper scope so shared questions can appear in several
-- exam dashboards without duplicating the question itself.
BEGIN;

ALTER TABLE attempts
    ADD COLUMN IF NOT EXISTS collection_id TEXT REFERENCES collections(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS paper_id TEXT REFERENCES papers(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_attempt_user_collection_time
    ON attempts(user_id,collection_id,at DESC) WHERE collection_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_attempt_user_collection_question
    ON attempts(user_id,collection_id,canonical_id,at DESC)
    WHERE collection_id IS NOT NULL AND canonical_id IS NOT NULL;

COMMIT;
