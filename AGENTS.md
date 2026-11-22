# Instructions for agents

21 November IST — private writing and saved-link retention staged locally.
New migration 0133 adds a separate completion marker and bounded cleanup for
essay_drafts, user_question_bookmarks, material_bookmarks and user_calendar_saved.
It requires the original study cleanup to finish, a still-closed account past
30 days and no active study hold. Both worker flags default off; enabling the
private flag alone cannot run cleanup. Earlier 0131/0132 sources/receipts remain
unchanged. Four active-account write guards prevent post-close recreation; the
app cannot forge the new marker. No broader table grant or public policy change.
A separate read-only 0133-aware preflight compares seven exact controls. The
246 selected regressions pass, including 41 new cleanup/restore cases, plus
calendar/mobile/audience/reopen/hold/key regressions. The isolated restored clone
preserves all 273 tables / 2,687,970 original rows and
65 sequence counters; all old functions/columns/FKs/triggers survive.
Only the new column, two functions and five triggers are added. Migration does
not sweep real records; rollback-only synthetic holds/batches/retries/other-owner/
closed-write cases pass. Seven restore comparisons pass. All three temporary clones
were removed; the three prior evidence/recovery copies remain. Cluster STOPPED.
0133 is unapplied in production, as are the prior staged launch migrations;
no production connection, provider, restart, policy publication or phone operation.
Current code preimages preserve prior frozen bindings. New local proposal covers
four private relation families; other preferences/shared/provider/log/backups,
final currentness/decision replay, separate key/identity copy and rollout remain.
Report: reports/finna-private-study-retention-20261121/.
Procedure: docs/FINNA-PRIVATE-STUDY-RETENTION.md. Never replay one-shot operators.


21 November IST — deletion/hold and original encryption-key recovery checks.
New read-only scripts/check-restore-retention.py compares every account closure/
purge marker, all protected hold fields and complete reopen envelopes without
changing roles or exporting IDs/values. Both saved-snapshot candidates pass all
three controls; mpsc remains unable to inspect or edit holds. Restored schema
metadata covers 273 tables/20 views, 2,450 columns, 458 FKs (174 user/31 selected
study-root references) and 165 non-internal triggers. Four hold types, release,
expiry, grace window and idempotent cleanup pass with synthetic rollback-only
rows. All test-clone values/schema/65 counters and the source preview survive.
108 focused tests pass, including 34 new cases. The initial synthetic closure
fixture omitted contribution_public=false and was corrected; initial failure
receipts remain. The two disposable check databases were removed, not the three
prior evidence/recovery databases. Cluster is STOPPED; production cleanup remains off.
Owner reports no known independent key backup. Live key matches root-only mfa.env;
its one saved pending-MFA ciphertext decrypts with correct account binding. A new
age-encrypted original-key backup on this computer was restored in a fresh process
without plaintext files/chat/report output. Wrong identity/tampering are rejected.
It requires ~/.ssh/id_ed25519; do not delete that identity. A separate identity
backup and second location remain unverified. Other saved cipher families are
empty and tested synthetically. No production write, restart, mail or payment.
Selected study cleanup is not complete erasure: essay drafts, individual bookmarks,
shared/provider/log/backups and other unselected locations remain separate review.
Procedure: docs/FINNA-DELETION-KEY-RECOVERY.md.
Report: reports/finna-deletion-key-recovery-20261121/. Never replay one-shot operators.


21 November IST — local full-copy recovery completed against the saved snapshot.
A third private database, finna_recovery_preview_20261121, copies the complete
newer reference, preserving 273 public tables / 2,697,411 rows before quarantine.
All 9489 accounts match in every field; 21 privacy and 8 billing projections pass.
Retired 7 web sessions, 1 mobile session and 9441 guest credentials only in the
preview. All ten quarantine counts are zero. All other table values, schema and
65 sequence counters are preserved; both original evidence databases remain unchanged.
The old workshop bank did NOT match the newer DB. A separate read-only SSH capture
now recovers the matching bank generation and canonical/source/served PDFs,
figures, private workbench and registered documents. 141,461 unique files are hash-
verified, with no reference gaps in the explicitly checked source scope. Original
mismatch/error receipts remain unchanged. No production DB/application write,
publisher, heartbeat, mail, payment, release or phone operation occurred.
Cluster is STOPPED. This finishes the local snapshot rehearsal, not final source
currentness, service/key recovery, controlled cutover or public-launch acceptance.
Owner supplies invoice/contact address A/77, Chanmari, Aizawl, Mizoram, India;
private drafts and local policy previews updated; web typecheck/build pass.
Report: reports/finna-full-copy-recovery-20261121/. Never replay old operators.


21 November IST — account restore mismatch diagnosed, no repair performed.
scripts/diagnose-restore-accounts.py uses the unchanged privacy read-only helper
and exports only account/delta/field/dependency aggregate counts, never IDs/values/
fingerprints. All 8811 shared account rows match in every stored field; reference
has 678 additional open accounts without email, candidate-only and changed rows 0.
Of 174 direct account FKs, only guest_credentials has rows for those additions
(678). The app correctly cannot read account_study_history_holds; a separate
read-only local-owner count finds both hold tables empty without granting access.
Do not turn this into a blanket users overwrite, infer erasure permission or copy
guest credentials. New repair plan recommends a complete current paired restore;
an additive preview would require a third disposable clone and separately reviewed
source-bound delta. No merge/repair/new production snapshot, deployment, provider
or learner write occurred. Cluster is STOPPED. Both earlier preflights stay blocked.
16 new scenarios plus the existing privacy preflight regression pass 60 tests.
See docs/FINNA-RESTORE-REPAIR-PLAN.md and
reports/finna-restore-account-diagnosis-20261121/. Preserve older receipts/sources.

21 November IST — separate billing restore preflight.
scripts/check-restore-billing.py compares eight explicit billing/access projections
as read-only mpsc, including 0132 refund markers, payment/refund/webhook receipts,
account rates and owner/referral/earned grants. It never repairs or calls providers;
all users are included, write timestamps excluded, missing schema fails closed.
32 new scenarios and the selected existing billing/privacy suite pass 129 tests.
The retained private clones passed seven billing/grant projections but differ in
users' access inputs (9489 vs 8811 rows). The unchanged privacy operator still
blocks on users; all ten quarantine counts remain zero. The private cluster was
started only for read-only checks and is STOPPED again. The reference remains the
earlier point-in-time snapshot, not final currentness evidence. No production
connection, migration, app/mail/payment write or promotion occurred.
Report: reports/finna-restore-billing-preflight-20261121/. Keep all older receipts
and frozen sources intact; do not rewrite accounts/receipts to force a pass.

21 November IST — local refund integrity and actual restore follow-up.
The 0132 billing draft remains unapplied; current billing/privacy/recovery tests
pass 125 cases, including real mpsc-role refund provenance, paginated processed
totals and concurrent event receipts. No refund creation or renewal cancellation
was performed. See reports/finna-refund-integrity-followup-20261121/.
A separate private PostgreSQL cluster at
/mnt/linux-storage/finna-restore-sandbox-20261121-6y96hgau is STOPPED and contains
the selected paired backup and an independent read-only production snapshot.
Keep its dumps/row fingerprints/diagnostics private. The first clone migration
attempt failed on missing Atlas tables. A clean follow-up applied schema-only
dependencies 0116/0117/0119/0121, then 0122–0132; 0118 content seed stayed unapplied.
Original values in 252 tables per database survived the staged migrations.
124,996 files and bank/database pairing verified. A synthetic retention smoke
rolled back its rows and restored sequence counters; no real study history swept.
Candidate credential retirement was rehearsed locally, but the privacy comparison
remains BLOCKED on different users controls. Do not rewrite identities or declare
the old candidate promotable. No production migration, flag, writer pause,
heartbeat, mail or payment write occurred. Collection interval is not final
currentness/cutover evidence. See reports/finna-local-restore-rehearsal-20261121/.
Preserve earlier source-bound receipts and both failed/successful rehearsal scopes.

20 November IST — owner selects 18+ only.
The owner explicitly replaced the earlier under-18 audience: “just dont do below 18”.
Guardian enrollment/provider/parental-consent design is removed from launch scope.
Local join/sign-in, age notice and policy previews now state the adult-only rule;
new guardian request creation is rejected while historical idempotent receipts,
review/withdrawal and restricted-account privacy/export/recovery/closure remain.
No age is inferred, no automatic under-18 upgrade or history deletion is added.
The current plan is docs/FINNA-ADULT-ONLY-PLAN.md; the old guardian plan is marked
superseded, with historical receipts preserved. A purpose-by-purpose retention
proposal is in docs/FINNA-RETENTION-PROPOSAL.md. The owner has since selected
study-history deletion 30 days after successful account closure with reopening
allowed before expiry; the exact records, recovery channel and remaining category
periods are unresolved; only expiry of the temporary recovery envelope is staged.
No study-history deletion cleanup is authorized.
Retention/recovery, adult-only
rollout, invoice/tax/refund/provider acceptance and physical/human/content/healthy-
week/volume gates remain. All launch flags remain off; 0122–0130 are unapplied in
production, with 0130 staged locally for account reopening. No deploy, new APK,
phone, mail or payment action.
Validation is recorded in reports/finna-adult-only-policy-20261120/.

20 November IST — current signed Android account/offline-retry acceptance.
The verified installed preview 01a448a3 passes actual Chrome synthetic-B sign-in,
explicit account confirmation/app return and account restoration after process death.
Offline fresh question 100/C stays pending without a server attempt. An offline cold
start shows connection feedback; online restart revalidates the saved identity without
another login. Home → Saved questions → Collections → Resume collection restores C;
Home Continue creates a new set. One actual explicit retry creates exactly one attempt
and authoritative 0-correct/1-revisit feedback. Another cold restart preserves the
result with no duplicate. Sign-out and guest restart pass; native revocation is verified
and the remaining owned browser parent retired. Staging ends with 2 synthetic accounts,
6 attempts (one new), 0 mail, 0 active auth. No production learner writes or phone input.
All 11 app-only images inspected; scoped UID 10219 crash buffer empty without clearing.
Original radios/shell UID restored, private synthetic credentials removed and emulator
stopped/data retained. All 3 HTTPS roots return 200; lint/typecheck pass; 171 upload inputs, 815 prior
native/operator report files and 1,079 protected API/migration/web/operator inputs preserved.
No runtime/dependency/schema/service/new-build/flag change. Previous 143/33 suites retain
old scope; no full offline, physical TalkBack/carrier/tablet/performance certification.
Retained harness notes cover keyboard bounds, lexicographic question selection,
immediate sign-out and changed UID output parsing. Beta 11f7cbfb remains current.
Next: guardian/consent/permitted-processing and retention/current-state/recovery
choices, invoice/tax/refund/provider acceptance, physical/owner/content/healthy-week/
human/volume gates. iOS deferred; all launch flags remain off; 0130 unreserved.
Report: reports/finna-current-signed-account-recovery-20261120/. Preserve frozen targets.

20 November IST — local restore privacy preflight and operator procedures.
Added a read-only operator comparison for a distinct restored candidate and an
independently established current reference. Twenty selected identity/privacy
control projections include closure, password/Google/MFA, age declarations,
request/event versions, staff grants, sharing/preferences, closed private documents
and durable delivery receipts. Ten bearer/queued-mail categories must be quarantined.
Uncertain/reserved immutable mail history is compared and reported for review, not
deleted to force success; cancelled account mail with cleared ciphertext is inert.
The tool uses repeatable-read read-only mpsc, fixed public tables, candidate DB clock,
timeouts and private salted server hashes. Only aggregate results are emitted.
Missing schema/privileges or identical candidate/reference fail closed. It never
repairs, promotes, proves reference currentness or authorizes sending/activation.
107 scoped checks pass, including 44 new cases and existing restore/request/closure/
retention/deferred-billing checks. Initial 46-pass/1-fail fixture attempted a document
insert after closure and correctly hit the existing guard; corrected pre-closure
fixture and all failure/intermediate logs remain. Final source-bound inputs match.
All 1,079 protected runtime/migration/web/operator inputs and 57 prior frozen report
files remain unchanged. All new isolated DBs removed; 13 baseline names retained.
Private procedures now cover request handling, restore quarantine/reconciliation and
future authorized any-reason seven-day refund handling using official provider
references. No legal/tax deadline, retention period or guardian method is selected.
No production connection, deployment, migration, mail, payment, phone or APK change.
No economy code/calibration change; prior 2,275/1,202 evidence is not a fresh run.
0130 remains unreserved. Database policy, age, checkout and referrals remain off.
Next: actual guardian verification and permitted processing/consent/withdrawal;
retention schedule and independent current-state preservation; reviewed repair/
recovery/cutover; invoice/tax/refund entitlement decisions and real provider tests.
Physical Android, human/content/healthy-week/volume gates remain; iOS is deferred.
Procedure: docs/FINNA-PRIVACY-OPERATIONS.md.
Report: reports/finna-restore-privacy-preflight-20261120/. Preserve frozen targets.

20 November IST — local CMS publication rewards and workflow notice admission.
CMS first-publication rewards now use database recipient admission before the
reward mutex/claims/profile/ledger. Restricted/busy targets leave source publication
and audit intact; source replay/revisions/restore do not remint a skipped first
publication. Registration, independent review, paid-preview/self exclusions and
one-per-IST-day remain. Mutex-onward and the entire historical reversal function
are byte-identical: recorded claim amounts reverse once despite restriction,
closure, busy/missing policy, with no daily-slot refund or history rewrite.
0129 guards new material/contribution-linked optional in-app notices at SQL INSERT,
including independent trusted publisher SQL. Missing/busy/restricted recipients or
missing policy suppress the copy without losing source/audit/archive integrity.
Existing notices/read controls, unrelated account/system notices and admitted
inbox preferences remain. The new function is not app-callable/disableable and its
lookup path puts public before pg_temp. No queue/backfill/new table/client mint API.
The trusted publisher checks its original immutable publication event, so a skipped
notice cannot backfill on original acknowledgement retry after confirmation/flag-off.
API decisions retain stale-version/state guards. Pair current publisher/API/0129
and all earlier guards after draining writers before any future policy activation.
Authorized governance decisions/reviewer identities/grants/quorum/source proof,
publication/credit/audit and prior private history retain their existing scope.
Social blocks do not annul private governance; no staff/MFA/disclosure/ownership/
native boundary was widened. This is not a legal retention/minor-processing basis.
2,275 full backend / 1,202 compatibility / 89 focused checks pass; 50 new cases; 137 API
runtime bindings plus separately bound publisher source,25 zero integrity fields.
Initial 82 focused checks also passed. The earlier restricted publication notice
assertion intentionally changes from 1 to 0 while source/audit/credit stay. No focused
failures, broad interruptions or applied-migration edits. Full/runtime/test/proof/
operator inputs are preserved. A fresh 252-table clone preserves all original
columns/values/indexes, existing function owner/ACL and 0129 exact body/config/trigger/
permissions. All clone/dump/stages and new local DBs removed; 13 baseline names,
62 prior frozen report files and 367 web inputs / 366 built files preserved. Both sites return 200.
0129 reserved/unapplied; 0122–0128 remain unapplied; 0130 next unreserved. No production
migration/restart/deploy, production bank sync, frontend/APK/phone/mail/payment.
Database policy, age, checkout/referrals stay off. Next: real guardian verification
method, consent/withdrawal/permitted minor processing; retention/backup/restore/
request/tax/refund procedures and guarded rollout/recovery. Existing physical Android,
human/content/healthy-week/volume gates remain; iOS stays deferred.
Report: reports/finna-cms-notice-eligibility-20261120/. Preserve frozen targets.

20 November IST — local database community tier admission and lookup hardening.
0127 filters current SQL weighted standing by active registered adult author and
voters when the database policy is on. Posting privileges/Guide candidacy use that
weight; display retains immutable historical max. Read-only real-role readers work
without processing leases or audit writes. Persistent capture admits the target
before the author-tier mutex, then leases the entire candidate voter set before
maturity calculation. Busy voters skip whole optional capture; nested rollback
releases newly acquired partial voter leases. Source votes/history stay intact.
Before-loss capture includes declarations/closure and existing moderation/block/
vote/email/maturity changes. Attempt maturity-boundary counting requires voter
admission. API restrictions/closure wait before rows; independent SQL retries55P03.
A skipped transient milestone has no delayed replay queue or history initialization.
A real mpsc temporary-vote-table regression exposed implicit pg_temp relation
shadowing in privileged tier capture (forged rank4 at a real rank1 threshold).
0128 orders pg_catalog,public,pg_temp for the five tier/audit functions, preserving
bodies/owners/ACL/history;0127 was never edited after application. No new award,
currency/table/client mint endpoint or guardian consent inference was introduced.
2225 full backend/1152 compatibility/45 new focused cases pass,136 runtime bindings
and25 zero fixture integrity fields. Initial35pass/2fail fixtures attempted a
foreign-key-protected attempt deletion and null required correctness; both now
assert existing integrity guards. Intermediate37new+18existing checks passed55;
the temporary-table reproduction failed before0128 and now passes. Logs remain.
Two successful fresh production-dump clones preserve252 original tables/columns/
values/indexes and function owner/ACL. The final clone verifies explicit lookup
order and read-only mode,0127/0128 exact bodies/configuration and default-off policy.
An intermediate combined helper had a tuple-path parsing error; a new separately
bound helper/rehearsal corrects it. A subsequent SSH connection failure also produced no accepted receipt; its exact
clone/dump/stage cleanup is verified. A fresh keepalive/server-receipt helper passes.
All four clone/dump/stages are removed.
All new local DBs removed;13 baseline names,60 prior frozen report files and367web
inputs/366built files remain identical. Both sites return200.0127/0128 reserved but
unapplied in production;0122–0126 stay unapplied;0129 next unreserved. No deploy,
restart, frontend/APK/phone/mail/payment change. All launch flags remain off.
Next: CMS material positive publication rewards/exact archive reversals and
administrative review/publication/CMS notice, quorum/source proof and retained
private governance/audit/history policy; actual guardian verification/consent/
withdrawal/minor-processing, retention/backup/restore/request/tax/refund procedures
and guarded launch. Existing physical/human/content/healthy-week/volume gates stay.
Report:reports/finna-tier-eligibility-20261120/. Preserve frozen targets.

