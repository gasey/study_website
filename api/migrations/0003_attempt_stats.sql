-- Per-question answer statistics.
--
-- The prototype's option buttons can show what share of learners picked each
-- option (`opts(q, picked, onPick, votes)` — the `votes` argument, v3.dc.html
-- line 2603). That needs two things the schema does not have yet:
--
--   1. an index for "all attempts on this question", since
--      idx_attempts_user_cq leads with user_id and cannot serve it;
--   2. a way to count picks per option — attempts already store chosen_text,
--      so this is a GROUP BY, not a new column.
--
-- It also gives real difficulty, which the bank does not have: `difficulty`
-- is NULL on every row because the imported value was a default 'medium' on
-- 96% of questions. Difficulty measured from actual answer rates is the only
-- honest version of that field.

BEGIN;

CREATE INDEX IF NOT EXISTS idx_attempts_canonical ON attempts(canonical_id);

-- Counts per question. Deliberately a view, not a materialised view or a
-- counter column: at 77,751 questions and a personal-project attempt volume
-- this aggregates in milliseconds, and a counter column is one more thing to
-- keep honest when attempts are re-scored after a key correction.
CREATE OR REPLACE VIEW v_question_stats AS
SELECT canonical_id,
       COUNT(*)::int                                   AS attempts,
       COUNT(*) FILTER (WHERE correct)::int            AS correct,
       COUNT(DISTINCT user_id)::int                    AS learners,
       ROUND(AVG(CASE WHEN correct THEN 1 ELSE 0 END)::numeric, 3) AS accuracy
  FROM attempts
 WHERE canonical_id IS NOT NULL
 GROUP BY canonical_id;

-- Share of picks per option text, for the vote bars under a revealed option.
CREATE OR REPLACE VIEW v_option_picks AS
SELECT canonical_id, chosen_text, COUNT(*)::int AS picks
  FROM attempts
 WHERE canonical_id IS NOT NULL AND chosen_text IS NOT NULL
 GROUP BY canonical_id, chosen_text;

COMMIT;
