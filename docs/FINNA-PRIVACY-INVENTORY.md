# Finna privacy implementation inventory

Current audience update, 20 November: **18+ only**, superseding the earlier
under-18 plan. Guardian-provider onboarding and minor enrollment are out of scope.
Existing/accidentally supplied data still needs privacy handling. The
[adult-only plan](FINNA-ADULT-ONLY-PLAN.md) governs launch; older checkpoints below
are historical. Retention periods and production policy activation remain open.

Reviewed 20 November 2026, IST. Private policy preparation; no public notice has
been published by this review. The owner selected account export followed by
study-history deletion 30 days after successful account closure, with reopening
allowed during that window. Reopening before expiry cancels pending study-history
deletion. Recovery uses a single-use link to the previously verified email and a
fresh password; old sessions stay revoked and Google/MFA must be reconnected or
set up again. Exact records/fields and exceptions remain unresolved; current
behavior still retains most study history after closure. Current production
source copies and read-only host observations are in
`reports/finna-policy-readiness-20261120/`. No learner rows were queried. Source
inspection establishes implementation behavior, not complete provider contractual
terms or observed browser traffic.

## Data, recipients and purpose

| Category | Reviewed implementation | Publication work remaining |
| --- | --- | --- |
| Hosting and backups | Oracle host serves the API/PostgreSQL. The installed paired snapshot script dumps the workflow database and selected workshop files to private server storage. Its source explicitly does no pruning or cloud upload | Confirm hosting region, infrastructure backup/snapshot settings, other copies, access controls and deletion schedule. This job alone does not establish an exhaustive backup inventory |
| Account and security | Email, handle, optional profile, password hashes, Google identity links, sessions, MFA material, security events. Login controls hash account/IP identifiers; hashing does not make these records anonymous | Document identity checks for privacy requests and the purpose/expiry of security metadata |
| Study and community | Answers, progress, mastery, review schedule, exams, notes/calendar, posts and chosen sharing/profile visibility | Retention after inactivity/closure and treatment of public text need an explicit policy |
| Resend | Deployed account mail and opted-in review digest use SMTP delivery. Recipient address and message content go to the transport. The reviewed mail transport avoids logging recipients/bodies/secrets | Verify provider-side retention/subprocessors and distinguish SMTP acceptance from delivery. Owner support Gmail is a separate channel |
| Google sign-in | Optional OAuth `openid email`; server exchanges authorization code and verifies identity. Creating an account can happen in the callback | Explain identity-link retention and validate this entry point in the adult-only rollout |
| Google Fonts | Deployed asset inventory checks font-server references; local `web/index.html` loads Google Fonts CSS and preconnects to Google font hosts | Describe external resource requests. Exact browser headers and provider-side retention were not measured |
| Razorpay | Checkout flag is false. Prepared API uses provider subscription/payment identifiers and status; local unapplied migration 0132 adds per-payment refund aggregates and a `billing_refunds` reference/status ledger. UI has a checkout script reference | Before activation, verify actual checkout data, provider notices, invoice identity and refund/reconciliation operations. The local webhook draft ends subscription-derived access only after a provider-confirmed processed full refund; it does not issue refunds or cancel renewals, and has not been deployed/configured against the provider. Do not say enabled checkout or no external payment processing |
| Optional external destinations | Local UI contains explicit WhatsApp sharing, Google Calendar, source links and older lesson links | These are user-triggered destinations, distinct from automatically loaded resources; inspect the exact published routes before finalizing the list |
| OpenStreetMap | Current entry-page dependency traversal reaches an Atlas bundle containing OpenStreetMap tile URLs. Base-map use can send tile requests to that provider | Source reachability is not captured browser traffic; review provider-side terms and retention |
| Staged Atlas/Desk extensions and referrals | Additional activity/referral records are local drafts. Local account export/closure source differs from the production source | Do not publish staged extensions as already rolled out. Existing Atlas base-map references are listed separately above |

The active-asset inventory follows 148 literal JS/CSS dependencies from the
current deployed entry page, including lazy routes. It distinguishes that graph
from 27 retained Atlas and 27 retained Account bundles found by a directory-wide
scan. It is a bounded source audit, not proof that every reachable route was used
or every possible external request was captured.

Finna's supplied support address is hruaitluangasailo20@gmail.com. Users who email
it send their message and address through the chosen email services. This review
did not send an email, test mailbox operation or select a support-mail retention period.

