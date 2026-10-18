-- MPSC schema v2 -- designed against bank/mpsc_bank_v2.json as it actually is,
-- not against the ExamPaper type the v1 schema assumed.
--
-- Supersedes db/mpsc_schema.sql, which cannot hold the current bank:
--   * answer_index INTEGER NOT NULL  -> 11,458 questions have no answer
--   * year INTEGER NOT NULL          ->    324 papers have no year
--   * options JSONB NOT NULL         ->  8,020 descriptive questions have none
--   * difficulty NOT NULL CHECK      ->  1,027 questions have no difficulty
--   * subject TEXT NOT NULL          ->     47 questions have no subject
--   * no page / sitting / figure / passage / marks / answer_source columns
--
-- Key convention change: a missing answer is NULL, not -1. The sentinel was a
-- JSON artefact; in SQL it defeats every aggregate and every join. Loaders must
-- translate -1 -> NULL. The CHECK below then makes an out-of-range answer
-- impossible to store at all.

BEGIN;

CREATE TABLE IF NOT EXISTS sittings (
    id             TEXT PRIMARY KEY,
    exam_name      TEXT,
    exam_type      TEXT,
    year           INTEGER,
    month          TEXT
);

CREATE TABLE IF NOT EXISTS papers (
    id             TEXT PRIMARY KEY,          -- canonical Old_Questions/... path
    exam_type      TEXT NOT NULL
                     CHECK (exam_type IN ('Departmental','Direct','Direct_NG','LDE')),
    exam_name      TEXT,
    post           TEXT,                      -- only 27 of 1,938 populated
    paper_number   TEXT,                      -- roman: I..VI
    paper_subject  TEXT,
    year           INTEGER,                   -- 324 unknown; 22 and 18 are known-bad
    month          TEXT,
    kind           TEXT CHECK (kind IN ('mcq','descriptive')),
    source_file    TEXT,
    pdf_path       TEXT,
    sitting_id     TEXT REFERENCES sittings(id) ON DELETE SET NULL,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS figure_groups (
    id             TEXT PRIMARY KEY,
    paper_id       TEXT REFERENCES papers(id) ON DELETE CASCADE,
    page           INTEGER
);

CREATE TABLE IF NOT EXISTS passage_groups (
    id             TEXT PRIMARY KEY,
    passage        TEXT
);

CREATE TABLE IF NOT EXISTS questions (
    id             TEXT PRIMARY KEY,
    paper_id       TEXT REFERENCES papers(id) ON DELETE CASCADE,
    type           TEXT NOT NULL CHECK (type IN ('mcq','descriptive')),

    -- qnum is an int for most rows but "1(a)" for descriptive sub-parts, so the
    -- printed label and the sort position are two different things.
    qnum           TEXT,
    qnum_seq       INTEGER,
    page           INTEGER,                   -- 1-based, matches the source PDF

    question       TEXT NOT NULL,
    options        JSONB NOT NULL DEFAULT '[]'::jsonb,
    answer_index   INTEGER,                   -- NULL = unknown, never -1
    answer_source  TEXT CHECK (answer_source IN ('key','official','derived','inferred','none')),
    answer_key_ref TEXT,                      -- citation when an official key set it

    subject        TEXT,
    topic          TEXT,
    topic_label    TEXT,
    difficulty     TEXT CHECK (difficulty IN ('easy','medium','hard')),
    explanation    TEXT,                      -- empty on 77,733 of 77,751 rows
    marks          NUMERIC,                   -- int and float both occur
    model_answer   TEXT,                      -- null everywhere today

    has_diagram    BOOLEAN NOT NULL DEFAULT false,
    used_vision    BOOLEAN NOT NULL DEFAULT false,
    figure_group_id TEXT REFERENCES figure_groups(id) ON DELETE SET NULL,
    figure_image   TEXT,
    passage        TEXT,
    passage_id     TEXT REFERENCES passage_groups(id) ON DELETE SET NULL,
    essay_kind     TEXT CHECK (essay_kind IN ('essay','letter','precis','comprehension')),

    -- Review/quality flags from the build guide. Applied in the correction
    -- stage, not by extraction.
    compensated    BOOLEAN NOT NULL DEFAULT false,  -- withdrawn by MPSC; keep answer NULL
    figure_based   BOOLEAN NOT NULL DEFAULT false,
    key_disputed   BOOLEAN NOT NULL DEFAULT false,
    dispute_note   TEXT,
    source_defect  TEXT CHECK (source_defect IN ('duplicate-options','hand-transcribed-matching-table')),
    verified_by    TEXT,

    stem_hash      TEXT,
    search         TSVECTOR GENERATED ALWAYS AS (to_tsvector('english', question)) STORED,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- An answer must point at an option that exists. Verified to hold for all
    -- 77,751 current rows, including the 8 with answer_index 4 on 5-option
    -- questions. This is the invariant the answer-key loader must not break.
    CONSTRAINT answer_in_range CHECK (
        answer_index IS NULL
        OR (answer_index >= 0 AND answer_index < jsonb_array_length(options))
    ),
    -- A withdrawn question must not carry an answer.
    CONSTRAINT compensated_has_no_answer CHECK (
        NOT compensated OR answer_index IS NULL
    )
);

CREATE INDEX IF NOT EXISTS idx_questions_paper       ON questions(paper_id);
CREATE INDEX IF NOT EXISTS idx_questions_subject     ON questions(subject, topic);
CREATE INDEX IF NOT EXISTS idx_questions_stem_hash   ON questions(stem_hash);
CREATE INDEX IF NOT EXISTS idx_questions_search      ON questions USING GIN(search);
CREATE INDEX IF NOT EXISTS idx_questions_unanswered  ON questions(paper_id)
    WHERE type = 'mcq' AND answer_index IS NULL;
CREATE INDEX IF NOT EXISTS idx_papers_type_year      ON papers(exam_type, year);
CREATE INDEX IF NOT EXISTS idx_papers_sitting        ON papers(sitting_id);

-- Progress sync, carried over unchanged from v1.
CREATE TABLE IF NOT EXISTS attempts (
    id             BIGSERIAL PRIMARY KEY,
    question_id    TEXT REFERENCES questions(id) ON DELETE CASCADE,
    correct        BOOLEAN NOT NULL,
    at             TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ingest_jobs (
    pdf_key        TEXT PRIMARY KEY,
    stage          TEXT NOT NULL,
    status         TEXT NOT NULL,
    error          TEXT,
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMIT;