20 November IST — local legacy contributor and voter visibility.
The default-off audience filter now covers legacy contributor ranks before dense
ranking/limits and published-contribution metadata before cursor pagination.
Bilateral viewer blocks and anonymous attribution remain; anonymous rankings create
no guest accounts, and both lists are private/no-store. Legacy Helpful totals omit
restricted voters and author-voter block pairs; new votes reject hidden authors,
while eligible actors can remove an own historical vote. Mock title protection is
retained and active-game/open-Cup title protection added. Published bank questions,
source credits, votes, reward receipts and tier milestones are preserved.
Shared Helpful query builders now resolve the flag at query time, including static
SELECT templates; feed/direct study/question reads, visible profile/weekly counts
and the current support count filter restricted voters before maturity weighting.
Read-only real-role readers work; no account-processing lease or persistent score
write is added. This does not finish SQL current standing, posting privileges,
Guide candidacy or milestone triggers. V.8 requires splitting review-sized phases;
the database target/voter/tier admission is the next separate migration/rehearsal.
2180 full backend/1107 compatibility/79 focused checks pass,39 new cases,133 runtime
bindings and25 zero fixture integrity fields. Initial25pass/7fail closed-account
fixtures violated the existing anonymization constraint; normal closure plus
separate unclosed/email-less fixtures now prove the boundary. Failure logs retained. An older Guide fixture created150 undeclared voters; its
reproduced failure now declares those synthetic voters adult. The initial broad
runs were stopped (exit2) with exact owned child signals and receipts before the
fixture edit; final suites use the corrected source hashes.
All47 predecessor report files,367 web inputs/366 built files and every migration
remain identical. All new local test DBs are removed;13 original names remain. An interrupted DROP
left one invalid unconnectable DB (datconnlimit=-2); its exact pending cleanup was
completed after checking owner, baseline absence and zero connections.
Both public sites return200. No new migration/remote clone/production deploy or
restart, frontend/APK/phone/mail/payment change.0127still unreserved;0122–0126remain
unapplied. All launch flags remain off. Next: complete database tier admission and
immutable before-loss capture; administrative notice/quorum/audit/history policy;
real guardian verification/consent/withdrawal, retention/restore/request/tax/refund
procedures and guarded launch. Existing human/content/physical/volume gates stay.
Report:reports/finna-contributor-visibility-20261120/. Preserve frozen targets.

20 November IST — local publication reward recipient admission.
Migration0126 admits new positive contribution rewards through the database-wide
policy/shared account lease before reward mutex/profile/ledger/claim writes. A
restricted/busy recipient leaves source publication, credits and audit intact;
trusted original-event replay does not remint after confirmation or flag-off.
No postponed-award queue, historical award backfill or client mint endpoint added.
Exact historical negative reversals bypass positive eligibility, including closed
accounts and policy-off mode. This fixes the old registered-email early exclusion
for closed reversals. Legacy/v2 original amounts, once-only matching, source proof,
quorum, tariffs and daily slots remain; the SQL body after the mutex is identical.
Zero source credits remain valid. This is internal ledger integrity, not cash/refund
execution, guardian permission or complete administrative processing policy.
2141 full backend/1068 compatibility/49 focused checks pass, including31 new cases,
130 exact runtime bindings and25 zero fixture integrity fields. Initial failures
were duplicate synthetic reversal revisions, a synchronous fixture waiting on a
legitimate FK row lock and stale pg_stat_activity polling; async pg_locks checks
now prove closure waits and finishes safely. One exact owned fixture query was
cancelled; all failure logs remain. No applied migration was edited.
A fresh production-dump clone preserves252 original tables/columns/values/indexes;
0126 matches the exact installed function body with its owner/ACL unchanged. Clone,
dump/stage/new local DBs are removed;13 baseline names,63 frozen predecessor files
and367 web inputs/366 built files remain identical. Both public sites return200.
0126reserved/unapplied;0122–0125remain unapplied,0127next unreserved. No production
restart/deploy, phone/APK/frontend/mail/payment change; all launch flags stay off.
Next: community target/voter weighting, tier capture and legacy contributor rank/
author/voter reads, administrative notice /
audit/history decisions, actual guardian verification/consent/withdrawal,
retention/restore/request/tax/refund and guarded launch. Do not enable policy yet.
Report:reports/finna-publication-eligibility-20261120/. Preserve frozen targets.

20 November IST — local synchronous activity and guest-transfer admission.
A database-wide operator policy defaults off; API startup rejects a mismatched
age flag and closes its new pool. Independent SQL activity uses the same shared
account lease as workers/restrictions, and missing policy fails closed. Restricted/
busy activity retains source attempts and durable reconciliation hints. The existing
admitted worker can rebuild activity; no new award or migration-time backfill.
Guest transfer leases both subjects before credential/target locks, rechecks active
adult eligibility and fresh proof, and preserves snapshots, assessments and once-only
receipts. SQL attempt ownership changes also check source and registered target.
Direct SQL restrictions fail/retry55P03 under admitted work; API restrictions wait
before row locks. A reproduced direct-function ownership race is fixed by0125;
0124 stays unchanged after application. The initial focused privilege failures are
fixture differences from postgres default grants, independently confirmed on clone.
2110 full backend/998 compatibility/35 focused checks pass,129 exact runtime
bindings and25 zero integrity fields. Interrupted first broad suites retain exit2
receipts before source changes. Two fresh production-dump clones preserve252
original tables/columns/values and existing indexes. Both clone/dump/stages and
all new local test DBs are removed;13 baseline names,71 prior report files and
367 web inputs/366 built files remain identical.0124/0125 reserved/unapplied in
production;0122/0123 remain unapplied,0126 next unreserved. No production restart/
deploy, phone/APK/frontend/mail/payment change; age/checkout/referrals stay off.
Remaining: positive publication awards with legitimate reversals, community tier
computation/milestones, administrative notices and historical controls, actual
guardian verification/consent/withdrawal, retention/restore/tax/refund and guarded
launch. Do not enable the database policy before those paths/rollout are verified.
Report:reports/finna-synchronous-activity-20261120/. Preserve all frozen targets.

20 November IST — local shared-subject visibility and social-notice guards.
With the optional age flag enabled, active-adult subject checks now precede
public/shared pagination and counts: creator discovery/profile/search, community
feeds/question/study replies/accepted snippets, materials/references, Guides,
Desk members/items/calendar/goals/chat/Inbox and stored game/Cup identities.
Existing blocks, disclosure and publication gates remain; stored history stays.
Restricted Desk owners hide rooms/invites, while eligible members can leave or
decline. Inbox previews recheck linked notes. Hidden game owners use an empty
string to preserve the response contract. Reserved team attribution is content,
never learner age verification. Owned export/private controls/moderation remain.
Immediate Desk/discussion notices use nonblocking account processing leases;
restriction/closure serialize with admitted notices. Suppressed optional notices
are not replayed. Existing private notice history and durable correction queues stay.
2075 full backend/946 compatibility/49 focused checks pass, including45 new cases,
126 exact runtime bindings and25 zero integrity fields. Retained focused failures
include a real unqualified invitation SQL correlation (fixed and rejected by the
helper), fixture catalog/session/moderation/body/anonymization mistakes and Cup
fixture credentials. Broad suites were deliberately interrupted to add the two
legacy Cup rank readers; final source-bound suites pass. All new test DBs are
removed,13 baseline names and42 prior frozen report files unchanged;367 web inputs/
366 built files preserved. No schema/production/frontend/APK/phone/mail/payment
change;0122/0123unapplied,0124next unreserved. Age/checkout/referrals remain off.
Synchronous review confirms attempt/adoption activity writes, positive publication
credits, SQL tier milestones and administrative review notices still need separate
database-side design/new migration/rehearsal. Visibility is not complete guardian
withdrawal, consent, minor-processing permission or erasure. Real verification,
retention/restore/tax/refund and guarded rollout remain open.
Report:reports/finna-community-eligibility-20261120/. Preserve older frozen targets.

20 November IST — local reassessment/correction eligibility guard.
The default-off age boundary now admits derived mock/attempt assessments and
in-app correction notices through nonblocking shared account processing leases,
with a fresh active-adult check. Restriction/closure wait for admitted transactions.
A restricted/busy target rolls back its whole page, retaining cursors, pending
status and failures. Temporary queue/account locks are released; individual jobs
are not acknowledged. At most10 source jobs/events are examined for other work.
Eligible accounts sharing a paused page also wait; no cursor skips restricted work.
Source/appearance invalidation continues without authorizing learner derivation.
Closed email-less accounts remain absent from the original notice recipient query.
Original results, assessments, notices and economic history are retained.
2030 full backend/837 compatibility checks and46 focused tests pass, including25
new guard cases,119 exact runtime bindings and25 zero fixture integrity fields.
The initial fixture failures (36pass/3fail,40pass/2fail) are retained and corrected.
An intermediate broad run was deliberately interrupted (exit2) to restore default-off
locked-oldest skipping; its regression and both final source-bound suites pass.
All new test databases are removed;13 pre-existing names and42 frozen game-report
files remain unchanged.367 web inputs/366 built files remain preserved.
No new migration, production restart/deploy, real mail/payment, frontend/APK or
phone change.0122/0123 remain unapplied,0124 next unreserved. Age/checkout/referrals
off; real guardian verification/consent, other synchronous/SQL-trigger paths,
community/Desk/identity exposure, retention/restore/tax/refund and guarded rollout
remain open. Report:reports/finna-reassessment-eligibility-20261120/.

20 November IST — local game lifecycle eligibility guard.
The default-off age boundary now checks participants before start, clock advance
and finalization, including voluntarily departed players' saved choices. Restricted
seats are released, public-result opt-in cleared and a once-only immutable marker
prevents old choices being processed or rejoined after confirmation/flag-off.
Account processing leases serialize admission with restriction/closure; a busy
account defers the room and releases temporary leases. Eligible opponents retain
original deadlines. All seven modes, timeout/reveal safety, replay, real worker
sweep, closure/restriction races and generic prepared index use are covered.
2005 full backend tests/791 compatibility checks pass with116 runtime bindings
and25 zero fixture integrity fields.26 new tests pass; the earlier51-test focused
run predates the index. The initial clone helper failed at import because its
filename shadowed Python's operator module; its log is retained. The corrected
fresh production-dump rehearsal preserves252 tables and all existing indexes;
0123 applies in6.448ms on the clone only. Clone/dump/stages/new test DBs are removed;
13 pre-existing local names remain unchanged. Migration0123 is reserved/unapplied,
0122 remains unapplied;0124 next unreserved. No production restart/application,
frontend/APK/phone/mail/payment change; age/checkout/referrals remain off.
Real guardian verification/consent, reassessment/notices, synchronous/SQL-trigger
and community/identity exposure, retention/restore/tax/refund and guarded rollout
remain open. Report:reports/finna-game-eligibility-20261120/. Preserve older targets.

20 November IST — local durable learning eligibility guard.
When the default-off age flag is enabled, worker claims require a declared adult
and an active registered account. An account-specific shared processing lease
precedes the job lock; under-18 restriction/closure take the exclusive lease first.
Fresh admission checks and bounded busy-candidate lookahead retain pending job
versions/cursors/history instead of acknowledging restricted work. Nightly enqueue
filters age declarations; the heartbeat counts age-paused jobs. No minor activation,
new migration, production/phone/APK/frontend/payment/mail change. The initial focused
run passed39/failed1 due to invalid JSON in a synthetic partial-write fixture;
the fixture is corrected.1979 full backend/765 compatibility checks pass with
114 source bindings and25 zero fixture integrity fields. Exact runtime/test inputs
are preserved. All new test databases are removed;13 pre-existing names are unchanged.
Real verification/consent, game/reassessment/synchronous-trigger/community review,
retention/restore/tax/refund and guarded rollout remain open.0122unapplied,0123next.
Report:reports/finna-learning-eligibility-20261120/. Older frozen targets stay preserved.

20 November IST — local background age restrictions added.
The default-off age boundary now covers review-reminder scheduling/reservation/
delivery, official-calendar notifications, bearer calendar feeds and weekly XP/game
standings. Under-18 declarations cancel pending study reminders, disable calendar
reminders and version-revoke active feed URLs; entries and historical receipts stay.
745 compatibility checks pass with 114 runtime source bindings and 25 clean fixture
integrity fields. All 1967 full backend tests pass with the exact sources preserved. No production,
mail, payment, APK, frontend or phone change; 367 web inputs/366 built files and the
prior 45-file privacy report are preserved. No new migration; 0122 remains unapplied,
0123 next unreserved. Real guardian verification/consent, learning/game/reassessment
and community/Desk review, retention/restore/tax/refund and guarded launch remain open.
Report:reports/finna-audience-background-20261120/. Preserve all older frozen targets.

20 November IST — privacy tools and age boundary implemented locally.
Owner confirmed Hruaitluanga, an individual trading as Finna. Local migration0122
adds owned privacy request receipts/append-only events and age declarations.
/account/privacy, owner /admin/privacy and /policies/:page previews are built;
policy previews have no publication effective date. AUDIENCE_GATE_ENABLED defaults
off. When enabled, adult declarations guard guest/email/Google/native study access
and pooled mutation commits; minor enrollment always remains unavailable.
No real guardian verifier, consent lifecycle or child-processing permission exists;
do not enable this flag as completed guardian support. Existing ages are not inferred.
1950full tests/717compatibility/113source bindings, actual components/build and
isolated1280/320 light/night QA pass. No production deployment, API restart, mail,
refund, APK or phone input. Paired production recoveryc8_khz6p remains current.
0122 is reserved/unapplied;0123 next unreserved;0110/0120 remain immutable.
Report:reports/finna-privacy-implementation-20261120/ (frozen; never rerun outputs).
Next: real guardian verification/consent and background-processing review,
retention/backup/request policy, tax/refund operations, guarded deployment/publication
and actual payment checks, plus existing physical/healthy-week/content/human gates.
Do not deploy the whole local API/web tree over production's narrower feature scope.

20 November IST — privacy inventory and guardian design prepared.
Owner selected no fixed refund-support response deadline and inclusion of under-18
students with a guardian process to be designed. Invoice identity remains undecided
(Finna or Hruaitluanga; no business status confirmed). Private legal drafts now
record these choices. Read FINNA-PRIVACY-INVENTORY.md and FINNA-GUARDIAN-PLAN.md
under docs/ before policy/guardian implementation. Fresh read-only production source,
backup/rotation and active-asset review identifies retained closure data, unpruned
database backups, Google Fonts and reachable OpenStreetMap tile references.
Guardian checks are not implemented; do not claim protected minor registration,
complete erasure, finalized retention or legal/payment readiness. Current runtime,
APK and deployment remain unchanged. Report:reports/finna-policy-readiness-20261120/.
Earlier frozen reports remain historical; no whole-plan completion is claimed.

20 November IST — further readiness planner alternatives rejected; policy inputs recorded.
Fresh analyzed252-table clone,48exact-result checks and12EXPLAIN ANALYZE runs compare
six transaction-local settings in both source scopes. Join2 is tied with deployedjoin1
(default4054.647→4048.332ms;all4151.020→4207.825ms);join3/4/5 andjoin8/from1 are64–71%slower.
All original values remain identical; clone/dump/stage removed. No runtime/dependency,
production statistics/schema/global configuration change or API restart; the prior
empty-pins release/current recoveryc8_khz6p and its1938-test proof remain current.
Owner supplied public nameFinna,support address and a7-day refund window,then explicitly
chose refunds for any reason within7days of the charge. These are saved in private
FINNA-LEGAL-DRAFTS.md; remaining legal/invoice,handling,age/retention/dispute /
provider details and publication are still pending. No policies published,mail sent,
refund issued,checkout enabled,new APK or phone input. Full plan remains open.
Report:reports/finna-readiness-plans-20261120/. Preserve all frozen evidence; do not rerun it.

20 November IST — targeted subject-wide query improvement deployed.
A single redundant SQL condition skips empty pin arrays before the scoped question join.
Four alternating warm samples improve the default-scope subject-wide detail query
4456.789→4058.535ms (8.94%); other cases have no material regression. Section counts
retain their existing timing under production JIT settings; this is a targeted gain.
1938full backend tests,705integrated/496production compatibility,64proposal/recovery
checks and105/77source bindings pass. Two fresh analyzed252-table clones preserve
all original values;520timed runs/260output comparisons match and both clones/dumps/stages are removed.
Only collection reader and matching production economy evidence are released;310source,
3470static, schema/private configuration and all writers remain protected. Live two-payload
hashes match; subject HTTP sample4.711→4.362s.8workers/4timers healthy,25integrity
counters0,ledger46→46; sites/API/staging healthy. No phone,new APK,migration,mail,
synthetic production learner activity or history rollback. Prior610Android,28ops and31rejected-query
report files are hash-preserved. Current paired recovery:/root/finna-empty-pins-backup-c8_khz6p.
Reports:reports/finna-empty-pins-20261120/ and the rejected redundant-join experiment
reports/finna-query-performance-20261120/. Do not rerun frozen deployment/evidence targets.
Further performance/maintenance work,actual healthy-week/monthly-human,owner/physical,
content/legal/payment/real-volume gates remain open;iOS deferred. Full plan remains open.

20 November IST — dependency/operations follow-up; website advisory item closed.
Fresh full and production web lockfile audits report0findings; the earlier picomatch advisory is withdrawn.
Mobile remains27moderate full/20production-install-graph entries from2underlying advisories,zero high/critical.
All27affected parent constraints reject the published fixed leaf major versions; supported registry ranges
have no newer release. No package changes,forced Expo/Jest downgrades,new APK build or phone input.
Current real-role read-only ops:8workers/4timers healthy,25integrity counters0,ledger46→46,verified backup,
existing actual restore still healthy and all3HTTPS checks200. Old collector/stats failures are retained;
collector history begins18November,so no healthy-week/monthly-human sign-off or rollout is claimed.
Bounded slow-log review classifies13older error lines as autovacuum cancellations without claiming cause;
query/maintenance investigation remains open. All610frozen Android files,171inputs/2regressions preserved.
Report: reports/finna-dependency-ops-review-20261120/ (main Finna repository). Android beta11f7cbfb remains current.
Full plan,physical/owner/content/legal/payment/real-volume gates remain open;iOS deferred.

20 November UTC — corrected signed Android update passes bounded emulator acceptance.
Preview01a448a3-d97b-4719-9da5-e2d4a873e406 and beta11f7cbfb-e878-44ed-998c-2eff382694a3 are FINISHED,
signature/package/origin/callback and16KB-alignment verified; installed bytes match both downloads.
143component/33logic tests,lint/typecheck,Android/web exports and171reviewed upload inputs pass.
Signed staging traverses all1000/end in200guarded swipes/259.55s with4explicit page recoveries;
all40unfiltered native pages return200. Two cold restarts restore999 at identical coordinates;
nonfinal993/partially visible994 also restore identical coordinates after a retained hierarchy-tool failure
and separate serial reinspection. Regular beta guest Home/Library/exam entry and compact320dp dark/200%
filter Clear all/Show questions pass. Test setup fixes for display recreation/modal bounds are recorded;
no runtime code change or additional build is made this continuation. All46retained images inspected.
Original display/network settings restored,shelluid2000,scoped crash buffers empty,emulator stopped/data retained.
Staging remains2registered synthetic accounts/5attempts/0mail/0active QA auth;all three HTTPS hosts200.
No phone input or production learner writes. Whole-report validation.json freezes the final evidence;
prior579proof bindings,83earlier local files and61current local files are preserved. Do not rerun frozen outputs.
Regular owner beta:reports/finna-native-emulator-extended-20261119/finna-beta-current.apk;
installation guide:docs/FINNA-ANDROID-BETA.md. Earlier queued checkpoints below are historical.
Next:owner install/feedback,physical TalkBack/network/tablet/performance coverage,actual healthy-week/monthly
human sign-off,reviewed content/official sources and public legal/support/refund/live-billing decisions.
Full native acceptance/full Finna plan remain open;iOS deferred because no device is available.

