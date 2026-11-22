BEGIN;

-- The owner approved a conservative local scope: personal practice/mock/review,
-- vocabulary/map answers, and derived progress after the existing 30-day reopen
-- window. This remains opt-in and is never run by migration application.
ALTER TABLE users ADD COLUMN study_history_purged_at timestamptz;
CREATE INDEX users_closed_study_history_pending
 ON users(closed_at,id) WHERE closed_at IS NOT NULL AND study_history_purged_at IS NULL;

-- A restricted operator can hold one account while a dispute or review is open.
-- The API role can read holds through the definer worker but cannot create them.
CREATE TABLE account_study_history_holds (
 user_id text NOT NULL REFERENCES users(id),
 hold_code text NOT NULL CHECK(hold_code IN ('legal','dispute','security','manual_review')),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 expires_at timestamptz,
 released_at timestamptz,
 PRIMARY KEY(user_id,created_at),
 CHECK(expires_at IS NULL OR expires_at>created_at),
 CHECK(released_at IS NULL OR released_at>=created_at)
);
CREATE INDEX account_study_history_holds_active ON account_study_history_holds(user_id,expires_at)
 WHERE released_at IS NULL;
REVOKE ALL ON account_study_history_holds FROM PUBLIC,mpsc;

-- Preserve economic receipts while removing their direct answer/session FK.
-- Canonical question claims remain as anti-replay evidence under the separate
-- rewards schedule; they are deliberately outside the study-history deletion.
ALTER TABLE reward_question_claims ALTER COLUMN attempt_id DROP NOT NULL;
ALTER TABLE reward_question_claims DROP CONSTRAINT reward_question_claims_attempt_id_fkey;
ALTER TABLE reward_question_claims ADD CONSTRAINT reward_question_claims_attempt_id_fkey
 FOREIGN KEY(attempt_id) REFERENCES attempts(id) ON DELETE SET NULL;
ALTER TABLE reward_ledger DROP CONSTRAINT reward_ledger_source_attempt_id_fkey;
ALTER TABLE reward_ledger ADD CONSTRAINT reward_ledger_source_attempt_id_fkey
 FOREIGN KEY(source_attempt_id) REFERENCES attempts(id) ON DELETE SET NULL;
ALTER TABLE mastery_milestones DROP CONSTRAINT mastery_milestones_source_attempt_id_fkey;
ALTER TABLE mastery_milestones ADD CONSTRAINT mastery_milestones_source_attempt_id_fkey
 FOREIGN KEY(source_attempt_id) REFERENCES attempts(id) ON DELETE SET NULL;
ALTER TABLE mastery_milestones DROP CONSTRAINT mastery_milestones_review_session_id_fkey;
ALTER TABLE mastery_milestones ADD CONSTRAINT mastery_milestones_review_session_id_fkey
 FOREIGN KEY(review_session_id) REFERENCES practice_study_sessions(id) ON DELETE SET NULL;
ALTER TABLE mastery_milestones DROP CONSTRAINT mastery_milestones_check;
ALTER TABLE mastery_milestones ADD CONSTRAINT mastery_milestones_check CHECK(
 (origin='baseline' AND ledger_id IS NULL AND source_attempt_id IS NULL AND review_session_id IS NULL)
 OR (origin='activity' AND ledger_id IS NOT NULL)
);
-- Reward proofs keep their opaque source IDs, but no longer pin a deleted
-- private study session/mock. The immutable reward rows and ledger survive.
ALTER TABLE mock_completion_rewards DROP CONSTRAINT mock_completion_rewards_mock_id_fkey;
ALTER TABLE review_session_rewards DROP CONSTRAINT review_session_rewards_session_id_fkey;

