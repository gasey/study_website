BEGIN;
CREATE TABLE reward_policy_versions (
 version text PRIMARY KEY, activated_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
INSERT INTO reward_policy_versions(version) VALUES('learning-v2-contribution');
CREATE TRIGGER immutable_reward_policy_version BEFORE UPDATE OR DELETE ON reward_policy_versions FOR EACH ROW EXECUTE FUNCTION review_immutable();
CREATE TABLE contribution_reward_claims (
 credit_id bigint PRIMARY KEY REFERENCES contribution_credit(id),
 publication_id text NOT NULL UNIQUE REFERENCES bank_publications(id),
 user_id text NOT NULL REFERENCES users(id), day date NOT NULL,
 ledger_id bigint NOT NULL UNIQUE REFERENCES reward_ledger(id)
);
CREATE TABLE contribution_reward_reversals (
 original_ledger_id bigint PRIMARY KEY REFERENCES reward_ledger(id),
 credit_id bigint NOT NULL UNIQUE REFERENCES contribution_credit(id),
 ledger_id bigint NOT NULL UNIQUE REFERENCES reward_ledger(id)
);
CREATE TRIGGER immutable_contribution_reward_claim BEFORE UPDATE OR DELETE ON contribution_reward_claims FOR EACH ROW EXECUTE FUNCTION review_immutable();
CREATE TRIGGER immutable_contribution_reward_reversal BEFORE UPDATE OR DELETE ON contribution_reward_reversals FOR EACH ROW EXECUTE FUNCTION review_immutable();
GRANT SELECT ON reward_policy_versions TO mpsc;
GRANT SELECT,INSERT ON contribution_reward_claims,contribution_reward_reversals TO mpsc;

CREATE FUNCTION reward_reviewer_eligible(reviewer text,author text,editor text,subject text,payload jsonb,baseline jsonb)
 RETURNS boolean LANGUAGE sql STABLE AS $$
 SELECT reviewer<>author AND reviewer<>editor
  AND EXISTS(SELECT 1 FROM review_grants g WHERE g.user_id=reviewer AND g.revoked_at IS NULL
    AND g.role IN ('owner','senior','reviewer') AND (g.subject_id IS NULL OR g.subject_id=subject))
  AND NOT EXISTS(SELECT 1 FROM (
    SELECT COALESCE(payload->'patch'->'classification'->>'subject_id',subject) AS sid
    UNION SELECT x->>'subject_id' FROM jsonb_array_elements(COALESCE(NULLIF(payload->'patch'->'relatedClassifications','null'::jsonb),'[]'::jsonb)) x
    UNION SELECT x->>'subject_id' FROM jsonb_array_elements(COALESCE(NULLIF(baseline->'record'->'relatedClassifications','null'::jsonb),'[]'::jsonb)) x
      WHERE payload->'patch' ?| ARRAY['classification','relatedClassifications']
  ) subjects WHERE sid IS NOT NULL AND NOT EXISTS(SELECT 1 FROM review_grants g WHERE g.user_id=reviewer
    AND g.revoked_at IS NULL AND g.role IN ('owner','senior','reviewer') AND (g.subject_id IS NULL OR g.subject_id=sid)))
$$;
CREATE OR REPLACE FUNCTION reward_contribution_credit() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE c bank_contributions%ROWTYPE; p bank_publications%ROWTYPE; r contribution_revisions%ROWTYPE;
 original reward_ledger%ROWTYPE; approvals integer; rejected boolean; senior boolean; needed integer;
 high boolean; spent integer; receipt bigint; day date;
BEGIN
 IF NEW.amount=0 OR NOT EXISTS(SELECT 1 FROM users WHERE id=NEW.user_id AND email IS NOT NULL) THEN RETURN NEW; END IF;
 PERFORM pg_advisory_xact_lock(hashtext('rewards:'||NEW.user_id));
 SELECT * INTO p FROM bank_publications WHERE id=NEW.publication_id;
 IF NEW.amount<0 THEN
   -- The publisher appends the negative credit before finalizing the reversion,
   -- in the same verified transaction. Reverse actual ledger amounts, including
   -- v1 receipts; a new tariff must never inflate or shrink an old reversal.
   SELECT l.* INTO original FROM contribution_credit cc JOIN reward_ledger l
     ON l.event_key='contribution-credit:'||cc.id AND l.user_id=cc.user_id
     WHERE cc.publication_id=p.manifest->'payload'->>'reverts_publication'
       AND cc.user_id=NEW.user_id AND cc.contribution_id=NEW.contribution_id
       AND cc.amount>0 AND NEW.amount=-cc.amount AND l.kind='contribution'
       AND NEW.event_key=p.id||':reversal:'||cc.publication_id ORDER BY l.id LIMIT 1;
   IF original.id IS NULL OR EXISTS(SELECT 1 FROM contribution_reward_reversals WHERE original_ledger_id=original.id)
     OR EXISTS(SELECT 1 FROM contribution_credit positive
       JOIN contribution_credit negative ON negative.user_id=positive.user_id AND negative.contribution_id=positive.contribution_id
         AND negative.amount=-positive.amount AND negative.id<>NEW.id
       JOIN bank_publications reversal ON reversal.id=negative.publication_id
         AND reversal.manifest->'payload'->>'reverts_publication'=positive.publication_id
       JOIN reward_ledger paid ON paid.event_key='contribution-credit:'||negative.id AND paid.user_id=negative.user_id
       WHERE original.event_key='contribution-credit:'||positive.id AND (paid.xp<0 OR paid.points<0)) THEN RETURN NEW; END IF;
   INSERT INTO reward_ledger(user_id,event_key,kind,xp,points,note,rule_version,reverses_id)
     VALUES(NEW.user_id,'contribution-credit:'||NEW.id,'contribution',-original.xp,-original.points,
       'Published contribution reward reversal','learning-v2',original.id) RETURNING id INTO receipt;
   INSERT INTO contribution_reward_reversals(original_ledger_id,credit_id,ledger_id) VALUES(original.id,NEW.id,receipt);
   RETURN NEW;
 END IF;
 SELECT * INTO c FROM bank_contributions WHERE id=NEW.contribution_id;
 SELECT * INTO r FROM contribution_revisions WHERE contribution_id=c.id AND revision=p.revision;
 IF c.author_id IS DISTINCT FROM NEW.user_id OR p.contribution_id IS DISTINCT FROM c.id
   OR p.state<>'applied' OR c.state<>'published' OR c.revision<>p.revision OR r.contribution_id IS NULL
   OR p.manifest->'payload' IS DISTINCT FROM r.payload OR p.manifest->'baseline' IS DISTINCT FROM r.baseline
   OR p.receipt->>'manifest_hash' IS DISTINCT FROM p.manifest_hash OR p.receipt->>'publication_id' IS DISTINCT FROM p.id
   OR jsonb_typeof(p.receipt->'after') IS DISTINCT FROM 'object' OR p.manifest->'payload'->>'reverts_publication' IS NOT NULL
   OR p.finished_at IS NULL OR p.finished_at<(SELECT activated_at FROM reward_policy_versions WHERE version='learning-v2-contribution')
   OR p.receipt->>'output_sha256' IS DISTINCT FROM (SELECT bank_checksum FROM sync_log WHERE finished_at IS NOT NULL ORDER BY id DESC LIMIT 1)
   OR EXISTS(SELECT 1 FROM admin_answer_decisions WHERE contribution_id=c.id)
   OR EXISTS(SELECT 1 FROM admin_bank_decisions WHERE contribution_id=c.id)
   OR EXISTS(SELECT 1 FROM contribution_events WHERE contribution_id=c.id AND actor_id='operator:owner-source-maintenance'
     AND action='operator_source_adjudication')
   OR EXISTS(SELECT 1 FROM contribution_reward_claims WHERE publication_id=p.id) THEN RETURN NEW; END IF;
 SELECT count(*) FILTER(WHERE d.decision='approve'),COALESCE(bool_or(d.decision<>'approve'),false),
   COALESCE(bool_or(d.decision='approve' AND EXISTS(SELECT 1 FROM review_grants g WHERE g.user_id=d.reviewer_id
     AND g.revoked_at IS NULL AND g.role IN ('owner','senior') AND (g.subject_id IS NULL OR g.subject_id=c.subject_id))),false)
   INTO approvals,rejected,senior FROM contribution_decisions d WHERE d.contribution_id=c.id AND d.revision=p.revision
     AND reward_reviewer_eligible(d.reviewer_id,c.author_id,r.actor_id,c.subject_id,r.payload,r.baseline)
     AND NOT EXISTS(SELECT 1 FROM contribution_revisions edited WHERE edited.contribution_id=c.id
       AND edited.revision<=p.revision AND edited.actor_id=d.reviewer_id);
 needed:=CASE WHEN c.kind IN ('answer','transcription','new_question','defect','duplicate') THEN 2 ELSE 1 END;
 IF approvals<needed OR rejected OR (r.baseline->'record'->>'answerSource' IN ('official','key')
    AND r.payload->'patch' ?| ARRAY['answerIndex','options','question','answerSource'] AND NOT senior) THEN RETURN NEW; END IF;
 day:=(now() AT TIME ZONE 'Asia/Kolkata')::date;
 SELECT count(*) INTO spent FROM reward_ledger WHERE user_id=NEW.user_id AND kind='contribution' AND points>0
   AND created_at>=day::timestamp AT TIME ZONE 'Asia/Kolkata' AND created_at<(day+1)::timestamp AT TIME ZONE 'Asia/Kolkata';
 IF spent>=3 THEN RETURN NEW; END IF;
 high:=c.kind IN ('answer','source_reference','source_request','transcription') AND approvals>=2 AND r.payload->'patch' ?| ARRAY['answerIndex','answerSource','answerKeyRef','sourceUrl','page','qnum','paperId'];
 INSERT INTO reward_profiles(user_id) VALUES(NEW.user_id) ON CONFLICT DO NOTHING;
 INSERT INTO reward_ledger(user_id,event_key,kind,xp,points,note,rule_version)
   VALUES(NEW.user_id,'contribution-credit:'||NEW.id,'contribution',CASE WHEN high THEN 40 ELSE 20 END,
     CASE WHEN high THEN 10 ELSE 5 END,'Independently reviewed live bank contribution','learning-v2') RETURNING id INTO receipt;
 INSERT INTO contribution_reward_claims(credit_id,publication_id,user_id,day,ledger_id) VALUES(NEW.id,p.id,NEW.user_id,day,receipt);
 RETURN NEW;
END $$;
COMMIT;
