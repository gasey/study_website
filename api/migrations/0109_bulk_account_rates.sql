BEGIN;
CREATE TABLE billing_rate_batches (
 id text PRIMARY KEY,actor_id text NOT NULL REFERENCES users(id),request_key text NOT NULL,
 request_hash text NOT NULL,result jsonb NOT NULL,created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(actor_id,request_key)
);
CREATE TRIGGER immutable_rate_batch BEFORE UPDATE OR DELETE ON billing_rate_batches FOR EACH ROW EXECUTE FUNCTION review_immutable();
CREATE TABLE billing_rate_allowlist (
 email_normalized text PRIMARY KEY CHECK(email_normalized=lower(btrim(email_normalized))),
 amount_paise integer NOT NULL DEFAULT 5000 CHECK(amount_paise=5000),
 added_by text NOT NULL REFERENCES users(id),note text NOT NULL CHECK(length(note) BETWEEN 1 AND 240),
 created_at timestamptz NOT NULL DEFAULT now(),revoked_at timestamptz,
 applied_user_id text REFERENCES users(id),applied_at timestamptz,
 version integer NOT NULL DEFAULT 1 CHECK(version>0),
 CHECK((applied_user_id IS NULL)=(applied_at IS NULL))
);
CREATE FUNCTION rate_allowlist_history() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF TG_OP='DELETE' THEN RAISE EXCEPTION 'Rate allowlist history is retained'; END IF;
 IF (NEW.email_normalized,NEW.amount_paise,NEW.added_by,NEW.note,NEW.created_at) IS DISTINCT FROM
    (OLD.email_normalized,OLD.amount_paise,OLD.added_by,OLD.note,OLD.created_at)
 OR (OLD.applied_user_id IS NOT NULL AND (NEW.applied_user_id,NEW.applied_at) IS DISTINCT FROM (OLD.applied_user_id,OLD.applied_at))
 OR NEW.version<>OLD.version+1 THEN RAISE EXCEPTION 'Rate allowlist history is immutable'; END IF;
 RETURN NEW;
END; $$;
CREATE TRIGGER rate_allowlist_history BEFORE UPDATE OR DELETE ON billing_rate_allowlist FOR EACH ROW EXECUTE FUNCTION rate_allowlist_history();
CREATE TABLE billing_rate_codes (
 code text PRIMARY KEY,amount_paise integer NOT NULL DEFAULT 5000 CHECK(amount_paise=5000),
 max_uses integer NOT NULL DEFAULT 100 CHECK(max_uses BETWEEN 1 AND 1000),
 uses integer NOT NULL DEFAULT 0 CHECK(uses>=0 AND uses<=max_uses),
 expires_at timestamptz NOT NULL,created_by text NOT NULL REFERENCES users(id),
 note text NOT NULL CHECK(length(note) BETWEEN 1 AND 240),created_at timestamptz NOT NULL DEFAULT now(),
 revoked_at timestamptz,version integer NOT NULL DEFAULT 1,
 request_key text NOT NULL,request_hash text NOT NULL,UNIQUE(created_by,request_key),
 CHECK(expires_at>created_at AND expires_at<=created_at+interval '90 days')
);
CREATE TABLE billing_rate_redemptions (
 code text NOT NULL REFERENCES billing_rate_codes(code),user_id text NOT NULL REFERENCES users(id),
 amount_paise integer NOT NULL DEFAULT 5000 CHECK(amount_paise=5000),created_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(code,user_id)
);
CREATE TRIGGER immutable_rate_redemption BEFORE UPDATE OR DELETE ON billing_rate_redemptions FOR EACH ROW EXECUTE FUNCTION review_immutable();
CREATE FUNCTION rate_code_history() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF TG_OP='DELETE' THEN RAISE EXCEPTION 'Group code history is retained'; END IF;
 IF (NEW.code,NEW.amount_paise,NEW.max_uses,NEW.expires_at,NEW.created_by,NEW.note,NEW.created_at,NEW.request_key,NEW.request_hash)
 IS DISTINCT FROM (OLD.code,OLD.amount_paise,OLD.max_uses,OLD.expires_at,OLD.created_by,OLD.note,OLD.created_at,OLD.request_key,OLD.request_hash)
 OR NEW.version<>OLD.version+1 OR (OLD.revoked_at IS NOT NULL AND NEW.revoked_at IS DISTINCT FROM OLD.revoked_at)
 OR (NEW.uses<>OLD.uses AND (NEW.uses<>OLD.uses+1 OR pg_trigger_depth()<2))
 THEN RAISE EXCEPTION 'Group code history is immutable'; END IF;
 RETURN NEW;
END; $$;
CREATE TRIGGER rate_code_history BEFORE UPDATE OR DELETE ON billing_rate_codes FOR EACH ROW EXECUTE FUNCTION rate_code_history();
CREATE FUNCTION count_rate_redemption() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 UPDATE billing_rate_codes SET uses=uses+1,version=version+1
 WHERE code=NEW.code AND revoked_at IS NULL AND expires_at>now() AND uses<max_uses;
 IF NOT FOUND THEN RAISE EXCEPTION 'Group code is unavailable'; END IF;
 RETURN NEW;
END; $$;
CREATE TRIGGER count_rate_redemption AFTER INSERT ON billing_rate_redemptions FOR EACH ROW EXECUTE FUNCTION count_rate_redemption();
GRANT SELECT,INSERT ON billing_rate_batches,billing_rate_redemptions TO mpsc;
GRANT SELECT,INSERT,UPDATE ON billing_rate_allowlist,billing_rate_codes TO mpsc;
COMMIT;
