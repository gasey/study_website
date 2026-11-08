# Reusable bank-completion prompt

Use this for Codex, Antigravity, OpenCode or another authorized worker. The
specialist tagging entry point remains TAGGING-WORKER-PROMPT.md.

```text
Continue completing the MPSC bank from its saved state. Preserve completed work.

Read AGENTS.md, CLAUDE.md, docs/QUESTION-REVIEW-RULES.md,
docs/PUBLIC-ANSWER-LANGUAGE.md, docs/QUESTION-TAGGING-RULES.md and
docs/TAGGING-WORKER-PROMPT.md. Use the appropriate existing specialist workflow.

Check fresh Oracle state and resume unfinished packets/requests first. Do not
restart completed batches or treat historical counts as the current backlog.
Run python3 scripts/tagging-work.py status. For tagging, claim one bounded packet
through the shared queue. Respect other workers' reservations; prioritize resolvable
blockers and reuse matching saved evidence/PDFs. Defer inaccessible work with exact
reasons instead of repeatedly attempting it.

Keep tagging, answers, source repairs and explanations separate. Tagging claims
do not reserve answer/source/fact edits; coordinate exact targets before overlap.
Inspect original wording, ordered options, figures and exam-period context. Solve
and check the reasoning. A second model is optional; agreement alone is not evidence.
Preserve official keys/booklet mappings and use existing admin conflict handling.

Explanations are optional for simple supported facts. Add useful technical working
where supportable. Mizo explanations require reliable language/source support;
never invent interpretations or filler. Blank prose alone does not reopen an
accepted answer.

For current affairs and other changing facts, check for a useful newer fact/event.
Browse and inspect current primary sources. Explain the original exam-period answer,
then prepare a concise “Update — checked DATE” with the newer fact's actual effective
date/reporting period and source link. Never substitute today's officeholder, figure
or winner into the old answer. A later change is not itself an official-key conflict.
Use existing dated-fact revisions, source-bound links and recheck deadlines; reuse
valid evidence across matching questions. Tagging-only work records update leads.
If no useful change is established, omit filler. If current evidence is unavailable,
record that internally rather than claiming unchanged or inventing a checked date.

Public wording follows the current policy: useful reasoning and clear answer labels;
model names/process certificates belong in admin/audit history. Verified means the
answer-review requirements were actually satisfied. Retain real conflicts/holds.

Save partial work and submit candidates through guarded workflows. Publish only
within current explicit authorization; previous bulk approvals do not cover future
batches. Respect existing provider/spending limits. When one lane is exhausted,
inspect the next real backlog without restarting the bank or adding unrelated UI work.

Report packet IDs, unique outcomes, unresolved issues, dated-update outcomes,
submission/publication state and exact resume command. Completion requires applicable
applied publication and live readback.
```
