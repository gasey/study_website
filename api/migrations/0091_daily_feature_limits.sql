BEGIN;
-- Per-account IST-day allowances. Request keys make retries and pagination
-- reuse a previously admitted query without charging another use.
CREATE TABLE rate_limits (
    user_id TEXT NOT NULL REFERENCES users(id),
    action TEXT NOT NULL CHECK (length(action) BETWEEN 1 AND 100),
    ist_date DATE NOT NULL,
    request_keys TEXT[] NOT NULL DEFAULT '{}',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, action, ist_date),
    CHECK (cardinality(request_keys) <= 1000)
);
GRANT SELECT, INSERT, UPDATE ON rate_limits TO mpsc;
COMMIT;
