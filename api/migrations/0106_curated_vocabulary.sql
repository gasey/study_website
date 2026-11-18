BEGIN;
-- Reviewed material revisions remain the publication/lifecycle authority.
-- These tables are immutable identities and projections, never another CMS.
CREATE TABLE vocab_decks (
 id text PRIMARY KEY REFERENCES materials(id),created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE vocab_cards (
 id text PRIMARY KEY,deck_id text NOT NULL REFERENCES vocab_decks(id),block_id text NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now(),UNIQUE(id,deck_id)
);
CREATE TABLE vocab_card_revisions (
 card_id text NOT NULL,deck_id text NOT NULL,revision integer NOT NULL,payload jsonb NOT NULL,
 content_hash text NOT NULL CHECK(content_hash ~ '^[0-9a-f]{64}$'),
 PRIMARY KEY(card_id,revision),FOREIGN KEY(card_id,deck_id) REFERENCES vocab_cards(id,deck_id),
 FOREIGN KEY(deck_id,revision) REFERENCES material_revisions(material_id,revision),
 CHECK(jsonb_typeof(payload)='object')
);
CREATE TABLE vocab_deck_items (
 deck_id text NOT NULL REFERENCES vocab_decks(id),revision integer NOT NULL,
 position integer NOT NULL CHECK(position>=0),card_id text NOT NULL,
 PRIMARY KEY(deck_id,revision,card_id),UNIQUE(deck_id,revision,position),
 FOREIGN KEY(card_id,revision) REFERENCES vocab_card_revisions(card_id,revision)
);
CREATE FUNCTION capture_vocab_publication(mid text) RETURNS void LANGUAGE plpgsql AS $$
DECLARE pub record;block record;cid text;
BEGIN
 SELECT m.id,m.published_revision,r.payload INTO pub FROM materials m JOIN material_revisions r
 ON r.material_id=m.id AND r.revision=m.published_revision
 WHERE m.id=mid AND m.status='published' AND r.payload->>'kind'='vocabulary-deck';
 IF NOT FOUND THEN RETURN; END IF;
 INSERT INTO vocab_decks(id) VALUES(pub.id) ON CONFLICT DO NOTHING;
 FOR block IN SELECT value AS payload,ordinality::int-1 AS position FROM jsonb_array_elements(pub.payload->'blocks') WITH ORDINALITY
 WHERE value->>'type'='vocabulary' LOOP
  cid='vc_'||encode(sha256(convert_to(pub.id||chr(31)||(block.payload->>'id')||chr(31)||COALESCE(block.payload->'vocabulary'->>'language','english')||chr(31)||lower(normalize(regexp_replace(btrim(block.payload->'vocabulary'->>'word'),'\s+',' ','g'),NFKC)),'UTF8')),'hex');
  INSERT INTO vocab_cards(id,deck_id,block_id) VALUES(cid,pub.id,block.payload->>'id') ON CONFLICT DO NOTHING;
  INSERT INTO vocab_card_revisions(card_id,deck_id,revision,payload,content_hash)
  VALUES(cid,pub.id,pub.published_revision,block.payload->'vocabulary',encode(sha256(convert_to((block.payload->'vocabulary')::text,'UTF8')),'hex')) ON CONFLICT DO NOTHING;
  INSERT INTO vocab_deck_items(deck_id,revision,position,card_id)
  VALUES(pub.id,pub.published_revision,block.position,cid) ON CONFLICT DO NOTHING;
 END LOOP;
END $$;
CREATE FUNCTION capture_vocab_material() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN PERFORM capture_vocab_publication(NEW.id);RETURN NEW;END $$;
CREATE TRIGGER capture_vocab_material AFTER UPDATE OF status,published_revision ON materials
 FOR EACH ROW WHEN(NEW.status='published') EXECUTE FUNCTION capture_vocab_material();
-- Derive only already-reviewed publications; no draft, review or attempt backfill.
SELECT capture_vocab_publication(id) FROM materials WHERE status='published';
CREATE VIEW v_curated_vocabulary AS
 SELECT c.id,c.deck_id,c.block_id,r.revision,r.payload,r.content_hash,i.position,m.author_id,
 d.payload->>'title' AS deck_title,d.payload->>'access' AS access,
 d.payload->>'collection_id' AS collection_id,d.payload->>'subject_id' AS subject_id,exam.exam_scope_id
 FROM vocab_cards c JOIN vocab_card_revisions r ON r.card_id=c.id
 JOIN materials m ON m.id=c.deck_id AND m.status='published' AND m.published_revision=r.revision
 JOIN material_revisions d ON d.material_id=m.id AND d.revision=m.published_revision AND d.payload->>'kind'='vocabulary-deck'
 JOIN vocab_deck_items i ON i.deck_id=c.deck_id AND i.revision=r.revision AND i.card_id=c.id
 JOIN collections exam ON exam.id=d.payload->>'collection_id' AND exam.kind='exam' AND exam.visibility='public'
 JOIN review_taxonomy subject ON subject.id=d.payload->>'subject_id' AND subject.level='subject' AND subject.active
 WHERE d.payload->>'access' IN ('free','pro');
ALTER TABLE review_items ADD COLUMN vocab_card_id text REFERENCES vocab_cards(id),ADD COLUMN vocab_content_hash text;
ALTER TABLE review_items ADD CONSTRAINT review_curated_identity CHECK(
 (vocab_card_id IS NULL AND canonical_id IS NOT NULL) OR
 (item_type='vocab' AND canonical_id IS NULL AND vocab_card_id=item_id AND vocab_content_hash IS NOT NULL AND vocab_content_hash ~ '^[0-9a-f]{64}$'));
CREATE TABLE vocab_exposures (
 user_id text NOT NULL REFERENCES users(id),card_id text NOT NULL REFERENCES vocab_cards(id),
 content_hash text NOT NULL,version integer NOT NULL DEFAULT 1,seen integer NOT NULL DEFAULT 0 CHECK(seen>=0),
 first_review_at timestamptz,last_exposure_at timestamptz,PRIMARY KEY(user_id,card_id)
);
CREATE TABLE vocab_presentations (
 id text PRIMARY KEY,user_id text NOT NULL REFERENCES users(id),card_id text NOT NULL REFERENCES vocab_cards(id),
 revision integer NOT NULL,content_hash text NOT NULL,state_version integer NOT NULL,
 mode text NOT NULL CHECK(mode IN ('recognition','cloze','mizo-to-english','english-to-mizo')),
 snapshot jsonb NOT NULL,issued_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 expires_at timestamptz NOT NULL DEFAULT clock_timestamp()+interval '2 hours',
 answered_at timestamptz,action text CHECK(action IN ('answer','reveal','defer')),chosen_index integer,result jsonb,
 CHECK(chosen_index IS NULL OR chosen_index BETWEEN 0 AND 5),
 FOREIGN KEY(card_id,revision) REFERENCES vocab_card_revisions(card_id,revision)
);
CREATE INDEX vocab_presentations_pending ON vocab_presentations(user_id,card_id,issued_at DESC) WHERE answered_at IS NULL;
CREATE FUNCTION vocab_presentation_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF OLD.answered_at IS NOT NULL OR ROW(OLD.id,OLD.user_id,OLD.card_id,OLD.revision,OLD.content_hash,OLD.state_version,OLD.mode,OLD.snapshot,OLD.issued_at,OLD.expires_at)
 IS DISTINCT FROM ROW(NEW.id,NEW.user_id,NEW.card_id,NEW.revision,NEW.content_hash,NEW.state_version,NEW.mode,NEW.snapshot,NEW.issued_at,NEW.expires_at)
 THEN RAISE EXCEPTION 'Vocabulary presentations and answered receipts are immutable'; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER vocab_presentation_immutable BEFORE UPDATE ON vocab_presentations FOR EACH ROW EXECUTE FUNCTION vocab_presentation_immutable();
CREATE TABLE vocab_attempts (
 id bigserial PRIMARY KEY,user_id text NOT NULL REFERENCES users(id),card_id text NOT NULL REFERENCES vocab_cards(id),
 revision integer NOT NULL,content_hash text NOT NULL,mode text NOT NULL,
 chosen_index integer NOT NULL CHECK(chosen_index BETWEEN 0 AND 5),chosen_text text NOT NULL,correct boolean NOT NULL,
 presentation_id text NOT NULL UNIQUE REFERENCES vocab_presentations(id),
 session_id text REFERENCES practice_study_sessions(id),at timestamptz NOT NULL DEFAULT clock_timestamp(),
 FOREIGN KEY(card_id,revision) REFERENCES vocab_card_revisions(card_id,revision)
);
CREATE INDEX vocab_attempts_latest ON vocab_attempts(user_id,card_id,at DESC,id DESC);
CREATE TABLE vocab_practice_receipts (
 user_id text NOT NULL REFERENCES users(id),request_key text NOT NULL,attempt_id bigint NOT NULL UNIQUE REFERENCES vocab_attempts(id),
 response jsonb NOT NULL,created_at timestamptz NOT NULL DEFAULT clock_timestamp(),PRIMARY KEY(user_id,request_key)
);
CREATE TABLE vocab_review_session_items (
 session_id text NOT NULL REFERENCES practice_study_sessions(id),card_id text NOT NULL REFERENCES vocab_cards(id),
 due_on date NOT NULL,was_due boolean NOT NULL,revision integer NOT NULL,content_hash text NOT NULL,
 presentation_id text NOT NULL UNIQUE REFERENCES vocab_presentations(id),opened_at timestamptz,
 attempt_id bigint UNIQUE REFERENCES vocab_attempts(id),PRIMARY KEY(session_id,card_id)
);
CREATE FUNCTION vocab_review_item_frozen() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF ROW(OLD.session_id,OLD.card_id,OLD.due_on,OLD.was_due,OLD.revision,OLD.content_hash,OLD.presentation_id)
 IS DISTINCT FROM ROW(NEW.session_id,NEW.card_id,NEW.due_on,NEW.was_due,NEW.revision,NEW.content_hash,NEW.presentation_id)
 OR (OLD.attempt_id IS NOT NULL AND OLD.attempt_id IS DISTINCT FROM NEW.attempt_id)
 THEN RAISE EXCEPTION 'Saved vocabulary review evidence is immutable'; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER vocab_review_item_frozen BEFORE UPDATE ON vocab_review_session_items FOR EACH ROW EXECUTE FUNCTION vocab_review_item_frozen();
CREATE TABLE vocab_review_completions (
 user_id text NOT NULL REFERENCES users(id),card_id text NOT NULL REFERENCES vocab_cards(id),scheduled_due date NOT NULL,
 session_id text NOT NULL REFERENCES practice_study_sessions(id),attempt_id bigint NOT NULL UNIQUE REFERENCES vocab_attempts(id),
 correct boolean NOT NULL,completed_on date NOT NULL,PRIMARY KEY(user_id,card_id,scheduled_due)
);
CREATE TABLE user_vocab_deck_mastery (
 user_id text NOT NULL REFERENCES users(id),deck_id text NOT NULL REFERENCES vocab_decks(id),
 proficient_at timestamptz,PRIMARY KEY(user_id,deck_id)
);
DO $$ DECLARE name text;BEGIN
 FOREACH name IN ARRAY ARRAY['vocab_decks','vocab_cards','vocab_card_revisions','vocab_deck_items','vocab_attempts','vocab_practice_receipts','vocab_review_completions'] LOOP
 EXECUTE format('CREATE TRIGGER immutable_%I BEFORE UPDATE OR DELETE ON %I FOR EACH ROW EXECUTE FUNCTION review_immutable()',name,name);
 END LOOP;
END $$;
GRANT SELECT ON v_curated_vocabulary TO mpsc;
GRANT SELECT,INSERT ON vocab_decks,vocab_cards,vocab_card_revisions,vocab_deck_items,vocab_attempts,vocab_practice_receipts,vocab_review_completions TO mpsc;
GRANT SELECT,INSERT,UPDATE ON vocab_exposures,vocab_presentations,vocab_review_session_items,user_vocab_deck_mastery TO mpsc;
GRANT USAGE,SELECT ON SEQUENCE vocab_attempts_id_seq TO mpsc;
COMMIT;
