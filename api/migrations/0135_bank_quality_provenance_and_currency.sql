BEGIN;

-- Phase V.16 (§VII.7, §VII.8): explanation provenance columns & question currency context checks.
-- Never edits earlier migrations; purely additive.

ALTER TABLE appearances
  ADD COLUMN IF NOT EXISTS explanation_model TEXT,
  ADD COLUMN IF NOT EXISTS explanation_prompt_version TEXT,
  ADD COLUMN IF NOT EXISTS explanation_generated_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS explanation_human_edited BOOLEAN NOT NULL DEFAULT false;

-- Backfill provenance where bank_contributions already recorded model_id/prompt_version in payload/rationale.
UPDATE appearances a
   SET explanation_model = COALESCE(a.explanation_model, src.model_id),
       explanation_prompt_version = COALESCE(a.explanation_prompt_version, src.prompt_version),
       explanation_generated_at = COALESCE(a.explanation_generated_at, src.created_at)
  FROM (
    SELECT DISTINCT ON (b.appearance_id)
           b.appearance_id,
           COALESCE(
             r.payload->'patch'->>'model_id',
             (regexp_match(COALESCE(r.payload->>'rationale', ''), 'model[_ ]id[=:]\s*([A-Za-z0-9._:-]+)'))[1]
           ) AS model_id,
           COALESCE(
             r.payload->'patch'->>'prompt_version',
             (regexp_match(COALESCE(r.payload->>'rationale', ''), 'prompt[_ ]version[=:]\s*([A-Za-z0-9._:-]+)'))[1]
           ) AS prompt_version,
           b.created_at
      FROM bank_contributions b
      JOIN contribution_revisions r
        ON r.contribution_id = b.id AND r.revision = b.revision
     WHERE b.appearance_id IS NOT NULL
       AND b.kind IN ('explanation', 'answer')
       AND (
         r.payload->'patch' ? 'model_id'
         OR COALESCE(r.payload->>'rationale', '') ~* 'model[_ ]id[=:]'
       )
     ORDER BY b.appearance_id, b.created_at DESC
  ) src
 WHERE a.id = src.appearance_id
   AND src.model_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_appearances_explanation_model
  ON appearances(explanation_model)
  WHERE explanation_model IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_bank_question_contexts_scheme_status
  ON bank_question_contexts((payload->>'scheme_status'))
  WHERE payload ? 'scheme_status';

CREATE INDEX IF NOT EXISTS idx_bank_question_contexts_time_behavior
  ON bank_question_contexts((payload->>'time_behavior'))
  WHERE payload ? 'time_behavior';

COMMIT;
