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
web/             Vite + React 18 + TS + Tailwind  → static, served by Caddy
api/             FastAPI + psycopg3               → uvicorn on :8000
api/migrations/  NNNN_*.sql, applied by migrate.sh
docs/            PLAN · DECISIONS · DESIGN-FIDELITY · design/ (the prototypes)
scripts/         deploy.sh · migrate.sh · sync-bank.sh · harvest_old_server.py
```

## Where things already live

- **Design handoff** — `docs/design/` (four `.dc.html` prototypes +
  `README.md`). High fidelity: colours, type, spacing and copy are final.
  They are references, not code; recreate them in React. The prototype
  markup beats the README where they disagree.
- **Schema** — `api/migrations/`. This repo owns the schema; the bank repo
  keeps only v1/v2 as history and a pointer README.
- **Bank data** — `../mpsc-question-bankv2/bank/mpsc_bank_v2.json`,
  77,751 questions across 1,938 papers. That repo is the data workshop
  (2 GB of PDFs, parsers, OCR) and stays separate.
- **A second, older corpus** — `ssh shiksha-dev`, database `mpsc_study`:
  140,552 rows, 26,490 questions absent from our bank, 70,839 explanations,
  and **no answer provenance at all**. An archive to harvest from, never a
  peer to sync with (DECISIONS #7).

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

## Working in parallel with the server

Two streams run at once: the bank is edited locally, and the server
accumulates attempts, reports and corrections. They do not collide, because
ownership is split by *what* the data is, not by where it lives.

| Data | Owner | Travels |
|---|---|---|
| questions, options, answer keys | local bank JSON | local → server, overwritten each sync |
| attempts, posts, reports, moderation | server | never synced, never touched |
| corrections *proposed* on the server | `bank_feedback` | server → export → local → back in a sync |

Start any session by asking who is ahead:

```bash
./scripts/sync-bank.sh --check
```

It prints both bank checksums and says IN SYNC or SERVER IS BEHIND, plus how
many proposals the server is holding. Every sync writes a `sync_log` row —
the bank checksum it carried, and the attempt count before and after — so
"did that sync eat my data?" is answerable from the table rather than from
memory.

**The server never edits bank content directly.** It raises a row in
`bank_feedback`; the fix is applied to the local JSON and reaches the server
through the normal sync. One authority for bank content, work still possible
on both sides. See DECISIONS #5 and #7.

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
4. **This VM is shared. Never rewrite `/etc/caddy/Caddyfile`.** It serves
   `family.hawayu.in` (Vansa) as well as us. Our config lives in
   `/etc/caddy/sites/study.hawayu.in.caddy` and the top-level file only
   does `import /etc/caddy/sites/*.caddy`. On 2026-10-18 a wholesale
   `sudo tee` of the shared file deleted Vansa's block and took that site
   down for some time — the cert was still on disk, so it failed as a TLS
   handshake error rather than a 404, and the session that caused it only
   checked its own URL and never noticed. After touching Caddy, systemd or
   Postgres, **curl the other site too**.
   Also: never add `log { output file ... }` — the packaged unit sets
   `ProtectSystem=full`, so `/var` is read-only and Caddy refuses to reload.
   Logs go to journald.
5. **`subject` and `difficulty` are NULL on purpose.** The old values were a
   placeholder `'gk'` on 90% of rows and a default `'medium'` on 96%. Do not
   "restore" them; they are being reclassified, and `subject_source` records
   where each one came from.

## Running locally

```bash
cd web && npm install && npm run dev      # :5175 (registered as "ism-app")
```

`web` proxies `/api` to the deployed service by default, so no local
database is needed. To run the API locally instead, tunnel the DB — it is
localhost-only on the server — and point the proxy at it:

```bash
ssh -L 5433:localhost:5432 ubuntu@152.67.31.231
cd api && .venv/bin/uvicorn app.main:app --reload   # :8000
DATABASE_URL=postgresql://mpsc@localhost:5433/mpsc API_TARGET=http://localhost:8000 npm run dev
```
