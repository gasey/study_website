# Module comparison intake

Shipped 2026-10-23. Admin: `/admin/bank?tab=modules`. This implements the initial P03 module evidence intake for LDC/UDC/Assistant and Combined Prelims. It does not complete bank adjudication or every P01–P08 release gate.

## Imported evidence

| Module | Records | Current exact unique | Ambiguous repeats | No current exact match | Raw unique answer disagreements |
|---|---:|---:|---:|---:|---:|
| LDC / UDC / Assistant | 3,339 | 1,113 | 143 | 2,083 | 96 |
| Combined Prelims | 3,415 | 455 | 1,438 | 1,522 | 1 |

All 6,754 source records remain present, with 7,744 candidate links (including historical candidates) and 42 references to historical reviewed packets. These counts identify matching records and answer claims; they do not establish correctness. Six exact clerical records have a module answer but no bank answer. Earlier adjudications may explain some disagreements.

The new `unicode-whitespace-stem-ordered-options-v2` matcher preserves punctuation and mathematical operators, normalizes Unicode/case/whitespace, and requires the complete stem and ordered options. The earlier punctuation-stripping report is retained as historical evidence. Its previous counts (clerical 1,914/290/1,135; Prelims 422/1,475/1,518) are not current exact-identity counts. A historical candidate is displayed explicitly and cannot support a correction unless its live identity actually matches the module. An unchanged historical mismatch is not mislabeled as a bank update.

## Workflow

1. Filter by module, paper, question/ID, match status, answer comparison, intake disposition or import run. Default lists the latest run of each module, conflict first, 20 rows per page.
2. Inspect module/current appearance side by side, ordered options, directions, passage/emphasis, original explanation/provenance labels, source PDF/registered figure where available, hashes, historical crosswalk and reviewed packets.
3. For repeats, select an appearance explicitly. Question number alone is never sufficient. Missing live candidates and changed bank snapshots remain visible.
4. Prepare a reviewed correction only for a matching live identity. The editor keeps the current bank answer. Applying a module answer to the proposed derived answer requires an explicit action; the contributor must supply reasoning and rationale.
5. Unmatched records can prepare a source request instead of a guessed canonical mapping. Dismiss/reopen requires a reason and expected version.
6. Saving creates a normal draft and append-only link/event. Reviewers and the author can inspect the immutable citation from the contribution detail without owner directory access. A module reference may accompany independent primary reasoning/paper/official-key evidence, but cannot qualify as an official key itself.
7. Existing independent quorum, mapped registered key requirements, stale baseline checks, MFA, publication worker, canonical local-bank sync and score reassessment rules remain in force. Importing, linking or dismissing never approves, publishes, scores, pays points or changes bank content.

## Storage and access

Migration `0038_module_audit_intake` is APPLIED; never edit it. Immutable runs/items/candidates/links/events use existing append-only triggers. Only triage disposition is mutable, under a row lock and optimistic version. Run IDs/hash checks and advisory locks make imports idempotent and transactional. Source snapshots are retained independently of live bank foreign keys so missing historical targets do not erase evidence. Candidate membership and live identity are validated again when attaching a contribution reference.

Owner-only directory/list/triage; linked contribution authors and scoped review-grant holders can read cited evidence. Private/no-store responses, existing session/CSRF and staff MFA controls apply. Active mocks with any associated candidate suppress list rows and block answer-bearing detail/triage. Reference validation does not promote module provenance. Old Evidence serialization omits absent module fields, preserving existing idempotency hashes.

Import is an operator CLI, not a browser upload. Only supported generated literal data are extracted from the TS module with TypeScript AST; module code is never evaluated. Original source/crosswalk/bank/packet/answer-review hashes and previous rows are retained. The importer writes only audit tables and checks the latest completed bank sync hash by default. `--allow-historical-bank` is an explicit operator exception; use only when deliberately retaining a historical audit, never to claim a current comparison.

## Reproduce / import

Run from the app repository, with the adjacent bank and legacy module repositories present and frontend dependencies installed:

```bash
python3 scripts/import-module-audits.py --module udc-ldc \
  --source ../india-study-map/src/data/banks/mpsc-udc-ldc.ts \
  --crosswalk reports/legacy-udc-ldc-crosswalk.csv \
  --answer-review reports/module-bank-answer-review.csv \
  --packet reports/assistant-2018-paper2-adjudication.json \
  --packet reports/ldc-april-2026-reviewed-key-claims.json \
  --packet reports/udc-arc-2020-paper2-adjudication.json \
  --packet reports/udc-artculture-2016-paper2-adjudication.json \
  --packet reports/udc-socialwelfare-2018-paper2-adjudication.json \
  --output reports/module-intake/udc-ldc.json
python3 scripts/import-module-audits.py --module combined-prelims \
  --source ../india-study-map/src/data/banks/mpsc-combined-prelims.json \
  --crosswalk reports/legacy-combined-prelims-crosswalk.csv \
  --answer-review reports/module-bank-answer-review.csv \
  --output reports/module-intake/combined-prelims.json
python3 scripts/import-module-audits.py --load reports/module-intake/udc-ldc.json --database 'dbname=mpsc'
```

Use a private staged directory on the DB host and peer-authenticated operator role; never print DB secrets. Review the prepared manifest before loading. Replaying an identical manifest returns `replayed:true`; modified bytes fail the canonical manifest hash. Changed source inputs produce a new immutable run. Previous runs remain selectable; normal operations have no destructive audit-delete endpoint.

## Verification and limits

Evidence: `reports/module-intake/`. Migration rehearsed against a production dump clone, then applied. Full suite: 75 passed, one upstream Starlette/AnyIO deprecation warning. Tests cover imports/replay/tampering, punctuation preservation, historical mismatch versus actual bank changes, immutable rows, actual mpsc grants, owner/linked-author access, filters and empty-page totals, candidate membership, stale snapshots, source requests, triage conflicts, active mock protection, reference provenance and old payload compatibility. Frontend production build passes.

Disposable browser rehearsal: synthetic owner list/detail, explicit proposed alternative, primary reasoning plus secondary immutable module citation, save draft, linked intake with unchanged live answer, reviewer citation inspection, historical sign mismatch with no correction action. Screenshots are synthetic, not screenshots of real owner activity. No production draft, review decision, approval or learner attempt was created. Real import/replay receipts and read-only SQL verify 2 runs / 6,754 items / 7,744 candidates / 0 links / 0 triage events, all open, 0 missing current exact appearances, 42 packet references.

The CLI currently supports two modules and bounds each run to 20,000 records. List max 50, candidates 20 per page, latest 100 runs, linked reviews/history latest 50. The directory needs owner sign-in and staff MFA. Figure availability depends on registered bank source assets; the UI does not fabricate missing images. Repeated identities and unmatched records still require source inspection; source fulfillment, independent adjudication and remaining missing bank answers are future work. The import adds evidence, not 6,754 newly verified answers.


## Research continuation — 2026-10-23

The later batch1 research release supersedes the initial two-run counts: four immutable historical runs now retain13,508item snapshots; latest-run workspace still6,754module records.97raw disagreements map to96bank appearances.20have research assessments (15answer proposals,4retain-bank recommendations,1defect);76remain unassessed.19typed payloads are prepared only, not contributions or approvals. New Research assessment panel displays selected-target rationale/source links and payload inspection. Read reports/module-adjudication-20261023/README.md for full evidence, reproduction commands and limits. The builder scripts/prepare-module-adjudication.py never writes bank/database; source hashes and expected identity/answer/provenance prevent stale preparation.
