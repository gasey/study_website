-- Paper-first exam viewer: browse a source paper, see its coverage, and take
-- a timed test using that paper's printed order and option order.
BEGIN;

ALTER TABLE collection_papers
    ADD COLUMN IF NOT EXISTS section_path TEXT,
    ADD COLUMN IF NOT EXISTS display_title TEXT,
    ADD COLUMN IF NOT EXISTS duration_minutes INTEGER CHECK (duration_minutes BETWEEN 1 AND 240),
    ADD COLUMN IF NOT EXISTS marks_correct NUMERIC CHECK (marks_correct >= 0),
    ADD COLUMN IF NOT EXISTS marks_wrong NUMERIC CHECK (marks_wrong >= 0),
    ADD COLUMN IF NOT EXISTS instructions TEXT,
    ADD COLUMN IF NOT EXISTS allow_browse BOOLEAN NOT NULL DEFAULT true,
    ADD COLUMN IF NOT EXISTS allow_practice BOOLEAN NOT NULL DEFAULT true,
    ADD COLUMN IF NOT EXISTS rule_source TEXT NOT NULL DEFAULT 'platform-default'
        CHECK (rule_source IN ('official-notice','paper-instructions','reviewed','platform-default'));

-- Paper membership is explicit and versioned. The saved section manifest
-- remains the source for which papers belong to a module.
INSERT INTO collection_papers
    (collection_id,version,paper_id,as_mock,section_path,display_title,
     duration_minutes,marks_correct,marks_wrong,allow_browse,allow_practice,rule_source)
SELECT DISTINCT s.collection_id,s.version,p.id,
       (SELECT COUNT(DISTINCT v.id) FROM appearances a
         JOIN v_scorable v ON v.id=a.canonical_id WHERE a.paper_id=p.id) >= 20,
       s.path,COALESCE(NULLIF(p.paper_subject,''),p.exam_name)||
          CASE WHEN p.year IS NOT NULL THEN ' · '||p.year::text ELSE '' END,
       NULL::integer,1::numeric,0::numeric,true,true,'platform-default'
  FROM collection_sections s
  JOIN collections c ON c.id=s.collection_id AND c.live_version=s.version
  CROSS JOIN LATERAL jsonb_array_elements_text(COALESCE(s.query->'paper_ids','[]'::jsonb)) ids(paper_id)
  JOIN papers p ON p.id=ids.paper_id
ON CONFLICT (collection_id,version,paper_id) DO UPDATE SET
    section_path=EXCLUDED.section_path,
    display_title=COALESCE(collection_papers.display_title,EXCLUDED.display_title),
    as_mock=EXCLUDED.as_mock,
    allow_browse=true,allow_practice=true;

ALTER TABLE mock_sessions ADD COLUMN IF NOT EXISTS paper_id TEXT REFERENCES papers(id);

CREATE TABLE IF NOT EXISTS mock_session_questions (
    mock_id       TEXT NOT NULL REFERENCES mock_sessions(id) ON DELETE CASCADE,
    position      INTEGER NOT NULL CHECK (position >= 0),
    canonical_id  TEXT NOT NULL REFERENCES canonical_questions(id),
    appearance_id TEXT REFERENCES appearances(id),
    options       JSONB NOT NULL,
    PRIMARY KEY (mock_id,position),
    UNIQUE (mock_id,canonical_id)
);

CREATE INDEX IF NOT EXISTS idx_collection_papers_browse
    ON collection_papers(collection_id,version,paper_id) WHERE allow_browse;
CREATE INDEX IF NOT EXISTS idx_mock_paper ON mock_sessions(paper_id) WHERE paper_id IS NOT NULL;

COMMIT;
