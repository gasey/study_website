# PDF and MPSC question-bank CMS upgrade

Final implementation plan — 5 November 2026. Status: CMS implemented and deployed.
Source ingestion and content verification continue as separate editorial work.

Delivery receipt: [PDF CMS release](sources/pdf-cms-release-20261105.json).
The live entry is `/admin/bank?tab=pdf-library`. Library, Needs attention and Activity
reuse the existing workbench, inventory, review and module composition screens.
The initial scan reconciled 5,822 file locations: 1,979 registered papers, 258 empty
registered sources, one missing document registration, zero registered papers
without a matching scanned PDF, and zero conflicting PDF matches. There are
1,796 unlinked distinct PDF hashes across all document categories; 563 are found
under the question-paper folder. These are discovery candidates, not verified new
exam papers. The missing LDC registration has available bytes and 100 questions.

Production list/filter queries measured 0.305–0.362 seconds; the inspected answer
detail measured 1.055 seconds. Full staff visual QA on phone/tablet remains
unverified because no signed-in browser session was available. Component tests,
the built production entry and role boundaries were checked without bypassing login.

## Outcome

Give admins one compact place to find a source PDF, see what is missing, continue
its import/review, and confirm where its questions appear publicly. Extend the
existing CMS rather than introduce another content store or publishing system.
The learner interface stays compact: official key / our answer when relevant,
expandable explanation and evidence, and a private Report action. Internal repair
history stays staff-only; material uncertainty and scoring restrictions remain honest.

## Existing foundation and measured gaps

Existing screens include AdminExamInventory (exam expectations, registered papers,
source availability, question coverage and document/history details), PaperWorkbench
(upload, extraction, source comparison, draft review and guarded publication),
BankAdmin (questions, documents, reports and publication history), Editorial, and
versioned module composition. Inventory exam associations and learner module
membership are different and must stay explicitly distinguished.

The 5 November Oracle audit found 1,979 registered papers, 1,721 with questions,
258 with none, and 82,383 questions in a matching bank/DB sync. All ten workbench
drafts were published. One LDC 2025 Paper II lacks a paper-document registration;
this is not evidence that its PDF bytes are missing. These are dated baseline
measurements, not hardcoded dashboard totals.

The canonical Old_Questions folder contains 2,558 PDFs and the served source folder
1,980. Raw file counts cannot establish the number of unregistered papers: reconcile
hashes, paths, aliases, document types and source identities first. The current
expected-paper register is not a complete official archive census.

## Delivery sequence

### 1. Reconcile Oracle PDFs and expose the actionable backlog

Build a resumable, read-only archive inventory job against configured source roots.
Persist a timestamped staff inventory index with path, size, modified time, SHA-256,
document type, and links to registered source documents, paper IDs and drafts.
Reuse unchanged scan entries; hash changed files in bounded background batches.
Do not scan the filesystem or hash PDFs during page requests. Treat incomplete
scans as incomplete, and retain the last complete snapshot on errors.

Expose distinct filters for unlinked files, ambiguous matches, registered papers
with no questions, missing document registrations, and confirmed missing files.
Exact hashes suggest identity but do not authorize merging paper IDs; preserve
aliases and booklet/source variants. Never auto-delete or auto-publish on discovery.
Start remediation with the 258 empty registered sources and the LDC registration
mismatch, after checking exact file evidence. Show counts with their units and scan
time; show unknown coverage when no source-backed expectation exists.

Acceptance: scan all configured roots, reconcile duplicate/alias fixtures, recover
from interruption, and demonstrate accurate live drill-downs for the known gaps.
The inventory must not modify bank content or expose private filesystem paths publicly.

### 2. Unite the existing CMS into a compact paper workspace

Use the existing bank admin area as the entry point, with Library, Needs attention,
and Activity views. Default to searchable, paginated rows instead of large cards.
Search title/exam/year; filter by document type, module and next required action.
Use one primary action per row: inspect source, continue import, review, or inspect
publication. Put hashes, technical metadata and full history in collapsed details.

Opening a paper keeps the selected filters and return position. Reuse the current
source preview, PaperWorkbench, Editorial and module composer through contextual
links; avoid duplicate editors. Summarize separate dimensions: file availability,
import coverage, review state, publication/sync, and learner module membership.
A PDF can be published with incomplete solution coverage; no universal green
“verified” status should conceal that distinction.

Acceptance: an admin can find a PDF, identify its gap and continue the existing
workflow without searching across menus. Verify phone/tablet layout, keyboard
navigation, loading/error/empty states and role-scoped access. Respect existing
review assignments and MFA; do not bypass login to obtain screenshots.

### 3. Connect intake, background jobs and publication receipts

Provide upload or choose-existing-source intake using the current workbench.
Reuse registered empty paper IDs; detect existing files/drafts before creating
another import. Show queued/running/failed/completed jobs with resumable, bounded
retries. Parser/OCR output remains staged. Make the next action and failure reason
clear; keep source comparison, corrections, reviewer ownership and approvals in
their established workflows. Edits invalidate stale approvals.

Display the existing guarded publication receipt and subsequent bank/DB sync
readback. Do not call an item live merely because extraction or approval finished.
Batch discovery/extraction may be supported within worker limits; publication must
retain per-payload checks, shared bank locking and idempotent recovery.

Acceptance: rehearse one existing-empty-source import and one new-source import on
a disposable database, including duplicate submission, stale approval, failed job,
and interrupted publication recovery. Verify no duplicate questions or receipts.

### 4. Make learner coverage and content quality actionable

Show which LDC, UDC, Assistant and other modules include each paper, with a link to
the existing versioned composer and its preview before publication. Show expected
versus imported counts only where expectations have evidence. Separate official
final/provisional keys, reviewed solutions, inferred answers, missing answers,
missing explanations and written questions using existing answer-status rules.
Route private learner reports into the established staff queue with source context.

Prioritize source-backed gaps in active LDC/UDC/Assistant modules, then other active
modules, then the historical archive. Missing source context and conflicting keys
come before explanation polish. Importing all 258 papers is a separate content
backlog, not an automatic consequence of shipping this dashboard.

Acceptance: module previews match existing membership and retain source IDs;
public scoring/reveal behavior and private reports remain unchanged. Public cards
must not gain admin workflow controls or misleading claims of verification.

## Release and completion

Ship incrementally: archive reconciliation first; unified navigation second; job
and receipt integration third; coverage and prioritized import work fourth.
Use new migrations for any index/job schema, rehearse on a disposable dump clone,
and test authorization, scan matching, retry/idempotency and source preservation.
Run relevant frontend checks and build locally; deploy with existing tooling.
Record baseline/readback counts, permissions, source protections and sync checks
for each release. Retain rollback artifacts; preserve immutable history.

CMS completion means the inventory is reconciled, the end-to-end workflow is
usable, failures are recoverable and public visibility is proven by readback.
Content completion requires separate evidence for each paper and its solutions.
No new CMS framework, canonical bank, or broad approval exception is required.
