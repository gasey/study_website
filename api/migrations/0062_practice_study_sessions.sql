BEGIN;
-- Study sets reference the shared bank and existing immutable answer receipts.
-- They never maintain a second attempt, score or reward ledger.
CREATE TABLE practice_study_sessions (
 id text PRIMARY KEY,
 user_id text NOT NULL REFERENCES users(id),
 collection_id text NOT NULL REFERENCES collections(id),
 request_key text NOT NULL,
 request_hash text NOT NULL,
 requested_size integer NOT NULL CHECK (requested_size IN (10,20)),
 question_ids text[] NOT NULL CHECK (cardinality(question_ids) BETWEEN 1 AND 20),
 paper_ids text[] NOT NULL,
 filters jsonb NOT NULL,
 position integer NOT NULL DEFAULT 0 CHECK (position >= 0),
 viewed_ids text[] NOT NULL DEFAULT '{}',
 version integer NOT NULL DEFAULT 1,
 created_at timestamptz NOT NULL DEFAULT now(),
 updated_at timestamptz NOT NULL DEFAULT now(),
 finished_at timestamptz,
 summary jsonb,
 UNIQUE(user_id,request_key),
 CHECK (cardinality(question_ids)=cardinality(paper_ids)),
 CHECK (position<cardinality(question_ids)),
 CHECK (viewed_ids <@ question_ids)
);
CREATE INDEX practice_study_sessions_owner ON practice_study_sessions(user_id,collection_id,updated_at DESC);
GRANT SELECT,INSERT,UPDATE ON practice_study_sessions TO mpsc;
COMMIT;
