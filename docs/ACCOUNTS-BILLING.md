# Accounts and billing

The Claude v3 account flow is implemented with email and password sign-in,
HTTP-only server sessions, guest-progress adoption, a seven-day no-card Pro
trial, Pro subscriptions, billing management, and free-plan mock/practice
limits. Passwords use scrypt; session tokens are random and only their hashes
are stored. New accounts are not charged at the end of the trial.

## Configure Razorpay

Add these settings to `/etc/mpsc/db.env` on the server, then restart `ism-api`:

```ini
RAZORPAY_CHECKOUT_ENABLED=false
RAZORPAY_KEY_ID=...
RAZORPAY_KEY_SECRET=...
RAZORPAY_WEBHOOK_SECRET=...
PUBLIC_ORIGIN=https://study.hawayu.in
```

Use Razorpay test keys first. Configure the webhook URL as
`https://study.hawayu.in/api/billing/webhook` and subscribe to subscription and
payment events. The webhook secret is configured separately from the API key
secret. All three values plus an explicit `RAZORPAY_CHECKOUT_ENABLED=true` are
required before plan buttons open Razorpay Checkout. Keep it false for deferred
activation; follow [the test-first setup guide](RAZORPAY-LATER.md). Without them, checkout reports as unavailable and cannot
pretend to succeed.

## Supported plans

Pro is ₹100 monthly. The owner can assign ₹50/month to selected registered accounts. New six-month and yearly checkout is retired; old provider references and subscription history remain intact.
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

## Owner prices and complimentary days — 16 November 2026

In Admin → Rewards & accounts, use **Monthly price & extra Pro days**. Find the
registered account by email, choose ₹50/month or restore ₹100/month, and enter
extra Pro days when desired. Prices apply to the next new subscription; existing
Razorpay mandates retain their agreed rate. No customer can select a discounted
price through checkout parameters. Anonymous visitors see ₹100/month.

Extra days stack after existing trial, paid, reward or granted access. They never
charge money, spend reward points, or change Razorpay's renewal date. Cancel an
existing renewal separately if charges should stop. Complimentary access survives
provider cancellation and expires at its recorded end. Existing unlimited manual
access needs no extension. Writes retain the existing owner, CSRF and MFA checks
and record actor-bound audit events; repeated grant requests reuse an operation key.

Provider plans are versioned by currency and price. The old ₹99 reference remains
immutable; ₹100 and ₹50 use distinct new references. Checkout stays disabled until
the owner chooses live activation using this corrected price policy.

## Account self-service — 17 November 2026

V.5 now deploys Profile's grouped controls, owned read-only JSON export, sign out
everywhere and recent-auth/MFA/owner-version/typed-confirmation account closure.
Staff access, owned open shared desks and unconfirmed recurring billing block
closure. Cancel renewal using the existing billing controls first; account closure
does not call Razorpay or pretend to cancel a mandate. Password editing now lives
in Account security. Email recovery availability remains governed by actual mail
configuration and delivery, not the presence of these controls.

Closure removes private identity/planning/credentials and sharing while preserving
anonymous immutable posts/audits/ledger and learning history. Closed accounts
cannot regain identity, credentials, shared-desk ownership/membership or Pro access,
including through later provider-state updates or manual plan-column changes.
Compatibility recovery retains those SQL protections.0097 is applied/immutable.
See reports/finnaplan-v5-recovery-20261117/README.md. Checkout/catalog activation
remain disabled pending their actual launch prerequisites.

## Bulk group prices — deployed18November2026

Use **Admin → Rewards & accounts → Group monthly prices**. Preview up to100
emails with one batch note, then explicitly add the previewed list. Only verified
email ownership applies a match; pending users match after actual verification
and successful login. Applications are once-only. Removing/re-enabling an entry
controls future matching; an applied account price is retained. Restore ₹100 using
the existing individual account-price tool when that is the intended change.

Alternatively create a group code (defaults100uses/30days; bounds1–1000/1–90), then
share its displayed link yourself. A signed-in member must explicitly claim it on
Plan & billing. The code changes only a future new subscription price, charges
nothing and grants no access/points. Existing renewal prices stay unchanged.
Revocation/cap/expiry stop new claims; prior assignments/receipts remain. Replaying
a claim never reverses a later manual price change. Search retained emails/codes
by email, code or note; View claim receipts provides cursor-paged owner history.
No phone-number matching is supported. Checkout and email sending remain disabled
until their independent real-provider launch gates are satisfied.

Evidence: `reports/finnaplan-v11-bulk-20261118/README.md`;0109 is immutable. Recovery
retains the current compatible API/schema/history, pauses new bulk matching and
restores prior static. Never restore older pricing/auth/review writers.


## Owner account overview — 18 November 2026

`/admin/users` offers private, read-only registered-account search and a combined
account/access/study/wallet/community overview. Global-owner permission and the
existing staff MFA policy apply. Exact email or literal handle prefix (3+ chars)
finds up to20matches; narrowing is explicit. This page links to Rewards & accounts
for price/extra-day changes and to the review queue for moderation. It grants no
access or discounts itself. Entitlement matches `account_has_pro()`; future grants
are labelled scheduled. Activity and study are aggregates, with no individual
answer browsing, private desks, authentication secrets or block identities.
