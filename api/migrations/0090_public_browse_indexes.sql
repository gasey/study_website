BEGIN;
-- Measured on a fresh production-dump clone for Finnaplan V.1. Both
-- indexes allow index-only reads: collection totals repeatedly resolve
-- approved taxonomy membership and canonical-to-source-paper identity.
CREATE INDEX browse_appearances_canonical_paper
    ON appearances(canonical_id, paper_id);
CREATE INDEX browse_approved_subject_topic
    ON question_classifications(subject_id, topic_id, question_id)
    WHERE review_status = 'approved';
COMMIT;
