# Legal-page working drafts — updated 21 November 2026

**Private repository drafts. Owner-selected business terms are recorded below;
the complete policies are not published. Legal/paid-checkout gates remain closed.**
Replace every `[[…]]` field and settle the choices below before implementing
published policy pages. These drafts describe the implemented product; they are
not a certification of legal or tax compliance.

## Recorded owner decisions — 20–21 November 2026

The owner supplied **Finna** as the public operator/name, **hruaitluangasailo20@gmail.com**
as the monitored support address, and a **seven-day refund request window**.
The owner then explicitly chose **refunds for any reason within seven days of the charge**
and **no fixed refund-support response deadline**. The owner later changed the
audience from under-18-with-guardian to **18+ only**; the earlier audience is superseded.
The owner subsequently confirmed **Hruaitluanga, trading as Finna — individual**
as the operator/invoice identity. This supersedes the earlier uncertain
“finna or hruaitluanga idk” answer. The owner later stated they are **not
GST-registered**. On 21 November the owner supplied **A/77, Chanmari, Aizawl,
Mizoram, India** for invoices and public contact/policy pages. Invoice/tax wording
and qualified tax review remain open.
The owner delegated the post-refund access choice; the selected draft treatment
is that a provider-confirmed full refund ends access from that subscription,
while unrelated active grants remain. Local migration 0132 and signed-webhook
reconciliation now record current partial/full payment aggregates and pending/
processed/failed refund status. Full-refund access handling is local and unapplied;
real provider event/status behavior and test-mode reconciliation/cancellation
remain to be validated. No provider renewal is automatically cancelled by the
refund webhook.
These are supplied business decisions, not verification of the support mailbox or of
tax registration or provider onboarding. No message has been sent to the mailbox.
On 20 November the owner changed the audience to **people aged 18 or over only**
(“just dont do below 18”). This supersedes the earlier under-18 choice; guardian
enrollment is no longer a launch requirement. The remaining fields below still
prevent complete policy publication and paid launch.

## Owner decisions and remaining fields

| Field | Needed value |
| --- | --- |
| Public operator | Hruaitluanga, an individual trading as Finna — explicitly confirmed by the owner |
| Monitored support | hruaitluangasailo20@gmail.com — owner-supplied monitored support; receipt/reply handling has not been tested |
| Public contact channel | hruaitluangasailo20@gmail.com; A/77, Chanmari, Aizawl, Mizoram, India — owner-supplied support and postal contact address |
| Refund eligibility | Any reason, requested within seven days of the charge — explicitly selected by the owner |
| Refund handling | No fixed support response deadline — owner selected. Provider processing estimate is separate; mandatory obligations are unaffected |
| Audience/age policy | **18+ only**, explicitly selected by the owner. No guardian enrollment. Guarded rollout and existing-account/correction handling remain; see [adult-only plan](FINNA-ADULT-ONLY-PLAN.md) |
| Retention/requests | Owner selected study-history deletion 30 days after successful closure, with reopening allowed during the window and reopening before expiry cancelling pending deletion. Exact records/fields, secure recovery, exceptions/holds, backups, provider/log copies and retained audit/payment history remain open in [FINNA-RETENTION-PROPOSAL.md](FINNA-RETENTION-PROPOSAL.md); legal/accounting review remains required. This does not set backup expiry or financial/security retention |
| Invoicing/tax | Owner states not GST-registered, with principal place of business in Mizoram and PAN-wide annual aggregate turnover under ₹10 lakh. A 21 November 2026 check of official CBIC material found the ₹10 lakh Section 22 threshold for Mizoram and a matching threshold exemption for inter-State taxable services. CBIC's amended Act limits Section 24(x) e-commerce-operator registration to operators required to collect TCS; its FAQ says an operator does not collect Section 52 TCS on its own-account sales. On the stated facts, GST registration does not appear mandatory solely because Finna sells its own subscriptions online while aggregate PAN turnover stays below ₹10 lakh. This is an inference and assumes Finna supplies only its own services directly, is not collecting Section 52 TCS for other suppliers, and has no other compulsory-registration trigger; confirm the characterization, invoice wording and exceptions with a qualified tax adviser. Invoice/contact address: **A/77, Chanmari, Aizawl, Mizoram, India**, supplied by the owner on 21 November. `[[INVOICE_TAX_DETAILS]]` remains open |
| Full-refund access | Provider-confirmed full refund ends access granted by that subscription; unrelated active grants remain. Partial-refund/provider-status behavior requires validation |
| Effective date | `[[EFFECTIVE_DATE]]` after approval/publication |

