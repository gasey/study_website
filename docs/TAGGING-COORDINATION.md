# Shared tagging coordination

The copyable entry point for every tool/model is
[TAGGING-WORKER-PROMPT.md](TAGGING-WORKER-PROMPT.md). This is a tagging candidate
queue, separate from the existing answer/explanation queue and bank publisher.
It invokes no model, creates no approval and changes no bank content.

After an explicitly authorized publication, `sync` marks current source-bound
question completions as `completed_live`, while retaining earlier drafts and
submitted proposals unchanged. This means the question has a current accepted
tagging outcome; it does not claim every historical model proposal was applied.

## One coordination authority

`python3 scripts/tagging-work.py` always connects to Oracle over existing authorized
SSH. There is no local queue fallback. The central SQLite workflow database is
`/var/lib/ism-tagging-coordination/queue.sqlite`, owned by postgres, mode-private.
Root-owned code lives in `/opt/ism-tagging-coordination/`, outside API rsync/delete.
Source reads use a repeatable-read, read-only PostgreSQL transaction. Inventory,
snapshots, approved paths and registered PDF metadata come from Oracle, not the
local recovery bank. The separate publisher still performs its own guards.

`sync` imports historical review exclusions additively, the exact frozen run's
blocked candidates, and later saved candidates outside that run. It also checks
current source-bound live completion events so an old blocked report does not
reopen an already completed target. A newer checkout can add saved work; a checkout
without old reports cannot erase previously imported history. Initial bootstrap
requires the old reports. The central store is a scheduling/candidate authority,
not a replacement for publication receipts or official bank content.

Every participant must use this command before new work. A legacy process that
manually selects targets outside the queue cannot be prevented from duplicating
work by the coordinator. Finish/import any already-running legacy packet, then
switch that process to the common prompt. Do not concurrently run `git add -A` or
commit other workers' changes in the shared checkout.

## Commands

```bash
python3 scripts/tagging-work.py status
python3 scripts/tagging-work.py sync
python3 scripts/tagging-work.py claim --worker antigravity-01 --model ACTUAL_MODEL --lane followup --size 50
python3 scripts/tagging-work.py resume --worker antigravity-01
python3 scripts/tagging-work.py save --worker antigravity-01 --file /private/draft.json
python3 scripts/tagging-work.py submit --worker antigravity-01 --file /private/candidates.json
python3 scripts/tagging-work.py release --worker antigravity-01 --reason 'Specific explanation of why this packet is being released'
python3 scripts/tagging-work.py release --worker antigravity-01 --defer --reason 'Specific missing evidence or unavailable source'
```

Choose a different worker label for each simultaneous session, including two
instances of the same tool/model. There is one active packet per label. Packets
are source-focused, at most 100 targets, and atomically reserve both canonical
and appearance IDs. Use 50 initially. `followup` revisits saved pending/blocker
work with attribution; `new` excludes all existing reviewed IDs. No batch-number
allocation is necessary. Source issues can be recorded as hold candidates.

Packet files appear in `reports/tagging-shared-tq_.../`. A successful submission
writes the same pending-candidates/oracle-packet format consumed by the existing
coverage audit. The central SQLite also retains packet snapshots, immutable draft
revisions, exact submitted JSON, hashes and workflow events. Do not call submit
a publication. Validation checks evidence fields and bindings; it cannot establish
that a model truthfully inspected a PDF or made a correct semantic judgment.

Keep/retag submissions require exact current source/document bindings, active
taxonomy parentage, explicit primary/related paths, inspection evidence and dated
context where relevant. A structurally valid hold can preserve absent evidence
without claiming an inspection. Every candidate must include `reviewer_tool` and
`reviewer_model`; record actual attribution, including any model switch.

## Interruption, ownership and recovery

Claims never auto-expire. Status exposes idle time so a slow worker cannot silently
lose its questions to another model. Local tokens in ignored
`state/tagging-coordination/WORKER.json` bind writes to a packet; retain these
privately when changing computers. Do not print, commit or paste tokens. Completed
sessions are archived under that private state directory. All workers already
have trusted operator SSH access; tokens protect against accidental cross-worker
writes, not against a malicious SSH administrator.

A claim request is saved locally before dispatch. `resume` safely replays that
same identity/token after a lost SSH response, then recovers packet, latest draft
and submitted result. Submission retry of identical JSON is idempotent. A changed
submission cannot overwrite a completed one. Only a matching active token can
save, submit or release. Release keeps all earlier drafts and audit events.
`--defer` moves the targets into a visible exception count rather than repeatedly
claiming inaccessible work. Deferred targets and lost-token/orphan recovery require
an operator follow-up; there is deliberately no automatic claim stealing. No
background model worker or scheduled review was started by installing this queue.

New-work booklet grouping uses conservative filename families only for scheduling:
one preferred registered A/1 source, with alternatives shelved and counted
separately. It proves neither equivalence nor full coverage. Variant-only content
and PDFs with opaque names need source/mapping inspection before alternate coverage
can be asserted; all alternate IDs remain in the inventory.

## Installation and checks

The initial installation is complete. For future code updates, copy
`tagging_queue_store.py`, `tagging_queue_server.py`, and `audit-review-coverage.py`
into the root-owned `/opt/ism-tagging-coordination/` directory. Preserve the SQLite
database and private worker state; never reset the queue to change models.
For backup, use SQLite's online backup API so the WAL is included consistently.
The coordinator has no daemon and needs no API/service restart.

```bash
python3 -m unittest discover -s scripts -p 'test_tagging_coordination.py' -v
```

Tests use temporary stores and artificial records only. They cover simultaneous
claims, canonical/booklet exclusions, idempotency, failed-read rollback, token
isolation, interrupted drafts, fresh-source rejection and submission preservation.

## Final publication reconciliation — 8 November 2026

Source-bound accepted live outcomes become `completed_live` while submitted packets,
drafts and results remain immutable. A later explicit owner-publication blocker
returns an older submitted reservation to the follow-up lane. The blocker must be
newer than the submission timestamp; a fresh submission after that blocker remains
submitted until its next disposition. This prevents repeated requeueing and retains
the original candidate, publication reason and audit event. No active claim is stolen.
