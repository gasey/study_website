# Finna retention proposal — decision draft

Private working proposal, 20 November 2026. **No complete category-by-category retention schedule is approved. Do not publish it or run study-history deletion/pruning jobs in production.** The owner selected export followed by study-history deletion 30 days after successful account closure, with reopening allowed during that period. Reopening before expiry cancels pending deletion. The owner approved a conservative implementation boundary: personal practice/mock/review, vocabulary/map answers and derived progress are in scope; multiplayer results, reward/payment/security records, public/shared content and backups are outside this job and need separate review. Local drafts are staged in migrations 0130 and 0131; 0131 is default-off and neither migration is applied in production. The complete schedule, legal/provider checks, backup reconciliation and production release gates remain open. The documented operator identity is Hruaitluanga, an individual trading as Finna.

Owner decisions recorded 20 November 2026: after account export and successful closure, delete the approved conservative study-history scope after **30 days**, and allow reopening during that period. The clock starts at successful closure; reopening before expiry cancels pending deletion. The owner selected a single-use link sent to the previously verified email; reopening sets a fresh password, leaves old sessions revoked and requires Google/MFA to be reconnected or set up again. Local migration 0130 and the recovery flow implement this path for verified-email accounts; unverified-email accounts still close but cannot self-reopen. Migration 0131 stages bounded cleanup with holds and detached reward links; the hourly caller defaults off. Neither migration is deployed/applied in production. This decision does not set backup expiry or financial/security retention and does not authorize production cleanup or an exact public erasure promise. Reconcile locations, legal/accounting exceptions and recovery before release. Keep the encryption key stable through each open recovery window.

## Rules for shaping the schedule

- Keep only the data needed for an identified service, security, support or legal purpose. Record a purpose and start point for each period.
- Apply shorter lifetimes to temporary credentials, caches and operational counters where safe. A job's eligibility threshold is not a deletion promise: jobs can fail, defer, or process a bounded number of rows.
- Preserve security, payment, correction and economic history needed to explain access, answer changes, disputes or accounting. Limit access and remove direct identifiers when a purpose ends where that is safe; do not claim data is anonymous merely because an email is removed or a hash is stored.
- Treat primary databases, application/proxy/journal logs, email/payment providers, host snapshots, paired dumps, release/recovery copies and exports as separate locations. An account deletion cannot rewrite old backups. A restore must reapply verified closure/erasure decisions before any candidate is promoted.
- Do not advertise an exact erasure deadline until the schedule has been approved, every relevant location is inventoried, and cleanup/backup restoration is tested.

## Proposed decision matrix

Durations below are **choices for owner and legal/accounting review**, not facts about current behavior or statements of law.

