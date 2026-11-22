BEGIN;
-- Display-only room goals. No attempts, rewards or calendar records are created.
CREATE TABLE study_desk_weekly_goals (
 desk_id text NOT NULL REFERENCES study_desks(id),
 week_start date NOT NULL CHECK(extract(isodow FROM week_start)=1),
 target integer NOT NULL CHECK(target BETWEEN 1 AND 10000),
 version integer NOT NULL DEFAULT 1 CHECK(version>0),
 updated_by text NOT NULL REFERENCES users(id),
 created_at timestamptz NOT NULL DEFAULT now(),
 updated_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(desk_id,week_start)
);
CREATE TRIGGER desk_goal_active_account_record BEFORE INSERT OR UPDATE ON study_desk_weekly_goals
 FOR EACH ROW EXECUTE FUNCTION active_account_record('updated_by');
REVOKE ALL ON study_desk_weekly_goals FROM mpsc;
GRANT SELECT,INSERT,UPDATE ON study_desk_weekly_goals TO mpsc;
COMMIT;
