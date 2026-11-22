# Finnaplan — learning, points, desk and community design

22 November IST — Part VII added on owner direction; document only, no code
or production state touched. The owner, reading the built site, reported it as
confusing and asked for module-by-module simplification. Part VII (§VII.0–VII.16)
is a subtraction document: 93 route declarations across ~88 paths reduced to a
~40-route target, seven hand-synced navigation surfaces to one generated
manifest, practice and mock merged into one `/practice` with a timer toggle
(reversing §4.4), the four mega-menus and `/more` deleted in favour of a new
`/index`. It adds the three content systems the plan never had: a first-party
**Guides** library recovering ~43 MB of authored content from 29 standalone
india-study-map modules (kept separate from user **Materials**), **question
currency** built on the two migration-0078 fields that shipped empty
(`bank_paper_profiles.period`, `time_behavior`), and **explanation voice** —
which requires provenance columns first, since `appearances.explanation` is
plain TEXT with no `model`/`prompt_version`, making the owner's "easily remove
them" currently impossible to query. Also: a typography system (the document
had none — 14px base, 21 arbitrary sizes, three fonts referenced but never
loaded), the layout contract taken from `india-study-map`'s 89-line
`combined-prelims.css`, written/essay/LDE questions as display-only (8,176
written questions; 289 LDE papers ingested and unreachable), and §VI.6 /
§VII.11, the keyboard-first authoring console Part VI omitted.
**One owner premise was corrected on the evidence**: official keys are 13,417
of 82,383 (16.3%), not "not many", and `v_scorable` is what mocks, mastery,
rewards and games stand on — so §VII.6 collapses the five-label learner
vocabulary to two and strips the badge from trusted answers, rather than hiding
the pool, which §0.2 already forbids ("provenance is a display property, not a
visibility filter"). Microservices, Kubernetes and WebSockets are declined with
reasons (§VII.13.1); one SSE endpoint replaces one 12-second admin poll.
Amendments recorded in place at §0.12, §13.1, §V.13 and Part VI. Nothing in
Part VII is implemented.

Same day, owner clarification — *"because some official keys are wrong"* —
added **§VII.6.2/§VII.6.3** (phase V.17) and, on a second request,
**§VII.16** (database work, phase V.18). The clarification is correct and
better than the scarcity argument: migration 0021 already disputes 8 wrong
keys in one paper, and `reports/assistant-2018-paper2-adjudication.md` records
210 UDC/LDC/Assistant disagreements. Reading `answer_comparison.py` against
migration 0032 surfaced the real defect: the two answer lanes are
reconstructed from **publication manifests, not columns**, so a question whose
column holds the official key while an applied `mode='verified'` +
`preserve_official_key` publication disagrees with it ("Shape B") stays inside
`v_scorable` and **scores on an answer the site's own reviewed working says is
wrong** — behind a green "Official key" badge, with the conflict visible only
inside a collapsed panel. `v_reviewed_answer_publications` cannot find these
(it requires `answer_source='derived'`), and `relation='disagree'` is computed
per question at read time, so **the population has never been counted**.
§VII.6.2 adds a third learner label (**Answer disputed**, always visible),
treats un-adjudicated conflicts as out-of-scoring on detection, and keeps
0021's rule that a key is never overwritten. §VII.6.3 gives the matview, the
`/admin/ops` count, seven automation jobs — including a **cluster gate** (more
than five conflicts in one paper means a page-offset transcription fault, not
five wrong keys) — and AI pre-adjudication as draft-only, never a verdict.
§VII.16 takes the opposite tack: it treats the **rejected** 20 November
optimisation (2.95% over 480 timed runs) as the acceptance bar, names the two
still-open measured shapes (collection counts at 1–1.6 s; an empty-pins branch
scanning 79,288 questions 45 times to return zero rows), and leads with the
one zero-risk item — a test proving the `answer_status` CASE, which exists in
three hand-synced copies, agrees across all 82,383 rows. All §VII.17
owner decisions are now locked in (first guides batch, merged free tier,
Study Desk scope & split, and the Shape B conflict count as Step 1 of V.17).

21 November IST — scoped release package and Bundle A standalone migration proof.
`scripts/build-scoped-release-manifest.py` and
`docs/FINNA-SCOPED-RELEASE-RUNBOOK.md` split the local checkout into Bundle A
(18 migrations: `0116/0117/0119/0120/0121` + `0122–0134`, 99 manifest-bound
files including paired `bank-review-worker.py` and restore/replay operators;
excluding immutable `0110`, Desk v4 `0111–0115`, Atlas seed `0118` and one-shot
scripts) and Bundle B (`0111–0115`, `0118`, gated after a real healthy week).
All 9 launch/cleanup flags verified default-off; `test_scoped_release_manifest.py`
passes 2/2 (proving Bundle A applies cleanly on isolated PostgreSQL without
Bundle B); local `web/` build passes (412 modules, 13.58s). `rollout_authorized`
is `false` and production is untouched.
Report: `reports/finna-scoped-release-package-20261121/`.


21 November IST — private preferences retention, erasure-decision replay and
audited 18+ age-declaration correction staged locally. New migration 0134 adds
a separate completion marker (`private_preferences_purged_at`) and bounded
cleanup for `user_calendar_preferences`, `inbox_preferences`, `inbox_desk_reads`
and `game_preferences` (`creator_blocks` stays excluded as a safety boundary).
It requires 30-day closure grace, both 0131 and 0133 completion markers and no
active hold; all three worker flags default off. Four active-account write guards
block post-close recreation and app-role marker forgery is rejected. Migration
0134 also adds append-only `account_audience_events` (immutable via
`review_immutable()`, no DOB/ID/free-text PII), logs self-declarations, and
adds owner-only `POST /api/account-privacy/admin/audience-correction` requiring
an `in_review` `correction` privacy request, recent owner auth, CSRF, staff MFA
when enforced and exact version, while forbidding grandfathering unknown accounts
as adult. New `scripts/replay-restore-erasure-decisions.py` exports a zero-PII
SHA-256-verified closure/hold/erasure ledger, verifies drift read-only, and
replays holds, closures and real bounded sweepers onto an isolated quarantined
candidate without forging purge markers or authorizing promotion. 170 isolated
PostgreSQL tests across 10 focused suites pass (including 24 new cases) in
138.76s. Earlier migrations (0001–0133) and frozen receipts are untouched; 0134
is unapplied in production and all launch/cleanup flags remain off. No
production connection, restart, mail, payment, policy publication or phone
action. Procedure: `docs/FINNA-PREFERENCES-RETENTION-AND-REPLAY.md`.
Report: `reports/finna-preferences-retention-replay-20261121/`.


21 November IST — private writing and saved-link retention staged locally.
New migration 0133 adds a separate completion marker and bounded cleanup for
essay_drafts, user_question_bookmarks, material_bookmarks and user_calendar_saved.
It requires the original study cleanup to finish, a still-closed account past
30 days and no active study hold. Both worker flags default off; enabling the
private flag alone cannot run cleanup. Earlier 0131/0132 sources/receipts remain
unchanged. Four active-account write guards prevent post-close recreation; the
app cannot forge the new marker. No broader table grant or public policy change.
A separate read-only 0133-aware preflight compares seven exact controls. The
246 selected regressions pass, including 41 new cleanup/restore cases, plus
calendar/mobile/audience/reopen/hold/key regressions. The isolated restored clone
preserves all 273 tables / 2,687,970 original rows and
65 sequence counters; all old functions/columns/FKs/triggers survive.
Only the new column, two functions and five triggers are added. Migration does
not sweep real records; rollback-only synthetic holds/batches/retries/other-owner/
closed-write cases pass. Seven restore comparisons pass. All three temporary clones
were removed; the three prior evidence/recovery copies remain. Cluster STOPPED.
0133 is unapplied in production, as are the prior staged launch migrations;
no production connection, provider, restart, policy publication or phone operation.
Current code preimages preserve prior frozen bindings. New local proposal covers
four private relation families; other preferences/shared/provider/log/backups,
final currentness/decision replay, separate key/identity copy and rollout remain.
Report: reports/finna-private-study-retention-20261121/.
Procedure: docs/FINNA-PRIVATE-STUDY-RETENTION.md. Never replay one-shot operators.


21 November IST — deletion/hold and original encryption-key recovery checks.
New read-only scripts/check-restore-retention.py compares every account closure/
purge marker, all protected hold fields and complete reopen envelopes without
changing roles or exporting IDs/values. Both saved-snapshot candidates pass all
three controls; mpsc remains unable to inspect or edit holds. Restored schema
metadata covers 273 tables/20 views, 2,450 columns, 458 FKs (174 user/31 selected
study-root references) and 165 non-internal triggers. Four hold types, release,
expiry, grace window and idempotent cleanup pass with synthetic rollback-only
rows. All test-clone values/schema/65 counters and the source preview survive.
108 focused tests pass, including 34 new cases. The initial synthetic closure
fixture omitted contribution_public=false and was corrected; initial failure
receipts remain. The two disposable check databases were removed, not the three
prior evidence/recovery databases. Cluster is STOPPED; production cleanup remains off.
Owner reports no known independent key backup. Live key matches root-only mfa.env;
its one saved pending-MFA ciphertext decrypts with correct account binding. A new
age-encrypted original-key backup on this computer was restored in a fresh process
without plaintext files/chat/report output. Wrong identity/tampering are rejected.
It requires ~/.ssh/id_ed25519; do not delete that identity. A separate identity
backup and second location remain unverified. Other saved cipher families are
empty and tested synthetically. No production write, restart, mail or payment.
Selected study cleanup is not complete erasure: essay drafts, individual bookmarks,
shared/provider/log/backups and other unselected locations remain separate review.
Procedure: docs/FINNA-DELETION-KEY-RECOVERY.md.
Report: reports/finna-deletion-key-recovery-20261121/. Never replay one-shot operators.


21 November IST — local full-copy recovery completed against the saved snapshot.
A third private database, finna_recovery_preview_20261121, copies the complete
newer reference, preserving 273 public tables / 2,697,411 rows before quarantine.
All 9489 accounts match in every field; 21 privacy and 8 billing projections pass.
Retired 7 web sessions, 1 mobile session and 9441 guest credentials only in the
preview. All ten quarantine counts are zero. All other table values, schema and
65 sequence counters are preserved; both original evidence databases remain unchanged.
The old workshop bank did NOT match the newer DB. A separate read-only SSH capture
now recovers the matching bank generation and canonical/source/served PDFs,
figures, private workbench and registered documents. 141,461 unique files are hash-
verified, with no reference gaps in the explicitly checked source scope. Original
mismatch/error receipts remain unchanged. No production DB/application write,
publisher, heartbeat, mail, payment, release or phone operation occurred.
Cluster is STOPPED. This finishes the local snapshot rehearsal, not final source
currentness, service/key recovery, controlled cutover or public-launch acceptance.
Owner supplies invoice/contact address A/77, Chanmari, Aizawl, Mizoram, India;
private drafts and local policy previews updated; web typecheck/build pass.
Report: reports/finna-full-copy-recovery-20261121/. Never replay old operators.


21 November IST — account restore blocker diagnosed. All 8,811 shared accounts
match in every stored field. The newer snapshot has 678 additional open accounts
without email, each with one guest credential; no accounts exist only in the older
copy and no shared account changed. The 174 direct account references have no other
linked rows for the additions; the app-protected hold table was separately checked
read-only and is empty in both copies. The aggregate diagnosis does not cover
indirect/provider references or final currentness. A concrete repair plan prefers
a complete current paired restore; any additive preview must use a third isolated
copy and a reviewed delta without importing credentials. No repair was executed,
production is unchanged, both preflights remain blocked and the cluster is stopped.
16 new diagnosis scenarios and the existing privacy regression pass 60 tests.
Plan: `docs/FINNA-RESTORE-REPAIR-PLAN.md`.
Receipt: `reports/finna-restore-account-diagnosis-20261121/`.

21 November IST — financial/access restore comparison. A separate read-only
operator now checks stored plan/trial/subscription inputs, full-refund access-end
markers, payment/refund/webhook receipts, account rates and owner/referral/earned
grants. Explicit columns fail closed when the staged refund schema is absent.
The retained clones match seven billing/grant projections; all users' access
inputs still differ (9,489 vs 8,811 rows), so both billing and privacy restore
checks remain blocked. Quarantine counts remain zero. The private cluster is
stopped again; there was no new production connection, repair, migration or
provider action. The earlier reference is point-in-time evidence, not a final
cutover reference. Receipt: `reports/finna-restore-billing-preflight-20261121/`.
The 32 new restore scenarios plus selected existing billing/privacy tests pass 129
cases; runtime billing and the original privacy checker remain unchanged.

21 November IST — actual local paired-backup/current-reference rehearsal. A spare
disk supplied a private socket-only PostgreSQL cluster, now stopped. The selected
paired backup and an independently read production snapshot both restored, and
124,996 workshop files plus the bank/database pair hash verified. The first 0131
attempt exposed absent Atlas tables; clean reruns applied schema dependencies
0116/0117/0119/0121 before 0122–0132, without the 0118 content seed or feature
activation. All original values in 252 tables per database were preserved through
those migrations. A rolled-back synthetic `mpsc` retention smoke removed personal
practice while keeping reward and multiplayer evidence. Local credential retirement
cleared all ten quarantine counts. Promotion remains blocked because current and
backup user controls differ; no identity records were rewritten to force a pass.
Production writers stayed live and no production write occurred. Final cutoff,
current-state repair/deletion reconciliation, provider/key/source recovery and
release acceptance remain. Receipt: `reports/finna-local-restore-rehearsal-20261121/`.

21 November IST — refund reconciliation integrity follow-up. The 0132 local draft
now validates the fetched payment's charged amount, currency and captured state,
preserves immutable refund identity/history, and reserves each webhook receipt
before applying effects. A refund arriving before its payment stays retryable.
Before ending access, a bounded paginated provider read must confirm processed
refunds add up to the entire payment; pending or failed portions cannot end access.
Tests use the actual `mpsc` role and cover missing permissions, malformed payloads,
concurrent duplicate event IDs, pagination and old-subscription refunds. The combined
billing/account-retention/export/restore regression passes 125 tests. This remains
local and unapplied; checkout/provider activation, renewal cancellation, release
and legal gates remain. Receipt: `reports/finna-refund-integrity-followup-20261121/`.

21 November IST — local billing refund-status reconciliation draft. Razorpay
refund webhooks now fetch the current refund and payment for a known captured
payment, validate their IDs/currency/amounts, and record pending/processed/failed
refund status plus partial/full payment aggregates. The existing owner-only billing
account view exposes recent payment and refund references. The 26 focused billing
tests pass, and the broader billing/account-retention/export/restore set passes 98,
including partial/full, failure/pending, duplicate delivery, unknown-payment and
retry-after-provider-mismatch cases. This is an unapplied 0132 draft: only a
processed full refund confirmed against the current provider payment ends that
subscription's access, while separate reward/access grants remain. The code does
not issue refunds or cancel provider renewals, and no Razorpay webhook is configured;
real provider behavior and full-refund cancellation workflow still need test-mode
validation. Receipt:
`reports/finna-billing-refund-reconciliation-20261121/`.

21 November IST — HTTPS staging hostname follow-up. The owner-added DNS name
`finna-staging.hawayu.in` resolves to `152.67.31.231`; the host validates its
Let's Encrypt certificate for that name (valid through 17 February 2027). The
staging page displays its synthetic-data warning, and `/api/health` reports
`status=ok`, 1,000 questions and 1,000 scorable questions. This is an
unauthenticated reachability/TLS check from the workspace, not a full Android,
mail, checkout or production test. The dedicated QA emulator reached ready state,
but Android System UI and launcher became unresponsive before Chrome displayed
the page; the AVD was stopped with its data retained. No Finna app or account
was used. Receipt:
`reports/finna-staging-https-check-20261121/`.

21 November IST — official-source GST threshold check for the owner-reported
Mizoram business. CBIC Section 22 states the ₹10 lakh special-state threshold;
Notification 10/2017 exempts qualifying inter-State service suppliers below
₹10 lakh; Notification 65/2017 covers qualifying small service suppliers using
an e-commerce operator required to collect TCS. CBIC explains its own-account
website sales do not attract Section 52 TCS for other suppliers. On the stated
facts, Finna selling only its own subscriptions with PAN-wide aggregate turnover
below ₹10 lakh does not appear to require GST registration solely for online
sales. Applying the own-account TCS explanation to Finna is an inference; verify
service classification, payment flow, turnover and all exceptions with a
qualified tax adviser before publication or checkout. No GST status or invoice
settings changed. Source notes are in `docs/FINNA-LEGAL-DRAFTS.md`.

21 November IST — mobile answer timing emulator acceptance. A signed staging preview
completed one synthetic answer on the dedicated API36 Android emulator: 198 ms
tap-to-response, split into 15 ms durable receipt write and 183 ms API round trip;
the server answer handler took 92.7 ms. The UDC wrong-answer filter reduced 1,000
synthetic questions to 3 and showed the attempted question. The module, study-status,
answer-status, subject, topic and year controls were visible in the native filter
sheet. This is one emulator sample, not physical-device certification. The synthetic
account was signed out and the emulator stopped with data retained. APK build
`eccfcd09-4911-4358-8f40-dd5a680525d5` is staging-only; its SHA-256 and package/cert
identity are in `reports/finna-answer-timing-20261120/validation.json`. Physical
TalkBack focus/speech and broader hardware/network sampling remain. No production
change. Timing receipt: `reports/finna-answer-timing-20261120/`.

21 November IST — local 30-day retention/reopen regression check. The focused
synthetic PostgreSQL suites for study-history deletion, verified-email reopening,
ordinary retention and restore privacy preflight pass 73 tests with one existing
Starlette/httpx deprecation warning. The read-only preflight tests use synthetic
candidate/reference databases; no current production backup was restored and no
production migration or cleanup gate changed. Migrations 0130–0131 remain local
drafts. Next retention gate is exact-scope/FK/trigger reconciliation plus the full
recovery rehearsal on an independently verified production clone. Receipt:
`reports/finna-retention-recovery-check-20261121/`.

21 November IST — cross-service adult/privacy regression follow-up. The focused
account privacy, audience, Google/native admission, assessment, learning, game,
publication, community, CMS and tier suites pass 344 tests in 270.33 seconds,
with one existing TestClient deprecation. This was a synthetic local PostgreSQL
run. `adb devices -l` found no connected physical device, so TalkBack/release
acceptance remains open. No production database, provider or phone was changed.
Receipt: `reports/finna-local-launch-check-20261121/`.

21 November IST — checked clone-rehearsal availability. The workspace has no
configured `FINNA_RESTORE_REFERENCE_DSN` or `FINNA_RESTORE_CANDIDATE_DSN` and no
local `/srv` restore environment. A read-only SSH check confirmed the documented
host is live production, found the 20 November paired backup, and measured 18.56
GB free. The existing restore procedure consumes a 10 GiB reserve and writes a
production worker-heartbeat row; it was not run. No production database was
queried or changed, no backup was restored, and no writer was drained. The new
retention comparison still needs a separately isolated candidate and an
independently current reference with 0130–0131 schema; the historical 18 November
receipt does not satisfy either requirement. The production-clone gate remains
open pending an adequately provisioned isolated restore environment and a
controlled writer cutoff. Availability details are in the retention regression
receipt.

21 November IST — completed local retention scope/FK/privilege audit. A fresh
synthetic PostgreSQL database applied the full local migration chain. Catalog
inspection traced 31 foreign-key references into selected study-delete roots;
delete ordering and retained-link detachment were checked against the staged
migration. The audit found `mpsc` had direct delete grants on four study roots
with no application delete path, so 0131 now revokes those grants while its
security-definer sweeper remains functional. Owner-scoped reset/rebuild deletes
on mutable projections remain intentionally supported. The four focused suites
pass 74 tests, one existing deprecation warning. This is local schema evidence
only; deployed grants/triggers, current-reference comparison, provider/mail,
full data-location review and recovery rehearsal remain open. No production
database or cleanup setting changed. Receipt:
`reports/finna-retention-recovery-check-20261121/`.

20 November IST — mobile answer timing follow-up. The native question card already
highlights the choice immediately and says “Waiting for answer confirmation…”;
the local pending-choice receipt remains durable before POST, and the authoritative
POST response is shown before the follow-up receipt write. Both native answer
paths now return a `Server-Timing` duration on isolated staging. A synthetic API
check measured 116.6 ms server / 136.77 ms round trip for direct question answers
and 113.6 ms / 130.49 ms for saved practice; one receipt replay took 1.5 ms server
/ 19.99 ms round trip. These are single API-host samples, not Android tap-to-
feedback. Typecheck/build and focused backend/mobile answer-isolation tests pass.
The native exam module already has website-style module/paper, subject, topic,
subtopic and answer-status filters. The 21 November emulator follow-up below
records one tap-to-correctness sample; physical TalkBack focus/speech checks
remain. Timing receipt:
reports/finna-answer-timing-20261120/.

20 November IST — conservative 30-day study-history cleanup staged locally.
The owner approved deleting personal practice/mock/review, vocabulary/map answers
and derived progress after the 30-day reopen window. Multiplayer results,
reward/payment/security records, public/shared content and backups are explicitly
outside this job. Migration 0131 adds bounded, resumable deletion, restricted holds,
receipt-link detachment, a completion marker and a default-off hourly gate. Synthetic
PostgreSQL coverage now includes retained rewards/games, holds, direct-delete guards,
the default-off worker and small-batch retries. It is a local draft only: migrations
0130–0131 are unapplied in production. Still required are restored-production-clone
reconciliation, exact field/location review, legal/accounting/security exceptions,
backup/restore reconciliation, real release/mail validation and a separate
production rollout decision. See docs/FINNA-RETENTION-PROPOSAL.md.

20 November IST — owner selects a 30-day study-history deletion and reopen window.
After export and account closure, the owner selected study-history deletion after
30 days and explicitly wants users to be able to reopen the account during that
window. The clock starts at successful closure, and reopening before expiry cancels
pending study-history deletion. Recovery uses a single-use link to the previously
verified email and a fresh password; old sessions stay revoked and Google/MFA must
be reconnected or set up again. Exact records/fields to erase, exceptions/holds,
and legal/accounting review remain open. The local implementation is not deployed.
No study-history erasure job or exact public
retention promise is authorized. The 30-day window does not set backup expiry or
financial/security retention.
See docs/FINNA-RETENTION-PROPOSAL.md and docs/FINNA-REMAINING.md.

20 November IST — owner confirms secure reopening by verified email.
The selected path retains an encrypted, minimal identity envelope for verified
accounts during the 30-day window, sends a single-use email link, restores the
account with a fresh password and leaves old sessions revoked. The local UI now
states what is restored and what private data is not. Reopen, closure and mail
checks pass; web typecheck passes. Migration 0130 remains unapplied in production.
Study-history deletion scope, exceptions, legal review, real-mail/release validation
and the remaining launch gates are still open. No production deployment occurred.

20 November IST — source-mapped candidate study-history deletion scope.
The retention draft now enumerates personal answer/score history, practice and
review state, derived progress/preferences, vocabulary/Atlas activity and the
separate multiplayer-answer problem. It records immutable scoring evidence,
reward/replay foreign keys and shared game rows as design blockers, with explicit
separation from payment/security records, public content and backups. This is a
private candidate boundary for review, not approval to delete. No deletion code,
schema change or cleanup job was added; exact fields, exceptions/holds and qualified
review remain open. See docs/FINNA-RETENTION-PROPOSAL.md.

20 November IST — local verified-email reopening implementation.
Migration 0130 stages a time-limited encrypted identity envelope for accounts
whose email was verified before closure. The account recovery request sends a
single-use link to that address; completion sets a fresh password, preserves old
session revocation, and requires Google/MFA to be reconnected or set up again.
Expired envelopes are removed by bounded cleanup and the read-only restore
preflight compares them. Focused account-reopen, mail, closure and restore checks
pass. This is local only; 0130 is unapplied in production. Study-history deletion
scope, exceptions, backup/provider reconciliation and legal/accounting review remain
open, so no study-history erasure job or public retention promise is active.

20 November IST — refund entitlement and invoice-status decisions recorded.
Following the owner's delegation to decide post-refund access, the private legal
draft records that a provider-confirmed full refund ends access granted by that
subscription; unrelated active grants remain. Partial-refund behavior and provider
status handling still need validation before checkout. The owner also stated they
are not GST-registered; invoice address/details and qualified tax review remain
open. These decisions do not enable checkout or publish policy pages. See
docs/FINNA-LEGAL-DRAFTS.md.

20 November IST — owner supplies GST threshold inputs.
The owner reports the principal place of business is Mizoram and PAN-wide annual
aggregate turnover is under ₹10 lakh. This is below the published service-supplier
registration threshold for Mizoram; GST registration is not assumed to be required
for Finna solely because it may sell subscriptions. Supply classification, other
compulsory-registration exceptions, invoice/tax treatment and adviser confirmation
remain open. Record this as owner-provided information, not independent verification.

20 November IST — local adult/privacy gate regression recheck.
Four focused backend files covering account privacy, audience/background
eligibility, learning eligibility and restore privacy preflight pass: 86 tests.
One existing Starlette/httpx deprecation warning remains. This is local
regression evidence only; it does not approve retention choices, production
deployment, feature-flag activation or destructive cleanup. Report:
reports/finna-policy-gate-check-20261120/.

20 November IST — physical Samsung Android follow-up.
The installed regular beta's TalkBack service was briefly enabled; the app
screen snapshot found 14/14 clickable controls labeled, but injected traversal
did not verify focus order or speech. TalkBack's original off settings were
restored. Two main-screen swipes rendered 150 frames: 2 janky (1.33%), p95 9 ms,
p99 16 ms; process PSS was 172,394 KiB. This is a short sample, not release
certification. The existing signed synthetic staging preview was verified and
opened on the phone, but practice redirected to staging sign-in. No credential or
answer was entered; the temporary staging package was removed and regular Finna
was left foreground. Physical answer latency, complete TalkBack, and broader
device/network/release profiling remain open. Report:
reports/finna-physical-android-check-20261120/.

20 November IST — owner selects 18+ only.
The owner explicitly replaced the earlier under-18 audience: “just dont do below 18”.
Guardian enrollment/provider/parental-consent design is removed from launch scope.
Local join/sign-in, age notice and policy previews now state the adult-only rule;
new guardian request creation is rejected while historical idempotent receipts,
review/withdrawal and restricted-account privacy/export/recovery/closure remain.
No age is inferred, no automatic under-18 upgrade or history deletion is added.
The current plan is docs/FINNA-ADULT-ONLY-PLAN.md; the old guardian plan is marked
superseded, with historical receipts preserved. Retention/recovery, adult-only
rollout, invoice/tax/refund/provider acceptance and physical/human/content/healthy-
week/volume gates remain. All launch flags remain off; 0122–0129 unapplied in
production; migration 0130 is now a local recovery draft, still unapplied. No
deploy, new APK, phone, mail or payment action.
Validation is recorded in reports/finna-adult-only-policy-20261120/.

20 November IST — current signed Android account/offline-retry acceptance.
The verified installed preview 01a448a3 passes actual Chrome synthetic-B sign-in,
explicit account confirmation/app return and account restoration after process death.
Offline fresh question 100/C stays pending without a server attempt. An offline cold
start shows connection feedback; online restart revalidates the saved identity without
another login. Home → Saved questions → Collections → Resume collection restores C;
Home Continue creates a new set. One actual explicit retry creates exactly one attempt
and authoritative 0-correct/1-revisit feedback. Another cold restart preserves the
result with no duplicate. Sign-out and guest restart pass; native revocation is verified
and the remaining owned browser parent retired. Staging ends with 2 synthetic accounts,
6 attempts (one new), 0 mail, 0 active auth. No production learner writes or phone input.
All 11 app-only images inspected; scoped UID 10219 crash buffer empty without clearing.
Original radios/shell UID restored, private synthetic credentials removed and emulator
stopped/data retained. All 3 HTTPS roots return 200; lint/typecheck pass; 171 upload inputs, 815 prior
native/operator report files and 1,079 protected API/migration/web/operator inputs preserved.
No runtime/dependency/schema/service/new-build/flag change. Previous 143/33 suites retain
old scope; no full offline, physical TalkBack/carrier/tablet/performance certification.
Retained harness notes cover keyboard bounds, lexicographic question selection,
immediate sign-out and changed UID output parsing. Beta 11f7cbfb remains current.
Next: the owner has selected **18+ only**, so guardian enrollment is out of scope.
Retention/current-state/recovery choices, invoice/tax/refund/provider acceptance,
physical/owner/content/healthy-week/human/volume gates remain. See
[adult-only plan](FINNA-ADULT-ONLY-PLAN.md) and
[retention proposal](FINNA-RETENTION-PROPOSAL.md). iOS deferred; all launch flags remain off; 0130 is a local draft and unapplied in production.
Report: reports/finna-current-signed-account-recovery-20261120/. Preserve frozen targets.

20 November IST — local restore privacy preflight and operator procedures.
Added a read-only operator comparison for a distinct restored candidate and an
independently established current reference. Twenty selected identity/privacy
control projections include closure, password/Google/MFA, age declarations,
request/event versions, staff grants, sharing/preferences, closed private documents
and durable delivery receipts. Ten bearer/queued-mail categories must be quarantined.
Uncertain/reserved immutable mail history is compared and reported for review, not
deleted to force success; cancelled account mail with cleared ciphertext is inert.
The tool uses repeatable-read read-only mpsc, fixed public tables, candidate DB clock,
timeouts and private salted server hashes. Only aggregate results are emitted.
Missing schema/privileges or identical candidate/reference fail closed. It never
repairs, promotes, proves reference currentness or authorizes sending/activation.
107 scoped checks pass, including 44 new cases and existing restore/request/closure/
retention/deferred-billing checks. Initial 46-pass/1-fail fixture attempted a document
insert after closure and correctly hit the existing guard; corrected pre-closure
fixture and all failure/intermediate logs remain. Final source-bound inputs match.
All 1,079 protected runtime/migration/web/operator inputs and 57 prior frozen report
files remain unchanged. All new isolated DBs removed; 13 baseline names retained.
Private procedures now cover request handling, restore quarantine/reconciliation and
future authorized any-reason seven-day refund handling using official provider
references. No legal/tax deadline, retention period or guardian method is selected.
No production connection, deployment, migration, mail, payment, phone or APK change.
No economy code/calibration change; prior 2,275/1,202 evidence is not a fresh run.
0130 remains unreserved. Database policy, age, checkout and referrals remain off.
Next: actual guardian verification and permitted processing/consent/withdrawal;
retention schedule and independent current-state preservation; reviewed repair/
recovery/cutover; invoice/tax/refund entitlement decisions and real provider tests.
Physical Android, human/content/healthy-week/volume gates remain; iOS is deferred.
Procedure: docs/FINNA-PRIVACY-OPERATIONS.md.
Report: reports/finna-restore-privacy-preflight-20261120/. Preserve frozen targets.

20 November IST — local CMS publication rewards and workflow notice admission.
CMS first-publication rewards now use database recipient admission before the
reward mutex/claims/profile/ledger. Restricted/busy targets leave source publication
and audit intact; source replay/revisions/restore do not remint a skipped first
publication. Registration, independent review, paid-preview/self exclusions and
one-per-IST-day remain. Mutex-onward and the entire historical reversal function
are byte-identical: recorded claim amounts reverse once despite restriction,
closure, busy/missing policy, with no daily-slot refund or history rewrite.
0129 guards new material/contribution-linked optional in-app notices at SQL INSERT,
including independent trusted publisher SQL. Missing/busy/restricted recipients or
missing policy suppress the copy without losing source/audit/archive integrity.
Existing notices/read controls, unrelated account/system notices and admitted
inbox preferences remain. The new function is not app-callable/disableable and its
lookup path puts public before pg_temp. No queue/backfill/new table/client mint API.
The trusted publisher checks its original immutable publication event, so a skipped
notice cannot backfill on original acknowledgement retry after confirmation/flag-off.
API decisions retain stale-version/state guards. Pair current publisher/API/0129
and all earlier guards after draining writers before any future policy activation.
Authorized governance decisions/reviewer identities/grants/quorum/source proof,
publication/credit/audit and prior private history retain their existing scope.
Social blocks do not annul private governance; no staff/MFA/disclosure/ownership/
native boundary was widened. This is not a legal retention/minor-processing basis.
2,275 full backend / 1,202 compatibility / 89 focused checks pass; 50 new cases; 137 API
runtime bindings plus separately bound publisher source,25 zero integrity fields.
Initial 82 focused checks also passed. The earlier restricted publication notice
assertion intentionally changes from 1 to 0 while source/audit/credit stay. No focused
failures, broad interruptions or applied-migration edits. Full/runtime/test/proof/
operator inputs are preserved. A fresh 252-table clone preserves all original
columns/values/indexes, existing function owner/ACL and 0129 exact body/config/trigger/
permissions. All clone/dump/stages and new local DBs removed; 13 baseline names,
62 prior frozen report files and 367 web inputs / 366 built files preserved. Both sites return 200.
0129 reserved/unapplied; 0122–0128 remain unapplied; 0130 next unreserved. No production
migration/restart/deploy, production bank sync, frontend/APK/phone/mail/payment.
Database policy, age, checkout/referrals stay off. Next: real guardian verification
method, consent/withdrawal/permitted minor processing; retention/backup/restore/
request/tax/refund procedures and guarded rollout/recovery. Existing physical Android,
human/content/healthy-week/volume gates remain; iOS stays deferred.
Report: reports/finna-cms-notice-eligibility-20261120/. Preserve frozen targets.

20 November IST — local database community tier admission and lookup hardening.
0127 filters current SQL weighted standing by active registered adult author and
voters when the database policy is on. Posting privileges/Guide candidacy use that
weight; display retains immutable historical max. Read-only real-role readers work
without processing leases or audit writes. Persistent capture admits the target
before the author-tier mutex, then leases the entire candidate voter set before
maturity calculation. Busy voters skip whole optional capture; nested rollback
releases newly acquired partial voter leases. Source votes/history stay intact.
Before-loss capture includes declarations/closure and existing moderation/block/
vote/email/maturity changes. Attempt maturity-boundary counting requires voter
admission. API restrictions/closure wait before rows; independent SQL retries55P03.
A skipped transient milestone has no delayed replay queue or history initialization.
A real mpsc temporary-vote-table regression exposed implicit pg_temp relation
shadowing in privileged tier capture (forged rank4 at a real rank1 threshold).
0128 orders pg_catalog,public,pg_temp for the five tier/audit functions, preserving
bodies/owners/ACL/history;0127 was never edited after application. No new award,
currency/table/client mint endpoint or guardian consent inference was introduced.
2225 full backend/1152 compatibility/45 new focused cases pass,136 runtime bindings
and25 zero fixture integrity fields. Initial35pass/2fail fixtures attempted a
foreign-key-protected attempt deletion and null required correctness; both now
assert existing integrity guards. Intermediate37new+18existing checks passed55;
the temporary-table reproduction failed before0128 and now passes. Logs remain.
Two successful fresh production-dump clones preserve252 original tables/columns/
values/indexes and function owner/ACL. The final clone verifies explicit lookup
order and read-only mode,0127/0128 exact bodies/configuration and default-off policy.
An intermediate combined helper had a tuple-path parsing error; a new separately
bound helper/rehearsal corrects it. A subsequent SSH connection failure also produced no accepted receipt; its exact
clone/dump/stage cleanup is verified. A fresh keepalive/server-receipt helper passes.
All four clone/dump/stages are removed.
All new local DBs removed;13 baseline names,60 prior frozen report files and367web
inputs/366built files remain identical. Both sites return200.0127/0128 reserved but
unapplied in production;0122–0126 stay unapplied;0129 next unreserved. No deploy,
restart, frontend/APK/phone/mail/payment change. All launch flags remain off.
Next: CMS material positive publication rewards/exact archive reversals and
administrative review/publication/CMS notice, quorum/source proof and retained
private governance/audit/history policy; actual guardian verification/consent/
withdrawal/minor-processing, retention/backup/restore/request/tax/refund procedures
and guarded launch. Existing physical/human/content/healthy-week/volume gates stay.
Report:reports/finna-tier-eligibility-20261120/. Preserve frozen targets.

20 November IST — local legacy contributor and voter visibility.
The default-off audience filter now covers legacy contributor ranks before dense
ranking/limits and published-contribution metadata before cursor pagination.
Bilateral viewer blocks and anonymous attribution remain; anonymous rankings create
no guest accounts, and both lists are private/no-store. Legacy Helpful totals omit
restricted voters and author-voter block pairs; new votes reject hidden authors,
while eligible actors can remove an own historical vote. Mock title protection is
retained and active-game/open-Cup title protection added. Published bank questions,
source credits, votes, reward receipts and tier milestones are preserved.
Shared Helpful query builders now resolve the flag at query time, including static
SELECT templates; feed/direct study/question reads, visible profile/weekly counts
and the current support count filter restricted voters before maturity weighting.
Read-only real-role readers work; no account-processing lease or persistent score
write is added. This does not finish SQL current standing, posting privileges,
Guide candidacy or milestone triggers. V.8 requires splitting review-sized phases;
the database target/voter/tier admission is the next separate migration/rehearsal.
2180 full backend/1107 compatibility/79 focused checks pass,39 new cases,133 runtime
bindings and25 zero fixture integrity fields. Initial25pass/7fail closed-account
fixtures violated the existing anonymization constraint; normal closure plus
separate unclosed/email-less fixtures now prove the boundary. Failure logs retained. An older Guide fixture created150 undeclared voters; its
reproduced failure now declares those synthetic voters adult. The initial broad
runs were stopped (exit2) with exact owned child signals and receipts before the
fixture edit; final suites use the corrected source hashes.
All47 predecessor report files,367 web inputs/366 built files and every migration
remain identical. All new local test DBs are removed;13 original names remain. An interrupted DROP
left one invalid unconnectable DB (datconnlimit=-2); its exact pending cleanup was
completed after checking owner, baseline absence and zero connections.
Both public sites return200. No new migration/remote clone/production deploy or
restart, frontend/APK/phone/mail/payment change.0127still unreserved;0122–0126remain
unapplied. All launch flags remain off. Next: complete database tier admission and
immutable before-loss capture; administrative notice/quorum/audit/history policy;
real guardian verification/consent/withdrawal, retention/restore/request/tax/refund
procedures and guarded launch. Existing human/content/physical/volume gates stay.
Report:reports/finna-contributor-visibility-20261120/. Preserve frozen targets.

20 November IST — local publication reward recipient admission.
Migration0126 admits new positive contribution rewards through the database-wide
policy/shared account lease before reward mutex/profile/ledger/claim writes. A
restricted/busy recipient leaves source publication, credits and audit intact;
trusted original-event replay does not remint after confirmation or flag-off.
No postponed-award queue, historical award backfill or client mint endpoint added.
Exact historical negative reversals bypass positive eligibility, including closed
accounts and policy-off mode. This fixes the old registered-email early exclusion
for closed reversals. Legacy/v2 original amounts, once-only matching, source proof,
quorum, tariffs and daily slots remain; the SQL body after the mutex is identical.
Zero source credits remain valid. This is internal ledger integrity, not cash/refund
execution, guardian permission or complete administrative processing policy.
2141 full backend/1068 compatibility/49 focused checks pass, including31 new cases,
130 exact runtime bindings and25 zero fixture integrity fields. Initial failures
were duplicate synthetic reversal revisions, a synchronous fixture waiting on a
legitimate FK row lock and stale pg_stat_activity polling; async pg_locks checks
now prove closure waits and finishes safely. One exact owned fixture query was
cancelled; all failure logs remain. No applied migration was edited.
A fresh production-dump clone preserves252 original tables/columns/values/indexes;
0126 matches the exact installed function body with its owner/ACL unchanged. Clone,
dump/stage/new local DBs are removed;13 baseline names,63 frozen predecessor files
and367 web inputs/366 built files remain identical. Both public sites return200.
0126reserved/unapplied;0122–0125remain unapplied,0127next unreserved. No production
restart/deploy, phone/APK/frontend/mail/payment change; all launch flags stay off.
Next: community target/voter weighting, tier capture and legacy contributor rank/
author/voter reads, administrative notice /
audit/history decisions, actual guardian verification/consent/withdrawal,
retention/restore/request/tax/refund and guarded launch. Do not enable policy yet.
Report:reports/finna-publication-eligibility-20261120/. Preserve frozen targets.

20 November IST — local synchronous activity and guest-transfer admission.
A database-wide operator policy defaults off; API startup rejects a mismatched
age flag and closes its new pool. Independent SQL activity uses the same shared
account lease as workers/restrictions, and missing policy fails closed. Restricted/
busy activity retains source attempts and durable reconciliation hints. The existing
admitted worker can rebuild activity; no new award or migration-time backfill.
Guest transfer leases both subjects before credential/target locks, rechecks active
adult eligibility and fresh proof, and preserves snapshots, assessments and once-only
receipts. SQL attempt ownership changes also check source and registered target.
Direct SQL restrictions fail/retry55P03 under admitted work; API restrictions wait
before row locks. A reproduced direct-function ownership race is fixed by0125;
0124 stays unchanged after application. The initial focused privilege failures are
fixture differences from postgres default grants, independently confirmed on clone.
2110 full backend/998 compatibility/35 focused checks pass,129 exact runtime
bindings and25 zero integrity fields. Interrupted first broad suites retain exit2
receipts before source changes. Two fresh production-dump clones preserve252
original tables/columns/values and existing indexes. Both clone/dump/stages and
all new local test DBs are removed;13 baseline names,71 prior report files and
367 web inputs/366 built files remain identical.0124/0125 reserved/unapplied in
production;0122/0123 remain unapplied,0126 next unreserved. No production restart/
deploy, phone/APK/frontend/mail/payment change; age/checkout/referrals stay off.
Remaining: positive publication awards with legitimate reversals, community tier
computation/milestones, administrative notices and historical controls, actual
guardian verification/consent/withdrawal, retention/restore/tax/refund and guarded
launch. Do not enable the database policy before those paths/rollout are verified.
Report:reports/finna-synchronous-activity-20261120/. Preserve all frozen targets.

20 November IST — local shared-subject visibility and social-notice guards.
With the optional age flag enabled, active-adult subject checks now precede
public/shared pagination and counts: creator discovery/profile/search, community
feeds/question/study replies/accepted snippets, materials/references, Guides,
Desk members/items/calendar/goals/chat/Inbox and stored game/Cup identities.
Existing blocks, disclosure and publication gates remain; stored history stays.
Restricted Desk owners hide rooms/invites, while eligible members can leave or
decline. Inbox previews recheck linked notes. Hidden game owners use an empty
string to preserve the response contract. Reserved team attribution is content,
never learner age verification. Owned export/private controls/moderation remain.
Immediate Desk/discussion notices use nonblocking account processing leases;
restriction/closure serialize with admitted notices. Suppressed optional notices
are not replayed. Existing private notice history and durable correction queues stay.
2075 full backend/946 compatibility/49 focused checks pass, including45 new cases,
126 exact runtime bindings and25 zero integrity fields. Retained focused failures
include a real unqualified invitation SQL correlation (fixed and rejected by the
helper), fixture catalog/session/moderation/body/anonymization mistakes and Cup
fixture credentials. Broad suites were deliberately interrupted to add the two
legacy Cup rank readers; final source-bound suites pass. All new test DBs are
removed,13 baseline names and42 prior frozen report files unchanged;367 web inputs/
366 built files preserved. No schema/production/frontend/APK/phone/mail/payment
change;0122/0123unapplied,0124next unreserved. Age/checkout/referrals remain off.
Synchronous review confirms attempt/adoption activity writes, positive publication
credits, SQL tier milestones and administrative review notices still need separate
database-side design/new migration/rehearsal. Visibility is not complete guardian
withdrawal, consent, minor-processing permission or erasure. Real verification,
retention/restore/tax/refund and guarded rollout remain open.
Report:reports/finna-community-eligibility-20261120/. Preserve older frozen targets.

20 November IST — local reassessment/correction eligibility guard.
The default-off age boundary now admits derived mock/attempt assessments and
in-app correction notices through nonblocking shared account processing leases,
with a fresh active-adult check. Restriction/closure wait for admitted transactions.
A restricted/busy target rolls back its whole page, retaining cursors, pending
status and failures. Temporary queue/account locks are released; individual jobs
are not acknowledged. At most10 source jobs/events are examined for other work.
Eligible accounts sharing a paused page also wait; no cursor skips restricted work.
Source/appearance invalidation continues without authorizing learner derivation.
Closed email-less accounts remain absent from the original notice recipient query.
Original results, assessments, notices and economic history are retained.
2030 full backend/837 compatibility checks and46 focused tests pass, including25
new guard cases,119 exact runtime bindings and25 zero fixture integrity fields.
The initial fixture failures (36pass/3fail,40pass/2fail) are retained and corrected.
An intermediate broad run was deliberately interrupted (exit2) to restore default-off
locked-oldest skipping; its regression and both final source-bound suites pass.
All new test databases are removed;13 pre-existing names and42 frozen game-report
files remain unchanged.367 web inputs/366 built files remain preserved.
No new migration, production restart/deploy, real mail/payment, frontend/APK or
phone change.0122/0123 remain unapplied,0124 next unreserved. Age/checkout/referrals
off; real guardian verification/consent, other synchronous/SQL-trigger paths,
community/Desk/identity exposure, retention/restore/tax/refund and guarded rollout
remain open. Report:reports/finna-reassessment-eligibility-20261120/.

20 November IST — local game lifecycle eligibility guard.
The default-off age boundary now checks participants before start, clock advance
and finalization, including voluntarily departed players' saved choices. Restricted
seats are released, public-result opt-in cleared and a once-only immutable marker
prevents old choices being processed or rejoined after confirmation/flag-off.
Account processing leases serialize admission with restriction/closure; a busy
account defers the room and releases temporary leases. Eligible opponents retain
original deadlines. All seven modes, timeout/reveal safety, replay, real worker
sweep, closure/restriction races and generic prepared index use are covered.
2005 full backend tests/791 compatibility checks pass with116 runtime bindings
and25 zero fixture integrity fields.26 new tests pass; the earlier51-test focused
run predates the index. The initial clone helper failed at import because its
filename shadowed Python's operator module; its log is retained. The corrected
fresh production-dump rehearsal preserves252 tables and all existing indexes;
0123 applies in6.448ms on the clone only. Clone/dump/stages/new test DBs are removed;
13 pre-existing local names remain unchanged. Migration0123 is reserved/unapplied,
0122 remains unapplied;0124 next unreserved. No production restart/application,
frontend/APK/phone/mail/payment change; age/checkout/referrals remain off.
Real guardian verification/consent, reassessment/notices, synchronous/SQL-trigger
and community/identity exposure, retention/restore/tax/refund and guarded rollout
remain open. Report:reports/finna-game-eligibility-20261120/. Preserve older targets.

20 November IST — local durable learning eligibility guard.
When the default-off age flag is enabled, worker claims require a declared adult
and an active registered account. An account-specific shared processing lease
precedes the job lock; under-18 restriction/closure take the exclusive lease first.
Fresh admission checks and bounded busy-candidate lookahead retain pending job
versions/cursors/history instead of acknowledging restricted work. Nightly enqueue
filters age declarations; the heartbeat counts age-paused jobs. No minor activation,
new migration, production/phone/APK/frontend/payment/mail change. The initial focused
run passed39/failed1 due to invalid JSON in a synthetic partial-write fixture;
the fixture is corrected.1979 full backend/765 compatibility checks pass with
114 source bindings and25 zero fixture integrity fields. Exact runtime/test inputs
are preserved. All new test databases are removed;13 pre-existing names are unchanged.
Real verification/consent, game/reassessment/synchronous-trigger/community review,
retention/restore/tax/refund and guarded rollout remain open.0122unapplied,0123next.
Report:reports/finna-learning-eligibility-20261120/. Older frozen targets stay preserved.

20 November IST — local background age restrictions added.
The default-off age boundary now covers review-reminder scheduling/reservation/
delivery, official-calendar notifications, bearer calendar feeds and weekly XP/game
standings. Under-18 declarations cancel pending study reminders, disable calendar
reminders and version-revoke active feed URLs; entries and historical receipts stay.
745 compatibility checks pass with 114 runtime source bindings and 25 clean fixture
integrity fields. All 1967 full backend tests pass with the exact sources preserved. No production,
mail, payment, APK, frontend or phone change; 367 web inputs/366 built files and the
prior 45-file privacy report are preserved. No new migration; 0122 remains unapplied,
0123 next unreserved. Real guardian verification/consent, learning/game/reassessment
and community/Desk review, retention/restore/tax/refund and guarded launch remain open.
Report:reports/finna-audience-background-20261120/. Preserve all older frozen targets.

20 November IST — local privacy implementation completed for this bounded slice.
The owner confirmed Hruaitluanga, an individual trading as Finna. Privacy request
forms/owner queue, a default-off adult age boundary and launch policy previews are
built and tested:1950full/717compatibility,113source bindings and final-build
1280/320 light/night browser QA. Migration0122 is local/unapplied;0123 next free.
Minor enrollment remains unavailable pending real guardian verification, consent
lifecycle and permitted background-processing review. Retention/tax/refund handling,
guarded deployment, final policy publication and actual payments remain open.
No new APK, connected phone, production restart or payment activation.
Report:reports/finna-privacy-implementation-20261120/.

20 November IST — private policy preparation continued.
Owner chose no fixed refund-support response deadline and an under-18 audience
with guardian controls to be designed. Legal/invoice identity remains undecided.
[Privacy inventory](FINNA-PRIVACY-INVENTORY.md) now describes current production
closure/cleanup, unpruned backups and external assets; [guardian plan](FINNA-GUARDIAN-PLAN.md)
sets out implementation gaps and acceptance requirements. Updated [policy drafts](FINNA-LEGAL-DRAFTS.md)
remain private. Guardian implementation, retention/request decisions, invoice/tax
details, public policies and actual payment checks remain open. No runtime change.
Evidence:reports/finna-policy-readiness-20261120/.

20 November IST — further readiness planner alternatives rejected; policy inputs recorded.
Fresh analyzed252-table clone,48exact-result checks and12EXPLAIN ANALYZE runs compare
six transaction-local settings in both source scopes. Join2 is tied with deployedjoin1
(default4054.647→4048.332ms;all4151.020→4207.825ms);join3/4/5 andjoin8/from1 are64–71%slower.
All original values remain identical; clone/dump/stage removed. No runtime/dependency,
production statistics/schema/global configuration change or API restart; the prior
empty-pins release/current recoveryc8_khz6p and its1938-test proof remain current.
Owner supplied public nameFinna,support address and a7-day refund window,then explicitly
chose refunds for any reason within7days of the charge. These are saved in private
FINNA-LEGAL-DRAFTS.md; remaining legal/invoice,handling,age/retention/dispute /
provider details and publication are still pending. No policies published,mail sent,
refund issued,checkout enabled,new APK or phone input. Full plan remains open.
Report:reports/finna-readiness-plans-20261120/. Preserve all frozen evidence; do not rerun it.

20 November IST — targeted subject-wide query improvement deployed.
A single redundant SQL condition skips empty pin arrays before the scoped question join.
Four alternating warm samples improve the default-scope subject-wide detail query
4456.789→4058.535ms (8.94%); other cases have no material regression. Section counts
retain their existing timing under production JIT settings; this is a targeted gain.
1938full backend tests,705integrated/496production compatibility,64proposal/recovery
checks and105/77source bindings pass. Two fresh analyzed252-table clones preserve
all original values;520timed runs/260output comparisons match and both clones/dumps/stages are removed.
Only collection reader and matching production economy evidence are released;310source,
3470static, schema/private configuration and all writers remain protected. Live two-payload
hashes match; subject HTTP sample4.711→4.362s.8workers/4timers healthy,25integrity
counters0,ledger46→46; sites/API/staging healthy. No phone,new APK,migration,mail,
synthetic production learner activity or history rollback. Prior610Android,28ops and31rejected-query
report files are hash-preserved. Current paired recovery:/root/finna-empty-pins-backup-c8_khz6p.
Reports:reports/finna-empty-pins-20261120/ and the rejected redundant-join experiment
reports/finna-query-performance-20261120/. Do not rerun frozen deployment/evidence targets.
Further performance/maintenance work,actual healthy-week/monthly-human,owner/physical,
content/legal/payment/real-volume gates remain open;iOS deferred. Full plan remains open.

20 November IST — dependency/operations follow-up; website advisory item closed.
Fresh full and production web lockfile audits report0findings; the earlier picomatch advisory is withdrawn.
Mobile remains27moderate full/20production-install-graph entries from2underlying advisories,zero high/critical.
All27affected parent constraints reject the published fixed leaf major versions; supported registry ranges
have no newer release. No package changes,forced Expo/Jest downgrades,new APK build or phone input.
Current real-role read-only ops:8workers/4timers healthy,25integrity counters0,ledger46→46,verified backup,
existing actual restore still healthy and all3HTTPS checks200. Old collector/stats failures are retained;
collector history begins18November,so no healthy-week/monthly-human sign-off or rollout is claimed.
Bounded slow-log review classifies13older error lines as autovacuum cancellations without claiming cause;
query/maintenance investigation remains open. All610frozen Android files,171inputs/2regressions preserved.
Report: reports/finna-dependency-ops-review-20261120/ (main Finna repository). Android beta11f7cbfb remains current.
Full plan,physical/owner/content/legal/payment/real-volume gates remain open;iOS deferred.

20 November UTC — corrected signed Android update passes bounded emulator acceptance.
Preview01a448a3-d97b-4719-9da5-e2d4a873e406 and beta11f7cbfb-e878-44ed-998c-2eff382694a3 are FINISHED,
signature/package/origin/callback and16KB-alignment verified; installed bytes match both downloads.
143component/33logic tests,lint/typecheck,Android/web exports and171reviewed upload inputs pass.
Signed staging traverses all1000/end in200guarded swipes/259.55s with4explicit page recoveries;
all40unfiltered native pages return200. Two cold restarts restore999 at identical coordinates;
nonfinal993/partially visible994 also restore identical coordinates after a retained hierarchy-tool failure
and separate serial reinspection. Regular beta guest Home/Library/exam entry and compact320dp dark/200%
filter Clear all/Show questions pass. Test setup fixes for display recreation/modal bounds are recorded;
no runtime code change or additional build is made this continuation. All46retained images inspected.
Original display/network settings restored,shelluid2000,scoped crash buffers empty,emulator stopped/data retained.
Staging remains2registered synthetic accounts/5attempts/0mail/0active QA auth;all three HTTPS hosts200.
No phone input or production learner writes. Whole-report validation.json freezes the final evidence;
prior579proof bindings,83earlier local files and61current local files are preserved. Do not rerun frozen outputs.
Regular owner beta:reports/finna-native-emulator-extended-20261119/finna-beta-current.apk;
installation guide:docs/FINNA-ANDROID-BETA.md. Earlier queued checkpoints below are historical.
Next:owner install/feedback,physical TalkBack/network/tablet/performance coverage,actual healthy-week/monthly
human sign-off,reviewed content/official sources and public legal/support/refund/live-billing decisions.
Full native acceptance/full Finna plan remain open;iOS deferred because no device is available.

19 November 18:03 UTC — startup-only guard143 local acceptance passes; new signed pair queued.
Current preview01a448a3-d97b-4719-9da5-e2d4a873e406 and beta11f7cbfb-e878-44ed-998c-2eff382694a3 are IN_QUEUE;
do not duplicate. Prior231e7a5c/3f284a4c are confirmed CANCELED after later draft-filter metadata unmounted
its list. The new listMounted latch waits only at startup;143component/33logic,lint/typecheck,Android/web
exports and171-file archive pass. Only questions.tsx differs from the prior candidate. Exact current inputs:
build-inputs-mount5.json; snapshots question-browser-mount5.tsx and QuestionPosition-mount5.test.tsx.
Current local-only debug-certificate probe traverses1000/end in168swipes/217.88s with3pagination recoveries.
All40unfiltered native pages revalidate304;five cold starts restore999 at identical coordinates (zero-pixel
difference),and nonfinal993 also restores identical coordinates. No root/reading-position seed in this probe;
original display/network baseline unchanged,shelluid2000,scoped crash log empty,emulator stopped/data retained.
mount5-local-validation.json freezes61current diagnostic files;local-validation.json preserves83earlier142-test
files. Do not overwrite/re-run those local evidence files. They are local diagnostic,not Expo-signed acceptance.
Finish new builds,download/verify signatures+current source,replace local staging APK (different certificate),
repeat with mount5-signed-* helpers,then freeze whole report/update docs. Latest official artifacts are not ready yet.
Report:reports/finna-native-emulator-extended-20261119/. No phone input/production learner writes. Full plan open.

19 November 17:23 UTC — further reading-position correction passes local native probes; signed replacements queued.
The fe640697 preview reaches1000/end with five explicit page-recovery taps, but its first serial cold restart
misses999. Later local probes expose temporary-end acknowledgement, an empty initial native render window,
late header layout and throttled terminal offsets. Only questions.tsx changes among171reviewed archive files.
All142component/33logic tests,lint/typecheck,Android/web exports pass. Final local-only debug-certificate
staging probe passes five real-swipe/cold-restart cycles with identical index998/inside259.8095703125; a
nonfinal question993 probe restores identical coordinates and PNG bytes. These are diagnostic local APKs,
not Expo-signed acceptance. New preview231e7a5c-dae2-45b9-951e-ac99cf8efa11 and beta3f284a4c-5db8-45d2-973c-2a286fce618d
are dispatched;do not duplicate. Native acceptance/download/signature checks remain for these new builds.
Final local bundle traverses1000/end in280swipes with7explicit recoveries;two further cold starts return999.
No phone input or production learner writes.
ADB root used only for owned-emulator guest diagnosis is removed (uid2000);baseline restored and emulator stopped.
Report:reports/finna-native-emulator-extended-20261119/ remains unfrozen. Full plan/physical/business/operations gates remain open.

19 November continuation — extended emulator QA and question-position correction in progress.
Signed staging666b8b61 traverses all1000 synthetic questions;all40native25-item pages load and end notice appears.
A fast-fling stall at item825 resumes after reversing/slow scrolling;the new browser adds explicit Load more questions.
Cold restart returns to the saved page but misses the visible question;layout ordering and duplicate-scroll regressions
now gate completion on native size,scroll acknowledgement and matching viewability. Initial3regressions fail before
correction;an additional duplicate-event regression catches an early candidate;final137component/33logic checks,
lint/typecheck and Android/web exports pass. Only src/app/questions.tsx differs in171reviewed upload inputs.
Compact320dp dark and tablet1280x800/800x1280 layouts at200%text retain navigation and pinned filter actions;
compact Subjects label wraps across lines. These are emulator checks,not physical tablet/TalkBack/smoothness acceptance.
Software-GPU frame delays are substantial;do not claim release performance passed. No phone input. Staging stays5attempts,
0mail,0active QA auth sessions;both existing hosts healthy. Display/network baseline restored and emulator stopped.
Candidatefd7d4075 canceled after duplicate-event regression. Replacement previewfe640697-a01b-458f-9215-81c4fbbb6b40
and beta56460d0a-5cd6-49dc-8778-f38ab0983593 are queued;do not duplicate. They are not yet downloaded/native accepted.
Report:reports/finna-native-emulator-extended-20261119/. Finish builds,verify signatures/current bundle,install on owned
emulator and repeat native recovery/long-list checks. Earlier APKs remain historical;Samsung retains old6df0b4c7.
Full plan remains open for physical acceptance,owner feedback,real healthy week,human/content/legal/payment/volume gates.

19 November continuation — answer response/exam UI update built and bounded signed HTTPS emulator QA passes.
Bank/practice choices highlight before disk persistence; durable pending writes still precede sending.
Practice applies the authoritative POST response without the former extra GET. Exam→module browsing,
subject/topic/subtopic filters, scoped Papers and pinned filter actions pass synthetic browser and native QA.
129 component / 33 logic tests, lint/typecheck, Android/web exports and Expo Doctor 20/20 pass.
SDK58 patch alignment is complete;20 moderate npm runtime-tree advisories remain,zero high/critical.
Final preview 666b8b61-9cdd-4a54-85cf-138bf876ac3e and beta e4816038-1b54-4678-8376-daa6a33f9ce8
are FINISHED,downloaded and signature/package/current-code verified. Beta signer matches prior beta.
Signed staging passes actual HTTPS browser handoff,account restore after force-stop,bank feedback/restore,
practice feedback,offline pending-choice restart and one explicit retry,restored result,500-question
English→Grammar→Verbs filter and logout/restart. Server logs confirm no success-answer GET refresh.
API36 x86_64 emulator only;no Samsung input or phone performance claim. The Samsung retains old6df0b4c7.
Regular beta passes public guest Home/Library/exam-entry smoke checks;scoped crash buffers empty.
Persistent https://finna-staging.hawayu.in has its own PostgreSQL cluster and API identity,production paths
hidden,mail/payments/signup/admin blocked.5 synthetic attempts total,0 mail;all QA sessions retired.
Both existing sites stay healthy;existing Caddy hashes unchanged. Prior 105 API / 20 PDF and frozen Android/
release evidence preserved. Emulator networking restored;AVD retained and emulator stopped to release RAM.
Phone-free launcher/runbook:scripts/finna-android-emulator.py and docs/FINNA-ANDROID-QA.md.
Reports:reports/finna-native-release-readiness-20261119/ and reports/finna-native-https-staging-20261119/.
Remaining:physical TalkBack,broader Android/network/tablet/full release profiling and owner feedback;
healthy-week,human/content,legal/payment and real-volume gates. iOS deferred. “Yes” supplied no actual
operator/legal name,support email or refund values;draft policies stay private.
Earlier dated checkpoints retain their original acceptance/source/binary scope.

19 November continuation — signed Android accessibility probe remains incomplete.
TalkBack bound with touch exploration; injected inputs did not establish focus
traversal or speech acceptance. Nine Finna-only captures inspected; settings
restored exactly. A later Home scrolling probe stopped on focus loss before a
post-swipe sample; no performance result claimed and no further phone input.
Current lint/typecheck pass; signed UID crash buffer empty without clearing logs.
Runtime unchanged; all prior evidence/source bindings preserved. Installed beta
still lacks the prior local logout correction. Report:
reports/finna-native-android-accessibility-20261119/.
Next: reachable HTTPS preview/signed account checks, complete TalkBack and broader
network/layout/performance coverage, then final combined signed build/feedback.
iOS deferred; full plan still has healthy-week, human/content, legal/payment gates.
Earlier dated checkpoints retain their original acceptance/source/binary scope.

19 November continuation — native Android mock/offline/expiry/deep-list recovery passes.
Fresh disposable1000-question fixture,one real browser login and native3-question
mock. A disconnected choice survives force-stop;no server save until explicit retry.
Two acknowledged B choices score2correct/0wrong;final pending C stays unanswered
when reopening after server expiry. Expiry is accelerated by moving only the fresh
fixture's started_at,not by changing phone time. Native automatic submit and result
reload after another restart produce exactly2attempts,one completed mock,no mail.
Removing an ADB reverse does not close existing keepalive immediately;second choice
was acknowledged,so final outage drains7seconds before selecting the third choice.
Offline cold startup withholds account identity but retains encrypted credential;
reconnect/restart restores the same account with no new auth flow. Revoking the
fixture browser parent triggers native expired-session UI and removes credential/
account AsyncStorage. Seed guest reading position975 on the1000-item dataset;
actual four swipes persist980,then force-stop/reopen restores the same two visible
questions. This is bounded deep-page restoration,not full1000-row/release performance.
14app-only captures inspected;UID10354 crash buffer empty,logs not cleared. Current
lint/typecheck pass;prior116component/29logic source bindings unchanged. No mobile/
API runtime,migration,dependency,production or cloud/store change this continuation.
105API/20PDF and25release/69Android/58account/26mock-preparation proof hashes match.
Only prior client.ts logout fix differs among170signed upload inputs;installed
signed beta6df0b4c7 still lacks it. Native expired credential remains absent;
synthetic guest seed,device helper,exact DB/API/Metro/private host credentials and
owned8091/50269forwards removed. Phone settings unchanged. Report:
reports/finna-native-android-recovery-20261119/. Next:TalkBack,full long-list/release
performance,wider Android,real background/network variants,reachable HTTPS preview
staging and a future combined signed build with logout correction. iOS deferred,
no device;healthy-week/legal/payment/content/human/volume gates remain.
Earlier dated checkpoints retain their original acceptance/source/binary scope.

19 November continuation — timed Android mock starts; dynamic capture helper verified.
Fresh disposable1000-question fixture and native browser handoff start a real
three-question/30-minute mock in Finna Dev. The half-second countdown prevents
standard uiautomator idle dumps. Added optional --dynamic-hierarchy to the existing
capture helper plus scripts/build-finna-dynamic-dumper.py and
scripts/android/FinnaDynamicDump.java. The read-only helper keeps package/keyboard/
focus guards, captures the running countdown and refuses foreign foreground with
no screenshot/XML. Reusable build's DEX matches the actual device-tested helper.
The phone then moved to another app before any answer; all phone input stopped.
No interrupted-answer/deadline/offline/expiry acceptance claimed this continuation.
30focused mock/session/logout tests,lint/typecheck and helper build pass. No mobile
or API runtime changes;prior local logout fix still awaits a combined signed build.
One local mock,zero saved answers/attempts/mail. Synthetic sessions/parents revoked;
Dev force-stopped in background and its sole synthetic SecureStore entry cleared
by harness with valid-empty-store readback (not a native logout acceptance).
Exact DB/API/Metro/private host credentials,device test jar/XML and owned8091/48007
forwards removed. Owner-controlled foreground preserved. Report:
reports/finna-native-android-mock-20261119/. Resume physical mock recovery/deadline/
offline/expiry with Finna Dev foreground;HTTPS staging,TalkBack,1000-row restoration/
performance,wider Android and signed build remain. iOS deferred,no device.
Earlier checkpoints and their source/binary acceptance scopes remain historical.

19 November continuation — native Android development account/recovery checks pass.
Samsung Android16 completes real Chrome login/confirmation/callback for two
synthetic accounts on a fresh 1000-question loopback fixture. SecureStore account
restore survives force-stop; an interrupted practice choice survives another
force-stop and explicit retry records exactly one A-owned attempt. B has zero
progress and independent exam preferences. Logout clears authenticated local data
and revokes all three test mobile sessions. Phone testing exposed a false logout
warning: credential retirement rejected its own acknowledgement. Only POST
/mobile/logout now accepts its revocation response after retirement; an obsolete
401 cannot expire a newer account, and other response guards remain. Two of four
new transport regressions fail before the fix; all116component/29logic checks,
lint/typecheck pass afterward. Cleared Metro cache and actual native logout verify
the correction. It is local/dev only, NOT in installed signed beta6df0b4c7.
Only mobile src/api/client.ts changed runtime;105API/20PDF/25prior release/69prior
Android proof hashes match,169/170signed upload inputs match. One synthetic local
attempt,no mail,no production access. Exact fixture DB/API/private credentials,
dedicated Metro and task ADB forwards removed;unrelated8000 preserved. Prior
pending8091/56439 cleanup resolved;owner display settings unchanged. Report:
reports/finna-native-android-account-20261119/. This is development HTTP over ADB,
not signed HTTPS staging or full physical-offline/release acceptance. Next: native
mock/offline/account-expiry cases,1000-row restoration/performance,TalkBack,wider
Android coverage,reachable HTTPS preview staging and a future combined signed
build with the logout fix. iOS deferred (no device),not an Android blocker.
Healthy-week/legal/payment/content/human/volume gates remain;0110/0120immutable,
0122nextunreserved. Earlier dated checkpoints retain their original scope.

19 November continuation — combined Android beta installed; iOS deferred.
Owner has no iOS device. Defer physical iOS acceptance without blocking Android;
no iOS build/store request. Signed beta6df0b4c7-fd5c-4c2a-a0af-0d6c355e0741 now
installed,exact112596770B/SHA2566cf90d6820c0514ca231e7899e0508d53d736049b6b40eb916e1abb20e14cc66.
13visually inspected captures pass guest tabs/questions/filters,hot200%font then
Mock test,dark200%,landscape and cold restart;exact UID10396 scoped crash log empty.
Three ActivityManager cold samples247/288/292ms are limited first-draw evidence.
Actual owner baseline font1/nightno/rotation0/auto0 restored. Two normal guest
Continue auth starts cancelled before credentials/confirmation;no learner answer/
attempt/mail/award or production account connection. Capture guards refused other
surfaces. A disposable1000-question development fixture passes unique pagination
and deep reads0/475/975;Finna Dev displays its synthetic paper. Native auth flow
interrupted before credentials when another surface took focus,then USB detached.
No further phone UI operated. Exact fixture DB/API/credentials and Metro8091
removed/stopped. Device reverse ports8091/56439 need checking on reconnection;
unrelated8000 untouched. Lint/typecheck and105API/20PDF/170upload/25prior proof
hashes pass. No mobile/backend runtime,migration,dependency,deployment,new cloud
build or store change. Report:reports/finna-native-android-acceptance-20261119/.
Native account/offline/replay/TalkBack/1000-row restoration/performance,reachable
HTTPS staging and broader Android acceptance remain. Existing Doctor15-package
warning and healthy-week/legal/payment/source/curation/human/volume gates remain.
0110/0120immutable;0122nextunreserved. Full plan remains open.

19 November owner clarification — no iOS device is available. Current native
validation continues on Android. Physical iOS acceptance is deferred until suitable
device access is available; it is not a blocker for Android work and is not marked
passed. Do not request an iOS build or store submission for this scope. Preserve
existing cross-platform source/configuration and any earlier export evidence.

19 November continuation — isolated live HTTPS/browser rehearsal passes.
22checks use a fresh disposable PostgreSQL DB and loopback HTTPS, every API
connection as mpsc. Desktop Chromium signs into two synthetic accounts through
real login/confirmation pages; PKCE/replay, practice ownership/answer replay,
stale presentation, mock deadline/saved-only scoring/result recovery, bearer and
parent revocation and cookie CSRF pass. Two synthetic attempts/no queued mail;
exact DB/server/TLS credentials removed. This is desktop-browser/server evidence,
not native handoff or physical network/SecureStore acceptance.112component/29logic/
40mobile backend tests,lint/typecheck pass;105API bindings/20PDF hashes preserved.
No runtime/API/schema/production change.170upload paths unchanged; exactly six
reviewed runtime files differ from installed beta. One combined internal signed
Android beta6df0b4c7-fd5c-4c2a-a0af-0d6c355e0741 finished; downloaded112596770B,
SHA256:6cf90d6820c0514ca231e7899e0508d53d736049b6b40eb916e1abb20e14cc66.
Same certificate/package,non-debuggable,production API and new fix markers verified;
170upload hashes still match. APK available but not installed/physically accepted.
Remote Doctor retains one version-check failure/15unchanged packages flagged.
Do not duplicate the build. Report:reports/finna-native-staging-20261119/.
Persistent reachable HTTPS staging/preview binary, native browser/offline/replay,
long-list/TalkBack/release-performance/iOS remain. Current production-account beta
cannot host synthetic fixtures. Healthy-week/monthly-human/legal/payment/source/
Atlas curation/real-volume gates remain.0110/0120immutable;0122nextunreserved.

19 November continuation — local timed-mock lifecycle/recovery correction.
Five of seven initial regressions failed: pending hydration did not gate answers,
disk-delayed sends survived credential change/unmount, stale route/foreground reads
could overwrite newer state. Mock now remounts by account/route/credential and
checks lifecycle/load order after each await. Hydration gates controls; delayed
choices are not sent after client deadline; server still enforces real expiry.
Submissions send answers:[] only, automatic expiry submits once, later retries are
explicit and duplicate-submit conflict reloads authoritative results.13new tests,
112component/29logic checks,lint/typecheck/Android export pass without a phone.
Isolated mobile deadline test passes; bank-review snapshot test had an independent
fixture failure (unreviewed derived cq_test). It now owns an eligible synthetic
fixture; standalone test and all21module tests pass, no scoring/runtime change.
Report:reports/finna-native-mock-lifecycle-20261119/. Prior local fix sources/proofs,
105API bindings/20PDF hashes preserved;164/170original upload inputs match. Six
runtime files now differ from installed beta b4a1a9d2-28c2-4299-a1f6-efe383d2d242;
none of these later local corrections is in that binary. No device/production/API/
schema/learner/mail/award/build/store action. Staging/system-browser/offline/device/
TalkBack/long-list/release-performance/iOS and healthy-week/legal/source/curation/
human/volume gates remain open. Applied0110/0120immutable;0122nextunreserved.

Earlier checkpoints below retain their original source/binary scope.

19 November continuation — local native practice replay/start correction.
Practice actions now wait for saved-choice loading; lifecycle/credential checks
stop obsolete sends/clears/refetches. Saved answer retries preserve exact version,
choice and presentation. Compose callbacks cannot navigate after unmount/account
change; same-selection retries retain their key and changed selections get a new
key. Six of ten original regressions failed;14final regressions and all99component/
29logic checks,lint/typecheck/Android export pass. Two existing isolated PostgreSQL
real-role backend tests pass for replay/ownership/presentation and review timing/
two-slot daily reward caps. No phone used. Report:reports/finna-native-practice-replay-20261119/.
Only practice/[id].tsx and useStartPractice.ts changed runtime this continuation;
prior answer/session sources and proofs preserved.105API bindings/20PDF hashes
match;165/170 original upload inputs match,5runtime files differ from installed
signed beta b4a1a9d2-28c2-4299-a1f6-efe383d2d242. No new binary, production/API/
schema/learner/mail/award/store action. Staging/system-browser/offline/device/
TalkBack/long-list/release-performance/iOS and healthy-week/legal/source/curation/
human/volume gates remain open. Applied0110/0120 immutable;0122 next unreserved.

Earlier checkpoints below retain their original source/binary scope.

19 November continuation — local native session lifecycle correction.
Five of six initial regressions failed: delayed restore/browser results could
re-authenticate after sign-out; local logout waited on network; stale credential
writes could survive. Session operations now invalidate obsolete callbacks after
each await, retire local identity immediately, and serialize private cleanup /
credential writes across provider remounts. Late logout cannot erase newer login;
failed offline verification detaches the in-memory bearer, retaining encrypted
storage for re-verification. Cleanup/revocation failures stay visible. Existing
PKCE/state/flow/callback and server boundaries remain.13new regressions and all85
component/29logic checks,lint/typecheck/Android export pass without a phone.
Report:reports/finna-native-session-lifecycle-20261119/. Only mobile session.tsx
changed this turn. Earlier answer fix/proofs intact;3runtime files now differ
from installed signed beta b4a1a9d2-28c2-4299-a1f6-efe383d2d242,167/170upload
inputs match. Neither local correction is in that binary.105API bindings/20PDF
hashes unchanged. No device/API/schema/production learner/mail/award/build/store
action. Isolated staging/system-browser/offline/replay/device/accessibility/
performance/iOS and actual healthy-week/legal/source/curation/human/volume gates
remain open. Applied0110/0120 immutable;0122 next unreserved.

Earlier checkpoints below retain their original source/binary scope.

19 November continuation — local native answer-isolation correction.
Confirmed four failures before the patch: a disk-delayed answer could send after
unmount/credential change; old feedback and in-flight results could outlive their
account/question scope. Existing root remount already protects ordinary account
preference switches; no PreferencesProvider change was needed. Mobile useAnswer
now binds reads/state/requests to lifecycle, credential generation and presentation;
current pending retries retain their original key/choice, changed presentations
are rejected locally. Two mobile runtime files changed;10new regressions and all
72component/29logic checks,lint,typecheck/Android export pass. No phone was used.
Report:reports/finna-native-account-isolation-20261119/. This patch is LOCAL and
NOT in installed signed beta b4a1a9d2-28c2-4299-a1f6-efe383d2d242. Its earlier
signed guest proof stays frozen; it does not certify this patch or account/replay.
105API bindings/20PDF hashes are unchanged;168/170 prior upload inputs match,
with exactly client.ts/useAnswer.ts changed. No backend/schema/production learner
write/mail/award/build/store action. Native staging/auth/offline/replay/performance/
accessibility/iOS and healthy-week/legal/source/curation/human/volume gates remain.

Earlier checkpoints below describe their original source/binary scope.

19 November continuation — corrected signed Android guest QA passes.
Signed beta b4a1a9d2-28c2-4299-a1f6-efe383d2d242 is finished and installed as
in.hawayu.finna. Installed base APK matches the verified download byte for byte;
same signing certificate, production API, no debug flag or local API. Exact hot
200% text → Mock test reproduction now passes, plus hot dark/200%, landscape
navigation, all five guest tabs, question browsing/filter sheet and cold restart
on Samsung Android16. App-scoped crash observation found no fatal/router errors.
Native display reconfiguration can return to Home; previous-screen preservation
is not certified. Owner settings font1.0/nightno/rotation0/auto-rotation1 restored;
Home left open. Task-owned USB8081/8089 forwards removed, unrelated8000 preserved.
Fresh lint/typecheck pass; prior62component/29logic/export checks remain bound to
unchanged source.105API bindings/20frozen PDF hashes/170uploaded input hashes match.
Current evidence:reports/finna-desk-pdf-20261119/router-remount/continuation/.
No new build, backend deployment, learner writes, mail, migration, awards or store
submission. Next native gate: isolated staging sign-in/offline/replay, long-list
restoration/performance, TalkBack, broader devices and iOS. This production-account
beta cannot host synthetic learner-write tests. Actual healthy week, monthly human,
legal/payment/source/curation/real-volume gates and full plan remain open.
Applied0110/0120 remain immutable;0122 is next unreserved.

Earlier checkpoints below are historical; the continuation above is current.

19 November signed-APK follow-up — first binary rejected after native QA.
Expo authentication/project linking are complete; do not restart device login.
First signed beta ebb0569f-a711-4bc2-a177-d803c1297626 compiled, verified and
installed as in.hawayu.finna. Five guest tabs, system theme,200%font and landscape
were checked, but opening Mock test then crashed with an unbound global router.
Rotation alone passes; a hot200%font change reproduces that exact crash.
It is NOT an accepted beta. Screens/hooks now use context-scoped useRouter;
plain destination translation receives that handle. Source lint forbids the global
router import.62component/29logic checks,lint,typecheck and Android production
export pass. A focused Home regression covers unavailable global routing and
replacement screen contexts. Actual Dev mock navigation also survives hot dark/
200%font changes; debug multiple-linking warning remains visible and is not hidden.
Corrected signed beta b4a1a9d2-28c2-4299-a1f6-efe383d2d242 is now requested.
Do not request another duplicate: inspect this ID, then verify/install/retest it.
Current report:reports/finna-desk-pdf-20261119/router-remount/; operational state
native-progress.json. Owner baseline font1.0/nightno/auto-rotation1 restored.
Only task-owned8081/8089 forwards are for Dev preview; preserve unrelated8000.
No production learner writes,mail,migration,award,store submission or paid upgrade.
Full staging/account/offline/replay/accessibility/performance/iOS and other plan
gates remain. Goal stays open;0110/0120 immutable,0122 next unreserved.

19 November Android continuation — Expo account/project connected; build running.
Owner completed the official browser/device login as hruaia123. Personal project
@hruaia123/finna verified,ID d3228a20-5fa5-4107-86f2-134081281285; public defaults
linked in the sibling mobile app. Native landscape QA found/fixed side-navigation
occlusion using horizontal safe areas; tab text fitting accounts for those insets.
Rotation/font settings restored. SDK58 expo-system-ui58.0.7/plugin added for the
configured automatic appearance; new-binary behavior still needs checking.
60component checks,final lint/typecheck pass. Reviewed170-file upload excludes
credentials/env/logs/reports/Git metadata; Free plan0/15Android builds before request.
EAS remote keystore created and internal Android beta build
 ebb0569f-a711-4bc2-a177-d803c1297626 is IN_PROGRESS. It uses real production accounts,
not staging fixtures. No store/OTA submission or paid plan change. Do not request
a duplicate build: inspect the existing ID, obtain/verify/install when complete.
Private raw build metadata/auth state are OUTSIDE app source; safe current paths
in reports/finna-desk-pdf-20261119/native-progress.json. See EXPO.md there. Metro
87620/readonly preview70117 retained; only task-owned USB8081/8089 forwards. Earlier
resume error was a trailing-comma parser bug,corrected; login is complete.105API
bindings and20frozen PDF hashes still match; no backend/schema/mail/awards changed.
Full native/staging/iOS,actual healthy-week/legal/payment/source/human/volume gates
remain. Goal stays open;0110/0120 immutable,0122 next unreserved.

19 November continuation — saved PDFs and initial Android guest QA verified.
Four authenticated synthetic Desk print pages/17A4 Chromium pages rendered and
visually checked; Mizo/wrapping/margins/privacy pass,7existing note tests pass.
SamsungAndroid16/arm64 Finna Dev installed (503Gradle tasks/20m15s); actual Home/
Exams/Library/questions/filters/mock-builder/Desk/Me guest navigation checked.
Two sibling mobile files changed: src/app/(tabs)/index.tsx removes unbounded
Home action heights (1285→135px normal/252px at200%); components/BottomNavigation.tsx
fits full large-text tab labels within available widths. Final60component tests,
lint/typecheck pass; earlier29logic tests cover unchanged domain code. Font1.0
restored, orientation untouched; Home left open. All105 API/evidence source
bindings and production unchanged; no learner writes/mail/migration/awards.
Reports:reports/finna-desk-pdf-20261119/validation.json (PDF), native-device-qa.json,
NATIVE.md and native-progress.json. Keep frozen earlier proofs/recovery intact.
Metro session81977/readonly-preview40021, USB8081/8089 and isolated package
/tmp/finna-native-device-64u4rahe remain for the user's development preview.
Build daemon stopped; private Expo auth request state moved OUTSIDE app source.
EAS confirms Not logged in; official device login opened in owner's system
browser. Waiting for owner sign-in/CLI approval and optional CONNECTION match
number (never ask for password/MFA code). Pending private-state location is only
in native-progress.json; resume the exact request, one CLI command at a time.
No source upload/project/signing/cloud build yet. Full auth/offline/replay/long-
list/TalkBack/rotation/appearance/signed-performance/iOS gates remain. Hot font
change triggered a debug Router warning; cold200% and restored launches are clean.
Real healthy week/legal/payment/source/curation/human/volume gates remain. Full
goal is open; applied0110/0120 immutable, local0111–0119/0121,0122 next unreserved.

Section-count follow-up investigated — 19 November 2026: no production change.
Declared join order and disabled nested loops regress default-scope sections;
flattened materialized/inline taxonomy gives no useful speed gain. Two fresh
analyzed252-table clones preserve every original value;72 alternative comparisons
across36 baseline scenarios match (108 measured runs including baselines).
The materialized candidate passes27 synthetic checks, including null paths,
duplicate secondary paths and orphan source scope. Proposals rejected; runtime/
evidence remain the prior subject-count-order release,105-source evidence reconciles.
Exact clones/dumps/stages removed; API active,study/recovery200. No migration/mail/
restart/bank/learner write. Existing recovery0vhv3tic remains current. Reports:
reports/finna-section-count-plans-20261119/ and
reports/finna-section-count-flat-20261119/. Further measured query work and actual
healthy-week/legal/payment/source/curation/native/device/PDF/monthly-human/volume
gates remain; full goal open. Applied0110/0120 immutable,0122 next unreserved.


Subject-wise count improvement deployed — 19 November 2026: only its detail
transaction uses declared joins; other collections keep the default join setting.
The aggregate uses prepare=False to prevent cached-plan crossover across IDs.
SQL/DTO/source/cache/answer authority/scoring/writers unchanged. Global proposal
rejected after small-exam regressions; clone-only statistics never deployed.
1716full backend/exit0,641 integrated/432production compatibility,105/77bindings,
25integrity,62proposal and5paired-recovery checks pass. Fresh analyzed252-table
clone preserves every original value;68 comparisons equal,23–40% target speedup.
Live subject HTTP7.213→4.484s; both checked payload hashes identical to prior release.
Two-file scoped reader/evidence release;310source/3470static, schema/environment/
mail intact,ledger46→46,all8workers/both sites/API/recovery healthy. Current paired
recovery:/root/finna-subject-count-order-backup-0vhv3tic. Receipts:
reports/finna-subject-count-order-staged-20261119/ and
reports/finna-subject-count-order-production-20261119/. Earlier frozen proofs stay.
Desk/Atlas/referrals remain staged,0110/0120 immutable,0111–0119/0121 local,0122 next.
No new emails/migration/awards. Further slow-query review, real healthy week,
legal/payment/source/curation/native/device/PDF/monthly-human/volume gates remain.
The full goal remains open.

Collection-count improvement deployed — 19 November 2026: indexed readiness
below50k distinct questions, authoritative bulk view for larger sets, narrow
aggregate rows; membership/source/cache/DTO/scoring/writers unchanged. Earlier
ID-first and eager-global-view proposals rejected and preserved. Fresh analyzed
252-table clone preserves all original values;68 comparisons equal, large detail
16–23% faster (default JIT-off8.873→7.197s). Still slow: no all-query speed claim.
1602full backend/exit0,537 integrated/328production compatibility,105/77bindings,
25integrity and5paired-recovery checks pass. Three-file scoped release excludes
Desk/Atlas/referrals;310source/3470static files, schema/environment intact;
ledger46→46,all8workers/both sites/recovery healthy. Live subject-wise HTTP7.213s.
Current paired recovery:/root/finna-collection-adaptive-backup-xlky5zb3.
Receipts:reports/finna-collection-counts-adaptive-20261119/ and
reports/finna-collection-adaptive-production-20261119/. No mail sent or new
migration;0110/0120 immutable,0111–0119/0121 local,0122 next. Further count work,
actual healthy week/monthly human, legal/payment/source/native/device/curation/
saved-PDF/real-volume gates remain. Full goal stays open; preserve frozen proofs.

Collection-count investigation — 19 November 2026: no production release.
The ID-first/narrow-readiness proposal preserves all 68 real-data comparison
cases across eight collections/two scopes/JIT on/off; fresh analyzed dump clone
preserves all original values across 252 tables and is removed. Latency gains
are too small/inconsistent (including section regressions) to justify release;
subject-wise detail still around 8.5s. 458 integrated/249 production-only
compatibility checks and four recovery-operator checks pass; the experimental
105/77-binding candidates are evidence only. Keep the existing live digest
release and its paired recovery. No ready collection-count release scope exists.
All1509 experimental full-suite tests pass/exit0; final local reader and
binding/evidence restored to the exact prior104-source referral proof and
reconciled. See validation.json in reports/finna-collection-counts-staged-20261119/. Count optimization remains open;
all referral/Desk/Atlas drafts and real-week/legal/payment/content/native/human
gates remain. Applied0110/0120 immutable; local0111–0119/0121 remain drafts.

Latest local growth continuation — referral access (19 November 2026):
Signup-only email/Google attribution; ten current verified-key scored attempts,
both accounts verified/open, atomic seven Pro days each and five credits per
referrer per rolling year. Immutable attribution/decisions, concurrent replay/cap
locks, no historical attachment/award endpoint/native widening, no XP/points,
plan-field or provider mutation. System access has source=referral/NULL actor;
owner grants retain attribution. Private status/export/closure and once-only Inbox
receipts; no outbound referral email. Profile link creation/withdrawal and optional
Join notice/removal, Google forwarding and signup submission interlocks are staged.
Default false plus legal/recovery/live-checkout/current-evidence gates; not deployed.
1456full backend tests/exit0,387compatibility,104bindings/25integrity,3actual React
components and364-file build pass. Fresh252-table production clone preserves all
original column values;0121 applies34.556ms, real-mpsc probe rolls back. Oracle's
legacy broad default ACL was caught and explicitly revoked before narrow grants;
final suite/calibration/clone rerun pass.1280/320 light/night UI fits1265/1265 and
305/305 after correcting long-email wrapping. Exact preview DB/processes/ports/
marker/tab and remote clones/packages removed; Light/viewport restored. Both live
sites/API HTTP200; no production deployment or real awards/emails. Receipt:
reports/finna-referrals-staged-20261119/. See docs/FINNA-REFERRALS.md.
Private legal drafts prepared in docs/FINNA-LEGAL-DRAFTS.md, not published; public
operator/support/refund and other policy decisions still missing. Actual healthy
week/monthly human sign-off, paid/legal/native/source/curation/volume/saved-PDF
gates remain.0110/0120 applied immutable;0111–0119 and0121 local drafts;0122 next.
The full goal remains open. Preserve all frozen earlier proofs/recovery operators.

Latest growth release — review digest (19 November 2026): account/profile opt-in,
verified-email/address/consent checks, eligible due count/streak/Smart Review,
18:00–22:00 IST, one committed attempt per account/day, silent empty queues,
signed-out POST unsubscribe (GET inert), stale-consent/closure/privacy guards.
Shared mail capacity prioritizes recovery with reserved headroom. Withdrawal works
while paused and bypasses subscription throttles. No default subscriptions or
synthetic production emails/reviews. Initial1434 full-suite tests passed; the final
one-line throttle correction is covered by current356 integrated/178 production
compatibility tests,101/76 source bindings and25 integrity checks. Two actual React
components,363-file integrated/350-file production builds and320px light/night
QA pass. Fresh249-table clones preserve old values. Production reconstruction
excludes staged Desk/Atlas, applies only0120, retains3120 prior chunks/3470 files;
API/study/family/recovery healthy, ledger46→46/integrity0. Follow-up changes only
router/evidence; current root recovery backup:/root/finna-digest-backup-dqul4iva.
Reports:finna-review-digest-staged-20261119,finna-review-digest-production-20261119,
finna-review-digest-withdrawal-20261119. Applied0110 and0120 immutable;0111–0119
remain unapplied/local,0121 next unreserved. Natural backup/stats jobs now have
healthy completion receipts; actual healthy week/monthly human sign-off, referral/
paid/legal/native/source/volume/saved-PDF gates remain. Full goal stays open.


Latest sender setup — 19 November 2026: owner-approved three Hostinger DNS
records saved; Resend study.hawayu.in Verified/Forge Ready. Sending-only key scoped
to that domain stored in root-only /etc/mpsc/db.env; SMTP STARTTLS/auth pass,
private transfer file removed. One explicitly approved owner recovery email used
the existing encrypted outbox/reservation/send path: attempt 1 accepted, ciphertext
cleared, Resend delivered. Owner completed password reset and new-password sign-in;
server confirms consumed token, zero live reset tokens and a fresh session.
General account mail is enabled after a bounded API restart; recovery available,
API/study/family HTTP 200. No secret/link is in receipts. See docs/FINNA-EMAIL-SETUP.md
and sender evidence under reports/finna-atlas-depth-staged-20261118/. No Atlas/Desk
deployment or schema change. Digest/referral/launch and real-week gates stay open.


Latest local Atlas continuation — district proposals and cross-links (19 November):
Atlas III.5 step 4 code is locally staged: saved-exam ordering from current
published sections/live curated bindings, full list retained; owner-selected
Chronicle anchors with source fingerprints and fresh two-way event links.
Source/attribution/date/reuse and per-layer provenance are editable and visible.
Eleven private district starting proposals carry 2021 illustrative boundaries
(ODbL 1.0), approximate HQ and available river/peak points (GeoNames CC BY 4.0).
Empty layers stay empty. No current legal survey, complete reviewed district
content, real topic mapping or independent human sign-off is claimed. Owner
inspection/publication still required; proposals never auto-publish.
1415 backend tests/exit 0,337 compatibility,98 bindings/25 integrity,7 actual
components/screens and361-file final build pass. Fresh249-table dump clone
preserves all original values; real-mpsc private draft/index/two-way Chronicle
and earlier probes roll back. Browser draft/attach/preview/local publish,
synthetic binding, relevance/all toggle and map↔Chronicle exact-event roundtrip
pass;320px light/night client/scroll305/305. Preview groups/ports/exactDB/marker
and agent tabs cleaned; user's community tab retained,Light/viewport reset.
Receipt:reports/finna-atlas-depth-staged-20261118/. No production deployment.
Applied0110immutable;0111–0119local drafts,0120still next (no new migration here).
Real healthy week and source/owner curation, actual saved-PDF, mail/provider,
legal/native/paid-launch/real-volume/human gates remain. Owner selected
study.hawayu.in for Resend; configuration/DNS/delivery status is documented in
FINNA-EMAIL-SETUP.md. Preserve frozen earlier proofs/operators. Full goal open.

Latest local Atlas continuation — drills and question maps (18 November):
Atlas III.5 step 3 is locally staged: explicit pin/custom point-or-line drill
authoring, server-issued immutable activity/results, current-version exploration,
wrong-tap real-question links and optional Today suggestions. Ten distinct map
activities can fill the warm-up display but cannot qualify for a chest; drills
award zero XP/points and never change mastery, streaks or canonical attempts.
Optional fresh geography map context now uses the same AtlasMap inside ordinary
question cards/details and Smart Review; existing answer/scoring flow is retained.
Legacy quiz data is not automatically activated. No real bindings were seeded.
1407 backend tests passed (exit 0), 329 fresh compatibility checks, 96 runtime
bindings/25 integrity checks, six actual component/screen checks and a 357-file
build pass. Fresh
249-table clone preserves every original value; draft 0119 applied in 33.481 ms,
real-mpsc exploration/answer probe rolled back without economic writes.
Synthetic browser author/publish, correct/wrong tap, explored index, ordinary
practice link, Today suggestion and question map checks passed; phone 320px
light/night client/scroll widths were 305/305. Final request-reset component
regression covers account reload and changing chapter during a pending write.
Receipt: reports/finna-atlas-drills-staged-20261118/. Preview process groups,
ports, exact database/marker and agent tabs removed; user community tab retained,
Light/viewport reset. No production deployment or real healthy-week claim.
Applied 0110 stays immutable; 0111–0119 are local drafts, 0120 next unreserved.
Next: reviewed district depth, exam relevance/ordering, Chronicle links and source
licensing; actual saved-PDF, provider, legal, native, real-volume and human gates
remain. Preserve earlier frozen proofs/operators. The full goal is incomplete.

Latest local Atlas continuation — chapter Studio and reviewed data (18 November):
Atlas now reads versioned chapter data from the API; no runtime TS corpus import.
Draft0117adds immutable versions/events and per-author CAS/autosaved drafts;
draft0118seeds exactly26 unchanged chapters as current-site content, not new source
or independent review. Shared AtlasChapter renders learner and visible DRAFT
preview. /admin/atlas provides chapter/fact forms, pin/line/area drawing, draggable
vertices, palette/default/reorder/duplicate/cross-chapter layer copy/GeoJSON import,
undo/redo and captured/reorderable timeline views. Topic manager moves to
/admin/atlas/bindings; both link directions now require the current published body
hash and active registry. Chapter hold/content changes hide stale links on fresh
reads. Owner/MFA/CSRF, exact saved-preview publish, immutable attribution/history,
hold/restore and preserved conflicting author drafts; no bank/reward/native grants.
1398full backend tests/exit0,312fresh compatibility checks,94runtime bindings/
25integrity,3actual components including empty/held/undo regressions and355-file
build pass. Synthetic browser drawing/drag/undo/autosave/reopen/capture/publish/
hold/restore/import-rejection/layer-copy and1280/320px light/night QA pass without
horizontal overflow. Fresh249-table clone preserves all original values;
0117/0118apply26.320/28.293ms, real-mpsc seed/publish/hold/restore probe rolls back.
Receipt:reports/finna-atlas-studio-staged-20261118/. Preview process groups,ports,
exactDB/marker and agent tabs cleaned; user community tab retained,Light/viewport
reset. No production deployment: actual V.13healthy-week gate stays open.
0110applied/immutable;0111–0118draft locally,0119next unreserved. Preserve earlier
frozen proofs/operators. Next non-economic drill authoring/activity/explored state,
bank-question map context, district depth/relevance/Chronicle and source licensing.
Real reviewed topic bindings remain unseeded. Actual saved-PDF pagination and
provider/source/legal/native/real-volume/human gates remain. Full goal incomplete.

Latest local Atlas continuation — reviewed topic bindings (18 November):
Existing26static chapters now have a shared, explicit owner-curated binding store,
ordinary asked-from-map question panel and reverse card/detail chapter/layer/event
links. No real topic mappings inferred or seeded. Owner/MFA/CSRF, CAS decisions,
immutable save/publish/hold/restore history and exact source/registry versions;
fresh reads preserve source scope, assessment embargo and normal browse allowance.
1384full backend tests/child exit0,298fresh compatibility checks,91runtime bindings/
25integrity,55direct-call/native/Atlas checks,3actual components and353-file build
pass. Browser save→8preview→publish→5+3pages→reverse→hold-empty→restore and inline
answer pass at1280/320px light/night, no horizontal overflow. Fresh249-table clone
preserves every original value;0116apply23.557ms,100-ID empty reverse1.633ms,
real-mpsc synthetic publish/hold probe rolled back. All preview process groups,
ports,exactDB/marker and agent tabs removed; user tab retained,Light/viewport reset.
Receipt:reports/finna-atlas-bindings-staged-20261118/. No production deployment;
actual V.13healthy-week gate remains.0110applied/immutable,0111–0116draft locally,
0117next unreserved. Next full chapter lifecycle/Atlas Studio, one learner/draft
renderer and truthful26-chapter migration, then drills/explored/depth/relevance/
Chronicle/source licensing. The binding manager is not the chapter editor. Actual
saved-PDF pagination and provider/source/legal/native/real-volume/human gates stay
open. Preserve older frozen scopes/proofs. Full plan and goal remain incomplete.

Latest local Desk continuation — central-calendar room view (18 November):
Room calendar reads explicitly shared central calendar_entries rows; personal exam
countdowns and opt-in milestones use the existing owner/CAS/recurrence framework.
Private default, per-entry room choice/withdrawal, exact membership epoch, blocks,
closure, flag and native guards; no second store, copied events or new rewards.
1379full backend/exit0,250fresh compatibility/calibration,84bindings/25integrity,
13focused calendar checks, actual central form/reader/circle screen,350-file build
and final1280/320px light/night browser sharing/withdrawal checks pass. Fresh249-table
clone preserves every original value;0115apply5.251ms, real-mpsc probe rolls back.
Receipt:reports/finna-desk-calendar-staged-20261118/. Preview process groups/ports,
exact database/marker and agent tabs cleaned; other user tab retained, Light and
viewport reset. No production rollout: actual V.13healthy-week gate remains.
0110applied/immutable;0111–0115draft reservations,0116next unreserved. Preserve all
frozen earlier scopes/proofs. Desk§1.7/1.8are locally staged; actual saved-PDF
pagination is unverified. Next Atlas/Studio; provider/source/legal/native/real-volume/
human gates and the full goal remain open. Never mark the whole plan complete here.

Previous local Desk continuation — question notes (18 November):
Personal/shared notes now attach canonical question IDs; room chat links use live
same-room references and recheck source/member/block/assessment visibility. Owned
saved-note JSON export and browser print/save-as-PDF reuse account guards; hidden
notes survive unrelated full-document saves. No server PDF engine:0077 is PDF-library
inventory, and an actual PDF save/pagination remains unverified. Native new paths
stay closed, no awards.1374full backend/exit0,237fresh compatibility/calibration,
82bindings/25integrity checks,5actual components,350-file build and synthetic
1280/320px browser QA pass. Fresh249-table clone preserves every original value;
0111/0112/0113/0114apply12.143/4.216/5.174/6.531ms, real-mpsc probe rolls back.
Receipt:reports/finna-desk-notes-staged-20261118/. No production rollout; actual V.13
healthy-week gate remains.0110applied/immutable;0111–0114draft reservations,0115next.
Preview processes/database/tabs cleaned. Preserve all frozen prior scopes/proofs.
Next room view of central calendar, then Atlas/Studio and external source/provider/
legal/native/real-volume/human gates. Full goal remains open.

One design file at the owner's request (15 November 2026), consolidating
the former LEARNING-SYSTEM-V2-DESIGN.md (Part I) and
DESK-VOCAB-COMMUNITY-V2-DESIGN.md (Part II). Part 0, added the same day,
is the whole-site product design and scaling plan; it sets the priority
order everything else serves — **browsing old questions first; the point
system is deliberately secondary**. Section numbers restart per part;
cross-part references are explicit. Status: phased implementation in progress.

**Latest local Desk continuation, 18 November 2026:** synchronized practice is
implemented locally through the existing frozen party engine: ten shared question /
bookmark sources,25 seconds,2–4 current Desk members, ordinary discovery/Play caps.
Epoch/block/closure/source-withdrawal/embargo guards also run before worker scoring;
immutable Desk binding, no external join code, explicit native denial on inherited
controls. No Desk-specific awards or personal-save/mistake copies.211 fresh
calibration/compatibility checks,80 bindings, components/build/browser checks and
fresh249-table preservation pass;0113 draft applies6.105 ms with rolled-back app-role
withdrawal probe. Final validation:reports/finna-desk-practice-staged-20261118/.
Production awaits the actual healthy week.0110 immutable;0111–0113 draft reservations,
0114 next unreserved. Notes/PDF, room calendar, Atlas/Studio and external gates remain.

**Previous local Desk continuation, 18 November 2026:** shared weekly goals, review-circle
flag/resolve/reopen/filters and opt-in current focus board are implemented and staged
locally. Production remains on the V.12release below; no genuine healthy-week
receipt is claimed. Draft0111/0112rehearsed13.590/4.693ms on fresh249-table clone,
preserving every original value. Real-mpsc rolled-back consent/goal/privilege probe,
1352full backend/exit0,15goal+recovery checks,3actual components/build and browser QA pass; receipts tracked
in reports/finna-desk-goals-staged-20261118/. Existing scoring/timer/recap/flag and
non-economic rules reused; new native paths stay closed.0110latest applied and
immutable;0113next unreserved locally. Synchronized practice, notes/PDF, room view
of the central calendar, Atlas/Studio and actual provider/launch/source/device/human
prerequisites remain. V.13production gate is retained; this is not plan completion.

**Latest implementation checkpoint, 18 November 2026:**
V.12 question-detail performance correction is deployed (18November2026).
get_question reuses existing bounded readiness/publication helpers; every other
question-router AST node/writer is identical. The unchanged helper is newly source-
bound (73total); fresh156calibration/compatibility checks,1335full backend/exit0
and2supplemental reader/evidence recovery checks pass. No scoring/source/visibility
rule or schema change. Actual clone83,383canonical statuses/reviewed flags match
with0mismatches,2scopes/JITon+off/missing/outside payload parity,249-table complete
preservation. Derived detailSQL~4.4s→3–4ms. Final fresh candidate/compatible-prior
249-table rehearsal matches statuses, preserves all rows and cleans clone/dump.
Live3API/evidence hashes match;5detail HTTP samples19–30ms,SQL2.8–5.4ms, answer
material absent and status/provenance correct. All8workers healthy,3account/
27private+3public learning reads plus5detail samples,25reward/3edit/2bulk counters0,
ledger46→46,mail0,bothsites200. Static348built/3344served,Python env/requirements,
PSQL logging/rotation,restore tool/13collector+unit files unchanged.0110immutable,
next0111. No bank/workshop/provider changes or synthetic production activity.
Receipt:reports/finnaplan-v12-query-performance-20261118/README.md.
Backup:/root/finna-v12-query-performance-backup-scpanrxd. Exact-source recovery
restores prior3-file reader/evidence pair, only restarts API and never restores
DB/history/static/environment. Later drift refuses recovery; target is frozen,
never replay this or older releases. Current baseline overlays3API files on the
build release’s3344static/new env/logging profile. All candidate/fullsuite/clone
processes completed; no preview/tab/temporary DB remains. No production recovery.
Other observed collection-count shapes~1–1.6s remain separately profiled. Build-only
picomatch advisory unpatched; runtime npm/Python dated audits clean. Monthly human
sign-off/real log review, natural backup/stats outcomes and a full healthy week
remain open. Desk/Atlas/Studio are the later build-order phase; current source audit
must distinguish existing desk toolbox/timer from missing v4 extensions and static
26chapter Atlas from missing curated bindings/Studio. See remaining index. Real
email/digest/referral/paid/legal/native/exam-source prerequisites remain. Full goal
stays open; never reset or complete it for a slice.

**Previous frontend build checkpoint (historical):**
V.12 frontend build-dependency remediation is deployed (18November2026).
Vite5.4.21→6.4.6,esbuild0.21.5→0.25.12,selector-parser6.1.4→6.1.6; all browser-runtime
npm versions unchanged. Runtime-only advisory scan0; full build graph retains11
package-chain findings from one unpatched picomatch GHSA-fc5q-39xc-vjpf (published
v2/v4 latest2.3.2/4.0.7). No risk acceptance/whole-project-clean claim. Four real
component/navigation scripts, build, two supplemental static recovery checks and
built-artifact1280/320px light/night QA pass.6887CSS AST entries keep rules /
declarations/cascade;15differences only media whitespace. Desktop1265/1265and
phone305/305no overflow; phone private search/all5sections and learner library pass.
No new full backend suite claimed for this static slice; preceding1324remains.
348built/3344served hashes,2996retained old chunks,17route shells/2entry assets
verified. API PID/environment/source/schema/PSQL config/restore-tool/13host paths
unchanged. All8workers healthy,3accounts/27private+3public learning reads,integrity0,
ledger46→46,mail0,bothsites200.0110immutable,next0111. Six synthetic screenshots;
preview API/web/tab/exactDB/marker cleaned,viewport reset. Native/device not certified.
Receipt:reports/finnaplan-v12-build-dependencies-20261118/README.md.
Backup:/root/finna-v12-build-dependencies-backup-vjq_0cd7. Exact-source recovery
restores prior HTML/assets while keeping newer immutable chunks for open tabs;
no service restart or DB/history rollback. Newer drift refuses recovery. Target
is frozen; never replay it or older dependency/logging/maintenance targets.
Actual initial log review (query-logging report/initial-log-review.json) captured
15duration entries since the real probe:1probe+14others,max4522.711ms. This is a
short observed window, not a long-term or human-signoff claim. Investigate query
shapes next using private logs/normalized aggregate metadata, never export bind
values or mark the healthy week complete. Source/runtime baseline now comes from
the build-dependencies scope (3344served) plus the deployed package/logging receipts.
Other email/paid/legal/native/exam-source/monthly-human/full-week/later product gates
remain open; continue the full goal without resetting/completing it for a slice.

**Previous query-logging checkpoint (historical):**
V.12 PostgreSQL slow-query logging is deployed (18November2026). Threshold1000ms,
bind parameter/error parameter lengths0; existing stderr/0640log and weekly10-file
rotation preserved. Three audited defaults changed via ALTER SYSTEM + reload only;
API PID/PostgreSQL start time unchanged.5operator checks pass. Actual read-only
mpsc probe logged1102.161ms; bind canary absent, no raw queries/values exported.
Exact source/environment/schema/static/collector/rotation guards pass,8workers
healthy,integrity0,ledger46→46,mail0,bothsites200. No schema migration;0110immutable,
next0111. This starts evidence collection today, not historical slow-query review.
Receipt:reports/finnaplan-v12-query-logging-20261118/README.md.
Backup:/root/finna-v12-query-logging-backup-9_m32fsh has private prior auto-conf and
exact operator/scope. Recovery refuses drift, resets only these3keys and verifies
prior config; never resets database/history or restarts services. Production
recovery not invoked. Frozen logging target must never be replayed.
Maintenance and Python dependency releases below remain current. Frontend npm
advisories, monthly human sign-off/actual log review, scheduled backup/stats outcomes
and full healthy week remain open. Continue independent frontend remediation;
email/digest/referral, paid/legal/native/exam-source and later product gates remain.

**Previous dependency checkpoint (historical):**
V.12 Python dependency remediation is deployed (18November2026). FastAPI0.163.2,
Starlette1.10.0 and their3fixed purepy dependencies installed from5SHA256-bound
local wheels, entirely offline on Oracle. All other production versions retained.
Actual live package versions exactly match the clean dated advisory input; this
is not a blanket/npm/future security guarantee.1324full framework backend checks,
81focused and2supplemental environment/wheel/recovery checks pass. Fresh249-table
clone under the staged Oracle environment preserves every original row; real-mpsc
learning/economy verification passes.2971installed environment-file fingerprints,
requirements and versions verified after atomic environment swap. API/static /
schema/economy bindings/restore-tool/13host collector+unit paths unchanged. All8
workers healthy,ledger46→46,25reward/3edit/2bulk integrity counters0,bothsites200,
0mail attempts. No synthetic production activity or database rollback.0110stays
immutable,next0111. Source/test changes here are requirements + bounded operator /
recovery guards; frontend markup and artifacts unchanged.
Receipt:reports/finnaplan-v12-dependencies-20261118/README.md.
Backup:/root/finna-v12-dependencies-backup-afhwfwbb stores exact prior environment /
requirements; recovery refuses later API/static/schema/environment/tool/unit drift
and never restores DB history. Frozen dependency target must never be replayed.
Local api/.venv updated from the same5offline wheels; pip check passes. Separate
candidate fullsuite completed515.23s,exit0; no running preview/test/clones remain.
Next: bounded slow-query logging with parameter suppression and existing rotation;
frontend npm findings remain separate. Monthly human sign-off, green week, real
scheduled backup/stats outcomes, email/digest/referral and launch/native/source /
later product work remain; full goal stays open.

**Previous maintenance checkpoint (historical):**
V.12 retention/site notice/restore maintenance is deployed (18 November2026).
0110is applied and IMMUTABLE; next migration0111. Hourly account cleanup keeps
progress/finance/adoption/durable replay receipts and original activity timestamps;
empty-guest filtering protects default/profile/access state, legacy actor IDs and
future/alternate/composite FKs.5s/1s limits,500transient/20guest batches and heartbeat
counts apply. Native notice/admin paths stay closed. Owner/MFA/CSRF/versioned
plain-text site notice has IST expiry, minute refresh and immutable account audit.
Initial live setting is blank; no synthetic production announcement.
1324full backend checks/exit0,154final source-bound compatibility/calibration /
72runtime bindings,25focused maintenance/9restore/2operator recovery checks
(overlap), real components/build and1280/320px light/night QA pass. Native guard
assertions were added after full collection and pass in the154final run; exact
runtime inputs unchanged. Final fresh248-table clone preserves every original
row; migration29.253ms,actual-mpsc rolled-back retention/notice/protection probe and
compatible prior readers pass. Live0110apply95.136ms.11API/348built/3211served
hashes match,2863retained chunks,284unchanged API/schema dependencies and13host
collector/unit paths protected.3real accounts/3public+27private learning reads,
25reward/3edit/2bulk integrity counters0,10tier+5bulk triggers,ledger46→46,
mail attempts0,bothsites200. All8workers healthy; real first sweep removed8expired
review budget buckets,0accounts/sessions/other records. Bank-review/host timer
healthy; natural backup/stats job receipts unknown, not backfilled.
Actual monthly paired restore completed18Nov10:17:14UTC from17Nov20:20:08UTC backup:
232archived tables/124944files,real read-only-role bank pairing and full cleanup.
Ops shows0days since success, attention at40days; verified restore tool installed.
Monthly human sign-off remains pending. Agent-assisted audit found dependency
advisories and disabled slow-query logging; TLS/bothsites200 and logrotate active.
No dependency-clean, whole-checklist, offsite/source completeness, device or real
healthy-week claim. No bank/workshop/Caddy/provider changes or production recovery.
Receipt:reports/finnaplan-v12-maintenance-20261118/README.md.
Backup:/root/finna-v12-maintenance-backup-n3jzh49v. Exact-source recovery preserves
0110,all DB history, retained-activity account reader and verified restore/tool /
collector paths; other API/static return to prior pair. Newer drift refuses recovery.
Frozen target finnaplan-v12-maintenance must never be replayed. Local preview API /
web/tab/exactDB/marker removed,viewport reset; five synthetic PNGs retained.
Next independent work: dependency/security and slow-query observability follow-up.
Separate /tmp/finna-security-candidate-20261118 contains FastAPI0.163.2/Starlette1.10.0,
81targeted checks and clean candidate advisory scan after pip upgrade; no package
or requirements update deployed yet. Existing api/.venv stays unchanged. Candidate
reports remain supplemental in maintenance report; move next work into a new
source-bound release, never rewrite frozen maintenance proofs. Email/digest/referral,
real healthy week, later Desk/Atlas/Studio, exam sources/native/device/legal/paid
launch prerequisites remain. Continue the full goal; never mark complete for a slice.

**Previous account-viewer checkpoint (historical):**
V.12 read-only account viewer is deployed at /admin/users (18 November).
Exact-email/literal-handle search and per-account account/access/study/economy /
community summaries use a repeatable-read/read-only snapshot,5s statement limit,
global-owner permission and the existing staff MFA/exact-ID exemption policy.
Native bearers and scoped owners are denied. No viewer mutations, answer history,
private desks, credential/device material, ledger item notes/keys or block identities.
Entitlement uses account_has_pro(); scoring and community rules reuse live helpers.
Search/results/selection clear across auth transitions; late responses are discarded.
44targeted compatibility checks,10final account/recovery and2separate recovery
checks (overlap), build, real component/navigation and1280/320px light/night QA pass.
Phone search controls stack; no overflow (1280/1280desktop,320/320phone). No new full
suite claimed for this read-only slice; preceding1277full/exit0 remains historical.
Final fresh248-table production-dump clone preserves every row. Live real-mpsc
read-only snapshots cover3accounts (12–29ms each),3public+27private learning reads,
25reward/3edit/2bulk counters0,10tier+5bulk triggers,ledger46→46,economy reconciled,
0mail attempts.3API/348built/3086served hashes,2738retained chunks and288unchanged
API/schema dependencies verify;13collector/unit paths stay fixed.9route shells,
anonymoususers401,runbook hash andbothsites200 pass. All7workers,bank-review/host
timer anddisk/backup probes healthy; first natural backup/stats outcomes unknown.
No migration, bank/workshop/Caddy/provider/dependency change, synthetic production
activity or commit.0109immutable; next0110. Mail/checkout remain disabled.
Receipt:reports/finnaplan-v12-users-20261118/README.md.
Backup:/root/finna-v12-users-backup-8eqzsmv9. Exact-source recovery guards installed
API/schema/static/collector/unit hashes and restores prior reader/static pair;
all history/writers/collectors stay.2disposable recovery checks pass; production
recovery not invoked. Never replay older frozen targets over this release.
Preview API/web/tab and exact final/interrupted disposable DBs removed; marker
cleaned,Light/viewport restored,user help tab retained. Four final synthetic PNGs.
Next independent work: V.12retention, site notice andmonthly checklist/actual
restore receipt; genuine healthy-week gate needs elapsed operation. V.11actual
email/digest/referral prerequisites,later Desk/Atlas/Studio work,V.7actual sources,
native/device andlaunchgates remain. Whole plan stays open. The user has explicitly
started a new unbounded active goal,finish without interruption; continue it and
never reset it or mark it complete for a single slice. Older usage-limited goal
notes below are historical and do not describe the current active goal.

**Previous collector-time checkpoint, 18 November 2026:**
V.12 cycle/collector release and final timer-time display correction are deployed
(18 November). Assessment/desk/calendar/game cycles, explicit mastery failures,
real additive bank/backup/stats outcome hooks and the five-minute host collector
now feed /admin/ops. Disk and newest paired-backup digest/index verification are
healthy; all seven worker observations are healthy. Natural bank-review execution
has a healthy receipt; backup/stats outcome hooks await their next scheduled runs,
with no historical successes backfilled. Mail worker health does not mean email
delivery: mail and checkout remain disabled. No green-week/restore claim.
The final read-only classifier uses a structured collector outcome instead of the
in-process100ms timestamp tolerance: collection/hash/peer-write latency cannot
create false attention. A normal-zero-exit requirement still guards timer success;
failed/stale/future/malformed receipts keep their own states. This correction
changes only ops.py; static2961files,collector/units,schema and68economy-bound
sources remain unchanged. No new full suite is claimed for the reader repair:
1,277full tests with exit0 precede only this read-only change;11focused regressions
and actual-mpsc production read-only candidate/live checks cover it. Worker release
also has118fresh calibration checks/68bindings,248-table exact preservation and
rolled-back real-role probes, build/components/navigation and1280/320px light/night
QA. Full release9API/347built/2961served/2614retained chunks/280unchanged dependencies
and6collector/unit hashes verify. Final live3public+27private learning reads,
25reward/3edit/2bulk counters0,10tier+5bulk triggers,ledger46→46,economy reconciled,
0mail attempts,anonymousops401 andbothsites200. No migration, bank/workshop/Caddy /
provider/dependency change, synthetic production activity or commit.0109immutable;
next0110. Only real operational heartbeat rows are added by collection.
Receipts:reports/finnaplan-v12-workers-20261118/README.md and
reports/finnaplan-v12-collector-time-20261118/README.md.
Worker backup:/root/finna-v12-workers-backup-9r_rlztk.
Final reader backup:/root/finna-v12-collector-time-backup-5atf23ce. Latest reader recovery restores only its exact
prior classifier after API/schema/static/unit/collector drift checks; current
writers,installed collectors and history stay. Do not invoke the older whole-worker
recovery over this reader update; its hash guard refuses. No production recovery
invoked. Initial preflight staging-cleanup permissions were fixed before release;
private temporary stages removed. Preview API/web/tab/DB marker cleaned,Light /
viewport restored,user help tab retained (IAB surface2→4). Five synthetic PNGs.
Next independent implementation: read-only /admin/users account viewer, then
retention/site notice/monthly checklist and actual restore/healthy-week evidence.
Observe first natural backup/stats outcomes. V.11actual email/digest/referral,
later product/real-volume ranking,V.7actual sources,native/device andlaunchgates
remain. Whole plan open; do not resume/reset usage-limited goal automatically.

**Previous worker release checkpoint, 18 November 2026:**
V.12 worker cycles and host collectors are deployed (18 November). Assessment,
desk retention, calendar and game cycles now write transaction-bound success /
bounded post-rollback failure receipts. Mastery failure labels are explicit;
last success survives failure. Desk notes show aggregate purge counts. Existing
mail/nightly receipts remain; worker health does not certify email delivery.
Exact additive outcome hooks on bank-review, paired-backup and stats jobs require
actual SERVICE_RESULT plus normal zero exit; original jobs/schedules are preserved
and none is manually started for proof. A new five-minute host collector measures
disk and verifies the newest backup pair's archive/dump digests plus dump index.
Root-only metadata/identity cache invalidates changed files; newest incomplete /
corrupt evidence fails visibly with no older fallback. Backup creation/collection
times are distinct;15minute collection/48hour backup staleness and10GiB disk warning
render. This is not a restore rehearsal or a green-week claim. First daily job
outcomes remain unknown until actual runs; none is backfilled. Mobile Questions
navigation preserves needs-review.
1277full backend tests pass with explicit process exit0.45targeted,14collector,
24final focused and2operator-recovery checks (overlap),118fresh calibration /
compatibility checks with68runtime bindings/25diagnostics, local build/components /
navigation and1280/320px light/night browser QA pass. Fresh248-table dump clone
preserves every row; actual-mpsc synthetic heartbeat/collector writes fully roll
back. Live3public+27private learning reads,25reward/3edit/2bulk counters0,
10tier+5bulk triggers,ledger46→46,economy reconciled,0mail attempts.9API/data,
347built/2961served hashes,2614retained chunks,280unchanged dependencies,
6collector/unit files,8shells,anonymous401/runbook hash andbothsites200 verify.
No migration, bank/workshop/Caddy/provider/dependency change, synthetic production
activity, success backfill or commit. Only real operational heartbeat rows are
added by collection.0109immutable;next0110. Mail/checkout remain disabled.
Receipt:reports/finnaplan-v12-workers-20261118/README.md.
Backup:/root/finna-v12-workers-backup-9r_rlztk. Recovery validates API/schema/static/base-unit/drop-in/collector
hashes, disables only the new host timer and restores the exact prior compatible
API/economy evidence/static pair. All history/heartbeat rows and original units /
schedules stay; disposable drift/recovery checks pass,production recovery not
invoked. Never replay frozen targets. Final browser reconnect changed IAB2→4;
preview tab/API/web/DB cleaned,Light/viewport restored,user help tab retained.
Next independent implementation: read-only account viewer, then retention/site
notice/monthly checklist and actual restore/healthy-week evidence. Observe first
natural backup/stats outcomes. V.11actual email/digest/referral, later product /
real-volume ranking,V.7actual sources,native/device andlaunchgates remain.
Whole plan open; do not resume/reset the usage-limited goal automatically.

**Previous ops dashboard checkpoint, 18 November 2026:**
V.12 read-only ops dashboard is deployed at /admin/ops (18 November). The
owner-only, web-only API uses a repeatable-read/read-only snapshot with a5s SQL
statement limit. Existing mail/mastery receipts, separate legacy reassessment
observation, explicit missing/stale/attention states, real per-process pool
occupancy, IST-yesterday mint/redemption/cap totals and bounded human-review
flags, plus five moderation queues with median age/48h counts are available.
Refresh and auth transitions discard old snapshots; failure is never empty data.
Runbook links and desktop/mobile admin navigation work. Worker instrumentation,
timer/disk/verified-backup collectors and live webhook metrics are NOT completed
by this slice; unknown rows remain explicit. No healthy-week claim.
44focused compatibility checks plus7final ops/recovery checks (overlapping suites),
real component/navigation checks, build and1280/320px/light/night synthetic browser
QA pass. No new full-suite run for this read-only slice; the prior full1259-case
bulk baseline remains historical. Fresh248-table production-dump clone preserves
all existing rows. Real-mpsc RR/read-only reads,3public+27private learning checks,
25reward/3edit/2bulk counters0,10tier+5bulk triggers,ledger46→46,economy reconciled,
0mail attempts.4API,347built/2838served hashes,2491retained chunks and284unchanged
dependencies verify;8route shells,anonymousops401 andrunbook hash pass;bothsites200.
No migration, economy-bound writer/evidence, bank/workshop/provider/unit/dependency
change, synthetic production activity or commit.0109immutable; next0110.
Receipt:reports/finnaplan-v12-ops-20261118/README.md.
Backup:/root/finna-v12-ops-backup-52_pa_zk. Exact-source recovery restores only prior
ops readers/router registration/pool helper/static; all current writers/schema /
history stay. Drift refusal and recovery tested in disposable files, production
recovery not invoked. Never replay frozen release targets. Preview tab13/API/web /
DB cleaned; Light/viewport restored and original user tab retained.
Next: standard cycle receipts for assessment/desk/calendar/game, actual timer /
backup/disk collectors; then account viewer, retention/site notice/checklists and
actual green-week evidence. V.11email/digest/referrals, later Desk/Atlas/Studio,
real-volume ranking,V.7actual sources,native/device and launch gates remain.
Whole plan stays open; do not resume/reset the usage-limited goal automatically.

**Previous bulk-pricing checkpoint, 18 November 2026:**
V.11 bulk ₹50 next-subscription pricing is deployed (18 November). Existing
owner Rewards & accounts has100-email preview/apply batches with exact preview
hashes and durable retries, verified-email-only matching at add/signup verification/
successful login, once-only application and retained removal history. Typed email
alone never matches. Optional pricing runs after identity commit and cannot block
sign-in. Group links prefill an explicit claim form; server-fixed5000paise,
100uses/30days defaults (bounds1–1000/1–90), per-code/account receipts, cap/expiry/
revocation and actual-price replay hold. No Pro/points/payment/provider action.
Owner search reaches retained emails/codes/notes; on-demand50-row cursor receipts
show who claimed, including revoked/expired/anonymous closed history. New routes
stay web-only; owner/MFA/CSRF/origin/account/version boundaries and own-data exports
hold. Existing mandates and manual account-price authority remain.
1,259full backend cases pass with explicit process exit0, then11focused final
read-only receipt checks;68earlier targeted/28boundary/2recovery checks. Final
104source-bound calibration/compatibility checks retain67runtime bindings and25
reward diagnostics. Build, real components/10redirects/111links and1280/320 light/
night synthetic browser QA pass,305/305px no overflow. Full suite precedes only
the final read-only receipt reader; that reader has focused/current calibration,
actual-mpsc clone and browser proof. Initial terminated/interrupted runner logs
remain historical. Fresh244-table clone preserves every prior row,0109apply
35.566ms; verified-once/batch/code replay/cap/revoke/owner-receipt probe fully rolls
back. Live3public+27private RR/read-only checks,25reward/3edit/2bulk counters0,
10tier+5bulk history triggers,ledger46→46,economy reconciled.11API/data,
345built/2713served hashes,2368retained chunks,274unchanged dependencies and8shells
verify; bothsites200.0code redemptions at apply, no agent production list/code/
discount, synthetic learner, bank/workshop/provider/billing/unit/dependency change
or commit. Mail disabled/unconfigured,0attempts; checkout/catalog remain closed.
0109applied/immutable; next0110. Receipt:
reports/finnaplan-v11-bulk-20261118/README.md. Backup:
/root/finna-v11-bulk-backup-0wysk7wv. Guarded recovery keeps0109/current compatible
pricing/auth/export/mail/onboarding/CMS/shared API and all histories, pauses only
new bulk assignment and restores prior static. Economy remains reconciled under
pause; disposable recovery passes, production recovery not invoked. Never replay
frozen targets or restore older writers.17synthetic PNGs include readable owner
claim receipts; tabs10–12/API/web/DBs cleaned, viewport/Light restored, original
user help tab retained. Native/device certification remains open.
Remaining index:docs/FINNA-REMAINING.md. V.11 still needs actual email delivery /
verification/recovery activation, opt-in digest with consent/unsubscribe, and
post-launch qualified/capped referrals. V.12ops dashboard/timer collectors, account
viewer, retention/site notice/checklists and actual green-week evidence remain;
next independent build is ops. Later Desk/Atlas/Studio, real-volume ranking,
V.7actual exam sources, native/device and catalog/legal/checkout gates remain.
Whole plan remains open; do not resume/reset the usage-limited goal automatically.

**Previous check-in checkpoint, 18 November 2026:**
V.11 optional primary-exam check-in is deployed (18 November). Today/account
study setup links to ten eligible distinct official-key questions, mixed by actual
approved active subjects/topics. One ordinary saved practice set/account/exam
resumes across retries/devices; selecting another primary preserves progress.
Normal source-bound grading, mastery, discovery caps and immutable feedback stay
in force; loading status creates no activity/earning plan and there is no bonus.
Finished suggestions use exact checked receipts/current eligibility; viewed,
skipped and excluded answers are not evidence. Existing focus stays until the
learner explicitly selects and saves. No exam-readiness claim. New endpoints and
inherited saved-set paths stay outside native capabilities; old recent lists
hide the marker. Account/primary change and request-key boundaries hold.
1,247full backend tests,55targeted/46boundary checks,2operator-recovery checks,
91fresh calibration/compatibility checks (61runtime bindings/25diagnostics), build,
actual components/10redirects/111links and1280/320px/light/night synthetic browser
QA pass. Fresh244-table dump preserves every existing row;0108apply5.177ms and
fully rolled-back real-mpsc10-check probe pass. Live3public+24private reads,
25reward/3edit counters0,10tier triggers,ledger46→46,economy reconciled.7API/data,
345built/2591served hashes,2246retained chunks,273unchanged dependencies and8shells
verify; bothsites200.0production check-in sets at apply; no synthetic learner /
award/bank/workshop/provider/billing/unit/dependency change or commit. Mail remains
disabled/unconfigured with0attempts.0108applied/immutable; next0109. Receipt:
reports/finnaplan-v11-onboarding-20261118/README.md. Backup:
/root/finna-v11-onboarding-backup-eoupr387. Recovery retains0108/current compatible
onboarding/mail/CMS/shared writers and all history, pauses only new check-in starts
and restores prior static. Pause preserves source-bound economy reconciliation;
changed writers still invalidate it. Disposable recovery passes; production
recovery not invoked. Never replay frozen targets or restore older writers.
Browser sample5correct/3wrong/1viewed/1skipped; only Mizo suggested from1/4 vs
English4/4, explicit saved focus survives reload. Clean screenshot:
reports/finnaplan-v11-onboarding-20261118/checkin-summary-desktop.png. Full-page
fixed-header artifacts/timing limits documented; preview tab/API/web/DB cleaned,
Light/viewport restored, original user tab retained. Native/device certification
remains open. Next V.11: opt-in due-review digest needs actual email transport /
consent/unsubscribe; referral stays post-launch/attempt/cap gated; bulk pricing
remains. V.12ops/users/retention and later Desk/Atlas/Studio, real-volume ranking,
V.7actual sources and catalog/legal/email/checkout activation remain. Whole plan open.

**Previous sharing checkpoint, 18 November 2026:**
V.11 public question/test share previews are deployed (18 November). Question
More copies a public source-bound HTML preview and offers WhatsApp; published
tests use their live immutable metadata. Escaped question/exam/year, Finna OG/
Twitter metadata and shared1200×630brand PNG replace bare links; explicit Open
links retain crawler metadata. No answers/private context, awards or messages.
Unavailable/exact-source/scope/native guards and current-item copy outcomes hold.
1,236full backend tests,12targeted,1operator-recovery,81fresh calibration checks
(58runtime bindings/25diagnostics), build/components and1280/320px/light/night
control QA pass. Fresh244-table dump preserves all rows;3public+21private reads,
25reward/3edit counters0,10tier triggers,ledger46→46,economy reconciled.4API/data,
344built/2469served hashes,2125retained chunks,273unchanged dependencies and8shells
verify; bothsites200. Mail remains disabled/unconfigured with0attempts. No SQL,
bank/workshop/learner/provider/billing/unit/dependency changes or commit.0107stays
applied/immutable; next0108. Receipt:reports/finnaplan-v11-sharing-20261118/README.md.
Backup:/root/finna-v11-sharing-backup-2__tbumw. Guarded recovery restores only prior
share/question readers, matching evidence/static and removes the new helper;
current mail/review/CMS/history remain. Disposable recovery passes; production
recovery not invoked. Never replay frozen targets. Shared thumbnail is brand art;
actual question/source is OG text. WhatsApp rendering/cache and OS-dark standalone
preview are not certified; browser clipboard success feedback is distinct from
empty session readback (exact payload/fallback covered in component tests).
Next independent V.11work: onboarding diagnostic; digest needs actual mail plus
consent/unsubscribe, referral retains post-launch gates, bulk pricing remains.
V.12ops/users/retention and later Desk/Atlas/Studio, real-volume ranking,V.7sources,
native/device and catalog/legal/email/checkout activation remain. Whole plan open.

**Previous built-in mail checkpoint, 18 November 2026:**
V.11 built-in account-mail durability/free-tier controls are deployed (18November).
Finna owns the encrypted verification/reset queue and background worker. Durable
capacity commits precede SMTP; concurrent processes share100reservations/UTCday
and a conservative3,000/rolling31days. Pending live links count at admission;
known/unknown reset requests get the same temporary-capacity response. Bounded
stable-key retries, uncertain lease recovery, closure/token rechecks and actual
worker heartbeats retain queue/privacy/history. Pauses preserve pending ciphertext;
completed account links retain their original one-use/MFA guards. No native
allowlist widening, new endpoint, frontend, dependency or unit-file changes.
1,229full backend tests,36account-focused checks,74fresh calibration/compatibility
checks (58runtime bindings/25reward diagnostics) and guarded recovery pass. A fresh
243-table dump preserves every old row;0107apply15.84ms and a fully rolled-back fake
SMTP probe pass.7API/data hashes,unchanged342built/2346served hashes,268unchanged
dependencies and8shells verify.21private learning reads +mail-capacity reads,
25reward/3edit counters0,10tier triggers,ledger46→46,reconciled economy and both
sites200. Runtime environment and public recovery availability confirm delivery
still disabled/unconfigured;0mail attempts, no SMTP contact, provider account,
sender/DNS/credential/billing/checkout activation, production fixture, bank/workshop
change or commit.0107 is applied/immutable; next0108. Receipt:
reports/finnaplan-v11-mail-20261118/README.md. Private backup:
/root/finna-v11-mail-backup-e2iq_wio. Recovery retains0107/full compatible API /
economy and every capacity/history record, pauses new mail and keeps ciphertext;
never restore older mail/review writers. Production recovery not invoked. Never
replay frozen targets. Resend is the target within the owner's free-tier preference;
actual account/verified domain/sender/private key and delivered one-use recovery
proof remain required. Setup:docs/FINNA-EMAIL-SETUP.md. Next independent V.11work:
share cards, onboarding, opt-in digest, post-launch referral gates and bulk rates;
exam taper already exists. V.12ops/users/retention and later Desk/Atlas/Studio,
real-volume ranking,V.7actual sources,native/device QA and catalog/legal/email /
checkout activation remain. This is not completion of the entire plan.

**Previous curated-practice checkpoint,18November2026:**
V.10 curated vocabulary practice and mixed Smart Review are deployed (18November).
Published Content Studio revisions supply reviewed English/Mizo word cards with
server-scored meaning, usage cloze and both translation directions (reverse mode
requires authored gloss choices). Current publication/Pro/block/source eligibility,
immutable feedback and typed shared Leitner dates remain. Five new cards/day is
shared with Bank vocabulary; due reviews remain available. Distinct-word progress,
retained words, decay and exact14-day finished-review mastery proof are separate
from awards. Curated cards never mint per-card XP/points or canonical attempts;
actual sourced grades feed the existing session/quest receipts and original caps.
New web format negotiation keeps old web/native queues compatible and rejects
mixed saved-set replays without the updated reader; no native allowlist widening.
1,217full backend tests,63final targeted,63source-bound calibration/compatibility
checks (53runtime bindings/25diagnostics), build/components and synthetic desktop/
320px/light/night browser QA pass.232-table dump preserves every old row;0106apply
99.489ms, rolled-back real-role probe passes.16API/data,342built/2346served hashes,
2004retained chunks,256unchanged dependencies and8shells verify.21new single-
snapshot private reads plus39independent tier checks,25reward/3edit counters0,
10tier triggers, ledger46→46, reconciled economy and bothsites200. No real cards
published, synthetic production activity, bank/workshop/provider/billing/unit/
dependency changes or commit.0106 is applied/immutable; next0107. Receipt:
reports/finnaplan-v10-curated-vocabulary-20261118/README.md. Private backup:
/root/finna-v10-curated-vocabulary-backup-_zbs4kcm. Recovery keeps0106/full compatible
CMS/shared API/economy, pauses curated writes and restores prior static; every
revision/grade/session remains. Disposable recovery passes; production recovery
not invoked. Never replay frozen targets or restore older writers over0106.
Next: V.11growth (Resend free-tier target; built-in queue, actual sender/domain/
credentials still needed), then V.12ops/users/retention and later Desk/Atlas/Studio.
Ranking needs real volume; V.7actual sources, native/device QA and catalog/legal/
email/checkout activation remain gates. This is not completion of the whole plan.

**Previous word-card authoring checkpoint,18November2026:**
V.10 curated vocabulary authoring is deployed (18 November). Content Studio
supports reviewed English/Mizo–English word cards, meanings, usage, glosses,
source/editorial notes, recognition choices and authored cloze prompts. Existing
immutable material revisions, exact owner review, Pro/body redaction and blocks
remain. Incomplete drafts save; submission/publication require valid distinct
choices, a single gap, bilingual gloss and actual exam/active-subject tags. Legacy
block serialization/retry shapes are unchanged. No production cards were authored
or published, no canonical content changed and no per-card award path was added.
This is authoring/reading, not curated learner practice or a words-known counter.
1,202 full backend tests,13final workflow/recovery checks plus1final recovery,
build, real-screen checklists and desktop/320px/light/night synthetic browser QA
pass. Candidate/live normalization checks preserve the1existing material revision;
9private learning reads, ledger46→46,22integrity counters0 and economy reconciled.
2API,341built/2223served hashes,1882oldchunks,266unchanged dependencies and8shells
verify; bothsites200. No SQL/provider/billing/bank/workshop/unit/dependency changes
or commit.0105 remains applied/immutable; next0106. Receipt:
reports/finnaplan-v10-vocabulary-authoring-20261118/README.md. Backup:
/root/finna-v10-vocabulary-authoring-backup-b9v_d6_p. Guarded recovery restores
prior parser/static, retains0105/current queue/economy and every authored revision;
new-format drafts require the compatible parser to edit/publish after recovery.
Disposable recovery passes; production recovery not invoked. Never replay frozen
targets or restore older queue writers over0105. No mobile endpoint widening;
new block native rendering is not certified. Next: curated scoring, current-review
eligibility, shared sessions/queue and distinct-word progress. Later V.11/V.12/
Desk/Atlas/Studio, real-volume ranking, V.7actual sources and native/device QA
remain; catalog/legal/email/checkout launch stays closed.

**Implementation checkpoint, 17 November 2026:** V.1 browse performance and
§0.9.2 combined-filter metering are deployed (migrations0090–0091), alongside
the previously shipped §5.5. Anonymous public catalog transport, validators,
private learner guards, allowance UI and release checks are recorded in
`reports/finnaplan-v1-20261117/README.md`. V.2 mastery/review, Today, progress rollups, focus,
calendar read layers, web screens, login backoff and the missing Daily Five
connection are deployed too (migrations0083 and0092,978 tests). A full-dump clone
rehearsed schema plus initial reconciliation while preserving all existing rows;
all deployed hashes and16 private read-only route checks passed. No seed awards
were minted (ledger46→46). See `reports/finnaplan-v2-today-20261117/README.md`.
V.3 habit is deployed too (0093): unified account streak, fixed daily plans,
new quest rings and replay/cap/timing-gated review awards.985backend checks,
phone earning/claim/reload flow,217-table preservation and19private read-only
live checks pass; no launch backfill (ledger46→46). Receipt:
`reports/finnaplan-v3-20261117/README.md`. V.4 economy is deployed too
(0094–0096): limits, completion/milestone/contribution awards,400/1500-point
catalog prices and a source-bound reconciliation gate.1035backend tests, seeded
seven-day calibration,221-table preservation, tested policy/catalog + file rollback,
20private role reads and12API/335static hash readbacks pass;19integrity checks0,
ledger46→46. Catalog stays disabled pending actual launch prerequisites; paid
checkout is still disabled and legal pages have not shipped. Receipt:
`reports/finnaplan-v4-20261117/README.md`. Earlier V.5 local checkpoints follow.
V.5 boards and Monday recap have a local, undeployed checkpoint:1044backend tests,
web build, responsive UI checks and read-only Oracle query rehearsal pass. A second
local checkpoint adds owned calendar entries, exam targets, recurring slots and ICS
in draft0097:1052tests, web build, phone/desktop QA and fresh229-table preservation
pass, ledger46→46. A third local checkpoint adds identity editing, moderated bios,
owner bio decisions and3curated points cosmetics, preserving all26existing avatar
records:1060tests, web build, phone UI and final229-table preservation pass.
See `reports/finnaplan-v5-profile-20261117/README.md`. A fourth checkpoint completes
legacy board/catalog transport and calendar week/Cup/shared Desk reads, plus the
composition-only owned-target Today taper:1065tests, build, desktop/320px QA and
fresh229-table preservation pass; ledger46→46. See
`reports/finnaplan-v5-integration-20261117/README.md`. Actual Desk event scheduling
has no current store and remains with the later Desk upgrade. Account self-service
now has a local checkpoint too: four Profile groups, owned JSON export, sign out
everywhere and guarded anonymous closure.1073tests, build, responsive QA and229-table
preservation pass; ledger46→46. See `reports/finnaplan-v5-account-20261117/README.md`.
V.5 is now deployed through bounded finnaplan-v5:1081backend tests,229-table
preservation,36private read checks,28API/337static hashes and22integrity checks0
pass; ledger46→46.0097 is applied/immutable; next free0098. Calibration now binds39
runtime artifacts and actual launch checks include cosmetic spending integrity.
Compatibility recovery restores prior static with quarantined current API,
preserving purchased-item validators, moderated-bio readers and closed-account
identity/credential/entitlement SQL guards. See
`reports/finnaplan-v5-recovery-20261117/README.md`. Native physical-device visual
certification remains open. V.6 review/focus API widening is now deployed with
three negotiated capabilities, exact frozen-choice receipts and unchanged web
assets: 1085 backend tests, 231-table preservation, 36 private real-mpsc reads,
six API/337 static hash checks and 22 integrity counters 0; ledger 46→46. 0098 is
now applied/immutable; next free 0099. Fresh calibration binds 41 runtime artifacts.
Native Smart Review/focus with durable retries and account-change guards passes
29 domain/60 component tests, lint/typecheck and Android/iOS/web export. No signed
binary/OTA or physical-device certification: EXPO_PROJECT_ID is missing and no
Android device is attached. See reports/finnaplan-v6-20261117/README.md.
V.9 website consolidation is now deployed: one Revise surface, personal Desk
toolbox, Chronicle date views, one Play grid, one Quick find and Inbox. Six
frontend scripts, 10 actual-router redirect cases, 111 navigation destinations,
desktop/dark/320px UI and static recovery checks pass. The static-only release
verifies 336 built/453 served hashes (117 prior chunks retained for open tabs)
and 153 unchanged V.6 API/migration dependencies. Fresh 36 private read-only mpsc
checks pass; all 22 integrity counters are 0 and both sites healthy. No API,
SQL, service or native binary change. Receipt: reports/finnaplan-v9-20261117/README.md.
Vocabulary remains on its existing server engine in this UI phase; Part II's
scheduler/data unification stays with V.10. Continue V.10 in its Part II order;
V.7 requires actual exam onboarding sources and V.8 is the standing never-list.
Later phases and catalog/legal/paid-checkout launch work remain pending.
See `reports/finnaplan-v5-calendar-20261117/README.md`.
See `reports/finnaplan-v5-boards-20261117/README.md`.
Later phases remain pending. The dated
design history below describes the baseline at the time it was written.

**Latest V.10 vocabulary review-proof correction, 18 November 2026:** V.10 bank vocabulary mastery proof is corrected/deployed (18 November).
The deck's Mastered display now requires an existing topic proficiency timestamp
and a finished, scored, exact server-issued Smart Review receipt touching that
deck at least14days later. A completion alone cannot supply the label; unfinished,
early, excluded, wrong-context/paper or mismatched receipts do not qualify. The
previous read used any review completion; no stored tier, award or history was
changed.24targeted vocabulary/mastery/recovery tests pass, including actual early
vs delayed and unfinished vs finished API flows. The unchanged web's1188-test
baseline/build/browser evidence remains linked; no new full-suite/browser run is
claimed for this reader-only correction. Real-mpsc candidate/live6catalog+30deck
overview checks and9+39+36independent private reads pass;3edit/22reward counters0,
ledger46→46, economy reconciled.1API helper,262unchanged dependencies, unchanged
341built/1983served static hashes and8route shells verify; both sites200. No SQL,
learner/reward/bank/workshop/provider/billing/unit/dependency changes or commit.
0104applied/immutable;0105stillfree. Receipt:
reports/finnaplan-v10-vocabulary-proof-20261118/README.md. Paired backup:
/root/finna-v10-vocabulary-proof-backup-xk1hk1ha. Recovery restores the prior
reader/static only after exact API/schema/static drift guards; no history/schema
changes. Do not replay this or older frozen targets. Next: vocabulary shared
scheduler/5words/Today, then curated/Mizo cards, cloze and session integration.

**Latest V.10 vocabulary deck continuation, 18 November 2026:** V.10 bank-derived vocabulary decks/progress are deployed (18 November).
Revise's Vocabulary view groups canonical questions by the four actual approved
active subtopics (synonyms, antonyms, idioms/phrases, one-word substitution), with
an honest Other vocabulary fallback. No inferred retagging, rewritten questions,
new content or provenance changes. Selection binds new/resumed cards and overview
to the chosen deck; an empty deck never silently serves another. Progress uses
latest verified-key canonical outcomes and shared mastery thresholds/45-day decay;
repeat drills do not inflate counts and recent excluded assessments do not erase
decay. Recognition is explicitly not a unique-words-mastered claim. Private reads
exclude active mock/game/Cup items; account expiry/change and stale deck responses
are cleared. Existing answer receipts, source links and the recognition scheduler
remain; full scheduler unification,5words/Today,curated/Mizo cards and cloze are
still pending.1188full backend tests plus14final targeted checks, four frontend
scripts, build and desktop/320px/light/night new-panel QA pass. Synthetic local
empty-deck, scoring and reload receipts verified; preview DBs/processes removed.
Real-mpsc read-only candidate/live6catalog+30deck-overview checks pass, plus
9tracker and39+36independent private checks. All3edit/22reward counters0; ledger
46→46, economy reconciled.2API artifacts,341built/1983served hashes,1642oldchunks,
261unchanged dependencies and8route shells verify; both sites200. No SQL,
migration, bank/workshop, learner/reward/provider/billing/unit/dependency changes
or commit. API restarted for the bounded pair.0104remains applied/immutable;
0105remains free. Receipt:reports/finnaplan-v10-vocabulary-20261118/README.md.
Paired backup:/root/finna-v10-vocabulary-backup-23qlbm10. Drift-guarded recovery
restores prior router/static and removes the new helper, retaining every schema,
learner/review/tier/economy artifact. Never replay this or older frozen targets.
New vocab routes remain web-only. Next: bank vocabulary shared scheduler, then
curated decks/modes/session integration. Ranking still needs actual volume;
V.7actual sources,V.11growth,V.12ops,later Desk/Atlas/Studio and signed native/device
QA remain. Catalog/legal/email-recovery/paid-checkout launch stays closed.

**Latest V.10 checklist continuation, 18 November 2026:** V.10 pre-submission checklists are deployed (18 November). Question proposals,
Content Studio materials, learning collections and timed tests now ask authors to
check sources, sharing rights and format/body size before review starts. The
transient confirmations bind to the current draft/account, clear permanently on
edit/revert and never restore an earlier account's proof. Materials/collections
require the current draft saved first; owner test publication retains its existing
preview confirmation. These are client readiness checks, not persisted legal
attestations or new API enforcement; authoritative source/format/ownership/review
rules remain unchanged. All four real screens pass component checks; 12 frontend
regression scripts,18targeted backend checks, existing1182-test unchanged-API
baseline, build, disposable recovery and desktop/320px/light/night browser QA
pass. Synthetic local material reached Submitted in the existing queue; it was
never reviewed/published and its disposable DB was removed.341built/1863served
hashes,1522retained chunks,262unchanged API/schema/data dependencies and24route
shells verify.6+3tracker and39+36independent private read checks pass;3edit and
22reward counters0, ledger46→46, economy reconciled, both sites200. Static only:
no API/SQL/unit/workshop/learner/reward/provider/billing/dependency changes or
commit.0104 remains applied/immutable;0105 remains free. Receipt:
reports/finnaplan-v10-checklists-20261118/README.md. Private static backup:
/root/finna-v10-checklists-backup-dtsxjt2x. Recovery restores prior static only and
refuses API/schema or newer-static drift. Never replay this or older frozen
installers. Next: vocabulary decks/scheduler unification. Ranking waits for actual
volume. V.7needs actual new-exam sources; V.8 remains the permanent never-list;
V.11growth,V.12ops,later Desk/Atlas/Studio and signed native/device QA remain.
Catalog/legal/email-recovery/paid-checkout launch stays closed.

**Latest V.10 submission-tracker continuation, 18 November 2026:** V.10's read-only submission tracker and current-access Create panel are deployed
(18 November). /create composes own questions/corrections, materials and learning
collections/mock tests from existing lifecycle tables: actual states, revision-bound
latest return notes, original draft links, dated queue positions and real30-day
median decision times (honest empty history, no SLA/progress fiction). Collection
links select the same existing draft. No new status store or review/award path.
Titles/notes are redacted until linked-question attempt/reveal/valid exceptional
disclosure, with active mock/game/Cup guards taking precedence. Reviewer block pairs
hide notes; queue/time aggregates exclude blocked accounts. Current caps/moderation
and invitation-only Mentor eligibility are explicit; no roles auto-granted.
1182full backend tests, six final targeted boundary/recovery tests, ten component /
navigation scripts, build and desktop/320px/light/night browser QA pass. Candidate
reads ran as mpsc in read-only transactions before deployment; six live tracker
reads plus three private handler checks verify40owned rows. Independent39+36private
checks pass;3edit/22reward counters0, ledger46→46, economy reconciled and both sites200.
Two API readers,340built/1743served hashes,1403retained chunks,260unchanged API/schema /
data dependencies and8route shells verify. No SQL/migration, learner writes,
synthetic production activity, currency/rate/provider/billing/bank/workshop/unit /
dependency change or commit.0104 remains applied/immutable,0105 remains free.
Receipt:reports/finnaplan-v10-submissions-20261118/README.md. Paired private API/static
backup:/root/finna-v10-submissions-backup-02i4ys3u. Drift-guarded recovery stops API,
restores prior router/static and removes the new helper; all tier capture, schema,
economy evidence, privacy guards and learner/review history remain. Disposable
recovery passes; production recovery was not invoked. Do not replay this or older
frozen installers. Next: §II.7.2 pre-submission source/rights/body-limit checklist,
then vocabulary decks/scheduler unification. Ranking still needs actual volume.
V.7 is pending actual new-exam-body sources (no invented registry/papers); V.8 is
the permanent never-list, not an incomplete feature. V.11growth, V.12ops/admin /
retention, later Desk/Atlas/Studio, signed native/device QA and catalog/legal/email /
checkout launch remain open. The new tracker route is explicitly web-only.

**Latest V.10 contributor-standing continuation, 18 November 2026:** V.10 contributor tiers, profile reputation and the dated weekly Guide strip are
now deployed (18 November). Current weighted votes still compute privileges;
only the highest earned display label is recorded in immutable creator_events.
Regular+ post flair and consented public-profile links appear on question/note /
share/reply authors. Public raw Helpful/accepted counts retain parent/reference,
block, disclosure and mock/game/Cup guards. Guides require current eligibility,
visible weekly Helpful activity, public creator consent and weekly-board opt-in;
moderation overrides privileges, and Mentor eligibility never grants a role.
1175backend tests, nine component/nav scripts, build and1440/320px/light/night UI
checks pass. Fresh232-table dump rehearsal preserves every existing row;0104apply
8.815ms, zero initial labels. Nine API/data artifacts,340built/1623served hashes,
1283oldchunks and251unchanged dependencies verify.39+36private read-only checks,
3zero edit/22zero reward counters, valid audit guards, ledger46→46, reconciled
economy and both sites200.0104 is now applied/immutable; nextfree0105. Receipt:
reports/finnaplan-v10-tiers-20261117/README.md. Private paired backup:
/root/finna-v10-tiers-backup-yslok8te. Recovery pauses all10tier capture triggers
before restoring prior API, matching prior economy evidence and static; it retains
0104/every earned label and all existing privacy/history guards. If pause fails,
keep/restart the complete candidate API (including games lock ordering and matching
evidence); do not install the old multi-player writer with capture active. Never
replay this or older frozen targets over newer releases. Multi-user attempt writers
must acquire every affected reward lock in sorted user order before tier capture;
normal aa_habit_attempt_lock precedes tier capture. No synthetic production activity,
learner-content/economy writes, bank/workshop/provider/billing/unit/dependency change,
award backfill or commit. Catalog/legal/email-recovery/paid-checkout launch remain
closed. Next: submissions/checklists/tier-aware Create, then vocabulary decks /
scheduler unification. Ranking needs real volume; V.11growth, V.12admin/maintenance
and later Desk/Atlas/Studio remain. V.7needs actual exam sources; signed native /
physical-device certification remains open. New standing/Guide endpoints stay
web-only; additive legacy author metadata is not native renderer certification.

**Latest V.10 block-shortcut continuation, 17 November 2026:** V.10 block shortcuts are now deployed (17 November): question posts/replies,
study notes, material shares and their replies expose a direct Block this author
control, separate from reporting. It reuses the existing account block for private
and public-profile authors; own/guest controls are absent. Success and uncertain
responses clear/refetch all mounted community snapshots, discard late pagination /
account outcomes and retain feedback plus a Blocked users/unblock link. Reply and
feed readers now also clear on auth expiry/community changes. Existing server
visibility, graph/follow/block, disclosure/assessment and moderation guards remain.
1154full backend tests, eight real component/navigation checks (10actual redirects /
111links), build and1440/320px/light/night browser QA pass. Static-only bounded
release verifies339built/1504served hashes,1165retained oldchunks,259unchanged API /
schema/data dependencies and20route shells.30+36private read checks,3zero edit /
22zero reward counters, valid nudge index/0invalid events, ledger46→46, economy
reconciled and both sites200. No API/SQL/migration/service/workshop/bank/provider /
billing/dependency change, production learner writes, award backfill or commit.
Receipt:reports/finnaplan-v10-blocks-20261117/README.md. Private static backup:
/root/finna-v10-blocks-backup-2zb4mj4f. Guarded static recovery preserves all API/learner/block
history and refuses drift; disposable recovery test passes.0103 remains applied /
immutable; nextfree0104. Do not replay this or older frozen installers over newer
releases. Next: public monotonic tiers/profile/Guide; submissions/checklists/full
Create; vocabulary scheduler/decks. Ranking needs real volume. V.11growth,
V.12admin/maintenance and later Desk/Atlas/Studio remain; V.7actual sources,
signed native/device QA and catalog/legal/paid-checkout launch remain open.

**Latest V.10 acceptance-reminder continuation, 17 November 2026:** V.10 once-only acceptance reminders are now deployed (17 November): the doubt
asker's open, published conversation can show “Did one of these solve it?” once.
Only another visible author's published reply qualifies; previously solved doubts,
blocks, pending/withdrawn/before-fix content, disclosure/assessment locks and sanctions
suppress it. A private web-only POST claims an append-only event under the same
parent lock as acceptance; a unique index makes concurrent/device claims once-only.
GET reads never consume prompts. Dismissal/reload does not repeat; uncertain network
responses may omit this optional prompt, never retry into a nag. No automatic
acceptance, Inbox/email notification, posting-budget slot or award is added.
1149backend tests, real components/build,10redirects/111links and1440/320px/night
browser checks pass. Fresh clone preserves232tables,0103apply5.316ms;0103now applied /
immutable, next0104. One API file,338built/1386served hashes,1048oldchunks and257unchanged
dependencies verify.30+36private read checks, valid nudge index/0invalid events,
3zero edit +22zero reward counters, ledger46→46, economy reconciled and both sites200.
Receipt:reports/finnaplan-v10-nudge-20261117/README.md. Private paired backup:
/root/finna-v10-nudge-backup-03bn068o. Recovery restores only the prior router/static while retaining
0103/all prompt and learner history, plus every existing edit/privacy guard. Drift
recovery tests pass in disposable files; production recovery was not invoked.
Do not replay this or any older frozen target over newer releases. No workshop/bank/
provider/billing/Caddy/unit/dependency change, synthetic production activity, award
backfill or commit. Next: block shortcuts, then public tiers/profile/Guide,
submissions/checklists/full Create, vocabulary scheduler/decks; ranking needs real
volume. Later V.11growth,V.12admin/maintenance and Desk/Atlas/Studio remain; V.7needs
actual exam sources, signed native/device QA and catalog/legal/checkout launch open.

**Latest V.10 honest-edits continuation, 17 November 2026:** V.10 honest edits are now deployed (17 November): own doubt/explanation/reply,
study/share/reply edits with immutable original/revision snapshots, visible edited
markers and private paginated history. Every edit uses the shared daily budget and
returns to author-only moderation; exact-version decisions and undo guards prevent
stale approval. Accepted-once replies permanently lock, including after unaccept;
SQL/edit/accept races and existing citation/reference/privacy gates hold. Web-only
new edit/history routes, saved edit drafts/retry keys and community refresh pass.
1136backend tests, components/build,10redirects/111links and1440/320px/night browser
checks pass. Fresh clone preserves231tables,0102apply22.486ms;0102now applied /
immutable, next0103. Seven API files,338built/1269served hashes,931oldchunks and
250unchanged dependencies verify.27+36private read checks,3zero edit +22zero reward
integrity counters, ledger46→46, economy reconciled and both sites200. Receipt:
reports/finnaplan-v10-edits-20261117/README.md. Private paired backup:
/root/finna-v10-edits-backup-u8o2ye8s. Recovery pauses edit-function EXECUTE and retains
current revision/moderation/privacy guards,0102and all history; prior static only.
Do not replay frozen targets. No workshop/bank/provider/billing/Caddy/unit/dependency
change, synthetic production activity, award backfill or commit. Next §7.1.6:
once-only acceptance nudge. Block shortcuts, public tiers/profile/Guide,
submissions/full Create, vocabulary scheduler/decks and later Desk remain. Ranking
needs real volume; V.7 requires actual sources. Native/device certification open.

**Latest V.10 question-composer continuation, 17 November 2026:** V.10 canonical question composer formatting and device drafts are now deployed
(17 November): safe thread/feed/accepted-text rendering, preview, restored post type
and five source pairs, account/question/parent/paper-context isolation and durable
retry keys. Fresh duplicate deflection, citation actions and immutable accepted
replies stay intact; expiry discards private views. Shared theme colors fix input /
accepted-card night contrast.1122 full backend tests plus1 new recovery test,
components/build,10redirects/111links and1440/320px/night browser checks pass.
Static-only release verifies339built/1152served hashes,813oldchunks,256unchanged
API/schema/data and18route shells; both sites200.24+36private read checks,
22zero integrity counters, ledger46→46, economy reconciled and launch dark.
No API/SQL/service change;0101immutable,0102free. Receipt:
reports/finnaplan-v10-discussion-composer-20261117/README.md. Private backup:
/root/finna-v10-discussion-composer-backup-z21hdaln. Guarded static recovery passes
in disposable files; production recovery not invoked. Never replay frozen targets.
Continue §7.1.5 edits with visible history and accepted-reply locks integrated into
that workflow, then once-only acceptance nudges; existing accepted content stays
immutable. Block shortcuts, public tiers/profile/Guide, submissions/full Create,
vocabulary scheduler/decks and later Desk remain. Ranking needs real volume;
V.7 requires actual onboarding sources. Signed native/device QA remains open.

**Latest V.10 composer continuation, 17 November 2026:** V.10 note/share/reply formatting and device drafts are now deployed
(17 November). Safe React bold/list/code readers and preview; private account +
composer/parent draft isolation, reload/uncertain-write retry continuity,
discard/success cleanup and global sign-out/expiry/cross-tab purge. Drafts contain
own input only, expire7days and cap32records; blocked storage stays in memory with
an honest notice.1122backend tests, renderer/hook/real-component regressions,
10redirects/111links, local build and1440/320px/night UI pass. Static-only release
verifies337built/1033served hashes,696oldchunks and256unchanged API/schema/data
files;15route shells and both sites200.24+36private read checks,22zero integrity
counters, ledger46→46 and economy reconciled; catalog/checkout dark. No API/SQL/
service changes;0101 remains applied/immutable and0102 free. Receipt:
reports/finnaplan-v10-composer-20261117/README.md. Private static backup:
/root/finna-v10-composer-backup-sn_jdlkz. Guarded recovery restores prior static
without history changes; never replay frozen installers. Canonical question
composer formatting/autosave, honest edits/accepted locks/nudges, block shortcuts,
public tier/profile/Guide, submissions/full Create, vocabulary scheduler/decks
and later Desk remain. Ranking waits for volume; V.7 requires actual exam sources.

**Latest V.10 reply continuation, 17 November 2026:** V.10 note/material reply conversations are now deployed (17 November):
on-demand chronological replies, shared30/60 IST-day limits, moderation,
Helpful/report/withdraw and parent/reference visibility guards. New accounts may
reply; parent/child author blocks, linked publication/disclosure/active assessment
checks hold. No nested replies, currency or community reply notifications added.
1121tests/build/components and desktop/320px/night QA pass. Fresh231-table clone
preserves all history;0101 applied/immutable, next0102. Three API files,
337built/916served hashes,252unchanged dependencies and579priorchunks verify.
24+36private mpsc reads,22zero integrity counters, ledger46→46 and both sites200;
economy reconciled, catalog/checkout dark. Receipt:
reports/finnaplan-v10-replies-20261117/README.md. Private paired backup:
/root/finna-v10-replies-backup-bo2iz0ht. Recovery restores prior router/static while
retaining0101/all history and parent/reference privacy readers; do not replay
frozen installers. Block shortcuts, remaining composer, public tier/profile/Guide,
submissions/checklists/full Create hub, vocabulary scheduler/decks and later Desk
work remain. Ranking waits for real volume; signed native/device QA stays open.

**Latest V.10 continuation, 17 November 2026:** V.10 reviewed material shares are now deployed (17 November): immutable
material anchors, current published-revision title/format/access cards, shared
maturity/limits/moderation/Helpful/report/withdraw and explicit native isolation.
Protected bodies and unreviewed edits stay out of share responses; publication
and both post/material author block pairs are rechecked. Moderator queues show
reviewed references and approval rechecks availability.1113tests/build/component
and desktop/320px/new-panel night checks pass. Fresh clone preserves231tables;
0100 applied/immutable, next0101. Six API files,337built/800served hashes and248
unchanged dependencies verify;463priorchunks retained.21+36private reads,
22zero integrity counters, ledger46→46 and both-site health pass. Economy
reconciles; catalog/checkout dark. Receipt:reports/finnaplan-v10-materials-20261117/README.md.
Private backup:/root/finna-v10-materials-backup-uiukv5l9. Recovery retains0100,
all history and the new native isolation guard; never replay frozen installers.
Remaining V.10 includes note replies/block shortcuts, remaining composer,
public tier/profile/Guide, submissions/checklists/full Create hub, vocabulary
scheduler/decks and later Desk work. Ranking still waits for real volume.

**Update, 16 November 2026** (synced against the live code and DEVLOG):
Part I §5.5 (admin access grants) is now **implemented and deployed** as
migration `0089_owner_billing_access` — see the rewritten §5.5 for what
actually shipped, including a per-account price facility the original
draft did not anticipate. Billing reality also firmed up: the ₹100/month
standard price is live-configured in Razorpay (checkout still disabled
pending the owner's launch choice), new checkout is **monthly-only**, and
the owner can assign **₹50/month** to selected accounts. Migrations
0084–0089 are now taken (stats, current-affairs ×4, owner billing), so
the schema work this plan proposes starts at **0090+**, not 0084+.
Everything else in Parts I–IV remains proposal, nothing implemented —
verified: no `user_topic_mastery` or `review_items` exists in
`api/migrations/` or `api/app/`.

Added the same day, all design-only: **§0.9** (a reconstructed stub for
the access-model section lost in consolidation — owner should check it),
**§0.10** (general bank design: MPSC as first tenant, not schema),
**§0.11** (exam-first personalization: the chosen exam as the site-wide
lens over library/vocabulary/feed/boards, with the economy global),
**Part I §12** (focus subjects, the leaderboard decision, game boards,
Home layout, phone optimization §12.5, Expo widening §12.6),
**Part I §13** (assistant-proposed improvements awaiting owner yes/no),
a **§5.5 planned extension** (bulk ₹50 by email allowlist / group claim
code — phone matching deferred: accounts have no phone field), and
**Part V** (the phased implementation guide — V.0 gates through V.8
prohibitions). Nothing in them is built.

A **de-duplication pass** ran the same day: §9 items 8–10 removed
(two were duplicates of Part II §2.3/§1.4; mastery certificates cut as
badge-adjacent per §5.6), the question-of-the-day proposal cut (third
daily-question feature), Desk's weekly focus summary merged into the one
§12.1 growth recap, and §12.4 disambiguated against the deployed `/feed`
Home. Also added: **Part II §7** (composer v2, creator pipeline v2, and
the paid-content stance: capacity is paid, correctness never is) and the
**free-month decision** in §5.4 (points are the single loyalty path;
upvotes never pay; a "Your free month" meter on Rewards).

Finally, the owner said **"decide all for me"**: every open item in the
document is now resolved — Part I §11 (thresholds adopted, ≥60% game
gate, district stays Daily-Five-only, catalog-live gate, claim-code
100-uses/30-days, all §13 proposals approved with referral bounds),
Part II §6 (throttles stand; Mizo gloss on curated cards only), Part III
(drills on Today as suggestions; owner curates bindings first), the
§0.11.3 ≥50 cohort gate, and the §0.9 stub adopted as canonical. All are
assistant decisions under owner delegation, versioned, and tunable only
with real usage evidence. **The plan now contains zero open questions**;
what remains is building it, in Part V order.

Last addition the same day: **§14, the Helper Calendar** — one `/calendar`
of toggleable honest layers (official exam dates, my-exam countdowns, the
Leitner **review-load forecast**, recurring progress-test slots, private
personal entries, streak heatmap, cup/desk events) with an ICS feed so
phone calendars do the reminding. Mints nothing, punishes nothing; two
small tables; forecast layer ships free with V.2, the rest in V.5.

And a **surface consolidation pass** (§0.12): one place per job, binding
map. Revision unified at `/revise` (mistakes screen and vocab review
become views, printable sheet becomes an export button); Today lives on
Home only (the Desk's copy cut, its mastery strip too, its self-reported
weekly target retired); `/important-days` merges into Chronicle; the desk
calendar is a view of §14's one store; games get one Play hub; the Expo
app is scoped to native value (offline), never web parity. Structural
sentence: *Home decides, `/revise` executes, My Desk holds your things,
rooms are social.*

Completing the set, same day: **§0.13** (the interaction map — every
user-to-user touch in one table with its guards; no DMs by design),
**§12.7** (profile tools: identity, study setup, privacy/security with
data export + account deletion, wallet shortcut), **§13.1** (the
second-sweep gaps: legal pages and email recovery as hard checkout
gates, SEO prerendering for public pages as the missing growth engine,
self-hosted §0.8 measurement, a support surface, the V.9 accessibility
pass, per-body licensing checks, Mizo UI noted), **Part V extended to
V.13** (consolidation retrofit, community, growth, admin phases + the
one final build-order table), and **Part VI** (admin console &
maintenance: ops dashboard over worker heartbeats, retention workers,
restore-rehearsal discipline, feature-gates panel with checklists, the
read-only user viewer). The document is complete: zero open questions,
one build order.

*(Superseded 22 November 2026 by **Part VII** — the owner, reading the
built site, found it confusing. Part VII is a subtraction document: 88
routes to ~40, seven navigation surfaces to two, practice and mock to
one, plus the three content systems the plan never had — Guides,
question currency and explanation voice. It carries four open questions
(§VII.16) and three new build phases (§VII.15). The build order below is
amended at §VII.15.)*

---

V.10 bank vocabulary shared scheduling is deployed (18November). Recognition,
Bank/game answers and mixed/vocabulary-only frozen Smart Review sets use one typed
canonical Leitner queue with1/3/7/16/35days,24h promotion guard, source reset and
Box5 graduation. Old question projections are retained but deduplicated. Today
limits new recognition to5/day; due reviews remain available. Queue/decks/Today/
calendar agree; loading a card creates no earning plan. Existing saved-set reward
receipts/caps remain; no new rates/awards or unique-word mastery claim.1197backend
tests,20final targeted checks,46source-bound economy evidence, build/components
and1440/320px/light/night synthetic browser QA pass. Fresh232-table clone preserves
all existing rows;0105apply15.054ms, rolled-back real-role probe passes.13API/data,
341built/2103served hashes,1762oldchunks,253unchanged dependencies and8route shells
verify.33new live private reads, ledger46→46,22integrity counters0, reconciled
economy and bothsites200. No production fixtures/bank/workshop/provider/billing/
unit/dependency changes or commit.0105 is applied/immutable; next0106. Receipt:
reports/finnaplan-v10-vocabulary-scheduler-20261118/README.md. Private backup:
/root/finna-v10-vocabulary-scheduler-backup-qcwydt2m. Recovery keeps0105/current
shared API/economy writers, pauses new recognition and restores prior static;
receipts/Bank/Smart Review/history remain. NEVER restore older queue writers over
0105. Disposable recovery passes; production recovery not invoked. Never replay
this or older frozen targets. New recognition routes remain web-only. Next:
reviewed curated/Mizo cards, usage cloze and distinct-word/session integration.
Ranking needs real volume; V.7actual sources,V.11growth,V.12ops,later Desk/Atlas/
Studio and native/device QA remain. Catalog/legal/email/checkout launch stays dark.

# Part 0 — The whole site: product thesis, architecture and scaling

## 0.1 Product thesis and priority order (owner, 15 November 2026)

What people come to study.hawayu.in for **today is to browse and read old
exam questions**. Everything else exists to make that core act better and to
bring people back to it. The hierarchy, in order:

1. **Browse** — the question bank, past papers and exams. The product.
2. **Learn** — the practice → review → mock loop (Part I). The retention
   layer that grows naturally out of browsing.
3. **Community & games** — the reasons to come back with other people
   (Part II + Part I §5.1 Play pillar). Social proof and fun, anchored to
   the same questions.
4. **Points & XP** — ambient reward. "Good that it's there," never the
   point. It seasons the loop; it must never gate, interrupt or headline
   anything.

Access implication — **revised by the owner later on 15 November 2026**
(the original draft said browsing would never be gated; §0.9 supersedes
that): browsing is free to *taste* as a guest, free in a chosen exam's
scope with an account, and unlimited — including cross-exam subject-wide
browsing — with Pro or points. The door is open, the library card is free,
the full archive is membership. Sign-up and upgrade are still earned by
demonstrated value, never demanded before value is shown, and §0.9's
integrity rules (no mid-question rug-pulls, honest meters, downgrade-safe
history) are binding.

## 0.2 The browse experience — the core product

Three entry geometries over the same bank (~78k questions, ~1.9k papers,
82k+ live appearances; fresh counts from the live DB, not this document):

- **By exam**: `/exams` → exam detail → its papers by year → paper view.
  The learner's mental model is "show me what this exam asked before."
- **By paper**: `/past-papers` directory → a paper in **original printed
  order** with booklet/series identity, source typography and the original
  PDF alongside (0077 library). The paper is a historical document; we
  preserve it, we don't reflow it.
- **By topic/search**: subject → topic drill-down (usable since the 8
  November taxonomy publication) and full-text search (0043) with
  filter chips (exam, year, subject, answer status).

The question card contract, everywhere it appears:

1. Question + options exactly as printed (figures, directions, emphasis).
2. Answer behind the existing reveal gate, labeled by provenance per
   `PUBLIC-ANSWER-LANGUAGE.md` — Official key / Verified answer /
   unverified states shown honestly. **Provenance is a display property,
   not a visibility filter**: the whole bank is browsable, including the
   ~84% without official keys; only scoring and rewards are restricted to
   the verified pool. This is what makes browse-first viable at all —
   browsing needs no answer guarantee, scoring does.
3. Source line: exam, year, paper, question number; dispute/provisional-key
   notices preserved.
4. **Inline answering** — one tap to attempt right on the card (the
   established prototype pattern). This is the single bridge from browsing
   to learning; it must stay frictionless and optional.
5. Explanation when published; discussion thread beneath, behind the
   disclosure gate.

Performance is a browse feature: paper views and filter flips must feel
instant. The two known slow queries get indexes/rollups before any growth
push, and Part I's mastery/progress rollups remove the per-request
`attempts` aggregation.

## 0.3 The progressive learner journey

Browsing converts to learning by gradient, never by wall:

```
read questions → tap an answer inline → device progress appears
→ natural account prompt (keep progress across devices / save a bookmark)
→ mistakes collect themselves → Smart Review offers itself on Today
→ mocks when ready → mastery map grows → points tick ambiently
```

Each step is offered at the moment it is useful, inside the browse flow —
never as an interstitial. Guests get the full browse experience plus
device-local progress; accounts add sync, review scheduling, rewards and
community voice. The Today card (Part I §4.3) is the signed-in home, but
the signed-out home is still a great library, not a locked lobby.

## 0.4 How community should work

Community is **anchored to the questions themselves**, not a parallel
social app. The doubt/explanation thread under each question is the atomic
unit (it already exists); the feed (Part II §3) is an aggregator over that
activity plus light study posts — a window into the library, not a
destination that competes with it. Desks stay private small-group spaces.

The compounding loop: a browser hits a confusing question → asks a doubt →
a Mentor-tier learner answers → the accepted answer sits on that question
for every future browser. Community effort accrues to the browse surface
permanently, which is why helpfulness earns standing (Part II §4.2) and why
social activity never needs to earn points to be worth doing.

## 0.5 Where games fit

Games are the same bank with a timer and company — casual on-ramps, never
homework. Daily Five is the one-tap daily hook; duels/cups/trail serve the
committed; a later "challenge a friend on this paper" affordance starts
games directly from browse. Game awards stay inside the Play sub-cap
(Part I §5.1) and server-owned results; games are optional by construction,
and no learning content is exclusive to them.

## 0.6 Where points fit (deliberately quiet)

Points surface in exactly three places: a small toast on earn, the wallet
on Profile/Rewards, and the catalog at redemption. No currency UI on browse
surfaces, no streak-guilt modals, no gated content. The calibrated economy
(Part I §5.4) stands unchanged — it simply isn't the headline.

## 0.7 Scaling plan

**Content scale** (the real growth axis):

- **S1 — deepen MPSC**: finish the parse/key backlog in the bank workshop
  (unparsed clerical papers, un-OCR'd answer keys), grow the verified pool
  from ~16% via key ingestion + the contribution pipeline. Every verified
  answer upgrades browse (labels), learning (scorable) and economy
  (rewardable) at once — the flywheel.
- **S2 — adjacent Mizoram exams**: MUDAL/other state bodies through the
  same paper → review → publish machinery; browse-only content is
  acceptable at entry (honest labels), verification follows demand.
- **S3 — beyond Mizoram**: the "India Study Map" name is the ambition; the
  exam-scope machinery (`exam_scope`, collections, Mizoram launch scope
  0046) already isolates cohorts, so new exams are data work, not
  architecture work.

**Traffic/infra scale** (staged by measurement — the OCI baseline of
~5.4k tps on the 77k bank says the single VM has real headroom):

- **T1 (now)**: fix the two known slow queries; ship the Part I rollups;
  add `Cache-Control: public` + ETag to anonymous browse responses
  (question/paper/exam reads are identical for every guest — let Caddy and
  browsers absorb them).
- **T2**: edge/CDN caching for anonymous browse, PDFs to object storage,
  connection pooling and Postgres tuning. Mind the shared-Caddyfile rule —
  study and family share the server.
- **T3 (only if measured demand)**: read replica for browse reads, a real
  search index when ILIKE degrades, horizontal split of API/DB. Stay on
  current cheap infra until ₹100 subscriptions pay for the next tier.

**Sequencing** (supersedes neither Part I §10 nor Part II §6 — it orders
them):

| Stage | Focus | Contents |
| --- | --- | --- |
| Now | **Browse excellence** | past-paper directory polish, search/filters, speed (T1), provenance labels everywhere, finish Finna port of remaining screens |
| Next | Learning loop | Part I phases 1–2 (mastery, Smart Review, Today, unified streak) |
| Then | Community & play | Part II feed/posts/votes, desk v4, vocabulary; Daily Five prominence |
| Later | Economy & scale | Part I phase 3 (spread, catalog live, admin grants), S2 content, T2 infra |
| Eventually | Expansion | S3 exams, mobile app parity (MobileBoundary widening per feature), T3 infra |

## 0.8 What success looks like (honest metrics only)

Measured from real activity, never invented: papers browsed per session and
search success rate (browse health); share of browsers who attempt at least
one question inline, and of those, 7-day return rate (the conversion that
matters); due-review completion rate (loop health); share of doubts with an
accepted answer within 48h (community health); redemption rate (economy
health — should be modest and stable, not viral). If browse metrics and
loop metrics ever conflict, browse wins — per §0.1.

## 0.9 Access model (reconstructed stub, 16 November 2026)

⚠ §0.1 cites a "§0.9" that was lost in the 15 November consolidation of
the two source documents. This stub records only what §0.1 itself
attributes to it, so the reference resolves. **Adopted as the canonical
§0.9 on 16 November 2026** under the owner's "decide all for me" — if a
richer pre-consolidation draft ever resurfaces, restoring it is an owner
edit, not a correction of this one. As cited:

- Browsing is free to **taste** as a guest, free within a **chosen exam's
  scope** with an account, and **unlimited** (including cross-exam
  subject-wide browsing) with Pro or points.
- Integrity rules, binding: **no mid-question rug-pulls** (a question you
  opened never slams shut over you), **honest meters** (any allowance
  shown is the real server-side number), and **downgrade-safe history**
  (losing Pro never deletes or hides what you already did).
- Sign-up and upgrade are earned by demonstrated value, never demanded
  before value is shown (§0.1, §0.3).

### 0.9.1 The authentication system (16 November 2026 — state + decisions)

What exists, verified: password + Google identity (0071), TOTP MFA
(0033), email-recovery schema (0057) **with no mail provider wired**,
server-issued HttpOnly guest identities (0056) with guest→account
progress adoption, session cookies with same-origin CSRF, mobile PKCE
pairing with `MobileBoundary` (IV.3, IV.8). Decisions completing it:

1. **Two sign-in methods, no third.** Password and Google. No phone OTP
   (no SMS infra — the recorded scope cut), no magic links until the
   mail provider exists, no new identity providers without an owner
   decision.
2. **Email verification becomes required for *new* accounts only after
   the mail provider ships** (§13 #1); existing accounts are
   grandfathered and nagged gently, never locked out of what they
   already had.
3. **MFA**: optional for learners (it exists; §12.7 surfaces it),
   required for staff (existing policy with the one recorded exemption).
4. **Login throttling** (§13.1 #15): per-account + per-IP backoff,
   lockout recoverable via email — ships in V.2.
5. **Sessions**: list + revoke in §12.7; sign-out-everywhere included.
6. **An account is required for**: sync, rewards/wallet, community
   voice, desks, calendar personal layers, mobile pairing. Never for
   reading the library (§0.1).

### 0.9.2 The paywall — fair, limited, and honest about what it sells

Owner direction: a free tier that *gives the real idea of the app*, with
the squeeze on what aspirants value most — **old-question practice
volume and power filtering** — because that is what they'll pay for.
Governing rule (§7.3): **capacity and convenience are paid; correctness
and reading never are.**

| Capability | Guest | Free account | Pro (₹100/50) |
| --- | --- | --- | --- |
| Read papers & questions (printed order, PDFs) | ✓ full, in chosen-exam taste | ✓ full within chosen exam | ✓ everything, cross-exam |
| Answer reveals | 20/day (device) | ✓ unmetered in scope | ✓ |
| Basic filters (exam, year, subject) | ✓ | ✓ | ✓ |
| **Power filtering** — multi-dimension combos (topic × year-range × answer-status), saved filter sets, cross-exam subject browse | — | taste: 3 power-filter queries/day | ✓ unlimited |
| Practice answers (scored) | device-local only | **50/day** (existing) | unlimited |
| Mocks | — | **1/month** (existing) | unlimited |
| Smart Review | — | 1 session/day (matches the award bound anyway) | unlimited sessions |
| Mistakes depth | — | last **20/day** (existing) | full history |
| Printable revision sheet | — | — | ✓ |
| Community (read/post/vote) | read | ✓ full | ✓ (never gated — community is trust, not inventory) |
| Daily Five, games | ✓ play | ✓ + earns | ✓ |
| Desk rooms | — | join | create (existing 3/owner) |
| Trial | — | **7-day no-card Pro trial** (existing) | — |

Why this split is fair *and* sells: the free account is a complete
studying life — a learner can browse their whole exam, practice 50
questions a day, keep a streak, review mistakes, post doubts, and earn
points toward a free month forever. What Pro adds is exactly what a
serious aspirant hits naturally in week two: the 51st practice question,
the second mock before the real exam, the topic×year×status filter
sweep, the full mistake history, cross-exam breadth. The limits teach
the value honestly instead of hiding it.

Integrity rules (binding, restating §0.9 with teeth):

1. **No mid-question rug-pulls**: a question already open never locks;
   limits gate the *next* action, with the meter visible before it.
2. **Honest meters everywhere**: "37/50 today", "1 mock available in
   March", "2 of 3 power filters used" — real server numbers (§0.6),
   shown *before* the wall, never as a surprise 402.
3. **Downgrade-safe**: lapsing Pro loses capacity going forward, never
   history — attempts, mastery, wallet, posts all remain.
4. **The limits are generous on purpose**: 50/day ≈ a solid daily
   session; the squeeze is on bingeing and power tooling, not on habit
   formation — the free loop must stay good enough to build the habit
   that makes Pro worth paying for.
5. **Earned Pro is identical to paid Pro** (redemptions/grants read
   through the same `account_has_pro()`); there is no second-class Pro.
6. Checkout gates stand (§13.1): legal pages + email recovery before any
   of this takes money.

Power-filter metering is the one new mechanism (a daily counter row,
same `rate_limits` helper Part II's throttles use); every other number
in the table already exists in production config. Build: the free-tier
numbers are live today; power-filter gating and the meter UI ride V.1's
browse work (the filters are being built there anyway).

## 0.10 General bank design — MPSC today, any exam tomorrow (16 Nov 2026)

Owner direction: the bank is currently MPSC questions; the design must be
a **general, exam-unspecified bank** where MPSC is the first tenant, not
the schema. This elaborates §0.7's S2/S3 into binding rules:

1. **Exam identity is data, never schema or code branches.** Exam bodies,
   exams, papers and collections are rows; `exam_scope` + collections +
   the Mizoram launch scope (0046) already isolate cohorts. New
   bank-reading code takes an `ExamScope` (IV.2) and must not contain
   body-specific conditionals. Historical names stay (the `mpsc` DB role,
   existing IDs) — renaming working history is churn, not generalization;
   the rule applies to *new* code and copy.
2. **One shared taxonomy, per-exam syllabus mappings.** The approved
   subject/topic/subtopic registry is global; an exam maps its syllabus
   onto it (which topics are in scope, in what weight/order) rather than
   forking it. Part I mastery is keyed `(subject, topic)` — exam-agnostic
   by construction — and the saved exam / focus subjects (§12.1) are the
   lens over it. Registry additions follow the existing tagging policy
   (`QUESTION-TAGGING-RULES.md`); a new exam never mints its own parallel
   taxonomy.
3. **Canonical identity stays within its source.** A question belongs to
   the paper that printed it; the same question appearing across bodies
   or years is appearance/presentation grouping, **never a canonical
   merge** (existing rule, restated because multi-exam makes the
   temptation constant). Cross-exam "similar questions" is a display
   feature, not a data operation.
4. **Per-exam honesty about verification.** Each exam's verified-answer
   pool grows independently; browse-only content is acceptable at entry
   (S2), provenance labels say so, and scoring/rewards stay restricted to
   each question's own verification state. No exam borrows another's
   credibility.
5. **One ingestion machinery.** New bodies are new source
   configurations into the same parse → review → guarded-publication
   pipeline on Oracle — never a second pipeline, never a second writable
   bank. Review ownership/attribution rules travel unchanged.
6. **Economy and learning are already general.** Discovery claims are
   per canonical question; caps are per account; mastery is per topic.
   Nothing in Part I needs a multi-exam change — which is the test that
   the generalization is right.
7. **Naming.** Public copy moves toward exam-neutral framing ("the
   bank", "past papers", per-exam titles from data). "India Study Map"
   remains the ambition name (S3); nothing user-facing should newly
   hardcode MPSC.

Onboarding a new exam body is therefore a **checklist, not a project**:
create body/exam/collection rows → map syllabus onto the registry →
ingest papers through the pipeline → verify labels render honestly →
enable its `exam_scope`. (Part V §V.7 carries the operational version.)

## 0.11 Exam-first personalization — the chosen exam as the site-wide lens

Owner direction (16 November 2026): the site runs on exams over the bank
— filters, practice, everything. When further exams exist (MPSC, SSC, …),
a learner **chooses what they are preparing for**, and every surface —
vocabulary, English, the XP displays, the feed — follows that choice.
§0.10 made the bank general; this section makes the *experience*
specific. The governing metaphor: **the chosen exam is a lens, never a
wall** — it reorders and pre-filters, it never deletes, hides earned
progress, or locks a door the access model (§0.9) left open.

### 0.11.1 The primary exam

- Learners can save multiple exams (the catalog's save/compare already
  exists); exactly **one is primary** at a time. Switching primary is
  free, instant, and non-destructive — re-lensing, not resetting.
- Onboarding asks one question — "What are you preparing for?" —
  skippable, offered at the §0.3 gradient moment, never as a wall.
  Guests and skippers get the neutral all-exams view with honest
  defaults.
- Schema sketch: extend the saved-exam mechanism with an `is_primary`
  flag, plus the §0.10.2 syllabus mapping made concrete:
  `exam_syllabus(exam_id, subject_id, topic_id NULL, weight,
  display_order)` — the one table every scoped surface reads. Built when
  the second exam body onboards (V.7); until then the MPSC scope
  machinery already answers every query.

### 0.11.2 The cascade — what the lens does per surface

| Surface | With a primary exam | Without |
| --- | --- | --- |
| Browse/bank | default filter chips pre-set to the exam; cross-exam browsing per §0.9 tiers | neutral directory |
| Practice / Today / Smart Review | new-question targets from `exam_syllabus` ∩ focus subjects (§12.1); the review queue still reviews *everything you got wrong*, whatever exam it came from — forgetting is exam-agnostic | saved-scope fallback, then honest empty state |
| Library modules (English, vocabulary, arithmetic, Mizo) | modules and decks carry exam applicability **derived from the syllabus mapping** (bank-derived decks inherit it from their source questions; curated decks get explicit exam tags at review time); the grid orders relevant modules first and labels the rest "not in <exam>'s syllabus" — labeled, never hidden | full grid, no labels |
| Games | question pools draw from the primary exam's scope by default; party/duel rooms may explicitly choose another scope; Daily Five stays cohort-specific where its content is (the district dimension is MPSC-shaped) | all-exams pool |
| Feed | question-anchored posts inherit their question's exam automatically; `study` posts take an optional exam tag; the For-you `T` affinity term (Part II §4.3) already boosts your exam — add an exam filter chip, default "my exam + general", always escapable | chronological, unscoped |
| Current affairs | briefs/quiz items carry exam-relevance tags at review time; default view scoped, full list one tap away | full list |
| Leaderboards & leagues | cohort by primary exam **only once population justifies it** (see 0.11.3) | global board |
| XP / points / streak / level | **global, always** — see 0.11.3 | same |
| Mastery | global data, exam-lensed display: the map defaults to the primary exam's syllabus subjects; everything else remains below | full map |

### 0.11.3 The economy stays whole (the one thing the lens never touches)

One account = **one XP total, one level, one wallet, one streak** across
every exam, permanently:

- Earning rules are already exam-agnostic (per-canonical claims,
  per-account caps — §5.1); the lens changes *which questions are
  suggested*, never what they pay. Nothing to farm by switching exams.
- Switching primary exam loses **nothing**: mastery rows, review queue,
  history, points all persist; an aspirant who moves from MPSC to SSC
  keeps their English mastery where the syllabi overlap — that is the
  shared-registry dividend (§0.10.2).
- Leaderboard cohorting is **display segmentation, population-gated**:
  boards split per exam only when a second exam has enough weekly-active
  opted-in accounts to make a real room (**≥50, adopted 16 November
  2026** under "decide all for me"; still tunable with evidence).
  Until then, one global board — §12.2's no-empty-rooms rule outranks
  cohort purity. Game boards follow the same gate.

### 0.11.4 Honesty rules for the lens

Scoping must stay a convenience, not a dark pattern: pre-set filter chips
are visible and removable, not silent; "not in your syllabus" labels are
derived from the reviewed mapping, never guessed by a model; relevance
tags on current affairs/decks are set at human review time; and no
surface ever shows a smaller number (due reviews, mistakes, wallet) than
the account's true total because of the lens. When a scoped view is
empty, it says "nothing in <exam> yet — see all", with the unscoped view
one tap away.

## 0.12 One place per job — the surface consolidation map (16 Nov 2026)

Owner direction: merge conflicting or redundant systems — "no same thing
in different places to avoid confusion for users." This section is the
**binding map**: for each job a learner has, the ONE surface that owns
it, what merges into it, and what that retires. Later sections are
amended where they conflicted; where two surfaces legitimately share
data, one owns the store and the other is a declared *view* of it.

| The job | The one place | Merges into it | Retired / demoted to a view |
| --- | --- | --- | --- |
| Revise what I got wrong | **`/revise`** — Smart Review + the queue browser | mistakes screen (becomes the queue's browse tab), due vocabulary (same Leitner queue, `item_type='vocab'`), printable sheet (an export button here, not a feature) | the standalone mistakes screen; any separate vocab-review entry |
| My daily plan | **Today, on Home only** | — | the Desk's copy of Today (Desk v4 §1.1 is amended below) — the same card in two homes was the confusion this section exists to kill |
| Weekly self-assessment | **progress-test slot (§14) + Monday growth recap (§12.1)** | — | the Desk's self-reported weekly answer target (self-reporting also violated the honest-counting rule) |
| What's coming (dates, schedule) | **`/calendar` (§14)** | desk calendar = a room-filtered *view* of the same store | any second calendar store |
| What happened (dated history content) | **Chronicle** | `/important-days` (its date list/calendar was Chronicle's job wearing an older skin) | `/important-days` as a standalone route — redirect in |
| Place-based study | **Atlas** | Chronicle cross-links by binding table (III.2.6) — links, never duplicated timelines | — |
| Discussing a question | **the question's own thread** (public) | — | Desk rooms keep *private* discussion (§1.5), but a room answer that deserves permanence is posted to the question's thread — the room never becomes a shadow Q&A that future browsers can't find |
| My wallet / earning | **Rewards screen** (with the free-month meter) | — | §0.6 already bans currency UI elsewhere; restated as a map row |
| Playing with the bank | **one Play hub** route | all 7 game modes + Daily Five + cups + Topic Trail as entries in one grid | scattered per-mode entry points |
| Notes, saved items, focus timer | **My Desk (personal)** — now purely a toolbox | — | its loop/plan ambitions (moved to Home), its weekly target (retired above) |

Two structural decisions underneath the table:

1. **Home is the dashboard; the Desk is the room; Revise is the gym.**
   The deepest previous confusion was three surfaces (Home, personal
   Desk, mistakes screen) each claiming a piece of "where I study
   today." Now: Home *decides* (Today, continue, recap), `/revise`
   *executes* the review work, My Desk *holds your things* (notes,
   saved, focus), and group Desk rooms are social spaces. No surface
   claims another's verb.
2. **The phone web is THE mobile experience; the Expo app is the
   offline companion.** The app does not chase screen parity — every
   `MobileBoundary` widening must be justified by something *native*
   (offline practice and replay, later push), never by "the web has it."
   One design language, one reference (`finna-20261114`), two renderers
   with deliberately different scopes — the alternative is maintaining
   every screen twice and shipping both late.

*(Extended 22 November 2026, Part VII: the table gains five rows it never
had — practice/mock → one `/practice` (§VII.4), guides → `/guides`
(§VII.5), navigation → one manifest plus `/index` (§VII.3), question
editing → one console (§VII.11), written questions → one browse mode
(§VII.9). §V.9's "mostly deletions" retrofit is largely absorbed into
V.14.)*

My additions (same one-place discipline applied forward): the ⌘K-style
quick switcher on web should be the *only* global search entry (search
boxes on individual screens scope to that screen, visibly); and the
Inbox stays the single notification surface — no screen grows its own
bell, badge or activity popover, ever. Both are cheap rules now and
expensive regrets later.

## 0.13 The interaction map — every way users touch each other (16 Nov 2026)

Owner request: design "users' interactions across the website" as one
system. This is the complete inventory — if an interaction isn't in this
table, it doesn't exist, and adding one means adding a row *with its
guard column filled in first*:

| Interaction | Where | Guard rails |
| --- | --- | --- |
| Reply to a doubt / explanation | question threads | disclosure gate, throttles (§3.3), reports, blocks |
| Accept an answer | own doubt | author-only; accepted reply locks (§7.1.5) |
| Helpful vote | posts | one per account, weighted by study history (§4.1), never self, never across blocks, never currency |
| Follow | profiles, feed | one-way, free, earns nothing; honest counts |
| Study post / material share | feed | §3.1 kinds, §3.3 throttles, tier lifts |
| Desk room membership | private rooms | invite-only, six seats, Pro-gated creation, retention purge |
| Room chat / review circle / shared goal | inside a room | room-private; permanent answers go to the question's thread (§0.12) |
| Duel / party / cup | games | server-owned results; §0.5 "challenge a friend on this paper" starts from browse |
| Shared-test challenge | link-scoped boards (§9.6) | visible only to link holders; normal discovery economy |
| Leaderboard presence | XP/game boards | opt-in, handle+XP+rank only (§12.2) |
| Profile view | creator/member profiles | shows only opted-in, computed-public facts |
| Block | everywhere | one block model, enforced in every list, vote, feed, room invite and board — no surface exempts itself |
| Report | any content | feeds the one moderation queue (VI.2 pulse) |

Deliberate absences, recorded as decisions: **no 1:1 direct messages**
(a private-DM surface is the single largest moderation liability a small
team can acquire; desk rooms are the private space, and they have seats,
invitations and retention); no @-mentions (§7.1.7); no gifting or
point transfers (§3 invariants); no public follower-count races (counts
shown are honest integers on the profile, never ranked).

Invariants that bind every row, current and future: blocks apply
*everywhere* without exception; every interaction is opt-in-able or
ignorable; none of it ever mints currency (§4.2); guests read, accounts
act; and each row names the one owning surface — an interaction never
gets a second home (§0.12).

---

# Part I — Learning system & point system

Status: **proposal, nothing implemented — except §5.5, which shipped
16 November 2026** (migration 0089; see that section for as-built facts).
Drafted 15 November 2026 by an AI
assistant for owner review; every reward amount, threshold and catalog change
below is a suggestion requiring an explicit owner decision before any migration
is written. This document extends `LEARNING-REWARDS.md` (award policy v1,
deployed 2026-10-21); it does not replace it, and it changes no bank content,
keys or scoring rules.

## 1. Baseline: what learning-v1 already provides

| Area | State | Where |
| --- | --- | --- |
| Currencies | XP (activity) + reward points (spendable), strictly separate from marks and contribution credit | `reward_ledger`, DECISIONS #16 |
| Earning | First correct answer to a unique verified-key MCQ: 10 XP + 1 pt; 300 XP/day shared cap; once-per-canonical lifetime claim | `learning_rewards.py`, migration 0034 |
| Progression | Levels `floor(sqrt(XP/40))` with scholar titles; weekly-XP leagues; opt-in leaderboard | `/api/rewards/me`, `/api/rewards/leaderboard` |
| Habit | Streak + purchasable shields (25 pts); three daily quest rings; Daily Five (0083) | `reward_profiles`, `daily_quest_claims`, `game_dailies` |
| Spending | Catalog with one offer (pro-week, 1000 pts, **disabled** pending launch review); 1 redemption/account/30 days | `reward_catalog`, `reward_redemptions` |
| Learning surfaces | Practice, study sessions, mocks with frozen snapshots + reassessment, 7 game modes, Topic Trail, vocabulary drills, mistakes list, study desks | respective routers |

The v1 economy is sound: server-owned, immutable ledger, idempotent,
provenance-gated. **The gap is pedagogical, not mechanical.** v1 rewards
*discovery* only — a question pays once, ever — so the economy rewards grinding
new questions and pays nothing for retention. There is no mastery model, no
review scheduling, and two streak implementations that disagree
(`reward_profiles` vs the attempt-derived streak in `/api/me/progress`).

The 8 November 2026 owner-authorized taxonomy publication (58,197 corrections,
`owner-taxonomy-final-20261108`) is what makes v2 feasible: topic labels are now
good enough to aggregate mastery per topic, which was not true in October.

## 2. Design goals

1. **Pedagogically robust** — close the learn→forget gap with scheduled review
   and a visible mastery model; the loop is Diagnose → Plan → Practice/Review →
   Prove (mock).
2. **Economically robust** — no inflation, no farmable source, every award
   server-derived from scored evidence, flat auditable rates.
3. **Operationally robust** — incremental rollups instead of full `attempts`
   scans per progress call; everything idempotent and replay-safe.
4. **Honest** — provenance rules intact: inferred/derived answers never score,
   never pay, and are always labeled per `PUBLIC-ANSWER-LANGUAGE.md`; empty
   states stay empty.

## 3. Invariants carried forward (non-negotiable)

- XP ≠ points ≠ exam marks ≠ contribution credit (DECISIONS #16). Spending
  never lowers rank.
- Rewards require: registered account, server-scored correct answer,
  `answer_source IN ('official','key')`, current `v_scorable` eligibility.
  Guests accumulate progress but never currency.
- Single immutable ledger, unique `event_key`, per-user reward lock, shared
  300 XP/day budget, no client award endpoint.
- Difficulty labels are retired (DECISIONS #19). Nothing below reintroduces
  them; where "hard for this learner" matters, it is derived from that
  learner's own attempt history, never from a label and never as a pay
  multiplier.
- No wagering, transfers, cash-outs, bought ranking boosts, or second cosmetic
  currency.

## 4. Learning system

### 4.1 Topic mastery model

Per `(user_id, subject_id, topic)` using **approved**
`question_classifications` only. States:

```
unseen → exploring → practicing → proficient → mastered
                                      ↓ (decay, display-only)
                                    rusty
```

Thresholds (**adopted as initial constants 16 November 2026**, §11 item
1; versioned like `RULE_VERSION`, tuned only against real usage):

| State | Entry condition (verified-key questions only) |
| --- | --- |
| exploring | ≥1 scored attempt in topic |
| practicing | ≥5 distinct questions attempted |
| proficient | ≥10 distinct attempted AND latest-attempt accuracy ≥70% |
| mastered | ≥20 distinct attempted AND latest-attempt accuracy ≥85% AND one completed review session touching the topic ≥14 days after reaching proficient |
| rusty | proficient/mastered with no verified activity in topic for 45 days — a display overlay; the earned tier is never removed |

Rules:

- Only server-scored attempts on verified-key questions move mastery.
  Attempts on inferred/derived questions appear in activity history but are
  excluded, exactly as they are excluded from rewards today.
- "Latest-attempt accuracy" uses the same latest-assessment semantics as
  `/api/me/score-summary`, so key corrections and reassessments (migration
  0032) re-derive mastery rather than freezing a wrong snapshot.
- Mastery is a *study aid*, not an exam-readiness certification; copy must say
  so (same honesty rule as the activity leaderboard disclaimer).

Storage: new rollup table `user_topic_mastery` maintained incrementally on
attempt insert and on reassessment completion (reusing the 0032 job pattern).
`/api/me/progress` reads the rollup instead of re-aggregating all attempts on
every call — this also fixes the known perf debt of live aggregation.

### 4.2 Review scheduler (spaced repetition)

A Leitner 5-box queue per `(user_id, canonical_id)`, **verified-key questions
only** (reviewing a question with an unverified answer would be teaching
unproven facts on a schedule):

- Wrong answer → box 1. Correct answer → promote one box.
- Box intervals: 1, 3, 7, 16, 35 days (IST dates, like every other boundary).
- Box 5 correct → graduated (leaves the queue; mastery keeps the credit).
- Seed on rollout from the existing mistakes data (latest-attempt-wrong
  questions enter box 1). No reward backfill of any kind.

Surface: **`/revise` — the one revision destination** (§0.12). It holds
the Smart Review session — server-composed from due items (cap ~20
per session, oldest-due first), run through the existing
`practice_study_sessions` machinery with `attempts.context='review'` (already
in the context CHECK since 0002) — plus the queue browser (the former
standalone mistakes screen, now a tab here), due vocabulary (same queue,
`item_type='vocab'`, Part II §2.3), and the printable-sheet **export
button** (§9.7 is a button, not a feature). Nothing else on the site
offers "review" under any name.

### 4.3 Daily plan ("Today")

A server-composed card for the Finna Home plan column:

1. due reviews (count + one-tap Smart Review),
2. a new-questions target drawn from the learner's weakest
   practicing/proficient topics *within their saved exam's scope*,
3. the Daily Five,
4. quest ring status.

All live data; a new account or a cleared queue shows an honest empty state,
never invented tasks. Guests see the plan (it drives learning) but, as
everywhere, earn nothing from it.

### 4.4 Mocks

Unchanged in v2. A later phase may let `mastered` require a mock-section
threshold; explicitly out of scope now.

## 5. Point system v2

### 5.1 Earning spread (owner direction, 15 November 2026)

The owner's requirement: points must be **spread across the different
activity pillars** — quiz games, tests, practice, revision, contributions —
so no single activity fills the wallet. The mechanism is **per-source daily
sub-caps** under the overall 25-pt/day cap (§5.4): the sub-caps sum to ~34,
so a learner reaches the 25-pt ceiling only by mixing pillars, and grinding
any one pillar stalls out well short of it. XP is untouched by sub-caps
(still only the shared 300 XP/day budget), so leaderboards keep rewarding
raw activity while the wallet rewards balanced study.

All awards are server-derived ledger rows with namespaced `event_key`s (no
ledger CHECK change; existing kinds reused):

| Pillar | Event | Award | Daily points sub-cap | Bound / idempotency |
| --- | --- | --- | --- | --- |
| **Learn** (practice & in-quiz discovery) | first correct answer to a unique verified-key MCQ (v1 rule, unchanged per-event) | 10 XP + 1 pt | **12 pts** | once per canonical, ever (existing claim) |
| **Revise** | Smart Review session completed: ≥8 due items, ≥60% correct | 20 XP + 2 pts | **4 pts** (2 sessions) | `review:{user}:{ist_date}:{n}` |
| **Prove** (tests) | full mock submitted, non-late, frozen snapshot (v1 eligibility) | 30 XP + 3 pts | **3 pts** (1 mock) | `mock:{user}:{session_id}` |
| **Play** (quiz games) | completed multiplayer/solo game (gauntlet, speed, duel, party, cup, trail) with server-scored result ≥60% correct | 15 XP + 2 pts | **4 pts** (2 games) | `game:{user}:{room_id}`, kind `game` |
| **Play** | Daily Five entry completed | 10 XP + 1 pt | **1 pt** | existing one-entry-per-day PK |
| **Habit** | quest rings claimed (§5.2): warm-up / review / plan | 20+30+50 XP, 2+3+5 pts | **10 pts** | existing `daily_quest_claims` |
| **Milestones** | topic reaches proficient / mastered | 30 XP + 3 pts / 60 XP + 5 pts | outside sub-caps, inside 25 cap | `mastery:{user}:{topic}:{tier}`, once per topic-tier, ever |

Notes on the spread:

- **Discovery is deliberately the narrowest point source** relative to v1
  (12 pts/day vs an effective 30): answering new questions keeps paying full
  XP up to the 300 cap, but wallet growth now requires revision, tests and
  games too. This is the owner's "spread" requirement expressed as policy.
- Game awards pay on **server-owned results only** (frozen room snapshots,
  server timing — the Games contract in `LEARNING-REWARDS.md` §Games
  contract), and first-correct answers inside games still earn discovery
  under the Learn sub-cap; the game-completion award is on top, bounded at 2
  games/day. Lost duels with ≥60% accuracy still qualify — the award pays
  honest participation, not victory, so there is no incentive to farm weak
  opponents.
- Review *items* pay nothing per question — the once-per-canonical discovery
  claim stays intact; only completing the scheduled session pays.
- Mastery milestones are bounded by taxonomy size: finite, auditable
  total supply.

**Contribute pillar** (the owner's "contribution system granting points and
XP"): the machinery already exists — `contribution_credit` rows mirror into
the ledger as `kind='contribution'` — so v2 only fixes the amounts and the
cap treatment:

| Event | Award | Bound |
| --- | --- | --- |
| Published bank contribution (independently reviewed, live-verified) | 20 XP + 5 pts | max 3 credited/day |
| High-impact published contribution (answer-key/source fix passing the two-review quorum) | 40 XP + 10 pts | within the same 3/day |
| Content Studio first independently-reviewed publication (v1, unchanged) | 20 XP + 5 pts | once/day (migration 0035 rule) |

Contribution awards are **exempt from the 25-pt daily cap**: the rate limiter
is independent human review, not a counter, and reviewed corrections to the
bank are worth more than any study grind. Reversals keep appending negative
credit exactly as today. Votes, posting volume and self-publication still
earn nothing (DECISIONS #17).

Anti-abuse: review sessions are server-composed (the client cannot pick its
own 8 easy repeats), server-scored, with a server-measured minimum response
latency (e.g. ≥3s/item) gating session and game awards — a deterrent
heuristic, not a proof, same stance as v1's caps.

### 5.2 Quest rings rewired to the loop

Keep three rings and the existing claim mechanics, repoint them:

1. **Warm-up** — 10 scored attempts or 1 game (as today).
2. **Review ring** — clear 8 due review items (replaces cross_stream_triad).
3. **Plan ring** — complete today's plan (replaces mastery_closure).

Quest keys are data in `daily_quest_claims`; old claims remain historical.

### 5.3 One streak

`reward_profiles.current_streak_days` becomes the single authority. A day
qualifies on ≥1 eligible scored attempt (any context) or a completed review
session. `/api/me/progress` reads it for accounts; the attempt-derived
computation remains only for guests, labeled "device activity", since guests
have no reward profile. Shields unchanged.

### 5.4 Spending — owner-calibrated economy (decided 15 November 2026)

The owner fixed the targets: **the paid plan is ₹100/month**, and one month
of Pro should be earnable in **about 2 months of daily use or about 3 months
of average use**.

Those two targets imply a heavy:average earning ratio of 1.5, but under
uncapped v2 rules a maxed-out day (~44 pts: 30 discovery + 4 sessions + 10
quests) is nearly 3× a typical day (~15 pts). The calibration therefore needs
one new lever: a **daily reward-points cap of 25 points** (IST day, points
only — the 300 XP/day cap is unchanged, so leaderboards and levels are
unaffected; once the points cap is reached, awards still pay their XP).

| Quantity | Value | Check |
| --- | --- | --- |
| **pro-month** catalog offer | **1500 pts → 30 Pro days** | primary redemption |
| Daily use (hits the 25-pt cap) | 25 pts/day | 1500 / 25 = **60 days ≈ 2 months** ✓ |
| Average use (~12 new correct questions + 1 review session + warm-up quest) | ~16–17 pts/day | 1500 / 16.7 = **90 days ≈ 3 months** ✓ |
| **pro-week** offer | **400 pts → 7 Pro days** | repriced from the provisional 1000; ~proportional to pro-month |
| Streak shield | 25 pts (unchanged) | one full day's earnings |
| Implied point value | ~15 pts ≈ ₹1 | 1500 pts ≈ the ₹100 monthly plan |

Notes:

- The ₹100/month price itself is billing configuration (Razorpay plan +
  pricing copy), outside the reward schema; recorded here so the economy and
  the price stay calibrated together. **As of 16 November 2026 that price is
  real**: live Razorpay plans exist at ₹100/month (checkout still disabled
  pending launch), new checkout is monthly-only (six-month/yearly retired),
  and the owner can set **₹50/month** on selected accounts
  (`billing_account_rates`, 0089). The ₹50 discount does **not** change this
  calibration: points redeem into *days of Pro*, not rupees, so the catalog
  prices (1500/400 pts) and the daily cap stay anchored to the standard
  ₹100 plan. The "implied point value" row below is a sanity check against
  the standard price only; a discounted account simply gets a better deal
  either way, which is the point of the discount.
- Free-plan limits (50 practice answers/day, 1 mock/calendar month, 20
  mistakes/day) do not block the earning spread: the 25-pt cap is reachable
  without a mock (12 Learn + 4 Revise + 4 Play + 1 Daily Five + 10 quests
  ≥ 25), and 12 first-correct answers fit well inside the 50-answer limit.
  This matters because the earn-your-way-to-Pro story (§5.4's whole premise)
  must work for the learner who hasn't paid yet. The 1-mock/month limit does
  mean the Prove sub-cap is effectively Pro-only on a daily basis — accepted:
  mocks are a Pro perk, and the cap math never required them.
- The existing 1-redemption/account/30-days rule stays for Pro offers. With
  the 25-pt cap, pro-month takes ≥60 days to afford, so the rule is never the
  binding constraint; it remains as a backstop. Shields and future small
  items get per-item limits instead.
- Subsidy check: the most engaged learners effectively earn ≤₹50/month of
  access value — sustainable next to the ₹100 plan, and earned access starts
  only after existing paid/trial periods, as v1 already enforces.

**The free month (owner question, 16 November 2026 — delegated and
decided).** The owner asked whether a user should "claim 1 month free
after long use or points", and whether upvotes or content should earn
points, delegating the fair-and-unabusable design. Decision: **the points
wallet is the loyalty program — one path, no second one.**

- *"Long use" does not get its own grant.* Account age is the single
  cheapest thing to farm (register, park, wait); points already measure
  the only "long use" that matters — verified study over time — and the
  §5.4 calibration already delivers exactly the owner's wish: a diligent
  learner claims a free month (pro-month, 1500 pts) after ~2 months, an
  average one after ~3. A tenure grant beside it would double-pay the
  same loyalty and create the farmable copy.
- *Upvotes never earn points* — Part II §4.2 stands, and this question is
  why it exists: votes are the one signal users can manufacture socially
  (rings, trading), and pricing them turns every moderation case into an
  economy dispute. What upvotes DO buy is the trust ladder → Mentor tier
  → invitation into contribution work — which is where social effort
  legitimately reaches the wallet, behind an independent human review.
- *Content earns points only through that reviewed contribution pipeline*
  (§5.1 Contribute: 20 XP + 5 pts, high-impact 40 + 10, ≤3 credited/day,
  reviewer-gated, outside the daily cap). The rate limiter is a person
  checking the work, not a counter — unabusable by construction, because
  the abuse would have to get past a human reviewer with an audit trail.
- *Make it legible*: the Rewards screen gains a **"Your free month"
  meter** — points toward 1500, e.g. "62% earned" — so the existing
  redemption *feels* like the claimable free month the owner wants. A
  meter, not a countdown; no guilt mechanics (§0.6). This is the only UI
  change the decision needs.

Why this can't be abused, in one list: awards need server-scored correct
answers on verified-key questions; each question pays once per lifetime;
25 pts/day hard cap; sub-caps force mixing pillars; contributions pass
human review; votes mint nothing; tenure mints nothing. Every farming
strategy left is just… studying.

### 5.5 Admin access grants — ✅ IMPLEMENTED 16 November 2026

Shipped as migration **`0089_owner_billing_access`** plus
`api/app/routers/billing.py` admin endpoints and the owner panel at
**Admin → Rewards & accounts → "Monthly price & extra Pro days"**
(see `ACCOUNTS-BILLING.md` §Owner prices and `RAZORPAY-SETUP-20261116.md`
for evidence; 27 billing/access/rewards tests green, full prod-dump
migration rehearsal passed). As built:

- Table is **`billing_access_grants`** (not the proposed `access_grants`):
  `(id, user_id, granted_by, idempotency_key, days, starts_at, ends_at,
  created_at)`, days bounded **1–3650**, `UNIQUE(user_id,
  idempotency_key)`, and an immutability trigger (`review_immutable()`) —
  no UPDATE/DELETE ever. Repeated grant requests replay via the operation
  key instead of double-granting.
- A grant **stacks after `max(ends_at)` of all existing access** (trial,
  paid, reward redemption, prior grants), never touches Razorpay,
  `users.plan_*` or renewal dates, and is read through the extended
  `account_has_pro()` (paid ∪ redemptions ∪ grants — the union IV.3
  proposed is now the deployed function).
- Writes keep owner + CSRF + staff-MFA checks and record actor-bound audit
  events. The proposed free-text *reason* field and 7-day one-click preset
  were not built; the audit trail carries attribution. Revocation has no
  surface yet — if ever needed it must append, never delete (the trigger
  enforces this).
- **Grants confer access only — never XP or points** (held, as designed).
  Points adjustments remain the ledger `kind='adjustment'` path.
- Billing UI shows granted access as its own `granted` status, separate
  from paid and rewarded, and lists active grant windows.

Shipped alongside it, *not in the original draft*: **per-account pricing**
— `billing_account_rates(user_id, amount_paise CHECK IN (5000,10000))`
lets the owner set ₹50/month on selected registered accounts (standard
₹100 otherwise; anonymous visitors always see ₹100). Prices apply to the
*next new* subscription; existing mandates keep their agreed rate, and no
checkout parameter can select the discount. Provider plan references are
versioned by price and immutable (the old ₹99 reference is retired but
preserved).

**Bulk ₹50 assignment — implemented/deployed18November2026 (owner request
16November).** The owner wants to grant ₹50/month to *known
people* in bulk — "all the mobile numbers from a WhatsApp group" — not
one email lookup at a time. Reality check first: **accounts have no
phone number anywhere in the schema** (verified — email + Google identity
only), so phone matching cannot work today and must not be faked. Two
mechanisms that do work, both writing the same `billing_account_rates`
rows the shipped tool writes:

1. **Email allowlist** — owner pastes a list of emails into Admin →
   Rewards & accounts; table
   `billing_rate_allowlist(email_normalized PK, amount_paise, added_by,
   note, created_at, applied_user_id NULL, applied_at NULL)`. Matching is
   applied immediately for existing accounts and **at signup/first-login**
   for future ones (the WhatsApp friend who hasn't registered yet — the
   actual bulk case). Owner-only visibility; one note per batch ("Group
   XYZ"); removing an entry stops future application but never silently
   revokes an applied rate (restore ₹100 per account, as today, with
   audit).
2. **Group claim code** — for when the owner has a WhatsApp group but not
   its members' emails: a code/link posted into the group;
   `billing_rate_codes(code PK, amount_paise, max_uses, uses, expires_at,
   created_by, revoked_at NULL)` + a redemption row per account. A
   signed-in account redeeming it gets the ₹50 rate. Leak containment,
   since anything posted in a group travels: max uses, expiry, one
   redemption per account, owner revocation, full audit of who redeemed —
   and the blast radius is inherently small (a discount on the *next*
   subscription, never free access, never points).

Implementation receipt: `reports/finnaplan-v11-bulk-20261118/README.md`.
0109 uses verified email ownership before once-only matching, exact batch preview
and durable request keys. Group claims are explicit, bounded and replay-safe;
owner search and a paginated claim audit retain history. Assignments change the
next new subscription price only. Actual email transport, paid checkout and
referrals remain independently gated.

Phone-number matching is **deferred until accounts have a verified phone
field**, which needs SMS infrastructure this codebase doesn't have (the
same deliberate scope-cut recorded in the scholarship module). Both
mechanisms keep every shipped invariant: rates apply to the next new
subscription only, existing mandates untouched, no checkout parameter can
self-select a discount, owner + MFA + audit on every write.

### 5.6 Deliberately not building

- The mobile redesign's invented four-balance economy, or any coin/gem second
  currency. (Points-priced cosmetics are fine and designed in §12.8 — the
  ban is on a *second* currency, not on cosmetic spending.)
- Badges/achievement walls — levels, titles, leagues and mastery tiers are
  enough signal; revisit only with evidence of demand.
- Difficulty-based pay multipliers — flat rates keep the economy auditable
  and respect the retired-labels decision.
- Any reward for votes, posting volume, desk activity, or self-reported
  completion (existing policy, restated).

## 6. Schema sketch (future migration 0090+, not written yet)

(Originally "0084+"; 0084–0089 have since been used by stats, the four
current-affairs migrations and owner billing. Next free number: 0090.)

- `user_topic_mastery(user_id, subject_id, topic, state, distinct_attempted,
  distinct_correct_latest, last_verified_activity_at, proficient_at,
  mastered_at, updated_at)` — PK `(user_id, subject_id, topic)`.
- `review_items(user_id, canonical_id, box, due_on, last_result,
  last_attempt_id, updated_at)` — PK `(user_id, canonical_id)`, partial index
  `WHERE due_on <= current IST date`.
- Review sessions reuse `practice_study_sessions` with a session kind and a
  frozen served-item list (same snapshot discipline as mocks).
- No changes to `reward_ledger` shape; new awards are rows with namespaced
  event keys. Rehearse on a disposable dump clone per CLAUDE.md; never edit
  applied migrations.

## 7. API surface

- `GET /api/me/mastery` — rollup per subject/topic.
- `GET /api/me/review-queue` — due counts; `POST /api/review-sessions` —
  compose a Smart Review (answers flow through the existing study-session
  answer endpoint).
- `GET /api/me/today` — the composed plan.
- `/api/rewards/me` gains the rewired quest definitions (shape unchanged).
- **Mobile trap:** every new learner-facing GET must be deliberately added to
  the `MobileBoundary` allowlist in `mobile_identity.py`, with the companion
  tests extended — widening is an owner-visible decision, not a side effect.

## 8. UI in the Finna language

The Finna Web reference already contains the vocabulary this design fills:
a plan column on Home, quest rings with a "Claim +XP" widget, and streak
stats. Concretely:

- **Home plan column**: the Today card (§4.3).
- **Exam progress / Profile**: a mastery grid per subject → topic replacing
  raw accuracy tables; rusty shown as an overlay, never as lost progress.
- **Rewards screen**: no structural change — session and milestone awards
  appear in the existing history/breakdown automatically via the ledger.
- Prototype markup over README, per `DESIGN-FIDELITY.md`, when porting the
  not-yet-ported Profile/Rewards reference layouts.

## 9. New feature slate (owner request, 15 November 2026)

Net-new learner-facing features that plug into the loop and the spread
economy. Each line names what it reuses — nothing here needs a new economy
mechanism beyond §5. Ordered by suggested build priority:

1. **Smart Review + Today card** (§4.2–4.3) — the core loop surfaces; reuses
   `practice_study_sessions`, mistakes data, quest claims.
2. **Mastery map** — subject → topic mastery grid on Exam progress and
   Profile (§8), from the `user_topic_mastery` rollup; rusty overlay; honest
   empty states.
3. ~~**Admin access grants** (§5.5)~~ — ✅ shipped 16 November 2026
   (migration 0089); see §5.5 for as-built details.
4. **Current-affairs daily quiz** — a dated 5-question quiz, freshness-gated
   by review state; pays through the normal Play sub-cap like Daily Five.
   Falls back to an honest "no checked items today" empty state.
   *Updated 16 November 2026*: current affairs is now two subsystems — the
   editorial tables (0064/0065) **and** the new feed/briefs pipeline
   (0085–0088: YouTube MCQ drafting, free RSS sources, runtime grants,
   briefs; design in `Currentaffairs.md`). The quiz must draw only from
   **reviewed/published** items in either source — AI-drafted MCQs from the
   YouTube pipeline never reach learners (or this quiz) without review, the
   same discipline that keeps them out of the bank.
5. **Cup seasons (league nights)** — a scheduled weekly cup per stream
   cohort using the existing cup mode and boards; seasonal titles only, no
   extra points beyond the §5.1 game award. Resets use IST weeks like
   leagues.
6. **Shared-test challenges** — shareable tests (0079) gain a per-test
   score board among people with the link; XP/points flow only through
   existing discovery rules (a shared test is practice), so there is nothing
   new to farm.
7. **Printable revision sheet** — an **export button inside `/revise`**
   (§0.12; not a standalone feature): a learner's due reviews / mistakes
   with explanations as a PDF (PDF library plumbing from 0077); study aid,
   no economy surface.
*De-duplicated 16 November 2026 — three former items removed:*
*vocabulary-in-the-review-loop* and *desk shared goals* were word-for-word
duplicates of Part II §2.3 and §1.4 and now live only there (one spec per
feature, or the two copies drift); *mastery certificates* were cut
entirely — a shareable "mastered" image is a badge by another name, which
§5.6 already declines, and the mastery map plus levels/titles carry the
same signal.

Explicitly deferred: anything requiring new moderation surface (public
tournaments with chat), cross-user point interactions, or mobile-first
builds (the `MobileBoundary` allowlist keeps mobile read-only on these until
widened deliberately).

Four further subsystems — the Study Desk upgrade, the vocabulary learner,
the feed & post system, and the helpful-vote model with its ranking
algorithm — are designed in the companion document
Part II of this file. None of them touch
the reward ledger; the no-points-for-social-activity policy holds
throughout.

## 10. Rollout phases

1. **Learn first, pay nothing new**: mastery rollup + review scheduler +
   Smart Review + Today card, with zero new award rows. Lets thresholds be
   tuned on real usage without minting anything.
2. **Habit**: unified streak, quest rewiring, review-session awards.
3. **Economy**: the §5.1 spread (sub-caps, game/mock awards, contribution
   amounts), the 25-pt daily cap, mastery milestones, catalog repricing
   (pro-month 1500 / pro-week 400) and enablement. (The admin grant tool
   originally slotted here shipped early — §5.5, 16 November 2026.)
4. **Feature slate**: §9 items in priority order, each shippable
   independently.

Each phase: new numbered migration rehearsed on a dump clone, isolated
PostgreSQL tests alongside the existing reward suite, local build, deploy via
`scripts/deploy.sh`, DEVLOG receipt.

## 11. Owner decisions

Decided 15 November 2026 (recorded in §5.1 and §5.4–5.5):

- Paid plan ₹100/month; pro-month redeemable at 1500 pts (≈2 months daily /
  ≈3 months average use); pro-week repriced to 400 pts; daily points cap 25.
- Points spread across pillars via per-source sub-caps; contributions pay
  points+XP (20/5, high-impact 40/10) outside the daily cap, reviewer-gated.
- Admin tool to grant arbitrary Pro days with a 7-day reward preset.

Decided/landed 16 November 2026:

- ₹100/month standard price confirmed and live-configured (checkout still
  disabled pending launch); new checkout monthly-only; ₹50/month assignable
  to selected accounts by the owner (`billing_account_rates`).
- §5.5 admin grants shipped as `billing_access_grants` (0089) — access
  only, never XP/points, exactly as designed.
- Focus subjects, the leaderboard decision, game boards and the Home
  layout: §12 addendum below.
- The free month: points are the single loyalty path (no tenure grant),
  upvotes never pay, content pays only via reviewed contributions; a
  "Your free month" meter on Rewards makes it legible (§5.4, owner-
  delegated 16 November).

**All remaining opens resolved 16 November 2026** — the owner said
"decide all for me"; the decisions below are assistant-made under that
delegation, recorded as initial constants (versioned, tunable only with
real usage evidence, every change a reviewed diff):

1. **Mastery thresholds**: the §4.1 table is adopted as written —
   5/10/20 distinct questions; 70% / 85% latest-attempt accuracy; the
   14-day proficient→mastered review gap; **45-day rusty window**. They
   are deliberately conservative: a too-easy "mastered" is a lie to the
   learner, a too-hard one is just slower — err slow.
2. **Game award threshold ≥60% stands**, and the contribution bound stays
   **3 credited/day** (the reviewer is the real limiter anyway).
3. **District dimension stays Daily-Five-only.** A district mastery or
   league view is population-gated exactly like exam cohorts (§0.11.3):
   build it when a real district cohort exists, not before.
4. **Catalog goes live when two things are true**: Phase D's
   reward-diagnostics reconciliation passes on a seeded week, **and**
   paid checkout has launched. Earned Pro must not predate purchasable
   Pro — the subsidy math (§5.4) should be real from the first
   redemption. *(Amended 16 Nov, §13.1: checkout itself now has two
   prerequisites — legal pages (terms/privacy/refund) published, and
   working email password recovery. The full flip checklist renders in
   the VI feature-gates panel.)*
5. **Claim codes**: default **100 max uses, 30-day expiry** (both
   editable per code). Allowlist applications at signup are **not**
   individually notified — they appear in the admin audit list for a
   weekly glance; the blast radius (a discount on a future subscription)
   doesn't warrant interrupting anyone, and there's no email infra yet
   anyway.
6. **§13: all six approved, in listed order**, each gated by its
   dependency — the email provider (#1) before the digest (#4) and
   before referral notifications. **Referral bounds**: 7 Pro days each
   side; the referred account must reach 10 scored attempts; ≤5 credited
   referrals per referrer per rolling year; launches only after paid
   checkout is live.

## 12. Addendum (16 November 2026): focus subjects, leaderboards, Home

Owner request: personal growth and a revision/study plan scoped to **the
subjects a learner actually cares about** ("everyone will not be interested
in every subject"), plus concrete decisions on the leaderboard, game
boards and the optimized Home layout. The spaced-repetition system itself
is already §4.2 and the feed/upvote ranking is already Part II §4 —
nothing there changes; this section personalizes what feeds them and
decides the display surfaces.

### 12.1 Focus subjects (choice-driven study plan)

Focus subjects sit **inside the primary-exam lens** (§0.11): the exam
decides the universe, focus subjects narrow it. A learner picks up to
**5 focus subjects** (from their primary exam's scope
by default; editable on Profile and inline on the Today card). Stored as
`user_focus_subjects(user_id, subject_id, created_at)` — PK pair, no
other state. Effects, all read-time:

- **Today's new-question target** (§4.3 item 2) draws from the weakest
  practicing/proficient topics *within focus subjects only*. With no
  focus set, it falls back to the saved exam's whole scope (today's
  behavior); with no saved exam either, honest empty state.
- **Mastery map** orders focus subjects first and defaults the Profile
  strip to them; everything else remains visible below — focus is a lens,
  never a filter that hides earned progress.
- **Review queue honesty rule**: spaced repetition reviews what you got
  *wrong*, not what you *like*. Due items from non-focus subjects stay in
  the queue and in the due count — forgetting curves don't care about
  interest. The concession to choice: Smart Review gains an optional
  "focus subjects only" toggle for a short session; the full queue is
  always one tap away and the Today due-count never lies by omission.
- **Weekly growth recap** (the "personal growth" surface — and the *only*
  weekly summary on the site; Desk's focus summary merged in here): a
  small card on Today each IST Monday — last week's XP, topics that
  advanced a mastery tier, reviews cleared, streak kept, focus time (from
  the server-timed desk focus sessions, when any) — computed from the
  ledger and rollups, never invented. Display only, no awards.

Economy: none. Focus changes *which* questions are suggested, never what
they pay — all §5.1 caps and claims are subject-agnostic, so flipping
focus subjects daily farms nothing.

### 12.2 The leaderboard decision

What the leaderboard shows (decided): **weekly XP inside a league cohort,
opt-in, handle + XP + rank only** — i.e. the existing league board stays
the one global board. What it must **never** show: accuracy, marks,
mastery tiers, wallet/points, or per-subject standings. Reasons: XP is
pure activity, safe to compare and already capped (300/day) so the board
has a fair ceiling; accuracy/marks boards shame struggling learners and
invite answer-farming; wallet is private economy; and per-subject boards
would fragment a small community into empty rooms. Weekly IST resets keep
it winnable by a newcomer; equal XP shares a rank (existing rule).

Presentation (new): show **top 10 + the viewer's neighborhood** (ranks
N−2…N+2 around you) instead of a top-100 wall — a mid-pack learner sees
beatable neighbors, not an unreachable summit. Opt-out accounts see their
own rank privately ("you'd be #23") without appearing to others
(unchanged privacy model).

### 12.3 Game leaderboards

Per-mode **weekly boards** (gauntlet, speed, duel wins, Daily Five streak)
from server-owned results only — same frozen-snapshot/server-scoring
contract as §5.1's Play awards, so there is nothing client-forgeable to
rank. Display: handle, mode score, rank; IST weeks; opt-in follows the
same flag as the XP board (one consent, all boards). Cup seasons (§9.5)
keep their own seasonal standings and titles. No new awards anywhere in
this — boards are display over results that already exist.

### 12.4 Home layout (optimized, decided)

Disambiguation (16 November): **"Home" is the `/feed` route** — the site
root redirects there since 16 November (`FINNA-REDESIGN-20261114.md`),
and the deployed redesign gives it a three-column contract (exam/plan/
progress · study/community stream · activity/saved). This section does
not invent a second Home; it assigns the priority list below **onto that
contract**: items 1–4 fill the left column top-down, the stream *is* item
6 (so "feed teaser" means the center column, not a duplicate widget), and
items 5 + 7 live in the right column. On phones the columns collapse into
the single priority-ordered list.

Signed-in Home, in priority order (one column on phones, Today pinned
first on desktop):

1. **Today card** (§4.3) — due reviews (one-tap Smart Review), the
   focus-subject question target, Daily Five, quest rings.
2. **Continue strip** — open mock / unfinished practice session resume
   (the existing ExamJourney resume data).
3. **Streak + level chip** — small header stat, not a panel; no guilt
   modals (§0.6).
4. **Mastery snapshot** — focus subjects first (§12.1), linking to the
   full map.
5. **Leaderboard teaser** — your league rank + two neighbors (§12.2),
   small, opt-in; hidden entirely when opted out.
6. **Feed teaser** — 3 For-you posts (Part II §4.3) incl. the
   "help someone" slot; links into the community tab.
7. **Weekly growth recap** — Mondays only (§12.1).

Browse (search, exams, papers) stays in the global nav above all of this —
Home must never bury the library (§0.1: browse wins). Signed-out Home is
unchanged by this addendum: library first, device-local progress, no fake
panels — a static one-line explainer of what Today becomes with an
account is the only advertisement.

Schema/API deltas this addendum adds to §6–7: `user_focus_subjects`,
`PATCH /api/me/focus-subjects`, the recap read (derivable from existing
tables; materialize only if measured slow), and board queries over
existing results. Mobile: all reads go through the deliberate
`MobileBoundary` widening rule (§7), as ever.

### 12.5 Phone optimization (web, 16 November 2026)

Context: the Finna redesign already ships a five-tab phone bar — **Home /
Exams / Library / Desk / Me** — with narrow geometry verified at 390px and
320px (`FINNA-REDESIGN-20261114.md` + its coverage audit). The new
surfaces slot into those five tabs; **no sixth tab, no new navigation
pattern**. Decisions:

- **One request, not one layout trick, is the real phone optimization.**
  `GET /api/me/today` returns the *entire* composed Today card (due count,
  focus target, Daily Five state, quest rings) in a single round trip —
  the phone Home renders from one GET, not four. Personal reads stay
  `private, no-store` (IV.2), so the speed comes from server-side
  composition, never client caching.
- **Home (phone)**: the §12.4 column order, single column; the Today card
  must fit above the fold at 390px with the due-review CTA as the primary
  thumb target. Leaderboard teaser collapses to one row (your rank + next
  neighbor); feed teaser lazy-loads below the fold; growth recap collapses
  to a tappable summary line on Mondays.
- **Smart Review (phone)**: full-screen one-question-at-a-time player —
  the existing practice player pattern, not a new component. Inline
  answering keeps `QuestionCard` (the owner-decided deviation from the
  reference's compact rows applies here too).
- **Mastery map (phone)**: subject accordion → topic chips; the dense
  desktop grid never renders under ~480px. Rusty is an icon overlay with
  the state in the accessible name (same honesty, less width).
- **Focus-subject picker (phone)**: bottom sheet from the Today card;
  inline checklist on desktop Profile. Same `PATCH`, same 5-subject cap.
- **Leaderboards (phone)**: neighborhood view (§12.2) is the default and
  the top-10 sits behind a toggle — the viewer's own context is the useful
  pixel at 390px. Game boards live where games live; XP board under Me.
  Counts over 99 use the established 99+ badge with the real number in
  the accessible name.
- **320px rule**: every new card is single-column, no horizontal scroll,
  no hover-only affordances. Loading/empty/error states are explicit —
  honest empty states are a phone feature too (a blank panel on a slow
  connection reads as a crash).

### 12.6 Mobile app (Expo) widening for these features

The IV.8 contract (allowlist diff + companion test + capability flag per
feature) applied to this addendum, in order:

1. **Reads first**: `/me/today`, `/me/mastery`, `/me/review-queue`,
   `/me/focus-subjects` GET, leaderboard/game-board GETs — display-only,
   no economy writes, safest possible widening.
2. **Then the practice writes**: review-session compose + the existing
   idempotent answer endpoint (offline attempts replay through it,
   IV.8.3). This is the point where the app earns like the web does —
   same server-side awards, nothing app-specific to audit.
3. **Focus-subject PATCH** ships with step 2 (first mobile write beyond
   attempts; trivial, but it is still a deliberate allowlist line).
4. Community/feed reads later; community **writes stay web-only** until
   moderation tooling is proven (unchanged IV.8 stance).

Each step: one allowlist diff, one `test_mobile_companion.py` extension,
one capability-list entry so old app builds degrade gracefully.

**Scope rule (§0.12.2, binding):** the app never chases screen parity
with the phone web. Every widening above must earn its place with
something native — offline practice and queued replay first, push later —
or it doesn't happen. "The web has it" is not a reason; it's the
beginning of maintaining every screen twice.

### 12.7 Profile tools (16 November 2026)

The Profile ("Me") tab becomes the one place for *account self-service* —
§0.12 applied to the self. One screen, four groups, almost all of it
already existing and merely gathered:

1. **Identity**: avatar (the existing editor), handle, leaderboard
   opt-in/out, creator-profile link when one exists.
2. **Study setup**: primary/saved exams (§0.11.1), focus subjects
   (§12.1), exam date for the taper (§13 #6) — the three personalization
   levers, side by side, each one tap from what it controls.
3. **Privacy & security**: MFA (0033), active sessions list with revoke,
   desk progress-sharing opt-in, blocked users. Plus **export my data**
   (a JSON of the account's own attempts/progress/posts — cheap honesty,
   reads only owned rows) and **delete my account** (existing account
   boundaries; entitlements end, immutable community/audit history is
   anonymized, not rewritten — the same append-only principle as
   everywhere).
4. **Wallet shortcut**: the Rewards screen link with the free-month
   meter peeking through (the meter itself stays on Rewards — §0.6).

Nothing here invents a subsystem; the section exists so these stop being
scattered across settings pages. Builds in V.5 alongside the boards.

### 12.8 Profile edit & the cosmetics system (owner request, 16 Nov 2026)

Baseline, verified in `AVATAR-EDITOR.md` + migration 0041 (live since
2026-10-23): the v3 avatar editor at `/avatar` — seven categories, 19
free starters, 7 level-reward unlocks, durable ownership in
`user_avatar_items` that survives XP reversals, append-only
`avatar_events`, `avatar_catalog.json` as the single catalog authority,
server-side catalog-only validation, and a deliberate launch cut: **no
coin shop, no paid cosmetics**. This section designs that deferred layer.

**A. Profile edit.** Handle: unique, renameable **once per 30 days**
(impersonation-churn guard), rename recorded as an account event. Short
bio: 140 chars, text-only, reportable, `needs_approval` honored like any
post. Both edit from the §12.7 identity group; avatar editing stays in
the existing editor.

**B. The points shop.** Points are the **only** purchase currency —
§5.6 bans a second cosmetic currency and §7.3 bans cash microtransactions,
so the sanctioned path is: catalog items gain an optional `price_points`
(bands: common 15–30, distinctive 50–75, showpiece frames 100–150). A
purchase is one transaction: a namespaced ledger spend row
(`cosmetic:{user}:{item}`, per-user lock, idempotent, own-once) +
`user_avatar_items` insert + `avatar_events` append — **zero new
tables**. Owned is owned forever: survives downgrades, XP reversals, and
rank is never affected (existing rules extend). The free-month meter
shows the real balance, so buying a hat visibly sets the meter back —
an honest, voluntary tradeoff, and a healthy points sink (currency
leaves circulation without costing access subsidy).

**C. The acquisition map** (complete; a path not listed doesn't exist):
free starters (live) · level unlocks (live) · points shop (B) ·
**earned-only prestige** — mastery-tier, league and cup-season items
that can *never* be purchased and have no purchasable lookalike, so an
earned frame stays meaningful. Decided against: **Pro-exclusive
cosmetics** — Pro buys capacity, never identity (§7.3); a payment-status
skin on leaderboards is soft pay-to-signal.

**D. Hard rules** (the lines that keep this clean): no loot boxes or
randomized purchases, ever — gambling-adjacent mechanics have no place
in front of students; no FOMO scarcity — seasonal items are earned
in-season and return in later seasons; no trading or gifting (the
no-transfers rule); no user-uploaded art (moderation surface — the
curated catalog is the whole inventory); cosmetics never affect
gameplay, ranking, visibility or trust signals (tier flair stays
visually distinct from decoration).

**E. The addition system** (how new cosmetics enter): admin-curated
only, through an **Admin → Cosmetics** console following the
reward-catalog pattern — list, add/retire item (category, asset
reference, `price_points` or unlock rule, active flag), optimistic
version + reason + audit + MFA. Honest coupling note: item *data* is
instant (catalog JSON), but new *art* is SVG geometry in the renderer,
so genuinely new shapes ship with a frontend release — the console
validates that an asset reference exists before an item can activate.
Existing catalog values stay compatible (the 0041 doc's standing rule).

**F. Build**: display/profile-edit pieces with V.5; the shop needs V.4's
economy live first (spending requires the cap/ledger rewrite to be
settled). Admin console rides V.12 with the rest of Part VI.

## 13. Proposed improvements (assistant suggestions, 16 November 2026)

Requested by the owner ("any new features or functions you want to add").
**None of these is decided** — each needs an explicit owner yes. Every one
is economy-safe by construction (access or display, never minted points)
and ordered by expected value per effort:

1. **Email delivery provider** — the highest-leverage unbuilt thing on
   the whole list, and it isn't a feature: `ACCOUNTS-BILLING.md` records
   that signup works but email verification and self-service password
   recovery don't exist. Everything below that touches email (digests,
   allowlist trust, referral notifications) stands on this, and losing a
   password today costs a support thread.
2. **Referral Pro-days** — "invite a friend; when they register and make
   their first 10 scored attempts, you both get 7 days of Pro" — paid as
   `billing_access_grants` rows (access only, never XP/points — the §5.5
   invariant), bounded (e.g. ≤5 credited referrals/account/year,
   owner-tunable), attempt-gated so dead signups pay nothing. Fits the
   WhatsApp-group growth reality this site actually lives in.
3. **WhatsApp share cards** — a share link for any question or shareable
   test (0079) with a proper OG preview (question text, exam/year badge,
   site name). Pure growth surface for the same reality: prep groups
   forward questions all day; today a forwarded link renders as a bare
   URL. No economy surface at all.
4. **Due-review digest (opt-in)** — one email per day at most, IST
   evening: due-review count, streak status, one-tap Smart Review link.
   Strictly opt-in, one-click unsubscribe, silent when the queue is
   empty (honest empty states apply to inboxes too). Depends on #1.
5. **Onboarding diagnostic** — on choosing a primary exam (§0.11.1), an
   optional 10-question mixed quiz from its verified pool seeds initial
   mastery estimates and suggests focus subjects (§12.1). Pays normal
   discovery rules — it *is* practice, nothing special to farm — and
   turns the cold-start Today card into a useful one on day one.
6. **Exam-day countdown + plan taper** — the learner sets their exam
   date (the calendar, 0042, is the single source of official dates;
   the Desk calendar, Part II §1.8, reads the same source); Today
   gradually shifts composition from new questions toward due reviews
   and mocks in the final weeks. Display/composition logic only; no new
   awards.

*(A "question of the day" proposal was cut in the 16 November
de-duplication pass: it was Daily Five with a third coat of paint — the
site would have had three daily-question features. The useful fragment
survives as a share-card variant of #3: Daily Five's first question can
render as a public shareable card.)*

Deliberately **not** proposed: cash referral bonuses, point gifts,
social-share rewards, or any mechanism where growth actions mint
currency — all of it would reopen the farming surface §5 closed.

### 13.1 Second sweep — what the plan was still missing (owner asked, 16 Nov)

Genuine gaps found on a final pass; none is a feature, all are
launch-critical or strategy-critical:

7. **Legal pages before checkout — a hard gate.** Terms of service,
   privacy policy, and a refund/cancellation policy page. Razorpay
   expects them, Indian consumer-protection rules expect them, and the
   plan currently schedules paid launch with none written. Add to the
   §11 resolution-4 checklist: **checkout does not flip without them.**
   (Also verify GST/invoicing obligations for the ₹100 subscription with
   the provider's documentation — flagged for the owner to confirm, not
   decided here.)
8. **Email provider before checkout, not just before the digest.** A
   paying customer with an unrecoverable password is a refund dispute
   waiting to happen. §13 #1 gains a second gate: **live checkout waits
   for working password recovery.**
9. **SEO is the missing growth engine.** The whole thesis is browse-first
   public content, yet the web app is a client-rendered SPA — search
   engines see an empty shell, while every bank question *is* a search
   query someone types before an exam. Add to T2: prerender/SSG for
   public question, paper and exam pages (the same anonymous-cacheable
   tier V.1 builds), plus sitemaps and structured data. Likely the
   highest-leverage growth work in the entire document.
10. **Honest measurement for §0.8.** The success metrics have no
    measurement plan. One tiny self-hosted events table (page views +
    the §0.8 events, no third-party SDKs — consistent with IV.8.4's
    stance) so "papers browsed per session" is a real number, not a
    feeling. Private by design: counts, not profiles.
11. **A support surface.** `/help`: FAQ, contact email, and the
    documented support-assisted password recovery (until #8 lands).
    Costs an afternoon; its absence costs trust at the first confused
    paying user.
12. **An accessibility pass** on the new surfaces (composer, calendar,
    review player): keyboard paths, focus management, accessible names
    on icon buttons. Exam aspirants on cheap phones and screen readers
    exist; the redesign audit already notes gaps — schedule it with V.9
    rather than "later".
13. **Content licensing check per new exam body** (S2/S3): MPSC past
    papers' reuse stance is established practice here; each new body's
    stance gets verified *before* ingestion, recorded in the V.7
    checklist as step 0.
14. **Mizo-language UI** — noted as an open consideration, not a
    commitment: the audience is Mizoram-first and the UI is
    English-only. Revisit after launch metrics show where learners
    struggle; glosses (Part II §2) are the near-term answer.

Third and final sweep (16 Nov, before declaring the design saturated):

15. **Login throttling** — IV.11 covers currency and privilege threats
    but never names credential-stuffing: per-account + per-IP sign-in
    backoff and a lockout-with-recovery path (recovery needs #8's email
    anyway). One afternoon, standard pattern, belongs in V.2's phase.
16. **Renewal-failure comms** — when a Razorpay mandate charge fails,
    the webhook already records the state; the *user* currently learns
    nothing until access lapses. Once email exists: one honest "your
    renewal failed, here's what happens and when" message, and billing
    shows the real provider state. No dunning pressure campaigns — one
    notice, honest countdown.
17. **Community cold start** — launch day's feed is empty, and the rules
    (rightly) ban invented activity. The honest seeding strategy: the
    owner and early reviewers post real study notes under their own
    names, Daily Five and doubts-on-questions carry the early social
    load (they generate real content as a side effect of studying), and
    the feed tab stays visually secondary until it has something true to
    say. Patience is the feature.

**Declared saturated.** Anything further added to this document before
real users touch V.2 would be speculation stacking on speculation — the
next improvements must come from measured §0.8 numbers, support
questions, and what the first hundred learners actually do. The plan's
own discipline (honest data over invention) applies to the plan itself.

*(Narrowed 22 November 2026, Part VII: saturation binds **additions**.
Subtraction stays open — a route nobody can find is already failing
without a metric to prove it. See §VII.0.)*

## 14. The Helper Calendar (owner request, 16 November 2026)

One calendar at `/calendar` — the single scheduling surface for the whole
site, replacing nothing but *unifying* what already exists (the exam
calendar 0042, its reminder worker, the Desk calendar reads) with what
Parts I and §12 create. It is composed of **toggleable layers over one
month/week grid**; every layer is honest data, and the calendar as a
whole **mints nothing and punishes nothing** — it schedules suggestions.

| Layer | Contents | Source |
| --- | --- | --- |
| **Official** | exam notifications, application windows, exam dates — dated reviewed entries only | exam calendar (0042), unchanged; reminders via its existing worker |
| **My exams** | the learner's own target exam date(s) with countdown; drives the §13.6 plan taper | learner-set, one tap from an official entry or manual |
| **Review forecast** | upcoming spaced-review load per day ("Sat: 32 due") projected from the Leitner queue — the learner sees a pile-up *before* it lands | `review_items.due_on`, no new schema; recomputes as they answer |
| **Progress tests** | a recurring self-test slot (weekly/fortnightly, learner-chosen weekday): a normal mock composed from their exam scope on that day | mock machinery unchanged; normal Prove award, nothing calendar-specific |
| **Personal** | the learner's own dated notes/goals ("finish Polity ch. 3") — private, plain text, CRUD | new `calendar_entries` |
| **Habit (past)** | streak heatmap of days with eligible activity — the look-back twin of the forecast | attempts/streak rollups, display only |
| **Community & play** | weekly cup night (§9.5), desk events (Part II §1.8 reads these same sources — one calendar store, two views) | existing schedules |

Rules and decisions (made under the standing "decide all for me"):

1. **Early review is allowed, honestly.** Tapping a future day's forecast
   lets the learner clear reviews early; the next interval is computed
   from the *actual* review date (standard Leitner behavior). The
   forecast is a projection, and the UI says so — it shifts as you work.
2. **A missed progress test reschedules silently.** No guilt banner, no
   streak damage, no penalty — §0.6 applies to calendars with special
   force, because exam aspirants already live under deadline dread. The
   slot simply moves to the next cadence day.
3. **Load-aware nudge**: when the forecast shows a heavy day coming,
   Today may *suggest* "clear 10 early?" — a suggestion row, never a
   requirement, never counted against the plan (same contract as Atlas
   drills).
4. **ICS feed export** (my addition — the highest-value helper here): a
   secret, revocable per-user feed URL (`calendar_feed_tokens`, token
   hashed at rest) so the whole thing lands in Google Calendar /
   phone calendars, which is where real reminder infrastructure already
   lives — no SMS/push build needed. The feed contains only that
   learner's own layers; revoking the token kills the URL.
5. **Email reminders ride the digest** (§13 #4), opt-in, once the email
   provider (#1) exists — the calendar never grows its own notification
   channel.
6. **Guests** see the Official layer only (it's public data); everything
   personal requires the account that owns it.

Schema sketch (with the 0090+ block): `calendar_entries(id, user_id,
date, title, note, kind CHECK ('personal','progress-test'), recurrence
NULL, created_at, updated_at)`; `calendar_feed_tokens(user_id,
token_hash, created_at, revoked_at NULL)`. The forecast, habit, official
and community layers need **no new tables** — they are reads over what
already exists, which is the test that the calendar is a lens and not a
new subsystem. Mobile: layer GETs in the first widening step (§12.6);
personal-entry writes ride the second. Build order: forecast + official
layers with V.2 (they're free once `review_items` exists); personal
entries, progress-test slots and ICS in V.5.

---

# Part II — Desk, vocabulary and community

Status: **proposal, nothing implemented**. Drafted 15 November 2026 as the
companion to Part I, covering four subsystems the
owner requested the same day: the Study Desk upgrade, a full vocabulary
learner, the feed & post system, and the likes/upvote model with its ranking
algorithm. The owner delegated the detailed decisions ("decide for me");
every choice below is therefore a concrete default, flagged where it is
reversible. Standing policies carried forward unchanged: **no social
activity ever earns XP or points** (DECISIONS #17: votes are discovery-only),
provenance and answer-reveal gates stay intact, honest empty states, opt-in
visibility everywhere.

## 1. Study Desk upgrade (Desk v4)

Baseline: Desk v3 (`STUDY-DESK.md`) — personal workspace plus six-seat
private rooms, invitations, chat, focus sessions, moderation, retention.
v4's theme: **the Desk becomes the home of the learning loop**, while
remaining non-economic.

1. **Toolbox, not a second home** (amended 16 November 2026 per §0.12).
   The original v4 draft rendered the Today card at the top of `/desk` —
   the same card in two homes, which is exactly the duplication §0.12
   exists to kill. The personal desk is now purely **your things**:
   notes, saved questions, the focus timer. The Today card lives on Home
   only; `/desk` links to it with one line, never re-renders it. The
   self-reported weekly answer target is **retired outright** — the
   Monday growth recap (§12.1) and quest rings already count the same
   thing honestly, and self-reporting violated the honest-counting rule
   anyway.
2. ~~**Mastery snapshot.**~~ Cut 16 November 2026 (§0.12): Home already
   carries the mastery snapshot (§12.4 item 4) — the same strip on the
   personal desk would be the Today-card duplication again, one item
   down. The desk links to the mastery map; it doesn't re-render it.
3. **Desk sessions.** A room can start a synchronized practice set over its
   shared/saved questions, reusing the existing party-mode game room
   machinery (frozen snapshots, server scoring). Economy: normal game rules
   apply — discovery and the Play sub-cap; nothing desk-specific pays.
4. **Shared weekly goal (display only).** One goal per room per IST week
   (e.g. "300 scored attempts together"), progress aggregated from members
   who already opted into sharing progress. A progress bar, not a currency:
   completing it awards nothing, by policy.
5. **Review circle.** Members can flag a question to the room ("discuss
   this") — extends the existing posted-mistakes mechanism; the room's
   shared-questions tab gains a "needs discussion" filter and resolved
   marks. Answer-reveal gates still apply per member.
6. **Focus v2.** Pomodoro presets on the existing server-timed focus
   sessions; an opt-in room focus board (display only, explicitly earns
   nothing — unchanged policy). *(The "private weekly focus summary"
   originally here was merged into the one weekly growth recap, Part I
   §12.1, in the 16 November de-duplication pass — two weekly summaries
   was one too many; the recap gains a focus-time line instead.)*
7. **Notes v2.** Notes attachable to a canonical question ID, linkable from
   room chat, exportable to PDF via the 0077 plumbing.
8. **Desk calendar — a view, never a store** (§0.12). The room shows a
   room-filtered view of the one Helper Calendar (§14): saved-exam
   countdowns and members' opt-in milestones. No desk-side calendar
   tables; entries created here are `calendar_entries` rows like any
   other.

Decided constraints: rooms stay private and six-seat; public/class desks
stay disabled; Pro still gates room creation (3/owner); everything ships
behind the existing `STUDY_DESKS_PRIVATE_ENABLED` flag; mobile gets GET-only
access unless the `MobileBoundary` allowlist is deliberately widened.

## 2. Vocabulary learner v2

Baseline: migration 0048 recognition drills that already write `attempts`.

1. **Decks.** Three sources, all reviewed before going live:
   - *Bank-derived English*: synonyms/antonyms/one-word-substitution/idiom
     questions already in the bank, grouped into decks by topic — these are
     canonical questions and keep their provenance.
   - *Curated word cards*: editor-authored cards (word, meaning, usage,
     Mizo gloss) published through the Content Studio review pipeline, never
     straight to live.
   - *Mizo↔English pairs* for the Mizo paper, same curated path.
2. **Modes.** Recognition (existing MCQ drill), delayed recall (re-asked
   days later via the scheduler), and usage cloze (pick the word that fits
   the sentence). All server-scored.
3. **One scheduler.** Vocab items enter the same Leitner `review_items`
   queue as questions, typed (`item_type='vocab'`). A "5 words a day" card
   appears on Today; due vocab can run as its own short session or mix into
   Smart Review.
4. **Progress.** Per-deck progress with the same mastery semantics
   (latest-attempt based, decay overlay), a words-known counter, and honest
   zero states.
5. **Economy (decided).** Bank-derived vocab questions pay discovery
   normally — they are verified canonical questions. **Curated cards pay no
   per-card points ever**: they are not canonical questions, have no
   official-key provenance, and would be the easiest thing on the site to
   farm. Vocab activity still counts toward quest rings and review-session
   completion awards (the Revise pillar), so daily vocab work is rewarded —
   at session granularity, not per card.

## 3. Feed & post system v2

Baseline, verified in `api/app/routers/community.py` + `discussions.py`:
question-anchored posts (`kind IN ('doubt','explanation')`) with replies,
accepted answers, helpful votes (`post_votes`), blocks, reports, idempotent
creation, `hidden`/`needs_approval`/`before_fix` moderation flags, pinning,
and the **disclosure gate** — discussion of a question is visible only after
the viewer has attempted or deliberately unlocked it (spoiler and
mock/game-integrity protection). The feed is chronological;
`following`/`mcqs`/`materials` tabs return `available=false`.

### 3.1 Post types (decided)

| Kind | Anchor | Notes |
| --- | --- | --- |
| `doubt` / `explanation` (existing) | canonical question | unchanged, disclosure-gated |
| **`study`** (new) | free-standing | short text post: progress note, tip, strategy; optional subject/topic tag; optional link to an internal entity |
| **`material-share`** (new) | Content Studio publication | a share card for an already-reviewed material |

Hard rules: text only (no image uploads in v1 — that is a moderation surface
we are not staffing); links may point **only to internal entities**
(questions, materials, papers, exams) — no external URLs (spam defense);
sample/invented activity never seeded.

### 3.2 Following

New `follows(user_id, followed_id, created_at)` (PK pair, no counts shown
beyond honest integers). The `following` tab becomes real: chronological
posts from followed authors, same visibility/block/disclosure filters as
everywhere. Follow is one-way, free, and earns nothing.

### 3.3 Posting guards (decided)

- Registered accounts only (guests read).
- New-account throttle: accounts younger than 3 days **or** with fewer than
  50 scored attempts may reply and vote, but not create `study` posts —
  doubts on questions they attempted are always allowed (that is core
  learning).
- Rate limits: 5 top-level posts/day, 30 replies/day (server-enforced,
  per-account).
- Reports feed the existing moderation admin; repeat-flagged authors drop
  into `needs_approval` for new posts.

### 3.4 Feed tabs

| Tab | Composition |
| --- | --- |
| For-you | ranked (§4), all visible kinds |
| Following | chronological, followed authors |
| Doubts | existing view (incl. unanswered filter) |
| Materials | the reviewed materials catalog, newest first |

## 4. Likes/upvotes and the ranking algorithm

### 4.1 Vote model (decided)

- Keep the single positive **"Helpful"** vote (existing `post_votes`
  toggle). **No downvotes**: a small exam-prep community under stress does
  not need a public punishment button; reports + moderation handle bad
  content, and accepted answers already mark quality on doubts.
- One vote per account per post; no self-votes; blocked-pair votes excluded
  (both already enforced or trivially kept).
- **Votes never mint currency** — they influence ranking and creator-profile
  stats only (standing policy).
- **Vote weight** (anti-brigading): a vote counts **1.0** from an account
  with ≥50 scored attempts, else **0.25**. Weight is computed at read time
  from the voter's attempt count — nothing stored, nothing to migrate, and
  farm accounts would have to actually study to gain influence.

### 4.2 What upvotes earn (decided, owner question 15 November 2026)

Never currency — and that is the design, not an omission. Helpful votes are
the one signal users can manufacture socially (sockpuppet rings, vote
trading); attaching XP or points to them would turn every moderation case
into an economy dispute and quietly break the calibrated ₹100/1500-point
targets in Part I §5.4. Instead, accumulated **lifetime weighted helpful
votes** (the §4.1 weights) buy standing and capability — a trust ladder:

| Lifetime weighted helpful | Tier | Unlocks |
| --- | --- | --- |
| 10 | **Helper** | new-account posting throttle lifted immediately (study posts before 3 days / 50 attempts) |
| 25 | **Regular** | rate limits raised to 10 posts / 60 replies per day; tier flair shown beside the name on posts |
| 50 | **Mentor** | Mentor flair; eligibility for reviewer/editorial invitations — the bridge into the contribution pipeline, which is where helpfulness starts earning real points (Part I §5.1, reviewer-gated) |
| 150 | **Guide** | featured in a weekly "most helpful" strip on the community tab (computed, dated, opt-out honored) |

Alongside the ladder, votes already buy **visibility** (the `W` term in the
ranking below) and **reputation**: profile and creator pages show lifetime
helpful count and accepted-answer count as raw integers.

Rules: tiers are computed at read time from `post_votes` joined against
voter attempt counts — no stored balances, nothing to migrate, nothing to
farm offline. Tiers only rise for display, but every privilege yields to
moderation: an author under `needs_approval` loses ladder privileges until
cleared. Accepted answers remain the strongest per-post signal (they rank
2× a vote and are counted separately on profiles). Thresholds are
owner-tunable constants, versioned like the ranking constants in §4.4.

So the full answer to "what does getting upvotes get you": **reach
(ranking), reputation (public counts and flair), privileges (throttles and
limits lifted), and eventually an invitation to the paid-in-points
contribution work — but never points directly.**

### 4.3 For-you ranking (decided)

Per-request scoring over a bounded recent window (last 14 days, capped at a
few hundred candidate posts — at current volume no stored scores or jobs;
materialize only when measurement says so):

```
hot(post) = (W + 2·A + min(R,5) + 1) / (age_hours + 6)^1.5 × T × Q
```

- `W` — weighted helpful votes (§4.1).
- `A` — 1 if a doubt has an accepted answer, else 0 (an answered doubt is
  more useful to the next reader than an open one).
- `R` — visible reply count, capped at 5 so chat threads can't dominate.
- `(age_hours + 6)^1.5` — HN-style gravity: a post gets roughly a day of
  prominence and is gone from For-you within about a week. The +6 offset
  stops a brand-new post with one vote from leapfrogging everything.
- `T` — topic affinity: ×1.25 when the post's question/tag falls inside the
  viewer's saved-exam scope or one of their weakest practicing topics (from
  `user_topic_mastery`); ×1.0 otherwise. Personalization is a boost, never a
  filter — nothing is hidden by the algorithm.
- `Q` — author damp: ×0.5 while an author is under repeat-flag
  `needs_approval` status; ×1.0 otherwise.

Presentation rules on top of the score: pinned posts first (existing);
at most 2 consecutive posts per author; per 10 items, inject 1 unanswered
doubt ("help someone") and 1 material share, when available. The disclosure
gate applies **before** ranking — the feed never ranks what the viewer may
not see. Tabs other than For-you stay purely chronological, so the ranked
view is always escapable and auditable.

### 4.4 Honesty rules

Raw integer counts only (votes, replies); no trending labels without a dated
reviewed pick (existing Hot-topics rule); empty tabs say so. The algorithm
constants above are versioned in one module so a change is a reviewed diff,
not a silent drift.

## 5. Schema sketch (future migrations, not written)

- `posts.canonical_id` becomes nullable; `kind` CHECK gains
  `'study','material-share'`; nullable `topic_tag`/`material_id` columns;
  existing moderation columns reused as-is.
- `follows(user_id, followed_id, created_at)` PK `(user_id, followed_id)`.
- `vocab_decks`, `vocab_cards` (reviewed-content lifecycle),
  `deck_items`; `review_items` gains `item_type` + nullable
  `vocab_card_id`.
- `desk_goals(room_id, ist_week, metric, target, created_by)`.
- No `reward_ledger` changes anywhere in this document — by design, none of
  these systems touch the economy.

## 6. Rollout and order

1. Desk loop integration + mastery strip (pure reads once v2 phase 1
   lands).
2. Vocabulary decks + scheduler unification (depends on `review_items`).
3. Feed: study posts + following + guards (chronological only).
4. Ranking algorithm + For-you, after a few weeks of real post volume to
   tune constants against.
5. Desk sessions, review circle, shared goals, calendar.

Open items — **resolved 16 November 2026 under the owner's "decide all
for me"**: the new-account throttle stands at **3 days / 50 attempts**
and the posting limits at **5 posts / 30 replies per day** (both lifted
by the §4.2 Helper/Regular tiers — the ladder is the escape valve, so the
defaults can stay strict). **Mizo gloss goes on curated cards only**:
bank-derived decks keep the printed source text untouched — a gloss is
editorial content, and editorial content lives in the reviewed curated
layer, never inside a canonical question's presentation.

## 7. Posting, content upload and paid content (16 November 2026 addendum)

Owner request: improve user posting, content upload, and the paid-content
story. Decisions below; everything inherits §3's guards, §4's no-currency
rule and the §5.1/Part I review-gated contribution economy unchanged.

### 7.1 Posting improvements (composer v2)

1. **Type-first composer.** One Create entry with three explicit shapes —
   *Doubt on a question* (anchored, from the question card as today),
   *Study note* (free-standing `study` post), *Share a material*
   (reviewed publication card). No blank-textarea ambiguity about what a
   post is.
2. **Duplicate-doubt deflection** — the single highest-value posting
   improvement available: before a doubt submits, show the question's
   existing threads ("3 discussions already — is yours one of these?")
   with one-tap join. Powered by the thread list that already exists on
   the question; no schema. Fewer fragmenting duplicates, less
   moderation, and the asker usually gets an *instant* answer.
3. **Formatting**: a minimal markdown subset (bold, lists, inline code) —
   rendered, never raw HTML. Still text-only, still internal links only
   (§3.1 hard rules stand); an internal question/material link renders as
   its card.
4. **Drafts**: client-side autosave per composer (the Studio autosave
   lesson); no server draft table for posts — a lost study note is cheap,
   a new table is not.
5. **Edits with honesty**: editable with a visible "edited" marker;
   a reply **locks once accepted** as the answer (it is now evidence
   other learners rely on — same immutability instinct as everywhere
   else). Moderation can still hide anything.
6. **Accepted-answer nudge**: a doubt with replies but no acceptance
   prompts its author once, gently ("did one of these solve it?") —
   directly serves the §0.8 48-hour-acceptance health metric. No
   nagging repeats.
7. *Not doing*: @-mentions (notification spam + a moderation surface we
   are not staffing), image uploads (standing rule), post scheduling.

### 7.2 Content upload (creator pipeline v2)

The machinery exists (Content Studio review lifecycle, 0035 award,
`ReviewBodyLimit`, the 0077 PDF library); what is missing is **the
author's view of it**:

1. **My submissions tracker** in the Create hub: every submission with
   its honest state — draft → submitted → in review → published /
   returned — with the reviewer's note on return and resubmission
   continuing the same thread (states read from the existing lifecycle;
   no parallel status store).
2. **Pre-submission checklist**, shown before review ever starts: source
   named and attributable, own-work/copyright declaration, format/size
   within the body limits. Catches the three most common returns at
   zero reviewer cost.
3. **Tier-aware Create hub**: the hub states plainly what the account can
   submit today — everyone: doubts/replies and study posts (within §3.3
   throttles); reviewed-publication authors: materials; **Mentor tier
   (§4.2): invited into bank contributions — the submissions that pay
   points** (Part I §5.1). The ladder becomes visible exactly where
   ambition forms.
4. **Review honesty**: show "typically reviewed in N days" computed from
   the real recent median, never a promised SLA; show queue position,
   not a fake progress bar.
5. *Not doing*: open uploads of arbitrary PDFs/images to the public
   (copyright + moderation surface), auto-publish for any tier, AI
   drafting of community content.

### 7.3 Paid content (decided stance)

**One subscription; capacity is paid, correctness never is.**

1. **No per-item paywalls.** A verified answer, an explanation or a
   community thread is never individually sold — paying buys *more*
   (full archive breadth per §0.9, limits lifted, deep mistakes, desk
   rooms), never *the truth about a question*. This is the browse-first
   thesis (§0.1) applied to money, and it keeps trust intact: a learner
   never discovers mid-study that the answer is behind a toll.
2. **Premium curated series live inside Pro** — e.g. editor-curated mock
   series land as Pro content, not as separate SKUs. One price (₹100/50),
   one entitlement (`account_has_pro()`), zero per-item purchase
   plumbing, refunds and inventory accounting never exist.
3. **No creator payouts, deliberately, for now.** Paying users cash for
   content means KYC, tax, fraud review and payment disputes — a
   different company. Creators are rewarded in the existing currencies:
   reviewed contributions pay points (Part I §5.1), exceptional work can
   earn owner-granted Pro days (`billing_access_grants` — access, never
   cash, bounded and audited), and standing/reach via the §4.2 ladder.
   Revisit payouts only if creator volume becomes a real constraint.
4. **If one-off paid items are ever wanted** (a priced test series
   outside Pro), they are Razorpay one-time payments, a separate design
   with its own doc — explicitly out of scope here, recorded so nobody
   bolts a shop onto the subscription tables.

---

# Part III — Atlas v2

Baseline: 26 hand-authored chapters under `web/src/atlas/data/chapters/`
(history, Indian and world geography, polity, Mizoram), each a static
TypeScript module of Leaflet layers, timeline events and facts, rendered by
a deliberately small shell (`screens/Atlas.tsx` + `atlas/AtlasMap.tsx`).
The Finna port gave it the chapter sidebar and phone selection. Its
weakness follows from its strength: it is a self-contained encyclopedia
that never touches the bank, the taxonomy or the learning loop.

## III.1 Thesis

Per Part 0, the product is old questions. **Atlas v2 turns every map into
an exam lens**: the question "what has MPSC actually asked about this
river/battle/schedule?" should be answerable from the map itself, and a
geography question in the bank should be able to show its map.

## III.2 Features

1. **Asked-from-this-map panel.** Each chapter (and individually taggable
   layers/pins) maps to subject/topic IDs in the approved taxonomy. The
   chapter view gains a panel of real bank questions for those topics —
   ordinary question cards with the full Part 0 contract (provenance
   labels, inline answering, discussion). Chapter→topic bindings are
   editor-curated data, not model inference; chapters whose topics have no
   tagged questions show an honest "none tagged yet", never padding.
2. **The reverse link.** Question cards whose topic is bound to a chapter
   get a small "View on Atlas" affordance that opens the chapter at the
   relevant layer/event view. One binding table serves both directions.
3. **Map drills (no economy).** Tap-the-map exercises generated from
   chapter pin data: "locate the Battle of Plassey", "which river is
   this?". Client-presented, server-recorded as plain activity — they are
   not canonical questions, so exactly like curated vocab cards (Part II
   §2.5) they pay **no points ever**; they can count toward the warm-up
   quest ring. Wrong drill taps enqueue the *bound topic's* real questions
   into the learner's practice suggestions rather than pretending the
   drill itself is scorable.
4. **Bank-question map mode.** Where a verified geography MCQ's topic is
   bound to a chapter, Smart Review and practice can offer it *with the
   map alongside* — same question, same scoring, same discovery rules,
   just better context. No new award type.
5. **Chapters as reviewed data.** Chapters move from bundle-shipped TS to
   database content published through the existing reviewed-content
   pipeline (Content Studio lifecycle): editors add chapters without a
   frontend deploy, the bundle stops growing per chapter, and chapter
   provenance/review history is recorded like any other published
   material. Existing 26 chapters migrate as the seed corpus, attributed
   as current-site content.
6. **Chronicle cross-links.** Chapter timeline events that correspond to
   dated Chronicle entries link both ways (same binding-table pattern,
   `chronicle_entry_id` on an event).
7. **Explored state (display only).** A per-user "explored" marker per
   chapter (viewed its layers, tried its drills) shown on the Atlas index
   — motivation UI. It never feeds `user_topic_mastery`: mastery moves
   only on scored attempts against verified questions, and a map view is
   neither.
8. **Mizoram depth.** District-level layers (boundaries, HQs, rivers,
   peaks) as first-class chapters — the district dimension already exists
   in profiles (0083); a later Daily Five "district geography" day can
   draw on the bound topics. Exam-scope filtering: with a saved exam, the
   Atlas index orders chapters by that exam's syllabus relevance (binding
   table again), with the full list always available.

## III.3 Atlas Studio — the admin authoring system (owner request, 15 November 2026)

A comprehensive manual authoring surface at `/admin/atlas`, built so the
owner can produce a complete chapter **without touching code, JSON or
coordinates by hand**. Design decisions:

1. **One rendering path.** The Studio's preview *is* the learner Atlas
   component rendering the draft — not a lookalike. This is the
   DESIGN-FIDELITY lesson applied: no drift between what the author sees
   and what learners get. Draft chapters render with a visible DRAFT
   watermark.
2. **Chapter editor.** Form fields for the existing chapter shape: title,
   subject, unit, summary, focus text, ordered facts list (plain text rows,
   add/remove/reorder). Nothing new to learn — the fields mirror what the
   26 hand-written chapters already contain.
3. **Layer editor — draw on the map.** The core of "easy manually":
   - **Pins**: click the map to place, drag to move; each pin gets a label
     and optional note. No typed coordinates anywhere (a read-only
     lat/lng display for verification).
   - **Lines** (rivers, routes, ranges): click a vertex sequence, double-
     click to finish; drag vertices to adjust.
   - **Areas** (regions, kingdoms, climate zones): same vertex flow,
     closed; fill + outline styling.
   - Per-layer controls: name, color from the site palette, dash/solid,
     default-on toggle, reorder, duplicate layer (start the next dynasty
     map from the last one), copy a layer from another chapter.
   - **GeoJSON import** per layer as a power path for traced boundaries —
     optional, never required.
   - Undo/redo across all drawing actions; autosaved drafts, so a
     half-finished chapter survives the browser closing.
4. **Event editor (timelines).** An event = caption + a map view + which
   layers are visible. Authoring a view is literally "pan/zoom the preview,
   toggle the layers, press *Capture view*". Events reorder by drag.
5. **Drill authoring.** Each pin has a "drillable" toggle and a tolerance
   radius (shown as a circle while editing); the Studio derives
   locate-this drills from drillable pins automatically. Custom prompts
   ("Which river forms this boundary?") attach to an existing pin/line.
   Nothing here mints points (III.2.3 stands).
6. **Binding editor.** Subject/topic pickers backed by the live approved
   taxonomy registry (search-as-you-type), at chapter and per-layer level.
   Beside each chosen topic the Studio shows the current count of tagged
   live questions — the author sees exactly what the asked-from-this-map
   panel will contain *before* publishing, and an honest "0 questions
   tagged yet" is visible up front, not discovered later.
7. **Lifecycle.** Draft → preview → publish, through the established
   reviewed-content machinery: versioned snapshots, publish creates an
   immutable version with attribution (`owner` under the solo-owner
   workflow), one-click rollback to any prior version, unpublish holds the
   chapter without deleting history. Staff permissions + the existing MFA
   policy gate the Studio; binding curation may later open to Mentor-tier
   invitees (Part II §4.2), chapter authoring stays staff-only.
8. **Validation, not surprises.** On save: required fields, at least one
   layer, coordinates within a sane bounding box for the chapter's region,
   every event referencing existing layers, drill tolerances positive.
   Failures are inline field errors, never a rejected blob.
9. **Seed import.** A one-time converter ingests the 26 existing TS
   chapters as published version 1s, attributed as current-site content —
   the Studio opens pre-populated, and the TS files retire.

## III.4 Data sketch (future migration, not written)

- `atlas_chapters(id, status, current_version_id, subject, unit, ...)` +
  `atlas_chapter_versions(id, chapter_id, body JSONB, authored_by, note,
  created_at)` — the reviewed-content lifecycle; `body` holds layers/
  events/facts/pins/drills in the current TS shape; publish points
  `current_version_id`, rollback repoints it, nothing is deleted.
- `atlas_drafts(chapter_id, user_id, body JSONB, updated_at)` — Studio
  autosave, one live draft per author per chapter.
- `atlas_topic_bindings(chapter_id, layer_id NULL, subject_id, topic_id)` —
  the two-way lens; editor-curated in the Studio.
- `atlas_drill_results(user_id, chapter_id, drill_id, correct, at)` —
  activity only, outside `attempts` (drills are not canonical questions and
  must never pollute attempt-derived stats).
- Explored state derivable from drill results + a viewed marker; no
  dedicated economy columns anywhere.

## III.5 Rollout

1. Binding table + asked-from-this-map panel + reverse link (pure reads;
   ships against the existing static chapters — nothing blocks on the
   Studio).
2. **Atlas Studio + chapters-as-data**: the version/draft tables, the seed
   import of the 26 TS chapters, and the authoring surface (chapter/layer/
   event editors with the single rendering path). From this point new
   chapters need no deploy.
3. Drill authoring + map drills + explored state + quest-ring hookup.
4. Mizoram district chapters + exam-scope ordering + Chronicle links.

Open items — **resolved 16 November 2026 under the owner's "decide all
for me"**: drills **do** appear on Today for learners whose weak topics
are map-bound — as a suggestion row, never a requirement, never counted
against the plan. Bindings are curated by the **owner first**;
Mentor-tier invitees join once Part II §4.2 ships. Both as originally
suggested.

---

# Part IV — Backend architecture (web + mobile)

The complete backend design: what exists (verified in code 15 November
2026), the conventions that bind it, and the exact backend work Parts 0–III
require. The API is FastAPI + psycopg3 (async pool) over PostgreSQL on the
Oracle VM, behind the shared Caddy; the bank workshop is a sibling system
that publishes content *into* this database and is out of scope here except
at its sync boundary.

## IV.1 Topology and runtime

```
Caddy (shared with family.hawayu.in — never rewrite the Caddyfile)
 ├─ study.hawayu.in  → static web build (rsynced by scripts/deploy.sh)
 │                   → /api/* → uvicorn FastAPI at /srv/api
 └─ /papers          → original PDF assets (reserved namespace)
PostgreSQL (same VM)  ←  guarded bank publication (Oracle workshop timers)
```

- One process, one async connection pool opened at startup (`db.py`):
  dict rows, `jit=off` (bank view queries trigger JIT compilation that
  costs more than the reads), request latency dominated by connection
  reuse, not queries, at current scale.
- In-process background workers as lifespan asyncio tasks: assessment
  reassessment queue (`scoring_revisions`), desk retention purge, calendar
  reminders, game lifecycle, account mail. No external queue — correct at
  this scale; the growth path is §IV.7.
- Middleware stack, in order: CORS → `AccountBoundary` (account/session
  resolution rules) → `MobileBoundary` (mobile-token path allowlist) →
  `ReviewBodyLimit` (payload caps) → `InvalidatePublicCatalog` (drops the
  public-catalog cache generation on admin/collection mutations).
- `/api/health` and `/api/scoring-facts` are the liveness/contract probes.

## IV.2 Application architecture

~45 routers (`app/routers/`) over ~55 services (`app/services/`), with
four binding conventions:

1. **Routers are thin, SQL lives close.** Handlers compose `cursor()`
   queries and service calls; schemas (Pydantic) define every response.
2. **Scope is explicit.** `exam_scope.py` (`question_scope`,
   `scope_condition`) threads cohort/exam scoping through every bank read;
   new bank-reading endpoints must take an `ExamScope`, never re-derive it.
3. **Learner data is never cached shared.** `Cache-Control: private,
   no-store` on personal reads; the only shared cache is the process-local
   public-catalog cache (TTL ≤60s, 32 keys, generation-invalidated) — a
   pattern to extend, not bypass (§IV.10).
4. **Awards and scoring happen in SQL functions/triggers**, not handler
   code (`reward_study_attempt()`, award triggers, immutability triggers) —
   so no endpoint shape change can mint currency or rewrite history.

## IV.3 Identity and access

Resolution order in `current_user()`: mobile session → account
`auth_sessions` cookie → server-issued HttpOnly **guest identity** (0056; a
real `users` row, `X-Device-Id` kept only as a compatibility preference).

| Tier | Gets | Gate |
| --- | --- | --- |
| Guest | full browse, device-bound progress/attempts | none (by Part 0 decree) |
| Account (`email IS NOT NULL`) | sync, rewards, streaks, community voice, desks | `require_account()` |
| Pro | deep mistakes, desk-room creation, other conveniences | `account_has_pro()` = paid plan ∪ reward redemptions ∪ admin grants (`billing_access_grants`, live since 0089) |
| Staff/owner | admin surfaces | role + staff MFA policy (with the one recorded exemption) |
| Mobile token (`ism_mobile_*`) | learner-only subset | `MobileBoundary` method/path allowlist, checked before auth |

Auth features in place: password + Google identity (0071), TOTP MFA
(0033), email recovery (0057), same-origin CSRF for cookie sessions
(mobile sessions exempt by `request.state.mobile_session`).

## IV.4 Data domains

Eight domains, 83 migrations; the invariant column is what new code must
never break:

| Domain | Core tables | Binding invariant |
| --- | --- | --- |
| Bank/content | `canonical_questions`, `appearances`, `papers`, `collections`, `question_classifications` | provenance CHECK + `v_scorable`; content arrives only via guarded publication; workflow data never imported from bank JSON |
| Learning | `attempts` (+ assessments/jobs 0032), `mock_sessions` (+frozen snapshots 0031), `practice_study_sessions`, checkpoints, module progress, vocabulary | attempts immutable, store `chosen_text`; corrections re-assess, never rewrite |
| Economy | `reward_ledger`, `reward_profiles`, `reward_question_claims`, catalog/redemptions, `daily_quest_claims` | immutable ledger, unique `event_key`, per-user lock, caps in SQL |
| Community | `posts`, `post_votes`, `discussion_disclosures`, `creator_blocks`, contribution pipeline (0030) | disclosure gate before visibility; moderation flags honored everywhere |
| Games | `game_rooms/members/cups/dailies` | frozen question snapshots, server timing/scoring only |
| Desk | desk rooms/items/messages/focus/invites (0040) | private, six-seat, retention purge, non-economic |
| Accounts/billing | `users`, `auth_sessions`, billing/Razorpay, MFA, avatars | redemptions/grants never touch `plan_*` or Razorpay |
| Admin/ops | audit events, moderation, inbox, exam calendar, pdf library, editorial/workbench | immutable audit history, attributed decisions |

New tables from Parts I–III join their domains: Learning gains
`user_topic_mastery`, `review_items` and `user_focus_subjects` (§12);
Economy gains the points-cap counters (the grants table landed 16 November
in Accounts/billing as `billing_access_grants` + `billing_account_rates`,
0089); Community gains `follows` + post-kind widening; Content gains vocab
decks/cards and `atlas_*`.

## IV.5 The integrity layer (cross-cutting)

The backend's real product is trust; these mechanisms are mandatory for
every new feature: immutability triggers (`review_immutable()` pattern) on
ledgers/history; unique `event_key` idempotency + client Idempotency-Key
headers on side-effectful POSTs; per-user advisory locks around wallet
mutations; optimistic version checks + reason strings + audit events on
admin mutations; provenance/eligibility only via `v_scorable` and
answer-status views; answer-reveal and disclosure gates applied before any
ranking or listing; honest empty states (no invented activity) as an API
property, not just UI.

## IV.6 API conventions

- REST-ish `/api/<domain>/...`; Pydantic response models; cursor or
  offset+`has_more` pagination (limit caps ~50).
- Reads default `private, no-store`; §IV.10 adds a public tier for
  anonymous browse.
- Side-effectful POSTs: Idempotency-Key header (≥16 chars) where retries
  are possible; server-generated receipts returned on replay.
- Rate limiting is per-feature today (desk invites, posts); Part II's
  throttles (5/30 posts, new-account rules) introduce a small shared
  `rate_limits` helper (counter table keyed `user:action:ist_date`) rather
  than N bespoke counters — one audited implementation.
- Errors: FastAPI status + terse human message; never leak other users'
  existence through error shape (established in desk invitations).

## IV.7 Background processing

Today: five in-process asyncio workers (IV.1) + systemd timers on the VM
(bank review/publication, backups). Design rule: **a worker must be
restart-safe and idle-cheap** (poll with backoff, claim rows with
`FOR UPDATE SKIP LOCKED` — the assessment queue already models this).

New work slots into the same pattern: mastery rollup consumes attempt/
assessment events (incremental, plus a nightly reconciler that recomputes
drifted users); review-item promotion is done at answer time (no worker);
due-date queries are index reads. The growth path when a worker starves
the event loop: move that worker to a second uvicorn-less process reading
the same queue tables — no architecture change, just a systemd unit.

## IV.8 Mobile backend

Verified flow: PKCE-style pairing (`/mobile-auth/start` → user-approved
`/authorize` → `/exchange`) issues `ism_mobile_*` bearer tokens;
`MobileBoundary` rejects any request outside its READ/WRITE regex
allowlist *before* auth (invalid token ⇒ 401 on allowed paths, 403 on
blocked — a free liveness probe). Mobile sessions are learner-only by
design: no staff, no billing writes, no `POST /auth/password` (same-origin
+ session-revocation semantics make it wrong for native).

Design for the Expo app's growth:

1. **The allowlist is the contract.** Every feature the app gains = an
   explicit allowlist diff + a companion test
   (`test_mobile_companion.py` pattern). Finnaplan's mobile set, in order:
   review-queue/mastery/today GETs, then attempts + review-session writes
   (practice on the go), then bookmarks/desks reads it already has, then
   community reads; community *writes* stay web-only until moderation
   tooling is proven. Each widening is an owner decision, recorded.
2. **Capability negotiation, not API versioning.** `/mobile/session`
   returns a `capabilities` list derived from the current allowlist; the
   app renders only what the server declares. Old app builds degrade
   gracefully without version-gated endpoints.
3. **Offline: cache, don't sync.** The app caches browse content
   (questions/papers it has seen) read-only; attempts made offline queue
   locally and replay through the normal idempotent answer endpoints
   (client-generated idempotency keys). No server-side CRDT/sync tables —
   the desk personal-plan conflict model stays the web's
   import/export/version-conflict flow.
4. **Push** (later): a `device_tokens` table + a notify worker for streak
   reminders and desk mentions, strictly opt-in, reusing calendar-reminder
   scheduling. No third-party analytics SDKs.

## IV.9 Build map — backend work for Parts 0–III

Each row: migration(s) + service + router(s) + tests. Order follows Part 0
sequencing; every migration rehearsed on a dump clone first.

| # | Work | Schema (0090+) | Code |
| --- | --- | --- | --- |
| 1 | Browse perf tier | indexes for the two slow queries | ETag/`Cache-Control: public` on anonymous bank/paper/exam reads, keyed by exam scope + content version (reuse `InvalidatePublicCatalog` generations); guests only — any cookie/token ⇒ private |
| 2 | Mastery + review | `user_topic_mastery`, `review_items` (+`item_type`), `user_focus_subjects` (§12.1) | `services/mastery.py` (incremental rollup + reconciler), `services/review_queue.py`; routers: `/me/mastery`, `/me/review-queue`, `/review-sessions` (compose via `practice_study_sessions`), `/me/today` (+focus filter, growth recap), `/me/focus-subjects` |
| 3 | Economy v2 | points-cap counters; `RULE_VERSION='learning-v2'` SQL function rewrite (sub-caps, session/game/mock awards, quest rewire) | extend `learning_rewards.py`; catalog rows repriced as data (1500/400); diagnostics extended; §12.2–12.3 board queries (display only, no schema) |
| 4 | ~~Admin grants~~ ✅ shipped 16 Nov 2026 | `billing_access_grants` + `billing_account_rates` (0089) | `account_has_pro()` union live; `/api/billing/admin/account` + `/days` + `/rate` (MFA, audit, idempotent); billing UI reads `granted` status |
| 5 | Community v2 | `posts.canonical_id` nullable, kind CHECK widened, `follows`, `rate_limits` | ranking constants module in `community.py` (For-you window query), throttles, following tab; vote weights computed in SQL at read |
| 6 | Vocabulary v2 | `vocab_decks/cards/deck_items`, review_items typing | curated-card lifecycle via content review; recall/cloze modes in `vocabulary.py` |
| 7 | Atlas v2 + Studio | `atlas_chapters/chapter_versions/drafts/topic_bindings/drill_results` | public chapter reads (cacheable tier); `/admin/atlas` Studio routers (draft autosave, publish/rollback, binding editor with live tagged counts); seed importer for the 26 TS chapters |
| 8 | Desk v4 | `desk_goals` | Today/mastery reads on desk; desk sessions reuse `games.py` party mode |
| 9 | Mobile widening | — | allowlist diffs + capability list + companion tests per feature (IV.8) |

## IV.10 Performance and capacity

Measured baseline: ~5.4k tps on the 77k bank, sub-ms queries behind a warm
pool — the single VM has an order of magnitude of headroom **if** reads
stay indexed and cacheable. The plan: fix the two known slow queries
before growth marketing; replace per-request `attempts` aggregation with
the mastery/progress rollups; three cache tiers — (a) process-local
public-catalog cache (exists), (b) HTTP public tier for anonymous browse
(build map #1; lets Caddy and browsers absorb guest traffic, which Part 0
predicts is most traffic), (c) nothing shared for learner data, ever. Pool
sizing stays settings-driven; watch `pool_max` vs Postgres
`max_connections` when adding the second worker process (IV.7).

## IV.11 Security model

Threats and standing mitigations: forged identity (server-issued HttpOnly
guest cookies, device-id advisory only); currency minting (no client award
path, SQL-function awards, immutable ledger, event keys, per-user locks,
caps); answer leakage into scoring (provenance CHECKs, `v_scorable`,
frozen mock/game snapshots, reveal + disclosure gates); privilege
escalation (role checks + staff MFA + MobileBoundary pre-auth, boundary
regexes tested); CSRF (same-origin checks, mobile exemption scoped to
bearer sessions); payment safety (redemptions/grants never touch Razorpay
or `plan_*`); abuse (idempotency receipts, body limits, per-feature + new
shared rate limits, vote weighting); secrets only in private credential
storage. Backups: paired backup/recovery per the Oracle runbook; a restore
rehearsal belongs in every migration-heavy release.

## IV.12 Operations and release gates

Deploy: build web locally, `scripts/deploy.sh [web|api|all]` rsyncs
artifacts; never build on Oracle; verify **both** study and family sites
after any Caddy/systemd/Postgres touch. Migrations: new numbered files
only, rehearsed on a disposable dump clone, never edited after apply.

Release gate, defined (the test suite alone is explicitly *not* one):
1. isolated-Postgres test suite green (including the reward/boundary
   guards); 2. migration rehearsed on a fresh prod-dump clone with timed
   apply; 3. deployed artifact SHA256s compared; 4. live health + one
   scripted end-to-end check of the changed flow; 5. DEVLOG receipt.
Observability stays minimal and boring: uvicorn/Caddy logs, Postgres
slow-query log at a real threshold, the reward reconciliation
(`/admin/bank/reward-diagnostics`) run after any economy change.

## IV.13 Testing strategy

Per existing pattern: isolated PostgreSQL tests (real role execution, no
production fixtures, no synthetic reviews), one guard test per boundary
promise (mobile allowlist, guest exclusion, provenance exclusion, replay
safety), plus per-feature flow tests. New-code rules: every award path
gets a replay test and a cap test; every ranking/visibility query gets a
blocked-user and a disclosure-gate test; the Studio gets a
publish/rollback/attribution test; capability negotiation gets an
old-client test (unknown capability ⇒ hidden, not crash).

---

# Part V — Implementation guide

Written 16 November 2026. **This is a guide, not a changelog: none of it
is implemented.** It sequences Parts 0–III + §12 into shippable phases
for whoever builds them (human or model), using only conventions that
already exist in this repository. Migration numbers below are the
next-free at time of writing — **take the actual next free number when
you start**, never renumber an applied file.

## V.0 Standing gates (every phase, no exceptions)

1. New numbered migration in `api/migrations/`, rehearsed on a disposable
   production-dump clone with timed apply, never edited after apply.
2. Isolated-PostgreSQL tests (real role execution, no production
   fixtures): every award path gets a **replay test and a cap test**;
   every visibility query gets a blocked-user and disclosure-gate test;
   every boundary promise gets a guard test.
3. Build web locally; deploy with `scripts/deploy.sh [web|api|all]`;
   never build on Oracle; never rewrite the shared Caddyfile; verify
   **both** study.hawayu.in and family.hawayu.in after infra-adjacent
   changes.
4. After any economy change: run `/admin/bank/reward-diagnostics`.
5. DEVLOG receipt before stopping; record limitations honestly.
6. Mobile: each new learner-facing endpoint is an explicit
   `MobileBoundary` allowlist decision + `test_mobile_companion.py`
   extension + capability-list entry (§12.6) — never a side effect.

## V.1 Phase A — Browse perf tier (no learner-visible change)

Build map IV.9 #1. Order: (a) identify/index the two known slow queries
(EXPLAIN on the dump clone, before/after timings recorded); (b) ETag +
`Cache-Control: public` on anonymous bank/paper/exam reads, keyed by exam
scope + content version via the existing `InvalidatePublicCatalog`
generations; any cookie/token ⇒ `private, no-store` unchanged.
**Tests**: a guest-vs-authenticated cache-header guard; invalidation on
admin mutation. **Done when**: timed queries improve on the clone, guest
responses carry correct validators, learner responses never do.

## V.2 Phase B — Mastery + review core (migration ~0090, zero new awards)

The largest phase; everything later leans on it. It deliberately mints
nothing, so thresholds can be tuned on real usage (§10 phase 1).

1. **Schema**: `user_topic_mastery`, `review_items` (+`item_type`),
   `user_focus_subjects` (§6, §12.1), with the partial due-date index.
2. **Services**: `services/mastery.py` — incremental rollup on attempt
   insert + reassessment completion (0032 job pattern) + nightly
   reconciler for drifted users; `services/review_queue.py` — Leitner
   promotion at answer time, box intervals 1/3/7/16/35 IST days.
3. **Seed**: latest-attempt-wrong questions into box 1. **No reward
   backfill of any kind.**
4. **Routers**: `/me/mastery`, `/me/review-queue`, `/review-sessions`
   (server-composed ≤20 due items through `practice_study_sessions`,
   `attempts.context='review'`), `/me/today` (single composed GET —
   §12.5), `/me/focus-subjects` GET/PATCH (≤5, registry-validated).
5. **Web**: Today card on Home (§12.4 order), Smart Review session
   (existing practice player), mastery map (desktop grid / phone
   accordion §12.5), focus bottom-sheet/checklist.
6. **Tests**: rollup vs. ground-truth aggregation on fixtures; promotion/
   demotion; reassessment re-derivation; focus-filter honesty (due count
   never shrinks); guest exclusion.

**Done when**: a learner sees due reviews and mastery move with zero new
ledger rows, and `/api/me/progress` reads rollups instead of scanning
`attempts`.

## V.3 Phase C — Habit (migration ~0091, first new award rows)

Unified streak (§5.3: `reward_profiles` authoritative; guest fallback
labeled "device activity"), quest rewiring (§5.2 — new quest keys as
data, old claims historical), review-session award (20 XP + 2 pts, §5.1
row 2, with the ≥3s/item latency heuristic). **Tests**: replay + cap +
streak-qualification matrix. **Done when**: both streak surfaces agree
and a completed Smart Review pays exactly once.

## V.4 Phase D — Economy v2 (migration ~0092, the owner-gated one)

`RULE_VERSION='learning-v2'` SQL function rewrite: per-pillar sub-caps
(§5.1 table), 25-pt daily cap counters, game/mock awards, mastery
milestones, contribution amounts; catalog repriced as data (pro-month
1500 / pro-week 400). **The enablement gate is §11 resolution 4** (diagnostics
pass + paid checkout live) — build everything dark, flip the catalog last. **Tests**:
one test per sub-cap, cap-interaction (XP continues after points cap),
milestone once-ever, contribution exemption. **Done when**:
reward-diagnostics reconciles a seeded week of mixed activity to the
rupee math in §5.4.

## V.5 Phase E — Boards, recap, calendar (one small migration)

Leaderboard neighborhood view (§12.2), per-mode weekly game boards
(§12.3) over existing server-owned results, Monday growth recap (§12.1)
— all display-only, reusing the existing opt-in flag. Plus the Helper
Calendar's owned layers (§14): `calendar_entries` +
`calendar_feed_tokens` (the phase's one migration), personal-entry CRUD,
progress-test slots, ICS feed. Plus profile edit (handle rename rule,
bio) and the cosmetics points shop (§12.8 — needs V.4's economy settled;
zero new tables, ledger spend + existing `user_avatar_items`). (The forecast/official/habit layers ship
earlier, free, with V.2 — they are pure reads.) **Tests**: opt-out
invisibility, IST week boundaries, empty-board honesty; calendar: feed
token revocation kills the URL, feed contains only the owner's layers,
missed progress test reschedules without side effects.

## V.6 Mobile app widening (interleaved, per §12.6)

After V.2: the reads (step 1). After V.3: review-session + answer writes
and focus PATCH (steps 2–3). Community reads after Part II ships;
community writes stay web-only. Each step is its own allowlist diff +
companion test + capability entry — one PR-sized decision at a time.

## V.7 New exam onboarding checklist (§0.10 operational)

Data work, not architecture work; no migration unless the registry needs
new approved topics:

1. Create exam body / exam / collection rows; configure `exam_scope`.
2. Map the syllabus onto the shared registry (new topics only through
   the tagging policy's approval path). **The second exam body is the
   trigger to build `exam_syllabus` + the `is_primary` saved-exam flag
   (§0.11.1) and wire the lens cascade (§0.11.2) — module/deck
   applicability labels, feed exam chips, scoped defaults. Until then
   MPSC's existing scope machinery is the lens and nothing needs
   building.**
3. Ingest papers through the Oracle parse → review → guarded-publication
   pipeline (source PDFs archived per `SOURCE-PDF-ARCHIVE.md`).
4. Verify in the browser: provenance labels honest, paper order
   preserved, scope filtering correct, scoring restricted to the new
   exam's own verified pool.
5. Enable discovery surfaces (exam catalog entry, saved-exam option)
   last. No seeded activity, no invented counts.

## V.8 Never, during any phase

No historical/bulk award backfill; no client-callable award endpoint; no
shared caching of learner data; no `ORDER BY random()`; no editing
applied migrations; rewards never touch Razorpay/`users.plan_*`; no
synthetic reviews or invented activity in tests or demos; AI-drafted
current-affairs MCQs never reach learners unreviewed; and when a phase's
diff grows past review size, split the phase — don't push through.

## V.9 Phase F — Consolidation retrofit (§0.12, mostly deletions)

The cheapest phase and the one users feel most: `/revise` assembled from
the existing mistakes screen + Smart Review + vocab due + export button;
the Desk stripped to its toolbox (Today copy, mastery strip and
self-reported target removed); `/important-days` redirecting into
Chronicle; the Play hub grid replacing scattered game entries; the
quick-switcher-as-only-global-search and Inbox-as-only-bell rules
enforced by removing, not adding. **Tests**: old routes redirect, nothing
404s, no orphaned nav entries. **Done when**: every §0.12 table row's
"retired" column is actually gone from the UI.

## V.10 Phase G — Community & content v2 (Part II)

Part II's own rollout order (§6) plus §7: study posts + following +
guards, then ranking after real volume; composer v2 with
duplicate-doubt deflection; the submissions tracker and tier-aware
Create hub; vocabulary decks + scheduler unification. Community writes
stay web-only (IV.8). **Tests**: §IV.13's blocked-user/disclosure pair on
every new query; throttle and tier-lift tests; dedup-deflection renders
existing threads.

## V.11 Phase H — Growth & pricing (§13 + §5.5 extension)

In approved order: email provider first (it gates #4 and referral
notifications); WhatsApp share cards; onboarding diagnostic; due-review
digest; referral Pro-days (7/7, 10-attempt gate, ≤5/year, post-launch
only); exam-day taper; the bulk-₹50 email allowlist + group claim codes
(100 uses / 30 days defaults). **Tests**: referral replay/cap/gate
matrix; allowlist applies at signup exactly once; revoked code stops
redeeming; taper never hides due reviews.

## V.12 Phase I — Admin & maintenance (Part VI)

Build Part VI's consoles in its §VI.5 order. Exception that moves
earlier: `worker_heartbeats` ships **inside V.2's migration** (the first
phase that adds a worker — the mastery reconciler should be born
observable), and the feature-gates panel ships with V.4 (the catalog
flip needs its checklist before anyone can flip anything).

## V.13 The final build order (everything above, one table)

| # | Phase | Delivers | Gate to next |
| --- | --- | --- | --- |
| 1 | V.1 perf | fast anonymous browse | timings recorded |
| 2 | V.2 core | mastery, `/revise`, Today, focus, calendar read-layers, heartbeats | rollups match ground truth |
| 3 | V.3 habit | one streak, rewired quests, first new awards | replay/cap tests green |
| 4 | V.4 economy | sub-caps, 25-pt cap, milestones, repricing, gates panel | diagnostics reconcile a seeded week |
| 5 | V.5 boards | leaderboards, recap, calendar owned-layers + ICS | opt-out/empty-state tests |
| 6 | V.9 consolidation | §0.12 map made real (mostly deletions) | zero dead routes |
| 7 | V.10 community | posts/votes/composer/uploads, vocab decks | moderation holds at real volume |
| 8 | V.11 growth | email, share cards, referral, digest, bulk ₹50 | each gated on its dependency |
| 9 | V.12 admin/maint | Part VI consoles, retention workers, checklists | ops page green for a full week |
| 10 | Parts II–III remainder | desk v4, Atlas v2 + Studio | their own rollout sections |

*(Amended 22 November 2026, §VII.15: three phases are inserted —
**V.14 surface & type** at position 2 (no migration, it is the owner's
stated problem), **V.16 bank quality & console** after V.2, and
**V.15 guides** after V.3. Prerendering moves to the front of V.11.
The amended table is at §VII.15.)*

Mobile widening (V.6) interleaves after rows 2, 3 and 7; a new exam body
(V.7) can onboard any time after row 2 — it is data work. Catalog-live
(§11 resolution 4) sits between rows 4 and 5 at the earliest, and only
with paid checkout launched.

---

# Part VI — Admin console & maintenance system

Added 16 November 2026 at the owner's request: "optimize the admin — a
robust production-level [console] and a maintenance system." Design only.
The admin already has real surfaces (the redesigned `/admin/bank`
workbench with overview/review/pipeline/audit, Rewards & accounts with
the 0089 pricing/grants panel, moderation, publishing, stats); this part
gives them a spine. The §0.12 discipline applies to admins too: **one
place per operational job.**

## VI.1 Principles (all existing patterns, now binding for every console)

1. Every mutation: optimistic version check + audit event + actor
   binding; staff MFA policy (with the one recorded exemption); reasons
   where the schema has them, factual change summaries where it doesn't
   (the solo-owner workflow rule).
2. Every list a console shows is a real query with an honest empty/error
   state — an outage must render as an outage, never as "nothing here."
3. Consoles read through the same API as everything else — no SQL-only
   admin features, or the audit trail develops holes.
4. Display-only by default; a button that changes production state names
   its consequence on the button, not in a tooltip.

## VI.2 The ops dashboard (`/admin/ops`) — the production-level piece

One read-only page answering "is the site healthy?" without SSH:

- **Workers**: `worker_heartbeats(worker PK, last_beat, last_ok, note)` —
  every in-process asyncio worker (assessment queue, desk purge,
  calendar reminders, game lifecycle, mail, mastery reconciler) beats on
  each cycle; the page shows staleness in color. Restart-safe, one tiny
  table, no external monitoring stack.
- **Timers**: the systemd jobs (bank review/publication, backups, stats
  checks) can't be read by the API directly — a collector step appended
  to each timer's unit writes its outcome row to the same heartbeats
  table. One pattern for both kinds of background work.
- **Probes**: `/api/health`, DB pool occupancy vs `pool_max`, webhook
  receipts in the last 24h (once checkout is live), last backup success
  timestamp, disk headroom (collector-written).
- **Economy watch**: yesterday's mint/redemption totals, cap-hit count,
  and two human-judgment flags — accounts at the daily cap ≥7 days
  running, new-account earning velocity outliers. Display only; a human
  decides, the reward-diagnostics page investigates.
- **Moderation pulse**: open reports count + median age (feeds the §0.8
  48h health metric).

No alerting infrastructure: the page is the alert, checked with the
morning tea. If the site ever earns real on-call, that is a later,
separate decision.

## VI.3 The maintenance system

1. **Retention workers** (each boring, heartbeat-registered, V.0-tested):
   the existing desk purge; expired `auth_sessions` sweep; old
   idempotency receipts; **guest users with zero attempts and 12 months
   of silence** (guests with progress are kept — adoption is a promise,
   §IV.3). Every sweep logs counts to its heartbeat note.
2. **Backup discipline**: the paired backup/recovery already in the
   Oracle runbook, plus a **monthly restore rehearsal** on a disposable
   clone, receipted in DEVLOG. The ops page shows days-since-last-
   rehearsal — a number that embarrasses at 40.
3. **Site notice, not maintenance mode**: an owner-set banner
   ("maintenance tonight 02:00 IST") stored like other admin settings,
   rendered site-wide. Honest comms instead of a write-freeze kill
   switch — deploys here are rsync + restart and don't need one; a 503
   switch is more likely to be left on by accident than to save a
   migration.
4. **The monthly checklist** (a doc section, run by a human, receipted
   in DEVLOG): restore rehearsal · dependency/CVE pass · Caddy cert +
   **both sites** check · slow-query log review · economy diagnostics ·
   moderation backlog · disk/log rotation glance · heartbeats all green.
5. **Runbook links everywhere**: every ops-page row links to its runbook
   section (the Oracle workbench runbook stays the operational truth;
   the ops page is its dashboard, not its replacement — §0.12 for ops).

## VI.4 The user viewer (`/admin/users`) — owner request, 16 Nov 2026

One read-only aggregation page per account, found by email or handle
search. The 0089 panel's account lookup is its seed; this is the full
picture, in sections:

1. **Account**: email, handle, created, roles, MFA state, active
   sessions count, last real activity (from auth events / attempts —
   never `last_login` alone).
2. **Access**: plan state, per-account rate (₹100/50), active grants,
   redemptions, trial — the same `account_has_pro()` truth billing shows
   the user, plus provider subscription reference when one exists.
3. **Study**: attempts total, verified-correct count, streak, mastery
   tier counts, saved/primary exam — aggregates only, never the
   learner's individual answer history page-by-page (staff curiosity is
   not a product feature).
4. **Economy**: wallet balance, last 20 ledger rows, days at the daily
   cap in the last 30 (the VI.2 anomaly flags, per-account).
5. **Community**: posts/replies counts, helpful received, ladder tier,
   open reports against, `needs_approval` state, blocks given/received
   **as counts only**.
6. **Actions are links, not buttons** (§0.12 for admin): rate and
   extra-days changes link to the Rewards & accounts panel; moderation
   state links to the moderation queue; nothing mutates from the viewer
   itself, so the audit trail stays where the tools are.

Guards: staff + MFA policy; the viewer never renders password hashes,
session tokens, raw device identifiers, or another user's private desk
content. It exists so "what is going on with this account" takes one
search instead of six consoles — and nothing more.

## VI.5 Build order and schema

1. `worker_heartbeats` + worker beats (ships early, inside V.2).
2. `/admin/ops` page reading heartbeats + probes; timer collectors.
3. Feature-gates panel (with V.4): catalog-live and checkout-enabled
   flips shown with their §11-resolution-4 checklist; the flip button
   stays disabled until its conditions read green — guard rails in the
   UI, decision still the owner's.
4. The user viewer (VI.4) — pure reads over existing tables.
5. Retention workers + site notice + monthly checklist doc.

Schema total: one table (`worker_heartbeats`), one settings row (site
notice). Everything else is reads — which is the Part VI test of
honesty: a maintenance system that needs ten tables is monitoring
itself, not the site.

## VI.6 The authoring console (owner request, 22 November 2026)

Part VI specified an ops dashboard, a maintenance system and a read-only
user viewer — and said nothing about the job admins actually spend their
hours on: tagging and correcting questions. That gap is filled in
**§VII.11**, which specifies the keyboard-first editor, the prefetching
queue, the repeat-last-tag and search-as-you-type interactions, and the
two bulk endpoints (`explanations/apply`, `contexts/apply`) that make
tagging's `/retag/apply` pattern symmetric. No existing guard is removed.

---

# Part VII — Simplification, guides and the authoring console

Written 22 November 2026 from owner direction. **Status: proposal,
nothing implemented.** This part does three jobs: it finishes the
consolidation §0.12 started and §V.9 never reached, it adds the two
content systems the document never had (reading guides, question
currency), and it specifies the admin authoring speed that Part VI left
blank.

It amends rather than replaces. Where a decision here contradicts an
earlier one, the earlier section is named and the reason given — §0.2's
provenance stance (§VII.6) and §13.1's saturation declaration (§VII.0)
are the two real collisions.

## VII.0 What this part amends, and why it exists at all

§13.1 closed with **"Declared saturated."** — nothing further until
measured §0.8 numbers arrive. That was the right rule for *inventing
features*. This part invents almost none. It is a subtraction document:
the owner, reading the built site, found it confusing, and the fix is
fewer surfaces, one font system, one practice flow, one index.
Subtraction does not need usage data to justify itself the way addition
does — a route that nobody can find is already failing without a metric
to prove it.

Three things here are genuinely new rather than subtractive, and each is
named as such: the **Guides library** (§VII.5), **question currency**
(§VII.7) and **explanation voice** (§VII.8). Each exists because content
the product already owns is currently unreachable, unlabelled or
unreadable — not because a feature idea arrived.

The owner's words, 22 November 2026:

> "users usually like to browse and make test too many things will
> confuse most users a straightforward"

That sentence is the whole part. Browse and make a test. Everything that
is not those two verbs earns its place or goes.

**Sections superseded or amended by this part:**

| Earlier section | What changes |
| --- | --- |
| §0.2 browse experience | Gains a fourth entry geometry: by guide (§VII.5) |
| §0.12 consolidation map | Gains 5 rows: practice/mock, guides, index, question editing, written questions (§VII.4, §VII.5, §VII.3, §VII.11, §VII.9) |
| §4.4 "Mocks unchanged in v2" | Reversed — mock and practice merge (§VII.4) |
| §12.5 phone optimization | Extended from geometry to typography (§VII.2) |
| §13.1 "Declared saturated" | Narrowed to additions; subtraction stays open |
| §V.13 build order | Gains phases V.14–V.16 (§VII.15) |
| Part VI | Gains VI.6, the authoring console (§VII.11) |

---

## VII.1 The layout standard — one column, no chrome, borrowed from Prelims

The owner named the reference: *"refer india-study-map mpsc prelims
module"*. That module is
`india-study-map/src/modules/mpsc-combined/combined-prelims.css` — **89
lines of flat CSS**, no preprocessor, no nesting, one class per line. It
is worth stating exactly what makes it the standard, because the
qualities are all absences:

1. **It declares no `font-family` anywhere.** Every control is
   `font: inherit`. The module inherits the shell and cannot drift from
   it. Finna's screens do the opposite — `finna.css`, `exam-paper.css`,
   `exam-experience.css`, `legacy-udc-ldc.css` and `atlas.css` each name
   their own stack, and three of those stacks (Newsreader, Public Sans,
   and IBM Plex Mono after `finna.css:136` disables it) **are never
   loaded at all**, so they silently fall back to Georgia and system-ui.
2. **Three chrome elements before content** — one hero, one row of four
   plain text buttons, the pane. No sidebar, no sticky nav (only the
   mock bar, and only while a timed paper is running), no icons, no
   emoji, no accordions, no toasts, no scroll-to-top button, no
   transitions or animations of any kind.
3. **Hairlines, not shadows.** One `1px var(--cp-line)` border
   everywhere; exactly one box-shadow in the file.
4. **A real spacing scale** — gaps at 8/12/14/18/22, radii at 9/12/13/14,
   and it holds. Two media queries total, at 760px and 480px.
5. **It owns no colour that the shell owns** — `var(--bg-app)`,
   `var(--bg-panel)`, `var(--text-primary)`, `var(--border)` with light
   fallbacks, so dark mode costs the module nothing.

This becomes binding for every Finna screen, as **the layout contract**:

- **No screen declares a font-family.** Only the shell does (§VII.2).
  Screens use `font: inherit` on controls. A screen that needs different
  type asks for a *role* token, never a family name.
- **Maximum two chrome rows above content** — the page header and, if
  the screen genuinely has modes, one row of tabs. No screen gets a
  sidebar except `/admin`.
- **One content column.** `max-width: 1160px` for grids, `850px` for
  anything being read. The question card's current two-column
  question-plus-provenance-aside split (`cp-question-body`
  `minmax(0,1fr) 190px`) is the only sanctioned exception, and §VII.6
  shrinks even that.
- **No decorative motion.** Transitions are permitted on `:focus-visible`
  and nowhere else.
- **Hairlines over shadows**, one elevation level, full stop.
- **Delete the four orphan stylesheets' font declarations** rather than
  loading the fonts they ask for. They have been invisible since the
  `data-design="finna"` override shipped; loading Newsreader and Public
  Sans now would be shipping a visual change disguised as a bug fix.

**Done when**: `grep -c font-family web/src/styles/*.css web/src/**/*.css`
returns a non-zero count only in the shell file, and no screen file
contains `box-shadow` with a blur over 10px.

---

## VII.2 Typography — the system the document never had

A sweep of Parts 0–VI finds **one** mention of typography (line 2482,
about preserving printed-paper appearance) and **no type scale, no font
stack, no typographic system at all**. Meanwhile the built site has:

- `Figtree` 400–900 plus `IBM Plex Mono` 400/500 loaded from Google
  Fonts as a **render-blocking stylesheet on every page**
  (`web/index.html:7-12`), with no `@font-face` and nothing self-hosted;
- `font-display` and `font-sans` set to the identical stack in
  `tailwind.config.js:47-52`, so `font-display` carries no meaning;
- `finna.css:136` neutralising `.font-mono` everywhere except `<pre>`
  and `<code>`, so the mono family is paid for and not used;
- a **14px base** with `line-height 1.45` (`finna.css:132`) — a
  marketing-page size for a product people read for three hours;
- **at least 21 distinct arbitrary sizes** hard-coded as Tailwind
  escape-hatch values (`text-[36px]`, `text-[46px]`, `text-[9.5px]`, …),
  with Tailwind's own `text-sm/base/lg/xl` scale essentially unused;
- `h1` at weight **900** with `-0.03em` tracking — the voice of a
  landing page, applied to a question bank.

### VII.2.1 Three roles, never more

| Role | Used for | Requirement |
| --- | --- | --- |
| **UI / text** | everything — nav, cards, question stems, options, guide body | one variable sans, self-hosted, 400–700 only |
| **Reading** | guide prose (§VII.5), long explanations, essay prompts | one variable serif, self-hosted, 400/600 + italic |
| **Numeric / code** | question numbers, timers, scores, IDs, `<pre>` | one mono, restored to actual use, tabular numerals |

Weights 800 and 900 are **deleted from the build**. Nothing in a study
product needs black. This alone removes two font files from the payload.

### VII.2.2 Self-host, preload, stop blocking

Replace the Google Fonts `<link>` with self-hosted `woff2` variable
fonts in `web/public/fonts/`, `font-display: swap`, a single
`<link rel="preload">` for the UI face only. The serif and mono load
lazily — a guide page can afford 80ms of fallback serif; the whole site
cannot afford a render-blocking third-party request on every cold load,
least of all on the phone connections this audience actually uses.

This also removes a privacy footprint the policy pages do not currently
declare: every page view is presently an un-consented request to
`fonts.gstatic.com`. §VII.2 is therefore a small but real item on the
privacy inventory, not only a design change.

### VII.2.3 The scale — eight steps, and they are the only ones

```
--t-xs    12px / 1.4    labels, metadata, source lines
--t-sm    14px / 1.5    secondary text, card meta, nav
--t-base  16px / 1.6    body, question stems, options   ← new base
--t-md    18px / 1.65   guide body (reading role)
--t-lg    21px / 1.35   card titles, section heads
--t-xl    26px / 1.25   page titles
--t-2xl   32px / 1.15   hero titles only
--t-3xl   40px / 1.1    the index page and nothing else
```

Base moves **14px → 16px**. Tracking: `-0.01em` at `--t-xl` and above,
`0` everywhere else. Guide body uses the reading role at `--t-md` with a
**66ch measure** — the codex module already proved that measure works
for this content.

An arbitrary `text-[Npx]` value in a component becomes a review failure.
The eight steps go into `tailwind.config.js` as the *whole* `fontSize`
map, which makes the escape hatch visible in diffs.

### VII.2.4 Phone

§12.5 fixed phone *geometry* (390/320px rules, single column, tap
targets) and left type alone. Extend it: the scale above is the phone
scale too, with only `--t-2xl` and `--t-3xl` clamping down. A study
product must stay legible at arm's length on a bus, which is where most
of this reading will happen.

**Tests**: computed `font-size` on the body is 16px; no element in a
rendered page tree uses a size outside the eight tokens; Lighthouse
reports zero render-blocking font requests.

**Done when**: `web/index.html` contains no `fonts.googleapis.com`, and
`tailwind.config.js` `fontSize` has exactly eight keys.

---

## VII.3 The index — one page that admits everything the site has

The owner asked for "a proper index too". The site currently has **five
separately maintained hard-coded link arrays** —
`Header.tsx:15` (primary nav), `Header.tsx:16` (four mega-menus,
~33 links), `navigation.ts:2` (phone tabs), `More.tsx:8` (~16 links),
`Library.tsx:7` and `:17` (two more tool lists) — plus
`quickAccess.ts:36` (a seventh curated list for ⌘K). Seven navigation
surfaces, hand-synced. `/revise`, `/desk`, `/games`, `/atlas`,
`/chronicle`, `/stats`, `/tests` and `/create` each appear in four to six
of them. This is precisely the "same thing in different places" §0.12
was written to stop, and it survived because §0.12 produced a map
without producing a **source**.

### VII.3.1 One manifest, generated navigation

A single `web/src/lib/siteMap.ts` exports every destination once:

```ts
type Destination = {
  id: string
  path: string
  label: string              // the only label; no per-surface renames
  section: 'study' | 'practice' | 'guides' | 'community' | 'you' | 'admin'
  blurb: string              // one line, shown on the index and in ⌘K
  surfaces: ('nav' | 'tabs' | 'index' | 'quickfind')[]
  minRole?: Role
}
```

Every navigation surface renders *from this array* and from nothing
else. The desktop nav takes `surfaces.includes('nav')`, the phone tab bar
takes `'tabs'`, ⌘K takes everything the user may see. The current
desktop/phone label mismatch — `/library` is "Subjects" on desktop and
"Library" on the phone — becomes structurally impossible.

This is the same discipline `india-study-map/src/modules/registry.ts`
already uses for its 43 modules, and it is the reason that site can list
everything it owns while Finna cannot.

### VII.3.2 `/index` — the honest contents page

One route, no auth, prerendered. Sections in fixed order — Study,
Practice, Guides, Community, You — each a plain list of label + one-line
blurb, generated from the manifest. No icons, no cards, no counts that
are not real.

It serves four jobs at once: the "proper index" the owner asked for, the
destination for the footer, the SEO entry §13.1 #9 called the highest-
leverage growth work in the document, and the place a new user is sent
after onboarding instead of being dropped on a feed.

### VII.3.3 Mega-menus are deleted

Four three-column mega-menus holding ~33 links are a desktop pattern for
a catalogue site with a hundred products. Finna has six. The desktop nav
becomes **six plain links**, matching §VII.4's consolidation:

**Exams · Papers · Practice · Guides · Community · Index**

The quick rail (Revise, Desk, Play, Atlas, Chronicle, "My exam") is
deleted from the header; those destinations live on Home, on `/index`
and in ⌘K. The phone tab bar stays at five and keeps its §12.5 freeze —
but **Library becomes Guides** (§VII.5), since that tab's current job,
holding eighteen unrelated destinations under one word, is the
confusion the owner is describing.

**Done when**: `Header.tsx`, `BottomBar.tsx`, `More.tsx`, `Library.tsx`
and `quickAccess.ts` contain **zero** hard-coded paths, and `/more` is
deleted — its content is `/index`.

---

## VII.4 Practice and mock become one surface

The owner: *"simplicy practice and mock...only one"*. This reverses
§4.4's "Mocks unchanged in v2".

### VII.4.1 What exists now

**Practice is not a page.** It is a query parameter — `/bank?pool=practice`
is what the header's "Practice" link points at, `/exams/:id?view=practice`
is the exam-scoped copy, `/practice-sets` is a 25-line catalog screen,
and `DeskPractice.tsx` is a fourth copy inside the Desk.

**Mock is a different flow entirely** — `/tests`, `/tests/make`,
`/tests/:id`, `/tests/:id/take`, `/exams/:id/mock`, `/results/:id`,
`/scoring`. Seven routes.

They share exactly one component (`MockRunner.tsx`, which branches on
`useParams()` at line 30) and nothing else: separate discovery, separate
entry points, separate state, separate paywall rows in §0.9.2.

Eleven routes and four code paths for what the learner experiences as one
question: *do I want a timer on this?*

### VII.4.2 One route, one toggle

**`/practice`**, with a setup step that is three controls and a button:

```
What        [ My exam ▾ ]  [ Subject ▾ ]  [ Paper ▾ ]  [ search… ]
How many    [ 10 ] [ 25 ] [ 50 ] [ full paper ]
Timer       ( ) Off — check each answer as I go
            ( ) On  — score at the end          [ 60 min ]

                                   [ Start ]
```

Timer off is today's practice: untimed, immediate reveal, no scoring.
Timer on is today's mock: server-held elapsed time, answers at the end,
a score. **Same picker, same question card, same runner, same results
page** — the results page simply omits the score block when the timer
was off.

Retired into it: `/bank?pool=practice`, `/exams/:id?view=practice`,
`/practice-sets`, `/exams/:id/mock`, `/tests/:testId/take`, `/mistakes`
(already a redirect), and `DeskPractice`'s separate **solo** session store.
The personal Desk keeps a *link* to `/practice` for solo runs (per §0.12's
rule that the personal Desk holds your things rather than duplicating Home),
while group Desk rooms keep their synchronized room practice sessions
(`0113_desk_practice_sessions.sql`, reusing party-mode room snapshots).

`/scoring` stops being a route and becomes a disclosure inside the
results page, where the question "how was this scored?" is actually
asked.

### VII.4.3 What this does not change

- **Scoring eligibility is unchanged.** A timed run still scores only
  from the verified pool; an untimed run still shows every question.
  The toggle changes presentation, not provenance (§VII.6).
- **Mock snapshots stay immutable** (`mock_sessions` + frozen snapshots,
  migration 0031). A timed run freezes; an untimed one does not.
- **The paywall rows merge (confirmed 22 November 2026).** §0.9.2's separate
  "50 practice answers/day" and "1 mock/month" become one free allowance —
  *one timed run a month, 50 answers a day untimed*. The copy gets shorter,
  which was the point.

**Done when**: `grep -r "pool=practice" web/src` is empty and the route
table has one practice entry.

---

## VII.5 Guides — the reading library (new)

The owner asked where to put "content study materials from
india-study-map website modules like english polity codex etc and quick
revesion etc a place where users can read guides a guide section
comprehensive".

The document has no such concept. "Guide" appears once in Parts 0–VI, as
a community ladder tier name (line 4120). Materials exist (§II.7.2) but
they are a **user-generated CMS** — `screens/Materials.tsx` is 32 lines,
headed "Community library". There is exactly one first-party guide in
the entire product: `EXAM_GUIDES = [MES_GUIDE]`, a one-item catalogue
powering the single route `/exams/mes`.

Meanwhile `india-study-map/public/` holds **29 standalone HTML study
artifacts, ~43 MB of real authored content** — the Polity Codex (132 KB:
21 topics, 21 note sections, 130 MCQs, 92 flashcards, with every MCQ
explanation cross-linked back into the notes), Quick Revision, Tenses &
Voice, the Answer-Writing Companion, the Comfort Trap, the JSO science
and maths guides, three subject labs, and the pipeline guide. Thirteen
thousand questions sit inside them in bespoke per-module shapes.

That content is finished, it is good, and today it is invisible to every
Finna user. This is the largest unforced loss in the product.

### VII.5.1 The decision — guides are first-party content, separate from materials

Two content systems, and they must not merge:

| | **Guides** (new) | **Materials** (§II.7.2, exists) |
| --- | --- | --- |
| Author | the site | users |
| Review | editorial, before publish | moderation, after publish |
| Shape | chaptered, versioned, indexed | single documents |
| Route | `/guides`, `/guides/:slug` | `/materials`, `/materials/:id` |
| Paywall | free to read; §0.9.2 untouched | unchanged |
| Promise | "this is correct and current" | "a user wrote this" |

Collapsing them would put the site's name behind user text, which §II.7
deliberately avoids. Keep both, label both clearly, and let the Guides
index link *out* to good materials on the same topic.

### VII.5.2 Structure — one shape for all of them

Every guide is a **chaptered document with an optional attached question
set**, stored in Postgres, not as embedded HTML:

```
guide            slug, title, subject_id, topic_id, exam_scope[],
                 summary, reading_minutes, status, version,
                 updated_at, review_due
guide_chapter    guide_id, ord, heading, body_markdown, anchor
guide_question   guide_id, chapter_anchor, question_id   -- bank FK
```

The crucial design note, taken directly from the codex module: its MCQs
carry `rel: ["topic-id"]`, so answering one wrong **jumps you to the
note that explains it**. `guide_question` reproduces that in the right
direction — questions already live in the bank, so a guide chapter
*claims* bank questions rather than carrying copies. That one decision
avoids importing 13,000 questions in bespoke shapes, which the
exploration correctly identified as the real cost of this migration.

### VII.5.3 The reading experience

The codex layout, with the §VII.1 contract applied:

- Sticky chapter index on the left at ≥900px, a `<details>` contents
  block above the body below it. No other chrome.
- Body in the reading role at `--t-md`, 66ch measure (§VII.2.3).
- Tables, callouts and definition lists; no flashcard widget, no tabs,
  no progress ring. **A guide is a document, not an app.** Every one of
  the source modules that grew tabs — `mizo-prelims-study/index.html` at
  8.3 MB with eight tab panes, a toast, a scroll-to-top FAB and its own
  localStorage state — grew them because it had nowhere else to put the
  questions. Finna has the bank.
- One button at the end of each chapter: **"Practice this chapter"** →
  `/practice` pre-filtered to that chapter's `guide_question` set. That
  is the entire integration, and it is the one the owner is describing
  when he says users like to browse and make tests.

### VII.5.4 Migration — three tiers, and an honest admission about the fourth

| Tier | Modules | Treatment |
| --- | --- | --- |
| **1. Prose guides** | Polity Codex notes, Comfort Trap, Answer-Writing Companion, Tenses & Voice prose, JSO science/maths guides, pipeline guide | Convert to `guide_chapter` markdown. Real work, highest value. |
| **2. Question payloads** | Codex 130, Quick Revision, Practice Hub 7,677, JSO 1,325, System Analyst 1,369, System Manager 843, Current Affairs 529, Mizo Prelims 329 | Reconcile against the bank. Most are already there; import only what is not, through the normal contribution path — **never by direct insert**. |
| **3. Reference data** | NCERT history `questions.json`/`chapters.json`, Chronicle timelines, glossaries | Already structured. Straight import. |
| **4. Apps, not guides** | Nihongo Lab (6.4 MB bundle + 39 MB jmdict), Atlas, Calc Lab, `mpsc-diagrams` (73 MB images) | **Out of scope.** These are applications; forcing them into a guide shape would break them. Link out or leave them. |

Two files are reachable on disk but **absent from
`india-study-map/src/modules/registry.ts`** and would be silently lost
in a mechanical migration: `public/pipeline-guide/index.html` (130 KB)
and `public/mpsc-jso-prep/science-study-guide.html` (377 KB). Name them
in the migration checklist explicitly.

Ten root-level `.html` files are **byte-identical duplicates** of files
in `public/` (verified by md5). Migrate from `public/`; delete the root
copies.

### VII.5.5 Scope honesty (confirmed 22 November 2026)

Tier 1 is perhaps 12–15 real guides and weeks of editing. Ship the
**shell plus `/guides/using-finna` (§VII.12.2) and the first three subject
guides** (**Polity Codex**, **Quick Revision**, **Tenses & Voice** — owner-confirmed
22 November 2026 because all three are finished and span three core subjects)
and an index that shows only what exists. An empty Guides tab
promising "more soon" is exactly the dishonest empty state §VI.1 bans.

**Done when**: `/guides` lists `/guides/using-finna` plus the three confirmed
subject guides, each chapter's "Practice this chapter" opens `/practice` with
a non-empty question set, and no guide body is served as raw embedded HTML.

---

## VII.6 Answer provenance — two words for learners, five for staff

The owner: *"offical keys there arent much so best to hide"*.

**The premise needs correcting before the decision is made, because the
numbers point the other way.**

| answer_status | count | share |
| --- | ---: | ---: |
| official (official key + transcribed key) | **13,417** | **16.3 %** |
| verified (derived + reviewed publication) | 57,448 | 69.7 % |
| needs-review | 3,121 | 3.8 % |
| written (non-MCQ) | 8,176 | 9.9 % |
| unsolved | 221 | 0.3 % |

*(Live Oracle readback, `reports/mpsc-answer-review-20261116/README.md:44`;
82,383 canonical rows. Current numbers: `GET /api/scoring-facts`.)*

So official keys are ~16% — matching §0.2's own "~84% without official
keys" — but they are not a rounding error, and **hiding them is not
available**: `v_scorable` (`WHERE status='live' AND answer_source IN
('official','key')`) is what powers mocks, mastery (`services/mastery.py:18`),
reward proofs (migrations 0034, 0093) and game scoring
(`services/game_selection.py:168`). Hide the official pool and scoring,
rewards and the entire economy lose their floor. §0.2 also already
decided the opposite in binding terms: **"Provenance is a display
property, not a visibility filter."**

### VII.6.1 What is actually wrong, and the real fix

The problem the owner is reacting to is not that keys exist. It is that
**the learner is shown a five-word vocabulary** — Official key / Verified
answer / Needs review / No answer yet / Written question — each with a
symbol (`▣ ✓ ? —`), each with a hardcoded hex palette that does not
re-theme in dark mode (`answerStatus.ts:16-21`), and each wrapped in a
`<details>` disclosure. Five states is a staff taxonomy wearing a
learner's clothes. And the one caveat that actually matters —
*"A provisional key may change when the final key is published"* — is
hidden **two layers deep**, inside `AnswerProvenance`'s collapsed panel,
while the always-visible badge says "Official key", which reads as final.

**The fix is to collapse the vocabulary, not the data:**

| Learner sees | Covers | Treatment |
| --- | --- | --- |
| *(nothing)* | official, verified | No badge at all. A trusted answer is just the answer. |
| **Not verified** | needs-review, unsolved, inferred | One amber line under the answer, always visible, never collapsed. |
| **Written question** | descriptive | A line, not a badge (§VII.9). |

- **Trusted answers lose their badge entirely.** 86% of the bank is
  trusted; badging the normal case teaches nothing and makes every page
  noisier. Badge the exception.
- **A provisional key is not a trusted answer.** Today `key_status =
  'provisional'` still renders the green "Official key" badge, with the
  caveat buried. It moves into **Not verified** until the final key
  publishes. This is a correctness fix, not a design preference.
- **The source line keeps everything.** Exam, year, paper, question
  number, key document, `key_status`, dispute notices — all of it,
  always visible, in `--t-xs`, per §0.2 item 3. The *provenance* stays;
  the *badge vocabulary* goes.
- **Staff keep all five states** in `/admin` and in the editorial
  workspace. The filter facets on `/bank` (`official|key|derived|
  inferred|none`) become a staff-only control; learners get one checkbox,
  **"Only questions I can be scored on"**, which maps to `pool=scorable`.
- **The conflict display stays exactly as built** (`AnswerComparison.tsx:57-65`).
  When an official key and a verified answer disagree, that is real
  information and it is already handled honestly.

This satisfies what the owner is asking for — less key chrome on screen —
without deleting the pool the economy stands on. If the owner wants
something stronger than this, it is a §0.2 amendment and needs its own
explicit decision.

**Done when**: `answerStatus.ts` exposes two learner labels; the
hardcoded hex palette is replaced by theme tokens; `key_status =
'provisional'` returns `trusted: false`.

---

### VII.6.2 Key-versus-solution conflicts (owner clarification, 22 November 2026)

The owner's reason for wanting less key chrome, given after the first
draft of this part: **"because some official keys are wrong."**

That is a stronger argument than scarcity, it is correct, and the
product already half-agrees with it. Migration
`0021_informatics_english_sentence_key_disputes` is the precedent — 8
questions in the 2021 Informatics Officer General English Paper-II where
the final key conflicts with the answer derivable from the printed stem.
Its comment is the policy, already written a year before this section:

> Keep the reviewed answers available in practice, but exclude them from
> official-key scoring and expose the discrepancy to learners.

The adjudication discipline is equally settled — see
`reports/assistant-2018-paper2-adjudication.md`: source SHA-256, bank
checksum before and after, every conflict solved independently from the
printed stem, the result recorded explicitly as a **derived-answer
claim, never an official-key claim**, applied by a hash-guarded importer
over a backup. That report also carries the only real number anyone has:
**"the UDC/LDC/Assistant disagreement count is now 210."**

So the question is not what to do with a conflict. It is why so few have
been found.

#### What is already built

| Piece | Where |
| --- | --- |
| `key_disputed` + `dispute_note` | `canonical_questions`, 0002:116 |
| Disputed → `answer_status='needs-review'` | 0050:6, mirrored in `question_readiness.py:12` |
| Disputed → excluded from `v_scorable` | 0002:155 (and the partial index at 0002:150) |
| Answer edits refused while disputed | `services/admin_bank_edits.py:70` |
| **Past scores re-assessed when answer facts change** | 0032, trigger + `scoring_revisions.py:29` → `reason='disputed_key'` |
| Two-lane comparison | `services/answer_comparison.py:59` → `agree \| disagree \| not-compared` |
| Conflict shown to the learner | `AnswerComparison.tsx:57-65` |

The hardest piece — retroactively re-assessing learner scores when a key
turns out to be wrong — exists. Nothing below needs to invent it.

#### The finding: two conflict shapes, and only one of them is safe

`published_comparison()` does not compare columns. There is only one
`answer_text` column; the two lanes are **reconstructed from applied
publication manifests**. That has a consequence nobody has written down:

- **Shape A — the solution won.** `answer_source='derived'`, and an
  official-key publication also exists in history. The derived answer
  sits in the column. These questions are *already* outside `v_scorable`
  (which requires `answer_source IN ('official','key')`), so they never
  score on the disputed value. 0021's eight are this shape. **Safe.**

- **Shape B — the key won, but the site published reasoning against
  it.** `answer_source IN ('official','key')`, `key_disputed = false`,
  **and** an applied publication exists with
  `admin_decision.mode = 'verified'`,
  `admin_decision.preserve_official_key = true` and a
  `solution_answer_text` that differs from `answer_text`. This is the
  mechanism `answer_comparison.py:35-40` calls `separate` — the
  supported way to say *"the key stands in the column, but our reviewed
  working disagrees"* without overwriting the key.

  A Shape B question is in `v_scorable`. It composes into mocks. It
  scores. It feeds mastery, reward proofs and game scoring. **And it
  scores on an answer the site's own reviewed working says is wrong**,
  behind a green "Official key" badge, with the disagreement visible
  only to a learner who taps *"View answer sources."*

Shape B is the actual defect, and it is invisible because
`relation='disagree'` is computed **per question, at read time, when
somebody opens the comparison panel.** No query anywhere asks for the
set. `v_reviewed_answer_publications` cannot find them — it requires
`c.answer_source='derived'` (0032:68), so by construction it only sees
Shape A. The 210 came from a hand-run campaign over a handful of papers.

**We do not know how many Shape B questions exist.** That is the first
thing to fix, and it is a query, not a feature.

#### The adjudication ladder — four outcomes, unchanged from practice

1. **Key right, solution wrong** → correct the solution through the
   normal `kind='answer'` path. The key was never at fault.
2. **Key wrong, solution right** → `key_disputed = true` + `dispute_note`
   in 0021's exact format (`'Q42: official key C; derived answer A.'`),
   solution stays available in practice, question leaves `v_scorable`.
   **The key column is never overwritten** — it is the historical record
   of what the examiner published, and an erratum may still arrive.
3. **Both wrong — the question is defective.** The computed answer is
   absent from the printed options. Hold it, set `source_defect`, and
   follow the rule the 2018 Paper II report already states: *"Do not pick
   the nearest option without a key or erratum."* Q90 and Q101 of that
   paper are the worked precedent.
4. **Undecided.** The disagreement is real, nobody has adjudicated. This
   is where nearly all of them live, and §VII.6.2 exists to give it a
   queue instead of a silence.

#### The learner-facing decision — a third label

§VII.6 collapsed five labels to two on the premise that official keys
were merely scarce. With the owner's actual reason, the collapse is
*more* defensible — "Official key" was never a correctness guarantee, so
rendering it green and final was misleading in both directions — but it
needs a third state, and that third state is the one that matters:

| Learner sees | Covers | Treatment |
| --- | --- | --- |
| *(nothing)* | official or verified, no disagreement | no badge |
| **Not verified** | needs-review, unsolved, provisional key | one amber line, always visible |
| **Answer disputed** | `key_disputed`, **and un-adjudicated Shape B** | one line, always visible, **never inside a disclosure** — names both answers and links the derivation |

The principle: what deserves permanent screen space is not *where an
answer came from* but **that two sources disagree**. Provenance is a
staff concern; disagreement is a learner concern. The existing conflict
aside (`AnswerComparison.tsx:57-65`) is already well written — it moves
out of the collapsed panel and becomes the always-visible treatment.

**Un-adjudicated Shape B is treated as disputed on detection, before a
human looks.** If the key and the reviewed working disagree, the site
does not know the answer, and a green badge is a claim it cannot
support. The cost is a handful of questions leaving the scorable pool;
the alternative is teaching a wrong answer as examiner fact. This is the
conservative direction and §0.2's honesty rules point at it.

---

### VII.6.3 Implementation guide — conflict detection and adjudication

**Phase V.17.** Depends on nothing; can run beside V.14. One migration
(`0137`, after §VII.7/VII.8's `0135` and §VII.5's `0136`).

#### Step 1 — Materialise the conflict set (migration 0137)

A materialised view, refreshed nightly, not a computed column — the
predicate must stay a *mirror* of `published_comparison()`, and a view
makes the drift visible in one place:

```sql
-- 0137_answer_conflicts.sql
-- Mirrors services/answer_comparison.py published_comparison().
-- If that function changes, this view changes in the same commit.
CREATE MATERIALIZED VIEW v_answer_conflicts AS
SELECT c.id                                              AS canonical_id,
       a.paper_id, a.qnum,
       'key-won'::text                                   AS shape,
       c.answer_text                                     AS official_answer,
       p.manifest->'admin_decision'->>'solution_answer_text' AS solution_answer,
       p.id                                              AS solution_publication_id,
       p.finished_at                                     AS detected_from
  FROM canonical_questions c
  JOIN bank_contributions b ON b.canonical_id = c.id
  JOIN bank_publications  p ON p.contribution_id = b.id
  JOIN appearances        a ON a.id = b.appearance_id AND a.is_primary
 WHERE c.status = 'live' AND c.type = 'mcq'
   AND c.answer_source IN ('official','key')
   AND NOT c.key_disputed
   AND b.state = 'published' AND p.state = 'applied'
   AND p.manifest->'admin_decision'->>'mode' = 'verified'
   AND (p.manifest->'admin_decision'->>'preserve_official_key')::boolean
   AND p.manifest->'admin_decision'->>'solution_answer_text'
       IS DISTINCT FROM c.answer_text
   -- source_matches(): a changed stem invalidates the comparison
   AND p.receipt->'after'->>'question' = c.question
   AND p.receipt->'after'->'options'   = c.options;

CREATE UNIQUE INDEX ON v_answer_conflicts (canonical_id, solution_publication_id);
GRANT SELECT ON v_answer_conflicts TO mpsc;
```

Shape A (`answer_source='derived'` with an official-key publication in
history) is a second branch of the same view, `shape = 'solution-won'`,
listed for completeness but **not** auto-demoted — those questions are
already outside `v_scorable` and carry no scoring risk.

**Do not add a `pending_dispute` column.** Exclusion from scoring comes
from the view, by making `v_scorable` subtract it:

```sql
-- v_scorable gains one clause; the partial index at 0002:150 gains none.
AND id NOT IN (SELECT canonical_id FROM v_answer_conflicts
                WHERE shape = 'key-won')
```

This keeps one source of truth and means an adjudicated question
re-enters the pool automatically when the view stops matching it. It
also means **a stale matview silently holds questions out of scoring** —
so the refresh is monitored (step 4), not fire-and-forget.

#### Step 2 — Surface it where the work happens

Three reads, no new permission model:

- `GET /api/admin/bank/conflicts` — the triage queue. Filterable by
  paper, exam, shape; **ordered by learner exposure** (attempt count on
  the canonical id) so the question 400 people answered wrong is
  adjudicated before the one nobody has seen. Paper-grouped by default,
  for the reason in step 5.
- `GET /api/admin/bank/conflicts/{qid}` — both lanes, both derivations,
  the key document page, the attempt count, and the prior publications.
  Everything an adjudicator needs on one screen.
- The existing `POST /api/admin/bank/edits` resolves it. **No new write
  endpoint.** Outcome 1 is `kind='answer'`; outcome 2 sets
  `key_disputed` + `dispute_note`; outcome 3 is the existing hold path.
  Every guard in §VII.11.1 applies unchanged.

In the UI this is a section of the §VII.11 authoring console, sharing
its queue, prefetch and keyboard model. Adjudication is slow thinking
per question, so the console's speed affordances matter less here than
its *evidence density* — but it costs nothing to reuse the shell.

#### Step 3 — The learner change

- `answerStatus.ts` gains the third state from §VII.6.2. Its input grows
  one boolean, `disputed`, already threaded from the API.
- The conflict aside moves out of the `<details>` in
  `AnswerComparison.tsx` and renders inline whenever `relation ===
  'disagree'` or `key_disputed`. Its existing copy is kept — it is
  already honest — with the footer line selected by adjudication state:
  adjudicated → *"The official key is preserved. See the explanation and
  source details."*; un-adjudicated → *"The official key and our
  reviewed working disagree. This question is excluded from scored
  tests while we check it."*
- Replace the hardcoded `#D9B76B / #FFF4D9 / #705015` with theme tokens
  so it survives night mode (§VII.6, same fix).

#### Step 4 — Automation

Seven jobs, in build order. All read-only except where stated; all
in-process asyncio or systemd per §IV.7 — **no queue, no new runtime.**

1. **Nightly refresh.** `REFRESH MATERIALIZED VIEW CONCURRENTLY
   v_answer_conflicts`, then write the row count and timestamp to
   `worker_heartbeats` (Part VI's one table). `/admin/ops` gains a line:
   *conflicts: N open, M new since yesterday, refreshed 04:12*. A stale
   refresh is now visible rather than silently freezing the scorable
   pool.

2. **Cluster gate — the one that prevents a bad campaign.** If a single
   paper produces **more than five** conflicts, flag the *paper*, not the
   questions. 0021 was eight conflicts in one paper; that shape is
   almost always a systematic transcription fault — a key page offset by
   one, a column misread, an OCR row shift — not eight independently
   wrong examiner answers. Clustered conflicts route to a paper-level
   re-transcription check **before** any per-question adjudication, and
   before auto-demotion applies. Adjudicating a page-offset error one
   question at a time produces eight wrong corrections and an immutable
   history of them.

3. **Exposure ranking.** A daily job joins the queue to attempt counts
   so ordering reflects real learner harm. Cheap, and it is what makes a
   long queue tolerable — the top twenty rows are most of the damage.

4. **Packet generation.** Extend `scripts/prepare-module-adjudication.py`
   (it already exists) to take a paper id and emit the exact packet
   shape `assistant-2018-paper2-adjudication.json` uses — canonical and
   appearance ids, prior and proposed indexes, option hashes, both bank
   checksums. The human adjudicates in a file they can read, which is
   how the 210 were found and is demonstrably the working process.

5. **AI pre-adjudication — draft only, never applied.** Reuse
   `services/mcq_solver_drafts.py`'s discipline: solve the question
   independently from the printed stem, attach the derivation, and write
   it into the packet as a *suggestion*. It never sets `key_disputed`,
   never publishes, and never counts as review — `CLAUDE.md` is explicit
   that AI agreement is not source verification, and a wrong key is
   precisely the case where a model that pattern-matches the key will
   agree with it. Its value is ordering and a first derivation, not a
   verdict.

6. **Erratum watch.** When a `review_documents` row for a paper that has
   open disputes is published or its `key_status` moves off
   `provisional`, re-open those disputes for re-check. This is the
   payoff for outcome 2's rule that the key column is never overwritten:
   when the corrected key arrives, the original is still there to
   compare against.

7. **Reassessment confirmation.** Migration 0032's trigger already
   enqueues score re-assessment when answer facts change. Add a test
   that proves it fires on a `key_disputed` flip specifically — the code
   path exists (`scoring_revisions.py:29` has the `disputed_key` reason)
   and nothing currently asserts it end to end.

**Deliberately not automated:** setting `key_disputed`. Every one of the
four outcomes is a human judgement about a printed source, and the
existing evidence requirements on answer changes exist because that
judgement has been wrong before. Automation finds and ranks the work; a
person decides it.

#### Step 5 — Order of operations

1. Ship the view and the `/admin/ops` count. **Look at the number before
   building anything else** — if Shape B is a dozen questions this is an
   afternoon; if it is four hundred it changes the plan, and either way
   the plan should not be written against a guess.
2. Run the cluster gate over the result and re-transcribe any paper over
   threshold.
3. Only then apply the `v_scorable` subtraction, so the scorable pool
   does not drop by a number that turns out to be a transcription bug.
4. Ship the learner label with the subtraction, in the same release —
   a question that silently stops scoring without explanation is worse
   than one that scores wrongly.
5. Work the queue by exposure, with packets.

**Tests**: the view's predicate and `published_comparison()` agree on a
seeded fixture of all four outcomes plus the `separate` explanation-only
shape; a disputed flip enqueues reassessment; a question leaving the
view re-enters `v_scorable` on the next refresh; the conflict aside
renders without being expanded; every existing bank guard passes
unchanged.

**Done when**: `/admin/ops` shows a conflict count, no Shape B question
is in `v_scorable`, and the top twenty by exposure are adjudicated.

---

## VII.7 Question currency — handling old and irrelevant questions (new)

The owner: *"distinguish old and unrelevant question how do we handle
it"*.

**Nothing in the product does this.** `canonical_questions.status` is
`('live','held','withdrawn','merged')` and that is the complete
lifecycle — no `retired`, `archived`, `obsolete`, `out_of_syllabus`,
`superseded_by` or `valid_until` column exists. `content_reports.kind =
'outdated'` is a *complaint type*; it sets no column. Parts 0–VI contain
zero occurrences of outdated/obsolete/irrelevant.

### VII.7.1 Two different problems, wrongly merged by the word "old"

1. **Stale facts.** A 2015 current-affairs question whose answer was
   true then. It is *not wrong* — it is dated. §QUESTION-TAGGING-RULES §4
   is explicit: "never replace its key with today's fact."
2. **Out-of-syllabus.** A question from a scheme that no longer exists,
   correct forever, useless for this exam.

A single "old" flag would conflate them and invite exactly the
destructive behaviour the tagging policy forbids.

### VII.7.2 Use the two fields that already exist and are empty

Before any new migration, populate what migration 0078 already shipped:

- **`bank_question_contexts.payload->>'time_behavior'`** ∈ `static |
  dated-event | changes-over-time | unknown`. This is the correct signal
  for staleness and it is **unpopulated** — zero rows as of 7 Nov.
- **`bank_paper_profiles.period`** ∈ `legacy | current | unknown`. The
  paper-level era marker. Also **zero rows**.

`GET /api/admin/bank/tag-issues` already filters on both
(`admin_bank_edits.py:95-96`). The pipework is built; nobody has turned
it on. Populating these is a tagging campaign, not an engineering
project, and it should run through the §VII.11 console.

One new field is genuinely needed, and only one:

```
-- migration 0135
ALTER TABLE bank_question_contexts  -- payload keys, no new table
  -- payload.scheme_status ∈ 'current' | 'superseded' | 'unknown'
  -- payload.superseded_note TEXT  (≥20 chars when 'superseded')
```

Kept as payload keys rather than columns so it inherits the existing
context-edit path and its audit trail, and so it cannot be set by SQL
outside the review workflow.

### VII.7.3 What the learner sees — a line, never a hidden question

**Nothing is hidden.** §0.11.4's lens rule — "labeled, never hidden" —
applies in full. A dated question gets one line under the source line:

> *Answer correct as of the 2015 paper. Check current figures.*

for `time_behavior ∈ (dated-event, changes-over-time)` on a paper older
than three years, and:

> *From a scheme that has since been revised.*

for `scheme_status = 'superseded'`.

The only behavioural consequence is **ordering, not exclusion**: the
default sort on `/practice` and `/bank` demotes `legacy`-period papers
below `current` ones. A learner who filters to 2015 still gets 2015.
Mock composition from `v_scorable` is unchanged — those questions were
on a real paper and remain fair game.

### VII.7.4 Where the signal comes from

- **Staff**, through the §VII.11 console's context editor, one bulk
  action over a paper (a whole paper usually shares a period).
- **Learners**, through the existing `content_reports.kind='outdated'`
  channel — which currently routes to a `kind='explanation'` correction
  and therefore dead-ends. Re-route it to a context proposal so the
  report can actually resolve to the flag it is describing.

**Done when**: `bank_paper_profiles.period` is non-`unknown` for every
paper before 2020, and an outdated report can be resolved by setting
`time_behavior` rather than by editing prose.

---

## VII.8 Explanation voice — removing AI wording (new)

The owner: *"make it less AI wording in the answers explanations to
easily remove them"*.

### VII.8.1 The state of play

- Explanations are drafted by `scripts/ai-question-review.py` and
  `services/mcq_solver_drafts.py`, reviewed, and published through the
  normal contribution path. That part is sound.
- **There is no style scrubber, no phrase blocklist, no linter and no
  post-processing of explanation text anywhere in the codebase.** The
  only server-side validation is a length floor — "at least 20
  characters" (`review_policy.py:123`) — and a 12,000-char ceiling.
- The anti-padding instructions exist **only as prompt text**
  (`ai-question-review.py:257-266`) and nothing checks the model's
  output against them.
- **`appearances.explanation` and `canonical_questions.explanation` are
  plain `TEXT` with no provenance columns.** There is no `ai_generated`,
  no `model`, no `prompt_version`, no `generated_at`. So the owner's
  actual request — *easily remove them* — is **currently impossible**:
  you cannot write a query that finds AI-written explanations, because
  nothing records which ones they are.

Note the schema already knows how to do this correctly elsewhere:
migrations 0085, 0086 and 0088 all carry first-class `model TEXT` +
`prompt_version TEXT` columns with uniqueness on
`(content_hash, model, prompt_version)`. And
`question_classifications.source` has a `'model'` value — **tagging has
provenance that explanations do not.**

### VII.8.2 Three pieces, in order

**1. Provenance first (migration 0135, same one as §VII.7).**

```sql
ALTER TABLE appearances
  ADD COLUMN explanation_model         TEXT,
  ADD COLUMN explanation_prompt_version TEXT,
  ADD COLUMN explanation_generated_at  TIMESTAMPTZ,
  ADD COLUMN explanation_human_edited  BOOLEAN NOT NULL DEFAULT false;
```

Backfilled from the `bank_contributions` payloads, which already carry
`model_id / prompt_version / solver_run_id` — stuffed into a rationale
*string* today (`mcq_solver_drafts.py:87-88`) rather than a queryable
column. This is the enabling change; without it every later step is
guesswork.

**2. A voice standard, enforced at submission.**

`docs/PUBLIC-ANSWER-LANGUAGE.md` is the existing home; extend it with an
explanation section and enforce it in `review_policy.py` as a **warning
surfaced in the editor**, not a hard rejection (a hard rejection would
block a human writing naturally):

- **No address to the reader.** No "Let's", "we can see", "you should
  note", "remember that".
- **No meta-commentary.** No "This question tests…", "The key here is…",
  "It is important to note that…".
- **No restating the answer as a conclusion.** "Therefore, the correct
  answer is (B)" — the interface already shows which option is correct.
  Start with the fact.
- **No hedging or padding.** No "generally speaking", "it can be said
  that", no closing revision advice.
- **No em-dash cascades.** At most one per sentence. *(The irony of this
  rule appearing in this document is noted and accepted — a design
  document and a one-line explanation are different objects.)*
- **Lead with the fact, then the discriminator.** Two sentences is
  usually the right length. The 20-char floor is not a target.

**3. The cleanup tool — `scripts/explanation-voice-report.py`.**

Read-only, matching the house pattern of the `prepare-*` scripts:
scan every explanation, score it against the blocklist, emit a ranked
packet of the worst offenders with before/after suggestions. The owner
reviews the packet; accepted rewrites go through
`POST /api/admin/bank/edits` with `kind='explanation'` in batches of 20,
exactly like the retag path. **It never writes bank data itself** —
`prepare-explanation-pilot.py:3-4` establishes that boundary and it
holds here.

The bulk endpoint is the missing piece: explanation fixes are today
strictly one question at a time, while tagging has `/retag/apply`.
§VII.11 adds the symmetric `/api/admin/bank/explanations/apply`.

**Done when**: `SELECT count(*) FROM appearances WHERE explanation_model
IS NOT NULL` returns a real number, and the voice report's top-500
packet has been worked through once.

---

## VII.9 Written, essay and LDE questions — display, list, do not answer

The owner: *"ESSAY LDE and written questions arrengments dont need to
answer..just display and lits"*. This is the cheapest high-value item in
the whole part, because the data is already there and already correctly
typed.

Parts 0–VI mention essay, descriptive, written and LDE **zero times**.
The entire learning model assumes MCQs. Meanwhile:

- **8,176 written questions** (9.9% of the bank) are stored as
  `type='descriptive'`, correctly forced to `answer_status='written'` as
  the first branch of `answer_status_sql()`
  (`question_readiness.py:12`) — so they can never be mislabelled
  "unsolved".
- `appearances.essay_kind ∈ ('essay','letter','precis','comprehension')`
  exists, is populated, and is filterable:
  `GET /api/questions?essay_kind=…`.
- `marks`, `passage`, `direction` are all carried on `PaperQuestion`.
  `qnum` is TEXT precisely so `"1(a)"` works.
- **289 LDE papers** are ingested and tagged — and **unreachable**:
  `MockRunner.tsx:63` throws *"LDE exam practice will be added as the
  exam library grows."*

### VII.9.1 The decision — a written question is a reading surface

No answering, no evaluation, no rubric, no auto-marking, no AI grading.
A written question renders as:

- the direction, the passage (where present), the question text, the
  marks, and the `essay_kind` as a plain word;
- the source line, as every question has;
- **no option list, no reveal gate, no answer area** — the reveal gate
  is meaningless where there is no key;
- one link: *"Write a practice answer"* → the existing `essay_drafts`
  flow (`GET/PUT /api/me/essay-drafts/{question_id}`), which already
  states the right principle in its migration: *"no automatic marks or
  public visibility; the learner owns the writing."*

**Fix the draft guard while here.** `me.py:44` restricts drafts to
`essay_kind='essay'`, so letter, précis and comprehension prompts are
served with nowhere to write. Widen it to all four kinds — a one-line
change that unblocks three quarters of the written bank.

### VII.9.2 Browsing them

Written questions become a **first-class filter**, not a residue:
`/practice` and `/bank` gain a *"Written answers"* mode that lists them
by paper, subject and `essay_kind`, with the count shown honestly.
`/essay` (currently a 110-line standalone screen) is retired into it per
§VII.3's one-manifest rule.

**LDE unblocks by the same move.** The 289 papers do not need practice
mechanics — they need to be *listed and readable*. Remove the
`MockRunner.tsx:63` throw, route LDE papers to the browse-and-read
surface, and drop the "will be added as the exam library grows" copy,
which has been false for as long as the papers have been ingested. LDE
stays out of `v_scorable` and out of exam-track definitions
(migration 0011) — unchanged.

**Done when**: an LDE paper is reachable from `/papers` and renders its
questions; a `precis` prompt accepts a draft.

---

## VII.10 Tests — one builder, two publishers

The owner wants *"a proper way to make tests by admin and users"*, and
the pieces mostly exist: `screens/TestMaker.tsx` (63 lines) at
`/tests/make` already does three steps — details → choose questions
(max 100) → review & share — with `duration_minutes`, `marks_correct`,
`marks_wrong`, `answer_mode`, a draft→review→publish workflow, and an
owner direct-publish path.

What is wrong is discovery and naming, not mechanics.

### VII.10.1 One builder, two outcomes

`/practice/build` — the same builder for everyone, with the publishing
step differing by role:

| | **A user builds** | **Admin / owner builds** |
| --- | --- | --- |
| Sources | bank + their saved questions | bank |
| Answer basis | official-key only, or practice estimate | same |
| Publish | submit → independent review → share link | `owner_publish` after preview confirmation (exists) |
| Appears in | their profile, the share link | `/practice` catalogue as a **featured test** |
| Label | "Made by @handle" | "Finna test" |

The featured-vs-user distinction is a label and a listing position, not a
second code path. §II.4.4's honesty rules apply: a user test never
renders as a site test.

### VII.10.2 Build from anywhere

The one real addition: a **selection tray**. `/bank` already has a
multi-select scratch list that feeds `?ids=…` into the builder
(`Bank.tsx:50-53`). Make it site-wide and persistent — select questions
while browsing a paper, a guide chapter, a subject or the index, then
*"Make a test from these (14)"*. That is the "users usually like to
browse and make test" loop the owner described, and it is currently
one screen's local state.

A guide chapter's "Practice this chapter" (§VII.5.3) is the same tray,
pre-filled.

**Done when**: the tray survives navigation, and `/tests/make` is gone
in favour of `/practice/build`.

---

## VII.11 VI.6 — The authoring console (new section of Part VI)

The owner: *"easier and straightforward and quick and smooth way for the
admin to change tags and modify or edit questions quickly"*.

**Part VI says nothing about this.** It specifies an ops dashboard, a
maintenance system and a read-only user viewer — no question editor, no
tag editor, no bulk edit, no authoring throughput at all. The only
authoring precedent in the document is Atlas Studio's binding editor
(§III.3, line 4404), which is the right model and the wrong subject.

### VII.11.1 What a trivial edit costs today

Fixing one typo, as owner, in the solo workflow:

1. `GET /api/admin/bank/tag-issues` — find it
2. `GET /api/review/taxonomy` — load the picker
3. `GET /api/review/questions/{qid}` — get `edit_hash` + `baseline_token`
4. `POST /api/admin/bank/routine-edits` — the write
5. `GET /api/contributions/{cid}` — **polled** until publishing ends
6. `GET /api/admin/bank/publications/{pubid}/verification` — readback

**Four round-trips before the write, six-plus with the async publish
poll and verification.** For a non-owner it is eight to ten, across two
or three people. Bulk retag caps at **20 targets**
(`retagging.py:98`), each requiring both a `baseline_hash` and a
`source_version` from a prior `/preview`, and internally it loops
`decide()` once per question — so twenty questions make twenty
contributions and twenty publications. The admin screen polls the batch
every 12 seconds.

None of this is wrong. Every guard — MFA, CSRF, rate limit, per-subject
grants, idempotency keys, advisory locks, stale-source checks, active-
assessment holds, immutable history, guarded publication with readback —
exists because something went wrong once. **Not one of them is removed
here.** The latency is not in the guards; it is in the *interface making
you pay for them one question at a time, with a page navigation between
each.*

### VII.11.2 One screen, keyboard-first

`/admin/bank?tab=edit` — a worklist on the left, the question on the
right, and the editor never navigates:

```
┌─ queue ──────────┐┌─ question ─────────────────────────────┐
│ ▸ 1,284 untagged ││  MPSC LDC 2018 · Paper I · Q14         │
│   312 legacy     ││  [ stem / options / answer / expl ]    │
│   88 reported    ││                                        │
│                  ││  subject  ▸ Polity          [tab]      │
│ ■ Q14  Polity    ││  topic    ▸ Fundamental Rights         │
│   Q15  —         ││  related  + Constitution               │
│   Q16  —         ││  period   ▸ legacy    time ▸ static    │
│   Q17  Geography ││                                        │
│                  ││  note ____________________             │
│ j/k move  e edit ││           ⌘↵ save & next               │
└──────────────────┘└────────────────────────────────────────┘
```

**The rules that make it fast:**

- **The queue prefetches.** Moving to the next question needs **zero**
  round-trips — the snapshot, its `baseline_hash`, its `source_version`
  and the taxonomy were fetched with the queue page. The 4-round-trip
  preamble collapses to one, amortised over 50 questions.
- **Save is one keystroke and does not navigate.** `⌘↵` writes and
  advances. The publish poll runs in the background with a per-row
  status dot; a failure surfaces in place and the row stays in the
  queue. Nobody watches a spinner.
- **Taxonomy picker is search-as-you-type** against the 181 active
  registry nodes, exactly as §III.3 specifies for Atlas bindings.
  Keyboard only — type three letters, Enter.
- **Repeat-last-tag.** `.` applies the previous question's full path.
  The common case is a run of questions from one paper sharing a
  subject; today each one is a fresh picker interaction.
- **Bulk acts on the queue selection**, not on a separate screen.
  Shift-select rows, apply one path or one context value to all of them,
  through the existing `/retag/preview` → `/retag/apply` pair. The 20-cap
  stays; the UI simply pages through it automatically and reports
  `3 of 7 batches` rather than making the operator re-select.
- **Context editing is in the same form** — `period`, `time_behavior`,
  `scheme_status` (§VII.7) as three selects, because a question's era is
  usually obvious at exactly the moment someone is looking at it, and
  will otherwise never be entered.

### VII.11.3 Two symmetric bulk endpoints

Tagging has `/retag/apply`; nothing else does. Add, with identical
guards, identical 20-cap, identical preview/baseline/idempotency
discipline:

- `POST /api/admin/bank/explanations/apply` — §VII.8's packet path
- `POST /api/admin/bank/contexts/apply` — §VII.7's currency campaign

Both reuse `admin_bank_edits.decide()`. No new permission model, no new
audit shape, no SQL-only path (§VI.1 rule 3 forbids it).

### VII.11.4 One small piece of real-time, and only one

Replace the 12-second batch poll with **Server-Sent Events** on the
batch-progress endpoint. One-way, one route, staff-only, degrades to the
existing poll when the connection drops. This is the single place in the
product where polling is genuinely the wrong tool, and it is why §VII.13
says no to WebSockets everywhere else.

**Done when**: a measured run tags 100 questions in under eight minutes
with no page navigation, and the publish failures from that run are
visible without leaving the screen.

---

## VII.12 Mobile — the intro and the guide

The owner asked for a "mobile guide and intro". The document has §12.6
(Expo widening), §IV.8 (mobile backend) and V.6 (interleaved rollout) —
and **zero occurrences of tour, first-run or welcome**. Onboarding asks
exactly one question today: *"What are you preparing for?"* (§0.11.1).

### VII.12.1 Intro — three cards, skippable, once

After the exam question, three cards. Not a tour, not an overlay, not
coach marks pointing at buttons:

1. **Browse** — every past paper, every question, free. *Open Papers.*
2. **Practice** — pick what, pick how many, timer optional. *Try 10
   questions.*
3. **Guides** — read first, practise after. *Open a guide.*

That is the product. If three sentences cannot describe it, §VII.1
through §VII.4 have not gone far enough.

The third card **starts a 10-question untimed run right there**, so the
first session ends with the learner having answered something rather
than having read about answering. Skippable at any point, shown once,
never re-triggered by a release.

### VII.12.2 The guide — a page, not a product tour

`/guides/using-finna`, authored as a normal guide (§VII.5) so it costs
no new system: what the answer labels mean, what "not verified" means,
how the timer toggle works, what scoring counts, what the free tier is.
Linked from `/index`, from the intro's last card, and from the support
surface §13.1 #13 proposed.

Writing it as a guide rather than a hardcoded screen also means it is
the **first guide**, which proves the pipeline before the subject guides
land.

### VII.12.3 The Expo app

§0.12 point 2 stands untouched: the phone web is *the* mobile
experience; the app is the offline companion and does not chase parity.
The app gets the same three intro cards and **no separate guide system**
— guides are reading, reading is web, the app links out. A
`MobileBoundary` widening for guides would be parity-chasing, which
§0.12 forbids by name.

---

## VII.13 Technical — what actually helps, and what does not

The owner asked about *"microservece or websocket or any kubernites or
anything that can imporve the website"*. The honest answer is that the
architecture already decided against all three, for reasons that still
hold, and the real wins are duller.

### VII.13.1 The three, answered directly

**Microservices — no.** §IV.1–IV.2 specify one FastAPI application, 56
routers, ~120 service modules, one Postgres. Splitting that across
services buys independent deployment and costs distributed transactions,
network failure modes, and an audit trail that can develop holes —
which §VI.1 rule 3 bans by name. The bank's integrity guarantees
(immutable history, guarded publication with readback, advisory locks,
stale-source tokens) are *single-database* guarantees. They do not
survive a service boundary without a distributed-transaction story
nobody wants to operate. The modular monolith is not a compromise here;
it is load-bearing.

**Kubernetes — no.** The whole site runs on one Oracle A1 VM with
systemd units and in-process asyncio workers (§IV.7), and measured
throughput on the 77k bank is **5,379 tps** with a 29-second migration.
Kubernetes solves multi-node orchestration for teams with multi-node
problems. A one-person team with a single VM would acquire a control
plane, a registry, an ingress, cert plumbing and a new class of outage —
to run the same process. Revisit at T3 in §0.7, which is explicitly
gated on *measured* demand and has not arrived.

**WebSockets — one exception, already named.** §IV.7's rule is "no
external queue"; the same logic applies to persistent connections.
Finna has no genuinely collaborative surface: a mock timer is
server-authoritative and polled, duels are turn-based, the Inbox is
checked not pushed. The one place where polling is clearly wrong is the
admin publish-batch progress poll every 12 seconds, and that is **SSE,
one-way, staff-only** (§VII.11.4). Not a WebSocket, not a gateway, not a
second runtime.

### VII.13.2 What actually moves the numbers

In descending order of measured leverage:

1. **Prerender the public pages and ship sitemaps.** §13.1 #9 already
   calls this "likely the highest-leverage growth work in the entire
   document" and it is still not built. Questions, papers, exams and now
   guides and `/index` (§VII.3.2) are public, static-shaped and
   invisible to search engines because they render client-side. This is
   the single biggest change available to the product and it is not an
   architecture change.
2. **Fix the two slow queries**, which are known and measured. A covering
   index beats every item below it combined.
3. **Turn on the HTTP cache tier for guest browse** — already specified
   at §IV.10 (ETag + `Cache-Control: public`, guests only; learner data
   stays `private, no-store` per the hard rule at §IV.2). Specified,
   not shipped.
4. **Serve papers and images from a CDN.** 264 MB of exam PDFs and 73 MB
   of diagrams currently come off the application host. Static bytes
   have no business occupying an application worker.
5. **Full-text search in Postgres** (`tsvector` + `pg_trgm`), one
   generated column, one GIN index. The index page, ⌘K and guide search
   all need it, and it is cheaper and better than the three separate
   client-side filters they would otherwise each grow.
6. **Self-host the fonts** (§VII.2.2) — removes a render-blocking
   third-party request from every cold page load.
7. **`LISTEN`/`NOTIFY` instead of poll loops** where a worker currently
   polls with backoff. Same database, no new dependency, no queue.
8. **Ship the explanation and context bulk endpoints** (§VII.11.3) —
   throughput for one person is as real a performance number as p95
   latency, and it is the one the bank is actually bottlenecked on.

### VII.13.3 Terminology, for the bank build

The owner asked about "tehicnal terms while building the bank". The
vocabulary already in use, which future work should not re-coin:

- **canonical question** vs **appearance** — one question, many printings.
- **answer_source** (`official | key | derived | inferred | none`) — how
  the answer was obtained. **answer_status** — what the learner is told
  (§VII.6).
- **`v_scorable`** — the pool eligible for scoring, rewards and games.
- **baseline_hash** (content digest) and **source_version** (xmin-bound
  token) — the two independent stale-source guards; both must match.
- **hold** (reversible, pending repair) vs **withdrawn** (source pulled,
  answer force-nulled) vs **merged** (deduplication). There is no
  "deleted".
- **contribution → revision → decision → publication → verification** —
  the five immutable stages every bank change passes through.
- **primary path** (one per question) vs **related paths** (≤12,
  "a ceiling, not a target").

---

## VII.14 Module-by-module improvement list

The site is **93 route declarations across ~88 paths**, 36,068 lines in
`web/src`, with seven navigation surfaces. Seven routes are already pure
redirect shims from a previous consolidation that left the old URLs
behind rather than deleting them.

Target: **~40 routes, two navigation surfaces, one manifest.**

Legend — **Keep** (improve in place) · **Merge** (into another module) ·
**Cut** (delete or demote to a view) · **New**.

### Core — the two verbs

| Module | Now | Verdict | Change |
| --- | --- | --- | --- |
| **Home** `/feed` | `StudyHome.tsx`, 72 lines, plus footer links duplicating nav | **Keep** | Today, continue, recap, one weak spot. Delete the footer link grid — that is `/index` now (§VII.3.2). Rename the route `/home`; `/feed` reads like the community feed it is not. |
| **Browse** `/bank`, `/bank/:id`, `/past-papers`, `/exams/:id/paper` | 3 parallel browsers — `Bank.tsx` (279), `ModuleQuestionBrowser`, `GuideQuestionBrowser` | **Merge → 1** | One browser component, parameterised by scope. Apply the Prelims filter bar (one explicit grid, native selects, uppercase 11px labels). Keep infinite scroll with the visible "Show more" fallback. Provenance per §VII.6. |
| **Practice** `?pool=practice` ×4 copies | not a route; 4 code paths | **Merge → `/practice`** | §VII.4. The single biggest simplification in this part. |
| **Mock** `/tests/*`, `/exams/:id/mock`, `/results`, `/scoring` — 7 routes | `MockRunner.tsx` (309) branching on params | **Merge → `/practice`** | §VII.4. `/scoring` becomes a disclosure on results. |
| **Test builder** `/tests/make` | `TestMaker.tsx` (63), works, undiscoverable | **Keep → `/practice/build`** | §VII.10. Add the site-wide selection tray. |
| **Guides** | does not exist | **New** `/guides` | §VII.5. ~43 MB of authored content currently invisible. |
| **Index** | does not exist | **New** `/index` | §VII.3.2. Also the SEO entry point. |

### Study surfaces

| Module | Now | Verdict | Change |
| --- | --- | --- | --- |
| **Exams** `/exams`, `/exams/:id`, `/exams/mes`, `/group-b` | ~1,400 lines, 18 files; 6 view tabs | **Keep, thin** | Tabs `Overview · Browse · Papers · Practice` — drop *Subjects* (that is `/library`) and *Progress* (that is Home). `/exams/mes`'s one-item `EXAM_GUIDES` catalogue retires into `/guides`. `/group-b` and `/exams/mes` become `/exams/:id`. |
| **Papers** `/past-papers` | `Papers.tsx` (35) + `PaperViewer` (156) | **Keep** | Add LDE and written papers (§VII.9). Move PDFs to a CDN (§VII.13.2 #4). |
| **Library** `/library` + 2 sub-routes | `LibraryShelf.tsx` (469); holds 18 unrelated destinations under one word | **Cut the tab, keep the shelves** | The phone tab becomes **Guides**. Shelf and subject pages survive as browse scopes. The two extra hardcoded link lists inside it (`Library.tsx:7`, `:17`) are deleted by §VII.3.1. |
| **Revise** `/revise` + 3 redirects | `Revise.tsx` (38), `Vocabulary.tsx` (500) | **Keep** | §0.12's owning surface, unchanged. Delete the three redirect shims — they have had a year to be unlinked. |
| **Subject modules** `/english`, `/arithmetic`, `/mizo`, `/essay` | 4 bespoke screens, ~500 lines + JSON | **Merge** | `/english`, `/arithmetic`, `/mizo` become library subject scopes. `/essay` becomes the written-answers mode (§VII.9.2). Their curated content becomes guides. |
| **Atlas** `/atlas` | 7,911 lines, mostly chapter data | **Keep, untouched** | Part III governs it. Not a guide; do not fold it in (§VII.5.4 tier 4). |
| **Chronicle** `/chronicle` | 160 lines | **Keep** | Already absorbed `/important-days`; delete that shim. |
| **Stats** `/stats/*` | 250 lines | **Demote to a view** | A tab on Home, not a destination. Nobody navigates to statistics; they encounter them. |
| **Calendar** `/calendar`, `/news` | 1,300 lines, 8 files | **Keep, merge the twin** | `/news` is `/calendar` with a filter. One route, two tabs. |
| **Desk** `/desk`, `/desk/:id` | **`StudyDesk.tsx` is 2,334 lines — the largest file in the repo**; ~3,900 lines total | **Keep, focus & split** | **Why Desk stays:** it is Finna's only private group-study space (§0.13 deliberately bans 1:1 DMs in favour of 6-seat invite-only rooms) and the learner's personal binder. **What changes (confirmed 22 Nov 2026):** (1) **Personal Desk** keeps question-linked notes (`0114`, with PDF export), saved questions/bookmarks, and the Pomodoro focus timer; remove duplicate Home widgets (Today card copy, mastery strip, self-reported weekly target) and remove `DeskPractice`'s separate *solo* practice session store — solo practice links to `/practice` (§VII.4.2). (2) **Group Desk Rooms** keep all staged Desk v4 capabilities (`0111–0115`): shared weekly goal (`DeskWeeklyGoal`), review circle (`0112`), synchronized group practice sessions (`0113`), room chat, and the room-filtered calendar view (`0115`). (3) Split the 2,334-line `StudyDesk.tsx` into focused room, notes/binder, and focus sub-components. |
| **Games** `/games`, `/games/:id`, `/trail`, `/duel` | `Games.tsx` (1,146) | **Keep** | §0.12 already decided one Play hub; `/trail` and `/duel` fold in. §0.5 caps the ambition; leave it capped. |

### Community and content

| Module | Now | Verdict | Change |
| --- | --- | --- | --- |
| **Community** `/community`, `/creators/*`, `/community/contributors`, `/community/questions`, `/website-bank` | ~1,500 lines; `QuestionDiscussion.tsx` is 904 | **Keep, dedupe routes** | `/website-bank` and `/community/questions` are the same component — one route. `/community/contributors` is a tab, not a page. |
| **Materials** `/materials`, `/studio/*` | 180 lines total, embedded at 4 entry points | **Keep, relabel** | Stays the user CMS. Label it **"From the community"** everywhere so §VII.5.1's boundary against first-party Guides is visible, not implied. |
| **Contribute** `/create`, `/contribute`, `/contribute/new`, `/contributions/:id(/edit)` | 350 lines, 4 routes for one job | **Merge → `/create`** | One route, one stepper. |
| **Inbox** `/inbox` + 2 redirects | **809 lines, one file** | **Keep, split** | §0.12's single notification surface. Split the file; delete the two shims. |
| **Profile / account** `/profile`, `/avatar`, `/account/*`, `/plans`, `/billing`, `/rewards`, `/board`, `/more`, `/policies/:page` — 12 routes | ~1,600 lines, 25 files | **Consolidate → 4** | `/profile` (with tabs), `/account` (security, privacy, email, recovery), `/plans` + `/billing`, `/policies/:page`. `/more` is deleted (§VII.3.3); `/board` and `/rewards` are profile tabs; `/avatar` is a profile route. |
| **Onboarding** `/onboarding` | one question | **Keep, extend** | §VII.12.1's three cards. |

### Admin and staff

| Module | Now | Verdict | Change |
| --- | --- | --- | --- |
| **Admin console** `/admin/bank` + 26 sidebar sections | ~3,500 lines, 55 files | **Keep, add the editor** | §VII.11 / new §VI.6. The 26 sections are defensible — admins are experts and `adminNavigation.ts` is already a single manifest, which is the pattern §VII.3.1 copies. |
| **Admin strays** `/admin/privacy`, `/admin/topic-trail`, `/admin/discovery`, `/admin/mcq-solver`, `/admin/desks`, `/admin/discussions`, `/admin/moderation`, `/admin/atlas*`, `/editorial`, `/paper-workbench`, `/current-affairs/*`, `/learning/manage` — 14 routes outside the console | each its own screen | **Merge → sections** | They are already in the sidebar as *shortcuts*; make them sections. §VI.1's "one place per operational job" applies to admins too, and today it does not. |
| **Editorial** `/editorial` | ~500 lines, 12 files | **Merge** | Becomes the review section of §VII.11's editor. Its tag-cleanup screen is the direct ancestor of that design. |

### Cut outright

| Route | Why |
| --- | --- |
| `/duel`, `/important-days`, `/notifications`, `/contribute/notifications`, `/revision`, `/mistakes`, `/vocabulary` | Pure redirect shims from the last consolidation. Shipping a redirect is how a consolidation ends; keeping it for a year is how the route count grows back. |
| `/review`, `/website-bank`, `/admin`, `/avatar` | Aliases to other routes. |
| `/more` | Replaced by `/index`. |
| `/scoring` | Disclosure on the results page. |
| `/exams/:id/*` → `Planned` | A stub route that renders "planned". Delete it; a 404 is more honest. |

### Cross-cutting, every module

1. **Font system** (§VII.2) — one shell declaration, eight sizes,
   self-hosted, 16px base.
2. **Layout contract** (§VII.1) — no screen declares a font-family; two
   chrome rows maximum; hairlines; no decorative motion.
3. **Navigation from one manifest** (§VII.3.1) — zero hardcoded paths in
   components.
4. **Provenance as the exception, not the rule** (§VII.6).
5. **Currency lines on dated questions** (§VII.7.3).
6. **Written questions readable everywhere they appear** (§VII.9).
7. **Every list has an honest empty state and an honest error state** —
   §VI.1's rule, applied to learner screens as well as admin ones: an
   outage renders as an outage, never as "nothing here".

---

## VII.15 Build order

Three phases, appended to §V.13. Each is independently shippable and
none blocks the V.2 learning core, which remains the critical path.

### V.14 — Surface and type (no new data, no migration)

The whole of §VII.1, §VII.2, §VII.3, §VII.4, §VII.6 (UI half), §VII.9
(UI half), §VII.10 and the §VII.14 route cuts.

Entirely front-end plus two one-line API relaxations (the `essay_kind`
draft guard at `me.py:44`, the `MockRunner.tsx:63` LDE throw). This is
the phase that answers the owner's actual complaint, and it needs no
schema change, so it can run alongside anything.

**Tests**: route count ≤ 40; zero hardcoded paths outside `siteMap.ts`;
one `font-family` declaration in the codebase; no `text-[Npx]` values;
every §VII.14 "Cut" route returns 404.
**Done when**: a new user can describe the site in one sentence after
the intro.

### V.15 — Guides (migration 0136: three tables)

§VII.5 and §VII.12.2. Shell, three guides, chapter→practice link,
`/guides/using-finna` first.

**Tests**: no guide body renders as raw embedded HTML; every
`guide_question` resolves to a live bank question; the index shows only
published guides.
**Done when**: three guides are readable and each chapter can start a
practice run.

### V.16 — Bank quality and the authoring console (migration 0135)

§VII.7 (currency), §VII.8 (explanation provenance and voice) and §VII.11
(the editor plus the two bulk endpoints). One migration covering the
explanation-provenance columns and the two context payload keys — note
this is **numbered before** the guides migration because the console is
what makes the content work affordable, and should ship first if the two
compete.

**Tests**: every existing bank guard still passes unchanged; a 100-
question tagging run completes with no page navigation; the voice report
is reproducible and writes nothing.
**Done when**: `bank_paper_profiles.period` is populated for every
pre-2020 paper and `explanation_model` is non-null for every
AI-drafted explanation.

### V.17 — Key-versus-solution conflicts (migration 0137)

§VII.6.2 and §VII.6.3. The conflict matview, the `/admin/ops` count, the
cluster gate, the `v_scorable` subtraction, the third learner label.

Sequenced **after V.16** because it reuses that console's queue, but the
view and the count can ship on their own at any time — and should,
because the number is currently unknown and it determines the size of
everything else in the phase.

**Tests**: §VII.6.3 step 5.
**Done when**: no Shape B question is in `v_scorable`.

### V.18 — Database work (no migration except where measured)

§VII.16, in its own order. The drift test (§VII.16.3) is independent of
every other phase and should run in CI from the first week.

**Done when**: both measured open shapes are closed or rejected in
writing.

### Updated final order

| # | Phase | Delivers |
| --- | --- | --- |
| 1 | V.1 perf | fast anonymous browse |
| 2 | **V.14 surface & type** | the simplification the owner asked for — no migration, can start now |
| — | **V.18 drift test** | §VII.16.3 only — zero risk, runs beside anything |
| 3 | V.2 core | mastery, `/revise`, Today, focus, calendar, heartbeats |
| 4 | **V.16 bank quality & console** | authoring speed, currency, explanation voice |
| 4½ | **V.17 conflicts** | wrong official keys found, ranked and adjudicated |
| 5 | V.3 habit | one streak, rewired quests |
| 6 | **V.15 guides** | the reading library |
| 7 | V.4 economy | sub-caps, milestones, repricing |
| 8 | V.5 boards | leaderboards, recap, calendar layers |
| 9 | V.9 consolidation | whatever §0.12 still owes after V.14 |
| 10 | V.10 community | posts, votes, composer, uploads |
| 11 | V.11 growth | **prerender + sitemaps first** (§VII.13.2 #1), then email, referral, digest |
| 12 | V.12 admin/maint | Part VI consoles, retention workers |
| 13 | Parts II–III remainder | desk v4, Atlas v2 + Studio |

**V.14 moves to position 2** because it is the owner's stated problem,
requires no migration, and makes every later phase cheaper to ship into
a smaller surface. **Prerendering moves to the front of V.11** on §13.1's
own assessment of its leverage.

---

## VII.16 Database improvements without regression (owner request, 22 November 2026)

The owner asked for database improvement *without regression*. The
qualifier is the hard part, and this repository has already shown it
knows how — twice in one week, in opposite directions.

### VII.16.1 The method is settled; it is the acceptance bar that matters

On **18 November** a real 1000 ms duration log exposed a derived-question
detail lookup taking **4.5 seconds**. Its broad reviewed-publication and
readiness subqueries were replaced with the bounded
`question_readiness` helpers already used elsewhere. Derived queries went
**~4.4 s → 3–4 ms**; other sources stayed at 2–4 ms. Verification: a
fresh 249-table production clone, full canonical readiness and
reviewed-derived parity over **82,383 questions with zero mismatches**,
old-versus-new payload comparison in two exam scopes with JIT on and
off, 1,335 backend checks, no migration and no index.
(`reports/finnaplan-v12-query-performance-20261118/`)

On **20 November** a plausible "redundant readiness joins" optimisation
was **rejected**: four warm samples across 32 cases showed only **2.95%**
improvement in summed case medians, with all 160 output comparisons
matching across 480 timed runs. Nothing shipped.
(`reports/finna-query-performance-20261120/`)

**That rejection is the most valuable artefact in this section.** The
bar is not "is it faster" — it is "is it enough faster to be worth a
change to a system whose correctness guarantees are load-bearing." A
2.95% median gain is noise wearing a lab coat. Any proposal below that
cannot clear a real margin on a real clone is to be rejected the same
way, and the rejection written up the same way.

Standing procedure, already practised and now binding for this part:

1. Reproduce on a **fresh production clone**, never production, never a
   synthetic fixture (`CLAUDE.md`).
2. Prove **output parity over the whole bank**, not a sample — the
   18 November run's 82,383-question zero-mismatch check is the shape.
3. Timed runs, warm, multiple samples, **median not best**.
4. New numbered migration; never edit an applied one. Rehearse on a
   disposable dump clone.
5. If the margin is small, **write the rejection up and stop.**

### VII.16.2 What is measured, open, and worth doing

Three items, in order. Only the first two are known-open; the third is
structural and needs its own measurement before anyone commits.

**1. Collection-count queries at 1–1.6 s.** Named explicitly in the
18 November report as "separate observed shapes" that the release
*did not* address, and still unaddressed. This is the largest confirmed
open latency in the product. It is also user-visible — collection counts
sit on browse surfaces §VII.14 keeps.

**2. The empty-pins branch: 726 ms scanning 79,288 questions 45 times
to return zero rows.** Found 20 November, follow-up at
`reports/finna-empty-pins-20261120/`. A branch that scans the whole bank
45 times to produce nothing is not a tuning problem, it is a missing
early-exit — the cheapest class of fix there is, and the one with the
least regression surface, because the correct output is already known to
be empty.

**3. `v_reviewed_answer_publications` is evaluated per row.** Migration
0032:65 defines it as a four-table join (`canonical_questions` ×
`bank_contributions` × `bank_publications` × `appearances`) with roughly
a dozen JSONB receipt comparisons — `question`, `options`, `direction`,
`passage`, `questionMarkup`, `optionsMarkup`, `hasDiagram`,
`figureImage`, plus an `answerIndex` type check and a final option
look-up by index. `answer_status_sql()` calls it through `EXISTS(…)`
for every `derived` row, which is **57,448 questions — 69.7% of the
bank**. The `OFFSET 0` optimisation barrier in
`question_readiness.py:5` exists precisely to stop the planner hoisting
it, which is a strong hint about its cost.

The 18 November fix bounded this at **one** call site. Every other site
still pays. Materialising it — refreshed on publication, since
publications are rare and reads are constant — is the one structural
change here with a plausibly large payoff.

**But it must be measured first, and it may well be rejected.** The
partial index `idx_cq_scorable` (0002:150) may already make the common
path cheap enough, and 20 November proved that an obviously-redundant
join can be worth 2.95%. Measure, then decide. If it ships, parity is
checked the 18 November way: matview against view, all 82,383 rows,
zero mismatches, before the first read is switched over.

### VII.16.3 The zero-risk one: stop the answer-status rule drifting

The `answer_status` CASE exists in **three** independently maintained
copies:

- `v_bank_answer_status` — migration 0050:6
- the inline CASE in migration 0049:41
- `answer_status_sql()` — `services/question_readiness.py:12`

`question_readiness.py`'s own docstring says *"Keep the CASE identical
to v_bank_answer_status (migration 0050)"* — an instruction addressed to
humans and enforced by nothing. §VII.6.2's conflict view would add a
fourth surface that must agree.

The fix is **a test, not a change**: assert that all three classify every
one of the 82,383 rows identically on a clone. Zero regression risk by
construction — it alters no query plan and no output. If they already
agree, the test is cheap insurance on the product's single most
load-bearing business rule. If they *disagree*, that is a live
correctness bug affecting what learners are told about answers, found
for the price of a test.

Do this first. It is the only item in §VII.16 that cannot make anything
worse.

### VII.16.4 Candidates that look like improvements and are not

Recorded so nobody spends a week rediscovering them:

- **Denormalising `answer_status` into a column.** Breaks the single
  source of truth, and the 0032 reassessment trigger already depends on
  answer facts changing *through* the publication path. A cached status
  column would need its own invalidation on five different writes.
  §VII.6.2 deliberately uses a view for the same reason.
- **Indexes added without measurement.** Every index is a write cost on
  a bank that takes bulk tagging campaigns of 58,000+ corrections. The
  existing index set (`idx_cq_scorable` partial, `idx_cq_stem_trgm` GIN,
  `idx_cq_search` GIN, `idx_cq_merged_into` partial) is already shaped
  around the measured hot paths, with a comment naming the hottest query
  explicitly.
- **Partitioning.** 82,383 rows. Partitioning helps at two to three
  orders of magnitude more. It would add planning overhead and break the
  partial indexes.
- **`ORDER BY random()`.** Already banned by `CLAUDE.md`; use the
  existing indexed selection helpers.
- **A connection pooler or read replica.** §0.7 puts the read replica at
  T3, explicitly gated on measured demand that has not arrived. Measured
  throughput is 5,379 tps on one VM.
- **Anything in §VII.13.1.** Microservices, Kubernetes and a queue do not
  become good ideas because the entry point is the database.

### VII.16.5 Full-text search — the one genuine addition

§VII.13.2 #5 needs it, and it is additive rather than a rewrite:
`tsvector` plus `pg_trgm` for `/index`, ⌘K and guide search. Note
`canonical_questions` **already has** a `search` column with a GIN index
(0002:152) and `stem_norm` with a trigram index (0002:151) — so the
question half exists. What is missing is guides (§VII.5, new tables, so
no regression surface at all) and a union across both.

Build it on the new tables first, where nothing can regress, and extend
to questions only if a measured need appears.

### VII.16.6 Order

1. **The drift test** (§VII.16.3) — no risk, highest information.
2. **Empty-pins early exit** (§VII.16.2 #2) — known output, smallest surface.
3. **Collection counts** (§VII.16.2 #1) — largest confirmed open latency.
4. **Measure the reviewed-publications matview** (§VII.16.2 #3) — then accept or reject in writing.
5. **Full-text on guide tables** (§VII.16.5) — ships with V.15.

**Tests**: every item carries whole-bank output parity on a fresh clone,
warm timed medians across ≥30 cases, and a written result — *including
when the result is "rejected, 2.95%."*

**Done when**: the two measured open shapes are closed or explicitly
rejected in `reports/`, and the answer-status drift test runs in CI.

---

## VII.17 Owner decisions locked in (22 November 2026)

All four open questions from the initial Part VII draft are now resolved by
the owner and binding for V.14–V.18:

1. **§VII.6 / §VII.6.2 — Three-label learner vocabulary & Shape B conflict count (resolved 22 Nov 2026).**
   The owner's reason for reducing official-key chrome is *"because some
   official keys are wrong"*, not scarcity. §VII.6.2 resolves it:
   trusted answers carry no badge; unverified/provisional answers show
   **Not verified**; conflicts (`key_disputed` or un-adjudicated Shape B)
   show **Answer disputed** inline, never collapsed inside a `<details>`
   disclosure. The official-key column is never overwritten.
   **Execution rule locked for V.17 (§VII.6.3 Step 5):** run the Shape B
   read-only conflict query / matview (`0137_answer_conflicts.sql`) on the
   isolated production clone and inspect the exact count + paper-cluster gate
   (>5 conflicts in one paper = transcription/offset check first) *before*
   activating the `v_scorable` subtraction.
2. **§VII.5 — First Guides release batch (resolved 22 Nov 2026).**
   Ship the `/guides` shell with `/guides/using-finna` (§VII.12.2) plus
   **Polity Codex**, **Quick Revision**, and **Tenses & Voice**. All three are
   complete in `india-study-map/public/`, span three core subjects, and verify
   the `guide → guide_chapter → guide_question → /practice` pipeline before
   converting the remaining Tier-1 prose guides.
3. **§VII.4 — Merged free-tier allowance (resolved 22 Nov 2026).**
   Once practice and mock merge into `/practice` with a timer toggle, the
   §0.9.2 free tier is stated as one rule: **1 timed run per month + 50
   untimed answers per day** (with full browse of all past papers, guides,
   and written questions always free).
4. **§VII.14 — Study Desk kept, focused, and split (resolved 22 Nov 2026).**
   Study Desk is **kept** — it is Finna's only private group-study space
   (§0.13 bans 1:1 DMs in favour of 6-seat invite-only rooms) and the
   learner's personal study binder. What changes is removing the duplicate
   *solo* surfaces that made `StudyDesk.tsx` 2,334 lines:
   - **Personal Desk** owns question-linked notes (`0114`, with PDF export),
     saved questions/bookmarks, and the Pomodoro focus timer. Remove its
     duplicate Today card, duplicate mastery strip, self-reported weekly
     target, and `DeskPractice`'s separate solo practice session store (solo
     practice links directly to `/practice`).
   - **Group Desk Rooms** keep all staged Desk v4 group features
     (`0111–0115`, Bundle B): shared weekly goal (`0111`), review circle
     (`0112`), synchronized room practice sessions (`0113`), question-note
     sharing (`0114`), room chat, and the room-filtered calendar view (`0115`).
   - **Code structure**: split `StudyDesk.tsx` (2,334 lines) into focused
     sub-components for personal binder/notes, focus timer, and group room tabs.

5. **§VII.6 / §VII.4 — No learner-facing "scorable" terminology or strict pool wall (resolved 22 Nov 2026).**
   The owner directed that "scorable" / strict official-key-only scoring
   terminology is too strict and must not be mentioned in learner-facing UI
   copy, filters, or guides. Backend `v_scorable` invariants remain intact for
   data integrity and auditability, while `/practice`, `/bank`, answer status
   notices, mock result summaries, and `/guides/using-finna` present clean
   learner wording (`All questions` / `With answers` / `Written answers`, and
   `Not verified` / `Answer disputed` without lecturing about "scored tests"
   or "verified official-key pool").

*Part VII (V.14–V.18) implemented 22 Nov 2026; see `DEVLOG.md` for live deployment and rehearsal receipts.*

---

## VII.18 The repeat loop — browse, test, return (owner request, 22 November 2026)

The owner asked for the whole site optimised around one person: an
aspirant who browses questions, makes tests, closes the app, opens it
again tomorrow, and does it again for months. Everything in this section
is written from inside that loop.

**Status: proposal. This is a follow-on to V.14–V.18, which shipped the
same day** — `/index`, `/guides`, the six-link header, the five phone
tabs, migrations 0135–0137 and the §VII.6.2 conflict work. Those phases
reduced the *surface*; this one fixes the *loop*, and none of it was
addressed by them. Migration `0138_fast_v_mock_practice` also closed
§VII.16.2 #3 independently, finding the predicted cost on the way:
`v_mock_practice` and `v_bank_answer_status` were materialising all 13k
rows of `v_scorable` and all 59k of `v_reviewed_answer_publications` at
**~4.7 s per derived answer click**, fixed by rewriting `id IN (…)` to a
correlated `EXISTS`. Every claim below was re-verified against the
post-V.18 code.

### VII.18.1 The loop, as the aspirant actually lives it

```
Day 1    open → LDC → Paper II 2018 → answer 30 → 11 wrong
Day 2    open → "what did I get wrong" → redo those 11 → 4 still wrong
Day 5    open → English, every exam → 50 questions → notice a repeat
Day 12   open → "I've seen this one three times and still miss it"
Week 20  full paper, timed, 2 hours
```

Three verbs, in this order of frequency: **return**, **browse**,
**test**. The product currently optimises the middle one and barely
acknowledges the other two.

The unit of the loop is **not the session, it is the question seen
again**. That is the lens for everything below: on the fourth encounter
with a question, what does the learner know that they did not know on
the first?

Today the answer is **nothing.** `QuestionCard.tsx` shows no personal
history at all — not "you've seen this", not "you got it wrong", not
"last seen on". The `Question` type in `web/src/lib/api.ts:57-59` carries
no per-user field, so the card could not show it even if someone wanted
to. The learner's own history with a question is invisible at the exact
moment it would change their behaviour.

### VII.18.2 Three signals that already exist and are dead

Before designing anything new: the three best signals for this loop are
already built, indexed, and in two cases wired all the way to the UI.
None of them works.

#### 1. `times_asked` — repeat frequency — is `1` on every row

`canonical_questions.times_asked / first_year / last_year` are real
columns (0002:121-123), maintained by `refresh_cq_counts()` (0002:222) as
`GREATEST(1, COUNT(DISTINCT COALESCE(p.sitting_id, p.id)))` — the number
of distinct past-paper sittings a question has appeared in, with booklet
series A/B/C/D correctly counted once. There is a dedicated index
(`idx_cq_times_asked`, 0002:147).

For an MPSC aspirant this is **the most valuable signal in the bank.**
Questions repeat across sittings; knowing which ones is most of the
strategy.

And it is dead. `web/src/components/FilterRail.tsx:93-96` says so in a
comment:

> Wired and correct, but matches nothing: every canonical question has
> exactly one appearance because the dedupe job has not run… Measured
> `max(times_asked) = 1`. Shown disabled rather than silently empty.

The consequences run through the whole product:

- the **"Asked N× · years"** pill (`QuestionCard.tsx:77-84`) never renders;
- the **"All N appearances ↗"** source link (`QuestionCard.tsx:58`) never renders;
- the `RepeatBadge` (`ProvenanceTag.tsx:11-18`) returns `null` below 2;
- the **"Repeats only"** filter is rendered permanently **disabled** (`FilterRail.tsx:100`);
- and worst — **`order=repeated` is the default sort on `/bank`**
  (`Bank.tsx:27`), labelled **"Most asked"** in a visible segmented
  control (`Bank.tsx:154-160`) and as **"Most repeated first"** in
  `QuestionStudyControls.tsx:7` and `ModuleStudy.tsx:144`. It resolves to
  `ORDER BY v.times_asked DESC, id` (`questions.py:351`), which with a
  constant column is `ORDER BY id`.

So the default ordering on the main browse screen is a **promise the
data cannot keep**, presented to every user, as the default, with a
human label. That is the single most misleading thing in the product.

**Running the dedupe job is therefore the highest-value item in this
entire section** — higher than any screen. It is not new work; it is
finishing work that is already wired at every layer. Until it runs:
change the default sort to `paper` and keep "Most asked" visibly
disabled next to the already-disabled repeats filter, for the same
honesty reason `FilterRail` gives.

#### 2. `v_question_stats` — real difficulty — is read by nothing

Migration `0003_attempt_stats.sql` creates two views:

- `v_question_stats` (0003:25) — per question: `attempts`, `correct`,
  `learners` (distinct users), `accuracy`;
- `v_option_picks` (0003:36) — per question per chosen option: `picks`,
  explicitly built for option vote-bars (0003:5-6).

Both are indexed (`idx_attempts_canonical`, 0003:19). `grep` across
`api/` and `web/src` returns **only the migration that creates them**.
Zero API reads. Zero UI reads. They have been dead since migration 0003.

The migration's own comment (0003:11-15) states the case better than
this section can:

> It also gives real difficulty, which the bank does not have:
> `difficulty` is NULL on every row… Difficulty measured from actual
> answer rates is the only honest version of that field.

`difficulty` is separately retired as a label (`schemas.py:44-45`,
`CLAUDE.md`). So the product threw away the dishonest difficulty signal
and never turned on the honest one sitting next to it.

**Use it, under §0.8's honesty rules.** Surface accuracy only above a
learner threshold (the discovery service already uses `participants >= 5`,
`services/discovery.py:95`), never as a predicted difficulty label,
always as observed fact: *"38% of learners pick C"*. The option
pick-bars are the strongest revision affordance in the whole design —
after answering, seeing that your wrong option is the one most people
pick tells you *why* you were wrong, which no explanation does as
quickly.

#### 3. `user_question_bookmarks` — a finished feature with no website

The table exists (0082:23-29), with a recency index. Full CRUD exists —
`GET/PUT/DELETE /api/mobile/bookmarks[/{qid}]` (`mobile.py:133-159`),
capability-gated, retention-handled (0133:30). The **mobile app uses it**
(`library.tsx` Saved segment).

The website has **no UI and no API wrapper** — `grep "mobile/bookmarks"
web/src` is empty. Instead the web Save button
(`PracticeAnswerPanel.tsx:96`) writes to a client-side desk JSON
document capped at 500 items (`:71`), and its confirmation toast links to
`/desk?tab=bookmarks` (`:108`) — **a tab that `StudyDesk.tsx:94` filters
out when there is no room id**, i.e. for every solo user.

So on the web, "Save for revision" saves into a different store from the
app and then links to a tab that does not exist. For a product whose
core loop is *come back to this question later*, that is the most
consequential broken path in the build.

### VII.18.3 The question card — the one surface that must change

Everything in the loop passes through this card. It gets one new block,
above the options, visible before answering:

```
┌────────────────────────────────────────────────────────┐
│ Polity · Fundamental Rights          LDC 2018 · Paper I│
│                                                        │
│ ● Seen 3× · wrong twice · last 5 days ago    [Saved ★] │   ← new
│ ● Asked in 4 sittings · 2013, 2016, 2018, 2021         │   ← dead today
│                                                        │
│ Which of the following…                                │
│  A ○ …          B ○ …                                  │
│  C ○ …          D ○ …                                  │
└────────────────────────────────────────────────────────┘
after answering:  38% of learners pick C          ← v_question_stats
```

Rules:

- **Personal history is one line, never a panel.** Seen count, wrong
  count, recency in days. Absent on first encounter — a first-time
  question shows nothing, which is also how the learner recognises one.
- **It is a filter, not just a label.** Tapping *"wrong twice"* opens
  browse filtered to the learner's twice-wrong questions. Every count in
  this product should be a link to the set it counts.
- **Option pick-bars appear only after answering**, only above the
  learner threshold, and only as observed percentages.
- Personal history is **never shown to guests** and never cached shared
  (§IV.2's `private, no-store` rule).

**API change**: `Question` gains an optional `history` object —
`{seen, wrong, last_seen_at, saved}` — populated only for an
authenticated request. The indexes exist
(`attempts_user_question_latest`, 0051:76; `idx_attempts_user_cq`,
0002:315), so this is a join, not a scan. It must be measured against
§VII.16's bar before it ships on a 25-item page.

### VII.18.4 Browse — one exam, or one subject, and nothing else

This resolves the owner's question: *should the bank be hidden and only
modules shown?*

**No — but the bank stops being a destination.** The schema already
settles it. A module is a **saved query**, not a separate corpus:

```sql
collection_sections.query JSONB
  -- {"subject":"gk","topic":"polity","year_gte":2016,"times_asked_gte":2}
```

and `routers/collections.py:53-56` already resolves a section from
`subject_id`/`topic_id` **with no `paper_ids` at all**. The six exam
modules of migration 0011 merely happen to be defined by paper lists.
`collections.kind` already allows `'exam' | 'guide' | 'tool' |
'practice'`.

So:

| Surface | What it is | Cost |
| --- | --- | --- |
| **Exam modules** — LDC, UDC, Assistant, Prelims, Group B ×2 | saved query by paper list | exists |
| **Subject modules** — English, Arithmetic, Reasoning, Polity, Mizo | saved query by `subject_id` | **one row + one section each** |
| **The bank** | the substrate both read from | reachable, never advertised |

The owner's concern — *"people will be interested in the whole english
maths arithmetic"* — is not an argument for keeping a raw bank link. It
is an argument for **subject modules**, which are more useful than the
raw bank (English spans every exam a learner will never think to filter
for) and cost no new schema, no new screen and no new progress system:
`module_learning_progress` (0026) and `exam_study_checkpoints` (0034)
already key off `collection_id`.

**What changes:**

1. `/bank` loses its nav entry. It is reached *from* a subject, an exam,
   a search or a guide chapter — never as a landing page. The 82,383-row
   firehose was never a product.
2. `/subjects/:id` becomes a peer of `/exams/:id`, same layout, same
   tabs, same progress.
3. The phone **Library** tab becomes **Subjects** (it currently hides 18
   unrelated destinations under one word, §VII.14).

#### The filter problem is a data problem

**58,370 of 82,249 questions have an approved subject but no topic** —
71% (`QUESTION-TAGGING-RULES.md` §7; 4,557 of them English). So the one
filter that would narrow a subject to something workable is empty for
seven questions in ten. No amount of filter UI fixes that.

Three changes, in order:

1. **Facet counts on every value, everywhere.** Never offer a filter
   that returns zero. This is the single biggest browse improvement
   available and it makes the coverage gap visible instead of
   frustrating. It is also how the dead `times_asked` filter would have
   announced itself years ago.
2. **Cut the default filter set from ten to four**: exam/paper, subject,
   year, and **your status**. Topic appears only where coverage exists.
   `source` goes staff-only (§VII.6). `pool`, `order`, `collection_id`
   and `seed` leave the visible surface.
3. **"Your status" is a first-class filter on `/bank`, which it is not
   today.** The API has supported `study_status ∈ all | unseen |
   answered | wrong | ever_wrong` since `schemas.py:340`, and
   `ModuleStudy.tsx:127`, the mobile browse pills
   (`questions.tsx:536-545`) and QuickFind all expose it —
   **`Bank.tsx` has no `study_status` at all.** The main browse screen
   cannot filter to the learner's own wrong answers. That is the loop's
   central query, missing from its central screen.

**Default `ever_wrong`, not `wrong`.** `me.py:358-378` gates mistakes on
the *latest* attempt being wrong, and `Mistakes.tsx:8-10` says so
explicitly. A question missed three times and then guessed right once
vanishes from revision. For a product built on repetition that is
precisely backwards: `ever_wrong` (`questions.py:267`) is the honest
default and the column is already there.

### VII.18.5 Tests and subject focus

§VII.4 merges practice and mock into `/practice`; §VII.10 makes one
builder. This section adds the two things the loop needs from them:

- **Build a test from any filtered set, in one tap.** The selection tray
  (§VII.10.2) gains a shortcut: whatever the current filter produces —
  *my twice-wrong English questions*, *LDC Paper II 2018*, *this guide
  chapter* — becomes a test without selecting individually. "Test these
  34" is the fastest path from browsing to testing, and browsing to
  testing is the loop.
- **Subject focus already exists and is nearly invisible.**
  `user_focus_subjects` (0092:23) caps at 5, `/me/focus-subjects` is
  live, and `Revise.tsx:32` exposes it as a single checkbox labelled
  "Focus subjects only". Promote it: focus subjects shape Home's Today,
  the default subject module order, and the review queue. One setting,
  three effects, no new table.

**Mocks keep their immutability** (frozen snapshots, 0031) and `v_scorable`
composition. Nothing in this section touches scoring.

### VII.18.6 Return — what the app owes you when you open it again

This is the most under-built verb and the cheapest to fix, because the
data is all there.

`GET /api/learning/resume` (`routers/learning.py:55-85`) already
aggregates **five** resume sources: an unsubmitted mock with
`current_position` and remaining minutes, a practice checkpoint
(`learning_checkpoints`, 0051:10), an unanswered vocabulary card, a
running focus session, and the first undone desk task. Exam browse state
— section, paper, query, pool, order, subject, offset — is separately
preserved per collection in `exam_study_checkpoints` (0034:50).

**It is displayed in exactly one place**: `StudyHome.tsx:29` picks *one*
item via `items.find(...)` and renders it. `/revise` shows nothing.
`/bank` shows nothing. The mobile app shows nothing of it.

What a return should look like, on both web Home and the phone Home tab,
above everything else:

```
Welcome back
  ▸ Continue — LDC Paper II 2018, question 31 of 50
  ▸ 14 reviews due today                    [Start]
  ▸ 11 questions you've missed twice        [Test these]
```

Three rows, all from existing endpoints (`/learning/resume`,
`/me/review-queue`, a `HAVING count(*)>=2` variant of the shape already
written at `study_desks.py:346`). No new table. If a row has no honest
content it is absent — never "0 reviews due" styled as an achievement,
never an invented streak.

**The review queue is already correct and should not be redesigned.**
`services/review_queue.py` is a dated Leitner system — intervals
`(1,3,7,16,35)` (`:4`), wrong resets to box 1, box 5 correct graduates to
`due_on = NULL`, only official/key snapshots count (`:36`), guests
excluded, and a key correction can reset a wrong schedule but never
grant a promotion (`reconcile()`, `:113`). That is a well-built spaced
repetition engine. The gap is not the engine; it is that the learner
meets it only by navigating to `/revise` and choosing a tab.

### VII.18.7 Saved — one store, one button, one list

Pick `user_question_bookmarks` and delete the alternative.

1. Add the four endpoints to the **web** API wrapper. They exist
   (`mobile.py:133-159`); only the capability gate needs widening.
2. `PracticeAnswerPanel`'s Save button writes there instead of the desk
   JSON doc, removing the 500-item client cap.
3. Saved questions appear in **one** place — the Subjects/Library "Saved"
   list — matching the mobile app's existing Saved segment. The toast
   stops linking to a tab that solo users cannot see.
4. Migrate existing desk-document saves once, then stop writing them.

This also closes a real web/app divergence: today a question saved on
the phone is invisible on the laptop and vice versa, in a product whose
whole premise is returning to the same questions.

### VII.18.8 Layout and arrangement — web and phone, one design

Applying §VII.1's layout contract and §VII.2's type scale to the loop:

**Home (web `/home`, phone Home tab)** — in order, nothing else:
1. Return block (§VII.18.6) — three rows maximum.
2. Today: one plan, from `daily_learning_plans`.
3. Your exam: coverage bar, next paper, one weak topic from
   `user_topic_mastery`.
4. Subjects row: your focus subjects (§VII.18.5), then the rest.

No footer link grid — that is `/index` (§VII.3.2). No stats tiles. On a
390px phone the return block must be fully visible without scrolling;
it is the reason the app was opened.

**Browse (`/exams/:id`, `/subjects/:id`, both)** — identical layout:
one hero, one tab row (`Overview · Browse · Papers · Practice`), one
filter card as an explicit grid with native selects and facet counts,
one result line, one card list, infinite scroll with a visible "Show
more" fallback. This is `combined-prelims.css`'s structure, which is
89 flat lines and the owner's named reference.

**Question card** — §VII.18.3, identical on web and phone. The phone
version already shows `Asked N×` vs `Asked once`
(`mobile QuestionCard.tsx:134-147`), so the two converge rather than
diverge.

**Practice runner** — one question, full width, options at 46px minimum
touch height, the answer panel in place rather than a sheet. After
answering: correct/wrong, option pick-bars, explanation, **Save**,
**Next**. Nothing else on screen.

**Phone tabs stay at five** (§12.5's freeze). V.14 shipped
**Home · Exams · Guides · Desk · Me**, which is already a large
improvement on the old Library tab. One further change is proposed and
it is the last one this part asks for: **Desk → Practice**.

The reasoning is frequency, not preference. §VII.17's owner decision
keeps the Desk — correctly, it is the only private group-study space and
the personal binder — but a toolbox is opened *occasionally*, and
`/practice` is the loop's daily verb. A tab is the scarcest real estate
in the product and should be allocated by how often a thing is opened.
Desk moves under Me, where the mobile app already routes several
destinations. If the owner would rather keep Desk on the bar, the
alternative is Guides → Practice, since guides are read in long sessions
and reached from subjects anyway — but one of the five must be
`/practice`.

**Mobile app specifics.** The app has 47 real screens and no stubs; in
several places it is *ahead* of the web (bookmarks UI, study-status
pills in browse, `Asked N×` on the card). Three cleanups it needs on its
own terms:

- `expo-sqlite` is a declared dependency and config plugin with **zero
  usages in `src/`** — remove it, or use it for the offline leg §0.12
  point 2 says is the app's only justification for existing.
- `@expo-google-fonts/ibm-plex-mono`, `newsreader` and `public-sans` are
  installed and unreferenced, and `fonts.mono` silently aliases
  `Figtree_700Bold` (`theme/index.tsx:73`). The same three phantom
  families haunt the web (§VII.2). Delete them in both places in the
  same change.
- Spacing is literal per component (`ui.tsx`) with no numeric scale.
  Adopt §VII.2.3's eight sizes and a 4px spacing scale so the two
  clients stop drifting.

The app is **not** getting guides (§VII.12.3) and is not chasing
parity — but the question card, the return block and the saved store are
exactly the three places where divergence hurts the loop, and all three
converge here.

### VII.18.9 Admin — the flow that keeps the loop honest

§VII.11 specifies the keyboard-first editor. This section adds what the
loop demands of it, because the aspirant's experience degrades from
exactly three admin failures:

1. **Untagged questions** — 71% have no topic, so subject modules are
   coarse and topic mastery is thin. The console's queue is already
   designed for this; the §VII.7 currency fields and the topic live in
   the same form, so one pass sets both.
2. **Wrong answers that nobody flagged** — §VII.6.2's conflict queue.
3. **A learner's report going nowhere** — `content_reports.kind='outdated'`
   currently routes to an `kind='explanation'` correction and dead-ends
   (§VII.7.4).

Three additions to the console, all small:

- **The report inbox is the queue's first tab.** A question a learner
  flagged, ordered by how many learners hit it, is worth ten untagged
  questions nobody has opened. Exposure ranking (§VII.6.3 step 4) sorts
  every admin queue in this product.
- **`.` repeats the last tag**, and the queue is paper-ordered by
  default, because a run of questions from one paper almost always
  shares a subject. This is the single biggest keystroke saving
  available.
- **One-tap "fix and next" from a question's own page.** An owner who
  spots a typo while browsing as a learner should correct it without
  navigating to the console — the same `routine-edits` call, triggered
  from the card, with the console's prefetch already holding the hashes.

Everything else in §VII.11 stands: no guard removed, no SQL-only path,
20-target bulk cap, full audit.

### VII.18.10 Order

Strictly by value per unit of work.

| # | Item | Why first |
| --- | --- | --- |
| 1 | **Run the dedupe job** (§VII.18.2 #1) | Turns on repeat frequency across six already-built surfaces. Until then, stop defaulting to a sort that cannot work. |
| 2 | **`study_status` on `/bank`, defaulting `ever_wrong`** | The loop's central query, missing from its central screen. One param. |
| 3 | **The return block** (§VII.18.6) | Five resume sources already aggregated; one of them displayed, in one place. |
| 4 | **Personal history on the card** (§VII.18.3) | The loop's core gap. Needs an API field and a §VII.16 measurement. |
| 5 | **One saved store** (§VII.18.7) | Fixes a broken path and a web/app split. Endpoints exist. |
| 6 | **Subject modules** (§VII.18.4) | Rows, not code. Answers the owner's English/maths concern directly. |
| 7 | **Facet counts, filters ten → four** | Makes browse usable at 82k. |
| 8 | **`v_question_stats` pick-bars** (§VII.18.2 #2) | Dead since 0003. Threshold-gated, honest, high revision value. |
| 9 | **Layout and type** (§VII.18.8) | Ships with V.14. |
| 10 | **Topic coverage campaign** | Long, continuous, through §VII.11's console. |

Items 1–3 are days, not weeks, and together they change the loop more
than everything after them.

**Tests**: a returning learner sees their position, their due reviews
and their repeated mistakes without navigating; a question seen before
says so; `/bank` can produce "my twice-wrong English questions" and turn
it into a test in one tap; a question saved on the phone appears on the
web.

**Done when**: `max(times_asked) > 1`, and no surface in the product
promises a signal its data cannot supply.

