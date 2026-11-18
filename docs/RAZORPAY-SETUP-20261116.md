# Finna Razorpay setup — 16 November 2026

## Installed test environment

- Merchant website `https://study.hawayu.in/feed` is approved in the Dashboard.
- Test API keys were generated with the owner's confirmation. An authenticated
  read of the Razorpay Plans API succeeded. No live API keys were generated.
- Hostinger A record `finna-test` points to `152.67.31.231`, TTL 300.
- HTTPS test webhook: `https://finna-test.hawayu.in/api/billing/webhook`.
- Razorpay Test Mode shows the webhook **Enabled**, with all ten subscription
  lifecycle events plus `payment.captured` and `payment.failed` (12 events).
- Separate root-owned Caddy snippet `/etc/caddy/sites/finna-test.caddy` forwards
  only that webhook. Other paths return 404. The shared Caddyfile is untouched.
- Service: `finna-razorpay-test`, listening only on `127.0.0.1:8011` on Oracle.
  It runs a billing-only application, without importing production workers.
- Database/role: `finna_paytest`; schema copied without account/content data.
  One explicitly synthetic test account was added. No live accounts were copied.
- Root-only server secrets: `/etc/finna-razorpay-test.env` (0600). Test keys and
  the separate webhook secret also have private local backups outside Git under
  `~/.local/share/finna/credentials/` (directory 0700, files 0600).
- The temporary uploaded key file was removed after server installation.

## Opening the private checkout

Run:

```sh
ssh -NT -o ServerAliveInterval=15 -o ExitOnForwardFailure=yes \
  -L 127.0.0.1:8011:127.0.0.1:8011 ubuntu@152.67.31.231
```

Then open `http://127.0.0.1:8011/`. Only this SSH tunnel exposes the test checkout.
Do not forward the whole test API through the public Caddy site. The page uses a
synthetic, unprivileged account and prominently identifies Test Mode. Its session
expires after seven days; renew only the isolated test session when needed.

## Verification so far

- Existing deferred-billing tests: **4 passed** on a disposable local database.
- Isolated API health confirms `test_mode:true` and `isolated_database:true`.
- An invalid webhook signature returns HTTP 400.
- Public test `/` and `/api/billing/config` both return HTTP 404.
- The test checkout created a ₹99 monthly subscription and opened Razorpay's
  test payment form using the official subscription test card.
- The first simulated bank redirect timed out. Finna displayed failure and the
  real Razorpay `payment.failed` webhook was received, with no paid entitlement.
- Retrying in the same checkout with Razorpay's documented synthetic OTP flow
  succeeded. Server-side verification and provider state both show `active`.
  The isolated account is `pro/active` with a current paid period, exactly one
  captured ₹99 receipt and one subscription. Provider-delivered webhook receipts:
  `payment.failed`, `payment.captured`, `subscription.authenticated`,
  `subscription.activated` and `subscription.charged`.
- The test page's cancel-renewal request returned successfully and retained the
  current active paid period. The future terminal cancellation event has not been
  awaited; the provider's list/fetch still shows `active`, as expected before
  period end. Do not claim a completed terminal cancellation from this check.
- Frozen acceptance receipt:
  `../reports/razorpay-setup-20261116/receipt.json`; screenshot:
  `../reports/razorpay-setup-20261116/test-payment-success.jpg`.
- Production checkout still reports `enabled:false`. Live study API health and
  the family site both passed following the Caddy reload.

Before any live launch, finish webhook redelivery, terminal subscription
cancellation, expiry and checkout-reopening cases. In particular, inspect checkout
resumption after abandonment and a new purchase after terminal subscription
states: the current checkout rejects any existing linked subscription. Generate
separate live keys/webhook only when live activation is explicitly chosen. Never
copy test provider IDs or synthetic rows into the production database.

## Evidence and sources

Screenshots: `../reports/razorpay-setup-20261116/` (no secrets).

- https://razorpay.com/docs/payments/subscriptions/test/
- https://razorpay.com/docs/payments/payments/test-card-details/
- https://razorpay.com/docs/webhooks/setup-edit-payments/

The test card page documents a random 4–10 digit test OTP for success. The first
bank redirect failed; the later retry succeeded. No user cancellation confirmation
was needed for the first attempt after Razorpay timed it out automatically.

## Launch preparation follow-up

- Fixed checkout resumption: an unpaid `created` subscription for the same plan
  is reused. A per-account transaction lock serializes concurrent checkout calls.
- Provider-confirmed `cancelled`, `completed` or `expired` subscriptions permit a
  new purchase. Nonterminal mandates still block a second subscription; a delayed
  old webhook cannot overwrite the new account link.
- Limited yearly subscription count to the provider's 100-year maximum (100
  yearly cycles rather than the invalid 120). Monthly/six-month counts remain120.
  Source: https://razorpay.com/docs/api/payments/subscriptions/create-subscription/
- Disposable-database billing suite: **13 passed**, including duplicate delivery,
  retry after rollback, terminal-state repurchase, and concurrent checkout.
