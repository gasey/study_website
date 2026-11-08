BEGIN;
-- Editorial configuration is server-owned; original bank rows and source IDs stay intact.
CREATE TABLE bank_source_providers (
 id text PRIMARY KEY, label text NOT NULL, kind text NOT NULL CHECK(kind IN ('exam-board','book','website','mock','other')),
 url text, active boolean NOT NULL DEFAULT true, created_by text REFERENCES users(id)
);
INSERT INTO bank_source_providers(id,label,kind,url) VALUES
 ('mpsc','Mizoram MPSC','exam-board','https://mpsc.mizoram.gov.in'),
 ('website','Website authored','website',NULL),('unknown','Source not assigned','other',NULL);
CREATE UNIQUE INDEX bank_provider_label ON bank_source_providers(lower(label)) WHERE active;
CREATE TABLE bank_scheme_revisions (
 scheme_id text NOT NULL, revision integer NOT NULL CHECK(revision>0), payload jsonb NOT NULL,
 actor_id text NOT NULL REFERENCES users(id), reason text NOT NULL CHECK(length(btrim(reason))>=20),
 created_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(scheme_id,revision)
);
CREATE TRIGGER bank_scheme_revisions_immutable BEFORE UPDATE OR DELETE ON bank_scheme_revisions
 FOR EACH ROW EXECUTE FUNCTION editorial_checks_immutable();
CREATE TABLE bank_paper_profiles (
 paper_id text PRIMARY KEY REFERENCES papers(id), provider_id text NOT NULL REFERENCES bank_source_providers(id),
 corpus text NOT NULL DEFAULT '', period text NOT NULL DEFAULT 'unknown' CHECK(period IN ('legacy','current','unknown')),
 scheme_id text, scheme_revision integer, scheme_paper_key text,
 payload jsonb NOT NULL DEFAULT '{}', context_fingerprint text NOT NULL,
 version integer NOT NULL DEFAULT 1, actor_id text NOT NULL REFERENCES users(id), updated_at timestamptz NOT NULL DEFAULT now(),
 FOREIGN KEY(scheme_id,scheme_revision) REFERENCES bank_scheme_revisions(scheme_id,revision),
 CHECK((scheme_id IS NULL AND scheme_revision IS NULL AND scheme_paper_key IS NULL) OR
       (scheme_id IS NOT NULL AND scheme_revision IS NOT NULL AND scheme_paper_key IS NOT NULL))
);
CREATE TABLE bank_question_contexts (
 question_id text PRIMARY KEY REFERENCES canonical_questions(id), appearance_id text NOT NULL REFERENCES appearances(id),
 source_version text NOT NULL, source_signature text NOT NULL, payload jsonb NOT NULL, version integer NOT NULL DEFAULT 1,
 actor_id text NOT NULL REFERENCES users(id), updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE bank_tag_resolutions (
 question_id text PRIMARY KEY REFERENCES canonical_questions(id), classification jsonb NOT NULL,
 appearance_id text NOT NULL REFERENCES appearances(id), source_signature text NOT NULL,
 reason text NOT NULL CHECK(length(btrim(reason))>=20), actor_id text NOT NULL REFERENCES users(id),
 updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE bank_cleanup_views (
 id text PRIMARY KEY, user_id text NOT NULL REFERENCES users(id), title text NOT NULL,
 filters jsonb NOT NULL, version integer NOT NULL DEFAULT 1, updated_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(user_id,title)
);
CREATE TABLE bank_repeat_relations (
 left_id text NOT NULL REFERENCES canonical_questions(id), right_id text NOT NULL REFERENCES canonical_questions(id),
 revision integer NOT NULL CHECK(revision>0), relation text NOT NULL CHECK(relation IN ('same-question','same-concept','extraction-duplicate','keep-separate')),
 left_appearance text NOT NULL REFERENCES appearances(id), right_appearance text NOT NULL REFERENCES appearances(id),
 left_version text NOT NULL,right_version text NOT NULL,actor_id text NOT NULL REFERENCES users(id),
 reason text NOT NULL CHECK(length(btrim(reason))>=20),created_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(left_id,right_id,revision),CHECK(left_id<right_id)
);
CREATE TRIGGER bank_repeat_relations_immutable BEFORE UPDATE OR DELETE ON bank_repeat_relations
 FOR EACH ROW EXECUTE FUNCTION editorial_checks_immutable();
CREATE INDEX bank_question_contexts_region ON bank_question_contexts((payload->>'region'));
CREATE INDEX bank_profiles_provider ON bank_paper_profiles(provider_id,period,paper_id);
CREATE INDEX bank_repeat_right ON bank_repeat_relations(right_id,left_id,revision DESC);
CREATE INDEX bank_cq_exact_stem ON canonical_questions(stem_norm) WHERE status<>'merged';
-- Definitions only. No existing question is reclassified by this migration.
INSERT INTO review_taxonomy(id,label,parent_id,level,version)
 SELECT 'english/writing','Writing','english','topic','2.1' WHERE EXISTS(SELECT 1 FROM review_taxonomy WHERE id='english')
 ON CONFLICT DO NOTHING;
INSERT INTO review_taxonomy(id,label,parent_id,level,version)
 SELECT id,label,'english/writing','subtopic','2.1' FROM (VALUES
 ('english/writing/essay','Essay writing'),('english/writing/precis','Précis writing'),('english/writing/letter','Letter writing')) v(id,label)
 WHERE EXISTS(SELECT 1 FROM review_taxonomy WHERE id='english/writing') ON CONFLICT DO NOTHING;
GRANT SELECT,INSERT,UPDATE ON bank_source_providers,bank_paper_profiles,bank_question_contexts,bank_tag_resolutions,bank_cleanup_views TO mpsc;
GRANT SELECT,INSERT ON bank_scheme_revisions,bank_repeat_relations TO mpsc;
ALTER TABLE mock_sessions ADD COLUMN paper_mode text NOT NULL DEFAULT 'practice' CHECK(paper_mode IN ('practice','full'));
ALTER TABLE mock_sessions ADD COLUMN scheme_snapshot jsonb;
COMMIT;
