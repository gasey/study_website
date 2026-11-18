BEGIN;

-- One optional prompt per doubt, shared by every session/device. Events remain
-- append-only, so dismissal, reloads and later unacceptance cannot reset it.
CREATE UNIQUE INDEX discussion_acceptance_nudge_once
ON discussion_events(post_id) WHERE action='acceptance_nudged';

COMMIT;
