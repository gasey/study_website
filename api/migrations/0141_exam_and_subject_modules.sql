BEGIN;
-- FINNAPLAN v2 P3 (V.28a): Publish top 5 cross-exam Subject modules (kind='practice',
-- taxonomy-defined, no paper_ids) AND publish all non-empty curated exams from
-- bank_exam_catalog as searchable Exam modules (kind='exam', paper-backed).

-- 1. Top 5 cross-exam Subject modules (verified against live review_taxonomy).
INSERT INTO collections (
    id, title, kind, route, visibility, position, live_version,
    exam_scope_id, series_grouping, science_projection, gk_gs_label
)
VALUES
    ('subject-english',     'English',                     'practice', '/subjects/english',     'public', 20, 1, 'mizoram-recruitment', true, false, NULL),
    ('subject-mathematics', 'Mathematics & Arithmetic',    'practice', '/subjects/mathematics', 'public', 21, 1, 'mizoram-recruitment', true, false, NULL),
    ('subject-reasoning',   'Reasoning & Aptitude',        'practice', '/subjects/reasoning',   'public', 22, 1, 'mizoram-recruitment', true, false, NULL),
    ('subject-gk-gs',       'General Knowledge & Studies', 'practice', '/subjects/gk-gs',       'public', 23, 1, 'mizoram-recruitment', true, true,  'General Knowledge & Studies'),
    ('subject-mizo',        'Mizo',                        'practice', '/subjects/mizo',        'public', 24, 1, 'mizoram-recruitment', true, false, NULL)
ON CONFLICT (id) DO NOTHING;

INSERT INTO collection_sections (collection_id, version, path, title, position, formats, query, pins, excludes)
VALUES
    ('subject-english',     1, 'all',               'All English questions',               0, '{}', '{"subject_id":"english"}'::jsonb,                '{}', '{}'),
    ('subject-mathematics', 1, 'all',               'All Mathematics questions',           0, '{}', '{"subject_id":"mathematics"}'::jsonb,            '{}', '{}'),
    ('subject-reasoning',   1, 'all',               'All Reasoning & Aptitude questions',  0, '{}', '{"subject_id":"reasoning-and-aptitude"}'::jsonb, '{}', '{}'),
    ('subject-gk-gs',       1, 'general-studies',   'General Studies',                     0, '{}', '{"subject_id":"general-studies"}'::jsonb,        '{}', '{}'),
    ('subject-gk-gs',       1, 'general-knowledge', 'General Knowledge',                   1, '{}', '{"subject_id":"general-knowledge"}'::jsonb,      '{}', '{}'),
    ('subject-mizo',        1, 'all',               'All Mizo questions',                  0, '{}', '{"subject_id":"mizo"}'::jsonb,                   '{}', '{}')
ON CONFLICT (collection_id, version, path) DO NOTHING;

-- 2. Publish all non-empty unlinked curated exams from bank_exam_catalog as exam modules.
CREATE TEMP TABLE _new_exam_modules ON COMMIT DROP AS
WITH candidate_exams AS (
    SELECT e.id AS exam_id,
           btrim(regexp_replace(e.title, '`+$', '')) AS clean_title,
           COALESCE(MIN(p.exam_scope_id), 'mizoram-recruitment') AS exam_scope_id,
           COUNT(DISTINCT a.canonical_id)::int AS question_count,
           array_agg(DISTINCT bep.paper_id ORDER BY bep.paper_id) AS paper_ids
      FROM bank_exam_catalog e
      JOIN bank_exam_papers bep ON bep.exam_id = e.id
      JOIN papers p ON p.id = bep.paper_id
      JOIN appearances a ON a.paper_id = bep.paper_id
     WHERE e.collection_id IS NULL
     GROUP BY e.id, e.title
    HAVING COUNT(DISTINCT a.canonical_id) > 0
), slugged AS (
    SELECT exam_id,
           clean_title,
           exam_scope_id,
           question_count,
           paper_ids,
           btrim(left(btrim(regexp_replace(lower(clean_title), '[^a-z0-9]+', '-', 'g'), '-'), 32), '-') AS base_slug,
           row_number() OVER (ORDER BY question_count DESC, clean_title, exam_id) AS pos_rank
      FROM candidate_exams
), deduped AS (
    SELECT exam_id,
           clean_title,
           exam_scope_id,
           question_count,
           paper_ids,
           pos_rank,
           CASE
             WHEN length(base_slug) >= 2
              AND count(*) OVER (PARTITION BY base_slug) = 1
              AND NOT EXISTS (SELECT 1 FROM collections c WHERE c.id = base_slug)
             THEN base_slug
             ELSE left(COALESCE(NULLIF(base_slug, ''), 'exam'), 31) || '-' || substr(md5(exam_id), 1, 6)
           END AS slug
      FROM slugged
)
SELECT exam_id,
       btrim(regexp_replace(slug, '-+', '-', 'g'), '-') AS slug,
       clean_title,
       exam_scope_id,
       paper_ids,
       100 + pos_rank::int AS position
  FROM deduped;

INSERT INTO collections (
    id, title, kind, route, visibility, position, live_version,
    exam_scope_id, series_grouping, science_projection
)
SELECT slug,
       clean_title,
       'exam',
       '/exams/' || slug,
       'public',
       position,
       1,
       exam_scope_id,
       true,
       false
  FROM _new_exam_modules
ON CONFLICT (id) DO NOTHING;

INSERT INTO collection_papers (
    collection_id, version, paper_id, as_mock, section_path,
    allow_browse, allow_practice, rule_source
)
SELECT m.slug,
       1,
       pid,
       false,
       'papers',
       true,
       true,
       'platform-default'
  FROM _new_exam_modules m
  CROSS JOIN LATERAL unnest(m.paper_ids) AS pid
ON CONFLICT (collection_id, version, paper_id) DO NOTHING;

INSERT INTO collection_sections (
    collection_id, version, path, title, position, formats, query, pins, excludes
)
SELECT m.slug,
       1,
       'papers',
       'Source papers',
       0,
       '{}',
       jsonb_build_object('paper_ids', to_jsonb(m.paper_ids)),
       '{}',
       '{}'
  FROM _new_exam_modules m
ON CONFLICT (collection_id, version, path) DO NOTHING;

UPDATE bank_exam_catalog e
   SET collection_id = m.slug,
       updated_at = now()
  FROM _new_exam_modules m
 WHERE e.id = m.exam_id
   AND e.collection_id IS NULL;

GRANT SELECT ON collections, collection_sections, collection_papers, bank_exam_catalog TO mpsc;
COMMIT;
