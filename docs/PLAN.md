# Plan

Tick boxes as work lands. Each milestone ends in something deployed and
visible at https://study.hawayu.in — not a branch that "works locally".

## Milestone 1 — vertical slice: Bank → Question detail

One path end to end: Postgres → FastAPI → React → deployed with HTTPS.
The point is to prove the whole stack and build the deploy pipeline once.
Every later screen is then additive on a proven path.

- [x] Monorepo scaffold, docs, git init
- [x] FastAPI service: health, `/api/questions`, `/api/questions/{id}`
- [x] Design tokens + app shell (header, nav, area-colour dots)
- [x] Bank screen: list, filters, search, provenance labels
- [x] Question detail: options, answer-before-reveal gate, appearances
- [x] Deploy script + systemd unit + Caddy reverse_proxy
- [x] Verified in a browser (behaviour + network; colours need a human eye — see DEVLOG)

**Done means:** a real question from the 77,751 renders at
study.hawayu.in over HTTPS, with its provenance visible, no console errors.

- [x] Filter rail (answer-key provenance); topic + repeats blocked on data

## Milestone 2 — accounts and attempts

- [x] `scripts/sync-bank.sh` — local bank → server, user data preserved

- [x] Anonymous device id (accounts deferred — DECISIONS.md #6)
- [x] Record attempts with `chosen_text`, so re-scoring survives key fixes
- [ ] Practice mode drawing from `v_practice`, unverified answers labelled
- [x] Per-device progress (`GET /api/me/progress`)

## Milestone 3 — mocks

- [ ] Mock generation from `v_scorable` only
- [ ] Server-authoritative timer (client counts down, server validates)
- [ ] Results and mistakes review
- [ ] `thread_locks` while a mock is live

## Milestone 4 — community

- [ ] Discussion threads, hidden until the user answers
- [ ] Explanations / doubts / accepted answers
- [ ] Error reports; auto-hold at 3 independent reports
- [ ] Re-score affected attempts after a key fix

## Milestone 5 — games and multiplayer

- [ ] WebSockets on FastAPI, Redis for room state
- [ ] Duels (1v1), weekly cup, Gauntlet Run
- [ ] Leaderboards, XP with daily caps, coins

## Milestone 6 — the rest

- [ ] Study materials + `/` block editor
- [ ] Admin console (bank browser, corrections, dupes, builder)
- [ ] Moderation queue
- [ ] Pricing, checkout, Razorpay/UPI
- [ ] Mobile reflow and contrast pass

## Blocked / parallel track, not infrastructure

- [ ] **Subject classification of ~69,757 questions.** `subject` is NULL by
      design; until it is filled, subject-filtered mocks, topic quizzes and
      category-based multiplayer cannot work. This is the real critical path
      for the product and is independent of all the above.
- [ ] Resolve ~1,508 duplicate-option questions (answer text cannot identify
      which position was correct).
- [ ] Page-image pipeline: `pdftoppm` → WebP → Cloudflare R2.
