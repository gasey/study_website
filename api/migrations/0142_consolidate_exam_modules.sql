BEGIN;
-- Consolidate duplicate and multi-sitting exam modules published by 0141 so each
-- exam appears under a single card/module instead of separate year/department cards.
--
-- Safety invariants:
-- 1. Never modifies collection_papers / collection_sections of existing flagship
--    modules (including frozen editorial-protection baselines `udc` and
--    `combined-prelims`).
-- 2. Preserves all learner attempts, checkpoints, bookmarks, and bank_exam_catalog
--    links by repointing them to the consolidated target collection before removing
--    redundant 0141 child collections.
-- 3. Only creates a new consolidated parent collection when at least one of its
--    source child collections exists, so empty/test databases remain clean.

CREATE TEMP TABLE _exam_consolidation_targets (
    target_id   TEXT PRIMARY KEY,
    title       TEXT NOT NULL,
    position    INT NOT NULL,
    create_new  BOOLEAN NOT NULL
) ON COMMIT DROP;

INSERT INTO _exam_consolidation_targets (target_id, title, position, create_new) VALUES
    -- Existing flagship modules (never create/modify their papers here)
    ('udc',                         'Upper Division Clerk (UDC)',                 1,   false),
    ('ldc',                         'Lower Division Clerk (LDC)',                 2,   false),
    ('assistant',                   'Assistant Grade',                            3,   false),
    ('combined-prelims',            'Mizoram Civil Services Prelims',             4,   false),
    ('group-b-gazetted',            'Group B · Gazetted',                         5,   false),
    ('group-b-non-gazetted',        'Group B · Non-Gazetted',                     6,   false),
    -- Consolidated multi-sitting exam modules (created from 0141 child sittings)
    ('mes',                         'Mizoram Engineering Service (MES)',          50,  true),
    ('mcs-main',                    'Mizoram Civil Services Mains (MCS)',         51,  true),
    ('junior-engineer',             'Junior Engineer (JE)',                       52,  true),
    ('inspector-of-legal-metrology','Inspector of Legal Metrology',               53,  true),
    ('acf',                         'Assistant Conservator of Forest (ACF)',      54,  true),
    ('motor-vehicle-inspector',     'Motor Vehicle Inspector (MVI)',              55,  true),
    ('mizoram-horticulture-service','Mizoram Horticulture Service (Grade-V)',     56,  true),
    ('staff-nurse',                 'Staff Nurse',                                57,  true),
    ('computer-operator',           'Computer Operator',                          58,  true),
    ('research-investigator',       'Research Investigator',                      59,  true),
    ('stenographer',                'Stenographer (Grade II & III)',              60,  true),
    ('sub-inspector-fcs-ca',        'Sub-Inspector (FCS&CA)',                     61,  true),
    ('sub-inspector-police',        'Sub-Inspector of Police (UB)',               62,  true),
    ('lab-technician',              'Laboratory Technician',                      63,  true),
    ('inspector-of-taxes',          'Inspector of Taxes',                         64,  true),
    ('middle-school-teacher',       'Middle School Teacher',                      65,  true),
    ('primary-school-teacher',      'Primary School Teacher',                     66,  true);

CREATE TEMP TABLE _exam_consolidation_map (
    old_id    TEXT PRIMARY KEY,
    target_id TEXT NOT NULL REFERENCES _exam_consolidation_targets(target_id)
) ON COMMIT DROP;

