# Decisions

> Current operations: read `CLAUDE.md` and `docs/PLAN.md`. This document is a
> historical decision ledger, not an executable task list. Oracle authority and
> the current runbooks supersede earlier local publishing locations and old counts.


Short records for choices that would be expensive to reverse. Newest last.
If you change one of these, add a new record saying why rather than editing
the old one.

---

## 1. FastAPI, not Django — 2026-10-18

**Considered:** Django + django-ninja; FastAPI + SQLAlchemy; Next.js API routes.

Django's case rested almost entirely on its admin panel. The design handoff
includes a fully specified Admin Console, so that admin is being built either
way and Django's version buys nothing. What remained told against it: the
schema is hand-written SQL with triggers, partial unique indexes, recursive
functions and generated columns, and Django's ORM wants to own the schema
through its own migrations. Multiplayer also needs WebSockets, which FastAPI
has natively and Django needs Channels plus Redis to match.

The data pipeline (parsers, OCR, answer-key tooling) is already Python, so a
Python API reuses those models instead of reimplementing them in TypeScript.
FastAPI emits OpenAPI, so the React app still gets generated types.

The handoff README suggests Next.js, but scoped to *"if no codebase exists
yet"* — one does, and it is Vite + React.

---

## 2. Fresh monorepo rather than building into india-study-map — 2026-10-18

The existing app is real (349 files in `src/`) but it is a research and
content workspace: 41 loose entries at the root, one-off HTML files, data
dumps. The new design is a full platform redesign with its own structure and
a backend that has no natural home there.

`india-study-map-app` starts clean with `web/` and `api/`. The old repo stays
untouched as a reference, and its valuable parts (`src/data`, `src/modules`)
get ported deliberately rather than inherited by accident.

---

## 3. Answers are identified by text, and only official keys are scorable — 2026-10-18

Inherited from schema v3 and reinforced after review. Two parts:

Storing the answer as option **text** on the canonical question, with each
appearance mapping its printed order via `option_order`, is what makes a
reprint with shuffled options unable to inherit the wrong letter. It also
means `attempts.chosen_text` survives a key correction and can be re-scored.

Separately, `v_scorable` admits only `answer_source IN ('official','key')` —
12,319 of 77,751 rows at the latest bank sync (12,342 canonical rows carry
an official/key label before duplicate-option and source-defect guards).
40,675 answers are model-inferred, which at the
measured ~91% high-confidence accuracy implies thousands of confidently wrong
"correct" answers. The project's own extraction guide already says a model
"may never write `official` or `key`"; the first draft of `v_scorable` did
not enforce it.

**Known hole:** ~1,508 questions print the same option text twice, so text
cannot identify which position was right. They are flagged
`source_defect = 'duplicate-options'` and excluded from both views until a
human fixes them.

---

## 4. Build locally, deploy artifacts — 2026-10-18

`npm run build` on one Ampere core is slow and competes with the running
site. Builds happen on a developer machine; `scripts/deploy.sh` rsyncs
`web/dist` to `/srv/study/public`. The server never compiles frontend code.

---

## 5. The bank is authored locally; the server database is a derived artifact — 2026-10-18

The question bank is edited locally, by hand and by various models, with
`mpsc-question-bankv2/bank/mpsc_bank_v2.json` under git as the single source
of truth. `scripts/sync-bank.sh` pushes it to the server. The sync is
one-way, re-runnable, and never reaches outside the bank tables.

What this buys: several models can work the bank in parallel, every change is
a reviewable diff, and the server can be rebuilt from scratch — which matters
on a free-tier box that Oracle may reclaim.

**Two classes of data, and they must never be synced alike:**

- *Bank data* — papers, questions, options, answer keys. Authored locally,
  overwritten on every sync.
- *User data* — users, attempts, posts, votes, reports, moderation. Created
  on the server, **never** touched by the sync. Losing it is unrecoverable;
  there is no local copy to restore from.

**Open tension — resolve before the Admin Console ships.** Admin is designed
to correct wrong keys and OCR errors, which are edits to *bank* data made on
the *server*. Under this decision the next sync destroys them. The intended
resolution is that admin writes to a correction queue which is exported back
into the local JSON, so fixes reach the server only through the normal sync.
The alternative — letting the server own `answer_text`/`answer_source` while
local owns the rest — splits truth by column and reproduces the local/prod
divergence that has already caused trouble on another project. Until this is
settled, do not build admin writes that mutate `canonical_questions`
directly.

---

## 6. Anonymous device ids before real accounts — 2026-10-18

Progress is attributed to a client-generated UUID in `localStorage`, sent as
`X-Device-Id`. The server creates a `users` row per device on first sight, so
attempts have a real foreign key and nothing special is needed later.

This is **not authentication.** The header is forgeable and identifies a
browser, not a person. Nothing that matters may be gated on it — no payments,
no moderation powers, no private data. It exists so practice, mocks and
mistake review can be built and tested now, without first standing up
registration, password reset and session management.

When accounts arrive, a signed-in user adopts the device's attempts by
reassigning `attempts.user_id`. Deferring the choice also avoids committing
to email/password versus Google before it is known which one users want.

**Profile scope — 2026-10-20.** The first profile uses the existing device
identity only. It can store a display name and show the device's progress,
but it is not an authenticated account, public profile, or cross-device sync.
Do not expose device profile data to other users. Complete the authentication
choice and signed-in device-adoption flow before offering account recovery,
public identity, or multi-device data access.

---

## 7. shiksha-dev is a source to harvest, not a database to sync with — 2026-10-18

Three stores now exist: the local bank JSON, the Oracle VM's `mpsc`, and
`mpsc_study` on the old shiksha-dev droplet (140,552 questions, 26,490 of
them absent from our bank). The instinct is to keep all three in sync. That
is a triangle, and triangles do not converge: when two corners edit the same
question there is no rule for which wins, and the result is the local/prod
divergence that has already cost time on another project — with an extra
corner.

The topology is a **line**:

```
shiksha-dev  ──import──▶  local bank JSON  ──sync-bank.sh──▶  Oracle VM
 (archive)                 (source of truth)                  (derived)
```

Exactly one authority at each step. Nothing is ever written back to
shiksha-dev, and nothing is written into the VM except by `sync-bank.sh`.

**Why the old server can be demoted to an archive:** it has no users. Its
nginx log is 113 distinct IPs of vulnerability scanners (`wp_filemanager.php`,
`opsh.php` and friends — all harmless, the box has no PHP installed at all).
Its newest data is ~11 days old and was written by us, not by learners. It is
a working box, not a production service.

**Import rules, which are not optional:**

- Its answers arrive as `inferred` at most. `mpsc_study.questions` has no
  `answer_source`; 64,706 rows carry an `answer_index` with no provenance,
  and `verified_by`/`key_disputed` are empty on every row. Importing those as
  `official` would inflate `v_scorable` from 12,319 genuinely keyed questions
  to tens of thousands of unprovenanced ones and destroy the single guarantee
  the product rests on.
- Its `subject` is not an improvement: 138,355 of 140,552 rows are the
  placeholder `'gk'` — 98%, against our 90%.
- Explanations are the clearest win: 70,839 of them, against roughly 18 in
  our bank.

Note `api.map.hawayu.in` still resolves to the old droplet. Consolidating or
retiring that subdomain is a separate decision from the data.

---

## 8. Brand vermilion split and brightened — 2026-10-18 (superseded by design palette restoration)

The handoff's brand vermilion `#C0462C` sat **RGB-distance 23** from the
wrong-answer state `#B0412A`. They are, to a user, the same colour — in a
system whose central rule is *"a colour names an area, never a state"*. Every
other pair in the palette is separated by 73–96.

Vermilion is now `{ DEFAULT: '#D9461C', dark: '#962F15' }`:

- **DEFAULT `#D9461C`** is the mark. Distance to the wrong-state is now 60,
  and saturation rises 0.77 → 0.87. Contrast on paper is 3.78 — above the
  3.0 floor for graphical objects, which is all a mark needs.
- **dark `#962F15`** is for text, at 6.75 contrast. The split exists because
  the prototype uses vermilion as `color:` in several places and the old
  single value was already at 4.41 — under AA for body text. Every area
  colour already carries this mid/dark split; vermilion should have too.

