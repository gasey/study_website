-- Keep taxonomy-v2 classifications and their review provenance separate from
-- the legacy subject/topic columns. These rows are bank-owned and reloaded by
-- sync-bank.sh; user activity remains untouched.
BEGIN;

CREATE TABLE IF NOT EXISTS question_classifications (
    question_id       TEXT PRIMARY KEY REFERENCES canonical_questions(id) ON DELETE CASCADE,
    subject_id        TEXT NOT NULL,
    subject_label     TEXT NOT NULL,
    topic_id          TEXT,
    topic_label       TEXT,
    subtopic_id       TEXT,
    subtopic_label    TEXT,
    taxonomy_version  TEXT NOT NULL,
    source            TEXT NOT NULL CHECK (source IN (
        'manual','assistant-reviewed','exact-signature-propagated',
        'legacy-migrated','model'
    )),
    review_status     TEXT NOT NULL CHECK (review_status IN ('pending','approved','rejected')),
    confidence        NUMERIC CHECK (confidence IS NULL OR confidence BETWEEN 0 AND 1),
    evidence          TEXT,
    is_primary        BOOLEAN NOT NULL DEFAULT true,
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_qc_subject ON question_classifications(subject_id, review_status);
CREATE INDEX IF NOT EXISTS idx_qc_topic ON question_classifications(topic_id, review_status)
    WHERE topic_id IS NOT NULL;

COMMIT;
