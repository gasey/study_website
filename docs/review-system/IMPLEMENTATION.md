# Implementation work packets

Start with SPECIFICATION.md. Work sequentially in one checkout; existing unrelated edits are present. Inspect `git status` and applicable instructions first. Do not overwrite another task's changes. Use existing architecture; do not introduce microservices, an AI approval service or a second question store.

Each packet is an integrated deliverable. Complete its tests and record file paths/commands/results before starting the next. Never report the entire system finished because one packet passes. Read only the files needed for the current packet to keep model usage economical.

| Packet | Files / work | Dependencies | Acceptance gates |
|---|---|---|---|
| P01 — contract and schema | Inspect `api/migrations`, `deps.py`, `db.py`, current scoring/report triggers. Add models/services for state transition rules and additive migrations for review entities, indexes, immutable history and permissions. Maintain `docs/review-system/ACCEPTANCE.md`; gates begin pending. | none | A03 constraints; A16 rehearsal |
| P02 — identity and API | Add strict session and scoped reviewer dependencies, CSRF checks, rate limits, idempotency; `api/app/routers/contributions.py`, `review.py`, typed schemas, register in `main.py`. Author revisions/submission, queue/decisions/appeals, permission management and holds. | P01 | A01–A04, A14 |
| P03 — evidence and module audit | Add typed evidence validation and baseline hashes; registered source locator validation; importer for existing `reports/*crosswalk.csv` and reviewed manifests. Preserve legacy/module provenance and unresolved matches. Integrate old content reports with single review intake and migrate old holds safely. | P02 | A05, A06, A11, A19 |
| P04 — publication | Extend `bank_feedback` compatibility; export/apply/receipt CLI, shared writer lock, backups, atomic write and replay. Extend `scripts/sync-bank.sh`/`bank_to_csv.py`; fix answer-only change detection; reconcile applied publication receipts and canonical revision history. Source requests/duplicate relations have idempotent fulfillment paths. | P03 | A07, A08, A12, A16 |
| P05 — effects and operations | Outbox worker, notifications, credit ledger and reversal, safe feed integration, audit access, metrics/logs/health/alerts and backup/restore runbook. Service unit/config changes scoped to this app. | P04 | A08, A12, A17, A18 |
| P06 — estimated scoring | Add eligibility from published reviewed revisions, strict/estimated mock API mode, frozen scoring snapshots and policy version. Extend mock results/reviews/profile aggregates with provenance breakdown and adjusted assessment history. Update `collections.py` stats and question pools, frontend API types, exam/paper/mock/result UI. Old clients default strict. | P04, P05 | A09–A11, A16 |
| P07 — contribution/reviewer UI | Implement v3 `/contribute`, typed editor, submission history, scoped queue, source/diff review, appeals, notifications, grants management; reuse `ui.tsx`, `ProvenanceTag`, account/session flow and source helpers. Wire header/profile/question entry points and routes. All actions call real endpoints. | P02–P06 | A01, A04, A13, A17 |
| P08 — release | Full isolated PostgreSQL integration suite, frontend browser flows, concurrency/failure/security/load checks, migration rehearsal, backup restoration, operational alerts and controlled rollout. Populate acceptance evidence and remaining limitations. | all | A01–A20 |

Suggested module boundaries: `services/contributions.py` for transactional transitions, `services/review_permissions.py` for authorization, `services/review_evidence.py` for validation, `services/publications.py` for receipt reconciliation, `services/scoring_revisions.py` for eligibility/snapshots/reassessment, and `workers/review_outbox.py`. Routers validate HTTP and delegate; avoid duplicating policy across routers and SQL views. Adjust paths only with documented reason.

## Tests that must be implemented

Use real isolated PostgreSQL for constraint/transaction/view behavior; mocks alone cannot prove locking or publication correctness. Use synthetic PDFs/fixtures with fixed hashes for review protocol tests and source mapping. Test filesystem importer against temporary bank files; never modify the real bank in unit/integration tests. Test sync on a clone. Treat seeded users and sessions as test-only.

- Unit: state graph, typed patch validation, option mapping, evidence requirements, permission scopes, scoring denominators.
- Integration: every mutation endpoint's authorized and unauthorized paths, idempotency and CSRF, quorum invalidation, report conversion, PostgreSQL locks and simultaneous workers.
- Round trip: accepted submission to feedback to local import to sync receipt, answer-only correction, replay after every failure point, unrelated-field preservation and compensation.
- Browser: author form/history, reviewer decision/request-changes, independent appeal, private/public rendering, keyboard use, mobile views, estimated mock and corrected-result explanation.
- Operations: worker termination/restart, DB unavailable, load, migration compatibility, backup restoration and alert delivery.

Add suitable test tooling only after checking installed repo dependencies. Record exact commands and fixture sizes. Use static checks/build as supporting evidence, never as a substitute for end-to-end behavior. No acceptance status is passed merely because the test file exists.

## Checkpoint after every packet

Append DEVLOG.md; update ACCEPTANCE.md and docs/PLAN.md truthfully. Record: packet, files changed, migrations pending/applied and target DB, commands/results, unresolved issues, next packet, and any deliberate deviation. Store no secrets or copied production personal data. Do not deploy from a mixed unreviewed working tree; identify the precise deployment artifact/revision and included changes.

## Escalation triggers for a stronger reviewer

Request focused review of actual diffs when changing bank ownership, canonical/appearance mapping, option identity, score snapshots/reassessment, permission inheritance, SQL locking, migrations or crash recovery. Provide reproduction and a small diff. A second model's opinion is code review evidence, never question-answer provenance or a human review vote. Continue other independent packet work while a design issue is unresolved; do not weaken a gate to make progress numbers look complete.
