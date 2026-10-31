# Accounts and billing

The Claude v3 account flow is implemented with email and password sign-in,
HTTP-only server sessions, guest-progress adoption, a seven-day no-card Pro
trial, Pro subscriptions, billing management, and free-plan mock/practice
limits. Passwords use scrypt; session tokens are random and only their hashes
are stored. New accounts are not charged at the end of the trial.

## Configure Razorpay

Add these settings to `/etc/mpsc/db.env` on the server, then restart `ism-api`:

```ini
RAZORPAY_KEY_ID=...
RAZORPAY_KEY_SECRET=...
RAZORPAY_WEBHOOK_SECRET=...
PUBLIC_ORIGIN=https://study.hawayu.in
```

Use Razorpay test keys first. Configure the webhook URL as
`https://study.hawayu.in/api/billing/webhook` and subscribe to subscription and
payment events. The webhook secret is configured separately from the API key
secret. Once all three Razorpay values are present, the plan buttons open
Razorpay Checkout. Without them, checkout reports as unavailable and cannot
pretend to succeed.

## Supported plans

Pro recurring plans are ₹99 monthly, ₹449 every six months, and ₹799 yearly.
Razorpay creates/caches the provider plan IDs on first checkout. The class
plan is shown as unavailable because class administration is not implemented.
Free users receive 50 bank practice answers a day and one mock per calendar
month, and can view up to 20 mistakes in a daily review. Active Pro
subscriptions and unexpired trial accounts bypass those limits. Plan perks
beyond the current practice, mock, and mistakes entitlements should be added
only when the corresponding product feature ships.

## Current limitation

There is no configured email delivery service. Account signup and login work,
and signed-in users can change their password, but email ownership verification
and self-service password recovery are not available yet. Configure a mail
provider before advertising recovery or verified-email features. Until then,
users who lose their password need a support-assisted recovery.

## Manual access and extension availability — 28 October 2026

A trusted operator can grant non-expiring Pro using `plan_code='pro'`, `plan_status='active'` and `plan_ends_at=NULL` when there is no linked provider subscription. Record the explicit owner authorization and an immutable account security event, then verify `account_has_pro(id)`. Do not create a payment record or claim payment was received for a manual grant. Billing displays “Unlimited Pro access · no expiry date” for this state.

The site has provider subscription and earned-reward extension mechanisms, but live checkout is unconfigured and the Pro-week reward is disabled as of this date. There is no admin manual-access form yet; ordinary users cannot grant or extend their own access through an API shortcut. The owner's requested account was granted unlimited Pro during this session. No authentication or contributor quotas changed.
