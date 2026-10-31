BEGIN;
-- Never bind these credentials to a caller-supplied legacy device UUID.
CREATE TABLE guest_credentials (
 token_hash text PRIMARY KEY,
 user_id text NOT NULL UNIQUE REFERENCES users(id),
 created_at timestamptz NOT NULL DEFAULT now(),
 expires_at timestamptz NOT NULL DEFAULT now()+interval '180 days',
 adopted_by text REFERENCES users(id),adopted_at timestamptz,
 CHECK((adopted_by IS NULL)=(adopted_at IS NULL))
);
CREATE TABLE guest_transfer_receipts (
 guest_id text PRIMARY KEY REFERENCES users(id),account_id text NOT NULL REFERENCES users(id),
 counts jsonb NOT NULL,created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TRIGGER immutable_guest_transfer BEFORE UPDATE OR DELETE ON guest_transfer_receipts
 FOR EACH ROW EXECUTE FUNCTION review_immutable();
ALTER TABLE account_security_events ADD COLUMN detail jsonb NOT NULL DEFAULT '{}'::jsonb;
ALTER TABLE auth_sessions ADD COLUMN public_id text NOT NULL DEFAULT md5(random()::text || clock_timestamp()::text);
CREATE UNIQUE INDEX auth_session_public_id ON auth_sessions(public_id);
GRANT SELECT,INSERT,UPDATE ON guest_credentials TO mpsc;
GRANT SELECT,INSERT ON guest_transfer_receipts TO mpsc;
COMMIT;