INSERT INTO _exam_consolidation_map (old_id, target_id) VALUES
    -- Redundant UDC sitting cards (100% of papers already in `udc`)
    ('udc-contract-2016-under-art-cult',       'udc'),
    ('udc-under-agriculturre-ch-deptt',        'udc'),
    ('udc-under-excise-deptt-2018',            'udc'),
    ('udc-under-sad-2018',                     'udc'),
    ('udc-under-social-welfare-departm',       'udc'),
    ('udc-under-tourism-deptt-2018',           'udc'),
    ('udc-contract-under-forest-depart',       'udc'),
    -- Redundant LDC sitting cards (100% of papers already in `ldc`)
    ('lower-division-clerk-under-mpsc',        'ldc'),
    ('lower-division-clerk-february-20',       'ldc'),
    ('lower-division-clerk-march-2026',        'ldc'),
    -- Redundant Assistant / Assistant & UDC sitting cards (100% already in `assistant`)
    ('assistant-grade-2010-under-gom-a',       'assistant'),
    ('assistant-grade-2018',                   'assistant'),
    ('assistant-udc',                          'assistant'),
    ('assistant-udc-2025',                     'assistant'),
    -- Redundant MCS Prelims sitting cards (already covered by `combined-prelims`)
    ('mcs-combined-preliminary-2016',          'combined-prelims'),
    ('mcs-combined-preliminary-2017',          'combined-prelims'),
    ('mcs-preliminary-2018',                   'combined-prelims'),
    -- Redundant Group B sitting cards (100% already in `group-b-gazetted` / `group-b-non-gazetted`)
    ('combined-competitive-examination',       'group-b-gazetted'),
    ('departmental-examinations-for-su',       'group-b-gazetted'),
    ('group-b-non-gazetted-technical-c',       'group-b-non-gazetted'),
    ('group-b-non-gazetted-various-dec',       'group-b-non-gazetted'),
    ('group-b-non-gazetted-various-dep',       'group-b-non-gazetted'),
    -- Mizoram Engineering Service (MES)
    ('jr-grade-of-mes-ae-sdo-under-p-e',       'mes'),
    ('jr-grade-of-mes-ae-sdo-under-phe',       'mes'),
    ('jr-grade-of-mizoram-engineering-489741', 'mes'),
    ('jr-grade-of-mizoram-engineering-68f122', 'mes'),
    ('jr-grade-of-mizoram-engineering-cc2403', 'mes'),
    -- Mizoram Civil Services Mains (MCS)
    ('mcs-combined-2014',                      'mcs-main'),
    ('mcs-combined-preliminary-main-20',       'mcs-main'),
    ('mcs-main-2016',                          'mcs-main'),
    ('mcs-combined-main-2017',                 'mcs-main'),
    ('mcs-main-2018',                          'mcs-main'),
    -- Junior Engineer (JE)
    ('j-e-under-irrigation-wr-2018',           'junior-engineer'),
    ('j-e-under-pwd-2018',                     'junior-engineer'),
    ('je-contract-under-phe-department',       'junior-engineer'),
    ('je-electrical-under-phe-march-20',       'junior-engineer'),
    ('je-under-agri-farmers-welfare-ma',       'junior-engineer'),
    ('je-under-phe-pwd-department-2016',       'junior-engineer'),
    ('junior-engineer-je-2016-contract',       'junior-engineer'),
    -- Inspector of Legal Metrology
    ('inspector-of-legal-metrology-201',       'inspector-of-legal-metrology'),
    ('inspector-of-legal-metrology-und',       'inspector-of-legal-metrology'),
    -- Assistant Conservator of Forest (ACF)
    ('acf-2018',                               'acf'),
    ('assistant-conservator-of-forest',        'acf'),
    -- Motor Vehicle Inspector (MVI)
    ('mvi-2014',                               'motor-vehicle-inspector'),
    ('motor-vehicle-inspetor-under-tra',       'motor-vehicle-inspector'),
    -- Mizoram Horticulture Service (Grade-V)
    ('grade-v-of-mhs-november-2017-und',       'mizoram-horticulture-service'),
    ('grade-v-of-mizoram-horticulture',        'mizoram-horticulture-service'),
    -- Staff Nurse
    ('staff-nurse-2014',                       'staff-nurse'),
    ('staff-nurse-under-mimer-2018',           'staff-nurse'),
    -- Computer Operator
    ('computer-operator-contract-unde-41d197', 'computer-operator'),
    ('computer-operator-contract-unde-3bbf5c', 'computer-operator'),
    ('computer-operator-under-mimer-20',       'computer-operator'),
    -- Research Investigator
    ('research-investigator-archaeolog',       'research-investigator'),
    ('research-investigator-under-art',        'research-investigator'),
    -- Stenographer (Grade II & III)
    ('steno-grade-ii-2015-contract-und',       'stenographer'),
    ('stenographer-grade-ii',                  'stenographer'),
    -- Sub-Inspector (FCS&CA)
    ('sub-inspector-under-fcs-ca-2018',        'sub-inspector-fcs-ca'),
    ('si-under-fcs-cas-and-receptionis',       'sub-inspector-fcs-ca'),
    -- Sub-Inspector of Police (UB)
    ('sub-inspector-ub-under-home-dept',       'sub-inspector-police'),
    ('sub-inspector-of-police-ub-march',       'sub-inspector-police'),
    -- Laboratory Technician
    ('lab-technician-under-mimer-2018',        'lab-technician'),
    ('laboratory-technician-contract-u',       'lab-technician'),
    -- Inspector of Taxes
    ('inspector-of-taxes-2016-under-ta',       'inspector-of-taxes'),
    ('inspector-of-taxes-2018',                'inspector-of-taxes'),
    -- Middle School Teacher
    ('middle-school-teacher-2015',             'middle-school-teacher'),
    ('middle-school-teacher-under-scho',       'middle-school-teacher'),
    -- Primary School Teacher
    ('primary-school-teacher-2015',            'primary-school-teacher'),
    ('primary-teacher-general-under-sc',       'primary-school-teacher');

