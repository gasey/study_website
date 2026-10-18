# India Study Map — agent working notes

MPSC exam-prep platform. Question bank, per-question discussion, user-made
study materials, games and duels, exam calendar, paid plans.

## Read this before touching anything

Whoever picks this up next — human or model — reads these four files first,
in this order. They exist because the same mistakes were being rediscovered
every session.

| File | What it holds | When you write to it |
|---|---|---|
| `CLAUDE.md` (this) | Layout, server, rules that must not be broken | A rule changes |
| `docs/PLAN.md` | Milestones, as checkboxes | Tick a box when work lands |
| `docs/DECISIONS.md` | Why a choice was made, and what was rejected | Any choice expensive to reverse |
| `docs/DESIGN-FIDELITY.md` | Exact values pulled from the prototype | You extract a new screen's spec |
| `DEVLOG.md` | Dated, append-only account of each session | **Every session, before you stop** |

**The devlog entry is not optional, and it is not a changelog.** Record what
you measured, what broke, and the trap you hit — the dead end you wasted an
hour on is worth more to the next session than the feature you shipped. Write
it as prose someone can act on, with real numbers.

Append; never rewrite history. If a past entry turns out to be wrong, add a
new entry saying so rather than editing the old one — that correction is
itself the useful record.

Before building a screen, read `docs/DESIGN-FIDELITY.md` and extract the
values for that screen from the prototype. The handoff README's token summary
is a simplification and disagrees with the markup in several places.

## Layout

```
web/    Vite + React 18 + TypeScript + Tailwind   → static, served by Caddy
api/    FastAPI + psycopg3                        → uvicorn on :8000
docs/   PLAN.md, DECISIONS.md
scripts/ deploy.sh
```

## Where things already live

- **Design handoff** — `../mpsc-question-bankv2/design/` (four `.dc.html`
  prototypes + `README.md`). High fidelity: colours, type, spacing and copy
  are final. They are references, not code; recreate them in React.
- **Schema** — `../mpsc-question-bankv2/db/mpsc_schema_v3.sql`, reviewed and
  tested. Migration guide in `../mpsc-question-bankv2/docs/`.
- **Bank data** — `../mpsc-question-bankv2/bank/mpsc_bank_v2.json`,
  77,751 questions across 1,938 papers.

## Server

Oracle Cloud Ampere A1, 4 OCPU / 24 GB, Mumbai. `ssh ubuntu@152.67.31.231`.
Postgres 16 (localhost only), Redis 7, Caddy 2 serving https://study.hawayu.in.
DB credentials in `/etc/mpsc/db.env` (root-only). Test database `bench`
already holds the full migrated bank.

## The schema is expected to change as features land

It is not frozen. v3 was written before most of the product existed, and
each feature will want columns, indexes or views it does not have. Changing
it is normal; changing it *carelessly* is what breaks things, because the
server database is derived from a local bank (DECISIONS #5) and a hand-made
`ALTER TABLE` on the box diverges from the repo silently.

So every schema change is a numbered file in `api/migrations/`:

```bash
./scripts/migrate.sh --status    # applied vs pending
./scripts/migrate.sh --dry-run   # rehearse on a dump clone; prod untouched
./scripts/migrate.sh             # apply
```

- Name them `NNNN_what_it_does.sql`; they run in filename order.
- **Never edit a migration that has been applied.** The runner checksums
  them and refuses, because an edited migration means the repo and the
  server disagree about what the schema is. Write a new one.
- Each file owns its transactions — `BEGIN`/`COMMIT` inside the file.
- `--dry-run` restores a dump into a throwaway clone rather than using
  `createdb -T`, which would need exclusive access and therefore downtime.
  It takes ~15s and includes real data, so backfills are rehearsed honestly.
- Prefer a **view** over a denormalised counter column. At this size
  aggregates run in milliseconds, and a counter is one more thing to keep
  honest when attempts are re-scored after a key correction.

## Build with the data that exists

The bank is incomplete on purpose and will improve later: ~69,757 questions
are unclassified, nothing is deduped, 11,459 MCQs have no key. **Do not block
features on that work.** Build against the 12,454 questions with official
keys and the 59,047 with any answer.

Where a control cannot be honest on today's data, show a short explanation
instead of the control — the topic filter and the repeats filter already do
this. Do not fake it, and do not hide the feature; say why it is empty.

## Rules that are not negotiable

1. **Never score a user against an inferred answer.** Only 12,454 of 77,751
   questions have an official key. `v_scorable` is the only source for mocks,
   duels and cups; `v_practice` is the wider pool and the UI *must* label
   those answers unverified. This is the project's own rule — see the
   extraction guide: a model "may never write `official` or `key`".
2. **Never `ORDER BY random()`.** 19.8 ms vs 0.67 ms for an id draw, and it
   degrades as the bank grows. Draw ids in the app, fetch by primary key.
3. **Never build on the server.** One ARM core makes `npm run build` painful.
   Build locally, rsync the output. `scripts/deploy.sh` does this.
4. **Never add `log { output file ... }` to the Caddyfile.** The packaged unit
   sets `ProtectSystem=full`, so `/var` is read-only and Caddy refuses to
   reload. Logs go to journald.
5. **`subject` and `difficulty` are NULL on purpose.** The old values were a
   placeholder `'gk'` on 90% of rows and a default `'medium'` on 96%. Do not
   "restore" them; they are being reclassified, and `subject_source` records
   where each one came from.

## Running locally

```bash
cd web && npm install && npm run dev      # :5173
cd api && uv run uvicorn app.main:app --reload   # :8000
```
