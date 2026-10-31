# Creator profiles, following and safety

Implemented 2026-10-22; migration0036_creator_profiles. This extends the existing Content Studio and published-material catalog. No second post store or reward economy.

## Product paths

- `/creators`: public creator directory, handle search and12-item pagination.
- `/creators/:id`: public handle/bio, aggregate follower count, published-material count, approved materials, publicly attributed published bank contribution summaries.
- `/creators/settings`: own opt-in visibility/bio, private following list, unfollow and blocked-account controls. Link from private account profile and directory.
- `/feed?tab=following`: approved materials from followed public creators, recent first,12/page. URL preserves the selected feed on refresh.
- Material cards/readers link author handles only when the creator profile is public. Plain author attribution on existing publications remains when the creator profile is hidden.
- Owner Content CMS includes a paginated creator-report queue and audited resolution with existing staff MFA.

## Consent and public contract

No profile is opted in by migration; existing accounts receive no public profile record automatically. Only registered accounts may opt in, follow, block or report. Public profiles expose handle, optional600-character plain-text bio, aggregate counts and published content summaries. They do not expose email, legal/display name from private account, role/grants, study progress, attempts, billing, sessions or passwords. Public follows/follower identity lists are not provided; an account can inspect its own follows. Follower count is an aggregate, including private follower accounts.

Turning visibility off removes the creator from directory and other users' profile routes and Following feeds. Existing deliberately published materials remain in the general catalog/readers: hiding a profile is not unpublishing content. Existing follows remain dormant; enabling the profile restores their feed visibility. Creator settings explains this before saving. The owner can preview their own hidden creator page. Bank contribution attribution independently honors users.contribution_public; only state=published summaries appear. Active mock target questions are excluded from those summaries using the existing answer-protection pattern. Drafts/reviewer notes are not public.

## Safety and concurrency

All graph writes require account cookies, same-origin CSRF, bounded bodies and the existing atomic40/minute CMS account budget. Unique compound keys make follow/unfollow/block/unblock idempotent. Maximum2000 follows and2000 blocks per account keeps private management lists bounded. Short graph mutations share an advisory transaction lock: follow, visibility and block cannot race into a forbidden relationship. No external calls or content writes run under this lock. Reassess lock granularity after actual graph load measurements before large-scale rollout.

Blocking deletes follows in both directions atomically. Both users' creator profiles, catalogs, Following lists and direct published-material reads filter the relation while signed in. Unblocking does not restore follows. Block scope is creator profiles/materials; it does not revoke public access when signed out, hide historical exam source attribution, or claim to be a universal site-wide moderation ban. Existing question discussions and rankings remain separate systems. UI states the signed-in material/profile scope. Block confirmation is inline and cancellable, with recovery through own settings.

Profile reports accept spam/harassment/impersonation/other,10–2000-character note; one current report/account/creator, repeat updates reopen it. Private creator_events preserves append-only report/action history. Reports are available only to the scoped all-subject owner. Resolving requires a reason and staff MFA, records resolver/history, and does not silently suspend accounts or unpublish materials. Owner handles inappropriate materials through the existing archive/review workflow. No automatic penalties based solely on report count.

No XP/points, wallet credit, permissions or publication rights are awarded for follows, followers, visibility or reports. Tests assert unchanged reward ledger after repeated follows. Existing review-based creator/publication award rules remain intact.

## API contracts and operations

- GET/POST `/api/creators/settings` (own account only).
- GET `/api/creators?q=&offset=&limit=` and `/api/creators/:id?offset=` (public opted-in profile or own hidden preview).
- POST `/api/creators/:id/follow`, `/block` with `{enabled:boolean}`; `/report` with reason/note.
- GET `/api/materials?following=true` requires sign-in and filters public creator membership plus both-direction blocks. `creator_id` filters public/own creator publications. Catalog never selects lesson bodies.
- GET `/api/admin/bank/creator-reports?offset=` and POST `/:id/resolve` with reason. Private/no-store caching for creator reads and existing material routes.
- Legacy `/api/community/feed?tab=following` is the old question-discussion contract; its message directs clients to the material publications endpoint. It does not become an answer-leaking mixed feed.

Tables: creator_profiles, creator_follows, creator_blocks, creator_reports, append-only creator_events. Appropriate indexes cover follower, reverse block and public-profile paths; application role has only required grants. No real dummy creators/follows/reports seeded. Applied migration must never be edited; fix forward with a new migration.

## Evidence and remaining scope

See reports/creator-profiles for integration/build/migration receipts, browser screenshots and final deployment identity. Synthetic localhost fixture has ISM_CREATORS_DEMO=1; disposable database includes one opted-in author and approved synthetic guide, never production data. Browser reader is outsider@example.test with no owner/reviewer grant. No production account password, MFA or consent toggled by the agent.

Remaining: universal cross-product blocking, direct messaging, notifications for follows, private follow approvals, seller payments/payouts, games, full load/accessibility/security release matrix, real bank reviewers and deferred email delivery. These are not claimed complete by this creator feature.

## 2026-10-23 block-scope extension

Question discussion reads/writes and feed projection now enforce creator blocks in both directions, including parent visibility and accepted-reply excerpts. This supersedes the earlier statement that question discussions were outside block scope. Settings copy now names profiles, materials and question discussions. Historical bank attribution, rankings and signed-out public access remain unchanged; see QUESTION-DISCUSSIONS.md.
