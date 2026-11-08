# Review workspace

Entry: https://study.hawayu.in/editorial

The workspace reviews existing registered source questions. A source question keeps
its canonical ID and appearance IDs wherever modules reuse it. Creating a review
assignment never copies a question or creates a separate module bank.

## Scope and access

Owners can reserve any existing paper-based module (from the current registered
collections), or an explicit selection of individual registered papers. The paper
picker identifies MPSC and Website sources. A reviewer creates their own account;
the owner separately confirms and activates the exact assignment. Inspection
access does not confer administration, independent approval or publication rights.
Existing UDC/Prelims assignments retain their original source memberships.

Assignments snapshot paper membership. Later module papers appear under Add
papers / check new sources; an owner must select them. Additions require the
current assignment version and an audit reason. Existing checks are retained;
revocation and account-email matching remain enforced. Scope expansion does not
alter the separate UDC/Prelims bank integrity baseline or publish imported content.

Paper-based modules are listed dynamically; no UDC/Prelims allowlist remains in
assignment creation. Question-only Important Days/practice-set metadata continues
through its independent workflow at /learning/manage. New PDF drafts continue
through /paper-workbench. These queues are linked from the workspace rather than
silently granting all source-paper access for a small tagged question set.

## Daily flow and authority

My work resumes assigned papers. Needs attention groups tag issues, answer/source
issues, learner submissions and publishing problems. Completed shows finished
papers and correction history. Tag search has its own paper scope, preserving the
paper position in My work. Searchable source and taxonomy pickers replace long
lists. Bank-wide queues require existing grants; assignment-only access remains
within assigned sources.

Inspect the question and applicable source, options/figures, answer evidence and
explanation or written guidance, then use Checked & next. This explicitly records
the source-review-v1 human attestation. Cannot verify requires a useful reason.
Edit opens tags, text/options, answer and explanation in place. Failed saves retain
the draft and position.

Authorised owners/publishers use Save & publish for final corrections within their
subject permissions. The append-only decision records actor, rationale, source
baseline and exact revision without fictional peer reviews. Answer changes retain
evidence/conflict controls. Assignment-only users submit proposals. Public
proposals retain independent review and cannot be self-approved. Approve & publish
queues publication only when that policy is met.

## Progress and corrections

Recorded counts saved inspections. Current checked requires an unchanged relevant
inspection fingerprint. Changed source/evidence, answer or explanation appears as
Recheck needed. New checks compare content fingerprints so taxonomy-only changes
do not reopen otherwise unchanged answer checks. Legacy checks retain strict
source-token behavior. Strict source versions still reject conflicting edits.
Inspection fingerprints are not exposed to answer-hidden learners.

Paper completion requires current Checked inspections and no pending/failed
correction. No additional compulsory whole-paper approval is introduced. Progress
refreshes after saves and on focus. Correction status distinguishes submitted,
queued/publishing, applied and failed. Inspection completion is not automatic
factual certification.

Tag cleanup filters actual reported issues, missing subject/topic, invalid paths,
or all visible questions, with module/bank/paper/year/search controls. Missing
subtopic alone is not an error. It does not infer semantic mistagging. Admins can
preview and apply up to 20 canonical targets with one rationale. The worker applies
the batch atomically under one bank lock, then verifies synced results. Failed
batches retry together against original immutable manifests.

Only explicitly linked matching reports close after verified publication. Tag
edits do not close answer reports. Admin maintenance earns no community points.
Canonical edits affect shared appearances. Staff MFA, assessment answer gates,
CSRF/origin protection, source evidence and historical reviews remain enforced.

## Implementation and validation

Migration 0072 adds nullable module scope, a standalone assignment title and stable
scope keys. An insert trigger preserves compatibility with existing exam-scope
operators during rollout. No bank-owned tables or bank JSON are changed by it.
The bulk source-version helper is equivalent to individual source-version tokens;
its shared-question and related-topic behavior is covered by API tests.

