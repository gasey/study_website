BEGIN;
-- Paper sets reuse registered source IDs. Existing exam assignments keep their scope.
ALTER TABLE editorial_assignments ALTER COLUMN collection_id DROP NOT NULL;
ALTER TABLE editorial_assignments ADD COLUMN title text;
ALTER TABLE editorial_assignments ADD COLUMN scope_key text;
UPDATE editorial_assignments SET scope_key='collection:'||collection_id;
-- Keep existing clients/operators compatible during the additive rollout.
CREATE FUNCTION editorial_assignment_scope_default() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF NEW.scope_key IS NULL AND NEW.collection_id IS NOT NULL THEN
  NEW.scope_key='collection:'||NEW.collection_id;
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER editorial_scope_default BEFORE INSERT ON editorial_assignments
 FOR EACH ROW EXECUTE FUNCTION editorial_assignment_scope_default();
ALTER TABLE editorial_assignments ALTER COLUMN scope_key SET NOT NULL;
ALTER TABLE editorial_assignments ADD CONSTRAINT editorial_scope_named
 CHECK (collection_id IS NOT NULL OR length(trim(title)) BETWEEN 3 AND 200);
CREATE UNIQUE INDEX editorial_scope_assignment ON editorial_assignments(email,scope_key) WHERE state<>'revoked';
COMMIT;
