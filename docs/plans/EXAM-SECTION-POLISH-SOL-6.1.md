# Exam section polish — Sol 6.1 implementation handoff

Prepared 28 October 2026. Implementation delivered29 October2026; see the delivery record below. Source-dependent review follow-ups remain pending.

## Outcome

Make the exam section easy to enter, quick to load and comfortable to practise in on a phone. Start with UDC/LDC/Assistant, then apply the reusable improvements to Group B and Combined Prelims. Keep one shared question bank with each exam's own source identity, paper structure and test settings.

This is refinement of the existing application, not a replacement design. Use the existing typography, colours, cards and controls from docs/DESIGN-FIDELITY.md and docs/design. Prioritize a shorter route to questions over adding decorative panels.

## Read before implementation

1. CLAUDE.md, docs/PLAN.md, docs/DECISIONS.md and docs/DESIGN-FIDELITY.md.
2. docs/CLASSIFICATION-AND-PAPER-IDENTITY.md and docs/GROUP-B-COMMON-SUBJECTS.md.
3. reports/udc-ldc-access-performance-20261028/STATUS.md, live-http.json and live-parity.jsonl.
4. Relevant code below and the current live screens. Historical counts in older documents are snapshots, not current requirements.

Run scripts/sync-bank.sh --check and inspect the working tree. This workspace contains substantial existing changes; preserve unrelated work and take targeted backups before editing. No new worktree, separate chat or subagent is required for this handoff.

## Rules already decided

- One canonical question bank. Exam membership and source appearance determine where a question is used; learning tags determine its content topic.
- UDC's knowledge heading is **General Knowledge**. UDC/LDC/Assistant currently use this learning presentation. Preserve each paper's verified printed wording; do not invent GS sections from stored taxonomy.
- Cross-exam discovery may use **GK/GS**. Preserve the compatible `gk-gs` discovery alias and existing stored taxonomy IDs.
- General English and knowledge study are shared across Group B streams. Specialist papers remain separately selectable through reviewed paper-role mappings. Do not infer recruitment status or technical membership from a filename or a leftover category.
- Printed paper/section names, marks, negative marking and duration need source evidence. Learning topic groups are not a claim about the official syllabus.
- Preserve question IDs, option order, original exam-date answers, progress, checkpoints and source-bound submissions.
- Only approved taxonomy is learner-visible. Corrections use the existing reviewed contribution workflow. Do not batch-relable content just to make a page look tidy.
- Preserve official-key versus verified-unofficial versus needs-review distinctions and existing scoring eligibility. Do not reintroduce difficulty labels.
- The owner's unlimited Pro grant is complete. Billing activation, access-extension administration and payment configuration are outside this polish plan.

## What is already implemented

Do not rebuild these features:

- Exam pages, paper cards, subject/topic study, browse/practice, progress and saved journeys.
- UDC/LDC/Assistant switching and own-exam English/GK shortcuts.
- General Knowledge labels in clerical topic maps and broad question badges.
- Active-exam source selection for questions shared between exams.
- Group B common/technical areas with explicit source rules.
- Admin paper identity editing and individual/batch retagging previews and review.
- Faster question queries and pagination without an unconditional250ms delay.

Recent live HTTP samples: UDC questions0.62s, LDC0.43s, UDC knowledge-filter questions0.98s. One cold UDC collection-detail request took3.12s. These are observations from one connection, not percentiles or service guarantees. Backend comparisons preserved all seven collection responses and seven question-query results apart from intentional source appearance selection.

## Priority 1 — Clear exam entry and page hierarchy

Inspect `/exams`, `/exams/udc`, `/exams/ldc` and `/exams/assistant` before changing their structure.

- Make exam cards consistently show exam name, available paper/question coverage and a clear study entry.
- On an exam page, prioritize the exam title, Continue/Start practice and Subjects & topics. Keep Past papers immediately accessible; place less frequent actions in the existing navigation.
- Reduce repeated hero actions, explanatory panels and competing calls to action. Avoid requiring learners to scroll through the same guidance every time they return to practice.
- Keep concise answer-provenance labels visible beside questions. Put longer explanations in accessible disclosures; do not hide the distinction between official and unofficial scoring.
- Show the active exam and current subject/topic clearly. Shortcuts should navigate and move focus/scroll to the relevant content, including when the target mounts asynchronously.
- Avoid a full new dashboard. Reuse existing saved-journey and progress components.

