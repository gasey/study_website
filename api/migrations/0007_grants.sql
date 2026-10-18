-- Grant the app role access to tables, including ones added later.
--
-- The original grant was a one-off `GRANT ... ON ALL TABLES`, which covers
-- only tables that existed at that moment. Migration 0006 added
-- mock_sessions, and the API immediately failed with
-- "permission denied for table mock_sessions" — in production, on the first
-- request that touched it.
--
-- ALTER DEFAULT PRIVILEGES fixes the class of bug rather than this instance:
-- anything `postgres` creates in `public` from now on is readable and
-- writable by `mpsc` without a follow-up grant. Any migration that adds a
-- table would otherwise have to remember, and one eventually will not.

BEGIN;

GRANT USAGE ON SCHEMA public TO mpsc;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO mpsc;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO mpsc;

-- Applies to objects created by `postgres`, which is who migrate.sh runs as.
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO mpsc;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO mpsc;

COMMIT;