**On the saturation increase.** The user reports feeling more engaged by
vivid colour, and that is measurable rather than taste: Valdez & Mehrabian
(1994) derive `Arousal = −0.31·Brightness + 0.60·Saturation`, making
saturation the dominant term, and studies of learning environments find
reading comprehension higher under vivid than pale colour, with the proposed
mechanism being arousal moving toward optimum on *difficult* reading.

The limit is Yerkes–Dodson: arousal and performance are curvilinear, so more
is not monotonically better, and a learner sits with this for hours. Hence
the shape — **calm reading surface, vivid accents.** The warm `#F4EFE4`
paper and ink body text stay exactly as they are; only marks and accents get
the extra chroma. Do not raise saturation on the reading surface itself.

## 9. Keep taxonomy-v2 claims separate from legacy bank columns — 2026-10-19

The local bank now carries taxonomy-v2 classifications with provenance and
review status. They do not overwrite the legacy `subject`/`topic` columns:
those fields have different meanings and the live sync contract still owns
them. Migration `0008_question_taxonomy.sql` stores the selected classification
path, labels, source, status, confidence, and evidence in a bank-owned table.

Learner-facing bank filters, chips, and taxonomy-backed collection queries use
only `approved` rows. Pending and rejected claims remain in the database for
audit but cannot shape scored exams. The bank sync owns this table; attempts,
accounts, reports, and other server-owned records are outside this path.

## 10. Modules browse source papers; attempts score canonical questions — 2026-10-20

An exam module is a versioned `collection` over the canonical bank. Its
`collection_papers` manifest provides the paper viewer and records whether a
paper can be browsed, practised, or used for a timed verified-key test. A
viewer reads `appearances` in printed order, including that printing's option
order. A timed session freezes those options and appearance references in
`mock_session_questions`, but scoring still compares the learner's chosen
option text with the canonical answer text. That keeps paper fidelity without
creating a second answer bank.

Paper rules have an explicit provenance field. Until official instructions
are entered, the UI describes tests as verified-key tests using platform
defaults; it does not imply a reconstructed paper is a fully scored official
simulation. Papers with fewer than 20 verified-key questions remain browseable
but cannot launch the timed test.

## 11. Separate exams from the study library — 2026-10-21

The Exams catalog lists exam collections and keeps their papers, mock tests,
bookmarks, and exam progress together. The Study Library owns subjects and
learning tools: Arithmetic, Reasoning, General Knowledge, English, Vocabulary,
and other taxonomy-backed subjects. A subject shelf opens its own topic,
paper, and question browser with inline answers and account progress.

Both surfaces query the canonical bank through the API. A learner stays in the
exam or subject workflow while practising; the Bank remains an optional source
archive for cross-exam search and detailed provenance. There is no second
question or answer store in a module. Account progress can be presented by
subject and by exam context while retaining the underlying canonical question
and attempt IDs.

## 12. Mizo and Essay are library workflows — 2026-10-21

The Mizo section uses approved `mizo` classifications for inline practice and
paper browsing. It links to Mizoram General Studies separately, so language and
literature are not conflated with all state GK. The taxonomy endpoint partitions
subject counts by topic; the library sums those rows for its subject totals.

Essay practice uses source appearances marked `essay_kind='essay'`. Learners can
select a printed prompt and save one private draft per canonical question in
`essay_drafts`. Server drafts require an authenticated account; guest drafts
stay in that browser's local storage and can be brought into the account with
an explicit save after sign-in. Descriptive writing has no automatic MCQ score.
Question lists now carry one representative source appearance, chosen from the
requested paper when a paper filter is active. The question card shows that
paper and its PDF link without a trip through the Bank detail page; the detail
page remains available for every appearance and full provenance.

## 13. Bank contribution publication and original mock results — 2026-10-21

A cookie-authenticated contribution is a proposal, never a direct bank edit. Explicit subject-scoped grants authorize review and publication; votes and paid plans do not. High-impact edits require two independent reviews. Accepted revisions carry baseline/source hashes into a durable export; the trusted workstation worker shares the bank writer lock, performs an atomic backed-up local JSON update, executes the existing sync, verifies live fields and acknowledges exactly once. Appending publication credit after live verification keeps review decisions and popularity separate from earned credit. A compensating reviewed revision reverses a correction and its credit without erasing history.

Original community MCQs receive stable source appearance IDs, community paper attribution and derived provenance. They are practiced on their own community surface and excluded from official exam candidate pools. Structural taxonomy changes, source ingestion and key registration remain trusted operator workflows.

New mocks now freeze their question content/options/key/provenance in immutable server-side snapshots at start, retaining original-result consistency if the bank changes before submission. Existing historical sessions cannot be reconstructed honestly and retain a fallback. A later adjusted assessment is separate work, not a reason to silently mutate the original result. The full enterprise release gates remain partially verified; see review-system/ACCEPTANCE.md.


## 14. Adjustments append to original scores — 2026-10-21

Original attempts/mock results are historical records. A changed answer or source creates an idempotent assessment carrying its own policy/input fingerprint and provenance breakdown. Content or presentation changes that cannot be safely mapped exclude the question from the adjusted denominator. Missing legacy snapshots cannot establish historical correctness and are excluded rather than reconstructed. Strict official/key scores remain separate from reviewed derived estimates. A derived label alone does not prove independent review: new timed estimates require a matching published reviewed receipt. Original and adjusted result routes both enforce overlapping-active-mock restrictions.

Reassessment uses bounded durable jobs, distinct per-new-record jobs and source-context revisions. Starting another attempt must not restart every historical scan; shared canonical jobs must not be locked in opposite orders by simultaneous submissions. Semantic score versions preserve A→B→A history while repeat processing of identical inputs is idempotent. Failed batches stop after five attempts and need an audited owner retry.

## 15. Staff MFA independent of the deferred mail provider — 2026-10-21

The user deferred selecting an email provider. TOTP and recovery codes therefore provide additional staff authentication without inventing email verification/recovery. Authenticator seeds use authenticated encryption bound to the user ID; recovery codes are random, hashed, one-use values. Enrollment requires a recent login and current password; replacing an enabled authenticator additionally requires a recently verified existing factor/recovery code. Codes cannot be replayed under concurrent requests. Enrollment and disabling revoke other sessions. Staff mutations require verification within fifteen minutes, and staff cannot disable MFA while holding a review grant.

The production encryption key is generated on the server and stored only in root-only /etc/mpsc/mfa.env, loaded by an app-specific systemd drop-in. It must be preserved with encrypted operational backups; database-only restore is insufficient to decrypt seeds. No owner seed or password was chosen by the implementation. A lost factor uses a saved recovery code; loss of both factors has no automatic email bypass. Legacy bearer-token moderation remains a separate operator mechanism and is not claimed to have account MFA.


## 16. XP, spendable points and paid access remain separate — 2026-10-21

Learning XP measures activity and drives levels/opt-in boards; net reward points buy enabled benefits. Spending cannot lower leaderboard rank. Existing contribution reputation stays independently visible, while new publication credit/reversal events generate traceable XP/points. A single immutable ledger, unique canonical claim and per-user lock bind practice/mock awards to server-validated verified-key activity; guests, repeats and unverified/late work do not pay. Shared daily budget is reserved for future games, which still require their own server-owned result proof.

Pro rewards are immutable dated entitlements, never mutations of Razorpay subscription/payment records. Central effective-access reads expire them by date. Trial/reward time queues; active paid subscriptions must finish before redemption. Catalog changes are owner-only, versioned and audited. Default1000points/7days is provisional and disabled pending launch review. No historical bulk awards or real dummy redemptions. See LEARNING-REWARDS.md for remaining abuse/game/payment scheduling limits.


## 2026-10-21 — CMS boundaries

Reuse materials and material_votes; immutable revision pointer publication prevents draft leakage. Typed React blocks replace arbitrary HTML. Pro uses account_has_pro, paid-preview never implies purchase entitlement. Helpful votes are discovery only; independently reviewed first publication earns20XP+5points max once/day, archive compensates and restore does not re-award. Adapt Shikshacom composition patterns to this stack; individual paid sales remain a separate future verified entitlement/payment system. See CONTENT-STUDIO.md.


## 2026-10-22 — Contextual material discovery

