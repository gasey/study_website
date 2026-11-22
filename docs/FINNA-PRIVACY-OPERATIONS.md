# Finna privacy, restore and refund operations

Prepared 20 November 2026. Private operator procedure for Hruaitluanga, an
individual trading as Finna. Support: hruaitluangasailo20@gmail.com.
This procedure has not been exercised against a real request or payment. Policy
publication, mailbox acceptance, adult-only rollout and checkout remain open.
It records how to prepare and verify work; it does not settle general retention
periods, legal deadlines or tax treatment. The owner has selected 18+ only and
study-history deletion 30 days after successful account closure, with reopening
allowed during that window. Reopening before expiry cancels pending study-history
deletion. Recovery uses a single-use link to the previously verified email and a
fresh password; old sessions stay revoked and Google/MFA must be reconnected or
set up again. The secure reopen path is implemented locally in migration 0130 but
is not applied in production or validated with the release build/real mail provider.
Exact records and exceptions remain unresolved; this procedure does not implement
study-history erasure. Minor
enrollment and guardian activation are out of current launch scope.

## Privacy request handling

1. Record receipt time, request type, case reference and assigned operator in a
   private case record. Preserve the original receipt time when more information
   is needed. Track any applicable deadline separately; the owner's no-fixed-refund-
   response choice is not a privacy response policy. Do not place request messages,
   account identifiers or exports in repository reports, analytics or public issues.
2. Prefer the account's authenticated request controls. A session must belong to
   the subject; refreshing/re-authenticating must not change that ownership.
   Email alone does not prove account control or guardianship. For a closed or
   inaccessible account, record the case and resolve an appropriate ownership
   verification method before disclosure. Do not solicit passwords, OTPs, recovery
   codes, card details or unapproved ID-document uploads.
3. Inspect the owned request and its current version. Only the existing owner
   role may move it into review or resolve it, with the application's existing
   recent-session/MFA/CSRF checks. Use the version displayed at review time; a
   conflict requires reloading the case. The subject can withdraw an open request.
4. Specify the actual operation and its scope. An access request can use the
   existing owned export, which omits credentials, other people's private records
   and active-assessment details. An erasure request requires reviewing the
   [inventory](FINNA-PRIVACY-INVENTORY.md), relevant retained records and provider/
   backup copies. Account closure is the implemented tombstone/anonymization
   workflow; it is not universal erasure. Resolve billing, staff and shared-desk
   blockers through their existing controls, not direct SQL bypasses.
5. Finna is 18+ only. Do not offer guardian enrollment or solicit guardian identity
   documents. Historical guardian request receipts can be reviewed, withdrawn or
   resolved without granting study access. Do not change an under-18 declaration
   to adult or treat a completed request as activation. An incorrect declaration
   needs reviewed correction, while privacy/export/closure remain available.
   Follow the [adult-only plan](FINNA-ADULT-ONLY-PLAN.md).
6. Record verification outcome, authorized action, affected systems, completion
   evidence and any retained category/exception in the restricted case record.
   Keep only the necessary evidence; retention of that record remains a policy
   decision. Do not copy identity documents into request events. The application's
   status transition is append-only audit evidence of a decision, not an erasure
   executor. Mark completed only after the actual operation has been verified.
7. Give the requester an accurate account of what was done and what remains,
   through the verified channel. Messaging requires the operator's authorization;
   no email or delivery test has been sent by this implementation.

## Retention decisions still required

