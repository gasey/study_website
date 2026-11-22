BEGIN;
-- Consent is prospective. No existing account is subscribed by this migration.
CREATE TABLE review_digest_preferences (
 user_id text PRIMARY KEY REFERENCES users(id), enabled boolean NOT NULL DEFAULT false,
 version integer NOT NULL DEFAULT 0 CHECK(version>=0),
 token_hash text UNIQUE, token_cipher text NOT NULL DEFAULT '',email_hash text,
 last_checked_day date, updated_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 CHECK(NOT enabled OR (token_hash IS NOT NULL AND token_cipher<>'' AND email_hash IS NOT NULL))
);
CREATE INDEX review_digest_candidates ON review_digest_preferences(last_checked_day,user_id) WHERE enabled;
CREATE TABLE review_digest_outbox (
 id bigserial PRIMARY KEY,user_id text NOT NULL REFERENCES users(id),day date NOT NULL,
 consent_version integer NOT NULL,created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 attempts integer NOT NULL DEFAULT 0 CHECK(attempts BETWEEN 0 AND 5),
 next_attempt_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 state text NOT NULL DEFAULT 'pending' CHECK(state IN ('pending','sent','cancelled')),
 sent_at timestamptz,last_error text,
 UNIQUE(user_id,day)
);
CREATE INDEX review_digest_pending ON review_digest_outbox(next_attempt_at,id) WHERE state='pending';
-- Separate anonymous ledger, counted under the same provider-wide advisory lock.
-- No FK: closing an account removes its outbox, never consumed capacity receipts.
CREATE TABLE review_digest_deliveries (
 id bigserial PRIMARY KEY,outbox_id bigint NOT NULL,attempt integer NOT NULL CHECK(attempt BETWEEN 1 AND 5),
 reserved_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 state text NOT NULL DEFAULT 'reserved' CHECK(state IN ('reserved','sent','failed','uncertain','cancelled')),
 finished_at timestamptz,error_type text,UNIQUE(outbox_id,attempt),
 CHECK((state='reserved')=(finished_at IS NULL))
);
CREATE INDEX review_digest_budget ON review_digest_deliveries(reserved_at);
CREATE TRIGGER review_digest_delivery_frozen BEFORE UPDATE OR DELETE ON review_digest_deliveries
 FOR EACH ROW EXECUTE FUNCTION account_mail_delivery_frozen();
GRANT SELECT,INSERT,UPDATE,DELETE ON review_digest_preferences,review_digest_outbox TO mpsc;
GRANT SELECT,INSERT,UPDATE ON review_digest_deliveries TO mpsc;
GRANT USAGE,SELECT ON SEQUENCE review_digest_outbox_id_seq,review_digest_deliveries_id_seq TO mpsc;
COMMIT;
