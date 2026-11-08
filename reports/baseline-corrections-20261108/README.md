# Baseline Reconciliations and Conflict Resolutions — 8 November 2026

## Executive Summary

- **Total records examined across 146 candidate files:** 10,698 saved candidate records covering 10,617 unique appearances (10,617 unique canonical questions).
- **Baseline mismatches reconciled:** 476 records across Batches 15–24.
  - 377 records (Batches 15–22): Candidate files recorded coarse appearance-table placeholders (e.g. `gk` or `statistics`) while the true Oracle baseline snapshot contained active classified paths (`computer-science`, `mathematics`, etc.).
  - 99 records (Batches 23–24): Candidate files had `current_primary` and `source_fingerprint` unpopulated (`null`).
  - **Reconciliation action:** All 476 records were verified against live Oracle database tables (`appearances`, `canonical_questions`, `question_classifications`) via SSH repeatable-read transactions. 0 mismatches between saved `oracle-packet.json` snapshots and the live Oracle database. Explicit corrections are saved in `reports/baseline-corrections-20261108/corrections.json`. Original candidate files remain untouched.
- **Proposal conflicts resolved:**
  - `8dee949fbd0738eb19ad`: Q44 in Tourist Officer General English. Clause identification task. Resolves to `tagging-pilot-20261107` (KEEP English > Grammar; no invented clause subtopic).
  - `paper_c538cfe8b8bf4bd895213c85ce108c0e_draft_c208b118b1614ae328024f60`: Precis task (14 marks). Resolves to `tagging-pilot-20261107` (RETAG English > Writing > Precis).
  - `paper_c538cfe8b8bf4bd895213c85ce108c0e_draft_7a4ff93d036980b7764acf6f`: Complaint letter task (10 marks). Resolves to `tagging-pilot-20261107` (RETAG English > Writing > Letter).
  - 6 overlapping Tourist Officer English items between Batch 9 and Batches 19/20 resolved with exact proposal signatures and physical PDF page inspections.
- **Post-Reconciliation Ledger:**
  - **Saved Candidate Records:** 10,698
  - **Unique Appearances:** 10,617
  - **Unique Canonical Questions:** 10,617
  - **Deduplicated Valid Candidates:** 10,617 (100% valid coverage)
  - **Baseline Issues:** 0
  - **Unresolved Conflicts:** 0
  - **Problems:** 0
  - **Live Writes:** 0 (all proposals remain pending under guarded publication rules)
