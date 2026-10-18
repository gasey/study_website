-- Make parallel work safe to reason about.
--
-- Two streams run at once: the bank is edited locally (by hand and by
-- models), while the server accumulates attempts, reports and corrections.
-- sync-bank.sh already refuses to touch user data, so neither stream
-- destroys the other. What was missing is a RECORD — without it nobody can
-- answer "is the server running the bank I have in front of me?", and the
-- two drift silently, which is exactly the failure this project has hit
-- before on another codebase.
--
-- Two tables, both small:
--   sync_log      — one row per sync-bank.sh run, with the bank's checksum
--   bank_feedback — the server's proposals back to the local bank

BEGIN;

CREATE TABLE IF NOT EXISTS sync_log (
    id              BIGSERIAL PRIMARY KEY,
    -- sha256 of the bank JSON that produced this sync. The answer to
    -- "which version is live" is this column, not a guess from timestamps.
    bank_checksum   TEXT NOT NULL,
    bank_bytes      BIGINT,
    questions_in    INTEGER NOT NULL,
    appearances_new INTEGER NOT NULL DEFAULT 0,
    canonical_new   INTEGER NOT NULL DEFAULT 0,
    canonical_upd   INTEGER NOT NULL DEFAULT 0,
    -- Recorded so a sync can never be blamed for losing them.
    attempts_before INTEGER,
    attempts_after  INTEGER,
    ran_by          TEXT,
    started_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at     TIMESTAMPTZ,
    CONSTRAINT sync_attempts_not_lost CHECK (
        attempts_after IS NULL OR attempts_before IS NULL
        OR attempts_after >= attempts_before
    )
);
CREATE INDEX IF NOT EXISTS idx_sync_log_time ON sync_log(started_at DESC);

-- The reverse channel. The server never edits bank content directly
-- (DECISIONS #5) — it PROPOSES, and the proposal is exported, applied to
-- the local JSON, and comes back through the normal sync. That keeps one
-- authority for bank content while still letting work happen on both sides.
CREATE TABLE IF NOT EXISTS bank_feedback (
    id            BIGSERIAL PRIMARY KEY,
    canonical_id  TEXT NOT NULL REFERENCES canonical_questions(id),
    kind          TEXT NOT NULL CHECK (kind IN
                    ('wrong_key','typo_ocr','outdated','ambiguous','duplicate','subject')),
    -- What the server thinks it should become. Free-form because the fix
    -- differs by kind: a corrected key, a cleaned stem, a subject label.
    proposed      JSONB NOT NULL,
    note          TEXT,
    raised_by     TEXT,
    evidence      TEXT,                       -- paper + page, a URL, anything checkable
    status        TEXT NOT NULL DEFAULT 'open'
                    CHECK (status IN ('open','exported','applied','rejected')),
    -- Set when the fix has made the round trip and come back in a sync, so
    -- the same correction is not exported twice.
    exported_at   TIMESTAMPTZ,
    applied_at    TIMESTAMPTZ,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT feedback_exported_has_time CHECK (
        (status = 'open') OR (status = 'rejected') OR exported_at IS NOT NULL
    )
);
CREATE INDEX IF NOT EXISTS idx_feedback_open ON bank_feedback(kind, created_at)
    WHERE status = 'open';

-- Convenience: what the server currently believes it is running.
CREATE OR REPLACE VIEW v_sync_state AS
SELECT bank_checksum, questions_in, finished_at,
       (SELECT COUNT(*) FROM bank_feedback WHERE status = 'open') AS open_feedback
  FROM sync_log
 WHERE finished_at IS NOT NULL
 ORDER BY started_at DESC
 LIMIT 1;

COMMIT;
