BEGIN;

-- The 30-day grace path keeps only the formerly verified identity needed to
-- return access. Personal identity is encrypted; the keyed digest supports
-- collision-safe lookup without storing a searchable email address.
CREATE TABLE account_closure_recovery (
 user_id text PRIMARY KEY REFERENCES users(id),
 email_hash text NOT NULL UNIQUE,
 identity_cipher text NOT NULL,
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 expires_at timestamptz NOT NULL
);
CREATE INDEX account_closure_recovery_expiry ON account_closure_recovery(expires_at,user_id);
GRANT SELECT,INSERT,UPDATE,DELETE ON account_closure_recovery TO mpsc;

ALTER TABLE account_email_tokens DROP CONSTRAINT account_email_tokens_purpose_check;
ALTER TABLE account_email_tokens ADD CONSTRAINT account_email_tokens_purpose_check
 CHECK(purpose IN ('verify','reset','reopen'));

CREATE FUNCTION queue_account_reopen_link(
 p_user text,p_email_hash text,p_token_hash text,p_token_cipher text
) RETURNS boolean LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE ended timestamptz; stored_hash text; deadline timestamptz;
BEGIN
 SELECT u.closed_at INTO ended FROM public.users u WHERE u.id=p_user FOR UPDATE;
 SELECT r.email_hash,r.expires_at INTO stored_hash,deadline
  FROM public.account_closure_recovery r WHERE r.user_id=p_user FOR UPDATE;
 IF ended IS NULL OR ended+interval '30 days'<=clock_timestamp()
   OR stored_hash IS NULL OR stored_hash<>p_email_hash OR deadline<=clock_timestamp()
   OR length(p_token_hash)<>64 OR length(p_token_cipher)<1
 THEN RETURN false; END IF;
 UPDATE public.account_email_tokens SET consumed_at=clock_timestamp()
  WHERE user_id=p_user AND purpose='reopen' AND consumed_at IS NULL;
 INSERT INTO public.account_email_tokens(token_hash,user_id,purpose,expires_at)
  VALUES(p_token_hash,p_user,'reopen',least(clock_timestamp()+interval '30 minutes',ended+interval '30 days'));
 INSERT INTO public.account_mail_outbox(user_id,purpose,token_cipher)
  VALUES(p_user,'reopen',p_token_cipher);
 RETURN true;
