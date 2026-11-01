BEGIN;
-- Viewing is deliberately separate from attempts, accuracy and reward receipts.
CREATE TABLE answer_reveals (
 user_id text NOT NULL REFERENCES users(id),
 canonical_id text NOT NULL REFERENCES canonical_questions(id),
 revealed_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY (user_id, canonical_id)
);
GRANT SELECT, INSERT, UPDATE ON answer_reveals TO mpsc;
COMMIT;