Reuse the CMS catalog and approved published-revision metadata for all discovery surfaces. Exact exam/subject relations define relevance; no title matching or irrelevant fallback. Rank the bounded preview by helpful votes with existing date/ID tie-breaks. No new recommendation store, counters, reward rules or bank requests. Shared cards keep demo/member access labels consistent; empty contexts invite an accurately prefilled draft.


## 2026-10-22 — Creator consent and follow graph

Public creator identity is separate, opt-in and private by default. Reuse published material revisions; exact following membership filters the existing metadata catalog. Public follower count is aggregate, no follower identity list. Hiding profile pauses its Following presence without withdrawing deliberately public publications. Blocks atomically remove both-direction follows and filter creator/material routes; signed-out public access and unrelated rankings/discussions are explicitly outside this initial block scope. No relationship activity pays points. Short graph mutations use one advisory lock to prevent privacy/block/follow races; benchmark before scaling.


## 2026-10-22 — Publishing work is a derived queue

Combine pending work through source-table queries, not a new mutable task status store. Owner-only unification preserves separate scoped reviewer permissions. Explicit static priority rules support ordering without adjudicating reports. Material differences use immutable revisions and stable block IDs; comparison does not change the version submitted for approval. Latest decision feedback is independent of a bounded autosave history, indexed by material/event ID. Retain existing publication pointer/quorum/MFA/reward rules.


## 2026-10-23 — Preserve module claims as immutable evidence

Use canonical bank identities with strict Unicode/whitespace stem and ordered-option matching, preserving punctuation/operators. Keep old punctuation-stripped crosswalk matches as historical candidates. Identity is not answer correctness; no module answer is automatically promoted. Source hashes, original claims and reviewed packets are immutable and independently re-openable from contribution review. Import only audit tables; normal correction quorum/official-key mapping/publication rules apply. Operator-only bounded CLI with bank-hash guard, transactional replay and append-only audit avoids an upload/parser surface in the web app. Mutable triage uses versioned locks, not a fabricated answer-resolution status.


## 2026-10-23 — Research is preparation, not an approval

Deduplicate answer recommendations by canonical bank appearance while preserving all module references. Exact stem/options equivalence does not establish paper identity. Preparation binds source manifests, bank/identity/answer/provenance/PDF hashes and validates normal typed payloads; unknowns stay explicit and defects never invent an answer index. Primary references support derived answers only; archived provisional-key inspection does not claim a final key. New immutable runs attach research to historical comparisons, keeping original runs and zero automated contribution/triage/publication side effects.


## 2026-10-23 — No difficulty feature

Explicit user decision supersedes earlier prototype/roadmap references: no difficulty labels, filters, scoring or authoring. Remove current controls and reject new writes. Preserve legacy storage and immutable payload parsing for historical integrity and replay compatibility; API compatibility property is deprecated. Do not replace retired author labels with inferred model difficulty.


## 2026-10-23 — Prepared research creates a normal draft

Load authoritative prepared payload from immutable server-side packet, verify its bank/context and exact candidate, then create a normal actor-owned draft. Deduplicate by actor+prepared proposal/payload across module appearances and retries. Preserve original evidence, attach current intake association and record one origin event. Existing decisions/MFA/quorum/publishing remain; do not submit or approve automatically. Editor retains every secondary citation across later saves.

## 2026-10-23 — Answer layout is a reading preference

A/B then C/D row order is stable. Default two columns above640px, one column below; user can choose a remembered List layout for long answers. Preference is browser-local with no answer mapping or scoring mutation. Reuse one shared component across module/paper/practice/mock so visual positions do not change unpredictably. Preserve warm product theme and adopt clearer letter/state cues from legacy modules, not their entire global theme. No claim that layout alone improves measured retention.


## 2026-10-23 — One discussion per canonical question

Use existing posts/replies/votes/conduct-moderation records as a shared canonical-question timeline. Module/paper context is verified metadata on the post, not another copy of its question or a separate feed discussion. Published top-level topics are projected into the existing feed under the same answer/block/mock gates. For uncheckable/descriptive questions, explicit disclosure opens discussion without inventing a practice attempt. Accepted replies/helpful votes indicate community feedback and do not change bank answers or earn points. A published discussion can be cited in an ordinary correction draft; author choice, independent review and bank publication retain authority.

First three approved posts require moderation. Post content/references remain immutable; author withdrawal is recoverable moderation state rather than deletion. Reuse existing owner session/MFA, conduct reporting, sanctions and creator blocks, extending the latter to question discussions. Transactional generic notifications link back to a gated thread. No websocket, second content store, source-fetch service or automatic answer promotion is needed for this scope.


## 2026-10-23 — Private Study Desk rollout

User chose private invitations with discovery/classes off while verification delivery is deferred. Deliver direct room membership for exact registered handles with seven-day recipient-bound invitations and a locked six-seat cap; no email directory or public join. Pro creates; invited learners join free. Personal account documents use versioned compare-and-swap, explicit guest import and account-bound saves. Individual attempts stay in the bank engine; shared resources reference canonical IDs and never copy keys or mint rewards. Progress, deliberate mistakes and focus state are separate opt-ins, off initially. New members see existing resources and only post-join chat; removal revokes access. Blocking hides content and cancels pending invitations without silently changing shared membership.

Use existing session/CSRF/rate limits and an additive migration. Moderators see exact reported snapshots only, never a private-desk browser, and cannot decide reports on their own content. Bounded retention removes closed chat/resources after30days and redacts resolved evidence after180days; open reports remain. Private feature flag can stop new sharing/edits while retaining safety, exits and personal work. No websocket is needed for six-seat desks; visible-only30-second polling is sufficient for the current private release. Capacity under public load and full account erasure remain unverified/not delivered.


## 2026-10-23 — Final-key compensation is not an answer letter

The verified2025final key supersedes provisional cells for the audited paper/booklets. Preserve Compensated explicitly in source transcription; never infer a letter from the old provisional key or a model answer. Prepare the existing unresolved-source exclusion with a clear compensation note, preserving paper visibility and history, for ordinary independent publication. Do not claim to reproduce official universal compensation marks. Numeric agreement with a key is only a comparison until source identity/options are checked. Final-key document registration is scoped to exact paper IDs; pending corrections cannot bypass account author identity, quorum, stale baselines or the local-bank publication worker.

## 2026-10-23 — Avatar identity is a curated account cosmetic

Use the existing v3 illustrated avatar and launch-mode Customize/Inventory. A server-owned JSON catalog controls all legal values and level requirements; no arbitrary URLs, uploads, raw SVG or client ownership claims. Existing users retain initials until explicit Save. Save uses account binding, a user-row lock and expected version; stale different looks cannot overwrite newer choices. Claimed level rewards stay owned after XP reversal without changing reward balances or restored credit. Cosmetic display inherits each existing identity's audience and block gate; no avatar lookup directory or new public profile visibility. Reuse one SVG renderer with unique clip IDs, and project config through existing list queries. Shop/badge/paid flows remain separate rather than inventing an economy.

## Question discovery uses the existing thread — 2026-10-23

User approved a clearer question entry and unified discussions. Keep /bank/:id as the permanent question page; rename the card action Open question and lower its emphasis. The question page expands discussion immediately behind the existing disclosure gate. Community Questions & Doubts discovers the same posts rather than creating another reply store. Keep community-authored MCQ practice distinct. Unanswered means a doubt with no published reply visible to the viewer; hidden, pending, obsolete and blocked replies do not disclose themselves through this filter. All topic queries retain question-answer/active-mock gates. Suggest correction remains a separate reviewed bank-change workflow; no helpful-vote points or automatic answer publication.

## Calendar notices and reminder authority — 2026-10-23

User approved the calendar/official-notice next step and explicitly allowed reuse of work-folder code. Adapt Shikshacom's calendar grid and notice publishing patterns, preserving this app's v3 design and session/owner permissions. One versioned event store powers calendar, notices, countdown and inbox links. Existing exam bookmarks are follows; individual saved notices cover unmatched departmental examinations. Dates come only from explicitly verified official sources. Source homepage listings remain labelled with exact title/reference, observed verification date and unstated-time limitations. No automatic fuzzy collection mapping. Initial technical import uses null actors plus evidence-hash history rather than owner impersonation. Imports never overwrite a staff revision. Notification delivery is optional in-app only; current email-provider deferral persists. Exported all-day calendar copies are explicit snapshots, not subscriptions. Staff publish corrections/withdrawals with a new immutable version; a published entry cannot silently return to draft.