| Category | Current behavior | Proposal to review | Decision needed |
| --- | --- | --- | --- |
| Browser age-flow token hashes | One-day expiry; bounded cleanup of up to 500 per pass | Keep the one-day expiry; disclose cleanup may lag; clear replaced tokens on the next declaration | Accept this disclosure and treatment? |
| Web/mobile sessions | Expired/revoked sessions require age and status thresholds; cleanup is hourly/bounded | Keep existing thresholds; list sign-in/security events separately | Confirm intended session lifetime and whether cleanup lag is acceptable |
| Login attempts, rate counters, temporary auth flows | Mixed thresholds from one day to 30 days; some auth routes delete login-attempt rows sooner than the worker | Retain only the minimum needed to investigate abuse; choose a consistent target after comparing false-lockout/security needs | Select target lifetime and define overrides for active investigations |
| Account identity and credentials | Retained while active; closure nulls email/password/name/avatar, removes some linked credentials, randomizes handle | Local migration 0130 stores an encrypted, keyed-email identity envelope for 30 days only when the address was verified before closure. A single-use link restores the account with a fresh password; sessions remain revoked; Google/MFA require reconnect/setup. Migration and delivery are not active in production | Verify encryption-key continuity through the grace period, mail configuration and abuse limits; decide handling for unverified-email closures and identifier release after expiry |
| Learning answers, progress, mastery, saved exams | Durable; generally retained after closure today | Owner-selected direction: offer export, allow reopening for 30 days, then delete study history. The clock starts at successful closure; reopening before expiry cancels pending deletion. Reconcile this with applicable minimum processing-record retention before promising erasure | Define exact records/fields, exceptions/holds, location coverage, cleanup/reconciliation and qualified legal/accounting review |
| Notes, calendars and private desk material | Some private calendar/desk data is removed on closure; coverage differs by subsystem | Delete private content at closure after ownership/share blockers are resolved; keep only minimal operation evidence | Approve immediate removal or a short recovery window; decide treatment of shared copies |
| Public posts, answers, profile and attribution | Public profile/sharing can be disabled; post text may remain and may identify the author | On closure, unpublish profile and offer post deletion or irreversible attribution removal; use a short queue for reviewed exceptions | Choose default (delete or anonymize) and exception process |
| Privacy/support requests and case evidence | New requests have append-only state events; no general expiry; email is outside the app | Keep the minimum case/audit record for a defined period after closure; delete free-form message copies sooner when the case closes if no hold applies | Choose period, case fields and mailbox deletion procedure |
| Payment, refund, invoice, tax, dispute and access ledger | Durable provider references, subscription state, webhook/replay history and local draft `billing_refunds` records; checkout is off. Migration 0132 is unapplied | Keep the legally required financial/accounting source records for the period confirmed for this individual operator, plus a minimal audit trail. Avoid retaining extra profile/study fields with them. Owner states not GST-registered. A provider-confirmed processed full refund ends access from that subscription; unrelated active grants remain. The local draft implements this entitlement change after current-state validation but does not cancel provider renewal | Operator/accountant must confirm invoice/tax fields and identify applicable tax, consumer/dispute and provider periods; validate real partial-refund/provider behavior and cancellation after a full refund |
| Security, staff, moderation, answer correction and reward/reversal audit | Durable in several tables; current cleanup does not provide one universal expiry | Keep security/processing logs for at least the applicable minimum; retain decision/reversal links needed to explain outcomes, with direct identity minimized after the hold expires | Confirm which records are true security/processing logs, their fields, access and event-specific start date |
| Database snapshots and release/recovery copies | Paired backup job does not prune; older dumps can contain closed accounts | Candidate: rolling 35-day paired backup window after complete location inventory, plus a longer encrypted disaster-recovery copy only if an approved recovery objective requires it. Expire copies automatically and test a restore followed by closure/erasure reconciliation | Is 35 days acceptable operationally? What recovery window and any protected hold are required? |
| PostgreSQL/application/proxy/journal/provider logs | PostgreSQL uses weekly rotation and ten rotated files; exact expiry is not guaranteed; other locations unknown | Candidate: 30-day searchable operational logs and up to 12 months only for narrowly scoped security events where required; separate ordinary diagnostics from access/security records | Inventory every source, then approve durations by log type and verify provider settings |
| Exports, local browser copies and user downloads | Supported export is user-triggered; downloaded copies leave Finna's control | Keep temporary server staging only as long as necessary for delivery (candidate 24 hours); tell users downloaded copies are theirs to secure/delete | Confirm whether exports are streamed or staged and the resulting deletion behavior |

## Legal and operational checks before publishing