19 November 18:03 UTC — startup-only guard143 local acceptance passes; new signed pair queued.
Current preview01a448a3-d97b-4719-9da5-e2d4a873e406 and beta11f7cbfb-e878-44ed-998c-2eff382694a3 are IN_QUEUE;
do not duplicate. Prior231e7a5c/3f284a4c are confirmed CANCELED after later draft-filter metadata unmounted
its list. The new listMounted latch waits only at startup;143component/33logic,lint/typecheck,Android/web
exports and171-file archive pass. Only questions.tsx differs from the prior candidate. Exact current inputs:
build-inputs-mount5.json; snapshots question-browser-mount5.tsx and QuestionPosition-mount5.test.tsx.
Current local-only debug-certificate probe traverses1000/end in168swipes/217.88s with3pagination recoveries.
All40unfiltered native pages revalidate304;five cold starts restore999 at identical coordinates (zero-pixel
difference),and nonfinal993 also restores identical coordinates. No root/reading-position seed in this probe;
original display/network baseline unchanged,shelluid2000,scoped crash log empty,emulator stopped/data retained.
mount5-local-validation.json freezes61current diagnostic files;local-validation.json preserves83earlier142-test
files. Do not overwrite/re-run those local evidence files. They are local diagnostic,not Expo-signed acceptance.
Finish new builds,download/verify signatures+current source,replace local staging APK (different certificate),
repeat with mount5-signed-* helpers,then freeze whole report/update docs. Latest official artifacts are not ready yet.
Report:reports/finna-native-emulator-extended-20261119/. No phone input/production learner writes. Full plan open.

19 November 17:23 UTC — further reading-position correction passes local native probes; signed replacements queued.
The fe640697 preview reaches1000/end with five explicit page-recovery taps, but its first serial cold restart
misses999. Later local probes expose temporary-end acknowledgement, an empty initial native render window,
late header layout and throttled terminal offsets. Only questions.tsx changes among171reviewed archive files.
All142component/33logic tests,lint/typecheck,Android/web exports pass. Final local-only debug-certificate
staging probe passes five real-swipe/cold-restart cycles with identical index998/inside259.8095703125; a
nonfinal question993 probe restores identical coordinates and PNG bytes. These are diagnostic local APKs,
not Expo-signed acceptance. New preview231e7a5c-dae2-45b9-951e-ac99cf8efa11 and beta3f284a4c-5db8-45d2-973c-2a286fce618d
are dispatched;do not duplicate. Native acceptance/download/signature checks remain for these new builds.
Final local bundle traverses1000/end in280swipes with7explicit recoveries;two further cold starts return999.
No phone input or production learner writes.
ADB root used only for owned-emulator guest diagnosis is removed (uid2000);baseline restored and emulator stopped.
Local-validation.json freezes83local diagnostic files;do not overwrite/re-run terminal4-local-* evidence.
Continue with terminal4-signed-* helpers after the new builds finish;whole-report freeze remains pending.
Report:reports/finna-native-emulator-extended-20261119/ remains unfrozen. Full plan/physical/business/operations gates remain open.

19 November continuation — extended emulator QA and question-position correction in progress.
Signed staging666b8b61 traverses all1000 synthetic questions;all40native25-item pages load and end notice appears.
A fast-fling stall at item825 resumes after reversing/slow scrolling;the new browser adds explicit Load more questions.
Cold restart returns to the saved page but misses the visible question;layout ordering and duplicate-scroll regressions
now gate completion on native size,scroll acknowledgement and matching viewability. Initial3regressions fail before
correction;an additional duplicate-event regression catches an early candidate;final137component/33logic checks,
lint/typecheck and Android/web exports pass. Only src/app/questions.tsx differs in171reviewed upload inputs.
Compact320dp dark and tablet1280x800/800x1280 layouts at200%text retain navigation and pinned filter actions;
compact Subjects label wraps across lines. These are emulator checks,not physical tablet/TalkBack/smoothness acceptance.
Software-GPU frame delays are substantial;do not claim release performance passed. No phone input. Staging stays5attempts,
0mail,0active QA auth sessions;both existing hosts healthy. Display/network baseline restored and emulator stopped.
Candidatefd7d4075 canceled after duplicate-event regression. Replacement previewfe640697-a01b-458f-9215-81c4fbbb6b40
and beta56460d0a-5cd6-49dc-8778-f38ab0983593 are queued;do not duplicate. They are not yet downloaded/native accepted.
Report:reports/finna-native-emulator-extended-20261119/. Finish builds,verify signatures/current bundle,install on owned
emulator and repeat native recovery/long-list checks. Earlier APKs remain historical;Samsung retains old6df0b4c7.
Full plan remains open for physical acceptance,owner feedback,real healthy week,human/content/legal/payment/volume gates.

19 November continuation — answer response/exam UI update built and bounded signed HTTPS emulator QA passes.
Bank/practice choices highlight before disk persistence; durable pending writes still precede sending.
Practice applies the authoritative POST response without the former extra GET. Exam→module browsing,
subject/topic/subtopic filters, scoped Papers and pinned filter actions pass synthetic browser and native QA.
129 component / 33 logic tests, lint/typecheck, Android/web exports and Expo Doctor 20/20 pass.
SDK58 patch alignment is complete;20 moderate npm runtime-tree advisories remain,zero high/critical.
Final preview 666b8b61-9cdd-4a54-85cf-138bf876ac3e and beta e4816038-1b54-4678-8376-daa6a33f9ce8
are FINISHED,downloaded and signature/package/current-code verified. Beta signer matches prior beta.
Signed staging passes actual HTTPS browser handoff,account restore after force-stop,bank feedback/restore,
practice feedback,offline pending-choice restart and one explicit retry,restored result,500-question
English→Grammar→Verbs filter and logout/restart. Server logs confirm no success-answer GET refresh.
API36 x86_64 emulator only;no Samsung input or phone performance claim. The Samsung retains old6df0b4c7.
Regular beta passes public guest Home/Library/exam-entry smoke checks;scoped crash buffers empty.
Persistent https://finna-staging.hawayu.in has its own PostgreSQL cluster and API identity,production paths
hidden,mail/payments/signup/admin blocked.5 synthetic attempts total,0 mail;all QA sessions retired.
Both existing sites stay healthy;existing Caddy hashes unchanged. Prior 105 API / 20 PDF and frozen Android/
release evidence preserved. Emulator networking restored;AVD retained and emulator stopped to release RAM.
Phone-free launcher/runbook:scripts/finna-android-emulator.py and docs/FINNA-ANDROID-QA.md.
Reports:reports/finna-native-release-readiness-20261119/ and reports/finna-native-https-staging-20261119/.
Remaining:physical TalkBack,broader Android/network/tablet/full release profiling and owner feedback;
healthy-week,human/content,legal/payment and real-volume gates. iOS deferred. “Yes” supplied no actual
operator/legal name,support email or refund values;draft policies stay private.
Earlier dated checkpoints retain their original acceptance/source/binary scope.

19 November continuation — signed Android accessibility probe remains incomplete.
TalkBack bound with touch exploration; injected inputs did not establish focus
traversal or speech acceptance. Nine Finna-only captures inspected; settings
restored exactly. A later Home scrolling probe stopped on focus loss before a
post-swipe sample; no performance result claimed and no further phone input.
Current lint/typecheck pass; signed UID crash buffer empty without clearing logs.
Runtime unchanged; all prior evidence/source bindings preserved. Installed beta
still lacks the prior local logout correction. Report:
reports/finna-native-android-accessibility-20261119/.
Next: reachable HTTPS preview/signed account checks, complete TalkBack and broader
network/layout/performance coverage, then final combined signed build/feedback.
iOS deferred; full plan still has healthy-week, human/content, legal/payment gates.
Earlier dated checkpoints retain their original acceptance/source/binary scope.

19 November continuation — native Android mock/offline/expiry/deep-list recovery passes.
Fresh disposable1000-question fixture,one real browser login and native3-question
mock. A disconnected choice survives force-stop;no server save until explicit retry.
Two acknowledged B choices score2correct/0wrong;final pending C stays unanswered
when reopening after server expiry. Expiry is accelerated by moving only the fresh
fixture's started_at,not by changing phone time. Native automatic submit and result
reload after another restart produce exactly2attempts,one completed mock,no mail.
Removing an ADB reverse does not close existing keepalive immediately;second choice
was acknowledged,so final outage drains7seconds before selecting the third choice.
Offline cold startup withholds account identity but retains encrypted credential;
reconnect/restart restores the same account with no new auth flow. Revoking the
fixture browser parent triggers native expired-session UI and removes credential/
account AsyncStorage. Seed guest reading position975 on the1000-item dataset;
actual four swipes persist980,then force-stop/reopen restores the same two visible
questions. This is bounded deep-page restoration,not full1000-row/release performance.
14app-only captures inspected;UID10354 crash buffer empty,logs not cleared. Current
lint/typecheck pass;prior116component/29logic source bindings unchanged. No mobile/
API runtime,migration,dependency,production or cloud/store change this continuation.
105API/20PDF and25release/69Android/58account/26mock-preparation proof hashes match.
Only prior client.ts logout fix differs among170signed upload inputs;installed
signed beta6df0b4c7 still lacks it. Native expired credential remains absent;
synthetic guest seed,device helper,exact DB/API/Metro/private host credentials and
owned8091/50269forwards removed. Phone settings unchanged. Report:
reports/finna-native-android-recovery-20261119/. Next:TalkBack,full long-list/release
performance,wider Android,real background/network variants,reachable HTTPS preview
staging and a future combined signed build with logout correction. iOS deferred,
no device;healthy-week/legal/payment/content/human/volume gates remain.
Earlier dated checkpoints retain their original acceptance/source/binary scope.

19 November continuation — timed Android mock starts; dynamic capture helper verified.
Fresh disposable1000-question fixture and native browser handoff start a real
three-question/30-minute mock in Finna Dev. The half-second countdown prevents
standard uiautomator idle dumps. Added optional --dynamic-hierarchy to the existing
capture helper plus scripts/build-finna-dynamic-dumper.py and
scripts/android/FinnaDynamicDump.java. The read-only helper keeps package/keyboard/
focus guards, captures the running countdown and refuses foreign foreground with
no screenshot/XML. Reusable build's DEX matches the actual device-tested helper.
The phone then moved to another app before any answer; all phone input stopped.
No interrupted-answer/deadline/offline/expiry acceptance claimed this continuation.
30focused mock/session/logout tests,lint/typecheck and helper build pass. No mobile
or API runtime changes;prior local logout fix still awaits a combined signed build.
One local mock,zero saved answers/attempts/mail. Synthetic sessions/parents revoked;
Dev force-stopped in background and its sole synthetic SecureStore entry cleared
by harness with valid-empty-store readback (not a native logout acceptance).
Exact DB/API/Metro/private host credentials,device test jar/XML and owned8091/48007
forwards removed. Owner-controlled foreground preserved. Report:
reports/finna-native-android-mock-20261119/. Resume physical mock recovery/deadline/
offline/expiry with Finna Dev foreground;HTTPS staging,TalkBack,1000-row restoration/
performance,wider Android and signed build remain. iOS deferred,no device.
Earlier checkpoints and their source/binary acceptance scopes remain historical.

19 November continuation — native Android development account/recovery checks pass.
Samsung Android16 completes real Chrome login/confirmation/callback for two
synthetic accounts on a fresh 1000-question loopback fixture. SecureStore account
restore survives force-stop; an interrupted practice choice survives another
force-stop and explicit retry records exactly one A-owned attempt. B has zero
progress and independent exam preferences. Logout clears authenticated local data
and revokes all three test mobile sessions. Phone testing exposed a false logout
warning: credential retirement rejected its own acknowledgement. Only POST
/mobile/logout now accepts its revocation response after retirement; an obsolete
401 cannot expire a newer account, and other response guards remain. Two of four
new transport regressions fail before the fix; all116component/29logic checks,
lint/typecheck pass afterward. Cleared Metro cache and actual native logout verify
the correction. It is local/dev only, NOT in installed signed beta6df0b4c7.
Only mobile src/api/client.ts changed runtime;105API/20PDF/25prior release/69prior
Android proof hashes match,169/170signed upload inputs match. One synthetic local
attempt,no mail,no production access. Exact fixture DB/API/private credentials,
dedicated Metro and task ADB forwards removed;unrelated8000 preserved. Prior
pending8091/56439 cleanup resolved;owner display settings unchanged. Report:
reports/finna-native-android-account-20261119/. This is development HTTP over ADB,
not signed HTTPS staging or full physical-offline/release acceptance. Next: native
mock/offline/account-expiry cases,1000-row restoration/performance,TalkBack,wider
Android coverage,reachable HTTPS preview staging and a future combined signed
build with the logout fix. iOS deferred (no device),not an Android blocker.
Healthy-week/legal/payment/content/human/volume gates remain;0110/0120immutable,
0122nextunreserved. Earlier dated checkpoints retain their original scope.

19 November continuation — combined Android beta installed; iOS deferred.
Owner has no iOS device. Defer physical iOS acceptance without blocking Android;
no iOS build/store request. Signed beta6df0b4c7-fd5c-4c2a-a0af-0d6c355e0741 now
installed,exact112596770B/SHA2566cf90d6820c0514ca231e7899e0508d53d736049b6b40eb916e1abb20e14cc66.
13visually inspected captures pass guest tabs/questions/filters,hot200%font then
Mock test,dark200%,landscape and cold restart;exact UID10396 scoped crash log empty.
Three ActivityManager cold samples247/288/292ms are limited first-draw evidence.
Actual owner baseline font1/nightno/rotation0/auto0 restored. Two normal guest
Continue auth starts cancelled before credentials/confirmation;no learner answer/
attempt/mail/award or production account connection. Capture guards refused other
surfaces. A disposable1000-question development fixture passes unique pagination
and deep reads0/475/975;Finna Dev displays its synthetic paper. Native auth flow
interrupted before credentials when another surface took focus,then USB detached.
No further phone UI operated. Exact fixture DB/API/credentials and Metro8091
removed/stopped. Device reverse ports8091/56439 need checking on reconnection;
unrelated8000 untouched. Lint/typecheck and105API/20PDF/170upload/25prior proof
hashes pass. No mobile/backend runtime,migration,dependency,deployment,new cloud
build or store change. Report:reports/finna-native-android-acceptance-20261119/.
Native account/offline/replay/TalkBack/1000-row restoration/performance,reachable
HTTPS staging and broader Android acceptance remain. Existing Doctor15-package
warning and healthy-week/legal/payment/source/curation/human/volume gates remain.
0110/0120immutable;0122nextunreserved. Full plan remains open.

19 November continuation — isolated live HTTPS/browser rehearsal passes.
22checks use a fresh disposable PostgreSQL DB and loopback HTTPS, every API
connection as mpsc. Desktop Chromium signs into two synthetic accounts through
real login/confirmation pages; PKCE/replay, practice ownership/answer replay,
stale presentation, mock deadline/saved-only scoring/result recovery, bearer and
parent revocation and cookie CSRF pass. Two synthetic attempts/no queued mail;
exact DB/server/TLS credentials removed. This is desktop-browser/server evidence,
not native handoff or physical network/SecureStore acceptance.112component/29logic/
40mobile backend tests,lint/typecheck pass;105API bindings/20PDF hashes preserved.
No runtime/API/schema/production change.170upload paths unchanged; exactly six
reviewed runtime files differ from installed beta. One combined internal signed
Android beta6df0b4c7-fd5c-4c2a-a0af-0d6c355e0741 finished; downloaded112596770B,
SHA256:6cf90d6820c0514ca231e7899e0508d53d736049b6b40eb916e1abb20e14cc66.
Same certificate/package,non-debuggable,production API and new fix markers verified;
170upload hashes still match. APK available but not installed/physically accepted.
Remote Doctor retains one version-check failure/15unchanged packages flagged.
Do not duplicate the build. Report:reports/finna-native-staging-20261119/.
Persistent reachable HTTPS staging/preview binary, native browser/offline/replay,
long-list/TalkBack/release-performance/iOS remain. Current production-account beta
cannot host synthetic fixtures. Healthy-week/monthly-human/legal/payment/source/
Atlas curation/real-volume gates remain.0110/0120immutable;0122nextunreserved.

19 November continuation — local timed-mock lifecycle/recovery correction.
Five of seven initial regressions failed: pending hydration did not gate answers,
disk-delayed sends survived credential change/unmount, stale route/foreground reads
could overwrite newer state. Mock now remounts by account/route/credential and
checks lifecycle/load order after each await. Hydration gates controls; delayed
choices are not sent after client deadline; server still enforces real expiry.
Submissions send answers:[] only, automatic expiry submits once, later retries are
explicit and duplicate-submit conflict reloads authoritative results.13new tests,
112component/29logic checks,lint/typecheck/Android export pass without a phone.
Isolated mobile deadline test passes; bank-review snapshot test had an independent
fixture failure (unreviewed derived cq_test). It now owns an eligible synthetic
fixture; standalone test and all21module tests pass, no scoring/runtime change.
Report:reports/finna-native-mock-lifecycle-20261119/. Prior local fix sources/proofs,
105API bindings/20PDF hashes preserved;164/170original upload inputs match. Six
runtime files now differ from installed beta b4a1a9d2-28c2-4299-a1f6-efe383d2d242;
none of these later local corrections is in that binary. No device/production/API/
schema/learner/mail/award/build/store action. Staging/system-browser/offline/device/
TalkBack/long-list/release-performance/iOS and healthy-week/legal/source/curation/
human/volume gates remain open. Applied0110/0120immutable;0122nextunreserved.

Earlier checkpoints below retain their original source/binary scope.

19 November continuation — local native practice replay/start correction.
Practice actions now wait for saved-choice loading; lifecycle/credential checks
stop obsolete sends/clears/refetches. Saved answer retries preserve exact version,
choice and presentation. Compose callbacks cannot navigate after unmount/account
change; same-selection retries retain their key and changed selections get a new
key. Six of ten original regressions failed;14final regressions and all99component/
29logic checks,lint/typecheck/Android export pass. Two existing isolated PostgreSQL
real-role backend tests pass for replay/ownership/presentation and review timing/
two-slot daily reward caps. No phone used. Report:reports/finna-native-practice-replay-20261119/.
Only practice/[id].tsx and useStartPractice.ts changed runtime this continuation;
prior answer/session sources and proofs preserved.105API bindings/20PDF hashes
match;165/170 original upload inputs match,5runtime files differ from installed
signed beta b4a1a9d2-28c2-4299-a1f6-efe383d2d242. No new binary, production/API/
schema/learner/mail/award/store action. Staging/system-browser/offline/device/
TalkBack/long-list/release-performance/iOS and healthy-week/legal/source/curation/
human/volume gates remain open. Applied0110/0120 immutable;0122 next unreserved.

Earlier checkpoints below retain their original source/binary scope.

19 November continuation — local native session lifecycle correction.
Five of six initial regressions failed: delayed restore/browser results could
re-authenticate after sign-out; local logout waited on network; stale credential
writes could survive. Session operations now invalidate obsolete callbacks after
each await, retire local identity immediately, and serialize private cleanup /
credential writes across provider remounts. Late logout cannot erase newer login;
failed offline verification detaches the in-memory bearer, retaining encrypted
storage for re-verification. Cleanup/revocation failures stay visible. Existing
PKCE/state/flow/callback and server boundaries remain.13new regressions and all85
component/29logic checks,lint/typecheck/Android export pass without a phone.
Report:reports/finna-native-session-lifecycle-20261119/. Only mobile session.tsx
changed this turn. Earlier answer fix/proofs intact;3runtime files now differ
from installed signed beta b4a1a9d2-28c2-4299-a1f6-efe383d2d242,167/170upload
inputs match. Neither local correction is in that binary.105API bindings/20PDF
hashes unchanged. No device/API/schema/production learner/mail/award/build/store
action. Isolated staging/system-browser/offline/replay/device/accessibility/
performance/iOS and actual healthy-week/legal/source/curation/human/volume gates
remain open. Applied0110/0120 immutable;0122 next unreserved.

