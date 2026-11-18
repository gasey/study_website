# Razorpay — prepared for later activation

Checkout is deliberately disabled by default, even when keys are present.
No merchant account was created, credentials installed, plan/subscription
created, payment made or webhook registered during this task.

## Activate in a separate test environment first

1. In the owner's Razorpay Dashboard, use **Test mode** and generate its API key
   pair. Use a separate staging database/API; test subscriptions must not grant
   access in the live service. Confirm Subscriptions is enabled for that merchant.
2. Place secrets in a root-owned mode-0600 server environment file, never in the
   app, `EXPO_PUBLIC_*`, Git, screenshots or chat. The API currently reads the
   existing systemd environment files; add these entries there through the
   operator's normal secret-management process:

   ```ini
   RAZORPAY_CHECKOUT_ENABLED=false
   RAZORPAY_KEY_ID=replace_with_test_key_id
   RAZORPAY_KEY_SECRET=replace_with_test_key_secret
   RAZORPAY_WEBHOOK_SECRET=replace_with_separate_webhook_secret
   ```

3. Register `https://STAGING_HOST/api/billing/webhook` in the Dashboard's Test
   mode. Subscribe to `subscription.authenticated`, `subscription.activated`,
   `subscription.charged`, `subscription.pending`, `subscription.halted`,
   `subscription.cancelled`, `subscription.completed`, `subscription.paused`,
   `subscription.resumed`, `payment.captured` and `payment.failed` where offered.
   The webhook secret is separate from the API secret. Deliver the original raw
   JSON body with its `X-Razorpay-Signature`; do not reserialize it before checking.
4. Inspect `GET /api/billing/config`: it must still return `enabled:false`.
   Switch the test server's `RAZORPAY_CHECKOUT_ENABLED=true`, restart the API,
   and verify `enabled:true`. The mobile app keeps payment secrets server-side
   and uses the secure website checkout rather than embedding payment collection.
5. Test success, cancelled/failed checkout, double taps, signed-callback mismatch,
   wrong-account verification, duplicate/delayed webhooks, provider timeouts,
   cancellation at period end, reward/trial overlap and entitlement expiry.
   Confirm exactly one payment receipt and correct access after re-delivery.
   Webhook effects and their deduplication receipt now commit together; a failed
   processing attempt remains retryable. Provider state is fetched to handle
   out-of-order subscription notifications. `authenticated` alone grants no
   active paid period. Test data never serves as a production payment receipt.
6. For live activation later, complete the merchant's Dashboard requirements,
   review the configured prices and applicable mobile-store billing rules, then
   install the **Live** API keys and a distinct live webhook secret in production.
   Use the live endpoint `https://study.hawayu.in/api/billing/webhook`.
   Do not reuse test-mode provider IDs or database rows. Keep the checkout flag
   false until test acceptance is recorded and the owner chooses to enable it.

Current prices are ₹100/month, or ₹50/month for owner-selected accounts. New six-month and yearly checkout is retired. These are current
code settings, not approval to charge anyone. No paid entry, prize payout or
material purchasing is added. Changing prices after provider plans have been
cached requires a versioned plan migration; do not silently reuse an old plan ID.

Disabling the checkout flag stops new checkouts; it does not cancel an existing
subscription. Keep valid webhooks and account status reads running while handling
existing subscribers. No activation/deactivation script prints secret values.

Primary references checked 15 November 2026:
[Subscriptions integration](https://razorpay.com/docs/payments/subscriptions/integration-guide/),
[Test subscriptions](https://razorpay.com/docs/payments/subscriptions/test/),
[Webhook validation, duplicates and ordering](https://razorpay.com/docs/webhooks/validate-test/).