The official [Digital Personal Data Protection Rules, 2025](https://www.meity.gov.in/static/uploads/2025/11/53450e6e5dc0bfa85ebd78686cadad39.pdf) include one-year wording in Rule 6(1)(e) for security logs and Rule 8(3) for specified processing personal data/logs. Rule 8(1)'s inactivity-erasure rule applies to listed fiduciary classes and purposes, which is a separate mechanism. The Rules contain phased commencement; this draft does not assert which provision is in force on the publication date or how the provisions apply to Finna. The owner must get current India-specific advice before selecting shorter periods or publishing a legal position. The [India Code Act copy](https://www.indiacode.nic.in/bitstream/123456789/22037/1/a2023-22.pdf) is marked current only through 19 November 2025, so it is not a complete 2026 consolidation. The [official PIB parliamentary response](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2202901) discusses transition and continuing SPDI framework; it does not settle Finna's specific retention schedule.

The technical inventory records observed cleanup thresholds and closure behavior in [FINNA-PRIVACY-INVENTORY.md](FINNA-PRIVACY-INVENTORY.md). The operator's case, restore and deletion procedure is in [FINNA-PRIVACY-OPERATIONS.md](FINNA-PRIVACY-OPERATIONS.md). Official-source availability and the limits of this research are recorded in the [20 November report](../reports/finna-adult-only-policy-20261120/research-note.md).

## Source-bound implementation coverage map

This map is from local source inspection on 20 November 2026. It identifies the
primary code path and known record families; it is not a claim that all
infrastructure, provider, log or backup locations have been discovered. No
policy duration is selected here.

| Purpose/category | Application records or code path | Existing lifecycle/control | Gap before a policy promise |
| --- | --- | --- | --- |
| Identity and credentials | `users`, `google_identities`, `auth_sessions`, `mobile_sessions`, `account_mfa`, `mfa_recovery_codes`, `account_email_tokens`, `account_mail_outbox`, `account_closure_recovery`; `api/app/services/account_tools.py`, `api/app/routers/account_recovery.py`, migration `0130_account_reopen_window.sql` | Local source revokes sessions, removes Google links and recovery codes, consumes email tokens, drops unsent account mail, clears MFA secrets, nulls direct profile/credential fields and randomizes handle. For previously verified email it keeps an encrypted identity envelope and keyed digest through `closed_at + 30 days`. A single-use link reopens before expiry with a fresh password; old sessions stay revoked. | Validate the release build and real provider mail path; inventory SMTP/provider copies and preserve the encryption key for every open grace period. Unverified-email closures cannot self-reopen. |
| Learning and assessment history | `attempts`, `user_activity_daily`, `user_topic_mastery`, `review_items`, learning job/cursor tables, exam bookmarks/checkpoints, game answers/events, and reward claims; export mapping in `api/app/services/account_tools.py` | Export streams selected owned records and withholds active-assessment rows. Closure leaves most durable learning and assessment history in place. `api/app/services/account_retention.py` deliberately preserves durable progress and replay/economic receipts. | Owner-selected direction is deletion 30 days after successful closure, with reopening before expiry cancelling pending deletion; confirm exact records/fields, exception/hold treatment and related cursors/game snapshots; then reconcile any statutory/security hold. Keep rewards/economic receipts separate unless specifically approved. |
| Private notes, calendar and desks | `personal_desks`, `calendar_entries`, `calendar_feed_tokens`, `study_desk_items`, `study_desk_messages`; `account_tools.close`; `api/app/services/desk_retention.py` | Closure deletes the private desk document and owned calendar entries and revokes feed tokens; reopening does not restore this already-deleted content. Shared desk owner closure is blocked until transfer/closure. Closed-desk items/messages become eligible after 30 days; resolved report snapshots are cleared after their row-specific `retain_until`. | Confirm shared-copy treatment. Bounded desk cleanup has no common privacy-request receipt or closure reconciliation. |
| Public contributions and attribution | `posts`, creator profiles/follows, public contribution and vote records, moderation/report records | Closure hides creator profile, clears bio/public contribution flag and removes follows; post text and some attributed history can remain. Selected public responses filter closed subjects but do not rewrite stored history or earlier captures. | Choose deletion vs attribution removal, reviewed exceptions, and how copies/citations are handled. |
| Privacy and support cases | `account_audience`, `privacy_requests`, `privacy_request_events`, account-security events; owner support mailbox is external | Privacy request status/events have no general expiry in the reviewed code. Requests capture no free-text identity evidence; closure does not clear the request history. Support Gmail and sent mail are outside the app. | Define case retention and mailbox handling, identity verification, legal holds, and the workflow that verifies completion across systems. |
| Billing, refund and economic evidence | `billing_subscriptions`, `billing_payments`, local draft `billing_refunds`, webhook/replay receipts, account rates/redemptions, `reward_ledger`, claims and access grants | Closure is blocked while recurring billing is unresolved. Immutable economic and provider-reference history is not swept by the transient cleanup worker. Checkout remains off in this local configuration. Owner-selected full-refund treatment ends only subscription-derived access after provider confirmation; unrelated active grants remain. The local refund webhook records current provider status, applies that full-refund entitlement consequence, and does not issue refunds or cancel renewal. | Accountant/legal review must identify actual record fields and applicable retention; validate implementation and provider/cancellation behavior. |
| Authentication/security and operational counters | `auth_login_attempts`, `rate_limits`, `review_rate_buckets`, Google/mobile/browser flow tables, `account_security_events`; `account_retention.sweep` | Hourly, bounded cleanup removes selected expired sessions/flows, stale login attempts and counters; login routes can delete attempts earlier. Session activity can be summarized into a durable security event. Error/lock contention can defer work. | Distinguish abuse counters from security/processing logs; inventory API/proxy/journal/host/provider logs and choose periods/start events by source. |
| Backups and recovery copies | `scripts/oracle-workshop-backup.py`, `ism-workshop-backup.timer`, `/srv/study/backups/workshop`; local pull described in `docs/ORACLE-PAPER-WORKBENCH-RUNBOOK.md` | Daily paired PostgreSQL dump plus selected bank/workshop files; root-only destination. Script explicitly does not prune or upload offsite. Local pull is periodic and can be stale/offline. A closure does not rewrite existing snapshots. `scripts/archive-review-backups.py` compresses hash-named review snapshots and keeps newest N raw files; it is not an account erasure schedule. | Inventory host/cloud snapshots, local pulls, release/rollback copies, source archives and manual copies. Decide expiry and holds. Define and rehearse a verified closure/erasure ledger replay before a restored copy can serve traffic. |
| User exports | `GET /data-export` in `api/app/routers/account_tools.py`, implemented by `account_tools.export` | Export is a bounded repeatable-read stream with `private, no-store`; no server staging directory appears in this path. The user’s browser/download copy is outside server control. | Reconfirm delivery behavior in the published deployment; document user-side copy limits and any browser cache/download guidance. |

The account-close path is a set of explicit updates/deletes, not a general
delete-by-user cascade. In particular, it does not presently erase attempts,
progress, mastery, review schedule, public post text, privacy-request history or
economic/audit receipts. This is current implementation behavior, not approval
to retain those records indefinitely. The owner selected study-history deletion
30 days after successful closure, with reopening allowed during that window. The
secure recovery channel, exact study-history scope and exceptions remain unresolved.
The existing bounded cleanup workers do not implement
this outcome; this map does not authorize destructive changes.

## Owner-approved conservative study-history boundary — implementation draft

The owner approved this boundary for the local implementation: personal answers,
scores and derived study progress are removed at expiry if the account has not
reopened. The deletion clock is `users.closed_at`; reopening before expiry cancels
the deletion. This is not a complete retention policy or permission to run cleanup
in production. The local, default-off migration is 0131; it still needs restored
production-clone testing, exact field/location reconciliation and qualified review.

| Candidate family | Local records found | Proposed treatment at expiry | Dependency or unresolved issue |
| --- | --- | --- | --- |
| Answer and score history | `attempts`, `attempt_assessments`, `mock_sessions`, `mock_session_answers`, `mock_session_questions`, `mock_assessments`, legacy `vocabulary_cards`, `answer_reveals` | Delete the closed user's answer rows and per-attempt/per-mock snapshots; remove private timed-test and legacy vocabulary answer state | Migration 0131 adds a narrowly scoped delete exception to selected immutable receipts and unlinks retained economic references. Verify correction/reassessment and all FK behavior on a restored clone |
| Practice and review state | `practice_study_sessions`, `study_focus_sessions`, `practice_request_receipts`, `learning_checkpoints`, `daily_revision_sessions`, `daily_revision_completions`, `review_items`, `review_session_items`, `review_item_completions` | Delete private sessions, retry responses, checkpoints, queues and completion history using resumable row batches | Dependency ordering and bounded retries are drafted; validate every child/parent combination and worker-generated rows on a clone |
| Derived progress and preferences | `user_activity_daily`, `user_activity_questions`, `user_topic_mastery`, `user_learning_days`, `daily_learning_plans`, `user_focus_subjects`, `user_exam_bookmarks`, `exam_study_checkpoints`, `module_learning_progress`, `user_vocab_deck_mastery`, `vocab_exposures`, `vocabulary_state`, `atlas_exploration`, `atlas_practice_suggestions`, `learning_rollup_jobs` | Delete per-user progress, activity projections, saved learning choices and unscored exploration state | Rollup jobs are removed with the projection; verify no independent worker can recreate rows for closed accounts before release |
| Vocabulary and unscored map activity | `vocab_attempts`, `vocab_presentations`, `vocab_practice_receipts`, `vocab_review_session_items`, `vocab_review_completions`, `atlas_drill_presentations`, `atlas_drill_results` | Delete personal responses, choice snapshots and retry receipts; retain shared vocabulary/map source content | Local triggers allow deletes only inside the expired-account sweeper. Verify exact assessment/export fields and all dependency paths on a restored clone |
| Multiplayer answer history — excluded | `game_answers`, the user's `game_members` row, `game_start_requests`, game-context `attempts`, shared rooms/events | Preserve from this cleanup as owner-directed exception; do not cascade-delete a room or other players' data | Decide a separate multiplayer retention and actor-ID policy before making a broader deletion or anonymization claim |

The owner explicitly excluded these from this study-history job; they remain under
their own schedule and need separate review:
`reward_ledger`, `reward_question_claims`, `mastery_milestones`,
`reward_redemptions`, reward/access grants, payment/refund/invoice records,
privacy-request and security events,
moderation/correction decisions, public posts, shared desk content, or system-wide
question/content snapshots. Some retained reward/replay rows referenced `attempts`
(`reward_question_claims`, `reward_ledger.source_attempt_id`, and
`mastery_milestones.source_attempt_id`). The local draft nulls those source links
while retaining the receipt/ledger rows; validate that this preserves anti-replay,
accounting and reward integrity before considering release.
Private calendar and personal desk documents are already deleted immediately at
closure and are not restored by account reopening. Shared desk copies and public
text remain separate policy decisions.

The migration-chain audit on the synthetic PostgreSQL schema found that the app
role previously held direct `DELETE` on four study roots with no application
delete path (`attempts`, `mock_sessions`, `review_items`, and
`study_focus_sessions`). Migration 0131 now revokes those privileges; the
security-definer sweeper remains able to remove eligible rows. Other mutable
projections retain existing owner-scoped reset/rebuild deletes, so this is not a
general database-level delete guard. Production grants and trigger behavior still
need confirmation on an isolated clone of the deployed schema.

Before production, independently trace every FK/trigger in the restored production
schema, enumerate every queue that might regenerate a row, test dependency-closed
accounts at several batch sizes and verify reopened/held accounts are skipped. The
scope must be reconciled with provider mail, logs, snapshots and recovery copies;
this database worker alone cannot promise complete erasure.

## Safe implementation order after decisions

1. Reconcile exact fields, retention exceptions/holds and every data location; get qualified legal/accounting review for statutory, financial and security periods.
2. Independently inventory each table, worker, provider and backup copy against the approved boundary, including fields that this database worker cannot erase.
3. Review migration 0131's constraints, function ownership, row batches and disabled caller; reconcile outputs and failures in an isolated restored clone.
4. Rehearse representative closure, reopen, hold, shared game, reward, pending worker, provider, backup-restore and batch-retry cases. Verify restored backups receive current closure/erasure decisions before promotion.
5. Validate the actual release build and mail provider, then separately authorize production migration/flag rollout. Publish a precise policy only after controls match it; never close a privacy request before system-by-system verification.

Until these decisions and checks are complete, `RETENTION_AND_REQUEST_POLICY` remains unresolved. Current production flags stay off, migrations 0130–0131 are local drafts, and no production cleanup or backup-pruning change is authorized.

## Actual local restore and retention smoke — 21 November 2026

The local clone rehearsal now restores the selected paired backup and a separately
read current production snapshot. Required empty schema dependencies were
0116/0117/0119/0121 before 0122–0132; 0118 content seeding was excluded. Original
values in 252 tables per database matched before and after migration. A synthetic
retention smoke ran through `mpsc`, removed private practice and receipt rows,
kept and unlinked reward evidence, and preserved multiplayer results. Test rows
were rolled back and sequence counters restored. The four study-root direct
DELETE grants are absent in the restored/migrated candidate.

Retiring copied web/mobile/guest credentials in the private candidate cleared all
quarantine categories, while the users-control mismatch against the fresh
reference remained blocked. This does not settle data-location/hold coverage,
production global role memberships, current-state repair, final writer cutoff,
provider/key continuity or policy exceptions. No real account's study history
was swept and no production cleanup flag changed. The private cluster is stopped.
[Actual clone receipt](../reports/finna-local-restore-rehearsal-20261121/README.md).


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
