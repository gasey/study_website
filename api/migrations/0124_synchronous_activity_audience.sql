BEGIN;
-- Operator-controlled, database-wide policy. No declaration or consent is
-- inferred. Keep off until the remaining SQL award/tier paths are reviewed.
CREATE TABLE audience_processing_policy (
 singleton boolean PRIMARY KEY DEFAULT true CHECK(singleton),
 enabled boolean NOT NULL DEFAULT false
);
INSERT INTO audience_processing_policy(singleton,enabled) VALUES(true,false);
REVOKE ALL ON audience_processing_policy FROM PUBLIC,mpsc;
GRANT SELECT ON audience_processing_policy TO mpsc;

CREATE FUNCTION audience_database_gate_enabled() RETURNS boolean
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE gate boolean;
BEGIN
 SELECT enabled INTO gate FROM public.audience_processing_policy WHERE singleton;
 IF NOT FOUND THEN RAISE EXCEPTION 'Audience processing policy is missing'; END IF;
 RETURN gate;
END $$;

-- Independent publisher/maintenance sessions use the same lease domain as
-- API workers. Never wait while holding source/job/reward rows. The policy row
-- share lock also prevents an operator changing policy beneath this transaction.
CREATE FUNCTION audience_processing_admit(uid text,allow_guest boolean DEFAULT false) RETURNS boolean
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE gate boolean;
BEGIN
 SELECT enabled INTO gate FROM public.audience_processing_policy WHERE singleton FOR SHARE;
 IF NOT FOUND THEN RAISE EXCEPTION 'Audience processing policy is missing'; END IF;
 IF NOT gate THEN RETURN true; END IF;
 IF uid IS NULL OR NOT pg_try_advisory_xact_lock_shared(hashtextextended('audience-learning-processing-v1:'||uid,0)) THEN RETURN false; END IF;
 RETURN EXISTS(SELECT 1 FROM public.users u JOIN public.account_audience a ON a.user_id=u.id
   WHERE u.id=uid AND u.closed_at IS NULL AND a.category='adult'
   AND (u.email IS NOT NULL OR (allow_guest AND EXISTS(SELECT 1 FROM public.guest_credentials g
     WHERE g.user_id=u.id AND g.adopted_by IS NULL AND g.expires_at>now()))));
END $$;

-- API restrictions take the exclusive lease before row locks. A direct SQL
-- restriction already owns its row, so it must fail/retry rather than wait
-- behind a processor which may need that row. No lock-order inversion.
CREATE FUNCTION audience_restriction_guard() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE uid text; restricting boolean:=false;
BEGIN
 IF TG_TABLE_NAME='account_audience' THEN
   IF TG_OP='DELETE' THEN uid:=OLD.user_id;restricting:=OLD.category='adult';
   ELSIF TG_OP='INSERT' THEN uid:=NEW.user_id;restricting:=NEW.category='under18';
   ELSE
     IF NEW.user_id IS DISTINCT FROM OLD.user_id THEN RAISE EXCEPTION 'Audience subject cannot change'; END IF;
     uid:=NEW.user_id;restricting:=NEW.category='under18' AND OLD.category<>'under18';
   END IF;
 ELSE
   uid:=OLD.id;
   restricting:=(OLD.closed_at IS NULL AND NEW.closed_at IS NOT NULL)
     OR (OLD.email IS NOT NULL AND NEW.email IS NULL);
 END IF;
 IF restricting AND public.audience_database_gate_enabled() THEN
   IF NOT pg_try_advisory_xact_lock(hashtextextended('audience-learning-processing-v1:'||uid,0)) THEN
     RAISE EXCEPTION 'Account processing is busy; retry the restriction transaction' USING ERRCODE='55P03';
   END IF;
 END IF;
 IF TG_OP='DELETE' THEN RETURN OLD; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER audience_declaration_restriction BEFORE INSERT OR UPDATE OR DELETE ON account_audience
 FOR EACH ROW EXECUTE FUNCTION audience_restriction_guard();
CREATE TRIGGER audience_account_restriction BEFORE UPDATE OF email,closed_at ON users
 FOR EACH ROW EXECUTE FUNCTION audience_restriction_guard();

-- Ownership transfer is a processing action for both subjects. A plain SQL
-- adoption must not bypass the API's two-subject admission. Original attempts,
-- assessments and source corrections retain their existing integrity rules.
CREATE FUNCTION audience_attempt_transfer_guard() RETURNS trigger
LANGUAGE plpgsql SET search_path=pg_catalog,public AS $$
DECLARE uid text;
BEGIN
 IF NEW.user_id IS NOT DISTINCT FROM OLD.user_id THEN RETURN NEW; END IF;
 FOR uid IN SELECT DISTINCT value FROM unnest(ARRAY[OLD.user_id,NEW.user_id]) value ORDER BY value LOOP
   IF NOT public.audience_processing_admit(uid,uid=OLD.user_id) THEN
     RAISE EXCEPTION 'Account processing is paused; retry after eligibility review' USING ERRCODE='55000';
   END IF;
 END LOOP;
 RETURN NEW;
END $$;
CREATE TRIGGER audience_attempt_transfer BEFORE UPDATE OF user_id ON attempts
 FOR EACH ROW EXECUTE FUNCTION audience_attempt_transfer_guard();

-- Source attempts and durable queue hints remain. Restricted/busy synchronous
-- activity is deferred to the existing admitted learning reconciliation; no
-- new award, receipt, historical backfill or eager replay is introduced here.
CREATE OR REPLACE FUNCTION record_learning_activity(target bigint) RETURNS void
LANGUAGE plpgsql SET search_path=pg_catalog,public AS $$
DECLARE d record; uid text;
BEGIN
 SELECT user_id INTO uid FROM attempts WHERE id=target;
 IF NOT FOUND OR NOT public.audience_processing_admit(uid) THEN RETURN; END IF;
 SELECT a.*,COALESCE(qc.subject_id,'') AS subject_key,COALESCE(qc.subject_label,'') AS subject_label INTO d
 FROM attempts a JOIN users u ON u.id=a.user_id AND u.email IS NOT NULL
 LEFT JOIN question_classifications qc ON qc.question_id=a.canonical_id AND qc.review_status='approved'
 WHERE a.id=target;
 IF NOT FOUND THEN RETURN; END IF;
 INSERT INTO user_activity_daily(user_id,collection_key,section_key,subject_key,subject_label,day,answered,correct,last_active_at)
 VALUES(d.user_id,COALESCE(d.collection_id,''),COALESCE(d.section_path,''),d.subject_key,d.subject_label,
   (d.at AT TIME ZONE 'Asia/Kolkata')::date,1,d.correct::int,d.at)
 ON CONFLICT(user_id,collection_key,section_key,subject_key,day) DO UPDATE SET
   answered=user_activity_daily.answered+1,correct=user_activity_daily.correct+EXCLUDED.correct,
   subject_label=EXCLUDED.subject_label,last_active_at=GREATEST(user_activity_daily.last_active_at,EXCLUDED.last_active_at);
 IF d.canonical_id IS NOT NULL THEN
  INSERT INTO user_activity_questions VALUES(d.user_id,COALESCE(d.collection_id,''),COALESCE(d.section_path,''),d.subject_key,d.canonical_id)
  ON CONFLICT DO NOTHING;
 END IF;
END $$;

REVOKE ALL ON FUNCTION audience_database_gate_enabled(),audience_processing_admit(text,boolean),
 audience_restriction_guard(),audience_attempt_transfer_guard() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION audience_database_gate_enabled(),audience_processing_admit(text,boolean) TO mpsc;
COMMIT;
