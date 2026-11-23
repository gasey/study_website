# Explanation backfill — operational continuation

Content decisions follow [Current review and solving rules](QUESTION-REVIEW-RULES.md).
This file is the explanation-only queue procedure; dated counts below are historical.
Run a fresh checkpoint, preserve source/answer boundaries and do not replay old packets.

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

The current prompt has no minimum word count and caps output at 700 tokens.
Direct supported recall may use the source-bound private `not-needed` disposition
without publishing filler or claiming any new answer review.
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


## 9 November 2026 — ordinary allowance and optional explanations

`ai-review-remote.py` now reports total contributions separately from ordinary
usage. Its ordinary counter follows `bank_review.create`: only taxonomy records
with both matching trusted authorization and exemption events are excluded. The
large frozen tagging publication must not falsely block ordinary explanation work.
No budget, exemption scope or API permission changed.

After inspecting a direct supported recall item, record why extra prose adds no
learning value:

```bash
python3 scripts/ai-question-review.py not-needed --id QUESTION --claim CLAIM --reason "Substantive source-specific reason"
```

This is a private queue disposition, not an answer verification, editorial sign-off
or production content change. It requires prepared source context, a current claim
and an unchanged live source fingerprint. A later source change reopens the item
on refresh. It cannot discard checked or publishing work. Keep this outcome
separate from unavailable evidence and unresolved answers.

Submit the next explanation only after the previous publication is applied; the
ordinary writer rejects overlapping outstanding exports. If a submission is
uncertain or refused, resume that exact item so its persisted request is reconciled.
Do not create a new request or leave a submitting/publishing item abandoned.

Latest checked packet: `docs/sources/mcs-publication-20261109.json`. Queue at
9 November IST: 35 published, 2 explanation-not-needed, 1,025 pending, 3 unresolved,
no active packet. These counts supersede prior dated continuation counts; do not
replay completed publications. Ordinary allowance after publication is 3/500,
with zero exports waiting and Oracle timer active.


## 10 November 2026 — audit follows the installed writer

The live staff-maintenance policy changed after the 9 November checkpoint. The
read adapter no longer copies a 500-item cap or a separate SQL definition of usage.
It inspects the installed operator writer's literal count query and role-based
limits, and fails if that contract is unrecognized. This reads policy; it does not
change any limit, permission or exemption. It supports both the prior capped
contract and the currently installed uncapped staff-maintenance contract.

An audit with `staff_maintenance_capped=false`, `ordinary_staff_limit=null` and
`ordinary_staff_remaining=null` means that the inspected staff path is uncapped;
it does not mean zero remaining. `learner_daily_limit` remains explicit (30 at
this checkpoint). `ordinary_used` follows the installed learner-contribution
counter and excludes the maintenance records that writer excludes. Total
contributions are reported separately. The policy digest identifies the count
query and limits used for that audit. Do not infer exhaustion from old receipts
or request a new quota exception because an obsolete report printed zero.

Latest packet/checkpoint: `docs/sources/mcs-publication-20261110.json`. Queue at
10 November IST: 47 published, five explanation-not-needed, 1,011 pending, three
unresolved, no active packet. Three new publications are applied and read back;
all historical output hashes are verified separately from later concurrent answer
publications. The observed shared export queue was empty at verification; always
check fresh state before submitting. Do not replay earlier packets.


## 11 November — continuation checkpoint

Receipt: `docs/sources/mcs-publication-20261111.json`. Three new explanations and
one separate source-passage repair are applied and exact-readback verified. Q58
was initially deferred for missing context; after the source correction, refresh
reopened its explanation as pending. Current queue: 50 published, six not-needed,
1,007 pending, three unresolved, no active packet. Blank explanations are assessed
selectively; these are not answer-review completion counts.

Canada's dated 2026 Q2 snapshot is an explanation addition with a private recheck
lead, not a new reusable dated-fact revision. MZU current source could not be
inspected; no current/unchanged status claim was made. At final observation all
four packet exports were applied, but 29 unrelated answer exports occupied the
shared queue. Check fresh export state before any submission and do not replay
other workflows. Source/answer restrictions, existing holds and historical
numbering/recovery deferrals remain in force.


