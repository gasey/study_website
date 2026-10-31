BEGIN;
-- Operational inventory, separate from locally authored question/paper content.
CREATE TABLE bank_exam_catalog (
 id text PRIMARY KEY, title text NOT NULL CHECK(length(btrim(title)) BETWEEN 2 AND 400),
 collection_id text UNIQUE REFERENCES collections(id), version integer NOT NULL DEFAULT 1,
 created_by text NOT NULL, created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE bank_exam_papers (
 exam_id text NOT NULL REFERENCES bank_exam_catalog(id),paper_id text NOT NULL REFERENCES papers(id),
 created_by text NOT NULL,created_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(exam_id,paper_id)
);
CREATE TABLE bank_paper_expectations (
 id text PRIMARY KEY,exam_id text NOT NULL REFERENCES bank_exam_catalog(id),title text NOT NULL CHECK(length(btrim(title)) BETWEEN 2 AND 600),
 year integer CHECK(year BETWEEN 1900 AND 2100),booklet text NOT NULL DEFAULT '',
 expected_questions integer CHECK(expected_questions BETWEEN 1 AND 2000),paper_id text REFERENCES papers(id),
 reference_url text NOT NULL DEFAULT '',paper_url text NOT NULL DEFAULT '',note text NOT NULL CHECK(length(btrim(note)) BETWEEN 10 AND 4000),
 context_fingerprint text,context_reviewed boolean NOT NULL DEFAULT false,archived boolean NOT NULL DEFAULT false,
 version integer NOT NULL DEFAULT 1,created_by text NOT NULL,updated_by text NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now(),updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX bank_expectations_exam ON bank_paper_expectations(exam_id,year,id) WHERE NOT archived;
CREATE INDEX bank_expectations_paper ON bank_paper_expectations(paper_id) WHERE NOT archived;
CREATE TABLE bank_inventory_events (
 id bigserial PRIMARY KEY,actor_id text NOT NULL,action text NOT NULL,target_id text NOT NULL,
 before_data jsonb,after_data jsonb,reason text NOT NULL,created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE bank_inventory_imports (
 sha256 text PRIMARY KEY CHECK(sha256 ~ '^[0-9a-f]{64}$'),manifest jsonb NOT NULL,
 imported_by text NOT NULL,created_at timestamptz NOT NULL DEFAULT now()
);
INSERT INTO bank_exam_catalog(id,title,collection_id,created_by) SELECT id,title,id,'migration:0049' FROM collections WHERE kind='exam';
INSERT INTO bank_exam_papers(exam_id,paper_id,created_by)
 SELECT DISTINCT cp.collection_id,cp.paper_id,'migration:0049' FROM collection_papers cp JOIN bank_exam_catalog e ON e.collection_id=cp.collection_id
 JOIN collections c ON c.id=cp.collection_id AND c.live_version=cp.version ON CONFLICT DO NOTHING;
INSERT INTO bank_exam_papers(exam_id,paper_id,created_by)
 SELECT DISTINCT s.collection_id,p.id,'migration:0049' FROM collection_sections s JOIN bank_exam_catalog e ON e.collection_id=s.collection_id
 JOIN collections c ON c.id=s.collection_id AND c.live_version=s.version
 JOIN papers p ON p.id IN (SELECT jsonb_array_elements_text(CASE WHEN jsonb_typeof(s.query->'paper_ids')='array' THEN s.query->'paper_ids' ELSE '[]'::jsonb END)) ON CONFLICT DO NOTHING;
CREATE VIEW v_bank_answer_status AS SELECT q.id,
 CASE WHEN q.type<>'mcq' THEN 'written'
 WHEN q.status='held' OR q.key_disputed OR q.source_defect IN ('duplicate-options','unresolved-source') OR (q.answer_text IS NOT NULL AND NOT valid_scoring_options(q.options)) THEN 'needs-review'
 WHEN q.answer_text IS NULL THEN 'unsolved'
 WHEN q.answer_source IN ('official','key') THEN 'official'
 WHEN q.answer_source='derived' AND EXISTS(SELECT 1 FROM v_reviewed_answer_publications r WHERE r.canonical_id=q.id) THEN 'verified'
 ELSE 'needs-review' END AS answer_status FROM canonical_questions q;
GRANT SELECT,INSERT,UPDATE ON bank_exam_catalog,bank_exam_papers,bank_paper_expectations,bank_inventory_imports TO mpsc;
GRANT DELETE ON bank_exam_papers TO mpsc;
GRANT SELECT,INSERT ON bank_inventory_events TO mpsc;
GRANT USAGE,SELECT ON SEQUENCE bank_inventory_events_id_seq TO mpsc;
GRANT SELECT ON v_bank_answer_status TO mpsc;
COMMIT;
