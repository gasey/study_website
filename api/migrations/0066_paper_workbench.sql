BEGIN;
CREATE TABLE paper_workbench_assets (
 sha256 text PRIMARY KEY CHECK(sha256 ~ '^[0-9a-f]{64}$'),
 bytes bigint NOT NULL CHECK(bytes>0 AND bytes<=20971520),
 filename text NOT NULL,created_by text NOT NULL REFERENCES users(id),created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE paper_workbench_drafts (
 id text PRIMARY KEY,author_id text NOT NULL REFERENCES users(id),source_sha256 text NOT NULL REFERENCES paper_workbench_assets(sha256),
 payload jsonb NOT NULL,version integer NOT NULL DEFAULT 1,
 state text NOT NULL DEFAULT 'draft' CHECK(state IN ('draft','review','approved','queued','publishing','published','failed')),
 submission_id text,extraction_id text,published_paper_id text,last_error text,
 created_at timestamptz NOT NULL DEFAULT now(),updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE paper_workbench_history (
 id bigserial PRIMARY KEY,draft_id text NOT NULL REFERENCES paper_workbench_drafts(id),version integer NOT NULL,
 actor_id text NOT NULL REFERENCES users(id),action text NOT NULL,payload jsonb NOT NULL,created_at timestamptz NOT NULL DEFAULT now(),UNIQUE(draft_id,version)
);
CREATE TABLE paper_workbench_reviewers (
 draft_id text NOT NULL REFERENCES paper_workbench_drafts(id),user_id text NOT NULL REFERENCES users(id),assigned_by text NOT NULL REFERENCES users(id),
 active boolean NOT NULL DEFAULT true,PRIMARY KEY(draft_id,user_id)
);
CREATE TABLE paper_workbench_reviews (
 id bigserial PRIMARY KEY,draft_id text NOT NULL REFERENCES paper_workbench_drafts(id),submission_id text NOT NULL,
 payload_hash text NOT NULL,reviewer_id text NOT NULL REFERENCES users(id),decision text NOT NULL CHECK(decision IN ('approve','changes')),
 note text NOT NULL,created_at timestamptz NOT NULL DEFAULT now(),UNIQUE(draft_id,submission_id,reviewer_id)
);
CREATE TABLE paper_workbench_jobs (
 id text PRIMARY KEY,draft_id text NOT NULL REFERENCES paper_workbench_drafts(id),kind text NOT NULL CHECK(kind IN ('extract','render','ocr','crop','publish')),
 args jsonb NOT NULL DEFAULT '{}',state text NOT NULL DEFAULT 'queued' CHECK(state IN ('queued','running','done','failed')),
 attempts integer NOT NULL DEFAULT 0,lease_until timestamptz,result jsonb,error text,
 created_at timestamptz NOT NULL DEFAULT now(),finished_at timestamptz
);
CREATE INDEX paper_workbench_job_queue ON paper_workbench_jobs(state,created_at);
CREATE TABLE paper_workbench_pages (
 extraction_id text NOT NULL REFERENCES paper_workbench_jobs(id),page integer NOT NULL CHECK(page>0),text text NOT NULL,
 PRIMARY KEY(extraction_id,page)
);
CREATE TRIGGER paper_workbench_history_immutable BEFORE UPDATE OR DELETE ON paper_workbench_history FOR EACH ROW EXECUTE FUNCTION editorial_checks_immutable();
CREATE TRIGGER paper_workbench_reviews_immutable BEFORE UPDATE OR DELETE ON paper_workbench_reviews FOR EACH ROW EXECUTE FUNCTION editorial_checks_immutable();
GRANT SELECT,INSERT ON paper_workbench_assets,paper_workbench_history,paper_workbench_reviews TO mpsc;
GRANT SELECT,INSERT,UPDATE ON paper_workbench_drafts,paper_workbench_reviewers,paper_workbench_jobs TO mpsc;
GRANT SELECT,INSERT ON paper_workbench_pages TO mpsc;
GRANT USAGE,SELECT ON SEQUENCE paper_workbench_history_id_seq,paper_workbench_reviews_id_seq TO mpsc;
COMMIT;
