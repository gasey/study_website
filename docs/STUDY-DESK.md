# Study Desk v3 — private release

## Delivered scope

`/desk` is the personal workspace; `/desk/:id` is a private six-seat desk. The scene, seven content tabs, illustration hot spots, typography, pill controls and two-column workspace follow the saved Claude v3 reference. Public discovery and class desks are disabled by the user's explicit rollout choice on 23 October 2026. Prototype sample names, online states and activity counts are replaced with actual membership and account data.

Personal goals, subject focus, daily/weekly checklist, weekly answer target, saved/recent bank questions and private notes save to the signed-in account. Guests retain a browser-only plan. Importing an earlier browser plan is explicit; JSON export is available. Failed saves retain the local copy. Concurrent edits produce a version conflict with explicit account/local resolution. Account identity is bound to writes, and account switching does not import another user's document.

Pro members may create up to three private desks. Invited registered users join free by exact handle. Invitations are recipient-bound, expire after seven days, are revocable/single-use and do not expose email search. Ten invitations per sender per day and a 30-day decline cooldown limit repeated requests. The sixth-seat check locks the room, so concurrent acceptance cannot overfill it. Owners can update settings, remove members, transfer to an eligible Pro member or close the desk. Owner exit requires transfer or closure. Transfer cancels outstanding invitations. Blocking cancels pending invitations and hides either party's content/progress but does not silently remove shared membership; leave/remove remain explicit.

Shared questions, bookmarks and notes use canonical bank IDs. Questions can be answered and discussed inline. Personal desk sets use the existing scorable pool; shared sets retain each question's actual provenance and unkeyed/descriptive behavior. No bank answer is copied, promoted or changed by a desk. Active mock questions cannot be shared or exposed through the shared question list. Private attempts and notes never post automatically.

Progress/accuracy, deliberately posted mistakes and current desk focus state each require a separate opt-in, initially off. Turning a switch off hides earlier mistake/update shares. Other members cannot read private preferences. Shared resources remain visible to members after the author leaves; new members see resources but only chat created since joining. This is disclosed before invitation acceptance. Removal or departure immediately revokes room access.

Chat is member-only with cursor pagination, own edit/delete, owner removal, mute and generic in-app notifications capped at one notice per room/recipient/hour. Visible room/chat refresh uses a 30-second poll rather than a websocket. Personal and shared-room focus sessions save server time and versions across reload/devices; pause/resume, completion and early ending retain actual elapsed seconds. A timer cannot be completed early by a client claim, and it earns no XP or spendable points.

## Privacy, review and retention

All desk reads are private/no-store. Registered mutations use the existing session, CSRF, request-size and rate-limit protections. New sharing and edits honor account sanctions. Safety withdrawal, leaving, blocking, reports and personal work remain available when new social posting is disabled.

Invitations can be reported before joining. Content reports retain the exact version as evidence. `/admin/desks` (also the bank-admin Private desk reports pane) is owner/session/MFA restricted; it exposes only reported snapshots, with audited queue reads and resolutions. It does not allow browsing private desks. Removal requires the reported version still to be current, and reports on the moderator's own content require another moderator. Desk/invitation reports require operational account review; there is no automatic ban based on a report. Other existing admin permissions and production MFA are unchanged.

The hourly bounded retention worker purges closed-desk items/messages after 30 days, in batches of 500. It redacts resolved report content 180 days after resolution; unresolved evidence remains visible for investigation. Minimal event metadata is append-only. Personal documents and focus history currently have no automated expiry. A closed desk cannot be reopened through this release, and there is no full account-erasure workflow in this packet. These are explicit operational limitations, not implied recovery capabilities.

Email verification and password-reset delivery are still deferred by the user. The user specifically authorized private invitations despite that deferral; this exception does not authorize public discovery, classes or wider social matching. An invitation is not identity verification. Operational report handling remains the owner team's responsibility; no response-time guarantee or public-scale capacity claim is made.

## Architecture and operations

Migration `0040_study_desks.sql` adds personal documents, room membership/invitations, shared resources/chat, server focus timers, exact report snapshots and append-only events. It does not edit bank data or previous migrations. API implementation is `api/app/routers/study_desks.py`; retention is `api/app/services/desk_retention.py`. The desk screen is lazy loaded; reusable scene, practice and focus components stay separate. App-wide personal storage is `web/src/lib/desk.ts` and shared API types/writes are `web/src/lib/studyDesks.ts`.

`STUDY_DESKS_PRIVATE_ENABLED` defaults false. This private release explicitly enables it on production. To pause new rooms/invites/acceptances/posts/edits, set it false in the existing root-only environment and restart the API. Existing reads, personal saves, focus, privacy controls, safety and exit routes remain available. Retain the additive schema when rolling back app artifacts; never edit or drop an applied migration to roll back. The pre-migration database dump and release evidence are stored privately on the server. No Caddy configuration changes are needed.

Useful read-only checks: API health, applied migration ledger, pending invitations versus active seat counts, open report age/count, and `journalctl -u ism-api` for retention failures. Do not log note or chat bodies. Polling, bounded pagination and indexes reduce unnecessary work; production load/restore exercises remain separate from synthetic correctness testing.

## Acceptance evidence

See `reports/study-desk-v3/` for the final test log, build, clone migration rehearsal, bank synchronization check, browser screenshots, deployment and artifact/health receipts.

- Isolated PostgreSQL tests exercise account isolation/CAS, cross-account writes, Pro/free invitations, expiry/decline/block guards, atomic last-seat acceptance, rejoining, revocation, deduplication, opt-in visibility, server-time focus, reports/audit permissions, retention and posting restrictions.
- Disposable browser accounts verified goal/checklist and private-note save/reload; actual invitation send/accept; separate personal data; no pre-join chat; inline canonical question; room chat; focus start/reload/pause/early end.
- At 360px the document width was 345px with no page overflow; the wide scene has its own scroll and equivalent labelled controls below it. Reduced motion and keyboard controls are implemented; no formal accessibility audit is claimed.
- Bank remains 77,751 questions and 12,490 strict scorable questions; no bank edits or real-user test records were made for this release.

## Deferred product scope

Public partner discovery, a mutual partner graph outside desk membership, classes/teacher permissions, paid shared resources, scheduled group mocks, games/duels, attachments and automated rewards are separate roadmap work. The user's private-only decision governs this release. Personal learning answers continue through existing bank attempt/scoring services; the desk does not invent a second scoring engine.

### Final release receipt — 23 October 2026

101 isolated tests passed (one upstream Starlette deprecation warning), production clone rehearsal and local build passed, migration0040 applied with none pending.35API files and26static artifacts match local output. Study health is77751questions/12490strict scorable; shared family site follows its redirect to200. Private flag enabled; public discovery/classes remain off. Live guest page rendered without browser errors; no production room/message/item/report test data was seeded. Synthetic report submission and owner snapshot-only dismissal were also verified in the browser. Documentation and evidence are mirrored privately under `/home/ubuntu/ism-release-reports/2026-10-23-study-desk-v3`.
