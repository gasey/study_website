BEGIN;
-- Staff discovery index only; never a second canonical content store.
CREATE TABLE pdf_library_scans (
 id bigserial PRIMARY KEY,
 state text NOT NULL CHECK(state IN ('queued','running','completed','failed')),
 requested_by text REFERENCES users(id),
 created_at timestamptz NOT NULL DEFAULT now(),
 started_at timestamptz, heartbeat_at timestamptz, finished_at timestamptz,
 files_seen integer NOT NULL DEFAULT 0, files_hashed integer NOT NULL DEFAULT 0,
 error text
);
CREATE UNIQUE INDEX pdf_library_one_scan ON pdf_library_scans((true)) WHERE state IN ('queued','running');
CREATE TABLE pdf_library_files (
 id bigserial PRIMARY KEY, scan_id bigint NOT NULL REFERENCES pdf_library_scans(id),
 root text NOT NULL CHECK(root IN ('canonical','served','workbench','documents')),
 relative_path text NOT NULL, sha256 text NOT NULL CHECK(sha256 ~ '^[0-9a-f]{64}$'),
 bytes bigint NOT NULL CHECK(bytes>=0), mtime_ns bigint NOT NULL, ctime_ns bigint NOT NULL,
 valid_pdf boolean NOT NULL,
 UNIQUE(scan_id,root,relative_path)
);
CREATE INDEX pdf_library_hash ON pdf_library_files(scan_id,sha256);
CREATE INDEX pdf_library_scan_latest ON pdf_library_scans(id DESC) WHERE state='completed';
GRANT SELECT,INSERT,UPDATE ON pdf_library_scans,pdf_library_files TO mpsc;
GRANT USAGE,SELECT ON SEQUENCE pdf_library_scans_id_seq,pdf_library_files_id_seq TO mpsc;
COMMIT;