## 12 November — continuation checkpoint

Receipt: `docs/sources/mcs-publication-20261112.json`. Two explanations and one
separate source-passage restoration applied and passed exact output/readback
verification. Q58's earlier repair now supports its explanation. II D Q62's newly
restored passage/directions reopen its explanation against fresh source context;
do not replay either source repair or imply sibling coverage. No source/answer
certification is inferred from explanation publication.

Queue after refresh: 52 published, 8 explanation-not-needed, 1003 pending,
3 unresolved, no active packet. Always check fresh Oracle source/export state
before claiming. Preserve historical identity/figure/radical blockers, deferred
2012/2013 recovery, original-simulation prerequisites and all scoring holds.


## 13 November — continuation checkpoint

Two explanations applied (2023 II D Q62 and II A Q27), with passage-limited
inference and a primary-reference communication-model caveat. Separately restored
the original common passage/directions on II C Q35 from its own pages 4–5; retain
printed wording, source image, answer provenance and original mapping. Q35's
explanation reopened after source refresh. Two direct recall items need no prose.

All three immutable outputs and live readbacks match. 780 prior global holds,
381 attempts, reviewer scope and unlimited access are preserved. 45 focused
tests pass; protected sync and services healthy. No time-sensitive fact update.

Queue: 54 published, 10 not-needed, 999 pending, 3 unresolved,
no active packet. Historical source/option repairs and exact-key notices remain;
keep 2012/2013 deferred and original simulation gated. Receipt: `docs/sources/mcs-publication-20261113.json`.

Do not replay applied source repairs or infer sibling coverage/new answer review
from explanation availability. Check fresh Oracle source fingerprints and shared
export state before claiming the next packet.


## 14 November — continuation checkpoint

Two explanations applied (2023 II C Q35 and I C Q57). Poverty-estimates prose
preserves the historical key, distinguishes survey data from estimate authority,
and adds separately dated 2024 naming / 2025 HCES-release notes from primary
sources. No assertion of latest-series status or new poverty statistic.

Three separate source publications restored printed common context on II A Q47,
II A Q39 and II B Q59; original answers/options, page/number, source image and
classification remain intact. These explanation candidates reopen after refresh;
no sibling coverage or new answer review is implied.

All five exact outputs and live readbacks match; 1676 prior global holds, 381
attempts, reviewer scope and unlimited access preserved. 45 focused tests pass;
protected sync and services healthy. Queue: 56 published, 10 not-needed,
997 pending, 3 unresolved, no active packet. Historical source/option repairs
and exact-key notices remain; keep 2012/2013 deferred and original simulation
gated. Receipt: `docs/sources/mcs-publication-20261114.json`.

Check fresh Oracle fingerprints/export state before claiming. Reconcile exact
intents after shared-queue conflicts; never replay applied source repairs or
restart another worker’s paused publisher during its atomic batch.


## 15 November — continuation checkpoint

Three explanation-only publications applied: 2023 II A Q39 (argument relevance),
I C Q78 (microwave ionization with explicit UV ambiguity) and I C Q47 (ordinary
local-government framework versus Sixth Schedule, preserving ADC autonomy caveat).
Official keys, question/options, source mappings, classifications and scoring
restrictions remain unchanged. No dated current-affairs revision was warranted.

II A Q47 and II B Q59 remain explanation-unavailable with concrete assumption/
inference limitations; no invented derivation or new answer acceptance. All three
immutable outputs and live readbacks match. Preserve 2258 prior global holds,
383 attempts, reviewer scope and unlimited access; 45 focused tests pass.
Protected sync/API/Study healthy, Oracle timer active, no service changes.

Queue: 59 published, 10 not-needed, 992 pending, 5 unresolved,
no active packet. Historical source/option repairs and exact-key notices remain;
keep 2012/2013 deferred and original simulation gated. Receipt: `docs/sources/mcs-publication-20261115.json`.