Acceptance: a learner can reach GK or English questions from the exam landing page in one action, identify the active exam, and return to the same topic using browser Back. The next study action is visible on a390px-wide phone without scrolling through multiple explanatory cards.

## Priority 2 — Remove the remaining loading bottleneck

Profile the current route before editing. Separate API time, frontend route/chunk loading and rendering; record at least five cold and five warm observations under stated conditions. Report median and range rather than inventing p95 from a tiny sample. Keep the existing before/after report for comparison.

- Trace ExamPage's dependency on full collection details before mounting its question panel. Questions already prefetch in parallel, but their display still waits for metadata.
- Prefer progressive rendering: let the requested question view become usable while secondary counts, paper metadata and personal panels resolve.
- Preserve the mounted practice component, selected answers and displayed feedback when late metadata arrives. Do not implement a loading branch that remounts the active question browser.
- Use stable skeletons for initial content and a small updating indicator for filter changes. Prevent stale results from being answerable under a newly selected filter while a replacement request is pending.
- Deduplicate matching requests and canonicalize default query parameters so prefetch and visible requests share the same cache key.
- Keep prefetch bounded to the next useful page and respect data-saving behaviour. Clear/invalidate personalized results when attempts change queue membership.
- Retain bounded readiness/source queries. Do not cache answers, bypass eligibility checks, or introduce a full-bank fetch to avoid loading indicators.
- Add an explicit retry for failed data loads. A failed secondary panel must not block otherwise available questions.

Acceptance: ordinary pagination has no deliberate delay and does not jump to a blank page; late or out-of-order responses cannot replace the current filter's results. Show an improvement in cold time-to-usable-question against the measured baseline. Aim for under2s on the same test connection and no regression from current warm question-request timings; if the target is missed, report the measured cause and finish the safe improvement rather than hiding it behind cached-only measurements.

## Priority 3 — Comfortable question practice and mobile filters

- Keep subject/topic and the active selection easy to see. Move less-used paper, section, answer-status and personal-status controls into a clearly labelled filter disclosure on small screens.
- Provide an obvious reset and a readable summary of active filters. Preserve selected source, exam, topic, answer pool and page in the URL where supported.
- Preserve the existing one-question practice and25-question browse modes. Keep count and pagination text consistent and disable only controls whose action is actually pending.
- On Next/Previous, move to the question heading or results start without trapping keyboard focus. Keep answer feedback and source links reachable on mobile.
- Keep touch targets at least44px and eliminate body-level horizontal overflow at390px and768px. Intentional tab scrolling may remain within its own container.
- Cover empty results, missing answers, missing diagrams, invalid filter values and end-of-queue states with concise, actionable copy.

Acceptance: complete a synthetic practice flow, change a topic, reset filters, navigate back, and resume the saved position without losing the exam context. Verify keyboard focus and a phone-width layout. Do not submit fabricated answers or create synthetic users on production.

## Priority 4 — Paper cards, schemes and exam identity

- Standardize paper cards around year, verified printed paper heading where available, booklet/series, question coverage and the relevant browse/practice action.
- Keep duplicate booklet appearances distinguishable without suggesting they are unique canonical questions.
- Show verified timing/marks where configured. Label platform-default practice settings clearly; never present a partial eligible set as a complete official paper.
- Keep question totals, official-key totals and reviewed-practice totals distinct. Do not add overlapping topic counts to claim a collection total.
- Audit a small representative set:2025 Assistant/UDC mixed Paper I, an older UDC GK/arithmetic paper, an LDC paper, a Group B common paper and a technical paper. Use their registered PDFs and current admin identity workflow.
- Collect suspicious content tags or missing source identity into a review docket with question/paper IDs and evidence. Existing Shibu Soren and specialist-looking UDC tags require review; do not declare them fixed through display changes.
- If centralizing presentation labels, use a small explicit exam configuration and preserve all current API/URL contracts. Avoid a broad taxonomy migration during polish.

