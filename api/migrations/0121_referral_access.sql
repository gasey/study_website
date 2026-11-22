BEGIN;
-- Access only. Existing owner grants keep their source and all original values.
ALTER TABLE billing_access_grants ADD COLUMN source text NOT NULL DEFAULT 'owner';
ALTER TABLE billing_access_grants ALTER COLUMN granted_by DROP NOT NULL;
ALTER TABLE billing_access_grants ADD CONSTRAINT billing_access_source CHECK(
 (source='owner' AND granted_by IS NOT NULL) OR
 (source='referral' AND granted_by IS NULL AND days=7 AND ends_at=starts_at+interval '7 days'));
ALTER TABLE google_auth_flows ADD COLUMN referral_code text;
CREATE TABLE referral_codes (
 user_id text PRIMARY KEY REFERENCES users(id),code text NOT NULL UNIQUE CHECK(code ~ '^[A-Za-z0-9_-]{24}$'),
 enabled boolean NOT NULL DEFAULT true,version integer NOT NULL DEFAULT 1 CHECK(version>0),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
CREATE TABLE referral_claims (
 referred_id text PRIMARY KEY REFERENCES users(id),referrer_id text NOT NULL REFERENCES users(id),
 invite_code text NOT NULL,invite_version integer NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now(),last_checked_at timestamptz,
 CHECK(referred_id<>referrer_id)
);
CREATE INDEX referral_claim_sweep ON referral_claims(last_checked_at,created_at,referred_id);
CREATE FUNCTION referral_signup_only() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF TG_OP='INSERT' THEN
  NEW.created_at=transaction_timestamp();
  IF NOT EXISTS(SELECT 1 FROM users u WHERE u.id=NEW.referred_id AND u.created_at=transaction_timestamp())
  THEN RAISE EXCEPTION 'A referral attaches only in the new account signup transaction'; END IF;
  IF NOT EXISTS(SELECT 1 FROM referral_codes c JOIN users u ON u.id=c.user_id
   WHERE c.user_id=NEW.referrer_id AND c.code=NEW.invite_code AND c.version=NEW.invite_version
   AND c.enabled AND u.email_verified_at IS NOT NULL AND u.email IS NOT NULL AND u.closed_at IS NULL)
  THEN RAISE EXCEPTION 'Referral invitation is unavailable'; END IF;
 ELSE
  IF ROW(OLD.referred_id,OLD.referrer_id,OLD.invite_code,OLD.invite_version,OLD.created_at)
   IS DISTINCT FROM ROW(NEW.referred_id,NEW.referrer_id,NEW.invite_code,NEW.invite_version,NEW.created_at)
  THEN RAISE EXCEPTION 'Referral signup attribution is immutable'; END IF;
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER referral_signup_only BEFORE INSERT OR UPDATE ON referral_claims
 FOR EACH ROW EXECUTE FUNCTION referral_signup_only();
CREATE TABLE referral_decisions (
 referred_id text PRIMARY KEY REFERENCES referral_claims(referred_id),
 referrer_id text NOT NULL REFERENCES users(id),
 state text NOT NULL CHECK(state IN ('credited','capped','closed')),
 decided_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 attempt_ids bigint[] NOT NULL DEFAULT '{}',
 referrer_grant_id bigint UNIQUE REFERENCES billing_access_grants(id),
 referred_grant_id bigint UNIQUE REFERENCES billing_access_grants(id),
 CHECK(referred_id<>referrer_id),
 CHECK((state='credited' AND cardinality(attempt_ids)=10 AND referrer_grant_id IS NOT NULL AND referred_grant_id IS NOT NULL)
   OR (state<>'credited' AND referrer_grant_id IS NULL AND referred_grant_id IS NULL))
);
CREATE INDEX referral_yearly_cap ON referral_decisions(referrer_id,decided_at) WHERE state='credited';
CREATE FUNCTION referral_decision_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 NEW.decided_at=clock_timestamp();
 IF NOT EXISTS(SELECT 1 FROM referral_claims c WHERE c.referred_id=NEW.referred_id AND c.referrer_id=NEW.referrer_id)
 THEN RAISE EXCEPTION 'Referral decision attribution mismatch'; END IF;
 IF NEW.state='credited' THEN
  PERFORM pg_advisory_xact_lock(hashtextextended('referral-cap:'||NEW.referrer_id,0));
  IF (SELECT count(*) FROM referral_decisions WHERE referrer_id=NEW.referrer_id AND state='credited'
      AND decided_at>NEW.decided_at-interval '1 year')>=5
  THEN RAISE EXCEPTION 'Referral yearly cap reached'; END IF;
  IF NOT EXISTS(SELECT 1 FROM billing_access_grants WHERE id=NEW.referrer_grant_id AND user_id=NEW.referrer_id
    AND source='referral' AND granted_by IS NULL AND days=7 AND idempotency_key='referral:'||NEW.referred_id||':referrer')
   OR NOT EXISTS(SELECT 1 FROM billing_access_grants WHERE id=NEW.referred_grant_id AND user_id=NEW.referred_id
    AND source='referral' AND granted_by IS NULL AND days=7 AND idempotency_key='referral:'||NEW.referred_id||':referred')
  THEN RAISE EXCEPTION 'Referral requires two matching access grants'; END IF;
  IF (SELECT count(DISTINCT a.id) FROM attempts a WHERE a.id=ANY(NEW.attempt_ids) AND a.user_id=NEW.referred_id)<>10
  THEN RAISE EXCEPTION 'Referral qualification receipt mismatch'; END IF;
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER referral_decision_guard BEFORE INSERT ON referral_decisions FOR EACH ROW EXECUTE FUNCTION referral_decision_guard();
CREATE TRIGGER immutable_referral_decision BEFORE UPDATE OR DELETE ON referral_decisions FOR EACH ROW EXECUTE FUNCTION review_immutable();
-- Oracle's legacy default ACL grants broad CRUD on new tables. Explicitly
-- remove inherited table privileges before adding this feature's narrow set.
REVOKE ALL ON referral_codes,referral_claims,referral_decisions FROM mpsc;
GRANT SELECT,INSERT,UPDATE ON referral_codes,referral_claims TO mpsc;
GRANT SELECT,INSERT ON referral_decisions TO mpsc;
COMMIT;
