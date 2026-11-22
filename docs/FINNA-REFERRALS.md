# Referral access — locally staged, 19 November 2026

Authority: FINNAPLAN §11 resolution 6, §13 #2 and V.11. Seven Pro days for each
account after the invited account reaches ten scored attempts; at most five
credited invitations per referrer in a rolling year. This is **not deployed**.
Draft migration `0121_referral_access.sql` is reserved; `0122` is next unreserved.
Applied `0110` and `0120` remain immutable; `0111`–`0119` remain local drafts.

`REFERRAL_REWARDS_ENABLED` defaults to `false`. Even when configured true, the
worker and signup attribution require the shared launch checklist: published
legal pages, successful delivered-email recovery, live paid checkout and matching
economy evidence/current diagnostics. The legal gate is currently closed. Do not
replace it with a test override in production or enable checkout to exercise this
feature. Native credentials have no new referral capability.

## Learner flow

A verified account explicitly creates a link in Profile. Its opaque code links
to `/join?ref=…`; Join explains the qualification and cap, and allows removal.
The optional code travels with email signup or the server-owned Google flow.
Only creation of a new account can attach attribution. Existing sign-in, Google
linking, guest adoption and later code submission cannot attach a referral.
Unavailable/revoked codes do not prevent signup. There is no award endpoint.

Both accounts must still have verified email and be open when qualification is
checked. Ten original official/key scoring snapshots must still be eligible under
the existing shared scoring rules, with correct/wrong assessed outcomes. Held,
unscorable, original inferred/derived, skipped, pre-signup/future, unsubmitted or
late mock attempts and active assessment disclosures do not qualify. Ordinary
practice keeps its ordinary rewards; referral qualification adds no XP or points.

The account-mail worker checks up to 25 pending claims per cycle after security
mail and the opt-in digest, in separate claim transactions. Account/cap/access
locks, unique claim/decision/grant keys and immutable receipts make replay safe.
Both access grants and the credited decision commit together. A failure before
the second grant rolls back the first. The database also enforces the five-credit
cap and matching two seven-day grants. Server timestamps govern the rolling year.
An invitation that hits the yearly cap receives a terminal `capped` result; it is
not reconsidered next year. Disabling a link stops future signups; existing valid
claims may still qualify. Closing either account prevents a pending credit.

Grants use existing `billing_access_grants`, `source='referral'`, seven days and
`granted_by=NULL` for the system action. Existing owner grants default to
`source='owner'` and retain their actor. Access stacks after trial, paid, redeemed
and granted access. No `users.plan_*`, Razorpay renewal dates, payments or currency
ledgers are modified. Account Inbox receives one private system receipt per party;
this implementation sends no additional referral email.

Private status exposes only the account's own invitation, qualification progress
and aggregate rolling-year credit count. It discloses no friend's identity, email,
answers or attempt IDs. Account export includes safe own referral/access history.
Closure disables its invitation and retains immutable audit/access receipts under
the existing account tombstone policy.

## Validation and operation

See [staging evidence](../reports/finna-referrals-staged-20261119/README.md).
Fixtures use disposable databases and synthetic identities; browser preview has
process-local fake launch readiness and no SMTP. Those overrides certify code
paths, not real paid launch, source review or human sign-off.

Reproduce focused checks from the repository root:

```sh
api/.venv/bin/python -m pytest api/tests/test_referrals.py api/tests/test_google_auth.py api/tests/test_account_tools.py api/tests/test_owner_billing_access.py api/tests/test_account_mail_automation.py api/tests/test_review_digest.py -q
node web/scripts/check-referrals.cjs /tmp/finna-submissions-renderer
api/.venv/bin/python scripts/prepare-referrals-economy-evidence.py --run-tests
api/.venv/bin/python scripts/rehearse-referrals.py
npm --prefix web run build
```

The renderer path must contain the existing React test-renderer dependency. The
clone operator checks applied migration hashes and skips them, including `0120`;
only unapplied drafts run in its temporary dump clone. It hashes every original
table's original columns before/after, rolls back its real-role probe, and removes
the clone/dump. It never changes production source/config/schema or starts workers.
Do not replay older digest rehearsals which assume `0120` is unapplied.

No referral deploy target exists yet. A future release needs a fresh frozen
scope, coherent source/evidence/schema package, migration rehearsal and recovery
operator. Pausing must retain access grants, terminal decisions and signup claims;
resume cannot backfill missing historical signups or reconsider capped claims.
The staged Desk/Atlas release still requires the actual healthy operations week.
