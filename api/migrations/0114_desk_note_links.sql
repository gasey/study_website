BEGIN;
ALTER TABLE study_desk_items ADD CONSTRAINT desk_item_id_room UNIQUE(id,desk_id);
ALTER TABLE study_desk_messages ADD COLUMN note_id text;
ALTER TABLE study_desk_messages ADD CONSTRAINT desk_message_note_same_room
 FOREIGN KEY(note_id,desk_id) REFERENCES study_desk_items(id,desk_id);
CREATE INDEX desk_message_note_links ON study_desk_messages(note_id) WHERE note_id IS NOT NULL;
COMMIT;
