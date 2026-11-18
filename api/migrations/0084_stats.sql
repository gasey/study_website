BEGIN;
-- Isolated statistical releases; no question/assessment tables are touched.
CREATE TABLE stats_releases (
 id text PRIMARY KEY,
 metric_id text NOT NULL,
 content_hash text NOT NULL,
 source_url text NOT NULL,
 edition text NOT NULL,
 reference_period text NOT NULL,
 methodology text NOT NULL,
 fetched_at timestamptz NOT NULL DEFAULT now(),
 published_at timestamptz,
 published_by text,
 status text NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','published','rejected')),
 payload jsonb NOT NULL,
 UNIQUE(metric_id, content_hash)
);
CREATE INDEX stats_published ON stats_releases(metric_id,published_at DESC) WHERE status='published';
CREATE TABLE stats_checks (
 metric_id text PRIMARY KEY,
 attempted_at timestamptz NOT NULL DEFAULT now(),
 succeeded_at timestamptz,
 error text
);
CREATE TABLE stats_import_runs (
 id bigserial PRIMARY KEY,
 metric_id text NOT NULL,
 started_at timestamptz NOT NULL DEFAULT now(),
 finished_at timestamptz,
 status text NOT NULL CHECK(status IN ('running','unchanged','pending','published','failed')),
 release_id text REFERENCES stats_releases(id),
 error text
);
CREATE TABLE stats_decisions (
 id bigserial PRIMARY KEY,
 release_id text NOT NULL REFERENCES stats_releases(id),
 actor_id text NOT NULL,
 decision text NOT NULL CHECK(decision IN ('publish','reject')),
 note text NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE stats_source_watches (
 source_id text PRIMARY KEY,
 content_hash text,
 checked_at timestamptz,
 links jsonb NOT NULL DEFAULT '[]'::jsonb,
 needs_review boolean NOT NULL DEFAULT false,
 error text
);
GRANT SELECT,INSERT,UPDATE,DELETE ON stats_releases,stats_checks,stats_import_runs,stats_decisions,stats_source_watches TO mpsc;
GRANT USAGE,SELECT ON SEQUENCE stats_import_runs_id_seq,stats_decisions_id_seq TO mpsc;
COMMIT;
