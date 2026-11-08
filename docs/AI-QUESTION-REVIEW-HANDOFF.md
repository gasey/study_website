# AI question review — portable continuation

For any tagging decision, first read [Question tagging rules](QUESTION-TAGGING-RULES.md)
and use [the model candidate prompt](QUESTION-TAGGING-MODEL-PROMPT.md). An explanation
queue assignment does not authorize incidental tag, source or answer changes.

## Resume in this workspace

Read `CLAUDE.md`, `docs/PLAN.md`, then run:

```bash
python3 scripts/ai-question-review.py checkpoint
python3 scripts/ai-question-review.py packet
```

The private queue is `state/ai-review/queue.sqlite`; immutable source, draft,
check, request, checkpoint and receipt JSON files live beside it. This directory
is ignored by Git, shared by accounts on this computer, and must be copied privately
as a whole when moving computers. Checkpoints in chat are not the source of truth.
Do not reset it to change accounts. One command holds the queue operation lock.

If a packet exists, `claim` resumes it and rotates its claim token, invalidating late
results. All items retain drafts and receipts. Finish or mark every item unresolved
before claiming another packet. Never abandon a submitting/publishing item: reconcile
its exact request first. No human approval is created by an account/model change.

```bash
python3 scripts/ai-question-review.py refresh --collection combined-prelims
python3 scripts/ai-question-review.py claim --collection combined-prelims --size 5
```

Use `--size 10` after the five-question pilot passes. The oldest two eligible items
are reserved; other slots prioritize Popular score, active Hot topics, then queue age.
Refresh gets live Oracle candidates, not the local recovery bank. Held/disputed,
incomplete-source, unclassified or already-explained questions are excluded.

## Draft, inspect, check

The packet command shows each exact source record and current claim token. Inspect
the original PDF's physical page, complete stem/options, context and figures. Its
registered document hash is in the packet. Hash-check downloaded sources, cache them
by SHA256 and reuse page extraction. The prepare command caches the registered hash, extracts
the target and adjacent pages, and renders the target for visual inspection. Never infer a missing instruction or key.

```bash
python3 scripts/ai-question-review.py prepare --id QUESTION --claim CLAIM
python3 scripts/ai-question-review.py opencode --id QUESTION --claim CLAIM --model opencode-go/MODEL
python3 scripts/ai-question-review.py draft --id QUESTION --claim CLAIM --file /private/draft.json
python3 scripts/ai-question-review.py check --id QUESTION --claim CLAIM --file /private/check.json
```

Connection verified on 3 November: the private personal key is installed locally;
a small GLM-5.3-Flash request returned `billing_source=go` and balance `cost=0`.
The connection receipt is `state/ai-review/go-connection-check.json` (no secret).
Use the existing key through `go_key()`; never print or export it into a packet.
Check `python3 scripts/ai-question-review.py provider` after changing machines.