CREATE FUNCTION sweep_expired_study_history(p_accounts integer DEFAULT 5,p_batch integer DEFAULT 200)
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE u record; t text; done integer:=0; completed integer:=0; removed bigint:=0; n integer;
BEGIN
 IF p_accounts<1 OR p_accounts>20 OR p_batch<1 OR p_batch>1000 THEN
   RAISE EXCEPTION 'Invalid study-history cleanup bounds';
 END IF;
 FOR u IN SELECT a.id FROM public.users a
   WHERE a.closed_at<=clock_timestamp()-interval '30 days'
     AND a.study_history_purged_at IS NULL
     AND NOT EXISTS(SELECT 1 FROM public.account_study_history_holds h
       WHERE h.user_id=a.id AND h.released_at IS NULL
         AND (h.expires_at IS NULL OR h.expires_at>clock_timestamp()))
   ORDER BY a.closed_at,a.id FOR UPDATE OF a SKIP LOCKED LIMIT p_accounts
 LOOP
   done:=done+1;
   PERFORM set_config('finna.study_history_purge_user',u.id,true);

   -- Delete the leaf receipts first; an attempt can only be removed after all
   -- personal answer/review references have been cleared. Rewards remain.
   DELETE FROM public.attempt_assessments aa USING public.attempts a
    WHERE aa.attempt_id=a.id AND a.user_id=u.id
      AND (a.context IN ('practice','review','mock','mock-derived','material') OR EXISTS(
        SELECT 1 FROM public.mock_sessions m WHERE m.id=a.mock_id AND m.user_id=u.id))
      AND aa.ctid IN(SELECT aa2.ctid FROM public.attempt_assessments aa2
        JOIN public.attempts a2 ON a2.id=aa2.attempt_id WHERE a2.user_id=u.id
        AND (a2.context IN ('practice','review','mock','mock-derived','material') OR EXISTS(
          SELECT 1 FROM public.mock_sessions m2 WHERE m2.id=a2.mock_id AND m2.user_id=u.id))
        ORDER BY aa2.id LIMIT p_batch FOR UPDATE OF aa2 SKIP LOCKED);
   GET DIAGNOSTICS n=ROW_COUNT; removed:=removed+n;

   DELETE FROM public.mock_assessments ma USING public.mock_sessions m
    WHERE ma.mock_id=m.id AND m.user_id=u.id
      AND ma.id IN(SELECT ma2.id FROM public.mock_assessments ma2
        JOIN public.mock_sessions m2 ON m2.id=ma2.mock_id WHERE m2.user_id=u.id
        ORDER BY ma2.id LIMIT p_batch FOR UPDATE OF ma2 SKIP LOCKED);
   GET DIAGNOSTICS n=ROW_COUNT; removed:=removed+n;

   DELETE FROM public.practice_request_receipts r WHERE r.user_id=u.id
    AND r.ctid IN(SELECT r2.ctid FROM public.practice_request_receipts r2
      WHERE r2.user_id=u.id ORDER BY r2.created_at,r2.request_key LIMIT p_batch FOR UPDATE SKIP LOCKED);
   GET DIAGNOSTICS n=ROW_COUNT; removed:=removed+n;
   DELETE FROM public.daily_revision_completions d USING public.daily_revision_sessions s
    WHERE d.session_id=s.id AND s.user_id=u.id
      AND d.ctid IN(SELECT d2.ctid FROM public.daily_revision_completions d2
        JOIN public.daily_revision_sessions s2 ON s2.id=d2.session_id WHERE s2.user_id=u.id
        ORDER BY d2.created_at,d2.session_id,d2.question_id LIMIT p_batch FOR UPDATE OF d2 SKIP LOCKED);
   GET DIAGNOSTICS n=ROW_COUNT; removed:=removed+n;
   DELETE FROM public.review_item_completions r WHERE r.user_id=u.id
    AND r.ctid IN(SELECT r2.ctid FROM public.review_item_completions r2
      WHERE r2.user_id=u.id ORDER BY r2.completed_on,r2.canonical_id LIMIT p_batch FOR UPDATE SKIP LOCKED);
   GET DIAGNOSTICS n=ROW_COUNT; removed:=removed+n;
   DELETE FROM public.review_session_items i USING public.practice_study_sessions s
    WHERE i.session_id=s.id AND s.user_id=u.id
      AND i.ctid IN(SELECT i2.ctid FROM public.review_session_items i2
        JOIN public.practice_study_sessions s2 ON s2.id=i2.session_id WHERE s2.user_id=u.id
        ORDER BY i2.session_id,i2.canonical_id LIMIT p_batch FOR UPDATE OF i2 SKIP LOCKED);
   GET DIAGNOSTICS n=ROW_COUNT; removed:=removed+n;
   DELETE FROM public.vocab_review_session_items i USING public.practice_study_sessions s
    WHERE i.session_id=s.id AND s.user_id=u.id
      AND i.ctid IN(SELECT i2.ctid FROM public.vocab_review_session_items i2
        JOIN public.practice_study_sessions s2 ON s2.id=i2.session_id WHERE s2.user_id=u.id
        ORDER BY i2.session_id,i2.card_id LIMIT p_batch FOR UPDATE OF i2 SKIP LOCKED);
   GET DIAGNOSTICS n=ROW_COUNT; removed:=removed+n;
   DELETE FROM public.vocab_review_completions c WHERE c.user_id=u.id
    AND c.ctid IN(SELECT c2.ctid FROM public.vocab_review_completions c2
      WHERE c2.user_id=u.id ORDER BY c2.completed_on,c2.card_id LIMIT p_batch FOR UPDATE SKIP LOCKED);
   GET DIAGNOSTICS n=ROW_COUNT; removed:=removed+n;
   DELETE FROM public.vocab_practice_receipts r WHERE r.user_id=u.id
    AND r.ctid IN(SELECT r2.ctid FROM public.vocab_practice_receipts r2
      WHERE r2.user_id=u.id ORDER BY r2.created_at,r2.request_key LIMIT p_batch FOR UPDATE SKIP LOCKED);
   GET DIAGNOSTICS n=ROW_COUNT; removed:=removed+n;
   DELETE FROM public.vocab_attempts a WHERE a.user_id=u.id
    AND NOT EXISTS(SELECT 1 FROM public.vocab_practice_receipts r WHERE r.attempt_id=a.id)
    AND NOT EXISTS(SELECT 1 FROM public.vocab_review_completions c WHERE c.attempt_id=a.id)
    AND NOT EXISTS(SELECT 1 FROM public.vocab_review_session_items i WHERE i.attempt_id=a.id)
    AND a.ctid IN(SELECT a2.ctid FROM public.vocab_attempts a2 WHERE a2.user_id=u.id
      AND NOT EXISTS(SELECT 1 FROM public.vocab_practice_receipts r WHERE r.attempt_id=a2.id)
      AND NOT EXISTS(SELECT 1 FROM public.vocab_review_completions c WHERE c.attempt_id=a2.id)
      AND NOT EXISTS(SELECT 1 FROM public.vocab_review_session_items i WHERE i.attempt_id=a2.id)
      ORDER BY a2.at,a2.id LIMIT p_batch FOR UPDATE SKIP LOCKED);
   GET DIAGNOSTICS n=ROW_COUNT; removed:=removed+n;
   DELETE FROM public.atlas_drill_results r WHERE r.user_id=u.id
    AND r.ctid IN(SELECT r2.ctid FROM public.atlas_drill_results r2 WHERE r2.user_id=u.id
      ORDER BY r2.at,r2.presentation_id LIMIT p_batch FOR UPDATE SKIP LOCKED);
   GET DIAGNOSTICS n=ROW_COUNT; removed:=removed+n;

   -- Detach retained awards/milestones before removing their personal sources.
   UPDATE public.mastery_milestones SET source_attempt_id=NULL,review_session_id=NULL
    WHERE ctid IN (SELECT mm.ctid FROM public.mastery_milestones mm WHERE mm.user_id=u.id
      AND (mm.source_attempt_id IN(SELECT a.id FROM public.attempts a WHERE a.user_id=u.id
       AND (a.context IN ('practice','review','mock','mock-derived','material') OR EXISTS(
         SELECT 1 FROM public.mock_sessions m WHERE m.id=a.mock_id AND m.user_id=u.id)))
      OR mm.review_session_id IN(SELECT s.id FROM public.practice_study_sessions s WHERE s.user_id=u.id))
      ORDER BY mm.user_id,mm.subject_id,mm.topic LIMIT p_batch FOR UPDATE SKIP LOCKED);
   GET DIAGNOSTICS n=ROW_COUNT; removed:=removed+n;
   UPDATE public.game_answers g SET attempt_id=NULL WHERE g.ctid IN(
     SELECT g2.ctid FROM public.game_answers g2 JOIN public.attempts a ON a.id=g2.attempt_id
      WHERE a.user_id=u.id
       AND (a.context IN ('practice','review','mock','mock-derived','material') OR EXISTS(
         SELECT 1 FROM public.mock_sessions m WHERE m.id=a.mock_id AND m.user_id=u.id))
      ORDER BY g2.room_id,g2.user_id,g2.position LIMIT p_batch FOR UPDATE OF g2 SKIP LOCKED);
   GET DIAGNOSTICS n=ROW_COUNT; removed:=removed+n;
   UPDATE public.review_notifications rn SET mock_id=NULL WHERE rn.ctid IN(
    SELECT rn2.ctid FROM public.review_notifications rn2 JOIN public.mock_sessions m ON m.id=rn2.mock_id
     WHERE rn2.user_id=u.id AND m.user_id=u.id
     ORDER BY rn2.created_at,rn2.id LIMIT p_batch FOR UPDATE OF rn2 SKIP LOCKED);
   GET DIAGNOSTICS n=ROW_COUNT; removed:=removed+n;

   DELETE FROM public.new_score_jobs j WHERE j.ctid IN(
     SELECT j2.ctid FROM public.new_score_jobs j2 WHERE
     j2.attempt_id IN(SELECT a.id FROM public.attempts a WHERE a.user_id=u.id
       AND (a.context IN ('practice','review','mock','mock-derived','material') OR EXISTS(
         SELECT 1 FROM public.mock_sessions m WHERE m.id=a.mock_id AND m.user_id=u.id)))
     OR j2.mock_id IN(SELECT m.id FROM public.mock_sessions m WHERE m.user_id=u.id)
     ORDER BY j2.id LIMIT p_batch FOR UPDATE OF j2 SKIP LOCKED);
   GET DIAGNOSTICS n=ROW_COUNT; removed:=removed+n;

   -- Old vocabulary mode stores answers in these private presentation rows.
   DELETE FROM public.vocabulary_cards v WHERE v.ctid IN(
     SELECT v2.ctid FROM public.vocabulary_cards v2 WHERE v2.user_id=u.id
     ORDER BY v2.issued_at,v2.id LIMIT p_batch FOR UPDATE SKIP LOCKED);
   GET DIAGNOSTICS n=ROW_COUNT; removed:=removed+n;

   -- Attempt deletion is capped separately. Multiplayer/duel/cup attempts and
   -- their shared results are outside this scope and are not deleted.
   DELETE FROM public.attempts a WHERE a.id IN(SELECT a2.id FROM public.attempts a2
     WHERE a2.user_id=u.id AND
       (a2.context IN ('practice','review','mock','mock-derived','material') OR EXISTS(
         SELECT 1 FROM public.mock_sessions m WHERE m.id=a2.mock_id AND m.user_id=u.id))
       AND NOT EXISTS(SELECT 1 FROM public.daily_revision_completions x WHERE x.attempt_id=a2.id)
       AND NOT EXISTS(SELECT 1 FROM public.review_item_completions x WHERE x.attempt_id=a2.id)
       AND NOT EXISTS(SELECT 1 FROM public.review_items x WHERE x.last_attempt_id=a2.id)
       AND NOT EXISTS(SELECT 1 FROM public.review_session_items x WHERE x.attempt_id=a2.id)
       AND NOT EXISTS(SELECT 1 FROM public.vocabulary_cards x WHERE x.attempt_id=a2.id)
       AND NOT EXISTS(SELECT 1 FROM public.game_answers x WHERE x.attempt_id=a2.id)
       AND NOT EXISTS(SELECT 1 FROM public.practice_request_receipts x WHERE x.attempt_id=a2.id)
       AND NOT EXISTS(SELECT 1 FROM public.attempt_assessments x WHERE x.attempt_id=a2.id)
       AND NOT EXISTS(SELECT 1 FROM public.new_score_jobs x WHERE x.attempt_id=a2.id)
     ORDER BY a2.id LIMIT p_batch FOR UPDATE OF a2 SKIP LOCKED);
   GET DIAGNOSTICS n=ROW_COUNT; removed:=removed+n;

   DELETE FROM public.vocab_presentations p WHERE p.user_id=u.id
    AND NOT EXISTS(SELECT 1 FROM public.vocab_attempts a WHERE a.presentation_id=p.id)
    AND NOT EXISTS(SELECT 1 FROM public.vocab_review_session_items i WHERE i.presentation_id=p.id)
    AND p.ctid IN(SELECT p2.ctid FROM public.vocab_presentations p2 WHERE p2.user_id=u.id
      AND NOT EXISTS(SELECT 1 FROM public.vocab_attempts a WHERE a.presentation_id=p2.id)
      AND NOT EXISTS(SELECT 1 FROM public.vocab_review_session_items i WHERE i.presentation_id=p2.id)
      ORDER BY p2.issued_at,p2.id LIMIT p_batch FOR UPDATE SKIP LOCKED);
   GET DIAGNOSTICS n=ROW_COUNT; removed:=removed+n;
   DELETE FROM public.atlas_drill_presentations p WHERE p.user_id=u.id
    AND NOT EXISTS(SELECT 1 FROM public.atlas_drill_results r WHERE r.presentation_id=p.id)
    AND p.ctid IN(SELECT p2.ctid FROM public.atlas_drill_presentations p2 WHERE p2.user_id=u.id
      AND NOT EXISTS(SELECT 1 FROM public.atlas_drill_results r WHERE r.presentation_id=p2.id)
      ORDER BY p2.created_at,p2.id LIMIT p_batch FOR UPDATE SKIP LOCKED);
   GET DIAGNOSTICS n=ROW_COUNT; removed:=removed+n;

   -- Remove private state/projections and activity whose source rows are now
   -- gone. Each delete is independently bounded and safely resumes next hour.
   FOREACH t IN ARRAY ARRAY[
    'answer_reveals','vocabulary_state','vocab_exposures','user_activity_questions',
    'user_activity_daily','user_topic_mastery','review_items','user_focus_subjects',
    'user_exam_bookmarks','exam_study_checkpoints','module_learning_progress',
    'learning_checkpoints','user_learning_days',
    'daily_learning_plans','atlas_exploration','atlas_practice_suggestions',
    'user_vocab_deck_mastery','learning_rollup_jobs','study_focus_sessions'
   ] LOOP
     n:=public.delete_account_study_history_rows(t,u.id,p_batch);
     removed:=removed+n;
   END LOOP;

   -- Session roots are removed only after every capped child batch has drained.
   DELETE FROM public.daily_revision_sessions s WHERE s.user_id=u.id
     AND NOT EXISTS(SELECT 1 FROM public.daily_revision_completions c WHERE c.session_id=s.id)
     AND s.ctid IN(SELECT s2.ctid FROM public.daily_revision_sessions s2 WHERE s2.user_id=u.id
       AND NOT EXISTS(SELECT 1 FROM public.daily_revision_completions c WHERE c.session_id=s2.id)
       ORDER BY s2.created_at,s2.id LIMIT p_batch FOR UPDATE SKIP LOCKED);
   GET DIAGNOSTICS n=ROW_COUNT; removed:=removed+n;
   DELETE FROM public.practice_study_sessions s WHERE s.user_id=u.id
     AND NOT EXISTS(SELECT 1 FROM public.review_session_items x WHERE x.session_id=s.id)
     AND NOT EXISTS(SELECT 1 FROM public.vocab_review_session_items x WHERE x.session_id=s.id)
     AND NOT EXISTS(SELECT 1 FROM public.vocab_review_completions x WHERE x.session_id=s.id)
     AND NOT EXISTS(SELECT 1 FROM public.vocab_attempts x WHERE x.session_id=s.id)
     AND NOT EXISTS(SELECT 1 FROM public.review_item_completions x WHERE x.session_id=s.id)
     AND s.ctid IN(SELECT s2.ctid FROM public.practice_study_sessions s2 WHERE s2.user_id=u.id
       AND NOT EXISTS(SELECT 1 FROM public.review_session_items x WHERE x.session_id=s2.id)
       AND NOT EXISTS(SELECT 1 FROM public.vocab_review_session_items x WHERE x.session_id=s2.id)
       AND NOT EXISTS(SELECT 1 FROM public.vocab_review_completions x WHERE x.session_id=s2.id)
       AND NOT EXISTS(SELECT 1 FROM public.vocab_attempts x WHERE x.session_id=s2.id)
       AND NOT EXISTS(SELECT 1 FROM public.review_item_completions x WHERE x.session_id=s2.id)
       ORDER BY s2.created_at,s2.id LIMIT p_batch FOR UPDATE SKIP LOCKED);
   GET DIAGNOSTICS n=ROW_COUNT; removed:=removed+n;

   -- A mock session is removable only after its target attempts have been
   -- deleted. Session answer/questions cascade; retained reward receipts use
   -- their opaque mock key without a foreign key to deleted study content.
   DELETE FROM public.mock_sessions m WHERE m.user_id=u.id AND NOT EXISTS(
      SELECT 1 FROM public.attempts a WHERE a.mock_id=m.id)
     AND NOT EXISTS(SELECT 1 FROM public.mock_assessments x WHERE x.mock_id=m.id)
     AND NOT EXISTS(SELECT 1 FROM public.new_score_jobs x WHERE x.mock_id=m.id)
     AND NOT EXISTS(SELECT 1 FROM public.review_notifications x WHERE x.mock_id=m.id)
     AND m.id IN(SELECT m2.id FROM public.mock_sessions m2 WHERE m2.user_id=u.id
       AND NOT EXISTS(SELECT 1 FROM public.attempts a2 WHERE a2.mock_id=m2.id)
       AND NOT EXISTS(SELECT 1 FROM public.mock_assessments x WHERE x.mock_id=m2.id)
       AND NOT EXISTS(SELECT 1 FROM public.new_score_jobs x WHERE x.mock_id=m2.id)
       AND NOT EXISTS(SELECT 1 FROM public.review_notifications x WHERE x.mock_id=m2.id)
       ORDER BY m2.started_at,m2.id LIMIT p_batch FOR UPDATE OF m2 SKIP LOCKED);
   GET DIAGNOSTICS n=ROW_COUNT; removed:=removed+n;

   -- The account remains closed. A marker avoids repeat work; this event is
   -- the minimal audit receipt and contains no answer, score or question ID.
   IF NOT EXISTS(SELECT 1 FROM public.attempts a WHERE a.user_id=u.id
        AND (a.context IN ('practice','review','mock','mock-derived','material') OR EXISTS(
          SELECT 1 FROM public.mock_sessions m WHERE m.id=a.mock_id AND m.user_id=u.id)))
      AND NOT EXISTS(SELECT 1 FROM public.mock_sessions WHERE user_id=u.id)
      AND NOT EXISTS(SELECT 1 FROM public.practice_study_sessions WHERE user_id=u.id)
      AND NOT EXISTS(SELECT 1 FROM public.practice_request_receipts WHERE user_id=u.id)
      AND NOT EXISTS(SELECT 1 FROM public.attempt_assessments aa JOIN public.attempts a ON a.id=aa.attempt_id
        WHERE a.user_id=u.id AND a.context IN ('practice','review','mock','mock-derived','material'))
      AND NOT EXISTS(SELECT 1 FROM public.mock_assessments ma JOIN public.mock_sessions m ON m.id=ma.mock_id WHERE m.user_id=u.id)
      AND NOT EXISTS(SELECT 1 FROM public.vocab_attempts WHERE user_id=u.id)
      AND NOT EXISTS(SELECT 1 FROM public.vocab_presentations WHERE user_id=u.id)
      AND NOT EXISTS(SELECT 1 FROM public.atlas_drill_results WHERE user_id=u.id)
      AND NOT EXISTS(SELECT 1 FROM public.atlas_drill_presentations WHERE user_id=u.id)
      AND NOT EXISTS(SELECT 1 FROM public.user_activity_daily WHERE user_id=u.id)
      AND NOT EXISTS(SELECT 1 FROM public.user_activity_questions WHERE user_id=u.id)
      AND NOT EXISTS(SELECT 1 FROM public.user_topic_mastery WHERE user_id=u.id)
      AND NOT EXISTS(SELECT 1 FROM public.review_items WHERE user_id=u.id)
      AND NOT EXISTS(SELECT 1 FROM public.review_item_completions WHERE user_id=u.id)
      AND NOT EXISTS(SELECT 1 FROM public.learning_rollup_jobs WHERE user_id=u.id)
      AND NOT EXISTS(SELECT 1 FROM public.learning_checkpoints WHERE user_id=u.id)
      AND NOT EXISTS(SELECT 1 FROM public.daily_revision_sessions WHERE user_id=u.id)
      AND NOT EXISTS(SELECT 1 FROM public.daily_revision_completions c JOIN public.daily_revision_sessions s ON s.id=c.session_id WHERE s.user_id=u.id)
      AND NOT EXISTS(SELECT 1 FROM public.user_learning_days WHERE user_id=u.id)
      AND NOT EXISTS(SELECT 1 FROM public.daily_learning_plans WHERE user_id=u.id)
      AND NOT EXISTS(SELECT 1 FROM public.user_focus_subjects WHERE user_id=u.id)
      AND NOT EXISTS(SELECT 1 FROM public.user_exam_bookmarks WHERE user_id=u.id)
      AND NOT EXISTS(SELECT 1 FROM public.exam_study_checkpoints WHERE user_id=u.id)
      AND NOT EXISTS(SELECT 1 FROM public.module_learning_progress WHERE user_id=u.id)
      AND NOT EXISTS(SELECT 1 FROM public.user_vocab_deck_mastery WHERE user_id=u.id)
      AND NOT EXISTS(SELECT 1 FROM public.study_focus_sessions WHERE user_id=u.id)
      AND NOT EXISTS(SELECT 1 FROM public.vocab_exposures WHERE user_id=u.id)
      AND NOT EXISTS(SELECT 1 FROM public.vocab_practice_receipts WHERE user_id=u.id)
      AND NOT EXISTS(SELECT 1 FROM public.vocab_review_session_items i JOIN public.practice_study_sessions s ON s.id=i.session_id WHERE s.user_id=u.id)
      AND NOT EXISTS(SELECT 1 FROM public.vocab_review_completions WHERE user_id=u.id)
      AND NOT EXISTS(SELECT 1 FROM public.vocab_presentations WHERE user_id=u.id)
      AND NOT EXISTS(SELECT 1 FROM public.vocabulary_state WHERE user_id=u.id)
      AND NOT EXISTS(SELECT 1 FROM public.vocabulary_cards WHERE user_id=u.id)
      AND NOT EXISTS(SELECT 1 FROM public.answer_reveals WHERE user_id=u.id)
      AND NOT EXISTS(SELECT 1 FROM public.atlas_exploration WHERE user_id=u.id)
      AND NOT EXISTS(SELECT 1 FROM public.atlas_practice_suggestions WHERE user_id=u.id)
      AND NOT EXISTS(SELECT 1 FROM public.review_session_items i JOIN public.practice_study_sessions s ON s.id=i.session_id WHERE s.user_id=u.id)
      AND NOT EXISTS(SELECT 1 FROM public.vocab_attempts WHERE user_id=u.id)
   THEN
     UPDATE public.users SET study_history_purged_at=clock_timestamp() WHERE id=u.id
       AND study_history_purged_at IS NULL;
     IF FOUND THEN
       INSERT INTO public.account_security_events(user_id,action,detail)
        VALUES(u.id,'closed_study_history_purged',jsonb_build_object('policy','personal-study-v1'));
       completed:=completed+1;
     END IF;
   END IF;
 END LOOP;
 RETURN jsonb_build_object('accounts_scanned',done,'accounts_completed',completed,'rows_removed',removed);
