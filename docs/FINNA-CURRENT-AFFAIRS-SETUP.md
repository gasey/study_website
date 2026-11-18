# Current-affairs collection and free-provider setup

## Installed behavior — 16 November 2026

The website owner workspace, `/current-affairs/automation`, has Official sources
and YouTube videos tabs, plus daily/weekly briefs. RBI press releases and
notifications, PIB national releases and Mizoram DIPR public pages collect on the
existing six-hour worker timer. Captured source passages and all revisions stay
private. Collection needs no account/API key. Empty or malformed feeds do not
become successful freshness claims. A rejected oversized/empty release is logged
without discarding other valid releases from that feed.

Gemini text drafting, direct public YouTube video analysis and Supadata native
captions are integrated but **disabled/awaiting keys**, at the owner's request.
No live Gemini/Supadata generation or quality test has been performed. All three
adapters have mocked protocol, validation and failure-path tests. Actual model
accuracy and account availability must be checked after keys are configured.
OpenCode remains an optional explicitly free-model provider; no subscription,
credit purchase or paid fallback is required or enabled.

PIB and DIPR use fixed official listing/article URLs, bounded public-page requests
and structure checks. No search API key is needed. PIB's previously empty RSS is
not used. Each page collector inspects at most eight unique releases per run;
article failures retain other successful captures and appear in private audit.
Publication timestamps without a zone explicitly record the Asia/Kolkata assumption.
DIPR article language is stored as unknown rather than guessing from the site's
English HTML label; preserve and review Mizo wording and names during translation.

Daily and rolling seven-day brief packets collect automatically, even without
AI keys. Their publication-date windows use Asia/Kolkata. A packet considers the
newest 100 official releases and 30 captured videos in that window, ranks them
using visible exam-topic keywords and deprioritizes recognized routine releases.
It selects at most eight complete sources / 80,000 source-text characters and
shows omissions. Substantial exact duplicate prose across sources combines
citations; short table values and repeated same-source passages retain context.
This triage is not a validated relevance classifier or complete news coverage.

With free generation configured, the worker proposes semantic claim grouping,
conflict warnings and supported quiz/card candidates from that bounded evidence.
The draft remains pending review. Daily/weekly jobs share the rolling call budget
with individual video/release drafts; a reserved job slot and oldest-generation
ordering keep briefs from starving. Identical packets are idempotent, changes
create new immutable inputs, and handoff rechecks every underlying source hash,
even before the next packet refresh. Private CMS notes retain source links and
passage/time references. MCQs/cards remain private candidates.

GDELT and Akashvani remain optional research candidates. There is no full-news
coverage claim or automatic publication. Actual semantic grouping and translation
quality cannot be established by synthetic tests; check them after keys exist.

## Configure privately when ready

Use the existing root-owned `/etc/mpsc/youtube-current-affairs.env`, mode 0600,
with `sudoedit`. Never put real keys in the repository, frontend or chat. The API
process does not receive these keys: the worker reads them on each invocation.
The website shows safe configuration metadata from the latest completed run.

