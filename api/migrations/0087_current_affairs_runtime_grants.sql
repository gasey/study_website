BEGIN;
-- Existing production default privileges can grant ALL on newly created tables.
-- Explicitly replace those defaults for this feature's runtime role only.
REVOKE ALL ON ca_youtube_transcripts,ca_youtube_events,ca_source_revisions,ca_source_events FROM PUBLIC,mpsc;
GRANT SELECT,INSERT ON ca_youtube_transcripts,ca_youtube_events,ca_source_revisions,ca_source_events TO mpsc;
REVOKE ALL ON ca_youtube_channels,ca_youtube_videos,ca_youtube_drafts,ca_youtube_runs,ca_youtube_generation_calls,ca_source_feeds,ca_source_items,ca_source_drafts,ca_caption_calls FROM PUBLIC,mpsc;
GRANT SELECT,INSERT,UPDATE ON ca_youtube_channels,ca_youtube_videos,ca_youtube_drafts,ca_youtube_runs,ca_youtube_generation_calls,ca_source_feeds,ca_source_items,ca_source_drafts,ca_caption_calls TO mpsc;
REVOKE ALL ON SEQUENCE ca_youtube_runs_id_seq,ca_youtube_generation_calls_id_seq,ca_youtube_events_id_seq,ca_source_events_id_seq,ca_caption_calls_id_seq FROM PUBLIC,mpsc;
GRANT USAGE,SELECT ON SEQUENCE ca_youtube_runs_id_seq,ca_youtube_generation_calls_id_seq,ca_youtube_events_id_seq,ca_source_events_id_seq,ca_caption_calls_id_seq TO mpsc;
COMMIT;
