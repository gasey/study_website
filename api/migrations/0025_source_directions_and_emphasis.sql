-- Preserve typography and shared source instructions recovered by the
-- predecessor exam modules. Markup is a tiny bounded token format rendered
-- as React text nodes; these columns never store trusted HTML.

ALTER TABLE appearances
  ADD COLUMN IF NOT EXISTS direction TEXT,
  ADD COLUMN IF NOT EXISTS question_markup TEXT,
  ADD COLUMN IF NOT EXISTS options_markup JSONB,
  ADD COLUMN IF NOT EXISTS source_context_ref TEXT;

ALTER TABLE canonical_questions
  ADD COLUMN IF NOT EXISTS direction TEXT,
  ADD COLUMN IF NOT EXISTS question_markup TEXT,
  ADD COLUMN IF NOT EXISTS options_markup JSONB,
  ADD COLUMN IF NOT EXISTS passage TEXT,
  ADD COLUMN IF NOT EXISTS source_context_ref TEXT;

-- PostgreSQL expands SELECT * when a view is created, so views made before
-- these columns existed do not expose them automatically. Recreate the
-- question-serving views so the API can read the new source context.
CREATE OR REPLACE VIEW v_all_questions AS
SELECT * FROM canonical_questions WHERE status = 'live';

CREATE OR REPLACE VIEW v_scorable AS
SELECT * FROM canonical_questions
 WHERE status = 'live'
   AND answer_text IS NOT NULL
   AND answer_source IN ('official','key')
   AND NOT key_disputed
   AND source_defect IS DISTINCT FROM 'duplicate-options';

CREATE OR REPLACE VIEW v_practice AS
SELECT * FROM canonical_questions
 WHERE status = 'live'
   AND answer_text IS NOT NULL
   AND source_defect IS DISTINCT FROM 'duplicate-options';

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname='appearances_options_markup_array'
      AND conrelid='appearances'::regclass
  ) THEN
    ALTER TABLE appearances ADD CONSTRAINT appearances_options_markup_array
      CHECK (options_markup IS NULL OR jsonb_typeof(options_markup)='array');
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname='canonical_options_markup_array'
      AND conrelid='canonical_questions'::regclass
  ) THEN
    ALTER TABLE canonical_questions ADD CONSTRAINT canonical_options_markup_array
      CHECK (options_markup IS NULL OR jsonb_typeof(options_markup)='array');
  END IF;
END $$;
