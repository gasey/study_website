# Website-user mock-test maker — 6 November 2026

Live entry: [Make a mock test](https://study.hawayu.in/tests/make). Public directory: [Shared tests](https://study.hawayu.in/tests). The creator entry is also in Create & contribute, More and the admin organisation workspace. The user clarified that this is a website-user feature, so normal signed-in accounts can create tests; staff status is not required.

The operational guide is [Admin quick start](ADMIN-QUICK-START-20261106.md). PDF Library now includes an expandable **How to use PDF Library** guide with links to Needs attention, Activity and Paper readiness. The prior [admin implementation guide](ADMIN-SYSTEM-IMPLEMENTATION-20261106.md) remains the technical delivery record for the bank tools.

## Reused model and workflow

Timed tests extend existing `learning_catalog` practice collections with an optional validated `test_config`. Authors, private drafts, optimistic revision checks, immutable history, feedback, independent review and withdrawal reuse that system. There is no second collection author/review database and no copied bank master.

Normal users enter title/instructions/main subject, select an answer basis, timer and marks, choose up to 100 existing bank questions and arrange their order. The bank picker supports official-key questions or the existing reviewed-worked-solution pool, across source scopes. Inferred/unreviewed answers are not eligible. Distinct IDs, reviewed repeat relations, source context/options and required figures are checked at save/publication/start. New MCQs still enter through the existing contribution/publication workflow before being selected.

Authors save and submit; an independent subject reviewer publishes. The ordinary review UI shows the timed settings with the question links. Publishing creates an immutable `learning_test_publications` edition containing the exact payload and private question/key/source snapshots. A draft edit leaves the published edition intact. Withdrawal clears the live pointer but retains publication and attempt history. Authors can stop their own published tests; staff retain review/withdraw permissions.

## Taking and sharing

Public pages expose title, instructions, question count, scoring/timing settings and edition, with no answer key, private snapshot or author/learner identity. Visitors can start as guests using the existing server-issued HttpOnly guest identity. Signed-in learners retain account ownership. The creator receives aggregate starts/completions/late completions per edition, not individual responses, scores or identities; starts are not presented as unique people.

The existing mock engine owns timing, saved answers, resume, server-side grading, frozen original results and later separate reassessments. Sessions reference an immutable test edition and title. Client-supplied collection, count, paper, answer-mode or marking overrides cannot replace published settings. Other active mocks/games, assessment answer gates and account boundaries remain in force. Generic old resume URLs also redirect correctly to the active shared test.

Shared tests are free, separate from ordinary mock-plan monthly allowance. A browser/account can start a specific test three times in 24 hours. Existing one-open-mock rules still apply. The builder permits up to 50 test collections per author. These are application bounds, not a claim of strong per-person identity for guests.

Copy link, WhatsApp and supported native sharing are deliberate user actions. The shared URL serves escaped server-rendered Open Graph title/description and directs the reader to the test landing page. Invitation text contains no private result. No message is sent automatically, and a share-button click is not recorded as confirmed delivery. Actual third-party WhatsApp preview rendering/delivery was not exercised.

New starts recheck the current source/presentation/key against the published snapshot. Changed, held or unsupported questions require an updated reviewed edition. Existing attempts can resume after withdrawal and retain their original questions/keys/results. This is learner-made practice, not automatic certification of an official examination or original-paper simulation.

## Verification and release

- 144 focused backend tests passed on disposable PostgreSQL databases, including five new multi-step user/guest/review/edition/privacy tests and existing bank, source, collection, scoring, assessment and editorial regressions.
- New UI checks cover normal-user creation, sign-in boundaries, save-before-submit, sharing only after review, link encoding/copy, pinned starts, old resume redirects and PDF-guide links. Existing organisation, correction, review-navigation and PDF Library checks pass. TypeScript/Vite production build passes.
- Migration 0079 was rehearsed on a disposable production dump clone. Question/appearance/paper/classification/attempt/assignment/grant/collection-history fingerprints and pre-existing mock values matched before/after. Applied migration checksum: `c14af5f359b1fe30`.
- Bounded API deployment checks inspected source preimages and appends only the new router to the deployed entry point. Release/rollback evidence: Oracle `/tmp/shareable-tests-1793975884/`. Previous frontend archive: `/tmp/shareable-tests-web-before-20261106.tgz`.
- An isolated build of task-start frontend source exactly matched all 114 previously deployed asset names and SHA256 contents before releasing the new frontend. Current entry: `index-Cof0_sdu.js`.
- Live readback covers test directory, unavailable-test 404, private management 401, route/assets, API health, restored workers and the family site. The public desktop directory and guest maker sign-in entry were inspected in the browser. No login bypass or synthetic production publication was used.
- Bank JSON SHA256 stayed `b6d5920f9b951694cb6c92426ff0b8d6fa3b70ce7b82a2ead8f055edd0eb80e0`; health remains 82,383 questions / 13,898 scorable. No question/key/classification content was changed by this feature.

Evidence: `reports/shareable-tests-20261106/`. No authenticated creator/staff responsive visual pass, real-traffic load benchmark, production test publication, actual WhatsApp sending or ad-network activation was performed. Advertising remains separate; the quick-start guide records the eventual placement approach and official policy reference. No traffic or income promise is made.

The first version is a bank-based test maker. Arbitrary form fields, direct unreviewed MCQ publishing, public leaderboards, respondent contact collection, downloadable certificates and ads/revenue configuration are not implemented. They should not be implied by “like Google Forms.” Corpus cleanup, historical scheme applicability, source imports and the labelled classification pilot remain the editorial follow-up recorded in the admin plan.