The owner confirmed OpenCode **Go**. This installation is OpenCode v2.0.32:
its general `opencode/…` catalog does not mean paid Console billing is permitted.
The runner accepts `opencode-go/MODEL` and sends a stateless request exclusively to
`https://opencode.ai/inference/go/openai/v1/chat/completions`. It verifies returned
`usage.opencode.billing_source` is Go and charged balance cost is zero. Redirects,
other providers and paid fallback are refused. No filesystem, shell, SSH or
publishing tools are exposed to the model. Stable packet session headers preserve
routing/cache identity. See the official [Go endpoints](https://opencode.ai/v2/docs/console/go/)
and [billing metadata](https://opencode.ai/v2/docs/console/api/inference/).

For guided local setup, run `python3 scripts/connect-opencode-go.py` in your own
terminal. It accepts the key through a hidden prompt, saves it with private
permissions and makes no model request. In Console use Account → Personal API keys
→ Add API key, select the Go workspace, and choose Restricted → Models: Request
when permission choices are shown.

A Go **personal API key** must be supplied privately through `OPENCODE_GO_API_KEY`
or `~/.local/share/ism-ai-review/opencode-go.key` (mode 600). Never paste it into
chat, a repository file, a command argument or a report. Existing Console OAuth
credentials were tested read-only and rejected with HTTP 401 by the Go API; no
model request or paid fallback occurred. Do not copy OAuth credentials into the
key file. Configure the actual Go personal key through the Console's normal setup.
The runner checks the installed model catalog and saves returned usage with drafts.
Use `opencode-go/glm-5.3-flash` for routine drafts when connected; escalate complex
items rather than repeatedly spending allowance. Manual drafts remain supported.

The v2 prompt targets 80–130 learner-facing words and caps output at 700 tokens.
It omits bank metadata, does not invent reference URLs and requires care with
subjective rankings and broad administrative-force wording. A single-question
calibration reduced completion tokens from 844 to 354; that is not a measured
percentage saving across ChatGPT plus checking work. Every draft still needs
original-source and reasoning checks. Image-flagged items remain manual.

Draft JSON has exactly `explanation` (20–16000 characters), `model` (actual identity)
and `evidence` (list). It changes explanation text only.

A separate checking pass supplies this exact check JSON:

```json
{
  "draft_sha256": "SHA256_OF_CANONICAL_DRAFT_JSON",
  "source_fingerprint": "PACKET_FINGERPRINT",
  "source_inspected": true,
  "options_checked": true,
  "reasoning_checked": true,
  "exam_date_checked": true,
  "checker": "actual checking model or operator",
  "notes": "Specific source inspection and independent reasoning findings, at least 40 characters.",
  "evidence": [{"kind": "reasoning", "note": "Executable calculation and its checked result, or precise logical/grammar reasoning."}]
}
```

Use the script's `digest()` helper for hashes (sorted compact JSON, UTF-8).
For factual claims use primary references: evidence kind `reference`, HTTPS `url`
and a substantive `note` describing inspected support and exam-date relevance.
The command validates evidence structure; the checking operator must actually
inspect/recompute it. Model agreement and checking boxes do not establish truth.
Two attempts per drafting/checking stage; at most fifty submissions per hour.
Use `unresolved --id … --claim … --reason '…'` for missing or conflicting evidence.

## Publish and recover

```bash
python3 scripts/ai-question-review.py publish --id QUESTION --claim CLAIM
```

This rechecks the full source fingerprint and blank explanation, submits one exact
explanation through owner maintenance with ordinary allowance, and stores its
publication ID. If `exported`, wait for the normal Oracle timer and run the same
command again. Only `applied` plus exact full source readback marks it published.
An uncertain SSH submission is reconciled by the exact normalized proposal's
idempotency key before any retry. Keep the same item/request; never create a variant
just to bypass an uncertain outcome. Source or human edits make the draft stale.

Source/answer repairs use their existing specialist workflows, not this queue.
Friends retain exact assignments and human sign-offs. Do not pause the normal worker
for single-item publication. Legacy multi-item batches must check/drain the Oracle
worker and restore its timer; the retired local timer is irrelevant.

## Discovery

`GET /api/discovery?collection_id=combined-prelims&limit=3` (or `udc`; maximum six)
returns no answers or discussion bodies and creates no attempts. Active assessments
withhold discovery. Seven-day registered practice/discussion signals are grouped
using conservative existing booklet rules; at least five participants are required.
Synthetic `.test` accounts and team activity are excluded. Ranking caches expire
in fifteen minutes; current eligibility is checked again on every read.

Recommended practice uses existing owner-inspected exact game pack sources, not
invented popularity. Owner controls are at `/admin/discovery`. Hot topic picks have
primary evidence/dates, exam/topic scope, a why-now note and at most fourteen days
until expiry. For factual assertions link an independently published current-affairs
revision; stale, superseded or retracted supporting revisions withhold the pick.
Keep answers out of discovery text. Saving a pick makes it draft again.

## First bounded trial — 3 November

Ten-item Go trial completed: nine audited explanation publications applied, one
number-pattern item (`cq_03281775c7e34f15`) unresolved with original content retained.
Seven Go calls across six distinct questions consumed 24,139 provider tokens, with
Go billing and zero prepaid balance cost on every call. A checked exact-question
reuse and two manual image-flagged explanations completed the nine. Source checks
and editing remained necessary; this is not an independent model accuracy score.
Report: `reports/go-review-batch-20261103/README.md`; private measurements and audit
artifacts: `state/ai-review/go-batch-20261103/`. Final audit preserved unrelated bank
content, attempts, assignments, memberships, checks and grants. Ordinary use was
384/500 at completion; refresh live allowance before another run. Queue: 14 total
published, one unresolved, 1050 pending, no active packet. Do not retry the unresolved
pattern without new defensible reasoning/evidence. Human sign-offs remain separate.

## Latest completed packet — 3 November, second batch

Next ten source-inspected questions completed: eight explanation-only publications
applied, two unresolved. Family item `cq_068bef5061686f96` has a concrete countermodel
to the keyed pairing; pattern `cq_074f9dbb041891eb` repeats the earlier unresolved
numbers. Preserve both until new evidence/clarification arrives. Six Go v2 calls
used 18,135 provider tokens, all Go billing and zero prepaid balance charge; two
image-flagged facts were explained manually. Every Go draft was independently
checked/edited; the appointment draft still needed key-metadata reasoning replaced
with a dated government source. Historical poverty/appointment answers stay dated.

Report: `reports/go-review-batch2-20261103/README.md`; private artifacts:
`state/ai-review/go-batch2-20261103/`. Full preservation audit passed for unrelated
bank content, attempts, assignments, memberships, checks and grants; exact eight
texts/pointers matched receipts. Ordinary allowance use was 392/500 at completion;
refresh it before continuing. Queue checkpoint: **22 total published, three
unresolved, 1040 pending, no active packet**, superseding the earlier trial counts.
No new code/schema deployment, human sign-off or source/answer repair occurred.

## Paste-ready continuation

> Continue the saved Prelims explanation workflow. Read CLAUDE.md, docs/PLAN.md and
> this handoff, then checkpoint and resume the active packet. The owner authorizes
> checked explanation-only publications through the audited Oracle workflow and
> ordinary allowance. Preserve human edits, recorded keys, provenance, holds and
> sign-offs. Use only confirmed subscription billing for OpenCode; never paid fallback.
> Inspect original sources and independently check reasoning before publication.
> Reconcile uncertain submissions, retain receipts and checkpoint before stopping.


## 8 November — reconciliation checkpoint

The ten-question packet completed on 3 November UTC is fully reconciled in
`docs/sources/mcs-publication-20261104.json`; it must not be replayed. Queue now
records 32 published, 1,030 pending and three unresolved, with no active packet.
Three separate audited source corrections removed stale pending-key clauses from
2023 Paper I C Q3/Q28/Q55, retaining the source-image reminder and all historical
answers. Their receipt is `docs/sources/mcs-source-notices-publication-20261107.json`.
Exact historical output checks and current target readbacks are separate because
other tasks published unrelated explanations later. All existing holds, previous
learner rows, assignments and access passed preservation checks. Latest durable
resume file: `docs/sources/mcs-continuation-checkpoint-20261107.json` (verified
8 November). Read fresh authority/queue/live eligibility before claiming new work.
