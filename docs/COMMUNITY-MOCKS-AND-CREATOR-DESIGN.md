# Community mock tests, taxonomy and creator recognition

Design proposal · 3 November 2026. Requested by the owner. This document specifies
future work; it does not claim the features are implemented or deployed.

## Product structure

Keep the existing Home / Exams / Library / Games / More navigation. Add one
Create destination inside the existing Creator studio, linked from More and the
user profile. Its choices are Mock test, Practice set, Question and Material.
Subject/tag suggestions belong inside the relevant picker, not another main page.

Library gains a Tests & practice view with three tabs: Discover, Saved and Mine.
Discover mixes reviewed practice sets and community mocks, visibly labelled by
type. Exams retain official paper mocks and gain a secondary Community tests link
scoped to that exam. Important Days remains a learning collection, able to link to
related tests without becoming another question bank.

Home keeps the next study action first. Use at most one three-card discovery row
for this feature, scoped to followed exams; a View all link opens Library. Do not
add separate rows for likes, points, new subjects, tags or creator leaderboards.
Reuse existing Popular discovery placement rather than adding another panel.

Test card: title; creator; exam/subject; question count and duration; source-bank
label; Helpful count; Start. Save and Report live in an overflow menu. Show at most
two tag chips plus '+N'. Mobile has full-width search and one Filters disclosure;
Exam, Subject, Bank and Tags live inside it. Sort choices: Relevant, Popular this
week, Most helpful, New. Avoid badge stacks and multiple social counters.

## Creation and use

1. Details: title, short purpose, exam (optional), approved subject(s). Default to
   private. Choose Timed mock or Untimed practice. An exam selection pre-fills
   subjects and scoring suggestions, but user tests remain labelled Community.
2. Questions: search approved live questions; filter MPSC / Website / Both,
   subject, topic, subtopic, tag and year. Pick exact questions or use balanced
   selection with per-subject counts. Preview actual eligible counts before save.
   Newly written questions enter the existing learner submission/review workflow.
3. Rules: total questions, duration and marks/penalty; advanced section rules and
   question order in a disclosure. Show maximum marks and penalty plainly.
4. Preview: inspect question order and coverage; Save private, Try test, or Submit
   for public review. Keep progress autosave visible with explicit save-error state.

Private tests made entirely from published eligible questions can run immediately.
Public discovery and share links require review. Initial release has no unlisted
sharing: private links must enforce owner access. Public URLs are stable; attempts
pin an immutable revision. Author edits create a draft while the live revision
remains available. Request changes, publish, withdraw and appeal retain history.
A withdrawal blocks new starts; completed attempts remain accessible to their owners.

A test is a reusable template; each start creates its own mock session. Keep
question IDs and provenance. Store the selected question order, question/answer
snapshots, approved taxonomy, scoring rules and template revision at start.
Freeze auto-selected questions when a public revision is submitted so review sees
what users will receive. Private auto-selection may generate a fresh session but
must record its exact selection and return a shortfall instead of silent substitution.

Start rechecks current eligibility. If a published question becomes held or loses
its usable key, pause starts for that fixed revision and show the author the issue.
Do not change an in-progress test's questions or original score. Continue the existing
separate correction/reassessment display for historical results.

Reuse assessment locks, saved answers, server deadlines, submission idempotency,
answer-withholding and mock results. Community tests never expose keys through
preview APIs during an active assessment. Public detail endpoints contain no keys.
The current mock selector deliberately excludes Community questions: implement an
explicit source-aware selector for user templates, with eligibility tests, rather
than removing that restriction from official paper mocks.

Initial scope: scored MCQs only, using the existing official-key and reviewed
practice eligibility modes with honest labels. Written questions remain in reading
sets. No claim that a community mock reproduces an official examination.
Respect existing attempt entitlements; creating/saving templates is free, and the
existing mock allowance applies when starting a scored session. Show this before
Start. Any change to free quotas is a separate product decision.

## Subjects and tags

