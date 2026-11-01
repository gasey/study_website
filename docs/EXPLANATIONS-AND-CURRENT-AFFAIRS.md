# Explanations and current-affairs context

MCQ/written response is the question format. Official/transcribed key, derived solution and inferred suggestion describe answer provenance. Published answer verification and explanation availability are separate. These presentation changes never grant scoring eligibility, clear holds or modify historical answers.

After answering, Bank, question detail, module study and paper browsing show a shared explanation panel:

- Missing text: “Explanation not yet available”, even when an official key exists.
- Official-key answer with text: “Explanation available”; separate explanation review is not inferred from the key.
- Published reviewed derived solution: “Reviewed solution working · unofficial”, unless the current item is disputed or requires source review.
- Unreviewed or held working: “Stored explanation · needs review”.

The explanation-only contribution link uses the existing audited proposal workflow. Admin and contributor forms ask for the rule/calculation, relevant distractors and supporting source; changing facts require exam-date and effective-date context. Nothing automatically labels arbitrary existing explanations as checked.

## Editorial workflow

For a substantive explanation, inspect the exact printed question, ordered choices, source page and current keyed/derived answer. Explain why the choice follows, show calculations or deductions, and discuss plausible distractors where useful. Prefer a short useful explanation over generic option-by-option filler. Use primary references for facts; record their dates. If the reasoning disagrees with the recorded answer, use the existing answer-adjudication workflow rather than editing explanation text to disguise a conflict. Preserve source identity, compensation holds and provenance.

For time-sensitive questions, distinguish the fact at the exam date from a newer dated fact. Keep the historical bank answer/scoring unchanged. A generic caution or portal link does not certify an update. Do not add a newer officeholder or figure without inspecting a dated primary source.

The small editorial revision-note registry lives in `web/src/lib/questionCurrentness.ts`. Each note has an ID, inspected-source date, event/period date, review deadline, revision hint and direct reference. Historical context must be narrowly bound to the original question/year. The Shibu Soren note is limited to 2025; Finance Commission and Budget notes are topic comparisons, not certification of the original answer. Do not add answer indices, scoring flags or key provenance to these notes.

Learners see date context first. Answer-bearing notes and reference links render only after answering or an explicit “Reveal revision context” action, which also works for unanswered/source-held items and does not submit an attempt. Switching question/year resets that reveal. An expired note remains clearly dated and marked “Recheck due”; it is not presented as verified current information. Unknown updates say no question-specific update was checked. This is an editorial workflow, not an automatic news feed or automatic answer rewrite.

Maintainers add/review a note after checking its source, then run the frontend tests/build and deploy the frontend. Learners can propose dates/sources through Suggest correction; existing server proposal/publication safeguards remain in force. A full browser-managed current-affairs editorial queue and separate per-explanation review metadata are future work, not features claimed by this release.

## Sources inspected on 1 November 2026

- Shibu Soren: Akashvani, 4 August 2025, https://newsonair.gov.in/former-jharkhand-cm-shibu-soren-passes-away/ — identifies the former Jharkhand Chief Minister and event date. Supports the existing 2025 example's context; no current officeholder is asserted.
- Finance Commission: Ministry of Finance report, https://www.indiabudget.gov.in/doc/16fcvol1.pdf — award period 1 April 2026 to 31 March 2031; official report listing also inspected at https://fincomindia.nic.in/ .
- Union Budget: Ministry of Finance, https://www.indiabudget.gov.in/ — 2026–2027 documents and separate Budget/Revised/Actuals context. No numerical budget answer is transferred between years.

Source check dates are editorial records. They never imply an official examination answer key or independent peer approval.
