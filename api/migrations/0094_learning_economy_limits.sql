-- V.4, limits and dark catalog only. No historical awards or counter backfill.
BEGIN;
CREATE FUNCTION reward_pillar(key text) RETURNS text LANGUAGE sql IMMUTABLE AS $$
 SELECT CASE split_part(key,':',1)
  WHEN 'question' THEN 'learn' WHEN 'review' THEN 'revise'
  WHEN 'mock' THEN 'prove' WHEN 'game' THEN 'play' WHEN 'daily' THEN 'daily'
  WHEN 'quest' THEN 'habit' WHEN 'mastery' THEN 'milestone' ELSE 'other' END
$$;
CREATE FUNCTION reward_pillar_cap(pillar text) RETURNS integer LANGUAGE sql IMMUTABLE AS $$
 SELECT CASE pillar WHEN 'learn' THEN 12 WHEN 'revise' THEN 4 WHEN 'prove' THEN 3
  WHEN 'play' THEN 4 WHEN 'daily' THEN 1 WHEN 'habit' THEN 10 ELSE NULL END
$$;
CREATE TABLE reward_daily_counters (
 user_id text NOT NULL REFERENCES users(id), day date NOT NULL,
 xp integer NOT NULL DEFAULT 0 CHECK(xp>=0), points integer NOT NULL DEFAULT 0 CHECK(points>=0),
 pillar_points jsonb NOT NULL DEFAULT '{}', PRIMARY KEY(user_id,day)
);
-- Serialize with every existing award writer. Initialize on first *new* event
-- from that day's actual immutable ledger, including pre-cutover receipts.
-- Counting happens AFTER INSERT: ON CONFLICT retries cannot consume a budget.
CREATE FUNCTION limit_learning_reward() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE d date; p text; cap integer; c reward_daily_counters%ROWTYPE;
BEGIN
 IF NEW.kind NOT IN ('study','game') OR NEW.xp<0 OR NEW.points<0 THEN RETURN NEW; END IF;
 PERFORM pg_advisory_xact_lock(hashtext('rewards:'||NEW.user_id));
 IF EXISTS(SELECT 1 FROM reward_ledger WHERE event_key=NEW.event_key) THEN RETURN NEW; END IF;
 d:=(NEW.created_at AT TIME ZONE 'Asia/Kolkata')::date;
 INSERT INTO reward_daily_counters(user_id,day,xp,points,pillar_points)
 SELECT NEW.user_id,d,COALESCE(sum(xp),0),COALESCE(sum(points),0),
   COALESCE(jsonb_object_agg(pillar,points),'{}'::jsonb)
 FROM (SELECT reward_pillar(event_key) AS pillar,sum(GREATEST(xp,0))::integer AS xp,
   sum(GREATEST(points,0))::integer AS points FROM reward_ledger
   WHERE user_id=NEW.user_id AND kind IN ('study','game')
     AND created_at>=d::timestamp AT TIME ZONE 'Asia/Kolkata'
     AND created_at<(d+1)::timestamp AT TIME ZONE 'Asia/Kolkata'
   GROUP BY reward_pillar(event_key)) earned
 ON CONFLICT DO NOTHING;
 SELECT * INTO c FROM reward_daily_counters WHERE user_id=NEW.user_id AND day=d FOR UPDATE;
 p:=reward_pillar(NEW.event_key); cap:=reward_pillar_cap(p);
 NEW.xp:=LEAST(NEW.xp,GREATEST(0,300-c.xp));
 NEW.points:=LEAST(NEW.points,GREATEST(0,25-c.points));
 IF cap IS NOT NULL THEN NEW.points:=LEAST(NEW.points,GREATEST(0,cap-COALESCE((c.pillar_points->>p)::integer,0))); END IF;
 NEW.rule_version:='learning-v2';
 RETURN NEW;
END $$;
CREATE FUNCTION count_learning_reward() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE d date; p text;
BEGIN
 IF NEW.kind NOT IN ('study','game') OR NEW.xp<0 OR NEW.points<0 THEN RETURN NEW; END IF;
 d:=(NEW.created_at AT TIME ZONE 'Asia/Kolkata')::date; p:=reward_pillar(NEW.event_key);
 UPDATE reward_daily_counters SET xp=xp+NEW.xp,points=points+NEW.points,
  pillar_points=jsonb_set(pillar_points,ARRAY[p],to_jsonb(COALESCE((pillar_points->>p)::integer,0)+NEW.points))
 WHERE user_id=NEW.user_id AND day=d;
 RETURN NEW;
END $$;
CREATE TRIGGER enforce_learning_v2 BEFORE INSERT ON reward_ledger FOR EACH ROW EXECUTE FUNCTION limit_learning_reward();
CREATE TRIGGER track_learning_v2 AFTER INSERT ON reward_ledger FOR EACH ROW EXECUTE FUNCTION count_learning_reward();
GRANT SELECT,INSERT,UPDATE ON reward_daily_counters TO mpsc;

-- Owner-approved prices. Opening redemption remains a separate, gated action.
UPDATE reward_catalog SET points=400,enabled=false,version=version+1,updated_at=now() WHERE id='pro-week';
INSERT INTO reward_catalog(id,title,points,pro_days,enabled) VALUES('pro-month','30 days of Pro',1500,30,false);
COMMIT;