END $$;

-- Immutable answer receipts and map results only permit sweeper-authorized
-- deletion. Mutable projections keep their existing owner-scoped application
-- operations; study roots with no application delete path are revoked below.
CREATE FUNCTION study_history_purge_context(p_user text) RETURNS boolean
LANGUAGE sql STABLE SET search_path=pg_catalog,public AS $$
 SELECT current_user=(SELECT pg_get_userbyid(p.proowner) FROM pg_catalog.pg_proc p
    WHERE p.oid='public.sweep_expired_study_history(integer,integer)'::regprocedure)
   AND current_setting('finna.study_history_purge_user',true)=p_user
   AND EXISTS(SELECT 1 FROM public.users u WHERE u.id=p_user
     AND u.closed_at<=clock_timestamp()-interval '30 days'
     AND u.study_history_purged_at IS NULL
     AND NOT EXISTS(SELECT 1 FROM public.account_study_history_holds h
       WHERE h.user_id=u.id AND h.released_at IS NULL
        AND (h.expires_at IS NULL OR h.expires_at>clock_timestamp())))
$$;

CREATE FUNCTION study_history_purge_delete_guard() RETURNS trigger
LANGUAGE plpgsql SET search_path=pg_catalog,public AS $$
DECLARE uid text;
BEGIN
 IF TG_TABLE_NAME='attempt_assessments' THEN
   SELECT user_id INTO uid FROM public.attempts WHERE id=OLD.attempt_id;
 ELSIF TG_TABLE_NAME='mock_assessments' THEN
   SELECT user_id INTO uid FROM public.mock_sessions WHERE id=OLD.mock_id;
 ELSE
   uid:=to_jsonb(OLD)->>'user_id';
 END IF;
 IF uid IS NOT NULL AND public.study_history_purge_context(uid) THEN RETURN OLD; END IF;
 RAISE EXCEPTION 'Study history is immutable outside the expired closed-account cleanup';