## 2026-10-23 — Durable games and audience-aware search

Use PostgreSQL snapshots, row locks and a supervised clock worker with bounded visible polling. This reuses existing deployment and survives reconnect/restart without introducing Redis. Reconsider transport after measured concurrency. Games share the existing canonical first-answer claims and 300 XP study budget; prototype sample XP, gems and cup coins do not define an implemented currency economy. Public cup results require reversible opt-in. Search each existing product audience rather than building a second public index of private content. Listings are existing paid previews; private desk discovery remains off. See GAMES-SEARCH.md for scope and limits.

## 2026-10-23 — Multiple reviewed paths, direct subject shelves

Keep the original selected primary classification and add explicit bank-owned relatedClassifications. Existing parked alternative claims are not approved related paths. Share approved paths through a database view for filtering while preserving primary subject progress totals and source provenance. Direct shelves are saved queries over taxonomy paths, enabling Geography/History discovery without another GS navigation layer or question copies. Use existing independently reviewed publication, local JSON authority and transactional sync for every link change. Keep author note tags distinct from reviewed question taxonomy. See LIBRARY-TOPICS.md for contracts and current coverage limits.

### 2026-10-23 — Explicit exam-source scope at launch
User confirmed MPSC plus existing Mizoram recruitment papers. Scope belongs to paper/collection metadata, independently of subject geography and canonical identity. Launch views derive distinct canonical IDs from scoped appearances; retain global views for later expansion. No production import default: unassigned papers do not silently enter launch pools. Legacy bank sync retains registered scopes, new community publications explicitly opt into Mizoram. Do not delete historical learning records when changing discovery scope. Games exposes only own unfinished mock metadata and uses existing runner/submission flow.

### 2026-10-24 — All exams opt-in and private Inbox
User clarified that All must include future outside/unassigned question sources. Make All an explicit typed request context, preserve the launch default and global views; do not auto-enrol new imports or widen competitive Games. Use a document-stable preference plus URL override/reload to prevent stale pool responses.

Inbox is one account-owned notification store plus existing accepted private desk channels. No arbitrary DMs or new chat identity system. Quiet preferences affect future notices and badge eligibility, keeping history visible. Header count includes unread conversations so hourly aggregated desk notices cannot hide later new messages. Self-service notices/read cursors do not require bank-staff MFA; all existing review/admin MFA is retained. No email/push or quiet-hour promises while providers are deferred.

## 24 October 2026 — Automatic recognition evidence; SPA focus

Vocabulary uses server-checked first choices and spaced, due reviews instead of mandatory self-confidence ratings. Correctness, source snapshot, account state and retry receipt commit atomically. No speed-derived confidence or runtime AI is needed. Original option order prevents changing positional/letter-referenced questions. Source-equivalent printings share semantic canonical progress across scope; historical answers remain evidence, not word-mastery claims. Old unscoped browser ratings cannot establish which account answered correctly and remain untouched. UI session size is convenience, not a reward/security boundary; server limits new canonical items to ten per IST day.

Replace full-document exam focus reloads with an observable per-document scope store and keyed scoped learner routes. Preserve the header/account and unscoped drafts while clearing old learner result state; explicit URL scope changes synchronize locally, cross-tab preference writes do not silently switch the active pool. Mock focus is pinned.

##24October — Final module presentation uses exact source identity
Final generated Group B/clerical modules are the presentation reference, while the local bank remains the content authority. Restore only source-hashed, uniquely numbered, equivalent stem/ordered-option/type matches. Ambiguous/reworded items stay in evidence. Formatting is not permission to change a key or classification. Mock review uses frozen source context; no current metadata is fabricated for legacy snapshots. Shared underscore blanks are ruled lines distinct from underline emphasis, and reading passages open by default.

##24October — Provenance is separate from review eligibility
A derived label is not proof of independent review. Learner reviewed_derived status comes from the existing applied/current-content publication view, never browser confidence or vote counts. A community solution can support a labelled practice estimate without an official key while remaining derived. Reuse normal answer proposals and publication ledger; do not pay for agreement or submission. No-recorded-key wording must not imply an exhaustive search proved no key exists.

## 2026-10-24 — Stable workspaces and public catalog cache

Community tabs filter one persistent layout; full content readers retain separate URLs. URL filters use replacement history and material readers remember their Community entry tab. Shared shell state no longer reloads private progress/session data on every route. Routes and exam CSS load on demand, with conservative code-only intent prefetch. Only explicitly public catalog metadata uses a scoped per-document 30-second cache and process-local 10-second server cache. Successful catalog/admin writes invalidate server entries; scoring and private learner content are never cached through this layer. Cold SQL remains a separate optimization target; no load-capacity claim follows from warm timings.

## 2026-10-24 — Four learner answer statuses

Collapse six provenance labels into Official key, Verified solution, Needs review and Unsolved. Preserve stored source types and current reviewed-derived receipt; do not migrate or promote bank answers. Verified solution requires the existing independently reviewed, applied, current-content publication. It stays unofficial and separate from strict scores. Disputed answers and duplicate/unresolved source defects override trusted-looking badges. Descriptive items show Written question. Official final/provisional is document metadata and must not be inferred from either a badge or popularity. Source filters remain explicitly separated as expandable source details. Legacy API verified retains its official/key meaning.

## 2026-10-24 — Server inventory, local canonical bank

Admin exam/expected-paper associations are operational metadata with versioned audited edits and read-only local export, separate from learner collections and canonical questions. Import official listing snapshots atomically/idempotently; exact historical URL associations are evidence, not PDF-content verification. Preserve manual changes on replay and flag unmatched entries without declaring PDFs missing. Record source-context fingerprints so edits invalidate prior checks. Use one server status view for admin filters and learner metadata, preserving reviewed publication requirements and existing scoring policy. Registered key/reference PDFs remain outside the static web root and require staff/mock-safe access. See ADMIN-EXAM-INVENTORY.md.

## 2026-10-24 — Connect workflow state without duplicating canonical authority

Extend expected-paper inventory with an audited evidence-backed intake state; Published means imported paper and completed bank sync, not verified answers. Use scoped computed quality filters rather than direct mass answer changes. Reuse existing mock/vocabulary/focus/task records, adding only a safe versioned practice checkpoint. Daily revision plans contain IDs and completion receipts backed by actual later attempts; neither checkboxes nor duplicate sessions award extra credit. Correction events fan out through existing durable Inbox and reassessment supervision, with no answer text in notices and no rewriting original results. Source PDFs and canonical content keep their established authority split. Details and boundaries in LEARNING-WORKFLOWS.md.


## 2026-10-24 — Explicit administrative answer authority

The user authorized direct official/corrected decisions by administrators. Owner/publisher (subject scoped, registered session, MFA on writes) may use the dedicated answer-decision endpoint. This does not simulate or waive community peer reviews: community proposals retain independent quorum. Immutable admin attestations bind actor, rationale, source snapshot and exact payload; eligibility rechecks the actor's current publishing grant. Official requires registered mapped key evidence; Verified is an administrator-checked unofficial worked solution, never represented as an official key. Needs review is a scoring hold; Unsolved removes the answer through canonical publication. Administrative maintenance receives no points. Existing source text/image repairs still follow their normal workflow.


## 2026-10-24 — Explicit owner-delegated source restoration

The user instructed completion/publication of the prepared LDC source repairs. A trusted SSH maintenance command may adjudicate the exact owner-authored source proposals with registered paper/hash evidence and explicit delegation, without inventing peer reviewers or authentication sessions. An immutable operator event binds owner authorization, revision, payload and baseline. Community HTTP proposal quorum is unchanged. Revocation and changed-content checks invalidate maintenance eligibility. Administrative source/answer work earns no contribution credit. See BANK-MAINTENANCE.md for the command and receipt reconciliation rules.


## 2026-10-25 — Bounded staff bank maintenance

Ordinary community proposals retain the 30/day limit. Authorized staff maintenance permits 500/day only after checking active owner/publisher role in the target subject; the internal admin flag alone grants nothing. Trusted SSH source intake requires an existing active owner, explicit authorization and a source-maintenance proposal kind. It creates an audited proposal, not a peer approval or publication. Existing target/baseline/evidence guards and normal HTTP authentication remain enforced. Owner repairs award no fabricated contribution credits. Public bank CSV staging directories require 0755 and CSVs 0644 for PostgreSQL traversal even under umask 077.


