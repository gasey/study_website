BEGIN;
CREATE TABLE practice_request_receipts (
 user_id text NOT NULL REFERENCES users(id),request_key text NOT NULL,
 request_hash text NOT NULL,attempt_id bigint NOT NULL REFERENCES attempts(id),
 response jsonb NOT NULL,created_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(user_id,request_key)
);
CREATE TRIGGER immutable_practice_receipt BEFORE UPDATE OR DELETE ON practice_request_receipts
 FOR EACH ROW EXECUTE FUNCTION review_immutable();
GRANT SELECT,INSERT ON practice_request_receipts TO mpsc;
COMMIT;