END $$;

CREATE FUNCTION study_history_purge_link_guard() RETURNS trigger
LANGUAGE plpgsql SET search_path=pg_catalog,public AS $$
DECLARE uid text;
BEGIN
 uid:=OLD.user_id;
 IF TG_TABLE_NAME='reward_ledger' AND OLD.source_attempt_id IS NOT NULL
   AND NEW.source_attempt_id IS NULL
   AND (to_jsonb(NEW)-'source_attempt_id')=(to_jsonb(OLD)-'source_attempt_id')
   AND public.study_history_purge_context(uid) THEN RETURN NEW; END IF;
 IF TG_TABLE_NAME='mastery_milestones' AND OLD.origin='activity'
   AND NEW.source_attempt_id IS NULL AND NEW.review_session_id IS NULL
   AND (to_jsonb(NEW)-'source_attempt_id'-'review_session_id')=
       (to_jsonb(OLD)-'source_attempt_id'-'review_session_id')
   AND public.study_history_purge_context(uid) THEN RETURN NEW; END IF;
 RAISE EXCEPTION 'Retained reward links are immutable outside expired closed-account cleanup';
END $$;

CREATE FUNCTION delete_account_study_history_rows(p_table text,p_user text,p_limit integer)
RETURNS integer LANGUAGE plpgsql SET search_path=pg_catalog,public AS $$
DECLARE n integer;
BEGIN
 IF p_table NOT IN ('answer_reveals','vocabulary_state','vocab_exposures',
   'user_activity_questions','user_activity_daily','user_topic_mastery','review_items',
   'user_focus_subjects','user_exam_bookmarks','exam_study_checkpoints',
   'module_learning_progress','learning_checkpoints',
   'user_learning_days','daily_learning_plans','atlas_exploration',
   'atlas_practice_suggestions','user_vocab_deck_mastery',
   'learning_rollup_jobs','study_focus_sessions') THEN RAISE EXCEPTION 'Study-history table is not allowlisted'; END IF;
 IF NOT public.study_history_purge_context(p_user) THEN RAISE EXCEPTION 'Account is not eligible for study-history cleanup'; END IF;
 EXECUTE format('DELETE FROM public.%I x WHERE x.user_id=$1 AND x.ctid IN '
   '(SELECT ctid FROM public.%I WHERE user_id=$1 ORDER BY ctid LIMIT $2 FOR UPDATE SKIP LOCKED)',p_table,p_table)
   USING p_user,p_limit;
 GET DIAGNOSTICS n=ROW_COUNT;
 RETURN n;