## 2026-10-25 — One administrative decision workflow

Reuse the existing direct answer-decision API, permission grants and canonical publication worker. Owner/admin access and explicit reviewer permission may coexist; reviewer alone does not gain publication authority or self-approve a community contribution. The user explicitly requested these grants for their named existing account. A verified explanation may also be the recorded administrative reason; independent community quorum remains separate. Save & next is navigation after a successful API response, never proof of publication. Inline status follows the real receipt, with bounded visibility-aware polling. Current-page order is retained until manual refresh and is not a frozen batch or an atomic bulk edit.

## 2026-10-25 — Group B umbrella and evidence-based model review

The user clarified that the Group B Non-Gazetted study umbrella must include UDC and Assistant Grade. Publish the union of explicit existing paper identities, keep their dedicated exam pages and preserve historical source titles. Collection membership is a study/navigation choice, not proof of a post's statutory category. The current union is 97 papers: 37 Combined Group B sources plus 60 distinct UDC/Assistant sources. Progress and corrections remain tied to existing question identities.

Source intake and answer adjudication remain separate. OCR/geometry restores source questions, written tasks, page images and instructions; it does not turn imported keys into Verified answers. A truncated official source stays visibly incomplete rather than receiving invented missing numbers. Written tasks appear in paper view and receive no MCQ answer index.

Use Luna for bounded, source-backed first review and escalate ambiguity/conflicts to Sol 6.1; audit the resulting evidence before an owner-delegated administrative decision. The pilot demonstrates the boundary: Luna misread Q69's repeated article, which the stronger source adjudication corrected. Model agreement or model confidence alone is insufficient for Verified. Mizo and disputed wording need appropriate language/source evidence. “Verified solution · unofficial” remains distinct from an authority-issued key, and administrative repairs award no community review credits.

Current-affairs learning notes preserve the historical question/answer and show their own explicit checking date and official source link. Do not silently replace old answers with present-day facts. English grammar contexts must carry subject plus topic to avoid treating a sentence containing “last year” as current affairs. Dated notes may need future review; they are not live fact guarantees.

## 2026-10-25 — Explicit game scope and player readiness

Games now resolve exam papers, optional exam sections and named areas into a frozen selection context. The strict shared predicate powers counts, draws and completion revalidation. Exclusions veto every approved related path; unknown classification is excluded when exclusions are active. A current pool revision binds confirmation and draw. Random matching uses the exact context hash, including rules and source pool, and never widens silently. Private invitations preview scope before joining; new multiplayer rooms require readiness from all present players, and parties additionally require the host to start. Existing null-context rooms keep their old lifecycle.

Recent-practice suggestions use distinct attempted canonical questions over 90 days, capped at 100; at least three matching questions are required. This is familiarity evidence, not mastery. Only confirmed non-cup choices are remembered per account. Fixed mixed weekly cups disclose that personal exclusions do not apply. Official/key game eligibility remains unchanged; newly verified unofficial computer solutions improve practice only. Curated topic choices expose understandable names, including Arithmetic (Numerical Ability), without asking students to understand taxonomy paths.

Do not reintroduce the redundant launch corpus DISTINCT into game candidate queries: the displayed appearance already enforces the Mizoram scope. It caused >45-second scans. Correlated anti joins over the taxonomy union also caused repeated scans; hashed NOT IN sets preserve exclusion semantics with subsecond bounded checks.


## 2026-10-26 — Bounded clerical verification and source fidelity

Owner-delegated bulk maintenance may group up to100 explicitly reviewed disjoint targets for one bank sync while retaining every immutable manifest, baseline, original-source check, individual receipt and normal acknowledgement. Only trusted SSH maintenance may use this path; no public permission, session or peer-review bypass is introduced. Verified solution remains unofficial; admin maintenance earns no community credits. Prepared journals are replayed as a complete batch, never reconstructed member by member after partial application. Unrelated bank drift or outstanding exports require reconciliation.

Source restoration and answer adjudication remain separate operations. Changing printed choices clears an untrusted mapping before a fresh answer decision. Exact printed typos remain visible and are explained; do not call them OCR errors without inspecting the source. A source category error or multiple genuinely valid English answers is held with a concrete reason rather than certified by majority model agreement. Original duplicate appearances retain their IDs and progress. See reports/clerical-verification-20261025/IMPLEMENTATION.md for operator sequence, evidence and limitations.

## 2026-10-26 — Explicit owner-run maintenance quota exemption

The owner explicitly asked to remove the blocking limit for this clerical review run. Preserve ordinary learner30/day and HTTP staff500/day limits. The trusted SSH command accepts an explicit --quota-exemption-run plus authorization reason; it checks the existing global owner and pins the exception to the exact1–100 canonical targets in that request. The process-local ContextVar is never set by a public route, persisted as an account flag, or enabled by a service environment setting. It vanishes when that command exits. Every newly created contribution records the run, owner authorization, canonical target and observed ordinary daily usage in contribution_events.

This exception changes only quota admission for owner-authorized answer/transcription/source-reference work. Current grants, active-test protections, source/evidence/baseline checks, source/answer separation, unofficial provenance, immutable exports/receipts and serial bank sync remain mandatory. Future use requires explicit owner authorization; the existence of this command is not blanket permission to lift limits on other work. Batch size100 remains bounded to protect transactions and verification time.

## 27 October 2026 — Preserve examiner evidence independently of reviewed working

An official final key is evidence of the examiner's selection, not an independent proof that the printed item or answer is correct. The owner explicitly requested contrast because official keys can contain mistakes. Compare two separate lanes from applied immutable publications, matching the full printed source context. Do not turn an imported/inferred answer or the official key itself into a reviewed solution.

Admin verified mode can now preserve an existing official key while publishing an explanation-only attestation. Its immutable admin metadata and reasoning evidence record the selected solution text; the local JSON's official answer index/source/key reference remain intact. A different solution puts an immediate scoring hold on the canonical question. This reuses the existing publication/JSON-authority workflow and needs no second mutable answer store or migration. Source edits invalidate old comparisons; drafts/reverted publications never appear. Historical official citations and worked reasoning remain separately accessible after subsequent decisions.

The shared comparison is lazy, explicitly reveals answers, is private/no-store and enforces existing mock/game/cup disclosure gates. No attempt, reward, peer vote or user is created by reading it. Original multi-accepted/compensated keys are not forced into a single answer index; that broader scoring support remains separate work. Exact owner-run quota scope includes explanation attestations needed for this review; public quotas and role checks are unchanged.

## Exam topic map follows the exam's papers — 2026-10-28

Subject and topic study under an exam is defined by canonical questions appearing in that exam's browsable listed papers, then grouped through approved taxonomy paths. This keeps an LDC topic drill inside LDC rather than drawing every English or Mathematics question in the bank. Counts use distinct canonical IDs at each level; child counts may overlap where a question has multiple approved paths. Missing topic tags are shown as missing coverage rather than inferred into a syllabus. The route does not change answer provenance or scored-mock eligibility.

## 28 October 2026 — Group B common subjects and technical sources

The owner finalized English/GK/GS as the first Group B learning entry, with
technical papers separate from launch. Implemented `/group-b`, combining both
live Group B groups or selecting one. GK and GS roll up into one virtual
learning subject while stable content taxonomy IDs and original source titles
remain intact. This avoids a destructive retagging migration for a navigation
and selection change. Approved primary content tags select common English
and GK/GS; specialist Science enters common practice only with an explicit
GK/GS source-paper role. Technical practice needs its own exact paper role,
never the complement of common subjects. The versioned manifest currently
covers four common and 25 technical papers. Unknown contexts remain visible
through full archives. Secondary tags continue to serve general Library
cross-topic discovery but cannot promote technical content into this common
feed. Answers save against actual source collections; the virtual shared
entry uses global continuation and real-collection personal history. Gazetted
departmental coverage is disclosed rather than presented as complete direct
recruitment preparation. No bank edits or schema migration were required.

## 28 October 2026 — Printed section boundaries for common science

