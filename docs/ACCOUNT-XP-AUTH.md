# Account, XP and leaderboard operations

Implementation: 29 October 2026. Release evidence: reports/account-xp-hardening-20261029. Original design: plans/XP-LEADERBOARD-AUTH-SOL-6.1.md. Migration0056–0059 are additive; applied migrations must never be edited.

## Identity and learner workflow

Public study remains available to guests. A server-generated 256-bit credential in the Secure, HttpOnly, SameSite=Lax `ism_guest` cookie now owns guest history. Only its hash is stored. `X-Device-Id` remains accepted for compatibility but cannot read, write or adopt another guest's history. New protected guests use random `guest_*` principals, never a caller-supplied `dev_*` identity. Legacy unproven device histories are retained in the database and are not automatically assigned to a new account. Signed-in histories are unchanged.

Sign-in/join preserves a validated same-origin `next` destination and exam filters. If this protected guest has practice answers, the form offers an unchecked transfer choice. A successful account login stays successful if transfer fails, and displays a separate notice. Transfer uses a locked one-use proof and immutable receipt; a retry by the same account returns the receipt, while another account receives409. No retrospective guest XP is awarded.

Transfer inventory:

| Records | Policy |
| --- | --- |
| Attempts | Transfer mutable user ownership; preserve scoring snapshot and immutable assessments; exclude answers in an active guest mock that conflicts with the account's active mock |
| Mock sessions | Transfer completed sessions and a nonconflicting active session; a conflicting guest session remains with the retired guest |
| Exam bookmarks | Merge set membership |
| Exam and learning checkpoints, module progress, essay drafts | Resolve natural-key collision by latest server `updated_at`; account wins exact timestamp ties |
| Vocabulary state/cards and daily revision | Account-only workflows; no guest transfer and no reassignment of immutable receipts |
| Posts, votes, reports, materials, notifications, creator/study-desk records | Excluded; authenticated authorship/membership is not proven by browser guest possession |
| Sessions, MFA, staff grants, billing, rewards and entitlements | Never transferred |

An adopted guest credential cannot read the retired principal. Logout clears both cookies so another person on a shared device starts a new guest session. Unknown legacy data stays retained; there is no public UUID-based manual claim operation.

`account_identity.account_session` is the shared account resolver used by optional identity and staff review identity. Expired account cookies may browse public pages, but intended account mutations return401 instead of silently recording to a device user. Session status supplies a CSRF value for an expired cookie so explicit logout can clear it. UI distinguishes sign-in-required errors from genuine expiry by checking current session status; a guest or network outage never becomes a false “session expired” notification. Continue as guest is an explicit choice.

Cookie-authenticated mutations require exact configured Origin and session-bound CSRF. Login, register, reset request/complete and email-token confirmation instead perform strict pre-auth Origin validation. `/api/games/preview` remains a read-only POST. Existing role and recent-MFA guards remain in force. Response caching defaults private/no-store for APIs; existing intentional public calendar reads keep their explicit policy.

The frontend bootstraps session/guest identity once before concurrent personalized reads. It shows a loading status, bounds the bootstrap to8seconds, coalesces calls, rejects stale API/review responses after account changes, remounts account-scoped workspaces, and reloads other tabs on a credential-free storage notification. Private wallet/placement responses never enter shared public caches.

## XP and receipts

The reward writer remains the database function and its existing triggers/game integration. No browser award endpoint was introduced. Canonical first-reward claims and the shared300XP/India-day study/game budget remain unchanged. Exam marks, publication credit, reward points and access entitlements remain separate.

Practice answers accept `Idempotency-Key` (16–100characters). Same account/key/body returns the immutable original response and creates one attempt; changed body/scope/question rejects409. A replay still returns the original result after a key correction. The frontend sends a unique key for each submitted answer. A later explicit repeat is a new attempt but cannot mint another canonical reward.

Answer responses add `reward`: status, XP/point delta, receipt ID and rule version. Status explains awarded, already rewarded, daily cap, guest, unofficial evidence, incorrect or otherwise ineligible. Both question details and shared question/practice cards show feedback. Mock/game award scheduling retains the existing submitted-result behavior and global claim contract; no new per-question result API was added there.