## Retention and closure facts

These are eligibility thresholds in bounded jobs, not guaranteed deletion times.
The hourly worker can defer on errors/locks and processes at most 500 rows per
transient category per cycle.

| Records | Current code behavior |
| --- | --- |
| Web/mobile sessions | Session creation must be over seven days old; expiry or revocation must also be over seven days old. Mobile sessions with no live parent have an additional eligibility path, still subject to creation age. Latest removed sign-in activity can survive in a security event |
| Daily request counters | Eligible when the IST date is over 30 days old and `updated_at` is over 30 days old |
| Review rate buckets | Eligible over one day after expiry |
| Login attempts | Worker threshold is 30 days. Authentication requests also delete attempts older than one day. This is not a guaranteed 30-day retention period |
| Google/mobile auth flows | Worker threshold is seven days after expiry. Google flow creation also deletes already-expired Google flows, and successful callback consumes its flow |
| Empty generated guests | At most 20 per cycle; account/credential creation and credential expiry must each be over 12 months old, with strict default-state and no-linked-data checks. Guests with progress are protected; this is not deletion of all guests after one year |
| Registered account closure | Revokes sessions; removes Google link, pending unsent account mail, review digest preferences/outbox, MFA secrets/recovery codes, calendar entries and private desk document; disables feed token/public profile and sharing; nulls email/password/name/avatar and randomizes the handle. Requires resolving billing, staff and desk ownership blockers |
| Retained after closure | Tombstone/internal account ID, attempts/progress, public post text and economic/access/moderation/security history can remain. Sent mail receipts and consumed token metadata are not universally erased by closure. Public posts may still contain personal information in their text. Verified-email reopening is staged locally in unapplied migration 0130; selected 30-day study-history deletion remains unimplemented. Neither decision sets public, economic, security, email or backup retention |
| Login backoff and durable receipts | No general expiry found in the reviewed cleanup for account/IP backoff, durable progress, security/economic/billing/replay/adoption records. Do not equate this with an approved permanent retention policy |
| Database snapshots | Installed paired backup script has no pruning. It includes database records present when taken; later account closure does not rewrite old dumps. Provider snapshots and separate manual/recovery copies need inventory |
| PostgreSQL logs | Current host policy rotates weekly and retains 10 rotated files, with compression and `notifempty`. This is file-count rotation, not a guaranteed 70-day erasure limit. Application, proxy, journal and provider log retention remain unconfirmed |

Account export returns selected owned fields, excludes credentials/answer keys/
moderator notes, and withholds active-assessment records until the assessment ends.
It is not a claim that every retained internal record is included in that download.

## Work before publication

- Implement the owner-selected 30-day post-close study-history deletion only after
  confirming exact records/fields, exceptions and legal/accounting review. The
  selected start is successful account closure; reopening before expiry cancels
  pending study-history deletion. Verified-email reopening is staged locally in
  unapplied migration 0130 and still needs release-build and real-mail validation. Separately
  decide retention by purpose for public text,
  security metadata, provider copies and backup expiry.
- Define identity verification, request tracking, erasure exceptions and applicable
  response deadlines. The owner's no-fixed-deadline choice concerns refund support;
  it does not settle privacy-rights or mandatory consumer deadlines.
- Define restore handling so removed identifiers/withdrawn consent are not silently
  reactivated when an older backup is restored; verify this in isolation.
- Inventory proxy/application/journal and provider logs, infrastructure snapshots,
  any other external assets and any mobile telemetry/update services separately.
- Complete guarded adult-only rollout and existing-account handling under the
  [adult-only plan](FINNA-ADULT-ONLY-PLAN.md). Do not enable minor enrollment.

This review leaves `RETENTION_AND_REQUEST_POLICY` open. No deletion sweep, backup
pruning, schema change, provider configuration change or deployment was performed.

## Local privacy tooling — not deployed

Migration0122 adds age-category declarations (no date of birth), opaque hashed
browser-flow references expiring after one day, request type/status and append-only
request events. Expired browser flows are eligible for bounded 500-row cleanup
on new declarations and in the hourly worker when the age boundary is enabled.
This is a cleanup threshold, not an exact erasure time.

