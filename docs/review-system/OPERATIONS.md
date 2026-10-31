# Review workspace operator guide

Deployed implementation checkpoint: 2026-10-21. Read ACCEPTANCE.md for tested coverage and outstanding release gates. This is not a claim that all enterprise readiness requirements have passed.

## Surfaces and identity

- `/admin/bank`: scoped question search, explicit scoring holds, legacy question reports, review queue, papers, registered taxonomy, publication history, permissions and audit.
- `/contribute`: account submissions and earned publication credit; `/contribute/new` edits immutable proposal revisions.
- `/community/contributors`: weekly/monthly/all-time net credit, with public attribution opt-out.
- `/community/questions`: original community MCQs, inline practice; these do not become official exam content.
- `/review/notifications`: private review and publication notices.

All contribution mutations require a real cookie session, same Origin and session-bound CSRF. Device IDs, subscription plans and reputation confer no review permission. Account signup currently does not verify email ownership. Never automatically grant an admin role just because an unverified signup matches an email.

The user nominated `hruaitluangasailo20@gmail.com`, but no matching account existed at the last deployment check. After the user signs up and confirms that it is their account, grant it explicitly using:

```bash
python3 scripts/bank-review-worker.py bootstrap --owner-email hruaitluangasailo20@gmail.com
```

This fails if there is not exactly one matching account. It does not create an account or choose a password. Only the owner can grant/revoke further permissions in People & permissions, with a login within the preceding 15 minutes. Reviewer and senior grants may be subject scoped. Publisher permission does not itself authorize review decisions.

## Publication and recovery

1. Author saves a validated draft and submits it. Revision changes invalidate earlier approvals.
2. Independent reviewers decide. Answer/text/option/new-MCQ/defect/duplicate changes require two approvals. Changing an official key additionally needs a senior reviewer and exact mapped key evidence.
3. An authorized publisher exports the accepted revision. Export checks current review grants, target baseline, evidence and the last bank checksum.
4. The trusted local worker takes the shared bank lock, verifies the manifest and source-file hashes, backs up the JSON bank, writes a durable prepared receipt, and atomically replaces the bank.
5. The normal sync sends the local bank to PostgreSQL. The worker verifies the live appearance, primary canonical fields and latest bank checksum before acknowledging publication and awarding credit.

The installed user timer `ism-bank-review.timer` checks every minute while this workstation's user service manager and network are available. It invokes only the fixed worker command; web proposal text never becomes a shell command. It does not invoke an AI model. If the workstation is offline, queued publications wait and the dashboard shows the stale worker heartbeat. This is not a continuously available server-side publisher.

```bash
systemctl --user status ism-bank-review.timer
journalctl --user -u ism-bank-review.service -n 50 --no-pager
python3 scripts/bank-review-worker.py once --dry-run
python3 scripts/bank-review-worker.py once
```

Receipts: `../mpsc-question-bankv2/bank/review-receipts/`. Backups: sibling `review-backups/`, keyed by input SHA256. A prepared receipt handles crashes before/after file replacement. Retrying a verified acknowledgement creates one credit and one notice. Do not delete receipts or restore an entire backup over newer changes. A drift failure requires comparison/rebase and fresh independent review; use Request revision in the contribution detail. Diagnose failures in the operator log; the browser receives a bounded safe error.

For an already applied publication, Propose reversal creates a compensating revision. It follows review/publication again and appends a negative credit entry. It does not erase audit history. New original MCQs can be withdrawn from scoring through an unresolved-source defect. Duplicate/source-fulfillment relationship reversal and restoring an official answer without newly mapped evidence require operator investigation.

## Source documents and taxonomy

Bootstrap registers the actual 1,938 paper PDFs and 177 taxonomy nodes by their repository taxonomy_version. Official keys are registered separately, never inferred from module agreement:

```bash
python3 scripts/bank-review-worker.py register-key --file /absolute/path/under/mpsc-question-bankv2/pdfs/key.pdf --paper EXACT_PAPER_ID --title 'Official final answer key' --status final
```

Then cite the registered key ID, SHA256, page, printed question, paper series and exact answer text in the editor. A source request can be drafted with a URL; an operator must ingest/register the paper first. A fresh reviewed revision links its registered paper ID before publication/fulfillment. Original MCQs need no source paper; existing-paper additions need the printed number and page and must not duplicate an existing appearance.

Question taxonomy edits use registered IDs and hierarchy. Structural taxonomy changes remain repository/operator work, followed by registry bootstrap; the admin page does not offer arbitrary taxonomy creation/deletion. All bank writer tools must retain the shared bank lock and preserve published manual classifications.

Legacy question reports are read in their original table, scoped to the same reviewer grants. They can start a correction in the normal editor. Rejecting one records a reason; marking one fixed requires an applied publication for the same canonical question. Report counts no longer automatically remove questions from scoring.

## Testing, deployments and rollback

