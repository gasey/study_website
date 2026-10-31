-- Allow a separate timed practice mode to score reviewed derived answers.
-- Official-key mocks remain on v_scorable and never include derived or inferred
-- claims. Derived-practice mocks can use official/key + derived answers, but
-- still exclude disputed keys and source defects. Legacy inferred answers stay
-- out of timed scoring.
BEGIN;

ALTER TABLE mock_sessions
    ADD COLUMN IF NOT EXISTS answer_mode TEXT NOT NULL DEFAULT 'official'
        CHECK (answer_mode IN ('official','derived-practice'));

ALTER TABLE attempts DROP CONSTRAINT IF EXISTS attempts_context_check;
ALTER TABLE attempts ADD CONSTRAINT attempts_context_check
    CHECK (context IN ('practice','mock','mock-derived','duel','cup','review','material'));

CREATE OR REPLACE VIEW v_mock_practice AS
SELECT * FROM canonical_questions
 WHERE status = 'live'
   AND answer_text IS NOT NULL
   AND answer_source IN ('official','key','derived')
   AND NOT key_disputed
   AND source_defect IS DISTINCT FROM 'duplicate-options';

GRANT SELECT ON v_mock_practice TO mpsc;

COMMIT;