Subjects are the shared curriculum hierarchy: subject → topic → subtopic. Users
select existing approved nodes or use 'Suggest a subject/topic' with parent,
definition, example questions and reason. Review can approve, reject or merge an
alias into an existing node. A learner cannot directly create a public subject.
Approved changes use the established taxonomy/classification publication workflow.

Tags are cross-cutting labels such as Environment Day, Budget 2026 or Map practice.
They are many-to-many, and do not replace subjects. Users may create private tags
for their own saved items immediately. Private labels remain owner-visible and
cannot influence search, popularity or points. Publishing a tag or applying it
publicly to a canonical question requires a proposal with examples and independent
review. Public tests may select existing approved tags; reviewers approve new tag
suggestions as part of their review before the test becomes discoverable.

Normalize case/spacing and maintain alias redirects; show existing matches before
creation. Stable IDs survive label changes. Public tags need a description and a
maximum of five per test. Merge preserves references/history and does not award
creation points twice. Deactivated tags disappear from new pickers while historical
attempts retain their saved labels. Private folders may have arbitrary names but
must never appear as official subject classifications.

## Helpful, Popular and points

Use one reaction called Helpful (thumbs up), not separate likes and upvotes. Save
is a personal bookmark. Report is the correctness/conduct channel. Popularity is
not an answer-quality certification. Question helpfulness cannot upgrade its key.

For tests, Helpful becomes available after a submitted attempt with at least half
the questions answered. One registered account gets one active vote per template,
can undo it, and cannot vote for its own work. Votes bind to the consumed revision;
material changes reset the current revision's helpful count and eligibility while
older votes remain in history. New revisions never re-award old creator milestones.
For materials, retain the existing material vote behavior and storage; do not
create a second reaction counter. Initial release excludes votes on subjects/tags.

Popular this week uses distinct qualified completers in the trailing seven days,
excluding the author and blocked/test/synthetic accounts. Require at least five
qualifying learners before applying a Popular label. Proposed score:
log(1 + unique completers) + 2 × helpful votes / (unique completers + 10), with votes
and completions from the same seven-day cohort/revision. Count each learner once,
and use latest qualified completion time then ID as deterministic tie breakers.
This is a launch rule to measure and adjust, not an established effectiveness claim.
Low-data results use Relevant/New with an honest empty Popular state. Most helpful
uses a Bayesian-smoothed helpful/completion ratio and the same minimum cohort.
Author self-attempts and repeat attempts cannot inflate discovery.

Keep Learning XP and redeemable reward-wallet points as they are. Introduce
Contribution points as a separate non-redeemable reputation total inside the
existing profile/Rewards page, labelled clearly; do not mix it into study accuracy
or silently convert votes into subscription credits. No navigation item for it.

Proposed initial contribution rules:
- Independently published original question: +10, once per canonical question.
- Independently published useful test: +5, once per template, minimum 10 eligible
  distinct questions. Reordered copies and minor edits do not qualify.
- First 5 distinct qualified Helpful voters on a test: +5; first 20: +10 more.
- Accepted public tag/subject proposal: +2 only when used by at least 3 published
  questions or collections; once per approved concept, with merged aliases sharing
  the same claim. No points for creating private tags, voting or raw submissions.

Start with a 50-point daily creator-award cap. Defer qualified awards beyond the
cap rather than losing them; a daily worker settles idempotently. Milestones settle
only after a seven-day holding window. Unique source/event claims prevent repeat
awards across edits, retries or imports. Freeze suspicious voting rings and burst
accounts for review using recorded events; do not infer identity from IP alone.
Undoing votes can reverse an unqualified milestone through a compensating ledger
entry; earning it again reinstates the existing claim, never creates extra rewards.
Content removed for abuse reverses associated awards with a reason and appeal.
Ordinary retirement does not revoke earned publication credit. A later independently
verified publication supersedes stale fraud decisions through an audited action.
Points do not grant reviewer/publisher roles automatically. Public creator rankings
are opt-in, displayed within Profiles only. Reassess thresholds using actual use.

