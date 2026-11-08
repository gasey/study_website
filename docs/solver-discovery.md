# MCQ solver discovery

Inspected 6 November 2026. This is Phase A and a safe Phase B scaffold for the
owner's `CODEX_QUESTION_BANK_SOLVER.md`. No production data, schema, billing or
service configuration was changed. Live OAuth and inference remain unverified.

## Existing data and ownership

The website uses React/Vite/TypeScript and FastAPI/psycopg/PostgreSQL. The sibling
`mpsc-question-bankv2` repository contains the Python extraction tools and bank
JSON. `CLAUDE.md` identifies Oracle's
`/srv/study/workshop/mpsc-question-bankv2` as the only writable canonical bank;
the local sibling bank is a **read-only recovery snapshot**, not live authority.
This discovery inspected local code/migrations and the recovery JSON; it did not
connect to Oracle or claim that its current counts match the snapshot.

The inspected JSON contains **81,627 questions**, **73,475 MCQs** and **8,152
descriptive items**. SHA256:
`99ce7a54d37581a8be55b6f144b677ab8855240371ed1ec67d6a142139dd45e0`.
The older 77,751-question inventory and its field crosswalk are historical.

| Existing representation | Meaning for the solver |
| --- | --- |
| `questions[].id`, `paperId`, `qnum`, `page` | Printed appearance identity and location; preserve verbatim |
| `question`, `options` | Stem and ordered string array; do not convert printed option order |
| `answerIndex` | Zero-based; null or legacy `-1` means unknown. Zero is a valid answer |
| `answerSource`, `answerKeyRef` | Provenance and registered-key pointer; model agreement does not create official evidence |
| `direction`, `passage`, `questionMarkup`, `optionsMarkup` | Printed context/formatting; retain in version hash; formatted content needs inspection |
| `hasDiagram`, `figureImage`, `figureGroupId`, `passageId` | Source/media context; referenced images are not sent in this text-only scaffold |
| `subject`, `topic`, `classifications` | Existing classification claims; no generated difficulty labels |
| `key_disputed`, `sourceDefect`, `compensated` | Review/scoring restrictions; never clear them |
| `reviewPublicationId`, `explanation` | Existing reviewed/public content; read-only |

The JSON root also has `papers`, `sittings`, `figureGroups` and `passageGroups`.
The adapter hashes the full appearance, its paper metadata and referenced groups,
including existing keys/explanations to detect human changes. Model inputs omit
all keys and existing explanations. Options get stable **stringified zero-based
indexes** such as `"0"`; they are tied to that exact version, not global option IDs.

Database migration `0002_schema_v3.sql` separates `canonical_questions` from
printed `appearances`. The canonical answer is `answer_text` in canonical option
order; appearances retain `answer_index` and explicit `option_order`. Status is
`live`, `held`, `withdrawn` or `merged`. A canonical answer must be one of its
options; withdrawn items have no answer. `scripts/bank_to_csv.py` preserves the
zero-based index and maps negative sentinels to NULL. Do **not** derive a current
canonical ID using the migration's historical MD5 backfill: merges can change
the current relationship.

## Existing review integration

`app.services.bank_review.snapshot(cur, canonical_id, appearance_id)` returns the
real record, source metadata and paper identity. Approved taxonomy comes from
`question_classifications` and `question_topic_links`; source evidence comes
from `review_documents`.

`POST /api/contributions` already creates a separate draft. It accepts the real
`Proposal` fields (`canonical_id`, `appearance_id`, `subject_id`, `patch`,
`rationale`, `evidence`), an `Idempotency-Key` and an
`X-Review-Source-Version` token. `bank_review.create` checks identity, protected
targets, the current source, taxonomy, evidence and allowance, then writes
`bank_contributions` and `contribution_revisions`. Publication is a later,
separate workflow. Existing actor credentials can perform more than draft-only
writes; they are not an appropriate unattended-worker credential.

The paper workbench is a whole-paper staging/review system with author ownership,
independent review and publication gates. Do not disguise solver output as a
human workbench review. The existing `scripts/ai-question-review.py` queue is
for supported-answer **explanation backfill**, includes a publisher and is tied
to different inference/billing. Its local checkpoint showed 1,030 pending,
32 published, three unresolved, no active packet; this work did not claim or
reset its items. It cannot safely double as an independent unknown-answer solver.

## Boundary implemented now

`tools/mcq-solver` is a separable Python 3.11+ package with its own SQLite ledger,
OAuth registration, process lock, typed bank/draft protocols and read-only JSON
adapter. It has no database DSN, public inference endpoint or publishing command.
Drafts go only to its local `drafts` table; review CSV and blind JSON packets
provide the tested offline path. All Phase B results require human source and
reasoning review. The five-item cap is enforced in both CLI and worker.

The production adapter is deliberately **not connected**. The next integration
should reuse `bank_review.snapshot` and `bank_review.create` behind a restricted
operator capability that can read exact assigned sources and create drafts only.
It needs authoritative canonical/appearance mappings, a fresh source version,
registered evidence, existing allowance/assignment checks and tests against a
disposable database. It must not expose submit, approve, publish or SQL update
capabilities. No speculative application migration was added for this scaffold.

Sequence: local eligibility assessment → explicit plan-sharing consent → PKCE
callback and OIDC verification → protected credentials → account model discovery
and streamed probe → read snapshot → claim one leased job → blind solve → validate
and compare hidden key → recheck source hash → save local review draft.

## Eligibility and authorization

The current [SIWC overview](https://developers.openai.com/siwc/token-sharing-open-source)
describes open-source/locally hosted applications; its
[VM guidance](https://developers.openai.com/siwc/token-sharing-open-source/self-hosted-vms)
describes an open-source app on a self-hosted VM. A private administration job
inside this website is not, by itself, proof of eligibility. No applicable OSS
license, public worker distribution or OpenAI integration approval was established
in this inspection. **Eligibility remains unconfirmed.**

The standalone package can be extracted into an owner-approved open-source
repository without the bank, private app, credentials or question content. The
owner must choose/confirm that route or obtain approval for the actual integration.
No license was assigned and no repository was published on the owner's behalf.
Setting a config flag records a real prior assessment; it does not grant access.

The Codex CLI's existing ChatGPT sign-in is a different client registration. This
worker never reads that credential store. Its login requires explicit consent
and the granted `chatgpt.tokens.use.direct` scope. The default target is
`gpt-6.1-sol` / `high`, documented in the
[model page](https://developers.openai.com/api/docs/models/gpt-6.1-sol), but current
account discovery and a successful probe must establish access. Neither happened
in this task. No API-key adapter exists.

The owner mentioned three ChatGPT accounts. This phase uses one selected
registration and has no account pooling or automatic rotation. Limit exhaustion
pauses the ledger until an explicit resume after legitimate allowance renewal.
The [account documentation](https://developers.openai.com/siwc/token-sharing-open-source/profiles-and-sessions)
also exposes app credit controls in ChatGPT Settings; confirm additional credits
are disabled before inference. The code cannot independently verify that setting.

See the [operator README](../tools/mcq-solver/README.md) for exact pilot commands,
authorization gates, credential transfer and remaining Phase B/C/D acceptance.
