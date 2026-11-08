BEGIN;
ALTER TABLE paper_workbench_reviews
 ADD COLUMN review_kind text NOT NULL DEFAULT 'independent' CHECK(review_kind IN ('independent','owner_ai')),
 ADD COLUMN review_model text,
 ADD COLUMN review_evidence jsonb,
 ADD CONSTRAINT paper_review_attribution CHECK (
  review_kind='independent' AND review_model IS NULL AND review_evidence IS NULL
  OR review_kind='owner_ai' AND decision='approve' AND length(review_model)>3
     AND review_evidence IS NOT NULL AND jsonb_typeof(review_evidence)='object'
 );
COMMIT;
