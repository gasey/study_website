-- MPSC schema v3 — migration from db/mpsc_schema_v2.sql
--
-- What changes, and why (full rationale: docs/BANK_SCHEMA_AND_EXTRACTION_GUIDE.md):
--   1. v2 `questions` holds one row per PRINTED APPEARANCE. It is renamed to
--      `appearances`. A new `canonical_questions` table holds one row per
--      DISTINCT question. Threads, reports, attempts, collections and
--      materials point at canonical ids, never at appearances.
--   2. Answers live on the canonical row as option TEXT. Each appearance maps
--      its printed A–D order to the canonical order via `option_order`, so a
--      repeat with shuffled options can never inherit the wrong letter.
--   3. Repeats: `times_asked`, `first_year`, `last_year` are maintained from
--      appearances (distinct sittings, so booklet series A/B/C/D count once).
--   4. Position on the page (`bbox`) and rendered page images for the
--      original-paper viewer.
--   5. Community, review, collections (formerly "modules") and study materials.
--
-- Safe to run on a populated v2 database. Every v2 column and CHECK survives.
-- Run inside one transaction; it either fully applies or not at all.
-- Target: PostgreSQL 14+.
--
-- REVIEW NOTES (2026-10-18) — changes from the first draft, each marked [R-n]:
--   [R-1] v_scorable admitted inferred answers into mocks and duels. Scored
--         play is now restricted to official/key, undisputed, defect-free.
--   [R-2] The backfill fired the per-row counts trigger 77,751 times and then
--         recomputed every row again. Trigger is disabled across the backfill
--         and the recount is one set-based statement.
--   [R-3] 12 hex chars of md5 is 48 bits; across 77,751 rows a collision is
--         ~1-in-90,000 and would abort the migration confusingly. Now 16.
--   [R-4] answer_source could land as NULL instead of 'none'.
--   [R-5] stem_norm was never populated, so idx_cq_stem_trgm indexed an
--         all-NULL column and the dedupe job had nothing to search.
--   [R-6] key_disputed / source_defect stayed on appearances only, so a
--         question with a disputed key was still scorable.
--   [R-7] subject is 90% the placeholder 'gk', topic holds PAPER NAMES, and
--         difficulty is 96% a default 'medium'. Those values are not data.
--         They are nulled; the columns stay because the product needs them.
--         topic_label (7,884 values, some ending '.pdf') is dropped outright.
--   [R-8] information_schema lookups had no table_schema filter.
--   [R-9] canonical_questions had no full-text index; v2's tsvector stayed
--         behind on appearances.

BEGIN;

-- ─────────────────────────────────────────────────────────────────────────
-- 0. Extensions
-- ─────────────────────────────────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS pg_trgm;   -- trigram index for duplicate candidates

-- ─────────────────────────────────────────────────────────────────────────
-- 0b. Pre-flight: refuse to migrate ambiguous answers          [R-1 support]
--
-- The whole design identifies the answer by option TEXT. When a question
-- prints the same option text twice, "the answer is 'Both A and B'" does not
-- say WHICH position was correct, and attempts.chosen_text cannot be rescored.
-- v2 already has a flag for this; this marks the rows so nothing silently
-- inherits the ambiguity.
-- ─────────────────────────────────────────────────────────────────────────
DO $$
DECLARE n INTEGER;
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables
                WHERE table_schema = current_schema() AND table_name = 'questions') THEN
        UPDATE questions q
           SET source_defect = 'duplicate-options'
         WHERE source_defect IS NULL
           AND jsonb_array_length(q.options) > 0
           AND (SELECT COUNT(DISTINCT e) FROM jsonb_array_elements_text(q.options) e)
             < jsonb_array_length(q.options);
        GET DIAGNOSTICS n = ROW_COUNT;
        RAISE NOTICE 'flagged % questions with duplicate option text', n;
    END IF;
END $$;

