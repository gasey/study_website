BEGIN;
-- One dated bank-review projection. Preserve every old schedule and receipt.
ALTER TABLE review_items ADD CONSTRAINT review_vocab_bank_identity
 CHECK(item_type<>'vocab' OR canonical_id IS NULL OR canonical_id=item_id);
CREATE INDEX review_items_vocab_due ON review_items(user_id,due_on,item_id)
 WHERE item_type='vocab' AND due_on IS NOT NULL;
-- Reuse recognition exposure history; no synthetic attempts, promotions or awards.
-- Existing question schedules can only bring a seeded vocabulary review earlier.
INSERT INTO review_items(user_id,item_type,item_id,canonical_id,box,due_on,last_result,last_attempt_id)
 SELECT s.user_id,'vocab',s.question_id,s.question_id,
 CASE WHEN s.score_version<>e.score_version OR s.appearance_version<>e.appearance_version
        OR s.appearance_id IS DISTINCT FROM e.primary_appearance_id
        OR old.last_result=false AND old.due_on<=(s.due_at AT TIME ZONE 'Asia/Kolkata')::date
      THEN 1 ELSE GREATEST(1,LEAST(5,s.stage)) END,
 CASE WHEN s.score_version<>e.score_version OR s.appearance_version<>e.appearance_version
        OR s.appearance_id IS DISTINCT FROM e.primary_appearance_id
      THEN (now() AT TIME ZONE 'Asia/Kolkata')::date
      ELSE LEAST((s.due_at AT TIME ZONE 'Asia/Kolkata')::date,old.due_on) END,
 s.stage>0 AND COALESCE(old.last_result,true),
 (SELECT max(a.id) FROM attempts a WHERE a.user_id=s.user_id AND a.canonical_id=s.question_id)
 FROM vocabulary_state s JOIN users u ON u.id=s.user_id AND u.email IS NOT NULL
 JOIN v_vocabulary_eligible e ON e.id=s.question_id AND e.focus='all'
 LEFT JOIN review_items old ON old.user_id=s.user_id AND old.item_type='question' AND old.item_id=s.question_id
 WHERE s.seen>0 ON CONFLICT DO NOTHING;
-- A canonical item is served once. A vocabulary schedule supersedes a retained
-- older question projection, including after graduation (due_on IS NULL).
CREATE VIEW v_bank_review_items AS
 SELECT DISTINCT ON(r.user_id,r.canonical_id) r.user_id,r.item_type,r.item_id,r.canonical_id,
 CASE WHEN stale.changed THEN 1 ELSE r.box END AS box,
 CASE WHEN stale.changed THEN (now() AT TIME ZONE 'Asia/Kolkata')::date ELSE r.due_on END AS due_on,
 CASE WHEN stale.changed THEN false ELSE r.last_result END AS last_result,r.last_attempt_id,r.updated_at
 FROM review_items r LEFT JOIN vocabulary_state s ON r.item_type='vocab' AND s.user_id=r.user_id AND s.question_id=r.canonical_id
 LEFT JOIN v_vocabulary_eligible current ON r.item_type='vocab' AND current.id=r.canonical_id AND current.focus='all'
 CROSS JOIN LATERAL(SELECT r.item_type='vocab' AND (s.score_version<>current.score_version OR s.appearance_version<>current.appearance_version
   OR s.appearance_id IS DISTINCT FROM current.primary_appearance_id) AS changed) stale
 WHERE r.canonical_id IS NOT NULL AND (r.item_type<>'vocab' OR EXISTS(
   SELECT 1 FROM v_vocabulary_eligible e WHERE e.id=r.canonical_id AND e.focus='all'))
 ORDER BY r.user_id,r.canonical_id,(r.item_type='vocab') DESC,r.item_type,r.item_id;
GRANT SELECT ON v_bank_review_items TO mpsc;
COMMIT;
