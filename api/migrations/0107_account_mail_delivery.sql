BEGIN;
-- Durable conservative send reservations survive process loss and account cleanup.
-- No address, token, body or user identifier is retained in this capacity ledger.
-- outbox_id intentionally has no FK: account closure deletes pending ciphertext.
CREATE TABLE account_mail_deliveries (
 id bigserial PRIMARY KEY,outbox_id bigint NOT NULL,attempt integer NOT NULL CHECK(attempt BETWEEN 1 AND 5),
 reserved_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 state text NOT NULL DEFAULT 'reserved' CHECK(state IN ('reserved','sent','failed','uncertain','cancelled')),
 finished_at timestamptz,error_type text,
 UNIQUE(outbox_id,attempt),
 CHECK((state='reserved')=(finished_at IS NULL))
);
CREATE INDEX account_mail_delivery_budget ON account_mail_deliveries(reserved_at);
CREATE INDEX account_mail_outbox_pending ON account_mail_outbox(next_attempt_at,id) WHERE sent_at IS NULL;
CREATE FUNCTION account_mail_delivery_frozen() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF TG_OP='DELETE' OR OLD.state<>'reserved' OR
 ROW(OLD.id,OLD.outbox_id,OLD.attempt,OLD.reserved_at) IS DISTINCT FROM ROW(NEW.id,NEW.outbox_id,NEW.attempt,NEW.reserved_at)
 THEN RAISE EXCEPTION 'Mail capacity reservations and final receipts are immutable'; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER account_mail_delivery_frozen BEFORE UPDATE OR DELETE ON account_mail_deliveries
 FOR EACH ROW EXECUTE FUNCTION account_mail_delivery_frozen();
GRANT SELECT,INSERT,UPDATE ON account_mail_deliveries TO mpsc;
GRANT USAGE,SELECT ON SEQUENCE account_mail_deliveries_id_seq TO mpsc;
COMMIT;
