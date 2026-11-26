BEGIN;

CREATE TABLE IF NOT EXISTS block_puzzle_runs (
    id                  TEXT PRIMARY KEY,
    user_id             TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    mode                TEXT NOT NULL CHECK (mode IN ('endless', 'daily')),
    daily_date          DATE,
    subject_scope       TEXT NOT NULL DEFAULT 'all',
    score               INT NOT NULL DEFAULT 0 CHECK (score >= 0),
    lines_cleared       INT NOT NULL DEFAULT 0 CHECK (lines_cleared >= 0),
    pieces_placed       INT NOT NULL DEFAULT 0 CHECK (pieces_placed >= 0),
    questions_answered  INT NOT NULL DEFAULT 0 CHECK (questions_answered >= 0),
    questions_correct   INT NOT NULL DEFAULT 0 CHECK (questions_correct >= 0),
    best_streak         INT NOT NULL DEFAULT 0 CHECK (best_streak >= 0),
    max_combo           INT NOT NULL DEFAULT 1 CHECK (max_combo >= 1),
    clutch_saves_used   INT NOT NULL DEFAULT 0 CHECK (clutch_saves_used >= 0 AND clutch_saves_used <= 3),
    status              TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'finished')),
    xp_awarded          INT NOT NULL DEFAULT 0 CHECK (xp_awarded >= 0),
    started_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at         TIMESTAMPTZ,
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_block_runs_mode_score
    ON block_puzzle_runs (mode, score DESC, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_block_runs_user_mode
    ON block_puzzle_runs (user_id, mode, score DESC);

CREATE INDEX IF NOT EXISTS idx_block_runs_daily_score
    ON block_puzzle_runs (daily_date, score DESC)
    WHERE mode = 'daily';

GRANT SELECT, INSERT, UPDATE, DELETE ON block_puzzle_runs TO mpsc;

COMMIT;
