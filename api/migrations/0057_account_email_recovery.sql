BEGIN;
ALTER TABLE users ADD COLUMN email_verified_at timestamptz;
CREATE TABLE account_email_tokens (
 token_hash text PRIMARY KEY,user_id text NOT NULL REFERENCES users(id),
 purpose text NOT NULL CHECK(purpose IN ('verify','reset')),
 created_at timestamptz NOT NULL DEFAULT now(),expires_at timestamptz NOT NULL,consumed_at timestamptz
);
CREATE INDEX account_email_token_user ON account_email_tokens(user_id,purpose,created_at DESC);
CREATE TABLE account_mail_outbox (
 id bigserial PRIMARY KEY,user_id text NOT NULL REFERENCES users(id),purpose text NOT NULL,
 token_cipher text NOT NULL,created_at timestamptz NOT NULL DEFAULT now(),
 attempts integer NOT NULL DEFAULT 0,next_attempt_at timestamptz NOT NULL DEFAULT now(),sent_at timestamptz,
 last_error text
);
GRANT SELECT,INSERT,UPDATE ON account_email_tokens,account_mail_outbox TO mpsc;
GRANT USAGE,SELECT ON SEQUENCE account_mail_outbox_id_seq TO mpsc;
COMMIT;
