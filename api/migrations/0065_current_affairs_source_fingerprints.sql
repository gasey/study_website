BEGIN;
-- Durable published links must survive byte-identical bank upserts that change xmin.
-- Existing un-fingerprinted links are withheld until a new reviewed revision;
-- never reconstruct evidence and present it as historical review.
ALTER TABLE current_affairs_links ADD COLUMN source_fingerprint text
 CHECK(source_fingerprint IS NULL OR source_fingerprint ~ '^[0-9a-f]{64}$');
COMMIT;
