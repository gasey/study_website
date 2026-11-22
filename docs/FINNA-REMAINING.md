# Finna remaining work

**Scoped release package — 21 November (night):** `scripts/build-scoped-release-manifest.py`
and [FINNA-SCOPED-RELEASE-RUNBOOK.md](FINNA-SCOPED-RELEASE-RUNBOOK.md) split the
dirty checkout into **Bundle A** (18 migrations `0116/0117/0119/0120/0121` +
`0122–0134`, 99 manifest-bound files including paired `bank-review-worker.py` and
restore/replay operators; excluding immutable `0110`, Desk v4 `0111–0115`, Atlas
seed `0118`, and all one-shot scripts) and **Bundle B** (`0111–0115`, `0118`,
gated after an actual healthy week). All 9 launch/cleanup flags are verified
default-off, Bundle A's standalone migration chain passes on isolated PostgreSQL
without Bundle B (`test_scoped_release_manifest.py`: 2/2), and local `web/`
production build passes (`tsc -b && vite build`, 13.58s). `rollout_authorized`
stays `false` and production is untouched.
[Runbook](FINNA-SCOPED-RELEASE-RUNBOOK.md) ·
[Receipt](../reports/finna-scoped-release-package-20261121/README.md).


**Latest local follow-up — 21 November (night):** migration **0134** stages
separately gated private-preference cleanup (`user_calendar_preferences`,
`inbox_preferences`, `inbox_desk_reads`, `game_preferences`; `creator_blocks`
preserved for safety), append-only `account_audience_events`, and owner-only
audited 18+ age-declaration correction (`POST /api/account-privacy/admin/audience-correction`,
requiring an `in_review` `correction` request, recent owner auth/CSRF/MFA, exact
version, and forbidding automatic grandfathering of unknown accounts). New
`scripts/replay-restore-erasure-decisions.py` exports a zero-PII SHA-256
closure/hold/erasure ledger, verifies candidate drift read-only, and replays
holds/closures/real sweepers onto an isolated quarantined candidate without
forging purge markers or authorizing promotion. **170 isolated-PostgreSQL tests
pass** across 10 focused suites (24 new cases). All three cleanup flags and
audience/launch flags remain off; production is untouched.
[Procedure](FINNA-PREFERENCES-RETENTION-AND-REPLAY.md) ·
[Receipt](../reports/finna-preferences-retention-replay-20261121/README.md).


**Earlier local follow-up — 21 November:** private essay drafts, individual
question/material bookmarks and saved calendar links now have a separately gated
cleanup implementation in migration **0133**. It reuses the 30-day closure window
and restricted holds, waits for base study cleanup, and records its own completion
marker. Stale closed-account writes cannot recreate these private records. Both
cleanup flags remain off, and 0133 is unapplied in production.

**246 selected tests pass**, including 41 new cases. The migration rehearsal on a
separate restored copy preserves all original rows and sequence counters; synthetic
cleanup/retry/hold checks and all seven supplemental restore comparisons pass.
The three temporary copies are removed; the private cluster is stopped. Prior
migrations and frozen receipts are preserved, with exact code/document preimages
for the two intentionally changed runtime files.

Next remaining work: other preferences and shared/public/support/moderation,
provider/log/backup retention and holds; final currentness and authoritative
erasure-decision replay; a separate recovery location/SSH-identity backup; full
service/provider configuration, actual mail/payment and physical Android
acceptance, and scoped production rollout. Human/content/healthy-week/volume
gates remain for the wider plan. No new key copy, public policy, deployment,
provider action or phone connection occurred in this follow-up.
[Private-study procedure](FINNA-PRIVATE-STUDY-RETENTION.md) ·
[Receipt](../reports/finna-private-study-retention-20261121/README.md).


**21 November follow-up:** the selected deletion/hold checks and encrypted
original-key backup/restore rehearsal now pass. The new read-only retention
preflight compares closure/purge markers, protected holds and reopen envelopes;
both saved-snapshot candidates match. All four hold codes, release/expiry,
30-day grace, permissions and idempotent cleanup are tested. The source preview
and all test-clone table values/schema/sequence counters are preserved. The
focused suite passes **108 tests**, including **34 new cases**.

