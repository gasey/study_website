BEGIN;

-- Store the state needed for a faithful moderation undo. Existing mod_actions
-- rows remain valid and continue to be append-only audit records.
ALTER TABLE mod_actions
    ADD COLUMN IF NOT EXISTS before_state JSONB;

DO $$
DECLARE action_check TEXT;
BEGIN
    SELECT conname INTO action_check
      FROM pg_constraint
     WHERE conrelid = 'mod_actions'::regclass
       AND contype = 'c'
       AND pg_get_constraintdef(oid) ILIKE '%action%'
     LIMIT 1;
    IF action_check IS NOT NULL THEN
        EXECUTE format('ALTER TABLE mod_actions DROP CONSTRAINT %I', action_check);
    END IF;
END $$;

ALTER TABLE mod_actions
    ADD CONSTRAINT mod_actions_action_check
    CHECK (action IN ('hide','unhide','approve','reject','lock','unlock',
                      'warn','mute','unmute','escalate','dismiss','restore',
                      'grant_appeal','deny_appeal'));

COMMIT;
