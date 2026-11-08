# Instructions for agents

Read `CLAUDE.md` and `docs/PLAN.md` before working in this repository.
For question review or solving, follow `docs/QUESTION-REVIEW-RULES.md`.
Use `docs/BANK-COMPLETION-PROMPT.md` for reusable whole-bank continuation,
including source-checked current-affairs updates alongside historical answers.
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

For simultaneous tagging work across Codex, Antigravity, OpenCode or other tools,
use `scripts/tagging-work.py` and the single reusable entry prompt in
`docs/TAGGING-WORKER-PROMPT.md`. Read `docs/TAGGING-COORDINATION.md`. Claim exact
targets centrally before working, resume existing sessions and save drafts there.
Do not create a local coordination queue, choose unreserved targets, overwrite
another worker's packet or commit unrelated shared-checkout changes. Submitted
queue results remain pending candidates, not published/approved corrections.

The reconciled Batch 1632 publication is complete. Read
`reports/owner-taxonomy-final-20261108/README.md` and the latest source-bound
Oracle outcomes before continuing. Current accepted tagging outcomes: 77,791;
258 blocked; 4,334 without a saved review in this pass. Never restart the completed
frozen runs or combine historical pending files into a new publication. This owner
authorization does not extend to unseen future batches.

The owner authorized acceptance/publication of the earlier frozen saved AI tagging pass
on 8 November 2026. Read `reports/owner-taxonomy-publication-20261108/README.md`
and its exact completion ledger before continuing that work. Original candidate
files remain historical pending inputs; they do not describe current publication
state. This bounded owner delegation is not an independent human review, answer
verification, or authorization to publish future model batches automatically.

For learner answer wording, follow `docs/PUBLIC-ANSWER-LANGUAGE.md`. Keep routine
AI/model processing labels in admin/audit history, use shared public answer labels,
and never turn unreviewed suggestions or tagging acceptance into verified answers.
