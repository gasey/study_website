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
12,454 questions with official keys, 59,047 with any answer — and improve
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
      beyond today's 12,454. A model may suggest into the review queue as
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
- [x] Bank card and filter rail, ported faithfully
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
- [x] **modules** (525, 53) — "Exams & tools" launcher, live at /exams
- [ ] **GET /api/collections** pagination/filtering when there is more than one exam
- [x] **ExamPage** (prototype `module`, 1699) — live at /exams/:id
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
      before code
- [ ] **onboard** (1676, 23), **account** (2064, 16)
- [ ] **profile** (924, 114) — materials, contributions, level, avatar
- [ ] **avatar** (1839, 77) — customisation bought with coins
- [ ] Migrate device attempts onto the signed-in user

## Phase 4 — community

- [ ] **feed** (169, 194) — the home surface. One area colour per card,
      white on neutral: doubts, materials, duel invites, calendar items, cup
      results, map challenges.
- [ ] **Discussion on a question** — hidden until the user answers (the gate
      is already enforced server-side). Explanations with one pinned, doubts
      with an accepted answer, error reports by type.
- [ ] **Error reports** — auto-hold at 3 independent reports; re-score
      affected attempts after a fix; +10 XP to reporters.
- [ ] **material** (823, 101) + **create** (728, 95) — the `/` slash-command
      block editor. Large; treat as its own sub-project.
- [ ] **inbox** (1064, 51), **news** (1792, 47), **calendar** (1618, 58)
- [ ] **partner** (1115, 274) — study desks and class desks
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

- [ ] **modq** (1483, 63) — Reported / New users / Appeals / My actions
- [ ] Conduct only; content accuracy stays with error reports
- [ ] 1–3 exams per moderator, 6-month terms, escalation over a rolling 90
      days. Tables already exist.
- [ ] `question_collections` must be populated or scoped queues return empty

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

- [ ] `India Study Map Mobile.dc.html` — 390×844, bottom tab bar
      (Home/Bank/Desk/Exams/Me), 44px minimum hit targets
- [ ] The handoff calls the mobile reflow and contrast pass **unfinished** —
      expect judgement calls, and record them
- [ ] **landing** (77, 92) — last, because it should describe a product that
      exists

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