Frontend regression scripts in web/scripts cover source-save behavior, tab draft
isolation, progress filters, eight-card pagination, future module and individual
paper selection, MFA disabling and context links. React component scripts accept
a directory containing react-test-renderer@18.3.1 as their first argument. Backend
tests use disposable PostgreSQL, never synthetic production inspections.

Migration 0073 adds final admin decisions, report linkage and inspection
fingerprints. Shared publication and worker paths revalidate current authority,
freshness and exact payloads. Atomic tag batches retain one input/output checksum
and durable receipts across interrupted sync/acknowledgement.

The 4 November release passed 157 backend tests, frontend regressions and build.
Read-only production checks preserved assignment/membership/grant hashes and
81,627 canonical questions. Overview reads measured 134ms for Prelims (30 papers)
and 165ms for UDC (48 papers). Signed-out entry passed 390px/768px overflow checks;
authenticated mobile/iPad visual verification remains pending.


### Tag discovery performance follow-up — 4 November

The cleanup query selects eligible source appearances once, groups open tag
reports once, and shares one filtered snapshot between count and page. Post-deploy
server route measurements: attention654ms, no-topic549ms, reported32ms,
no-subject60ms, invalid396ms. These exclude browser/network rendering. Validation
now totals158 focused backend tests, including shared-bank source selection,
current browsable module scope, report deduplication and beyond-end pagination.

Both banks are searchable within actual grants; saving and publishing a tag
correction updates the canonical question wherever modules reuse it. Search does
not automatically reclassify existing content. Missing-topic coverage gaps and
learner-reported issues remain distinct; semantic correctness needs inspection.


## Finding the workspace

After sign-in, staff and assigned reviewers have a Review workspace shortcut below
the site header. More also shows a prominent Review & administration section.
Staff can open Admin dashboard there; admin sidebar links back to review and tag
cleanup. Assigned-only reviewers see review access without admin shortcuts.

Start with one module or selected paper and finish its inspections/corrections.
Staff can use Tag issues in this module to scope the tag list while preserving the
current My work source position. The tag list uses the module's current browsable
papers; inspection assignments retain their reserved membership snapshot. Use
Across the bank on admin home for broader issues. Published canonical corrections
benefit every module reusing that question; another whole-bank pass is not needed
just to apply the same correction again.


## Shared module review — 4 November 2026

Open `/editorial`, choose a module or assigned source set, then open a source paper.
Exam homes expose Review this module to staff and active assigned reviewers.
Direct examples: `/editorial?scope=module%3Agroup-b-non-gazetted` and
`/editorial?scope=module%3Agroup-b-gazetted`. Existing assignment URLs still work.
The chooser is searchable and paged. Papers open in Remaining at the next useful
source; All and Needs attention remain available. Search covers the full paper.
URLs retain module, source and queue position.

An unchanged exact-source inspection counts in every accessible module using it,
with its original reviewer attribution. It is not copied to new assignments or
credited to the current user. Another appearance of the shared question still
needs its own source check. Evidence changes can make checks stale; tag-only
changes do not invalidate matching source evidence. Admins can explicitly resolve
conflicting inspections with a recorded reason. Reports and pending/failed
corrections remain separate completion blockers.

Owner/publisher authority permits direct checks without manufactured assignments.
Assigned-only access remains frozen; parent modules grant no new permissions.
MFA, assessment gates, public-submission rules and guarded publication remain.
Canonical corrections reach shared uses after publication/sync; this release does
not automatically retag or certify bank content.

Counts distinguish questions from appearances and show checked elsewhere as a
subset. Held/restricted source records remain reviewable, so totals can exceed
learner practice availability. The selection disclosure is read-only; owner setup is described below. The tag shortcut
uses source-collection scope, not necessarily the exact learning area. Source-paper composition is available through owner setup below.

