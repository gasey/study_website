BEGIN;

-- Phase V.15 (§VII.5, §VII.16.5): first-party Guides reading library.
-- Strictly separate from user-generated `materials` CMS.
-- Includes Postgres full-text search (tsvector + GIN) on the new guide tables.

CREATE TABLE IF NOT EXISTS guides (
  id TEXT PRIMARY KEY,
  slug TEXT UNIQUE NOT NULL CHECK (slug ~ '^[a-z0-9][a-z0-9-]{1,100}$'),
  title TEXT NOT NULL CHECK (length(btrim(title)) BETWEEN 2 AND 200),
  subject_id TEXT REFERENCES review_taxonomy(id),
  topic_id TEXT REFERENCES review_taxonomy(id),
  exam_scope TEXT[] NOT NULL DEFAULT '{}',
  summary TEXT NOT NULL CHECK (length(btrim(summary)) BETWEEN 10 AND 1000),
  reading_minutes INTEGER NOT NULL DEFAULT 5 CHECK (reading_minutes BETWEEN 1 AND 240),
  status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'published', 'archived')),
  version INTEGER NOT NULL DEFAULT 1 CHECK (version > 0),
  review_due DATE,
  created_by TEXT REFERENCES users(id),
  updated_by TEXT REFERENCES users(id),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  search TSVECTOR GENERATED ALWAYS AS (
    setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
    setweight(to_tsvector('english', coalesce(summary, '')), 'B')
  ) STORED
);

CREATE TABLE IF NOT EXISTS guide_chapters (
  guide_id TEXT NOT NULL REFERENCES guides(id) ON DELETE CASCADE,
  ord INTEGER NOT NULL CHECK (ord >= 1),
  anchor TEXT NOT NULL CHECK (anchor ~ '^[a-z0-9][a-z0-9-]{0,80}$'),
  heading TEXT NOT NULL CHECK (length(btrim(heading)) BETWEEN 2 AND 240),
  body_markdown TEXT NOT NULL CHECK (length(btrim(body_markdown)) >= 10),
  search TSVECTOR GENERATED ALWAYS AS (
    setweight(to_tsvector('english', coalesce(heading, '')), 'A') ||
    setweight(to_tsvector('english', coalesce(body_markdown, '')), 'C')
  ) STORED,
  PRIMARY KEY (guide_id, anchor),
  UNIQUE (guide_id, ord)
);

CREATE TABLE IF NOT EXISTS guide_questions (
  guide_id TEXT NOT NULL,
  chapter_anchor TEXT NOT NULL,
  question_id TEXT NOT NULL REFERENCES canonical_questions(id) ON DELETE CASCADE,
  ord INTEGER NOT NULL DEFAULT 1 CHECK (ord >= 1),
  PRIMARY KEY (guide_id, chapter_anchor, question_id),
  FOREIGN KEY (guide_id, chapter_anchor) REFERENCES guide_chapters(guide_id, anchor) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_guides_status ON guides(status, slug);
CREATE INDEX IF NOT EXISTS idx_guides_search ON guides USING GIN (search);
CREATE INDEX IF NOT EXISTS idx_guide_chapters_search ON guide_chapters USING GIN (search);
CREATE INDEX IF NOT EXISTS idx_guide_questions_question ON guide_questions(question_id);

GRANT SELECT, INSERT, UPDATE ON guides, guide_chapters, guide_questions TO mpsc;
GRANT DELETE ON guide_chapters, guide_questions TO mpsc;

COMMIT;
