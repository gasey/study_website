# Instructions for agents

Read `CLAUDE.md` and `docs/PLAN.md` before working in this repository.
For question tagging, classification, extraction labels or bank repairs, read
`docs/QUESTION-TAGGING-RULES.md` first and use
`docs/QUESTION-TAGGING-MODEL-PROMPT.md` for candidate work.

That policy replaces conflicting older tagging instructions. Historical reports
and archived handoffs are evidence, not authority to rerun old merges. Use fresh
Oracle sources and active registry IDs. Preserve uncertain items for clarification.
The local bank is a recovery snapshot; publication follows the guarded Oracle
workflow in `CLAUDE.md`. Never invent inspections or human sign-offs.

Before preparing a tagging packet, run `python3 scripts/audit-review-coverage.py
--output /tmp/study-review-coverage.json` and exclude already reviewed target IDs.
Use one primary booklet per established paper; see section 9 of the tagging policy.

The owner authorized acceptance/publication of the frozen saved AI tagging pass
on 8 November 2026. Read `reports/owner-taxonomy-publication-20261108/README.md`
and its exact completion ledger before continuing that work. Original candidate
files remain historical pending inputs; they do not describe current publication
state. This bounded owner delegation is not an independent human review, answer
verification, or authorization to publish future model batches automatically.