END $$;

-- Split UPDATE immutability from DELETE authorization on study receipts.
DROP TRIGGER IF EXISTS immutable_attempt_assessment ON attempt_assessments;
DROP TRIGGER IF EXISTS immutable_mock_assessment ON mock_assessments;
DROP TRIGGER IF EXISTS immutable_practice_receipt ON practice_request_receipts;
DROP TRIGGER IF EXISTS immutable_daily_learning_plan ON daily_learning_plans;
DROP TRIGGER IF EXISTS immutable_review_item_completion ON review_item_completions;
DROP TRIGGER IF EXISTS immutable_vocab_attempts ON vocab_attempts;
DROP TRIGGER IF EXISTS immutable_vocab_practice_receipts ON vocab_practice_receipts;
DROP TRIGGER IF EXISTS immutable_vocab_review_completions ON vocab_review_completions;
DO $$ DECLARE t text; BEGIN
 FOREACH t IN ARRAY ARRAY['attempt_assessments','mock_assessments','practice_request_receipts',
   'daily_learning_plans','review_item_completions','vocab_attempts',
   'vocab_practice_receipts','vocab_review_completions'] LOOP
   EXECUTE format('CREATE TRIGGER retention_%I_update BEFORE UPDATE ON public.%I FOR EACH ROW EXECUTE FUNCTION public.review_immutable()',t,t);
   EXECUTE format('CREATE TRIGGER retention_%I_delete BEFORE DELETE ON public.%I FOR EACH ROW EXECUTE FUNCTION public.study_history_purge_delete_guard()',t,t);
 END LOOP;
