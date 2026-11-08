# Simpler editorial workflow — implementation brief

Implemented and deployed 4 November 2026. The design below is retained as the
implementation record. See [the workspace runbook](EDITORIAL-WORKSPACE.md) for the
current operating flow. Preserve unrelated work in this checkout.

Release validation: 157 focused backend tests, frontend regressions and production
build passed. Migration 0073 was rehearsed on a disposable clone before application.
Live health and worker checks passed; assignment/membership/grant hashes remained
unchanged and no synthetic production reviews were created. Signed-out entry
layouts passed at 390px and 768px. Authenticated phone/iPad visual QA remains
unverified because the available browser has no signed-in session.

## Owner direction and product decision

The owner wants fewer steps, a smooth daily flow, easy discovery and repair of
wrong subject/topic tags, and final decisions by authorised admins. Public
submissions still need review. This supersedes the assumption that every admin
correction must be submitted to another human. It does not grant new account roles.

Redesign the workflow around the work to finish; retain the current bank, IDs,
assignments, source evidence and immutable history. Do not rebuild the database or
introduce another question bank. Deliver working vertical slices in the order below.

Default permission interpretation: owner/publisher can make final decisions within
their existing subject grants. Assignment-only editors can check assigned papers
and propose changes; they cannot publish. Sangzel already has owner access; Solomon's
Prelims assignment alone does not give publication rights. Recheck actual grants
when implementing; do not create grants based on this document.

## What the code currently does

| Friction | Existing implementation | Change |
| --- | --- | --- |
| Routine inspection repeats confirmations | EditorialQuestionReview has four checkboxes, an outcome, a mandatory ten-character note and save buttons | One explicit Checked & next action with a visible statement of what is being checked |
| A correction leaves the paper workspace | Separate contribution-editor link | Inline editor with current source and list position retained |
| Admin tags take more steps than admin answers | admin_answers.py records a final decision and queues publication; retagging.py only creates submitted proposals | Add an explicit final admin decision for existing-question corrections, starting with taxonomy |
| Bulk tags repeat rationale and evidence | AdminRetagging has two textareas, preview selection, independent approval and separate publication | One useful explanation, one before/after preview, one Apply tags action for authorised admins |
| Wrong-tag discovery is weak | browse_admin supports text, subject, topic, paper and answer issues, but no dedicated tag-quality queue | Add precise tag-quality filters and searchable hierarchical paths |
| Tiny metadata changes reopen whole checks | editorial_access includes row xmin values and both primary/related tags in one token | Keep strict write-conflict tokens; introduce separate content-based inspection fingerprints |
| Report resolution is another task | resolve_legacy_report requires a manual applied-publication link | Link reports when deciding; resolve after verified application of the relevant correction |
| Daily tools are scattered | /editorial, questions, retag, reports, workflow and contribution detail | One editorial entry with contextual views; keep existing links working |

## Daily experience

Use `/editorial` as the main entry with three sections:

- **My work**: assigned papers, recent work and one Continue action. Owners may
  choose permitted work outside an assignment without creating a fake assignment.
- **Needs attention**: saved views for Tags, Answer/source issues, Learner
  submissions and Publishing problems. These are filters within a common task
  list, not four new dashboards.
- **Completed**: completed reviews and resolved work, with the real actor/date.
  Show paper completion separately from published-correction history.

Keep paper selection, module/bank scope and recent work visible near the top.
Move assignment management and other setup controls into Manage. Preserve old
admin URLs and bookmarks; link/redirect them to the equivalent filtered view only
when feature parity is ready. Keep unrelated moderation/settings tools available.

On a question, show source identity, question, answer/explanation and compact
subject/topic chips. Provide three primary actions:

1. **Checked & next**: deliberately confirms the displayed inspection statement.
   Record actor, time, exact source version and attestation wording/version.
   No repetitive free-text note when nothing is wrong. Keep optional notes.
   A checklist inspection does not relabel an answer as official or change scoring.