Earlier checkpoints below retain their original source/binary scope.

19 November continuation — local native answer-isolation correction.
Confirmed four failures before the patch: a disk-delayed answer could send after
unmount/credential change; old feedback and in-flight results could outlive their
account/question scope. Existing root remount already protects ordinary account
preference switches; no PreferencesProvider change was needed. Mobile useAnswer
now binds reads/state/requests to lifecycle, credential generation and presentation;
current pending retries retain their original key/choice, changed presentations
are rejected locally. Two mobile runtime files changed;10new regressions and all
72component/29logic checks,lint,typecheck/Android export pass. No phone was used.
Report:reports/finna-native-account-isolation-20261119/. This patch is LOCAL and
NOT in installed signed beta b4a1a9d2-28c2-4299-a1f6-efe383d2d242. Its earlier
signed guest proof stays frozen; it does not certify this patch or account/replay.
105API bindings/20PDF hashes are unchanged;168/170 prior upload inputs match,
with exactly client.ts/useAnswer.ts changed. No backend/schema/production learner
write/mail/award/build/store action. Native staging/auth/offline/replay/performance/
accessibility/iOS and healthy-week/legal/source/curation/human/volume gates remain.

Earlier checkpoints below describe their original source/binary scope.

19 November continuation — corrected signed Android guest QA passes.
Signed beta b4a1a9d2-28c2-4299-a1f6-efe383d2d242 is finished and installed as
in.hawayu.finna. Installed base APK matches the verified download byte for byte;
same signing certificate, production API, no debug flag or local API. Exact hot
200% text → Mock test reproduction now passes, plus hot dark/200%, landscape
navigation, all five guest tabs, question browsing/filter sheet and cold restart
on Samsung Android16. App-scoped crash observation found no fatal/router errors.
Native display reconfiguration can return to Home; previous-screen preservation
is not certified. Owner settings font1.0/nightno/rotation0/auto-rotation1 restored;
Home left open. Task-owned USB8081/8089 forwards removed, unrelated8000 preserved.
Fresh lint/typecheck pass; prior62component/29logic/export checks remain bound to
unchanged source.105API bindings/20frozen PDF hashes/170uploaded input hashes match.
Current evidence:reports/finna-desk-pdf-20261119/router-remount/continuation/.
No new build, backend deployment, learner writes, mail, migration, awards or store
submission. Next native gate: isolated staging sign-in/offline/replay, long-list
restoration/performance, TalkBack, broader devices and iOS. This production-account
beta cannot host synthetic learner-write tests. Actual healthy week, monthly human,
legal/payment/source/curation/real-volume gates and full plan remain open.
Applied0110/0120 remain immutable;0122 is next unreserved.

Earlier checkpoints below are historical; the continuation above is current.

19 November signed-APK follow-up — first binary rejected after native QA.
Expo authentication/project linking are complete; do not restart device login.
First signed beta ebb0569f-a711-4bc2-a177-d803c1297626 compiled, verified and
installed as in.hawayu.finna. Five guest tabs, system theme,200%font and landscape
were checked, but opening Mock test then crashed with an unbound global router.
Rotation alone passes; a hot200%font change reproduces that exact crash.
It is NOT an accepted beta. Screens/hooks now use context-scoped useRouter;
plain destination translation receives that handle. Source lint forbids the global
router import.62component/29logic checks,lint,typecheck and Android production
export pass. A focused Home regression covers unavailable global routing and
replacement screen contexts. Actual Dev mock navigation also survives hot dark/
200%font changes; debug multiple-linking warning remains visible and is not hidden.
Corrected signed beta b4a1a9d2-28c2-4299-a1f6-efe383d2d242 is now requested.
Do not request another duplicate: inspect this ID, then verify/install/retest it.
Current report:reports/finna-desk-pdf-20261119/router-remount/; operational state
native-progress.json. Owner baseline font1.0/nightno/auto-rotation1 restored.
Only task-owned8081/8089 forwards are for Dev preview; preserve unrelated8000.
No production learner writes,mail,migration,award,store submission or paid upgrade.
Full staging/account/offline/replay/accessibility/performance/iOS and other plan
gates remain. Goal stays open;0110/0120 immutable,0122 next unreserved.

19 November Android continuation — Expo account/project connected; build running.
Owner completed the official browser/device login as hruaia123. Personal project
@hruaia123/finna verified,ID d3228a20-5fa5-4107-86f2-134081281285; public defaults
linked in the sibling mobile app. Native landscape QA found/fixed side-navigation
occlusion using horizontal safe areas; tab text fitting accounts for those insets.
Rotation/font settings restored. SDK58 expo-system-ui58.0.7/plugin added for the
configured automatic appearance; new-binary behavior still needs checking.
60component checks,final lint/typecheck pass. Reviewed170-file upload excludes
credentials/env/logs/reports/Git metadata; Free plan0/15Android builds before request.
EAS remote keystore created and internal Android beta build
 ebb0569f-a711-4bc2-a177-d803c1297626 is IN_PROGRESS. It uses real production accounts,
not staging fixtures. No store/OTA submission or paid plan change. Do not request
a duplicate build: inspect the existing ID, obtain/verify/install when complete.
Private raw build metadata/auth state are OUTSIDE app source; safe current paths
in reports/finna-desk-pdf-20261119/native-progress.json. See EXPO.md there. Metro
87620/readonly preview70117 retained; only task-owned USB8081/8089 forwards. Earlier
resume error was a trailing-comma parser bug,corrected; login is complete.105API
bindings and20frozen PDF hashes still match; no backend/schema/mail/awards changed.
Full native/staging/iOS,actual healthy-week/legal/payment/source/human/volume gates
remain. Goal stays open;0110/0120 immutable,0122 next unreserved.

19 November continuation — saved PDFs and initial Android guest QA verified.
Four authenticated synthetic Desk print pages/17A4 Chromium pages rendered and
visually checked; Mizo/wrapping/margins/privacy pass,7existing note tests pass.
SamsungAndroid16/arm64 Finna Dev installed (503Gradle tasks/20m15s); actual Home/
Exams/Library/questions/filters/mock-builder/Desk/Me guest navigation checked.
Two sibling mobile files changed: src/app/(tabs)/index.tsx removes unbounded
Home action heights (1285→135px normal/252px at200%); components/BottomNavigation.tsx
fits full large-text tab labels within available widths. Final60component tests,
lint/typecheck pass; earlier29logic tests cover unchanged domain code. Font1.0
restored, orientation untouched; Home left open. All105 API/evidence source
bindings and production unchanged; no learner writes/mail/migration/awards.
Reports:reports/finna-desk-pdf-20261119/validation.json (PDF), native-device-qa.json,
NATIVE.md and native-progress.json. Keep frozen earlier proofs/recovery intact.
Metro session81977/readonly-preview40021, USB8081/8089 and isolated package
/tmp/finna-native-device-64u4rahe remain for the user's development preview.
Build daemon stopped; private Expo auth request state moved OUTSIDE app source.
EAS confirms Not logged in; official device login opened in owner's system
browser. Waiting for owner sign-in/CLI approval and optional CONNECTION match
number (never ask for password/MFA code). Pending private-state location is only
in native-progress.json; resume the exact request, one CLI command at a time.
No source upload/project/signing/cloud build yet. Full auth/offline/replay/long-
list/TalkBack/rotation/appearance/signed-performance/iOS gates remain. Hot font
change triggered a debug Router warning; cold200% and restored launches are clean.
Real healthy week/legal/payment/source/curation/human/volume gates remain. Full
goal is open; applied0110/0120 immutable, local0111–0119/0121,0122 next unreserved.

Section-count follow-up investigated — 19 November 2026: no production change.
Declared join order and disabled nested loops regress default-scope sections;
flattened materialized/inline taxonomy gives no useful speed gain. Two fresh
analyzed252-table clones preserve every original value;72 alternative comparisons
across36 baseline scenarios match (108 measured runs including baselines).
The materialized candidate passes27 synthetic checks, including null paths,
duplicate secondary paths and orphan source scope. Proposals rejected; runtime/
evidence remain the prior subject-count-order release,105-source evidence reconciles.
Exact clones/dumps/stages removed; API active,study/recovery200. No migration/mail/
restart/bank/learner write. Existing recovery0vhv3tic remains current. Reports:
reports/finna-section-count-plans-20261119/ and
reports/finna-section-count-flat-20261119/. Further measured query work and actual
healthy-week/legal/payment/source/curation/native/device/PDF/monthly-human/volume
gates remain; full goal open. Applied0110/0120 immutable,0122 next unreserved.


Subject-wise count improvement deployed — 19 November 2026: only its detail
transaction uses declared joins; other collections keep the default join setting.
The aggregate uses prepare=False to prevent cached-plan crossover across IDs.
SQL/DTO/source/cache/answer authority/scoring/writers unchanged. Global proposal
rejected after small-exam regressions; clone-only statistics never deployed.
1716full backend/exit0,641 integrated/432production compatibility,105/77bindings,
25integrity,62proposal and5paired-recovery checks pass. Fresh analyzed252-table
clone preserves every original value;68 comparisons equal,23–40% target speedup.
Live subject HTTP7.213→4.484s; both checked payload hashes identical to prior release.
Two-file scoped reader/evidence release;310source/3470static, schema/environment/
mail intact,ledger46→46,all8workers/both sites/API/recovery healthy. Current paired
recovery:/root/finna-subject-count-order-backup-0vhv3tic. Receipts:
reports/finna-subject-count-order-staged-20261119/ and
reports/finna-subject-count-order-production-20261119/. Earlier frozen proofs stay.
Desk/Atlas/referrals remain staged,0110/0120 immutable,0111–0119/0121 local,0122 next.
No new emails/migration/awards. Further slow-query review, real healthy week,
legal/payment/source/curation/native/device/PDF/monthly-human/volume gates remain.
The full goal remains open.

Collection-count improvement deployed — 19 November 2026: indexed readiness
below50k distinct questions, authoritative bulk view for larger sets, narrow
aggregate rows; membership/source/cache/DTO/scoring/writers unchanged. Earlier
ID-first and eager-global-view proposals rejected and preserved. Fresh analyzed
252-table clone preserves all original values;68 comparisons equal, large detail
16–23% faster (default JIT-off8.873→7.197s). Still slow: no all-query speed claim.
1602full backend/exit0,537 integrated/328production compatibility,105/77bindings,
25integrity and5paired-recovery checks pass. Three-file scoped release excludes
Desk/Atlas/referrals;310source/3470static files, schema/environment intact;
ledger46→46,all8workers/both sites/recovery healthy. Live subject-wise HTTP7.213s.
Current paired recovery:/root/finna-collection-adaptive-backup-xlky5zb3.
Receipts:reports/finna-collection-counts-adaptive-20261119/ and
reports/finna-collection-adaptive-production-20261119/. No mail sent or new
migration;0110/0120 immutable,0111–0119/0121 local,0122 next. Further count work,
actual healthy week/monthly human, legal/payment/source/native/device/curation/
saved-PDF/real-volume gates remain. Full goal stays open; preserve frozen proofs.

Collection-count investigation — 19 November 2026: no production release.
The ID-first/narrow-readiness proposal preserves all 68 real-data comparison
cases across eight collections/two scopes/JIT on/off; fresh analyzed dump clone
preserves all original values across 252 tables and is removed. Latency gains
are too small/inconsistent (including section regressions) to justify release;
subject-wise detail still around 8.5s. 458 integrated/249 production-only
compatibility checks and four recovery-operator checks pass; the experimental
105/77-binding candidates are evidence only. Keep the existing live digest
release and its paired recovery. No ready collection-count release scope exists.
All1509 experimental full-suite tests pass/exit0; final local reader and
binding/evidence restored to the exact prior104-source referral proof and
reconciled. See validation.json in reports/finna-collection-counts-staged-20261119/. Count optimization remains open;
all referral/Desk/Atlas drafts and real-week/legal/payment/content/native/human
gates remain. Applied0110/0120 immutable; local0111–0119/0121 remain drafts.

Latest local growth continuation — referral access (19 November 2026):
Signup-only email/Google attribution; ten current verified-key scored attempts,
both accounts verified/open, atomic seven Pro days each and five credits per
referrer per rolling year. Immutable attribution/decisions, concurrent replay/cap
locks, no historical attachment/award endpoint/native widening, no XP/points,
plan-field or provider mutation. System access has source=referral/NULL actor;
owner grants retain attribution. Private status/export/closure and once-only Inbox
receipts; no outbound referral email. Profile link creation/withdrawal and optional
Join notice/removal, Google forwarding and signup submission interlocks are staged.
Default false plus legal/recovery/live-checkout/current-evidence gates; not deployed.
1456full backend tests/exit0,387compatibility,104bindings/25integrity,3actual React
components and364-file build pass. Fresh252-table production clone preserves all
original column values;0121 applies34.556ms, real-mpsc probe rolls back. Oracle's
legacy broad default ACL was caught and explicitly revoked before narrow grants;
final suite/calibration/clone rerun pass.1280/320 light/night UI fits1265/1265 and
305/305 after correcting long-email wrapping. Exact preview DB/processes/ports/
marker/tab and remote clones/packages removed; Light/viewport restored. Both live
sites/API HTTP200; no production deployment or real awards/emails. Receipt:
reports/finna-referrals-staged-20261119/. See docs/FINNA-REFERRALS.md.
Private legal drafts prepared in docs/FINNA-LEGAL-DRAFTS.md, not published; public
operator/support/refund and other policy decisions still missing. Actual healthy
week/monthly human sign-off, paid/legal/native/source/curation/volume/saved-PDF
gates remain.0110/0120 applied immutable;0111–0119 and0121 local drafts;0122 next.
The full goal remains open. Preserve all frozen earlier proofs/recovery operators.

Latest growth release — review digest (19 November 2026): account/profile opt-in,
verified-email/address/consent checks, eligible due count/streak/Smart Review,
18:00–22:00 IST, one committed attempt per account/day, silent empty queues,
signed-out POST unsubscribe (GET inert), stale-consent/closure/privacy guards.
Shared mail capacity prioritizes recovery with reserved headroom. Withdrawal works
while paused and bypasses subscription throttles. No default subscriptions or
synthetic production emails/reviews. Initial1434 full-suite tests passed; the final
one-line throttle correction is covered by current356 integrated/178 production
compatibility tests,101/76 source bindings and25 integrity checks. Two actual React
components,363-file integrated/350-file production builds and320px light/night
QA pass. Fresh249-table clones preserve old values. Production reconstruction
excludes staged Desk/Atlas, applies only0120, retains3120 prior chunks/3470 files;
API/study/family/recovery healthy, ledger46→46/integrity0. Follow-up changes only
router/evidence; current root recovery backup:/root/finna-digest-backup-dqul4iva.
Reports:finna-review-digest-staged-20261119,finna-review-digest-production-20261119,
finna-review-digest-withdrawal-20261119. Applied0110 and0120 immutable;0111–0119
remain unapplied/local,0121 next unreserved. Natural backup/stats jobs now have
healthy completion receipts; actual healthy week/monthly human sign-off, referral/
paid/legal/native/source/volume/saved-PDF gates remain. Full goal stays open.


Latest sender setup — 19 November 2026: owner-approved three Hostinger DNS
records saved; Resend study.hawayu.in Verified/Forge Ready. Sending-only key scoped
to that domain stored in root-only /etc/mpsc/db.env; SMTP STARTTLS/auth pass,
private transfer file removed. One explicitly approved owner recovery email used
the existing encrypted outbox/reservation/send path: attempt 1 accepted, ciphertext
cleared, Resend delivered. Owner completed password reset and new-password sign-in;
server confirms consumed token, zero live reset tokens and a fresh session.
General account mail is enabled after a bounded API restart; recovery available,
API/study/family HTTP 200. No secret/link is in receipts. See docs/FINNA-EMAIL-SETUP.md
and sender evidence under reports/finna-atlas-depth-staged-20261118/. No Atlas/Desk
deployment or schema change. Digest/referral/launch and real-week gates stay open.


Latest local Atlas continuation — district proposals and cross-links (19 November):
Atlas III.5 step 4 code is locally staged: saved-exam ordering from current
published sections/live curated bindings, full list retained; owner-selected
Chronicle anchors with source fingerprints and fresh two-way event links.
Source/attribution/date/reuse and per-layer provenance are editable and visible.
Eleven private district starting proposals carry 2021 illustrative boundaries
(ODbL 1.0), approximate HQ and available river/peak points (GeoNames CC BY 4.0).
Empty layers stay empty. No current legal survey, complete reviewed district
content, real topic mapping or independent human sign-off is claimed. Owner
inspection/publication still required; proposals never auto-publish.
1415 backend tests/exit 0,337 compatibility,98 bindings/25 integrity,7 actual
components/screens and361-file final build pass. Fresh249-table dump clone
preserves all original values; real-mpsc private draft/index/two-way Chronicle
and earlier probes roll back. Browser draft/attach/preview/local publish,
synthetic binding, relevance/all toggle and map↔Chronicle exact-event roundtrip
pass;320px light/night client/scroll305/305. Preview groups/ports/exactDB/marker
and agent tabs cleaned; user's community tab retained,Light/viewport reset.
Receipt:reports/finna-atlas-depth-staged-20261118/. No production deployment.
Applied0110immutable;0111–0119local drafts,0120still next (no new migration here).
Real healthy week and source/owner curation, actual saved-PDF, mail/provider,
legal/native/paid-launch/real-volume/human gates remain. Owner selected
study.hawayu.in for Resend; configuration/DNS/delivery status is documented in
FINNA-EMAIL-SETUP.md. Preserve frozen earlier proofs/operators. Full goal open.

Latest local Atlas continuation — drills and question maps (18 November):
Atlas III.5 step 3 is locally staged: explicit pin/custom point-or-line drill
authoring, server-issued immutable activity/results, current-version exploration,
wrong-tap real-question links and optional Today suggestions. Ten distinct map
activities can fill the warm-up display but cannot qualify for a chest; drills
award zero XP/points and never change mastery, streaks or canonical attempts.
Optional fresh geography map context now uses the same AtlasMap inside ordinary
question cards/details and Smart Review; existing answer/scoring flow is retained.
Legacy quiz data is not automatically activated. No real bindings were seeded.
1407 backend tests passed (exit 0), 329 fresh compatibility checks, 96 runtime
bindings/25 integrity checks, six actual component/screen checks and a 357-file
build pass. Fresh
249-table clone preserves every original value; draft 0119 applied in 33.481 ms,
real-mpsc exploration/answer probe rolled back without economic writes.
Synthetic browser author/publish, correct/wrong tap, explored index, ordinary
practice link, Today suggestion and question map checks passed; phone 320px
light/night client/scroll widths were 305/305. Final request-reset component
regression covers account reload and changing chapter during a pending write.
Receipt: reports/finna-atlas-drills-staged-20261118/. Preview process groups,
ports, exact database/marker and agent tabs removed; user community tab retained,
Light/viewport reset. No production deployment or real healthy-week claim.
Applied 0110 stays immutable; 0111–0119 are local drafts, 0120 next unreserved.
Next: reviewed district depth, exam relevance/ordering, Chronicle links and source
licensing; actual saved-PDF, provider, legal, native, real-volume and human gates
remain. Preserve earlier frozen proofs/operators. The full goal is incomplete.