The current [cleanup thresholds](FINNA-PRIVACY-INVENTORY.md#retention-and-closure-facts)
remain unchanged. A threshold in a bounded cleanup worker is not an exact deletion
deadline. No backup pruning or durable-data expiry job is authorized here. The
owner-selected study-history delay is staged locally in 0131; it remains disabled
and unapplied in production.

| Category | Decide before claiming a complete policy |
| --- | --- |
| Closed/inactive study records and public text | The owner approved the conservative boundary (personal practice/mock/review, vocabulary/map answers and derived progress; multiplayer, rewards/payments/security, public/shared content and backups excluded). A bounded local draft is staged in migration 0131 with a default-off caller; it is not deployed/applied. A rolled-back synthetic retention smoke passed on the restored production clone. Still reconcile all fields/locations and legal/accounting/security exceptions, and validate the 0130 reopen path on the release build with real mail. Separately decide public-text purpose, removal/anonymization and exceptions |
| Privacy/age declarations, historical guardian requests and support mail | Minimum fields, access, period, closure treatment and lawful exceptions; no guardian enrollment or raw ID collection |
| Security, moderation and economic/replay history | Purpose and duration for each category; preserve replay protection and immutable integrity until a reviewed replacement exists |
| Payment/refund/invoice/dispute records | Applicable accounting/tax requirements, access, storage and expiry; operator/tax review is still required |
| Paired dumps, release copies, provider snapshots and offsite copies | Complete location inventory, expiry, legal holds, pruning procedure and restore reconciliation; the current paired job does not prune |
| Proxy/application/journal/provider logs | Actual configuration and provider retention; file rotation alone does not establish an erasure deadline |

## Restoring without reopening old access

21 November local rehearsal: the paired backup and an independently read current
dump restored into a private socket-only cluster on the spare disk. Applying the
current staged schema required 0116/0117/0119/0121 before 0122–0132; no 0118 content
seed or production deployment ran. Original values in 252 tables per database
survived the migration sequence. A synthetic retention smoke passed and was
rolled back, including restoration of sequence counters. Local retirement of the
restored web/mobile/guest credentials cleared the quarantine counts, but the
`users` comparison still differs. That block must remain until a reviewed current-
state repair and final cutoff are established. The cluster is stopped. This is
rehearsal evidence, not a production recovery authorization. [Receipt](../reports/finna-local-restore-rehearsal-20261121/README.md).

An intact paired dump establishes recoverability. It cannot establish that old
identifiers, sessions, consent or pending deliveries are still valid. The existing
monthly restore tool remains unchanged and does not perform this comparison.

1. Quarantine the candidate before restoring: no public traffic, login, email,
   payment callbacks, schedulers, publishers or background workers. Use private
   storage and least privilege. Preserve the selected backup receipt and matching
   bank/database hashes. Do not run a frozen installer over a newer release.
2. Establish a trustworthy current reference and cutoff independently of the old
   backup. Drain all writers before the final comparison. Include closures,
   declarations, withdrawals, privacy requests, unlinking and preference changes
   since the backup. The checker cannot prove that the supplied reference is
   current. If the only surviving copy is the old backup, this gate is unresolved;
   comparing that backup with another copy of itself is not evidence of currentness.
3. Reconcile the candidate using a separately reviewed, source-bound repair plan
   and existing authorized workflows. This checker supplies no repair SQL. Do not
   disable immutable-history/closure guards, manufacture consent, infer an age,
   delete reward receipts or replay old publications to make a comparison pass.
   Preserve pending/terminal privacy requests and their event history. Include
   closed-account private documents and any separately recorded erasure actions.
4. Retire restored bearer access: web/mobile sessions, guest credentials, recovery/
   verification links, OAuth/mobile/browser flows and calendar feed URLs. The
   check requires no usable candidate credential in those categories, including
   an orphan mobile credential. Password/Google/MFA state is separately compared
   to the current reference; choosing how people safely re-authenticate remains
   part of the recovery plan. Do not silently remove a real MFA factor.
5. Resolve every pending account/review mail item and reserved/uncertain send
   against authoritative delivery records. A missing success receipt is not
   permission to send again. The checker blocks these candidate queues; it never
   cancels, deletes, retries or marks deliveries sent. Preserve immutable capacity
   receipts: they are compared with the reference, and reserved/uncertain totals
   are reported separately for review. Matching historical uncertainty is not a
   queued message and must not be erased to make a check pass. An unsent account
   outbox row whose ciphertext was already cleared is likewise not deliverable.
   Other outbound/in-app jobs still need their own review.
6. Run the new checker from the reviewed checkout with DSNs supplied privately
   through the operator environment, not shell arguments, command history or
   receipt text. Both databases must expose the currently staged schema, including
   privacy tables; missing schema or privileges is an error, not a skipped check:

   ```bash
   api/.venv/bin/python scripts/check-restore-privacy.py --run
   ```

   Required environment names: `FINNA_RESTORE_REFERENCE_DSN` and
   `FINNA_RESTORE_CANDIDATE_DSN`. Use the repository virtual environment and the
   intended host/socket settings. The tool uses repeatable-read, read-only
   transactions as `mpsc`, fixed public table references, UTC and bounded query/
   lock timeouts. The server computes fresh salted row hashes; record contents,
   salts and fingerprints are not printed or persisted. Output contains table
   names, aggregate counts and an operator source hash. Exit 0 means the bounded
   checks passed; 2 means a mismatch or quarantine blocker; 1 means an error.
7. A pass covers 21 selected identity/privacy-control projections (including staff
   grants and durable mail receipts) and 10 candidate credential/mail categories.
   Reserved/uncertain delivery totals remain visible, and provider reconciliation
   is always unverified by this tool. It does not verify all retained content, erasure
   actions, guardian evidence, infrastructure isolation, currentness, bank sync,
   billing/provider state or logs/backups. It always reports
   `promotion_authorized: false`. Keep the candidate isolated until the complete
   current code/migration pair, policy/flag agreement, separate deletion evidence,
   request/provider reconciliation and rollback plan have been verified.
8. Record the final source-bound decision before reopening. Activate only the
   reviewed writer set; the staged audience guards require all writers drained
   and the matching API/publisher/migrations paired. Old workers can bypass newer
   assumptions. No reopening or deployment is performed by this document.

Re-run after any relevant source or reference change. Independent current-state
preservation, actual full disaster recovery, provider reconciliation and the
retention schedule remain open. The owner selected 18+ only, so guardian enrollment
is out of scope; use the [adult-only plan](FINNA-ADULT-ONLY-PLAN.md) for age cases.
The initial tests used isolated synthetic databases. The later actual restore
rehearsal used private local copies of the paired backup and a separately collected
production snapshot; it did not expose either copy to application traffic or change
production.

## Billing and access restore companion

Run `scripts/check-restore-billing.py --run` with the same private
`FINNA_RESTORE_REFERENCE_DSN` and `FINNA_RESTORE_CANDIDATE_DSN` environment names
after bringing both isolated databases to the reviewed staged schema. This is a
separate read-only comparison; the privacy operator and its historical receipts
keep their original scope. The billing tool requires refund columns/tables from
0132, including for empty tables; missing schema or read privileges returns an
error. It never applies migrations or calls a provider.

Eight fixed projections compare all users' stored plan/trial/subscription links,
closure and email-presence eligibility; subscriptions and their full-refund access
end markers; payment amounts/owners/refund totals; refund states; webhook replay
receipts; account rates; owner/referral grants; and earned access redemptions.
Expired and future records are included. Evaluating only who has Pro today could
miss lost receipts and access that returns later. Free/guest account additions also
produce a users mismatch; this is an exact stored-input comparison, not a paid-user
count or a provider balance audit. Write-only `updated_at` timestamps are excluded
because 0132 backfills payment timestamps independently in each restore.

The tool uses distinct databases, repeatable-read/read-only `mpsc` transactions,
fixed public references, UTC, bounded timeouts and freshly salted server hashes.
It exports only aggregate counts/table names and its source hash. Exit 0 means
these projections match; 2 means a mismatch; 1 means an error. It always leaves
currentness/provider reconciliation unverified and promotion unauthorized. Check
reward balances/ledger, catalog and provider configuration, runtime/schema
integrity, deletion propagation and live provider/refund/renewal state separately.
Drain writers and bind an authoritative final reference before any final cutover.
Do not delete financial receipts, regrant access or rewrite accounts to force a
pass; any repair needs its own reviewed source-bound plan.

The 21 November local follow-up found seven billing/grant projections matching
between the retained clones, while users' access inputs still differed (9,489
reference rows; 8,811 candidate rows). Both privacy and billing checks remain
blocked, candidate quarantine counts stay zero, and the private cluster is stopped.
This uses the earlier point-in-time reference, not a new production snapshot or
final currentness evidence. [Receipt](../reports/finna-restore-billing-preflight-20261121/README.md).

