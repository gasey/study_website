BEGIN;
ALTER TABLE review_notifications ADD COLUMN mock_id TEXT REFERENCES mock_sessions(id);
ALTER TABLE mock_sessions ADD COLUMN excluded_presentations INTEGER NOT NULL DEFAULT 0;
ALTER TABLE attempts ADD COLUMN scoring_snapshot JSONB;
ALTER TABLE appearances ADD COLUMN context_revision BIGINT NOT NULL DEFAULT 0;
CREATE TABLE mock_assessments (
 id TEXT PRIMARY KEY, mock_id TEXT NOT NULL REFERENCES mock_sessions(id),
 input_hash TEXT NOT NULL, policy_version TEXT NOT NULL, payload JSONB NOT NULL,
 created_at TIMESTAMPTZ NOT NULL DEFAULT now(), UNIQUE(mock_id,input_hash,policy_version)
);
CREATE INDEX mock_assessments_history ON mock_assessments(mock_id,created_at DESC,id);
CREATE TABLE attempt_assessments (
 id BIGSERIAL PRIMARY KEY, attempt_id BIGINT NOT NULL REFERENCES attempts(id),
 input_hash TEXT NOT NULL, policy_version TEXT NOT NULL, payload JSONB NOT NULL,
 created_at TIMESTAMPTZ NOT NULL DEFAULT now(), UNIQUE(attempt_id,input_hash,policy_version)
);
CREATE INDEX attempt_assessments_history ON attempt_assessments(attempt_id,id DESC);
CREATE TABLE question_score_versions (canonical_id TEXT PRIMARY KEY REFERENCES canonical_questions(id),version BIGINT NOT NULL DEFAULT 1);
CREATE TABLE assessment_jobs (
 canonical_id TEXT PRIMARY KEY REFERENCES canonical_questions(id), requested_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 mock_cursor TEXT, attempt_cursor BIGINT NOT NULL DEFAULT 0,
 finished_at TIMESTAMPTZ, failures INTEGER NOT NULL DEFAULT 0,last_error TEXT
);
CREATE TABLE new_score_jobs (
 id BIGSERIAL PRIMARY KEY,mock_id TEXT REFERENCES mock_sessions(id),attempt_id BIGINT REFERENCES attempts(id),appearance_id TEXT REFERENCES appearances(id),
 finished_at TIMESTAMPTZ,failures INTEGER NOT NULL DEFAULT 0,last_error TEXT,
 CHECK(num_nonnulls(mock_id,attempt_id,appearance_id)=1),UNIQUE(mock_id),UNIQUE(attempt_id),UNIQUE(appearance_id)
);
CREATE INDEX new_score_jobs_pending ON new_score_jobs(id) WHERE finished_at IS NULL;
CREATE INDEX assessment_jobs_pending ON assessment_jobs(requested_at) WHERE finished_at IS NULL;
CREATE INDEX mock_questions_canonical ON mock_session_questions(canonical_id,mock_id);
CREATE INDEX mock_sessions_question_ids ON mock_sessions USING gin(question_ids);
CREATE TRIGGER immutable_mock_assessment BEFORE UPDATE OR DELETE ON mock_assessments FOR EACH ROW EXECUTE FUNCTION review_immutable();
CREATE TRIGGER immutable_attempt_assessment BEFORE UPDATE OR DELETE ON attempt_assessments FOR EACH ROW EXECUTE FUNCTION review_immutable();
CREATE OR REPLACE FUNCTION immutable_attempt_snapshot() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF OLD.scoring_snapshot IS NOT NULL AND NEW.scoring_snapshot IS DISTINCT FROM OLD.scoring_snapshot THEN
  RAISE EXCEPTION 'attempt scoring snapshot is immutable';
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER immutable_attempt_scoring_snapshot BEFORE UPDATE ON attempts FOR EACH ROW EXECUTE FUNCTION immutable_attempt_snapshot();
CREATE OR REPLACE FUNCTION enqueue_score_reassessment() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 INSERT INTO question_score_versions(canonical_id) VALUES (NEW.id) ON CONFLICT(canonical_id) DO UPDATE SET version=question_score_versions.version+1;
 INSERT INTO assessment_jobs(canonical_id) VALUES (NEW.id)
 ON CONFLICT(canonical_id) DO UPDATE SET requested_at=now(),mock_cursor=NULL,attempt_cursor=0,finished_at=NULL,failures=0,last_error=NULL;
 RETURN NEW;