2. **Edit**: open the relevant Tags, Answer, Text/options or Explanation form in
   place. Prepopulate source identity, evidence references that actually exist,
   and the current baseline. Admin button: Save & publish. Assigned editor button:
   Submit correction. Show only the fields the chosen operation needs.
3. **Cannot verify**: choose a meaningful reason (missing source/key, unclear
   scan/figure, disputed answer, other), optional detail except Other, then continue.
   Keep the question unresolved. Skipping is navigation, never verification.

An admin tag-only correction verifies that tag decision, not the whole question.
A correct answer alone also does not certify the source text/options/explanation.
For written questions, describe relevant marking guidance and explicitly allow
not-applicable MCQ checks. Never manufacture four true legacy flags for an action
that did not assert all four checks.

Preserve scroll, filters, selection and next-item order after save. Show the last
action if the item leaves a filtered list. Save editable drafts automatically,
with explicit storage/sync state; the existing tab-local 24-hour draft storage
may be retained initially and must be labelled honestly. Autosave never publishes
or signs a review. On failure, retain edits and stay on the question.

## Find and fix tags

Tags means the existing approved subject/topic/subtopic hierarchy and related
paths. A paper's exam title is source identity, not evidence of the question's topic.
Module membership is a separate concept. Label these separately in the UI.

Default Tags views:

- **Reported wrong tags**: unresolved classification reports, grouped by canonical
  question. Show report count and reason, not a claim that every report is correct.
- **No subject**: no approved primary subject.
- **No topic**: approved subject but no topic. This is a coverage gap, not necessarily
  an error; subtopics remain optional unless a specific module requires them.
- **Invalid classification**: inactive/missing taxonomy nodes or broken parent paths.
- **All tags**: search any permitted question, including ones with no report.

Do not invent a reliable automatic 'wrong tags' detector. Semantic mismatch
suggestions are a later optional feature; label the method/reason and keep them
unverified. Paper headings or keyword matching cannot auto-retag questions.

Search question text/exact ID and narrow by bank, module, source paper/year and
current subject/topic. The target picker searches labels and displays full paths,
not raw IDs or a long series of dropdowns. Reuse the existing GK/GS display mapping
without losing stored identities. Related paths have an explicit Add/remove UI.

Default issue sort: invalid paths, reported tags, missing subjects, missing topics;
then oldest unresolved first, with canonical ID as stable tie-breaker. Offer paper
order and most-reported sorts. Derive dates/counts from real records. For a computed
gap without a recorded date, say Date unavailable and use deterministic paper/ID
order, rather than inventing an issue creation time. Counts and pagination must
use the same permission, bank and module predicates.

Single edit: click a chip, search/select a valid path, see before/after, Apply tags.
Use one concise reason, optionally a meaningful reason choice plus detail. Persist
the actual explanation once; do not ask the user to retype rationale as evidence.

Bulk edit: keep the existing 20-question maximum. Select exact questions, choose
one operation, inspect a compact preview, Apply to N questions. No second set of
checkboxes for the same selection; allow exclusions in the preview. Preserve
unrelated related paths, remove duplicate primary/related paths, and make bulk
add-related/remove-related/replace-primary distinct operations. No unbounded
'select all matching' and no bulk answer changes.

Selections are canonical IDs with a source appearance for context. De-duplicate
shared questions across modules/papers. Display 'Also used in N papers/modules'
near the change preview. A published tag correction updates shared categorisation;
it can alter tag-based module selection. It does not rewrite frozen source-paper
assignments or create module-specific copies. Refresh affected counts after sync.

## Decision policy: fewer human steps, explicit authority