Ledger metadata marks existing receipts `legacy-v1`; new receipts carry `learning-v1`, mechanically linked attempt IDs, and material archive reversal references. Existing immutable rows and balances are not rewritten. Contribution events remain traceable by their existing unique event keys and credit records. Wallet responses include source breakdown, next India reset, daily remaining and level floor. Existing level thresholds are preserved: Level1 is0–159XP and Level2 starts160XP.

## Leaderboard and owner support

`/board` remains opt-in, default month, and includes existing learning/publication XP. It is MPSC activity, not exam rank. Equal XP shares dense rank; immutable internal account IDs stabilize ties without entering public responses. Responses include explicit India period bounds, snapshot time, total independent of page rows, and caller-only public placement. Private/zero/negative scores have no public placement. Opt-out removes public visibility immediately without a board cache.

Admin → Rewards & points contains read-only reconciliation and account lookup. Requires global owner grant. Diagnostics count claims/receipt mismatches, over-cap days, wallet debts, legacy metadata, and pending/failed/expired mail; account lookup returns bounded receipt/security history. It never repairs records or grants points. Existing audited catalog controls remain separate and disabled offers stay disabled.

For an incident: inspect the receipt and original source/claim, check effective entitlement and security events, then decide whether an explicit compensating event is justified. Never delete/rewrite immutable ledgers or grant inferred official answer provenance. Report-only reconciliation is not authority to repair balances automatically.

## Recovery and verification: installed, mail disabled

Routes: `/account/recovery`, `/api/auth/recovery/status`, `/recovery/request`, `/recovery/complete`, `/email/request`, `/email/confirm` (API paths under `/api/auth`). Account security shows verification and session controls. Existing accounts are not automatically marked verified or blocked from access/rewards.

Tokens are random, hashed, purpose-bound, single-use and expire after30minutes. Request responses are generic when delivery is configured. Recovery invalidates all active sessions and reset tokens, preserves MFA enrollment, and requires an unused authenticator/recovery code when MFA is enabled. It never logs the user in automatically. Password change rotates the retained session and revokes other sessions. The session list exposes opaque IDs and dates, never cookie tokens/hashes; revoke operations are account-bound and audited.

The durable mail outbox stores its token encrypted with the existing configured MFA encryption key, reusing account-bound encryption. Worker runs every10seconds, uses row locks/SKIP LOCKED, TLS SMTP with10second connection timeout, at most5attempts while link is valid, and stores exception class only. Successful delivery clears the encrypted token. A crash between SMTP acceptance and commit may resend the same single-use link; it cannot reset twice. Failed/expired unsent rows are visible in diagnostics. No email addresses or tokens are emitted in application metrics.

**Production sending is off.** Required settings, placed in the existing protected systemd environment configuration:

- `ACCOUNT_MAIL_ENABLED=true` only after controlled acceptance.
- `SMTP_HOST`, `SMTP_PORT` (default587; STARTTLS), `SMTP_FROM`.
- `SMTP_USERNAME`, `SMTP_PASSWORD` when required by provider.
- Existing valid `MFA_ENCRYPTION_KEY` and exact `PUBLIC_ORIGIN`.

No credentials belong in the repository or reports. Do not enable sending merely because the routes exist. Configure a trusted delivery account, verify sender/domain requirements, authorize a controlled real delivery test, inspect failures, and then enable learner mail. Until then UI/status honestly says unavailable. Automated acceptance covers token consumption, expiry, replay, MFA preservation, generic requests and encrypted queue construction; it does not prove external inbox delivery. No production reset/verification emails were sent during this implementation.

## Release and rollback

Backups: `/tmp/account-xp-api-before-20261029.tgz`, `/tmp/account-xp-web-before-20261029.tgz` on the server. Migrations rehearsed on a dump clone; build locally and upload only selected API files/static output. Retain additive schema and immutable history on rollback. Restoring the old auth code would reintroduce legacy device adoption, so prefer a forward fix or disable affected mutation routes while investigating rather than reverting identity protection blindly. Old open frontend tabs may receive403 and should refresh to obtain the new CSRF client.

Check `/api/health`, public exam/topic routes, anonymous board pagination, recovery availability, ledger baseline fingerprint, owner unlimited entitlement and family.hawayu.in after the API restart. Do not create synthetic production learners, XP, rankings or resets for acceptance. Use the disposable local fixture for those workflows. Query timings from a few live reads are smoke evidence, not a representative load-test p95 guarantee.
