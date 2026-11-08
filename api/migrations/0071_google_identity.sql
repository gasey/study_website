BEGIN;
CREATE TABLE google_identities (
 subject text PRIMARY KEY,
 user_id text NOT NULL UNIQUE REFERENCES users(id),
 created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE google_auth_flows (
 token_hash text PRIMARY KEY,
 stage text NOT NULL CHECK(stage IN ('authorize','complete')),
 verifier text,
 nonce text,
 subject text,
 email text,
 link_user_id text REFERENCES users(id),
 session_hash text,
 expires_at timestamptz NOT NULL DEFAULT now()+interval '10 minutes'
);
CREATE INDEX google_auth_flow_expiry ON google_auth_flows(expires_at);
GRANT SELECT,INSERT ON google_identities TO mpsc;
GRANT SELECT,INSERT,DELETE ON google_auth_flows TO mpsc;
COMMIT;
