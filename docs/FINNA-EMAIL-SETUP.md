# Finna email delivery and built-in automation

19 November 2026. Resend is configured for the verified `study.hawayu.in` sender.
A sending-only key scoped to that domain is stored privately on the server. SMTP
authentication passed and the owner-approved recovery email was delivered.
The owner completed the password reset and signed in with the new password.
General account-mail sending is now enabled after a bounded API restart and
healthy checks for both hosted sites. Google sign-in and email delivery are separate.

Finna owns the existing encrypted durable account-mail outbox and background
worker (`api/app/services/account_mail.py`). Verification/reset requests queue
one-use30-minute links; delivery retries are bounded. The provider transports the
message. The opt-in review digest is now deployed with verified-email consent,
signed-out POST unsubscribe, IST-day dedup and empty-queue silence. Finna owns
consent and delivery receipts; existing accounts remain off until explicit opt-in.

## Selected domain — 19 November 2026

The owner selected **study.hawayu.in**. Active sender:
`Finna <no-reply@study.hawayu.in>`. The non-secret, disabled configuration is in
[finna-study-mail.env.example](examples/finna-study-mail.env.example); it is not
loaded into the running service. Do not replace the existing encryption key.

The initial read-only audit found mail disabled and no SMTP settings. After the
owner approved the exact DNS records and scoped credential, the three records
were saved in Hostinger and Resend verified the domain in Tokyo
(`ap-northeast-1`), with tracking and receiving off. Existing website records and
nameservers were preserved; no optional parent DMARC change was made.

`Finna <no-reply@study.hawayu.in>` and certificate-verified STARTTLS on port 587
are configured in the existing root-only `/etc/mpsc/db.env`. The key has Sending
access limited to `study.hawayu.in`; SMTP authentication succeeded. The private
transfer file was removed after successful server storage. The existing encryption
key and all non-mail settings were preserved. No code or service unit was changed,
and the API was subsequently restarted only to load the approved mail settings.

The owner explicitly approved one recovery email to their existing account. A
single controlled process used Finna's normal encrypted outbox, reservation and
send path while the running API and stored configuration kept general sending
disabled. Outbox 1 was accepted on attempt 1, its ciphertext cleared, and Resend
reports **delivered**. A receipt query failed after sending; read-only recovery of
the receipt confirmed success, without a second message. The owner must complete
the password change themselves; no password or recovery link belongs in receipts.
The owner subsequently completed recovery and signed in with the new password.
Server readback confirms the controlled token was consumed, zero live reset tokens
remain, and a fresh authenticated session exists after recovery. No additional
endpoint replay with a new password was attempted. General account mail was then
enabled; `/api/auth/recovery/status` reports `available: true`, and the API, study
and family sites returned HTTP 200.

