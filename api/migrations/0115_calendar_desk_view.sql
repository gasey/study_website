-- Explicit sharing stays on the one account-owned calendar store.
BEGIN;
ALTER TABLE calendar_entries ADD COLUMN desk_id text REFERENCES study_desks(id);
ALTER TABLE calendar_entries ADD COLUMN desk_joined_at timestamptz;
ALTER TABLE calendar_entries ADD CONSTRAINT calendar_desk_consent_epoch
 CHECK ((desk_id IS NULL) = (desk_joined_at IS NULL));
CREATE INDEX calendar_entries_desk_view ON calendar_entries(desk_id,date,id) WHERE desk_id IS NOT NULL;
COMMIT;
