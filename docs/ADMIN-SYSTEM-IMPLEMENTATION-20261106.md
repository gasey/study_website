# Admin bank organisation — 6 November 2026

Implemented the workflow and data-model changes from [the review](ADMIN-SYSTEM-REVIEW-20261106.md) in the existing React/FastAPI/PostgreSQL application. The admin tools are deployed at [Modules & schemes](https://study.hawayu.in/admin/bank?tab=organization). This delivers the machinery for cleaning the bank; it does not claim that all 82,383 records have been semantically reviewed or that other external banks have been imported.

## Daily cleanup

Open **Questions → Learning tags**, or follow the exact-source correction link from the workbench. The inspector retains the selected question, appearance, source paper, filters and return location. Fully tagged questions can be opened for semantic correction. Save/submit and next use the existing correction and publication rules; failures retain the current item and draft.

Filter by provider, module, paper, primary subject/topic/subtopic, related path, era, region and time context. Save a named view to retain a scope and resume position under your account. Primary classification and additional learning paths remain separate operations using the existing controlled taxonomy and bounded batch tools.

The workbench now opens the existing correction editor inline for tags, text, source and explanation. This avoids another screen transition while retaining the source snapshot and existing permission/MFA checks. Main navigation has four destinations: Work queue, Questions, Papers, and Modules & schemes; specialist tools remain accessible.

## Learning topics and context

GK/GS are one discovery grouping with an explicit mapping to the original stored taxonomy IDs. The picker, filters and learning projection share that mapping. Historical IDs and classifications were not rewritten. English now has additive Writing → Essay, Précis and Letter paths in both the database taxonomy and authoritative registry.

**Context & repeated questions** records controlled region and language, static/dated/changing-answer behaviour, reference period and date basis, evidence, checked date and review-due date. Existing dated-fact connections remain the place for reviewed factual updates. These facets are independent of source provider, module membership and learning paths; they do not replace historical keys. Context becomes stale when its source/classification changes.

A subject-only classification can be recorded as intentional with an evidence reason. It leaves the missing-topic queue only while its source and classification still match. This prevents forcing narrow or speculative tags onto genuinely broad questions.

## Legacy and current exam schemes

**Modules & schemes → Exam schemes** supports custom, legacy, current and unknown editions, with immutable revisions. Each revision describes paper names, format, duration, marks, negative marking, qualifying threshold, sections, exact/indicative allocations and written choice groups. Unknown rules remain empty. Source URL, SHA256, evidence page and explicit source inspection are required before a revision can be marked verified.

Draft templates cover legacy/custom, Non-Gazetted 2024, MCS prelims 2025, Gazetted 2025 and Non-Gazetted general 2026. They are starting points, not saved approvals. No effective date or missing historical marking rule was invented. Recruitment-specific applicability must be checked against the source notice and amendments. The 2026 technical-route naming inconsistency remains documented in the review; no synthetic technical template was introduced.

**Paper readiness** links an individual paper to an exact scheme revision and paper key, source provider, corpus and explicit era. Existing papers are not automatically called current or legacy. The layout editor stores every appearance ID in reviewed order and assigns printed sections; restarted question numbering is supported. New scheme revisions do not relink historical papers.

**Source providers** registers exam boards, books, websites, mocks and other origins. Existing MPSC/website fallbacks remain; unknown providers are explicit. Registering a provider does not import its questions or establish completeness. **Modules** links to the existing versioned module composer and cleanup scopes; there is no second master bank.

## Original papers, practice and repeats

Paper counts represent printed appearances. Original-paper viewing retains individual source positions and can display reviewed sections/order. Practice and full simulation are explicit modes. Full simulation requires source-current layout, complete positions/locators/figures, a verified pinned scheme, complete supported timing/marking rules and every position eligible for official-key MCQ scoring. It stores the scheme snapshot with the session.

Written/mixed papers, compensated/excluded positions, repeated canonical IDs in one paper, incomplete sources, choice groups and unsupported variable-mark structures remain available for original-paper study/eligible practice and cannot silently become incomplete full simulations. This release does not implement written-answer marking or a variable-mark simulation engine.

Repeated wording is a candidate for source comparison, not an automatic merge. Reviewers can record keep-separate, same-concept, same-question or extraction-duplicate relationships against both source snapshots. The immutable relationship history preserves all IDs, appearances, answers and attempts.

Generated collection/section mocks may use one candidate from a current reviewed same-question/extraction-duplicate group, only when the MCQs have matching answer text and option sets. Selection prefers official, then key, then derived answer provenance. Stale links, conflicting answers, different options and same-concept links do not suppress candidates. Original-paper sessions preserve printed positions. This is deliberately narrower than global canonical merging or deduplication of every practice surface.

## Validation and release

- 127 focused backend tests passed, including disposable-PostgreSQL integration tests for source/role boundaries, legacy revisions, context invalidation, saved-view ownership, related filters, preserved appearances, repeat selection and pinned full-simulation rules.
- Six focused frontend regression scripts and the TypeScript/Vite production build passed. The new organisation check covers exact fully-tagged deep links, return scope, old query aliases, controlled topic/related filters, GK/GS storage IDs and the inline editor's next action.
- Migration 0078 was rehearsed on a disposable production dump clone. Source/question/classification/attempt/assignment/grant fingerprints were unchanged. Its applied checksum is `1bfb8122231d4686`; the applied file was not rewritten.
- The deployment stages only the inspected API files, checks deployed preimages and retains rollback backups. Frontend task-start assets matched the previously deployed build before the new build was published.
- Live checks cover API health, public answer-free paper readiness, anonymous rejection of staff organisation routes, frontend assets, worker restoration and the family site.
- The authoritative question-bank JSON SHA256 remained `b6d5920f9b951694cb6c92426ff0b8d6fa3b70ce7b82a2ead8f055edd0eb80e0`. The only canonical-bank filesystem edit was additive taxonomy definitions through the authority/lock/backup workflow.

Aggregate release evidence is in `reports/admin-system-implementation-20261106/`. No authenticated staff visual QA, real-size filter latency benchmark, labelled classification pilot or exhaustive 80k-question content review was performed. Those are remaining acceptance tasks, not completed work implied by deployment. No bulk model run, fabricated human review or mass reclassification was started.

For implementation/model guidance and the inspected official MPSC sources, see the review. The next content step is a measured representative English/GK/GS cleanup pilot, then bounded reviewed batches using these tools.

## Solo-owner follow-up

The later [solo-owner release](SOLO-OWNER-WORKFLOW-20261106.md) adds optional
routine notes, automatic factual change summaries, explicit owner paper/test
publication and an interactive live database map. Independent review remains
available; ordinary user submissions retain it. The [quick start](ADMIN-QUICK-START-20261106.md)
describes the current controls and remaining source/content work.
