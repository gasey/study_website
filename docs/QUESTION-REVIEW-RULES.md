# Current question review and solving rules

Policy `study-review-v1`, 8 November 2026. This is the current content-review policy
for Codex, Antigravity, OpenCode and manual owner work. It replaces conflicting old
review/solver handoffs. Technical runbooks remain procedures, not extra content
policies. [Tagging rules](QUESTION-TAGGING-RULES.md) remain the classification policy;
[public answer language](PUBLIC-ANSWER-LANGUAGE.md) controls learner wording.

## One workflow

1. Read current Oracle state and existing evidence. Resume unfinished requests and
   receipts before selecting work. Never restart a completed review from old batch
   numbers or historical totals. Reuse earlier valid source inspection; record the
   reason and earlier decision when intentionally re-reviewing an item.
2. Work on exact bounded canonical/appearance IDs with fresh source fingerprints.
   Inspect the registered hash-matched original: printed instructions, complete stem,
   ordered choices, underlining, passages, figures, exam period and booklet identity.
   One primary booklet per established family; preserve alternate source/key mappings.
3. Solve the actual task. Check calculations, logic, grammar and option mapping;
   inspect appropriate primary references for factual claims and time-sensitive
   answers. Review the reasoning separately from drafting. A second model is optional,
   not a mandatory extra stage; agreement alone is not validation. A supported owner
   review can accept checked work without inventing another person's sign-off.
4. Keep separate outcomes for source/transcription, answer/key, explanation,
   classification and historical context. A correct tag does not verify an answer;
   an explanation does not verify an official key. Save explicit missing evidence,
   ambiguity or defects as unresolved, without guessing an option to finish a batch.
5. Store candidates with actual tool/model/operator attribution and evidence in
   admin/audit history. Complete source binding, reasoning and legitimate acceptance
   through the existing review workflow before calling an answer verified. Never
   fabricate a source inspection, reference, independent review or human approval.
6. Publish only within the owner's current explicit scope and actual role/assignment,
   through guarded proposals, immutable manifests and normal Oracle synchronization.
   Source/reasoning checks and existing permission/assignment/source protections still
   apply. Ordinary contributors retain independent review; owners use the existing
   solo-owner path where permitted. A saved draft or model confidence is not approval.
7. Finish only after applied publication and exact live readback. Preserve prior
   decisions, sources, attempts, holds and receipts. Report unique outcomes, remaining
   blockers and the resume location. Do not overwrite answers, repair question content
   with SQL, reset protection baselines or use stale local bank snapshots as authority.

## Official keys and disagreements

Official means a correctly matched examiner key with exact paper/booklet/question
mapping. Provisional and final keys retain their actual status. A reviewed worked
solution is distinct from an official key. If they disagree, preserve both labelled
answers, evidence and scoring holds; resolve through the dedicated answer workflow.
Never replace an old dated answer with today's fact or transfer option letters
between booklets. Missing or multiple valid choices remain explicit defects.

## Learner explanations

Explain why the answer follows and, where useful, why alternatives fail. Include
necessary exam-date context, assumptions and real source defects. Do not append
review-process certificates, model names, AI-generated labels, batch numbers or
blanket claims such as independently reviewed. Keep them as actual audit metadata.
Show Official key, Verified answer, Worked solution and Explanation according to
[the public vocabulary](PUBLIC-ANSWER-LANGUAGE.md). Keep concrete conflicts and
restrictions visible; never label an unaccepted answer verified for appearance.

## When an explanation is useful

Answer correctness and public explanation coverage are separate. A missing learner
explanation alone does not invalidate an existing accepted answer, create a scoring
hold, or justify reopening a finished review. Review evidence is still required;
optional public prose is not optional source/reasoning validation.

| Question type | Explanation expectation |
| --- | --- |
| Direct fact, name, date, spelling or clear recall | Optional. A supported answer may stand alone; do not repeat it as filler. |
| Arithmetic, reasoning, science, engineering or other technical task | Prefer concise useful working when the method can be supported: formula/principle, essential steps, units/assumptions and the conclusion. No artificial word count. |
| Conceptual, ambiguous or easily confused choices | Explain the distinction when reliable evidence supports it. An unresolved ambiguity blocks acceptance, not merely explanation coverage. |
| Mizo language, literature, culture, idiom or source-dependent usage | Explain only where competent language review or reliable original/reference material supports it. A known source-backed answer need not have a translation or long explanation. Do not invent etymology, meanings, literary attribution or English paraphrases. |
| Official-key answer without supported reasoning | Keep the matched official key. Do not invent a derivation to make the card look complete. |