Do not retry the family/prayer explanations without additional reasoning evidence.
Preserve explicit scientific/institutional ambiguity in new prose. Check fresh
Oracle fingerprints and publication state before selecting the next packet.


## 16 November — continuation checkpoint

Three checked explanations applied (2023 II A Q32, I B Q31, I D Q67): cultural
interpretation, standard lapse rate with limits, and biological trickling filters.
One direct recall target needs no prose. No dated current-affairs revision.

Two separate source publications correct II B Q52's physical locator8→7 and
restore its printed Q52–56 directions. Retain printed number, exact identity,
question/options, provenance and scoring; its explanation reopened after refresh.
All five immutable outputs/live readbacks match. Preserve 2335 prior global
holds, 387 attempts, reviewer scope and unlimited access. 45 tests pass;
protected sync/API/Study healthy, Oracle timer active, no service changes.

Queue: 62 published, 11 not-needed, 988 pending, 5 unresolved,
no active packet. Preserve prior unresolved reasoning evidence gaps. Historical
source/option repairs and exact-key notices remain; keep 2012/2013 deferred and
original simulation gated. Receipt: `docs/sources/mcs-publication-20261116.json`.

Check fresh Oracle fingerprints/export state before claiming. Do not replay the
Q52 source corrections or transfer option letters/identity between booklets.


## 17 November — continuation checkpoint

Five explanations applied with exact source/live readbacks: 2023 II B Q52
(strong/weak argument relevance, without empirical policy claims), I D Q8
(44 subject entries in 2023 top100, with separate dated 2026 top50 update),
I A Q11 (Deka's historical 1May2023 term start), II C Q28 (reward power versus
authority/expertise/identification), and II C Q54 (intended visual-aids choice,
acknowledging feedback can be constructive). Preserved original answers, ordered
options, locators, printed identities and notices. C-series pending-key notices
remain; explanations do not certify key-document mappings or clear scoring holds.

Inspected registered original pages, Ministry2023 physicalp11, Ministry2026
release and publisher textbook. University publicpage retrieved after TLS chain
failure with verification disabled; limitation retained internally. No latest
officeholder or newappointment claim. QS update explicitly distinguishes 2026
top50 from 2023 top100; neither historical key nor score changes.

Recorded separate classification lead: I A Q11 university appointment incorrectly
stored under public works accounts. Supported historical Current Affairs route
needs central re-review reservation, fresh active taxonomy/related-path baseline
and its own guarded publication. No unreserved tag proposal or retag claimed.

Five immutable output reconstructions prove target explanation/pointer changes
only. Preserve 2572 prior global holds, 387 prior attempts, reviewer rows/grants
and owner unlimited access. No peer credits, quota exemptions, provider calls,
synthetic learner attempts, schema/frontend deployment or service-state changes.
45 focused tests pass. Protected bank/taxonomy sync, API and Study route healthy;
Oracle timer active, wakeup observed `inactive`.

Queue: 67 published, 11 not-needed, 983 pending,
5 unresolved, no active packet. These are explanation-queue counts,
not whole-bank completion. Preserve unresolved inference limitations, source/option
backlog and exact-key checks. Keep 2012/2013 deferred and simulation gated.
Receipt: `docs/sources/mcs-publication-20261117.json`. Private proof: `reports/mcs-continue-20261117/`.

Resume from fresh Oracle export/fingerprints; do not replay completed Q52 locator
and direction repairs. Separate classification lead is not a reserved candidate.


## 18 November — continuation checkpoint

Published three checked explanations: 2023 II A Q33 distinguishes emotional
self-awareness from self-management and neighbouring self-terms; II C Q32 explains
short, focused closed questions and their possible uses while explicitly avoiding
guaranteed savings/shyness claims and retaining open-question follow-ups; I A Q24
distinguishes the 1924 Kanpur case (Dange, Muzaffar Ahmad, Nalini Gupta) from
Ashfaqulla Khan's Kakori association. Inspected exact registered pages, CASEL,
Open University/MacEwan teaching references, DIKSHA-hosted Tamil Nadu history
physicalp68/printed64, and primary MHA historical corroboration. C-series generic
pending-key notice remains; no key-mapping acceptance implied.

