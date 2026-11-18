# YouTube current-affairs preparation

The 16 November free-provider/official-source extension is documented in
[FINNA-CURRENT-AFFAIRS-SETUP.md](FINNA-CURRENT-AFFAIRS-SETUP.md). The original
0085 release below remains historical context; current worker behavior includes
RBI collection, explicit video-evidence kinds and free-project/provider guards.

Finna prepares private study drafts from available public YouTube captions. The
owner workspace is `/current-affairs/automation` on the website. Nothing from this
pipeline becomes a learner fact, scored question or public material automatically.

## Reference and implementation

The working references were the two supplied local guides in Downloads:
`Current_Affairs_Automation_Guide.md` and `Current_Affairs_Quiz_Build_Guide.md`.
The exact “Claude Fable” handoff filename/provenance was not established. The old
`india-study-map/HANDS-OFF.md` describes a different historical news pipeline.
These documents are references, not authority to import their generated examples,
expose answer JSON, replace infrastructure or publish unattended. The existing
Finna API, PostgreSQL, content studio and source/publication rules take precedence.
The 14 November Finna design supplies the current screen tokens.

## Flow

1. An owner registers a channel ID and allowed caption languages in the website.
2. A systemd timer polls its public Atom feed every six hours. Feed discovery is
   recent uploads only, not a complete historical channel backfill. Title changes
   update the queued title, but do not silently replace captured source evidence.
3. At most three due videos per run attempt caption collection, prioritizing recent publication dates. The downloader is
   pinned `yt-dlp==2026.7.4`, skips media, ignores personal config/cache and uses no
   cookies, login, proxies or challenge bypass. Source errors remain visible.
4. Timestamped JSON3 captions are normalized and saved with a SHA256 identity,
   language, automatic/manual attribution, retrieval time and collection method.
   Repeated rolling captions are deduplicated only when their time windows overlap.
   Repeated words later in a video are retained. Oversized input is rejected,
   rather than silently truncated.
5. If configured, the model receives title/date and the exact transcript cues.
   A private tool-denied OpenCode process uses an explicitly allowed free model.
   Optional Gemini uses a private server key and an explicitly configured model.
   There is no automatic provider or paid-model fallback.
6. JSON validation checks lengths, distinct options, answer index, duplicate
   questions and cue/fact references. One invalid-JSON repair attempt is permitted.
   Validation establishes structure and traceability, not factual correctness.
7. A unique source-hash + prompt-version + model binding stages a private draft.
   The owner can inspect facts, proposed MCQs/cards, warnings and timestamp links,
   reject it, or create one idempotent private content-studio notes draft.
   MCQs/cards remain private pipeline candidates. Source-checking, assessment
   authoring and learner publication still require their existing workflows.

A publication timestamp is not a fact's event date or reporting period. Hindi
speech recognition/translation can confuse names and figures. The model prompt
preserves uncertainty and permits fewer questions or empty lists rather than padding.

## OpenCode and cost controls

Owner clarification, 16 November: OpenCode must remain free-only, with no future
subscription or paid upgrade. Other free providers and content feeds were researched
in [FINNA-CURRENT-AFFAIRS-FREE-APIS.md](FINNA-CURRENT-AFFAIRS-FREE-APIS.md). They are
recommendations, not newly configured live providers.

OpenCode is the CLI runner; the selected model performs generation. This adapter
uses OpenCode 2.0.32. Supported names are explicitly restricted to:

- `opencode/deepseek-v4.1-flash-free` (configured initial model)
- `opencode/glm-5.3-flash-free` (optional explicit operator selection)

The official model documentation describes free offers as time-limited and
requiring OpenCode. Availability and quotas can change. Model existence is not a
promise of future free capacity or transcript quality. An unrecognized/paid model
name fails configuration rather than falling through to another model. Free quota
errors (429) enter `quota_wait` for at least six hours and stop the current batch; a request does not buy credits.
The rolling 24-hour limit defaults to six generation attempts and is capped at 20.
Both failed attempts and JSON repairs consume this ledger budget. OpenCode may make
auxiliary requests within a CLI attempt; the UI accurately labels attempts rather
than claiming an exact provider request/token count.

The first real local test on the supplied public video reached OpenCode but was
refused with `provider.quota`, HTTP 429, “Free usage limit reached.” No successful
model output or quality assessment should be inferred from the synthetic tests.

## Server operation

- API: `/srv/api/app/routers/youtube_current_affairs.py` and its service helper.
- Worker: `/srv/api/youtube-current-affairs.py`, using `/srv/api/.venv/bin/python`.
- Units: `ism-youtube-current-affairs.service` and `.timer`.
- Schedule: 00:30, 06:30, 12:30 and 18:30 Asia/Kolkata; up to ten minutes jitter,
  with catch-up after downtime. No exact minute delivery promise.
- Private settings: `/etc/mpsc/youtube-current-affairs.env` (root, mode 0600).
- Database identity: existing `/etc/mpsc/db.env`; explicit `PGDATABASE=mpsc` is
  required when the role's default DB differs. Do not print credential files.
