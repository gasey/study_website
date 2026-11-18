BEGIN;

-- Votes/weights remain computed. The only persisted display state is a label
-- milestone in the existing immutable audit, never a vote balance or currency.
CREATE UNIQUE INDEX creator_tier_once ON creator_events(target_id,(detail->>'rank'))
 WHERE action='community_tier_earned';

CREATE FUNCTION community_weighted_helpful(uid text) RETURNS numeric
LANGUAGE sql VOLATILE SET search_path=pg_catalog,public AS $$
 SELECT COALESCE(sum(CASE WHEN (SELECT count(*) FROM
   (SELECT 1 FROM attempts a WHERE a.user_id=v.user_id AND a.correct IS NOT NULL
     AND a.canonical_id IS NOT NULL LIMIT 50) scored)=50 THEN 1.0 ELSE 0.25 END),0)
 FROM post_votes v JOIN posts p ON p.id=v.post_id
 WHERE p.author_id=uid AND NOT p.hidden AND NOT p.needs_approval AND NOT p.before_fix
 AND v.user_id<>p.author_id AND EXISTS(SELECT 1 FROM users u WHERE u.id=v.user_id AND u.email IS NOT NULL)
 AND NOT EXISTS(SELECT 1 FROM creator_blocks b WHERE
   (b.user_id=v.user_id AND b.blocked_id=p.author_id) OR
   (b.user_id=p.author_id AND b.blocked_id=v.user_id))
$$;

CREATE FUNCTION community_tier_rank(score numeric) RETURNS integer
LANGUAGE sql IMMUTABLE SET search_path=pg_catalog,public AS $$
 SELECT CASE WHEN score>=150 THEN 4 WHEN score>=50 THEN 3
   WHEN score>=25 THEN 2 WHEN score>=10 THEN 1 ELSE 0 END
$$;

CREATE FUNCTION community_display_tier_rank(uid text) RETURNS integer
LANGUAGE sql VOLATILE SET search_path=pg_catalog,public AS $$
 SELECT GREATEST(community_tier_rank(community_weighted_helpful(uid)),
   COALESCE((SELECT max((detail->>'rank')::integer) FROM creator_events
     WHERE target_id=uid AND action='community_tier_earned'),0))
$$;

CREATE FUNCTION community_record_tier(uid text) RETURNS void
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE previous integer; earned integer;
BEGIN
 IF uid IS NULL OR NOT EXISTS(SELECT 1 FROM users WHERE id=uid AND email IS NOT NULL) THEN RETURN; END IF;
 PERFORM pg_advisory_xact_lock(hashtextextended('community-tier:'||uid,0));
 SELECT COALESCE(max((detail->>'rank')::integer),0) INTO previous
   FROM creator_events WHERE target_id=uid AND action='community_tier_earned';
 IF previous=4 THEN RETURN; END IF;
 earned:=community_tier_rank(community_weighted_helpful(uid));
 IF earned>previous THEN
   INSERT INTO creator_events(actor_id,action,target_id,detail)
   VALUES('system:community-tier-v1','community_tier_earned',uid,
     jsonb_build_object('rank',earned,'tier',(ARRAY['Helper','Regular','Mentor','Guide'])[earned],
       'policy_version','community-v2.2')) ON CONFLICT DO NOTHING;
 END IF;
END $$;

-- The app's pre-existing audit INSERT grant must not permit forged tier labels.
CREATE FUNCTION community_tier_event_guard() RETURNS trigger
LANGUAGE plpgsql SET search_path=pg_catalog,public AS $$
BEGIN
 IF NEW.action='community_tier_earned' AND current_user<>
   (SELECT pg_get_userbyid(proowner) FROM pg_proc WHERE oid='community_record_tier(text)'::regprocedure)
 THEN RAISE EXCEPTION 'community tier history is server-owned' USING ERRCODE='42501'; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER creator_tier_event_guard BEFORE INSERT ON creator_events
 FOR EACH ROW EXECUTE FUNCTION community_tier_event_guard();