A-series I Q93 folktale/name recall receives no filler or invented literary
interpretation. D-series I Q54 poverty item is privately unresolved: primary
Planning Commission23July2013 and MoSPI30July2025 sources distinguish poverty
estimation from consumption-data/MPCE collection. Need exact2023 mandate and key
mapping before a confident derivation. Preserve existingA, source/options and
scoring; private explanation disposition creates no public hold. The newer
HCES source describes2023–24, not2026 measurements. No public dated-update or
unchanged-role claim was published. Do not retry without relevant new evidence.

All three publications applied with full live/public readbacks and reconstructed
immutable outputs proving target explanation/pointer changes only. Preserve 2570
prior global holds, 387 prior learner attempts, reviewer scope/grants and owner
unlimited access. No peer votes/credits, quota exceptions, external model calls,
synthetic learner writes, API/frontend/schema deployment or service-state changes.
45 focused tests pass. Protected bank/taxonomy sync, API and Study route healthy;
Oracle timer active and wakeup observed `inactive`. Live subscription
usage tool unavailable; ordinary staff quota independently audited, uncapped.

Queue: 70 published, 12 not-needed, 978 pending,
6 unresolved, no active packet. Explanation counters do not establish
complete answer/source review. Earlier appointment-tag lead, historical source/
option defects and exact-key notices remain. Keep2012/2013 deferred and original
simulation gated. Receipt: `docs/sources/mcs-publication-20261118.json`.
Private proof: `reports/mcs-continue-20261118/`.

Resume from fresh Oracle snapshots and export state. Preserve prior source repairs,
optional-prose decisions and unresolved evidence gaps; never replay packet writes.


## 19 November — continuation checkpoint

Four explanations applied: 2023 I C Q66 explains HCFCs as transitional CFC
replacements and ozone depletion, with dated Indian2025 phase-out schedule context
(67.5% scheduled step, not measured achievement); II C Q26 explains emotional
intelligence while acknowledging related competence terminology; II C Q83 works
LIGHT/ENDURE substitution through 10|2|7|3|1|6|5 → RINGLET; II C Q40 distinguishes
visible face/mouth structures from internal brain without falsely calling lips a
separate sense organ. Inspected exact registered original pages and primary
EPA/OzoneCell/publisher references. Generic pending-key notices remain; explanation
publication does not certify key-document matching. Historical answers preserved.

Separate guarded transcription restores II B Q53's missing shared Q52–56 rubric
from physicalp7, applied to exactQ53 physicalp8. Reused priorQ52 rubric evidence
only after matching registered document ID/hash and reinspecting both pages; no
Q52repair replay or sibling coverage claimed. PrintedQ53/page8, question/options,
answer/keyprovenance, classification and scoring unchanged. Its explanation
candidate reopens after fresh source refresh; do not replay direction repair.

All five immutable outputs and exact live/public readbacks verified. Preserve
2549 prior global scoring holds, 387 prior attempts, reviewer scope/grants and owner
unlimited access. No peer votes/credits, quota exceptions, reset consumption,
external provider calls, synthetic learner writes, API/frontend/schema release
or service-state changes. 45 focused tests pass. Protected bank/taxonomy sync,
API and Study route healthy; Oracle timer active, wakeup `inactive`.
Start usage26%primary/95%weeklyused; ordinary usage allowed. Publication policy
independently audited uncapped for staff; learner30/day unchanged.

Queue: 74 published, 12 not-needed, 974 pending,
6 unresolved, no active packet. Counters describe explanation queue,
not complete answer/source certification. Retain previous poverty/family/prayer/
number-pattern evidence gaps, reserved appointment-tag follow-up, historical
source/option defects and exact-key notices. Keep2012/2013 deferred and original
simulation gated. Receipt: `docs/sources/mcs-publication-20261119.json`;
private evidence `reports/mcs-continue-20261119/`.

Check fresh Oracle fingerprints, queue and usage before claiming. Preserve all
completed rubric repairs and exact booklet identities. Q53explanation remains next
work, not a new answer/key decision.


