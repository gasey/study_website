BEGIN;
-- Explicit owner decisions are distinct from independent and scoped AI reviews.
ALTER TABLE paper_workbench_reviews DROP CONSTRAINT paper_workbench_reviews_review_kind_check;
ALTER TABLE paper_workbench_reviews ADD CONSTRAINT paper_workbench_reviews_review_kind_check
 CHECK(review_kind IN ('independent','owner_ai','owner'));
ALTER TABLE paper_workbench_reviews DROP CONSTRAINT paper_review_attribution;
ALTER TABLE paper_workbench_reviews ADD CONSTRAINT paper_review_attribution CHECK (
 (review_kind='independent' AND review_model IS NULL AND review_evidence IS NULL)
 OR (review_kind='owner_ai' AND decision='approve' AND length(review_model)>3
   AND review_evidence IS NOT NULL AND jsonb_typeof(review_evidence)='object')
 OR (review_kind='owner' AND decision='approve' AND review_model IS NULL
   AND review_evidence IS NOT NULL AND jsonb_typeof(review_evidence)='object'
   AND review_evidence ?& ARRAY['approval_kind','owner_id','author_id','source_sha256','payload_hash','submission_id','inspections']
   AND review_evidence->>'approval_kind'='owner'
   AND review_evidence->>'owner_id'=reviewer_id
   AND review_evidence->>'payload_hash'=payload_hash
   AND review_evidence->>'submission_id'=submission_id
   AND (review_evidence->>'source_sha256') ~ '^[a-f0-9]{64}$'
   AND jsonb_typeof(review_evidence->'inspections')='array')
);
COMMIT;