Current non-secret evidence is in
`reports/finna-atlas-depth-staged-20261118/sender-server-configuration.json`,
`sender-controlled-recovery.json`, and `resend-domain-verified.png` /
`resend-recovery-delivered.png`. See [Resend verified domains](https://resend.com/docs/dashboard/domains/introduction)
and [SMTP settings](https://resend.com/docs/send-with-smtp), checked 19 November.

## Provider setup

1. Create/use a Resend account and verify an actual sending domain using the exact
   DNS records shown by that account. Keep account credentials/API keys private.
2. Create a sending key and place it only in the server's existing root-only
   `/etc/mpsc/db.env`, alongside the settings below. The sender must belong to the
   domain actually verified. The placeholders are not a live mailbox or a key.
3. Keep sending disabled while validating the selected sender, DNS and delivery
   through a controlled owner test. Do not rotate the existing encryption key.
4. Enable account mail only after actual sender verification and a one-use recovery flow
   succeeds. Record the result, including the replay/expiry behavior and sender.
   Checkout remains subject to its existing independent launch checklist.

```dotenv
ACCOUNT_MAIL_ENABLED=false
SMTP_HOST=smtp.resend.com
SMTP_PORT=587
SMTP_USERNAME=resend
SMTP_PASSWORD=PRIVATE_RESEND_SENDING_KEY
SMTP_FROM="Finna <no-reply@ACTUALLY_VERIFIED_DOMAIN>"
SMTP_DAILY_LIMIT=100
SMTP_MONTHLY_LIMIT=3000
```

The existing transport uses certificate-verified STARTTLS;587 matches that mode.
Do not set465 with the current STARTTLS-only client. No secret belongs in this
file, Git, chat, screenshots or diagnostic receipts. After a deliberate bounded
mail configuration change/restart, verify the API and both hosted sites using the
Oracle runbook. Do not rewrite Caddy or create an unrelated scheduled job.

## Free-plan limits and pending work

Verified18November2026: Resend free transactional tier is3,000emails/month and100/
day. The domain/key and controlled delivered email are now verified as recorded above.
General account sending is now enabled after actual recovered-account proof. The
initial disabled-state audit remains historical in
`reports/finnaplan-v11-readiness-20261118/provider-status.json`. The V.11implementation adds shared conservative daily/monthly reservations,
recovery priority, bounded stable-key retries, account/token rechecks, quota-aware
request admission and a worker heartbeat. Deployment status is recorded in reports/finnaplan-v11-mail-20261118/README.md. SMTP
acceptance is distinct from inbox delivery. The delivered-email/recovered-account
gate passed for this sender on 19 November; checkout retains separate launch gates. Future digest/referral jobs must use this same
capacity boundary rather than bypass it.

Sources checked18November2026:
[Resend pricing](https://resend.com/pricing),
[Resend SMTP prerequisites/settings](https://resend.com/docs/send-with-smtp),
[Google sign-in overview](https://developers.google.com/identity/gsi/web/guides/overview).
Alternative verified free tier: Brevo offers300sends/day, including transactional
email ([official plans](https://help.brevo.com/hc/en-us/articles/208589409-About-Brevo-s-pricing-plans)).
No paid plan, auto-upgrade or spending authorization is implied by this setup.

Finna counts every durable send reservation, including uncertain/failed attempts,
against100perUTCcalendar day and3,000over a rolling31days. The latter is deliberately
conservative across account billing reset dates. Request admission also accounts
for queued live links. These are Finna's own capacity controls; the provider's
account quota additionally includes any inbound mail or other apps using that
team. Verified source:[Resend account quotas](https://resend.com/docs/knowledge-base/account-quotas-and-limits).

## Authentication records — 19 November 2026

The owner approved and Hostinger saved exactly:

| Type | Host under hawayu.in | Value |
| --- | --- | --- |
| TXT | resend._domainkey.study | Exact public DKIM value in the DNS receipt |
| CNAME | rsend.study | rsend-apne1.forge.rmta.net |
| CNAME | send.study | send.forge.rmta.net |

TTL 3600. Exact public values are recorded in
`reports/finna-atlas-depth-staged-20261118/resend-domain-required-dns.json`.
Hostinger remains authoritative (`artemis.dns-parking.com`,
`hermes.dns-parking.com`). Resend's authenticated dashboard reports Verified and
Forge Ready. Domain verification and provider delivery do not certify that the
owner has successfully recovered the account; the separate completed recovery/
sign-in proof is in `sender-recovery-completion.json` and activation/readback is
in `sender-activation.json`.

## Opt-in review digest — deployed 19 November 2026

Profile and `/account/email-preferences` let verified users choose reminders.
The live owner account currently shows Off and requires email verification in
Account security before enabling. No subscription was created on the owner's
behalf. Reminders include only the current eligible due count, study streak and
Smart Review link. They send between18:00–22:00 IST, at most one committed attempt
per account/date; uncertain transmissions are not retried into possible duplicates.
Empty queues, stale consent/address, closed accounts, held questions and current
assessment embargoes suppress delivery. Opt-out bypasses subscription throttling.

The existing mail worker and shared capacity budget are used. Default digest
headroom preserves10 daily/100 rolling-month attempts for security mail; pending
security links have priority. Anonymous immutable digest reservations count even
if cancelled/uncertain, including after private preference/outbox closure cleanup.

Messages carry HTTPS `List-Unsubscribe` and `List-Unsubscribe-Post` headers. The
body link uses the retained API landing page so it survives restoration of an
older frontend. GET is inert; an opaque-token POST performs withdrawal without
cookies. Uvicorn redacts that URL's query. Header protocol source:
[RFC8058](https://www.rfc-editor.org/rfc/rfc8058), checked19November. Actual first
opted-in inbox delivery and DKIM coverage of these headers are not certified by
synthetic tests; no test digest was sent to a real account.

Only0120 was applied in this growth release; staged Desk/Atlas remain excluded.
Current scope/proofs and copied recovery operator are documented in
`reports/finna-review-digest-withdrawal-20261119/README.md` and the Oracle runbook.
To withdraw the feature keep compatible API/capacity readers and schema/history,
disable only REVIEW_DIGEST_ENABLED, and use the guarded matching backup. Never
restore an older shared capacity reader over digest reservations.