Request forms store no free-text personal details, ID images or copied email.
The signed-in account can list/withdraw its requests; the existing owner role can
review and mark a status with session/CSRF/MFA/version checks. Supported account
export includes audience and request records, excluding browser hashes and request
replay keys. Completing a request record does not itself erase data or change age eligibility.
Retention for these privacy request records remains part of the unfinalized schedule.
Under the current 18+ decision, guardian enrollment is out of launch scope; see
the [adult-only plan](FINNA-ADULT-ONLY-PLAN.md).

The subsequent local background-boundary work cancels pending review reminders,
disables official-calendar reminders and revokes active calendar-feed credentials
when an existing account declares under 18. It retains private calendar entries,
sent/cancelled delivery records and historical study/economic data. With the
default-off age flag enabled, both reminder paths and calendar feeds require an
adult declaration; weekly standings omit unknown/under-18 accounts. Previously
downloaded calendars/public captures cannot be recalled. This is not a durable retention schedule. This under-18 transition behavior is a
historical implementation detail from before the 18+ decision; see the
[adult-only plan](FINNA-ADULT-ONLY-PLAN.md).

The next local slice parks the durable learning reconciler's restricted jobs
without deleting or acknowledging them. Requested/processed versions, attempt
cursor, review schedule, mastery, activity and economic history stay retained.
Adult confirmation can allow the existing pending work to resume. A shared
account-specific processing lease serializes admitted work with restriction and
closure; skipped busy candidates release their locks. Pending age-restricted work
is counted in the worker heartbeat. This changes processing admission, not data
retention, and does not recall data in backups or implement guardian consent.

The local game guard now releases restricted seats, clears their public-result
opt-in and retains an append-only room/account `audience_access_ended` event.
No birth date, guardian document or age-category value is included in that event.
Saved choices and all prior attempts/economic history remain; the marker prevents
later rejoining/finalization of that room even after confirmation or flag-off.
Index0123 changes lookup/uniqueness only and is unapplied in production. Retention
for events/history remains part of the unsettled schedule, and existing room
member/identity exposure still needs separate review. This is not erasure or
completed guardian consent. [Game receipt](../reports/finna-game-eligibility-20261120/README.md).

Local reassessment/correction admission now preserves restricted accounts' pending
cursors, failures and jobs by rolling back the current mixed page. It appends no
new assessment or notice for that paused page. Eligible accounts on the same page
also wait; bounded lookahead can process other source jobs/events. Source integrity
invalidation continues, while original results and existing assessment/notice/
economic history remain retained. Closure's original email removal excludes that
account from notice recipients without adding a new erasure policy. Admission
uses the existing restriction/closure account lease and creates no consent record,
provider data, age inference, retention schedule or new schema. [Reassessment receipt](../reports/finna-reassessment-eligibility-20261120/README.md).

Local public/shared subject filters now omit missing/under-18/closed subjects from
selected creator/community/material/Desk/Inbox/game/Cup responses when the age flag
is enabled. They do not delete content, relationships, calendar entries, results,
notices, votes, tier milestones or economic receipts. New optional social/Desk
notices are suppressed under an account-processing lease for restricted/busy
recipients; suppressed notices are not automatically replayed on confirmation.
Owned exports, private relationship controls and privileged moderation keep their
explicit historical scope. Responses use SQL snapshots and cannot retract prior
captures. This creates no new retention policy, verification record or guardian
consent. SQL activity/publication/tier trigger handling and administrative review
notices remain a separate source-bound follow-up. [Shared-subject receipt](../reports/finna-community-eligibility-20261120/README.md).

Local0124 introduces one singleton boolean database policy, containing no learner,
guardian or provider identity.0125 binds direct activity writes to the exact admitted
owner after a concurrent transfer. Synchronous activity can be deferred with its
existing source/queue history retained; the admitted learning reconciler can rebuild
it later. Guest transfer checks both subjects and retains immutable assessments and
its existing receipt, without new rewards or age inference. The SQL restriction
retry and API-before-row-lock protocol preserve admitted transaction boundaries.
Production was only read for two fresh dump clones; all original252-table values/
columns and indexes are preserved, then clones/dumps/private stages removed.
These migrations remain unapplied in production, policy/age/checkout/referrals off.
No retention deletion or adult-only rollout is implemented.
Publication/reversal/tier processing and administrative/history decisions remain.
[Activity/transfer receipt](../reports/finna-synchronous-activity-20261120/README.md).

