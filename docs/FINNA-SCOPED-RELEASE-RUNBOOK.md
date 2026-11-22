# Finna scoped release runbook

This runbook defines the exact, reviewable deployment order for the locally staged
Finna work. **Do not deploy the whole dirty checkout and do not replay historical
one-shot scripts (`scripts/deploy-*`, `scripts/rehearse-*`, `scripts/prepare-*`).**
Generating the manifest or reading this runbook does **not** authorize a production
deployment or flag activation.

## Release split

| Bundle | Scope | Migration order | Gate |
| --- | --- | --- | --- |
| **Bundle A** | Core privacy, 18+ audience, verified-email reopen (`0130`), study/private/preference retention (`0131`, `0133`, `0134`), billing refund reconciliation (`0132`), paired API & trusted publisher (`scripts/bank-review-worker.py`) | Schema deps: `0116`, `0117`, `0119`, `0120`, `0121` → Core: `0122`–`0134` | Explicit owner authorization + pre-flight gates below; **all flags stay OFF** at deploy |
| **Bundle B** | Desk v4 (`0111`–`0115`) and Atlas v2/Studio content seed (`0118`) | `0111`, `0112`, `0113`, `0114`, `0115`, `0118` | Actual **healthy-week** operations receipt after Bundle A |

`api/migrations/0110_site_maintenance.sql` is **already applied and immutable in
production** — never re-apply it.

## Pre-flight gates (before any Bundle A cutover)

1. **Generate and verify the manifest locally:**
   ```sh
   api/.venv/bin/python scripts/build-scoped-release-manifest.py \
     --out reports/finna-scoped-release-package-20261121/manifest.json
   ```
   Confirm `rollout_authorized: false`, all 9 launch/cleanup flags default to
   `false`, and zero forbidden paths appear.
2. **Verify local frontend build:** `cd web && npm run build` passes cleanly (never
   compile on Oracle).
3. **Fresh paired backup & key continuity:** take a fresh paired Oracle backup
   before draining writers; verify the age-encrypted original-key archive and its
   second-location SSH-identity backup (`~/.ssh/id_ed25519`).
4. **External & owner gates (before enabling any flag):**
   - Qualified legal/tax review (invoice fields, GST threshold confirmation,
     remaining retention schedules for shared/public/support/log/backup data).
   - Real Resend mail delivery test (reopen link & support mailbox
     `hruaitluangasailo20@gmail.com`).
   - Razorpay test-mode webhook, renewal cancellation, and partial/full refund
     reconciliation before `RAZORPAY_CHECKOUT_ENABLED=true`.
   - Physical Android TalkBack focus/speech and release-device acceptance.

## Controlled Bundle A cutover sequence (when separately authorized)

1. **Drain every writer on Oracle (`ubuntu@152.67.31.231`):**
   - Stop `ism-paper-documents.service`, `ism-paper-publisher.service`, and
     `ism-oracle-bank-review.timer`; wait until `ism-oracle-bank-review.service`
     is inactive.
   - Stop `ism-api.service` during the schema + paired code switchover.
   - Confirm zero active application/worker writers in `pg_stat_activity`.
2. **Apply Bundle A migrations in exact order** (`0116`, `0117`, `0119`, `0120`
   if unapplied, `0121`, then `0122`–`0134`), each inside its own transaction,
   skipping `0110` and excluding `0111`–`0115` and `0118`.
3. **Deploy only the manifest-bound files** (staged API files, `api/requirements.txt`,
   paired `scripts/bank-review-worker.py`, read-only restore/replay operators, and
   locally built `web/dist/`). Never rewrite shared `/etc/caddy/Caddyfile`.
4. **Restart services with all new flags OFF** (`AUDIENCE_GATE_ENABLED=false`,
   `STUDY_HISTORY_RETENTION_ENABLED=false`, `PRIVATE_STUDY_RETENTION_ENABLED=false`,
   `PRIVATE_PREFERENCES_RETENTION_ENABLED=false`, `RAZORPAY_CHECKOUT_ENABLED=false`,
   `REFERRAL_REWARDS_ENABLED=false`, `STUDY_DESKS_PRIVATE_ENABLED=false`,
   `ACCOUNT_MAIL_ENABLED=false`, `REVIEW_DIGEST_ENABLED=false`).
5. **Post-deploy verification:**
   - Verify **both** `https://study.hawayu.in` and `https://family.hawayu.in` return
     HTTP 200.
   - Check `/api/health` and `/admin/bank/reward-diagnostics`.
   - Confirm `ism-paper-documents.service`, `ism-paper-publisher.service`, and
     `ism-oracle-bank-review.timer` are healthy.
   - Only after separate per-flag approval, enable flags one at a time (draining
     writers before any `AUDIENCE_GATE_ENABLED` transition).

## Controlled rollback & restore reconciliation

- **Code rollback:** restore the previous `/srv/api` and `/srv/study/public`
  artifacts while **retaining** the applied `0116`–`0134` schema, purge completion
  markers, and immutable audit tables (`account_audience_events`,
  `privacy_request_events`, `account_security_events`). Never drop purge markers
  or claim old receipts cover newly purged tables.
- **Database restore:** before promoting any restored backup, quarantine copied
  credentials, run the read-only preflights (`check-restore-privacy.py`,
  `check-restore-billing.py`, `check-restore-retention.py`,
  `check-restore-private-study.py`), and reconcile authoritative closure/hold/erasure
  decisions with `scripts/replay-restore-erasure-decisions.py`.
