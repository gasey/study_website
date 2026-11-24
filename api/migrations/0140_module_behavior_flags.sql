BEGIN;
-- FINNAPLAN v2 P1 (V.26): Per-module behaviour becomes data on collections
-- instead of hardcoded exam-id tuples in application code.
ALTER TABLE collections
  ADD COLUMN IF NOT EXISTS series_grouping    BOOLEAN NOT NULL DEFAULT false,
  ADD COLUMN IF NOT EXISTS science_projection BOOLEAN NOT NULL DEFAULT false,
  ADD COLUMN IF NOT EXISTS gk_gs_label        TEXT;

UPDATE collections
   SET series_grouping = true
 WHERE id IN ('udc', 'combined-prelims');

UPDATE collections
   SET science_projection = true
 WHERE id IN ('udc', 'ldc', 'assistant', 'combined-prelims');

UPDATE collections
   SET gk_gs_label = 'General Knowledge'
 WHERE id IN ('udc', 'ldc', 'assistant');

UPDATE collections
   SET gk_gs_label = 'General Studies'
 WHERE id = 'combined-prelims';

GRANT SELECT ON collections TO mpsc;
COMMIT;
