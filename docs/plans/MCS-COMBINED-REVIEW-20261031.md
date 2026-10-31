# MPSC MCS Combined review — 31 October 2026

Review only: live read-only endpoints, current source and authoritative local bank inspected. No application, bank, account or deployment changes. Current route `/exams/combined-prelims` is explicitly Prelims; it is not a complete MCS Prelims/Mains product. No fresh visual browser review was completed in this audit.

## Findings, in implementation priority

1. **P1 — Incomplete booklets must be repaired before authentic paper simulation.** Live metadata lists 24 booklets, of which 23 contain questions. Total 1,921 questions; 1,098 eligible official-key questions; 814 need review; 9 have no answer. 2025 Paper I D has 5 questions; Paper II B has 8 and C has 1. 2023 Paper I C has 0 and Paper II C has 12. Live appearance endpoints independently confirm Paper II C 2025 only Q41, Paper I D 2025 only Q25/45/58/62/64, and the empty 2023 booklet. Local raw bank rows match these small totals: the UI did not cause the gaps. 2023 Paper II A/B/D each has 98 records and 2016 Paper I C has 102; these require source-by-source reconciliation, not forced padding/deletion to reach 100. Missing extractions versus cancelled questions are not yet adjudicated.

2. **P1 — Existing timed play is generic practice.** All 24 paper records have `rule_source=platform-default`, null duration, +1 correct / zero wrong. `MockRunner.tsx` requests 20 minutes; paper starts load all eligible paper questions, overriding the requested question count. Therefore a 100-question eligible booklet can receive 20-minute practice timing. The card discloses practice rules, but the combined tab says “Timed paper” and runner says “Paper test.” These labels are too strong for actual exam simulation. The collection-wide mock samples across both paper roles. Relevant code: `web/src/screens/MockRunner.tsx`, `api/app/routers/mocks.py`, `web/src/screens/ExamPage.tsx`, `web/src/components/ExamPaperCard.tsx`. Preserve generic quick practice, make its purpose explicit, and add authentic paper mode only after completeness, applicable rules and key outcomes are checked.

3. **P1 — Paper I/II must be the study boundary.** The collection currently has one `papers` section. Subject endpoint returns 23 bank categories; “General Knowledge & Studies” (980), Science (164), English (143), Reasoning and Aptitude (408), Mathematics (123), plus specialist subjects such as medicine/electrical engineering. The classifications may describe valid question content; their presence is not itself proof of misclassification. They are unsuitable as the primary exam syllabus navigation. Introduce source-backed Paper I (General Studies) and Paper II (Aptitude Tests) roles; derive membership from the booklet, then use canonical topic tags for revision within each role. Science must be inside the GS study path and independently filterable. English comprehension and numeracy belong under the appropriate aptitude-paper appearance. A shared question can retain appearances in several exams/papers. Do not globally rename GK to GS.

4. **P1 — Explanation coverage is poor.** Paper-card counts sum to 1,749 missing explanations out of 1,921 (91.0%). 2025 Paper I A has 100 official keys and 100 missing explanations; several 2023 booklets likewise. Official-key status establishes answer provenance, not explanation readiness. Prioritize source-verified 2025/2023 solutions, passages, diagrams and maths working. “Classified” (unclassified=0) does not imply reviewed correctness or syllabus alignment. Published unofficial solutions must retain their separate status.

5. **P2 — Identity and series need grouping.** Every current paper has null `paper_label` and `instructions`; extracted titles include “CSP”, “I-A” and “Exam Paper”. The filename fallback helps, but year → paper role → A/B/C/D booklet selection would reduce repetitive cards. Preserve separate source question numbering, option permutations, PDF mapping and key versions. Similar series must not be assumed equivalent without a verified crosswalk; never transplant an answer letter.

6. **P2 — Mains is a separate next stage.** No additional MCS Combined paper records outside this Prelims collection were found in the local bank. Current Prelims should remain usable as the first delivery target. Plan a parent MCS Combined area with Prelims and separately inventoried Mains; do not portray Mains as available merely because generic essay tools exist.

## Official scheme evidence

[2025 Gazette rules, 16 May 2025](https://mpsc.mizoram.gov.in/uploads/attachments/2025/05/ed66b8372965ef5a6f0d0742da1aa831/rules-the-mizoram-civil-services-combined-competitive-examination-rules-2025.pdf), printed pages 6–9: Prelims has two 200-mark, two-hour papers; Paper I General Studies and Paper II Aptitude Tests. Wrong answers incur one third of their assigned marks; blank answers have no penalty. Paper II requires 33%; Paper I threshold is determined by the Commission. Both papers must be attended. These rules support separate paper outcomes, not one combined percentage or a prediction of admission.

[Official 2025 scheme notification page](https://mpsc.mizoram.gov.in/post/notification-for-scheme-of-examination-for-mizoram-civil-service-combined) and [linked scheme PDF](https://mpsc.mizoram.gov.in/uploads/attachments/2025/08/fb8d7186b8634c80aa7e83e1a6dccd4c/notification-for-scheme-of-examination-for-mizoram-civil-service-combined-.pdf) were located. The latter is image-based in web extraction; per-booklet instructions, final keys, compensation/cancellations and applicable notification dates still need reconciliation before configuring scoring. Do not apply the 2025 scheme retroactively to 2014–2023.

## Proposed implementation sequence

1. Inventory each 2025/2023 source PDF, printed numbers, series, final key and amendments. Record extracted/expected counts, defects and source-backed exam rules. Retain empty/partial booklets as clearly labelled PDF/partial resources.
2. Repair missing source appearances in the authoritative local bank through normal validation/publication. Verify numbering, option order, diagrams, passages and actual duplicate relationships. Start with complete Series A as a study entry only after source validation; do not declare other series complete by copying.
3. Add exam → stage → paper-role → year/booklet relationships using the existing source-identity workflow. Keep canonical learning taxonomy independent. Add an MCS-specific GS display projection and GS/Aptitude topic panels.
4. Deliver useful explanations for ready recent papers. Track extraction, key, explanation and classification readiness separately.
5. Introduce two explicit actions: “Quick practice” and “Original-paper simulation.” Simulation requires source-confirmed rules and complete/adjudicated paper coverage; otherwise offer clearly labelled eligible-question practice. Freeze scoring/rules with the attempt, preserve historical attempts/XP, and show separate GS/Aptitude outcomes. Never extrapolate a subset score into a real pass/fail result.
6. Polish grouped year/paper/series cards, source-linked viewer, resume, wrong-answer revision and per-paper progress. Keep the existing paper viewer, source PDF tools and boxed layout.

## Acceptance checks for subsequent work

- UDC/LDC/Assistant retain General Knowledge; MCS Paper I displays General Studies and includes Science filtering.
- Paper I practice does not draw Paper II solely because a tag overlaps; printed paper membership wins.
- Paper II result explains qualifying performance only when the complete applicable scheme supports it; no invented Paper I cutoff.
- Partial/PDF-only/held/cancelled items remain explicit and cannot masquerade as a complete exam.
- A/B/C/D printed choices map correctly to canonical answers; source-specific conflicting keys enter review rather than automatic propagation.
- No regressions in official/reviewed eligibility, historical scoring, account isolation, progress, PDF page mapping or bank publication.

Evidence: local ignored directory `reports/mcs-review-20261031/` contains live collection, topic inventory and local raw-count comparison. One uncached collection read took about 1.33 seconds; this is a smoke observation, not a performance benchmark. No claim of exhaustive syllabus, final-key or historical-rule verification.
