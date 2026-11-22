BEGIN;

-- Separate from immutable 0131 and 0133 scopes/receipts. This migration never
-- runs cleanup; its caller requires three default-off settings.
ALTER TABLE users ADD COLUMN private_preferences_purged_at timestamptz;
CREATE INDEX users_closed_private_preferences_pending ON users(closed_at,id)
 WHERE closed_at IS NOT NULL AND study_history_purged_at IS NOT NULL
 AND private_study_purged_at IS NOT NULL AND private_preferences_purged_at IS NULL;

CREATE FUNCTION sweep_expired_private_preferences(p_accounts integer DEFAULT 5,p_batch integer DEFAULT 200)
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE u record; t text; scanned integer:=0; completed integer:=0;
        removed bigint:=0; n integer;
BEGIN
 IF p_accounts IS NULL OR p_batch IS NULL
   OR p_accounts<1 OR p_accounts>20 OR p_batch<1 OR p_batch>1000 THEN
   RAISE EXCEPTION 'Invalid private-preferences cleanup bounds';
 END IF;
 FOR u IN SELECT a.id FROM public.users a
   WHERE a.closed_at<=clock_timestamp()-interval '30 days'
     AND a.study_history_purged_at IS NOT NULL
     AND a.private_study_purged_at IS NOT NULL
     AND a.private_preferences_purged_at IS NULL
     AND NOT EXISTS(SELECT 1 FROM public.account_study_history_holds h
       WHERE h.user_id=a.id AND h.released_at IS NULL
         AND (h.expires_at IS NULL OR h.expires_at>clock_timestamp()))
   ORDER BY a.closed_at,a.id FOR UPDATE OF a SKIP LOCKED LIMIT p_accounts
 LOOP
   scanned:=scanned+1;
   FOREACH t IN ARRAY ARRAY[
     'user_calendar_preferences','inbox_preferences','inbox_desk_reads','game_preferences'
   ] LOOP
     EXECUTE format('DELETE FROM public.%I x WHERE x.user_id=$1 AND x.ctid IN '
       '(SELECT ctid FROM public.%I WHERE user_id=$1 ORDER BY ctid LIMIT $2 FOR UPDATE SKIP LOCKED)',t,t)
       USING u.id,p_batch;
     GET DIAGNOSTICS n=ROW_COUNT;removed:=removed+n;
   END LOOP;
   IF NOT EXISTS(SELECT 1 FROM public.user_calendar_preferences WHERE user_id=u.id)
     AND NOT EXISTS(SELECT 1 FROM public.inbox_preferences WHERE user_id=u.id)
     AND NOT EXISTS(SELECT 1 FROM public.inbox_desk_reads WHERE user_id=u.id)
     AND NOT EXISTS(SELECT 1 FROM public.game_preferences WHERE user_id=u.id)
   THEN
     UPDATE public.users SET private_preferences_purged_at=clock_timestamp() WHERE id=u.id
       AND private_preferences_purged_at IS NULL;
     IF FOUND THEN
       INSERT INTO public.account_security_events(user_id,action,detail)
        VALUES(u.id,'closed_private_preferences_purged',jsonb_build_object('policy','private-preferences-v1'));
       completed:=completed+1;
     END IF;
   END IF;
 END LOOP;
 RETURN jsonb_build_object('accounts_scanned',scanned,'accounts_completed',completed,'rows_removed',removed);
END $$;
REVOKE ALL ON FUNCTION sweep_expired_private_preferences(integer,integer) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION sweep_expired_private_preferences(integer,integer) TO mpsc;

-- Stale requests and workers cannot recreate private preference rows after closure.
CREATE TRIGGER private_preferences_account_active BEFORE INSERT OR UPDATE ON user_calendar_preferences
 FOR EACH ROW EXECUTE FUNCTION active_account_record('user_id');
CREATE TRIGGER private_preferences_account_active BEFORE INSERT OR UPDATE ON inbox_preferences
 FOR EACH ROW EXECUTE FUNCTION active_account_record('user_id');
CREATE TRIGGER private_preferences_account_active BEFORE INSERT OR UPDATE ON inbox_desk_reads
 FOR EACH ROW EXECUTE FUNCTION active_account_record('user_id');
CREATE TRIGGER private_preferences_account_active BEFORE INSERT OR UPDATE ON game_preferences
 FOR EACH ROW EXECUTE FUNCTION active_account_record('user_id');

CREATE FUNCTION private_preferences_purge_marker_guard() RETURNS trigger
LANGUAGE plpgsql SET search_path=pg_catalog,public AS $$
DECLARE changed boolean;
BEGIN
 IF TG_OP='INSERT' THEN changed:=NEW.private_preferences_purged_at IS NOT NULL;
 ELSE changed:=NEW.private_preferences_purged_at IS DISTINCT FROM OLD.private_preferences_purged_at;
 END IF;
 IF changed
   AND current_user<>(SELECT pg_get_userbyid(p.proowner) FROM pg_catalog.pg_proc p
     WHERE p.oid='public.sweep_expired_private_preferences(integer,integer)'::regprocedure)
 THEN RAISE EXCEPTION 'Private-preferences completion is operator managed'; END IF;
 RETURN NEW;
END $$;
REVOKE ALL ON FUNCTION private_preferences_purge_marker_guard() FROM PUBLIC;
CREATE TRIGGER private_preferences_purge_marker_guard BEFORE INSERT OR UPDATE OF private_preferences_purged_at ON users
 FOR EACH ROW EXECUTE FUNCTION private_preferences_purge_marker_guard();

-- Immutable audit trail for age-category declarations and owner-reviewed corrections.
-- No free-text personal details, date of birth, identity uploads or email copies.
CREATE TABLE account_audience_events (
 id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 user_id text NOT NULL REFERENCES users(id),
 actor_id text NOT NULL REFERENCES users(id),
 previous_category text CHECK(previous_category IS NULL OR previous_category IN ('adult','under18')),
 new_category text NOT NULL CHECK(new_category IN ('adult','under18')),
 request_id text REFERENCES privacy_requests(id),
 reason_code text NOT NULL CHECK(reason_code IN ('self_declaration','owner_verified_correction')),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 CHECK(
   (reason_code='self_declaration' AND request_id IS NULL)
   OR (reason_code='owner_verified_correction' AND request_id IS NOT NULL)
 )
);
CREATE INDEX account_audience_events_user ON account_audience_events(user_id,id DESC);
CREATE TRIGGER immutable_account_audience_event BEFORE UPDATE OR DELETE ON account_audience_events
 FOR EACH ROW EXECUTE FUNCTION review_immutable();
REVOKE ALL ON account_audience_events FROM PUBLIC,mpsc;
GRANT SELECT,INSERT ON account_audience_events TO mpsc;
GRANT USAGE,SELECT ON SEQUENCE account_audience_events_id_seq TO mpsc;

COMMENT ON COLUMN users.private_preferences_purged_at IS
 'Completion of the separately gated private preference cleanup (calendar/inbox/desk-read/game preferences); 0131/0133 completions alone do not certify it.';
COMMENT ON FUNCTION sweep_expired_private_preferences(integer,integer) IS
 'Bounded private preference cleanup after base and private-study cleanup, closure grace and holds; separately opt-in, never executed by migration application.';
COMMENT ON TABLE account_audience_events IS
 'Append-only audit trail for self-declarations and owner-reviewed age-category corrections; never stores DOB, ID documents or free-text PII.';

COMMIT;