## Storage and API boundaries

Extend existing learning_catalog with a new mock-template kind in a new migration;
reuse its author/version/live_payload/history and independent review model. Define
a separate typed mock payload (sections, IDs, timing, marking, source/answer mode),
not loose practice metadata. Preserve existing day/practice payload validation.
Use an immutable revision table for public templates and a mock_session source
reference to that revision; no attempt depends on a mutable live_payload.

Additional records:
- tag_definitions: ID, owner for private tags, scope, canonical label, aliases,
  description, review state; constraints enforce ownership and uniqueness.
- tag_assignments/proposals: approved target IDs, exact target type, revision,
  author, reviewer, reasons and immutable events. Use typed references with foreign
  keys or a resource registry; never unconstrained target_type/target_id pairs.
- taxonomy_proposals: parent/level, rationale, examples, merge target and review
  history; adoption delegates to canonical taxonomy publication.
- collection_votes: user, collection, consumed revision, active state and timestamps;
  unique(user,collection). Separate immutable vote events preserve toggles.
- collection_bookmarks: unique(user,collection), private by default.
- creator_point_claims and creator_point_ledger: claim identity, rule version,
  amount, status, release time, source, reversal link and reason. Separate from the
  existing spendable reward ledger; no payment/redeem endpoint.
- daily_collection_metrics: aggregate qualifying completions/votes by revision and
  date, rebuilt from server events. Never expose learner identities in public counts.

Reuse /api/learning-catalog for authoring/review, with cursor pagination and per-kind
payloads. Add POST /api/learning-catalog/{id}/start that calls shared mock-session
creation with template eligibility; use existing mock save/submit/results routes.
Helpful uses idempotent PUT/DELETE actions on /{id}/helpful; bookmark likewise.
GET /discover accepts exam, subjects, bank, approved tags, sort and cursor. Subject
and tag suggestions have owner-visible status and scoped reviewer decisions.
Enforce actor/session, CSRF, ownership, scoped grants, expected versions and rate
limits server-side. Public cache contains aggregates only; private queries are
no-store. All lists and searches are bounded and indexed. Withdrawal, moderation
and publication invalidate public ranking caches immediately.

## Review workspace and rollout

Add Tests, Questions and Subjects & tags filters to existing review navigation.
Keep 'Mine: awaiting review' within Studio with counts and requested changes. Users
see their submissions only; scoped reviewers see authorized queues. A test review
checks coverage, canonical question identity, scoring eligibility, duplication,
labels and title claims. It does not invent new question certification. Authors
cannot independently approve their own template, tag or taxonomy proposal.

Phase 1: private mock builder + existing runner + Saved/Mine; question selection,
source separation and immutable attempts. No public ranking or points yet.
Phase 2: reviewed public tests, public/private tags, taxonomy proposals, Helpful,
bookmarks and Library discovery. Clean up duplicate More links to Website bank.
Phase 3: qualified Popular metrics and contribution-point ledger, holding windows,
abuse review and opt-in creator profile statistics.

Acceptance checks: private resources never leak through IDs/search; self-review
and duplicate votes fail; stale saves conflict; held keys block new starts;
changed revisions preserve old attempts; mixed-source modes do not change official
paper mocks; plan limits and assessment locks hold; concurrent start/submit/reward
calls do not duplicate records; vote undo/reinstatement cannot farm points; merges
preserve identity; no fabricated popularity; no horizontal overflow at360/390px;
Home gains at most one existing-slot discovery row and no new bottom-navigation item.

## Example

A learner creates 'Environment basics · 20 questions', chooses Science, selects
MPSC and Website questions, adds the approved Environment Day tag, and saves a
30-minute private mock. After independent publication, it appears in Library and
relevant exam discovery. Other learners take it and mark Helpful on the result
screen. Qualified activity may earn a Popular label and audited contribution
points. The same question IDs remain in their original banks and can also appear
in Important Days or another reviewed collection.
