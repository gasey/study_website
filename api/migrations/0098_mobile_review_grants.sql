-- Native Smart Review uses the same frozen-set reader as web practice.
-- Make its view permission explicit for the runtime role on clean restores.
BEGIN;
GRANT SELECT ON v_all_questions TO mpsc;
COMMIT;
