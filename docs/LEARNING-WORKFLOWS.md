# Intake, quality review, continuation, correction updates and daily revision

Implemented 24 October 2026, following the user's five-workflow request and Astra's architecture review.

## Entry points

- `/admin/bank?tab=intake`: expected-paper intake, within the existing admin console.
- `/admin/bank?tab=quality`: scoped quality totals and question-repair drilldowns.
- `/library` and personal `/desk`: Pick up where you left off and daily revision.
- `/revision`: account-owned daily sessions; one durable session per India date and question focus.
- `/inbox`: correction notices in Score updates, linking to the question update and affected original/adjusted mock results.

## Authority and permissions

Canonical questions, options, keys and tags remain local-bank-owned. These features never write a canonical answer. Existing proposals, independent reviewer quorum, publication worker and sync receipts remain mandatory for content corrections. Intake stages describe operational paper handling, not answer confidence. Difficulty is not reintroduced.

Intake reads require a global inventory grant. Writes require owner/publisher, current CSRF, same origin, existing staff MFA policy and optimistic versions. Quality discovery respects approved subject classifications and grants, including subject-only reviewers. Personal requests require a registered session and exact X-Learning-User binding; writes use CSRF/origin/rate/body limits. Private responses use private, no-store. No private catalog caching is introduced.

Migration 0051 adds intake state, practice checkpoints, daily-session IDs/completion receipts, correction events and notification references. Previously applied migrations are unchanged.

## 1. Paper intake

Stages: Discovered → Acquired → Extracted → Review → Ready → Published. Every transition has an evidence/change note and append-only inventory event. Cannot skip forward; can move back for repair. Failures stay at their actual stage and clear only on a successful retry. Stale saves return 409. Source identity replacement restarts acquisition and invalidates old extraction/review.

Acquisition records PDF SHA256; browser hashing reads a selected PDF locally without uploading it. Produce extraction evidence locally:

```sh
python3 scripts/extract-paper-intake.py /absolute/path/paper.pdf --output /absolute/path/intake-output
```

The tool writes extracted.txt and artifact.json with source/text SHA256, pages, character count, tool and review caveat. Load artifact.json in the admin form. It is text extraction, not automatic question segmentation, answer solving or figure recovery. Low-text documents fail visibly; OCR/reviewed transcription remains an explicit operator step. Retain the extracted text with the artifact in the local data workshop.

Review requires a linked registered paper. Ready additionally requires the inventory's explicit current source-context check and an actual matching archived PDF hash. Published checks the stored review fingerprint again, actual PDF hash again, nonzero imported appearances, exact expected count when known, and a completed bank-sync receipt. The normal local-bank import/publication path must populate the paper; changing an intake dropdown cannot import or verify answers.

A published row can become stale after paper context changes. Its stage is retained as historical evidence and the UI flags the stale review. Publication does not assert that every answer/explanation is verified. Unknown expected counts remain unknown; the existing paper diagnostics help staff establish them. Expectations are not a complete official archive census and unmatched is not confirmed missing.

Both authenticated inventory export and scripts/export-bank-inventory.py now include bank_paper_intake. Export is server operational metadata → local snapshot, never a server overwrite of the canonical JSON. No scheduled export was introduced.

## 2. Quality review

Totals: unanswered MCQs, disputed keys, missing MCQ explanations, flagged missing figure images, explicit unresolved-source context issues, Needs review and held. Counts are distinct canonical questions; categories overlap. Exam/year must match the same printed appearance. Missing-figure checks also apply to that selected paper/exam/year. Subject grants constrain both totals and the existing repair list.

Drilldowns retain subject/exam/year and enter the existing question/source inspector. Missing passages/directions alone are not labelled defects. Only an explicitly flagged unresolved source or recorded missing diagram is reported as such. These are coverage/triage filters, not bulk answer approval. Each repair follows existing versioned review/publication.

## 3. Continue studying

The account summary aggregates existing mock current_position/server clock, active vocabulary card/resume_id, focus session, next unfinished desk task and new practice checkpoint. An expired mock remains resumable for submission; no new timer starts. Expired vocabulary cards are omitted. Focus timers at their end offer the existing completion flow.

Practice position is recorded after successful shared-card answers and when opening a question. Checkpoints allow only internal study routes and whitelisted filters, validate question/source identity and compare expected version. They contain no answers or arbitrary redirect URL. Continuation opens a current question panel inside the original module/filters; it does not force navigation into the Bank. This is current question continuation, not restoration of an already-revealed transient feedback panel. Original attempts remain separate.

