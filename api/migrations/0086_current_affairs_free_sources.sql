BEGIN;
-- Additive private source staging; no learner/bank/answer/scoring changes.
ALTER TABLE ca_youtube_transcripts ALTER COLUMN automatic DROP NOT NULL;
ALTER TABLE ca_youtube_transcripts ADD COLUMN evidence_kind text NOT NULL DEFAULT 'captions' CHECK(evidence_kind IN ('captions','model_video_analysis'));
CREATE TABLE ca_source_feeds (
 id text PRIMARY KEY CHECK(id IN ('rbi-press','rbi-notifications')),
 title text NOT NULL,
 enabled boolean NOT NULL DEFAULT true,
 checked_at timestamptz,
 last_error text
);
INSERT INTO ca_source_feeds(id,title) VALUES ('rbi-press','RBI press releases'),('rbi-notifications','RBI notifications');
CREATE TABLE ca_source_items (
 id text PRIMARY KEY,
 feed_id text NOT NULL REFERENCES ca_source_feeds(id),
 source_url text NOT NULL,
 title text NOT NULL,
 published_at timestamptz NOT NULL,
 current_hash text NOT NULL,
 status text NOT NULL DEFAULT 'source_ready' CHECK(status IN ('source_ready','needs_configuration','quota_wait','draft_ready','generation_failed')),
 next_attempt_at timestamptz NOT NULL DEFAULT now(),
 last_error text,
 first_seen_at timestamptz NOT NULL DEFAULT now(),
 last_seen_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(feed_id,source_url)
);
CREATE INDEX ca_source_queue ON ca_source_items(next_attempt_at,published_at DESC) WHERE status<>'draft_ready';
CREATE TABLE ca_source_revisions (
 item_id text NOT NULL REFERENCES ca_source_items(id),
 content_hash text NOT NULL,
 title text NOT NULL,
 source_url text NOT NULL,
 published_at timestamptz NOT NULL,
 publication_raw text NOT NULL,
 timezone_basis text NOT NULL,
 cues jsonb NOT NULL,
 fetched_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(item_id,content_hash)
);
CREATE TABLE ca_source_drafts (
 id text PRIMARY KEY,
 item_id text NOT NULL REFERENCES ca_source_items(id),
 content_hash text NOT NULL,
 prompt_version text NOT NULL,
 model text NOT NULL,
 payload jsonb NOT NULL,
 status text NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','rejected','exported')),
 material_id text,
 created_at timestamptz NOT NULL DEFAULT now(),
 FOREIGN KEY(item_id,content_hash) REFERENCES ca_source_revisions(item_id,content_hash),
 UNIQUE(item_id,content_hash,prompt_version,model)
);
CREATE TABLE ca_source_events (
 id bigserial PRIMARY KEY,
 item_id text REFERENCES ca_source_items(id),
 actor_id text NOT NULL,
 action text NOT NULL,
 detail jsonb NOT NULL DEFAULT '{}',
 created_at timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE ca_youtube_generation_calls ALTER COLUMN video_id DROP NOT NULL;
ALTER TABLE ca_youtube_generation_calls ADD COLUMN source_item_id text REFERENCES ca_source_items(id);
ALTER TABLE ca_youtube_generation_calls ADD CONSTRAINT ca_generation_one_target CHECK(num_nonnulls(video_id,source_item_id)=1);
CREATE INDEX ca_generation_budget ON ca_youtube_generation_calls(started_at);
CREATE TABLE ca_caption_calls (
 id bigserial PRIMARY KEY,
 video_id text NOT NULL REFERENCES ca_youtube_videos(id),
 started_at timestamptz NOT NULL DEFAULT now(),
 status text NOT NULL DEFAULT 'started' CHECK(status IN ('started','succeeded','failed')),
 reserved_credits integer NOT NULL DEFAULT 1 CHECK(reserved_credits=1)
);
CREATE INDEX ca_caption_month_budget ON ca_caption_calls(started_at);
GRANT SELECT,INSERT,UPDATE ON ca_source_feeds,ca_source_items,ca_source_drafts,ca_caption_calls TO mpsc;
GRANT SELECT,INSERT ON ca_source_revisions,ca_source_events TO mpsc;
GRANT USAGE,SELECT ON SEQUENCE ca_source_events_id_seq,ca_caption_calls_id_seq TO mpsc;
COMMIT;