-- Lock affected authors in one order before every gain/loss. Existing web vote
-- routes already lock their post first. No user/post rows are locked from here.
-- Capture before a decrease and after a gain: a read never writes audit state.
CREATE FUNCTION community_tier_change() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE ids text[]; uid text; voters text[]; capture boolean:=false;
BEGIN
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
   IF (OLD.email IS NULL)=(NEW.email IS NULL) THEN RETURN NEW; END IF;
   voters:=ARRAY[OLD.id];capture:=true;
 ELSIF TG_TABLE_NAME='attempts' THEN
   IF TG_OP='UPDATE' AND ROW(OLD.user_id,OLD.correct IS NOT NULL,OLD.canonical_id IS NOT NULL)
     IS NOT DISTINCT FROM ROW(NEW.user_id,NEW.correct IS NOT NULL,NEW.canonical_id IS NOT NULL) THEN RETURN NEW; END IF;
   voters:=ARRAY[CASE WHEN TG_OP<>'INSERT' AND OLD.correct IS NOT NULL AND OLD.canonical_id IS NOT NULL THEN OLD.user_id END,
                 CASE WHEN TG_OP<>'DELETE' AND NEW.correct IS NOT NULL AND NEW.canonical_id IS NOT NULL THEN NEW.user_id END];
   -- Weights change only across 49/50 scored attempts, not on every answer.
   SELECT array_agg(voter) INTO voters FROM unnest(voters) voter WHERE voter IS NOT NULL AND
     (SELECT count(*) FROM (SELECT 1 FROM attempts a WHERE a.user_id=voter
       AND a.correct IS NOT NULL AND a.canonical_id IS NOT NULL LIMIT 51) scored) IN (49,50);
   capture:=true;
 END IF;
 IF voters IS NOT NULL THEN
   SELECT array_agg(DISTINCT p.author_id ORDER BY p.author_id) INTO ids
     FROM post_votes v JOIN posts p ON p.id=v.post_id WHERE v.user_id=ANY(voters);
 END IF;
 FOR uid IN SELECT DISTINCT value FROM unnest(ids) value WHERE value IS NOT NULL ORDER BY value LOOP
   PERFORM pg_advisory_xact_lock(hashtextextended('community-tier:'||uid,0));
   IF capture THEN PERFORM community_record_tier(uid); END IF;
 END LOOP;
 IF TG_OP='DELETE' THEN RETURN OLD; END IF;
 RETURN NEW;
END $$;

CREATE TRIGGER community_tier_vote_before BEFORE INSERT OR UPDATE OR DELETE ON post_votes
 FOR EACH ROW EXECUTE FUNCTION community_tier_change();
CREATE TRIGGER community_tier_vote_after AFTER INSERT OR UPDATE OR DELETE ON post_votes
 FOR EACH ROW EXECUTE FUNCTION community_tier_change();
CREATE TRIGGER community_tier_post_before BEFORE UPDATE OF hidden,needs_approval,before_fix ON posts
 FOR EACH ROW EXECUTE FUNCTION community_tier_change();
CREATE TRIGGER community_tier_post_after AFTER UPDATE OF hidden,needs_approval,before_fix ON posts
 FOR EACH ROW EXECUTE FUNCTION community_tier_change();
CREATE TRIGGER community_tier_block_before BEFORE INSERT OR DELETE ON creator_blocks
 FOR EACH ROW EXECUTE FUNCTION community_tier_change();
CREATE TRIGGER community_tier_block_after AFTER INSERT OR DELETE ON creator_blocks
 FOR EACH ROW EXECUTE FUNCTION community_tier_change();
CREATE TRIGGER community_tier_user_before BEFORE UPDATE OF email ON users
 FOR EACH ROW EXECUTE FUNCTION community_tier_change();
CREATE TRIGGER community_tier_user_after AFTER UPDATE OF email ON users
 FOR EACH ROW EXECUTE FUNCTION community_tier_change();
CREATE TRIGGER community_tier_attempt_before BEFORE INSERT OR UPDATE OR DELETE ON attempts
 FOR EACH ROW EXECUTE FUNCTION community_tier_change();
CREATE TRIGGER community_tier_attempt_after AFTER INSERT OR UPDATE OR DELETE ON attempts
 FOR EACH ROW EXECUTE FUNCTION community_tier_change();

REVOKE ALL ON FUNCTION community_record_tier(text),community_tier_change(),community_tier_event_guard() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION community_weighted_helpful(text),community_tier_rank(numeric),community_display_tier_rank(text) TO mpsc;

-- Initialize labels from actual current votes only; no claimed past peak and no
-- learner notification, synthetic activity, points or reward rows are created.
DO $$ DECLARE uid text; BEGIN
 FOR uid IN SELECT DISTINCT author_id FROM posts p JOIN post_votes v ON v.post_id=p.id ORDER BY author_id LOOP
   PERFORM community_record_tier(uid);
 END LOOP;
END $$;
COMMIT;
