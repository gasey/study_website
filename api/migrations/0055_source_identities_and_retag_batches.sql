BEGIN;
-- Audited operational source metadata; bank-authored papers/questions stay separate.
CREATE TABLE bank_paper_identities (
 paper_id text PRIMARY KEY REFERENCES papers(id),
 metadata jsonb NOT NULL CHECK(jsonb_typeof(metadata)='object'),
 source_ref jsonb NOT NULL,
 context_fingerprint text NOT NULL,
 version integer NOT NULL DEFAULT 1 CHECK(version>0),
 updated_by text NOT NULL, updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE bank_retag_batches (
 id text PRIMARY KEY,author_id text NOT NULL REFERENCES users(id),
 idempotency_key text NOT NULL,request_hash text NOT NULL,
 contribution_ids text[] NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(author_id,idempotency_key)
);
GRANT SELECT,INSERT,UPDATE ON bank_paper_identities TO mpsc;
GRANT SELECT,INSERT ON bank_retag_batches TO mpsc;
COMMIT;
