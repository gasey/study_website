# Decisions

Short records for choices that would be expensive to reverse. Newest last.
If you change one of these, add a new record saying why rather than editing
the old one.

---

## 1. FastAPI, not Django — 2026-10-18

**Considered:** Django + django-ninja; FastAPI + SQLAlchemy; Next.js API routes.

Django's case rested almost entirely on its admin panel. The design handoff
includes a fully specified Admin Console, so that admin is being built either
way and Django's version buys nothing. What remained told against it: the
schema is hand-written SQL with triggers, partial unique indexes, recursive
functions and generated columns, and Django's ORM wants to own the schema
through its own migrations. Multiplayer also needs WebSockets, which FastAPI
has natively and Django needs Channels plus Redis to match.

The data pipeline (parsers, OCR, answer-key tooling) is already Python, so a
Python API reuses those models instead of reimplementing them in TypeScript.
FastAPI emits OpenAPI, so the React app still gets generated types.

The handoff README suggests Next.js, but scoped to *"if no codebase exists
yet"* — one does, and it is Vite + React.

---

## 2. Fresh monorepo rather than building into india-study-map — 2026-10-18

The existing app is real (349 files in `src/`) but it is a research and
content workspace: 41 loose entries at the root, one-off HTML files, data
dumps. The new design is a full platform redesign with its own structure and
a backend that has no natural home there.

`india-study-map-app` starts clean with `web/` and `api/`. The old repo stays
untouched as a reference, and its valuable parts (`src/data`, `src/modules`)
get ported deliberately rather than inherited by accident.

---

## 3. Answers are identified by text, and only official keys are scorable — 2026-10-18

Inherited from schema v3 and reinforced after review. Two parts:

Storing the answer as option **text** on the canonical question, with each
appearance mapping its printed order via `option_order`, is what makes a
reprint with shuffled options unable to inherit the wrong letter. It also
means `attempts.chosen_text` survives a key correction and can be re-scored.

Separately, `v_scorable` admits only `answer_source IN ('official','key')` —
12,454 of 77,751 rows. 40,675 answers are model-inferred, which at the
measured ~91% high-confidence accuracy implies thousands of confidently wrong
"correct" answers. The project's own extraction guide already says a model
"may never write `official` or `key`"; the first draft of `v_scorable` did
not enforce it.

**Known hole:** ~1,508 questions print the same option text twice, so text
cannot identify which position was right. They are flagged
`source_defect = 'duplicate-options'` and excluded from both views until a
human fixes them.

---

## 4. Build locally, deploy artifacts — 2026-10-18

`npm run build` on one Ampere core is slow and competes with the running
site. Builds happen on a developer machine; `scripts/deploy.sh` rsyncs
`web/dist` to `/srv/study/public`. The server never compiles frontend code.

---

## 5. The bank is authored locally; the server database is a derived artifact — 2026-10-18

The question bank is edited locally, by hand and by various models, with
`mpsc-question-bankv2/bank/mpsc_bank_v2.json` under git as the single source
of truth. `scripts/sync-bank.sh` pushes it to the server. The sync is
one-way, re-runnable, and never reaches outside the bank tables.

What this buys: several models can work the bank in parallel, every change is
a reviewable diff, and the server can be rebuilt from scratch — which matters
on a free-tier box that Oracle may reclaim.

**Two classes of data, and they must never be synced alike:**

- *Bank data* — papers, questions, options, answer keys. Authored locally,
  overwritten on every sync.
- *User data* — users, attempts, posts, votes, reports, moderation. Created
  on the server, **never** touched by the sync. Losing it is unrecoverable;
  there is no local copy to restore from.

**Open tension — resolve before the Admin Console ships.** Admin is designed
to correct wrong keys and OCR errors, which are edits to *bank* data made on
the *server*. Under this decision the next sync destroys them. The intended
resolution is that admin writes to a correction queue which is exported back
into the local JSON, so fixes reach the server only through the normal sync.
The alternative — letting the server own `answer_text`/`answer_source` while
local owns the rest — splits truth by column and reproduces the local/prod
divergence that has already caused trouble on another project. Until this is
settled, do not build admin writes that mutate `canonical_questions`
directly.