Technical preference is not permission to guess: if working cannot be established,
retain any valid accepted key and record the explanation limitation internally. If
that limitation also undermines the answer, keep the answer unresolved instead.
Mizo is not exempt from answer verification; it is exempt from forced explanation.

In working reports distinguish `available`, `not-needed`, `unavailable-with-current-evidence`
and `needs-correction` explanation outcomes, with an internal reason for the last
three. These are report terms, not new database enums or automatic bank writes.
Do not count every blank explanation as unfinished answer review. Existing valid
explanations are preserved; remove or correct defective content only through the
normal correction workflow. Public cards omit empty explanation blocks.

Existing publication endpoint contracts still apply. This policy does not waive
required review evidence or authorize filler in an explanation-only submission;
that queue only selects items for which a useful explanation can be supported.

## Current-affairs explanations: historical answer and dated update

When reviewing a changing fact, check whether a relevant newer event or fact can
help the learner revise. If supported, include a concise dated update alongside
the historical explanation. This applies to officeholders, appointments, schemes,
rankings, statistics, awards, records and other changing facts, including questions
whose primary tag is a specialist subject rather than Current Affairs.

- First explain the answer for the question's original reference period. Keep the
  printed question, ordered choices, historical key and scoring attached to that exam.
- Browse and inspect a current primary source before asserting a newer fact. Record
  its direct URL/title, publication date, effective date or reporting period, and
  actual checked date. Model memory or the newest search-result date is insufficient.
- Present the addition as **Update — checked DATE**, with the fact's own date/edition
  stated explicitly. A report published this year may describe an older period;
  never relabel its figures as this year's measurements. Compare like units and
  definitions, and distinguish related events from directly comparable facts.
- For named award/tournament editions, retain the original winner; any later edition
  is a separately labelled revision fact. A newer fact is not an error in the old key
  and must not trigger an answer-conflict hold solely because time has passed.
- Use the existing dated current-affairs workflow at `/current-affairs/manage` for
  reusable fact revisions, source-bound links and review deadlines. A brief explanation
  addition uses the existing explanation-correction workflow when authorized, tied to
  the same inspected evidence. Do not create competing copies of the current fact.
- Reuse a still-applicable inspected revision across matching questions. Check the
  actual freshness/source context before claiming it is current; prioritize missing,
  changed or recheck-due facts. Do not research unrelated news or redo accepted tags.
- If no useful change is found, keep the explanation concise. Record internally
  whether no change was verified or current evidence was unavailable; never infer
  unchanged from a missing connection. Missing update evidence alone does not
  invalidate a sound historical answer. Omit an unsupported update.

Updates remain dated snapshots, with real sources and recheck deadlines, rather than
claims of permanent currency. Existing stale/archived notices, fact-review permissions
and answer-reveal/assessment gates remain in force. Tagging-only workers record the
update lead separately; their tagging claim does not authorize explanation/fact edits.
This policy asks future review work to prepare relevant updates; it does not claim
that current facts have already been populated or enable automatic news publication.

## Which procedure to use

| Work | Current procedure |
| --- | --- |
| Classification | QUESTION-TAGGING-RULES.md + TAGGING-WORKER-PROMPT.md; central Oracle claims |
| Existing-answer explanation backfill | AI-QUESTION-REVIEW-HANDOFF.md; checkpoint and resume its explanation queue |
| Newer current-affairs facts | Existing `/current-affairs/manage` dated-fact workflow; retain the historical exam answer |
| Answer, key or source correction | Existing admin answer/correction workflow; ORACLE-PAPER-WORKBENCH-RUNBOOK.md |
| Local solver | tools/mcq-solver/README.md; drafts only until accepted through the existing workflow |
| Public wording | PUBLIC-ANSWER-LANGUAGE.md; shared answerStatus.ts |

Explanation backfill cannot change answers or sources. The tagging claim queue
reserves tagging work only; do not treat it as an answer-solving reservation system.
For answer work, coordinate exact targets through the current review assignments
and existing drafts; do not start overlapping workers without an applicable claim.
No provider calls, spending, background worker or future bulk publication is
newly authorized by this policy. Existing billing restrictions remain in force.

## Retired guidance

The 28 October NEXT-REVIEW-HANDOFF is archived in docs/history and has no operational
authority: its local-writer/timer instructions and counts must not be followed.
The November solver discovery/pilot/source-review documents are historical evidence,
not competing review rules. The original solver implementation brief remains an
architecture reference; this policy governs current content decisions. Historical
reports, published receipts and private queues are preserved, not deleted or reset.
