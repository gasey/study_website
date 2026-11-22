BEGIN;

-- Read-only weighted views and admitted, server-owned immutable milestones.
CREATE OR REPLACE FUNCTION community_weighted_helpful(uid text) RETURNS numeric
LANGUAGE sql VOLATILE SET search_path=pg_catalog,public AS $$
 WITH gate AS MATERIALIZED (SELECT public.audience_database_gate_enabled() AS enabled)
 SELECT COALESCE(sum(CASE WHEN (SELECT count(*) FROM
   (SELECT 1 FROM attempts a WHERE a.user_id=v.user_id AND a.correct IS NOT NULL
     AND a.canonical_id IS NOT NULL LIMIT 50) scored)=50 THEN 1.0 ELSE 0.25 END),0)
 FROM post_votes v JOIN posts p ON p.id=v.post_id CROSS JOIN gate
 WHERE (NOT gate.enabled OR EXISTS(SELECT 1 FROM public.users target JOIN public.account_audience a ON a.user_id=target.id
   WHERE target.id=uid AND target.email IS NOT NULL AND target.closed_at IS NULL AND a.category='adult'))
 AND (NOT gate.enabled OR EXISTS(SELECT 1 FROM public.users voter JOIN public.account_audience a ON a.user_id=voter.id
   WHERE voter.id=v.user_id AND voter.email IS NOT NULL AND voter.closed_at IS NULL AND a.category='adult'))
 AND p.author_id=uid AND NOT p.hidden AND NOT p.needs_approval AND NOT p.before_fix
 AND v.user_id<>p.author_id AND EXISTS(SELECT 1 FROM users u WHERE u.id=v.user_id AND u.email IS NOT NULL)
 AND NOT EXISTS(SELECT 1 FROM creator_blocks b WHERE
   (b.user_id=v.user_id AND b.blocked_id=p.author_id) OR
   (b.user_id=p.author_id AND b.blocked_id=v.user_id))
$$;

CREATE OR REPLACE FUNCTION community_record_tier(uid text) RETURNS void
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE previous integer; earned integer; voter text;
BEGIN
 IF uid IS NULL THEN RETURN; END IF;
 -- Admission owns the policy row share lock even with the policy off. With it
 -- on, take the target lease before any blocking tier lock. Restriction/closure
 -- must not hold an exclusive account lease while waiting on this transaction.
 IF NOT public.audience_processing_admit(uid)
   OR NOT EXISTS(SELECT 1 FROM users WHERE id=uid AND email IS NOT NULL) THEN RETURN; END IF;
 PERFORM pg_advisory_xact_lock(hashtextextended('community-tier:'||uid,0));
 SELECT COALESCE(max((detail->>'rank')::integer),0) INTO previous
   FROM creator_events WHERE target_id=uid AND action='community_tier_earned';
 IF previous=4 THEN RETURN; END IF;
 -- The nested block releases every newly acquired voter lease on contention.
 -- The tier mutex freezes gain/loss writers for this author. All candidate
 -- voters are leased, even currently ineligible ones, before reading attempts;
 -- a busy candidate must never turn into a persisted partial weighted total.
 BEGIN
   IF public.audience_database_gate_enabled() THEN
     FOR voter IN SELECT DISTINCT v.user_id FROM post_votes v JOIN posts p ON p.id=v.post_id
       WHERE p.author_id=uid AND NOT p.hidden AND NOT p.needs_approval AND NOT p.before_fix
       AND v.user_id<>p.author_id AND NOT EXISTS(SELECT 1 FROM creator_blocks b WHERE
         (b.user_id=v.user_id AND b.blocked_id=p.author_id) OR
         (b.user_id=p.author_id AND b.blocked_id=v.user_id)) ORDER BY v.user_id LOOP
       IF NOT pg_try_advisory_xact_lock_shared(hashtextextended('audience-learning-processing-v1:'||voter,0)) THEN
         RAISE EXCEPTION 'Community voter processing is busy' USING ERRCODE='PFT01';
       END IF;
     END LOOP;
   END IF;
   earned:=community_tier_rank(community_weighted_helpful(uid));
   IF earned>previous THEN
     INSERT INTO creator_events(actor_id,action,target_id,detail)
     VALUES('system:community-tier-v1','community_tier_earned',uid,
       jsonb_build_object('rank',earned,'tier',(ARRAY['Helper','Regular','Mentor','Guide'])[earned],
         'policy_version','community-v2.2')) ON CONFLICT DO NOTHING;
   END IF;
 EXCEPTION WHEN SQLSTATE 'PFT01' THEN
   RETURN;
 END;
END $$;