The original production key now has an encrypted backup on this computer, verified
by a fresh-process restore and decryption of the saved pending-MFA record. Keep
`~/.ssh/id_ed25519`: that private identity is required to decrypt the archive.
A second recovery location and a separate backup of that identity remain unverified.
No plaintext key is saved in the repository, chat or report. Production settings,
cleanup flags and services remain unchanged.

Still open: the retention/hold treatment of unselected private drafts/bookmarks,
shared/external/log/backup locations; final currentness and erasure-decision replay;
full service/provider configuration and scoped rollout; actual mail/payment,
physical Android and later content/human/healthy-week/volume acceptance.
[Procedure](FINNA-DELETION-KEY-RECOVERY.md) ·
[Checks and evidence](../reports/finna-deletion-key-recovery-20261121/README.md).


The local snapshot-recovery rehearsal is complete in a third isolated copy:
all 9,489 accounts match, all 21 privacy and 8 billing comparisons pass, and copied
credentials are quarantined. Both evidence databases remain unchanged. The older
workshop bank mismatch was resolved with a read-only matching-generation/source
capture; 141,461 unique files and the checked database source references verify.
This is the saved 09:15–09:17 UTC database snapshot, not a final production cutoff.
[Completed local receipt](../reports/finna-full-copy-recovery-20261121/README.md).

The owner supplied **A/77, Chanmari, Aizawl, Mizoram, India** for invoices and
contact/policy pages. Private drafts and local About/Contact/Privacy previews now
include it; web typecheck/build pass. Invoice/tax review, policy publication,
real mail/payment acceptance, physical Android, scoped production rollout and
the later content/human/healthy-week/volume gates remain. iOS stays deferred.


Owner update, 20 November: **Finna is for people aged 18 or over.** The earlier
under-18/guardian enrollment plan is superseded. Current launch scope is in the
[adult-only plan](FINNA-ADULT-ONLY-PLAN.md).

Updated 21 November 2026. The current Android beta is ready for owner installation.
The complete Finna launch remains open. This page consolidates the current state;
earlier checkpoint wording is preserved in the linked frozen reports.

Earlier diagnosis of the original older candidate: all 8,811 shared accounts match in every
stored field; the newer reference has 678 additional open accounts without email,
each with a guest credential. No accounts exist only in the older candidate and no
shared account changed. The focused regression passes 60 tests, with 16 new
diagnosis scenarios. All 174 direct account references in the staged clones were reviewed, including
a separate count of the protected hold table; no other linked rows for the additions
were found. Indirect/external references and final currentness remain outside this
diagnosis. No repair was performed. The [repair plan](FINNA-RESTORE-REPAIR-PLAN.md)
prefers a complete current paired restore and defines a third-copy additive-preview
fallback. [Diagnosis receipt](../reports/finna-restore-account-diagnosis-20261121/README.md).

The earlier local follow-up adds an independent read-only billing/access restore
comparison. Seven billing/grant projections match in the retained clones, but
users' stored access inputs differ, so both billing and privacy comparisons remain
blocked. The 32 new scenarios and selected existing billing/privacy checks pass
129 tests. No records were repaired and no production/provider action occurred;
the private cluster is stopped. A current reference after writer cutoff and a
reviewed repair plan are still required. [Receipt](../reports/finna-restore-billing-preflight-20261121/README.md).

The staging DNS follow-up now passes from the workspace: `finna-staging.hawayu.in`
resolves to the expected host, HTTPS validates, the staging banner is present, and
the unauthenticated API health result reports 1,000 synthetic/scorable questions.
The Let's Encrypt certificate currently expires 17 February 2027. This confirms
endpoint reachability only. Android emulator browser loading was inconclusive
because System UI and launcher became unresponsive; authenticated native, provider
and physical-device acceptance remain separate. [Receipt](../reports/finna-staging-https-check-20261121/README.md).

20 November follow-up: the native question card already highlights a choice
immediately and says “Waiting for answer confirmation…” while the authoritative
request is pending. Its saved-choice write still happens before sending to preserve
safe retry; the server result is applied before the post-answer receipt write.
Both native answer paths now return `Server-Timing` on isolated staging. A
synthetic API run measured 116.6 ms server / 136.77 ms round trip for a direct
question answer and 113.6 ms / 130.49 ms for saved practice; one receipt replay
took 1.5 ms server / 19.99 ms round trip. These are single API-host samples,
not phone latency. A signed staging preview then completed one real answer on the
dedicated Android emulator: tap-to-response 198 ms, including a 15 ms durable
receipt write and 183 ms API round trip; the answer handler took 92.7 ms. The
wrong-answer filter reduced the synthetic UDC set from 1,000 to 3 questions and
showed the answered sample. This is one emulator sample, not physical-device or
carrier-network certification. Physical TalkBack focus/speech, broader hardware
and network sampling remain. The QA account was signed out; no phone is connected
and the emulator is stopped with its data retained. [Timing receipt](../reports/finna-answer-timing-20261120/README.md).