## Diagnosing account mismatches before repair

Use `scripts/diagnose-restore-accounts.py --run` with the same private reference/
candidate environment variables. It uses the unchanged privacy helper for
repeatable-read, read-only `mpsc` connections. Fresh server-side salts/hashes stay
private; only totals, field names/change counts and direct foreign-key dependency
counts are exported. It compares every stored account field, partitions missing/
extra/shared/changed accounts, and requires matching account columns and FK
inventories. Account values/IDs and fingerprints are never exported.

This is a diagnosis, not a gate or repair. Exit 0 means the bounded diagnosis
completed, even when accounts differ; 2 means dependency-review gaps; 1 means an
error. Missing read permissions and composite/non-ID references remain explicit
gaps. It never broadens privileges. Indirect/unconstrained/provider references,
deletion decisions and reference currentness require separate review. The receipt
always leaves repair and promotion unauthorized.

The local diagnosis finds all 8,811 shared accounts identical, 678 reference-only
open accounts without email, no candidate-only accounts and no changed fields.
Among 174 direct references in the staged clones, only their 678 guest credentials
are nonzero. The protected hold table is correctly unreadable to `mpsc`; a separate
read-only local-owner count verified it empty in both copies without changing
permissions. The tool's original gap receipt is preserved. No account repair or
credential import ran, and the cluster is stopped. Use the
[repair plan](FINNA-RESTORE-REPAIR-PLAN.md) and
[diagnosis receipt](../reports/finna-restore-account-diagnosis-20261121/README.md).