-- ─────────────────────────────────────────────────────────────────────────
-- 1. Concepts — "same fact, different question". Only reviewers create links.
-- ─────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS concepts (
    id          TEXT PRIMARY KEY,
    label       TEXT NOT NULL,
    subject     TEXT,
    topic       TEXT,
    created_by  TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ─────────────────────────────────────────────────────────────────────────
-- 2. Canonical questions — one row per distinct question
-- ─────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS canonical_questions (
    id              TEXT PRIMARY KEY,                 -- 'cq_' + 16-char hex; never reused  [R-3]
    type            TEXT NOT NULL CHECK (type IN ('mcq','descriptive')),
    question        TEXT NOT NULL,
    options         JSONB NOT NULL DEFAULT '[]'::jsonb,   -- canonical order
    answer_text     TEXT,                              -- correct option TEXT; NULL = unknown
    answer_source   TEXT CHECK (answer_source IN ('official','key','derived','inferred','none')),
    answer_key_ref  TEXT,

    subject         TEXT,
    -- Where `subject` came from. The same discipline as answer_source: a
    -- classification you cannot trace is a classification you cannot trust.
    -- 'paper'    — derived from a subject-specific paper ("Mechanical Eng. Paper-I")
    -- 'manual'   — set by a reviewer
    -- 'inferred' — model-classified; do not build scored features on it
    subject_source  TEXT CHECK (subject_source IN ('paper','manual','inferred')),
    topic           TEXT,
    difficulty      TEXT CHECK (difficulty IN ('easy','medium','hard')),
    concept_id      TEXT REFERENCES concepts(id) ON DELETE SET NULL,

    status          TEXT NOT NULL DEFAULT 'live'
                      CHECK (status IN ('live','held','withdrawn','merged')),
    held_reason     TEXT,                              -- e.g. 'report:typo_ocr x4'
    merged_into     TEXT REFERENCES canonical_questions(id),

    -- Quality flags promoted from the appearance row: these describe the
    -- QUESTION, not the printing, and v_scorable has to see them.      [R-6]
    key_disputed    BOOLEAN NOT NULL DEFAULT false,
    dispute_note    TEXT,
    source_defect   TEXT CHECK (source_defect IN ('duplicate-options','hand-transcribed-matching-table')),
    explanation     TEXT,

    times_asked     INTEGER NOT NULL DEFAULT 1,
    first_year      INTEGER,
    last_year       INTEGER,

    fingerprint     JSONB,                             -- {stem, option_set, answer, negation, numbers, minhash}
    stem_norm       TEXT,                              -- normalised stem, for trigram search  [R-5]
    search          TSVECTOR GENERATED ALWAYS AS (to_tsvector('english', question)) STORED,  -- [R-9]
    checked_at      DATE,                              -- current-affairs freshness ("Checked Oct 2026")
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- A known answer must be one of the options.
    CONSTRAINT cq_answer_is_an_option CHECK (
        answer_text IS NULL OR type <> 'mcq' OR options ? answer_text
    ),
    -- Merged rows must say where they went; live rows must not.
    CONSTRAINT cq_merge_target CHECK (
        (status = 'merged') = (merged_into IS NOT NULL)
    ),
    CONSTRAINT cq_no_self_merge CHECK (merged_into IS NULL OR merged_into <> id),
    -- Withdrawn (compensated by MPSC) questions carry no answer.
    CONSTRAINT cq_withdrawn_no_answer CHECK (status <> 'withdrawn' OR answer_text IS NULL)
);

CREATE INDEX IF NOT EXISTS idx_cq_subject     ON canonical_questions(subject, topic);
CREATE INDEX IF NOT EXISTS idx_cq_status      ON canonical_questions(status);
CREATE INDEX IF NOT EXISTS idx_cq_times_asked ON canonical_questions(times_asked DESC) WHERE status = 'live';
CREATE INDEX IF NOT EXISTS idx_cq_concept     ON canonical_questions(concept_id);
CREATE INDEX IF NOT EXISTS idx_cq_stem_trgm   ON canonical_questions USING GIN (stem_norm gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_cq_search      ON canonical_questions USING GIN (search);          -- [R-9]
CREATE INDEX IF NOT EXISTS idx_cq_merged_into ON canonical_questions(merged_into) WHERE merged_into IS NOT NULL;
-- The mock/duel draw is the hottest query in the product; index exactly it. [R-1]
CREATE INDEX IF NOT EXISTS idx_cq_scorable    ON canonical_questions(subject, topic)
    WHERE status = 'live' AND answer_source IN ('official','key')
      AND NOT key_disputed AND answer_text IS NOT NULL;

-- Normalised stem used by the trigram index and the dedupe job.          [R-5]
CREATE OR REPLACE FUNCTION norm_stem(t TEXT) RETURNS TEXT
LANGUAGE sql IMMUTABLE AS $$
    SELECT regexp_replace(
             regexp_replace(lower(COALESCE(t,'')), '[^a-z0-9\s]', ' ', 'g'),
             '\s+', ' ', 'g')
$$;

-- Follow merge chains to the live row. Every foreign-key reader should use this.
CREATE OR REPLACE FUNCTION resolve_cq(cid TEXT) RETURNS TEXT
LANGUAGE sql STABLE AS $$
    WITH RECURSIVE chain(id, next, depth) AS (
        SELECT id, merged_into, 0 FROM canonical_questions WHERE id = cid
        UNION ALL
        SELECT c.id, c.merged_into, chain.depth + 1
        FROM canonical_questions c JOIN chain ON c.id = chain.next
        WHERE chain.depth < 20
    )
    SELECT id FROM chain WHERE next IS NULL LIMIT 1;
$$;

-- ─────────────────────────────────────────────────────────────────────────
-- 3. Appearances — the v2 questions table, renamed and extended
-- ─────────────────────────────────────────────────────────────────────────
DO $$
BEGIN
    -- table_schema pinned so a 'questions' table in another schema cannot
    -- make this branch lie.                                              [R-8]
    IF EXISTS (SELECT 1 FROM information_schema.tables
                WHERE table_schema = current_schema() AND table_name = 'questions')
       AND NOT EXISTS (SELECT 1 FROM information_schema.tables
                WHERE table_schema = current_schema() AND table_name = 'appearances') THEN
        ALTER TABLE questions RENAME TO appearances;
        ALTER INDEX IF EXISTS idx_questions_paper      RENAME TO idx_app_paper;
        ALTER INDEX IF EXISTS idx_questions_subject    RENAME TO idx_app_subject;
        ALTER INDEX IF EXISTS idx_questions_stem_hash  RENAME TO idx_app_stem_hash;
        ALTER INDEX IF EXISTS idx_questions_search     RENAME TO idx_app_search;
        ALTER INDEX IF EXISTS idx_questions_unanswered RENAME TO idx_app_unanswered;
    END IF;
END $$;

ALTER TABLE appearances
    ADD COLUMN IF NOT EXISTS canonical_id  TEXT REFERENCES canonical_questions(id),
    ADD COLUMN IF NOT EXISTS option_order  INTEGER[],          -- option_order[i] = canonical index of printed option i
    ADD COLUMN IF NOT EXISTS series        TEXT,               -- booklet series A/B/C/D
    ADD COLUMN IF NOT EXISTS bbox          JSONB,              -- {"x0","y0","x1","y1"} PDF points, page-relative
    ADD COLUMN IF NOT EXISTS bbox_source   TEXT CHECK (bbox_source IN ('text','ocr','manual')),
    ADD COLUMN IF NOT EXISTS is_primary    BOOLEAN NOT NULL DEFAULT false;  -- the printing whose text/options are canonical

-- option_order must be a permutation of the canonical options when present.
ALTER TABLE appearances DROP CONSTRAINT IF EXISTS app_option_order_len;
ALTER TABLE appearances ADD CONSTRAINT app_option_order_len CHECK (
    option_order IS NULL OR array_length(option_order, 1) = jsonb_array_length(options)
);
ALTER TABLE appearances DROP CONSTRAINT IF EXISTS app_bbox_shape;
ALTER TABLE appearances ADD CONSTRAINT app_bbox_shape CHECK (
    bbox IS NULL OR (bbox ? 'x0' AND bbox ? 'y0' AND bbox ? 'x1' AND bbox ? 'y1')
);

CREATE INDEX IF NOT EXISTS idx_app_canonical ON appearances(canonical_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_app_one_primary ON appearances(canonical_id) WHERE is_primary;

-- ─────────────────────────────────────────────────────────────────────────
-- 4. Keep repeat counts honest
-- ─────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION refresh_cq_counts(cid TEXT) RETURNS VOID
LANGUAGE sql AS $$
    UPDATE canonical_questions c SET
        times_asked = GREATEST(1, sub.n),
        first_year  = sub.y0,
        last_year   = sub.y1,
        updated_at  = now()
    FROM (
        SELECT COUNT(DISTINCT COALESCE(p.sitting_id, p.id)) AS n,
               MIN(p.year) AS y0, MAX(p.year) AS y1
        FROM appearances a JOIN papers p ON p.id = a.paper_id
        WHERE a.canonical_id = cid
    ) sub
    WHERE c.id = cid;
$$;

CREATE OR REPLACE FUNCTION trg_app_counts() RETURNS TRIGGER
LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP IN ('UPDATE','DELETE') AND OLD.canonical_id IS NOT NULL THEN
        PERFORM refresh_cq_counts(OLD.canonical_id);
    END IF;
    IF TG_OP IN ('INSERT','UPDATE') AND NEW.canonical_id IS NOT NULL THEN
        PERFORM refresh_cq_counts(NEW.canonical_id);
    END IF;
    RETURN NULL;
END $$;

DROP TRIGGER IF EXISTS app_counts ON appearances;
CREATE TRIGGER app_counts
    AFTER INSERT OR DELETE OR UPDATE OF canonical_id, paper_id ON appearances
    FOR EACH ROW EXECUTE FUNCTION trg_app_counts();

-- ─────────────────────────────────────────────────────────────────────────
-- 5. Duplicate review queue
-- ─────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS dupe_candidates (
    id           BIGSERIAL PRIMARY KEY,
    a_id         TEXT NOT NULL REFERENCES canonical_questions(id),
    b_id         TEXT NOT NULL REFERENCES canonical_questions(id),
    tier         TEXT NOT NULL CHECK (tier IN ('exact','reordered','near','concept')),
    similarity   NUMERIC(5,4) NOT NULL,
    checks       JSONB NOT NULL,          -- {"answer":true,"negation":true,"numbers":false,"same_sitting":true}
    blocked      BOOLEAN NOT NULL,        -- any guard failed → merge is not allowed
    decision     TEXT CHECK (decision IN ('merge','concept','different')),
    decided_by   TEXT,
    decided_at   TIMESTAMPTZ,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT dc_ordered_pair CHECK (a_id < b_id),
    CONSTRAINT dc_blocked_cannot_merge CHECK (NOT blocked OR decision IS DISTINCT FROM 'merge'),
    UNIQUE (a_id, b_id)
);
CREATE INDEX IF NOT EXISTS idx_dc_open ON dupe_candidates(tier, similarity DESC) WHERE decision IS NULL;

-- ─────────────────────────────────────────────────────────────────────────
-- 6. Page images for the original-paper viewer
-- ─────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS page_images (
    paper_id   TEXT NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    page       INTEGER NOT NULL CHECK (page >= 1),
    url        TEXT NOT NULL,             -- object-storage key: pages/{paper_id}/{page}.webp
    width_px   INTEGER,
    height_px  INTEGER,
    pdf_w_pt   NUMERIC,                   -- to scale bbox → pixels
    pdf_h_pt   NUMERIC,
    bytes      INTEGER,
    PRIMARY KEY (paper_id, page)
);
ALTER TABLE papers
    ADD COLUMN IF NOT EXISTS page_count  INTEGER,
    ADD COLUMN IF NOT EXISTS pdf_url     TEXT,          -- full PDF in object storage
    ADD COLUMN IF NOT EXISTS pdf_bytes   INTEGER;

-- ─────────────────────────────────────────────────────────────────────────
-- 7. Users (minimal; the app's auth service owns the rest)
-- ─────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id          TEXT PRIMARY KEY,
    handle      TEXT UNIQUE NOT NULL,
    name        TEXT,
    role        TEXT NOT NULL DEFAULT 'learner'
                  CHECK (role IN ('learner','contributor','scholar','mentor','staff')),
    level       INTEGER NOT NULL DEFAULT 1,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Attempts move from appearance ids to canonical ids (keep the printing for analytics).
ALTER TABLE attempts
    ADD COLUMN IF NOT EXISTS user_id        TEXT REFERENCES users(id),
    ADD COLUMN IF NOT EXISTS canonical_id   TEXT REFERENCES canonical_questions(id),
    ADD COLUMN IF NOT EXISTS chosen_text    TEXT,       -- option text chosen, so re-scoring survives key fixes
    ADD COLUMN IF NOT EXISTS context        TEXT CHECK (context IN ('practice','mock','duel','cup','review','material')),
    ADD COLUMN IF NOT EXISTS rescored_at    TIMESTAMPTZ;
CREATE INDEX IF NOT EXISTS idx_attempts_user_cq ON attempts(user_id, canonical_id);

-- ─────────────────────────────────────────────────────────────────────────
-- 8. Discussion on a question
-- ─────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS posts (
    id            BIGSERIAL PRIMARY KEY,
    canonical_id  TEXT NOT NULL REFERENCES canonical_questions(id),
    kind          TEXT NOT NULL CHECK (kind IN ('explanation','doubt','reply')),
    parent_id     BIGINT REFERENCES posts(id) ON DELETE CASCADE,
    author_id     TEXT NOT NULL,                  -- users.id, or 'team'
    body          TEXT NOT NULL CHECK (length(body) BETWEEN 1 AND 5000),
    about_option  INTEGER,                        -- "Why not B?" — canonical option index
    pinned        BOOLEAN NOT NULL DEFAULT false,
    accepted      BOOLEAN NOT NULL DEFAULT false,
    before_fix    BOOLEAN NOT NULL DEFAULT false, -- set when the key changes after this was written
    hidden        BOOLEAN NOT NULL DEFAULT false, -- auto-hidden by abuse reports
    helpful       INTEGER NOT NULL DEFAULT 0,
    helpful_w     NUMERIC NOT NULL DEFAULT 0,     -- weighted: votes from people who answered correctly count more
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT post_reply_has_parent CHECK ((kind = 'reply') = (parent_id IS NOT NULL)),
    CONSTRAINT post_pin_is_explanation CHECK (NOT pinned OR kind = 'explanation')
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_posts_one_pin ON posts(canonical_id) WHERE pinned;
CREATE UNIQUE INDEX IF NOT EXISTS idx_posts_one_accepted ON posts(parent_id) WHERE accepted;
CREATE INDEX IF NOT EXISTS idx_posts_thread ON posts(canonical_id, kind, created_at);

CREATE TABLE IF NOT EXISTS post_votes (
    post_id     BIGINT NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    user_id     TEXT NOT NULL,
    weight      NUMERIC NOT NULL DEFAULT 1,       -- 1.5 if voter answered correctly, 1 otherwise
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (post_id, user_id)
);

-- ─────────────────────────────────────────────────────────────────────────
-- 9. Reports — two kinds, kept apart on purpose
-- ─────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS content_reports (     -- errors in the question itself → Review queue
    id              BIGSERIAL PRIMARY KEY,
    canonical_id    TEXT NOT NULL REFERENCES canonical_questions(id),
    kind            TEXT NOT NULL CHECK (kind IN ('wrong_key','typo_ocr','outdated','ambiguous','duplicate')),
    reporter_id     TEXT NOT NULL,
    note            TEXT,
    evidence_paper  TEXT REFERENCES papers(id),
    evidence_page   INTEGER,
    status          TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open','confirmed','fixed','rejected')),
    resolved_by     TEXT,
    resolved_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (canonical_id, kind, reporter_id)       -- "I see this too" = one row per person
);
CREATE INDEX IF NOT EXISTS idx_cr_open ON content_reports(canonical_id, kind) WHERE status = 'open';

CREATE TABLE IF NOT EXISTS abuse_reports (       -- conduct only → Reports
    id           BIGSERIAL PRIMARY KEY,
    post_id      BIGINT NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    reason       TEXT NOT NULL CHECK (reason IN ('spam','harassment','answer_leak','copyright','other')),
    reporter_id  TEXT NOT NULL,
    weight       NUMERIC NOT NULL DEFAULT 1,      -- Mentors count 2.5 (two Mentor reports = five learners)
    status       TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open','upheld','dismissed')),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (post_id, reporter_id)
);

-- Hold a question from mocks and cups: 3 independent reports, or 1 from a Scholar.
CREATE OR REPLACE FUNCTION trg_cr_hold() RETURNS TRIGGER
LANGUAGE plpgsql AS $$
DECLARE n INTEGER; scholar BOOLEAN;
BEGIN
    SELECT COUNT(*), bool_or(u.role IN ('scholar','mentor','staff'))
      INTO n, scholar
      FROM content_reports r LEFT JOIN users u ON u.id = r.reporter_id
     WHERE r.canonical_id = NEW.canonical_id AND r.kind = NEW.kind AND r.status IN ('open','confirmed');
    IF n >= 3 OR COALESCE(scholar, false) THEN
        UPDATE canonical_questions
           SET status = 'held', held_reason = 'report:' || NEW.kind || ' x' || n, updated_at = now()
         WHERE id = NEW.canonical_id AND status = 'live';
    END IF;
    RETURN NULL;
END $$;
DROP TRIGGER IF EXISTS cr_hold ON content_reports;
CREATE TRIGGER cr_hold AFTER INSERT ON content_reports FOR EACH ROW EXECUTE FUNCTION trg_cr_hold();

-- Auto-hide a post at weighted abuse score ≥ 5.
CREATE OR REPLACE FUNCTION trg_ar_hide() RETURNS TRIGGER
LANGUAGE plpgsql AS $$
BEGIN
    IF (SELECT COALESCE(SUM(weight),0) FROM abuse_reports WHERE post_id = NEW.post_id AND status = 'open') >= 5 THEN
        UPDATE posts SET hidden = true WHERE id = NEW.post_id;
    END IF;
    RETURN NULL;
END $$;
DROP TRIGGER IF EXISTS ar_hide ON abuse_reports;
CREATE TRIGGER ar_hide AFTER INSERT ON abuse_reports FOR EACH ROW EXECUTE FUNCTION trg_ar_hide();

-- ─────────────────────────────────────────────────────────────────────────
-- 10. Collections (UI: "Exams & tools"; formerly "modules")
-- ─────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS collections (
    id             TEXT PRIMARY KEY,               -- 'udc-ldc', 'mpsc-combined-prelims'
    title          TEXT NOT NULL,
    kind           TEXT NOT NULL CHECK (kind IN ('exam','guide','tool','practice')),
    route          TEXT,                           -- '/exams/udc-ldc' or a static app path
    visibility     TEXT NOT NULL DEFAULT 'public' CHECK (visibility IN ('public','pro','hidden')),
    position       INTEGER NOT NULL DEFAULT 0,
    live_version   INTEGER,
    draft_version  INTEGER,
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS collection_sections (
    collection_id  TEXT NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
    version        INTEGER NOT NULL,
    path           TEXT NOT NULL,                  -- 'gk/polity'
    title          TEXT NOT NULL,
    position       INTEGER NOT NULL,
    formats        TEXT[] NOT NULL DEFAULT '{}',   -- {'notes','flashcards','mind-map'}
    query          JSONB NOT NULL,                 -- {"subject":"gk","topic":"polity","year_gte":2016,"times_asked_gte":2}
    pins           TEXT[] NOT NULL DEFAULT '{}',   -- canonical ids forced in, in this order
    excludes       TEXT[] NOT NULL DEFAULT '{}',
    note           TEXT,                           -- collection-only note, e.g. "dropped from 2026 syllabus"
    PRIMARY KEY (collection_id, version, path)
);

CREATE TABLE IF NOT EXISTS collection_papers (   -- which full papers become mocks
    collection_id  TEXT NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
    version        INTEGER NOT NULL,
    paper_id       TEXT NOT NULL REFERENCES papers(id),
    as_mock        BOOLEAN NOT NULL DEFAULT true,
    PRIMARY KEY (collection_id, version, paper_id)
);

-- ─────────────────────────────────────────────────────────────────────────
-- 11. Study materials (anyone can create; no review at launch)
-- ─────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS materials (
    id            TEXT PRIMARY KEY,
    author_id     TEXT NOT NULL,
    title         TEXT NOT NULL,
    tags          TEXT[] NOT NULL DEFAULT '{}',
    blocks        JSONB NOT NULL,                 -- ordered [{type, ...}]; mock blocks store canonical ids
    status        TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft','published','removed')),
    published_at  TIMESTAMPTZ,
    helpful       INTEGER NOT NULL DEFAULT 0,
    helpful_w     NUMERIC NOT NULL DEFAULT 0,     -- studied voters 1.0, never-opened voters 0.25
    studied       INTEGER NOT NULL DEFAULT 0,
    impact_pts    NUMERIC,                        -- null until ≥ 50 learners marked studied
    impact_n      INTEGER,
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT mat_blocks_array CHECK (jsonb_typeof(blocks) = 'array')
);
CREATE INDEX IF NOT EXISTS idx_mat_author ON materials(author_id, status);
CREATE INDEX IF NOT EXISTS idx_mat_tags   ON materials USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_mat_rank   ON materials((helpful_w + COALESCE(impact_pts,0))) WHERE status = 'published';

CREATE TABLE IF NOT EXISTS material_votes (
    material_id  TEXT NOT NULL REFERENCES materials(id) ON DELETE CASCADE,
    user_id      TEXT NOT NULL,
    helpful      BOOLEAN NOT NULL DEFAULT false,
    studied      BOOLEAN NOT NULL DEFAULT false,
    studied_at   TIMESTAMPTZ,
    PRIMARY KEY (material_id, user_id)
);

-- ─────────────────────────────────────────────────────────────────────────
-- 12. Backfill: one canonical row per existing appearance (no merging here)
--     Merging is done by the dedupe job in Phase 3 of the guide.
--
--     The counts trigger is OFF across this section. Left on, the UPDATE
--     below fires it once per row — 77,751 aggregate queries — and the
--     recount at the end repeats the work.                            [R-2]
-- ─────────────────────────────────────────────────────────────────────────
ALTER TABLE appearances DISABLE TRIGGER app_counts;

INSERT INTO canonical_questions (id, type, question, options, answer_text, answer_source, answer_key_ref,
                                 subject, subject_source, topic, difficulty, status,
                                 key_disputed, dispute_note, source_defect, explanation, stem_norm)
SELECT 'cq_' || substr(md5(a.id), 1, 16),                      -- [R-3] 16 chars, not 12
       a.type, a.question, a.options,
       CASE WHEN a.answer_index IS NOT NULL THEN a.options ->> a.answer_index END,
       -- [R-4] 'none' is the fallback, never NULL: an unrecorded provenance
       -- must not be indistinguishable from an unset column.
       COALESCE(a.answer_source, 'none'),
       a.answer_key_ref,
       -- [R-7] subject/topic/difficulty are NOT carried. 'gk' on 90% of rows,
       -- paper names in topic, and a default 'medium' are noise that looks
       -- like data. NULL says "unknown", which is the truth. The classifier
       -- fills these and sets subject_source.
       NULL, NULL, NULL, NULL,
       CASE WHEN a.compensated THEN 'withdrawn' ELSE 'live' END,
       a.key_disputed, a.dispute_note, a.source_defect, NULLIF(a.explanation, ''),  -- [R-6]
       norm_stem(a.question)                                   -- [R-5]
FROM appearances a
WHERE a.canonical_id IS NULL
ON CONFLICT (id) DO NOTHING;

UPDATE appearances a
   SET canonical_id = 'cq_' || substr(md5(a.id), 1, 16),
       option_order = CASE WHEN jsonb_array_length(a.options) > 0
                           THEN ARRAY(SELECT generate_series(0, jsonb_array_length(a.options) - 1)) END,
       is_primary   = true
 WHERE a.canonical_id IS NULL;

-- Withdrawn questions must not keep an answer (mirrors v2 compensated_has_no_answer).
UPDATE canonical_questions SET answer_text = NULL WHERE status = 'withdrawn';

-- [R-2] One set-based pass instead of 77,751 function calls.
UPDATE canonical_questions c SET
    times_asked = GREATEST(1, s.n),
    first_year  = s.y0,
    last_year   = s.y1,
    updated_at  = now()
FROM (
    SELECT a.canonical_id AS cid,
           COUNT(DISTINCT COALESCE(p.sitting_id, p.id)) AS n,
           MIN(p.year) AS y0, MAX(p.year) AS y1
    FROM appearances a JOIN papers p ON p.id = a.paper_id
    WHERE a.canonical_id IS NOT NULL
    GROUP BY a.canonical_id
) s
WHERE c.id = s.cid;

ALTER TABLE appearances ENABLE TRIGGER app_counts;

-- Every appearance now has a canonical row.
ALTER TABLE appearances ALTER COLUMN canonical_id SET NOT NULL;

-- Point existing attempts at canonical rows.
UPDATE attempts t SET canonical_id = a.canonical_id
  FROM appearances a WHERE a.id = t.question_id AND t.canonical_id IS NULL;

-- [R-7] topic_label held paper names and '.pdf' filenames, fully redundant
-- with papers.exam_name. It is not promoted to canonical and is dropped here.
ALTER TABLE appearances DROP COLUMN IF EXISTS topic_label;

-- ─────────────────────────────────────────────────────────────────────────
-- 13. Read views the app uses
-- ─────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE VIEW v_bank AS
SELECT c.*,
       (SELECT jsonb_agg(jsonb_build_object(
                  'paper_id', a.paper_id, 'year', p.year, 'exam', p.exam_name,
                  'paper', p.paper_number, 'qnum', a.qnum, 'page', a.page, 'series', a.series,
                  'has_bbox', a.bbox IS NOT NULL)
                ORDER BY p.year DESC NULLS LAST)
          FROM appearances a JOIN papers p ON p.id = a.paper_id
         WHERE a.canonical_id = c.id) AS appearances,
       (SELECT COUNT(*) FROM posts WHERE canonical_id = c.id AND NOT hidden) AS post_count,
       (SELECT jsonb_agg(jsonb_build_object('kind', kind, 'n', n))
          FROM (SELECT kind, COUNT(*) n FROM content_reports
                 WHERE canonical_id = c.id AND status IN ('open','confirmed') GROUP BY kind) r) AS open_reports
FROM canonical_questions c
WHERE c.status <> 'merged';

-- [R-1] Questions counted in mocks, duels and cups.
--
-- Of 77,751 rows only ~12,478 reach this bar. That is the point. An inferred
-- answer is a model's guess: at ~91% high-confidence accuracy that is roughly
-- 3,500 questions whose "correct" answer is wrong, and a learner who is marked
-- wrong against a guess carries the error into the exam hall. Scoring happens
-- only against an official key.
--
-- Also excluded: disputed keys, and duplicate-option questions where the
-- answer TEXT cannot identify which position was correct.
CREATE OR REPLACE VIEW v_scorable AS
SELECT * FROM canonical_questions
 WHERE status = 'live'
   AND answer_text IS NOT NULL
   AND answer_source IN ('official','key')
   AND NOT key_disputed
   AND source_defect IS DISTINCT FROM 'duplicate-options';

-- [R-1] The wider pool for untimed practice. Callers MUST surface
-- answer_source in the UI so an inferred answer is visibly unverified.
CREATE OR REPLACE VIEW v_practice AS
SELECT * FROM canonical_questions
 WHERE status = 'live'
   AND answer_text IS NOT NULL
   AND source_defect IS DISTINCT FROM 'duplicate-options';

COMMIT;

-- ─────────────────────────────────────────────────────────────────────────
-- 14. Moderation
--     Moderator is an appointment, not a reputation tier: a Mentor can also
--     be a moderator. Scope is per collection (exam). Conduct only — keys and
--     explanations stay with reviewers.
--
--     [R-10] The handoff copy of this section quoted every function body with
--     a bare `$`. Postgres needs `$$` (or `$tag$`); a lone `$` is a syntax
--     error, so the whole block failed and no moderation table was created.
--     Verified by running it: ERROR: syntax error at or near "$".
-- ─────────────────────────────────────────────────────────────────────────
BEGIN;

CREATE TABLE IF NOT EXISTS moderators (
    user_id       TEXT PRIMARY KEY REFERENCES users(id),
    status        TEXT NOT NULL DEFAULT 'nominated'
                    CHECK (status IN ('nominated','active','paused','ended')),
    appointed_by  TEXT REFERENCES users(id),
    term_start    DATE,
    term_end      DATE,                               -- 6-month terms
    all_scopes    BOOLEAN NOT NULL DEFAULT false,     -- staff-granted global scope
    CONSTRAINT mod_term CHECK (term_end IS NULL OR term_end > term_start)
);

CREATE TABLE IF NOT EXISTS moderator_scopes (
    user_id        TEXT NOT NULL REFERENCES moderators(user_id) ON DELETE CASCADE,
    collection_id  TEXT NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, collection_id)
);

-- Which collection a question belongs to, for scoping reports on its thread.
-- NOTE: nothing populates this yet. Until it is filled, v_mod_queue returns
-- collection_id NULL for every row, and the scoped app query below matches
-- nothing — a moderator without all_scopes sees an empty queue.
CREATE TABLE IF NOT EXISTS question_collections (
    canonical_id   TEXT NOT NULL REFERENCES canonical_questions(id),
    collection_id  TEXT NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
    PRIMARY KEY (canonical_id, collection_id)
);

ALTER TABLE posts
    ADD COLUMN IF NOT EXISTS needs_approval  BOOLEAN NOT NULL DEFAULT false,  -- first 3 posts of new accounts
    ADD COLUMN IF NOT EXISTS hidden_by       TEXT,                            -- 'auto' | users.id
    ADD COLUMN IF NOT EXISTS hidden_reason   TEXT;

CREATE TABLE IF NOT EXISTS thread_locks (
    canonical_id  TEXT PRIMARY KEY REFERENCES canonical_questions(id),
    locked_by     TEXT NOT NULL,                     -- 'auto:live-mock' | users.id
    reason        TEXT,
    until         TIMESTAMPTZ,                       -- NULL = until unlocked
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Every moderation action, reversible. Never deleted.
CREATE TABLE IF NOT EXISTS mod_actions (
    id            BIGSERIAL PRIMARY KEY,
    actor_id      TEXT NOT NULL,                     -- users.id or 'auto'
    action        TEXT NOT NULL CHECK (action IN ('hide','unhide','approve','reject','lock','unlock',
                                                  'warn','mute','unmute','escalate','dismiss')),
    post_id       BIGINT REFERENCES posts(id),
    target_user   TEXT REFERENCES users(id),
    canonical_id  TEXT REFERENCES canonical_questions(id),
    rule          TEXT CHECK (rule IN ('spam','harassment','answer_leak','copyright','off_topic','other')),
    note          TEXT,
    reverses      BIGINT REFERENCES mod_actions(id), -- set on an undo
    sampled       BOOLEAN NOT NULL DEFAULT false,    -- picked for staff review (1 in 10)
    review_result TEXT CHECK (review_result IN ('upheld','reversed')),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_mod_actions_actor  ON mod_actions(actor_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_mod_actions_target ON mod_actions(target_user, created_at DESC);

-- Sanctions ladder (per person, rolling 90 days):
--   1 warning → 2 mute 24h → 3 mute 7d (+ no duels/cups) → 4 suspension (staff only).
--   answer_leak during a live cup: auto-hide + 7-day cup ban regardless of step.
CREATE TABLE IF NOT EXISTS sanctions (
    id          BIGSERIAL PRIMARY KEY,
    user_id     TEXT NOT NULL REFERENCES users(id),
    kind        TEXT NOT NULL CHECK (kind IN ('warning','mute','cup_ban','suspension')),
    step        INTEGER NOT NULL CHECK (step BETWEEN 1 AND 4),
    starts_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    ends_at     TIMESTAMPTZ,                         -- NULL for warnings
    action_id   BIGINT NOT NULL REFERENCES mod_actions(id),
    lifted_at   TIMESTAMPTZ,
    lifted_by   TEXT,
    -- Volunteer moderators cap at a 7-day mute; suspension is staff-only.
    -- [R-12] The original read `kind <> 'mute' OR ends_at <= starts_at + 7d`.
    -- With ends_at NULL that CHECK evaluates to NULL, which PASSES — so an
    -- indefinite mute was storable and the cap was bypassable. A mute must
    -- now carry an end date.
    CONSTRAINT sanction_mute_cap CHECK (
        kind <> 'mute'
        OR (ends_at IS NOT NULL AND ends_at <= starts_at + interval '7 days')
    )
);
CREATE INDEX IF NOT EXISTS idx_sanctions_active ON sanctions(user_id) WHERE lifted_at IS NULL;

CREATE TABLE IF NOT EXISTS appeals (
    id           BIGSERIAL PRIMARY KEY,
    sanction_id  BIGINT REFERENCES sanctions(id),
    action_id    BIGINT REFERENCES mod_actions(id),
    user_id      TEXT NOT NULL REFERENCES users(id),
    body         TEXT NOT NULL,
    status       TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open','granted','denied')),
    decided_by   TEXT,
    decided_at   TIMESTAMPTZ,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (action_id, user_id)                      -- one appeal per action
);

-- Guard rails the app must also enforce; these make the worst cases impossible to store.
CREATE OR REPLACE FUNCTION trg_mod_guard() RETURNS TRIGGER
LANGUAGE plpgsql AS $$
DECLARE author TEXT;
BEGIN
    IF NEW.actor_id = 'auto' THEN RETURN NEW; END IF;
    -- Not on your own post.
    IF NEW.post_id IS NOT NULL THEN
        SELECT author_id INTO author FROM posts WHERE id = NEW.post_id;
        IF author = NEW.actor_id THEN RAISE EXCEPTION 'moderators cannot act on their own posts'; END IF;
    END IF;
    IF NEW.target_user = NEW.actor_id THEN RAISE EXCEPTION 'moderators cannot act on themselves'; END IF;
    -- [R-11] The original selected the reversed action's actor into a variable
    -- and then never tested it, so the rule its comment described was not
    -- enforced. Dead code removed rather than guessed at: decide whether a
    -- moderator may reverse their OWN action (self-correction, usually fine)
    -- or only another's, then add the check here. Until then the app owns it.
    -- Sample 1 in 10 for staff review.
    NEW.sampled := (random() < 0.1);
    RETURN NEW;
END $$;
DROP TRIGGER IF EXISTS mod_guard ON mod_actions;
CREATE TRIGGER mod_guard BEFORE INSERT ON mod_actions FOR EACH ROW EXECUTE FUNCTION trg_mod_guard();

-- An appeal is decided by someone other than the moderator who acted.
CREATE OR REPLACE FUNCTION trg_appeal_guard() RETURNS TRIGGER
LANGUAGE plpgsql AS $$
DECLARE orig TEXT;
BEGIN
    IF NEW.decided_by IS NOT NULL THEN
        SELECT actor_id INTO orig FROM mod_actions WHERE id = NEW.action_id;
        IF orig = NEW.decided_by THEN RAISE EXCEPTION 'an appeal must be decided by a different moderator'; END IF;
    END IF;
    RETURN NEW;
END $$;
DROP TRIGGER IF EXISTS appeal_guard ON appeals;
CREATE TRIGGER appeal_guard BEFORE UPDATE OF decided_by ON appeals FOR EACH ROW EXECUTE FUNCTION trg_appeal_guard();

-- Moderator queue: open abuse reports + first posts, limited to the moderator's scope.
CREATE OR REPLACE VIEW v_mod_queue AS
SELECT 'report' AS item, ar.post_id, p.canonical_id, p.author_id, p.body,
       SUM(ar.weight) AS score, array_agg(DISTINCT ar.reason) AS reasons,
       MIN(ar.created_at) AS first_at, qc.collection_id
  FROM abuse_reports ar
  JOIN posts p ON p.id = ar.post_id
  LEFT JOIN question_collections qc ON qc.canonical_id = p.canonical_id
 WHERE ar.status = 'open'
 GROUP BY ar.post_id, p.canonical_id, p.author_id, p.body, qc.collection_id
UNION ALL
SELECT 'first_post', p.id, p.canonical_id, p.author_id, p.body, 0, ARRAY['first_post'], p.created_at, qc.collection_id
  FROM posts p LEFT JOIN question_collections qc ON qc.canonical_id = p.canonical_id
 WHERE p.needs_approval;
-- App query: SELECT * FROM v_mod_queue q WHERE EXISTS (SELECT 1 FROM moderator_scopes s
--   WHERE s.user_id = $me AND s.collection_id = q.collection_id) OR $me_all_scopes ORDER BY score DESC, first_at;

COMMIT;

-- ─────────────────────────────────────────────────────────────────────────
-- Post-migration checks (run by hand; all should return 0)
-- ─────────────────────────────────────────────────────────────────────────
-- SELECT COUNT(*) FROM appearances WHERE canonical_id IS NULL;
-- SELECT COUNT(*) FROM appearances a JOIN canonical_questions c ON c.id = a.canonical_id
--   WHERE a.answer_index IS NOT NULL AND c.answer_text <> a.options ->> a.answer_index;
-- SELECT COUNT(*) FROM canonical_questions WHERE status = 'merged' AND merged_into IS NULL;
-- SELECT COUNT(*) FROM canonical_questions c WHERE NOT EXISTS (SELECT 1 FROM appearances a WHERE a.canonical_id = c.id) AND c.status <> 'merged';
-- SELECT COUNT(*) FROM canonical_questions WHERE answer_source IS NULL;          -- [R-4]
-- SELECT COUNT(*) FROM canonical_questions WHERE stem_norm IS NULL;              -- [R-5]
--
-- Expected after backfill on the current bank:
--   77,751 appearances, 77,751 canonical rows
--   v_scorable  ≈ 12,478   (official + key, undisputed)
--   v_practice  ≈ 69,700   (everything with an answer and usable options)
--   source_defect = 'duplicate-options' ≈ 1,080