END $$;
DROP TRIGGER IF EXISTS atlas_results_immutable ON atlas_drill_results;
CREATE TRIGGER atlas_results_immutable_update BEFORE UPDATE ON atlas_drill_results
 FOR EACH ROW EXECUTE FUNCTION atlas_chapter_history_immutable();
CREATE TRIGGER atlas_results_purge_delete BEFORE DELETE ON atlas_drill_results
 FOR EACH ROW EXECUTE FUNCTION study_history_purge_delete_guard();
DROP TRIGGER IF EXISTS atlas_presentations_immutable ON atlas_drill_presentations;
CREATE TRIGGER atlas_presentations_immutable_update BEFORE UPDATE ON atlas_drill_presentations
 FOR EACH ROW EXECUTE FUNCTION atlas_chapter_history_immutable();
CREATE TRIGGER atlas_presentations_purge_delete BEFORE DELETE ON atlas_drill_presentations
 FOR EACH ROW EXECUTE FUNCTION study_history_purge_delete_guard();

DROP TRIGGER IF EXISTS immutable_reward_ledger ON reward_ledger;
CREATE TRIGGER immutable_reward_ledger_delete BEFORE DELETE ON reward_ledger
 FOR EACH ROW EXECUTE FUNCTION review_immutable();
CREATE TRIGGER immutable_reward_ledger_links BEFORE UPDATE ON reward_ledger
 FOR EACH ROW EXECUTE FUNCTION study_history_purge_link_guard();