Latest local Atlas continuation — chapter Studio and reviewed data (18 November):
Atlas now reads versioned chapter data from the API; no runtime TS corpus import.
Draft0117adds immutable versions/events and per-author CAS/autosaved drafts;
draft0118seeds exactly26 unchanged chapters as current-site content, not new source
or independent review. Shared AtlasChapter renders learner and visible DRAFT
preview. /admin/atlas provides chapter/fact forms, pin/line/area drawing, draggable
vertices, palette/default/reorder/duplicate/cross-chapter layer copy/GeoJSON import,
undo/redo and captured/reorderable timeline views. Topic manager moves to
/admin/atlas/bindings; both link directions now require the current published body
hash and active registry. Chapter hold/content changes hide stale links on fresh
reads. Owner/MFA/CSRF, exact saved-preview publish, immutable attribution/history,
hold/restore and preserved conflicting author drafts; no bank/reward/native grants.
1398full backend tests/exit0,312fresh compatibility checks,94runtime bindings/
25integrity,3actual components including empty/held/undo regressions and355-file
build pass. Synthetic browser drawing/drag/undo/autosave/reopen/capture/publish/
hold/restore/import-rejection/layer-copy and1280/320px light/night QA pass without
horizontal overflow. Fresh249-table clone preserves all original values;
0117/0118apply26.320/28.293ms, real-mpsc seed/publish/hold/restore probe rolls back.
Receipt:reports/finna-atlas-studio-staged-20261118/. Preview process groups,ports,
exactDB/marker and agent tabs cleaned; user community tab retained,Light/viewport
reset. No production deployment: actual V.13healthy-week gate stays open.
0110applied/immutable;0111–0118draft locally,0119next unreserved. Preserve earlier
frozen proofs/operators. Next non-economic drill authoring/activity/explored state,
bank-question map context, district depth/relevance/Chronicle and source licensing.
Real reviewed topic bindings remain unseeded. Actual saved-PDF pagination and
provider/source/legal/native/real-volume/human gates remain. Full goal incomplete.

Latest local Atlas continuation — reviewed topic bindings (18 November):
Existing26static chapters now have a shared, explicit owner-curated binding store,
ordinary asked-from-map question panel and reverse card/detail chapter/layer/event
links. No real topic mappings inferred or seeded. Owner/MFA/CSRF, CAS decisions,
immutable save/publish/hold/restore history and exact source/registry versions;
fresh reads preserve source scope, assessment embargo and normal browse allowance.
1384full backend tests/child exit0,298fresh compatibility checks,91runtime bindings/
25integrity,55direct-call/native/Atlas checks,3actual components and353-file build
pass. Browser save→8preview→publish→5+3pages→reverse→hold-empty→restore and inline
answer pass at1280/320px light/night, no horizontal overflow. Fresh249-table clone
preserves every original value;0116apply23.557ms,100-ID empty reverse1.633ms,
real-mpsc synthetic publish/hold probe rolled back. All preview process groups,
ports,exactDB/marker and agent tabs removed; user tab retained,Light/viewport reset.
Receipt:reports/finna-atlas-bindings-staged-20261118/. No production deployment;
actual V.13healthy-week gate remains.0110applied/immutable,0111–0116draft locally,
0117next unreserved. Next full chapter lifecycle/Atlas Studio, one learner/draft
renderer and truthful26-chapter migration, then drills/explored/depth/relevance/
Chronicle/source licensing. The binding manager is not the chapter editor. Actual
saved-PDF pagination and provider/source/legal/native/real-volume/human gates stay
open. Preserve older frozen scopes/proofs. Full plan and goal remain incomplete.

Latest local Desk continuation — central-calendar room view (18 November):
Room calendar reads explicitly shared central calendar_entries rows; personal exam
countdowns and opt-in milestones use the existing owner/CAS/recurrence framework.
Private default, per-entry room choice/withdrawal, exact membership epoch, blocks,
closure, flag and native guards; no second store, copied events or new rewards.
1379full backend/exit0,250fresh compatibility/calibration,84bindings/25integrity,
13focused calendar checks, actual central form/reader/circle screen,350-file build
and final1280/320px light/night browser sharing/withdrawal checks pass. Fresh249-table
clone preserves every original value;0115apply5.251ms, real-mpsc probe rolls back.
Receipt:reports/finna-desk-calendar-staged-20261118/. Preview process groups/ports,
exact database/marker and agent tabs cleaned; other user tab retained, Light and
viewport reset. No production rollout: actual V.13healthy-week gate remains.
0110applied/immutable;0111–0115draft reservations,0116next unreserved. Preserve all
frozen earlier scopes/proofs. Desk§1.7/1.8are locally staged; actual saved-PDF
pagination is unverified. Next Atlas/Studio; provider/source/legal/native/real-volume/
human gates and the full goal remain open. Never mark the whole plan complete here.

Read `CLAUDE.md` and `docs/PLAN.md` before working in this repository.

Previous local Desk continuation — question notes (18 November):
Personal/shared notes now attach canonical question IDs; room chat links use live
same-room references and recheck source/member/block/assessment visibility. Owned
saved-note JSON export and browser print/save-as-PDF reuse account guards; hidden
notes survive unrelated full-document saves. No server PDF engine:0077 is PDF-library
inventory, and an actual PDF save/pagination remains unverified. Native new paths
stay closed, no awards.1374full backend/exit0,237fresh compatibility/calibration,
82bindings/25integrity checks,5actual components,350-file build and synthetic
1280/320px browser QA pass. Fresh249-table clone preserves every original value;
0111/0112/0113/0114apply12.143/4.216/5.174/6.531ms, real-mpsc probe rolls back.
Receipt:reports/finna-desk-notes-staged-20261118/. No production rollout; actual V.13
healthy-week gate remains.0110applied/immutable;0111–0114draft reservations,0115next.
Preview processes/database/tabs cleaned. Preserve all frozen prior scopes/proofs.
Next room view of central calendar, then Atlas/Studio and external source/provider/
legal/native/real-volume/human gates. Full goal remains open.

Previous staged continuation — synchronized Desk practice (18 November):
Private rooms now create/join/resume the existing frozen party engine over explicit
question/bookmark shares: ten official-key-eligible questions,25 seconds,2–4 players.
Six-seat Desk/Pro creation rules stay; no private saves or consent-based mistake
copy, no new awards. Current membership epoch, either-direction blocks, exact
source withdrawal/author departure, closure, embargo and the private flag guard
reads/writes and lifecycle finalization. Generic join codes cannot bypass Desk;
binding/context/snapshots are immutable. Native new paths remain closed; inherited
ready/start/answer reject bound rooms, existing GET/seat release remain. Existing
GameRoom player reused, explicit confirmation and stable request replay, active
resume and honest assessment-locked empty states. Semantic night colors corrected
for practice intro/sidebar/game surface.80 fresh source bindings,211 compatibility /
calibration checks including reward diagnostics, actual components/build/browser
checks pass. Fresh249-table production clone preserves every original value;
0111/0112/0113apply13.169 / 4.642 / 6.105 ms, real-mpsc rolled-back binding/withdrawal /
consent/privilege probe passes. 1,366 full backend tests passed with exit 0. Final validation lives in
reports/finna-desk-practice-staged-20261118/. No production rollout: actual V.13
healthy-week gate remains.0110 applied/immutable;0111–0113 are draft reservations,
0114 next unreserved. Keep all earlier frozen scopes/proofs/operators intact.
Next question notes/PDF via account export safeguards, room view of the central
calendar, then Atlas/Studio; provider/source/legal/native/real-volume/human gates
and the full goal remain open.

Previous local Desk continuation — 18 November:
Owner “do it / go” has locally staged Desk v4 weekly room goals, review-circle
flag/resolve/reopen/filter controls and the opt-in current focus board. No production
rollout: V.13still requires an actual healthy week. Existing private-desks flag,
server timer/recap, verified-scoring helper, six-seat/Pro rules and reward policy
remain. Goal current membership/consent/blocks/join-time/IST week/latest assessment
and owner/CAS guards; circle shares item versions and per-viewer mock/game gates.
Native new goal/discussion paths stay closed.1352full backend/exit0,15goal+recovery
checks,3actual components/build and browser QA pass. Final proof lives in reports/finna-desk-goals-staged-20261118/.
Fresh249-table production clone preserves every original value;0111/0112apply
13.590/4.693ms, real-mpsc rolled-back probe/consent revoke/delete privilege pass.
0110is latest APPLIED/immutable.0111/0112are draft reservations locally, unapplied
in production;0113next unreserved. No release target/operator deployment yet.
Keep older frozen release proofs intact. Latest LIVE baseline is still the detail-
performance/build/environment/logging stack below. Never replay older targets.
Continue synchronized practice, notes/PDF, central-calendar view then Atlas in its
order; source/provider/legal/native/human/full-week gates and full goal remain open.

Latest continuation checkpoint — question-detail performance:
V.12 question-detail performance correction is deployed (18November2026).
get_question reuses existing bounded readiness/publication helpers; every other
question-router AST node/writer is identical. The unchanged helper is newly source-
bound (73total); fresh156calibration/compatibility checks,1335full backend/exit0
and2supplemental reader/evidence recovery checks pass. No scoring/source/visibility
rule or schema change. Actual clone83,383canonical statuses/reviewed flags match
with0mismatches,2scopes/JITon+off/missing/outside payload parity,249-table complete
preservation. Derived detailSQL~4.4s→3–4ms. Final fresh candidate/compatible-prior
249-table rehearsal matches statuses, preserves all rows and cleans clone/dump.
Live3API/evidence hashes match;5detail HTTP samples19–30ms,SQL2.8–5.4ms, answer
material absent and status/provenance correct. All8workers healthy,3account/
27private+3public learning reads plus5detail samples,25reward/3edit/2bulk counters0,
ledger46→46,mail0,bothsites200. Static348built/3344served,Python env/requirements,
PSQL logging/rotation,restore tool/13collector+unit files unchanged.0110immutable,
next0111. No bank/workshop/provider changes or synthetic production activity.
Receipt:reports/finnaplan-v12-query-performance-20261118/README.md.
Backup:/root/finna-v12-query-performance-backup-scpanrxd. Exact-source recovery
restores prior3-file reader/evidence pair, only restarts API and never restores
DB/history/static/environment. Later drift refuses recovery; target is frozen,
never replay this or older releases. Current baseline overlays3API files on the
build release’s3344static/new env/logging profile. All candidate/fullsuite/clone
processes completed; no preview/tab/temporary DB remains. No production recovery.
Source audit of Desk/Atlas completed in docs/FINNA-DESK-ATLAS-GAPS.md; no later
phase implementation or fabricated bindings/chapters was introduced. Existing
focus presets/toolbox are already present; reuse them.
Other observed collection-count shapes~1–1.6s remain separately profiled. Build-only
picomatch advisory unpatched; runtime npm/Python dated audits clean. Monthly human
sign-off/real log review, natural backup/stats outcomes and a full healthy week
remain open. Desk/Atlas/Studio are the later build-order phase; current source audit
must distinguish existing desk toolbox/timer from missing v4 extensions and static
26chapter Atlas from missing curated bindings/Studio. See remaining index. Real
email/digest/referral/paid/legal/native/exam-source prerequisites remain. Full goal
stays open; never reset or complete it for a slice.

Previous frontend build checkpoint:
V.12 frontend build-dependency remediation is deployed (18November2026).
Vite5.4.21→6.4.6,esbuild0.21.5→0.25.12,selector-parser6.1.4→6.1.6; all browser-runtime
npm versions unchanged. Runtime-only advisory scan0; full build graph retains11
package-chain findings from one unpatched picomatch GHSA-fc5q-39xc-vjpf (published
v2/v4 latest2.3.2/4.0.7). No risk acceptance/whole-project-clean claim. Four real
component/navigation scripts, build, two supplemental static recovery checks and
built-artifact1280/320px light/night QA pass.6887CSS AST entries keep rules /
declarations/cascade;15differences only media whitespace. Desktop1265/1265and
phone305/305no overflow; phone private search/all5sections and learner library pass.
No new full backend suite claimed for this static slice; preceding1324remains.
348built/3344served hashes,2996retained old chunks,17route shells/2entry assets
verified. API PID/environment/source/schema/PSQL config/restore-tool/13host paths
unchanged. All8workers healthy,3accounts/27private+3public learning reads,integrity0,
ledger46→46,mail0,bothsites200.0110immutable,next0111. Six synthetic screenshots;
preview API/web/tab/exactDB/marker cleaned,viewport reset. Native/device not certified.
Receipt:reports/finnaplan-v12-build-dependencies-20261118/README.md.
Backup:/root/finna-v12-build-dependencies-backup-vjq_0cd7. Exact-source recovery
restores prior HTML/assets while keeping newer immutable chunks for open tabs;
no service restart or DB/history rollback. Newer drift refuses recovery. Target
is frozen; never replay it or older dependency/logging/maintenance targets.
Actual initial log review (query-logging report/initial-log-review.json) captured
15duration entries since the real probe:1probe+14others,max4522.711ms. This is a
short observed window, not a long-term or human-signoff claim. Investigate query
shapes next using private logs/normalized aggregate metadata, never export bind
values or mark the healthy week complete. Source/runtime baseline now comes from
the build-dependencies scope (3344served) plus the deployed package/logging receipts.
Other email/paid/legal/native/exam-source/monthly-human/full-week/later product gates
remain open; continue the full goal without resetting/completing it for a slice.

Previous query-logging checkpoint:

V.12 PostgreSQL slow-query logging is deployed (18November2026). Threshold1000ms,
bind parameter/error parameter lengths0; existing stderr/0640log and weekly10-file
rotation preserved. Three audited defaults changed via ALTER SYSTEM + reload only;
API PID/PostgreSQL start time unchanged.5operator checks pass. Actual read-only
mpsc probe logged1102.161ms; bind canary absent, no raw queries/values exported.
Exact source/environment/schema/static/collector/rotation guards pass,8workers
healthy,integrity0,ledger46→46,mail0,bothsites200. No schema migration;0110immutable,
next0111. This starts evidence collection today, not historical slow-query review.
Receipt:reports/finnaplan-v12-query-logging-20261118/README.md.
Backup:/root/finna-v12-query-logging-backup-9_m32fsh has private prior auto-conf and
exact operator/scope. Recovery refuses drift, resets only these3keys and verifies
prior config; never resets database/history or restarts services. Production
recovery not invoked. Frozen logging target must never be replayed.
Maintenance and Python dependency releases below remain current. Frontend npm
advisories, monthly human sign-off/actual log review, scheduled backup/stats outcomes
and full healthy week remain open. Continue independent frontend remediation;
email/digest/referral, paid/legal/native/exam-source and later product gates remain.

Previous dependency checkpoint:

V.12 Python dependency remediation is deployed (18November2026). FastAPI0.163.2,
Starlette1.10.0 and their3fixed purepy dependencies installed from5SHA256-bound
local wheels, entirely offline on Oracle. All other production versions retained.
Actual live package versions exactly match the clean dated advisory input; this
is not a blanket/npm/future security guarantee.1324full framework backend checks,
81focused and2supplemental environment/wheel/recovery checks pass. Fresh249-table
clone under the staged Oracle environment preserves every original row; real-mpsc
learning/economy verification passes.2971installed environment-file fingerprints,
requirements and versions verified after atomic environment swap. API/static /
schema/economy bindings/restore-tool/13host collector+unit paths unchanged. All8
workers healthy,ledger46→46,25reward/3edit/2bulk integrity counters0,bothsites200,
0mail attempts. No synthetic production activity or database rollback.0110stays
immutable,next0111. Source/test changes here are requirements + bounded operator /
recovery guards; frontend markup and artifacts unchanged.
Receipt:reports/finnaplan-v12-dependencies-20261118/README.md.
Backup:/root/finna-v12-dependencies-backup-afhwfwbb stores exact prior environment /
requirements; recovery refuses later API/static/schema/environment/tool/unit drift
and never restores DB history. Frozen dependency target must never be replayed.
Local api/.venv updated from the same5offline wheels; pip check passes. Separate
candidate fullsuite completed515.23s,exit0; no running preview/test/clones remain.
Next: bounded slow-query logging with parameter suppression and existing rotation;
frontend npm findings remain separate. Monthly human sign-off, green week, real
scheduled backup/stats outcomes, email/digest/referral and launch/native/source /
later product work remain; full goal stays open.

Previous maintenance checkpoint:
V.12 retention/site notice/restore maintenance is deployed (18 November2026).
0110is applied and IMMUTABLE; next migration0111. Hourly account cleanup keeps
progress/finance/adoption/durable replay receipts and original activity timestamps;
empty-guest filtering protects default/profile/access state, legacy actor IDs and
future/alternate/composite FKs.5s/1s limits,500transient/20guest batches and heartbeat
counts apply. Native notice/admin paths stay closed. Owner/MFA/CSRF/versioned
plain-text site notice has IST expiry, minute refresh and immutable account audit.
Initial live setting is blank; no synthetic production announcement.
1324full backend checks/exit0,154final source-bound compatibility/calibration /
72runtime bindings,25focused maintenance/9restore/2operator recovery checks
(overlap), real components/build and1280/320px light/night QA pass. Native guard
assertions were added after full collection and pass in the154final run; exact
runtime inputs unchanged. Final fresh248-table clone preserves every original
row; migration29.253ms,actual-mpsc rolled-back retention/notice/protection probe and
compatible prior readers pass. Live0110apply95.136ms.11API/348built/3211served
hashes match,2863retained chunks,284unchanged API/schema dependencies and13host
collector/unit paths protected.3real accounts/3public+27private learning reads,
25reward/3edit/2bulk integrity counters0,10tier+5bulk triggers,ledger46→46,
mail attempts0,bothsites200. All8workers healthy; real first sweep removed8expired
review budget buckets,0accounts/sessions/other records. Bank-review/host timer
healthy; natural backup/stats job receipts unknown, not backfilled.
Actual monthly paired restore completed18Nov10:17:14UTC from17Nov20:20:08UTC backup:
232archived tables/124944files,real read-only-role bank pairing and full cleanup.
Ops shows0days since success, attention at40days; verified restore tool installed.
Monthly human sign-off remains pending. Agent-assisted audit found dependency
advisories and disabled slow-query logging; TLS/bothsites200 and logrotate active.
No dependency-clean, whole-checklist, offsite/source completeness, device or real
healthy-week claim. No bank/workshop/Caddy/provider changes or production recovery.
Receipt:reports/finnaplan-v12-maintenance-20261118/README.md.
Backup:/root/finna-v12-maintenance-backup-n3jzh49v. Exact-source recovery preserves
0110,all DB history, retained-activity account reader and verified restore/tool /
collector paths; other API/static return to prior pair. Newer drift refuses recovery.
Frozen target finnaplan-v12-maintenance must never be replayed. Local preview API /
web/tab/exactDB/marker removed,viewport reset; five synthetic PNGs retained.
Next independent work: dependency/security and slow-query observability follow-up.
Separate /tmp/finna-security-candidate-20261118 contains FastAPI0.163.2/Starlette1.10.0,
81targeted checks and clean candidate advisory scan after pip upgrade; no package
or requirements update deployed yet. Existing api/.venv stays unchanged. Candidate
reports remain supplemental in maintenance report; move next work into a new
source-bound release, never rewrite frozen maintenance proofs. Email/digest/referral,
real healthy week, later Desk/Atlas/Studio, exam sources/native/device/legal/paid
launch prerequisites remain. Continue the full goal; never mark complete for a slice.

