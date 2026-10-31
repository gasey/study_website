# Bank administration and contribution product blueprint

Date: 2026-10-21. Status: proposal only; no implementation or deployment authorized by this planning request.

This expands the product design around SPECIFICATION.md and IMPLEMENTATION.md. Those documents describe intended behavior, not shipped capability. Their permission, revision, publication and acceptance requirements remain the technical baseline. New original community MCQs and the ranking rules below are proposed extensions; reconcile the baseline documents before implementation. Sample counts, pricing and rules in the supplied design are illustrative, not production requirements.

## 1. Product structure

| Surface | Purpose |
|---|---|
| Library | Learn and practise within Arithmetic, Mizo, English, Essay and other modules |
| Exams | Official exam structure, source papers, saved exams and timed tests |
| Bank | Cross-subject question discovery, provenance and all appearances |
| Community / Feed | Discussions, useful explanations, selected published MCQs and improvement stories |
| Contribute | Submit improvements, discover work, follow decisions and see earned credit |
| Community / Contributors | Weekly, monthly and all-time contribution leaderboard |
| Admin | Manage source content, taxonomy, review, publication, permissions and bank health |

Top navigation remains Library, Exams, Community and Study desk. Put Contribute and Contributors inside Community's navigation, with a visible Contribute action on question cards. Do not add every admin feature to the learner navigation.

Suggested routes: /contribute, /contribute/mine, /contributions/:id, /community/questions, /community/contributors and /admin. Reuse existing feed and profile routes.

## 2. Design inspiration and admin layout

Use docs/design/Admin Console.dc.html and India Study Map v3.dc.html: warm paper backgrounds, Newsreader headings, Public Sans controls, IBM Plex Mono metadata, compact filters, status chips and a grouped sidebar. Retain typography and the question editor's source/preview relationship. Use real counts and operational states.

Desktop question workspace:

    Question list / filters | Source PDF and printed question | Revision editor
                            |                               | Learner preview
                            |                               | Evidence and history

Allow resizable panes and a two-pane mode. On smaller screens use explicit Source / Edit / Preview / History tabs. Keep Save draft, Submit for review and Publish as separate actions. The visible action depends on the account's permission and the revision's state.

Admin sidebar:

1. Overview: missing answers, unresolved provenance, malformed options, missing figures, stale classifications, publication failures and oldest pending work.
2. Questions: saved filters, question editor, duplicates and bulk change previews.
3. Papers & sources: exams, sittings, series, paper sections, page images, PDF registry, official keys and import jobs.
4. Taxonomy: subject/topic/subtopic tree, aliases, version changes and affected modules.
5. Collections: exam manifests, Library query rules, explicit inclusions/exclusions and scoring rules.
6. Contributions & review: intake, assignments, evidence, conflicts, appeals and holds.
7. Community & rewards: conduct reports, public attribution, vote abuse and credit ledger.
8. People & access: contributor restrictions and explicitly assigned reviewer/publisher scopes.
9. Operations: staged releases, sync receipts, backups, job failures and immutable audit history.

The first dashboard should answer “what can I repair next?” Display counts by severity and subject, plus a short actionable queue. Activity graphs are secondary.

## 3. Editing scope

The editor must distinguish the canonical question from an individual printed appearance. An appearance owns its paper, booklet series, printed number, page, printed option order and source layout. The canonical question owns its normalized content and versioned answer identity. Expose the scope before saving.

Editable groups:

- Content: stem, instructions, passages, bold/underline/emphasis, equations, option text and order, figure references, language and question type.
- Source: registered PDF, file hash, page/crop, paper/section/series/number, and supporting citations. Uploaded files are quarantined and validated before registration.
- Answer: stable option identity, worked explanation, official/transcribed/derived/inferred status, confidence, provisional/final/superseded key evidence and dispute flags.
- Classification: controlled subject/topic/subtopic IDs, aliases, difficulty, skills, exam relevance and explicit historical/as-of dates. Difficulty estimates and human labels retain separate provenance.
- Eligibility: browse, practice, estimated mock, official-key mock, withdrawn or held, with reasons. Derive eligibility from rules rather than presenting arbitrary “make scorable” switches.
- Relationships: duplicate candidates, variants, shared passages and concept links; canonical merges require a dedicated mapping preview.

