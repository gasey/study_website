BEGIN;
ALTER TABLE topic_trail_packs ADD COLUMN canonical_ids text[] CHECK(canonical_ids IS NULL OR cardinality(canonical_ids) BETWEEN 1 AND 100);
COMMIT;
