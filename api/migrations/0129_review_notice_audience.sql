BEGIN;
-- Prospective optional contribution/CMS workflow notices, including independent
-- publisher SQL. Source decisions, publication/audit/credit records, exact reward
-- corrections and existing private notice history retain their own scope.
CREATE FUNCTION audience_review_notice_recipient() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public,pg_temp AS $$
DECLARE gate boolean;
BEGIN
 IF NEW.contribution_id IS NULL AND NEW.material_id IS NULL THEN RETURN NEW; END IF;
 -- Missing operator policy suppresses this optional notice rather than rolling
 -- back a legitimate archive/reversal or source/audit transaction. Never infer
 -- permission from session settings. Hold policy agreement through source commit.
 SELECT enabled INTO gate FROM public.audience_processing_policy WHERE singleton FOR SHARE;
 IF NOT FOUND THEN RETURN NULL; END IF;
 IF gate AND NOT public.audience_processing_admit(NEW.user_id) THEN RETURN NULL; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER audience_review_notice_recipient BEFORE INSERT ON review_notifications
 FOR EACH ROW EXECUTE FUNCTION audience_review_notice_recipient();
REVOKE ALL ON FUNCTION audience_review_notice_recipient() FROM PUBLIC,mpsc;
-- No history update/delete, queue, backfill, client mint function or new table.
COMMIT;
