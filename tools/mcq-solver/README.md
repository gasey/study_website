# Personal MCQ solver

Phase A and five-question Phase B pilot, 6 November 2026. Python 3.11+. It reads the
existing bank JSON and saves **separate local drafts**. It cannot publish, change
keys or call a paid API-key adapter. The real SIWC pilot is complete; its five
records were then inspected against the original PDFs. See
[the source-review release](../../docs/solver-source-review-20261106.md).
The private website can save source-reviewed contribution drafts with recent
owner MFA. This is not a five-MCQ accuracy result: four records have format defects.

Read [discovery](../../docs/solver-discovery.md) before integration. This directory
can become a standalone personal worker; no open-source license or eligibility
claim is implied by its location here. The approved implementation brief is
[retained here](docs/CODEX_QUESTION_BANK_SOLVER.md).

## Install and inspect

```bash
cd /home/hruaia/workspace/projects/personal/india-study-map-app/tools/mcq-solver
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
.venv/bin/python -m pip install --no-deps -e .
.venv/bin/python -m unittest discover -s tests -v
```

Use the explicit source path; this local bank is a recovery snapshot, not Oracle
authority. These commands read it without altering queue/auth state:

```bash
.venv/bin/mcq-solver --config config.example.toml \
  --bank /home/hruaia/workspace/projects/personal/mpsc-question-bankv2/bank/mpsc_bank_v2.json doctor
.venv/bin/mcq-solver \
  --bank /home/hruaia/workspace/projects/personal/mpsc-question-bankv2/bank/mpsc_bank_v2.json \
  sync --dry-run --limit 5
```

Global options precede the command. Default queue location:
`~/.local/share/mcq-solver`; default credentials:
`~/.config/mcq-solver/credentials`. Parent directories must be owner-only;
credentials are atomically written with mode 0600 and refreshed under a process
lock. State belongs to the operator, never a public web service.

The private `source-holds.json` in the state directory can exclude known malformed
appearances from selection and from already queued work. It contains `version: 1`
and a `question_ids` array of appearance ID strings. These holds do not edit the bank;
remove a hold only after inspecting its repaired authoritative source.

## Eligibility and consent before real inference