## Completed and available

- Standalone signed Android beta **6d2bc67d** runs without a connected phone or
  development server. [Installation guide](FINNA-ANDROID-BETA.md).
- Answer-choice highlighting and authoritative practice feedback avoid the former
  extra GET. Exam/module, subject/topic/subtopic and scoped-paper browsing are
  implemented. Current source retains its 143 component / 33 logic test evidence;
  the focused answer-recovery and question-card suites also pass (22 tests).
  Answer selection highlights immediately, and local source now announces the
  pending check while correctness waits for the durable retry receipt and one
  server POST. Staging records server time for both native answer routes: the
  latest synthetic sample is about 114–117 ms server-side. The remaining mobile-
  signed staging preview measured 198 ms tap-to-response on one Android emulator
  answer (15 ms durable receipt write, 183 ms API round trip, 92.7 ms server
  handler). This is a diagnostic sample, not an owner-phone speed guarantee.
  Website-style exam filters were exercised in the native app, including module,
  study/answer status, subject, topic and year controls; “wrong” narrowed the
  synthetic set from 1,000 to 3. Broader physical/network sampling and TalkBack
  focus/speech acceptance remain.
- Current signed preview **01a448a3** passes synthetic browser sign-in, account
  restart, offline pending-choice recovery, one explicit retry/one attempt, saved
  result restart, sign-out revocation and guest restart on the dedicated API36
  emulator. Cold startup needs online account/catalogue revalidation; general
  offline study is not certified. Lint/typecheck pass. [Current receipt](../reports/finna-current-signed-account-recovery-20261120/README.md).
- Signed long-list traversal reaches all 1,000 synthetic questions, with exact
  reading-position recovery and compact 200% text filter checks. [Traversal receipt](../reports/finna-native-emulator-extended-20261119/README.md).
- Local audience guards cover the staged request/worker/SQL/shared-visibility/
  reward/tier/notice paths reviewed so far. The latest backend checkpoint passes
  2,275 backend / 1,202 compatibility checks and its clone rehearsal. These are
  local staged changes. Migrations **0122–0130 are unapplied in production**;
  0130 is a local recovery draft, not a production activation. [Backend receipt](../reports/finna-cms-notice-eligibility-20261120/README.md).
- A fresh focused local recheck passes **86** account-privacy, audience/background,
  learning-eligibility and restore-preflight tests. This does not select retention
  policy or authorize production rollout. [Recheck](../reports/finna-policy-gate-check-20261120/README.md).
- Private request/restore/refund procedures and a read-only restore preflight are
  prepared; 107 scoped checks pass, including 44 new cases. This does not complete
  retention policy, actual repair or disaster recovery.
  [Procedure](FINNA-PRIVACY-OPERATIONS.md) · [Receipt](../reports/finna-restore-privacy-preflight-20261120/README.md).
- The verified-email account-reopen flow is implemented locally in migration
  **0130** and the recovery mail/UI paths. Its encrypted identity envelope expires
  after 30 days; reopening sets a new password and leaves sessions revoked. Bounded
  cleanup and the restore preflight include the envelope. Focused checks pass;
  production migration, mail activation and study-history deletion remain off.
- Operator identity is **Hruaitluanga, an individual trading as Finna**. Support is
  **hruaitluangasailo20@gmail.com**. The approved refund rule is **any reason within
  seven days of the relevant charge**, with no fixed refund-support response target.
  Mandatory obligations are not waived. Policy drafts remain private.

## Work still required

