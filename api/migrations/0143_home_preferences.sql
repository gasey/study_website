BEGIN;

CREATE TABLE IF NOT EXISTS user_home_preferences (
    user_id      TEXT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    prefs        JSONB NOT NULL DEFAULT '{}'::jsonb,
    onboarded_at TIMESTAMPTZ,
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

GRANT SELECT, INSERT, UPDATE, DELETE ON user_home_preferences TO mpsc;

COMMIT;
