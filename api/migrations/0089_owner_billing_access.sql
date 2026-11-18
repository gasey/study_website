BEGIN;
CREATE TABLE billing_account_rates (
 user_id TEXT PRIMARY KEY REFERENCES users(id),
 amount_paise INTEGER NOT NULL CHECK(amount_paise IN (5000,10000)),
 updated_by TEXT NOT NULL REFERENCES users(id),updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE billing_access_grants (
 id BIGSERIAL PRIMARY KEY,user_id TEXT NOT NULL REFERENCES users(id),
 granted_by TEXT NOT NULL REFERENCES users(id),idempotency_key TEXT NOT NULL,
 days INTEGER NOT NULL CHECK(days BETWEEN 1 AND 3650),
 starts_at TIMESTAMPTZ NOT NULL,ends_at TIMESTAMPTZ NOT NULL,
 created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 UNIQUE(user_id,idempotency_key),CHECK(ends_at>starts_at)
);
CREATE INDEX billing_access_grants_user_end ON billing_access_grants(user_id,ends_at DESC);
CREATE TRIGGER immutable_billing_access_grant BEFORE UPDATE OR DELETE ON billing_access_grants FOR EACH ROW EXECUTE FUNCTION review_immutable();
CREATE OR REPLACE FUNCTION account_has_pro(uid TEXT) RETURNS BOOLEAN LANGUAGE sql STABLE AS $$
 SELECT EXISTS(SELECT 1 FROM users WHERE id=uid AND plan_code='pro' AND ((plan_status IN ('active','authenticated') AND (plan_ends_at IS NULL OR plan_ends_at>now())) OR (plan_status='trial' AND trial_ends_at>now()) OR plan_ends_at>now()))
 OR EXISTS(SELECT 1 FROM reward_redemptions WHERE user_id=uid AND starts_at<=now() AND ends_at>now())
 OR EXISTS(SELECT 1 FROM billing_access_grants WHERE user_id=uid AND starts_at<=now() AND ends_at>now());
$$;
GRANT SELECT,INSERT,UPDATE ON billing_account_rates TO mpsc;
GRANT SELECT,INSERT ON billing_access_grants TO mpsc;
GRANT USAGE,SELECT ON SEQUENCE billing_access_grants_id_seq TO mpsc;
COMMIT;