| Actor/work | Human action | After action |
| --- | --- | --- |
| Admin correcting existing tags, explanation or text | Inspect, edit, Save & publish | Attributed final admin decision; ordinary guarded publication |
| Admin deciding an answer | Existing final answer adjudication, embedded in the workspace | Preserve official-key mapping, unofficial labels, holds and assessment protections |
| Assigned editor without publication grants | Check or submit correction | One owner-facing inbox; no automatic role upgrade |
| Learner submission/correction | Submit for review | Keep existing review policy; no self-publication and no automatic conversion to an admin decision |
| Inconclusive/disputed item | Leave unresolved or explicitly escalate | Admin chooses when evidence is sufficient; never auto-certify |

The default simplification does not silently lower the existing public-submission
quorum. Show public submissions in one inbox and combine the last eligible review
and publication action when the actor has both permissions and policy is met.
If quorum is still unmet, record review and show the remaining requirement.
An owner can make a separate, explicit final admin correction to resolve the issue;
link it to the public report/submission and preserve authorship/history. Do not
fabricate peer approvals or silently rewrite a learner's proposed revision.

No mandatory extra whole-paper approval after every question is already properly
checked and all blocking corrections are resolved. Derive paper completion from
current evidence. An optional owner 'Close review' can record a summary decision,
but must not pretend that the owner personally rechecked every answer. Retain
individual reviewer and decision attribution. This avoids adding another routine
sign-off layer to the earlier proposal.

New PDF imports, current-affairs facts and new learner questions have distinct
validation needs. Link their existing tools from this workspace. Do not silently
relax their separate approval contracts during the existing-question rollout.

## Backend contracts and integrity

Reuse contributions, immutable revisions, publications, outbox, receipts and
events. Introduce a small append-only admin decision record for existing-question
corrections; do not overload admin_answer_decisions with unrelated modes or mark
ordinary proposals approved merely because their author is staff.

Suggested record: decision ID, actor, canonical/source IDs, contribution ID,
revision, decision kind, baseline hash, payload hash, concise reason, creation time,
idempotency key/request hash and optional linked report/submission IDs. Use the
next unused numbered migration after inspecting the current ledger, not a number
assumed by this brief. Keep old migrations and historical decisions unchanged.

An admin decision and its publication request must be one transaction:

1. Authenticate with existing session, origin, CSRF and staff MFA enforcement.
2. Validate current grant for both original and destination subjects, and all
   changed related paths. Unclassified questions require appropriate global access.
3. Lock/read exact source and compare baseline; validate approved taxonomy,
   proposal fields, evidence, answer availability and active assessment restrictions.
4. Reject stale or conflicting pending changes with useful existing-work links.
   Reject invalid/no-op tag updates. Preserve existing direct answer attestations
   that intentionally record a valid same-answer decision.
5. Write immutable contribution/revision and final decision, queue publication via
   a shared service, and return stable decision/publication IDs plus state.
6. Publish through the current Oracle authority, lock, source protection, JSON
   change, normal sync and live readback. No direct bank-content SQL shortcut.

Extract common manifest/outbox creation from existing routes instead of maintaining
another near-copy. Extend eligibility to recognise the exact new decision's
revision/baseline/payload and current grant, never a client-supplied bypass flag.
Audit where the worker obtains queued manifests: add/check authorisation again
immediately before application. Revoking a grant while a job is queued must not
leave a newly unauthorised publication path. Revalidate both source and destination
subject grants, including related subjects, at that boundary.

Bulk validation/queueing is atomic: one stale member produces a conflict before
any new decision is queued. Later publication of individual items may partially
succeed; report per-item status honestly and retry only unchanged failed items
with stable keys. A timeout/reload must not duplicate decisions, jobs or credit.

Admin maintenance earns no community contribution points. Extend the worker's
existing admin_answer_decisions/operator-maintenance credit exclusion for the new
decision records. A public contribution keeps its original author/credit rules;
an admin adopting a report must not manufacture a learner contribution or points.