For Gemini, create a project/key in [Google AI Studio](https://aistudio.google.com/api-keys)
and keep that project on the **Free tier with billing disabled**. Then configure:

```ini
CA_LLM_PROVIDER=gemini
CA_GEMINI_API_KEY=YOUR_PRIVATE_KEY
CA_GEMINI_MODEL=gemini-3.8-flash
CA_GEMINI_FREE_PROJECT=1
CA_GENERATION_ENABLED=1
CA_SOURCE_GENERATION_ENABLED=1
CA_DAILY_CALL_LIMIT=6
CA_BRIEFS_ENABLED=1
```

`CA_GEMINI_FREE_PROJECT=1` is the operator's confirmation of the billing-disabled
project. The Gemini inference key does not let this app independently inspect
Google Cloud billing status. Do not set this flag on a billing-enabled project.
Only the checked free-model ID is accepted by this release. Free availability can
change; a quota/access error queues a later retry, never a paid fallback. This
free tier is intended here for public source content, not private learner records.

For Supadata, create its [Free account](https://supadata.ai/pricing), with no paid
plan or auto-recharge, and add:

```ini
CA_CAPTION_PROVIDER=supadata
CA_SUPADATA_API_KEY=YOUR_PRIVATE_KEY
CA_SUPADATA_MONTHLY_LIMIT=90
CA_VIDEO_INPUT=captions
```

Before a native-caption request the adapter calls `/v1/me` and rejects any plan
other than `Free`. It requires remaining provider credits and reserves one local
credit before requesting `/v1/transcript` with **mode=native, text=false**. No
`auto`/`generate` mode, transcription job polling or paid upgrade is attempted.
Supadata currently grants 100 free credits/month; native unavailable/failed
requests can consume allowance. The local UTC calendar-month budget is a
conservative guard, not a replacement for the provider's billing-period counter.
The actual provider balance is checked as well. Caption origin is stored as
unknown when the API does not report automatic versus manual; it is never guessed.

To try Gemini's direct public-video input instead of collecting a missing caption
track, configure `CA_VIDEO_INPUT=gemini_url` with Gemini generation enabled. The
worker uses the stateless Interactions API, a fixed YouTube URL and explicit free
model. This path creates **model-produced video evidence**, not a downloaded
caption track. Its timestamps/claims need inspection. Existing captured captions
continue to use text drafting unless a source retry is explicitly queued. Preview
availability and video/token/request caps may change.

For OpenCode-only generation instead, select `CA_LLM_PROVIDER=opencode` and enable
`CA_GENERATION_ENABLED=1`. The existing allowlist accepts only its two supported
free model IDs. Supadata is independent of that choice. Keep the Gemini and
Supadata keys absent until choosing those providers. There is no automatic
provider failover, credential/account rotation or subscription escalation.

## First live verification after key configuration

Run the existing service once and inspect the owner workspace and its journal:

```sh
sudo systemctl start ism-youtube-current-affairs.service
sudo journalctl -u ism-youtube-current-affairs.service -n 30 --no-pager
sudo systemctl list-timers ism-youtube-current-affairs.timer
```

A partial run exits nonzero so quota/source failures remain visible; its timer
continues on schedule. Wait for a running worker before starting another. The
shared advisory lock and rolling six-attempt budget cover both video and official
source generation, including failed calls and repairs. When official generation
is enabled, one job slot is reserved for releases so a video backlog does not
starve them. No API process restart is needed merely to change worker settings.

Use the saved supplied video transcript as the first quality test. Check names,
figures, reporting/effective dates, evidence references, proposed answers and
translation against the actual source before any publication. Synthetic tests
establish protocol/validation behavior only. Official-source paragraphs preserve
source order; RBI dates without timezone are normalized as Asia/Kolkata with that
assumption explicitly displayed and audited.

## Review and integrity

Only owners can inspect these queues; existing session/MFA/CSRF policies apply.
Answer-bearing source/draft inspection and notes handoff are withheld during
active mocks/games/cup release windows. Mobile learner credentials cannot call
these admin endpoints. Private responses use `no-store`; account switches clear
private UI data. Feed controls allow only the four fixed approved official sources.

Generated facts reference captured source paragraphs/cues. Handoff creates one
private CMS notes draft, with source identity/model attribution and an unverified
warning, never a published revision. A changed source blocks stale pending-draft
handoff; old evidence and drafts remain retained. Proposed MCQs/cards stay
private candidates and do not modify the question bank, historical keys or scoring.

Migration 0086 adds separate immutable source evidence/audit tables, a caption
request budget and generic generation targets. Existing caption origins can be
unknown and video evidence has an explicit kind. It does not rewrite 0085 or bank
content. The bounded initial release is `scripts/deploy.sh current-affairs-free`,
with exact source preimages, production dump-clone rehearsal, atomic migration
checksum, source/config backups, bank fingerprints and both-site health checks.
Migration 0087 explicitly replaces production's broader default table grants:
the runtime role can select/append evidence and audit records, but cannot update,
delete or truncate them. Its rehearsal restored production ACLs as well as data;
the initial 0086 rehearsal omitted ACLs and did not expose that default-grant
behavior. Production permissions were corrected and independently checked before
handoff; a fresh worker run exercised collection under the restricted role.
It must not be replayed over a newer release. Any recovery preserves additive
DDL, the 0087 grants, immutable evidence and the migration ledger, while restoring only this
feature's exact source/config backup through a fresh bounded update.

Implementation/verification receipts:
`reports/current-affairs-free-release-20261116/` and
`reports/current-affairs-plan-completion-20261116/`.

Migration 0088 adds the page-source IDs, original-language metadata and private
brief/input/draft tables. It explicitly revokes inherited broad grants: packet
inputs cannot be rewritten by the runtime role; generated draft payloads permit
only status/material-ID updates. The bounded initial command is
`scripts/deploy.sh current-affairs-briefs`, with an ACL-preserving production-clone
rehearsal and frozen source preimages. Never replay over a newer release. Recovery
retains additive DDL, evidence, ledger and restricted grants. If restoring the old
router/worker, keep the compatible new source mapping/page adapter and pause the
new page feeds; the previous router needs that mapping to list the new feed rows.
