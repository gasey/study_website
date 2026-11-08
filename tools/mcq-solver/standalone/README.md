# Personal MCQ Solver

A Python 3.11+ command-line worker for private, controlled multiple-choice
question solving. It reads a local question-bank snapshot and keeps proposed
solutions in a separate SQLite review queue. Initial runs are limited to five
questions, processed one at a time.

Prepared under the MIT license for owner review. This package contains no
question content, credentials or application server. Real hosted inference
requires separately established eligibility and explicit OAuth consent.

## Install

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
.venv/bin/python -m pip install --no-deps -e .
.venv/bin/python -m unittest discover -s tests -v
```

No paid API-key adapter exists. The worker ignores API-key environment variables
and never imports another application's tokens or browser session cookies.

## Input format

Supply a private JSON snapshot with `papers` and `questions` arrays, optionally
`figureGroups` and `passageGroups` dictionaries. A question needs `id`, `paperId`,
`type: "mcq"`, `question` and an ordered array of nonempty `options` strings.
`answerIndex` is zero-based; null or legacy -1 means unknown. Optional context
includes `qnum`, `page`, `direction`, `passage`, `subject`, `topic`, source markup
and media references. Published keys and explanations are never modified.

`sync` selects complete unanswered or flagged MCQs in source order. This is not a
stratified accuracy evaluation. Missing diagrams and source/key flags always
require review. Existing keys and explanations are excluded from blind prompts.
Full source/key/media metadata is hashed to invalidate stale proposals.

## Inspect without inference

```bash
.venv/bin/mcq-solver --bank /private/bank.json doctor
.venv/bin/mcq-solver --bank /private/bank.json sync --dry-run --limit 5
.venv/bin/mcq-solver --bank /private/bank.json export-packet \
  --out /private/blind-packet.json --limit 5
```

The default queue is `~/.local/share/mcq-solver`. Credentials belong under
`~/.config/mcq-solver/credentials`, separate from the repository. Files are
private to the runtime user. `--state-dir`, `--credentials-dir`, `--config`,
`--bank` and `--model` are global options and precede the command.

## Sign in with ChatGPT

Read the current [official eligibility documentation](https://developers.openai.com/siwc/token-sharing-open-source)
for the actual application and hosting arrangement. A config flag, license or
successful test does not establish account entitlement or integration approval.
Keep `eligibility = "unconfirmed"` until the basis is established. A remotely
hosted/paid service may require OpenAI approval. This tool is not a public
inference proxy and supplies no endpoint for site visitors.

Copy `config.example.toml` to `~/.config/mcq-solver/config.toml`. After verifying
eligibility, record `oss_self_hosted` or `openai_authorized` and a substantive
`eligibility_evidence` reference. Then explicitly approve plan sharing in the
browser on the local computer:

```bash
.venv/bin/mcq-solver login --approve-plan-sharing
```

This opens the system browser and receives OAuth on `127.0.0.1`. The flow uses
PKCE, state and nonce, verifies the ID token against OpenAI's published keys,
retains the issued client registration and requires `chatgpt.tokens.use.direct`.
It does not use a client secret. Existing credentials for coding assistants do
not authorize this worker. If you deliberately need to request omitted consent,
use `login --approve-plan-sharing --reconsent`.

Before inference, inspect this application's settings at
[ChatGPT Usage](https://chatgpt.com/settings/usage), disable additional credit
spending, and set `credits_disabled_confirmed = true` in the config. This records
operator confirmation; the worker cannot independently inspect that setting.

```bash
.venv/bin/mcq-solver models
.venv/bin/mcq-solver test-inference
.venv/bin/mcq-solver --bank /private/bank.json sync --limit 5
.venv/bin/mcq-solver --bank /private/bank.json run --limit 5
.venv/bin/mcq-solver status
.venv/bin/mcq-solver export-review --out /private/review.csv
```

The default selection is `gpt-6.1-sol` with high reasoning. Account-specific
discovery and a completed streamed probe are required before processing jobs.
Model or reasoning changes require another probe and corresponding queue jobs.
An unavailable model is a stop; there is no automatic downgrade. A model ID
returned by the provider must match the configured slug exactly in this release.

Inference uses only public `https://api.openai.com/v1` endpoints, OAuth bearer
authorization, `store: false` and `stream: true`. It supplies complete input
context each time and saves output only after `response.completed`. Partial,
failed or incomplete streams are discarded.

## Draft review and offline import

All saved results require human source/reasoning review. Qualitative certainty
is not a calibrated probability. The worker compares official keys after blind
inference and flags disagreement without changing them. No human approval or
publication is created.

Offline `import-results --file /private/results.json` accepts at most five items
in an array. Each has `question_id`, `question_version_hash` copied from the
blind packet, and a `response` object with exactly:

```json
{
  "question_id": "EXACT_PACKET_ID",
  "selected_option_id": "0",
  "explanation": "Specific, useful reasoning for the exact stem and choices.",
  "certainty": "uncertain",
  "review_required": true,
  "review_reasons": ["Original source needs human inspection"],
  "topic": "Arithmetic"
}
```

Option IDs are stringified zero-based indexes. A null selection requires a
concrete review reason. Imported output is attributed to `offline-import`, with
unverified model provenance. Duplicate imports do not duplicate drafts.
CSV exports escape formula prefixes, reject credential-shaped content and refuse
to overwrite existing files.

## Recovery and limits

`stop` creates a durable stop request. SIGTERM/SIGINT stop before the next job;
the current bounded request can finish and save its validated draft. Expired
leases recover after a crash and old lease holders cannot commit. At most three
attempts per job, persisted exponential backoff/jitter and Retry-After apply.
There is one worker lock per state directory.

Plan usage/consent failures persist a pause across restarts. Wait for legitimate
renewal or reauthorize as appropriate; then explicitly `resume`, run
`test-inference`, and continue. Resume makes no network request and does not
reset attempts. No account rotation, credential pooling or limit evasion exists.

SQLite draft commits are idempotent. If a provider finishes immediately before
a process crash, inference may repeat after the lease expires; exactly-once
provider usage cannot be guaranteed. Back up the queue with SQLite's backup API
while stopped; back up credentials separately and securely.

For a [self-hosted VM](https://developers.openai.com/siwc/token-sharing-open-source/self-hosted-vms),
create its persistent host using `init-host` before importing a credential session.
Complete OAuth locally and use `export-credentials --ssh-host ALIAS
--remote-python /absolute/venv/bin/python --remote-credentials-dir /private/auth`.
SSH uses strict host-key checking and stdin, preserving the VM host ID. Local
refresh is suspended before transfer; the VM owns subsequent refreshes. An
uncertain transfer remains suspended for inspection. Do not blindly replay it or
run refreshes from two copies of the same session. No VM paths/users/services are
created automatically and no public port is required.

## Current scope

Deterministic tests cover five mock questions, draft persistence, OAuth identity
checks, streaming failures, stale sources, leases, usage pauses and no-overwrite
guarantees. They make no real model calls and are not model accuracy measurements.
This release has no live database writer or publication adapter. Application
integration belongs in a separate private service with authenticated draft-only
permissions and human review. Larger evaluations and unattended scheduling remain
separate approval gates.

See [official sign-in](https://developers.openai.com/siwc/token-sharing-open-source/sign-in),
[preview limitations](https://developers.openai.com/siwc/token-sharing-open-source/preview-limitations)
and [recovery](https://developers.openai.com/siwc/token-sharing-open-source/errors-and-recovery).

## License

MIT. See `LICENSE`. The license covers this software, not runtime question-bank
inputs, third-party sources, hosted services or private integration code.