Publication display: **Saving → Publishing → Applied**, or **Needs attention**.
Queued/accepted is never displayed as applied. Automatically resolve explicitly
linked matching reports only after successful live readback; compare issue kind
to changed fields. A tag fix must not close an answer complaint on the same question.
Keep rejection/dismissal as a separate reasoned admin action. A later conflicting
report or changed baseline must not be silently swept up by an older publication.

'Undo' means a new attributed inverse correction against the current baseline.
Queued work requires explicit cancellation support before offering Cancel. Applied
work uses guarded reversal; no blind history deletion or overwriting later edits.

## Progress without needless re-verification

Keep the current strict source version for write conflicts. Separately store
versioned content fingerprints for inspection aspects: source text/options/context/
figures, answer/evidence, explanation, and taxonomy. Include actual source/document
identities and relevant content, not xmin alone. Use deterministic stable formats.

Tag-only changes invalidate or replace the tag assessment; they do not reopen an
unchanged answer assessment. Source/option/key changes invalidate dependent answer
and explanation assessments. An explanation-only change reopens the explanation
aspect. Role-aware UI must say exactly what needs rechecking.

Persist immutable fingerprints with each new attestation. Older checks lacking
content fingerprints remain on the current conservative stale-token logic until
explicitly checked again. Never compute a current fingerprint and attach it to an
old review as though that reviewer inspected today's source.

Paper progress uses distinct appearances for source checking; tag issues use
canonical questions. Do not conflate these denominators. A second appearance may
have different printed options even when it shares a canonical question.
Completion requires applicable current checks and no unresolved blocking work;
pending publication is not completion. Reconcile from persisted state after
refresh, publication and return to the workspace.

## Responsive interaction

Reuse Admin Console prototype tokens and existing source/question renderers.
Desktop: compact work list and flexible question/editor panel. Tablet: list drawer
plus question; source PDF opens alongside only when there is adequate width.
Phone: one panel, source sheet/disclosure, bottom question actions above the site's
bottom navigation and safe-area inset. Avoid nested scroll traps and covered form
fields when the keyboard opens. Keep 44px targets, wrapping chips, visible focus,
labelled search, and announced save/error states. Shortcuts must not fire in text
fields and must have visible equivalents. Do not add a dashboard full of counters.

## Implementation order and file map

### 1. Admin tag correction, end to end

Start with the strongest pain point: admin opens a misclassified question and
fixes its path without finding a second reviewer. Implement admin-decision storage,
permissions, shared publication service and same-screen single-tag editing; then
add bulk Apply tags. Relevant files:

- `api/app/routers/retagging.py`, `admin_answers.py`, `bank_workspace.py`
- `api/app/services/bank_review.py`, `review_policy.py`, `review_identity.py`
- New small admin-decision/publication service and a numbered migration
- `scripts/bank-review-worker.py`, `scripts/review_bank_store.py`
- `web/src/screens/AdminRetagging.tsx`, `web/src/components/LearningTaxonomyPicker.tsx`
- `web/src/components/AdminQuestionWorkbench.tsx`, `AdminReviewProgress.tsx`

### 2. Discover tag problems and retain context

Extend browse_admin or a focused permission-equivalent query for tag issue types,
stable sorting, bank/module scope and counts. Use existing content_reports for
reported errors; inspect its allowed kinds and extend via migration if needed.
Add the searchable path picker, saved filter URLs and before/after preview. Reuse
the existing 20-item preview/batch concept; do not carry over compulsory peer review
for the new final-admin action. Keep the old proposal route for other actors.

### 3. Simplify question inspection

Update `EditorialQuestionReview.tsx`, `EditorialReview.tsx`, `editorialReview.ts`,
`api/app/routers/editorial.py` and `editorial_access.py`. Add explicit one-action
attestation and aspect fingerprints. Embed the correction panel with role-aware
buttons. Preserve source-bound drafts, missing-evidence handling, exact assignment
scope, active-assessment answer gates and 25-question page continuation.

