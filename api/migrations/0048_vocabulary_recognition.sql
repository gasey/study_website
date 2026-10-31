BEGIN;
CREATE VIEW v_vocabulary_eligible AS
 SELECT q.id,requested.focus,src.id AS appearance_id,prim.id AS primary_appearance_id,
 src.exam_scope_id,prim.context_revision AS appearance_version,src.context_revision AS source_version,
 COALESCE((SELECT version FROM question_score_versions sv WHERE sv.canonical_id=q.id),0) AS score_version
 FROM v_scorable q
 CROSS JOIN (VALUES ('mizoram-recruitment'),('all')) requested(focus)
 JOIN LATERAL(SELECT a.* FROM appearances a WHERE a.canonical_id=q.id AND a.is_primary ORDER BY a.id LIMIT 1) prim ON true
 JOIN LATERAL(SELECT a.*,p.exam_scope_id FROM appearances a JOIN papers p ON p.id=a.paper_id
   WHERE a.canonical_id=q.id AND (requested.focus='all' OR p.exam_scope_id='mizoram-recruitment')
   AND a.question=q.question AND a.options=q.options
   AND COALESCE(a.direction,q.direction) IS NOT DISTINCT FROM COALESCE(prim.direction,q.direction)
   AND COALESCE(a.passage,q.passage) IS NOT DISTINCT FROM COALESCE(prim.passage,q.passage)
   AND COALESCE(a.question_markup,q.question_markup) IS NOT DISTINCT FROM COALESCE(prim.question_markup,q.question_markup)
   AND COALESCE(a.options_markup,q.options_markup) IS NOT DISTINCT FROM COALESCE(prim.options_markup,q.options_markup)
   AND COALESCE(a.has_diagram,false)=COALESCE(prim.has_diagram,false)
   AND a.figure_image IS NOT DISTINCT FROM prim.figure_image
   AND (NOT COALESCE(a.has_diagram,false) OR NULLIF(btrim(a.figure_image),'') IS NOT NULL)
   ORDER BY a.is_primary DESC,a.id LIMIT 1) src ON true
 WHERE q.type='mcq' AND jsonb_array_length(q.options) BETWEEN 2 AND 6
 AND NOT EXISTS(SELECT 1 FROM jsonb_array_elements_text(q.options) o WHERE o IS NULL OR btrim(o)='')
 AND (SELECT count(DISTINCT normalize(regexp_replace(btrim(o),'\s+',' ','g'),NFC)) FROM jsonb_array_elements_text(q.options) o)=jsonb_array_length(q.options)
 AND EXISTS(SELECT 1 FROM v_question_paths t WHERE t.question_id=q.id AND t.subject_id='english' AND t.topic_id='english/vocabulary');
CREATE TABLE vocabulary_state (
 user_id TEXT NOT NULL REFERENCES users(id),question_id TEXT NOT NULL REFERENCES canonical_questions(id),
 content_hash TEXT NOT NULL,score_version BIGINT NOT NULL DEFAULT 0,appearance_version BIGINT NOT NULL DEFAULT 0,appearance_id TEXT,version INTEGER NOT NULL DEFAULT 0,stage INTEGER NOT NULL DEFAULT 0 CHECK(stage BETWEEN 0 AND 6),
 seen INTEGER NOT NULL DEFAULT 0,graded INTEGER NOT NULL DEFAULT 0,correct INTEGER NOT NULL DEFAULT 0,lapses INTEGER NOT NULL DEFAULT 0,
 due_at TIMESTAMPTZ NOT NULL DEFAULT now(),first_review_at TIMESTAMPTZ,last_review_at TIMESTAMPTZ,last_exposure_at TIMESTAMPTZ,last_credit_day DATE,
 PRIMARY KEY(user_id,question_id),CHECK(correct<=graded AND graded<=seen)
);
CREATE INDEX vocabulary_due ON vocabulary_state(user_id,due_at);
CREATE TABLE vocabulary_cards (
 id TEXT PRIMARY KEY,user_id TEXT NOT NULL REFERENCES users(id),question_id TEXT NOT NULL REFERENCES canonical_questions(id),
 exam_scope TEXT NOT NULL CHECK(exam_scope IN ('all','mizoram-recruitment')),
 snapshot JSONB NOT NULL,display_order INTEGER[] NOT NULL,content_hash TEXT NOT NULL,state_version INTEGER NOT NULL,
 issued_at TIMESTAMPTZ NOT NULL DEFAULT now(),expires_at TIMESTAMPTZ NOT NULL DEFAULT now()+interval '30 minutes',
 answered_at TIMESTAMPTZ,action TEXT,chosen_index INTEGER,attempt_id BIGINT REFERENCES attempts(id),result JSONB,
 CHECK((answered_at IS NULL AND chosen_index IS NULL AND attempt_id IS NULL AND result IS NULL) OR (answered_at IS NOT NULL AND result IS NOT NULL))
);
CREATE INDEX vocabulary_active_cards ON vocabulary_cards(user_id,exam_scope,issued_at DESC) WHERE answered_at IS NULL;
CREATE FUNCTION vocabulary_card_immutable() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN
 IF OLD.answered_at IS NOT NULL AND NEW IS DISTINCT FROM OLD THEN RAISE EXCEPTION 'Vocabulary result receipts are immutable'; END IF;
 IF ROW(NEW.id,NEW.user_id,NEW.question_id,NEW.exam_scope,NEW.snapshot,NEW.display_order,NEW.content_hash,NEW.state_version,NEW.issued_at)
 IS DISTINCT FROM ROW(OLD.id,OLD.user_id,OLD.question_id,OLD.exam_scope,OLD.snapshot,OLD.display_order,OLD.content_hash,OLD.state_version,OLD.issued_at)
 THEN RAISE EXCEPTION 'Vocabulary presentation is immutable'; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER vocabulary_card_immutable BEFORE UPDATE ON vocabulary_cards FOR EACH ROW EXECUTE FUNCTION vocabulary_card_immutable();
GRANT SELECT ON v_vocabulary_eligible TO mpsc;
GRANT SELECT,INSERT,UPDATE ON vocabulary_state,vocabulary_cards TO mpsc;
COMMIT;