| Area | Concrete remaining work |
| --- | --- |
| Adult-only access | Owner selected **18+ only**, superseding the earlier under-18 audience. Guardian enrollment/provider selection is out of launch scope. Local copy and new-request handling use that rule. A 21 November cross-service rerun passes 344 account privacy, audience, Google/native, assessment, learning, game, publication, community, CMS and tier tests. Review existing-account/correction handling and validate all guarded registration, guest, Google and native paths against the exact enabled release. Production guards remain off/unapplied. No physical phone is connected now, so release-device/TalkBack acceptance remains. [Adult-only plan](FINNA-ADULT-ONLY-PLAN.md) · [Local test receipt](../reports/finna-local-launch-check-20261121/README.md) |
| Retention and recovery | The verified-email reopen path is implemented locally in migration 0130, but unapplied in production and not yet exercised against the real mail provider or release build. The owner approved the conservative study-history boundary: personal practice/mock/review, vocabulary/map answers and derived progress; multiplayer, rewards/payments/security, public/shared content and backups stay outside it. Migration 0131 now contains a bounded, resumable local draft with explicit holds, safe receipt unlinking and a default-off worker gate. The 21 November synthetic recheck passes 74 focused tests; catalog inspection found 31 foreign-key references into selected delete roots, and migration 0131 revokes direct app-role deletion on four study roots without application delete paths. The later actual local rehearsal restored the paired backup plus a separate fresh production snapshot, verified 124,996 files and bank/database pairing, and preserved original values in 252 tables per database through the staged migrations. It exposed schema dependencies 0116/0117/0119/0121 before 0122–0132; no Atlas content seed or feature activation ran. A rolled-back synthetic retention smoke preserved rewards/multiplayer, and local credential retirement cleared all quarantine counts. The original older candidate remains blocked on users; the later complete-source third preview now passes all privacy/billing/account comparisons with credentials quarantined and both evidence copies unchanged. Still reconcile the exact field/location/trigger/hold scope, global production roles, backup/source/key behavior, current-state repair and final writer cutoff, and actual release/mail recovery. The read-only restore checker cannot establish reference currentness or authorize production restore/promotion. [Proposal](FINNA-RETENTION-PROPOSAL.md) · [Inventory](FINNA-PRIVACY-INVENTORY.md) · [Synthetic receipt](../reports/finna-retention-recovery-check-20261121/README.md) · [Actual clone rehearsal](../reports/finna-local-restore-rehearsal-20261121/README.md) |
| Legal and payments | Finish invoice/tax review and policy/contact/invoice publication and version binding. A 21 November official-source check supports a provisional conclusion that GST registration is not required solely for Finna's own online subscriptions while PAN-wide turnover remains below the Mizoram ₹10 lakh threshold; supply characterization and compulsory-registration exceptions still need a qualified tax adviser. New local migration 0132 and webhook code reconcile current pending/processed/failed refund state and partial/full payment aggregates; a processed full refund confirmed against current provider state ends only that subscription's access, while unrelated grants remain. The owner-only account view exposes recent payment/refund references. The latest integrity follow-up passes 125 synthetic billing/privacy/recovery tests and validates processed totals through a paginated refund read. Refund-before-charge delivery remains retryable, and concurrent duplicate event IDs apply once. Migration 0132 is unapplied and no provider webhook was configured or exercised. The draft does not issue refunds or cancel provider renewals; validate the refund/cancellation workflow in provider test mode before any separate live activation. Verify mailbox handling. [Drafts](FINNA-LEGAL-DRAFTS.md) · [Latest integrity receipt](../reports/finna-refund-integrity-followup-20261121/README.md) |
| Guarded deployment | Review the scoped API/publisher/migration set and recovery plan, including the schema dependencies found by the actual clone rehearsal (0116/0117/0119/0121 before 0122–0132; 0118 content seed excluded from that rehearsal). Drain every writer before any audience-policy transition; pair the current API, trusted publisher and all guards. Do not deploy the whole dirty checkout or replay old installers. Local implementation and a flag are not rollout approval. |
| Android physical and owner acceptance | A bounded Samsung A55 scroll sample is recorded: 150 frames, 2 janky (1.33%), p95 9 ms / p99 16 ms; app PSS about 168 MiB. A signed staging preview now also has one synthetic emulator answer measurement (198 ms tap-to-response) and a working wrong-answer filter. Still complete physical TalkBack speech/focus traversal; collect broader device, carrier-network/tablet and sustained release frame/memory samples. These bounded samples are not release certification. iOS remains deferred because no device is available. [Physical sample](../reports/finna-physical-android-check-20261120/README.md) · [Answer timing](../reports/finna-answer-timing-20261120/README.md) |
| Operations, content and scale | Actual healthy week before gated Desk/Atlas/Studio rollout; monthly human sign-off; reviewed district/topic/Chronicle content and official new-exam sources; real volume before rankings. Keep query/maintenance follow-through open. The two mobile dependency advisories are remediated locally; install/audit, typecheck, 33 logic tests, 143 component tests, lint and all-platform export pass. Signed beta **6d2bc67d** includes the lockfile and has been installed/launched on the owner's Samsung. That earlier build still needs physical TalkBack traversal/speech and broader device/network acceptance; the separate diagnostic preview has only one emulator answer-timing sample. [Remediation receipt](../reports/finna-mobile-dependency-remediation-20261120/README.md) · [Earlier operations review](../reports/finna-dependency-ops-review-20261120/README.md) |

