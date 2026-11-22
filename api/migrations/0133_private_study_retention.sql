BEGIN;

-- Separate from the immutable 0131 scope/receipt. This migration never runs
-- cleanup and its caller requires two default-off settings.
ALTER TABLE users ADD COLUMN private_study_purged_at timestamptz;
CREATE INDEX users_closed_private_study_pending ON users(closed_at,id)
 WHERE closed_at IS NOT NULL AND study_history_purged_at IS NOT NULL
 AND private_study_purged_at IS NULL;

CREATE FUNCTION sweep_expired_private_study(p_accounts integer DEFAULT 5,p_batch integer DEFAULT 200)
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE u record; t text; scanned integer:=0; completed integer:=0;
        removed bigint:=0; n integer;
BEGIN
 IF p_accounts IS NULL OR p_batch IS NULL
   OR p_accounts<1 OR p_accounts>20 OR p_batch<1 OR p_batch>1000 THEN
   RAISE EXCEPTION 'Invalid private-study cleanup bounds';
 END IF;
 FOR u IN SELECT a.id FROM public.users a
   WHERE a.closed_at<=clock_timestamp()-interval '30 days'
     AND a.study_history_purged_at IS NOT NULL
     AND a.private_study_purged_at IS NULL
     AND NOT EXISTS(SELECT 1 FROM public.account_study_history_holds h
       WHERE h.user_id=a.id AND h.released_at IS NULL
         AND (h.expires_at IS NULL OR h.expires_at>clock_timestamp()))
   ORDER BY a.closed_at,a.id FOR UPDATE OF a SKIP LOCKED LIMIT p_accounts
 LOOP
   scanned:=scanned+1;
   FOREACH t IN ARRAY ARRAY[
     'essay_drafts','user_question_bookmarks','material_bookmarks','user_calendar_saved'
   ] LOOP
     EXECUTE format('DELETE FROM public.%I x WHERE x.user_id=$1 AND x.ctid IN '
       '(SELECT ctid FROM public.%I WHERE user_id=$1 ORDER BY ctid LIMIT $2 FOR UPDATE SKIP LOCKED)',t,t)
       USING u.id,p_batch;
     GET DIAGNOSTICS n=ROW_COUNT;removed:=removed+n;
   END LOOP;
   IF NOT EXISTS(SELECT 1 FROM public.essay_drafts WHERE user_id=u.id)
     AND NOT EXISTS(SELECT 1 FROM public.user_question_bookmarks WHERE user_id=u.id)
     AND NOT EXISTS(SELECT 1 FROM public.material_bookmarks WHERE user_id=u.id)
     AND NOT EXISTS(SELECT 1 FROM public.user_calendar_saved WHERE user_id=u.id)
   THEN
     UPDATE public.users SET private_study_purged_at=clock_timestamp() WHERE id=u.id
       AND private_study_purged_at IS NULL;
     IF FOUND THEN
       INSERT INTO public.account_security_events(user_id,action,detail)
        VALUES(u.id,'closed_private_study_purged',jsonb_build_object('policy','private-study-extras-v1'));
       completed:=completed+1;
     END IF;
   END IF;
 END LOOP;
 RETURN jsonb_build_object('accounts_scanned',scanned,'accounts_completed',completed,'rows_removed',removed);
END $$;
REVOKE ALL ON FUNCTION sweep_expired_private_study(integer,integer) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION sweep_expired_private_study(integer,integer) TO mpsc;

-- Stale requests and workers cannot recreate private records after closure.
-- The existing account trigger locks the owner against concurrent closure.
CREATE TRIGGER private_study_account_active BEFORE INSERT OR UPDATE ON essay_drafts
 FOR EACH ROW EXECUTE FUNCTION active_account_record('user_id');
CREATE TRIGGER private_study_account_active BEFORE INSERT OR UPDATE ON user_question_bookmarks
 FOR EACH ROW EXECUTE FUNCTION active_account_record('user_id');
CREATE TRIGGER private_study_account_active BEFORE INSERT OR UPDATE ON material_bookmarks
 FOR EACH ROW EXECUTE FUNCTION active_account_record('user_id');
CREATE TRIGGER private_study_account_active BEFORE INSERT OR UPDATE ON user_calendar_saved
 FOR EACH ROW EXECUTE FUNCTION active_account_record('user_id');

CREATE FUNCTION private_study_purge_marker_guard() RETURNS trigger
LANGUAGE plpgsql SET search_path=pg_catalog,public AS $$
DECLARE changed boolean;
BEGIN
 IF TG_OP='INSERT' THEN changed:=NEW.private_study_purged_at IS NOT NULL;
 ELSE changed:=NEW.private_study_purged_at IS DISTINCT FROM OLD.private_study_purged_at;
 END IF;
 IF changed
   AND current_user<>(SELECT pg_get_userbyid(p.proowner) FROM pg_catalog.pg_proc p
     WHERE p.oid='public.sweep_expired_private_study(integer,integer)'::regprocedure)
 THEN RAISE EXCEPTION 'Private-study completion is operator managed'; END IF;
 RETURN NEW;
END $$;
REVOKE ALL ON FUNCTION private_study_purge_marker_guard() FROM PUBLIC;
CREATE TRIGGER private_study_purge_marker_guard BEFORE INSERT OR UPDATE OF private_study_purged_at ON users
 FOR EACH ROW EXECUTE FUNCTION private_study_purge_marker_guard();

COMMENT ON COLUMN users.private_study_purged_at IS
 'Completion of the separately gated private essay/bookmark/calendar-link cleanup; 0131 study-history completion alone does not certify it.';
COMMENT ON FUNCTION sweep_expired_private_study(integer,integer) IS
 'Bounded private writing and saved-link cleanup after base study cleanup, closure grace and holds; separately opt-in, never executed by migration application.';

COMMIT;
