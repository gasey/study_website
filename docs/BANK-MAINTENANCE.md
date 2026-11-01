# Owner-delegated source maintenance

Community proposals retain independent review. A trusted operator can perform a specifically owner-authorized source restoration through `scripts/owner-bank-maintenance.py`. This command uses the existing SSH channel; it creates no account, browser session, MFA claim, reviewer vote or permission grant.

## Source publication

A JSON request records the existing owner's email, explicit authorization, contribution ID, exact reviewed payload hash, registered paper ID and PDF SHA256, and review reason. Only the owner's transcription, source-reference, new printed question or source-defect proposals are accepted. The owner must still have an active global owner grant. A reviewer objection blocks the command. Registered source evidence is validated through the ordinary proposal service.

`allow_rebase` must be explicit. It only allows changes outside the proposal's patched fields; the immutable revision and current source snapshot are recorded. A conflicting edit needs a new inspected proposal.

The command records `operator:owner-source-maintenance` and the delegating owner in an append-only event. This is administrative maintenance, not an independent review. The publication manifest binds the exact source, payload, baseline, bank checksum and authorization. The normal worker dry run, canonical local JSON write, server sync, content comparison and publication receipt still apply. Administrative source and answer maintenance receive no contribution credits.

```
python3 scripts/owner-bank-maintenance.py --request request.json --output receipt.json
api/.venv/bin/python scripts/bank-review-worker.py once --dry-run
api/.venv/bin/python scripts/bank-review-worker.py once
```

Publish in sequence. Each successful publication changes the bank checksum; do not export a stack of manifests against an outdated bank version. Inspect a failed publication before continuing. An already applied source request replays its existing receipt. A failed request is not silently re-exported.

## Answer decisions

The same trusted command can invoke the direct admin answer service under explicit operator delegation. It records a separate authorization event; its internal account reference does not assert a browser login or recent MFA. Browser endpoints continue to require session/CSRF/MFA. Current role, primary appearance, source integrity and active-assessment checks still run.

Official status needs a mapped registered authority key. A checked worked solution is `Verified solution` with `derived` source and remains unofficial. Record the date and scope of any unsuccessful key search; absence from a search does not prove that no key exists. Needs review places a hold. Unsolved removes the answer through canonical publication. Source faults remain visible in paper view and are excluded from grading and scored pools.

For an exactly mapped official key, the worked explanation is optional. Leaving it empty stores no explanation; the audit reason remains in rationale/evidence and does not count as a learner explanation. A key-only answer still requires its matching registered document, printed question, booklet and option text. Derived solutions and community-authored questions still require useful explanations. The owner batch publisher enforces the same distinction.

## Batch coordination and stale exports

Before queuing a multi-item answer/source publication, stop the local `ism-bank-review.timer` and wait for any running `ism-bank-review.service` to finish. Do not interrupt a running publication. The trusted maintenance CLI refuses new export batches while either unit is active. Review-hold batches create no publications and do not need this pause. Resume the timer after publishing and verifying the whole batch.

Separate reviewed `unresolved-source` clearances can also use source batches. Each item must include the complete current `expected_source`, a null answer index, distinct nonempty choices, an available figure reference when required, registered exact-paper evidence, and a `disputeNote` explaining the review. Its patch contains only `sourceDefect: null` and that note. The publisher independently checks the immutable source/flag baseline, paper evidence and unchanged bank hash. Source transcription never clears a flag automatically; answering remains a later decision after live clearance verification. Existing grading holds are preserved.

If a single-item worker advanced the bank before a batch acquired its lock, preserve the successfully applied member. Never rewrite the other immutable manifests to change their bank checksum. `scripts/retire-stale-owner-exports.py --request request.json --output receipt.json` can withdraw an explicit set of 1–100 unapplied owner answer exports. It requires the current bank checksum, existing owner delegation, all outstanding export IDs, unchanged exact source snapshots and a recorded withdrawal reason. It preserves manifests and canonical content, records the failed stale exports and withdrawn contributions, and writes no peer approvals or rewards. Fresh owner decisions must then recheck current source/key evidence and create fresh exports through the ordinary maintenance tool. The original failed/withdrawn history remains visible; it is not presented as applied publication.

## Verification and recovery

Compare the current local/server bank checksums, source appearances and canonical learner content before acknowledging a publication. Never fabricate sync-log entries or receipts for intermediate versions. Retired difficulty is preserved as raw appearance metadata where present; canonical difficulty is intentionally null. Its absence must not fail publication verification.

If sync committed but acknowledgement failed, first verify the exact current output checksum and every changed live value against the durable receipt. Only then record the operator reconciliation and acknowledge that publication. Never delete the original failed event or pretend it never happened. Unrelated bank edits require explicit reconciliation rather than a blind retry.

The LDC Law & Judicial Paper II first-paper evidence is in `reports/ldc-paper-publication`. Its real-content acceptance rehearsal runs in a disposable local database with synthetic accounts and attempts. It does not submit production learner answers or start a production mock.
