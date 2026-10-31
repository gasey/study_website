# Exam calendar and official notices

## Delivered surfaces

`/calendar` follows Claude v3's month/list calendar, date selection, event categories and personal countdown. `/news` is the official-notice index backed by the same records, not a separate current-affairs editorial service. Month queries cover overlapping date ranges, including multi-day events; filters and month/list view live in the URL. Dated events and dateless announcements are supported. Notices link to their exact recorded official source, reference, verification date and verification note. Dates already passed are labelled. Archived notices leave listings/countdowns and retain a clearly withdrawn permalink.

Registered learners can follow public exam collections, save individual notices and opt into inbox reminders. Follows reuse `user_exam_bookmarks`, so exam bookmarks and calendar following stay one store. Saving a notice works even when no exact exam collection exists. No automatic inferred association from a similar job title. The feed has a following/saved-date countdown. Account-specific reads are private/no-store; browser responses are guarded against stale account changes.

Exports are RFC5545 `.ics` with stable event UIDs, sequence versions, escaped values, CRLF and UTF-8 octet folding. All-day end dates are exclusive; a one-day event ends on the next day. Per-event Google Calendar links use the same dates. These are copies, not a live subscribed calendar; source revisions do not update an already imported copy. Exact closing/reporting times must be checked in the official notice.

## Staff workflow

Owner-only **Admin → Calendar & notices** supports drafts, publication, revisions and withdrawal, with server validation, existing staff session/MFA/CSRF/rate limits, row/advisory locks, expected-version conflict handling and immutable revision snapshots. A stale save returns409. Published notices must be withdrawn rather than returned to draft. Official URLs are HTTPS and restricted to `mpsc.mizoram.gov.in` and `mpsconline.mizoram.gov.in`; no arbitrary fetch or HTML execution. Public calendar queries exclude nonpublic linked exam collections. No new staff grants were created.

`0042_exam_calendar.sql` owns new tables/indexes and the inbox event reference. Once applied, never edit it. Bank questions, keys and learner scores are unaffected. Bounded public reads cache for30seconds; personalized reads do not share caches.

## Inbox reminder worker

A supervised FastAPI lifespan task sweeps every60seconds. Only registered accounts with reminders explicitly enabled receive alerts, for their followed exams or saved entries. The audience is deduplicated. Unique inbox keys bind event/version/phase/user, making retries/multiple API workers safe. Each of the update and date phases inserts at most500rows per sweep. Updates and withdrawals during the last7days produce alerts; date alerts occur7days before,1day before and on the start date in Asia/Kolkata. An update and a due-date reminder can both arrive. Disabling reminders/unfollowing or unsaving affects subsequent sweeps; existing inbox receipts remain. Archived events receive no date alerts.

These are in-app inbox messages, not email, browser push, SMS or exact-time alarms. Downtime extending beyond a calendar-day delivery window can miss that window; updates retain a7day catch-up window. Errors are logged to the API journal and retried. Account preference is off by default; no production account was opted in by deployment. Large-audience load and disaster-recovery exercises remain operational work.

## Official starter intake

MPSC's main site returned403. The official online application portal was read directly in a browser on23October2026. Its rendered advertisement list verified15departmental examination application deadlines on9November2026, plus the passed LDC12October and Peon13October deadlines:17records. Departmental rows explicitly say they are not general recruitment vacancies. Closing times and exam dates were not in the listing and were not invented. Only the exact LDC item maps to the existing LDC collection; other entries remain individually saveable without fabricated collection mappings.

Evidence snapshot and SHA, screenshots and reviewed manifest are in `reports/exam-calendar/`. `scripts/import-official-calendar.py` validates the event contract and evidence hash, defaults to dry-run and imports only new deterministic IDs. Replay preserves all existing staff revisions. Technical intake writes nullable actor IDs with a hash-bearing reason; it does not impersonate the owner or create accounts. The importer is an operator tool, not a public auto-scraper. This is a starter intake, not a claim that all MPSC notices or revisions have been captured. Staff must maintain notices through the console.

## Reused code and validation

Inspected `work/shiksha-teacher-dashboard/src/components/CalendarWidget.jsx`: adapted Monday-first grids, month navigation and event indicators. Inspected `work/Admin-dashboard/src/pages/content/QuestionsAndNotices.jsx` and `work/shiksha-backend/content/{models.py,studio_views.py}`: adapted draft/published notice management, explicit errors and derived countdowns to this FastAPI/TypeScript app. Existing repositories were read only; no Django or unrelated dashboard dependency was copied.

Integration tests exercise permission/CSRF/URL/date/field validation, draft visibility, published/withdrawn public contracts, immutable history, concurrent revisions, bookmark reuse, saved-data isolation, hidden collections, reminder preferences, replay/deduplicated audience/withdrawal delivery and technical-import hash/replay preservation. Browser synthetic accounts verified follow/save/reminders across refresh, month/list, all-day export, admin revision/history and withdrawal, plus360px layout without document overflow. Source verification uses the official portal; synthetic browser dates are never production seed data. Production rehearsal/deployment/checksum/health receipts are maintained with the report packet.
