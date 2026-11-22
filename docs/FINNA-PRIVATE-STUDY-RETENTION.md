# Private writing and saved-link retention

Migration **0133** is a local implementation draft for the next part of Finna's
30-day post-closure cleanup. It has not been applied in production. Both cleanup
settings remain off. The earlier 0131 migration and its completion receipts are
preserved unchanged.

## Exact scope

| Private relation | Fields covered by row deletion | Shared source retained |
| --- | --- | --- |
| `essay_drafts` | `user_id`, `canonical_id`, `body`, `updated_at` | Canonical question and other learners' writing |
| `user_question_bookmarks` | `user_id`, `question_id`, `created_at` | Canonical question and other learners' saved links |
| `material_bookmarks` | `material_id`, `user_id`, `created_at` | Material, revisions, author, purchases, reports and other learners' saved links |
| `user_calendar_saved` | `user_id`, `event_id`, `created_at` | Calendar event, source/history and other learners' saved links |

These are private writing/preferences associated with study, rather than the
shared source records they reference. This staged extension uses the existing
30-day closure window. It is not a new erasure promise or a retention decision for
all remaining categories. Policy wording and scoped release review still precede
production activation.

## Eligibility and completion

The separate `sweep_expired_private_study` function requires all of the following:

- The account is still closed and at least 30 days past `closed_at`.
- The original study-history cleanup has completed (`study_history_purged_at`).
- The new private-writing/link cleanup has not completed (`private_study_purged_at`).
- No unreleased hold is active in `account_study_history_holds`.

All four existing hold codes apply. An unexpired hold with no release pauses the
step; a null expiry continues until release. Any remaining active hold still
blocks the step when another expires or is released. Reopening before the closure
window ends cancels cleanup eligibility. The new completion field is separate:
an older 0131 receipt cannot certify deletion of the four newly covered relations.

Each call claims at most 5 accounts by default (hard maximum 20), locks the account
rows with `SKIP LOCKED`, and deletes at most 200 rows per table/account by default
(hard maximum 1,000). Null or out-of-range limits fail. If a table still has rows,
the completion marker stays empty and the next batch resumes. After all four
tables drain, one minimal security event records policy `private-study-extras-v1`;
it contains no essay body, question/material/event ID or answer.

The app role cannot forge the new completion marker. The four private relations
also acquire the existing active-account INSERT/UPDATE guard, preventing stale
requests or workers from recreating rows after closure. Ordinary private editing
and saving for active accounts keeps its existing permissions. No broader table
grant is introduced.

## Worker and release gates

The retention worker calls the new step only when **both**
`STUDY_HISTORY_RETENTION_ENABLED` and `PRIVATE_STUDY_RETENTION_ENABLED` are true.
Both default to false. The private setting by itself cannot invoke cleanup, and
applying the migration executes no cleanup. The original job runs first; accounts
with unfinished base cleanup remain ineligible for this extension.

Before a separate production activation, review the exact migration/API/config
pair, source-bound restored-clone evidence, exported data/recovery window,
authoritative current holds/closure/erasure decisions and worker drain/cutover.
Keep policy text consistent with the release actually enabled. Turning the flag
off stops future batches; it does not restore records deleted by a committed
batch. Retain completion/audit state and the new schema during a controlled code
rollback rather than claiming that old receipts cover the added records.

## Restore checks and limits

`scripts/check-restore-private-study.py` is a separate, read-only 0133-aware gate.
It compares seven controls: all account closure/base/private completion markers,
all hold fields, full reopen envelopes, and exact rows in the four private tables.
Use two independently selected DSNs through `FINNA_RESTORE_REFERENCE_DSN` and
`FINNA_RESTORE_CANDIDATE_DSN`, then run:

```sh
api/.venv/bin/python scripts/check-restore-private-study.py --run
```

Both databases must have the 0133 schema. Missing schema or protected-hold access
fails closed. The tool changes no role or grant, rejects the same database on both
sides, and emits aggregate counts/table names rather than private draft text,
identifiers, ciphertext or fingerprints. The earlier retention/privacy/billing
checks remain separate; their frozen sources are unchanged.

Saved-snapshot equality is not final currentness or external erasure-ledger replay.
These four tables do not cover public/shared content, moderation and support
cases, rewards/payment/security history, every preference, provider mail, host
logs, snapshots or backup copies. Their remaining schedules, holds and restore
propagation still need separate reconciliation. The encrypted key backup and
required private SSH identity are unchanged by this work.

See [the local evidence](../reports/finna-private-study-retention-20261121/README.md),
[deletion/key recovery](FINNA-DELETION-KEY-RECOVERY.md) and
[the remaining launch work](FINNA-REMAINING.md).
