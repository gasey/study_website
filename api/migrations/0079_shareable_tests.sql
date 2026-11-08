BEGIN;
-- Timed tests extend reviewed learning collections rather than duplicating authors/review.
ALTER TABLE learning_catalog ADD COLUMN live_test_version integer;
CREATE TABLE learning_test_publications (
 entry_id text NOT NULL REFERENCES learning_catalog(id),
 revision integer NOT NULL CHECK(revision>0),
 payload jsonb NOT NULL,
 questions jsonb NOT NULL CHECK(jsonb_typeof(questions)='array'),
 published_by text NOT NULL REFERENCES users(id),
 published_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(entry_id,revision)
);
CREATE TRIGGER learning_test_publication_immutable BEFORE UPDATE OR DELETE ON learning_test_publications
 FOR EACH ROW EXECUTE FUNCTION editorial_checks_immutable();
ALTER TABLE learning_catalog ADD CONSTRAINT learning_live_test_publication
 FOREIGN KEY(id,live_test_version) REFERENCES learning_test_publications(entry_id,revision);
ALTER TABLE mock_sessions ADD COLUMN learning_test_id text;
ALTER TABLE mock_sessions ADD COLUMN learning_test_version integer;
ALTER TABLE mock_sessions ADD COLUMN learning_test_title text;
ALTER TABLE mock_sessions ADD CONSTRAINT mock_learning_test_publication
 FOREIGN KEY(learning_test_id,learning_test_version) REFERENCES learning_test_publications(entry_id,revision);
ALTER TABLE mock_sessions ADD CONSTRAINT mock_learning_test_complete CHECK(
 (learning_test_id IS NULL AND learning_test_version IS NULL AND learning_test_title IS NULL) OR
 (learning_test_id IS NOT NULL AND learning_test_version IS NOT NULL AND learning_test_title IS NOT NULL));
CREATE INDEX mock_learning_test_stats ON mock_sessions(learning_test_id,learning_test_version,started_at) WHERE learning_test_id IS NOT NULL;
INSERT INTO collections(id,title,kind,route,visibility,position)
 VALUES('shared-tests','Shared mock tests','tool','/tests','hidden',1000);
GRANT SELECT,INSERT ON learning_test_publications TO mpsc;
COMMIT;
