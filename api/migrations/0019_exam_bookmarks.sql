CREATE TABLE IF NOT EXISTS user_exam_bookmarks (
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    collection_id TEXT NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, collection_id)
);

CREATE INDEX IF NOT EXISTS user_exam_bookmarks_collection_idx
    ON user_exam_bookmarks(collection_id);