## 21 November — continuation checkpoint

Three explanations applied: 2023 II B Q53 evaluates the two arguments using
the restored importance and relevance test without deciding education policy.
I B Q66 explains Kyoto's market mechanisms and retains the historical answer,
with a dated UNFCCC notice about the scheduled 31 March 2026 ITL closure. This
does not claim an independently observed shutdown or the end of all carbon
markets. I A Q16 explains the Great Bath's proposed ritual use while retaining
archaeological uncertainty. Exact original pages, UNFCCC sources and NCERT
physical/printed page 8 were inspected. NCERT's certificate chain failed normal
verification; the public download used disabled verification, recorded privately.

A separate guarded transcription restores II C Q51's missing Q47–51 rubric
from the same physical page 6, bound to its own registered C-series PDF. Prior
B-series text served only as a draft template; the C-series heading and body
were visually checked. Printed Q51/page 6, options, key A, classification and
scoring are unchanged. Its explanation reopens after a fresh source refresh;
do not replay the source repair or infer coverage of other appearances.
I C Q98's weaving explanation remains unavailable: a reliable craft or language
reference is needed. No translations or sequence derivation were invented; its
existing answer and pending-key notice remain. No public hold was created.

All four immutable outputs and exact live/public readbacks verified. Preserve
3095 prior global scoring holds, 404 attempts, reviewer scope and grants, and
owner unlimited access. No peer votes, credits, quota exceptions, reset use,
external model calls, synthetic learner writes, application/schema release or
service-state changes. All 45 focused tests pass. Protected bank/taxonomy sync,
API and Study route are healthy. Oracle timer active; wakeup observed
`inactive`. Start usage: 3% primary and 83% weekly used; ordinary
usage allowed. Staff maintenance is uncapped; learner allowance stays 30/day.
The prior checkpoint `ad265164d` was confirmed on GitHub before new work.

Queue: 77 published, 12 not-needed, 970 pending,
7 unresolved; no active packet. These are explanation-queue counts,
not whole-bank answer/source certification. Prior poverty, family, prayer and
number-pattern evidence gaps, the reserved appointment-tag follow-up, historical
source/option defects and exact-key checks remain. Keep 2012/2013 deferred and
original simulation gated. Receipt: `docs/sources/mcs-publication-20261121.json`.
Private proof: `reports/mcs-continue-20261121/`.

Check fresh Oracle fingerprints, exports and usage before claiming. C51 explanation
remains next work; weaving needs specific craft/language evidence. Preserve source repairs.


## 24 November — active shared worker

Independent heartbeat reconciled substantial intervening work in the shared
explanation queue. “Review remaining Finna questions” is actively processing
packet `packet_cb035911e16ed909`; do not rotate its claims or duplicate that work.
At 2026-11-23T20:42:00.160717+00:00, the snapshot showed 316 published, 225 not-needed, 475
unclaimed pending, 43 unresolved, plus an active ten-item packet: seven checked
and three not-needed. Checked items are not claimed published here. These dated
counts supersede the older 21 November queue totals, but can advance immediately.

Read-only Oracle audit found no pending exports at observation, protected bank/
taxonomy sync matched, timer active, wakeup inactive, API healthy and Study HTTP200.
Recorded MCS inventory:59held (1duplicate-options,4unresolved-source,54other) and
2942live; this does not certify source/key/answer completeness. Owner unlimited
access remains active. The known I A Q11 university-appointment tag still reads
Financial Rules/Public Works Accounts and needs a separately reserved correction.

All45focusedtests pass. No queue refresh/claim, draft, content publication, learner
or account/history change, service change, reset consumption or provider call by
this continuation. Usage was available (11%primary/7%weeklyused); ordinary staff
publication remains uncapped, learner30/day unchanged. Historical source/option/
key-mapping tasks remain. Keep2012/2013deferred and simulationgated.
Receipt:`docs/sources/mcs-checkpoint-20261124.json`; private audit:`reports/mcs-checkpoint-20261124/`.
