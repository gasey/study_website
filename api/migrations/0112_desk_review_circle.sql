BEGIN;
ALTER TABLE study_desk_items ADD COLUMN discussion_state text NOT NULL DEFAULT 'none'
 CHECK(discussion_state IN ('none','needed','resolved'));
ALTER TABLE study_desk_items ADD CONSTRAINT desk_discussion_question_only
 CHECK(discussion_state='none' OR (question_id IS NOT NULL AND kind IN ('question','mistake')));
CREATE INDEX desk_discussion_items ON study_desk_items(desk_id,discussion_state,id DESC)
 WHERE deleted_at IS NULL AND discussion_state<>'none';
COMMIT;
