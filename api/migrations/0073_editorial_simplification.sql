BEGIN;
ALTER TABLE content_reports DROP CONSTRAINT content_reports_kind_check;
ALTER TABLE content_reports ADD CONSTRAINT content_reports_kind_check
 CHECK(kind IN ('wrong_key','typo_ocr','outdated','ambiguous','duplicate','subject'));
CREATE TABLE admin_bank_decisions (
 id text PRIMARY KEY,
 actor_id text NOT NULL REFERENCES users(id),
 canonical_id text NOT NULL REFERENCES canonical_questions(id),
 appearance_id text NOT NULL REFERENCES appearances(id),
 contribution_id text UNIQUE NOT NULL REFERENCES bank_contributions(id),
 revision integer NOT NULL,
 kind text NOT NULL CHECK(kind IN ('taxonomy','explanation','transcription','source_reference','defect')),
 baseline_hash text NOT NULL,
 payload_hash text NOT NULL,
 reason text NOT NULL CHECK(length(btrim(reason))>=20),
 request_key text NOT NULL,
 request_hash text NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(actor_id,request_key)
);
CREATE INDEX admin_bank_decision_question ON admin_bank_decisions(canonical_id,created_at DESC);
CREATE TRIGGER immutable_admin_bank_decision BEFORE UPDATE OR DELETE ON admin_bank_decisions
 FOR EACH ROW EXECUTE FUNCTION review_immutable();
CREATE TABLE admin_bank_report_links (
 decision_id text NOT NULL REFERENCES admin_bank_decisions(id),
 report_id bigint NOT NULL REFERENCES content_reports(id),
 PRIMARY KEY(decision_id,report_id)
);
CREATE TRIGGER immutable_admin_bank_report_link BEFORE UPDATE OR DELETE ON admin_bank_report_links
 FOR EACH ROW EXECUTE FUNCTION review_immutable();
ALTER TABLE editorial_checks ADD COLUMN fingerprints jsonb;
ALTER TABLE editorial_checks ADD COLUMN attestation text;
CREATE INDEX content_reports_subject_open ON content_reports(canonical_id,created_at,id)
 WHERE kind='subject' AND status IN ('open','confirmed');
GRANT SELECT,INSERT ON admin_bank_decisions,admin_bank_report_links TO mpsc;
COMMIT;