Expanded the common-source manifest to version2026-10-28.2 after reviewing
23 further papers and75 candidate science questions. Mixed GK/arithmetic
papers identify GK as printed questions1-75; source roles now carry optional
question-number bounds. The membership predicate and displayed source
appearance use the same rule, so a Science-tagged speed calculation atQ97
cannot enter common GK/GS through its paper's GK heading.74 questions become
eligible; the arithmetic item remains in full-paper browsing. Unknown/compound
question numbers do not satisfy a bounded role. Two possible existing content
classification defects were recorded for independent review; source-role work
does not silently rewrite approved canonical classifications or answers.

### 28 October 2026 — Original paper labels and learning topics

Source appearances may carry a curated paper_label from inspected covers. Never derive official GK/GS wording from question taxonomy or recruitment name. Card badges prefer the approved topic; GK/GS is the shared fallback for either broad subject. Unreviewed source titles remain absent.

### 28 October 2026 — Audited source identity and virtual GK/GS discovery

Source identity is an operational overlay in bank_paper_identities, separate from bank-authored questions/papers and taxonomy. Global owner/publisher saves require source inspection, version and source-context match; inventory events store before/after. Only matching source references receive public overlay titles/printed years/section names. Printed year is distinct from archive indexing. Existing reviewed manifest labels remain fallback.

GK/GS is a virtual learner subject with shared topic aliases derived from normalized topic labels, counted DISTINCT in SQL. Original registry IDs stay stable for bank publication and historic links. Editors resolve unified choices to existing taxonomy paths; pending claims stay hidden. Shared discovery never certifies an existing classification as correct.

Batch retagging creates ordinary submitted taxonomy contributions in one transaction with per-target baseline hashes and a batch idempotency record. The selected batch supports per-revision review and publication through established endpoints; author self-approval and stale publication remain blocked. Existing staff maintenance budget remains500/day; no new quota exemption. See docs/CLASSIFICATION-AND-PAPER-IDENTITY.md.

### 28 October 2026 — User clarification: UDC has GK, not GS

Keep one shared bank and handle each exam through its own identity and scheme. UDC's knowledge component must be presented as General Knowledge; the virtual GK/GS learning category must not become a purported UDC paper/section title. Preserve verified full mixed-paper wording. Cross-exam learning retains the combined category. Existing verified UDC source labels already comply, but shared collection topic headings still need exam-specific presentation mapping. Save that remaining work explicitly rather than claiming source-label controls implement a full exam scheme.

### 28 October 2026 — Clerical exam presentation and bounded question reads

UDC, LDC and Assistant learning maps name the shared knowledge category General Knowledge. The discovery ID remains `gk-gs`; stored taxonomy and printed source identity remain independent. Question badges use the same exam-aware fallback when there is no narrower approved topic. A shared canonical question's displayed source must belong to the active exam; a newer appearance in a different exam must not replace it. Clerical workspaces link their own English/GK questions and allow switching between UDC, LDC and Assistant.

Profiling traced slow exam reads to per-question JSON paper-list expansion and whole-bank publication/status scans. Materialize each section's paper list once, probe launch/origin eligibility for bounded candidates, reuse selected IDs when loading question details, and compute readiness only for the exam's questions. The indexed readiness CASE follows migration0050 exactly and still delegates independent-review validity to v_reviewed_answer_publications. Synthetic policy parity and production read-only comparisons must preserve counts and eligibility. No materialized entitlement or answer cache was introduced.

The owner explicitly requested unlimited Pro for their named account. Applied active Pro with no plan expiry and an immutable account_security_events entry; no payment subscription exists for that account. Paid checkout and reward redemption mechanisms exist but are currently disabled in production. Manual access changes currently require trusted administration; this session does not add a public grant endpoint.

### 29 October 2026 — Progressive exam practice and focused study controls

Public exam identity has a small /api/collections/{id}/header read with the same public-visibility and exam-scope checks as full metadata. ExamPage can render practice after that validated identity arrives while paper coverage continues loading. Full metadata updates props in the same mounted question browser; retry retains the available header and answer state. Unknown/hidden/out-of-scope exams do not receive a provisional public identity.

Focused study views use a compact hero and omit repeated readiness/journey panels; detailed answer guidance and test actions stay in an accessible disclosure on overview/papers. Subject/topic/search remain primary on desktop and use a compact toggle on phones, with the selected path always visible. Paper/section/pool/status/layout controls stay under More filters. During filter changes, previous questions remain visible but their answer options and handler are disabled until the new request key resolves. Reset preserves the exam and view. Equivalent default query parameters coalesce with prefetch; personalized queues remain uncached.

Collection paper cards and the paper viewer reuse verified source identity headings, while preserving source filename/booklet context and archive year. Platform-default timing/marks remain explicitly labelled. The source-cover audit is evidence for a follow-up, not publication of complete official schemes. Existing tag concerns remain unsubmitted review dockets. Hash navigation waits for lazy content and accounts for the real sticky-header height.

### 29 October 2026 — Bounded clerical taxonomy adjudication

Keep Luna's candidate generation separate from final question-level review. This pass selected120 exact corrections; retained/held82 rather than classifying all clerical content by its paper label. Historical classifier batches omit newer restored records, so a bounded merge must preserve every unselected bank record and global conflict history and refuse unresolved selected ties. The canonical local bank remains the authority and publishes via ordinary sync; this workshop workflow does not invent community approvals. Clerical practice must send the source appearance displayed within its active exam, even without a paper filter, so attempt history preserves that source context.

### 29 October 2026 — Reduce outer margins, preserve text spacing

For the owner's all-pages congestion request, widen shared workspaces1440px and reduce outer gutters rather than tightening internal text/button spacing. Keep narrow reading/form columns bounded. Past-paper lists share one row component across exam modules, keeping short source/booklet identity and actionable nonzero counts visible while full identity and test caveats/actions are disclosed on demand. All original test eligibility, answer provenance and source links remain; this is presentation only.

### 29 October 2026 — Owner correction: boxes and uncapped outer shell

The owner prefers boxed paper cards, not full-width rows. Restore the responsive card grid and keep the cleaner content/details disclosure. The1440px cap still produced unwanted outer margins on wider monitors; shared workspaces now use100% available width, with16px desktop/12px mobile gutters. This supersedes the earlier row layout and1440px outer-shell decision. Narrow prose/form components retain their own reading limits.

### 29 October 2026 — Clerical GK includes a Science discovery branch

Assistant/UDC/LDC GK discovery includes canonical Science and the existing Science in the news topic. Keep original Science paths for deep study and compatible links; add virtual GK → Science → canonical topic branches rather than writing duplicate bank tags. Same-path projection drives map and question filtering with DISTINCT counts. Source paper labels and Group B technical/common boundaries remain independent. This is an exam-specific presentation rule, not certification of legacy tags.

### 29 October 2026 — Owner clarification: MPSC-only current product

Focus current learner experience, homepage positioning and preparation upgrades on MPSC (Mizoram Public Service Commission). Exam selection means choosing within MPSC. Expansion to other exam systems is deferred. Preserve reusable bank and exam configuration architecture for that future expansion; do not expose broader choices merely because the backend supports them. No content deletion or access-policy changes implied.

### 29 October 2026 — Atlas placement and restoration

Use Interactive Atlas as the name of the restored Leaflet map tool. Home is Library → Modules & tools, route /atlas, with contextual subject links. Keep Study Desk/progress identity distinct. Restore original chapter layers with a separate lazy map renderer; bank questions and scoring remain under existing provenance rules. Exclude known outdated legacy administrative boundaries; OSM attribution and illustrative-overlay context remain visible. MPSC focus includes Mizoram, India and relevant world study chapters.

### 29 October 2026 — Protected guest identity and shared account mutation boundary

Replace UUID-based guest ownership/adoption with random server-issued HttpOnly proof and protected guest principals. Legacy unproven device records remain retained; do not attach fresh proof to arbitrary old UUID histories. Transfer is an explicit post-authentication choice, locked and receipted, restricted to learning data. Cookie account mutations share Origin/CSRF guards and expired account writes cannot silently become guest writes. Reset tokens preserve enabled MFA; email delivery is gated off until configured and delivery-tested. Retain current XP economics/levels and opt-in activity ranking. Add immutable answer request receipts, provenance metadata and read-only reconciliation rather than a second award writer or mutable balance. See docs/ACCOUNT-XP-AUTH.md.

### 30 October 2026 — Task-focused admin navigation

