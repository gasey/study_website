-- Keep the attempt history canonical and shared, while retaining where a
-- learner studied and making in-flight timed papers resume after refresh.
BEGIN;

ALTER TABLE attempts
    ADD COLUMN IF NOT EXISTS section_path TEXT;

ALTER TABLE mock_sessions
    ADD COLUMN IF NOT EXISTS current_position INTEGER NOT NULL DEFAULT 0
        CHECK (current_position >= 0);

CREATE TABLE IF NOT EXISTS mock_session_answers (
    mock_id       TEXT NOT NULL REFERENCES mock_sessions(id) ON DELETE CASCADE,
    question_id   TEXT NOT NULL REFERENCES canonical_questions(id),
    chosen_index  INTEGER CHECK (chosen_index IS NULL OR chosen_index >= 0),
    marked        BOOLEAN NOT NULL DEFAULT false,
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (mock_id, question_id)
);

CREATE INDEX IF NOT EXISTS idx_attempt_user_collection_section_time
    ON attempts(user_id,collection_id,section_path,at DESC)
    WHERE collection_id IS NOT NULL AND section_path IS NOT NULL;

COMMIT;
