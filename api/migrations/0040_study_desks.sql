BEGIN;
CREATE TABLE personal_desks (
 user_id TEXT PRIMARY KEY REFERENCES users(id), document JSONB NOT NULL DEFAULT '{}',
 version INTEGER NOT NULL DEFAULT 1 CHECK(version>0), updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE study_desks (
 id TEXT PRIMARY KEY,owner_id TEXT NOT NULL REFERENCES users(id),name TEXT NOT NULL CHECK(length(name) BETWEEN 3 AND 100),
 goal TEXT NOT NULL DEFAULT '' CHECK(length(goal)<=500),closed_at TIMESTAMPTZ,
 version INTEGER NOT NULL DEFAULT 1,created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE study_desk_members (
 desk_id TEXT REFERENCES study_desks(id),user_id TEXT REFERENCES users(id),
 joined_at TIMESTAMPTZ NOT NULL DEFAULT now(),left_at TIMESTAMPTZ,
 sharing JSONB NOT NULL DEFAULT '{"progress":false,"mistakes":false,"times":false}',muted BOOLEAN NOT NULL DEFAULT false,
 PRIMARY KEY(desk_id,user_id)
);
CREATE INDEX desk_members_by_user ON study_desk_members(user_id,desk_id) WHERE left_at IS NULL;
CREATE TABLE study_desk_invites (
 id TEXT PRIMARY KEY,desk_id TEXT NOT NULL REFERENCES study_desks(id),sender_id TEXT NOT NULL REFERENCES users(id),
 recipient_id TEXT NOT NULL REFERENCES users(id),state TEXT NOT NULL DEFAULT 'pending' CHECK(state IN ('pending','accepted','declined','cancelled','expired')),
 expires_at TIMESTAMPTZ NOT NULL DEFAULT now()+interval '7 days',created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX desk_one_pending_invite ON study_desk_invites(desk_id,recipient_id) WHERE state='pending';
CREATE INDEX desk_invites_by_recipient ON study_desk_invites(recipient_id,created_at DESC) WHERE state='pending';
CREATE TABLE study_desk_items (
 id TEXT PRIMARY KEY,desk_id TEXT NOT NULL REFERENCES study_desks(id),author_id TEXT NOT NULL REFERENCES users(id),
 kind TEXT NOT NULL CHECK(kind IN ('question','note','bookmark','mistake','update')),
 question_id TEXT REFERENCES canonical_questions(id),title TEXT NOT NULL DEFAULT '',body TEXT NOT NULL DEFAULT '',
 version INTEGER NOT NULL DEFAULT 1,deleted_at TIMESTAMPTZ,created_at TIMESTAMPTZ NOT NULL DEFAULT now(),updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 request_key TEXT NOT NULL,request_hash TEXT NOT NULL,UNIQUE(author_id,request_key),
 CHECK(length(title)<=140 AND length(body)<=4000),CHECK(kind NOT IN ('question','bookmark','mistake') OR question_id IS NOT NULL)
);
CREATE INDEX desk_items_recent ON study_desk_items(desk_id,created_at DESC,id) WHERE deleted_at IS NULL;
CREATE TABLE study_desk_messages (
 id BIGSERIAL PRIMARY KEY,desk_id TEXT NOT NULL REFERENCES study_desks(id),author_id TEXT NOT NULL REFERENCES users(id),
 body TEXT NOT NULL CHECK(length(body)<=2000),version INTEGER NOT NULL DEFAULT 1,
 deleted_at TIMESTAMPTZ,created_at TIMESTAMPTZ NOT NULL DEFAULT now(),updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 request_key TEXT NOT NULL,request_hash TEXT NOT NULL,UNIQUE(author_id,request_key)
);
CREATE INDEX desk_messages_recent ON study_desk_messages(desk_id,id DESC);
CREATE TABLE study_focus_sessions (
 id TEXT PRIMARY KEY,user_id TEXT NOT NULL REFERENCES users(id),desk_id TEXT REFERENCES study_desks(id),
 duration_seconds INTEGER NOT NULL CHECK(duration_seconds BETWEEN 300 AND 7200),
 state TEXT NOT NULL CHECK(state IN ('running','paused','completed','cancelled')),
 elapsed_seconds INTEGER NOT NULL DEFAULT 0 CHECK(elapsed_seconds>=0),resumed_at TIMESTAMPTZ,
 version INTEGER NOT NULL DEFAULT 1,created_at TIMESTAMPTZ NOT NULL DEFAULT now(),ended_at TIMESTAMPTZ,
 CHECK((state='running')=(resumed_at IS NOT NULL))
);
CREATE UNIQUE INDEX focus_one_active ON study_focus_sessions(user_id) WHERE state IN ('running','paused');
CREATE INDEX focus_history ON study_focus_sessions(user_id,created_at DESC);
CREATE TABLE study_desk_events (
 id BIGSERIAL PRIMARY KEY,desk_id TEXT REFERENCES study_desks(id),actor_id TEXT NOT NULL REFERENCES users(id),
 action TEXT NOT NULL,detail JSONB NOT NULL DEFAULT '{}',created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE FUNCTION study_desk_events_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'study desk events are append-only'; END $$;
CREATE TRIGGER study_desk_events_immutable BEFORE UPDATE OR DELETE ON study_desk_events FOR EACH ROW EXECUTE FUNCTION study_desk_events_immutable();
CREATE TABLE study_desk_reports (
 id BIGSERIAL PRIMARY KEY,desk_id TEXT NOT NULL REFERENCES study_desks(id),reporter_id TEXT NOT NULL REFERENCES users(id),
 target_kind TEXT NOT NULL CHECK(target_kind IN ('desk','item','message','invite')),target_id TEXT NOT NULL,
 reason TEXT NOT NULL CHECK(length(reason) BETWEEN 10 AND 2000),snapshot JSONB NOT NULL,
 state TEXT NOT NULL DEFAULT 'open' CHECK(state IN ('open','resolved')),resolution TEXT,
 retain_until TIMESTAMPTZ NOT NULL DEFAULT now()+interval '180 days',created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 UNIQUE(reporter_id,target_kind,target_id)
);
ALTER TABLE review_notifications ADD COLUMN study_desk_id TEXT REFERENCES study_desks(id);
ALTER TABLE review_notifications ADD COLUMN study_invite_id TEXT REFERENCES study_desk_invites(id);
GRANT SELECT,INSERT,UPDATE,DELETE ON personal_desks,study_desks,study_desk_members,study_desk_invites,study_desk_items,study_desk_messages,study_focus_sessions,study_desk_reports TO mpsc;
GRANT SELECT,INSERT ON study_desk_events TO mpsc;
GRANT USAGE,SELECT ON SEQUENCE study_desk_messages_id_seq,study_desk_events_id_seq,study_desk_reports_id_seq TO mpsc;
COMMIT;
