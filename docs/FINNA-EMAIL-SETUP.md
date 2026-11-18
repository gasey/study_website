# Finna email delivery and built-in automation

18November2026. Resend free tier is the selected implementation target after the
owner requested Google authentication or a free email tier. Google sign-in and
email delivery solve separate jobs. No provider account, domain verification,
credentials or sending have been activated by this work.

Finna owns the existing encrypted durable account-mail outbox and background
worker (`api/app/services/account_mail.py`). Verification/reset requests queue
one-use30-minute links; delivery retries are bounded. The provider transports the
message. Opt-in review digests need their own consent, one-click unsubscribe,
IST-day dedup and empty-queue rules before activation. Finna owns their consent
and delivery receipts.

## Provider setup

1. Create/use a Resend account and verify an actual sending domain using the exact
   DNS records shown by that account. Keep account credentials/API keys private.
2. Create a sending key and place it only in the server's existing root-only
   `/etc/mpsc/db.env`, alongside the settings below. The sender must belong to the
   domain actually verified. The placeholders are not a live mailbox or a key.
3. Keep sending disabled while validating the selected sender, DNS and delivery
   through a controlled owner test. Do not rotate the existing encryption key.
4. Enable account mail only after an actual verification and one-use recovery flow
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
day. Production sending still needs the verified domain and private key. Finna
currently has no SMTP host/sender/key configured and sending is disabled; the
read-only running-process audit is in
`reports/finnaplan-v11-readiness-20261118/provider-status.json`. No test email has
been sent. The V.11implementation adds shared conservative daily/monthly reservations,
recovery priority, bounded stable-key retries, account/token rechecks, quota-aware
request admission and a worker heartbeat. Deployment status is recorded in reports/finnaplan-v11-mail-20261118/README.md. SMTP
acceptance is distinct from inbox delivery; an actual recovered account after
delivery remains a launch gate. Future digest/referral jobs must use this same
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
