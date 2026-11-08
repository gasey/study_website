# How to use the admin tools

The [implementation guide](ADMIN-SYSTEM-IMPLEMENTATION-20261106.md) is a record of what changed, how it works and what was tested. It is not an installation step or another tool you need to run. The website already has those admin changes.

## Start with PDFs

Open [PDF Library](https://study.hawayu.in/admin/bank?tab=pdf-library), sign in with your staff account, and open **How to use PDF Library** for the short guide inside the website.

1. **Find the paper first.** Search its exam/paper name. Use More filters for year, document type or next task. Open the item, then **Open PDF** or **Preview PDF**. Check that it is the exact paper and booklet you intend to handle.
2. **Choose the work that is missing.** Open **Needs attention**. **Import questions** finds registered sources that need transcription. **Unlinked PDFs**, **Registration** and **Conflicts** are source-identity tasks. They do not mean “publish everything.” Use the action shown on the matching item to continue its existing work. Use **Upload PDF** only when the source is absent; search first to avoid another copy.
3. **Inspect the workbench draft.** Compare it with the PDF: identity/year, printed numbers, section instructions, text, all options, shared passages, diagrams and answer-key references. An extraction finishing does not establish that its questions are correct. Written questions stay written.
4. **Preview and publish as owner.** Save the draft, select **Preview publication** in **Publish as owner**, and check its counts against your source inspection. Select **Publish this saved paper as owner** when ready; the note is optional. This records your own decision. The optional independent-review section remains available for a future team. **Draft & publication receipt** shows whether publication succeeded. **Activity** shows processing jobs, failed jobs and the latest completed bank sync. A published receipt and bank readback establish completion; a processing job alone does not.
5. **Put the paper in the right place.** Open **Coverage, sources & history** for registration/coverage. Use the module workspace to add reviewed source membership. Use [Paper readiness](https://study.hawayu.in/admin/bank?tab=organization&organization_view=paper) to set provider, corpus, legacy/current/unknown era, exact scheme edition, printed sections and order. An old paper must not inherit the newest scheme automatically.

## Sort and fix bank questions

Use [Question tagging rules](QUESTION-TAGGING-RULES.md) for GK/GS, Current Affairs,
cross-exam English and uncertain classifications. Future models must use the
[candidate prompt](QUESTION-TAGGING-MODEL-PROMPT.md); old merge instructions are retired.

Open [Learning tags](https://study.hawayu.in/admin/bank?tab=retag). Choose a manageable scope: provider → module → source paper, then subject/topic or a specific issue. Save a named view so you can return to it.

**Exam year** is visible beside Bank and Sort in Learning tags, and beside Exam
in [Questions](https://study.hawayu.in/admin/bank?tab=questions). Enter the full
four-digit year to filter original paper appearances; leave it blank for all
years, or use the applied year's **Clear** button. This is the exam/paper year,
separate from a current-affairs event's reference period. Other exam/source
filters stay selected. [Papers](https://study.hawayu.in/admin/bank?tab=papers)
also has an **All years** dropdown. Year filtering does not change paper metadata.

Open a question with its exact source, inspect it, change the primary learning path, and add related paths only for genuinely additional knowledge being tested. Use **Save & next** or **Submit & next** according to your permission. A failed save keeps the current item. Publication status is separate from a saved or submitted correction.

As a global owner, you can leave **Owner note** empty for ordinary tag, text/OCR,
explanation and source-page/printed-number corrections. The server records what
changed and who saved it. **Save & next** saves your decision and advances; it
does not invent an independent reviewer. Use a note for unusual decisions that
your future self would struggle to understand. Changing the correct answer still
needs supporting reasoning and the existing solution/key evidence. Holds and
scheme verification also keep their reasons/evidence.

For a batch of similar tag fixes, select up to 20 questions, preview once and
apply. Your owner note is optional. Review the preview for exceptions before
applying; unrelated topics should not be swept into the same batch.

Treat cleanup as constructing and polishing a reusable bank: first establish the
original source, then correct question/options, assign one primary learning path
and useful related paths, and finally fix answer/explanation evidence. Work one
paper or saved issue queue at a time. Modules reuse the same questions; copying a
question into another module creates needless cleanup work.

## See the database

Open [Database map](https://study.hawayu.in/admin/bank?tab=database), also linked
from the admin header. **Content flow** explains papers → printed positions →
shared questions → modules/tests. **Tables & foreign keys** shows actual live
database links and columns. Choose an area, select a card, follow its connected
tables or open its related admin tool. Zoom, scroll, search or switch to **List**
on a smaller screen. **Refresh live counts** updates the figures.

This is an owner-only, read-only map of selected content/workflow tables. It
does not expose learner answers, private rows, credentials or a SQL console.
The topic-coverage meter measures missing detail, not whether tags are correct.

Use **Context & repeated questions** for region/language, reference period, changing-answer behaviour and source-backed repeat comparisons. A region, source board, exam year or module is not an extra subject tag. GK/GS display together for discovery while their historical IDs remain traceable. English Writing includes Essay, Précis and Letter paths.

## Legacy examinations

Open [Modules & schemes](https://study.hawayu.in/admin/bank?tab=organization). Choose **New custom / legacy scheme**, or begin with an appropriate draft template. Enter only rules supported by that paper's applicable notification. Leave unknown timing, marks or penalties empty. Verify source/applicability before marking a scheme verified, then link each paper to its exact revision through Paper readiness.

Changing a scheme creates a new revision. It does not silently change historical paper links or completed attempts. Mixed/written/incomplete papers remain available for study even when they cannot run as complete scored simulations.

## What remains from the bank work

The admin software was implemented and deployed. These content and acceptance tasks remain:

- Check a representative English/GK/GS, Mizoram, technical and legacy-paper pilot for classification accuracy and correction time, then scale bounded reviewed batches.
- Review and repair the corpus itself: missing/misplaced topics, OCR/options/figures, source references, unsupported answers and explanations. The tools did not automatically classify all 82,383 records.
- Verify scheme applicability and configure actual papers; supplied templates begin as drafts.
- Continue source imports from the reconciled PDF backlog. Unlinked PDFs must be identified before being treated as new papers.
- Complete authenticated staff desktop/phone visual checks and benchmark the new combined cleanup filters on the real-sized bank.

The dated audit figures and their qualifications are in [the review](ADMIN-SYSTEM-REVIEW-20261106.md); use the live queues for today's workload.

## Website-user mock tests

This is a learner feature, separate from admin bank repair. Use [Make a mock test](https://study.hawayu.in/tests/make), also available under **Create & contribute** and **More**.

1. Sign in, enter a title/instructions, choose the main subject, time limit, marks and answer basis.
2. Find existing eligible bank questions, add up to 100, inspect their sources and arrange their order. New MCQs use the existing bank contribution workflow, then become selectable after publication and scoring eligibility.
3. Ordinary website users save the draft and submit it for independent review. Staff review it in [Learning collections](https://study.hawayu.in/learning/manage?kind=practice). As owner, choose **Preview owner publication**, inspect the questions/settings, then **Publish test as owner**; it saves the exact current draft before publication. A second person and a typed reason are optional for this owner action.
4. After publication, open the test page, copy its link or choose **Share on WhatsApp**. WhatsApp/native sharing opens only when you select it; the website does not send messages automatically. Your private answers/result are not included.
5. Visitors can take the published test as guests. The server owns timing/scoring and saves the question/key/rule snapshot. Shared tests are free, with three starts per test in 24 hours, separate from ordinary mock-plan allowance.
6. The creator can see aggregate starts/completions by edition and stop new attempts through **Stop sharing / new attempts**. Learner identities, individual scores and responses are private. Withdrawn links stop new starts, while existing sessions and completed results remain accessible to their owners.

This first version assembles tests from the bank. It is not an unrestricted form builder, public leaderboard or mechanism for collecting respondents' phone numbers/emails. Draft edits stay private until another approved edition is published through an owner decision or independent review. Changed/held sources block new starts until the test is updated; existing attempt snapshots stay intact.

## Popularity and advertising

Share useful reviewed tests with a direct route back to the website. Measure actual starts and completions; no traffic, share delivery or ad-income estimate is fabricated. Advertising is not configured by this feature. An ad account, approved placements and the site's applicable consent/privacy setup remain separate work.

Plan any eventual ads in clearly labelled, separated areas of the landing/results pages. Keep question options, timer, Next and Submit controls clear of ads. Google's current [AdSense placement policy](https://support.google.com/adsense/answer/1346295?hl=en) specifically cautions against ads near interactive/navigation controls that can cause accidental clicks. No approval or ad earnings are implied by the layout.