The current [Razorpay website-review instructions](https://github.com/razorpay/markdown-docs/blob/master/payments/dashboard/account-settings/business-website-details.md)
ask for business/service and policy pages, website review and invoice material.
This is provider documentation, not a substitute for the operator's own policies.
Do not copy Razorpay's own subscription refund terms into Finna's policy.

### Invoice/contact issuer block — owner supplied, 21 November 2026

Hruaitluanga, trading as Finna (individual). Address: **A/77, Chanmari, Aizawl,
Mizoram, India**. Support: hruaitluangasailo20@gmail.com.

The address is now filled in the private drafts and local About/Contact/Privacy
previews. This does not issue an invoice, publish the policies or settle tax
wording. The publication effective date remains tied to the reviewed release.

### GST source check — 21 November 2026

This is a limited source check, not tax advice. The [CBIC copy of CGST Act
Section 22](https://cbic-gst.gov.in/hindi/CGST-bill-e.html) gives the ₹10 lakh
threshold for supplies from special-category States such as Mizoram and defines
aggregate turnover across a PAN on an all-India basis. The [CBIC amended Act
(Section 24)](https://cbic-gst.gov.in/pdf/CGST-Act-Updated-31082021.pdf) reflects
the amendment limiting Section 24(x) registration to e-commerce operators
required to collect TCS. [Notification 10/2017 –
Integrated Tax](https://cbic-gst.gov.in/hindi/pdf/integrated-tax/10_2017_IT.pdf)
provides a matching ₹10 lakh threshold exemption for inter-State taxable
services. The [official Notification 65/2017 – Central Tax](https://www.gstcouncil.gov.in/en/node/3992)
provides a ₹10 lakh exemption for qualifying service suppliers using an e-commerce
operator required to collect TCS. CBIC's [e-commerce FAQ](https://cbic-gst.gov.in/hindi/sectoral-faq.html)
says Section 52 TCS is collected for other suppliers when an operator collects
their consideration, not for the operator's own-account sales. Applying that
rule to Finna's own digital subscriptions is an inference; the exact supply/payment
structure and all
compulsory-registration exceptions still require tax-adviser confirmation.
Until then, do not represent Finna as GST-registered or collect GST unless the
owner obtains registration; have a tax adviser confirm the correct receipt/invoice
wording for the unregistered period.

## Terms — product text ready for review

Finna, available at study.hawayu.in, is operated by Hruaitluanga, an individual trading as Finna.
Contact hruaitluangasailo20@gmail.com for account or service questions. Postal contact:
A/77, Chanmari, Aizawl, Mizoram, India. These terms take
effect on `[[EFFECTIVE_DATE]]`.

Finna provides study questions, past-paper references, practice, review tools and
community features. Answer labels distinguish official keys, verified answers,
worked solutions and explanations. Provisional, disputed and unscored material
keeps its displayed limitations. Study progress and mastery displays are study
aids and do not certify exam readiness or guarantee an examination result.

Keep your account credentials private. Use an email address you can access and
use the security controls to review sessions, recover access or add an
authenticator. Finna is for people aged 18 or over. Do not register or use study
features if you are under 18. Guardian enrollment is not offered. Contact support
about an existing account, an incorrect age declaration or personal data. A support
request does not grant study access. Local adult-admission controls still require
a guarded rollout; do not present them as active in production before validation.

Community posting and sharing must follow the site's displayed community rules.
Private desk material is shared only through the room and sharing settings you
choose. Submit material only when you have permission to share it; source and
reuse notices remain attached to content. Moderation can limit or hide content
under the applicable community process.

New accounts receive a seven-day, no-card Pro trial. The trial itself does not
charge a payment method. Paid checkout is currently unavailable. Before any
paid launch, the site must display the actual offered monthly price and recurring
payment terms before purchase. The current planned standard price is ₹100/month;
selected eligible accounts may have an assigned ₹50/month rate. Do not describe
either as a universal discount or a purchased subscription before checkout is live.

When paid subscriptions are launched, Plan & billing provides cancellation.
Cancellation requests stop renewal through the provider's confirmed cancellation
flow; access already paid for remains through the applicable access period.
Extra granted/earned access does not change a provider's renewal mandate.
Refunds follow the separately published cancellation/refund policy.

`[[OPERATOR_APPROVED_SERVICE_CHANGE_AND_DISPUTE_TERMS]]`. This section still needs
the operator's decisions; no liability waiver, governing forum or legal promise
has been selected for them.

## Privacy — factual implementation inventory and draft text

Finna's operator is Hruaitluanga, an individual trading as Finna; privacy requests can be sent to
hruaitluangasailo20@gmail.com. Effective date: `[[EFFECTIVE_DATE]]`.

The service stores the account email, handle and optional profile fields,
authentication/session records, study answers and progress, selected exams and
focus subjects, saved notes/calendar entries, community submissions and sharing
choices. It also keeps security, moderation and economic/access audit records.
Some display/profile information can be made public through explicit creator or
leaderboard visibility settings. A public post can be visible beyond its author.

Cookies support signed-in sessions and guest progress. Browser preferences and
local state support the interface. Finna stores password hashes rather than
plaintext passwords; account and recovery capabilities are protected and are not
included in the account's downloadable data export.

Email verification, recovery and opted-in evening review mail use Resend. Email
delivery requires the recipient address and the relevant message content.
Evening review reminders are off by default and can be withdrawn from the account
or the reminder's unsubscribe link without signing in. Referral access receipts
in the staged implementation use the account Inbox, without additional outbound
referral email.

If you choose Google sign-in, Google handles its authorization flow and Finna
records the resulting verified identity link. Planned paid checkout uses Razorpay;
Finna's billing records store payment/subscription references and status rather
than card numbers. Checkout remains disabled until the launch prerequisites pass.

The API and database run on Oracle-hosted infrastructure. The deployed website
includes Google Fonts resources; loading them causes the browser to contact
Google's font servers. The browser necessarily sends network request information
to servers it contacts. Optional links to WhatsApp, Google Calendar, source sites
and older lesson pages open the selected destination when used.

The [privacy inventory](FINNA-PRIVACY-INVENTORY.md) records the reviewed production
sources, backup behavior and remaining hosting/log/provider questions. The deployed
Atlas asset reachable from the current entry page includes OpenStreetMap tile
URLs; using that base map can send requests to the tile provider. Local Atlas/Studio
extensions remain staged. This source review does not measure actual browser
traffic. Confirm the complete provider list before publication; no country-only
storage promise is made.

Account tools allow users to download their own supported records, review/revoke
sessions and request account closure once stated blockers are resolved. Closure
removes account credentials/profile identifiers and withdraws sharing under the
implemented tombstone process. It does not erase immutable access/economic and
moderation history or automatically remove all text previously posted in public.
Transient cleanup is bounded and periodic. Some records have cleanup thresholds;
other study, audit, security and payment records currently have no automatic expiry.
The paired backup job includes the workflow database and does not automatically
prune its backups. Closing an account does not remove existing backup copies.
`[[RETENTION_AND_REQUEST_POLICY]]` must settle the purpose and retention of each
remaining category, backup expiry, restore handling and privacy-request procedure.
The code's current absence of expiry is an implementation fact, not an approved
indefinite-retention policy.

## Cancellation/refunds — facts and selected draft treatment

Support: hruaitluangasailo20@gmail.com. Operator: Hruaitluanga, an individual trading as Finna.

The seven-day no-card trial does not charge automatically. Paid plans are not
currently sold through the site. Once launched, subscription cancellation will
be available from Plan & billing. The implemented API requests cancellation at
the end of the current billing cycle, preserving already-paid access. Confirm
the resulting provider status before reporting cancellation as complete.
Razorpay separately documents [subscription cancellation options](https://github.com/razorpay/markdown-docs/blob/master/payments/subscriptions/pause-resume-cancel.md).

Cancellation and refund are separate actions. The owner has selected a
request-based refund for any reason within seven days of the charge. The current
Finna cancellation endpoint does not issue or submit a refund; it only requests
the provider's end-of-cycle cancellation flow. Do not describe cancellation as
a refund or promise an automatic refund.

After a **provider-confirmed full refund**, access granted by the refunded
subscription ends. Other independently active grants remain. This treatment is a
policy decision for the draft; implement and test it only after provider status
semantics, partial-refund behavior, and the scoped launch plan are reviewed.

Owner-approved refund terms and remaining handling details:

For a paid Finna subscription, you may request a refund for any reason within
seven days of the relevant charge by emailing hruaitluangasailo20@gmail.com.
Include your account email and the payment or subscription reference so support
can identify the charge. Do not send passwords, OTPs or full card details.
This is a request-based policy; canceling renewal does not itself submit or
process a refund request.

Finna does not promise a fixed support response deadline for refund requests.
The seven-day deadline concerns when you submit the request, rather than when
support replies or the payment provider returns funds. Any applicable mandatory
consumer or privacy deadlines still apply; this choice does not waive them.
Provider processing starts after the refund has actually been initiated. The
current cancellation endpoint does not initiate a refund.


- Eligible cases: Any reason.
- Request deadline: Seven days from the relevant charge.
- Request channel and required non-secret transaction reference: hruaitluangasailo20@gmail.com.
- Support response target: No fixed deadline, as selected by the owner; separate
  from the request window and the provider estimate below.
- Receipt/invoice issuer: Hruaitluanga, an individual trading as Finna; A/77,
  Chanmari, Aizawl, Mizoram, India. Invoice/tax treatment: `[[INVOICE_TAX_DETAILS]]`.

### Provider processing reference — checked 20 November 2026

Razorpay currently describes normal refunds as taking about five to seven working
days after initiation, and returning to the payment method used for the charge.
This is a provider estimate, separate from Finna’s seven-day request window and
the owner's choice of no fixed support response deadline. Finna has not enabled or promised
instant refunds. [Razorpay refund documentation](https://razorpay.com/docs/payments/refunds).

The owner’s seven-day eligibility choice does not itself publish these pages,
verify a support inbox, execute a refund or enable checkout. The provider’s website
review still calls for About, Contact, Pricing, Terms, Privacy and Refund policy
pages plus a sample invoice. [Provider website-review requirements](https://github.com/razorpay/markdown-docs/blob/master/payments/dashboard/account-settings/business-website-details.md).

After decisions are supplied: implement the public terms/privacy/refund and
operator/contact pages, link them from signup/plans/checkout, bind the exact
published versions to the legal launch check, and validate the actual provider
test/live flow. No draft or configured flag alone should mark that work complete.

The current 18+ audience decision requires the [adult-only rollout plan](FINNA-ADULT-ONLY-PLAN.md),
not guardian enrollment. Historical implementation notes below retain their original scope.
The current draft does not certify child-account protection, legal identity,
invoice/tax status, retention compliance or a working refund operations process.

## Local implementation continuation — 20 November 2026

The repository now contains `/account/privacy`, an owner request queue at
`/admin/privacy`, and About/Contact/Terms/Privacy/Refund previews at
`/policies/about` and the linked policy routes. They are explicitly working
previews with no publication effective date. Request receipts record operator
review; they do not execute erasure, refunds or guardian verification.

The new local migration0122 and age boundary remain undeployed. The boundary
is off by default; when enabled, declared under-18 accounts cannot use study
features, and new under-18 enrollment remains unavailable until a real verifier
and permitted-processing review exist. Existing users are not assigned ages.
Retention schedules, provider verification, invoice/tax handling, final public
publication and actual payment operations remain launch work.


20 November operator follow-up: [private request, restore and refund procedures](FINNA-PRIVACY-OPERATIONS.md)
are now documented. The local read-only restore checker compares selected current
controls, requires candidate bearer/queued-mail quarantine, preserves immutable
send history and reports uncertainty for separate reconciliation. It does not
establish reference currentness, perform repairs, verify a guardian or authorize
promotion. Retention periods, permitted minor processing, legal/tax decisions and
real provider/mail acceptance remain open; no production change or message.
[Source-bound evidence](../reports/finna-restore-privacy-preflight-20261120/README.md).
