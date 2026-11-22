BEGIN;
-- Local launch preparation. No age or consent is inferred for existing users.
CREATE TABLE account_audience (
 user_id text PRIMARY KEY REFERENCES users(id),
 category text NOT NULL CHECK(category IN ('adult','under18')),
 version integer NOT NULL DEFAULT 1 CHECK(version>0),
 declared_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
CREATE TABLE audience_browser_flows (
 token_hash text PRIMARY KEY CHECK(length(token_hash)=64),
 category text NOT NULL CHECK(category IN ('adult','under18')),
 expires_at timestamptz NOT NULL DEFAULT now()+interval '1 day',
 created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX audience_browser_expiry ON audience_browser_flows(expires_at);
CREATE TABLE privacy_requests (
 id text PRIMARY KEY,
 user_id text NOT NULL REFERENCES users(id),
 kind text NOT NULL CHECK(kind IN ('access','correction','erasure','guardian')),
 request_key text NOT NULL CHECK(length(request_key) BETWEEN 16 AND 80),
 state text NOT NULL DEFAULT 'received' CHECK(state IN ('received','in_review','completed','declined','withdrawn')),
 version integer NOT NULL DEFAULT 1 CHECK(version>0),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 updated_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 UNIQUE(user_id,request_key)
);
-- No free-text personal data, ID uploads, email copies or child identity here.
CREATE TABLE privacy_request_events (
 id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 request_id text NOT NULL REFERENCES privacy_requests(id),
 actor_id text NOT NULL REFERENCES users(id),
 state text NOT NULL CHECK(state IN ('received','in_review','completed','declined','withdrawn')),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
CREATE TRIGGER immutable_privacy_request_event BEFORE UPDATE OR DELETE ON privacy_request_events
 FOR EACH ROW EXECUTE FUNCTION review_immutable();
REVOKE ALL ON account_audience,audience_browser_flows,privacy_requests,privacy_request_events FROM mpsc;
GRANT SELECT,INSERT,UPDATE ON account_audience,privacy_requests TO mpsc;
GRANT SELECT,INSERT,DELETE ON audience_browser_flows TO mpsc;
GRANT SELECT,INSERT ON privacy_request_events TO mpsc;
GRANT USAGE,SELECT ON SEQUENCE privacy_request_events_id_seq TO mpsc;
COMMIT;