END $$;
REVOKE ALL ON FUNCTION queue_account_reopen_link(text,text,text,text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION queue_account_reopen_link(text,text,text,text) TO mpsc;

CREATE OR REPLACE FUNCTION active_account_record() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE ended timestamptz; queue_owner name; reopen_owner name;
BEGIN
 EXECUTE 'SELECT closed_at FROM users WHERE id=$1 FOR SHARE'
 INTO ended USING to_jsonb(NEW)->>TG_ARGV[0];
 IF ended IS NOT NULL THEN
   SELECT pg_get_userbyid(p.proowner) INTO queue_owner FROM pg_catalog.pg_proc p
    WHERE p.oid='public.queue_account_reopen_link(text,text,text,text)'::regprocedure;
   SELECT pg_get_userbyid(p.proowner) INTO reopen_owner FROM pg_catalog.pg_proc p
    WHERE p.oid='public.reopen_closed_account(text,text,text,text,text,jsonb,text)'::regprocedure;
   IF TG_TABLE_NAME='account_email_tokens' THEN
     IF NEW.purpose='reopen' AND current_user IN (queue_owner,reopen_owner)
       AND NEW.expires_at<=ended+interval '30 days'
       AND EXISTS(SELECT 1 FROM account_closure_recovery r
         WHERE r.user_id=(to_jsonb(NEW)->>TG_ARGV[0]) AND r.expires_at>clock_timestamp())
     THEN RETURN NEW; END IF;
   END IF;
   RAISE EXCEPTION 'Account is closed';
 END IF;
 RETURN NEW;
END $$;

CREATE FUNCTION reopen_closed_account(
 p_token_hash text,p_email text,p_email_hash text,p_password_hash text,
 p_name text,p_avatar jsonb,p_handle text
) RETURNS text LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE uid text; ended timestamptz; stored_hash text; deadline timestamptz;
        final_handle text; function_owner name;
BEGIN
 -- Read the token's owner without taking a token lock first. Closure locks the
 -- user before consuming tokens, so all competing paths use user -> token.
 PERFORM pg_advisory_xact_lock(hashtextextended('account-email-owner:'||lower(p_email),0));
 SELECT t.user_id INTO uid FROM public.account_email_tokens t
  WHERE t.token_hash=p_token_hash AND t.purpose='reopen'
    AND t.consumed_at IS NULL AND t.expires_at>clock_timestamp();
 IF uid IS NULL THEN RAISE EXCEPTION 'Invalid or expired account-reopen link'; END IF;
 SELECT u.closed_at INTO ended FROM public.users u WHERE u.id=uid FOR UPDATE;
 IF ended IS NULL OR ended+interval '30 days'<=clock_timestamp() THEN
   RAISE EXCEPTION 'Account-reopen period has expired';
 END IF;
 SELECT t.user_id INTO uid FROM public.account_email_tokens t
  WHERE t.token_hash=p_token_hash AND t.purpose='reopen'
    AND t.consumed_at IS NULL AND t.expires_at>clock_timestamp() FOR UPDATE;
 IF uid IS NULL THEN RAISE EXCEPTION 'Invalid or expired account-reopen link'; END IF;
 SELECT r.email_hash,r.expires_at INTO stored_hash,deadline
  FROM public.account_closure_recovery r WHERE r.user_id=uid FOR UPDATE;
 IF stored_hash IS NULL OR stored_hash<>p_email_hash OR deadline<=clock_timestamp()
   OR p_email IS NULL OR p_password_hash IS NULL THEN
   RAISE EXCEPTION 'Account-reopen information has expired';
 END IF;
 IF EXISTS(SELECT 1 FROM public.users u WHERE lower(u.email)=lower(p_email) AND u.id<>uid) THEN
   RAISE EXCEPTION 'The email address is already in use';
 END IF;
 final_handle:=p_handle;
 IF final_handle IS NULL OR EXISTS(SELECT 1 FROM public.users u WHERE lower(u.handle)=lower(final_handle) AND u.id<>uid) THEN
   final_handle:='learner-'||substr(md5(uid),1,12);
 END IF;
 UPDATE public.account_email_tokens SET consumed_at=clock_timestamp()
  WHERE user_id=uid AND purpose='reopen' AND consumed_at IS NULL;
 UPDATE public.users SET closed_at=NULL,email=p_email,email_verified_at=clock_timestamp(),
   password_hash=p_password_hash,name=p_name,avatar=p_avatar,handle=final_handle,
   avatar_version=avatar_version+1,identity_version=identity_version+1
  WHERE id=uid;
 DELETE FROM public.account_closure_recovery WHERE user_id=uid;
 INSERT INTO public.account_security_events(user_id,action)
  VALUES(uid,'account_reopened');
 RETURN uid;
END $$;
REVOKE ALL ON FUNCTION reopen_closed_account(text,text,text,text,text,jsonb,text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION reopen_closed_account(text,text,text,text,text,jsonb,text) TO mpsc;

CREATE OR REPLACE FUNCTION closed_identity_stays_anonymous() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE function_owner name;
BEGIN
 IF OLD.closed_at IS NOT NULL AND
   (NEW.closed_at,NEW.email,NEW.password_hash,NEW.name,NEW.handle,NEW.avatar,NEW.email_verified_at,NEW.contribution_public)
     IS DISTINCT FROM
   (OLD.closed_at,OLD.email,OLD.password_hash,OLD.name,OLD.handle,OLD.avatar,OLD.email_verified_at,OLD.contribution_public)
 THEN
   SELECT pg_get_userbyid(p.proowner) INTO function_owner FROM pg_catalog.pg_proc p
    WHERE p.oid='public.reopen_closed_account(text,text,text,text,text,jsonb,text)'::regprocedure;
   IF NEW.closed_at IS NULL AND current_user=function_owner THEN RETURN NEW; END IF;
   RAISE EXCEPTION 'Closed accounts cannot restore an identity';
 END IF;
 RETURN NEW;
END $$;

COMMIT;
