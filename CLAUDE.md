# India Study Map — agent working notes

MPSC exam-prep platform. Question bank, per-question discussion, user-made
study materials, games and duels, exam calendar, paid plans.

This file is context for whoever picks the work up next, human or agent.
Chronological history lives in `DEVLOG.md`; the milestone checklist lives in
`docs/PLAN.md`; the reasoning behind irreversible choices lives in
`docs/DECISIONS.md`. Append to the log, tick the plan, and add a decision
record when you choose something that would be expensive to undo.

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