## Refund preparation and reconciliation

Owner-selected terms: refunds for any reason when requested within seven days
of the relevant charge, through the support address above. There is no fixed
refund-support response target. Preserve the received time; processing delay
does not move the request outside its original window. Record charge/request
timestamps in UTC with an IST display. Ambiguous boundary cases need operator
review rather than a fabricated reason-based rejection. Mandatory obligations
and tax treatment remain to be determined separately.

This is an operator checklist for future authorized payment work. Checkout stays
off. No real refund, dashboard action, API request, webhook subscription or email
has been initiated by this continuation.

1. Create a restricted case reference, received time and non-secret charge/payment
   reference. Verify account/payment ownership through the appropriate controls.
   Do not request card details, OTPs or banking passwords. Record test versus live
   mode and merchant identity to avoid acting on the wrong environment.
2. Verify the captured payment, currency, amount, charge time and prior refunds
   in the provider. Compare the request time to the owner's seven-day rule; a
   reason is not an eligibility condition. Record remaining refundable amount
   before any action. Razorpay documents refunds for captured payments and caps
   cumulative partial refunds at the captured amount. See [issue refunds](https://razorpay.com/docs/payments/refunds/issue).
3. Prepare one concrete refund decision bound to the case, payment, amount and
   existing refunds. An authorized operator must review it before execution.
   Use the normal source refund route; do not substitute a separate bank transfer
   or turn study points/access rewards into cash. Razorpay describes returning
   funds to the original payment method. See [refund overview](https://razorpay.com/docs/payments/refunds).
4. After an authorized attempt, save its refund reference and observed state.
   On timeout or ambiguous response, query that payment's refunds before retrying;
   do not create another refund simply because a response was lost. The official
   [refund APIs](https://razorpay.com/docs/payments/refunds/apis) include payment-
   scoped retrieval and refund-id retrieval. No automated refund worker or
   idempotency guarantee is implemented here.
5. Keep subscription cancellation separate. Finna's current `/api/billing/cancel`
   requests cycle-end cancellation; it does not initiate a refund. Confirm recurring
   billing state in the provider and the application. The local draft now ends
   access from the refunded subscription after a processed full refund is confirmed;
   cancel the provider renewal separately. Invoice/credit-note treatment still needs
   adviser review; do not hand-edit access or rewrite reward ledgers as a substitute.
6. Reconcile the refund's status and settlement/reference in the provider. A
   request or created refund is not proof of completion. Razorpay lists pending,
   processed and failed states; availability of pending depends on the merchant
   account. [View refund details](https://razorpay.com/docs/payments/refunds/view).
   Preserve failed/uncertain cases for investigation. Local migration 0132 and
   webhook code now cover authenticated refund events and query the provider's
   current refund/payment state before recording pending, processed or failed
   status. Synthetic tests cover partial/full aggregates, duplicates, unknown
   payments and retry after provider mismatch. This draft is unapplied and no
   provider webhook is configured. It does not issue refunds; only a processed
   full refund confirmed against the current payment ends subscription-derived
   access, while separate grants remain. It does not cancel provider renewals.
   A full aggregate alone is insufficient: the paginated refund list must show
   processed amounts equal to the entire captured charge. Pending or failed
   portions do not end access. An unknown local payment leaves the event
   retryable without a provider lookup, allowing charge/refund delivery to arrive
   out of order. Investigate persistently missing charges before the provider's
   retry window expires. The list read is bounded to ten pages of 100 records;
   larger or inconsistent sets require manual reconciliation. Validate provider
   response times and retry handling as part of real test-mode acceptance.
   The documented [refund events](https://razorpay.com/docs/webhooks/refunds)
   and [fetch-refund endpoint](https://razorpay.com/docs/api/refunds/fetch-with-id)
   still require real test-mode validation, including cancellation after a full
   refund.
7. Record final outcome and send an accurate update only through the authorized
   verified channel. Follow through on tax/invoice reconciliation and the approved
   record-retention schedule before closing the case. Real test-mode end-to-end
   refund/cancellation/reconciliation and live acceptance remain launch gates.

Provider pages were checked on 20 November 2026. These are provider workflow
references, not a determination of Finna's legal or tax obligations.


## Completed local snapshot-recovery follow-up — 21 November 2026

The third full-reference preview passes 21 privacy and 8 billing projections;
all 9,489 account rows match in every field. Credential quarantine retired 7 web,
1 mobile and 9,441 guest rows only in that copy. All other public table values,
schema and sequence counters survive, and both evidence databases are unchanged.
The protected hold table remains app-inaccessible and is separately verified empty.
The old paired bank belonged to the older DB, so it was not reused for the newer
preview. A read-only capture now supplies the matching generation and source/
served/workbench/registered assets: 141,461 unique file hashes and the explicitly
checked registered-document, paper, figure and latest PDF-inventory references
verify. No workers, API, publisher, heartbeat or provider were started for recovery.
The private cluster is stopped. Saved-snapshot recovery is complete locally;
authoritative final currentness/cutoff, service/crypto-key/configuration recovery,
deletion/hold reconciliation, actual release/mail/provider/device acceptance and
separate rollout remain. [Receipt](../reports/finna-full-copy-recovery-20261121/README.md).


## Deletion/hold and original-key follow-up — 21 November 2026

The selected technical checks now pass: exact protected-hold/closure/purge/escrow
comparison, four hold types and release/expiry/grace behavior, restricted app
permissions and rollback-only cleanup in an independent restored clone. The
source preview and all cloned table values, public schema and sequence counters
are preserved. Both temporary check databases were removed; the three earlier
recovery/evidence databases remain. The private cluster is stopped.

The owner reported no known key backup. A separate age-encrypted original-key
archive on this computer passes fresh-process restore, saved pending-MFA
ciphertext/account binding, wrong-identity and tamper checks. It requires the
existing private SSH identity; neither that identity's separate backup nor a
second recovery location is verified. No plaintext key was saved or exported to
reports. Other cipher families were empty in the saved snapshot and are covered
synthetically. This is actual local key-backup recovery evidence, not release/
mail/provider or whole-service recovery acceptance.

The focused suites pass 108 tests, including 34 new cases. The schema catalog
covers 273 base tables and 20 views (the legacy `catalog.public_tables` label in
raw clone receipts counts all 293 relations), 2,450 columns, 458 FKs and 165
non-internal triggers. The explicit study sweep covers 38 delete tables plus two
cascaded mock children. Other private drafts/bookmarks, shared/provider/log and
backup copies remain outside that allowlist; reconcile their treatment before a
broader erasure promise. Final reference currentness and external decision replay
remain unverified. No production migration, cleanup, restart, mail or payment ran.
[Procedure](FINNA-DELETION-KEY-RECOVERY.md) ·
[Receipt](../reports/finna-deletion-key-recovery-20261121/README.md).


## Private writing and saved-link follow-up — 21 November 2026

Migration 0133 is a local, separately gated extension for the four private
writing/link relations identified by the earlier audit. It does not alter the
0131 allowlist, old completion marker, or earlier immutable migration receipts.
A separate `users.private_study_purged_at` marker prevents an old base-cleanup
receipt from certifying deletion of newly covered records. Eligibility requires
base cleanup completion, continued closure past 30 days, and no active hold.
The original and new worker settings must both be enabled; both remain off.

The new function deletes capped account-owned rows, emits one minimal policy
receipt at completion, and leaves questions/material/calendar sources, other
learners and excluded economic/shared records intact. Four INSERT/UPDATE guards
block recreation for closed accounts; app-role marker forgery is rejected. The
supplemental read-only restore checker requires 0133 on both sides and compares
seven controls without exporting private text or identifiers.

246 selected regressions, including 41 new cases, and a separate restored-dump
clone rehearsal pass. Original table values/counters and old schema definitions
are preserved; no real account is purged. All three temporary clones are removed and
the private cluster is stopped. Production is unchanged and 0133 remains unapplied.
This is local implementation evidence; remaining locations and policy/activation
review still precede any broader erasure promise or production cleanup.
[Procedure](FINNA-PRIVATE-STUDY-RETENTION.md) ·
[Receipt](../reports/finna-private-study-retention-20261121/README.md).