1. Establish that the actual standalone worker qualifies under current SIWC
   eligibility, or obtain OpenAI's approval for the proposed integration. See
   [official overview](https://developers.openai.com/siwc/token-sharing-open-source).
   This checkout has not established that. Do not mark eligibility confirmed
   simply to get past the gate.
2. Copy `config.example.toml` into `~/.config/mcq-solver/config.toml`. Record the
   actual basis as `eligibility = "oss_self_hosted"` or `"openai_authorized"`
   and a substantive `eligibility_evidence` reference. No credentials go there.
3. Locally run the following command, only after you explicitly approve sharing
   your plan with **Personal MCQ Solver**. It opens the system browser; approve
   the requested scopes there. The listener binds only to `127.0.0.1`, using a
   free port and `/auth/callback`. Do not run login over SSH on the VM.

```bash
.venv/bin/mcq-solver login --approve-plan-sharing
```

The brief explicitly requires this separate approval. Existing Codex credentials
are neither imported nor reused. The code implements the documented
[registration flow](https://developers.openai.com/siwc/token-sharing-open-source/sign-in)
with fresh state/nonce/PKCE, issued client ID persistence and signed OIDC checks.
On later sign-in it reuses that registration. If consent omitted plan permission,
identity is retained but inference stays disabled. To deliberately request that
permission again: `login --approve-plan-sharing --reconsent`.

4. In [ChatGPT Settings → Usage](https://chatgpt.com/settings/usage), inspect this
   app's plan allowance and turn off use of additional credits. Then set
   `credits_disabled_confirmed = true` in your config. This is operator
   confirmation, not a server-verified billing receipt. The worker uses only
   OAuth and cannot enable billing or fall back to an API key.

No three-account rotation is implemented. Never switch credentials to evade a
limit. Each runtime uses one selected registration. The current CLI intentionally
does not offer automatic account discovery or pooling.

## Exact five-question pilot commands

After eligibility, consent and credit settings are established:

```bash
.venv/bin/mcq-solver doctor
.venv/bin/mcq-solver models
.venv/bin/mcq-solver test-inference
.venv/bin/mcq-solver \
  --bank /home/hruaia/workspace/projects/personal/mpsc-question-bankv2/bank/mpsc_bank_v2.json \
  sync --limit 5
.venv/bin/mcq-solver \
  --bank /home/hruaia/workspace/projects/personal/mpsc-question-bankv2/bank/mpsc_bank_v2.json \
  run --limit 5
.venv/bin/mcq-solver status
.venv/bin/mcq-solver export-review --out /tmp/mcq-solver-five-review.csv
```

The probe is one additional small request and is never automatic. Its receipt is
bound to the validated subject/client, model and reasoning setting and lasts 24
hours. `run` refreshes the same account's model catalog, uses one request at a
time and refuses an unprobed model. An explicit `--model MODEL` override requires
running `models`, `test-inference`, `sync` and `run` with that same selection.
An unavailable model or rejected reasoning level stops; it never downgrades.
Provider-returned model IDs must match the selected slug exactly in this phase;
an unexpected alias/snapshot stops for inspection rather than being relabeled.

`--dry-run` and `--no-write` on `sync`/`run` are read-only previews: no inference,
token refresh or queue mutation. `run` operates on already synced jobs. Repeating
`sync` does not duplicate them. Every exported result retains source hash, model,
reasoning, prompt version, run ID, key agreement and a blank human approval.
All drafts require human review; validation cannot establish factual correctness.

Missing diagrams, source defects, unknown answers and official-key disagreements
remain flagged. Images are not yet sent. Full records/media metadata are hashed;
the model receives only text context, ordered option IDs, subject/topic and year,
without existing keys/explanations. Inspect original PDFs before accepting drafts.

Limits above five are refused in this scaffold. The 20/100-question evaluations,
calibrated subject reports and any 1,000+ batch or scheduler are later phases.

## Offline export and import

This works while hosted inference is blocked. It does not submit anything to the
website. Export contains no existing answer or explanation:

```bash
.venv/bin/mcq-solver \
  --bank /home/hruaia/workspace/projects/personal/mpsc-question-bankv2/bank/mpsc_bank_v2.json \
  export-packet --limit 5 --out /tmp/mcq-solver-blind-packet.json
```

Prepare a JSON array, at most five items. Each item has exactly `question_id`,
`question_version_hash` from the packet, and `response` with the seven fields
below. Option IDs are strings containing the zero-based index, not A/B/C letters.

```json
{
  "question_id": "EXACT_PACKET_ID",
  "question_version_hash": "EXACT_PACKET_HASH",
  "response": {
    "question_id": "EXACT_PACKET_ID",
    "selected_option_id": "0",
    "explanation": "Specific reasoning addressing the exact question and options goes here.",
    "certainty": "uncertain",
    "review_required": true,
    "review_reasons": ["Original source still needs inspection"],
    "topic": "Existing subject / topic"
  }
}
```

```bash
.venv/bin/mcq-solver \
  --bank /home/hruaia/workspace/projects/personal/mpsc-question-bankv2/bank/mpsc_bank_v2.json \
  import-results --file /tmp/mcq-solver-results.json
.venv/bin/mcq-solver export-review --out /tmp/mcq-solver-offline-review.csv
```

Imported output is explicitly attributed to `offline-import` / `not_verified`,
never to an allegedly verified hosted model. Imports validate IDs and current
hashes, reject duplicates/malformed outputs, and are idempotent. Exports use
exclusive file creation, private permissions and spreadsheet formula escaping.

## Stop, resume and recovery

`mcq-solver stop` creates a durable stop request; SIGTERM/SIGINT also prevent
claiming the next job. A current request may finish and save its validated draft.
Network reads time out after 90 seconds; a streamed response has a 300-second
processing bound plus one read timeout. Leases last 600 seconds. Following a
crash, an expired lease is recovered atomically; stale workers cannot commit.
The process lock enforces one worker per state directory.

Rate/network failures persist bounded backoff with jitter and Retry-After;
each job has at most three attempts. Partial output is discarded. A crash after
the provider completed but before the local commit can repeat inference after
lease expiry: there are no duplicate saved drafts, but exactly-once provider
spending cannot be promised. The worker does not store raw streams or tokens in
diagnostics. Error codes are allowlisted; unexpected details are discarded.

Plan exhaustion, unavailable allowance and consent/identity failures persist a
global pause, so restarting cannot continue requests. Check the actual account's
usage/access; never guess a reset time. After legitimate renewal or reauthorization:

```bash
.venv/bin/mcq-solver resume
.venv/bin/mcq-solver test-inference
# Then run the bounded pilot command again.
```

`resume` clears the pause/stop flags and makes paused jobs eligible up to the
attempt limit. It makes no network request, changes no account and does not reset
attempt counts. Permanent failures remain for inspection. Revoked/expired refresh
credentials are cleared while the issued client/identity mapping is retained for
local reauthorization. Temporary refresh failures retain credentials.

## Oracle handover after a successful local pilot

No deployment or new service user was created. Use a dedicated low-privilege
account and an installed worker venv with a confirmed path. Do not give it the
website's production database secret. Copy only this worker's code and a permitted
read snapshot; a scoped production draft capability is separate pending work.
Do not start a systemd timer in this phase.

Following the [VM guidance](https://developers.openai.com/siwc/token-sharing-open-source/self-hosted-vms),
initialize the VM's host before importing a credential session. Example deployment
paths below are a proposed new layout, **not verified existing VM paths**. Configure
the `mcqsolver-oracle` SSH alias for the dedicated account first.

```bash
ssh mcqsolver-oracle /opt/mcq-solver/.venv/bin/python -m mcq_solver \
  --credentials-dir /home/mcqsolver/.config/mcq-solver/credentials init-host
.venv/bin/mcq-solver export-credentials --ssh-host mcqsolver-oracle \
  --remote-python /opt/mcq-solver/.venv/bin/python \
  --remote-credentials-dir /home/mcqsolver/.config/mcq-solver/credentials
```

Transfer uses SSH stdin, strict host-key checking and captured output; tokens are
never placed in arguments, logs or temporary export files. The VM preserves its
own host ID. Local refresh is suspended **before** transfer; after confirmation,
local tokens are removed and the VM owns refreshes. If transfer is uncertain,
keep the laptop suspended and inspect the VM's `doctor` result. Do not replay the
transfer blindly or resume both copies of a rotating session. Import refuses to
overwrite any existing VM registration. A later local login may create a fresh
session for reauthorization; do not copy the VM's rotating tokens back.

For queue backup, stop the worker and use SQLite's backup API to a protected path;
restore only while stopped and preserve the entire ledger. Credentials require a
separate protected backup and session-revocation procedure; never check them in.
Host IDs remain stable across reboot. No scheduler or production restore was tested.

## Acceptance status

- Phase A: discovery, standalone package, typed adapter, config and mocked tests.
- Safe Phase B: implemented OAuth/refresh/transfer and streamed probe code; verified
  with mocks and signed test JWTs, **not a real account grant**.
- Five-question test: deterministic synthetic end-to-end draft persistence and
  real-bank read-only selection. Not a live five-question inference evaluation.
- Remaining Phase B: confirmed eligibility, owner OAuth consent, real model/probe,
  restricted production draft writer and one authoritative draft readback.
- Remaining C/D: real 5/20/100 evaluation, human inspection, approved scaling,
  live VM deployment/recovery and unattended scheduling.

Additional implementation references: [streaming](https://developers.openai.com/siwc/token-sharing-open-source/models-and-inference),
[preview restrictions](https://developers.openai.com/siwc/token-sharing-open-source/preview-limitations),
[errors](https://developers.openai.com/siwc/token-sharing-open-source/errors-and-recovery),
[sessions](https://developers.openai.com/siwc/token-sharing-open-source/profiles-and-sessions).
