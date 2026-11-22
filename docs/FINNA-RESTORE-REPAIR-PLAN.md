# Finna restore repair plan

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


Prepared 21 November 2026 from the retained private local clones. This is a
reviewable recovery plan. No identity repair, merge, production recovery or
promotion has been executed. The reference is an earlier point-in-time snapshot;
it does not establish current production state.

## What actually differs

| Account comparison | Observed count |
| --- | ---: |
| Accounts in the older candidate | 8,811 |
| Accounts in the newer reference | 9,489 |
| Shared accounts identical in every stored field | 8,811 |
| Shared accounts with changed fields | 0 |
| Accounts present only in the candidate | 0 |
| Accounts present only in the reference | 678 |

All 678 reference-only accounts are open and have no email. Each has one direct
guest-credential reference. The catalog inventory in the staged local clones found
174 direct account foreign keys. All app-readable dependencies have zero other rows linked to those 678
accounts, and there are no changed shared accounts. The one app-inaccessible
dependency is `account_study_history_holds`; a separate read-only local-owner count
verified zero total rows in each copy. No permission was granted to the app.

These are aggregate observations, not permission to delete the accounts or declare
them anonymous/unused everywhere. Indirect references, JSON/text identifiers,
external systems, later production changes and deletion decisions are outside
this diagnosis. Matching shared fields does not certify that the source itself is
correct. Both existing restore gates remain blocked until their inputs reconcile.
See the [diagnosis receipt](../reports/finna-restore-account-diagnosis-20261121/README.md).

## Preferred recovery route

1. Preserve the existing candidate/reference and their source-bound evidence.
   Keep them offline with no API, SMTP, worker or publisher attached. Do not
   overwrite shared identities or discard accounts to clear a comparison.
2. Prepare the exact reviewed API/publisher/migration/configuration set and a
   separate cutover decision. Identify all writers and their drain/resume sequence.
   Production remains unchanged until that release/recovery work is ready.
3. For the final recovery capture, use a complete current database and matching
   workshop/assets after the authorized writer cutoff. Preserve the immutable
   backup receipt and source hashes. Do not mix a newer database with older files
   merely because one bank hash matches; verify the generation and all referenced
   assets. Original PDFs/figures, keys, provider state and other excluded copies
   require their own inventory and continuity evidence.
4. Restore into a new isolated candidate. Validate the schema-only dependencies
   0116/0117/0119/0121 before 0122–0132 against the exact source state. The earlier
   rehearsal did not run the 0118 content seed or activate Atlas/other flags.
   Verify original values, ownership/permissions, flags and asset pairing.
5. Apply the reviewed credential/outbound quarantine to the new copy. Do not
   import the 678 guest credentials from the reference. Retire copied sessions,
   tokens/flows/feed URLs and reconcile mail queues without replaying deliveries
   or deleting immutable receipts. Preserve current identity/security/privacy and
   financial decisions through their reviewed workflows.
6. Re-run privacy and billing preflights plus the account diagnosis against the
   authoritative final reference. Resolve every scope/gap, then verify deletion/
   hold decisions, provider/payment/renewal state, key continuity and the recovery
   authentication experience. A bounded checker pass alone is insufficient.
7. Record the source-bound recovery decision and rollback/resume plan before
   reopening only the reviewed writer set. No public launch flag is enabled by
   this document.

## Fallback if the older database must be retained

Prepare a **third, disposable local preview** with a separately reviewed,
source-bound additive repair. Never edit the two evidence databases. The currently
observed preview delta is exactly 678 missing account rows, zero shared-account
updates and zero candidate-account deletions; guest credentials must remain
quarantined and must not be copied. This observation is not an approved SQL repair.

Before any preview, bind the exact two snapshot/source hashes, verify all account
fields and the 174-reference inventory again, separately review protected holds
and indirect/external references, and check unique-handle/email/id conflicts.
Abort if the delta has changed, any shared identity differs, an unreviewed dependent
record exists or a current closure/erasure decision is missing. Preserve immutable
payment/reward/security history and original IDs; do not synthesize consent or
credentials. Compare the entire resulting scope and quarantine after the preview.

This fallback still needs file/source pairing, an authoritative final reference
and a separately authorized production decision. Prefer a complete current restore
when its required sources are available; do not build a production merge from the
aggregate report alone.

## Remaining before rollout

Currentness/cutoff, scoped release review, source/key/assets and deletion/hold
reconciliation remain. Actual release/mail recovery, payment test-mode acceptance,
invoice/policy review and physical Android acceptance are separate launch gates.
The local cluster is stopped. iOS remains deferred.


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