Previous account-viewer checkpoint (historical):
V.12 read-only account viewer is deployed at /admin/users (18 November).
Exact-email/literal-handle search and per-account account/access/study/economy /
community summaries use a repeatable-read/read-only snapshot,5s statement limit,
global-owner permission and the existing staff MFA/exact-ID exemption policy.
Native bearers and scoped owners are denied. No viewer mutations, answer history,
private desks, credential/device material, ledger item notes/keys or block identities.
Entitlement uses account_has_pro(); scoring and community rules reuse live helpers.
Search/results/selection clear across auth transitions; late responses are discarded.
44targeted compatibility checks,10final account/recovery and2separate recovery
checks (overlap), build, real component/navigation and1280/320px light/night QA pass.
Phone search controls stack; no overflow (1280/1280desktop,320/320phone). No new full
suite claimed for this read-only slice; preceding1277full/exit0 remains historical.
Final fresh248-table production-dump clone preserves every row. Live real-mpsc
read-only snapshots cover3accounts (12–29ms each),3public+27private learning reads,
25reward/3edit/2bulk counters0,10tier+5bulk triggers,ledger46→46,economy reconciled,
0mail attempts.3API/348built/3086served hashes,2738retained chunks and288unchanged
API/schema dependencies verify;13collector/unit paths stay fixed.9route shells,
anonymoususers401,runbook hash andbothsites200 pass. All7workers,bank-review/host
timer anddisk/backup probes healthy; first natural backup/stats outcomes unknown.
No migration, bank/workshop/Caddy/provider/dependency change, synthetic production
activity or commit.0109immutable; next0110. Mail/checkout remain disabled.
Receipt:reports/finnaplan-v12-users-20261118/README.md.
Backup:/root/finna-v12-users-backup-8eqzsmv9. Exact-source recovery guards installed
API/schema/static/collector/unit hashes and restores prior reader/static pair;
all history/writers/collectors stay.2disposable recovery checks pass; production
recovery not invoked. Never replay older frozen targets over this release.
Preview API/web/tab and exact final/interrupted disposable DBs removed; marker
cleaned,Light/viewport restored,user help tab retained. Four final synthetic PNGs.
Next independent work: V.12retention, site notice andmonthly checklist/actual
restore receipt; genuine healthy-week gate needs elapsed operation. V.11actual
email/digest/referral prerequisites,later Desk/Atlas/Studio work,V.7actual sources,
native/device andlaunchgates remain. Whole plan stays open. The user has explicitly
started a new unbounded active goal,finish without interruption; continue it and
never reset it or mark it complete for a single slice. Older usage-limited goal
notes below are historical and do not describe the current active goal.

Previous collector-time checkpoint (18 November 2026):
V.12 cycle/collector release and final timer-time display correction are deployed
(18 November). Assessment/desk/calendar/game cycles, explicit mastery failures,
real additive bank/backup/stats outcome hooks and the five-minute host collector
now feed /admin/ops. Disk and newest paired-backup digest/index verification are
healthy; all seven worker observations are healthy. Natural bank-review execution
has a healthy receipt; backup/stats outcome hooks await their next scheduled runs,
with no historical successes backfilled. Mail worker health does not mean email
delivery: mail and checkout remain disabled. No green-week/restore claim.
The final read-only classifier uses a structured collector outcome instead of the
in-process100ms timestamp tolerance: collection/hash/peer-write latency cannot
create false attention. A normal-zero-exit requirement still guards timer success;
failed/stale/future/malformed receipts keep their own states. This correction
changes only ops.py; static2961files,collector/units,schema and68economy-bound
sources remain unchanged. No new full suite is claimed for the reader repair:
1,277full tests with exit0 precede only this read-only change;11focused regressions
and actual-mpsc production read-only candidate/live checks cover it. Worker release
also has118fresh calibration checks/68bindings,248-table exact preservation and
rolled-back real-role probes, build/components/navigation and1280/320px light/night
QA. Full release9API/347built/2961served/2614retained chunks/280unchanged dependencies
and6collector/unit hashes verify. Final live3public+27private learning reads,
25reward/3edit/2bulk counters0,10tier+5bulk triggers,ledger46→46,economy reconciled,
0mail attempts,anonymousops401 andbothsites200. No migration, bank/workshop/Caddy /
provider/dependency change, synthetic production activity or commit.0109immutable;
next0110. Only real operational heartbeat rows are added by collection.
Receipts:reports/finnaplan-v12-workers-20261118/README.md and
reports/finnaplan-v12-collector-time-20261118/README.md.
Worker backup:/root/finna-v12-workers-backup-9r_rlztk.
Final reader backup:/root/finna-v12-collector-time-backup-5atf23ce. Latest reader recovery restores only its exact
prior classifier after API/schema/static/unit/collector drift checks; current
writers,installed collectors and history stay. Do not invoke the older whole-worker
recovery over this reader update; its hash guard refuses. No production recovery
invoked. Initial preflight staging-cleanup permissions were fixed before release;
private temporary stages removed. Preview API/web/tab/DB marker cleaned,Light /
viewport restored,user help tab retained (IAB surface2→4). Five synthetic PNGs.
Next independent implementation: read-only /admin/users account viewer, then
retention/site notice/monthly checklist and actual restore/healthy-week evidence.
Observe first natural backup/stats outcomes. V.11actual email/digest/referral,
later product/real-volume ranking,V.7actual sources,native/device andlaunchgates
remain. Whole plan open; do not resume/reset usage-limited goal automatically.

Previous worker release checkpoint (18 November 2026):
V.12 worker cycles and host collectors are deployed (18 November). Assessment,
desk retention, calendar and game cycles now write transaction-bound success /
bounded post-rollback failure receipts. Mastery failure labels are explicit;
last success survives failure. Desk notes show aggregate purge counts. Existing
mail/nightly receipts remain; worker health does not certify email delivery.
Exact additive outcome hooks on bank-review, paired-backup and stats jobs require
actual SERVICE_RESULT plus normal zero exit; original jobs/schedules are preserved
and none is manually started for proof. A new five-minute host collector measures
disk and verifies the newest backup pair's archive/dump digests plus dump index.
Root-only metadata/identity cache invalidates changed files; newest incomplete /
corrupt evidence fails visibly with no older fallback. Backup creation/collection
times are distinct;15minute collection/48hour backup staleness and10GiB disk warning
render. This is not a restore rehearsal or a green-week claim. First daily job
outcomes remain unknown until actual runs; none is backfilled. Mobile Questions
navigation preserves needs-review.
1277full backend tests pass with explicit process exit0.45targeted,14collector,
24final focused and2operator-recovery checks (overlap),118fresh calibration /
compatibility checks with68runtime bindings/25diagnostics, local build/components /
navigation and1280/320px light/night browser QA pass. Fresh248-table dump clone
preserves every row; actual-mpsc synthetic heartbeat/collector writes fully roll
back. Live3public+27private learning reads,25reward/3edit/2bulk counters0,
10tier+5bulk triggers,ledger46→46,economy reconciled,0mail attempts.9API/data,
347built/2961served hashes,2614retained chunks,280unchanged dependencies,
6collector/unit files,8shells,anonymous401/runbook hash andbothsites200 verify.
No migration, bank/workshop/Caddy/provider/dependency change, synthetic production
activity, success backfill or commit. Only real operational heartbeat rows are
added by collection.0109immutable;next0110. Mail/checkout remain disabled.
Receipt:reports/finnaplan-v12-workers-20261118/README.md.
Backup:/root/finna-v12-workers-backup-9r_rlztk. Recovery validates API/schema/static/base-unit/drop-in/collector
hashes, disables only the new host timer and restores the exact prior compatible
API/economy evidence/static pair. All history/heartbeat rows and original units /
schedules stay; disposable drift/recovery checks pass,production recovery not
invoked. Never replay frozen targets. Final browser reconnect changed IAB2→4;
preview tab/API/web/DB cleaned,Light/viewport restored,user help tab retained.
Next independent implementation: read-only account viewer, then retention/site
notice/monthly checklist and actual restore/healthy-week evidence. Observe first
natural backup/stats outcomes. V.11actual email/digest/referral, later product /
real-volume ranking,V.7actual sources,native/device andlaunchgates remain.
Whole plan open; do not resume/reset the usage-limited goal automatically.

Previous ops dashboard checkpoint (18 November 2026):
V.12 read-only ops dashboard is deployed at /admin/ops (18 November). The
owner-only, web-only API uses a repeatable-read/read-only snapshot with a5s SQL
statement limit. Existing mail/mastery receipts, separate legacy reassessment
observation, explicit missing/stale/attention states, real per-process pool
occupancy, IST-yesterday mint/redemption/cap totals and bounded human-review
flags, plus five moderation queues with median age/48h counts are available.
Refresh and auth transitions discard old snapshots; failure is never empty data.
Runbook links and desktop/mobile admin navigation work. Worker instrumentation,
timer/disk/verified-backup collectors and live webhook metrics are NOT completed
by this slice; unknown rows remain explicit. No healthy-week claim.
44focused compatibility checks plus7final ops/recovery checks (overlapping suites),
real component/navigation checks, build and1280/320px/light/night synthetic browser
QA pass. No new full-suite run for this read-only slice; the prior full1259-case
bulk baseline remains historical. Fresh248-table production-dump clone preserves
all existing rows. Real-mpsc RR/read-only reads,3public+27private learning checks,
25reward/3edit/2bulk counters0,10tier+5bulk triggers,ledger46→46,economy reconciled,
0mail attempts.4API,347built/2838served hashes,2491retained chunks and284unchanged
dependencies verify;8route shells,anonymousops401 andrunbook hash pass;bothsites200.
No migration, economy-bound writer/evidence, bank/workshop/provider/unit/dependency
change, synthetic production activity or commit.0109immutable; next0110.
Receipt:reports/finnaplan-v12-ops-20261118/README.md.
Backup:/root/finna-v12-ops-backup-52_pa_zk. Exact-source recovery restores only prior
ops readers/router registration/pool helper/static; all current writers/schema /
history stay. Drift refusal and recovery tested in disposable files, production
recovery not invoked. Never replay frozen release targets. Preview tab13/API/web /
DB cleaned; Light/viewport restored and original user tab retained.
Next: standard cycle receipts for assessment/desk/calendar/game, actual timer /
backup/disk collectors; then account viewer, retention/site notice/checklists and
actual green-week evidence. V.11email/digest/referrals, later Desk/Atlas/Studio,
real-volume ranking,V.7actual sources,native/device and launch gates remain.
Whole plan stays open; do not resume/reset the usage-limited goal automatically.

Previous bulk-pricing checkpoint (18 November 2026):
V.11 bulk ₹50 next-subscription pricing is deployed (18 November). Existing
owner Rewards & accounts has100-email preview/apply batches with exact preview
hashes and durable retries, verified-email-only matching at add/signup verification/
successful login, once-only application and retained removal history. Typed email
alone never matches. Optional pricing runs after identity commit and cannot block
sign-in. Group links prefill an explicit claim form; server-fixed5000paise,
100uses/30days defaults (bounds1–1000/1–90), per-code/account receipts, cap/expiry/
revocation and actual-price replay hold. No Pro/points/payment/provider action.
Owner search reaches retained emails/codes/notes; on-demand50-row cursor receipts
show who claimed, including revoked/expired/anonymous closed history. New routes
stay web-only; owner/MFA/CSRF/origin/account/version boundaries and own-data exports
hold. Existing mandates and manual account-price authority remain.
1,259full backend cases pass with explicit process exit0, then11focused final
read-only receipt checks;68earlier targeted/28boundary/2recovery checks. Final
104source-bound calibration/compatibility checks retain67runtime bindings and25
reward diagnostics. Build, real components/10redirects/111links and1280/320 light/
night synthetic browser QA pass,305/305px no overflow. Full suite precedes only
the final read-only receipt reader; that reader has focused/current calibration,
actual-mpsc clone and browser proof. Initial terminated/interrupted runner logs
remain historical. Fresh244-table clone preserves every prior row,0109apply
35.566ms; verified-once/batch/code replay/cap/revoke/owner-receipt probe fully rolls
back. Live3public+27private RR/read-only checks,25reward/3edit/2bulk counters0,
10tier+5bulk history triggers,ledger46→46,economy reconciled.11API/data,
345built/2713served hashes,2368retained chunks,274unchanged dependencies and8shells
verify; bothsites200.0code redemptions at apply, no agent production list/code/
discount, synthetic learner, bank/workshop/provider/billing/unit/dependency change
or commit. Mail disabled/unconfigured,0attempts; checkout/catalog remain closed.
0109applied/immutable; next0110. Receipt:
reports/finnaplan-v11-bulk-20261118/README.md. Backup:
/root/finna-v11-bulk-backup-0wysk7wv. Guarded recovery keeps0109/current compatible
pricing/auth/export/mail/onboarding/CMS/shared API and all histories, pauses only
new bulk assignment and restores prior static. Economy remains reconciled under
pause; disposable recovery passes, production recovery not invoked. Never replay
frozen targets or restore older writers.17synthetic PNGs include readable owner
claim receipts; tabs10–12/API/web/DBs cleaned, viewport/Light restored, original
user help tab retained. Native/device certification remains open.
Remaining index:docs/FINNA-REMAINING.md. V.11 still needs actual email delivery /
verification/recovery activation, opt-in digest with consent/unsubscribe, and
post-launch qualified/capped referrals. V.12ops dashboard/timer collectors, account
viewer, retention/site notice/checklists and actual green-week evidence remain;
next independent build is ops. Later Desk/Atlas/Studio, real-volume ranking,
V.7actual exam sources, native/device and catalog/legal/checkout gates remain.
Whole plan remains open; do not resume/reset the usage-limited goal automatically.

Previous check-in checkpoint (18 November 2026):
V.11 optional primary-exam check-in is deployed (18 November). Today/account
study setup links to ten eligible distinct official-key questions, mixed by actual
approved active subjects/topics. One ordinary saved practice set/account/exam
resumes across retries/devices; selecting another primary preserves progress.
Normal source-bound grading, mastery, discovery caps and immutable feedback stay
in force; loading status creates no activity/earning plan and there is no bonus.
Finished suggestions use exact checked receipts/current eligibility; viewed,
skipped and excluded answers are not evidence. Existing focus stays until the
learner explicitly selects and saves. No exam-readiness claim. New endpoints and
inherited saved-set paths stay outside native capabilities; old recent lists
hide the marker. Account/primary change and request-key boundaries hold.
1,247full backend tests,55targeted/46boundary checks,2operator-recovery checks,
91fresh calibration/compatibility checks (61runtime bindings/25diagnostics), build,
actual components/10redirects/111links and1280/320px/light/night synthetic browser
QA pass. Fresh244-table dump preserves every existing row;0108apply5.177ms and
fully rolled-back real-mpsc10-check probe pass. Live3public+24private reads,
25reward/3edit counters0,10tier triggers,ledger46→46,economy reconciled.7API/data,
345built/2591served hashes,2246retained chunks,273unchanged dependencies and8shells
verify; bothsites200.0production check-in sets at apply; no synthetic learner /
award/bank/workshop/provider/billing/unit/dependency change or commit. Mail remains
disabled/unconfigured with0attempts.0108applied/immutable; next0109. Receipt:
reports/finnaplan-v11-onboarding-20261118/README.md. Backup:
/root/finna-v11-onboarding-backup-eoupr387. Recovery retains0108/current compatible
onboarding/mail/CMS/shared writers and all history, pauses only new check-in starts
and restores prior static. Pause preserves source-bound economy reconciliation;
changed writers still invalidate it. Disposable recovery passes; production
recovery not invoked. Never replay frozen targets or restore older writers.
Browser sample5correct/3wrong/1viewed/1skipped; only Mizo suggested from1/4 vs
English4/4, explicit saved focus survives reload. Clean screenshot:
reports/finnaplan-v11-onboarding-20261118/checkin-summary-desktop.png. Full-page
fixed-header artifacts/timing limits documented; preview tab/API/web/DB cleaned,
Light/viewport restored, original user tab retained. Native/device certification
remains open. Next V.11: opt-in due-review digest needs actual email transport /
consent/unsubscribe; referral stays post-launch/attempt/cap gated; bulk pricing
remains. V.12ops/users/retention and later Desk/Atlas/Studio, real-volume ranking,
V.7actual sources and catalog/legal/email/checkout activation remain. Whole plan open.

Previous sharing checkpoint (18 November 2026):
V.11 public question/test share previews are deployed (18 November). Question
More copies a public source-bound HTML preview and offers WhatsApp; published
tests use their live immutable metadata. Escaped question/exam/year, Finna OG/
Twitter metadata and shared1200×630brand PNG replace bare links; explicit Open
links retain crawler metadata. No answers/private context, awards or messages.
Unavailable/exact-source/scope/native guards and current-item copy outcomes hold.
1,236full backend tests,12targeted,1operator-recovery,81fresh calibration checks
(58runtime bindings/25diagnostics), build/components and1280/320px/light/night
control QA pass. Fresh244-table dump preserves all rows;3public+21private reads,
25reward/3edit counters0,10tier triggers,ledger46→46,economy reconciled.4API/data,
344built/2469served hashes,2125retained chunks,273unchanged dependencies and8shells
verify; bothsites200. Mail remains disabled/unconfigured with0attempts. No SQL,
bank/workshop/learner/provider/billing/unit/dependency changes or commit.0107stays
applied/immutable; next0108. Receipt:reports/finnaplan-v11-sharing-20261118/README.md.
Backup:/root/finna-v11-sharing-backup-2__tbumw. Guarded recovery restores only prior
share/question readers, matching evidence/static and removes the new helper;
current mail/review/CMS/history remain. Disposable recovery passes; production
recovery not invoked. Never replay frozen targets. Shared thumbnail is brand art;
actual question/source is OG text. WhatsApp rendering/cache and OS-dark standalone
preview are not certified; browser clipboard success feedback is distinct from
empty session readback (exact payload/fallback covered in component tests).
Next independent V.11work: onboarding diagnostic; digest needs actual mail plus
consent/unsubscribe, referral retains post-launch gates, bulk pricing remains.
V.12ops/users/retention and later Desk/Atlas/Studio, real-volume ranking,V.7sources,
native/device and catalog/legal/email/checkout activation remain. Whole plan open.

