# Plan

Feature-by-feature build order, derived from the prototype rather than
invented. Line references are into `docs/design/India Study Map v3.dc.html`
unless noted. Extract exact values per `docs/DESIGN-FIDELITY.md` before
building any screen — the handoff README's summary disagrees with the markup.

Tick boxes as work lands. Every phase ends in something deployed at
https://study.hawayu.in, not a branch that works locally.

## The shape of the work

28 screens, 2,206 lines of markup, plus a separate 147 KB Admin Console.

| Bucket | Screens (lines) |
|---|---|
| large (100+) | partner 274, contribute 203, feed 194, bank 162, profile 114, material 101 |
| medium (50–99) | create 95, module 93, landing 92, avatar 77, scoring 71, checkout 67, modq 63, calendar 58, duel 54, modules 53, inbox 51, board 51 |
| small (<50) | news 47, games 47, exam 45, results 36, mistakes 36, pricing 34, market 26, search 23, onboard 23, account 16 |

Size is a poor proxy for effort. `exam` is 45 lines but needs a
server-authoritative timer and thread locking; `partner` is 274 lines of
mostly static layout.

---

## Phase 0 — data work *(deferred by decision, 2026-10-18)*

**Build around these, do not wait for them.** They were going to be the
critical path; the call is to ship features against the data that exists —
12,319 questions in the verified-key scoring pool and 66,464 in the practice
pool at the latest sync — and improve
the bank later. Where a control cannot be honest today, it ships as a short
explanation instead (the topic and repeats filters already do).

Each item below still blocks a specific feature. That is recorded so the
blockage is visible, not so the build stops.

- [ ] **Subject classification of ~69,757 questions.** 90% carry the
      placeholder `'gk'`; `subject`/`topic` are NULL by design. Blocks topic
      filters, subject-wise mocks, category games, and the topic chip on
      every bank card. Derive subject from the paper where the paper is
      subject-specific ("Mechanical Engineering Paper-I") — cheap and
      reliable — and classify only the General Studies / GK papers by
      content. Record provenance in `subject_source`.
- [ ] **Dedupe (guide phases 2–3).** Measured `max(times_asked) = 1`; zero
      canonicals have more than one appearance. Blocks the "Asked N×" badge,
      repeat filters and sort — all prominent in the design. Exact and
      reordered-option merges first, near-duplicates to human review via
      `dupe_candidates`.
- [ ] **Page images.** `pdftoppm` → WebP → Cloudflare R2, coordinates into
      `page_images`. Blocks the original-paper viewer, which is what makes
      provenance tangible.
- [ ] **Answer keys for the 11,459 unanswered MCQs.** Grows `v_scorable`
      beyond today's 12,319. A model may suggest into the review queue as
      `inferred`; it may never write `official` or `key`.
- [ ] **Resolve ~1,508 duplicate-option questions** — answer text cannot
      identify which position was correct, so they are excluded from both
      pools.

---

## Phase 1 — foundations (unlocks every later screen)

