# Site moderation admin

`/admin/moderation` is the owner-only console for the V3 moderation queues.
It adapts the review-queue interaction pattern from the ShikshaCom admin app
to this FastAPI/PostgreSQL service and the V3 visual design.

## Access

The console uses a separate bearer token. `X-Device-Id` is not authentication
and is never accepted for moderation. The API reads `ADMIN_TOKEN` from the
process environment, compares it in constant time, and returns 503 while the
secret has not been provisioned. The browser keeps the entered token in
`sessionStorage` for the current tab session only.

On the production host, the secret belongs in the root-owned, mode-0600
`/etc/mpsc/admin-token.env`, loaded through an `ism-api.service` systemd
drop-in. It must not be committed, put in Vite variables, or copied to the
public web root. The local provisioned copy is `.admin-token` at the repository
root; it is gitignored and mode 0600.

## Queue behavior

- **Reported:** aggregate open conduct reports by post. Hide marks open reports
  upheld; dismiss marks them dismissed. A post hidden automatically by the
  abuse-report threshold is restored only when its reports are dismissed and
  it has no explicit moderator-hide metadata.
- **New users:** approve a held first post, or reject and hide it with a note.
  Publishing is blocked while conduct reports remain open.
- **Appeals:** only a different moderator can decide an appeal. Granting an
  appeal lifts its active sanction; denial requires a note.
- **My actions:** append-only `mod_actions` entries expose eligible reversals.
  Undo restores the captured post/report or appeal/sanction state and writes a
  new `restore` action referencing the original.

The migration adds the state snapshot column and action names needed to retain
reversal history. Moderation does not change question answers, keys, attempts,
or scores. Volunteer moderator scopes and multi-person identities are a later
stage; this first console is site-owner access only.
