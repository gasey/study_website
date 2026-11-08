BEGIN;
ALTER TABLE editorial_checks ALTER COLUMN assignment_id DROP NOT NULL;
ALTER TABLE editorial_checks ADD COLUMN origin_scope text;
ALTER TABLE editorial_checks ADD COLUMN scope_revision text;
ALTER TABLE editorial_checks ADD COLUMN request_key text;
ALTER TABLE editorial_checks ADD COLUMN request_hash text;
ALTER TABLE editorial_checks ADD CONSTRAINT editorial_check_origin CHECK
 (assignment_id IS NOT NULL OR (origin_scope IS NOT NULL AND scope_revision IS NOT NULL));
CREATE INDEX editorial_checks_appearance ON editorial_checks(appearance_id,id DESC);
CREATE UNIQUE INDEX editorial_checks_request ON editorial_checks(reviewer_id,request_key) WHERE request_key IS NOT NULL;
CREATE TABLE editorial_check_resolutions (
 id bigserial PRIMARY KEY,
 check_id bigint NOT NULL REFERENCES editorial_checks(id),
 resolution_check_id bigint NOT NULL REFERENCES editorial_checks(id),
 actor_id text NOT NULL REFERENCES users(id),
 fingerprint text NOT NULL,
 reason text NOT NULL CHECK(length(btrim(reason))>=15),
 created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(check_id,resolution_check_id)
);
CREATE INDEX editorial_resolution_source ON editorial_check_resolutions(check_id);
CREATE TRIGGER editorial_resolution_immutable BEFORE UPDATE OR DELETE ON editorial_check_resolutions
 FOR EACH ROW EXECUTE FUNCTION editorial_checks_immutable();
GRANT SELECT,INSERT ON editorial_check_resolutions TO mpsc;
GRANT USAGE,SELECT ON SEQUENCE editorial_check_resolutions_id_seq TO mpsc;
COMMIT;
