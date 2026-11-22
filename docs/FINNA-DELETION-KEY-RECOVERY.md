# Finna deletion holds and encryption-key recovery

This is the technical check and recovery procedure for the staged 0130/0131
account-reopen and personal-study cleanup paths. Neither migration nor the
production cleanup gate is activated by these checks. Results and exact source
bindings are in [the 21 November report](../reports/finna-deletion-key-recovery-20261121/README.md).

## Deletion and hold boundary

The selected study sweep has 38 explicitly deleted tables and two mock child
tables removed by cascade. The source-bound catalog in the report enumerates
every public column, foreign key and non-internal trigger; it classifies each
relation against this selected sweep. The restored schema has 31 foreign keys
into its seven checked answer/session roots and 174 direct foreign keys to users.
These counts are dependency evidence, not proof of erasure from every location.

| Control | Fields and behavior |
| --- | --- |
| Closure and completion | `users.id`, `closed_at`, `study_history_purged_at`. Only a still-closed account at least 30 days after closure is eligible. Reopening before expiry cancels that eligibility. The completion marker and minimal security receipt are written only after selected roots and projections drain. |
| Restricted holds | Every field in `account_study_history_holds`: `user_id`, `hold_code`, `created_at`, `expires_at`, `released_at`. Any unreleased, unexpired hold blocks the study sweep. A null expiry remains active until release. An expired or released hold does not override another active hold. |
| Hold permissions | `mpsc` has no SELECT, INSERT, UPDATE or DELETE on holds. Its sweeper can inspect them through its security-definer function. The read-only restore check requires a separately authorized reader; it never grants app access. |
| Recovery envelope | Every field in `account_closure_recovery`, including the encrypted identity, keyed email hash and expiry, must reconcile with the authoritative reference. An envelope is not a credential that may bypass a token, expiry or fresh password. |
| Economic and shared history | Keep rewards, claims, financial/security/privacy-case records, shared content and multiplayer results under their separate policies. Selected reward source links are detached; immutable value and anti-replay receipts survive. |

The hold is specifically a **study-history hold**. It does not stop expiry of the
30-day encrypted identity envelope, revoke an already-used reopen token, preserve
private calendar/desk documents deleted at closure, or rewrite backups. Placing a
hold after a completed purge cannot recover deleted data. Do not describe it as a
system-wide legal hold or promise complete account erasure.

Other private records remain outside migration 0131's explicit allowlist. Examples
include `essay_drafts.body`, individual question/material bookmarks and saved
calendar events. Shared/public/moderation content and provider/log/backup copies
also remain separate. Their location, purpose, retention and hold treatment need
explicit reconciliation before making a broader deletion promise; this check
does not silently add them to the deletion job.

An authorized hold operator should lock the account row in the same transaction
before placing or releasing a hold, verify its closure/purge state, and preserve
the hold history. The study worker takes the account lock while deciding and
deleting. Keep writers drained during a final restore and reconcile the current
decision source before any restored database serves traffic.

## Restore comparison

`scripts/check-restore-retention.py` is read-only and compares three controls:
closure/purge markers for every account, all hold rows/fields, and complete
encrypted reopen envelopes. Missing, extra or changed rows block the check.
It rejects a database compared with itself. An absent schema or insufficient
protected-table privilege fails closed, with sanitized diagnostics.

Supply two separately verified DSNs through `FINNA_RESTORE_REFERENCE_DSN` and
`FINNA_RESTORE_CANDIDATE_DSN`, then run:

```sh
api/.venv/bin/python scripts/check-restore-retention.py --run
```

The reader needs only authorized SELECT access. The tool changes no role,
decision, credential or grant, and emits counts/table names rather than account
identifiers, ciphertext or fingerprints. Run the existing privacy and billing
checks as well. Equality against a saved snapshot does not establish final
currentness, replay an external erasure ledger, prove that deleted answer rows
are absent, or authorize promotion. Those remain separate checks.

## Key dependencies and recovery

`MFA_ENCRYPTION_KEY` is one Fernet key used by these current application paths:

- `account_mfa.secret_cipher` and `pending_cipher`;
- `account_mail_outbox.token_cipher`;
- `review_digest_preferences.token_cipher`;
- `account_closure_recovery.identity_cipher`;
- the HMAC lookup produced by `closure_email_hash`, derived from that same key.

Ciphertexts are bound to the owning account ID. A different valid key cannot
decrypt them and changes the closed-email lookup. Missing/invalid keys reject
encryption. Wrong-key reopening must return a temporary failure without consuming
the link, discarding the envelope or reopening the account. Restoring the original
key allows the same still-valid link to complete; old sessions remain revoked.

The implementation has a single key, with no key-version identifier, fallback
keyring or rotation/reindex procedure. Do not replace it with a new random key
during recovery. A deliberate rotation would need a separately reviewed plan for
all ciphertext families **and** the keyed email lookup, not only MFA seeds.

The read-only server check finds the running key in the root-owned, mode-0600
`/etc/mpsc/mfa.env`, included in the service's effective environment-file list.
It matches the running process and passes an in-memory synthetic probe. The
original `/etc/mpsc/db.env`-only probe did not find it; that initial result is
preserved alongside the effective-environment follow-up. No key value or key
fingerprint was exported and no service/configuration was changed.

The saved snapshot's one nonempty pending-MFA ciphertext decrypts with the live
key and the correct account binding. The other four ciphertext columns are empty
in that snapshot; their recovery behavior is exercised with synthetic data, not
claimed as real-record acceptance. Local and deployed MFA helper hashes match.

The owner reported no known independent key backup. A separate encrypted backup
of the **real original key** is now stored on this computer at:

`/home/hruaia/.local/share/finna-secret-recovery/20261121-original-mfa-key/mfa-key.json.age`

The key was streamed through SSH directly into age encryption; it was never
written as plaintext or emitted to chat/reports. The directory is mode 0700 and
the archive mode 0600. It is encrypted to the existing SSH public key corresponding
to `/home/hruaia/.ssh/id_ed25519`; that private identity is required for recovery.
Age's [official usage documentation](https://github.com/FiloSottile/age#usage)
describes SSH Ed25519 recipients and identity-file decryption. The downloaded
Ubuntu age package was checked against its authenticated APT metadata and
extracted privately, without installing or changing software on the server.

The encrypted backup was decrypted only into process memory. A fresh verifier
used the recovered real key to decrypt the saved pending-MFA record with its
account binding, and checked four synthetic payload shapes. An unrelated identity
and a modified archive both fail authentication. Only aggregate receipts and the
encrypted archive hash are recorded. No service was restarted or provider called.

This backup is independent of the Oracle server, so loss of that server no longer
leaves only its live configuration as the demonstrated key source. It remains
dependent on this computer and its SSH private identity; a separate backup of
that identity and a second recovery location have not been verified. Do not delete
the SSH identity on the assumption that the encrypted archive alone is enough.
The paired database/workshop backup and local pull scripts still exclude key
configuration; no automatic secret-backup job was added.

Before a real host-loss cutover:

1. Identify the approved independent secret backup, its access custodian and
   decryption method. Verify the original key can be retrieved without exposing it
   in chat, reports, command arguments or logs.
2. Restore it into the intended isolated service environment through the approved
   secret mechanism. Keep API traffic, SMTP, digest, cleanup and other workers off.
3. Check account binding and all nonempty restored ciphertext families in memory;
   verify closed-email lookup hashes as well. Record only aggregate results and
   explicitly list empty/unexercised families.
4. Reconcile closure/hold/erasure decisions, retire copied bearer access and stale
   mail, and verify the exact source/configuration pair before a separate cutover.
   Never send old outbox tokens merely to demonstrate successful decryption.

The synthetic regression also backs up a generated key to a private file,
restores it in a fresh Python process and verifies payloads plus the email lookup.
The separate encrypted real-key rehearsal above supplies actual key-recovery
evidence. Neither test authorizes a production restart, a mail replay or cutover.


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
