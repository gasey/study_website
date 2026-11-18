-- Private scheduling suggestions only; no attempts, rewards or notification jobs.
BEGIN;
CREATE TABLE calendar_entries (
 id uuid PRIMARY KEY,
 user_id text NOT NULL REFERENCES users(id),
 date date NOT NULL CHECK (date BETWEEN DATE '2000-01-01' AND DATE '2100-12-31'),
 title text NOT NULL CHECK (length(btrim(title)) BETWEEN 1 AND 180),
 note text NOT NULL DEFAULT '' CHECK (length(note)<=3000),
 kind text NOT NULL CHECK (kind IN ('personal','progress-test','exam-target')),
 recurrence integer CHECK (recurrence IN (7,14)),
 collection_id text REFERENCES collections(id),
 version integer NOT NULL DEFAULT 1 CHECK (version>0),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 updated_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 CHECK ((kind='progress-test' AND recurrence IS NOT NULL AND collection_id IS NOT NULL)
   OR (kind<>'progress-test' AND recurrence IS NULL))
);
CREATE INDEX calendar_entries_owner_date ON calendar_entries(user_id,date,id);
CREATE TABLE calendar_feed_tokens (
 user_id text PRIMARY KEY REFERENCES users(id),
 token_hash text UNIQUE CHECK (token_hash ~ '^[0-9a-f]{64}$'),
 version integer NOT NULL CHECK (version>0),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 revoked_at timestamptz,
 CHECK ((token_hash IS NULL) = (revoked_at IS NOT NULL))
);
GRANT SELECT,INSERT,UPDATE,DELETE ON calendar_entries TO mpsc;
GRANT SELECT,INSERT,UPDATE ON calendar_feed_tokens TO mpsc;
-- V.5 identity and cosmetic extensions; preserve all existing values and ownership.
ALTER TABLE users ADD COLUMN identity_version integer NOT NULL DEFAULT 0 CHECK(identity_version>=0);
ALTER TABLE users ADD COLUMN handle_changed_at timestamptz;
CREATE UNIQUE INDEX users_handle_casefold ON users(lower(handle));
ALTER TABLE creator_profiles ADD COLUMN bio_version integer NOT NULL DEFAULT 0 CHECK(bio_version>=0);
ALTER TABLE creator_profiles ADD COLUMN bio_needs_approval boolean NOT NULL DEFAULT false;
ALTER TABLE creator_profiles ADD COLUMN bio_hidden boolean NOT NULL DEFAULT false;
ALTER TABLE avatar_events DROP CONSTRAINT avatar_events_action_check;
ALTER TABLE avatar_events ADD CONSTRAINT avatar_events_action_check CHECK(action IN ('saved','reset','purchased'));
-- Account closure retains the user ID as an anonymous immutable-history anchor.
ALTER TABLE users ADD COLUMN closed_at timestamptz;
ALTER TABLE users ADD CONSTRAINT closed_account_anonymous CHECK(closed_at IS NULL OR
 (email IS NULL AND password_hash IS NULL AND name IS NULL AND avatar IS NULL AND email_verified_at IS NULL AND NOT contribution_public));
CREATE OR REPLACE FUNCTION account_has_pro(uid TEXT) RETURNS BOOLEAN LANGUAGE sql STABLE AS $$
 SELECT EXISTS(SELECT 1 FROM users u WHERE u.id=uid AND u.closed_at IS NULL AND (
 (u.plan_code='pro' AND ((u.plan_status IN ('active','authenticated') AND (u.plan_ends_at IS NULL OR u.plan_ends_at>now())) OR (u.plan_status='trial' AND u.trial_ends_at>now()) OR u.plan_ends_at>now()))
 OR EXISTS(SELECT 1 FROM reward_redemptions WHERE user_id=uid AND starts_at<=now() AND ends_at>now())
 OR EXISTS(SELECT 1 FROM billing_access_grants WHERE user_id=uid AND starts_at<=now() AND ends_at>now())));
$$;
CREATE FUNCTION closed_identity_stays_anonymous() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF OLD.closed_at IS NOT NULL AND
   (NEW.closed_at,NEW.email,NEW.password_hash,NEW.name,NEW.handle,NEW.avatar,NEW.email_verified_at,NEW.contribution_public)
     IS DISTINCT FROM
   (OLD.closed_at,OLD.email,OLD.password_hash,OLD.name,OLD.handle,OLD.avatar,OLD.email_verified_at,OLD.contribution_public)
 THEN RAISE EXCEPTION 'Closed accounts cannot restore an identity'; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER closed_identity_stays_anonymous BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION closed_identity_stays_anonymous();
CREATE FUNCTION active_account_record() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE ended timestamptz;
BEGIN
 -- Lock the owner even when active: credential creation and closure serialize.
 EXECUTE 'SELECT closed_at FROM users WHERE id=$1 FOR SHARE'
 INTO ended USING to_jsonb(NEW)->>TG_ARGV[0];
 IF ended IS NOT NULL THEN RAISE EXCEPTION 'Account is closed'; END IF;
 RETURN NEW;
END $$;
DO $$
DECLARE t text;
BEGIN
 FOREACH t IN ARRAY ARRAY['auth_sessions','mobile_sessions','google_identities','account_email_tokens','account_mfa','mfa_recovery_codes','creator_profiles','reward_profiles','personal_desks','calendar_entries','calendar_feed_tokens','user_avatar_items','user_focus_subjects','user_exam_bookmarks','study_desk_members'] LOOP
   EXECUTE format('CREATE TRIGGER active_account_record BEFORE INSERT OR UPDATE ON %I FOR EACH ROW EXECUTE FUNCTION active_account_record(''user_id'')',t);
 END LOOP;
END $$;
CREATE TRIGGER active_account_record BEFORE INSERT OR UPDATE ON study_desks
 FOR EACH ROW EXECUTE FUNCTION active_account_record('owner_id');
GRANT SELECT ON billing_subscriptions TO mpsc;
GRANT SELECT,UPDATE ON auth_sessions TO mpsc;
-- Closure-only cleanup grants; immutable history/ledger grants are unchanged.
GRANT DELETE ON google_identities,account_mail_outbox,mfa_recovery_codes TO mpsc;
COMMIT;
