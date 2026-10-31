-- The learner bank should include published questions even when no answer
-- key is available. Held, withdrawn, and merged records remain excluded.
CREATE OR REPLACE VIEW v_all_questions AS
SELECT * FROM canonical_questions
 WHERE status = 'live';
