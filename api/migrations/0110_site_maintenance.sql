BEGIN;
-- One owner-managed setting. Immutable audit uses account_security_events.
CREATE TABLE site_notice (
 singleton boolean PRIMARY KEY DEFAULT true CHECK(singleton),
 message text NOT NULL DEFAULT '' CHECK(length(message)<=500),
 expires_at timestamptz,version integer NOT NULL DEFAULT 1 CHECK(version>0),
 updated_by text REFERENCES users(id),updated_at timestamptz NOT NULL DEFAULT now()
);
INSERT INTO site_notice(singleton) VALUES(true);
GRANT SELECT,UPDATE ON site_notice TO mpsc;
GRANT DELETE ON auth_sessions,mobile_sessions,rate_limits,review_rate_buckets,
 auth_login_attempts,google_auth_flows,mobile_auth_flows TO mpsc;
CREATE INDEX retention_rate_limits_day ON rate_limits(ist_date,user_id,action);
CREATE INDEX retention_guest_expiry ON guest_credentials(expires_at,user_id) WHERE adopted_by IS NULL;

-- No broad user/guest DELETE grant. This narrow function can remove at most20
-- generated guests whose last possible credential use was over12months ago.
-- It refuses ALL linked data, including unknown future FKs and legacy text IDs.
CREATE FUNCTION sweep_empty_guests(apply_changes boolean DEFAULT false)
 RETURNS TABLE(scanned integer,eligible integer,removed integer)
 LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $$
DECLARE candidate record;ref record;item jsonb;linked boolean;keep boolean;
 guards text:='';refs jsonb:='[]';base text;
BEGIN
 scanned:=0;eligible:=0;removed:=0;
 base:='SELECT u.id FROM public.users u JOIN public.guest_credentials g ON g.user_id=u.id
   WHERE u.id ~ ''^guest_[0-9a-f]{32}$'' AND u.email IS NULL AND u.closed_at IS NULL
    AND u.role=''learner'' AND u.created_at<now()-interval ''12 months''
    AND g.adopted_by IS NULL AND g.created_at<now()-interval ''12 months''
    AND g.expires_at<now()-interval ''12 months''';
 -- Avoid catalog/planner work on an ordinary empty cycle.
 EXECUTE 'SELECT EXISTS('||base||')' INTO linked;
 IF NOT linked THEN RETURN NEXT;RETURN;END IF;
 FOR ref IN
  SELECT DISTINCT n.nspname,c.relname,format('r.%I=u.id',a.attname) AS predicate
   FROM pg_catalog.pg_attribute a JOIN pg_catalog.pg_class c ON c.oid=a.attrelid
   JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
   JOIN pg_catalog.pg_type t ON t.oid=a.atttypid
   WHERE n.nspname='public' AND c.relkind IN ('r','p') AND a.attnum>0 AND NOT a.attisdropped
    AND t.typcategory='S' AND (a.attname ~ '(_id|_by)$' OR a.attname='target_user')
    AND NOT(c.relname='guest_credentials' AND a.attname='user_id')
  UNION
  SELECT n.nspname,c.relname,
    string_agg(format('r.%I=u.%I',a.attname,b.attname),' AND ' ORDER BY keys.ord) AS predicate
   FROM pg_catalog.pg_constraint fk JOIN pg_catalog.pg_class c ON c.oid=fk.conrelid
   JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
   CROSS JOIN LATERAL unnest(fk.conkey,fk.confkey) WITH ORDINALITY keys(local_key,remote_key,ord)
   JOIN pg_catalog.pg_attribute a ON a.attrelid=c.oid AND a.attnum=keys.local_key
   JOIN pg_catalog.pg_attribute b ON b.attrelid=fk.confrelid AND b.attnum=keys.remote_key
   WHERE fk.contype='f' AND fk.confrelid='public.users'::regclass
    AND NOT(n.nspname='public' AND c.relname='guest_credentials' AND a.attname='user_id')
   GROUP BY fk.oid,n.nspname,c.relname
 LOOP
  guards:=guards||format(' AND NOT EXISTS(SELECT 1 FROM %I.%I r WHERE %s)',ref.nspname,ref.relname,ref.predicate);
  refs:=refs||jsonb_build_array(jsonb_build_object('schema',ref.nspname,'table',ref.relname,'predicate',ref.predicate));
 END LOOP;
 -- Filter linked data before LIMIT, so protected old guests cannot starve
 -- newer empty accounts. Only20 data-free candidates are ever locked.
 FOR candidate IN EXECUTE base||guards||' ORDER BY g.expires_at,u.id LIMIT 20' ||
   CASE WHEN apply_changes THEN ' FOR UPDATE OF u,g SKIP LOCKED' ELSE '' END
 LOOP
  scanned:=scanned+1;keep:=false;
  -- A fresh snapshot under the locks catches references committed while we
  -- waited. Full composite/alternate-key joins preserve their exact owners.
  FOR item IN SELECT value FROM jsonb_array_elements(refs)
  LOOP
   EXECUTE format('SELECT EXISTS(SELECT 1 FROM %I.%I r JOIN public.users u ON %s WHERE u.id=$1)',
     item->>'schema',item->>'table',item->>'predicate') INTO linked USING candidate.id;
   IF linked THEN keep:=true;EXIT;END IF;
  END LOOP;
  IF NOT keep THEN
   eligible:=eligible+1;
   IF apply_changes THEN
    BEGIN
     DELETE FROM public.guest_credentials WHERE user_id=candidate.id;
     DELETE FROM public.users WHERE id=candidate.id;
     removed:=removed+1;
    EXCEPTION WHEN foreign_key_violation THEN
     NULL;
    END;
   END IF;
  END IF;
 END LOOP;
 RETURN NEXT;
END;
$$;
REVOKE ALL ON FUNCTION sweep_empty_guests(boolean) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION sweep_empty_guests(boolean) TO mpsc;
COMMIT;