DROP TRIGGER IF EXISTS immutable_mastery_milestone ON mastery_milestones;
CREATE TRIGGER immutable_mastery_milestone_delete BEFORE DELETE ON mastery_milestones
 FOR EACH ROW EXECUTE FUNCTION review_immutable();
CREATE TRIGGER immutable_mastery_milestone_links BEFORE UPDATE ON mastery_milestones
 FOR EACH ROW EXECUTE FUNCTION study_history_purge_link_guard();

REVOKE ALL ON FUNCTION sweep_expired_study_history(integer,integer),
 delete_account_study_history_rows(text,text,integer),study_history_purge_context(text),
 study_history_purge_delete_guard(),study_history_purge_link_guard() FROM PUBLIC;
-- No current API path deletes these study roots directly. Keep their deletion
-- inside the security-definer sweeper, even though mpsc can delete other
-- mutable projections for established owner-scoped reset/rebuild operations.
REVOKE DELETE ON attempts,mock_sessions,review_items,study_focus_sessions FROM mpsc;
GRANT EXECUTE ON FUNCTION sweep_expired_study_history(integer,integer) TO mpsc;
COMMENT ON FUNCTION sweep_expired_study_history(integer,integer) IS
 'Bounded, opt-in deletion of approved private study history after the 30-day closure recovery window; never run from migration application.';
COMMENT ON TABLE account_study_history_holds IS
 'Restricted operator holds that pause closed-account study-history cleanup; mpsc has no write grant.';

COMMIT;
