# Accounts and billing

21 November owner update: invoice/contact address is **A/77, Chanmari, Aizawl,
Mizoram, India**, for Hruaitluanga, an individual trading as Finna. The private
legal drafts and local About/Contact/Privacy previews include it. Invoice/tax
review, policy publication/effective date and actual provider acceptance remain
separate; checkout remains disabled.

## Privacy and launch preparation — 20 November 2026

The owner confirmed **Hruaitluanga, an individual trading as Finna**, with support
at hruaitluangasailo20@gmail.com. Refund eligibility is any reason within seven
days of the relevant charge; the owner selected no fixed refund-support response
deadline. This does not waive applicable mandatory deadlines or initiate refunds.

Local `/account/privacy` provides owned request receipts/withdrawal and an owner
queue at `/admin/privacy`, linked from Operations. Request status changes do not
execute erasure, payments or identity verification. `/policies/about` and its
linked pages are working launch previews without an effective publication date.

Migration0122 and the default-off `AUDIENCE_GATE_ENABLED` foundation are local only.
The flag blocks study access until adult declaration; minor enrollment remains
unavailable because no real guardian verifier or child-processing launch decision
exists. Existing ages are not inferred. Retention/backup schedules, real guardian
verification, invoice/tax details, scoped deployment/public policy publication and
actual payment/refund/reconciliation checks remain. Checkout stays disabled.

## Local refund-status reconciliation draft — 21 November 2026

Integrity follow-up: the combined billing/privacy/recovery regression now passes
125 tests, including actual `mpsc` role execution. The draft checks the fetched
payment's charged amount/currency/capture state, prevents changes to established
refund identity/history, and keeps a refund retryable when its charge has not
arrived yet. Event receipts are reserved before effects so concurrent deliveries
with the same event ID apply at most once. Ending subscription access also requires
a bounded paginated refund list whose processed amounts equal the entire charge;
pending/failed portions cannot end access. [Follow-up receipt](../reports/finna-refund-integrity-followup-20261121/README.md).

Unapplied migration 0132 adds per-payment refund aggregates and a refund-reference
ledger. Signed refund webhooks for known payments fetch the current Razorpay refund
and payment state before recording pending, processed or failed status; partial
and full aggregate states are retained. The owner-only billing account endpoint
returns the latest payment/refund references without provider notes or card data.
No refund-creation API is called by Finna. Only a processed full refund confirmed against
the current payment ends that subscription's access; separate grants remain. The
draft does not cancel provider renewals, and no Razorpay webhook subscription is
configured. Verify the refund/cancellation workflow in provider test mode before
launch. Synthetic
tests: `api/tests/test_billing_deferred.py` and
`api/tests/test_owner_billing_access.py`; receipt:
`reports/finna-billing-refund-reconciliation-20261121/`. The broader local
billing/account-retention/export/restore regression passes 98 tests.

See [guardian plan](FINNA-GUARDIAN-PLAN.md), [policy drafts](FINNA-LEGAL-DRAFTS.md)
and reports/finna-privacy-implementation-20261120/.

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

## Current delivery and launch status — 19 November 2026

Resend is configured for `study.hawayu.in`. Account email, verification and
self-service password recovery are enabled. The owner completed a delivered
recovery link, password reset and new-password sign-in. Opt-in evening review
email is also deployed; each verified account must subscribe explicitly.
See [email setup and delivery evidence](FINNA-EMAIL-SETUP.md).

Paid checkout remains disabled. Legal pages and actual provider launch checks
must be completed before activation. Referral access is being staged locally
behind `REFERRAL_REWARDS_ENABLED=false`; it does not enable paid checkout.

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
