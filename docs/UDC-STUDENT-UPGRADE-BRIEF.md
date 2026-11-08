# UDC finalization brief for Sol

Reviewed 1 November 2026 against the public guest UI at https://study.hawayu.in/exams/udc and https://study.hawayu.in/exams/combined-prelims, plus current local frontend source. This brief records the original review and implementation sequence. The first frontend release implements P0 and the mistake-preview improvement. The2Novemberfollow-up implements bounded sessions, saved order/position, summaries and targeted mistake practice. Synthetic account/guest/check/reveal/replay/finish workflows and responsive layouts were exercised; live verification avoids fabricated answers to real questions. Evidence and limits are recorded in DEVLOG.md.

## Student verdict

UDC already has useful subject filters, answer provenance, source PDFs, saved-journey support and a mistake review panel. The priority is making the next study action obvious and giving practice a manageable finish. Avoid adding more dashboard widgets.

## Confirmed audience and scope

The user confirmed that this module is for students preparing specifically for UDC. Broader preparation is an optional later move to Group B Non-Gazetted, not the default UDC experience.

- Keep subjects, questions, paper lists, practice sessions, mistakes and progress scoped to the UDC collection throughout navigation and resume. Shared Assistant/UDC papers remain valid where their source explicitly includes UDC; do not exclude them just because the title also names Assistant.
- Subject shortcuts must open UDC-filtered study, not an unrestricted subject bank. Global exam-focus settings must not silently widen the UDC collection.
- Remove the prominent UDC/LDC/Assistant switcher from the UDC overview. Other exams remain available through Exams.
- Add one secondary link near the bottom of the overview or after a session: “Want broader practice? Explore Group B Non-Gazetted.” Target `/exams/group-b-non-gazetted`. Do not interrupt practice with this suggestion or automatically mix that bank into UDC sessions.
- Keep UDC progress distinguishable when the student opts into broader study. Preserve existing shared-question progress semantics; do not invent an incompatible tracking system.
- Prelims is a reference for clear structure and booklet presentation, not a syllabus or content source to copy into UDC.

Scope acceptance: starting, filtering, resuming and reviewing a UDC session retains the UDC collection; no automatic cross-exam recommendations dominate its primary actions; broader Group B practice requires an explicit navigation choice.

## Observed comparison

| Area | UDC | Prelims | Decision |
| --- | --- | --- | --- |
| Starting structure | Generic clerical switcher and GK/English shortcuts | Explicit GS and Aptitude paper choices | Use UDC subject shortcuts driven by available taxonomy; use paper roles only when source metadata establishes them |
| Booklets | 2025 Paper I A–D and Paper II A–D occupy eight cards | Series selectors inside paper groups; 30 booklets shown in 15 groups | Reuse the grouping presentation, with safe UDC grouping metadata |
| Coverage | 3,859 questions; 32 official-key questions; one 100% bar labelled Past papers | 2,967 questions; 1,546 official-key questions | Remove UDC's uninformative coverage bar; explain available practice separately from official keys |
| Navigation | Seven views/actions, plus repeated subject and practice links | Similar repeated navigation | Simplify both eventually; implement and verify UDC first |
| Practice | Opens question 1 of 3,569 with pagination above and below | Shared question-browser implementation | Add bounded sessions; keep full-bank navigation in Browse |

Counts are snapshots, not constants. Official-key availability does not prove overall answer quality; verified unofficial solutions are a separate category.

## P0 — finalize the student entry point

