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

---

## 6. Anonymous device ids before real accounts — 2026-10-18

Progress is attributed to a client-generated UUID in `localStorage`, sent as
`X-Device-Id`. The server creates a `users` row per device on first sight, so
attempts have a real foreign key and nothing special is needed later.

This is **not authentication.** The header is forgeable and identifies a
browser, not a person. Nothing that matters may be gated on it — no payments,
no moderation powers, no private data. It exists so practice, mocks and
mistake review can be built and tested now, without first standing up
registration, password reset and session management.

When accounts arrive, a signed-in user adopts the device's attempts by
reassigning `attempts.user_id`. Deferring the choice also avoids committing
to email/password versus Google before it is known which one users want.

---

## 7. shiksha-dev is a source to harvest, not a database to sync with — 2026-10-18

Three stores now exist: the local bank JSON, the Oracle VM's `mpsc`, and
`mpsc_study` on the old shiksha-dev droplet (140,552 questions, 26,490 of
them absent from our bank). The instinct is to keep all three in sync. That
is a triangle, and triangles do not converge: when two corners edit the same
question there is no rule for which wins, and the result is the local/prod
divergence that has already cost time on another project — with an extra
corner.

The topology is a **line**:

```
shiksha-dev  ──import──▶  local bank JSON  ──sync-bank.sh──▶  Oracle VM
 (archive)                 (source of truth)                  (derived)
```

Exactly one authority at each step. Nothing is ever written back to
shiksha-dev, and nothing is written into the VM except by `sync-bank.sh`.

**Why the old server can be demoted to an archive:** it has no users. Its
nginx log is 113 distinct IPs of vulnerability scanners (`wp_filemanager.php`,
`opsh.php` and friends — all harmless, the box has no PHP installed at all).
Its newest data is ~11 days old and was written by us, not by learners. It is
a working box, not a production service.

**Import rules, which are not optional:**

- Its answers arrive as `inferred` at most. `mpsc_study.questions` has no
  `answer_source`; 64,706 rows carry an `answer_index` with no provenance,
  and `verified_by`/`key_disputed` are empty on every row. Importing those as
  `official` would inflate `v_scorable` from 12,454 genuinely keyed questions
  to tens of thousands of unprovenanced ones and destroy the single guarantee
  the product rests on.
- Its `subject` is not an improvement: 138,355 of 140,552 rows are the
  placeholder `'gk'` — 98%, against our 90%.
- Explanations are the clearest win: 70,839 of them, against roughly 18 in
  our bank.

Note `api.map.hawayu.in` still resolves to the old droplet. Consolidating or
retiring that subdomain is a separate decision from the data.