Local0126 adds no new data tables or age inference. It suppresses new positive
publication reward derivation for restricted/busy recipients while retaining the
existing publication/credit/audit records. Original-event replay does not backfill
that reward. An exact existing reward receipt may still receive its once-only
negative correction for a closed account, including with policy off. This fixes
an old email-presence exclusion; original source, ledger and daily-slot history
stay retained. No learner result is rescored, record erased, cash refund issued,
retention schedule settled or guardian processing authorized. A fresh clone of
production preserves252 original tables/columns/values/indexes, then clone/dump/
private stage are removed. Migration0126 remains unapplied in production; all launch
flags stay off. Community/admin/history and retention/launch work remain.
[Publication receipt](../reports/finna-publication-eligibility-20261120/README.md).

Local legacy ranks/publication metadata and current Helpful/visible weekly totals
now filter eligible subjects at read time. Signed-in bilateral blocks personalize
the legacy lists, so they use private/no-store; anonymous rank reads create no guest
identity. Active mock/game/open-Cup title protection stays. Eligible actors can
remove their own old contribution votes. Source canonical bank questions, immutable
credits/reward receipts/milestones, votes and administrative history remain stored.
The support Helpful number is a current aggregate, not a rewritten audit record.
SQL tier current standing/privileges/Guide candidacy and milestone admission remain
unguarded work; this slice is not erasure, completed withdrawal or permitted minor
processing. No new data tables, migration, retention decision or production change;
0127 unreserved and all launch flags off.
[Contributor/voter receipt](../reports/finna-contributor-visibility-20261120/README.md).

Local0127/0128 add no data table or inferred age. Current tier weighting excludes
restricted targets/voters when enabled; complete candidate voter admission precedes
new immutable milestone persistence. Busy sets are not partially persisted. Source
votes, attempts, receipts and earned labels remain, with valid before-loss capture
including declarations/closure. A busy transient unrecorded milestone has no durable
replay queue. Read-only current views are point-in-time and write no audit. Explicit
public-before-temporary relation lookup prevents app-created temporary vote tables
from altering privileged capture. No historical initialization/award, erasure,
retention schedule, consent or permitted minor-processing decision is supplied.
Two successful252-table production-dump clones preserve original data/indexes; an
intermediate helper/SSH failures and all four clone/dump/stages are cleaned.
Both migrations remain unapplied; separate CMS publication rewards/reversals, administrative notice/history and real guardian/
retention/launch procedures remain. Keep every launch flag off.
[Tier receipt](../reports/finna-tier-eligibility-20261120/README.md).

Local 0129 adds only an INSERT trigger/function for optional material/contribution
workflow notice copies; no table, inferred age, notice replay queue or history
rewrite. Missing/busy/restricted recipients and missing operator policy suppress
new copies, while source/audit/archive integrity continues. Existing notices and
read controls and unrelated account/system notices remain. The trusted publisher's
immutable source event prevents delayed original-notice backfill. CMS positive
rewards now use the same database recipient lease before claims/ledger; its prior
reward mutex-onward and reversal body remain byte-identical. Original claim amounts
reverse once without current recipient eligibility, preserving gross cap/history.
This is trusted workflow integrity, not new protection against arbitrary privileged
claim/ledger tampering. Existing reviewer/grant/quorum/source proof and retained
private governance/audit retain their authorization scope. No legal retention or
adult-only rollout is settled. Fresh 252-table dump-clone apply preserves all
original data/indexes and is cleaned. 0129 unapplied; actual guardian verification/
consent/withdrawal and retention/backup/restore/request/tax/refund/launch remain.
Keep database policy, age, checkout and referrals off.
[CMS/notice receipt](../reports/finna-cms-notice-eligibility-20261120/README.md).


20 November operator follow-up: [private request, restore and refund procedures](FINNA-PRIVACY-OPERATIONS.md)
are now documented. The local read-only restore checker compares selected current
controls, requires candidate bearer/queued-mail quarantine, preserves immutable
send history and reports uncertainty for separate reconciliation. It does not
establish reference currentness, perform repairs, verify a guardian or authorize
promotion. Retention periods, permitted minor processing, legal/tax decisions and
real provider/mail acceptance remain open; no production change or message.
[Source-bound evidence](../reports/finna-restore-privacy-preflight-20261120/README.md).

