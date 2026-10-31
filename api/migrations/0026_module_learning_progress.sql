-- Persist short guided-lesson progress separately from answer attempts. These
-- items are conceptual checks, not canonical bank questions or scored answers.
BEGIN;

CREATE TABLE IF NOT EXISTS module_learning_progress (
    user_id    TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    module_id  TEXT NOT NULL CHECK (module_id ~ '^[a-z0-9][a-z0-9-]{1,39}$'),
    item_id    TEXT NOT NULL CHECK (item_id ~ '^[a-z0-9][a-z0-9-]{1,79}$'),
    visited    BOOLEAN NOT NULL DEFAULT true,
    correct    BOOLEAN,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id,module_id,item_id)
);

CREATE INDEX IF NOT EXISTS idx_module_learning_progress_recent
    ON module_learning_progress(user_id,updated_at DESC);

COMMIT;
