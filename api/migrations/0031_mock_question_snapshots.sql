-- New mocks freeze the presented content and answer used for their original
-- result. Historical sessions cannot be reconstructed; do not fabricate a
-- start-time snapshot for them. Their existing fallback is retained.
BEGIN;
ALTER TABLE mock_session_questions ADD COLUMN snapshot JSONB;
ALTER TABLE mock_session_questions ADD COLUMN snapshot_at TIMESTAMPTZ;
CREATE OR REPLACE FUNCTION mock_snapshot_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF OLD.snapshot IS NOT NULL AND (NEW.snapshot IS DISTINCT FROM OLD.snapshot OR NEW.options IS DISTINCT FROM OLD.options OR NEW.canonical_id IS DISTINCT FROM OLD.canonical_id OR NEW.mock_id IS DISTINCT FROM OLD.mock_id) THEN
  RAISE EXCEPTION 'mock question snapshot is immutable';
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER immutable_mock_snapshot BEFORE UPDATE ON mock_session_questions FOR EACH ROW EXECUTE FUNCTION mock_snapshot_immutable();
COMMIT;