END $$;
CREATE TRIGGER canonical_score_changed AFTER UPDATE ON canonical_questions FOR EACH ROW
 WHEN ((OLD.type,OLD.question,OLD.options,OLD.answer_text,OLD.answer_source,OLD.key_disputed,OLD.source_defect,OLD.status,OLD.direction,OLD.passage,OLD.question_markup,OLD.options_markup)
 IS DISTINCT FROM (NEW.type,NEW.question,NEW.options,NEW.answer_text,NEW.answer_source,NEW.key_disputed,NEW.source_defect,NEW.status,NEW.direction,NEW.passage,NEW.question_markup,NEW.options_markup))
 EXECUTE FUNCTION enqueue_score_reassessment();
CREATE FUNCTION valid_scoring_options(opts JSONB) RETURNS BOOLEAN LANGUAGE sql IMMUTABLE PARALLEL SAFE AS $$
 SELECT jsonb_typeof(opts)='array' AND jsonb_array_length(opts) BETWEEN 2 AND 8
 AND NOT EXISTS(SELECT 1 FROM jsonb_array_elements(opts) v WHERE jsonb_typeof(v)<>'string' OR btrim(v #>> '{}')='')
 AND (SELECT count(DISTINCT btrim(v))=count(*) FROM jsonb_array_elements_text(opts) v)
$$;
CREATE OR REPLACE VIEW v_scorable AS SELECT * FROM canonical_questions
 WHERE status='live' AND type='mcq' AND answer_text IS NOT NULL AND answer_source IN ('official','key')
 AND NOT key_disputed AND source_defect IS DISTINCT FROM 'duplicate-options' AND source_defect IS DISTINCT FROM 'unresolved-source'
 AND valid_scoring_options(options);
-- A derived label alone is not evidence of the independent review protocol.
-- Existing original results are retained; new timed estimates use this view.
CREATE VIEW v_reviewed_answer_publications AS SELECT c.id AS canonical_id,p.id AS publication_id
 FROM canonical_questions c JOIN bank_contributions b ON b.canonical_id=c.id
 JOIN bank_publications p ON p.contribution_id=b.id JOIN appearances a ON a.id=b.appearance_id AND a.is_primary
 WHERE c.status='live' AND c.type='mcq' AND c.answer_text IS NOT NULL AND c.answer_source='derived'
 AND valid_scoring_options(c.options) AND NOT c.key_disputed
 AND c.source_defect IS DISTINCT FROM 'duplicate-options' AND c.source_defect IS DISTINCT FROM 'unresolved-source'
 AND p.state='applied' AND b.state='published'
       AND b.kind IN ('answer','new_question','transcription')
       AND (p.manifest->'payload'->'patch') ? 'answerIndex'
       AND p.receipt->'after'->>'answerSource'='derived'
       AND p.receipt->'after'->>'question'=c.question
       AND p.receipt->'after'->'options'=c.options
       AND (p.receipt->'after'->>'direction') IS NOT DISTINCT FROM COALESCE(a.direction,c.direction)
       AND (p.receipt->'after'->>'passage') IS NOT DISTINCT FROM COALESCE(a.passage,c.passage)
       AND (p.receipt->'after'->>'questionMarkup') IS NOT DISTINCT FROM COALESCE(a.question_markup,c.question_markup)
       AND NULLIF(p.receipt->'after'->'optionsMarkup','null'::jsonb) IS NOT DISTINCT FROM COALESCE(a.options_markup,c.options_markup)
       AND (p.receipt->'after'->>'hasDiagram')::boolean=a.has_diagram
       AND (p.receipt->'after'->>'figureImage') IS NOT DISTINCT FROM a.figure_image
       AND jsonb_typeof(p.receipt->'after'->'answerIndex')='number'
       AND p.receipt->'after'->'options'->>((p.receipt->'after'->>'answerIndex')::int)=c.answer_text;
CREATE OR REPLACE VIEW v_mock_practice AS SELECT c.* FROM canonical_questions c
 WHERE c.id IN (SELECT id FROM v_scorable) OR c.id IN (SELECT canonical_id FROM v_reviewed_answer_publications);
GRANT SELECT ON v_reviewed_answer_publications TO mpsc;
CREATE OR REPLACE FUNCTION enqueue_attempt_reassessment() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF NEW.context='practice' THEN INSERT INTO new_score_jobs(attempt_id) VALUES (NEW.id) ON CONFLICT DO NOTHING; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER attempt_assessment_pending AFTER INSERT ON attempts FOR EACH ROW EXECUTE FUNCTION enqueue_attempt_reassessment();
CREATE OR REPLACE FUNCTION enqueue_publication_reassessment() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE target TEXT;
BEGIN
 SELECT canonical_id INTO target FROM bank_contributions WHERE id=NEW.contribution_id;
 IF target IS NOT NULL THEN
  INSERT INTO question_score_versions(canonical_id) VALUES (target) ON CONFLICT(canonical_id) DO UPDATE SET version=question_score_versions.version+1;
  INSERT INTO assessment_jobs(canonical_id) VALUES (target)
  ON CONFLICT(canonical_id) DO UPDATE SET requested_at=now(),mock_cursor=NULL,attempt_cursor=0,finished_at=NULL,failures=0,last_error=NULL;
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER publication_assessment_pending AFTER UPDATE OF state ON bank_publications FOR EACH ROW
 WHEN (NEW.state IN ('applied','reverted') AND OLD.state IS DISTINCT FROM NEW.state) EXECUTE FUNCTION enqueue_publication_reassessment();
CREATE OR REPLACE FUNCTION enqueue_appearance_reassessment() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 NEW.context_revision=OLD.context_revision+1;
 INSERT INTO new_score_jobs(appearance_id) VALUES (NEW.id) ON CONFLICT(appearance_id) DO UPDATE SET finished_at=NULL,failures=0,last_error=NULL;
 RETURN NEW;
END $$;
CREATE TRIGGER appearance_context_changed BEFORE UPDATE ON appearances FOR EACH ROW
 WHEN (NEW.canonical_id IS NOT NULL AND (OLD.direction,OLD.passage,OLD.question_markup,OLD.options_markup,OLD.has_diagram,OLD.figure_image) IS DISTINCT FROM (NEW.direction,NEW.passage,NEW.question_markup,NEW.options_markup,NEW.has_diagram,NEW.figure_image)) EXECUTE FUNCTION enqueue_appearance_reassessment();
GRANT INSERT,UPDATE ON review_worker_health TO mpsc;
INSERT INTO assessment_jobs(canonical_id)
 SELECT DISTINCT canonical_id FROM attempts WHERE canonical_id IS NOT NULL
 UNION SELECT DISTINCT unnest(question_ids) FROM mock_sessions WHERE submitted_at IS NOT NULL
 ON CONFLICT DO NOTHING;
GRANT SELECT,INSERT,UPDATE ON question_score_versions TO mpsc;
GRANT SELECT,INSERT ON mock_assessments,attempt_assessments TO mpsc;
GRANT SELECT,INSERT,UPDATE,DELETE ON assessment_jobs,new_score_jobs TO mpsc;
GRANT USAGE,SELECT ON ALL SEQUENCES IN SCHEMA public TO mpsc;
COMMIT;
