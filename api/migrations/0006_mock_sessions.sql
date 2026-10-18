-- Timed mocks.
--
-- The security property that matters: **the clock belongs to the server**.
-- The client counts down for display only. `started_at` is recorded here
-- when the mock begins, and elapsed time is computed here on submit. A
-- client that lies about how long it took changes nothing.
--
-- The question set is frozen into `question_ids` at start. Three reasons:
-- resume works, a re-sync of the bank cannot change a paper mid-attempt,
-- and the order shown is the order scored.

BEGIN;

CREATE TABLE IF NOT EXISTS mock_sessions (
    id                TEXT PRIMARY KEY,
    user_id           TEXT NOT NULL REFERENCES users(id),
    collection_id     TEXT NOT NULL REFERENCES collections(id),
    section_path      TEXT,

    -- Frozen at start, in display order. Not a filter re-evaluated later.
    question_ids      TEXT[] NOT NULL,
    duration_seconds  INTEGER NOT NULL CHECK (duration_seconds BETWEEN 60 AND 4 * 3600),

    -- Scoring rules are stored per session, not read from config at submit
    -- time, so a rule change can never silently re-score a finished mock.
    marks_correct     NUMERIC NOT NULL DEFAULT 1,
    marks_wrong       NUMERIC NOT NULL DEFAULT 0,   -- negative marking: set > 0 to deduct

    started_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    submitted_at      TIMESTAMPTZ,
    elapsed_seconds   INTEGER,
    --: true when the submission arrived after the allowed window. Recorded
    --: rather than rejected: a slow network should not destroy an attempt,
    --: but the result must say it was late.
    late              BOOLEAN NOT NULL DEFAULT false,

    n_correct         INTEGER,
    n_wrong           INTEGER,
    n_skipped         INTEGER,
    score             NUMERIC,

    CONSTRAINT mock_not_empty CHECK (cardinality(question_ids) > 0),
    -- A submitted session must carry a full result; an open one must not.
    CONSTRAINT mock_result_complete CHECK (
        (submitted_at IS NULL
         AND elapsed_seconds IS NULL AND n_correct IS NULL AND score IS NULL)
        OR
        (submitted_at IS NOT NULL
         AND elapsed_seconds IS NOT NULL AND n_correct IS NOT NULL AND score IS NOT NULL)
    )
);

CREATE INDEX IF NOT EXISTS idx_mock_user ON mock_sessions(user_id, started_at DESC);
-- At most one mock open per user: finishing or abandoning is required before
-- starting another, which also makes "resume" unambiguous.
CREATE UNIQUE INDEX IF NOT EXISTS idx_mock_one_open
    ON mock_sessions(user_id) WHERE submitted_at IS NULL;

-- Answers given inside a mock. attempts already stores chosen_text for
-- re-scoring; this ties each one to its session and position so a paper can
-- be reviewed question by question afterwards.
ALTER TABLE attempts
    ADD COLUMN IF NOT EXISTS mock_id  TEXT REFERENCES mock_sessions(id) ON DELETE CASCADE,
    ADD COLUMN IF NOT EXISTS position INTEGER;
CREATE INDEX IF NOT EXISTS idx_attempts_mock ON attempts(mock_id, position);

COMMIT;
