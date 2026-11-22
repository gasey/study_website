# Finna guardian process — proposed implementation

## Superseded — guardian enrollment is out of launch scope

On 20 November 2026, the owner changed the audience to **18+ only**. Do not
continue guardian/provider/parental-consent implementation or treat the proposal
below as current launch work. Retain the existing adult-admission restrictions and
privacy/closure controls; do not infer ages or delete history. The
[adult-only plan](FINNA-ADULT-ONLY-PLAN.md) is the current scope.

## Historical proposal and implementation checkpoints

20 November 2026. The owner chose to include under-18 students, with a guardian
process to be designed. **Guardian verification and minor activation remain
unimplemented.** A local adult-declaration boundary and pending-enrollment UI
are now implemented behind a default-off flag. No production user has been
assigned an age or guardian status by this work.

## Current gap

Reviewed production email registration accepts email/password; Google callback
can provision an account. Neither production path collects age eligibility or verifies a
guardian. Guest identity can be created before registration and stores progress.
Google email verification, an email OTP, a paid card and a checkbox alone must
not be described as verification of a parent or lawful guardian.

## Legal design inputs checked on 20 November

The Act defines a child as under 18. Section 9 addresses parental consent and
restrictions on harmful processing, tracking/behavioural monitoring and targeted
advertising. Consent alone does not remove those restrictions.
[MeitY Act, sections 2(f) and 9](https://www.meity.gov.in/static/uploads/2024/02/Digital-Personal-Data-Protection-Act-2023.pdf).

Rule 10 describes checking an identifiable adult using reliable identity/age
details or an authorised token route. The education exception has conditions;
Finna's eligibility has not been established. Rule 1 phases Rules 5–16, including
Rule 10, to eighteen months after publication. These are implementation planning
inputs, not a statement that all provisions are already in force or that Finna
is exempt. [MeitY Rules, rules 1/10/12 and Fourth Schedule](https://www.meity.gov.in/static/uploads/2025/11/53450e6e5dc0bfa85ebd78686cadad39.pdf).
The annotated Act records the separate phased commencement of sections 7–17.
[India Code Act with commencement note](https://www.indiacode.nic.in/bitstream/123456789/22037/1/a2023-22.pdf).

## Proposed flow

1. Ask for an age category before creating a persistent study identity. Keep public
   reading possible where it needs no learner profile. Design guest handling as
   well as signup; a screen placed only after signup leaves the earlier gap.
2. For an under-18 learner, start a minimal, short-lived pending flow. Explain the
   requested data, uses, community visibility and guardian controls. Do not activate
   a learner account, save study behavior, send reminders or adopt guest progress
   before the required review/consent completes.
3. Let the parent/lawful guardian identify themselves, confirm their relationship
   and complete an appropriate adult identity/age verification method. Select and
   review that method before implementation; no provider, ID-document upload or
   paid identity service is selected by this document.
4. Record the minimum verification result/reference, guardian relationship,
   consent scope, policy version, time and withdrawal status. Avoid retaining raw
   identity documents when the selected method can supply a sufficient result.
   Choose pending-flow and evidence retention before storing real records.
5. Provision/link the learner transactionally only after successful verification
   and permitted processing review. Default public profile, leaderboard exposure,
   community posting/sharing, referrals and outbound reminders off for minors;
   decide separately which features can safely be made available.
6. Give the guardian a reviewed way to inspect permissions, withdraw consent and
   request export/closure. Withdrawal must stop relevant processing and delivery,
   retire sessions and apply the documented retention exceptions. Define adult
   transition without silently broadening consent on a birthday.

Proposed server states: `pending → verified-and-consented → withdrawn`; expired,
rejected and superseded pending attempts cannot activate an account. Each consent
change requires a new version so a stale callback cannot restore withdrawn consent.
Account authentication and consent are separate checks.

## Backend and mobile acceptance requirements

- Enforce eligibility in email registration, Google provisioning/linking, guest
  creation/adoption, browser-to-mobile handoff and every protected learner writer;
  enforce it on the server so older APKs/direct requests cannot bypass it.
- Review attempts, mastery, streaks, XP, review schedules, activity collection and
  ranking for child tracking/monitoring restrictions. Do not enable them merely
  because the guardian has consented; do not assume the education exception.
- Reject replayed/expired approvals, cross-account guardian links and races between
  approval, withdrawal, account closure and mail reservation. Consent receipts
  must not contain passwords, bearer tokens or raw identity documents.
- Test no learner provisioning/progress/email before approval, callback replay,
  withdrawal during mail/answer requests, account switching, offline pending work,
  older-client requests, export scope and backup-restore handling on fixtures.
- Provide accessible explanations and recovery when verification fails. Establish
  how existing accounts are assessed without inventing their ages or guardian links.

## Remaining decisions and release gate

Select a suitable verification method, minimum data/retention, guardian request
procedure, minor feature permissions and treatment of existing accounts. Review
the legal application to Finna's actual activities and commencement dates before
release. Publish language matching the working controls, then verify web and
signed Android paths. Migration0122 is now reserved for the local foundation and
is unapplied in production. Index0123 is also reserved/unapplied after its fresh
dump-clone rehearsal;0124 is the next unreserved number at this checkpoint.
Check that allocation afresh before creating another migration.

## Implemented locally — not deployed

Migration0122 adds account age categories, short-lived opaque browser age flows,
privacy requests and append-only request events. `AUDIENCE_GATE_ENABLED` defaults
to false. When enabled, new guest/email/Google study identities require an adult
declaration; under-18 enrollment always reports unavailable. Existing accounts
must explicitly confirm their own age category before study access. An existing
under-18 account cannot self-upgrade through an adult browser choice.

The central boundary covers web and old native credentials. Mutation transactions
recheck eligibility under a row lock before commit, rolling back stale admission
when a restriction changes concurrently. An existing account choosing under 18
revokes other web/mobile sessions and disables review reminders. Privacy requests,
export, closure and recovery remain available; no child learner activation or
identity-document upload/approval endpoint exists.

The next local continuation extends that boundary outside signed-in requests:
review-reminder scheduling, reservation and delivery require an adult declaration
when the flag is on. Delivery rechecks after locking the account, before reading
the due queue or calling mail transport. Unknown ages are withheld too. Existing
subscriptions are not treated as age verification.

Calendar reminders use the same eligibility filter. A short transaction advisory
lock serializes their set-based notification inserts with an under-18 declaration;
the insert takes a fresh statement snapshot after waiting. That declaration also
disables official-calendar reminders, cancels pending review-reminder outbox rows
and revokes active calendar bearer URLs with a new version. Calendar entries and
delivery history are retained. The bearer feed itself checks eligibility after an
account row lock and rechecks token validity, so a stale reader cannot bypass a
concurrent restriction. An already retrieved calendar cannot be remotely erased.

Weekly XP and game standings exclude missing/under-18 categories before ranking
when the flag is on. Existing public opt-ins do not override eligibility. The
default-off compatibility behavior remains covered by existing tests. No migration,
provider integration, actual message, production deployment or new APK is involved.

Learning reconciliation now has a separate local admission guard. With the age
flag on, the worker selects adult accounts only and takes a shared transaction
lease for that account before locking its job. Busy candidates are skipped in a
bounded ten-account lookahead; skipped candidates release their temporary locks.
The worker rechecks category and active account state with a fresh statement
snapshot before any queue/mastery/activity rebuild. The lease lasts until commit.
An under-18 declaration or account closure takes the exclusive lease before its
user/job/reward-related locks, so admitted work finishes before restriction commits.
Other accounts' learning leases are independent.

Missing/under-18/closed accounts' jobs are not marked done or failed: requested and
processed versions, cursors and historical records remain. An eligible adult can
resume the pending work, using the existing replay-safe reconciliation. Nightly
enqueue filters the current age category, and the worker heartbeat reports the
number of age-restricted jobs still pending. Existing source-correction triggers
can still invalidate a job, and a stale nightly selection may still enqueue a
version hint; neither authorizes a study rebuild because final admission rechecks.
No ages are inferred, no queued history is deleted and no guardian approval exists.

This guard concerns the durable learning reconciler. It does not establish the
permitted scope of minor study tracking, stop every synchronous/SQL-trigger path,
or finish the reassessment and community review below. The flag stays off.

### Background review still open

| Path | Current treatment / remaining work |
| --- | --- |
| Review reminders and official-calendar inbox reminders | Local eligibility checks and restriction serialization described above; synthetic checks only |
| Calendar subscriptions and weekly standings | Local eligibility checks; no retroactive erasure of downloaded calendars or public captures |
| Learning reconciler | Local worker admission/lease, fresh category recheck, parked job preservation, closure/restriction serialization and pending-job heartbeat are implemented. Finish real consent/permission policy and rollout review; this is not permission to process minor study behavior |
| Game lifecycle | Local start/advance/finish and worker sweep admission release restricted seats, retain saved choices and prior receipts, preserve eligible opponents' deadlines and append a permanent room/account ending marker. Shared processing leases serialize with restriction/closure. All seven modes/replay/timeout/index/race checks pass; stored member/identity exposure still needs separate review |
| Reassessment and correction notices | Local active-adult admission and processing leases now guard derived assessments/notices. Restricted/busy pages roll back without consuming cursors or acknowledging jobs; bounded lookahead can process other source jobs/events. Source invalidation continues and original results stay. Same-page eligible accounts also wait; real permission/consent and rollout remain open |
| Account recovery/security mail | Separate from optional study reminders. Recovery remains available to restricted accounts; no email sent by this continuation |
| Retention and operational jobs | Continue current bounded cleanup and health receipts; do not invent new durable-data expiry or backup pruning |
| Referrals and community/Desk exposure | Referral activation stays off. Local subject checks now guard selected creator/community/material/Desk/Inbox and game/Cup readers; immediate Desk/discussion notices use processing leases. Historical private controls and moderation/export access remain explicit exceptions; full withdrawal/permission and SQL-trigger review stay open |

This is a safety foundation, not completed guardian support. Real verification,
consent evidence/withdrawal, existing-account rollout, background study-processing
review, minor feature permissions and retention/restore decisions still need work.
Do not enable the flag on production as a substitute for those steps.

The local game continuation also checks voluntarily departed participants before
finalization, since the original controller can process their saved choices.
A busy account defers the room and rolls back temporary admission leases. Restricted
waiting hosts cancel the lobby; running opponents keep their original deadlines.
The append-only event contains only the existing room/account relationship and
an audience-access ending action, with no birth date, document or category value.
Confirmation or turning the flag off does not reactivate that room's choices.
Migration0123 adds only its partial unique index; no existing rows are rewritten.
This is processing admission, not completed community withdrawal, consent or
permission to track minors. See the [game receipt](../reports/finna-game-eligibility-20261120/README.md).

The local reassessment continuation guards direct mock/attempt derivation and
in-app correction fanout. Admission uses a fresh active-adult read after a
nonblocking shared account lease. A paused mixed page rolls back earlier writes,
temporary locks and cursor changes; individual jobs retain their pending state
without restriction failure counts. Eligibility can resume the original work with
existing unique hashes/notice keys. The ten-job/event lookahead is bounded: it does
not guarantee progress past arbitrarily many paused queues, and eligible accounts
on the same page also wait. Source/appearance invalidation still queues the need
for review without authorizing restricted learner derivation. Closure's original
email removal means closed accounts are absent from notice recipient selection.
No schema or guardian verification was added; other synchronous/SQL-trigger and
community/identity paths still require review. See the [reassessment receipt](../reports/finna-reassessment-eligibility-20261120/README.md).

Local shared-subject readers now require active-adult eligibility when the age
flag is enabled, while retaining all stored posts, material revisions, votes,
Desk memberships/shares/calendar entries and game/economic history. Blocks,
publication and assessment disclosure remain conjunctive. Counts/pages/ranks omit
restricted subjects before slicing. Reserved team attribution creates no age
record. A restricted Desk owner's room becomes unavailable for shared reading;
eligible members retain leave/decline controls. Owned export, private relationship
management and privileged moderation retain their intentional historical scope.
Immediate social/Desk notices use nonblocking shared account leases, coordinated
with restriction/closure; suppressed optional notices are not later replayed.
Reads reflect their SQL snapshots and cannot recall previous captures. This does
not implement full withdrawal, identity verification, minor-processing permission
or erasure. A source-bound synchronous review identifies remaining SQL activity,
publication-credit and tier triggers, plus administrative review notices. These
need separate database policy, lock-order and reversal tests, a new migration and
fresh clone rehearsal before activation. [Shared-subject receipt](../reports/finna-community-eligibility-20261120/README.md).

Local0124/0125 add default-off database activity admission and two-subject guest
transfer. They preserve attempts, assessments, receipts and durable reconciliation
hints. Busy/restricted activity can be rebuilt by the existing admitted worker
when eligible, without migration-time backfill or a new award path. Direct SQL
restrictions use nonblocking exclusive leases and require retry55P03; API
restrictions acquire the exclusive lease before row locks.0125 fixes the reproduced
direct-call ownership race. API startup checks policy/flag agreement, which is not
live reconfiguration: a future activation must stop/drain every writer and be
separately reviewed. Keep the database policy off until positive publication/reversal,
community tier and remaining processing/guardian/launch gates are complete.
This is not a malicious-database-role sandbox, guardian verification, consent or
permission to process minors. [Activity/transfer receipt](../reports/finna-synchronous-activity-20261120/README.md).

Local0126 adds database admission for new publication reward recipients, before
reward locks and derived writes. Restricted/busy publication still records its
source credit and existing administrative audit; the trusted original event is
not automatically replayed after confirmation. Exact existing negative reward
corrections remain available even for closed accounts and with policy off; this
preserves immutable ledger integrity without recomputing learner results or issuing
cash refunds. Source/quorum/cap/receipt bodies are unchanged. Administrative review
and retained governance metadata are not claimed fully reviewed for guardian use.
Community voter/target/tier SQL and legacy contributor reads, real verification/
consent/withdrawal and remaining
processing/retention/launch gates still block activation.0126 remains unapplied;
keep database policy/age/checkout/referrals off. [Publication receipt](../reports/finna-publication-eligibility-20261120/README.md).

Local contributor/voter read guards now filter legacy ranks/pages and current
Helpful/visible weekly totals, preserving attribution choices, blocks, disclosures,
source bank content and stored credits/votes/milestones. They do not provide a
transactional target-processing lease, consent/withdrawal, current SQL tier guards
or guardian verification. The SQL tier migration and administrative history policy
remain separate blocking work. No schema/production change;0127 remains unreserved
and every launch flag stays off.
[Contributor/voter receipt](../reports/finna-contributor-visibility-20261120/README.md).

Local0127 guards database current tier weighting for active registered adult
authors/voters and admits target plus complete candidate voter sets before immutable
milestone capture. Optional busy capture skips its whole score; existing milestones
stay. Declarations/closure capture eligible standing before loss, and attempt
maturity-boundary counting requires voter admission. No consent, actual guardian
verification, minor-processing authorization, erasure or delayed-award replay is
inferred.0128 separately prevents temporary relations influencing trusted tier
calculation. Both remain unapplied in production and all launch flags remain off.
Separate CMS material reward/reversal admission, administrative review/CMS/quorum/
audit/history decisions and actual verification/
consent/withdrawal, retention and launch procedures remain blocking work.
[Tier receipt](../reports/finna-tier-eligibility-20261120/README.md).

Local CMS first-publication rewards now check registered active-adult recipient
admission through the database policy before reward locks/derived writes. 0129 guards
new material/contribution optional in-app workflow notices, including SQL publishers;
missing/busy/restricted targets or missing policy suppress the copy while source/
audit and exact historical archive corrections retain integrity. Original trusted
publisher retries cannot replay a skipped notice after confirmation/flag-off.
Existing source decisions, grants/quorum/reviewer proof and private notice/history
controls retain their existing scope; no historical reviewer age or legal basis is
inferred. Authorized governance is independent of social blocks. These technical
guards do not implement real guardian verification, consent evidence/withdrawal,
permitted minor processing or legal retention. Those decisions and procedures remain
open. 0129 remains unapplied; every launch flag stays off. A future guarded rollout
must pair current API, publisher and all required migrations after draining writers.
[CMS/notice receipt](../reports/finna-cms-notice-eligibility-20261120/README.md).


20 November operator follow-up: [private request, restore and refund procedures](FINNA-PRIVACY-OPERATIONS.md)
are now documented. The local read-only restore checker compares selected current
controls, requires candidate bearer/queued-mail quarantine, preserves immutable
send history and reports uncertainty for separate reconciliation. It does not
establish reference currentness, perform repairs, verify a guardian or authorize
promotion. Retention periods, permitted minor processing, legal/tax decisions and
real provider/mail acceptance remain open; no production change or message.
[Source-bound evidence](../reports/finna-restore-privacy-preflight-20261120/README.md).
