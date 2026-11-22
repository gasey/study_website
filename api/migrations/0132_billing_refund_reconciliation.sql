BEGIN;

ALTER TABLE billing_payments
  ADD COLUMN IF NOT EXISTS amount_refunded_paise INTEGER NOT NULL DEFAULT 0
    CHECK (amount_refunded_paise >= 0),
  ADD COLUMN IF NOT EXISTS refund_status TEXT
    CHECK (refund_status IS NULL OR refund_status IN ('partial','full')),
  ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();

ALTER TABLE billing_subscriptions
  ADD COLUMN IF NOT EXISTS access_ended_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS access_end_reason TEXT
    CHECK (access_end_reason IS NULL OR access_end_reason='full_refund');

CREATE TABLE IF NOT EXISTS billing_refunds (
  razorpay_refund_id TEXT PRIMARY KEY,
  razorpay_payment_id TEXT NOT NULL REFERENCES billing_payments(razorpay_payment_id) ON DELETE RESTRICT,
  amount_paise INTEGER NOT NULL CHECK (amount_paise > 0),
  currency TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('pending','processed','failed')),
  provider_created_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_billing_refunds_payment
  ON billing_refunds(razorpay_payment_id,provider_created_at DESC);

GRANT SELECT,INSERT ON billing_payments TO mpsc;
REVOKE UPDATE ON billing_payments FROM mpsc;
GRANT UPDATE(status,amount_refunded_paise,refund_status,updated_at) ON billing_payments TO mpsc;
GRANT SELECT,INSERT ON billing_webhook_events TO mpsc;
GRANT UPDATE(status,current_start,current_end,updated_at,access_ended_at,access_end_reason) ON billing_subscriptions TO mpsc;
GRANT SELECT,INSERT ON billing_refunds TO mpsc;
GRANT UPDATE(amount_paise,currency,status,provider_created_at,updated_at) ON billing_refunds TO mpsc;

COMMIT;