- Installed only the updated router in the isolated test service, with a backup
  at `/srv/finna-razorpay-test/app/routers/billing.before-next-20261116.py`.
- The real provider Test API immediately cancelled the synthetic paid mandate.
  Its `subscription.cancelled` webhook arrived and changed the test account to
  `free/cancelled`. A subsequent test purchase created a new unpaid mandate;
  reopening checkout reused that exact mandate. No additional test payment made.
- This supersedes the earlier unverified terminal-cancellation limitation. Actual
  provider expiry over elapsed time and provider-dashboard manual redelivery were
  not performed; application handling is covered by synthetic integration tests.
- Production billing remains unchanged and `enabled:false`; both public sites
  are healthy. Live-mode Dashboard is at the approved site's Generate Key button.
  Live keys have not been generated; action-time credential approval is pending.

## Live configuration prepared

The owner generated the live keys in Razorpay and reported completion. The
one-time secret dialog was still open, so the pair was saved privately without
regenerating it. Authenticated live Plans API access succeeded.

- Live credentials and a distinct live webhook secret are installed in the
  existing `/etc/mpsc/db.env` (root,0600). Local private backups are outside Git
  under `~/.local/share/finna/credentials/razorpay-live*.json` (0600).
- Live Dashboard webhook `https://study.hawayu.in/api/billing/webhook` shows
  **Enabled ·12 events**. No real payment was performed or claimed.
- The tested billing router is installed in production. The bounded installer
  `scripts/install-razorpay-live.py` checks the exact previous router hash,
  preserves the prior root environment/router, and restores them on health failure.
  Successful rollback directory: `/root/finna-billing-backup-bb2mqe0h`.
- All three live plans were created through the existing server plan helper and
  fetched back from Razorpay to verify INR amount, period and interval: ₹99 monthly,
  ₹449 every six months, ₹799 yearly. Production has3 provider plan references,
  zero subscriptions/payments/webhook receipts; no test rows/provider IDs copied.
- Temporary uploaded credential JSON files were removed. Shared Caddy and
  systemd unit files were not modified. Both public sites are healthy.
- `RAZORPAY_CHECKOUT_ENABLED=false` and public billing config `enabled:false`.
  Final owner choice to enable real customer checkout is pending, as required by
  the activation guide. Disabling this flag later does not cancel paid mandates.
- Evidence: `../reports/razorpay-setup-20261116/live-prepared.json` and
  `../reports/razorpay-setup-20261116/live-webhook-enabled.jpg`.

The first real payment and its live provider delivery require the owner to perform
an actual checkout. The simulated test acceptance does not prove a live charge.

## Owner-corrected price policy and access controls

The owner corrected pricing to ₹100/month, then specified ₹50/month for selected
people and the ability to grant extra days. Monthly checkout is now the only new
purchase option. Historical ₹99, six-month and yearly provider references remain;
no old provider record, paid mandate or receipt was rewritten.

- Production and Test Mode both have distinct ₹100/month and ₹50/month plans,
  created/fetched through the versioned plan helper and verified against Razorpay.
- Owner-selected rates use `billing_account_rates`; public visitors see ₹100.
  The server derives the checkout amount from the authenticated account. A price
  change during checkout forces a refresh. Existing mandates retain their price.
- Admin → Rewards & accounts includes Monthly price & extra Pro days. Search an
  existing account by email, select ₹50/₹100, or grant1–3650 extra days per action.
  The existing global-owner, CSRF, staff MFA and write-limit checks remain intact.
- Extra-day records are immutable and idempotent, stack after existing trial,
  paid, reward and granted periods, and are included by `account_has_pro`.
  Provider cancellation cannot revoke a separate valid grant. Extra days neither
  create payments nor move provider renewal dates; the UI explains this.
- All27 billing/owner-access/reward tests passed. Frontend build passed.
- `0089_owner_billing_access` was rehearsed against a full production dump clone.
  Existing account access fingerprints and bank counts were unchanged. Only this
  migration was applied; unrelated pending migrations were not run.
- Bounded four-router release and frontend deployment passed both-site health.
  Paired API/web/database backup: `/root/finna-owner-billing-suy2t3ca`.
- Actual isolated TEST API checked ₹100 and ₹50 checkout amounts, account isolation,
  reopening reuse, seven-day manual access, and retry deduplication. These were
  synthetic test accounts only; no payment made during this pricing rehearsal.
- Production has zero account-rate overrides, zero manual-day grants, zero
  subscriptions and zero payments. The owner has not identified discount recipients.
- Checkout remains disabled pending launch choice under the corrected price policy.
  No real charge has been made or verified.
- Live owner browser check: the new admin panel rendered and exact-account lookup
  returned the expected price and both rate controls plus the extra-days form.
  Read-only lookup only; no rate/day grant changed in production. Captured
  `../reports/finna-owner-billing-20261116/owner-controls-live.jpg` and the public
  monthly plan screenshot; left the blank account finder open for the owner.