Never silently rewrite printed history. If a corrected practice rendering differs from the paper, preserve the transcription, mark the correction, and show the learner which version they see. An original community MCQ must never be assigned a fabricated MPSC paper appearance.

Every draft displays before/after diff, field validation, affected exams/modules, scoring impact and evidence. Changing options checks answer mapping and invalidates stale reviews. Bulk edits preview exact affected IDs, field changes and exclusions; support bounded jobs, resumable status and compensating revisions.

Taxonomy rename, alias, move and merge are different operations. Stable IDs survive display renames. A merge previews saved collection filters, reports and progress associations. Published taxonomy versions allow old attempts to remain explainable.

## 4. Publication and bank ownership

Today the local JSON bank is authoritative; sync-bank.sh copies bank-owned content into PostgreSQL. Direct browser edits to those server rows would be lost on later sync.

Recommended near-term flow:

    Admin or contributor draft -> immutable proposal revision -> independent review
    -> accepted revision -> publication manifest -> controlled bank worker
    -> local bank validation and atomic update -> database sync -> verified receipt
    -> published status, attribution and points

The admin UI drives the workflow; the user should not need to edit JSON or run commands for each change. A controlled worker performs the guarded publication. If the designated bank host is offline, accepted changes remain visibly awaiting publication. The app must not call them published early.

All bank writers must honor one lock and revision checks. Every publication records input/output hashes, affected canonical/appearance IDs and immutable revisions. Retry does not apply a change twice. Rollback creates a compensating revision against current data, preserving unrelated edits and user records. No generic shell command endpoint.

A later database-authority migration is possible, but would require changing every importer, classification writer and synchronization path together. Do not create two writable authorities during the admin rollout.

## 5. Contribution workflow

On every question card: Answer / Save / Discuss / Suggest correction. The correction drawer captures source context automatically. A report can be submitted without knowing the replacement answer. During timed tests, capture a flag without revealing solutions or discussions; reveal after submission.

Contribution kinds: missing answer, answer correction, explanation, transcription/formatting, image/instruction repair, taxonomy, source evidence, duplicate report and new MCQ.

The Contribute page provides My drafts, Submitted, Changes requested, Awaiting publication and Published. Opportunity lists prioritize currently useful work such as missing keys in popular exam sections. Each task shows evidence requirements and whether it is already claimed.

Workflow: Draft -> Submitted -> In review -> Changes requested / Rejected / Accepted -> Publishing -> Published. Include Withdrawn, Stale baseline, Publication failed and Reverted. Authors can appeal with new evidence. Any substantive revision invalidates previous approvals.

Two independent non-author reviewers for answer, option, stem, new-MCQ or provenance changes; one for ordinary source-location, explanation or valid taxonomy changes. Disagreement and official-key changes require senior adjudication. At a small launch, appoint a second reviewer before enabling high-impact community publication; do not invent votes to satisfy quorum. Emergency removal from scoring can be a reasoned temporary hold, with later review.

AI can suggest tags, detect likely duplicates and prepare explanations. Its suggestions enter review with model/source metadata and never count as an independent human approval. Reputation, subscription and likes do not grant review rights.

## 6. Community MCQs and learner use

Support two origins: source-paper MCQs and original community MCQs. Original submissions require an original stem, meaningful distractors, an answer rationale, topic/language, and evidence for factual claims. Check duplication, copyright and safety. Their provenance is Community-authored, with public author attribution and a review badge, never Official key.

Before approval: the author gets a private preview and reviewers get a sandbox. Drafts cannot enter public practice, rankings or exam mocks.

After publication: browse at Community -> Questions and in a community filter within the Bank. Show selected items as interactive feed cards. Library modules can offer an explicit “Include reviewed community questions” option. Official paper reconstruction always contains only that paper's printed appearances. Custom/practice mocks may offer an explicit community pool and must label it.

Question discussions use one canonical thread, linked from feed, Bank, Library and Exams. Do not copy comments into independent threads on each surface. An explanation can be proposed for adoption through review; likes do not silently replace the published explanation.

## 7. Points and leaderboard

Maintain separate concepts:

