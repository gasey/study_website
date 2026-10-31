BEGIN;
ALTER TABLE auth_sessions ADD COLUMN mfa_verified_at TIMESTAMPTZ;
CREATE TABLE account_mfa (
 user_id TEXT PRIMARY KEY REFERENCES users(id), secret_cipher TEXT,
 pending_cipher TEXT,pending_until TIMESTAMPTZ,enabled_at TIMESTAMPTZ,
 last_counter BIGINT NOT NULL DEFAULT -1,updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE mfa_recovery_codes (
 user_id TEXT NOT NULL REFERENCES users(id),code_hash TEXT NOT NULL,used_at TIMESTAMPTZ,
 created_at TIMESTAMPTZ NOT NULL DEFAULT now(),PRIMARY KEY(user_id,code_hash)
);
CREATE TABLE account_security_events (
 id BIGSERIAL PRIMARY KEY,user_id TEXT NOT NULL REFERENCES users(id),action TEXT NOT NULL,
 created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TRIGGER immutable_account_security_event BEFORE UPDATE OR DELETE ON account_security_events FOR EACH ROW EXECUTE FUNCTION review_immutable();
GRANT SELECT,INSERT,UPDATE ON account_mfa,mfa_recovery_codes TO mpsc;
GRANT SELECT,INSERT ON account_security_events TO mpsc;
GRANT USAGE,SELECT ON ALL SEQUENCES IN SCHEMA public TO mpsc;
COMMIT;