```bash
api/.venv/bin/pip install -r api/requirements-dev.txt
api/.venv/bin/python -m pytest api/tests -q
npm run build --prefix web
./scripts/migrate.sh --dry-run
./scripts/migrate.sh
./scripts/deploy.sh
./scripts/sync-bank.sh --check
```

Tests create/drop isolated `ism_review_test_*` PostgreSQL databases and temporary synthetic banks. They never modify the real question JSON or production user data. Frontend/browser fixtures use synthetic accounts and localhost only. The app checkout already contained unrelated changes; deployment evidence uses a file SHA256 manifest rather than claiming a clean Git revision.

Migrations 0030 and 0031 are additive but applied: never edit them. Preserve the review tables and user history on rollback. Revert a bad bank publication with a reviewed compensation; restore an application artifact only after checking backward compatibility. Migration clone rehearsal succeeded; full disaster recovery/point-in-time restore and alert delivery have not been rehearsed by this implementation.

After API/systemd/PostgreSQL changes check both study.hawayu.in and the shared VM's family.hawayu.in. Never replace the shared Caddyfile.

## Limits carried into the next checkpoint

- Full mock reassessment history and adjusted scores after later corrections remain outstanding. New mocks have immutable content/key snapshots and original results; pre-snapshot historical sessions retain their existing fallback and cannot be honestly reconstructed.
- Existing derived-practice eligibility predates this contribution workflow. It is not evidence that all historical derived answers passed the new independent-review protocol. Strict official/key pools remain separate.
- Staff MFA, email verification, comprehensive load/accessibility/security testing, backup restore and externally delivered alerts remain outstanding.
- Taxonomy structural editing and PDF/image upload/ingestion remain operator tasks. The UI supports registered source/figure references.
- Contribution drafts require a valid proposal before saving; partial form autosave and a full module-crosswalk adjudication UI remain outstanding.
- Review permissions are not yet provisioned for the nominated owner account. No grants were issued to a substitute account.

### Owner provisioning completed — 2026-10-21

After the user confirmed signup, the exact nominated account was found and explicitly granted `owner` covering all subjects. The active grant was verified in PostgreSQL. Earlier pending-account statements describe the preceding checkpoint. The user can open `/admin/bank`; signing out and back in refreshes the session if needed.


## Adjusted scores and staff MFA — deployed 2026-10-21

Migrations 0032/0033 are applied and additive. Preserve assessment history, source/context revisions and account security tables on any application rollback. Do not roll back to code that silently permits staff mutations without the current MFA policy. Original scores remain immutable; adjusted assessments can exclude unsafe presentations. The background score-reassessment worker runs bounded batches every fifteen seconds. Check review_worker_health and both assessment_jobs/new_score_jobs failure counts. Five failures park a job for investigation; the owner retry endpoint /api/admin/bank/assessments/retry accepts a reason and resets at most fifty jobs from each queue, with an audit event. Do not repeatedly reset an unexplained failure.

Production MFA config is /etc/mpsc/mfa.env (root:root 0600); /etc/systemd/system/ism-api.service.d/mfa.conf loads it. MFA_ENFORCE_STAFF=true. Preserve the existing MFA_ENCRYPTION_KEY: silently regenerating it makes enrolled seeds unreadable. Never print it into logs, screenshots, Git or release reports. An encrypted backup must contain this file separately from the DB, restricted to the authorized operator. Disaster restore of both database and secret has not yet been rehearsed.

Owner action: open /account/security after signing in, enter the current password, scan the locally generated QR with an authenticator, confirm a code and securely save the ten recovery codes. Existing owner credentials were not changed. Setup needs a login from the past fifteen minutes and expires after ten minutes. Staff writes require a factor verification from the past fifteen minutes; read access remains available. A used TOTP cannot be immediately reused: wait for the next thirty-second code or use an unused recovery code. Other sessions are revoked at enrollment/disable. Recovery-code rotation invalidates old codes. An enabled factor is also required during new sign-ins.

If the phone is lost, sign in using an unused recovery code, then replace the authenticator after verifying the session. If both phone and all recovery codes are lost, there is no automated bypass: preserve account/security audit history and arrange a separately authenticated operator recovery procedure before changing credentials. No such destructive reset was performed. Staff cannot disable MFA while holding an active review grant. Learner MFA is optional. Legacy bearer-token moderation is separate and not protected by this account workflow.

Mail remains deferred by the user's explicit choice; email verification and password-reset delivery are not configured. The owner still needs to nominate real independent reviewers for genuine two-person approval. Dummy approvals remain isolated test evidence and must not be imported into real publication decisions.

Local and server artifacts: reports/review-system/{scoring,security}; server private report copy at /home/ubuntu/ism-release-reports/2026-10-21-review. No seeds, recovery codes or production credentials are included. Check both study.hawayu.in and family.hawayu.in after systemd/API/Postgres actions.


## Using the repair workspace — 2026-10-21