- [x] Monorepo, docs, deploy pipeline, HTTPS
- [x] FastAPI + Postgres; question list, detail, answer gate
- [x] `scripts/sync-bank.sh` — local bank is truth, user data preserved
- [x] Anonymous device id + attempts with `chosen_text` (DECISIONS #6)
- [x] Bank screen: search, answer pools, inline answer feedback, and source/year filters wired to the question API
- [x] Approved taxonomy-v2 subject/topic filters and topic chips backed by the database
- [x] Numbered migrations + `scripts/migrate.sh` (status / dry-run / apply)
- [x] **Component library** in `web/src/components/ui.tsx`: PillButton,
      OutlinePill, Chip, CountBadge, Checkbox, GroupTitle, Card, NotYet,
      Avatar. Still to add when a screen needs them: tabs, toast, segmented
      control.
- [x] **App shell**: mega-menu header, dark footer, planned-route pages that
      name the phase that owns them.
- [ ] **search** (1460, 23) — small, and exercises the shell.

## Phase 2 — exams and mocks *(the core product)* — **complete**

Needs no accounts; attempts already work anonymously.

- [x] **First collection seeded** — `iti-instructor-2026`: 9 sections,
      16 papers, 1,446 official-key questions (migration 0005).
- [x] **modules** (525, 53) — "Exams & tools" launcher, live at /exams; lists launch collections and uses live counts; LDE is deferred
- [ ] **GET /api/collections** pagination/filtering once the exam library grows
- [x] **ExamPage** (prototype `module`, 1699) — live at /exams/:id; section cards launch section-scoped mocks
- [x] **Paper viewer** — module papers are first-class records over shared
      canonical questions; browse in printed question/option order and open a
      timed test from the paper when verified-key coverage is sufficient.
- [x] **Paper-aware timed sessions** — freeze the selected paper's ordered
      appearances/options at start; score by canonical answer text, and retain
      the usual server-owned timer and review record.
- [x] Collection sections support paper and approved taxonomy-v2 saved queries; mock draws use the section query
- [x] **MockRunner** (prototype `exam`, 578) — timed paper, sticky dark
      header, palette with answered/marked/current state, auto-submit at
      zero, resume on reload. Timer is server-authoritative (0006).
- [x] Inline results + review after submit
- [x] **results** (1582) standalone at /results/:mockId, and **mistakes** (1546) at /mistakes
- [x] **scoring** (1389) — live at /scoring, numbers served from the DB
- [x] Mocks draw from `v_scorable` only
- [ ] `thread_locks` while a mock is live — moved to Phase 4; nothing to lock until discussion exists

## Phase 3 — accounts ← **next**

Replaces the anonymous device id. Needed by everything below.

- [ ] Decide auth: own JWT vs `fastapi-users` vs Google — decision record
      before account and cross-device code
- [ ] **onboard** (1676, 23), **account** (2064, 16)
- [x] **private browser profile** — editable display name, user row, and
      server-backed progress; account identity and cross-device sync remain
      gated on the auth decision above
- [ ] **full account profile** (924, 114) — materials, contributions, level, avatar
- [ ] **avatar** (1839, 77) — customisation bought with coins
- [ ] Migrate device attempts onto the signed-in user

## Phase 4 — community

Study Desk and social delivery follow [the comprehensive Study Desk plan](STUDY-DESK-PLAN.md):
personal desk → mutual partners/private desks and deliberate shared activity →
collaboration → opt-in discovery → optional public publishers/classes. The user
endorsed the private partner model; later stages remain proposed future scope.
Minimum blocking, reporting, and operational moderation are release requirements
for the first social stage, ahead of the broader Phase 6 moderation programme.

- [x] **feed** (169, 194) — the `/feed` home surface, with live exam links,
      device practice stats, and the safe published-discussion read path.
      Following, materials, news, duels, calendar, cups, and public challenges
      remain unavailable until the account, moderation, and data foundations
      exist; the UI does not invent activity.
- [ ] **Discussion on a question** — hidden until the user answers (the gate
      is already enforced server-side). Explanations with one pinned, doubts
      with an accepted answer, error reports by type.
- [ ] **Error reports** — auto-hold at 3 independent reports; re-score
      affected attempts after a fix; +10 XP to reporters.
- [ ] **material** (823, 101) + **create** (728, 95) — the `/` slash-command
      block editor. Large; treat as its own sub-project.
- [ ] **inbox** (1064, 51), **news** (1792, 47), **calendar** (1618, 58)
- [ ] **partner** (1115, 274) — personal desk, mutual partners, private shared
      desks and activity first; discovery and class desks follow later gates.
      `/desk` has a personal-study tab and a clearly labelled partner
      UI preview; real accounts, invitations, shared desks, and moderation
      remain unbuilt.
- [ ] **contribute** (2080, 203)

## Phase 5 — games and multiplayer

- [ ] WebSockets on FastAPI; Redis for room state, presence, leaderboards.
      Redis earns its place once there is more than one uvicorn worker —
      without it two workers cannot see each other's rooms.
- [ ] **games** (1916, 47), **duel** (623, 54), **board** (677, 51)
- [ ] Gauntlet Run, speed round, weekly cup, Locate-on-map
- [ ] XP with daily caps, coins from cup placings
- [ ] Scored play draws from `v_scorable` only — never score a duel on a
      model's guess

## Phase 6 — moderation

- [x] **modq** (1483, 63) — owner-only `/admin/moderation` with Reported /
      New users / Appeals / My actions, a separately provisioned bearer
      secret, logged actions, and reversible state snapshots.
- [ ] Conduct only; content accuracy stays with error reports
- [ ] 1–3 exams per moderator, 6-month terms, escalation over a rolling 90
      days. Tables already exist.
- [ ] `question_collections` must be populated or scoped queues return empty
      (volunteer scopes are deferred; this first console is site-owner-wide).

## Phase 7 — money *(highest risk; do last)*

- [ ] **pricing** (1963, 34), **checkout** (1997, 67), **market** (1038, 26)
- [ ] Free / Pro / Class; UPI and Razorpay
- [ ] Never handle card details directly — use the provider's hosted flow

## Phase 8 — admin console

Separate file, `docs/design/Admin Console.dc.html` (147 KB). Tabs: overview,
bank (browse/corrections), browser, editor, builder, dupes, homepage, roles,
plans, flags, settings.

- [ ] **Resolve DECISIONS #5 first.** Admin corrects wrong keys — server-side
      edits to bank data that the next sync destroys, because local is the
      source of truth. Until a correction queue that exports back to local
      JSON exists, **do not build admin writes that mutate
      `canonical_questions` directly.**
- [ ] Bank browser with the PDF pane and highlighted question region
- [ ] Corrections queue, dupes review, Module Maker

## Phase 9 — mobile and polish

- [x] Mobile pass — bottom tab bar (Home/Bank/Desk/Exams/Me), 44px minimum
      hit targets everywhere, no horizontal scroll at 390px on any screen
- [ ] The handoff calls the mobile reflow and contrast pass **unfinished** —
      expect judgement calls, and record them
- [x] **landing** (77, 92) — public homepage at `/`, live question sample,
      truthful exam collections, and links into the existing bank and exams.

---

## Standing rules

1. Extract values from the prototype before building. Never from the README,
   never from an adjacent screen.
2. Ship each screen deployed and verified, not merely typechecked.
3. If the data cannot support a control, show the explanation — never a
   control that silently returns nothing. Two already do this.
4. Scored play reads `v_scorable`. Practice may read `v_practice` and must
   label unverified answers.
5. Append to `DEVLOG.md` before stopping.

## Community contribution review — design handoff, 2026-10-20

Specification and implementation entry point: [review-system/START-HERE.md](review-system/START-HERE.md). This is planned work; the new review system is not implemented or deployed. The current user direction adds reviewed derived answers for estimated mocks, with strict official-key scoring retained separately.

- [ ] P01: review contracts, schema and integrity constraints.
- [ ] P02: authenticated contribution/reviewer APIs and scoped permissions.
- [ ] P03: evidence, module comparisons and legacy report intake.
- [ ] P04: guarded local-bank publication and sync receipts.
- [ ] P05: notifications, attribution/credit, worker and operations.
- [ ] P06: reviewed estimated scoring, snapshots and reassessment.
- [ ] P07: Claude v3 contributor and reviewer UI.
- [ ] P08: acceptance gates A01–A20 and controlled production rollout.

## Admin/contribution deployment checkpoint — 2026-10-21

The design-only status above is superseded by this checkpoint. Implemented and deployed: scoped admin/question/source/report/review workspace; immutable contributor revisions; evidence mapping and quorum; guarded local publication/sync receipts; replay-safe credit/votes/notifications; community original-MCQ practice; explicit holds; and snapshots for newly started mocks. The local worker timer is installed. Twenty-one isolated integration tests pass and the frontend builds. This does not mark the full P01–P08 packets or A01–A20 gates complete: see review-system/ACCEPTANCE.md and OPERATIONS.md. Owner grant awaits the nominated account's signup and confirmation. Adjusted mock reassessment, staff MFA/email verification, full operations/load/accessibility gates and advanced source/module ingestion remain outstanding.


## Scoring and account-security checkpoint — 2026-10-21

This supersedes the outstanding reassessment/MFA and pending-owner notes above.

- [x] P06 implementation: immutable original scores, separate adjusted mock/practice assessments, reviewed-derived admission, exact presentation snapshots, bounded replay-safe background reassessment and private notices. Migration 0032 applied; 34 scoring/review integration tests passed before MFA work.
- [x] Account authenticator implementation: encrypted account-bound TOTP seeds, replay prevention, single-use hashed recovery codes, password/recent-login enrollment, staff write enforcement and security events. Migration 0033 applied; combined suite 41 passed. Owner enrollment is deliberately left to the owner.
- [x] Local frontend build and API/static deployment; local/server artifact hashes verified. Production clone migration rehearsal and both shared-site health checks passed.
- [ ] Email verification and password recovery: user chose mail provider later. No delivery is configured or claimed.
- [ ] Complete P08 release gates, actual independent reviewer provisioning, bank answer adjudication and advanced ingestion/admin tools. Current evidence is recorded in review-system/ACCEPTANCE.md; these packets are not all complete.


## Bank repair workspace checkpoint — 2026-10-21

- [x] Admin paginated issue queue, paper filtering and exact-appearance inspector with instructions/formatting/figures/provenance/existing corrections.
- [x] Paper-page/question ordering, refreshable URL filters and appearance-preserving correction-editor links; actual overview issue shortcuts.
- [x] 44 combined isolated tests pass, TypeScript/Vite build, desktop/360px browser checks and deployment artifact comparison. Both shared sites healthy.
- [ ] Source PDF bounding-box highlights and module-comparison ingestion/adjudication remain separate work. Native PDF embedding depends on browser support; source links are always provided when available.
- [ ] Bank missing answers still need evidence-backed adjudication and independent reviewed publication; no answers were changed by this UI packet.


## Exam journey and rewards — 2026-10-21

- [x] Exam journey continuation, recent results and account practice checkpoint, URL/filter/page persistence, source context in practice.
- [x] Browser20-question mock rehearsal; overlapping-start recovery; submit→permanent result navigation; saved answer/mark/position verified after refresh.
- [x] Learning XP/levels, opt-in week/month/all-time board, distinct reward wallet/history and new contribution credit/reversal integration.
- [x] Atomic/idempotent earned-Pro redemption, effective access gates and owner catalog controls; provisional offer disabled pending launch review.
- [x] Migration0034 clone rehearsal/live apply,52passing tests, local build/deploy and both-site health/artifact comparison.
- [ ] Actual game controllers/duels/cups and full game reward/anti-abuse/load matrix. Follow docs/LEARNING-REWARDS.md; do not trust client awards.
- [ ] Business decision to activate redemption and finalize earn/redemption rates. No cash/transfer/payment changes delivered by point rewards.


## Content Studio — 2026-10-21

- [x] User material editor, immutable drafts/history, owner review and approved reader revisions.
- [x] Material catalog/pagination/search, helpful/studied/save/report, author notifications and controlled creator rewards.
- [x] Actual Pro gating and paid-preview demo; canonical bank question references.
- [x] Migration0035 clone/live,60tests, local build and browser workflow/responsive evidence.
- [ ] Individual content checkout, seller/payout/refund workflows, hosted media and remaining enterprise release gates. See CONTENT-STUDIO.md.


## Material discovery — 2026-10-22

- [x] Shared published-material discovery cards in feed, exam overviews, subject practice, English and Arithmetic/Reasoning learning.
- [x] Exact context filters retained through catalog search/pagination and prefilled creator entry links.
- [x] Loading/retry/empty states and shared safe reader links/access labels.
- [ ] Creator public profiles/following and remaining CMS/payment/launch gates remain separate work.


## Creator community — 2026-10-22

- [x] Opt-in public creator directory/profile, public materials and reviewed contribution summaries.
- [x] Account follow/unfollow and refreshable Following publication feed.
- [x] Visibility controls, private follow/block management, bidirectional material/profile block filtering and owner report review.
- [x] No follow/upvote XP or reward changes. See CREATOR-PROFILES.md for scope and evidence.
- [ ] Universal cross-product blocking, messaging/follow approvals, payments and remaining release gates.


## Publishing workflow polish — 2026-10-22

- [x] Derived owner dashboard for pending materials, bank corrections and three report types, explicit priorities, filters and exact work links.
- [x] Material preview, revision/block comparison, latest review history and inline decision feedback.
- [x] Persistent author feedback above editor and repaired inbox route/unread badge.
- [x]70integration tests, clone index rehearsal and synthetic owner→author browser flow; release identity/evidence in reports/publishing-dashboard.
- [ ] Older full event timeline UI beyond30events, broad operational release gates and bank adjudication remain. See PUBLISHING-DASHBOARD.md.


## Module comparison intake — 2026-10-23

- [x] P03 initial immutable module/crosswalk/packet import, conservative current identity matching and preserved historical claims.
- [x] Owner paginated comparison workspace, source inspection, explicit candidate selection, triage and linked draft/source-request workflows.
- [x] Read-only cited evidence for linked authors/reviewers; module claims cannot promote official provenance.
- [x] 75 tests, clone/live migration0038, build, synthetic browser rehearsal and real6754-row import/replay.
- [ ] Independently adjudicate evidence, fulfill source requests, expand other modules and complete broader release gates. See MODULE-COMPARISON-INTAKE.md.


## Module research batch 1 — 2026-10-23

- [x] Deduplicate97conflict rows into96bank targets and preserve original module appearances.
- [x] Research20targets; prepare15answer/3context/1defect payloads with primary references/source hashes and explicit pending76.
- [x] Attach research to new immutable runs and display readable assessment/source links/prepared payload inspection in admin.
- [x]78tests, frontend build and synthetic browser proof; no production submission/approval/bank mutation.
- [ ] Independently review/submit/publish appropriate prepared proposals; research remaining76targets and inspect exact paper identities.


## Difficulty retirement — 2026-10-23

- [x] Remove remaining admin/editor difficulty labels and controls; taxonomy saves only subject/topic/subtopic.
- [x] Reject new difficulty edits and stale legacy changes while preserving immutable history/idempotency.
- [x]80tests/build/synthetic browser evidence; no migration/data mutation.
- [ ] Next implementation: explicit prepared-research→draft workflow preserving all citations and validating the live baseline.


## Prepared drafts and answer layouts — 2026-10-23

- [x] Explicit prepared-research→editable draft with complete citations, live bank/context guards, deduplicated clicks and normal independent review.
- [x] Retain secondary sources on later author revisions.
- [x] Shared remembered2×2/List options across learner bank/module/paper/mock/detail and subject practice; narrow single-column fallback, fixed answer order and explicit states.
- [x]83tests, build and synthetic draft/edit/citation plus layout/persistence/mobile browser proof.
- [ ] Real independent reviewers/publications, remaining76research targets and wider operational release gates remain.


## Next bank-answer audit — queued 2026-10-23

- [ ] Inspect and verify the linked MPSC Combined Prelims 2025 final-key PDF against exact paper/series/question identities; record source and page evidence before using any key cells. The link was found during legacy-module inspection but its mapped cells have **not** been verified.
- [ ] Continue evidence research for the remaining76 distinct bank appearances from the module-conflict cohort. Turn supported findings into editable correction drafts with citations; preserve independent review and publication requirements.
- [ ] Re-measure the current objective unanswered count, then work through the previously reported1,652 missing answer indexes using official keys where available and explicitly sourced/reviewed derived answers where not. Do not present the earlier count as a fresh measurement or mark unsupported answers scorable.
- [ ] Keep descriptive questions visible in paper views with a clear descriptive/scoring status; do not treat them as missing MCQ answer indexes.


## Question discussion and sharing — 2026-10-23

- [x] Shared inline canonical-question doubts/explanations/replies and source-context share links across bank/module/paper/subject practice.
- [x] Helpful feedback, asker-accepted replies, private first-post moderation, conduct reports, existing block/sanction enforcement, withdrawal and thread locks.
- [x] Published-topic feed links and transactional reply/acceptance inbox notices, preserving answer/active-mock gates.
- [x] Discussion evidence and supporting sources carried into ordinary editable correction drafts; current baseline/independent publication rules retained.
- [x] 91 isolated tests, local build, migration rehearsal and synthetic browser workflow/mobile proof. See QUESTION-DISCUSSIONS.md and reports/question-discussions.
- [ ] Remaining bank-answer audit stays queued above. Real independent reviewers and wider P08 release gates remain separate outstanding work.


## Study Desk v3 private release — 2026-10-23

- [x] V3 interactive six-seat scene and exact seven workspace tabs; real member/empty states, responsive layout and lazy loading.
- [x] Account-saved personal plan/notes/saved/recent questions, explicit browser import/export and concurrent-device conflict handling.
- [x] Private Pro-created desks, free exact-recipient acceptance, capacity/expiry/cooldown/block guards, settings and safe membership lifecycle.
- [x] Inline canonical questions/practice, shared notes/bookmarks, explicit progress/mistake/focus sharing, member chat and generic muted inbox notifications.
- [x] Server-time focus persistence, scoped report snapshots/owner MFA review, sanctions and bounded retention.
- [x] Isolated tests, browser account/invitation/privacy/focus/mobile checks and clone migration rehearsal. Deployment receipts in reports/study-desk-v3.
- [ ] Public discovery/classes remain off per user. Separate partner graph, link invitations, games/group mocks/paid collaboration, email delivery and wider operational rollout remain future scope. See STUDY-DESK.md.


## Combined Prelims2025 final-key audit pass — 2026-10-23

- [x] Direct official final-key download verified byte-for-byte against the archived source; all800cells manually transcribed with8compensated markers.
- [x] Compare514existing appearances; visually map9flagged sources:3answer differences/6compensated, plus2page fixes and1equation restoration.12typed proposals prepared.
- [x] Register4exact-paper final-key documents; import/replay a new immutable Combined intake retaining prior research.8flagged appearances have exact candidates; Q41II-C stays a direct correction with no fabricated module link.
- [x] Fresh bank gap audit:1652MCQs (1543negative/109null),7973descriptive;47MCQs have no options.104synthetic/isolated tests pass. Evidence reports/bank-final-key-20261023.
- [ ] Independently review/publish the9flagged appearances; rebase companion proposals after each publication. The bank/scoring outputs are still unchanged.
- [ ] Continue full stem/option identity verification beyond the9flagged cases;505number/cell agreements alone are not correctness proof. Research76older conflict targets and missing-answer backlog remain.
- [ ] Restore source/type/options for the47zero-option MCQs, then prioritize the larger unanswered paper cohorts in missing-mcq-queue.csv.

## Avatar editing — 2026-10-23

- [x] V3 Customize/Inventory, seven categories, real preview, shuffle/revert/save/initial reset and responsive layout.
- [x] Curated server catalog, account-bound versioned writes, durable actual-XP level rewards and append-only history; no point/XP spending or granting.
- [x] Shared renderer and saved look in account/profile, creator/material/discussion/feed, leaderboards and desk membership/scene; preserve visibility/block rules.
- [x] Tests, build, clone migration rehearsal and synthetic save/reload/reset/inventory/desk/mobile checks. See AVATAR-EDITOR.md and reports/avatar-editor.
- [ ] Coin/badge cosmetics, uploads and other future avatar commerce remain separate product work; no fake shop/wallet is exposed.

## Question discussion discovery refinement — 2026-10-23

- [x] Secondary Open question link; dedicated page opens the shared discussion while list practice keeps it collapsed inline.
- [x] Community Questions & Doubts with All discussions/Doubts/Unanswered doubts filters and links to the same canonical thread.
- [x] Unanswered considers only published, visible replies; answer disclosure, active mocks, moderation and bilateral blocks remain enforced. Legacy doubts URLs remain supported.
- [x] Focused discussion integration tests and browser discovery→question/inline verification. See reports/question-discovery.

## Exam calendar and official notices — 2026-10-23

- [x] V3 month/list/date selection, event filters, saved notices, shared exam bookmarks/follows and account countdown in the feed.
- [x] Official-notice index, direct source/reference/verification notes, Google Calendar and all-day .ics export.
- [x] Owner console draft/publish/versioned edits/withdrawal/history, strict official-source validation and existing MFA/CSRF permissions.
- [x] Explicit opt-in, bounded retry-safe inbox updates/withdrawals and7day/1day/day reminders using India dates.
- [x] Read Shikshacom calendar/notices code for reuse; verify official portal starter packet17deadlines with retained evidence. No guessed exam dates.
- [ ] Staff must maintain later notices/revisions. Email/push, subscribed live calendars, automated official-source ingestion and broad operational load/recovery gates remain separate work. See EXAM-CALENDAR.md.

## Automatic MPSC collection — queued by user

- [ ] Scheduled official-page/PDF collection without AI, duplicate/change detection and retained source hashes.
- [ ] Extract predictable date patterns into private admin drafts; keep ambiguous/scanned notices for staff entry and approval.
- [ ] Retry/backoff, visible last-success/error status, change/withdrawal review and manual publishing fallback. Never cancel an event merely because a source disappears.

## 2026-10-23 games/search release

- [x] Gauntlet, speed rounds, private/random duels, private multiplayer rooms and scheduled weekly cups backed by strict bank questions.
- [x] Server clocks, durable reconnect, race/idempotency guards, saved progress and shared daily reward limits.
- [x] Global header search across questions, public people, visible notes/materials, joined desks, paid previews and exams.
- [ ] Verify physical mobile layouts, observe a real Sunday cup and measure public-load capacity.
- [ ] Locate-on-map, run upgrades/cosmetics and prize economics remain future work; earlier Phase 5 checklist is superseded only for delivered modes above.

## 2026-10-23 — Subject-first Library and topic relationships

- [x] Direct Geography, History, Polity, Economy, Science, Environment, Mizoram GK and Current Affairs shelves; Subjects / Modules & tools / Saved notes navigation.
- [x] Practice/browse/notes/discussions with explicit source/year/exam/progress filters and pagination.
- [x] Reviewed secondary paths across discovery, exam selection and games, preserving the bank publication/sync authority.
- [x] Owner database map with real counts and relationship navigation.
- [ ] Add reviewed narrower Geography/History/Polity topics and explicit regions; classify missing topics without promoting parked alternatives.

### 2026-10-23 — Launch focus and mock recovery
- [x] Include existing Mizoram recruitment archive in explicit launch scope; exclude future outside/unassigned imports from learner pools.
- [x] Show launch context and accessible subject-shelf exam filter.
- [x] Link Games directly to an unfinished mock, preserving section/paper/mode and expired submission recovery.
- [ ] Future outside-exam selector and scope management UI when expanding beyond Mizoram.
See EXAM-FOCUS-AND-MOCK-RESUME.md for acceptance and limitations.

### 2026-10-24 — All exams and Inbox
- [x] Explicit All exams source filter across question/Library/public-exam/search/mock workflows, retaining default Mizoram focus.
- [x] Unified v3 Inbox with actual private desk chat, durable notices/read state, delivery preferences, pagination and accurate badges.
- [x] Astra specialization audit and implementation packets: GAMES-SPECIALIZATION-PLAN.md.
- [ ] Implement game-specialization packets P0-A/P0-B first; explicit topic setup/queues/cup tracks follow their acceptance gates.
- [ ] Configure email/push providers when selected; arbitrary DMs remain outside current safe desk-only launch.
See ALL-EXAMS-AND-INBOX.md for evidence and limits.

### 24 October: automatic vocabulary and smooth focus

- [x] Astra design and code-risk review; no confidence questionnaire.
- [x] Automatic account recognition scheduler, bounded source-safe queue, immutable replay/recovery and exposure-aware spacing.
- [x] SPA focus switching with preserved header/auth and reduced-motion transition.
- [x] 148 isolated tests and synthetic browser workflow.
- [ ] Future reviewed word/typed-recall content, guest adoption and reminder delivery; see VOCABULARY-AUTOMATIC.md for actual limits.

Release follow-up: automatic review and smooth focus deployed with0048; final150tests pass. Importer unknown-mode guard and retired-difficulty propagation regression included. Final limits and receipts in VOCABULARY-AUTOMATIC.md.

### English source fidelity —24October
- [x] Restore1,077 source-verified final-module presentations; shared blanks/emphasis/open passages.
- [x] Preserve source formatting in immutable mock-result review;152tests plus renderer checks.
- [ ] Resolve unmatched module identities/text differences from retained evidence; do not treat backlog count as missing instructions.
See ENGLISH-SOURCE-FORMATTING.md.

### Answer provenance help —24October
- [x] Shared hover/touch/keyboard label help, current reviewed-derived status and evidence submission links.
- [x] No-key solution guidance and existing publication-only contribution credit explained;153tests.
See ANSWER-PROVENANCE-HELP.md.

### 2026-10-24 navigation/performance release

Shared route/CSS splitting, scoped public catalog coalescing/cache, event-driven header summaries, Back scroll restoration and persistent Community tabs are implemented and deployed. Evidence: docs/NAVIGATION-PERFORMANCE.md and reports/navigation-performance. Follow-up: profile cold catalog SQL (still ~1–2 seconds), physical-device checks and representative concurrency measurements before making capacity claims.

English explanation pilot: all 200 received a blind answer check and draft critique. 22 prepared explanation packets pass gates;178 held, including source context/key/citation/option issues. Reports/english-explanation-pilot preserves originals, critiques and mandatory supplemental source mismatches. No production publication, human approvals or reward credit. Sol revision pass stopped at usage limit; no partial rewritten packet was promoted. Resume from the preserved reviews, then independent human approval through the existing workflow.

### Admin exam and paper inventory — 24 October 2026

Implemented exam/archive browsing, paper PDF/key inspector, four answer-status filters plus written type, exam/year/paper/topic intersections, coverage diagnostics and versioned expected-paper register with archival/restore, source-context fingerprint checks, audit history and JSON/local snapshot export. User-open official MPSC pages captured;921expectations/122source groups,669historical exact-URL associations and252unmatched entries. Four registered key PDFs synced privately. Canonical bank unchanged. Remaining data work: independently resolve252associations, verify extraction completeness and add other archive listing snapshots; no automatic extraction or answer approval implied.

## 2026-10-24 — Connected bank and learner workflows

- [x] Evidence-backed expected-paper intake with extraction artifacts, retry history, stale review checks, actual archived PDF hashing and completed bank-sync publication proof.
- [x] Subject-scoped review dashboard and combined exam/year/issue drilldowns for missing answers/explanations/figures, disputed keys and explicit source-context defects.
- [x] Unified saved mock/practice/vocabulary/focus/task continuation in Library and the personal Desk; practice remains inside its module.
- [x] Durable generic correction notices for saved/attempted questions, retry monitoring, preference handling and guarded original/adjusted-result links.
- [x] Account-owned daily revision combining latest mistakes, saved questions and due vocabulary, deduplication, real-attempt completion and existing scheduling/rewards.
- [ ] Automated crawling/OCR/question segmentation/import; physical-mobile and public-load certification. These are not implied by the intake stage tracker. See LEARNING-WORKFLOWS.md.

### First source-review intake batch

- [x] LDC Law &Judicial February2026PaperII: official/local/registered PDF hash matched,11pages visually reviewed,100printed questions vs99bank appearances, missingQ43 identified.
- [x]21source/defect/new-question proposals submitted with exact source evidence;2source figure crops mirrored; intake Review/expected count100 exported locally.
- [ ] Independent review/publication of this batch; rebase Q72dependent locator/context proposals; then prepare fresh derived-answer revisions for Q56/70/73/74/75. No approval or bank-completion claim. See reports/source-review-ldc-law-2026/README.md.


## 2026-10-24 — Delivered admin decisions and simpler audit

- Direct Official key / Corrected verified solution / Needs review / Unsolved controls in the question inspector, with evidence, reason, immutable history and normal local/server publication.
- Plain-language paper counts, actionable filters and next step; technical source/history details collapsed.
- 182 backend/offline tests, 11 Node checks, build and synthetic browser rehearsal passed. Migration 0052 deployed.
- Pending: the LDC source restoration queue remains unapproved; after restoration, rebase its five answer followups onto the new source content. Bank-wide unanswered questions and source completeness remain ongoing editorial work.


## 2026-10-24 — First-paper publication acceptance

In progress under explicit owner instruction: publish the 21 prepared LDC Law & Judicial Paper II source repairs, then eight explicit unofficial worked-solution attestations (the five answer followups, restored Q43 and adjacent table Q71–72). Exclude the two faulty source questions. Verify all100printed numbers, source context/images, browsing, practice and paper-specific reviewed mock against actual publication receipts in a disposable local DB. Preserve the remaining original answer statuses; source restoration is not blanket answer verification.

Added regression coverage for legacy unanswered -1, deliberately retired canonical difficulty, explicit operator authority and current-content rebase. Full sync now skips unchanged appearances/classifications/source-defect metadata, preserving row versions; a focused SQL regression checks unchanged and changed cases.190tests pass before the final real-paper acceptance rehearsal.


### First-paper completion receipt

Delivered all 21 source repairs and eight verified unofficial worked solutions; the 100-question paper is restored. Q29/Q99 remain source-faulted and excluded. The real-paper disposable-DB acceptance passed browsing, source context/figures, practice, blocked defective questions and mock start/resume/8-of-8 submission.191 backend tests and 11 Node checks pass. The intake is Published with sync112; no independent human reviewer or contribution credit was invented. Pending editorial work: 90 original answers in this paper, 1,649 MCQ answer indexes bank-wide, plus other papers' source audits. See reports/ldc-paper-publication/README.md.

## UDC follow-up after 25 October 2026 release

- [x] Connect 18 omitted historical Direct UDC papers, preserving collection version 1; publish version 2 with46 papers / 3,449 questions.
- [x] Add readable review-state lists, safe practice entry points, source/year search and pagination, and historical-date hints.
- [x] Open shared Materials in place; clarify Notes/Materials/Study Desk/Creator studio purposes.
- [ ] Resolve 8 unanswered UDC MCQs from exact source context/figures.
- [ ] Restore 4 empty UDC paper records and audit other partial paper numbering against PDFs.
- [ ] Verify 3,441 UDC answers and supply 2,755 missing explanations through evidence-backed publication; counts overlap and are a release snapshot.
- [ ] Add dated current-affairs supplements where checked sources support them. Current date hints are guidance, not current-answer verification.

## LDC follow-up after 25 October 2026 refinement

- [x] Audit all banked direct LDC membership: four papers / 350 questions; no omitted direct records found.
- [x] Expose per-paper readiness, direct reviewed-set practice, in-module review links and a balanced paper grid.
- [x] Fix unavailable-paper loading and add recently-worded current-affairs hints with a dated primary reference.
- [ ] Verify 263 remaining LDC answers; supply 228 missing explanations (overlapping categories).
- [ ] Resolve the two retained faulty-source questions with source evidence.
- [ ] Confirm actual LDC paper timing and marking instructions; current practice defaults are labelled.


## 2026-10-25 — LDC coverage correction and 2025 import

Published the missing February 2025 MPSC Paper I/II through the canonical bank and guarded collection version 2: six papers, 528 items (525 MCQs, three written tasks). Restored full written content and original figures/markup. 170 legacy answer claims remain unverified; two unanswered and three newly imported defective-source MCQs are explicit. Existing 77,752 records preserved. Eight linked direct archive pages checked; no additional LDC links found there. Paper instructions are now exposed by the collection API and shown by the reader. Evidence and remaining 436 answer reviews / 403 missing explanations: reports/ldc-2025-import/README.md.


## 2026-10-25 UDC packet status

Completed: 30 verified unofficial worked solutions, all eight prior blanks resolved, nine source repairs, distinct official/solution/review displays and 39 applied publications. Acceptance checks and local/server sync passed; timer active. Remaining: 3,419 UDC answer reviews, missing explanations, held source defects and empty-paper coverage. Continue with evidence-backed paper batches. Full bank synchronization per publication is slow; a future bounded batch publication design needs separate review. Evidence: reports/udc-answer-review-20261025/README.md.


## 2026-10-25 — Admin review usability

- [x] Confirm owner/admin and add explicit all-subject reviewer access to the requested existing email.
- [x] Direct review entry points, exam filtering and compact advanced filters.
- [x] Explicit answer decision cards, printed-option radios and explanation-based audit reason.
- [x] Save & next within the loaded page; inline real publication progress and manual refresh.
- [x] Build/deploy, static hash comparison and disposable local browser rehearsal; production access remains authenticated.

This changes review usability, not the remaining answer-review counts or publication throughput. Recent cards are session-only; durable records stay in the existing ledger.


## 2026-10-25 — Direct exam review filters

- [x] Pinned UDC / LDC / Assistant Grade / All exams review filters with persistent URL scope and visible scope banner.
- [x] Measured UDC inventory scope: 3,419 Needs review and 30 verified unofficial solutions.
- [ ] Assistant Grade source/answer review: baseline 1,015 questions, six unsolved and 1,003 needing review. Check six unanswered entries, the additive-inverse duplicate options, and five registered empty papers. Existing six verified solutions are shared with UDC and must not be counted as new work.

- [x] Repair the 18 missing UDC operational inventory links so admin review uses the full 46-paper collection, preserving existing associations with per-link audit events. Final scoped count is 3,419 Needs review / 30 verified.

## 2026-10-25 — Assistant / Group B source coverage and review

- [x] Restore Assistant Grade to 22 nonempty source papers / 1,568 records, including April 2024 shared Assistant/UDC papers and historical written tasks.
- [x] Match all 37 Combined Group B source PDFs to fresh official downloads; import 22 absent papers and all available printed questions.
- [x] Include the existing UDC and Assistant Grade tracks in the Group B study umbrella without copying question/progress identities: 97 papers.
- [x] Restore 29 written tasks in the three remaining empty historical UDC papers; keep descriptive questions out of MCQ scoring.
- [x] Disclose the official truncated December 2024 booklet A and source numbering defects.
- [x] Add dated Finance Commission/budget revision notes and extend currentness hints while suppressing grammar false positives.
- [x] Finish and reconcile 23 English solutions plus one dated current-affairs solution through audited publication; retain Q61/Q68 for adjudication rather than certifying ambiguity.
- [ ] Continue subject-specific evidence review of imported questions; source completion is not answer verification.
- [x] Games: ship Astra's first-release topic entry: exam/recent practice/named areas, exclusions, strict live counts, preview confirmation, account preferences and ready lobbies. See docs/plans/GAME-TOPIC-SELECTION-ASTRA-20261025.md and reports/games-topic-implementation-20261025/IMPLEMENTATION.md.

- [x] Final source metadata: 482 broad subject updates, written-only paper kind and duplicate printed-number disclosure; 80,547 local/server bank records in sync.

## 2026-10-25 — Games selection and bounded computer review

- [x] Deploy migration 0054, immutable room context and exact-context random matching; keep legacy rooms compatible.
- [x] Add Arithmetic, Vocabulary, Grammar and other familiar choices without requiring taxonomy knowledge. Insufficient pools explicitly refuse starts.
- [x] Publish eight clear December 2024 common Paper II computer solutions with references; hold Q5 and Q9. Local source MCQs missing answer indexes: 2,103.
- [x] Rehearse private joining/readiness, same-question duels, exact queues, full-room handling, idempotent starts and party host starts in a disposable database; remove it afterwards.
- [ ] Later games: mutually accepted common-area intersection, controlled mixtures and subject-specific cups. No automatic broadening.
- [ ] Expand reviewed source keys and approved topic coverage for zero/undersized game pools; do not relabel unofficial solutions as official keys.

- [ ] Correct all remaining-work dashboards/CLI summaries to treat legacy answerIndex=-1 as unanswered: source has2,103null +1,532sentinel =3,635 unusable MCQ indexes. Investigate the one-record canonical/source discrepancy (DB3,636) separately.


## 2026-10-26 — LDC / UDC / Assistant / Group B verification

- [x] Audit exact collection union and admin scope:8,588 records,6,213 Needs review at start; all inventory links match.
- [x] Restore printed English underlines, complete shared instructions/passages, malformed mathematics/options, source locators and required figures; keep original source typos visible.
- [x] Publish315 independently audited unofficial worked solutions through normal immutable receipts and live verification; verified union70→385, unanswered1,999→1,965, Needs review6,213→5,932.
- [x] Record11 genuine source/ambiguity holds with concrete admin reasons; no fabricated official keys or peer votes.
- [x] Add bounded trusted-owner batching with exact input/output journals, individual receipts, source guards and recovery. No new public endpoint.
- [ ] Resume35 already reviewed solutions after the existing500/day rolling staff cap permits; inspect pending-reviewed-35-request.json and its expected_source guard. No published status claimed for these35.
- [ ] Continue the remaining5,932 Needs review plus1,965 unanswered union records, source instructions/options and7,028 missing MCQ explanations. Per-exam CSV worklists and counts are in reports/clerical-verification-20261025.
- [ ] Independently inspect additional continued-page figures and specialized/Mizo questions; zero empty required-figure flags is not a complete source-context audit.

See reports/clerical-verification-20261025/IMPLEMENTATION.md for source evidence, rate-limit/recovery details and measured limitations. Existing accounts/attempts and canonical IDs remain shared and preserved.


### 2026-10-26 clerical review checkpoint

- [x] Inventory remaining5,932 Needs review identities/93sources; independent root source/solution audit of648appearances, including English directions/targets and maths notation.
- [x] Save512 distinct guarded deferred answer requests (477new+35prior), with explicit unofficial provenance and current-source integrity checks.
- [ ] Restore source display for108 additional supported solutions, then prepare fresh guarded answer decisions.
- [ ] Publish audited answers within the unchanged500/day staff maintenance quota; currently full. No new promotions in this pass.
- [ ] Independently audit returned model-only packets and complete remaining source reviews. Full5k objective remains incomplete; see reports/clerical-review-remaining-20261026/PROGRESS.md.


### 2026-10-26 owner-authorized quota lift and publication

- [x] Remove the daily quota blocker for the explicitly authorized trusted-owner run; keep ordinary user/staff limits and exact-target/source/role checks.
- [x] Publish all512 previously pending independently audited solutions, including prior35; six batches,512applied receipts, zero outstanding exports. This supersedes the earlier quota-blocked checkpoint.
- [x] Confirm local/server exact sync, unchanged question identities/scoring pool, and preservation of every original user/attempt ID; restore review timer.
- [ ] Restore108 additional supported source-first solutions, then rebaseline and publish their answers.
- [ ] Complete independent audit of719model-reviewed items and remaining4,532individual reviews; handle57source holds/fourcandidates/tworouting items. Current Needs review5,422; whole5k task remains incomplete. See reports/clerical-publication-unlimited-20261026.

### 26 October 2026 — Source, pagination and independent audit completion

- [x] Complete source-first packet:107 supported unofficial solutions; preserve the genuine duplicate-choice hold and restore context for 15 ambiguous English items.
- [x] Audit 719 model recommendations independently, then perform lead evidence/semantic adjudication:624 published;95 documented unresolved, not promoted.
- [x] Publish 731 worked solutions through 1,088 individual immutable receipts; recover partial exports, reconcile queue 0 and restore existing timer.
- [x] Deploy shared responsive pagination:25 questions/browse,1/practice; URL filter/page persistence, next-page prefetch and bounded memory metadata cache. Build and live guest checks recorded; signed-in checkpoint/answer scenarios not exercised.
- [x] Preserve 80,547 IDs/nonquestion metadata, users/attempt history and strict official scoring pool; confirm local/server checksum and private release mirror. This supersedes the pending 108/719 entries above.
- [ ] Continue 4,532 not-yet-individually-reviewed items and documented source/ambiguity backlog. Current union has 4,647 Needs review,2,007 unsolved,1,628 verified solutions,127 official and 179 written questions. These worklists overlap; do not add them as independent totals.
- [ ] Resolve 95 independent-packet ambiguities and 16 original-source holds using clearer evidence or explicitly reviewed editorial corrections; preserve originals and distinguish unofficial solutions.
- [ ] Bank-wide raw 3,645 unusable MCQ indexes and descriptive scoring remain separate unfinished tasks. Source/answer count differences are explained in reports/source-pagination-review-20261026/IMPLEMENTATION.md.


## Full 5,000 clerical review — 2026-10-26 continuation

- [x] Re-inventory the exact4,647 needs-review IDs in the8,588-question union of LDC/UDC/Assistant/Group B non-gazetted; use explicit source SHA/page/choice guards and preserve the earlier731-solution release.
- [x] Independently adjudicate the root359-question packet; publish218 supported unofficial solutions and9 exact source restorations; preserve141 unresolved cases.
- [x] Complete the1,275 health/science first pass and a lead semantic pass; publish1,112 supported unofficial worked solutions, retaining163 exclusions. Correct clinical formula, date/scope, multi-option and typo problems before publication; keep persistent lead overrides.
- [ ] Finish independent English review and exact emphasis/choice/instruction restorations for all1,220. The first900 have an independent second pass; frozen695 supported answers and283 source patches are being published in the current run.320 await a second pass; uncertain/source-defective items remain excluded.
- [ ] Finish GS/GK:773/1,793 have durable first-pass dossiers (1–401 and1,001–1,372).257 from the lead-checked first300 are prepared for publication;1,020 have not completed a first pass. Keep date-specific claims anchored to the paper, with visible source qualifications.
- [ ] Resolve held questions individually and perform final all-scope acceptance audit; do not claim the full5,000 complete. The three review workers stopped with usage-limit errors; pending IDs and exact continuation notes are in reports/full-5000-review-20261026/CONTINUE.md. See STATUS.md/release-integrity.json for actual applied counts, rather than treating draft recommendations as published.


### 27 October 2026 — Superseding full-review pass results

- [x] Review every original4,647 backlog ID across the four overlapping exam collections; complete English second audit and all1,793 GS/GK first passes.
- [x] Publish3,824 additional unique unofficial worked solutions and604 source restorations; preserve the unresolved printed-choice defect and its withdrawn verification.
- [x] Reconcile source publication failures by exact IDs, register the existing LDC source, restore107 printed shared directions, and revalidate seven answers after instruction context changed.
- [x] Audit all80,547 IDs, final live eligibility/receipts, exact bank SHA, baseline users/attempts, and unchanged12,490 strict official-key pool.
- [ ] Resolve remaining822 Needs review questions individually; the separate2008 unsolved questions and2761 missing explanations in the union remain unfinished. Use reports/full-5000-review-20261026/STATUS.md and unresolved-review-final.json.

### 27 October 2026 — English emphasis repair acceptance

- [x] Restore86 visually source-checked English targets,68 instruction fields and six option OCR defects; render legacy Markdown and safe HTML-like emphasis consistently across shared question views.
- [x] Deploy the shared renderer; verify live italics and combined bold/underline, source-text checks and production build.
- [x] Revalidate66 answers after context changes and publish14 additional unofficial worked solutions; preserve six explicit ambiguity holds, withdrawing two previous verifications.
- [x] Validate all80,547 IDs, final receipts, live verified eligibility, original learners/attempts, zero pending exports and matching local/live bank checksum.
- [ ] Continue remaining820 Needs review items (English256),1998 unsolved items and2743 missing MCQ explanations in the overlapping four-exam union. Formatting candidate coverage117/117 does not imply all English/source-context issues bank-wide are resolved. See reports/english-context-readiness-20261027/STATUS.md.

### 27 October 2026 — Remaining820 continuation and key/solution contrast

- [x] Restore47 actual three-choice sources; separately verify40 unofficial answers, retaining seven explicit ambiguities.
- [x] Apply222 exact registered final-key mappings; retain four demonstrated source/key conflicts as scoring holds. Net258 resolved from820; 562 remain.
- [x] Add lazy shared official-key/reviewed-solution comparison with active-test protection, exact source matching and explicit missing-evidence states.
- [x] Let admin publish separately reviewed working without replacing official evidence; automatically hold disagreeing answers. Publish three genuine agreeing examples through immutable local/server roundtrip.
- [x] Preserve80,547 IDs/nonquestion metadata, exact receipts, learner IDs, zero exported queue and matching local/live SHA. See reports/remaining-820-review-20261027/release-integrity.json.
- [ ] Continue562 needs-review,1998 unsolved and2518 missing explanations. Resolve technical multi-accepted key, original incomplete/duplicate options, Part-B comprehension wording, and the March/April2026 PwD LDC paper-date discrepancy before further key mapping.

### 27 October 2026 — Source underline clarity / fresh-chat handoff

- [x] Restore actual underline spans for little and ASCE2021Q64–70; restore exact clause directions from preceding source page and revalidate the existing little solution.
- [x] Improve shared underline thickness/weight and render legacy bold target spans as underlined only when explicitly required by the source instruction. No automatic missing-target inference.
- [x] Deploy and inspect live underline styling. Preserve options, answers, IDs and exact local/server publication receipts.
- [x] Prepare docs/NEXT-REVIEW-HANDOFF.md for a fresh chat. Core pending review remains562; the seven newly formatted ASCE questions are still needs-review.

### 27 October 2026 — Additional English/computer source packet

- [x] Independently inspect the 27 prepared candidates and original source pages; restore 18 exact question, target or shared-direction fields.
- [x] Publish 24 source-supported unofficial worked solutions; retain three concrete ambiguity/meaning holds. Correct the falsely inferred target on Taxation Q4 from *always* to printed *tall*.
- [x] Verify all80,547 IDs, unchanged nonquestion metadata, 42 exact receipts, 25 changed records, zero pending exports and matching local/live SHA. The official scoring pool remains12,708.
- [ ] Continue the remaining538 needs-review items in the overlapping four-exam union, plus1998 unsolved items and the separate missing-explanation backlog. See reports/additional-27-review-20261027/STATUS.md.

### 27 October 2026 — PwD LDC key/source date investigation

- [x] Inspect the original March-labelled PwD LDC paper covers, five candidate cells and the May final key's April sitting dates; preserve the unresolved date bridge and do not register a final-key mapping.
- [x] Correct Paper-II Q62's physical PDF locator from11 to12 and independently verify Q49 Lalsavunga and Q62 Rs7 gain as unofficial solutions.
- [x] Verify three immutable receipts, exact local/live checksum,80,547 IDs, zero pending exports and unchanged official scoring pool. Core needs-review now536; separate unsolved1998.
- [ ] Find an authoritative reschedule/identity document before mapping the PwD final key. Retain three source-concern candidates under review. See reports/pwd-ldc-identity-review-20261027/STATUS.md.

### 27 October 2026 — English, maths and computer priority pass

- [x] Reconcile priority input packets against live status; inspect printed English pages and the two garbled Taxation maths expressions before decisions.
- [x] Restore Assistant/UDC MPSC Paper I Q72's printed blank and full direction, then publish three independent unofficial English worked answers and two source-inspected computer best-choice answers. Preserve original examiner evidence and active reported-speech holds.
- [x] Audit six exact receipts, all80,547 IDs/nonquestion metadata, zero pending exports and matching local/live SHA. Strict official scoring pool remains12,708; core needs-review is531.
- [ ] Continue source-first review of180 English,23 mathematics and52 computer-science priority holds; other276 needs-review IDs and1998 unsolved questions are separate work. See reports/priority-review-20261027/STATUS.md and remaining-531-docket.json.

### 27 October 2026 — All 531 remaining review IDs reconciled

- [x] Reconcile every ID to its prior individual review reason, current live status, and the SHA-checked source PDF. See reports/all-531-review-20261027/adjudication-register.json; carried-forward reasons are distinguished from newly viewed pages.
- [x] Restore the actual italic targets in Taxation English Q5/Q6, publish three net supported unofficial answers, and retain a corrective hold on the resilient nearest-choice item.
- [x] Audit six immutable publications, one direct hold, exact receipts, all80,547 IDs, zero pending exports, and local/live SHA025a0390d365b388b58033327f379f3d32d5891ee351330aa7af8bf1cfe297cd. Official scoring remains12,708; core needs-review is528.
- [ ] Resolve the528 source/meaning holds with exact examiner evidence, corrected source, or a documented editorial best-choice decision. Priority subjects: English177, maths23, computer52; other276. The separate1998 unsolved questions are outside this count.

### 28 October 2026 — OpenCode Go Luna priority-subject solve

- [x] Save 252 first-pass worked solutions from the owner-requested `opencode-go/gpt-6-luna` model: English177, mathematics23, computer science52. Preserve source-review reasons and distinguish proposals from verified answers in `reports/luna-solve-20261027/solution-register.json` and `worked-solutions.md`.
- [x] Publish the source-formatted DC Serchhip Q48 and two independently adjudicated unofficial English answers. Improve the already verified Revenue Q23 explanation. Audit the seven packet receipts, three changed records from the preceding release, all80,547 IDs, zero pending exports and exact local/live SHA. Core needs-review is504; strict official scoring remains12,708.
- [ ] Resolve the remaining504 needs-review items with new source/key evidence or a defensible unique-answer decision. Priority subjects account for239 (English164, maths23, computer52); other subjects account for265. The separate1998 unsolved items remain outside this queue.

### 28 October 2026 — Luna drafts in admin review

- [x] Add the 252 saved OpenCode Go Luna drafts to the authenticated admin question inspector for their exact source appearance. Show proposed choice, working and source caveats as unverified review notes; keep bank answers and scoring unchanged.
- [x] Deploy the API and web interface; verify production loads252 drafts, the inspector denies unauthenticated access, health returns200 and the bank remains IN SYNC.

### 28 October 2026 — Remaining 504 continuation

- [x] Resolve two historical date holds using official exam dates and primary RBI/PIB records; publish exact unofficial answers with immutable receipts.
- [x] Audit two changed appearances, all80,547 IDs/nonquestion metadata, unchanged official scoring pool and local/live bank SHA.
- [ ] Continue502 needs-review questions under the strict unique-answer standard: English164, mathematics23, computer science52, and263 in other subjects. The separate1998 unsolved and179 written items remain outside this queue. See reports/remaining-504-review-20261028/STATUS.md.

### 28 October 2026 — Study each exam by subject and topic

- [x] Expose approved subject, topic and subtopic counts for each public exam's browsable papers, using distinct canonical questions and preserving exam scope.
- [x] Add subject/topic entry from `/exams` and each exam page; route topic and subtopic actions into exam-scoped browse/practice filters with saved checkpoints.
- [x] Deploy API and web; verify seven live exam trees and matched subject/topic/subtopic question counts. Preserve existing answer provenance, scoring and bank checksum. See docs/EXAM-SUBJECT-TOPIC-STUDY.md.

## Group B common-subject launch — 28 October 2026

- [x] Shared English/GK/GS entry across live Group B gazetted/non-gazetted papers.
- [x] Separate technical-paper search, pagination, subject/topic browse and practice.
- [x] Exact, versioned source roles for specialist science separation; approved primary paths only.
- [x] Source-preserving answers and continuation on the actual recruitment collection.
- [x] Backend regression tests, production build and desktop/mobile browser checks.
- [ ] Extend reviewed paper roles and direct-recruitment Gazetted coverage as new source papers are ingested.

See [GROUP-B-COMMON-SUBJECTS.md](GROUP-B-COMMON-SUBJECTS.md).

### Group B source coverage follow-up — 28 October

- [x] Review remaining mapped papers for common-science context and explicit section boundaries.
- [x] Add 23 source roles; verify 74 added common questions and preserve technical/Gazetted counts.
- [x] Apply printed question bounds to membership and displayed source; regression-test boundary cases.
- [ ] Independently review two existing classification concerns in reports/group-b-source-coverage-20261028/classification-follow-ups.json.
- [ ] Verify recruitment notices and acquire additional Gazetted direct-recruitment sources.

- [x] Separate source-verified paper headings from question learning badges; deploy nine reviewed source labels and verify all four Shibu Soren appearances.
- [ ] Review four Shibu Soren Indian History tags for Current Affairs (reports/gk-source-labels-20261028/taxonomy-review.json).

### 28 October 2026 — Paper identity and reviewed retagging administration

- [x] Add source identity editor with cover evidence page, printed titles/year, section question ranges, optimistic version/context guards, inventory audit and JSON export.
- [x] Add selected retagging previews and atomic/idempotent submission of up to20 ordinary contributions; independent review and queued publication use existing routes and worker.
- [x] Add current/proposed preview and shared GK/GS picker to individual and related-path authoring.
- [x] Combine GK/GS learning subjects and same-name topics in bank/library/collection topic trees; preserve legacy URLs and stored registry IDs.
- [x] Rehearse migration0055 on a production clone; apply and deploy targeted API/web changes. Validate62 backend tests,15 frontend checks and build; verify all12 shared live topic counts and unchanged Group B common3677.
- [ ] Review existing misclassified content, starting with the four Shibu Soren records, through Admin → Learning tags.

### 28 October 2026 — Saved exam-specific identity follow-up

- [x] Record the user's rule: one shared bank with separate exam identities; UDC knowledge is General Knowledge, not General Studies.
- [x] Give UDC/LDC/Assistant learning headings explicit exam presentation mappings → General Knowledge; retain GK/GS for cross-exam discovery. Do not infer paper names from content taxonomy.
- [ ] Audit/configure each exam's practice scheme from verified sources (sections, marks, timing and source-bound keys), reusing canonical questions and keeping technical papers separate.

### 28 October 2026 — UDC/LDC module and loading performance

- [x] Add clerical exam switching and own-exam English/GK routes; keep shared canonical questions and source-paper test settings.
- [x] Keep displayed source appearances inside the selected exam.
- [x] Remove the unconditional browser delay for question pagination; narrow collection membership expansion and readiness queries.
- [x] Compare seven production collection responses and seven question queries before/after; preserve every count, item and readiness field apart from intentional source selection.
- [x] Apply owner-requested unlimited Pro with no expiry to the named account, audit it and show a billing label for unlimited access.

### 28 October 2026 — Sol 6.1 exam polish handoff

- [x] Save the prioritized implementation handoff in docs/plans/EXAM-SECTION-POLISH-SOL-6.1.md, grounded in the deployed UDC/LDC fixes and measured loading limitations.
- [ ] Implement exam hierarchy, progressive question loading, mobile practice/filter polish and source-aware paper-card refinements from that plan; verify and release through the existing workflow.

### 29 October 2026 — Exam polish implementation and deployment

- [x] Simplify exam entry and focused study headers; move repeated guidance/test controls into a disclosure and keep saved journeys on overview.
- [x] Add scoped lightweight exam identity and progressive question display, retaining answer state across late metadata and retry.
- [x] Add grouped secondary filters, reset, pending-result answer guards, canonical prefetch keys and delayed-target keyboard/scroll focus.
- [x] Show verified paper headings on cards/viewer; audit five representative source covers and record scheme/content review follow-ups.
- [x] Verify35 backend tests,16 frontend checks, production build, seven collection response comparisons and three responsive widths; deploy targeted changes and preserve bank sync.
- [ ] Investigate intermittent long browser-entry observations; measurements do not establish consistently sub-two-second loading.
- [ ] Complete source-confirmed scheme/section publication and independent review of the saved tag candidates through the existing admin workflow.

### 29 October 2026 — Clerical learning tags usable with shared bank

- [x] Run requested Luna triage:202 targeted entries/9 OpenCodeGo calls, separate reviewer120 explicit corrections, canonical classification-only sync and live verification.
- [x] Fill102/127 missing topics; resolve4 Shibu Soren and3 clerical Civil Engineering errors, preserve source headings and answer provenance.
- [x] Verify126/126 current subject/topic links across UDC/LDC/Assistant; fix practice to record displayed exam source.
- [ ] Continue25 remaining topic gaps and broader legacy-tag audits; uncertain entries are not force-tagged. LDC unchanged by this correction batch, routes verified. Evidence: reports/clerical-tags-20261029/STATUS.md.

### 29 October 2026 — Paper-list readability and site spacing

- [x] Replace dense paper grids across shared exam modules with readable rows, compact nonzero status links and expandable details/tests.
- [x] Widen shared shell1440px; reduce outer gutters16px desktop/12px phone, align exam/Combined hero offsets and retain narrow reading limits.
- [x] Verify UDC disclosure/actions, LDC390px and Combined1280px without horizontal overflow;16 frontend checks and production build; deploy static frontend only.

Owner correction29October: paper box grid restored; shared1440px cap removed. Live1920px check:1905px full-width container,x0,16px content gutter,no overflow. Earlier full-width paper rows were rejected; preserve boxes in future changes.

### 29 October 2026 — Clerical GK Science filtering

- [x] Include Science within GK for Assistant/UDC/LDC, add Physics/Chemistry/Biology/news branch filters, preserve existing Science deep links and canonical tags.
- [x] Verify29 backend tests,16 frontend checks,17 live count/result comparisons, unchanged unrelated taxonomy/maps and desktop/mobile navigation; deploy targeted API/frontend.
- [ ] Audit broadly tagged GK questions for missing Science classifications through separate content review; current grouping uses existing approved tags.

### 29 October 2026 — Interactive Atlas

- [x] Inspect original26 map chapters and restore Interactive Atlas under Library tools, with menu/homepage/contextual subject entry points.
- [x] Add layer toggles, searchable feature list/focus, timelines/reset, notes and subject-practice links; exclude known obsolete base administrative overlay.
- [x] Validate26 chapter datasets,17 frontend checks, production build and desktop/mobile live rendering; deploy frontend.
- [ ] Independently review inherited atlas facts and historical extents; legacy chapter quizzes remain outside scored practice pending provenance review.

### 29 October 2026 — XP, leaderboard and authentication handoff

- [x] Inspect existing auth/MFA, guest adoption, reward ledger, leaderboard and frontend flows; save implementation system design in docs/plans/XP-LEADERBOARD-AUTH-SOL-6.1.md.
- [ ] P0: unify identity/CSRF and explicit expiry behavior, protect guest ownership/transfer, restore safe post-login destination and isolate account caches.
- [ ] P1: recovery/verification/session controls, reward receipts/reconciliation, leaderboard placement/period/privacy polish and isolated concurrency tests.
- [ ] P2: owner diagnostics and measured release/operations acceptance. No functionality deployed by the planning session.

### 29 October 2026 — XP/account hardening implementation

- [x] Implement protected guest credentials/consented transfer, shared session resolution and cookie mutation Origin/CSRF boundary.
- [x] Preserve safe post-login exam destination; isolate account changes across requests/tabs and provide explicit expired-session recovery.
- [x] Add session list/revocation, password session rotation, purpose-bound recovery/verification tokens and encrypted gated mail outbox.
- [x] Add idempotent practice receipts, XP outcome messages, rule/source metadata, leaderboard period/placement/tie/pagination fixes and owner diagnostics.
- [x] Validate isolated backend suite, frontend tests/build, synthetic desktop/mobile guest→account→XP→board and cross-tab logout; rehearse migrations0056–0059 on a production clone.
- [ ] Configure SMTP and authorize/verify controlled external delivery before enabling recovery/verification email. Code existence is not delivery readiness.
- [ ] Establish representative-load latency/operational monitoring targets beyond smoke timings.

Release follow-up: migrations0056–0059 applied,13API SHA256s matched, static index-CsXsy59b.js deployed. Original34reward receipts/fingerprint and unlimited owner entitlement preserved; bank IN SYNC, study healthy/family307. Evidence: reports/account-xp-hardening-20261029/STATUS.md. Mail delivery and representative load acceptance remain pending external/configuration work.

### 30 October 2026 — Simplify admin workflow

- [x] Reduce the owner's primary navigation from21flat entries to five daily tasks; group specialist tools and preserve all existing tab bookmarks/role visibility.
- [x] Add task-focused Home with disclosed system details; remove its duplicate full publishing queue and ineffective paper filters.
- [x] Simplify queue filters/reset, persist reviewer filters in URLs, and open reported questions directly in the inspector.
- [x] Replace report resolution prompt chains with an inline form that preserves server validation and audited outcomes.
- [x] Verify23frontend checks,18existing review/publication/tag regression tests, production build and owner/reviewer desktop/mobile acceptance; deploy static frontend only. See reports/admin-workflow-20261030/STATUS.md.

Release verified: static index-CXed5_X2.js and admin asset match live SHA256; protected entry/return path work, bank IN SYNC and health80,547/12,708. Temporary browser/database/services cleaned up. No backend or migration changes.

- [x] 2026-10-30: Preserve admin capabilities while consolidating review filters, deferring taxonomy, coalescing pending reads, enabling cross-page Save & next and returning to the exact report.

### Paper workspace — 31 October 2026

Implemented Paper / Focus / Question + PDF, whole-paper search, printed question map, visit flags/scratchpad, source page navigation/zoom and exam-aware GK/Science filtering. See docs/PAPER-WORKSPACE.md and reports/paper-workspace-20261030/STATUS.md. Persistent notes and source bounding-box highlights are future work, not claimed capabilities.

### 31 October 2026 — MCS Combined source expansion and paper roles

- [x] Add recovered2015/2017/2018Papers I/II as600provisionalsource records with PDF/images, explicit review labels and no inferred keys.
- [x] Version MCS Prelims into source-backed GS/Aptitude sections; retain role through topic/paper/practice links and support old all-paper bookmarks.
- [x] Display General Studies with nested Science for MCS while retaining clerical General Knowledge; distinguish quick timed practice and partial paper coverage.
- [x] Run293backend/34frontendtests, build, bank dry run and migration clone rehearsal; verify all600live records and149source assets.
- [ ] Repair36option extraction gaps and complete source/booklet/final-key checks, explanations and learning classification for the new600.
- [ ] Complete restored2023/2025source/key review, implement authentic source-confirmed simulation and independently inventory Mains. Source extraction restoration is completed below;2012/2013search is explicitly deferred by the owner.

### Deferred by owner — 2012/2013 MCS booklets

- [ ] Later: recover actual2012/2013Papers I/II from a working source or scan; do not repeat the same failed search without new evidence. Owner explicitly deferred this on31October2026. Continue remaining available MCSPrelimswork now.

### 31 October 2026 — Recent MCS source restoration

- [x] Restore480missing printed appearances from eight existing2023/2025PDFs; all16recentbooklets now contain printed1–100, with source page images and no inferred keys/tags.
- [x] Audit final-key compensation entries, place18existingquestions under audited scoring holds, and keep held questions visible in printed-paper browsing while excluding withdrawn records and grading.
- [x] Group MCS boxed cards by year and Paper I/II, retaining separate A/B/C/D selection, counts, source PDFs and answer readiness.
- [ ] Review the restored480transcriptions, three unresolved option extractions, classifications and final-key mappings; continue36recovered-copy source defects and checked explanations. Source coverage alone is not answer readiness.
- [ ] Implement source-confirmed original-paper simulation after complete paper/key/compensation adjudication; Mains remains separately inventoried future work.

### 31 October 2026 — MCS tags and final-key readiness

- [x] Reuse existing approved classifications for332restored copies with exact normalized stems and full ordered options; skip conflicting, unmatched and defective sources. Save bounded workshop claims and prove classification-only changes.
- [x] Publish329newofficial-key mappings from each booklet's own final key, with current source/key/baseline checks and no fabricated explanations.
- [x] Resolve the three earlier2025answer differences: final-key correction for I B Q15, date-range option restoration/final key for I B Q30, and equation/source image/page/final key/checked working for II C Q41.
- [x] Protect all24compensated source entries with persistent grading holds while retaining printed-paper browsing.
- [x] Keep official-key audit notes separate from optional worked explanations; retain strict explanation requirements for derived solutions and community MCQs.
- [x] Prevent owner export batches from racing the single-item publisher; reconcile99staleunappliedexports with unchanged source checks, immutable history and fresh decisions. Verify314backendtests and all live published values.
- [ ] Review148remainingrecenttaggaps (including three option extraction defects and three compensated entries); recovered600stillneed classification and source/key review. Continue useful worked explanations and historical2014/2016numbering audits before authentic simulation.

### 31 October 2026 — Recent MCS tags completed; continuation scheduled

- [x] Directly classify the148remainingrecentappearances with question-level evidence and a bounded workshop merge; preserve every non-classification field.
- [x] Restore2023II C Q86/Q87/Q96transcriptions through audited source publication while preserving compensation holds and unresolved-source review.
- [x] Publish60additionalexactfinal-keyanswers within ordinary staff quotas; retain honest missing worked explanations.
- [x] Exclude private-font glyph corruption and changed transcriptions from automatic key mapping; require explicit source/manual key review.
- [x] Schedule one same-thread continuation for1November02:10IST after the reported Codex reset, using latest checkpoints and separate website quotas.
- [ ] Continue80remainingautomatickeycandidates as rolling staff allowance permits, repairedQ87manualmapping, Q39root-glyph repair and three recent source-flag decisions. Recovered600classifications/36optiongaps, explanations and historical numbering remain before simulation.

### 31 October 2026 — Recovered MCS classification and maths continuation

- [x] Add373exact-matchapprovedlearningpaths and directly review64remainingrecoveredGSappearances; all300recoveredGSitems now classified, with no answer transfer.
- [x] Repair2025II C Q39's printed square-root approximation and publish its final-key B, plus2023II C Q87's final-key C, both with checked worked explanations.
- [x] Keep already-published repaired questions out of the new-key preparer's unfinished manual queue; verify30focusedtests and complete bank/live diff checks.
- [ ] Review163remainingrecoveredAptitudeclassifications and source/option defects; prepare80recentkeymappings for publication once ordinary staff allowance frees up (500/500used; recheck live rolling window).
- [ ] Continue worked explanations,2014/2016numbering and source-confirmed simulation prerequisites.2012/2013search remains deferred; scheduled continuation remains in place.

### 31 October 2026 — MCS learning classifications completed

- [x] Review and publish the remaining163recoveredAptitudetags with source passage/figure checks; MCS GS/Aptitude now have zero unclassified questions.
- [x] Prepare13source-onlytranscriptiondrafts from inspected pages for audited publication later; keep all answers, source flags and scoring holds unchanged.
- [x] Retain the02:10ISTCodexresetcontinuation and add one21:35ISTwebsiteallowancecontinuation on1November, both reading current checkpoints/quotas.
- [ ] Recheck staff allowance, then publish80preparedrecentkeymappings and source repairs using the audited workflow. Finish source flags, recovered booklet/final-key checks, explanations and historical numbering before original-paper simulation.2012/2013remainsdeferred.

### 1 November 2026 — Scheduled reset review and historical source audit

- [x] Execute early continuation; confirm Codex reset, website quota500/500, completed tags and no outstanding exports. Preserve canonical bank unchanged.
- [x] Audit600printedpositions across six imported2014/2016sourcePDFs; identify two duplicate imports, missing2014II Q39andtwo wrong page locators, plus missingQ38image. Save unapplied source/identity/history packet.
- [x] Add reproducible read-only audit CLI with13focusedtests; stage13checkedmathsexplanations for existing official answers without publishing or inventing peer review.
- [x] Discover/hash four unimported image-only2016-labelledPaperIIA–Dscans; inspect source headers/Q100andrecordOCRlimits and exact PaperI B cover-rule evidence.
- [ ] At21:35ISToronceactualquotaallows: reprepare/publish80recentkeymappings and reviewed source/explanation drafts through ordinary audited workflows. Historical duplicate retirement/new original-source ingestion need explicit history-preserving workflows, not community answer invention or relationship links alone.
- [ ] Plan careful source-only intake for the four scanned PaperIIbooklets, verify sitting/year/source and every printed position/figure/option, then version the collection. Do not blindly import legacyOCR or declare400verifiedquestions.2012/2013remainsdeferred; simulation stays gated.

### 1 November 2026 — Immediate MCS publication completed

- [x] Publish the remaining 80 source-checked recent official-key mappings with a scoped, audited exception authorized by the owner's immediate instruction after the quota blocker; leave ordinary website limits unchanged.
- [x] Publish 13 checked maths explanations while preserving existing official answers/key provenance.
- [x] Publish 13 recovered-copy source transcriptions without assigning answers or clearing source flags.
- [x] Restore 2014 II Q11/Q12 shared passages and Q38 diagram, then correct the two page locators using fresh source-reference exports.
- [x] Verify all 111 publications, full bank diff, exact live records, 24 compensation holds, learner history and unlimited owner access; restore publisher timer. MCS official-eligible increases 1,473 → 1,553. 49 focused tests pass.
- [ ] Continue three recent and 36 recovered-copy source-flag adjudications, additional explanations, history-preserving duplicate appearance repair and unanswered original-source intake for missing 2014 II Q39.
- [ ] Verify sitting/source identity and carefully transcribe four image-only Paper II booklet leads. Keep 2012/2013 deferred and authentic simulation gated.
- [x] Existing 21:35 IST follow-up cancelled at the owner's request on 1 November. Further content publication remains pending and requires fresh ordinary-allowance checks; prior scoped exceptions do not persist.

### 1 November 2026 — Explanation clarity and dated current-affairs revision

- [x] Separate MCQ format, answer provenance and explanation availability across Bank, detail, module study and paper browsing; preserve scoring rules and source identities.
- [x] Show missing explanations honestly and provide explanation-only proposals; add teaching/source/date guidance to contributor and admin forms.
- [x] Add three inspected-source editorial notes (2025 Shibu Soren example, Finance Commission period, Union Budget year comparison), effective/check/review dates, explicit unknown-update state and recheck-due handling.
- [x] Protect answer-bearing notes and links until answer/reveal; keep historical scoring unchanged and avoid assigning a year from an unrelated appearance on question detail.
- [x] Deploy the tested frontend after networking was restored; verify the live entrypoint, API health, bank sync and actual revision-note reveal in the browser, then push the completed release to GitHub. The earlier sandbox blocker is resolved.
- [ ] Continue substantive source-checked explanations and specific dated updates through the documented editorial/publication workflow. A full browser-managed update queue and separate per-explanation review metadata remain future work.

- [x] 2026-11-01: Explicit Check answer versus Show answer across bank/module/detail/paper practice; unified explanation/revision panel; protected reveal ledger and 30-minute retry window. Migration rehearsed/applied, API/web deployed, 329 API and 40 frontend checks pass; live reveal and reload safeguard verified. See docs/EXPLANATIONS-AND-CURRENT-AFFAIRS.md.

- [x] 2026-11-01 follow-up: restore private reading mode and retry time, unlock discussion after reveal with active-test/account/moderation protection, add saved revision / Retry later / contextual Next question, and defer daily-revision eligibility until cooldown expires. Bounded private state reads keep public catalog caching intact.
- [x] Review all 39 remaining MCS source flags against printed sources; prepare 31 transcription drafts, 35 separate source-clearance/answer drafts and four existing-key explanations, retaining four unresolved questions. Save exact source/answer checks and a predecessor-enforcing read-only preparer.
- [x] Publish the checked MCS follow-up packet: 105 audited decisions applied and verified on 1 November under the owner's explicit bounded quota exception. Includes 31 source repairs, 35 separate defect clearances, 32 unofficial solutions, three exact official keys and 39 worked explanations. Four unresolved sources remain flagged/unanswered. Ordinary limits unchanged; Codex continuation remains cancelled.
- [x] Deploy the final frontend restore-generation fix after network access was restored. Production build and live index match; fresh Show answer displays the answer, explanation, 30-minute retry countdown and unlocked discussion without reload. API healthy (81,627 / 13,163); family site returns 307. The owner cancelled the 21:35 IST continuation.

- [x] Add guarded owner batching for separately reviewed unanswered unresolved-source clearances; exact source, distinct choices, figure reference, source evidence and explanatory note required. All 353 backend tests pass; API deployed, publisher restored after live verification.


### 1 November — efficient recent MCS explanations and revision context

- [x] Use bounded Luna drafting with operator source/reasoning checks; prepare72explanation-only updates in28groups, preserving every existing answer and key reference. Save the strict live inventory and source/locator findings.
- [x] Add tested guarded explanation-only owner publication support;391backendtests and50frontendtests pass. Deploy API and six dated current-affairs notes, verify the live frontend and a protected source-specific note.
- [ ] Publish the checked72-item recent-explanation packet after the new bounded quota-exception choice is answered (or ordinary allowance becomes available). No new exception approval or publication has occurred at this checkpoint.
- [x] Audit original-simulation prerequisites and collect exact2025cover evidence; retain timed-practice labelling and compensation holds.
- [ ] Resolve the separate tenpage-locator/tworadicalstem findings and the unconfirmedEnglishmeaning/key review lead through fresh audited source/answer workflows. Continue the wider explanation backlog and simulation prerequisites;2012/2013recovery staysdeferred.