Checkpoint saves are best effort after the core answer is saved; failure cannot roll back or fabricate the actual attempt. A later successful checkpoint replaces the older position. Account changes clear personal panels and in-flight responses are discarded or rejected by the account header.

## 4. Correction notifications

DB triggers record actual changes to canonical question text/options/answer evidence/explanation/presentation/scoring availability, affected source context/figures, and applied/reverted review publications. No-op updates and unrelated syncs create no event. No historical backlog is invented by migration.

The existing supervised reassessment worker also processes bounded correction batches (up to ten batches of 100 recipients per 15-second tick). Each event/recipient notification is idempotent, with one generic notice even when the question is both saved and attempted. Saved IDs come from account desk JSON; earlier attempts qualify independently. Notifications respect the existing scores preference and silent-inbox behavior. A source context change and a canonical change in the same import may legitimately create separate events; retries of one event do not duplicate its notice.

Notices contain changed field names, never keys or explanation content. Detail requires ownership of the notice and existing overlapping mock/game/cup disclosure guards. It links affected submitted mocks to their original and append-only adjusted assessments. Practice and mock records are never rewritten. Worker failures are retained, shown with score/correction jobs in admin Overview and retried through the existing owner-audited retry action.

Recipients are evaluated when an event batch runs; a recently added bookmark can therefore receive an earlier pending event. Notification fanout is eventual, not an email or push delivery claim. Existing score reassessment notices remain separate and can accompany the more general question-update notice.

## 5. Daily revision

Candidates combine latest unresolved mistakes (using existing adjusted assessments when available), account-saved questions and due/invalidated vocabulary. Only the existing official or independently reviewed practice pool qualifies; unreviewed derived answers are excluded from this daily assessed flow. Paper browsing remains available elsewhere. Active mocks/games/cups exclude their questions from discovery and existing answer guards recheck on use.

Pick up to 20 distinct IDs, reserving up to eight due-vocabulary, eight mistakes and four saved slots, then fill unused space from the remaining eligible candidates. Overlaps count once. There is one durable plan per account/Asia-Kolkata date/focus; retries and multiple tabs reuse it. A real later practice/review attempt creates an idempotent completion receipt through a DB trigger. Clients cannot tick arbitrary completion, create a second grade or mint completion rewards. Existing first-answer reward limits remain the only source of study rewards.

Vocabulary entries route to the existing automatic scheduler with a target question and return link; active existing cards resume instead of allocating duplicates. Once a target is consumed the helper returns to ordinary scheduling. Already completed/now-held/removed/ineligible items do not block the rest of the session. Saved questions recur on future days until unsaved; this does not introduce a separate generic confidence/SRS engine.

## Acceptance and evidence

Reports: reports/learning-workflows. Isolated PostgreSQL tests cover route/account/CSRF protection, optimistic conflicts, same-source identity, daily mix/dedup/completion, account isolation, active mock/unreviewed exclusions, correction retry/preferences/no-op/answer gates, scoped dashboard consistency and complete intake gates/stale context/failure recovery/actual archive hash. Existing full suite and frontend checks are also run.

Synthetic browser rehearsal: saved activities, revision start→answer→completion, audited acquired stage, dashboard→missing-explanation workbench, current-question continuation within English. Production checks are read-only. No production fake learners, answers, reviews, approvals or points are created.

Read-only live data profiling initially found a 4.4–4.7-second daily query. Restricting eligibility to materialized personal candidate IDs and suppressing JIT only within that small query's transaction reduces unnecessary full-bank eligibility work and bounds compilation overhead. Final sampled query times were 400.57ms for the Mizoram focus and 265.09ms for All exams; retained in query-timings-final.txt; they are samples, not public-load certification.

Deployment script now changes static-file ownership only under /srv/study/public. Protected registered-document ownership is restored to root:www-data (directory750/files640); a web release must never recursively chown the whole /srv/study tree again. Shared Caddy is unchanged.

## Remaining boundaries

Automated official-site crawling, OCR/AI parsing and automatic question import are not added by these workflows. Staff still review extraction/source identity and use the existing canonical bank worker for publication. Email/push delivery, physical-mobile certification, high-concurrency/load and disaster-recovery exercises remain separate. Feature delivery does not mean the entire question bank has been verified.
