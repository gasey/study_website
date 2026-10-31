BEGIN;
CREATE TABLE admin_answer_decisions (
 id text PRIMARY KEY,canonical_id text NOT NULL REFERENCES canonical_questions(id),appearance_id text NOT NULL REFERENCES appearances(id),
 actor_id text NOT NULL REFERENCES users(id),mode text NOT NULL CHECK(mode IN ('official','verified','needs-review','unsolved')),
 contribution_id text UNIQUE REFERENCES bank_contributions(id),revision integer,
 baseline_hash text NOT NULL,payload_hash text NOT NULL,reason text NOT NULL CHECK(length(btrim(reason))>=20),
 request_key text NOT NULL,request_hash text NOT NULL,created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(actor_id,request_key),CHECK((mode='needs-review')=(contribution_id IS NULL))
);
CREATE INDEX admin_answer_question_history ON admin_answer_decisions(canonical_id,created_at DESC,id);
CREATE TRIGGER immutable_admin_answer_decision BEFORE UPDATE OR DELETE ON admin_answer_decisions FOR EACH ROW EXECUTE FUNCTION review_immutable();
GRANT SELECT,INSERT ON admin_answer_decisions TO mpsc;
COMMIT;