- Study progress/XP: participation and learning. Answering the same MCQ repeatedly cannot farm contribution credit. Competitive test rank comes from a defined scored attempt.
- Contribution credit: bank improvements actually published, backed by a ledger entry.
- Helpful votes: community appreciation, used as a limited discovery signal.

Initial proposed credit schedule (retain the baseline spec's simple launch values):

| Event | Contribution credit |
|---|---:|
| Published new MCQ | 25 |
| Published correction, answer, explanation, source or taxonomy improvement | 10 |
| Confirmed and published defect report | 10 |
| Submission, draft, raw upvote or source request | 0 |
| Duplicate/no-op proposal | 0 |
| Reverted publication | Reversal of its original award |

Treat related changes to one question in one proposal as one improvement award. A batch awards per distinct accepted question, not per field or click. Prevent splits of the same fix into multiple rewards. Competing duplicate proposals link to one issue; reviewers can assign documented shared attribution, with a capped reward budget. No penalties for sincere rejected proposals; deliberate abuse has a separate moderation process.

Use an append-only credit ledger with a unique publication/event key, beneficiary, amount, rule version, subject and reversal reference. Award after verified publication, never at submission or merely at review acceptance. Published changes later shown wrong reverse that award; policy changes or unrelated later updates do not automatically punish an earlier valid contributor. Exclude administrative backfills/import volume from public competition.

Leaderboard: Community -> Contributors, with weekly/monthly/all-time periods and subject filters. Show contributions published, credit, helpful explanations and a link to the actual work. Profile gets a contribution tab; Contribute gets personal progress; the feed may show a small weekly highlight.

Rank by net eligible published credit, then distinct questions improved. Equal results share rank; account age should not break ties. Periods use Asia/Kolkata boundaries. Reversal adjusts the original event's attributed period with an audit note, preventing negative activity from being misrepresented as a fresh contribution. Offer public display opt-out. No monetary rewards or automatic privileged roles at launch.

## 8. Votes, discovery and question selection

Votes answer “was this useful?” and never “is this officially correct?”. One authenticated account vote per published object; no self-voting, retry duplication or points for votes cast. Allow withdrawal. A question vote and an explanation vote target different objects. Report inaccurate content through the review queue rather than using downvotes as a substitute for evidence.

Feed eligibility first: published, permitted, not blocked/held for that use, and answer-reveal rules satisfied. Then rank with an explainable initial score; all components normalized to [0,1]:

    score = 0.40 interest_match + 0.25 freshness
          + 0.20 helpfulness + 0.15 exploration

Interest match uses explicitly followed subjects/exams. Freshness decays over roughly seven days. Helpfulness uses Bayesian-smoothed helpful votes per eligible unique impression, with a conservative prior and protection from repeated voter/author pairs. Exploration gives eligible new authors/content some exposure. Suppress repeats already answered recently and cap consecutive items from one author or topic. Provide Latest and Following alternatives. These weights are launch hypotheses to measure, not validated engagement claims.

Question usefulness and question difficulty are different metrics. Estimate difficulty only after enough distinct genuine first attempts; show sample size, use smoothing, and exclude the author, reviewer preview attempts, suspicious bursts and repeated practice. Low accuracy alone does not prove difficulty: a bad key or ambiguous stem can cause it.

Practice selection: honor subject/exam/topic/paper filters and eligibility first; then choose a mix such as 50% due mistakes/review, 30% unseen relevant questions and 20% weak topics, backfilling when a bucket is empty. This is separate from feed ranking. Tests use a frozen syllabus blueprint, quotas, scoring mode and question revisions, not social popularity. Sample from indexed candidate sets rather than sorting the full bank randomly on every request.

Review priority: scoring blockers first; then affected active modules, unique learners exposed, source quality and age. Raw report/vote volume has a bounded contribution. Ordinary report floods cannot automatically remove an exam's questions. A scoped reviewer can apply an immediate auditable scoring hold.

Abuse controls: per-account and per-network limits, duplicate detection, unusual reciprocal voting/review patterns, reviewer disagreement audits and reversible awards. Suspicious signals queue investigation; shared IP alone must not penalize students using the same hostel or college network.

## 9. Data, security and operations

Use the existing React/FastAPI/PostgreSQL stack with a bounded worker and transactional outbox. A separate admin shell under /admin is sufficient initially; a different subdomain is an optional later deployment choice, not an authorization boundary.

Extend the existing planned contribution/revision/review/publication tables, rather than building another independent review subsystem. Add stable option identities/mappings, source evidence records, explicit permissions, publication receipts and credit ledger. Attach votes to published canonical objects/revisions, with uniqueness constraints. Keep user votes, attempts, drafts and moderation records outside bank sync ownership.

Require authenticated sessions, scoped server authorization, CSRF protection, recent authentication for permission changes, and staff MFA before full production administration. No shared owner token for volunteer actions. Sanitize rich text, validate uploads in a worker, restrict source fetching, record actor/reason/time, and expose no infrastructure secrets in the browser.

Guard concurrent edits with expected revision/version and a diff-based rebase flow. Publishing cannot silently overwrite a changed baseline. Historic attempts retain question/options/scoring snapshots. Corrections can produce an explicit adjusted result and explanation; never invisibly rewrite a completed competitive ranking.

Use indexed pagination and bounded bulk jobs. Source thumbnails load lazily; OCR/PDF processing runs away from request handlers. Cache public lists by content version, invalidate only affected content, and preserve private cache boundaries. Track queue age, review latency, publication failures, read latency, credit reversals and dispute rate. Rehearse backup restore and rollback before production signoff.

## 10. Build order and model allocation

1. Sol 6.1: reconcile this blueprint with the existing spec; finalize authority, source/option identity and revision contracts. Deliver schema/API contract and meaningful acceptance tests first.
2. Sol 6.1: editor, source viewer, revision diff, scoped permissions and guarded publication end to end. This must survive a subsequent ordinary bank sync.
3. Sol 6.1: contributor intake, independent review, appeals, holds and exact-once publication credit. Complete concurrency and authorization tests.
4. Luna: bounded UI work against stable contracts—tables, filters, forms, responsive layouts, empty/error states and documentation. Sol reviews each integrated slice.
5. Sol 6.1: public community question pool, votes, credit ledger and leaderboards. Luna can implement presentation components.
6. Astra or Sol 6.1 at higher reasoning: focused review of permission boundaries, publication crash recovery, fraud incentives, scoring revisions and release acceptance. Astra is optional for difficult design conflicts; it is not needed for every component.

This allocation is an engineering recommendation. Official OpenAI model-selection guidance describes GPT-6.1 Sol for complex work balancing quality/cost, Luna for scoped efficient work and Astra for the most demanding analysis: https://developers.openai.com/api/docs/guides/model-selection . Check availability in the actual implementation environment.

## 11. Acceptance scenarios before calling the system complete

- Correct a printed option, prove the PDF mapping, publish it, and verify the question in Bank, Library and the intended exam; replay sync and confirm the correction remains.
- Change a tag and verify saved collection queries, subject counts and affected modules without breaking historical progress.
- Two editors race: one gets a conflict, neither silently loses work. Editing a reviewed proposal invalidates stale approvals.
- An author cannot approve their own work; an out-of-scope or revoked reviewer cannot decide it; forging a role or device ID grants no permission.
- Lose connection during publication and retry: one published revision, one credit award, complete receipt. Reverse it with a compensating change.
- Original MCQ stays out of official paper views, appears only after approval in community browsing, and enters optional practice only when eligible.
- A live mock cannot reveal its solutions through feed, contribution, detail or reviewer-preview APIs for an ordinary test taker.
- Unanswered, malformed and descriptive items remain browseable with correct eligibility; no index is fabricated to fill a count.
- Votes cannot edit an answer, award correctness or grant reviewer rights. Repeated submissions/votes/retries do not duplicate credit.
- Compare leaderboard totals to ledger events and exercise reversals, opt-out and period boundaries.
- Validate accessibility, source-page links, pagination, upload rejection, queue recovery, staging load and backup restore.

No implementation, migration, live question edit or deployment is part of this document's creation.

## Implementation checkpoint — 2026-10-21

The user subsequently authorized implementation and nominated an owner email. The core admin and contribution workflow is now deployed at `/admin/bank` and `/contribute`. The nominated account is not registered yet, so its owner grant remains pending. See ACCEPTANCE.md for executed checks and incomplete release gates; OPERATIONS.md documents publication, recovery, source registration and the workstation worker.