### 4. Consolidate daily queues and progress

Update `EditorialPaperOverview.tsx`, `EditorialReviewContext.tsx`, AdminHome,
adminNavigation and existing reporting/contribution detail components. Implement
the three workspace sections, publication/report reconciliation and contextual
return links. Expand admin final correction to explanation/text only through the
same tested decision service. Embed the existing answer tool, retaining its
specific official-key handling. Do not implement separate competing queues.

### 5. Release and verify

Read the current migration/deploy/runbooks. Rehearse additive migrations on a
disposable production dump clone. Build web locally. Add a targeted deployment
manifest for the actual changed router/service/worker files: the existing
editorial-api target ships only the old editorial pair and migration 0072, so it
is insufficient for this change. Drain/restart publishers per the Oracle runbook;
never ship unrelated dirty files as a side effect. Verify study and family health.

Do not silently migrate existing pending contributions into final admin decisions.
They retain their old status; an authorised admin may explicitly adopt a fresh
revision through the new flow. Keep old links and history readable. Record what
was deployed and what remains unverified in DEVLOG.

## Acceptance scenarios

1. Owner finds a reported Geography question tagged Physics, changes its primary
   path and publishes in one editor; no peer approval screen appears. Related
   paths and original exam identity remain correct. Both shared module views
   reflect the applied classification after sync.
2. Assignment-only reviewer sees Submit correction, cannot invoke the admin route,
   and cannot access another assignment. A learner cannot finalise their own work.
3. Subject-scoped publisher cannot move a question into or out of an unauthorised
   subject; revocation while queued prevents newly unauthorised application.
4. Invalid, missing and reported tags produce honest, permission-scoped, stable
   search results. Missing subtopic alone does not claim a factual error.
5. Twenty selected tag changes have one preview/action. One stale target queues
   none; replay does not duplicate jobs. Later partial worker failure is visible.
6. Unchanged question: read source and click Checked & next, without typing a
   filler note. The saved record truthfully captures the explicit attestation.
7. A tag change does not erase valid answer inspection; changed options/key reopen
   dependent checks. Old checks retain honest conservative freshness semantics.
8. Edits survive save failure. Back/refresh preserves filters and resumes the
   correct question across page boundaries. No stale source is silently accepted.
9. A tag report closes only after its linked tag publication applies and reads
   back correctly; unrelated answer reports stay open. Queue failure stays visible.
10. Official-key evidence, scoring holds, historical attempts and active mock/game
    answer gates remain intact. Admin decision does not fabricate an official key.
11. Direct admin maintenance does not earn community points; public contribution
    attribution remains intact. Reversal creates history and rejects stale bases.
12. Desktop, 768px iPad and 390px/360px phone: keyboard and touch work, no horizontal
    overflow, no bottom navigation overlap, long paths/questions wrap, save state
    is readable and drafts survive navigation as documented.

Extend the existing source-identity/retagging, admin-answer, bank-review, editorial
assignment and publication-verification tests. Update tests that deliberately
encode the old admin-tag peer-review requirement only for the new admin route;
retain coverage of the public proposal route. Exercise the complete publication
roundtrip on an isolated bank/database and run focused frontend/component checks
plus production build. Do authenticated visual QA when a legitimately available
session permits it; do not claim it from component tests. No synthetic production
checks, decisions, papers or user grants for testing.

## Handoff prompt

Implement this brief in the existing India Study Map repository, beginning with
the admin tag correction vertical slice. Read current repository instructions and
the linked publication runbook first. The owner authorised simpler final admin
decisions while retaining review for public submissions. Preserve permissions,
source protection and immutable history; do not create synthetic peer approvals.
Work through the remaining slices in order, test each meaningful change, rehearse
migrations, use a targeted deployment, and report tested outcomes and remaining
limitations. Do not stop after cosmetic UI changes or call queued jobs applied.
