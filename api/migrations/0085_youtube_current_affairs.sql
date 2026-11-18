BEGIN;
-- Private automation records. No bank, assessment, attempt or public fact writes.
CREATE TABLE ca_youtube_channels (
 id text PRIMARY KEY CHECK(id ~ '^UC[A-Za-z0-9_-]{22}$'),
 title text NOT NULL,
 enabled boolean NOT NULL DEFAULT true,
 languages jsonb NOT NULL DEFAULT '["hi-orig","hi","en-orig","en"]',
 checked_at timestamptz,
 last_error text,
 created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE ca_youtube_videos (
 id text PRIMARY KEY CHECK(id ~ '^[A-Za-z0-9_-]{11}$'),
 channel_id text NOT NULL REFERENCES ca_youtube_channels(id),
 title text NOT NULL,
 published_at timestamptz NOT NULL,
 published_precision text NOT NULL DEFAULT 'timestamp' CHECK(published_precision IN ('timestamp','day')),
 discovered_at timestamptz NOT NULL DEFAULT now(),
 status text NOT NULL DEFAULT 'discovered' CHECK(status IN ('discovered','transcript_pending','transcript_ready','needs_configuration','quota_wait','draft_ready','generation_failed')),
 transcript_hash text,
 attempts integer NOT NULL DEFAULT 0,
 next_attempt_at timestamptz NOT NULL DEFAULT now(),
 last_error text,
 updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ca_youtube_queue ON ca_youtube_videos(next_attempt_at,discovered_at) WHERE status<>'draft_ready';
CREATE TABLE ca_youtube_transcripts (
 video_id text NOT NULL REFERENCES ca_youtube_videos(id),
 content_hash text NOT NULL,
 language text NOT NULL,
 automatic boolean NOT NULL,
 provider text NOT NULL,
 cues jsonb NOT NULL,
 fetched_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(video_id,content_hash)
);
CREATE TABLE ca_youtube_drafts (
 id text PRIMARY KEY,
 video_id text NOT NULL REFERENCES ca_youtube_videos(id),
 transcript_hash text NOT NULL,
 prompt_version text NOT NULL,
 model text NOT NULL,
 payload jsonb NOT NULL,
 status text NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','rejected','exported')),
 material_id text,
 created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(video_id,transcript_hash,prompt_version,model),
 FOREIGN KEY(video_id,transcript_hash) REFERENCES ca_youtube_transcripts(video_id,content_hash)
);
CREATE TABLE ca_youtube_runs (
 id bigserial PRIMARY KEY,
 started_at timestamptz NOT NULL DEFAULT now(),
 finished_at timestamptz,
 status text NOT NULL DEFAULT 'running' CHECK(status IN ('running','succeeded','partial','failed')),
 summary jsonb NOT NULL DEFAULT '{}'
);
CREATE TABLE ca_youtube_generation_calls (
 id bigserial PRIMARY KEY,
 video_id text NOT NULL REFERENCES ca_youtube_videos(id),
 model text NOT NULL,
 started_at timestamptz NOT NULL DEFAULT now(),
 status text NOT NULL DEFAULT 'started' CHECK(status IN ('started','succeeded','failed'))
);
CREATE TABLE ca_youtube_events (
 id bigserial PRIMARY KEY,
 video_id text REFERENCES ca_youtube_videos(id),
 actor_id text NOT NULL,
 action text NOT NULL,
 detail jsonb NOT NULL DEFAULT '{}',
 created_at timestamptz NOT NULL DEFAULT now()
);
GRANT SELECT,INSERT,UPDATE ON ca_youtube_channels,ca_youtube_videos,ca_youtube_drafts,ca_youtube_runs,ca_youtube_generation_calls TO mpsc;
GRANT SELECT,INSERT ON ca_youtube_transcripts,ca_youtube_events TO mpsc;
GRANT USAGE,SELECT ON SEQUENCE ca_youtube_runs_id_seq,ca_youtube_generation_calls_id_seq,ca_youtube_events_id_seq TO mpsc;
COMMIT;