Database audience policy, age, checkout, referral and earned-Pro catalog activation
remain off. No production deployment, new APK or phone connection was needed for
the latest checkpoint. An internal staging APK was built solely for the emulator
answer-timing check; no production deploy or physical-phone connection occurred.
[Adult-only change receipt](../reports/finna-adult-only-policy-20261120/README.md). Synthetic staging remains available; the emulator is stopped with its data retained.

## Critical path

1. **Retention scope and closure behavior:** the owner selected study-history
   deletion after export and a 30-day post-close window in which the account can be
   reopened. The clock starts at successful closure, and reopening before expiry
   cancels pending study-history deletion. The selected recovery flow uses a
   single-use link to the previously verified email and a fresh password; old
   sessions stay revoked and Google/MFA must be reconnected or set up again. The
   reopen implementation is local and remains unapplied; validate it on the
   release build and real mail provider. The owner approved the conservative
   boundary (personal practice/mock/review, vocabulary/map answers and derived
   progress; multiplayer, rewards/payments/security, public/shared content and
   backups excluded). A bounded default-off local cleanup draft is in migration
   0131. Reconcile exact fields/locations and exceptions with a qualified adviser,
   extend the completed local clone/synthetic retention rehearsal to cover exact
   deletion/hold/location reconciliation and backup/restore propagation. The
   original older candidate remains blocked on missing accounts, while the complete-source
   third preview now reconciles all 9,489 accounts and the selected privacy/billing
   controls. The matching bank/source capture and checked asset references verify.
   Controlled final writer cutoff, service/key recovery and currentness remain necessary.
   Do not apply the migration, enable cleanup or make an exact public retention
   promise until those gates and a separate rollout decision are complete.
2. **Qualified-adviser and owner/external checks:** settle periods/exceptions for
   remaining categories in the [retention proposal](FINNA-RETENTION-PROPOSAL.md)
   and confirm invoice/tax fields. The owner selected a seven-day, any-reason
   refund rule and stated they are not GST-registered. The owner reports Mizoram
   and PAN-wide annual aggregate turnover under ₹10 lakh, which is below the
   published service-supplier threshold. Confirm classification and any exception
   with a qualified tax adviser; do not assume GST registration is automatically
   required for paid launch.
   Full-refund access treatment is recorded in [legal drafts](FINNA-LEGAL-DRAFTS.md);
   partial-refund and actual provider-status behavior still require validation.
3. **Local engineering, after those decisions:** complete the rule-to-table/provider/
   backup mapping and reviewed restore repair. Build on the actual local clone
   rehearsal and bounded cleanup draft to finish end-to-end closure, refunds,
   delivery/key continuity and recovery checks. The separate billing restore
   preflight now covers stored access and payment/refund/grant receipts; it does
   not certify reward balances, provider/configuration state or final currentness.
   Keep production flags off until the scoped release and recovery plan are
   reviewed.
4. **Owner/external acceptance:** confirm the support mailbox works; perform real
   provider test-mode purchase/cancellation/refund/reconciliation; install and
   assess Android on physical hardware, including TalkBack. iOS stays deferred
   because no iOS device is available. Healthy-week, content and real-volume
   gates remain before wider rollout.

The owner has settled the audience as 18+ only; guardian implementation is no
longer a launch requirement. Physical/human/provider acceptance cannot be
substituted with more automated tests. Earlier chronological remaining-work notes
are preserved in the [previous frozen snapshot](../reports/finna-current-signed-account-recovery-20261120/document-preimages/docs__FINNA-REMAINING.md).