Validation: 104 backend regressions, frontend behavior checks and local build
passed. Production scope/status service reads measured UDC216ms, Assistant73ms,
Group B Non-Gazetted534ms, Gazetted20ms and NG common241ms, excluding network/render
time. Assignment/grant/membership hashes, 81,627 questions and zero human source
checks were preserved. Signed-out entry widths passed at390px and768px;
authenticated visual QA remains pending. No synthetic production reviews or
fabricated signed-in sessions were created.


## Module setup — source-paper composition

Global owners can open **Module setup · admin** below daily review content. Normal
reviewers keep the same review workflow. Start from the current module, or choose
Create a new module and a published source library. New modules stay hidden until
published and can be resumed under Unpublished modules.

Choose individual papers through search, or import another module's browseable
paper library. Imports are explicit snapshots of the version shown in preview;
they do not copy the child module's filtered learning areas or silently absorb
future papers. Exclusions override imports. Existing Group B science/technical
roles still decide those learning areas. Original paper rules stay with retained
sources; imported/new papers are not automatically enabled as timed mocks.

Save draft & preview changes shows current/proposed paper, canonical-question and
source-appearance totals, plus added/removed papers. Exclude an added paper from
that preview if needed, then preview again. Enter a brief reason and publish the
new version. This is the owner's final selection decision; no second admin is
required. Failed publication retains the draft and retries use the same key.
A changed source version or selection requires a fresh preview. Publication history
records the actor, reason, source versions and immutable selection.

Only this module's published configuration changes. Exact assignments, source
checks, attempts and canonical tags/content are preserved. Other compiled modules
keep their snapshots until explicitly updated. Existing specialised section filters
remain; this panel does not add arbitrary query editing or new per-question pins.
Restricted existing modules cannot be made public through this editor. Staff MFA,
CSRF and global-owner authorization apply to configuration writes.

Read-only production previews of unchanged UDC, Group B Non-Gazetted and Gazetted
all reported zero additions/removals. Measured service times were1072ms,1718ms and
300ms respectively, excluding browser/network. No production composition draft or
publication was created for testing. Migration0075 and the local frontend build
were deployed after115 backend tests and component/navigation checks passed.

## Daily continuation refinement — 4 November 2026

Use **Continue reviewing** in the selected module summary to open unfinished work,
even before its first inspection. This keeps the current unfinished paper when
possible, otherwise choosing the most recently active unfinished source. The source
paper list remains searchable. Module setup is collapsed below daily review content.

After Checked & next or Save unresolved & next succeeds, continuation resolves
against fresh remaining rows in original paper order. It skips the saved appearance,
wraps once and handles page boundaries when saved rows leave the queue. A paper with
no other matching unresolved row shows an explicit saved/end state; Continue
reviewing moves to another paper when one remains. Failed saves keep position and
drafts. A correction receipt offers a separate next-unresolved action and discloses
that publication may still be pending; saving a correction is not a source check.

The summary separates inspections remaining, source appearances with unresolved
issues, corrections submitted/awaiting publication and failed publications. The last
two count canonical corrections once across papers. Issue and inspection categories
can overlap. Source/answer attention uses this module's accessible sources; wrong-tag
cleanup uses its source collection; learner submissions and publishing use the
existing permission-bounded bank queues. These shortcuts do not imply exact
learning-area membership for those broader queues.

118 backend regressions and focused UI/build checks passed; API/web deployment and
read-only preservation/health checks passed. Authenticated phone/iPad visual QA
remains unverified. See DEVLOG.md for release receipts and exact limits.

## Source locators and written context — 4 November 2026

The quick editor's **Source reference** action repairs the physical PDF page and
printed question number within the current original paper. **Text / context** now
also edits section instructions and shared passages. These preserve the exact
appearance/canonical binding and use existing final admin or public-proposal paths.
Paper-library membership remains in owner Module setup. Original resources without
extracted questions are labelled explicitly; PDF availability is never inferred
from a zero count. The [Gazetted audit](GROUP-B-GAZETTED-AUDIT.md) records the first
137-entry source repair and its remaining coverage/duplicate limits.