Previous mail checkpoint (18 November 2026):
V.11 built-in account-mail durability/free-tier controls are deployed (18November).
Finna owns the encrypted verification/reset queue and background worker. Durable
capacity commits precede SMTP; concurrent processes share100reservations/UTCday
and a conservative3,000/rolling31days. Pending live links count at admission;
known/unknown reset requests get the same temporary-capacity response. Bounded
stable-key retries, uncertain lease recovery, closure/token rechecks and actual
worker heartbeats retain queue/privacy/history. Pauses preserve pending ciphertext;
completed account links retain their original one-use/MFA guards. No native
allowlist widening, new endpoint, frontend, dependency or unit-file changes.
1,229full backend tests,36account-focused checks,74fresh calibration/compatibility
checks (58runtime bindings/25reward diagnostics) and guarded recovery pass. A fresh
243-table dump preserves every old row;0107apply15.84ms and a fully rolled-back fake
SMTP probe pass.7API/data hashes,unchanged342built/2346served hashes,268unchanged
dependencies and8shells verify.21private learning reads +mail-capacity reads,
25reward/3edit counters0,10tier triggers,ledger46→46,reconciled economy and both
sites200. Runtime environment and public recovery availability confirm delivery
still disabled/unconfigured;0mail attempts, no SMTP contact, provider account,
sender/DNS/credential/billing/checkout activation, production fixture, bank/workshop
change or commit.0107 is applied/immutable; next0108. Receipt:
reports/finnaplan-v11-mail-20261118/README.md. Private backup:
/root/finna-v11-mail-backup-e2iq_wio. Recovery retains0107/full compatible API /
economy and every capacity/history record, pauses new mail and keeps ciphertext;
never restore older mail/review writers. Production recovery not invoked. Never
replay frozen targets. Resend is the target within the owner's free-tier preference;
actual account/verified domain/sender/private key and delivered one-use recovery
proof remain required. Setup:docs/FINNA-EMAIL-SETUP.md. Next independent V.11work:
share cards, onboarding, opt-in digest, post-launch referral gates and bulk rates;
exam taper already exists. V.12ops/users/retention and later Desk/Atlas/Studio,
real-volume ranking,V.7actual sources,native/device QA and catalog/legal/email /
checkout activation remain. This is not completion of the entire plan.

Previous curated-practice checkpoint (18November2026):
V.10 curated vocabulary practice and mixed Smart Review are deployed (18November).
Published Content Studio revisions supply reviewed English/Mizo word cards with
server-scored meaning, usage cloze and both translation directions (reverse mode
requires authored gloss choices). Current publication/Pro/block/source eligibility,
immutable feedback and typed shared Leitner dates remain. Five new cards/day is
shared with Bank vocabulary; due reviews remain available. Distinct-word progress,
retained words, decay and exact14-day finished-review mastery proof are separate
from awards. Curated cards never mint per-card XP/points or canonical attempts;
actual sourced grades feed the existing session/quest receipts and original caps.
New web format negotiation keeps old web/native queues compatible and rejects
mixed saved-set replays without the updated reader; no native allowlist widening.
1,217full backend tests,63final targeted,63source-bound calibration/compatibility
checks (53runtime bindings/25diagnostics), build/components and synthetic desktop/
320px/light/night browser QA pass.232-table dump preserves every old row;0106apply
99.489ms, rolled-back real-role probe passes.16API/data,342built/2346served hashes,
2004retained chunks,256unchanged dependencies and8shells verify.21new single-
snapshot private reads plus39independent tier checks,25reward/3edit counters0,
10tier triggers, ledger46→46, reconciled economy and bothsites200. No real cards
published, synthetic production activity, bank/workshop/provider/billing/unit/
dependency changes or commit.0106 is applied/immutable; next0107. Receipt:
reports/finnaplan-v10-curated-vocabulary-20261118/README.md. Private backup:
/root/finna-v10-curated-vocabulary-backup-_zbs4kcm. Recovery keeps0106/full compatible
CMS/shared API/economy, pauses curated writes and restores prior static; every
revision/grade/session remains. Disposable recovery passes; production recovery
not invoked. Never replay frozen targets or restore older writers over0106.
Next: V.11growth (Resend free-tier target; built-in queue, actual sender/domain/
credentials still needed), then V.12ops/users/retention and later Desk/Atlas/Studio.
Ranking needs real volume; V.7actual sources, native/device QA and catalog/legal/
email/checkout activation remain gates. This is not completion of the whole plan.

Previous word-card authoring checkpoint (18November2026):
V.10 curated vocabulary authoring is deployed (18 November). Content Studio
supports reviewed English/Mizo–English word cards, meanings, usage, glosses,
source/editorial notes, recognition choices and authored cloze prompts. Existing
immutable material revisions, exact owner review, Pro/body redaction and blocks
remain. Incomplete drafts save; submission/publication require valid distinct
choices, a single gap, bilingual gloss and actual exam/active-subject tags. Legacy
block serialization/retry shapes are unchanged. No production cards were authored
or published, no canonical content changed and no per-card award path was added.
This is authoring/reading, not curated learner practice or a words-known counter.
1,202 full backend tests,13final workflow/recovery checks plus1final recovery,
build, real-screen checklists and desktop/320px/light/night synthetic browser QA
pass. Candidate/live normalization checks preserve the1existing material revision;
9private learning reads, ledger46→46,22integrity counters0 and economy reconciled.
2API,341built/2223served hashes,1882oldchunks,266unchanged dependencies and8shells
verify; bothsites200. No SQL/provider/billing/bank/workshop/unit/dependency changes
or commit.0105 remains applied/immutable; next0106. Receipt:
reports/finnaplan-v10-vocabulary-authoring-20261118/README.md. Backup:
/root/finna-v10-vocabulary-authoring-backup-b9v_d6_p. Guarded recovery restores
prior parser/static, retains0105/current queue/economy and every authored revision;
new-format drafts require the compatible parser to edit/publish after recovery.
Disposable recovery passes; production recovery not invoked. Never replay frozen
targets or restore older queue writers over0105. No mobile endpoint widening;
new block native rendering is not certified. Next: curated scoring, current-review
eligibility, shared sessions/queue and distinct-word progress. Later V.11/V.12/
Desk/Atlas/Studio, real-volume ranking, V.7actual sources and native/device QA
remain; catalog/legal/email/checkout launch stays closed.

Previous shared-scheduler checkpoint (18 November 2026):
V.10 bank vocabulary shared scheduling is deployed (18November). Recognition,
Bank/game answers and mixed/vocabulary-only frozen Smart Review sets use one typed
canonical Leitner queue with1/3/7/16/35days,24h promotion guard, source reset and
Box5 graduation. Old question projections are retained but deduplicated. Today
limits new recognition to5/day; due reviews remain available. Queue/decks/Today/
calendar agree; loading a card creates no earning plan. Existing saved-set reward
receipts/caps remain; no new rates/awards or unique-word mastery claim.1197backend
tests,20final targeted checks,46source-bound economy evidence, build/components
and1440/320px/light/night synthetic browser QA pass. Fresh232-table clone preserves
all existing rows;0105apply15.054ms, rolled-back real-role probe passes.13API/data,
341built/2103served hashes,1762oldchunks,253unchanged dependencies and8route shells
verify.33new live private reads, ledger46→46,22integrity counters0, reconciled
economy and bothsites200. No production fixtures/bank/workshop/provider/billing/
unit/dependency changes or commit.0105 is applied/immutable; next0106. Receipt:
reports/finnaplan-v10-vocabulary-scheduler-20261118/README.md. Private backup:
/root/finna-v10-vocabulary-scheduler-backup-qcwydt2m. Recovery keeps0105/current
shared API/economy writers, pauses new recognition and restores prior static;
receipts/Bank/Smart Review/history remain. NEVER restore older queue writers over
0105. Disposable recovery passes; production recovery not invoked. Never replay
this or older frozen targets. New recognition routes remain web-only. Next:
reviewed curated/Mizo cards, usage cloze and distinct-word/session integration.
Ranking needs real volume; V.7actual sources,V.11growth,V.12ops,later Desk/Atlas/
Studio and native/device QA remain. Catalog/legal/email/checkout launch stays dark.

Previous mastery-proof checkpoint (18 November 2026):
V.10 bank vocabulary mastery proof is corrected/deployed (18 November).
The deck's Mastered display now requires an existing topic proficiency timestamp
and a finished, scored, exact server-issued Smart Review receipt touching that
deck at least14days later. A completion alone cannot supply the label; unfinished,
early, excluded, wrong-context/paper or mismatched receipts do not qualify. The
previous read used any review completion; no stored tier, award or history was
changed.24targeted vocabulary/mastery/recovery tests pass, including actual early
vs delayed and unfinished vs finished API flows. The unchanged web's1188-test
baseline/build/browser evidence remains linked; no new full-suite/browser run is
claimed for this reader-only correction. Real-mpsc candidate/live6catalog+30deck
overview checks and9+39+36independent private reads pass;3edit/22reward counters0,
ledger46→46, economy reconciled.1API helper,262unchanged dependencies, unchanged
341built/1983served static hashes and8route shells verify; both sites200. No SQL,
learner/reward/bank/workshop/provider/billing/unit/dependency changes or commit.
0104applied/immutable;0105stillfree. Receipt:
reports/finnaplan-v10-vocabulary-proof-20261118/README.md. Paired backup:
/root/finna-v10-vocabulary-proof-backup-xk1hk1ha. Recovery restores the prior
reader/static only after exact API/schema/static drift guards; no history/schema
changes. Do not replay this or older frozen targets. Next: vocabulary shared
scheduler/5words/Today, then curated/Mizo cards, cloze and session integration.

Previous vocabulary decks checkpoint (18 November 2026):
V.10 bank-derived vocabulary decks/progress are deployed (18 November).
Revise's Vocabulary view groups canonical questions by the four actual approved
active subtopics (synonyms, antonyms, idioms/phrases, one-word substitution), with
an honest Other vocabulary fallback. No inferred retagging, rewritten questions,
new content or provenance changes. Selection binds new/resumed cards and overview
to the chosen deck; an empty deck never silently serves another. Progress uses
latest verified-key canonical outcomes and shared mastery thresholds/45-day decay;
repeat drills do not inflate counts and recent excluded assessments do not erase
decay. Recognition is explicitly not a unique-words-mastered claim. Private reads
exclude active mock/game/Cup items; account expiry/change and stale deck responses
are cleared. Existing answer receipts, source links and the recognition scheduler
remain; full scheduler unification,5words/Today,curated/Mizo cards and cloze are
still pending.1188full backend tests plus14final targeted checks, four frontend
scripts, build and desktop/320px/light/night new-panel QA pass. Synthetic local
empty-deck, scoring and reload receipts verified; preview DBs/processes removed.
Real-mpsc read-only candidate/live6catalog+30deck-overview checks pass, plus
9tracker and39+36independent private checks. All3edit/22reward counters0; ledger
46→46, economy reconciled.2API artifacts,341built/1983served hashes,1642oldchunks,
261unchanged dependencies and8route shells verify; both sites200. No SQL,
migration, bank/workshop, learner/reward/provider/billing/unit/dependency changes
or commit. API restarted for the bounded pair.0104remains applied/immutable;
0105remains free. Receipt:reports/finnaplan-v10-vocabulary-20261118/README.md.
Paired backup:/root/finna-v10-vocabulary-backup-23qlbm10. Drift-guarded recovery
restores prior router/static and removes the new helper, retaining every schema,
learner/review/tier/economy artifact. Never replay this or older frozen targets.
New vocab routes remain web-only. Next: bank vocabulary shared scheduler, then
curated decks/modes/session integration. Ranking still needs actual volume;
V.7actual sources,V.11growth,V.12ops,later Desk/Atlas/Studio and signed native/device
QA remain. Catalog/legal/email-recovery/paid-checkout launch stays closed.

Previous checklist checkpoint (18 November 2026):
V.10 pre-submission checklists are deployed (18 November). Question proposals,
Content Studio materials, learning collections and timed tests now ask authors to
check sources, sharing rights and format/body size before review starts. The
transient confirmations bind to the current draft/account, clear permanently on
edit/revert and never restore an earlier account's proof. Materials/collections
require the current draft saved first; owner test publication retains its existing
preview confirmation. These are client readiness checks, not persisted legal
attestations or new API enforcement; authoritative source/format/ownership/review
rules remain unchanged. All four real screens pass component checks; 12 frontend
regression scripts,18targeted backend checks, existing1182-test unchanged-API
baseline, build, disposable recovery and desktop/320px/light/night browser QA
pass. Synthetic local material reached Submitted in the existing queue; it was
never reviewed/published and its disposable DB was removed.341built/1863served
hashes,1522retained chunks,262unchanged API/schema/data dependencies and24route
shells verify.6+3tracker and39+36independent private read checks pass;3edit and
22reward counters0, ledger46→46, economy reconciled, both sites200. Static only:
no API/SQL/unit/workshop/learner/reward/provider/billing/dependency changes or
commit.0104 remains applied/immutable;0105 remains free. Receipt:
reports/finnaplan-v10-checklists-20261118/README.md. Private static backup:
/root/finna-v10-checklists-backup-dtsxjt2x. Recovery restores prior static only and
refuses API/schema or newer-static drift. Never replay this or older frozen
installers. Next: vocabulary decks/scheduler unification. Ranking waits for actual
volume. V.7needs actual new-exam sources; V.8 remains the permanent never-list;
V.11growth,V.12ops,later Desk/Atlas/Studio and signed native/device QA remain.
Catalog/legal/email-recovery/paid-checkout launch stays closed.

Previous submission tracker checkpoint (18 November 2026):
V.10's read-only submission tracker and current-access Create panel are deployed
(18 November). /create composes own questions/corrections, materials and learning
collections/mock tests from existing lifecycle tables: actual states, revision-bound
latest return notes, original draft links, dated queue positions and real30-day
median decision times (honest empty history, no SLA/progress fiction). Collection
links select the same existing draft. No new status store or review/award path.
Titles/notes are redacted until linked-question attempt/reveal/valid exceptional
disclosure, with active mock/game/Cup guards taking precedence. Reviewer block pairs
hide notes; queue/time aggregates exclude blocked accounts. Current caps/moderation
and invitation-only Mentor eligibility are explicit; no roles auto-granted.
1182full backend tests, six final targeted boundary/recovery tests, ten component /
navigation scripts, build and desktop/320px/light/night browser QA pass. Candidate
reads ran as mpsc in read-only transactions before deployment; six live tracker
reads plus three private handler checks verify40owned rows. Independent39+36private
checks pass;3edit/22reward counters0, ledger46→46, economy reconciled and both sites200.
Two API readers,340built/1743served hashes,1403retained chunks,260unchanged API/schema /
data dependencies and8route shells verify. No SQL/migration, learner writes,
synthetic production activity, currency/rate/provider/billing/bank/workshop/unit /
dependency change or commit.0104 remains applied/immutable,0105 remains free.
Receipt:reports/finnaplan-v10-submissions-20261118/README.md. Paired private API/static
backup:/root/finna-v10-submissions-backup-02i4ys3u. Drift-guarded recovery stops API,
restores prior router/static and removes the new helper; all tier capture, schema,
economy evidence, privacy guards and learner/review history remain. Disposable
recovery passes; production recovery was not invoked. Do not replay this or older
frozen installers. Next: §II.7.2 pre-submission source/rights/body-limit checklist,
then vocabulary decks/scheduler unification. Ranking still needs actual volume.
V.7 is pending actual new-exam-body sources (no invented registry/papers); V.8 is
the permanent never-list, not an incomplete feature. V.11growth, V.12ops/admin /
retention, later Desk/Atlas/Studio, signed native/device QA and catalog/legal/email /
checkout launch remain open. The new tracker route is explicitly web-only.

Previous contributor-standing checkpoint (18 November 2026):
V.10 contributor tiers, profile reputation and the dated weekly Guide strip are
now deployed (18 November). Current weighted votes still compute privileges;
only the highest earned display label is recorded in immutable creator_events.
Regular+ post flair and consented public-profile links appear on question/note /
share/reply authors. Public raw Helpful/accepted counts retain parent/reference,
block, disclosure and mock/game/Cup guards. Guides require current eligibility,
visible weekly Helpful activity, public creator consent and weekly-board opt-in;
moderation overrides privileges, and Mentor eligibility never grants a role.
1175backend tests, nine component/nav scripts, build and1440/320px/light/night UI
checks pass. Fresh232-table dump rehearsal preserves every existing row;0104apply
8.815ms, zero initial labels. Nine API/data artifacts,340built/1623served hashes,
1283oldchunks and251unchanged dependencies verify.39+36private read-only checks,
3zero edit/22zero reward counters, valid audit guards, ledger46→46, reconciled
economy and both sites200.0104 is now applied/immutable; nextfree0105. Receipt:
reports/finnaplan-v10-tiers-20261117/README.md. Private paired backup:
/root/finna-v10-tiers-backup-yslok8te. Recovery pauses all10tier capture triggers
before restoring prior API, matching prior economy evidence and static; it retains
0104/every earned label and all existing privacy/history guards. If pause fails,
keep/restart the complete candidate API (including games lock ordering and matching
evidence); do not install the old multi-player writer with capture active. Never
replay this or older frozen targets over newer releases. Multi-user attempt writers
must acquire every affected reward lock in sorted user order before tier capture;
normal aa_habit_attempt_lock precedes tier capture. No synthetic production activity,
learner-content/economy writes, bank/workshop/provider/billing/unit/dependency change,
award backfill or commit. Catalog/legal/email-recovery/paid-checkout launch remain
closed. Next: submissions/checklists/tier-aware Create, then vocabulary decks /
scheduler unification. Ranking needs real volume; V.11growth, V.12admin/maintenance
and later Desk/Atlas/Studio remain. V.7needs actual exam sources; signed native /
physical-device certification remains open. New standing/Guide endpoints stay
web-only; additive legacy author metadata is not native renderer certification.


