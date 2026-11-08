# Public answer language

Policy `study-answer-language-v1`, 8 November 2026. Applies to learner question
cards, paper browsing, practice, mock results and answer-source filters. The owner
requested clear, confident product wording without routine AI/model attribution.
This display policy does not change answer acceptance or scoring rules.

## Public vocabulary

| Existing state | Public label | Meaning |
| --- | --- | --- |
| Official / transcribed official key | Official key | Answer from the examination authority |
| Derived answer with completed answer review | Verified answer | Answer accepted through the answer review workflow |
| Available working, without asserting review | Worked solution | Describes the solution content, not verification |
| Answer not yet accepted | Suggested answer | Available for study; not presented as verified |
| Conflict, hold or unresolved source defect | Needs review | Keep the specific issue and scoring restriction visible |
| Explanation body after permitted reveal | Explanation | Distinct from options; no implied verification from its presence |
| No answer | No answer yet | Honest empty state |

Use concise labels on the card. Put supporting source and scoring details in the
existing expandable source panel. A reviewed answer may be called Verified answer
without claiming an independent human review. Do not add AI solved, model names,
provider names, generated confidence or processing/batch labels to routine learner
badges. Keep actual model/reviewer provenance, owner delegation, original candidates,
publication receipts and correction history in admin and audit records. Answer
questions about provenance truthfully; this policy does not authorize false claims.

Official keys remain distinct from reviewed solutions. Provisional-key notices,
conflicting option choices, holds and score exclusions remain visible. Do not rename
an unreviewed suggestion Verified answer, infer answer verification from accepted
tags, or treat an explanation as an official key. No warning is required merely
because AI assisted preparation; warnings must describe a real unresolved issue.

## Implementation

Use `web/src/lib/answerStatus.ts` for shared public status and source-help copy.
Badges, legends, filters and answer comparison should use the same vocabulary.
Keep internal enum values, database review states, answer sources, reveal gates and
scoring rules unchanged. Presentation changes apply to existing records at render
time; no bank migration, review rerun or history rewrite is needed.

Existing learner explanations may contain the exact historical footer “Original
printed source and ordered choices independently reviewed. Verified worked solution,
unofficial; no matching examiner key is asserted.” The presentation helper omits
that exact trailing process certificate, leaving the reasoning and actual answer
status visible. Stored text, receipts and admin history remain untouched. Do not
use broad AI-word or warning removal: substantive assumptions, conflicts, source
defects and references must remain. New explanations must not append this footer.

An explanation is optional learner content. Omit an empty explanation section;
do not imply an accepted answer is incomplete solely because prose is absent.
Use the subject-specific expectations in QUESTION-REVIEW-RULES.md: useful technical
working where supported, simple facts without filler, and Mizo explanations only
where reliable language/source evidence supports them. Answer/source review and
actual conflicts remain separate from explanation availability.

For changing facts, an explanation may show **At the time of this exam** followed
by **Update — checked DATE**. State the newer fact's effective date or reporting
period and link its inspected primary source. Newer facts supplement the historical
answer; they do not replace the official key or imply the old answer was wrong.
Keep updates concise and retain applicable stale/recheck notices.