Keep stable admin tab IDs while reducing the owner's primary menu to Home, Review answers, Learning tags, Review queue and Papers & exams. Scope the visible primary work to existing permissions; group specialist tools behind More tools on desktop and a labelled section picker on phones. Home provides task entry/counts with diagnostics disclosed on demand; the combined publishing queue mounts only on its own page. Question reports open the inspector directly and resolve through an inline validated form. API roles, MFA, independent review and exact applied-publication requirements remain authoritative. See docs/ADMIN-WORKFLOW.md.

### 31 October 2026 — Source-faithful paper workspace

Use source appearance identity for paper interactions and retain printed options/numbers. Shared learning tags are projected into exam-aware GK labels; Science remains a nested filtering choice for clerical GK. PDF comparison uses recorded page mappings with lazy local PDF.js rendering. Flags/scratchpads are explicitly visit-only until a persistent notes product is implemented. Full-paper loading follows actual appearance batches, not canonical totals.

### 31 October 2026 — MCS paper role is source membership

Collection version2uses separate GS/Aptitude manifests and retains version1. Learning topics filter inside the selected source role; shared canonical categories do not determine which exam paper a question belongs to. MCS shows General Studies and includes Science as a discovery overlay, while clerical GK labels remain unchanged. Recovered third-party PDFs are provisional source resources, never automatically official keys or reviewed explanations. New source records stay outside answer practice/scored modes until adjudication. Table/figure options that cannot be transcribed point explicitly to their source image and carry a source-review flag.

## Explanation availability and dated revision notes — 1 November 2026

Keep question format, answer provenance and explanation status separate. An official key can exist without an explanation, and does not certify any accompanying teaching text. Reuse published reviewed-derived eligibility only for the corresponding unofficial solution's working; unresolved/disputed items remain provisional. Do not invent a separate explanation-review status where no metadata establishes it.

Keep current-affairs revision notes outside canonical answers and scoring. Use a small dated editorial registry with direct sources and review deadlines; constrain historical context to the relevant question/year. Expired notes disclose that rechecking is due, and missing notes explicitly acknowledge that no specific update has been checked. Render answer-bearing notes/references only after answering or explicit revision-context reveal. Existing proposal/publication guards continue to govern bank edits. This avoids both silent historic-answer replacement and the misleading implication that a generic portal link verifies today's fact. See docs/EXPLANATIONS-AND-CURRENT-AFFAIRS.md for the workflow and current limits.

### 1 November 2026 — UDC preparation stays within UDC

The owner confirmed that UDC is a focused preparation destination; students can explicitly move to Group B Non-Gazetted later for broader practice. This supersedes the UDC part of the earlier clerical switcher decision. UDC's overview now has one journey action block, its own approved subject shortcuts and five primary views. Other exams remain in Exams; the broader Group B link sits at the bottom. Shared Assistant/UDC source papers remain legitimate UDC resources. Resume restores an allowlist of study filters and UDC only offers an active timed-session resume for its own collection.

Group the eight exact registered 2025 Assistant/UDC booklet IDs into Paper I and Paper II navigation cards. Require their expected 2025 year and paper role; leave every other identity separate. Differences in historical department/sitting metadata make year-only grouping unsafe. This changes presentation only; all source IDs, questions, keys and scoring rules retain their current identities. Reuse the Prelims series selector with an explicit exam ID. New sitting families need an explicit metadata audit before extending grouping.

### 2 November 2026 — Bounded UDC study sets share the existing attempt engine

The owner approved the second UDC release: 10/20-question sets, saved position, finish summaries and targeted mistake practice. Freeze canonical IDs and source paper IDs at creation using the existing UDC collection/taxonomy/pool filters. Later reads use these exact IDs rather than re-running a shrinking wrong/unseen queue. Current holds and unavailable sources still apply; missing questions retain their slots and can be skipped. A smaller eligible pool produces a visibly smaller set.

Migration 0062 adds session metadata only. Ordinary attempts and immutable practice receipts remain the answer/progress/reward authority. A deterministic session/question receipt key and one shared transaction encompass checking, awarding and updating the session version. Duplicate checks replay; stale-tab navigation fails explicitly. Finished summaries retain original checked feedback, with unofficial-answer counts and a clear distinction from an exam score. Restored checked questions use the attempt's original text/options snapshot. Reveals remain reading, never an attempt or award; finishing reconciles server-recorded reveals even when the acknowledgement was interrupted. Per-question review/active-test guards still apply to saved answer feedback.

Guests use their protected HttpOnly principal; signed-in users use the existing account boundary. Explicit proven-guest transfer adopts session metadata and preserves immutable receipt ownership through its adopted attempt. It also carries answer-view timestamps forward using the later server timestamp, so signing in cannot reset the reading cooldown. Set creation, position and history never grant XP. Completed set summaries and active continuation appear in the existing exam journey, while general UDC progress still derives from attempts.


### 2 November 2026 — Quiet booklet sources and conservative study-series grouping

The owner requested hiding repeated series controls in UDC and MCS Prelims and addressing duplicated study questions. Keep original booklet records and printed-order paper browsing intact. Collapse series selectors into Booklet series & original sources, remove series from grouped-card display titles, move PDF links into Paper details and put per-question source identity behind Source details. Source issues, figures, passages and answer-provenance labels remain visible.

General collection question queues for UDC/combined-prelims collapse only identical text copies within the same filename family, year and paper role. Require exact case-sensitive question, ordered options, canonical and source context/markup, answer text/source, explanation, status/defect/dispute state and derived-review status. Any recorded figure or diagram prevents collapse. This is query presentation, not canonical deduplication; no IDs, source counts, attempts, credits or saved-set contents change. A selected paper bypasses grouping and keeps its original questions. Other modules and timed papers are unchanged.

Apply subject/source/pool filters before grouping and learner-status filters afterwards. Prefer the current learner's most recently attempted eligible copy, otherwise the lowest ID. This preserves usable legacy feedback and prevents a parallel booklet copy resurfacing in the same unseen queue. Different solutions, reordered options, OCR differences and figures deliberately remain separate until supported review. This does not enable the general repeats filter or claim complete deduplication. New UDC sets use the shared queue; already frozen sets are preserved.


### 2 November 2026 — Verify admin publication readback and preserve original study feedback

The owner requested the remaining UDC readiness work and a fresh audit of fast admin editing/confirmation and later mismatches. Keep existing source/issue filters and Save & next; do not introduce blanket verification or relax evidence, role, source, quota or stale-publication guards. Expand publisher verification from a few canonical fields to every learner field represented in the primary receipt, including provenance/key reference, source context and markup. Secondary source records do not overwrite shared primary content.

Add a private read-only post-publication comparison endpoint, using a repeatable-read snapshot, original/current subject grants and active-test protection. Return only mismatch field names. Distinguish a subsequent legitimate publication from unexplained drift. The admin progress card rechecks after application and can recheck again from contribution history. This verifies publication consistency, not the factual truth of a reviewer’s conclusion. No approval or correction is created by a recheck.

Current UDC short sets send a hash of the displayed answer-free presentation. Before a new check, hold shared source/canonical locks and reject a changed presentation without creating an attempt/reward. Keep the field optional for existing API clients; older clients and unlimited study routes retain legacy behavior and are not represented as covered by this gate. New attempts snapshot the original answer-status/review context. Saved sets preserve original feedback/totals and explicitly flag later question/key/context/figure/review changes. Older snapshots must not inherit a later derived-review badge. Original attempts/mock results/credits are not rewritten; existing adjusted assessments remain separate.

Keep UDC coverage claims tied to actual archive counts. Main subject shortcuts prioritise five direct-recruitment areas; historical extras remain accessible. Explicitly distinguish written preparation from MCQ sets and keep default timed rules labelled practice. The current syllabus redirect could not be fetched; do not claim full current syllabus or authentic paper-rule verification. The offline backlog/source audit prepares evidence only and creates no bank changes. Release gates remain pending restricted server/database access.

### 2 November — Feed begins with the learner's next action

The owner requested a student-focused feed redesign. The feed now offers active timed practice first, then a real saved learning checkpoint, otherwise explicit exam choice. Resume links retain the original paper/section/answer mode; the server resume service remains authoritative. Do not label the first public collection as the learner's chosen exam. Community discovery, followed creators, community MCQs, discussions and materials remain available below study actions. Remove duplicate rails, placeholder social previews and games promotions from the feed; retain those destinations elsewhere. Progress is labelled all-time and is not represented as exam readiness. This is a frontend composition change, with no change to question eligibility or answer visibility.