-- Restrict to mappings whose source collection actually exists in this database
-- (and whose existing target exists when create_new = false).
CREATE TEMP TABLE _active_map ON COMMIT DROP AS
SELECT m.old_id, m.target_id, t.title, t.position, t.create_new
  FROM _exam_consolidation_map m
  JOIN _exam_consolidation_targets t ON t.target_id = m.target_id
  JOIN collections src ON src.id = m.old_id
 WHERE t.create_new OR EXISTS (SELECT 1 FROM collections dst WHERE dst.id = m.target_id);

-- 1. Create new consolidated exam collections (only when source sittings exist).
INSERT INTO collections (
    id, title, kind, route, visibility, position, live_version,
    exam_scope_id, series_grouping, science_projection
)
SELECT DISTINCT
       am.target_id,
       am.title,
       'exam',
       '/exams/' || am.target_id,
       'public',
       am.position,
       1,
       COALESCE(
           (SELECT MIN(c.exam_scope_id)
              FROM _active_map am2
              JOIN collections c ON c.id = am2.old_id
             WHERE am2.target_id = am.target_id),
           'mizoram-recruitment'
       ),
       true,
       false
  FROM _active_map am
 WHERE am.create_new
ON CONFLICT (id) DO NOTHING;

-- 2. Populate collection_papers for newly created consolidated collections.
--    For `mcs-main`, exclude the 4 prelim papers already covered by `combined-prelims`.
INSERT INTO collection_papers (
    collection_id, version, paper_id, as_mock, section_path,
    allow_browse, allow_practice, rule_source
)
SELECT DISTINCT
       am.target_id,
       1,
       cp.paper_id,
       false,
       'papers',
       true,
       true,
       'platform-default'
  FROM _active_map am
  JOIN collections src ON src.id = am.old_id
  JOIN collection_papers cp
    ON cp.collection_id = src.id
   AND cp.version = src.live_version
 WHERE am.create_new
   AND NOT (
       am.target_id = 'mcs-main'
       AND cp.paper_id IN (
           'Old_Questions/Direct_2014-2018/MCS Combined 2014 Preliminary Exam Paper I.pdf',
           'Old_Questions/Direct_2014-2018/MCS Combined 2014 Preliminary Exam Paper II.pdf',
           'Old_Questions/Direct_2014-2018/1.Preliminary Paper-I.pdf',
           'Old_Questions/Direct_2014-2018/2.Preliminary paper-II.pdf'
       )
   )
ON CONFLICT (collection_id, version, paper_id) DO NOTHING;

