# Finnaplan — learning, points, desk and community design

One design file at the owner's request (15 November 2026), consolidating
the former LEARNING-SYSTEM-V2-DESIGN.md (Part I) and
DESK-VOCAB-COMMUNITY-V2-DESIGN.md (Part II). Part 0, added the same day,
is the whole-site product design and scaling plan; it sets the priority
order everything else serves — **browsing old questions first; the point
system is deliberately secondary**. Section numbers restart per part;
cross-part references are explicit. Status: proposal, nothing implemented.

**Update, 16 November 2026** (synced against the live code and DEVLOG):
Part I §5.5 (admin access grants) is now **implemented and deployed** as
migration `0089_owner_billing_access` — see the rewritten §5.5 for what
actually shipped, including a per-account price facility the original
draft did not anticipate. Billing reality also firmed up: the ₹100/month
standard price is live-configured in Razorpay (checkout still disabled
pending the owner's launch choice), new checkout is **monthly-only**, and
the owner can assign **₹50/month** to selected accounts. Migrations
0084–0089 are now taken (stats, current-affairs ×4, owner billing), so
the schema work this plan proposes starts at **0090+**, not 0084+.
Everything else in Parts I–IV remains proposal, nothing implemented —
verified: no `user_topic_mastery` or `review_items` exists in
`api/migrations/` or `api/app/`.

Added the same day, all design-only: **§0.9** (a reconstructed stub for
the access-model section lost in consolidation — owner should check it),
**§0.10** (general bank design: MPSC as first tenant, not schema),
**§0.11** (exam-first personalization: the chosen exam as the site-wide
lens over library/vocabulary/feed/boards, with the economy global),
**Part I §12** (focus subjects, the leaderboard decision, game boards,
Home layout, phone optimization §12.5, Expo widening §12.6),
**Part I §13** (assistant-proposed improvements awaiting owner yes/no),
a **§5.5 planned extension** (bulk ₹50 by email allowlist / group claim
code — phone matching deferred: accounts have no phone field), and
**Part V** (the phased implementation guide — V.0 gates through V.8
prohibitions). Nothing in them is built.

A **de-duplication pass** ran the same day: §9 items 8–10 removed
(two were duplicates of Part II §2.3/§1.4; mastery certificates cut as
badge-adjacent per §5.6), the question-of-the-day proposal cut (third
daily-question feature), Desk's weekly focus summary merged into the one
§12.1 growth recap, and §12.4 disambiguated against the deployed `/feed`
Home. Also added: **Part II §7** (composer v2, creator pipeline v2, and
the paid-content stance: capacity is paid, correctness never is) and the
**free-month decision** in §5.4 (points are the single loyalty path;
upvotes never pay; a "Your free month" meter on Rewards).

Finally, the owner said **"decide all for me"**: every open item in the
document is now resolved — Part I §11 (thresholds adopted, ≥60% game
gate, district stays Daily-Five-only, catalog-live gate, claim-code
100-uses/30-days, all §13 proposals approved with referral bounds),
Part II §6 (throttles stand; Mizo gloss on curated cards only), Part III
(drills on Today as suggestions; owner curates bindings first), the
§0.11.3 ≥50 cohort gate, and the §0.9 stub adopted as canonical. All are
assistant decisions under owner delegation, versioned, and tunable only
with real usage evidence. **The plan now contains zero open questions**;
what remains is building it, in Part V order.

Last addition the same day: **§14, the Helper Calendar** — one `/calendar`
of toggleable honest layers (official exam dates, my-exam countdowns, the
Leitner **review-load forecast**, recurring progress-test slots, private
personal entries, streak heatmap, cup/desk events) with an ICS feed so
phone calendars do the reminding. Mints nothing, punishes nothing; two
small tables; forecast layer ships free with V.2, the rest in V.5.

And a **surface consolidation pass** (§0.12): one place per job, binding
map. Revision unified at `/revise` (mistakes screen and vocab review
become views, printable sheet becomes an export button); Today lives on
Home only (the Desk's copy cut, its mastery strip too, its self-reported
weekly target retired); `/important-days` merges into Chronicle; the desk
calendar is a view of §14's one store; games get one Play hub; the Expo
app is scoped to native value (offline), never web parity. Structural
sentence: *Home decides, `/revise` executes, My Desk holds your things,
rooms are social.*

Completing the set, same day: **§0.13** (the interaction map — every
user-to-user touch in one table with its guards; no DMs by design),
**§12.7** (profile tools: identity, study setup, privacy/security with
data export + account deletion, wallet shortcut), **§13.1** (the
second-sweep gaps: legal pages and email recovery as hard checkout
gates, SEO prerendering for public pages as the missing growth engine,
self-hosted §0.8 measurement, a support surface, the V.9 accessibility
pass, per-body licensing checks, Mizo UI noted), **Part V extended to
V.13** (consolidation retrofit, community, growth, admin phases + the
one final build-order table), and **Part VI** (admin console &
maintenance: ops dashboard over worker heartbeats, retention workers,
restore-rehearsal discipline, feature-gates panel with checklists, the
read-only user viewer). The document is complete: zero open questions,
one build order.

---

# Part 0 — The whole site: product thesis, architecture and scaling

## 0.1 Product thesis and priority order (owner, 15 November 2026)

What people come to study.hawayu.in for **today is to browse and read old
exam questions**. Everything else exists to make that core act better and to
bring people back to it. The hierarchy, in order:

1. **Browse** — the question bank, past papers and exams. The product.
2. **Learn** — the practice → review → mock loop (Part I). The retention
   layer that grows naturally out of browsing.
3. **Community & games** — the reasons to come back with other people
   (Part II + Part I §5.1 Play pillar). Social proof and fun, anchored to
   the same questions.
4. **Points & XP** — ambient reward. "Good that it's there," never the
   point. It seasons the loop; it must never gate, interrupt or headline
   anything.

Access implication — **revised by the owner later on 15 November 2026**
(the original draft said browsing would never be gated; §0.9 supersedes
that): browsing is free to *taste* as a guest, free in a chosen exam's
scope with an account, and unlimited — including cross-exam subject-wide
browsing — with Pro or points. The door is open, the library card is free,
the full archive is membership. Sign-up and upgrade are still earned by
demonstrated value, never demanded before value is shown, and §0.9's
integrity rules (no mid-question rug-pulls, honest meters, downgrade-safe
history) are binding.

## 0.2 The browse experience — the core product

Three entry geometries over the same bank (~78k questions, ~1.9k papers,
82k+ live appearances; fresh counts from the live DB, not this document):

- **By exam**: `/exams` → exam detail → its papers by year → paper view.
  The learner's mental model is "show me what this exam asked before."
- **By paper**: `/past-papers` directory → a paper in **original printed
  order** with booklet/series identity, source typography and the original
  PDF alongside (0077 library). The paper is a historical document; we
  preserve it, we don't reflow it.
- **By topic/search**: subject → topic drill-down (usable since the 8
  November taxonomy publication) and full-text search (0043) with
  filter chips (exam, year, subject, answer status).

The question card contract, everywhere it appears:

1. Question + options exactly as printed (figures, directions, emphasis).
2. Answer behind the existing reveal gate, labeled by provenance per
   `PUBLIC-ANSWER-LANGUAGE.md` — Official key / Verified answer /
   unverified states shown honestly. **Provenance is a display property,
   not a visibility filter**: the whole bank is browsable, including the
   ~84% without official keys; only scoring and rewards are restricted to
   the verified pool. This is what makes browse-first viable at all —
   browsing needs no answer guarantee, scoring does.
3. Source line: exam, year, paper, question number; dispute/provisional-key
   notices preserved.
4. **Inline answering** — one tap to attempt right on the card (the
   established prototype pattern). This is the single bridge from browsing
   to learning; it must stay frictionless and optional.
5. Explanation when published; discussion thread beneath, behind the
   disclosure gate.

Performance is a browse feature: paper views and filter flips must feel
instant. The two known slow queries get indexes/rollups before any growth
push, and Part I's mastery/progress rollups remove the per-request
`attempts` aggregation.

## 0.3 The progressive learner journey

Browsing converts to learning by gradient, never by wall:

```
read questions → tap an answer inline → device progress appears
→ natural account prompt (keep progress across devices / save a bookmark)
→ mistakes collect themselves → Smart Review offers itself on Today
→ mocks when ready → mastery map grows → points tick ambiently
```

Each step is offered at the moment it is useful, inside the browse flow —
never as an interstitial. Guests get the full browse experience plus
device-local progress; accounts add sync, review scheduling, rewards and
community voice. The Today card (Part I §4.3) is the signed-in home, but
the signed-out home is still a great library, not a locked lobby.

## 0.4 How community should work

Community is **anchored to the questions themselves**, not a parallel
social app. The doubt/explanation thread under each question is the atomic
unit (it already exists); the feed (Part II §3) is an aggregator over that
activity plus light study posts — a window into the library, not a
destination that competes with it. Desks stay private small-group spaces.

The compounding loop: a browser hits a confusing question → asks a doubt →
a Mentor-tier learner answers → the accepted answer sits on that question
for every future browser. Community effort accrues to the browse surface
permanently, which is why helpfulness earns standing (Part II §4.2) and why
social activity never needs to earn points to be worth doing.

## 0.5 Where games fit

Games are the same bank with a timer and company — casual on-ramps, never
homework. Daily Five is the one-tap daily hook; duels/cups/trail serve the
committed; a later "challenge a friend on this paper" affordance starts
games directly from browse. Game awards stay inside the Play sub-cap
(Part I §5.1) and server-owned results; games are optional by construction,
and no learning content is exclusive to them.

## 0.6 Where points fit (deliberately quiet)

Points surface in exactly three places: a small toast on earn, the wallet
on Profile/Rewards, and the catalog at redemption. No currency UI on browse
surfaces, no streak-guilt modals, no gated content. The calibrated economy
(Part I §5.4) stands unchanged — it simply isn't the headline.

## 0.7 Scaling plan

**Content scale** (the real growth axis):

- **S1 — deepen MPSC**: finish the parse/key backlog in the bank workshop
  (unparsed clerical papers, un-OCR'd answer keys), grow the verified pool
  from ~16% via key ingestion + the contribution pipeline. Every verified
  answer upgrades browse (labels), learning (scorable) and economy
  (rewardable) at once — the flywheel.
- **S2 — adjacent Mizoram exams**: MUDAL/other state bodies through the
  same paper → review → publish machinery; browse-only content is
  acceptable at entry (honest labels), verification follows demand.
- **S3 — beyond Mizoram**: the "India Study Map" name is the ambition; the
  exam-scope machinery (`exam_scope`, collections, Mizoram launch scope
  0046) already isolates cohorts, so new exams are data work, not
  architecture work.

**Traffic/infra scale** (staged by measurement — the OCI baseline of
~5.4k tps on the 77k bank says the single VM has real headroom):

- **T1 (now)**: fix the two known slow queries; ship the Part I rollups;
  add `Cache-Control: public` + ETag to anonymous browse responses
  (question/paper/exam reads are identical for every guest — let Caddy and
  browsers absorb them).
- **T2**: edge/CDN caching for anonymous browse, PDFs to object storage,
  connection pooling and Postgres tuning. Mind the shared-Caddyfile rule —
  study and family share the server.
- **T3 (only if measured demand)**: read replica for browse reads, a real
  search index when ILIKE degrades, horizontal split of API/DB. Stay on
  current cheap infra until ₹100 subscriptions pay for the next tier.

**Sequencing** (supersedes neither Part I §10 nor Part II §6 — it orders
them):

| Stage | Focus | Contents |
| --- | --- | --- |
| Now | **Browse excellence** | past-paper directory polish, search/filters, speed (T1), provenance labels everywhere, finish Finna port of remaining screens |
| Next | Learning loop | Part I phases 1–2 (mastery, Smart Review, Today, unified streak) |
| Then | Community & play | Part II feed/posts/votes, desk v4, vocabulary; Daily Five prominence |
| Later | Economy & scale | Part I phase 3 (spread, catalog live, admin grants), S2 content, T2 infra |
| Eventually | Expansion | S3 exams, mobile app parity (MobileBoundary widening per feature), T3 infra |

## 0.8 What success looks like (honest metrics only)

Measured from real activity, never invented: papers browsed per session and
search success rate (browse health); share of browsers who attempt at least
one question inline, and of those, 7-day return rate (the conversion that
matters); due-review completion rate (loop health); share of doubts with an
accepted answer within 48h (community health); redemption rate (economy
health — should be modest and stable, not viral). If browse metrics and
loop metrics ever conflict, browse wins — per §0.1.

## 0.9 Access model (reconstructed stub, 16 November 2026)

⚠ §0.1 cites a "§0.9" that was lost in the 15 November consolidation of
the two source documents. This stub records only what §0.1 itself
attributes to it, so the reference resolves. **Adopted as the canonical
§0.9 on 16 November 2026** under the owner's "decide all for me" — if a
richer pre-consolidation draft ever resurfaces, restoring it is an owner
edit, not a correction of this one. As cited:

- Browsing is free to **taste** as a guest, free within a **chosen exam's
  scope** with an account, and **unlimited** (including cross-exam
  subject-wide browsing) with Pro or points.
- Integrity rules, binding: **no mid-question rug-pulls** (a question you
  opened never slams shut over you), **honest meters** (any allowance
  shown is the real server-side number), and **downgrade-safe history**
  (losing Pro never deletes or hides what you already did).
- Sign-up and upgrade are earned by demonstrated value, never demanded
  before value is shown (§0.1, §0.3).

### 0.9.1 The authentication system (16 November 2026 — state + decisions)

What exists, verified: password + Google identity (0071), TOTP MFA
(0033), email-recovery schema (0057) **with no mail provider wired**,
server-issued HttpOnly guest identities (0056) with guest→account
progress adoption, session cookies with same-origin CSRF, mobile PKCE
pairing with `MobileBoundary` (IV.3, IV.8). Decisions completing it:

1. **Two sign-in methods, no third.** Password and Google. No phone OTP
   (no SMS infra — the recorded scope cut), no magic links until the
   mail provider exists, no new identity providers without an owner
   decision.
2. **Email verification becomes required for *new* accounts only after
   the mail provider ships** (§13 #1); existing accounts are
   grandfathered and nagged gently, never locked out of what they
   already had.
3. **MFA**: optional for learners (it exists; §12.7 surfaces it),
   required for staff (existing policy with the one recorded exemption).
4. **Login throttling** (§13.1 #15): per-account + per-IP backoff,
   lockout recoverable via email — ships in V.2.
5. **Sessions**: list + revoke in §12.7; sign-out-everywhere included.
6. **An account is required for**: sync, rewards/wallet, community
   voice, desks, calendar personal layers, mobile pairing. Never for
   reading the library (§0.1).

### 0.9.2 The paywall — fair, limited, and honest about what it sells

Owner direction: a free tier that *gives the real idea of the app*, with
the squeeze on what aspirants value most — **old-question practice
volume and power filtering** — because that is what they'll pay for.
Governing rule (§7.3): **capacity and convenience are paid; correctness
and reading never are.**

| Capability | Guest | Free account | Pro (₹100/50) |
| --- | --- | --- | --- |
| Read papers & questions (printed order, PDFs) | ✓ full, in chosen-exam taste | ✓ full within chosen exam | ✓ everything, cross-exam |
| Answer reveals | 20/day (device) | ✓ unmetered in scope | ✓ |
| Basic filters (exam, year, subject) | ✓ | ✓ | ✓ |
| **Power filtering** — multi-dimension combos (topic × year-range × answer-status), saved filter sets, cross-exam subject browse | — | taste: 3 power-filter queries/day | ✓ unlimited |
| Practice answers (scored) | device-local only | **50/day** (existing) | unlimited |
| Mocks | — | **1/month** (existing) | unlimited |
| Smart Review | — | 1 session/day (matches the award bound anyway) | unlimited sessions |
| Mistakes depth | — | last **20/day** (existing) | full history |
| Printable revision sheet | — | — | ✓ |
| Community (read/post/vote) | read | ✓ full | ✓ (never gated — community is trust, not inventory) |
| Daily Five, games | ✓ play | ✓ + earns | ✓ |
| Desk rooms | — | join | create (existing 3/owner) |
| Trial | — | **7-day no-card Pro trial** (existing) | — |

Why this split is fair *and* sells: the free account is a complete
studying life — a learner can browse their whole exam, practice 50
questions a day, keep a streak, review mistakes, post doubts, and earn
points toward a free month forever. What Pro adds is exactly what a
serious aspirant hits naturally in week two: the 51st practice question,
the second mock before the real exam, the topic×year×status filter
sweep, the full mistake history, cross-exam breadth. The limits teach
the value honestly instead of hiding it.

Integrity rules (binding, restating §0.9 with teeth):

1. **No mid-question rug-pulls**: a question already open never locks;
   limits gate the *next* action, with the meter visible before it.
2. **Honest meters everywhere**: "37/50 today", "1 mock available in
   March", "2 of 3 power filters used" — real server numbers (§0.6),
   shown *before* the wall, never as a surprise 402.
3. **Downgrade-safe**: lapsing Pro loses capacity going forward, never
   history — attempts, mastery, wallet, posts all remain.
4. **The limits are generous on purpose**: 50/day ≈ a solid daily
   session; the squeeze is on bingeing and power tooling, not on habit
   formation — the free loop must stay good enough to build the habit
   that makes Pro worth paying for.
5. **Earned Pro is identical to paid Pro** (redemptions/grants read
   through the same `account_has_pro()`); there is no second-class Pro.
6. Checkout gates stand (§13.1): legal pages + email recovery before any
   of this takes money.

Power-filter metering is the one new mechanism (a daily counter row,
same `rate_limits` helper Part II's throttles use); every other number
in the table already exists in production config. Build: the free-tier
numbers are live today; power-filter gating and the meter UI ride V.1's
browse work (the filters are being built there anyway).

## 0.10 General bank design — MPSC today, any exam tomorrow (16 Nov 2026)

Owner direction: the bank is currently MPSC questions; the design must be
a **general, exam-unspecified bank** where MPSC is the first tenant, not
the schema. This elaborates §0.7's S2/S3 into binding rules:

1. **Exam identity is data, never schema or code branches.** Exam bodies,
   exams, papers and collections are rows; `exam_scope` + collections +
   the Mizoram launch scope (0046) already isolate cohorts. New
   bank-reading code takes an `ExamScope` (IV.2) and must not contain
   body-specific conditionals. Historical names stay (the `mpsc` DB role,
   existing IDs) — renaming working history is churn, not generalization;
   the rule applies to *new* code and copy.
2. **One shared taxonomy, per-exam syllabus mappings.** The approved
   subject/topic/subtopic registry is global; an exam maps its syllabus
   onto it (which topics are in scope, in what weight/order) rather than
   forking it. Part I mastery is keyed `(subject, topic)` — exam-agnostic
   by construction — and the saved exam / focus subjects (§12.1) are the
   lens over it. Registry additions follow the existing tagging policy
   (`QUESTION-TAGGING-RULES.md`); a new exam never mints its own parallel
   taxonomy.
3. **Canonical identity stays within its source.** A question belongs to
   the paper that printed it; the same question appearing across bodies
   or years is appearance/presentation grouping, **never a canonical
   merge** (existing rule, restated because multi-exam makes the
   temptation constant). Cross-exam "similar questions" is a display
   feature, not a data operation.
4. **Per-exam honesty about verification.** Each exam's verified-answer
   pool grows independently; browse-only content is acceptable at entry
   (S2), provenance labels say so, and scoring/rewards stay restricted to
   each question's own verification state. No exam borrows another's
   credibility.
5. **One ingestion machinery.** New bodies are new source
   configurations into the same parse → review → guarded-publication
   pipeline on Oracle — never a second pipeline, never a second writable
   bank. Review ownership/attribution rules travel unchanged.
6. **Economy and learning are already general.** Discovery claims are
   per canonical question; caps are per account; mastery is per topic.
   Nothing in Part I needs a multi-exam change — which is the test that
   the generalization is right.
7. **Naming.** Public copy moves toward exam-neutral framing ("the
   bank", "past papers", per-exam titles from data). "India Study Map"
   remains the ambition name (S3); nothing user-facing should newly
   hardcode MPSC.

Onboarding a new exam body is therefore a **checklist, not a project**:
create body/exam/collection rows → map syllabus onto the registry →
ingest papers through the pipeline → verify labels render honestly →
enable its `exam_scope`. (Part V §V.7 carries the operational version.)

## 0.11 Exam-first personalization — the chosen exam as the site-wide lens

Owner direction (16 November 2026): the site runs on exams over the bank
— filters, practice, everything. When further exams exist (MPSC, SSC, …),
a learner **chooses what they are preparing for**, and every surface —
vocabulary, English, the XP displays, the feed — follows that choice.
§0.10 made the bank general; this section makes the *experience*
specific. The governing metaphor: **the chosen exam is a lens, never a
wall** — it reorders and pre-filters, it never deletes, hides earned
progress, or locks a door the access model (§0.9) left open.

### 0.11.1 The primary exam

- Learners can save multiple exams (the catalog's save/compare already
  exists); exactly **one is primary** at a time. Switching primary is
  free, instant, and non-destructive — re-lensing, not resetting.
- Onboarding asks one question — "What are you preparing for?" —
  skippable, offered at the §0.3 gradient moment, never as a wall.
  Guests and skippers get the neutral all-exams view with honest
  defaults.
- Schema sketch: extend the saved-exam mechanism with an `is_primary`
  flag, plus the §0.10.2 syllabus mapping made concrete:
  `exam_syllabus(exam_id, subject_id, topic_id NULL, weight,
  display_order)` — the one table every scoped surface reads. Built when
  the second exam body onboards (V.7); until then the MPSC scope
  machinery already answers every query.

### 0.11.2 The cascade — what the lens does per surface

| Surface | With a primary exam | Without |
| --- | --- | --- |
| Browse/bank | default filter chips pre-set to the exam; cross-exam browsing per §0.9 tiers | neutral directory |
| Practice / Today / Smart Review | new-question targets from `exam_syllabus` ∩ focus subjects (§12.1); the review queue still reviews *everything you got wrong*, whatever exam it came from — forgetting is exam-agnostic | saved-scope fallback, then honest empty state |
| Library modules (English, vocabulary, arithmetic, Mizo) | modules and decks carry exam applicability **derived from the syllabus mapping** (bank-derived decks inherit it from their source questions; curated decks get explicit exam tags at review time); the grid orders relevant modules first and labels the rest "not in <exam>'s syllabus" — labeled, never hidden | full grid, no labels |
| Games | question pools draw from the primary exam's scope by default; party/duel rooms may explicitly choose another scope; Daily Five stays cohort-specific where its content is (the district dimension is MPSC-shaped) | all-exams pool |
| Feed | question-anchored posts inherit their question's exam automatically; `study` posts take an optional exam tag; the For-you `T` affinity term (Part II §4.3) already boosts your exam — add an exam filter chip, default "my exam + general", always escapable | chronological, unscoped |
| Current affairs | briefs/quiz items carry exam-relevance tags at review time; default view scoped, full list one tap away | full list |
| Leaderboards & leagues | cohort by primary exam **only once population justifies it** (see 0.11.3) | global board |
| XP / points / streak / level | **global, always** — see 0.11.3 | same |
| Mastery | global data, exam-lensed display: the map defaults to the primary exam's syllabus subjects; everything else remains below | full map |

### 0.11.3 The economy stays whole (the one thing the lens never touches)

One account = **one XP total, one level, one wallet, one streak** across
every exam, permanently:

- Earning rules are already exam-agnostic (per-canonical claims,
  per-account caps — §5.1); the lens changes *which questions are
  suggested*, never what they pay. Nothing to farm by switching exams.
- Switching primary exam loses **nothing**: mastery rows, review queue,
  history, points all persist; an aspirant who moves from MPSC to SSC
  keeps their English mastery where the syllabi overlap — that is the
  shared-registry dividend (§0.10.2).
- Leaderboard cohorting is **display segmentation, population-gated**:
  boards split per exam only when a second exam has enough weekly-active
  opted-in accounts to make a real room (**≥50, adopted 16 November
  2026** under "decide all for me"; still tunable with evidence).
  Until then, one global board — §12.2's no-empty-rooms rule outranks
  cohort purity. Game boards follow the same gate.

### 0.11.4 Honesty rules for the lens

Scoping must stay a convenience, not a dark pattern: pre-set filter chips
are visible and removable, not silent; "not in your syllabus" labels are
derived from the reviewed mapping, never guessed by a model; relevance
tags on current affairs/decks are set at human review time; and no
surface ever shows a smaller number (due reviews, mistakes, wallet) than
the account's true total because of the lens. When a scoped view is
empty, it says "nothing in <exam> yet — see all", with the unscoped view
one tap away.

## 0.12 One place per job — the surface consolidation map (16 Nov 2026)

Owner direction: merge conflicting or redundant systems — "no same thing
in different places to avoid confusion for users." This section is the
**binding map**: for each job a learner has, the ONE surface that owns
it, what merges into it, and what that retires. Later sections are
amended where they conflicted; where two surfaces legitimately share
data, one owns the store and the other is a declared *view* of it.

| The job | The one place | Merges into it | Retired / demoted to a view |
| --- | --- | --- | --- |
| Revise what I got wrong | **`/revise`** — Smart Review + the queue browser | mistakes screen (becomes the queue's browse tab), due vocabulary (same Leitner queue, `item_type='vocab'`), printable sheet (an export button here, not a feature) | the standalone mistakes screen; any separate vocab-review entry |
| My daily plan | **Today, on Home only** | — | the Desk's copy of Today (Desk v4 §1.1 is amended below) — the same card in two homes was the confusion this section exists to kill |
| Weekly self-assessment | **progress-test slot (§14) + Monday growth recap (§12.1)** | — | the Desk's self-reported weekly answer target (self-reporting also violated the honest-counting rule) |
| What's coming (dates, schedule) | **`/calendar` (§14)** | desk calendar = a room-filtered *view* of the same store | any second calendar store |
| What happened (dated history content) | **Chronicle** | `/important-days` (its date list/calendar was Chronicle's job wearing an older skin) | `/important-days` as a standalone route — redirect in |
| Place-based study | **Atlas** | Chronicle cross-links by binding table (III.2.6) — links, never duplicated timelines | — |
| Discussing a question | **the question's own thread** (public) | — | Desk rooms keep *private* discussion (§1.5), but a room answer that deserves permanence is posted to the question's thread — the room never becomes a shadow Q&A that future browsers can't find |
| My wallet / earning | **Rewards screen** (with the free-month meter) | — | §0.6 already bans currency UI elsewhere; restated as a map row |
| Playing with the bank | **one Play hub** route | all 7 game modes + Daily Five + cups + Topic Trail as entries in one grid | scattered per-mode entry points |
| Notes, saved items, focus timer | **My Desk (personal)** — now purely a toolbox | — | its loop/plan ambitions (moved to Home), its weekly target (retired above) |

Two structural decisions underneath the table:

1. **Home is the dashboard; the Desk is the room; Revise is the gym.**
   The deepest previous confusion was three surfaces (Home, personal
   Desk, mistakes screen) each claiming a piece of "where I study
   today." Now: Home *decides* (Today, continue, recap), `/revise`
   *executes* the review work, My Desk *holds your things* (notes,
   saved, focus), and group Desk rooms are social spaces. No surface
   claims another's verb.
2. **The phone web is THE mobile experience; the Expo app is the
   offline companion.** The app does not chase screen parity — every
   `MobileBoundary` widening must be justified by something *native*
   (offline practice and replay, later push), never by "the web has it."
   One design language, one reference (`finna-20261114`), two renderers
   with deliberately different scopes — the alternative is maintaining
   every screen twice and shipping both late.

My additions (same one-place discipline applied forward): the ⌘K-style
quick switcher on web should be the *only* global search entry (search
boxes on individual screens scope to that screen, visibly); and the
Inbox stays the single notification surface — no screen grows its own
bell, badge or activity popover, ever. Both are cheap rules now and
expensive regrets later.

## 0.13 The interaction map — every way users touch each other (16 Nov 2026)

Owner request: design "users' interactions across the website" as one
system. This is the complete inventory — if an interaction isn't in this
table, it doesn't exist, and adding one means adding a row *with its
guard column filled in first*:

| Interaction | Where | Guard rails |
| --- | --- | --- |
| Reply to a doubt / explanation | question threads | disclosure gate, throttles (§3.3), reports, blocks |
| Accept an answer | own doubt | author-only; accepted reply locks (§7.1.5) |
| Helpful vote | posts | one per account, weighted by study history (§4.1), never self, never across blocks, never currency |
| Follow | profiles, feed | one-way, free, earns nothing; honest counts |
| Study post / material share | feed | §3.1 kinds, §3.3 throttles, tier lifts |
| Desk room membership | private rooms | invite-only, six seats, Pro-gated creation, retention purge |
| Room chat / review circle / shared goal | inside a room | room-private; permanent answers go to the question's thread (§0.12) |
| Duel / party / cup | games | server-owned results; §0.5 "challenge a friend on this paper" starts from browse |
| Shared-test challenge | link-scoped boards (§9.6) | visible only to link holders; normal discovery economy |
| Leaderboard presence | XP/game boards | opt-in, handle+XP+rank only (§12.2) |
| Profile view | creator/member profiles | shows only opted-in, computed-public facts |
| Block | everywhere | one block model, enforced in every list, vote, feed, room invite and board — no surface exempts itself |
| Report | any content | feeds the one moderation queue (VI.2 pulse) |

Deliberate absences, recorded as decisions: **no 1:1 direct messages**
(a private-DM surface is the single largest moderation liability a small
team can acquire; desk rooms are the private space, and they have seats,
invitations and retention); no @-mentions (§7.1.7); no gifting or
point transfers (§3 invariants); no public follower-count races (counts
shown are honest integers on the profile, never ranked).

Invariants that bind every row, current and future: blocks apply
*everywhere* without exception; every interaction is opt-in-able or
ignorable; none of it ever mints currency (§4.2); guests read, accounts
act; and each row names the one owning surface — an interaction never
gets a second home (§0.12).

---

# Part I — Learning system & point system

Status: **proposal, nothing implemented — except §5.5, which shipped
16 November 2026** (migration 0089; see that section for as-built facts).
Drafted 15 November 2026 by an AI
assistant for owner review; every reward amount, threshold and catalog change
below is a suggestion requiring an explicit owner decision before any migration
is written. This document extends `LEARNING-REWARDS.md` (award policy v1,
deployed 2026-10-21); it does not replace it, and it changes no bank content,
keys or scoring rules.

## 1. Baseline: what learning-v1 already provides

| Area | State | Where |
| --- | --- | --- |
| Currencies | XP (activity) + reward points (spendable), strictly separate from marks and contribution credit | `reward_ledger`, DECISIONS #16 |
| Earning | First correct answer to a unique verified-key MCQ: 10 XP + 1 pt; 300 XP/day shared cap; once-per-canonical lifetime claim | `learning_rewards.py`, migration 0034 |
| Progression | Levels `floor(sqrt(XP/40))` with scholar titles; weekly-XP leagues; opt-in leaderboard | `/api/rewards/me`, `/api/rewards/leaderboard` |
| Habit | Streak + purchasable shields (25 pts); three daily quest rings; Daily Five (0083) | `reward_profiles`, `daily_quest_claims`, `game_dailies` |
| Spending | Catalog with one offer (pro-week, 1000 pts, **disabled** pending launch review); 1 redemption/account/30 days | `reward_catalog`, `reward_redemptions` |
| Learning surfaces | Practice, study sessions, mocks with frozen snapshots + reassessment, 7 game modes, Topic Trail, vocabulary drills, mistakes list, study desks | respective routers |

The v1 economy is sound: server-owned, immutable ledger, idempotent,
provenance-gated. **The gap is pedagogical, not mechanical.** v1 rewards
*discovery* only — a question pays once, ever — so the economy rewards grinding
new questions and pays nothing for retention. There is no mastery model, no
review scheduling, and two streak implementations that disagree
(`reward_profiles` vs the attempt-derived streak in `/api/me/progress`).

The 8 November 2026 owner-authorized taxonomy publication (58,197 corrections,
`owner-taxonomy-final-20261108`) is what makes v2 feasible: topic labels are now
good enough to aggregate mastery per topic, which was not true in October.

## 2. Design goals

1. **Pedagogically robust** — close the learn→forget gap with scheduled review
   and a visible mastery model; the loop is Diagnose → Plan → Practice/Review →
   Prove (mock).
2. **Economically robust** — no inflation, no farmable source, every award
   server-derived from scored evidence, flat auditable rates.
3. **Operationally robust** — incremental rollups instead of full `attempts`
   scans per progress call; everything idempotent and replay-safe.
4. **Honest** — provenance rules intact: inferred/derived answers never score,
   never pay, and are always labeled per `PUBLIC-ANSWER-LANGUAGE.md`; empty
   states stay empty.

## 3. Invariants carried forward (non-negotiable)

- XP ≠ points ≠ exam marks ≠ contribution credit (DECISIONS #16). Spending
  never lowers rank.
- Rewards require: registered account, server-scored correct answer,
  `answer_source IN ('official','key')`, current `v_scorable` eligibility.
  Guests accumulate progress but never currency.
- Single immutable ledger, unique `event_key`, per-user reward lock, shared
  300 XP/day budget, no client award endpoint.
- Difficulty labels are retired (DECISIONS #19). Nothing below reintroduces
  them; where "hard for this learner" matters, it is derived from that
  learner's own attempt history, never from a label and never as a pay
  multiplier.
- No wagering, transfers, cash-outs, bought ranking boosts, or second cosmetic
  currency.

## 4. Learning system

### 4.1 Topic mastery model

Per `(user_id, subject_id, topic)` using **approved**
`question_classifications` only. States:

```
unseen → exploring → practicing → proficient → mastered
                                      ↓ (decay, display-only)
                                    rusty
```

Thresholds (**adopted as initial constants 16 November 2026**, §11 item
1; versioned like `RULE_VERSION`, tuned only against real usage):

| State | Entry condition (verified-key questions only) |
| --- | --- |
| exploring | ≥1 scored attempt in topic |
| practicing | ≥5 distinct questions attempted |
| proficient | ≥10 distinct attempted AND latest-attempt accuracy ≥70% |
| mastered | ≥20 distinct attempted AND latest-attempt accuracy ≥85% AND one completed review session touching the topic ≥14 days after reaching proficient |
| rusty | proficient/mastered with no verified activity in topic for 45 days — a display overlay; the earned tier is never removed |

Rules:

- Only server-scored attempts on verified-key questions move mastery.
  Attempts on inferred/derived questions appear in activity history but are
  excluded, exactly as they are excluded from rewards today.
- "Latest-attempt accuracy" uses the same latest-assessment semantics as
  `/api/me/score-summary`, so key corrections and reassessments (migration
  0032) re-derive mastery rather than freezing a wrong snapshot.
- Mastery is a *study aid*, not an exam-readiness certification; copy must say
  so (same honesty rule as the activity leaderboard disclaimer).

Storage: new rollup table `user_topic_mastery` maintained incrementally on
attempt insert and on reassessment completion (reusing the 0032 job pattern).
`/api/me/progress` reads the rollup instead of re-aggregating all attempts on
every call — this also fixes the known perf debt of live aggregation.

### 4.2 Review scheduler (spaced repetition)

A Leitner 5-box queue per `(user_id, canonical_id)`, **verified-key questions
only** (reviewing a question with an unverified answer would be teaching
unproven facts on a schedule):

- Wrong answer → box 1. Correct answer → promote one box.
- Box intervals: 1, 3, 7, 16, 35 days (IST dates, like every other boundary).
- Box 5 correct → graduated (leaves the queue; mastery keeps the credit).
- Seed on rollout from the existing mistakes data (latest-attempt-wrong
  questions enter box 1). No reward backfill of any kind.

Surface: **`/revise` — the one revision destination** (§0.12). It holds
the Smart Review session — server-composed from due items (cap ~20
per session, oldest-due first), run through the existing
`practice_study_sessions` machinery with `attempts.context='review'` (already
in the context CHECK since 0002) — plus the queue browser (the former
standalone mistakes screen, now a tab here), due vocabulary (same queue,
`item_type='vocab'`, Part II §2.3), and the printable-sheet **export
button** (§9.7 is a button, not a feature). Nothing else on the site
offers "review" under any name.

### 4.3 Daily plan ("Today")

A server-composed card for the Finna Home plan column:

1. due reviews (count + one-tap Smart Review),
2. a new-questions target drawn from the learner's weakest
   practicing/proficient topics *within their saved exam's scope*,
3. the Daily Five,
4. quest ring status.

All live data; a new account or a cleared queue shows an honest empty state,
never invented tasks. Guests see the plan (it drives learning) but, as
everywhere, earn nothing from it.

### 4.4 Mocks

Unchanged in v2. A later phase may let `mastered` require a mock-section
threshold; explicitly out of scope now.

## 5. Point system v2

### 5.1 Earning spread (owner direction, 15 November 2026)

The owner's requirement: points must be **spread across the different
activity pillars** — quiz games, tests, practice, revision, contributions —
so no single activity fills the wallet. The mechanism is **per-source daily
sub-caps** under the overall 25-pt/day cap (§5.4): the sub-caps sum to ~34,
so a learner reaches the 25-pt ceiling only by mixing pillars, and grinding
any one pillar stalls out well short of it. XP is untouched by sub-caps
(still only the shared 300 XP/day budget), so leaderboards keep rewarding
raw activity while the wallet rewards balanced study.

All awards are server-derived ledger rows with namespaced `event_key`s (no
ledger CHECK change; existing kinds reused):

| Pillar | Event | Award | Daily points sub-cap | Bound / idempotency |
| --- | --- | --- | --- | --- |
| **Learn** (practice & in-quiz discovery) | first correct answer to a unique verified-key MCQ (v1 rule, unchanged per-event) | 10 XP + 1 pt | **12 pts** | once per canonical, ever (existing claim) |
| **Revise** | Smart Review session completed: ≥8 due items, ≥60% correct | 20 XP + 2 pts | **4 pts** (2 sessions) | `review:{user}:{ist_date}:{n}` |
| **Prove** (tests) | full mock submitted, non-late, frozen snapshot (v1 eligibility) | 30 XP + 3 pts | **3 pts** (1 mock) | `mock:{user}:{session_id}` |
| **Play** (quiz games) | completed multiplayer/solo game (gauntlet, speed, duel, party, cup, trail) with server-scored result ≥60% correct | 15 XP + 2 pts | **4 pts** (2 games) | `game:{user}:{room_id}`, kind `game` |
| **Play** | Daily Five entry completed | 10 XP + 1 pt | **1 pt** | existing one-entry-per-day PK |
| **Habit** | quest rings claimed (§5.2): warm-up / review / plan | 20+30+50 XP, 2+3+5 pts | **10 pts** | existing `daily_quest_claims` |
| **Milestones** | topic reaches proficient / mastered | 30 XP + 3 pts / 60 XP + 5 pts | outside sub-caps, inside 25 cap | `mastery:{user}:{topic}:{tier}`, once per topic-tier, ever |

Notes on the spread:

- **Discovery is deliberately the narrowest point source** relative to v1
  (12 pts/day vs an effective 30): answering new questions keeps paying full
  XP up to the 300 cap, but wallet growth now requires revision, tests and
  games too. This is the owner's "spread" requirement expressed as policy.
- Game awards pay on **server-owned results only** (frozen room snapshots,
  server timing — the Games contract in `LEARNING-REWARDS.md` §Games
  contract), and first-correct answers inside games still earn discovery
  under the Learn sub-cap; the game-completion award is on top, bounded at 2
  games/day. Lost duels with ≥60% accuracy still qualify — the award pays
  honest participation, not victory, so there is no incentive to farm weak
  opponents.
- Review *items* pay nothing per question — the once-per-canonical discovery
  claim stays intact; only completing the scheduled session pays.
- Mastery milestones are bounded by taxonomy size: finite, auditable
  total supply.

**Contribute pillar** (the owner's "contribution system granting points and
XP"): the machinery already exists — `contribution_credit` rows mirror into
the ledger as `kind='contribution'` — so v2 only fixes the amounts and the
cap treatment:

| Event | Award | Bound |
| --- | --- | --- |
| Published bank contribution (independently reviewed, live-verified) | 20 XP + 5 pts | max 3 credited/day |
| High-impact published contribution (answer-key/source fix passing the two-review quorum) | 40 XP + 10 pts | within the same 3/day |
| Content Studio first independently-reviewed publication (v1, unchanged) | 20 XP + 5 pts | once/day (migration 0035 rule) |

Contribution awards are **exempt from the 25-pt daily cap**: the rate limiter
is independent human review, not a counter, and reviewed corrections to the
bank are worth more than any study grind. Reversals keep appending negative
credit exactly as today. Votes, posting volume and self-publication still
earn nothing (DECISIONS #17).

Anti-abuse: review sessions are server-composed (the client cannot pick its
own 8 easy repeats), server-scored, with a server-measured minimum response
latency (e.g. ≥3s/item) gating session and game awards — a deterrent
heuristic, not a proof, same stance as v1's caps.

### 5.2 Quest rings rewired to the loop

Keep three rings and the existing claim mechanics, repoint them:

1. **Warm-up** — 10 scored attempts or 1 game (as today).
2. **Review ring** — clear 8 due review items (replaces cross_stream_triad).
3. **Plan ring** — complete today's plan (replaces mastery_closure).

Quest keys are data in `daily_quest_claims`; old claims remain historical.

### 5.3 One streak

`reward_profiles.current_streak_days` becomes the single authority. A day
qualifies on ≥1 eligible scored attempt (any context) or a completed review
session. `/api/me/progress` reads it for accounts; the attempt-derived
computation remains only for guests, labeled "device activity", since guests
have no reward profile. Shields unchanged.

### 5.4 Spending — owner-calibrated economy (decided 15 November 2026)

The owner fixed the targets: **the paid plan is ₹100/month**, and one month
of Pro should be earnable in **about 2 months of daily use or about 3 months
of average use**.

Those two targets imply a heavy:average earning ratio of 1.5, but under
uncapped v2 rules a maxed-out day (~44 pts: 30 discovery + 4 sessions + 10
quests) is nearly 3× a typical day (~15 pts). The calibration therefore needs
one new lever: a **daily reward-points cap of 25 points** (IST day, points
only — the 300 XP/day cap is unchanged, so leaderboards and levels are
unaffected; once the points cap is reached, awards still pay their XP).

| Quantity | Value | Check |
| --- | --- | --- |
| **pro-month** catalog offer | **1500 pts → 30 Pro days** | primary redemption |
| Daily use (hits the 25-pt cap) | 25 pts/day | 1500 / 25 = **60 days ≈ 2 months** ✓ |
| Average use (~12 new correct questions + 1 review session + warm-up quest) | ~16–17 pts/day | 1500 / 16.7 = **90 days ≈ 3 months** ✓ |
| **pro-week** offer | **400 pts → 7 Pro days** | repriced from the provisional 1000; ~proportional to pro-month |
| Streak shield | 25 pts (unchanged) | one full day's earnings |
| Implied point value | ~15 pts ≈ ₹1 | 1500 pts ≈ the ₹100 monthly plan |

Notes:

- The ₹100/month price itself is billing configuration (Razorpay plan +
  pricing copy), outside the reward schema; recorded here so the economy and
  the price stay calibrated together. **As of 16 November 2026 that price is
  real**: live Razorpay plans exist at ₹100/month (checkout still disabled
  pending launch), new checkout is monthly-only (six-month/yearly retired),
  and the owner can set **₹50/month** on selected accounts
  (`billing_account_rates`, 0089). The ₹50 discount does **not** change this
  calibration: points redeem into *days of Pro*, not rupees, so the catalog
  prices (1500/400 pts) and the daily cap stay anchored to the standard
  ₹100 plan. The "implied point value" row below is a sanity check against
  the standard price only; a discounted account simply gets a better deal
  either way, which is the point of the discount.
- Free-plan limits (50 practice answers/day, 1 mock/calendar month, 20
  mistakes/day) do not block the earning spread: the 25-pt cap is reachable
  without a mock (12 Learn + 4 Revise + 4 Play + 1 Daily Five + 10 quests
  ≥ 25), and 12 first-correct answers fit well inside the 50-answer limit.
  This matters because the earn-your-way-to-Pro story (§5.4's whole premise)
  must work for the learner who hasn't paid yet. The 1-mock/month limit does
  mean the Prove sub-cap is effectively Pro-only on a daily basis — accepted:
  mocks are a Pro perk, and the cap math never required them.
- The existing 1-redemption/account/30-days rule stays for Pro offers. With
  the 25-pt cap, pro-month takes ≥60 days to afford, so the rule is never the
  binding constraint; it remains as a backstop. Shields and future small
  items get per-item limits instead.
- Subsidy check: the most engaged learners effectively earn ≤₹50/month of
  access value — sustainable next to the ₹100 plan, and earned access starts
  only after existing paid/trial periods, as v1 already enforces.

**The free month (owner question, 16 November 2026 — delegated and
decided).** The owner asked whether a user should "claim 1 month free
after long use or points", and whether upvotes or content should earn
points, delegating the fair-and-unabusable design. Decision: **the points
wallet is the loyalty program — one path, no second one.**

- *"Long use" does not get its own grant.* Account age is the single
  cheapest thing to farm (register, park, wait); points already measure
  the only "long use" that matters — verified study over time — and the
  §5.4 calibration already delivers exactly the owner's wish: a diligent
  learner claims a free month (pro-month, 1500 pts) after ~2 months, an
  average one after ~3. A tenure grant beside it would double-pay the
  same loyalty and create the farmable copy.
- *Upvotes never earn points* — Part II §4.2 stands, and this question is
  why it exists: votes are the one signal users can manufacture socially
  (rings, trading), and pricing them turns every moderation case into an
  economy dispute. What upvotes DO buy is the trust ladder → Mentor tier
  → invitation into contribution work — which is where social effort
  legitimately reaches the wallet, behind an independent human review.
- *Content earns points only through that reviewed contribution pipeline*
  (§5.1 Contribute: 20 XP + 5 pts, high-impact 40 + 10, ≤3 credited/day,
  reviewer-gated, outside the daily cap). The rate limiter is a person
  checking the work, not a counter — unabusable by construction, because
  the abuse would have to get past a human reviewer with an audit trail.
- *Make it legible*: the Rewards screen gains a **"Your free month"
  meter** — points toward 1500, e.g. "62% earned" — so the existing
  redemption *feels* like the claimable free month the owner wants. A
  meter, not a countdown; no guilt mechanics (§0.6). This is the only UI
  change the decision needs.

Why this can't be abused, in one list: awards need server-scored correct
answers on verified-key questions; each question pays once per lifetime;
25 pts/day hard cap; sub-caps force mixing pillars; contributions pass
human review; votes mint nothing; tenure mints nothing. Every farming
strategy left is just… studying.

### 5.5 Admin access grants — ✅ IMPLEMENTED 16 November 2026

Shipped as migration **`0089_owner_billing_access`** plus
`api/app/routers/billing.py` admin endpoints and the owner panel at
**Admin → Rewards & accounts → "Monthly price & extra Pro days"**
(see `ACCOUNTS-BILLING.md` §Owner prices and `RAZORPAY-SETUP-20261116.md`
for evidence; 27 billing/access/rewards tests green, full prod-dump
migration rehearsal passed). As built:

- Table is **`billing_access_grants`** (not the proposed `access_grants`):
  `(id, user_id, granted_by, idempotency_key, days, starts_at, ends_at,
  created_at)`, days bounded **1–3650**, `UNIQUE(user_id,
  idempotency_key)`, and an immutability trigger (`review_immutable()`) —
  no UPDATE/DELETE ever. Repeated grant requests replay via the operation
  key instead of double-granting.
- A grant **stacks after `max(ends_at)` of all existing access** (trial,
  paid, reward redemption, prior grants), never touches Razorpay,
  `users.plan_*` or renewal dates, and is read through the extended
  `account_has_pro()` (paid ∪ redemptions ∪ grants — the union IV.3
  proposed is now the deployed function).
- Writes keep owner + CSRF + staff-MFA checks and record actor-bound audit
  events. The proposed free-text *reason* field and 7-day one-click preset
  were not built; the audit trail carries attribution. Revocation has no
  surface yet — if ever needed it must append, never delete (the trigger
  enforces this).
- **Grants confer access only — never XP or points** (held, as designed).
  Points adjustments remain the ledger `kind='adjustment'` path.
- Billing UI shows granted access as its own `granted` status, separate
  from paid and rewarded, and lists active grant windows.

Shipped alongside it, *not in the original draft*: **per-account pricing**
— `billing_account_rates(user_id, amount_paise CHECK IN (5000,10000))`
lets the owner set ₹50/month on selected registered accounts (standard
₹100 otherwise; anonymous visitors always see ₹100). Prices apply to the
*next new* subscription; existing mandates keep their agreed rate, and no
checkout parameter can select the discount. Provider plan references are
versioned by price and immutable (the old ₹99 reference is retired but
preserved).

**Planned extension — bulk ₹50 assignment (owner request 16 November
2026, design only).** The owner wants to grant ₹50/month to *known
people* in bulk — "all the mobile numbers from a WhatsApp group" — not
one email lookup at a time. Reality check first: **accounts have no
phone number anywhere in the schema** (verified — email + Google identity
only), so phone matching cannot work today and must not be faked. Two
mechanisms that do work, both writing the same `billing_account_rates`
rows the shipped tool writes:

1. **Email allowlist** — owner pastes a list of emails into Admin →
   Rewards & accounts; table
   `billing_rate_allowlist(email_normalized PK, amount_paise, added_by,
   note, created_at, applied_user_id NULL, applied_at NULL)`. Matching is
   applied immediately for existing accounts and **at signup/first-login**
   for future ones (the WhatsApp friend who hasn't registered yet — the
   actual bulk case). Owner-only visibility; one note per batch ("Group
   XYZ"); removing an entry stops future application but never silently
   revokes an applied rate (restore ₹100 per account, as today, with
   audit).
2. **Group claim code** — for when the owner has a WhatsApp group but not
   its members' emails: a code/link posted into the group;
   `billing_rate_codes(code PK, amount_paise, max_uses, uses, expires_at,
   created_by, revoked_at NULL)` + a redemption row per account. A
   signed-in account redeeming it gets the ₹50 rate. Leak containment,
   since anything posted in a group travels: max uses, expiry, one
   redemption per account, owner revocation, full audit of who redeemed —
   and the blast radius is inherently small (a discount on the *next*
   subscription, never free access, never points).

Phone-number matching is **deferred until accounts have a verified phone
field**, which needs SMS infrastructure this codebase doesn't have (the
same deliberate scope-cut recorded in the scholarship module). Both
mechanisms keep every shipped invariant: rates apply to the next new
subscription only, existing mandates untouched, no checkout parameter can
self-select a discount, owner + MFA + audit on every write.

### 5.6 Deliberately not building

- The mobile redesign's invented four-balance economy, or any coin/gem second
  currency. (Points-priced cosmetics are fine and designed in §12.8 — the
  ban is on a *second* currency, not on cosmetic spending.)
- Badges/achievement walls — levels, titles, leagues and mastery tiers are
  enough signal; revisit only with evidence of demand.
- Difficulty-based pay multipliers — flat rates keep the economy auditable
  and respect the retired-labels decision.
- Any reward for votes, posting volume, desk activity, or self-reported
  completion (existing policy, restated).

## 6. Schema sketch (future migration 0090+, not written yet)

(Originally "0084+"; 0084–0089 have since been used by stats, the four
current-affairs migrations and owner billing. Next free number: 0090.)

- `user_topic_mastery(user_id, subject_id, topic, state, distinct_attempted,
  distinct_correct_latest, last_verified_activity_at, proficient_at,
  mastered_at, updated_at)` — PK `(user_id, subject_id, topic)`.
- `review_items(user_id, canonical_id, box, due_on, last_result,
  last_attempt_id, updated_at)` — PK `(user_id, canonical_id)`, partial index
  `WHERE due_on <= current IST date`.
- Review sessions reuse `practice_study_sessions` with a session kind and a
  frozen served-item list (same snapshot discipline as mocks).
- No changes to `reward_ledger` shape; new awards are rows with namespaced
  event keys. Rehearse on a disposable dump clone per CLAUDE.md; never edit
  applied migrations.

## 7. API surface

- `GET /api/me/mastery` — rollup per subject/topic.
- `GET /api/me/review-queue` — due counts; `POST /api/review-sessions` —
  compose a Smart Review (answers flow through the existing study-session
  answer endpoint).
- `GET /api/me/today` — the composed plan.
- `/api/rewards/me` gains the rewired quest definitions (shape unchanged).
- **Mobile trap:** every new learner-facing GET must be deliberately added to
  the `MobileBoundary` allowlist in `mobile_identity.py`, with the companion
  tests extended — widening is an owner-visible decision, not a side effect.

## 8. UI in the Finna language

The Finna Web reference already contains the vocabulary this design fills:
a plan column on Home, quest rings with a "Claim +XP" widget, and streak
stats. Concretely:

- **Home plan column**: the Today card (§4.3).
- **Exam progress / Profile**: a mastery grid per subject → topic replacing
  raw accuracy tables; rusty shown as an overlay, never as lost progress.
- **Rewards screen**: no structural change — session and milestone awards
  appear in the existing history/breakdown automatically via the ledger.
- Prototype markup over README, per `DESIGN-FIDELITY.md`, when porting the
  not-yet-ported Profile/Rewards reference layouts.

## 9. New feature slate (owner request, 15 November 2026)

Net-new learner-facing features that plug into the loop and the spread
economy. Each line names what it reuses — nothing here needs a new economy
mechanism beyond §5. Ordered by suggested build priority:

1. **Smart Review + Today card** (§4.2–4.3) — the core loop surfaces; reuses
   `practice_study_sessions`, mistakes data, quest claims.
2. **Mastery map** — subject → topic mastery grid on Exam progress and
   Profile (§8), from the `user_topic_mastery` rollup; rusty overlay; honest
   empty states.
3. ~~**Admin access grants** (§5.5)~~ — ✅ shipped 16 November 2026
   (migration 0089); see §5.5 for as-built details.
4. **Current-affairs daily quiz** — a dated 5-question quiz, freshness-gated
   by review state; pays through the normal Play sub-cap like Daily Five.
   Falls back to an honest "no checked items today" empty state.
   *Updated 16 November 2026*: current affairs is now two subsystems — the
   editorial tables (0064/0065) **and** the new feed/briefs pipeline
   (0085–0088: YouTube MCQ drafting, free RSS sources, runtime grants,
   briefs; design in `Currentaffairs.md`). The quiz must draw only from
   **reviewed/published** items in either source — AI-drafted MCQs from the
   YouTube pipeline never reach learners (or this quiz) without review, the
   same discipline that keeps them out of the bank.
5. **Cup seasons (league nights)** — a scheduled weekly cup per stream
   cohort using the existing cup mode and boards; seasonal titles only, no
   extra points beyond the §5.1 game award. Resets use IST weeks like
   leagues.
6. **Shared-test challenges** — shareable tests (0079) gain a per-test
   score board among people with the link; XP/points flow only through
   existing discovery rules (a shared test is practice), so there is nothing
   new to farm.
7. **Printable revision sheet** — an **export button inside `/revise`**
   (§0.12; not a standalone feature): a learner's due reviews / mistakes
   with explanations as a PDF (PDF library plumbing from 0077); study aid,
   no economy surface.
*De-duplicated 16 November 2026 — three former items removed:*
*vocabulary-in-the-review-loop* and *desk shared goals* were word-for-word
duplicates of Part II §2.3 and §1.4 and now live only there (one spec per
feature, or the two copies drift); *mastery certificates* were cut
entirely — a shareable "mastered" image is a badge by another name, which
§5.6 already declines, and the mastery map plus levels/titles carry the
same signal.

Explicitly deferred: anything requiring new moderation surface (public
tournaments with chat), cross-user point interactions, or mobile-first
builds (the `MobileBoundary` allowlist keeps mobile read-only on these until
widened deliberately).

Four further subsystems — the Study Desk upgrade, the vocabulary learner,
the feed & post system, and the helpful-vote model with its ranking
algorithm — are designed in the companion document
Part II of this file. None of them touch
the reward ledger; the no-points-for-social-activity policy holds
throughout.

## 10. Rollout phases

1. **Learn first, pay nothing new**: mastery rollup + review scheduler +
   Smart Review + Today card, with zero new award rows. Lets thresholds be
   tuned on real usage without minting anything.
2. **Habit**: unified streak, quest rewiring, review-session awards.
3. **Economy**: the §5.1 spread (sub-caps, game/mock awards, contribution
   amounts), the 25-pt daily cap, mastery milestones, catalog repricing
   (pro-month 1500 / pro-week 400) and enablement. (The admin grant tool
   originally slotted here shipped early — §5.5, 16 November 2026.)
4. **Feature slate**: §9 items in priority order, each shippable
   independently.

Each phase: new numbered migration rehearsed on a dump clone, isolated
PostgreSQL tests alongside the existing reward suite, local build, deploy via
`scripts/deploy.sh`, DEVLOG receipt.

## 11. Owner decisions

Decided 15 November 2026 (recorded in §5.1 and §5.4–5.5):

- Paid plan ₹100/month; pro-month redeemable at 1500 pts (≈2 months daily /
  ≈3 months average use); pro-week repriced to 400 pts; daily points cap 25.
- Points spread across pillars via per-source sub-caps; contributions pay
  points+XP (20/5, high-impact 40/10) outside the daily cap, reviewer-gated.
- Admin tool to grant arbitrary Pro days with a 7-day reward preset.

Decided/landed 16 November 2026:

- ₹100/month standard price confirmed and live-configured (checkout still
  disabled pending launch); new checkout monthly-only; ₹50/month assignable
  to selected accounts by the owner (`billing_account_rates`).
- §5.5 admin grants shipped as `billing_access_grants` (0089) — access
  only, never XP/points, exactly as designed.
- Focus subjects, the leaderboard decision, game boards and the Home
  layout: §12 addendum below.
- The free month: points are the single loyalty path (no tenure grant),
  upvotes never pay, content pays only via reviewed contributions; a
  "Your free month" meter on Rewards makes it legible (§5.4, owner-
  delegated 16 November).

**All remaining opens resolved 16 November 2026** — the owner said
"decide all for me"; the decisions below are assistant-made under that
delegation, recorded as initial constants (versioned, tunable only with
real usage evidence, every change a reviewed diff):

1. **Mastery thresholds**: the §4.1 table is adopted as written —
   5/10/20 distinct questions; 70% / 85% latest-attempt accuracy; the
   14-day proficient→mastered review gap; **45-day rusty window**. They
   are deliberately conservative: a too-easy "mastered" is a lie to the
   learner, a too-hard one is just slower — err slow.
2. **Game award threshold ≥60% stands**, and the contribution bound stays
   **3 credited/day** (the reviewer is the real limiter anyway).
3. **District dimension stays Daily-Five-only.** A district mastery or
   league view is population-gated exactly like exam cohorts (§0.11.3):
   build it when a real district cohort exists, not before.
4. **Catalog goes live when two things are true**: Phase D's
   reward-diagnostics reconciliation passes on a seeded week, **and**
   paid checkout has launched. Earned Pro must not predate purchasable
   Pro — the subsidy math (§5.4) should be real from the first
   redemption. *(Amended 16 Nov, §13.1: checkout itself now has two
   prerequisites — legal pages (terms/privacy/refund) published, and
   working email password recovery. The full flip checklist renders in
   the VI feature-gates panel.)*
5. **Claim codes**: default **100 max uses, 30-day expiry** (both
   editable per code). Allowlist applications at signup are **not**
   individually notified — they appear in the admin audit list for a
   weekly glance; the blast radius (a discount on a future subscription)
   doesn't warrant interrupting anyone, and there's no email infra yet
   anyway.
6. **§13: all six approved, in listed order**, each gated by its
   dependency — the email provider (#1) before the digest (#4) and
   before referral notifications. **Referral bounds**: 7 Pro days each
   side; the referred account must reach 10 scored attempts; ≤5 credited
   referrals per referrer per rolling year; launches only after paid
   checkout is live.

## 12. Addendum (16 November 2026): focus subjects, leaderboards, Home

Owner request: personal growth and a revision/study plan scoped to **the
subjects a learner actually cares about** ("everyone will not be interested
in every subject"), plus concrete decisions on the leaderboard, game
boards and the optimized Home layout. The spaced-repetition system itself
is already §4.2 and the feed/upvote ranking is already Part II §4 —
nothing there changes; this section personalizes what feeds them and
decides the display surfaces.

### 12.1 Focus subjects (choice-driven study plan)

Focus subjects sit **inside the primary-exam lens** (§0.11): the exam
decides the universe, focus subjects narrow it. A learner picks up to
**5 focus subjects** (from their primary exam's scope
by default; editable on Profile and inline on the Today card). Stored as
`user_focus_subjects(user_id, subject_id, created_at)` — PK pair, no
other state. Effects, all read-time:

- **Today's new-question target** (§4.3 item 2) draws from the weakest
  practicing/proficient topics *within focus subjects only*. With no
  focus set, it falls back to the saved exam's whole scope (today's
  behavior); with no saved exam either, honest empty state.
- **Mastery map** orders focus subjects first and defaults the Profile
  strip to them; everything else remains visible below — focus is a lens,
  never a filter that hides earned progress.
- **Review queue honesty rule**: spaced repetition reviews what you got
  *wrong*, not what you *like*. Due items from non-focus subjects stay in
  the queue and in the due count — forgetting curves don't care about
  interest. The concession to choice: Smart Review gains an optional
  "focus subjects only" toggle for a short session; the full queue is
  always one tap away and the Today due-count never lies by omission.
- **Weekly growth recap** (the "personal growth" surface — and the *only*
  weekly summary on the site; Desk's focus summary merged in here): a
  small card on Today each IST Monday — last week's XP, topics that
  advanced a mastery tier, reviews cleared, streak kept, focus time (from
  the server-timed desk focus sessions, when any) — computed from the
  ledger and rollups, never invented. Display only, no awards.

Economy: none. Focus changes *which* questions are suggested, never what
they pay — all §5.1 caps and claims are subject-agnostic, so flipping
focus subjects daily farms nothing.

### 12.2 The leaderboard decision

What the leaderboard shows (decided): **weekly XP inside a league cohort,
opt-in, handle + XP + rank only** — i.e. the existing league board stays
the one global board. What it must **never** show: accuracy, marks,
mastery tiers, wallet/points, or per-subject standings. Reasons: XP is
pure activity, safe to compare and already capped (300/day) so the board
has a fair ceiling; accuracy/marks boards shame struggling learners and
invite answer-farming; wallet is private economy; and per-subject boards
would fragment a small community into empty rooms. Weekly IST resets keep
it winnable by a newcomer; equal XP shares a rank (existing rule).

Presentation (new): show **top 10 + the viewer's neighborhood** (ranks
N−2…N+2 around you) instead of a top-100 wall — a mid-pack learner sees
beatable neighbors, not an unreachable summit. Opt-out accounts see their
own rank privately ("you'd be #23") without appearing to others
(unchanged privacy model).

### 12.3 Game leaderboards

Per-mode **weekly boards** (gauntlet, speed, duel wins, Daily Five streak)
from server-owned results only — same frozen-snapshot/server-scoring
contract as §5.1's Play awards, so there is nothing client-forgeable to
rank. Display: handle, mode score, rank; IST weeks; opt-in follows the
same flag as the XP board (one consent, all boards). Cup seasons (§9.5)
keep their own seasonal standings and titles. No new awards anywhere in
this — boards are display over results that already exist.

### 12.4 Home layout (optimized, decided)

Disambiguation (16 November): **"Home" is the `/feed` route** — the site
root redirects there since 16 November (`FINNA-REDESIGN-20261114.md`),
and the deployed redesign gives it a three-column contract (exam/plan/
progress · study/community stream · activity/saved). This section does
not invent a second Home; it assigns the priority list below **onto that
contract**: items 1–4 fill the left column top-down, the stream *is* item
6 (so "feed teaser" means the center column, not a duplicate widget), and
items 5 + 7 live in the right column. On phones the columns collapse into
the single priority-ordered list.

Signed-in Home, in priority order (one column on phones, Today pinned
first on desktop):

1. **Today card** (§4.3) — due reviews (one-tap Smart Review), the
   focus-subject question target, Daily Five, quest rings.
2. **Continue strip** — open mock / unfinished practice session resume
   (the existing ExamJourney resume data).
3. **Streak + level chip** — small header stat, not a panel; no guilt
   modals (§0.6).
4. **Mastery snapshot** — focus subjects first (§12.1), linking to the
   full map.
5. **Leaderboard teaser** — your league rank + two neighbors (§12.2),
   small, opt-in; hidden entirely when opted out.
6. **Feed teaser** — 3 For-you posts (Part II §4.3) incl. the
   "help someone" slot; links into the community tab.
7. **Weekly growth recap** — Mondays only (§12.1).

Browse (search, exams, papers) stays in the global nav above all of this —
Home must never bury the library (§0.1: browse wins). Signed-out Home is
unchanged by this addendum: library first, device-local progress, no fake
panels — a static one-line explainer of what Today becomes with an
account is the only advertisement.

Schema/API deltas this addendum adds to §6–7: `user_focus_subjects`,
`PATCH /api/me/focus-subjects`, the recap read (derivable from existing
tables; materialize only if measured slow), and board queries over
existing results. Mobile: all reads go through the deliberate
`MobileBoundary` widening rule (§7), as ever.

### 12.5 Phone optimization (web, 16 November 2026)

Context: the Finna redesign already ships a five-tab phone bar — **Home /
Exams / Library / Desk / Me** — with narrow geometry verified at 390px and
320px (`FINNA-REDESIGN-20261114.md` + its coverage audit). The new
surfaces slot into those five tabs; **no sixth tab, no new navigation
pattern**. Decisions:

- **One request, not one layout trick, is the real phone optimization.**
  `GET /api/me/today` returns the *entire* composed Today card (due count,
  focus target, Daily Five state, quest rings) in a single round trip —
  the phone Home renders from one GET, not four. Personal reads stay
  `private, no-store` (IV.2), so the speed comes from server-side
  composition, never client caching.
- **Home (phone)**: the §12.4 column order, single column; the Today card
  must fit above the fold at 390px with the due-review CTA as the primary
  thumb target. Leaderboard teaser collapses to one row (your rank + next
  neighbor); feed teaser lazy-loads below the fold; growth recap collapses
  to a tappable summary line on Mondays.
- **Smart Review (phone)**: full-screen one-question-at-a-time player —
  the existing practice player pattern, not a new component. Inline
  answering keeps `QuestionCard` (the owner-decided deviation from the
  reference's compact rows applies here too).
- **Mastery map (phone)**: subject accordion → topic chips; the dense
  desktop grid never renders under ~480px. Rusty is an icon overlay with
  the state in the accessible name (same honesty, less width).
- **Focus-subject picker (phone)**: bottom sheet from the Today card;
  inline checklist on desktop Profile. Same `PATCH`, same 5-subject cap.
- **Leaderboards (phone)**: neighborhood view (§12.2) is the default and
  the top-10 sits behind a toggle — the viewer's own context is the useful
  pixel at 390px. Game boards live where games live; XP board under Me.
  Counts over 99 use the established 99+ badge with the real number in
  the accessible name.
- **320px rule**: every new card is single-column, no horizontal scroll,
  no hover-only affordances. Loading/empty/error states are explicit —
  honest empty states are a phone feature too (a blank panel on a slow
  connection reads as a crash).

### 12.6 Mobile app (Expo) widening for these features

The IV.8 contract (allowlist diff + companion test + capability flag per
feature) applied to this addendum, in order:

1. **Reads first**: `/me/today`, `/me/mastery`, `/me/review-queue`,
   `/me/focus-subjects` GET, leaderboard/game-board GETs — display-only,
   no economy writes, safest possible widening.
2. **Then the practice writes**: review-session compose + the existing
   idempotent answer endpoint (offline attempts replay through it,
   IV.8.3). This is the point where the app earns like the web does —
   same server-side awards, nothing app-specific to audit.
3. **Focus-subject PATCH** ships with step 2 (first mobile write beyond
   attempts; trivial, but it is still a deliberate allowlist line).
4. Community/feed reads later; community **writes stay web-only** until
   moderation tooling is proven (unchanged IV.8 stance).

Each step: one allowlist diff, one `test_mobile_companion.py` extension,
one capability-list entry so old app builds degrade gracefully.

**Scope rule (§0.12.2, binding):** the app never chases screen parity
with the phone web. Every widening above must earn its place with
something native — offline practice and queued replay first, push later —
or it doesn't happen. "The web has it" is not a reason; it's the
beginning of maintaining every screen twice.

### 12.7 Profile tools (16 November 2026)

The Profile ("Me") tab becomes the one place for *account self-service* —
§0.12 applied to the self. One screen, four groups, almost all of it
already existing and merely gathered:

1. **Identity**: avatar (the existing editor), handle, leaderboard
   opt-in/out, creator-profile link when one exists.
2. **Study setup**: primary/saved exams (§0.11.1), focus subjects
   (§12.1), exam date for the taper (§13 #6) — the three personalization
   levers, side by side, each one tap from what it controls.
3. **Privacy & security**: MFA (0033), active sessions list with revoke,
   desk progress-sharing opt-in, blocked users. Plus **export my data**
   (a JSON of the account's own attempts/progress/posts — cheap honesty,
   reads only owned rows) and **delete my account** (existing account
   boundaries; entitlements end, immutable community/audit history is
   anonymized, not rewritten — the same append-only principle as
   everywhere).
4. **Wallet shortcut**: the Rewards screen link with the free-month
   meter peeking through (the meter itself stays on Rewards — §0.6).

Nothing here invents a subsystem; the section exists so these stop being
scattered across settings pages. Builds in V.5 alongside the boards.

### 12.8 Profile edit & the cosmetics system (owner request, 16 Nov 2026)

Baseline, verified in `AVATAR-EDITOR.md` + migration 0041 (live since
2026-10-23): the v3 avatar editor at `/avatar` — seven categories, 19
free starters, 7 level-reward unlocks, durable ownership in
`user_avatar_items` that survives XP reversals, append-only
`avatar_events`, `avatar_catalog.json` as the single catalog authority,
server-side catalog-only validation, and a deliberate launch cut: **no
coin shop, no paid cosmetics**. This section designs that deferred layer.

**A. Profile edit.** Handle: unique, renameable **once per 30 days**
(impersonation-churn guard), rename recorded as an account event. Short
bio: 140 chars, text-only, reportable, `needs_approval` honored like any
post. Both edit from the §12.7 identity group; avatar editing stays in
the existing editor.

**B. The points shop.** Points are the **only** purchase currency —
§5.6 bans a second cosmetic currency and §7.3 bans cash microtransactions,
so the sanctioned path is: catalog items gain an optional `price_points`
(bands: common 15–30, distinctive 50–75, showpiece frames 100–150). A
purchase is one transaction: a namespaced ledger spend row
(`cosmetic:{user}:{item}`, per-user lock, idempotent, own-once) +
`user_avatar_items` insert + `avatar_events` append — **zero new
tables**. Owned is owned forever: survives downgrades, XP reversals, and
rank is never affected (existing rules extend). The free-month meter
shows the real balance, so buying a hat visibly sets the meter back —
an honest, voluntary tradeoff, and a healthy points sink (currency
leaves circulation without costing access subsidy).

**C. The acquisition map** (complete; a path not listed doesn't exist):
free starters (live) · level unlocks (live) · points shop (B) ·
**earned-only prestige** — mastery-tier, league and cup-season items
that can *never* be purchased and have no purchasable lookalike, so an
earned frame stays meaningful. Decided against: **Pro-exclusive
cosmetics** — Pro buys capacity, never identity (§7.3); a payment-status
skin on leaderboards is soft pay-to-signal.

**D. Hard rules** (the lines that keep this clean): no loot boxes or
randomized purchases, ever — gambling-adjacent mechanics have no place
in front of students; no FOMO scarcity — seasonal items are earned
in-season and return in later seasons; no trading or gifting (the
no-transfers rule); no user-uploaded art (moderation surface — the
curated catalog is the whole inventory); cosmetics never affect
gameplay, ranking, visibility or trust signals (tier flair stays
visually distinct from decoration).

**E. The addition system** (how new cosmetics enter): admin-curated
only, through an **Admin → Cosmetics** console following the
reward-catalog pattern — list, add/retire item (category, asset
reference, `price_points` or unlock rule, active flag), optimistic
version + reason + audit + MFA. Honest coupling note: item *data* is
instant (catalog JSON), but new *art* is SVG geometry in the renderer,
so genuinely new shapes ship with a frontend release — the console
validates that an asset reference exists before an item can activate.
Existing catalog values stay compatible (the 0041 doc's standing rule).

**F. Build**: display/profile-edit pieces with V.5; the shop needs V.4's
economy live first (spending requires the cap/ledger rewrite to be
settled). Admin console rides V.12 with the rest of Part VI.

## 13. Proposed improvements (assistant suggestions, 16 November 2026)

Requested by the owner ("any new features or functions you want to add").
**None of these is decided** — each needs an explicit owner yes. Every one
is economy-safe by construction (access or display, never minted points)
and ordered by expected value per effort:

1. **Email delivery provider** — the highest-leverage unbuilt thing on
   the whole list, and it isn't a feature: `ACCOUNTS-BILLING.md` records
   that signup works but email verification and self-service password
   recovery don't exist. Everything below that touches email (digests,
   allowlist trust, referral notifications) stands on this, and losing a
   password today costs a support thread.
2. **Referral Pro-days** — "invite a friend; when they register and make
   their first 10 scored attempts, you both get 7 days of Pro" — paid as
   `billing_access_grants` rows (access only, never XP/points — the §5.5
   invariant), bounded (e.g. ≤5 credited referrals/account/year,
   owner-tunable), attempt-gated so dead signups pay nothing. Fits the
   WhatsApp-group growth reality this site actually lives in.
3. **WhatsApp share cards** — a share link for any question or shareable
   test (0079) with a proper OG preview (question text, exam/year badge,
   site name). Pure growth surface for the same reality: prep groups
   forward questions all day; today a forwarded link renders as a bare
   URL. No economy surface at all.
4. **Due-review digest (opt-in)** — one email per day at most, IST
   evening: due-review count, streak status, one-tap Smart Review link.
   Strictly opt-in, one-click unsubscribe, silent when the queue is
   empty (honest empty states apply to inboxes too). Depends on #1.
5. **Onboarding diagnostic** — on choosing a primary exam (§0.11.1), an
   optional 10-question mixed quiz from its verified pool seeds initial
   mastery estimates and suggests focus subjects (§12.1). Pays normal
   discovery rules — it *is* practice, nothing special to farm — and
   turns the cold-start Today card into a useful one on day one.
6. **Exam-day countdown + plan taper** — the learner sets their exam
   date (the calendar, 0042, is the single source of official dates;
   the Desk calendar, Part II §1.8, reads the same source); Today
   gradually shifts composition from new questions toward due reviews
   and mocks in the final weeks. Display/composition logic only; no new
   awards.

*(A "question of the day" proposal was cut in the 16 November
de-duplication pass: it was Daily Five with a third coat of paint — the
site would have had three daily-question features. The useful fragment
survives as a share-card variant of #3: Daily Five's first question can
render as a public shareable card.)*

Deliberately **not** proposed: cash referral bonuses, point gifts,
social-share rewards, or any mechanism where growth actions mint
currency — all of it would reopen the farming surface §5 closed.

### 13.1 Second sweep — what the plan was still missing (owner asked, 16 Nov)

Genuine gaps found on a final pass; none is a feature, all are
launch-critical or strategy-critical:

7. **Legal pages before checkout — a hard gate.** Terms of service,
   privacy policy, and a refund/cancellation policy page. Razorpay
   expects them, Indian consumer-protection rules expect them, and the
   plan currently schedules paid launch with none written. Add to the
   §11 resolution-4 checklist: **checkout does not flip without them.**
   (Also verify GST/invoicing obligations for the ₹100 subscription with
   the provider's documentation — flagged for the owner to confirm, not
   decided here.)
8. **Email provider before checkout, not just before the digest.** A
   paying customer with an unrecoverable password is a refund dispute
   waiting to happen. §13 #1 gains a second gate: **live checkout waits
   for working password recovery.**
9. **SEO is the missing growth engine.** The whole thesis is browse-first
   public content, yet the web app is a client-rendered SPA — search
   engines see an empty shell, while every bank question *is* a search
   query someone types before an exam. Add to T2: prerender/SSG for
   public question, paper and exam pages (the same anonymous-cacheable
   tier V.1 builds), plus sitemaps and structured data. Likely the
   highest-leverage growth work in the entire document.
10. **Honest measurement for §0.8.** The success metrics have no
    measurement plan. One tiny self-hosted events table (page views +
    the §0.8 events, no third-party SDKs — consistent with IV.8.4's
    stance) so "papers browsed per session" is a real number, not a
    feeling. Private by design: counts, not profiles.
11. **A support surface.** `/help`: FAQ, contact email, and the
    documented support-assisted password recovery (until #8 lands).
    Costs an afternoon; its absence costs trust at the first confused
    paying user.
12. **An accessibility pass** on the new surfaces (composer, calendar,
    review player): keyboard paths, focus management, accessible names
    on icon buttons. Exam aspirants on cheap phones and screen readers
    exist; the redesign audit already notes gaps — schedule it with V.9
    rather than "later".
13. **Content licensing check per new exam body** (S2/S3): MPSC past
    papers' reuse stance is established practice here; each new body's
    stance gets verified *before* ingestion, recorded in the V.7
    checklist as step 0.
14. **Mizo-language UI** — noted as an open consideration, not a
    commitment: the audience is Mizoram-first and the UI is
    English-only. Revisit after launch metrics show where learners
    struggle; glosses (Part II §2) are the near-term answer.

Third and final sweep (16 Nov, before declaring the design saturated):

15. **Login throttling** — IV.11 covers currency and privilege threats
    but never names credential-stuffing: per-account + per-IP sign-in
    backoff and a lockout-with-recovery path (recovery needs #8's email
    anyway). One afternoon, standard pattern, belongs in V.2's phase.
16. **Renewal-failure comms** — when a Razorpay mandate charge fails,
    the webhook already records the state; the *user* currently learns
    nothing until access lapses. Once email exists: one honest "your
    renewal failed, here's what happens and when" message, and billing
    shows the real provider state. No dunning pressure campaigns — one
    notice, honest countdown.
17. **Community cold start** — launch day's feed is empty, and the rules
    (rightly) ban invented activity. The honest seeding strategy: the
    owner and early reviewers post real study notes under their own
    names, Daily Five and doubts-on-questions carry the early social
    load (they generate real content as a side effect of studying), and
    the feed tab stays visually secondary until it has something true to
    say. Patience is the feature.

**Declared saturated.** Anything further added to this document before
real users touch V.2 would be speculation stacking on speculation — the
next improvements must come from measured §0.8 numbers, support
questions, and what the first hundred learners actually do. The plan's
own discipline (honest data over invention) applies to the plan itself.

## 14. The Helper Calendar (owner request, 16 November 2026)

One calendar at `/calendar` — the single scheduling surface for the whole
site, replacing nothing but *unifying* what already exists (the exam
calendar 0042, its reminder worker, the Desk calendar reads) with what
Parts I and §12 create. It is composed of **toggleable layers over one
month/week grid**; every layer is honest data, and the calendar as a
whole **mints nothing and punishes nothing** — it schedules suggestions.

| Layer | Contents | Source |
| --- | --- | --- |
| **Official** | exam notifications, application windows, exam dates — dated reviewed entries only | exam calendar (0042), unchanged; reminders via its existing worker |
| **My exams** | the learner's own target exam date(s) with countdown; drives the §13.6 plan taper | learner-set, one tap from an official entry or manual |
| **Review forecast** | upcoming spaced-review load per day ("Sat: 32 due") projected from the Leitner queue — the learner sees a pile-up *before* it lands | `review_items.due_on`, no new schema; recomputes as they answer |
| **Progress tests** | a recurring self-test slot (weekly/fortnightly, learner-chosen weekday): a normal mock composed from their exam scope on that day | mock machinery unchanged; normal Prove award, nothing calendar-specific |
| **Personal** | the learner's own dated notes/goals ("finish Polity ch. 3") — private, plain text, CRUD | new `calendar_entries` |
| **Habit (past)** | streak heatmap of days with eligible activity — the look-back twin of the forecast | attempts/streak rollups, display only |
| **Community & play** | weekly cup night (§9.5), desk events (Part II §1.8 reads these same sources — one calendar store, two views) | existing schedules |

Rules and decisions (made under the standing "decide all for me"):

1. **Early review is allowed, honestly.** Tapping a future day's forecast
   lets the learner clear reviews early; the next interval is computed
   from the *actual* review date (standard Leitner behavior). The
   forecast is a projection, and the UI says so — it shifts as you work.
2. **A missed progress test reschedules silently.** No guilt banner, no
   streak damage, no penalty — §0.6 applies to calendars with special
   force, because exam aspirants already live under deadline dread. The
   slot simply moves to the next cadence day.
3. **Load-aware nudge**: when the forecast shows a heavy day coming,
   Today may *suggest* "clear 10 early?" — a suggestion row, never a
   requirement, never counted against the plan (same contract as Atlas
   drills).
4. **ICS feed export** (my addition — the highest-value helper here): a
   secret, revocable per-user feed URL (`calendar_feed_tokens`, token
   hashed at rest) so the whole thing lands in Google Calendar /
   phone calendars, which is where real reminder infrastructure already
   lives — no SMS/push build needed. The feed contains only that
   learner's own layers; revoking the token kills the URL.
5. **Email reminders ride the digest** (§13 #4), opt-in, once the email
   provider (#1) exists — the calendar never grows its own notification
   channel.
6. **Guests** see the Official layer only (it's public data); everything
   personal requires the account that owns it.

Schema sketch (with the 0090+ block): `calendar_entries(id, user_id,
date, title, note, kind CHECK ('personal','progress-test'), recurrence
NULL, created_at, updated_at)`; `calendar_feed_tokens(user_id,
token_hash, created_at, revoked_at NULL)`. The forecast, habit, official
and community layers need **no new tables** — they are reads over what
already exists, which is the test that the calendar is a lens and not a
new subsystem. Mobile: layer GETs in the first widening step (§12.6);
personal-entry writes ride the second. Build order: forecast + official
layers with V.2 (they're free once `review_items` exists); personal
entries, progress-test slots and ICS in V.5.

---

# Part II — Desk, vocabulary and community

Status: **proposal, nothing implemented**. Drafted 15 November 2026 as the
companion to Part I, covering four subsystems the
owner requested the same day: the Study Desk upgrade, a full vocabulary
learner, the feed & post system, and the likes/upvote model with its ranking
algorithm. The owner delegated the detailed decisions ("decide for me");
every choice below is therefore a concrete default, flagged where it is
reversible. Standing policies carried forward unchanged: **no social
activity ever earns XP or points** (DECISIONS #17: votes are discovery-only),
provenance and answer-reveal gates stay intact, honest empty states, opt-in
visibility everywhere.

## 1. Study Desk upgrade (Desk v4)

Baseline: Desk v3 (`STUDY-DESK.md`) — personal workspace plus six-seat
private rooms, invitations, chat, focus sessions, moderation, retention.
v4's theme: **the Desk becomes the home of the learning loop**, while
remaining non-economic.

1. **Toolbox, not a second home** (amended 16 November 2026 per §0.12).
   The original v4 draft rendered the Today card at the top of `/desk` —
   the same card in two homes, which is exactly the duplication §0.12
   exists to kill. The personal desk is now purely **your things**:
   notes, saved questions, the focus timer. The Today card lives on Home
   only; `/desk` links to it with one line, never re-renders it. The
   self-reported weekly answer target is **retired outright** — the
   Monday growth recap (§12.1) and quest rings already count the same
   thing honestly, and self-reporting violated the honest-counting rule
   anyway.
2. ~~**Mastery snapshot.**~~ Cut 16 November 2026 (§0.12): Home already
   carries the mastery snapshot (§12.4 item 4) — the same strip on the
   personal desk would be the Today-card duplication again, one item
   down. The desk links to the mastery map; it doesn't re-render it.
3. **Desk sessions.** A room can start a synchronized practice set over its
   shared/saved questions, reusing the existing party-mode game room
   machinery (frozen snapshots, server scoring). Economy: normal game rules
   apply — discovery and the Play sub-cap; nothing desk-specific pays.
4. **Shared weekly goal (display only).** One goal per room per IST week
   (e.g. "300 scored attempts together"), progress aggregated from members
   who already opted into sharing progress. A progress bar, not a currency:
   completing it awards nothing, by policy.
5. **Review circle.** Members can flag a question to the room ("discuss
   this") — extends the existing posted-mistakes mechanism; the room's
   shared-questions tab gains a "needs discussion" filter and resolved
   marks. Answer-reveal gates still apply per member.
6. **Focus v2.** Pomodoro presets on the existing server-timed focus
   sessions; an opt-in room focus board (display only, explicitly earns
   nothing — unchanged policy). *(The "private weekly focus summary"
   originally here was merged into the one weekly growth recap, Part I
   §12.1, in the 16 November de-duplication pass — two weekly summaries
   was one too many; the recap gains a focus-time line instead.)*
7. **Notes v2.** Notes attachable to a canonical question ID, linkable from
   room chat, exportable to PDF via the 0077 plumbing.
8. **Desk calendar — a view, never a store** (§0.12). The room shows a
   room-filtered view of the one Helper Calendar (§14): saved-exam
   countdowns and members' opt-in milestones. No desk-side calendar
   tables; entries created here are `calendar_entries` rows like any
   other.

Decided constraints: rooms stay private and six-seat; public/class desks
stay disabled; Pro still gates room creation (3/owner); everything ships
behind the existing `STUDY_DESKS_PRIVATE_ENABLED` flag; mobile gets GET-only
access unless the `MobileBoundary` allowlist is deliberately widened.

## 2. Vocabulary learner v2

Baseline: migration 0048 recognition drills that already write `attempts`.

1. **Decks.** Three sources, all reviewed before going live:
   - *Bank-derived English*: synonyms/antonyms/one-word-substitution/idiom
     questions already in the bank, grouped into decks by topic — these are
     canonical questions and keep their provenance.
   - *Curated word cards*: editor-authored cards (word, meaning, usage,
     Mizo gloss) published through the Content Studio review pipeline, never
     straight to live.
   - *Mizo↔English pairs* for the Mizo paper, same curated path.
2. **Modes.** Recognition (existing MCQ drill), delayed recall (re-asked
   days later via the scheduler), and usage cloze (pick the word that fits
   the sentence). All server-scored.
3. **One scheduler.** Vocab items enter the same Leitner `review_items`
   queue as questions, typed (`item_type='vocab'`). A "5 words a day" card
   appears on Today; due vocab can run as its own short session or mix into
   Smart Review.
4. **Progress.** Per-deck progress with the same mastery semantics
   (latest-attempt based, decay overlay), a words-known counter, and honest
   zero states.
5. **Economy (decided).** Bank-derived vocab questions pay discovery
   normally — they are verified canonical questions. **Curated cards pay no
   per-card points ever**: they are not canonical questions, have no
   official-key provenance, and would be the easiest thing on the site to
   farm. Vocab activity still counts toward quest rings and review-session
   completion awards (the Revise pillar), so daily vocab work is rewarded —
   at session granularity, not per card.

## 3. Feed & post system v2

Baseline, verified in `api/app/routers/community.py` + `discussions.py`:
question-anchored posts (`kind IN ('doubt','explanation')`) with replies,
accepted answers, helpful votes (`post_votes`), blocks, reports, idempotent
creation, `hidden`/`needs_approval`/`before_fix` moderation flags, pinning,
and the **disclosure gate** — discussion of a question is visible only after
the viewer has attempted or deliberately unlocked it (spoiler and
mock/game-integrity protection). The feed is chronological;
`following`/`mcqs`/`materials` tabs return `available=false`.

### 3.1 Post types (decided)

| Kind | Anchor | Notes |
| --- | --- | --- |
| `doubt` / `explanation` (existing) | canonical question | unchanged, disclosure-gated |
| **`study`** (new) | free-standing | short text post: progress note, tip, strategy; optional subject/topic tag; optional link to an internal entity |
| **`material-share`** (new) | Content Studio publication | a share card for an already-reviewed material |

Hard rules: text only (no image uploads in v1 — that is a moderation surface
we are not staffing); links may point **only to internal entities**
(questions, materials, papers, exams) — no external URLs (spam defense);
sample/invented activity never seeded.

### 3.2 Following

New `follows(user_id, followed_id, created_at)` (PK pair, no counts shown
beyond honest integers). The `following` tab becomes real: chronological
posts from followed authors, same visibility/block/disclosure filters as
everywhere. Follow is one-way, free, and earns nothing.

### 3.3 Posting guards (decided)

- Registered accounts only (guests read).
- New-account throttle: accounts younger than 3 days **or** with fewer than
  50 scored attempts may reply and vote, but not create `study` posts —
  doubts on questions they attempted are always allowed (that is core
  learning).
- Rate limits: 5 top-level posts/day, 30 replies/day (server-enforced,
  per-account).
- Reports feed the existing moderation admin; repeat-flagged authors drop
  into `needs_approval` for new posts.

### 3.4 Feed tabs

| Tab | Composition |
| --- | --- |
| For-you | ranked (§4), all visible kinds |
| Following | chronological, followed authors |
| Doubts | existing view (incl. unanswered filter) |
| Materials | the reviewed materials catalog, newest first |

## 4. Likes/upvotes and the ranking algorithm

### 4.1 Vote model (decided)

- Keep the single positive **"Helpful"** vote (existing `post_votes`
  toggle). **No downvotes**: a small exam-prep community under stress does
  not need a public punishment button; reports + moderation handle bad
  content, and accepted answers already mark quality on doubts.
- One vote per account per post; no self-votes; blocked-pair votes excluded
  (both already enforced or trivially kept).
- **Votes never mint currency** — they influence ranking and creator-profile
  stats only (standing policy).
- **Vote weight** (anti-brigading): a vote counts **1.0** from an account
  with ≥50 scored attempts, else **0.25**. Weight is computed at read time
  from the voter's attempt count — nothing stored, nothing to migrate, and
  farm accounts would have to actually study to gain influence.

### 4.2 What upvotes earn (decided, owner question 15 November 2026)

Never currency — and that is the design, not an omission. Helpful votes are
the one signal users can manufacture socially (sockpuppet rings, vote
trading); attaching XP or points to them would turn every moderation case
into an economy dispute and quietly break the calibrated ₹100/1500-point
targets in Part I §5.4. Instead, accumulated **lifetime weighted helpful
votes** (the §4.1 weights) buy standing and capability — a trust ladder:

| Lifetime weighted helpful | Tier | Unlocks |
| --- | --- | --- |
| 10 | **Helper** | new-account posting throttle lifted immediately (study posts before 3 days / 50 attempts) |
| 25 | **Regular** | rate limits raised to 10 posts / 60 replies per day; tier flair shown beside the name on posts |
| 50 | **Mentor** | Mentor flair; eligibility for reviewer/editorial invitations — the bridge into the contribution pipeline, which is where helpfulness starts earning real points (Part I §5.1, reviewer-gated) |
| 150 | **Guide** | featured in a weekly "most helpful" strip on the community tab (computed, dated, opt-out honored) |

Alongside the ladder, votes already buy **visibility** (the `W` term in the
ranking below) and **reputation**: profile and creator pages show lifetime
helpful count and accepted-answer count as raw integers.

Rules: tiers are computed at read time from `post_votes` joined against
voter attempt counts — no stored balances, nothing to migrate, nothing to
farm offline. Tiers only rise for display, but every privilege yields to
moderation: an author under `needs_approval` loses ladder privileges until
cleared. Accepted answers remain the strongest per-post signal (they rank
2× a vote and are counted separately on profiles). Thresholds are
owner-tunable constants, versioned like the ranking constants in §4.4.

So the full answer to "what does getting upvotes get you": **reach
(ranking), reputation (public counts and flair), privileges (throttles and
limits lifted), and eventually an invitation to the paid-in-points
contribution work — but never points directly.**

### 4.3 For-you ranking (decided)

Per-request scoring over a bounded recent window (last 14 days, capped at a
few hundred candidate posts — at current volume no stored scores or jobs;
materialize only when measurement says so):

```
hot(post) = (W + 2·A + min(R,5) + 1) / (age_hours + 6)^1.5 × T × Q
```

- `W` — weighted helpful votes (§4.1).
- `A` — 1 if a doubt has an accepted answer, else 0 (an answered doubt is
  more useful to the next reader than an open one).
- `R` — visible reply count, capped at 5 so chat threads can't dominate.
- `(age_hours + 6)^1.5` — HN-style gravity: a post gets roughly a day of
  prominence and is gone from For-you within about a week. The +6 offset
  stops a brand-new post with one vote from leapfrogging everything.
- `T` — topic affinity: ×1.25 when the post's question/tag falls inside the
  viewer's saved-exam scope or one of their weakest practicing topics (from
  `user_topic_mastery`); ×1.0 otherwise. Personalization is a boost, never a
  filter — nothing is hidden by the algorithm.
- `Q` — author damp: ×0.5 while an author is under repeat-flag
  `needs_approval` status; ×1.0 otherwise.

Presentation rules on top of the score: pinned posts first (existing);
at most 2 consecutive posts per author; per 10 items, inject 1 unanswered
doubt ("help someone") and 1 material share, when available. The disclosure
gate applies **before** ranking — the feed never ranks what the viewer may
not see. Tabs other than For-you stay purely chronological, so the ranked
view is always escapable and auditable.

### 4.4 Honesty rules

Raw integer counts only (votes, replies); no trending labels without a dated
reviewed pick (existing Hot-topics rule); empty tabs say so. The algorithm
constants above are versioned in one module so a change is a reviewed diff,
not a silent drift.

## 5. Schema sketch (future migrations, not written)

- `posts.canonical_id` becomes nullable; `kind` CHECK gains
  `'study','material-share'`; nullable `topic_tag`/`material_id` columns;
  existing moderation columns reused as-is.
- `follows(user_id, followed_id, created_at)` PK `(user_id, followed_id)`.
- `vocab_decks`, `vocab_cards` (reviewed-content lifecycle),
  `deck_items`; `review_items` gains `item_type` + nullable
  `vocab_card_id`.
- `desk_goals(room_id, ist_week, metric, target, created_by)`.
- No `reward_ledger` changes anywhere in this document — by design, none of
  these systems touch the economy.

## 6. Rollout and order

1. Desk loop integration + mastery strip (pure reads once v2 phase 1
   lands).
2. Vocabulary decks + scheduler unification (depends on `review_items`).
3. Feed: study posts + following + guards (chronological only).
4. Ranking algorithm + For-you, after a few weeks of real post volume to
   tune constants against.
5. Desk sessions, review circle, shared goals, calendar.

Open items — **resolved 16 November 2026 under the owner's "decide all
for me"**: the new-account throttle stands at **3 days / 50 attempts**
and the posting limits at **5 posts / 30 replies per day** (both lifted
by the §4.2 Helper/Regular tiers — the ladder is the escape valve, so the
defaults can stay strict). **Mizo gloss goes on curated cards only**:
bank-derived decks keep the printed source text untouched — a gloss is
editorial content, and editorial content lives in the reviewed curated
layer, never inside a canonical question's presentation.

## 7. Posting, content upload and paid content (16 November 2026 addendum)

Owner request: improve user posting, content upload, and the paid-content
story. Decisions below; everything inherits §3's guards, §4's no-currency
rule and the §5.1/Part I review-gated contribution economy unchanged.

### 7.1 Posting improvements (composer v2)

1. **Type-first composer.** One Create entry with three explicit shapes —
   *Doubt on a question* (anchored, from the question card as today),
   *Study note* (free-standing `study` post), *Share a material*
   (reviewed publication card). No blank-textarea ambiguity about what a
   post is.
2. **Duplicate-doubt deflection** — the single highest-value posting
   improvement available: before a doubt submits, show the question's
   existing threads ("3 discussions already — is yours one of these?")
   with one-tap join. Powered by the thread list that already exists on
   the question; no schema. Fewer fragmenting duplicates, less
   moderation, and the asker usually gets an *instant* answer.
3. **Formatting**: a minimal markdown subset (bold, lists, inline code) —
   rendered, never raw HTML. Still text-only, still internal links only
   (§3.1 hard rules stand); an internal question/material link renders as
   its card.
4. **Drafts**: client-side autosave per composer (the Studio autosave
   lesson); no server draft table for posts — a lost study note is cheap,
   a new table is not.
5. **Edits with honesty**: editable with a visible "edited" marker;
   a reply **locks once accepted** as the answer (it is now evidence
   other learners rely on — same immutability instinct as everywhere
   else). Moderation can still hide anything.
6. **Accepted-answer nudge**: a doubt with replies but no acceptance
   prompts its author once, gently ("did one of these solve it?") —
   directly serves the §0.8 48-hour-acceptance health metric. No
   nagging repeats.
7. *Not doing*: @-mentions (notification spam + a moderation surface we
   are not staffing), image uploads (standing rule), post scheduling.

### 7.2 Content upload (creator pipeline v2)

The machinery exists (Content Studio review lifecycle, 0035 award,
`ReviewBodyLimit`, the 0077 PDF library); what is missing is **the
author's view of it**:

1. **My submissions tracker** in the Create hub: every submission with
   its honest state — draft → submitted → in review → published /
   returned — with the reviewer's note on return and resubmission
   continuing the same thread (states read from the existing lifecycle;
   no parallel status store).
2. **Pre-submission checklist**, shown before review ever starts: source
   named and attributable, own-work/copyright declaration, format/size
   within the body limits. Catches the three most common returns at
   zero reviewer cost.
3. **Tier-aware Create hub**: the hub states plainly what the account can
   submit today — everyone: doubts/replies and study posts (within §3.3
   throttles); reviewed-publication authors: materials; **Mentor tier
   (§4.2): invited into bank contributions — the submissions that pay
   points** (Part I §5.1). The ladder becomes visible exactly where
   ambition forms.
4. **Review honesty**: show "typically reviewed in N days" computed from
   the real recent median, never a promised SLA; show queue position,
   not a fake progress bar.
5. *Not doing*: open uploads of arbitrary PDFs/images to the public
   (copyright + moderation surface), auto-publish for any tier, AI
   drafting of community content.

### 7.3 Paid content (decided stance)

**One subscription; capacity is paid, correctness never is.**

1. **No per-item paywalls.** A verified answer, an explanation or a
   community thread is never individually sold — paying buys *more*
   (full archive breadth per §0.9, limits lifted, deep mistakes, desk
   rooms), never *the truth about a question*. This is the browse-first
   thesis (§0.1) applied to money, and it keeps trust intact: a learner
   never discovers mid-study that the answer is behind a toll.
2. **Premium curated series live inside Pro** — e.g. editor-curated mock
   series land as Pro content, not as separate SKUs. One price (₹100/50),
   one entitlement (`account_has_pro()`), zero per-item purchase
   plumbing, refunds and inventory accounting never exist.
3. **No creator payouts, deliberately, for now.** Paying users cash for
   content means KYC, tax, fraud review and payment disputes — a
   different company. Creators are rewarded in the existing currencies:
   reviewed contributions pay points (Part I §5.1), exceptional work can
   earn owner-granted Pro days (`billing_access_grants` — access, never
   cash, bounded and audited), and standing/reach via the §4.2 ladder.
   Revisit payouts only if creator volume becomes a real constraint.
4. **If one-off paid items are ever wanted** (a priced test series
   outside Pro), they are Razorpay one-time payments, a separate design
   with its own doc — explicitly out of scope here, recorded so nobody
   bolts a shop onto the subscription tables.

---

# Part III — Atlas v2

Baseline: 26 hand-authored chapters under `web/src/atlas/data/chapters/`
(history, Indian and world geography, polity, Mizoram), each a static
TypeScript module of Leaflet layers, timeline events and facts, rendered by
a deliberately small shell (`screens/Atlas.tsx` + `atlas/AtlasMap.tsx`).
The Finna port gave it the chapter sidebar and phone selection. Its
weakness follows from its strength: it is a self-contained encyclopedia
that never touches the bank, the taxonomy or the learning loop.

## III.1 Thesis

Per Part 0, the product is old questions. **Atlas v2 turns every map into
an exam lens**: the question "what has MPSC actually asked about this
river/battle/schedule?" should be answerable from the map itself, and a
geography question in the bank should be able to show its map.

## III.2 Features

1. **Asked-from-this-map panel.** Each chapter (and individually taggable
   layers/pins) maps to subject/topic IDs in the approved taxonomy. The
   chapter view gains a panel of real bank questions for those topics —
   ordinary question cards with the full Part 0 contract (provenance
   labels, inline answering, discussion). Chapter→topic bindings are
   editor-curated data, not model inference; chapters whose topics have no
   tagged questions show an honest "none tagged yet", never padding.
2. **The reverse link.** Question cards whose topic is bound to a chapter
   get a small "View on Atlas" affordance that opens the chapter at the
   relevant layer/event view. One binding table serves both directions.
3. **Map drills (no economy).** Tap-the-map exercises generated from
   chapter pin data: "locate the Battle of Plassey", "which river is
   this?". Client-presented, server-recorded as plain activity — they are
   not canonical questions, so exactly like curated vocab cards (Part II
   §2.5) they pay **no points ever**; they can count toward the warm-up
   quest ring. Wrong drill taps enqueue the *bound topic's* real questions
   into the learner's practice suggestions rather than pretending the
   drill itself is scorable.
4. **Bank-question map mode.** Where a verified geography MCQ's topic is
   bound to a chapter, Smart Review and practice can offer it *with the
   map alongside* — same question, same scoring, same discovery rules,
   just better context. No new award type.
5. **Chapters as reviewed data.** Chapters move from bundle-shipped TS to
   database content published through the existing reviewed-content
   pipeline (Content Studio lifecycle): editors add chapters without a
   frontend deploy, the bundle stops growing per chapter, and chapter
   provenance/review history is recorded like any other published
   material. Existing 26 chapters migrate as the seed corpus, attributed
   as current-site content.
6. **Chronicle cross-links.** Chapter timeline events that correspond to
   dated Chronicle entries link both ways (same binding-table pattern,
   `chronicle_entry_id` on an event).
7. **Explored state (display only).** A per-user "explored" marker per
   chapter (viewed its layers, tried its drills) shown on the Atlas index
   — motivation UI. It never feeds `user_topic_mastery`: mastery moves
   only on scored attempts against verified questions, and a map view is
   neither.
8. **Mizoram depth.** District-level layers (boundaries, HQs, rivers,
   peaks) as first-class chapters — the district dimension already exists
   in profiles (0083); a later Daily Five "district geography" day can
   draw on the bound topics. Exam-scope filtering: with a saved exam, the
   Atlas index orders chapters by that exam's syllabus relevance (binding
   table again), with the full list always available.

## III.3 Atlas Studio — the admin authoring system (owner request, 15 November 2026)

A comprehensive manual authoring surface at `/admin/atlas`, built so the
owner can produce a complete chapter **without touching code, JSON or
coordinates by hand**. Design decisions:

1. **One rendering path.** The Studio's preview *is* the learner Atlas
   component rendering the draft — not a lookalike. This is the
   DESIGN-FIDELITY lesson applied: no drift between what the author sees
   and what learners get. Draft chapters render with a visible DRAFT
   watermark.
2. **Chapter editor.** Form fields for the existing chapter shape: title,
   subject, unit, summary, focus text, ordered facts list (plain text rows,
   add/remove/reorder). Nothing new to learn — the fields mirror what the
   26 hand-written chapters already contain.
3. **Layer editor — draw on the map.** The core of "easy manually":
   - **Pins**: click the map to place, drag to move; each pin gets a label
     and optional note. No typed coordinates anywhere (a read-only
     lat/lng display for verification).
   - **Lines** (rivers, routes, ranges): click a vertex sequence, double-
     click to finish; drag vertices to adjust.
   - **Areas** (regions, kingdoms, climate zones): same vertex flow,
     closed; fill + outline styling.
   - Per-layer controls: name, color from the site palette, dash/solid,
     default-on toggle, reorder, duplicate layer (start the next dynasty
     map from the last one), copy a layer from another chapter.
   - **GeoJSON import** per layer as a power path for traced boundaries —
     optional, never required.
   - Undo/redo across all drawing actions; autosaved drafts, so a
     half-finished chapter survives the browser closing.
4. **Event editor (timelines).** An event = caption + a map view + which
   layers are visible. Authoring a view is literally "pan/zoom the preview,
   toggle the layers, press *Capture view*". Events reorder by drag.
5. **Drill authoring.** Each pin has a "drillable" toggle and a tolerance
   radius (shown as a circle while editing); the Studio derives
   locate-this drills from drillable pins automatically. Custom prompts
   ("Which river forms this boundary?") attach to an existing pin/line.
   Nothing here mints points (III.2.3 stands).
6. **Binding editor.** Subject/topic pickers backed by the live approved
   taxonomy registry (search-as-you-type), at chapter and per-layer level.
   Beside each chosen topic the Studio shows the current count of tagged
   live questions — the author sees exactly what the asked-from-this-map
   panel will contain *before* publishing, and an honest "0 questions
   tagged yet" is visible up front, not discovered later.
7. **Lifecycle.** Draft → preview → publish, through the established
   reviewed-content machinery: versioned snapshots, publish creates an
   immutable version with attribution (`owner` under the solo-owner
   workflow), one-click rollback to any prior version, unpublish holds the
   chapter without deleting history. Staff permissions + the existing MFA
   policy gate the Studio; binding curation may later open to Mentor-tier
   invitees (Part II §4.2), chapter authoring stays staff-only.
8. **Validation, not surprises.** On save: required fields, at least one
   layer, coordinates within a sane bounding box for the chapter's region,
   every event referencing existing layers, drill tolerances positive.
   Failures are inline field errors, never a rejected blob.
9. **Seed import.** A one-time converter ingests the 26 existing TS
   chapters as published version 1s, attributed as current-site content —
   the Studio opens pre-populated, and the TS files retire.

## III.4 Data sketch (future migration, not written)

- `atlas_chapters(id, status, current_version_id, subject, unit, ...)` +
  `atlas_chapter_versions(id, chapter_id, body JSONB, authored_by, note,
  created_at)` — the reviewed-content lifecycle; `body` holds layers/
  events/facts/pins/drills in the current TS shape; publish points
  `current_version_id`, rollback repoints it, nothing is deleted.
- `atlas_drafts(chapter_id, user_id, body JSONB, updated_at)` — Studio
  autosave, one live draft per author per chapter.
- `atlas_topic_bindings(chapter_id, layer_id NULL, subject_id, topic_id)` —
  the two-way lens; editor-curated in the Studio.
- `atlas_drill_results(user_id, chapter_id, drill_id, correct, at)` —
  activity only, outside `attempts` (drills are not canonical questions and
  must never pollute attempt-derived stats).
- Explored state derivable from drill results + a viewed marker; no
  dedicated economy columns anywhere.

## III.5 Rollout

1. Binding table + asked-from-this-map panel + reverse link (pure reads;
   ships against the existing static chapters — nothing blocks on the
   Studio).
2. **Atlas Studio + chapters-as-data**: the version/draft tables, the seed
   import of the 26 TS chapters, and the authoring surface (chapter/layer/
   event editors with the single rendering path). From this point new
   chapters need no deploy.
3. Drill authoring + map drills + explored state + quest-ring hookup.
4. Mizoram district chapters + exam-scope ordering + Chronicle links.

Open items — **resolved 16 November 2026 under the owner's "decide all
for me"**: drills **do** appear on Today for learners whose weak topics
are map-bound — as a suggestion row, never a requirement, never counted
against the plan. Bindings are curated by the **owner first**;
Mentor-tier invitees join once Part II §4.2 ships. Both as originally
suggested.

---

# Part IV — Backend architecture (web + mobile)

The complete backend design: what exists (verified in code 15 November
2026), the conventions that bind it, and the exact backend work Parts 0–III
require. The API is FastAPI + psycopg3 (async pool) over PostgreSQL on the
Oracle VM, behind the shared Caddy; the bank workshop is a sibling system
that publishes content *into* this database and is out of scope here except
at its sync boundary.

## IV.1 Topology and runtime

```
Caddy (shared with family.hawayu.in — never rewrite the Caddyfile)
 ├─ study.hawayu.in  → static web build (rsynced by scripts/deploy.sh)
 │                   → /api/* → uvicorn FastAPI at /srv/api
 └─ /papers          → original PDF assets (reserved namespace)
PostgreSQL (same VM)  ←  guarded bank publication (Oracle workshop timers)
```

- One process, one async connection pool opened at startup (`db.py`):
  dict rows, `jit=off` (bank view queries trigger JIT compilation that
  costs more than the reads), request latency dominated by connection
  reuse, not queries, at current scale.
- In-process background workers as lifespan asyncio tasks: assessment
  reassessment queue (`scoring_revisions`), desk retention purge, calendar
  reminders, game lifecycle, account mail. No external queue — correct at
  this scale; the growth path is §IV.7.
- Middleware stack, in order: CORS → `AccountBoundary` (account/session
  resolution rules) → `MobileBoundary` (mobile-token path allowlist) →
  `ReviewBodyLimit` (payload caps) → `InvalidatePublicCatalog` (drops the
  public-catalog cache generation on admin/collection mutations).
- `/api/health` and `/api/scoring-facts` are the liveness/contract probes.

## IV.2 Application architecture

~45 routers (`app/routers/`) over ~55 services (`app/services/`), with
four binding conventions:

1. **Routers are thin, SQL lives close.** Handlers compose `cursor()`
   queries and service calls; schemas (Pydantic) define every response.
2. **Scope is explicit.** `exam_scope.py` (`question_scope`,
   `scope_condition`) threads cohort/exam scoping through every bank read;
   new bank-reading endpoints must take an `ExamScope`, never re-derive it.
3. **Learner data is never cached shared.** `Cache-Control: private,
   no-store` on personal reads; the only shared cache is the process-local
   public-catalog cache (TTL ≤60s, 32 keys, generation-invalidated) — a
   pattern to extend, not bypass (§IV.10).
4. **Awards and scoring happen in SQL functions/triggers**, not handler
   code (`reward_study_attempt()`, award triggers, immutability triggers) —
   so no endpoint shape change can mint currency or rewrite history.

## IV.3 Identity and access

Resolution order in `current_user()`: mobile session → account
`auth_sessions` cookie → server-issued HttpOnly **guest identity** (0056; a
real `users` row, `X-Device-Id` kept only as a compatibility preference).

| Tier | Gets | Gate |
| --- | --- | --- |
| Guest | full browse, device-bound progress/attempts | none (by Part 0 decree) |
| Account (`email IS NOT NULL`) | sync, rewards, streaks, community voice, desks | `require_account()` |
| Pro | deep mistakes, desk-room creation, other conveniences | `account_has_pro()` = paid plan ∪ reward redemptions ∪ admin grants (`billing_access_grants`, live since 0089) |
| Staff/owner | admin surfaces | role + staff MFA policy (with the one recorded exemption) |
| Mobile token (`ism_mobile_*`) | learner-only subset | `MobileBoundary` method/path allowlist, checked before auth |

Auth features in place: password + Google identity (0071), TOTP MFA
(0033), email recovery (0057), same-origin CSRF for cookie sessions
(mobile sessions exempt by `request.state.mobile_session`).

## IV.4 Data domains

Eight domains, 83 migrations; the invariant column is what new code must
never break:

| Domain | Core tables | Binding invariant |
| --- | --- | --- |
| Bank/content | `canonical_questions`, `appearances`, `papers`, `collections`, `question_classifications` | provenance CHECK + `v_scorable`; content arrives only via guarded publication; workflow data never imported from bank JSON |
| Learning | `attempts` (+ assessments/jobs 0032), `mock_sessions` (+frozen snapshots 0031), `practice_study_sessions`, checkpoints, module progress, vocabulary | attempts immutable, store `chosen_text`; corrections re-assess, never rewrite |
| Economy | `reward_ledger`, `reward_profiles`, `reward_question_claims`, catalog/redemptions, `daily_quest_claims` | immutable ledger, unique `event_key`, per-user lock, caps in SQL |
| Community | `posts`, `post_votes`, `discussion_disclosures`, `creator_blocks`, contribution pipeline (0030) | disclosure gate before visibility; moderation flags honored everywhere |
| Games | `game_rooms/members/cups/dailies` | frozen question snapshots, server timing/scoring only |
| Desk | desk rooms/items/messages/focus/invites (0040) | private, six-seat, retention purge, non-economic |
| Accounts/billing | `users`, `auth_sessions`, billing/Razorpay, MFA, avatars | redemptions/grants never touch `plan_*` or Razorpay |
| Admin/ops | audit events, moderation, inbox, exam calendar, pdf library, editorial/workbench | immutable audit history, attributed decisions |

New tables from Parts I–III join their domains: Learning gains
`user_topic_mastery`, `review_items` and `user_focus_subjects` (§12);
Economy gains the points-cap counters (the grants table landed 16 November
in Accounts/billing as `billing_access_grants` + `billing_account_rates`,
0089); Community gains `follows` + post-kind widening; Content gains vocab
decks/cards and `atlas_*`.

## IV.5 The integrity layer (cross-cutting)

The backend's real product is trust; these mechanisms are mandatory for
every new feature: immutability triggers (`review_immutable()` pattern) on
ledgers/history; unique `event_key` idempotency + client Idempotency-Key
headers on side-effectful POSTs; per-user advisory locks around wallet
mutations; optimistic version checks + reason strings + audit events on
admin mutations; provenance/eligibility only via `v_scorable` and
answer-status views; answer-reveal and disclosure gates applied before any
ranking or listing; honest empty states (no invented activity) as an API
property, not just UI.

## IV.6 API conventions

- REST-ish `/api/<domain>/...`; Pydantic response models; cursor or
  offset+`has_more` pagination (limit caps ~50).
- Reads default `private, no-store`; §IV.10 adds a public tier for
  anonymous browse.
- Side-effectful POSTs: Idempotency-Key header (≥16 chars) where retries
  are possible; server-generated receipts returned on replay.
- Rate limiting is per-feature today (desk invites, posts); Part II's
  throttles (5/30 posts, new-account rules) introduce a small shared
  `rate_limits` helper (counter table keyed `user:action:ist_date`) rather
  than N bespoke counters — one audited implementation.
- Errors: FastAPI status + terse human message; never leak other users'
  existence through error shape (established in desk invitations).

## IV.7 Background processing

Today: five in-process asyncio workers (IV.1) + systemd timers on the VM
(bank review/publication, backups). Design rule: **a worker must be
restart-safe and idle-cheap** (poll with backoff, claim rows with
`FOR UPDATE SKIP LOCKED` — the assessment queue already models this).

New work slots into the same pattern: mastery rollup consumes attempt/
assessment events (incremental, plus a nightly reconciler that recomputes
drifted users); review-item promotion is done at answer time (no worker);
due-date queries are index reads. The growth path when a worker starves
the event loop: move that worker to a second uvicorn-less process reading
the same queue tables — no architecture change, just a systemd unit.

## IV.8 Mobile backend

Verified flow: PKCE-style pairing (`/mobile-auth/start` → user-approved
`/authorize` → `/exchange`) issues `ism_mobile_*` bearer tokens;
`MobileBoundary` rejects any request outside its READ/WRITE regex
allowlist *before* auth (invalid token ⇒ 401 on allowed paths, 403 on
blocked — a free liveness probe). Mobile sessions are learner-only by
design: no staff, no billing writes, no `POST /auth/password` (same-origin
+ session-revocation semantics make it wrong for native).

Design for the Expo app's growth:

1. **The allowlist is the contract.** Every feature the app gains = an
   explicit allowlist diff + a companion test
   (`test_mobile_companion.py` pattern). Finnaplan's mobile set, in order:
   review-queue/mastery/today GETs, then attempts + review-session writes
   (practice on the go), then bookmarks/desks reads it already has, then
   community reads; community *writes* stay web-only until moderation
   tooling is proven. Each widening is an owner decision, recorded.
2. **Capability negotiation, not API versioning.** `/mobile/session`
   returns a `capabilities` list derived from the current allowlist; the
   app renders only what the server declares. Old app builds degrade
   gracefully without version-gated endpoints.
3. **Offline: cache, don't sync.** The app caches browse content
   (questions/papers it has seen) read-only; attempts made offline queue
   locally and replay through the normal idempotent answer endpoints
   (client-generated idempotency keys). No server-side CRDT/sync tables —
   the desk personal-plan conflict model stays the web's
   import/export/version-conflict flow.
4. **Push** (later): a `device_tokens` table + a notify worker for streak
   reminders and desk mentions, strictly opt-in, reusing calendar-reminder
   scheduling. No third-party analytics SDKs.

## IV.9 Build map — backend work for Parts 0–III

Each row: migration(s) + service + router(s) + tests. Order follows Part 0
sequencing; every migration rehearsed on a dump clone first.

| # | Work | Schema (0090+) | Code |
| --- | --- | --- | --- |
| 1 | Browse perf tier | indexes for the two slow queries | ETag/`Cache-Control: public` on anonymous bank/paper/exam reads, keyed by exam scope + content version (reuse `InvalidatePublicCatalog` generations); guests only — any cookie/token ⇒ private |
| 2 | Mastery + review | `user_topic_mastery`, `review_items` (+`item_type`), `user_focus_subjects` (§12.1) | `services/mastery.py` (incremental rollup + reconciler), `services/review_queue.py`; routers: `/me/mastery`, `/me/review-queue`, `/review-sessions` (compose via `practice_study_sessions`), `/me/today` (+focus filter, growth recap), `/me/focus-subjects` |
| 3 | Economy v2 | points-cap counters; `RULE_VERSION='learning-v2'` SQL function rewrite (sub-caps, session/game/mock awards, quest rewire) | extend `learning_rewards.py`; catalog rows repriced as data (1500/400); diagnostics extended; §12.2–12.3 board queries (display only, no schema) |
| 4 | ~~Admin grants~~ ✅ shipped 16 Nov 2026 | `billing_access_grants` + `billing_account_rates` (0089) | `account_has_pro()` union live; `/api/billing/admin/account` + `/days` + `/rate` (MFA, audit, idempotent); billing UI reads `granted` status |
| 5 | Community v2 | `posts.canonical_id` nullable, kind CHECK widened, `follows`, `rate_limits` | ranking constants module in `community.py` (For-you window query), throttles, following tab; vote weights computed in SQL at read |
| 6 | Vocabulary v2 | `vocab_decks/cards/deck_items`, review_items typing | curated-card lifecycle via content review; recall/cloze modes in `vocabulary.py` |
| 7 | Atlas v2 + Studio | `atlas_chapters/chapter_versions/drafts/topic_bindings/drill_results` | public chapter reads (cacheable tier); `/admin/atlas` Studio routers (draft autosave, publish/rollback, binding editor with live tagged counts); seed importer for the 26 TS chapters |
| 8 | Desk v4 | `desk_goals` | Today/mastery reads on desk; desk sessions reuse `games.py` party mode |
| 9 | Mobile widening | — | allowlist diffs + capability list + companion tests per feature (IV.8) |

## IV.10 Performance and capacity

Measured baseline: ~5.4k tps on the 77k bank, sub-ms queries behind a warm
pool — the single VM has an order of magnitude of headroom **if** reads
stay indexed and cacheable. The plan: fix the two known slow queries
before growth marketing; replace per-request `attempts` aggregation with
the mastery/progress rollups; three cache tiers — (a) process-local
public-catalog cache (exists), (b) HTTP public tier for anonymous browse
(build map #1; lets Caddy and browsers absorb guest traffic, which Part 0
predicts is most traffic), (c) nothing shared for learner data, ever. Pool
sizing stays settings-driven; watch `pool_max` vs Postgres
`max_connections` when adding the second worker process (IV.7).

## IV.11 Security model

Threats and standing mitigations: forged identity (server-issued HttpOnly
guest cookies, device-id advisory only); currency minting (no client award
path, SQL-function awards, immutable ledger, event keys, per-user locks,
caps); answer leakage into scoring (provenance CHECKs, `v_scorable`,
frozen mock/game snapshots, reveal + disclosure gates); privilege
escalation (role checks + staff MFA + MobileBoundary pre-auth, boundary
regexes tested); CSRF (same-origin checks, mobile exemption scoped to
bearer sessions); payment safety (redemptions/grants never touch Razorpay
or `plan_*`); abuse (idempotency receipts, body limits, per-feature + new
shared rate limits, vote weighting); secrets only in private credential
storage. Backups: paired backup/recovery per the Oracle runbook; a restore
rehearsal belongs in every migration-heavy release.

## IV.12 Operations and release gates

Deploy: build web locally, `scripts/deploy.sh [web|api|all]` rsyncs
artifacts; never build on Oracle; verify **both** study and family sites
after any Caddy/systemd/Postgres touch. Migrations: new numbered files
only, rehearsed on a disposable dump clone, never edited after apply.

Release gate, defined (the test suite alone is explicitly *not* one):
1. isolated-Postgres test suite green (including the reward/boundary
   guards); 2. migration rehearsed on a fresh prod-dump clone with timed
   apply; 3. deployed artifact SHA256s compared; 4. live health + one
   scripted end-to-end check of the changed flow; 5. DEVLOG receipt.
Observability stays minimal and boring: uvicorn/Caddy logs, Postgres
slow-query log at a real threshold, the reward reconciliation
(`/admin/bank/reward-diagnostics`) run after any economy change.

## IV.13 Testing strategy

Per existing pattern: isolated PostgreSQL tests (real role execution, no
production fixtures, no synthetic reviews), one guard test per boundary
promise (mobile allowlist, guest exclusion, provenance exclusion, replay
safety), plus per-feature flow tests. New-code rules: every award path
gets a replay test and a cap test; every ranking/visibility query gets a
blocked-user and a disclosure-gate test; the Studio gets a
publish/rollback/attribution test; capability negotiation gets an
old-client test (unknown capability ⇒ hidden, not crash).

---

# Part V — Implementation guide

Written 16 November 2026. **This is a guide, not a changelog: none of it
is implemented.** It sequences Parts 0–III + §12 into shippable phases
for whoever builds them (human or model), using only conventions that
already exist in this repository. Migration numbers below are the
next-free at time of writing — **take the actual next free number when
you start**, never renumber an applied file.

## V.0 Standing gates (every phase, no exceptions)

1. New numbered migration in `api/migrations/`, rehearsed on a disposable
   production-dump clone with timed apply, never edited after apply.
2. Isolated-PostgreSQL tests (real role execution, no production
   fixtures): every award path gets a **replay test and a cap test**;
   every visibility query gets a blocked-user and disclosure-gate test;
   every boundary promise gets a guard test.
3. Build web locally; deploy with `scripts/deploy.sh [web|api|all]`;
   never build on Oracle; never rewrite the shared Caddyfile; verify
   **both** study.hawayu.in and family.hawayu.in after infra-adjacent
   changes.
4. After any economy change: run `/admin/bank/reward-diagnostics`.
5. DEVLOG receipt before stopping; record limitations honestly.
6. Mobile: each new learner-facing endpoint is an explicit
   `MobileBoundary` allowlist decision + `test_mobile_companion.py`
   extension + capability-list entry (§12.6) — never a side effect.

## V.1 Phase A — Browse perf tier (no learner-visible change)

Build map IV.9 #1. Order: (a) identify/index the two known slow queries
(EXPLAIN on the dump clone, before/after timings recorded); (b) ETag +
`Cache-Control: public` on anonymous bank/paper/exam reads, keyed by exam
scope + content version via the existing `InvalidatePublicCatalog`
generations; any cookie/token ⇒ `private, no-store` unchanged.
**Tests**: a guest-vs-authenticated cache-header guard; invalidation on
admin mutation. **Done when**: timed queries improve on the clone, guest
responses carry correct validators, learner responses never do.

## V.2 Phase B — Mastery + review core (migration ~0090, zero new awards)

The largest phase; everything later leans on it. It deliberately mints
nothing, so thresholds can be tuned on real usage (§10 phase 1).

1. **Schema**: `user_topic_mastery`, `review_items` (+`item_type`),
   `user_focus_subjects` (§6, §12.1), with the partial due-date index.
2. **Services**: `services/mastery.py` — incremental rollup on attempt
   insert + reassessment completion (0032 job pattern) + nightly
   reconciler for drifted users; `services/review_queue.py` — Leitner
   promotion at answer time, box intervals 1/3/7/16/35 IST days.
3. **Seed**: latest-attempt-wrong questions into box 1. **No reward
   backfill of any kind.**
4. **Routers**: `/me/mastery`, `/me/review-queue`, `/review-sessions`
   (server-composed ≤20 due items through `practice_study_sessions`,
   `attempts.context='review'`), `/me/today` (single composed GET —
   §12.5), `/me/focus-subjects` GET/PATCH (≤5, registry-validated).
5. **Web**: Today card on Home (§12.4 order), Smart Review session
   (existing practice player), mastery map (desktop grid / phone
   accordion §12.5), focus bottom-sheet/checklist.
6. **Tests**: rollup vs. ground-truth aggregation on fixtures; promotion/
   demotion; reassessment re-derivation; focus-filter honesty (due count
   never shrinks); guest exclusion.

**Done when**: a learner sees due reviews and mastery move with zero new
ledger rows, and `/api/me/progress` reads rollups instead of scanning
`attempts`.

## V.3 Phase C — Habit (migration ~0091, first new award rows)

Unified streak (§5.3: `reward_profiles` authoritative; guest fallback
labeled "device activity"), quest rewiring (§5.2 — new quest keys as
data, old claims historical), review-session award (20 XP + 2 pts, §5.1
row 2, with the ≥3s/item latency heuristic). **Tests**: replay + cap +
streak-qualification matrix. **Done when**: both streak surfaces agree
and a completed Smart Review pays exactly once.

## V.4 Phase D — Economy v2 (migration ~0092, the owner-gated one)

`RULE_VERSION='learning-v2'` SQL function rewrite: per-pillar sub-caps
(§5.1 table), 25-pt daily cap counters, game/mock awards, mastery
milestones, contribution amounts; catalog repriced as data (pro-month
1500 / pro-week 400). **The enablement gate is §11 resolution 4** (diagnostics
pass + paid checkout live) — build everything dark, flip the catalog last. **Tests**:
one test per sub-cap, cap-interaction (XP continues after points cap),
milestone once-ever, contribution exemption. **Done when**:
reward-diagnostics reconciles a seeded week of mixed activity to the
rupee math in §5.4.

## V.5 Phase E — Boards, recap, calendar (one small migration)

Leaderboard neighborhood view (§12.2), per-mode weekly game boards
(§12.3) over existing server-owned results, Monday growth recap (§12.1)
— all display-only, reusing the existing opt-in flag. Plus the Helper
Calendar's owned layers (§14): `calendar_entries` +
`calendar_feed_tokens` (the phase's one migration), personal-entry CRUD,
progress-test slots, ICS feed. Plus profile edit (handle rename rule,
bio) and the cosmetics points shop (§12.8 — needs V.4's economy settled;
zero new tables, ledger spend + existing `user_avatar_items`). (The forecast/official/habit layers ship
earlier, free, with V.2 — they are pure reads.) **Tests**: opt-out
invisibility, IST week boundaries, empty-board honesty; calendar: feed
token revocation kills the URL, feed contains only the owner's layers,
missed progress test reschedules without side effects.

## V.6 Mobile app widening (interleaved, per §12.6)

After V.2: the reads (step 1). After V.3: review-session + answer writes
and focus PATCH (steps 2–3). Community reads after Part II ships;
community writes stay web-only. Each step is its own allowlist diff +
companion test + capability entry — one PR-sized decision at a time.

## V.7 New exam onboarding checklist (§0.10 operational)

Data work, not architecture work; no migration unless the registry needs
new approved topics:

1. Create exam body / exam / collection rows; configure `exam_scope`.
2. Map the syllabus onto the shared registry (new topics only through
   the tagging policy's approval path). **The second exam body is the
   trigger to build `exam_syllabus` + the `is_primary` saved-exam flag
   (§0.11.1) and wire the lens cascade (§0.11.2) — module/deck
   applicability labels, feed exam chips, scoped defaults. Until then
   MPSC's existing scope machinery is the lens and nothing needs
   building.**
3. Ingest papers through the Oracle parse → review → guarded-publication
   pipeline (source PDFs archived per `SOURCE-PDF-ARCHIVE.md`).
4. Verify in the browser: provenance labels honest, paper order
   preserved, scope filtering correct, scoring restricted to the new
   exam's own verified pool.
5. Enable discovery surfaces (exam catalog entry, saved-exam option)
   last. No seeded activity, no invented counts.

## V.8 Never, during any phase

No historical/bulk award backfill; no client-callable award endpoint; no
shared caching of learner data; no `ORDER BY random()`; no editing
applied migrations; rewards never touch Razorpay/`users.plan_*`; no
synthetic reviews or invented activity in tests or demos; AI-drafted
current-affairs MCQs never reach learners unreviewed; and when a phase's
diff grows past review size, split the phase — don't push through.

## V.9 Phase F — Consolidation retrofit (§0.12, mostly deletions)

The cheapest phase and the one users feel most: `/revise` assembled from
the existing mistakes screen + Smart Review + vocab due + export button;
the Desk stripped to its toolbox (Today copy, mastery strip and
self-reported target removed); `/important-days` redirecting into
Chronicle; the Play hub grid replacing scattered game entries; the
quick-switcher-as-only-global-search and Inbox-as-only-bell rules
enforced by removing, not adding. **Tests**: old routes redirect, nothing
404s, no orphaned nav entries. **Done when**: every §0.12 table row's
"retired" column is actually gone from the UI.

## V.10 Phase G — Community & content v2 (Part II)

Part II's own rollout order (§6) plus §7: study posts + following +
guards, then ranking after real volume; composer v2 with
duplicate-doubt deflection; the submissions tracker and tier-aware
Create hub; vocabulary decks + scheduler unification. Community writes
stay web-only (IV.8). **Tests**: §IV.13's blocked-user/disclosure pair on
every new query; throttle and tier-lift tests; dedup-deflection renders
existing threads.

## V.11 Phase H — Growth & pricing (§13 + §5.5 extension)

In approved order: email provider first (it gates #4 and referral
notifications); WhatsApp share cards; onboarding diagnostic; due-review
digest; referral Pro-days (7/7, 10-attempt gate, ≤5/year, post-launch
only); exam-day taper; the bulk-₹50 email allowlist + group claim codes
(100 uses / 30 days defaults). **Tests**: referral replay/cap/gate
matrix; allowlist applies at signup exactly once; revoked code stops
redeeming; taper never hides due reviews.

## V.12 Phase I — Admin & maintenance (Part VI)

Build Part VI's consoles in its §VI.5 order. Exception that moves
earlier: `worker_heartbeats` ships **inside V.2's migration** (the first
phase that adds a worker — the mastery reconciler should be born
observable), and the feature-gates panel ships with V.4 (the catalog
flip needs its checklist before anyone can flip anything).

## V.13 The final build order (everything above, one table)

| # | Phase | Delivers | Gate to next |
| --- | --- | --- | --- |
| 1 | V.1 perf | fast anonymous browse | timings recorded |
| 2 | V.2 core | mastery, `/revise`, Today, focus, calendar read-layers, heartbeats | rollups match ground truth |
| 3 | V.3 habit | one streak, rewired quests, first new awards | replay/cap tests green |
| 4 | V.4 economy | sub-caps, 25-pt cap, milestones, repricing, gates panel | diagnostics reconcile a seeded week |
| 5 | V.5 boards | leaderboards, recap, calendar owned-layers + ICS | opt-out/empty-state tests |
| 6 | V.9 consolidation | §0.12 map made real (mostly deletions) | zero dead routes |
| 7 | V.10 community | posts/votes/composer/uploads, vocab decks | moderation holds at real volume |
| 8 | V.11 growth | email, share cards, referral, digest, bulk ₹50 | each gated on its dependency |
| 9 | V.12 admin/maint | Part VI consoles, retention workers, checklists | ops page green for a full week |
| 10 | Parts II–III remainder | desk v4, Atlas v2 + Studio | their own rollout sections |

Mobile widening (V.6) interleaves after rows 2, 3 and 7; a new exam body
(V.7) can onboard any time after row 2 — it is data work. Catalog-live
(§11 resolution 4) sits between rows 4 and 5 at the earliest, and only
with paid checkout launched.

---

# Part VI — Admin console & maintenance system

Added 16 November 2026 at the owner's request: "optimize the admin — a
robust production-level [console] and a maintenance system." Design only.
The admin already has real surfaces (the redesigned `/admin/bank`
workbench with overview/review/pipeline/audit, Rewards & accounts with
the 0089 pricing/grants panel, moderation, publishing, stats); this part
gives them a spine. The §0.12 discipline applies to admins too: **one
place per operational job.**

## VI.1 Principles (all existing patterns, now binding for every console)

1. Every mutation: optimistic version check + audit event + actor
   binding; staff MFA policy (with the one recorded exemption); reasons
   where the schema has them, factual change summaries where it doesn't
   (the solo-owner workflow rule).
2. Every list a console shows is a real query with an honest empty/error
   state — an outage must render as an outage, never as "nothing here."
3. Consoles read through the same API as everything else — no SQL-only
   admin features, or the audit trail develops holes.
4. Display-only by default; a button that changes production state names
   its consequence on the button, not in a tooltip.

## VI.2 The ops dashboard (`/admin/ops`) — the production-level piece

One read-only page answering "is the site healthy?" without SSH:

- **Workers**: `worker_heartbeats(worker PK, last_beat, last_ok, note)` —
  every in-process asyncio worker (assessment queue, desk purge,
  calendar reminders, game lifecycle, mail, mastery reconciler) beats on
  each cycle; the page shows staleness in color. Restart-safe, one tiny
  table, no external monitoring stack.
- **Timers**: the systemd jobs (bank review/publication, backups, stats
  checks) can't be read by the API directly — a collector step appended
  to each timer's unit writes its outcome row to the same heartbeats
  table. One pattern for both kinds of background work.
- **Probes**: `/api/health`, DB pool occupancy vs `pool_max`, webhook
  receipts in the last 24h (once checkout is live), last backup success
  timestamp, disk headroom (collector-written).
- **Economy watch**: yesterday's mint/redemption totals, cap-hit count,
  and two human-judgment flags — accounts at the daily cap ≥7 days
  running, new-account earning velocity outliers. Display only; a human
  decides, the reward-diagnostics page investigates.
- **Moderation pulse**: open reports count + median age (feeds the §0.8
  48h health metric).

No alerting infrastructure: the page is the alert, checked with the
morning tea. If the site ever earns real on-call, that is a later,
separate decision.

## VI.3 The maintenance system

1. **Retention workers** (each boring, heartbeat-registered, V.0-tested):
   the existing desk purge; expired `auth_sessions` sweep; old
   idempotency receipts; **guest users with zero attempts and 12 months
   of silence** (guests with progress are kept — adoption is a promise,
   §IV.3). Every sweep logs counts to its heartbeat note.
2. **Backup discipline**: the paired backup/recovery already in the
   Oracle runbook, plus a **monthly restore rehearsal** on a disposable
   clone, receipted in DEVLOG. The ops page shows days-since-last-
   rehearsal — a number that embarrasses at 40.
3. **Site notice, not maintenance mode**: an owner-set banner
   ("maintenance tonight 02:00 IST") stored like other admin settings,
   rendered site-wide. Honest comms instead of a write-freeze kill
   switch — deploys here are rsync + restart and don't need one; a 503
   switch is more likely to be left on by accident than to save a
   migration.
4. **The monthly checklist** (a doc section, run by a human, receipted
   in DEVLOG): restore rehearsal · dependency/CVE pass · Caddy cert +
   **both sites** check · slow-query log review · economy diagnostics ·
   moderation backlog · disk/log rotation glance · heartbeats all green.
5. **Runbook links everywhere**: every ops-page row links to its runbook
   section (the Oracle workbench runbook stays the operational truth;
   the ops page is its dashboard, not its replacement — §0.12 for ops).

## VI.4 The user viewer (`/admin/users`) — owner request, 16 Nov 2026

One read-only aggregation page per account, found by email or handle
search. The 0089 panel's account lookup is its seed; this is the full
picture, in sections:

1. **Account**: email, handle, created, roles, MFA state, active
   sessions count, last real activity (from auth events / attempts —
   never `last_login` alone).
2. **Access**: plan state, per-account rate (₹100/50), active grants,
   redemptions, trial — the same `account_has_pro()` truth billing shows
   the user, plus provider subscription reference when one exists.
3. **Study**: attempts total, verified-correct count, streak, mastery
   tier counts, saved/primary exam — aggregates only, never the
   learner's individual answer history page-by-page (staff curiosity is
   not a product feature).
4. **Economy**: wallet balance, last 20 ledger rows, days at the daily
   cap in the last 30 (the VI.2 anomaly flags, per-account).
5. **Community**: posts/replies counts, helpful received, ladder tier,
   open reports against, `needs_approval` state, blocks given/received
   **as counts only**.
6. **Actions are links, not buttons** (§0.12 for admin): rate and
   extra-days changes link to the Rewards & accounts panel; moderation
   state links to the moderation queue; nothing mutates from the viewer
   itself, so the audit trail stays where the tools are.

Guards: staff + MFA policy; the viewer never renders password hashes,
session tokens, raw device identifiers, or another user's private desk
content. It exists so "what is going on with this account" takes one
search instead of six consoles — and nothing more.

## VI.5 Build order and schema

1. `worker_heartbeats` + worker beats (ships early, inside V.2).
2. `/admin/ops` page reading heartbeats + probes; timer collectors.
3. Feature-gates panel (with V.4): catalog-live and checkout-enabled
   flips shown with their §11-resolution-4 checklist; the flip button
   stays disabled until its conditions read green — guard rails in the
   UI, decision still the owner's.
4. The user viewer (VI.4) — pure reads over existing tables.
5. Retention workers + site notice + monthly checklist doc.

Schema total: one table (`worker_heartbeats`), one settings row (site
notice). Everything else is reads — which is the Part VI test of
honesty: a maintenance system that needs ten tables is monitoring
itself, not the site.
