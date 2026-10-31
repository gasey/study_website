# All exams and unified Inbox

Implemented 24 October 2026. No bank questions, answer keys or classifications are changed by this release.

## All exams

The header focus selector offers **MPSC & Mizoram recruitment** (default) and **All exams · all questions**. All includes canonical questions from other exam systems and unassigned source papers; normal pool/subject/origin filters still apply. There is no need to duplicate questions. Current production papers are all assigned to Mizoram, so both scopes currently have the same totals.

Typed `exam_scope=mizoram-recruitment|all` queries select whitelisted eligibility views. The selection reaches question browsing/details/answering, source paper directories, taxonomy, Library shelves/facets, public exam collections/paper views, mock admission/revalidation, home/scoring facts, community question discovery and global question/exam search. Private/hidden collection visibility, scoring safety, disclosures and account history rules remain in effect. Questions with an explicit unavailable source cannot be graded against a different printing.

A browser preference saves an explicit selector choice; the URL can carry the scope for a shared view. Each document freezes its focus until explicit change/reload, preventing another tab from relabelling pending responses. Changing focus reloads and clears collection/paper/section/pagination restrictions; other subject/search filters remain. Shared question cards include All scope when required. Imports still require explicit paper scope to enter the default Mizoram pool. All does not automatically import any outside dataset.

Games deliberately retain their existing Mizoram strict-key pool; the header says so on Games. Specialization rules are separately planned by Astra in GAMES-SPECIALIZATION-PLAN.md. No game rules, rewards or matchmaking changed here.

## Inbox

`/inbox`, `/notifications` and the legacy contribution-notifications route use the same Inbox. v3's two-column layout contains durable notifications/settings and joined private desk message threads. Notification categories: discussions, desks, exam notices, contributions, content reviews, score updates and system. New categories derive from existing linked record fields; review event keys remain unique.

Notifications use bounded keyset pages and category/unread filters. Individual read/unread is idempotent. Mark-all uses the observed page snapshot and category; notifications inserted later remain unread. Preferences affect new notifications only: quiet updates stay in All but do not count as unread. Marking one unread explicitly brings it back into the count. The historical legacy unread API remains notification-only. The header uses the unified count: unread non-quiet notifications plus conversations containing unread partner messages. Counts refresh on navigation, focus, Inbox changes and every30seconds while visible. They are not a count of unique underlying events: a desk update notice and its unread conversation can both contribute.

Migration0047 backfills categories without changing read states, adds delivery preferences/silent state and per-account desk read cursors. Existing publications/reminder/discussion/desk producers write the same notification table; a trigger consistently applies preferences to future inserts. No producer is replaced by a client-only mock.

Messages reuse existing desk chat controls: registered sessions, explicit invitation/membership, join-time visibility, bilateral blocks, restrictions, bounded payloads, idempotent sends, CSRF/origin and durable server storage. Threads are paginated; selected conversations can be resolved separately after a list refresh. Message history uses bounded older cursors. Server clamps read cursors to messages visible to the member; future messages cannot be marked read in advance. Leaving/closure/revocation is rechecked on reads and sends. The UI clears stale private state on account change and ignores outdated responses. Writes include the expected account; private Inbox reads also reject a mismatched expected account.

Self-service Inbox state/preferences use the same registered-session/origin/CSRF/write-limit identity checks without requiring privileged bank MFA. This does not exempt any review/admin mutation: their existing identity dependency still requires staff MFA. Desk message sends retain their original account and replay guards.

Inbox supports existing private **desk conversations**, not arbitrary direct messages or public people discovery. Block/report/member controls remain in the linked desk. Selected messages poll every15seconds and threads every30seconds while visible; this is HTTP polling, not instantaneous push. No attachments, typing presence, arbitrary DMs or external deliveries are claimed. Email/push are explicitly unavailable; the user deferred selecting an email provider. Quiet-hour push exceptions from the prototype are not presented as working controls.

## Design and reused patterns

Reference: v3 Inbox markup1064–1114 in docs/design/India Study Map v3.dc.html:1240px main,36/24/96padding,40px desktop gap,14px card corners,340/480px flexible column bases,Newsreader36–52title,14px rows and Mono11times. Message colors use existing magenta/cream tokens. Long lists are scrollable; mobile wrapping is implemented but physical mobile testing remains unclaimed.

Read Shikshacom's work/shiksha-backend/notifications/models.py and views.py. Reused its architectural patterns: one recipient-owned notification store, identical list/badge scoping, categories and compatibility endpoints. The FastAPI/PostgreSQL implementation uses this app's existing identity, notices and private desk engine; no Django service or dependency was copied into production.

## Acceptance and limits

140API/integration tests pass (one upstream AnyIO deprecation warning). Scope tests prove default exclusion and explicit All inclusion of synthetic outside sources, accurate facets/papers/collections, preserved grading and global mock creation. Inbox tests cover ownership, cursor pages, read-all snapshot, quiet preferences, CSRF, expected-account binding, staff self-service, blocks, joined/left access and future-read clamping. Migration0047 rehearsed against a disposable production-data clone. Final browser/build/deployment receipts live in reports/all-exams-inbox. No production fixture accounts/messages/attempts are created.

No load/capacity, physical mobile, external email/push delivery, general DMs or new Games specialization implementation is certified by this release. Historical learning and audit retention rules remain unchanged.

## Deployment receipt

0047checksum86e5ece06b7bb582applied; no pending migrations.140tests passed/one upstream warning in24.79s.46API/33static artifact SHA256s match. Production health77751/12490; launch andAll currently equal because all1938paper scopes areMizoram. LiveGeography936underboth; default0.670s/All0.384s, Allcollections1.366s in single probes. Guest Inbox endpoints401and UIshowslogin. No production fixtures. Family site200, shared Caddy unchanged. Private backup27,011,643bytes/mode600and reports mirror under2026-10-24-all-exams-inbox.

## 24 October follow-up

Focus switching is now SPA-based with a preserved header/account session, scoped route reset and a reduced-motion-aware entry transition. This supersedes this document’s earlier full-reload implementation note. Vocabulary now has account-bound automatic recognition scheduling shared across equivalent scope printings; see VOCABULARY-AUTOMATIC.md. Inbox behavior remains unchanged.
