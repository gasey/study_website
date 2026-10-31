BEGIN;
-- Existing immutable entries retain an honest legacy label. New entries carry
-- their rule version and mechanically provable source reference.
ALTER TABLE reward_ledger ADD COLUMN rule_version text NOT NULL DEFAULT 'legacy-v1';
ALTER TABLE reward_ledger ALTER COLUMN rule_version SET DEFAULT 'learning-v1';
ALTER TABLE reward_ledger ADD COLUMN source_attempt_id bigint REFERENCES attempts(id);
ALTER TABLE reward_ledger ADD COLUMN reverses_id bigint REFERENCES reward_ledger(id);
CREATE FUNCTION reward_receipt_metadata() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF NEW.kind IN ('study','game') AND NEW.event_key LIKE 'question:%' THEN
  SELECT c.attempt_id INTO NEW.source_attempt_id FROM reward_question_claims c
   WHERE c.user_id=NEW.user_id AND NEW.event_key='question:'||c.user_id||':'||c.canonical_id;
 END IF;
 IF NEW.event_key LIKE 'cms-archived:%' THEN
  SELECT id INTO NEW.reverses_id FROM reward_ledger
   WHERE event_key=replace(NEW.event_key,'cms-archived:','cms-published:') AND user_id=NEW.user_id;
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER add_reward_receipt_metadata BEFORE INSERT ON reward_ledger FOR EACH ROW EXECUTE FUNCTION reward_receipt_metadata();
COMMIT;