## Private local recovery copies — 21 November 2026

The actual restore rehearsal copied the selected paired backup and an independent
read-only production `pg_dump` to
`/mnt/linux-storage/finna-restore-sandbox-20261121-6y96hgau`. This is a separate
mode-0700 local storage location containing private dumps, restored databases,
extracted workshop files and row-fingerprint/diagnostic evidence. The socket-only
PostgreSQL cluster has no TCP listener and is stopped. No app, mail worker or
scheduler is connected. Candidate credential retirement was tested locally; the
original dump files and reference still require the same private handling.
These copies must be included in the backup/recovery-copy inventory and reviewed
retention/removal procedure; no general expiry is selected here. Exported report
receipts contain aggregate counts and source/file hashes, not account records or
row fingerprints. No production records were changed.
[Actual clone receipt](../reports/finna-local-restore-rehearsal-20261121/README.md).


## Additional private recovery material — 21 November 2026

The same 0700 sandbox now also holds the complete third database preview,
`matching-workshop.tar.gz` / `matching-workshop/`, and
`registered-documents.tar.gz` / `registered-documents-recovery/`, and
`referenced-dot-pdfs.tar.gz` / `referenced-dot-pdfs-recovery/`. These include
original/source/served PDFs and figures, private workbench uploads, registered
evidence and current matching bank/provenance inputs (141,461 unique files).
All captured file hashes and the explicitly checked snapshot asset references
verify. The captures are read-only source access; no source writer was paused.
Private row fingerprints, source manifests/reference/gap metadata and raw
diagnostics remain inside that sandbox. No private leaf-file list or raw rows are
exported to reports. The cluster is stopped and no app/mail/publisher is attached.
Include these copies in the reviewed retention/removal inventory; no general
expiry, pruning or source-deletion decision is selected by this rehearsal.
This is a local saved-snapshot check, not independent offsite continuity, final
currentness, crypto-key recovery or public launch approval.
[Receipt](../reports/finna-full-copy-recovery-20261121/README.md).


## Original-key encrypted recovery copy — 21 November 2026

The owner reported no known separate key backup. A new encrypted key archive is
at `/home/hruaia/.local/share/finna-secret-recovery/20261121-original-mfa-key/mfa-key.json.age`
under a 0700 directory, with mode 0600. It contains the original MFA/mail/digest/
reopen key and minimal source metadata, encrypted to the public SSH identity
corresponding to `/home/hruaia/.ssh/id_ed25519`. The private SSH identity is required
for decryption and was not copied or modified. The archive and nearby instructions
are outside the repository and reports. No plaintext key was written.
The backup was restored in process memory, verified against the saved pending-MFA
record and synthetic payloads, and rejected with an unrelated identity/tampering.
It is independent of Oracle, but not of this computer; separately protected
identity/second-location recovery remains unverified. No general expiry/pruning
schedule is implied. Include this secret backup and the retained private diagnostic
material in the reviewed retention/removal inventory.

The two disposable retention-check database copies were removed after recording
aggregate evidence; the original three private recovery/evidence databases remain
unchanged. Schema-only catalog reports contain column/constraint/trigger metadata,
not learner rows. Raw fingerprints and diagnostics remain in the private sandbox.
[Receipt](../reports/finna-deletion-key-recovery-20261121/README.md).


## Private writing/link cleanup draft — 21 November 2026

The staged 0133 scope now explicitly covers the complete rows of essay_drafts,
user_question_bookmarks, material_bookmarks and user_calendar_saved after base
study cleanup, continued closure past 30 days and hold checks. The new completion
field and minimal security event distinguish it from the earlier 0131 scope.
Shared source records and other learners' records remain. No key/identity file,
provider or public policy location changed. Migration/flags remain unapplied/off.

The restored-clone rehearsal produced two disposable copies; both were removed
after validation. Original three private evidence/recovery databases remain.
Private fingerprints/raw diagnostics stay in the existing 0700 sandbox and are
not exported. New reports contain only aggregates, code and schema definitions.
Other preferences, shared/support/moderation and provider/log/backup copies still
require separate retention/hold/restore reconciliation.
[Procedure](FINNA-PRIVATE-STUDY-RETENTION.md) ·
[Receipt](../reports/finna-private-study-retention-20261121/README.md).