1. Put a single primary Start practice / Continue practice action first. Reuse ExamJourney checkpoint logic rather than building another resume system. Keep Review mistakes alongside it. Show subject shortcuts next, then a short recent-paper preview and View all papers.
2. Use five primary destinations: Overview, Subjects, Past papers, Practice, Progress. Make Browse questions a secondary action. Offer Timed practice explicitly; replace the ambiguous Exam label. Preserve existing deep links and URL filters.
3. Remove the single-section 100% Question coverage bar. It measures bank composition, not syllabus completion or student mastery.
4. Group UDC booklet series into one card per actual exam sitting and paper. Match department/recruitment, year/date and paper identity, not year alone. Unknown identities remain separate. Preserve each series' question order, PDF, key and source appearance. Do not merge question records or answers. Prelims' year/role grouping must not be copied blindly into UDC.
5. Show concise answer-source badges and retain their explanations on demand. Explain whether a timed set uses official keys or reviewed unofficial solutions, its size and marking rules before starting. Never call a mixed or partial set a full exam simulation.

Acceptance: a new student can start practice within two deliberate actions; returning students have an obvious resume action; all eight 2025 booklet sources remain reachable without eight separate top-level cards; old browse/paper URLs still work. Grouping tests must cover same-year different departments and unknown metadata.

## P1 — make practice feel finishable

1. Add 10/20-question sessions with a subject choice and clear Question 3 of 10 progress. Handle smaller eligible pools honestly. Keep unrestricted browsing available separately.
2. Replace duplicate page-number controls in session mode with Previous, Check answer and Next. Keep provisional selection and explicit checking; Show answer remains reading mode and must not award attempt credit.
3. End a session with correct/wrong/skipped totals and Review mistakes / Practise again. Distinguish viewed answers from attempted questions.
4. Save the session question IDs/order, position and filters using the existing persistence conventions. Verify refresh/resume and account/guest boundaries. Avoid a second incompatible progress store.
5. Let students retry mistakes without revealing the answer in the queue preview. Current ModuleProgressPanel renders `answer: ...` beside missed questions; retain answer reveal in the review interaction instead.
6. Review the prominent "Retry after 30 minutes" copy: clarify that reward eligibility and learning/re-reading are different. Inspect backend rules before changing behavior; do not loosen scoring protections as a copy fix.

Acceptance: no duplicate attempt on repeated checks; revealed answers earn no accuracy/reward credit; refreshing preserves session context; completing a short set provides an actual finish state; empty/partially reviewed pools do not produce misleading scores.

## Remove or demote

- Repeated Start practice and Subjects & topics buttons across the hero, clerical block, journey and tabs.
- Empty community-material panels from the main overview; display them when content exists or behind Resources.
- XP/rewards as a prominent next-step action; retain access in progress/account areas.
- Cross-exam switching as a large content block; keep other exams in Exams navigation and offer only the secondary Group B Non-Gazetted expansion link described above.
- Long source filenames and repeated metadata above the question; keep a short source line and expandable details, with provenance still visible.
- Global social/plan/inbox distractions during a practice session: consider a compact study header as a separate scoped change after checking navigation accessibility.

Do not remove PDFs, answer-source distinctions, correction/report links, written questions from browsing, historical paper coverage, or progress history. Simplify presentation rather than deleting study material.

## Implementation locations and verification

- `web/src/screens/ExamPage.tsx`: overview, hero, navigation and paper rendering; changes here affect multiple exam types.
- `web/src/components/ExamJourney.tsx`: existing continue/resume behavior.
- `web/src/components/McsBookletGroup.tsx`, `web/src/lib/mcsBooklets.ts`: presentation reference; currently MCS-specific, including a hard-coded collection ID.
- `web/src/components/ExamPaperCard.tsx`: source and test actions.
- `web/src/screens/ModuleStudy.tsx`: practice browser and progress/mistake display.
- `web/src/components/ExamStudyTopics.tsx`: reuse taxonomy-backed subject/topic navigation.

Inspect applicable repository instructions and current work before editing. First ship P0 as a focused change, then P1 session behavior. Validate UDC and regress Prelims/LDC/Assistant because components are shared. Check 360px and 390px mobile widths, keyboard navigation, long titles, no horizontal page overflow, filtered deep links, loading/error/empty states and source identity after booklet switches. Run the repository's appropriate build/check commands and meaningful tests for grouping and session behavior. Do not claim performance gains without measurement; retain existing request prefetching and lazy loading unless profiling justifies changes.
