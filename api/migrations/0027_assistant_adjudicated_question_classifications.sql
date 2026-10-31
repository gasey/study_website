-- A later question-level adjudication can resolve conflicting prior
-- assistant-reviewed subject claims while preserving its distinct provenance.
ALTER TABLE question_classifications
    DROP CONSTRAINT IF EXISTS question_classifications_source_check;

ALTER TABLE question_classifications
    ADD CONSTRAINT question_classifications_source_check CHECK (source IN (
        'manual', 'assistant-adjudicated', 'assistant-reviewed',
        'exact-signature-propagated', 'legacy-migrated', 'model'
    ));
