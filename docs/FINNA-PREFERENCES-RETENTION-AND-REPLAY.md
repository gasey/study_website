# Private preferences retention, erasure-decision replay and audited 18+ correction

Migration **0134** (`api/migrations/0134_preferences_retention_and_audience_audit.sql`)
is a local implementation draft covering three remaining local gaps from
[FINNA-REMAINING.md](FINNA-REMAINING.md). It is **unapplied in production**, all
cleanup and audience flags remain **off**, and earlier migrations (`0001`–`0133`)
and frozen receipts are preserved unchanged.

## 1. Private preferences retention (separately gated)

| Private preference table | Fields covered by row deletion | Excluded / preserved |
| --- | --- | --- |
| `user_calendar_preferences` | `user_id`, `reminders`, `updated_at` | Official calendar events and history |
| `inbox_preferences` | `user_id`, `in_app`, `updated_at` | Other learners' inbox settings |
| `inbox_desk_reads` | `user_id`, `desk_id`, `last_message_id`, `updated_at` | Shared desk rooms, items and messages |
| `game_preferences` | `user_id`, `selection`, `updated_at` | Multiplayer game results and rooms |

`creator_blocks` is explicitly excluded because it enforces bilateral safety and
moderation visibility boundaries.

`sweep_expired_private_preferences(p_accounts DEFAULT 5, p_batch DEFAULT 200)` requires:
- Account closed at least 30 days (`closed_at <= clock_timestamp() - interval '30 days'`).
- Both prior cleanup stages completed (`study_history_purged_at IS NOT NULL` and `private_study_purged_at IS NOT NULL`).
- `private_preferences_purged_at IS NULL`.
- No active unreleased hold in `account_study_history_holds`.

Four `active_account_record('user_id')` triggers block post-closure INSERT/UPDATE on
these tables, and `private_preferences_purge_marker_guard` rejects `mpsc` forgery of
`private_preferences_purged_at` on both INSERT and UPDATE. In `account_retention.sweep`,
the step runs only when **all three** default-off flags are enabled:
`STUDY_HISTORY_RETENTION_ENABLED`, `PRIVATE_STUDY_RETENTION_ENABLED`, and
`PRIVATE_PREFERENCES_RETENTION_ENABLED`.

## 2. Authoritative erasure/hold-decision restore replay

`scripts/replay-restore-erasure-decisions.py` reconciles an isolated restored backup
against an authoritative reference without exporting PII or forging purge markers:

1. **Export ledger (read-only):**
   ```sh
   FINNA_RESTORE_REFERENCE_DSN=... api/.venv/bin/python scripts/replay-restore-erasure-decisions.py --export-ledger --out ledger.json
   ```
   Requires `REPEATABLE READ, READ ONLY`, `SELECT` on `account_study_history_holds`,
   and the `0134` schema. Exports only opaque user IDs, closure/purge timestamps,
   hold records, active reopen-envelope user IDs, and a canonical `ledger_sha256`.
   Zero emails, handles, passwords, essay bodies, answers or ciphertexts are exported.

2. **Verify candidate (read-only):**
   ```sh
   FINNA_RESTORE_CANDIDATE_DSN=... api/.venv/bin/python scripts/replay-restore-erasure-decisions.py --verify-candidate --ledger ledger.json
   ```
   Verifies `ledger_sha256` and reports aggregate drift across closures, holds,
   reopen envelopes, and all three purge markers. Exits `0` if reconciled, `2` if
   drift exists, `1` on error.

3. **Apply on an isolated quarantined candidate:**
   ```sh
   FINNA_RESTORE_CANDIDATE_DSN=... api/.venv/bin/python scripts/replay-restore-erasure-decisions.py --apply-candidate --ledger ledger.json --allow-isolated-candidate-write
   ```
   Fails closed if `ledger_sha256` fails OR if any active unrevoked web/mobile session
   exists in the candidate (enforcing credential quarantine first). Replays holds
   before closures, replays unapplied closures, removes stale reopen envelopes, and
   invokes the real bounded SQL sweepers (`sweep_expired_study_history`,
   `sweep_expired_private_study`, `sweep_expired_private_preferences`) only when no
   non-ledger-purged expired account would be affected. Never forges purge markers
   and always emits `promotion_authorized: false`.

## 3. Audited 18+ age-declaration correction

Migration `0134` adds append-only `account_audience_events` (protected by
`review_immutable()`) storing only structured `reason_code` (`self_declaration` or
`owner_verified_correction`), `previous_category`, `new_category`, `actor_id`,
`user_id`, and `request_id` — no DOB, ID documents, or free-text PII.

`POST /api/account-privacy/admin/audience-correction` requires:
- `AUDIENCE_GATE_ENABLED=true`
- Authenticated `owner` role with recent sign-in, CSRF, same-origin, and staff MFA
  when enforced
- An open `in_review` privacy request of `kind='correction'` for the target user
- Exact `expected_audience_version`
- **No automatic grandfathering:** unknown accounts (no `account_audience` row)
  cannot be upgraded to `adult` by an owner; they must confirm their own age category
  at `/account/privacy`. Correcting an account to `under18` acquires both
  `calendar_publication_lock` and `learning_processing_lock` and revokes active
  sessions, review digests, calendar reminders, and feed tokens.

## Limits

This is local implementation evidence only. Production migrations (`0111`–`0134`)
remain unapplied and all launch/cleanup flags remain off. Shared/public content,
moderation/support cases, provider mail, host logs, backup pruning, qualified
legal/tax review, real mail/Razorpay test-mode validation, physical Android
TalkBack/release checks, second-location SSH/key backup and scoped production
rollout remain open in [FINNA-REMAINING.md](FINNA-REMAINING.md).
