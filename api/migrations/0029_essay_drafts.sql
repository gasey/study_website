-- One private draft per learner and canonical essay prompt. Drafts have no
-- automatic marks or public visibility; the learner owns the writing.
BEGIN;

CREATE TABLE IF NOT EXISTS essay_drafts (
    user_id       TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    canonical_id  TEXT NOT NULL REFERENCES canonical_questions(id) ON DELETE CASCADE,
    body          TEXT NOT NULL DEFAULT '' CHECK (length(body) <= 30000),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, canonical_id)
);

CREATE INDEX IF NOT EXISTS idx_essay_drafts_user_recent
    ON essay_drafts(user_id, updated_at DESC);

COMMIT;
