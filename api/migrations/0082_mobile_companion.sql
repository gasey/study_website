BEGIN;
CREATE TABLE mobile_auth_flows (
 id text PRIMARY KEY,
 challenge text NOT NULL,
 state text NOT NULL,
 redirect_uri text NOT NULL,
 expires_at timestamptz NOT NULL DEFAULT now()+interval '10 minutes',
 code_hash text UNIQUE,
 parent_session_hash text,
 authorized_at timestamptz,
 consumed_at timestamptz
);
CREATE TABLE mobile_sessions (
 token_hash text PRIMARY KEY,
 public_id text NOT NULL UNIQUE,
 user_id text NOT NULL REFERENCES users(id),
 parent_session_hash text NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now(),
 expires_at timestamptz NOT NULL DEFAULT now()+interval '30 days',
 revoked_at timestamptz
);
CREATE INDEX mobile_sessions_owner ON mobile_sessions(user_id,expires_at);
CREATE TABLE user_question_bookmarks (
 user_id text NOT NULL REFERENCES users(id),
 question_id text NOT NULL REFERENCES canonical_questions(id),
 created_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(user_id,question_id)
);
CREATE INDEX user_question_bookmarks_recent ON user_question_bookmarks(user_id,created_at DESC,question_id);
GRANT SELECT,INSERT,UPDATE,DELETE ON mobile_auth_flows,mobile_sessions,user_question_bookmarks TO mpsc;
COMMIT;
