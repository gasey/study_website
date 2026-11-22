# Finna age eligibility — 18+ only

Owner decision, 20 November 2026: **“just dont do below 18.”** Finna is for
people aged **18 or over**. This supersedes the earlier request to include
under-18 students. Guardian enrollment, verification providers, parental consent
and minor feature design are removed from the current launch scope. The old
[guardian proposal](FINNA-GUARDIAN-PLAN.md) is retained as historical work.

## Current implementation

The local age boundary admits an explicit adult declaration. It is a declaration,
not identity verification. No date of birth or identity document is requested.
An anonymous under-18 choice does not create a learner account. Existing accounts
must confirm their own category; a browser choice cannot overwrite an existing
under-18 declaration. Email confirmation, Google identity or payment is not proof
of age. Incorrect declarations need a reviewed correction process, without an
automatic account upgrade through support-request completion.

Local registration, Google provisioning, guest progress and native authorization
have adult-admission guards when the policy is enabled. Restricted existing
accounts retain privacy requests, supported export, recovery, session revocation
and closure controls. New guardian requests are no longer offered or accepted.
Previously recorded guardian receipts retain their retry, review and withdrawal
history; they cannot enroll anyone or grant study access. No history is deleted
or existing user classified as an adult by this decision.

The age selector, audience notice, join/sign-in copy and policy previews now state
the 18+ rule, without promising future guardian access or inviting under-18 users
to use public study material. The adult-only rule does not establish that no child
can visit a public URL or that the server collects no request/security metadata.
Existing or accidentally supplied under-18 data still needs appropriate privacy
handling; it is not a reason to erase audit/economic history directly.

## Before activation

- Review the age declaration/correction procedure and handling of existing unknown
  or under-18 accounts. Do not automatically grandfather existing accounts as adult.
- Rehearse the complete guarded release: current API, trusted publisher and
  migrations 0122–0129, with every writer drained during the policy transition.
  Check email/Google/guest/native paths, stale/revoked sessions and background work
  with the enabled policy. Do not deploy the whole dirty checkout.
- Validate the paired web and native browser sign-in return, adult confirmation,
  under-18 rejection and continued privacy/closure access against the exact release.
- Bind published 18+ terms/privacy versions after retention and other legal/payment
  fields are settled. Public policy previews are still drafts.

**Production audience/age policy and other launch flags remain off.** Migrations
0122–0129 remain unapplied in production; 0130 is unreserved. This local scope
change does not activate a flag, deploy, infer ages, create a new APK or require a
phone. Retention/recovery, invoice/tax/refund/provider acceptance, physical Android
and the existing human/content/healthy-week/volume gates remain in
[the remaining plan](FINNA-REMAINING.md).

[Implementation and validation receipt](../reports/finna-adult-only-policy-20261120/README.md).
