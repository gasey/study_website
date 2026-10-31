# Question-bank review handoff — 28 October 2026

## Start here

Read `CLAUDE.md`, `docs/PLAN.md`, `docs/DECISIONS.md`, `docs/DESIGN-FIDELITY.md` and the latest `DEVLOG.md` entry. The latest continuation is `reports/remaining-504-review-20261028/`; read `STATUS.md`, `local-audit.json` and `remaining-502-docket.json`. The OpenCode Go Luna priority packet is `reports/luna-solve-20261027/`; the preceding full source review is `reports/all-517-review-20261027/`. Never replay completed publication requests.

## Current verified state

- The overlapping LDC/UDC/Assistant/Group B non-gazetted union has 8,588 questions: **5,564 verified unofficial, 345 official, 502 needs-review, 1,998 unsolved and 179 written**. Do not sum individual exam totals.
- All 252 English/mathematics/computer-science questions from the original priority scope have a saved OpenCode Go Luna first-pass worked solution. Thirteen are independently verified and published (11 before the current pass, two in it); **239 remain needs-review**: English 164, mathematics 23, computer science 52. The other 263 open questions are documented in the latest 502-item docket and preceding 517-item review.
- The saved Luna drafts are available in the authenticated admin question inspector for their exact printed appearances. They remain review notes and do not alter answer status or scoring. Source: `api/app/data/luna_priority_solutions.json`, generated from the packet's `solution-register.json`.
- Strict official scoring pool: 12,708. Bank IDs: 80,547. Users: 30; attempts: 113. Pending exports: 0. Local/live bank SHA-256: `ba66d401a1314cc3d2115b28291969d81343062d84e154cc1d5f9a3bbb9141f0`. `scripts/sync-bank.sh --check` returned IN SYNC.
- The latest pass published two date-dependent unofficial answers using official exam-date and institutional records; their exact receipts and two changed appearances were audited. The remaining priority 239 were unchanged. Pending exports are 0; the review timer is active/enabled after receipt verification. The latest packet has a SHA-verified private mirror and final live checks.

## Review standard and remaining work

The owner's instruction to use Luna overrode the prior handoff's no-OpenCode preference for generating drafts. Luna made 18 successful saved calls; the owner subsequently reported a usage limit, so do not make more calls without a new need. Its answers are suggestions, not source or examiner evidence. A choice is eligible for verified unofficial status only after source inspection and an independent unique-answer determination. Many maths computations yield values absent from the printed options; other questions have missing emphasis, duplicate or incomplete options, ambiguous wording, or source/key identity problems. Keep the 239 unverified priority items in needs-review. The 1,998 unsolved items and missing MCQ explanations are separate backlogs.

The five PwD LDC final-key mappings remain unregistered because the final key is dated 8 May 2026 for April exams while source booklets say March 2026. Technical Medical Record III Q45 accepts A and B in the final key; Technical English Q35 has an incomplete option C; Lab IV Q38 repeats “Lymphocyte”. Assistant/UDC2025 Part-B comprehension Q3 is not covered by numbered Part-A key row 3. Do not force a single index in these cases.

## Safe publication

Local JSON authority is `../mpsc-question-bankv2/bank/mpsc_bank_v2.json`; never change question content directly with SQL. Begin with `scripts/sync-bank.sh --check`; stop `ism-bank-review.timer` before guarded publications and restore it after every receipt, local/live bank checksum and pending export are audited. Use trusted-owner maintenance, immutable publication, local bank sync, exact live-content verification and acknowledgement. Do not replay old exports or prepared batches. Preserve official-key provenance and active mock/game/cup protections. Append measured outcomes to `DEVLOG.md` and mirror final packets privately with SHA checks.
