BEGIN;
CREATE TABLE editorial_assignments (
 id text PRIMARY KEY,
 email text NOT NULL CHECK(email=lower(email)),
 collection_id text NOT NULL REFERENCES collections(id),
 user_id text REFERENCES users(id),
 state text NOT NULL DEFAULT 'pending' CHECK(state IN ('pending','active','revoked')),
 version integer NOT NULL DEFAULT 1,
 created_by text NOT NULL REFERENCES users(id),
 reason text NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now(),
 activated_at timestamptz,
 CHECK(state<>'active' OR user_id IS NOT NULL)
);
CREATE UNIQUE INDEX editorial_live_assignment ON editorial_assignments(email,collection_id) WHERE state<>'revoked';
CREATE TABLE editorial_assignment_papers (
 assignment_id text NOT NULL REFERENCES editorial_assignments(id),
 paper_id text NOT NULL REFERENCES papers(id),
 PRIMARY KEY(assignment_id,paper_id)
);
CREATE TABLE editorial_checks (
 id bigserial PRIMARY KEY,
 assignment_id text NOT NULL REFERENCES editorial_assignments(id),
 appearance_id text NOT NULL REFERENCES appearances(id),
 canonical_id text NOT NULL REFERENCES canonical_questions(id),
 reviewer_id text NOT NULL REFERENCES users(id),
 source_version text NOT NULL,
 outcome text NOT NULL CHECK(outcome IN ('checked','needs_correction','cannot_verify')),
 checklist jsonb NOT NULL,
 note text NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX editorial_checks_source ON editorial_checks(assignment_id,appearance_id,id DESC);
CREATE FUNCTION editorial_checks_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
 BEGIN RAISE EXCEPTION 'Editorial checks are append-only'; END $$;
CREATE TRIGGER editorial_checks_immutable BEFORE UPDATE OR DELETE ON editorial_checks
 FOR EACH ROW EXECUTE FUNCTION editorial_checks_immutable();
GRANT SELECT,INSERT,UPDATE ON editorial_assignments TO mpsc;
GRANT SELECT,INSERT ON editorial_assignment_papers,editorial_checks TO mpsc;
GRANT USAGE,SELECT ON SEQUENCE editorial_checks_id_seq TO mpsc;
COMMIT;