CREATE OR REPLACE FUNCTION community_tier_change() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE ids text[]; uid text; voters text[]; capture boolean:=false; gate boolean; candidate text; admitted text[];
BEGIN
 gate:=public.audience_database_gate_enabled();
 IF TG_TABLE_NAME='post_votes' THEN
   IF TG_OP='UPDATE' AND ROW(OLD.post_id,OLD.user_id) IS NOT DISTINCT FROM ROW(NEW.post_id,NEW.user_id) THEN RETURN NEW; END IF;
   SELECT array_agg(DISTINCT author_id ORDER BY author_id) INTO ids FROM posts
     WHERE id IN (CASE WHEN TG_OP<>'INSERT' THEN OLD.post_id END,CASE WHEN TG_OP<>'DELETE' THEN NEW.post_id END);
   capture:=CASE WHEN TG_WHEN='BEFORE' THEN TG_OP<>'INSERT' ELSE TG_OP<>'DELETE' END;
 ELSIF TG_TABLE_NAME='posts' THEN
   IF ROW(OLD.hidden,OLD.needs_approval,OLD.before_fix) IS NOT DISTINCT FROM ROW(NEW.hidden,NEW.needs_approval,NEW.before_fix) THEN RETURN NEW; END IF;
   ids:=ARRAY[OLD.author_id];capture:=true;
 ELSIF TG_TABLE_NAME='creator_blocks' THEN
   ids:=CASE WHEN TG_OP='INSERT' THEN ARRAY[NEW.user_id,NEW.blocked_id] ELSE ARRAY[OLD.user_id,OLD.blocked_id] END;
   capture:=(TG_WHEN='BEFORE' AND TG_OP='INSERT') OR (TG_WHEN='AFTER' AND TG_OP='DELETE');
 ELSIF TG_TABLE_NAME='users' THEN
   IF (OLD.email IS NULL)=(NEW.email IS NULL)
     AND (NOT gate OR (OLD.closed_at IS NULL)=(NEW.closed_at IS NULL)) THEN RETURN NEW; END IF;
   voters:=ARRAY[OLD.id];capture:=true;
   IF gate THEN ids:=ARRAY[OLD.id]; END IF;
 ELSIF TG_TABLE_NAME='account_audience' THEN
   IF NOT gate THEN
     IF TG_OP='DELETE' THEN RETURN OLD; ELSE RETURN NEW; END IF;
   END IF;
   IF TG_OP='UPDATE' AND OLD.category=NEW.category THEN RETURN NEW; END IF;
   uid:=CASE WHEN TG_OP='DELETE' THEN OLD.user_id ELSE NEW.user_id END;
   ids:=ARRAY[uid];voters:=ARRAY[uid];capture:=true;
 ELSIF TG_TABLE_NAME='attempts' THEN
   IF TG_OP='UPDATE' AND ROW(OLD.user_id,OLD.correct IS NOT NULL,OLD.canonical_id IS NOT NULL)
     IS NOT DISTINCT FROM ROW(NEW.user_id,NEW.correct IS NOT NULL,NEW.canonical_id IS NOT NULL) THEN RETURN NEW; END IF;
   voters:=ARRAY[CASE WHEN TG_OP<>'INSERT' AND OLD.correct IS NOT NULL AND OLD.canonical_id IS NOT NULL THEN OLD.user_id END,
                 CASE WHEN TG_OP<>'DELETE' AND NEW.correct IS NOT NULL AND NEW.canonical_id IS NOT NULL THEN NEW.user_id END];
   -- Weights change only across 49/50 scored attempts, not on every answer.
   IF gate THEN
     -- Do not derive even the maturity-boundary count before voter admission.
     FOR candidate IN SELECT DISTINCT value FROM unnest(voters) value WHERE value IS NOT NULL ORDER BY value LOOP
       IF public.audience_processing_admit(candidate) THEN
         IF (SELECT count(*) FROM (SELECT 1 FROM attempts a WHERE a.user_id=candidate
           AND a.correct IS NOT NULL AND a.canonical_id IS NOT NULL LIMIT 51) scored) IN (49,50) THEN
           admitted:=array_append(admitted,candidate);
         END IF;
       END IF;
     END LOOP;
     voters:=admitted;
   ELSE
     SELECT array_agg(voter) INTO voters FROM unnest(voters) voter WHERE voter IS NOT NULL AND
       (SELECT count(*) FROM (SELECT 1 FROM attempts a WHERE a.user_id=voter
         AND a.correct IS NOT NULL AND a.canonical_id IS NOT NULL LIMIT 51) scored) IN (49,50);
   END IF;
   capture:=true;
 END IF;
 IF voters IS NOT NULL THEN
   SELECT array_agg(DISTINCT author ORDER BY author) INTO ids FROM (
     SELECT unnest(ids) AS author
     UNION SELECT p.author_id FROM post_votes v JOIN posts p ON p.id=v.post_id WHERE v.user_id=ANY(voters)
   ) affected;
 END IF;
 FOR uid IN SELECT DISTINCT value FROM unnest(ids) value WHERE value IS NOT NULL ORDER BY value LOOP
   IF NOT gate OR public.audience_processing_admit(uid) THEN
     PERFORM pg_advisory_xact_lock(hashtextextended('community-tier:'||uid,0));
     IF capture THEN PERFORM community_record_tier(uid); END IF;
   END IF;
 END LOOP;
 IF TG_OP='DELETE' THEN RETURN OLD; END IF;
 RETURN NEW;
END $$;

-- Declarations and closure affect both the author and every author whose votes
-- change weight. Capture current eligible standing BEFORE loss; AFTER observes
-- the new declaration. Existing immutable labels are never deleted or rewritten.
DROP TRIGGER community_tier_user_before ON users;
DROP TRIGGER community_tier_user_after ON users;
CREATE TRIGGER community_tier_user_before BEFORE UPDATE OF email,closed_at ON users
 FOR EACH ROW EXECUTE FUNCTION community_tier_change();
CREATE TRIGGER community_tier_user_after AFTER UPDATE OF email,closed_at ON users
 FOR EACH ROW EXECUTE FUNCTION community_tier_change();
CREATE TRIGGER community_tier_audience_before BEFORE INSERT OR UPDATE OR DELETE ON account_audience
 FOR EACH ROW EXECUTE FUNCTION community_tier_change();
CREATE TRIGGER community_tier_audience_after AFTER INSERT OR UPDATE OR DELETE ON account_audience
 FOR EACH ROW EXECUTE FUNCTION community_tier_change();

-- CREATE OR REPLACE retains original ownership and grants. No initialization,
-- historical replay, award, new table, client mint endpoint or session GUC.
COMMIT;