-- 3. Populate collection_sections for newly created consolidated collections.
INSERT INTO collection_sections (
    collection_id, version, path, title, position, formats, query, pins, excludes
)
SELECT cp.collection_id,
       1,
       'papers',
       'Source papers',
       0,
       '{}',
       jsonb_build_object('paper_ids', to_jsonb(array_agg(DISTINCT cp.paper_id ORDER BY cp.paper_id))),
       '{}',
       '{}'
  FROM collection_papers cp
 WHERE cp.collection_id IN (SELECT DISTINCT target_id FROM _active_map WHERE create_new)
   AND cp.version = 1
 GROUP BY cp.collection_id
ON CONFLICT (collection_id, version, path) DO UPDATE
   SET query = EXCLUDED.query;

-- 4. Detach bank_exam_catalog sitting rows (collection_id is UNIQUE; sitting rows
--    stay intact with their bank_exam_papers & expectations) and repoint all
--    learner/workflow references to the consolidated target collection.
UPDATE bank_exam_catalog e
   SET collection_id = NULL,
       updated_at = now()
  FROM _active_map am
 WHERE e.collection_id = am.old_id;

UPDATE attempts a
   SET collection_id = am.target_id
  FROM _active_map am
 WHERE a.collection_id = am.old_id;

-- exam_study_checkpoints has PK (user_id, collection_id): preserve existing target row if any.
DELETE FROM exam_study_checkpoints esc
 USING _active_map am
 WHERE esc.collection_id = am.old_id
   AND EXISTS (
       SELECT 1 FROM exam_study_checkpoints existing
        WHERE existing.user_id = esc.user_id
          AND existing.collection_id = am.target_id
   );

UPDATE exam_study_checkpoints esc
   SET collection_id = am.target_id
  FROM _active_map am
 WHERE esc.collection_id = am.old_id;

-- user_exam_bookmarks has PK (user_id, collection_id): drop duplicate before repointing.
DELETE FROM user_exam_bookmarks ueb
 USING _active_map am
 WHERE ueb.collection_id = am.old_id
   AND EXISTS (
       SELECT 1 FROM user_exam_bookmarks existing
        WHERE existing.user_id = ueb.user_id
          AND existing.collection_id = am.target_id
   );

UPDATE user_exam_bookmarks ueb
   SET collection_id = am.target_id
  FROM _active_map am
 WHERE ueb.collection_id = am.old_id;

UPDATE mock_sessions ms
   SET collection_id = am.target_id
  FROM _active_map am
 WHERE ms.collection_id = am.old_id;

UPDATE practice_study_sessions pss
   SET collection_id = am.target_id
  FROM _active_map am
 WHERE pss.collection_id = am.old_id;

UPDATE exam_calendar_events ece
   SET collection_id = am.target_id
  FROM _active_map am
 WHERE ece.collection_id = am.old_id;

UPDATE calendar_entries ce
   SET collection_id = am.target_id
  FROM _active_map am
 WHERE ce.collection_id = am.old_id;

UPDATE editorial_assignments ea
   SET collection_id = am.target_id
  FROM _active_map am
 WHERE ea.collection_id = am.old_id;

UPDATE topic_trail_packs ttp
   SET collection_id = am.target_id
  FROM _active_map am
 WHERE ttp.collection_id = am.old_id;

UPDATE discovery_picks dp
   SET collection_id = am.target_id
  FROM _active_map am
 WHERE dp.collection_id = am.old_id;

UPDATE module_composition_drafts mcd
   SET collection_id = am.target_id
  FROM _active_map am
 WHERE mcd.collection_id = am.old_id;

UPDATE module_composition_history mch
   SET collection_id = am.target_id
  FROM _active_map am
 WHERE mch.collection_id = am.old_id;

-- 5. Remove the redundant 0141 child collections (cascades their own collection_papers/sections).
DELETE FROM collections c
 USING _active_map am
 WHERE c.id = am.old_id;

GRANT SELECT ON collections, collection_sections, collection_papers, bank_exam_catalog TO mpsc;
COMMIT;