Acceptance: the learner can distinguish a source paper from a revision topic group, see why a timed test is available or unavailable, and open the correct original source. UDC must not acquire a General Studies paper heading. Group B common study must not absorb specialist questions through a broad fallback.

## Priority 5 — Verification and release

Use focused checks for changed behaviour rather than expanding the test suite for cosmetic adjustments.

- Re-run relevant existing tests and add regression coverage only for meaningful state, scope, scoring or loading bugs discovered during implementation.
- Check source membership, question IDs/order, counts and answer readiness before/after for UDC, LDC, Assistant, Group B and Combined Prelims. Keep source-aware option handling and saved progress intact.
- Check390px,768px and1280px layouts; verify loading, empty, error and populated states. Save screenshots of the actual final screens.
- Build locally. Follow the established targeted deployment workflow, inspect remote drift and retain rollback backups. Never replace the shared Caddy configuration. After service/database changes, verify both study.hawayu.in and family.hawayu.in.
- Confirm bank sync remains correct; append DEVLOG.md and update docs/PLAN.md with what actually shipped and any evidence-dependent follow-ups.
- Final report: changes, live links, measured timings with cold/warm distinction, tests, screenshot and specific remaining limitations.

## Primary code locations

- `web/src/screens/Exams.tsx` — discovery/cards.
- `web/src/screens/ExamPage.tsx` — hierarchy, metadata loading and view navigation.
- `web/src/screens/ModuleStudy.tsx` — question loading, filters, practice and progress.
- `web/src/screens/PaperViewer.tsx` — printed-order paper browsing.
- `web/src/screens/GroupBStudy.tsx` — common versus technical study.
- `web/src/components/ExamStudyTopics.tsx`, `ExamJourney.tsx`, `Pagination.tsx` — topic entry, resume and navigation.
- `web/src/lib/api.ts`, `requestCache.ts`, `questionLabels.ts` — request reuse and contextual labels.
- `api/app/routers/collections.py`, `questions.py` — scoped collection and question queries.
- `api/app/services/question_readiness.py`, `learning_taxonomy.py`, `source_identity.py`, `group_b_study.py` — policy boundaries to preserve.
- `api/tests/test_exam_context_readiness.py`, `test_collection_paper_readiness.py`, `test_source_identity_retagging.py`, `test_group_b_study.py`, `test_scoring_revisions.py`, `test_learning_workflows.py` and `web/tests/navigation.test.mjs` — existing regression coverage.

## Suggested execution order

1. Inspect current screens and establish loading/layout baselines.
2. Implement priorities1–3 together as the first coherent release; verify practice state and URL behaviour before deployment.
3. Complete priority4's source/card audit and safe presentation changes, keeping content-review proposals distinct from published corrections.
4. Run the release checks, deploy the verified result and record remaining source-dependent work.

## Prompt to give Sol 6.1

Implement `docs/plans/EXAM-SECTION-POLISH-SOL-6.1.md` in `/home/hruaia/workspace/projects/personal/india-study-map-app`. Follow the repository instructions and the existing shared-bank/exam-identity decisions. Begin with current-screen inspection and measured loading baselines, then finish the prioritized polish, verification and targeted deployment. Preserve unrelated workspace changes, question identities, progress, source context and scoring policy. Use the existing admin workflow for any content proposals. Report actual results and remaining evidence-dependent work; do not claim unfinished phases are complete.

## Delivery record — 29 October 2026

Deployed the hierarchy, progressive loading, study-filter, focus and paper-heading refinements. Metadata failure/retry and delayed arrival were rehearsed against a disposable synthetic database; selected answers and feedback survived. Scoped API regression checks passed; local layouts at390/768/1280px had no body overflow. The five-cover audit and unsubmitted content-review docket are saved separately. No canonical bank content, scoring eligibility or account entitlement was changed by this polish release.

See `reports/exam-polish-20261028/STATUS.md` for code, tests, screenshots and timing methods. The main hierarchy/loading work is implemented. Intermittent long browser observations, complete source-confirmed scheme publication and independent content-tag corrections remain explicit follow-ups; this release does not claim those are complete.