For the learning/points/community/admin build (the "Finnaplan" work), the
design authority is `docs/FINNAPLAN.md` — owner-decided 15–16 November
2026, zero open questions. Implement in its Part V order (continue V.10;
V.0 gates apply to every phase; V.8 is the never-list). Migration
numbering starts at the actual next free number (0090+ at time of
writing). §5.5 (admin grants, 0089) is already deployed — do not
re-implement it. V.1 browse performance, anonymous catalog transport and
§0.9.2 combined-filter metering are deployed (17 November; migrations
0090–0091). See `reports/finnaplan-v1-20261117/README.md`. V.2 is now deployed (17 November): mastery/review, progress rollups, Today,
focus, calendar read layers, web screens, login backoff and the missing Daily Five
connection. Migrations0083 and0092 are applied and immutable; do not edit them or
rerun frozen installers over newer releases. V.3 habit is also deployed (17 November): one account streak, fixed daily plans,
new Review/Plan quest rings and bounded timed review-session awards. Migration0093
is applied and immutable. V.4 economy is deployed too (17 November):
0094–0096 are applied and immutable; next free is0097 for V.5. The seeded week
reconciles to60-day heavy /≈90-day average Pro-month earning.1035backend tests,
221-table full-dump preservation, SQL policy/catalog + paired-file rollback,
20private read-only route checks and all12API/335static hashes pass. Live reward
integrity checks are all0; ledger46→46, no award backfill. See
`reports/finnaplan-v4-20261117/README.md` and its frozen release receipt.
Keep catalog activation dark: economy reconciliation now checks exact release
artifacts + live diagnostics, but actual checkout remains disabled and legal
pages have not shipped. Do not rerun frozen V.1–V.4 installers over newer releases.
V.5 boards/recap are now a local checkpoint (not deployed):1044backend tests,
web build, desktop/320px UI and real-mpsc read-only Oracle query rehearsal pass.
See `reports/finnaplan-v5-boards-20261117/README.md`. Calendar/ICS now has its own local checkpoint:1052backend tests, web build,
phone/desktop UI and fresh229-table dump preservation pass. See
`reports/finnaplan-v5-calendar-20261117/README.md`. Draft0097 now contains the
private entry/feed tables, now extended locally for profile identity/bio and shop
rules. It is not applied in production. Profile/shop now have a local checkpoint:
1060backend tests, build, phone UI and final229-table dump preservation pass;
ledger46→46. See `reports/finnaplan-v5-profile-20261117/README.md`. Current26avatar
items stay intact;3points-only cosmetics added, with atomic own-once spending,
versioned handle cooldown, moderated bio reads and3owner spend integrity counters.
Two more local batches now cover legacy board/catalog transport and week/Cup/Desk/
Today target integration:1065backend tests, web build, desktop/320px QA and fresh
229-table preservation pass; ledger46→46. See
`reports/finnaplan-v5-integration-20261117/README.md`. Old avatar readers keep the
26 numeric-level items; new web reads/saves opt into catalog_version=2. Old clients
cannot replace newer saved looks; unsupported board selectors retire honestly.
Desk has no scheduled-event store yet: only actual Cup/owned/official reads compose;
new Desk scheduling stays with its later upgrade. Today taper preserves started
plans and every due review. Account self-service is now also implemented locally:
Profile's four groups, owned read-only snapshot export, sign out everywhere and
versioned/recent-auth/MFA-gated account closure with anonymous immutable history
and durable entitlement/credential guards.1073backend tests, build, desktop/320px
QA and229-table clone preservation pass; ledger46→46. See
`reports/finnaplan-v5-account-20261117/README.md`. Draft0097 is extended again and
still unapplied at that historical checkpoint. V.5 is now deployed through the
bounded finnaplan-v5 target:1081 backend tests, fresh229-table preservation,
36private real-mpsc read checks,28API/337static hash readbacks and all22integrity
checks0 pass; ledger46→46.0097 is now applied and immutable; next free0098.
See reports/finnaplan-v5-recovery-20261117/README.md. Fresh calibration binds39
runtime sources and includes cosmetic integrity in the actual launch gate.
Private recovery data is /root/finna-v5-backup-olyz_k9b, including prior and
released artifacts. Recovery keeps the current privacy readers/catalog/SQL
tombstones, pauses new V.5 writes and restores prior static. Never restore old
validators/bio readers or replay the frozen V.1–V.5 installers over newer code.
No commit or blanket dirty-checkout API deployment was made. Catalog activation
and checkout remain dark. Native physical-device renderer certification remains
open; safe legacy transport does not certify visual parity. V.6 review/focus API
widening is now deployed: 1085 backend tests, 33 companion checks, 231-table
preservation, 36 private real-mpsc reads and all 22 integrity checks 0;
ledger 46→46. 0098 is applied/immutable; next free 0099. Six API artifacts
changed; all 337 web artifacts remain identical. 41 runtime sources bind the
fresh economy proof. Native Smart Review/focus, durable retries and account-change
guards pass 29 domain and 60 component tests, lint/typecheck and Android/iOS/web
export. No signed binary/OTA or physical-device QA is claimed: EXPO_PROJECT_ID
is missing and no Android device is attached. Receipt:
reports/finnaplan-v6-20261117/README.md. Paired backup:
/root/finna-v6-backup-twlrhihp. V.6 recovery restores V.5 API/static while retaining
0098's view grant and every V.5 privacy/catalog/tombstone guard. Never replay the
frozen V.6 installer or older releases over newer code. Continue V.9's website
layout/navigation consolidation; V.7 requires actual onboarding sources and
V.8 is the standing never-list. Community mobile widening waits for Part II.
V.9 website consolidation is now deployed: Revise owns queue/mistakes/vocabulary/
print; Desk is saved questions/notes/focus; Chronicle owns the retired date views;
Play has all seven available entries; Quick find and Inbox own search/notifications.
Six frontend scripts pass, including 10 actual-router redirects and 111 resolving
navigation links, stale-account guards and date filters. Desktop/dark/320px browser
checks pass against a disposable fixture. The bounded static release verifies 336
built/453 served artifacts, retaining 117 prior chunks for open tabs. All 153 V.6
API/migration dependencies remain exact; 36 private read-only mpsc reads pass and
all 22 integrity counters are 0. Both sites healthy; no API/SQL/service changes.
Receipt: reports/finnaplan-v9-20261117/README.md. Private static backup:
/root/finna-v9-backup-075wq8ox. Do not replay any frozen installer over this newer
inventory. Vocabulary still uses its existing server engine; Part II scheduler
unification belongs to V.10. Printing is limited to loaded questions; actual PDF/
printer output is not certified. Continue V.10 in its Part II rollout order.
V.10 first bounded slice is now deployed: chronological Following question
threads reuse creator_follows consent/blocks; followed materials remain available.
Duplicate-doubt deflection refreshes existing discussions, opens replies inline
and retains the draft. Stale account/privacy snapshots are discarded. 1091 full
backend tests plus targeted boundary/recovery tests pass; build and desktop/320px
UI pass. One API reader changed,249API/schema files exact;336built/568served hashes,
16community +36private read-only checks and22zero integrity counters pass. Both
sites200; ledger46→46. Receipt:reports/finnaplan-v10-following-20261117/README.md.
Private paired backup:/root/finna-v10-following-backup-olmh87jd. NoSQL/migration or
workshop change;0099 remains free. Do not replay frozen installers. V.10 is still
partial: study/material posts, guards/tiers, remaining composer/content pipeline
and vocabulary scheduler unification remain. Ranking waits for real volume.
Legacy mobile question-discussion writes already existed and remain; no new route
or capability was added. New V.10 study/material mutations must stay web-only.
V.10 study-note slice is now deployed: notes/optional internal reference,
moderation/report/Helpful/withdraw, shared IST-day5posts/30replies (Regular10/60),
Helper maturity lift, computed vote weights and web-only new note routes. Mixed
feeds opt into content_version=2; original clients keep question-only items. Old
native question writes remain, but native v2 feeds/new note paths are denied.
Linked question disclosure/assessment and referenced publication/block gates hold.
1106 tests/build/component regressions and desktop320px/new-panel night QA pass.
Fresh clone preserves231tables;0099 now applied/immutable, nextfree0100. Seven API
files,337built/684served hashes,246unchanged dependencies,21+36private read checks,
22zero integrity counters and both-site health pass; ledger46→46. Receipt:
reports/finnaplan-v10-study-20261117/README.md. Paired backup:
/root/finna-v10-study-backup-19b2t23i. Recovery retains0099/all history; do not replay
frozen installers. No workshop/currency/billing/provider change. V.10 is still
partial: material shares, note replies/block shortcuts, remaining composer,
monotonic public tier/flair/profile/Guide UI, submissions/checklists and fuller
Create hub, vocabulary decks/scheduler and later Desk work remain. Status tiers
are current computed privileges, not finished public tier-display history.
Ranking waits for actual volume. Existing discovery-panel night contrast remains
outside the new-note-panel check; signed native/device QA remains outstanding.
V.10 reviewed material shares are now deployed (17 November): immutable
material anchors, current published-revision title/format/access cards, shared
maturity/limits/moderation/Helpful/report/withdraw and explicit native isolation.
Protected bodies and unreviewed edits stay out of share responses; publication
and both post/material author block pairs are rechecked. Moderator queues show
reviewed references and approval rechecks availability.1113tests/build/component
and desktop/320px/new-panel night checks pass. Fresh clone preserves231tables;
0100 applied/immutable, next0101. Six API files,337built/800served hashes and248
unchanged dependencies verify;463priorchunks retained.21+36private reads,
22zero integrity counters, ledger46→46 and both-site health pass. Economy
reconciles; catalog/checkout dark. Receipt:reports/finnaplan-v10-materials-20261117/README.md.
Private backup:/root/finna-v10-materials-backup-uiukv5l9. Recovery retains0100,
all history and the new native isolation guard; never replay frozen installers.
Remaining V.10 includes note replies/block shortcuts, remaining composer,
public tier/profile/Guide, submissions/checklists/full Create hub, vocabulary
scheduler/decks and later Desk work. Ranking still waits for real volume.
V.10 note/material reply conversations are now deployed (17 November):
on-demand chronological replies, shared30/60 IST-day limits, moderation,
Helpful/report/withdraw and parent/reference visibility guards. New accounts may
reply; parent/child author blocks, linked publication/disclosure/active assessment
checks hold. No nested replies, currency or community reply notifications added.
1121tests/build/components and desktop/320px/night QA pass. Fresh231-table clone
preserves all history;0101 applied/immutable, next0102. Three API files,
337built/916served hashes,252unchanged dependencies and579priorchunks verify.
24+36private mpsc reads,22zero integrity counters, ledger46→46 and both sites200;
economy reconciled, catalog/checkout dark. Receipt:
reports/finnaplan-v10-replies-20261117/README.md. Private paired backup:
/root/finna-v10-replies-backup-bo2iz0ht. Recovery restores prior router/static while
retaining0101/all history and parent/reference privacy readers; do not replay
frozen installers. Block shortcuts, remaining composer, public tier/profile/Guide,
submissions/checklists/full Create hub, vocabulary scheduler/decks and later Desk
work remain. Ranking waits for real volume; signed native/device QA stays open.
V.10 note/share/reply formatting and device drafts are now deployed
(17 November). Safe React bold/list/code readers and preview; private account +
composer/parent draft isolation, reload/uncertain-write retry continuity,
discard/success cleanup and global sign-out/expiry/cross-tab purge. Drafts contain
own input only, expire7days and cap32records; blocked storage stays in memory with
an honest notice.1122backend tests, renderer/hook/real-component regressions,
10redirects/111links, local build and1440/320px/night UI pass. Static-only release
verifies337built/1033served hashes,696oldchunks and256unchanged API/schema/data
files;15route shells and both sites200.24+36private read checks,22zero integrity
counters, ledger46→46 and economy reconciled; catalog/checkout dark. No API/SQL/
service changes;0101 remains applied/immutable and0102 free. Receipt:
reports/finnaplan-v10-composer-20261117/README.md. Private static backup:
/root/finna-v10-composer-backup-sn_jdlkz. Guarded recovery restores prior static
without history changes; never replay frozen installers. Canonical question
composer formatting/autosave, honest edits/accepted locks/nudges, block shortcuts,
public tier/profile/Guide, submissions/full Create, vocabulary scheduler/decks
and later Desk remain. Ranking waits for volume; V.7 requires actual exam sources.
V.10 canonical question composer formatting and device drafts are now deployed
(17 November): safe thread/feed/accepted-text rendering, preview, restored post type
and five source pairs, account/question/parent/paper-context isolation and durable
retry keys. Fresh duplicate deflection, citation actions and immutable accepted
replies stay intact; expiry discards private views. Shared theme colors fix input /
accepted-card night contrast.1122 full backend tests plus1 new recovery test,
components/build,10redirects/111links and1440/320px/night browser checks pass.
Static-only release verifies339built/1152served hashes,813oldchunks,256unchanged
API/schema/data and18route shells; both sites200.24+36private read checks,
22zero integrity counters, ledger46→46, economy reconciled and launch dark.
No API/SQL/service change;0101immutable,0102free. Receipt:
reports/finnaplan-v10-discussion-composer-20261117/README.md. Private backup:
/root/finna-v10-discussion-composer-backup-z21hdaln. Guarded static recovery passes
in disposable files; production recovery not invoked. Never replay frozen targets.
Continue §7.1.5 edits with visible history and accepted-reply locks integrated into
that workflow, then once-only acceptance nudges; existing accepted content stays
immutable. Block shortcuts, public tiers/profile/Guide, submissions/full Create,
vocabulary scheduler/decks and later Desk remain. Ranking needs real volume;
V.7 requires actual onboarding sources. Signed native/device QA remains open.
V.10 honest edits are now deployed (17 November): own doubt/explanation/reply,
study/share/reply edits with immutable original/revision snapshots, visible edited
markers and private paginated history. Every edit uses the shared daily budget and
returns to author-only moderation; exact-version decisions and undo guards prevent
stale approval. Accepted-once replies permanently lock, including after unaccept;
SQL/edit/accept races and existing citation/reference/privacy gates hold. Web-only
new edit/history routes, saved edit drafts/retry keys and community refresh pass.
1136backend tests, components/build,10redirects/111links and1440/320px/night browser
checks pass. Fresh clone preserves231tables,0102apply22.486ms;0102now applied /
immutable, next0103. Seven API files,338built/1269served hashes,931oldchunks and
250unchanged dependencies verify.27+36private read checks,3zero edit +22zero reward
integrity counters, ledger46→46, economy reconciled and both sites200. Receipt:
reports/finnaplan-v10-edits-20261117/README.md. Private paired backup:
/root/finna-v10-edits-backup-u8o2ye8s. Recovery pauses edit-function EXECUTE and retains
current revision/moderation/privacy guards,0102and all history; prior static only.
Do not replay frozen targets. No workshop/bank/provider/billing/Caddy/unit/dependency
change, synthetic production activity, award backfill or commit. Next §7.1.6:
once-only acceptance nudge. Block shortcuts, public tiers/profile/Guide,
submissions/full Create, vocabulary scheduler/decks and later Desk remain. Ranking
needs real volume; V.7 requires actual sources. Native/device certification open.
V.10 once-only acceptance reminders are now deployed (17 November): the doubt
asker's open, published conversation can show “Did one of these solve it?” once.
Only another visible author's published reply qualifies; previously solved doubts,
blocks, pending/withdrawn/before-fix content, disclosure/assessment locks and sanctions
suppress it. A private web-only POST claims an append-only event under the same
parent lock as acceptance; a unique index makes concurrent/device claims once-only.
GET reads never consume prompts. Dismissal/reload does not repeat; uncertain network
responses may omit this optional prompt, never retry into a nag. No automatic
acceptance, Inbox/email notification, posting-budget slot or award is added.
1149backend tests, real components/build,10redirects/111links and1440/320px/night
browser checks pass. Fresh clone preserves232tables,0103apply5.316ms;0103now applied /
immutable, next0104. One API file,338built/1386served hashes,1048oldchunks and257unchanged
dependencies verify.30+36private read checks, valid nudge index/0invalid events,
3zero edit +22zero reward counters, ledger46→46, economy reconciled and both sites200.
Receipt:reports/finnaplan-v10-nudge-20261117/README.md. Private paired backup:
/root/finna-v10-nudge-backup-03bn068o. Recovery restores only the prior router/static while retaining
0103/all prompt and learner history, plus every existing edit/privacy guard. Drift
recovery tests pass in disposable files; production recovery was not invoked.
Do not replay this or any older frozen target over newer releases. No workshop/bank/
provider/billing/Caddy/unit/dependency change, synthetic production activity, award
backfill or commit. Next: block shortcuts, then public tiers/profile/Guide,
submissions/checklists/full Create, vocabulary scheduler/decks; ranking needs real
volume. Later V.11growth,V.12admin/maintenance and Desk/Atlas/Studio remain; V.7needs
actual exam sources, signed native/device QA and catalog/legal/checkout launch open.
V.10 block shortcuts are now deployed (17 November): question posts/replies,
study notes, material shares and their replies expose a direct Block this author
control, separate from reporting. It reuses the existing account block for private
and public-profile authors; own/guest controls are absent. Success and uncertain
responses clear/refetch all mounted community snapshots, discard late pagination /
account outcomes and retain feedback plus a Blocked users/unblock link. Reply and
feed readers now also clear on auth expiry/community changes. Existing server
visibility, graph/follow/block, disclosure/assessment and moderation guards remain.
1154full backend tests, eight real component/navigation checks (10actual redirects /
111links), build and1440/320px/light/night browser QA pass. Static-only bounded
release verifies339built/1504served hashes,1165retained oldchunks,259unchanged API /
schema/data dependencies and20route shells.30+36private read checks,3zero edit /
22zero reward counters, valid nudge index/0invalid events, ledger46→46, economy
reconciled and both sites200. No API/SQL/migration/service/workshop/bank/provider /
billing/dependency change, production learner writes, award backfill or commit.
Receipt:reports/finnaplan-v10-blocks-20261117/README.md. Private static backup:
/root/finna-v10-blocks-backup-2zb4mj4f. Guarded static recovery preserves all API/learner/block
history and refuses drift; disposable recovery test passes.0103 remains applied /
immutable; nextfree0104. Do not replay this or older frozen installers over newer
releases. Next: public monotonic tiers/profile/Guide; submissions/checklists/full
Create; vocabulary scheduler/decks. Ranking needs real volume. V.11growth,
V.12admin/maintenance and later Desk/Atlas/Studio remain; V.7actual sources,
signed native/device QA and catalog/legal/paid-checkout launch remain open.
Monday recap
belongs to V.5; consolidation/vocabulary remain V.9/V.10. Later phases pending.
For question review or solving, follow `docs/QUESTION-REVIEW-RULES.md`.
Use `docs/BANK-COMPLETION-PROMPT.md` for reusable whole-bank continuation,
including source-checked current-affairs updates alongside historical answers.
For question tagging, classification, extraction labels or bank repairs, read
`docs/QUESTION-TAGGING-RULES.md` first and use
`docs/QUESTION-TAGGING-MODEL-PROMPT.md` for candidate work.

That policy replaces conflicting older tagging instructions. Historical reports
and archived handoffs are evidence, not authority to rerun old merges. Use fresh
Oracle sources and active registry IDs. Preserve uncertain items for clarification.
The local bank is a recovery snapshot; publication follows the guarded Oracle
workflow in `CLAUDE.md`. Never invent inspections or human sign-offs.

Before preparing a tagging packet, run `python3 scripts/audit-review-coverage.py
--output /tmp/study-review-coverage.json` and exclude already reviewed target IDs.
Use one primary booklet per established paper; see section 9 of the tagging policy.

For simultaneous tagging work across Codex, Antigravity, OpenCode or other tools,
use `scripts/tagging-work.py` and the single reusable entry prompt in
`docs/TAGGING-WORKER-PROMPT.md`. Read `docs/TAGGING-COORDINATION.md`. Claim exact
targets centrally before working, resume existing sessions and save drafts there.
Do not create a local coordination queue, choose unreserved targets, overwrite
another worker's packet or commit unrelated shared-checkout changes. Submitted
queue results remain pending candidates, not published/approved corrections.

The reconciled Batch 1632 publication is complete. Read
`reports/owner-taxonomy-final-20261108/README.md` and the latest source-bound
Oracle outcomes before continuing. Current accepted tagging outcomes: 77,791;
258 blocked; 4,334 without a saved review in this pass. Never restart the completed
frozen runs or combine historical pending files into a new publication. This owner
authorization does not extend to unseen future batches.

The owner authorized acceptance/publication of the earlier frozen saved AI tagging pass
on 8 November 2026. Read `reports/owner-taxonomy-publication-20261108/README.md`
and its exact completion ledger before continuing that work. Original candidate
files remain historical pending inputs; they do not describe current publication
state. This bounded owner delegation is not an independent human review, answer
verification, or authorization to publish future model batches automatically.

For learner answer wording, follow `docs/PUBLIC-ANSWER-LANGUAGE.md`. Keep routine
AI/model processing labels in admin/audit history, use shared public answer labels,
and never turn unreviewed suggestions or tagging acceptance into verified answers.

For new exam guides and branches, follow `tools/mes-build/README.md`: check official
syllabus/format changes, retain separate scheme versions and source evidence, and
scope progress by exam + scheme + branch. Reuse the existing immutable admin scheme
and paper-readiness workflow for scoring. A frontend guide is not a published scheme
revision, and year-based paper grouping must remain visibly inferred.
