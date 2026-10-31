BEGIN;

ALTER TABLE users ADD COLUMN contribution_public BOOLEAN NOT NULL DEFAULT true;

CREATE TABLE review_grants (
 id BIGSERIAL PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id),
 role TEXT NOT NULL CHECK(role IN ('owner','publisher','senior','reviewer')),
 subject_id TEXT, granted_by TEXT NOT NULL, reason TEXT NOT NULL,
 created_at TIMESTAMPTZ NOT NULL DEFAULT now(), revoked_at TIMESTAMPTZ
);
CREATE UNIQUE INDEX review_grants_active ON review_grants(user_id,role,COALESCE(subject_id,'')) WHERE revoked_at IS NULL;
CREATE TABLE review_documents (
 id TEXT PRIMARY KEY, paper_id TEXT REFERENCES papers(id), title TEXT NOT NULL,
 source_file TEXT NOT NULL, sha256 TEXT NOT NULL CHECK(sha256 ~ '^[0-9a-f]{64}$'),
 kind TEXT NOT NULL CHECK(kind IN ('paper','official-key','reference')),
 key_status TEXT CHECK(key_status IN ('provisional','final','superseded')),
 registered_by TEXT NOT NULL, registered_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE review_taxonomy (
 id TEXT PRIMARY KEY, label TEXT NOT NULL, parent_id TEXT REFERENCES review_taxonomy(id),
 level TEXT NOT NULL CHECK(level IN ('subject','topic','subtopic')), version TEXT NOT NULL,
 active BOOLEAN NOT NULL DEFAULT true
);
CREATE TABLE bank_contributions (
 id TEXT PRIMARY KEY, author_id TEXT NOT NULL REFERENCES users(id),
 canonical_id TEXT REFERENCES canonical_questions(id), appearance_id TEXT REFERENCES appearances(id),
 kind TEXT NOT NULL CHECK(kind IN ('answer','transcription','explanation','taxonomy','source_reference','new_question','defect','duplicate','source_request')),
 subject_id TEXT NOT NULL, title TEXT NOT NULL,
 state TEXT NOT NULL DEFAULT 'draft' CHECK(state IN ('draft','submitted','in_review','changes_requested','rejected','withdrawn','accepted','publishing','publication_failed','published','reverted')),
 revision INTEGER NOT NULL DEFAULT 1, lock_version INTEGER NOT NULL DEFAULT 1,
 lease_user TEXT REFERENCES users(id), lease_until TIMESTAMPTZ,
 idempotency_key TEXT NOT NULL, request_hash TEXT NOT NULL,
 created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 UNIQUE(author_id,idempotency_key)
);
CREATE INDEX contributions_queue ON bank_contributions(state,created_at,id);
CREATE INDEX contributions_author ON bank_contributions(author_id,created_at DESC,id);
CREATE INDEX contributions_target ON bank_contributions(canonical_id,state);
CREATE TABLE contribution_revisions (
 contribution_id TEXT NOT NULL REFERENCES bank_contributions(id), revision INTEGER NOT NULL,
 payload JSONB NOT NULL, baseline JSONB NOT NULL, baseline_hash TEXT NOT NULL,
 actor_id TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 PRIMARY KEY(contribution_id,revision)
);
CREATE TABLE contribution_decisions (
 id BIGSERIAL PRIMARY KEY, contribution_id TEXT NOT NULL, revision INTEGER NOT NULL,
 reviewer_id TEXT NOT NULL REFERENCES users(id), decision TEXT NOT NULL CHECK(decision IN ('approve','reject','request_changes')),
 rationale TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 FOREIGN KEY(contribution_id,revision) REFERENCES contribution_revisions(contribution_id,revision),
 UNIQUE(contribution_id,revision,reviewer_id)
);
CREATE TABLE contribution_events (
 id BIGSERIAL PRIMARY KEY, contribution_id TEXT REFERENCES bank_contributions(id),
 actor_id TEXT NOT NULL, action TEXT NOT NULL, detail JSONB NOT NULL DEFAULT '{}',
 created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX contribution_events_target ON contribution_events(contribution_id,id);
CREATE TABLE contribution_appeals (
 id BIGSERIAL PRIMARY KEY, contribution_id TEXT NOT NULL REFERENCES bank_contributions(id),
 revision INTEGER NOT NULL, reason TEXT NOT NULL, state TEXT NOT NULL DEFAULT 'open' CHECK(state IN ('open','granted','denied')),
 decided_by TEXT REFERENCES users(id), decision_reason TEXT,
 created_at TIMESTAMPTZ NOT NULL DEFAULT now(), UNIQUE(contribution_id,revision)
);
CREATE TABLE review_holds (
 id BIGSERIAL PRIMARY KEY, canonical_id TEXT NOT NULL REFERENCES canonical_questions(id),
 reason TEXT NOT NULL, placed_by TEXT NOT NULL, released_by TEXT,
 previous_status TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now(), released_at TIMESTAMPTZ
);
CREATE UNIQUE INDEX review_holds_active ON review_holds(canonical_id) WHERE released_at IS NULL;
CREATE TABLE bank_publications (
 id TEXT PRIMARY KEY, contribution_id TEXT NOT NULL REFERENCES bank_contributions(id), revision INTEGER NOT NULL,
 manifest JSONB NOT NULL, manifest_hash TEXT NOT NULL, exported_by TEXT NOT NULL,
 state TEXT NOT NULL DEFAULT 'exported' CHECK(state IN ('exported','applied','failed','reverted')),
 receipt JSONB, error TEXT, created_at TIMESTAMPTZ NOT NULL DEFAULT now(), finished_at TIMESTAMPTZ,
 UNIQUE(contribution_id,revision)
);
CREATE TABLE contribution_credit (
 id BIGSERIAL PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id),
 contribution_id TEXT NOT NULL REFERENCES bank_contributions(id), publication_id TEXT NOT NULL REFERENCES bank_publications(id),
 amount INTEGER NOT NULL, event_key TEXT NOT NULL UNIQUE, reason TEXT NOT NULL,
 subject_id TEXT NOT NULL, rule_version TEXT NOT NULL DEFAULT 'v1',
 created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX contribution_credit_rank ON contribution_credit(created_at,user_id);
CREATE TABLE contribution_votes (
 user_id TEXT NOT NULL REFERENCES users(id), contribution_id TEXT NOT NULL REFERENCES bank_contributions(id),
 created_at TIMESTAMPTZ NOT NULL DEFAULT now(), PRIMARY KEY(user_id,contribution_id)
);
CREATE TABLE review_notifications (
 id BIGSERIAL PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id), contribution_id TEXT REFERENCES bank_contributions(id),
 event_key TEXT NOT NULL UNIQUE, message TEXT NOT NULL, read_at TIMESTAMPTZ,
 created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX review_notifications_user ON review_notifications(user_id,id DESC);
CREATE TABLE review_rate_buckets (
 bucket TEXT PRIMARY KEY, count INTEGER NOT NULL DEFAULT 1, expires_at TIMESTAMPTZ NOT NULL
);
CREATE TABLE review_outbox (
 id BIGSERIAL PRIMARY KEY, event_key TEXT NOT NULL UNIQUE, kind TEXT NOT NULL,
 payload JSONB NOT NULL, attempts INTEGER NOT NULL DEFAULT 0, available_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 finished_at TIMESTAMPTZ, last_error TEXT
);
CREATE TABLE review_worker_health (worker_id TEXT PRIMARY KEY, seen_at TIMESTAMPTZ NOT NULL DEFAULT now(), status TEXT NOT NULL);
GRANT SELECT ON review_worker_health TO mpsc;
CREATE TABLE question_duplicate_links (
 left_id TEXT NOT NULL REFERENCES canonical_questions(id), right_id TEXT NOT NULL REFERENCES canonical_questions(id),
 contribution_id TEXT NOT NULL REFERENCES bank_contributions(id), PRIMARY KEY(left_id,right_id), CHECK(left_id<>right_id)
);
CREATE OR REPLACE FUNCTION review_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'review history is append-only'; END $$;
CREATE TRIGGER immutable_revision BEFORE UPDATE OR DELETE ON contribution_revisions FOR EACH ROW EXECUTE FUNCTION review_immutable();
CREATE TRIGGER immutable_decision BEFORE UPDATE OR DELETE ON contribution_decisions FOR EACH ROW EXECUTE FUNCTION review_immutable();
CREATE TRIGGER immutable_event BEFORE UPDATE OR DELETE ON contribution_events FOR EACH ROW EXECUTE FUNCTION review_immutable();
CREATE TRIGGER immutable_credit BEFORE UPDATE OR DELETE ON contribution_credit FOR EACH ROW EXECUTE FUNCTION review_immutable();

-- Report counts prioritize work. Only an explicit review action changes scoring eligibility.
DROP TRIGGER IF EXISTS cr_hold ON content_reports;
INSERT INTO review_holds(canonical_id,reason,placed_by,previous_status)
 SELECT id,COALESCE(held_reason,'Existing hold'),'migration:0030','live'
 FROM canonical_questions WHERE status='held' ON CONFLICT DO NOTHING;

ALTER TABLE papers DROP CONSTRAINT papers_exam_type_check;
ALTER TABLE papers ADD CONSTRAINT papers_exam_type_check CHECK(exam_type IN ('Departmental','Direct','Direct_NG','LDE','Community'));
ALTER TABLE canonical_questions DROP CONSTRAINT canonical_questions_source_defect_check;
ALTER TABLE canonical_questions ADD CONSTRAINT canonical_questions_source_defect_check
 CHECK(source_defect IN ('duplicate-options','hand-transcribed-matching-table','correct-option-added','diagram-not-embedded','unresolved-source'));
CREATE OR REPLACE VIEW v_scorable AS SELECT * FROM canonical_questions
 WHERE status='live' AND answer_text IS NOT NULL AND answer_source IN ('official','key')
 AND NOT key_disputed AND source_defect IS DISTINCT FROM 'duplicate-options' AND source_defect IS DISTINCT FROM 'unresolved-source';
CREATE OR REPLACE VIEW v_practice AS SELECT * FROM canonical_questions
 WHERE status='live' AND answer_text IS NOT NULL AND source_defect IS DISTINCT FROM 'duplicate-options' AND source_defect IS DISTINCT FROM 'unresolved-source';
CREATE OR REPLACE VIEW v_mock_practice AS SELECT * FROM canonical_questions
 WHERE status='live' AND answer_text IS NOT NULL AND answer_source IN ('official','key','derived')
 AND NOT key_disputed AND source_defect IS DISTINCT FROM 'duplicate-options' AND source_defect IS DISTINCT FROM 'unresolved-source';
GRANT SELECT,INSERT,UPDATE,DELETE ON review_grants,review_documents,review_taxonomy,bank_contributions,
 contribution_revisions,contribution_decisions,contribution_events,contribution_appeals,review_holds,
 bank_publications,contribution_credit,contribution_votes,review_notifications,review_rate_buckets,
 review_outbox,question_duplicate_links TO mpsc;
GRANT USAGE,SELECT ON ALL SEQUENCES IN SCHEMA public TO mpsc;
COMMIT;