Open /admin/bank?tab=questions&issue=missing for the missing-MCQ queue. Other issue values: all,defect,held,malformed,unverified,keyed,descriptive. Subject/paper/search/selected appearance/offset are saved in URL query parameters, so refresh and copied workspace links retain context. Papers & sources has Inspect paper questions links. Results are canonical questions; a paper filter chooses that paper's representative appearance and orders by PDF page/printed number. Select another appearance in the inspector when comparing repeated sources.

Inspect source instructions/figures/options and existing corrections before proposing work. Propose answer correction, Text/options/figures and Tags/difficulty open the existing editor with the exact selected appearance. Submitted repairs still need the existing independent review/publication pipeline. Descriptive items show their written-answer presence, with no fabricated MCQ score. A missing embedded PDF viewer does not imply missing source: use Open source PDF. Source bounding boxes and module comparison ingestion remain outstanding. This read-only inspector does not require recent MFA; staff mutations retain the deployed policy.


## Reward policy operations — 2026-10-21

See ../LEARNING-REWARDS.md.0034is applied; never edit it. Admin→Rewards & points can change catalog point cost/enable status with explicit owner grant, current policy version and audited reason. Default1000points/7daysPro is provisional and disabled; earning/leaderboard features are live. Do not treat a balance ledger as a paid Razorpay record or overwrite billing state to redeem points. Keep immutable reward/redemption/claim tables on rollback and include them in backup restoration. Disable offers to stop new redemptions without erasing existing access.

No arbitrary award browser endpoint exists. Operators must not bulk-credit old activity or imports without an explicit policy and idempotent migration. Negative contribution reversals can produce wallet debt, blocking new redemption. Future games must share account caps/question identity and provide server-side result proof. Existing rewards are activity records; score reassessment does not silently rewrite them. Full game/abuse/restore/load validation remains outstanding.


## CMS operations — migration0035

Applied0035 is immutable. Owner /admin/bank?tab=content inspects exact drafts, publishes/requests changes, archives/restores and resolves reports. Archive removes public access and reverses a creator award once; restore never re-awards. Never publish by directly changing status/pointers. Paid demo is not checkout. Pro access uses actual entitlements. Evidence/docs mirrored to private release folder; see CONTENT-STUDIO.md.


## Creator safety — migration0036

Do not edit applied0036. Public profiles require own account opt-in; do not toggle real user consent as deployment setup. Owner Content CMS includes paginated Creator reports; existing staff MFA guards resolution. Use reasoned material archive workflow for content removal; report resolution itself does not ban accounts or award/penalize points. Blocking scope and remaining release matrix are in CREATOR-PROFILES.md.


## Publishing workbench — 2026-10-22

Use /admin/bank?tab=workflow for pending work, explicit priorities and exact report links. All-subject owner permission required for combined queue. CMS inspector compares immutable versions and sends reasoned version-guarded decisions; it does not bypass bank quorum/publication. Authors open /notifications or /inbox for feedback links.0037material event index is applied/immutable. No bank data or real moderation decision seeded by release. See PUBLISHING-DASHBOARD.md.


## Module evidence import — 2026-10-23

See ../MODULE-COMPARISON-INTAKE.md for prepare/load commands, hashes, matching policy and access.0038APPLIED, never edit. Load only reviewed immutable manifests with the latest bank-sync hash guard, private staging and operator peer-auth; identical replay is safe. No HTTP upload and no auto-publication. Source request and derived-answer reviews follow existing independent workflow. New source inputs create new runs; default workspace uses latest per module. Original historical crosswalk/answer-review/packet records remain inspectable. Artifact and live counts evidence: reports/module-intake.


## Prepared research draft action — 2026-10-23

Owner chooses a candidate with a prepared assessment, then Create … draft. Server validates immutable payload hash, research/run/latest-sync bank checksums, target identity/answer/provenance and full viewed snapshot. Stale failures require refreshed/rechecked research, not overriding checks. Retries/duplicate appearances reopen the same actor-owned draft; closed states open detail. All original citations plus current intake association remain. Draft creation does not submit/review/publish or grant credit. Follow normal independent review thereafter. No migration.


## Question discussion operations — 2026-10-23

Owner session moderation: `/admin/discussions` or bank admin Question discussions; existing staff MFA and CSRF apply. Process first-three-post approvals and conduct reports; the shared bearer console remains compatible for its existing actions/undo. Source links and report notes are displayed. Active mock questions are omitted from session-owner moderation reads and cannot be moderated by that user until the mock finishes. Permission grants are checked/locked in the same transaction as moderation reads/writes. Own posts require another authorized moderator. Use reasoned lock/unlock to pause a question thread.

Wrong-key/transcription claims become normal evidence-backed contribution drafts. Discussion acceptance/votes never publish answers. Include posts/votes/abuse reports/mod_actions, discussion_disclosures/events and new review_notifications references in database backups. Event/content immutability is enforced by0039; do not delete or rewrite history. Citation/excerpt snapshots already stored in contributions remain review history if an author later withdraws the source post. Full behavior/limits in QUESTION-DISCUSSIONS.md.