- OpenCode ARM binary: `/opt/finna-opencode/2.0.32/opencode`, verified against the
  official npm package's SHA512 integrity and recorded binary SHA256.
- CLI state: isolated `/var/lib/finna-youtube-current-affairs`, mode 0700,
  `XDG_CONFIG_HOME`, `XDG_DATA_HOME`, `XDG_CACHE_HOME`, `XDG_STATE_HOME`. This
  installation does not inherit a staff member's interactive OpenCode sessions.

Initial free-only configuration:

```ini
CA_LLM_PROVIDER=opencode
CA_GENERATION_ENABLED=1
CA_OPENCODE_MODEL=opencode/deepseek-v4.1-flash-free
CA_OPENCODE_BIN=/opt/finna-opencode/2.0.32/opencode
CA_DAILY_CALL_LIMIT=6
```

To pause generation, set `CA_GENERATION_ENABLED=0`; captions still collect.
Pause individual channels in the owner screen. Disable the timer to pause all
scheduled work. Settings take effect at the next worker invocation; the website
shows configuration from the latest completed run, never private keys.

An optional Gemini setup needs `CA_LLM_PROVIDER=gemini`, `CA_GEMINI_MODEL`, and
`CA_GEMINI_API_KEY`. Select a current supported free-tier model and a project with
billing disabled if zero spend is required. This adapter does not itself enforce
Google account billing policy. No Gemini key was configured by this release.

Inspect with `systemctl status ism-youtube-current-affairs.timer` and
`journalctl -u ism-youtube-current-affairs.service`. A partial run exits nonzero so
source/provider failures remain visible. Timer invocations continue on schedule.
There is no email/Telegram notification integration in this release.

### Supplied captions and backfill

An operator can supply a source file when captions are obtained legitimately
elsewhere. Keep raw metadata/captions private; downloader metadata may contain
transient signed URLs. Record the true method and caption type:

```text
youtube-current-affairs.py --metadata-file /private/minimal-video-metadata.json
youtube-current-affairs.py --video VIDEO_ID --transcript-json3 /private/captions.json3 --language hi --automatic
```

Use the same service identity/environment as the scheduled worker. Metadata
requires ID, channel ID/title, video title and timestamp or upload date. A missing
precise timestamp is recorded as day precision. Reimporting the same normalized
transcript preserves the original immutable source record. Generated-file import
also requires an existing transcript and accurate `--model` attribution; it only
stages validated private JSON and never publishes.

YouTube's official caption-download API requires permission to edit the video;
a general YouTube API key does not unlock arbitrary third-party transcripts.
Public caption collection can be denied by YouTube on cloud server IPs. In that
case the state remains `transcript_pending`; do not claim fully unattended
operation, evade the denial or generate from the title alone.

## Access and data boundaries

All automation API routes require the existing owner session and staff policy.
Mutations require CSRF and use bounded request bodies. Private responses are
`no-store`. The learner/mobile endpoint allowlist does not include these routes.
Transcript/draft answer inspection and notes handoff are withheld during active
mocks/games/cup answer-release windows. UI payloads clear on account changes.

Migration 0085 creates separate workflow tables only. Runtime grants allow source
and audit inserts/reads but prohibit modifying/deleting those records. Existing
question/options/answers, provenance, attempts and scoring are not written here.
Generated notes are handed to `materials` as drafts with no published revision.
Model attribution and the explicit absence of source verification stay in audit.

## Deployment and recovery

`bash scripts/deploy.sh youtube-current-affairs` is the **initial frozen release**.
It checks the exact remote entry-point preimage, requires new feature files/units,
rehearses the additive migration on a disposable production dump clone, checks
immutable grants and question/answer fingerprints, records the migration checksum
atomically, backs up the entry point, installs only this feature and checks both
study and family sites. It deliberately excludes unrelated local API edits and
unapplied migration 0083. Frontend builds use `scripts/deploy.sh web` locally.

After initial installation, prepare a fresh bounded update; never change the frozen
preimage to silence a rejection or replay its DDL. On failure source rollback
retains additive tables/migration evidence. To recover after a successful release,
stop/disable this feature's units, restore the recorded source backup as part of a
fresh preimage-checked update, remove only this feature's router registration, then
restart/check the API and both sites. Keep workflow evidence and applied migration
checksums. Do not rewrite Caddy, bank data or unrelated timers.

Evidence is in `reports/youtube-current-affairs-20261115/`.

## Primary references

- [OpenCode free models](https://opencode.ai/docs/console/models/#free-models)
- [OpenCode automation and private servers](https://opencode.ai/docs/cli/)
- [OpenCode configuration schema](https://opencode.ai/config.json)
- [YouTube caption-download permission](https://developers.google.com/youtube/v3/docs/captions/download)
- [YouTube channel feed identifiers](https://developers.google.com/youtube/v3/guides/push_notifications)
- [yt-dlp subtitle options](https://github.com/yt-dlp/yt-dlp#subtitle-options)
