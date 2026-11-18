BEGIN;
-- Private collection and review workflow only; no question/answer publication.
ALTER TABLE ca_source_feeds DROP CONSTRAINT ca_source_feeds_id_check;
ALTER TABLE ca_source_feeds ADD CONSTRAINT ca_source_feeds_id_check CHECK(id IN ('rbi-press','rbi-notifications','pib-releases','mizoram-dipr'));
INSERT INTO ca_source_feeds(id,title) VALUES ('pib-releases','PIB national releases'),('mizoram-dipr','Mizoram DIPR releases');
ALTER TABLE ca_source_revisions ADD COLUMN language text NOT NULL DEFAULT 'en';
CREATE TABLE ca_briefs (
 id text PRIMARY KEY,
 cadence text NOT NULL CHECK(cadence IN ('daily','weekly')),
 period_start date NOT NULL,
 period_end date NOT NULL CHECK(period_end>=period_start),
 current_hash text NOT NULL,
 status text NOT NULL DEFAULT 'source_ready' CHECK(status IN ('source_ready','draft_ready','needs_configuration','quota_wait','generation_failed')),
 last_error text,
 next_attempt_at timestamptz NOT NULL DEFAULT now(),
 updated_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(cadence,period_end)
);
CREATE TABLE ca_brief_inputs (
 brief_id text NOT NULL REFERENCES ca_briefs(id),
 content_hash text NOT NULL,
 payload jsonb NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(brief_id,content_hash)
);
CREATE TABLE ca_brief_drafts (
 id text PRIMARY KEY,
 brief_id text NOT NULL,
 content_hash text NOT NULL,
 model text NOT NULL,
 prompt_version text NOT NULL,
 payload jsonb NOT NULL,
 status text NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','rejected','exported')),
 material_id text,
 created_at timestamptz NOT NULL DEFAULT now(),
 FOREIGN KEY(brief_id,content_hash) REFERENCES ca_brief_inputs(brief_id,content_hash),
 UNIQUE(brief_id,content_hash,model,prompt_version)
);
ALTER TABLE ca_youtube_generation_calls ADD COLUMN brief_id text REFERENCES ca_briefs(id);
ALTER TABLE ca_youtube_generation_calls DROP CONSTRAINT ca_generation_one_target;
ALTER TABLE ca_youtube_generation_calls ADD CONSTRAINT ca_generation_one_target CHECK(num_nonnulls(video_id,source_item_id,brief_id)=1);
REVOKE ALL ON ca_briefs,ca_brief_inputs,ca_brief_drafts FROM PUBLIC,mpsc;
GRANT SELECT,INSERT,UPDATE ON ca_briefs TO mpsc;
GRANT SELECT,INSERT ON ca_brief_inputs,ca_brief_drafts TO mpsc;
GRANT UPDATE(status,material_id) ON ca_brief_drafts TO mpsc;
CREATE INDEX ca_brief_queue ON ca_briefs(next_attempt_at,period_end DESC) WHERE status<>'draft_ready';
COMMIT;