### 2 November — Non-Gazetted hub and focused exam routes

The owner clarified the broader Group B Non-Gazetted module: users may want only English, GK and Current Affairs. Default `/group-b` to NG, preserving explicit combined and Gazetted query selections. Use General Knowledge for NG learning labels; Current Affairs is a separate entry into an actual approved GK topic. Keep canonical taxonomy/source titles unchanged. The official July 2024 NG scheme supports GK terminology; a newer May 2025 notice exists but its PDF returned403, so no new current marks/duration claims are introduced. UDC/LDC/Assistant remain focused routes; preparation overlap does not establish identical syllabus, statutory classification or a complete source union. Existing UDC/Assistant collection membership is preserved, and LDC is linked without silently adding its bank. See docs/GROUP-B-NON-GAZETTED-MODULE.md.

### 2 November — Group B navigation and GK/GS correction

Separate the NG study-home choices from active topic/practice controls. Centralize URL transitions so source changes clear incompatible filters while read/practice changes preserve the selected topic and reset pagination/answer-status. Keep explicit combined/Gazetted links valid. GK remains a discovery label only: the original January2026 Health & Family Welfare NG technical PaperII explicitly says General Studies. This corrects any interpretation of the preceding note as saying GS does not occur in Non-Gazetted examinations. Preserve printed paper titles and existing taxonomy/source roles.


### 2 November — Selectable exam/year archive

The owner now requests an MPSC-style exam/year list with ascending/descending ordering. Add it as an archive presentation, defaulting Group B Past papers to list while retaining the existing card option and other module defaults. Each row retains its exact source paper; do not merge similarly named sittings or booklets. Year and exam-name order is deterministic, unknown years last for date sorts, and URL filters restore the selected view. This is the explicit exception to the earlier card-only preference for paper lists.

Human handoff readiness is distinct from final certification. Report official keys and reviewed unofficial answers separately, include held items in editorial backlog, and require real human attribution for final paper sign-off. Do not count approved taxonomy as answer verification.


### 2 November — Human editorial authority over re-parsed UDC/Prelims content

Freeze the handed-off exact source scope as an integrity baseline, not factual certification. Parser/tooling changes to protected questions, paper/context records or source assets become staged comparisons. A mandatory sync gate catches drift even if a legacy/raw writer bypassed its local hook. Only existing validated immutable publication manifests advance bounded targets, with a journal durable before replacement and exact replay after interruption. Do not auto-rebaseline, silently add sources, merge source IDs or grant parser results human/official provenance.

Introduce distinct source-editor assignments rather than global reviewer roles. Bind invitations to the owner-designated email plus an explicitly activated existing account ID, with frozen paper membership and revocation. Do not auto-claim by email or create passwords. Source inspection and attributed append-only checks are allowed; ordinary contributions still require independent approval/publication. A checked source is a human inspection record, not an official-key or solution promotion. Reject stale ordinary proposal/check forms using source versions before saving. Owner retains activation/publishing control; historical checks remain earlier checks when content changes.

### 2 November — Dated connections are independently published editorial context

Implement the manual first version of Current Affairs Connections as server-owned entity/revision/source-link records. Historical bank content and scoring retain their canonical authority. Exact assigned-source editors can author context; only an independent owner publishes it. Unknown time references remain explicit; precise entity/jurisdiction/fact-type identity connects GS/GK questions without rewriting source labels or taxonomy. No automatic model inference or officeholder update is trusted.

Use transaction-version source tokens for short-lived authoring freshness and separate semantic evidence fingerprints for durable published connections. A byte-identical bank upsert must not remove every link; actual source/key/context changes withhold stale context. New endpoint access blocks the entire feature during active assessments, since entity facts can disclose another question's answer even when IDs differ. Explicit viewing applies existing review cooldowns to all linked canonical IDs. Existing public static notes and externally reachable PDFs are not represented as covered by these new server controls.

### 2 November — General changing facts and comparable measurement series

The election-office example does not define the current-affairs product scope. Add explicit fact categories plus immutable comparison metadata for rankings/statistics and separate reporting periods/editions per fact. Commodity, exporter/producer metric, value/volume basis, unit/currency, compared population, source series and methodology define one comparable connection. Preserve this identity across replacements by comparing with the entity's first immutable proposal under its existing row lock. A different definition needs a distinct named connection. This keeps the existing schema/additive JSON compatibility and avoids silently recasting historical data.

Annual statistics and awards do not obey officeholder term-expiry rules; overlap validation depends on fact category, with distinct reporting editions retained. Link comparability is a reviewed explicit status and explanation, not inferred from similar words or matching GS/GK tags. Older records retain general/unclear defaults. Normalizing legacy defaults for idempotent replay avoids treating an old successful request as changed merely because optional fields were added.

### 3 November — one Oracle canonical bank and browser paper preparation

The owner authorized implementing the remaining website/PDF/admin/game work and moving the local workshop to the existing Oracle VM. Physical bank authority now lives in `/srv/study/workshop/mpsc-question-bankv2`; this supersedes DECISIONS #5's location, not its ownership separation. PostgreSQL still holds workflow/user data and derives exam content from guarded JSON sync. A machine-bound write policy disables local publication, the local timer is disabled, and Oracle owns the existing correction publisher plus an independently reviewed whole-paper publisher. Both share the bank lock. Parser results remain staged. No production bank content was edited through direct SQL.

Keep human-edited draft payloads separate from extracted page text and OCR jobs. Saving creates immutable version history and invalidates review; no person who edited a paper may approve it. Exact draft assignments do not expand UDC/Prelims collection access. Source/key hashes, independent review and roles are rechecked at publication, with durable receipts and readback. New paper membership requires a separate deliberate collection change. This preserves the handed-off 78 sources and their 6,931 questions.

Document processing runs as www-data with bounded Poppler/qpdf/Tesseract subprocesses; the privileged publication bridge does not parse untrusted PDFs. Deployment drains workers, and new workers finish their current lease on graceful shutdown. Paired daily recovery snapshots are verified and fetched read-only into private local storage when this computer is online; continuous external-cloud offsite storage remains unconfigured.

Topic Trail is a versioned mode in existing game_rooms, preserving assessment locks, snapshot exclusion and exactly-once rewards. The live vocabulary pool fell from thirteen canonical records to seven distinct usable questions after booklet deduplication. The physics taxonomy also included geography questions. Therefore approved taxonomy alone cannot select a narrow pack: add owner-inspected exact source lists. Launch only ten source-matched Constitution basics questions from Prelims, with explicit pilot/limited-variety expectations. Never count a UI fixture's synthetic approvals as human review of production content.

### 3 November — consolidated AI continuation and honest discovery

The owner requested implementation of the finalized portable-review plan and removal
of contradictory active instructions. CLAUDE.md is now a short current entry point;
PLAN.md contains active work and links the unchanged historical ledger. Past local
publishing paths, old counts and bounded quota exceptions are not standing authority.
No protection, source/provenance, human-review, assessment or backup rule was removed.

Use one private SQLite queue across accounts, with rotating claims, immutable source
and evidence files, exact proposal reconciliation and serial Oracle publication.
Five pilot explanations were source-checked, applied and fully read back through
ordinary allowance. A complete before/after bank comparison permits only those five
explanations and their required reviewPublicationId audit pointers. Attempts, exact
assignments, permission grants and human checks remained unchanged.

The owner confirmed OpenCode Go. Installed v2 Console OAuth is not accepted as a Go
API key (read-only probe returned 401). Use the documented Go-only inference endpoint
with a privately supplied personal Go API key, stable packet session headers, bounded
output and verified Go/zero-balance-cost usage. This stateless model call has no tools
or production credentials. Missing keys or exhausted/unconfirmed billing stop work;
a billing mismatch blocks subsequent Go calls until operator reconciliation. No paid
model request occurred during implementation; the pilot used manually checked drafts.

Popular questions reflect distinct registered practice/discussion participation in
seven days, conservatively grouped across identical booklets, with a five-participant
threshold. Editorial recommendations come from existing inspected exact source lists.
Hot topics are owner-managed dated picks; factual support must use independently
published current-affairs revisions and becomes unavailable when stale or withdrawn.
Display creates no attempt and assessments withhold discovery. Never seed popularity
or label these sections as predictions.
