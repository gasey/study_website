# Admin and question-bank review — 6 November 2026

**Verdict: keep the current architecture; improve the cleanup workflow before expanding it.** The current `india-study-map-app` already has canonical questions, printed appearances, controlled classifications, related-topic support, source inspection, versioned module composition and guarded publication. It is a useful operational system. It is not yet a sufficiently consistent, efficient workspace for classifying and repairing the whole 80k+ corpus.

This review concerns the current app at study.hawayu.in, not the older `india-study-map`/`mpsc-backend` implementation. Code findings refer to the current working checkout, which contains substantial existing changes; they are not a claim that every local file matches deployed assets. Live counts came from read-only Oracle bank and PostgreSQL queries. No production content, permissions, reviews or application code were changed. No authenticated browser session was available, so authenticated desktop/mobile usability remains unverified.

**1. What the fresh inventory shows**

The authoritative MPSC bank checksum was `b6d5920f9b951694cb6c92426ff0b8d6fa3b70ce7b82a2ead8f055edd0eb80e0` during this inspection.

| Measure | Observed |
|---|---:|
| Stored questions / appearances | 82,383 |
| MCQs | 74,207 |
| Written questions | 8,176 |
| Papers | 1,979 |
| Records with an approved primary subject but no topic | 58,373 — 70.9% |
| Records without a page locator | 7,854 |
| Records without a printed question number | 884 |
| Records with no explanation | 68,406 |
| MCQs with missing/negative answer index | 4,212 |
| Approved related-topic links in PostgreSQL | 0 |
| Canonical IDs with multiple appearances in PostgreSQL | 0 |

All bank records have one approved primary classification; that status does not establish semantic correctness or personal human inspection. Missing topics are coverage gaps, not automatically errors. Missing/negative answer indices include intentional exclusions; they are not all answer-generation tasks. Do not force every written item into an MCQ explanation or scoring workflow.

The live database has 82,383 canonical rows, 82,383 appearances, 82,249 live rows and 134 held rows. Its papers are all in `mizoram-recruitment`: 1,194 Direct, 386 Departmental, 289 LDE and 110 Direct_NG. No Community papers appeared in this inventory. Other website lessons, static modules and external banks need a separate ingestion/completeness inventory; a “Website bank” dropdown is not evidence that those questions are integrated.

Zero shared canonical IDs means canonical reuse is not populated in this database. It does **not** prove which records are duplicates or justify merging all matching stems. Repeated extraction, booklet variants, genuinely repeated questions and questions about changing facts need different treatment.

**2. Findings ranked for this user's priorities**

| Priority | Finding and evidence | Recommended change |
|---|---|---|
| P1 | The answer inspector's “Retag with preview” link sends `q`, while the new tag screen reads `tag_q` and defaults to `attention`. Even changing the parameter alone can hide a correctly populated but semantically wrong tag. [Workbench](../web/src/components/AdminQuestionWorkbench.tsx#L99), [consumer](../web/src/components/EditorialTagCleanup.tsx#L15). | One shared navigation helper: exact question, `tag_issue=all`, source appearance, current scope and return location. Add a regression for a fully tagged question with a wrong topic. |
| P1 | Tag cleanup exposes current subject but not current topic/subtopic. The API already accepts topic. [Cleanup](../web/src/components/EditorialTagCleanup.tsx), [API](../api/app/routers/admin_bank_edits.py#L50). | Add topic/subtopic and primary/related/any-path filters. Allow correction of a known misplaced cluster without searching one question at a time. |
| P1 | The new searchable picker displays raw GK and GS hierarchies; learner browsing uses a combined projection. The live registry puts Current Affairs under GS, while GK contains Static GK, Sports, Art and Culture, and Science in the news. [Picker](../web/src/components/SearchableTaxonomyPicker.tsx), [projection](../web/src/lib/learningTaxonomy.ts). | Reuse one explicit learning catalogue in editor, filters, counts and modules. Do not require an editor to know whether a topic happens to live under a legacy GK or GS ID. |
| P1 | English's active topic nodes are only Grammar, Vocabulary, Sentence Correction and Comprehension. They do not adequately describe all writing tasks in official schemes. | Add reviewed writing paths for essay, précis and letter writing; distinguish language skill from an essay's content theme. Keep format, marks and choice instructions separate. |
| P1 | “Both banks” is hardcoded to MPSC versus `exam_type='Community'`; all other sources become MPSC in this view. [API](../api/app/routers/admin_bank_edits.py#L69). | Use explicit source/provider and corpus identity. Recruitment mode is not source identity. Register other exam boards, books, website-authored items and mocks without conflating them. |
| P1 | Original-paper mocks select an eligible canonical pool, then deduplicate by canonical ID. This is useful practice, but cannot by itself guarantee the complete printed paper. [Mock selection](../api/app/routers/mocks.py#L127). | Separate original-paper representation, eligible practice and scheme-based simulation. Exact paper mode must preserve each printed position and visibly handle excluded/compensated/written items. |
| P2 | Daily review is reachable through editorial, answer review, tag cleanup, reports, queues and multiple paper tools. There are already inline controls, but context is not uniformly retained. [Navigation](../web/src/lib/adminNavigation.ts). | Consolidate entry and navigation, retaining the existing services. Use one inspector with purpose-specific editing modes and one persistent work context. |
| P2 | Multiple tagging and canonical sharing exist structurally but have zero approved/shared instances in the inspected database. | Pilot reviewed related paths and repeat groups. Measure actual reuse and accuracy before broad rollout. |

The existing final-admin correction, 20-item batch, baseline/source conflict checks, immutable history, publication receipts and draft retention should be retained. Requiring extra approval for every authorised admin tag change would undo recent usability improvements.

**3. Recommended implementation model**

Use one editorial system with several independent dimensions. Extend the current React/FastAPI/PostgreSQL application and Oracle publication pipeline; no new service stack or second master bank is required.

| Dimension | Meaning | Existing base / extension |
|---|---|---|
| Question | Reusable learning content and its stable identity | `canonical_questions`; preserve existing IDs |
| Source appearance | Exactly what was printed, where, and in which option order | `appearances`, papers, documents, source references |
| Learning classification | What knowledge or skill is tested | Primary `question_classifications` plus reviewed `question_topic_links` |
| Context facets | Geography, language, time sensitivity, reference period, content format | Reuse existing context fields; add controlled facets only where missing |
| Exam scheme | Versioned paper/section names, marks, duration, choice rules, qualification and scoring | Extend collection configuration with a source-backed scheme revision and explicit section mapping |
| Module / collection | A reusable selection of approved questions or source papers | Existing versioned collection/composition services |
| Review/publication | What was checked, by whom, against which source, and whether applied | Existing editorial checks, decisions, publications and receipts |

A source tag belongs to the occurrence/document. A topic belongs to the tested content. Module membership describes reuse. These must not be interchangeable free-text tags.

Represent learning areas consistently: History, Geography, Polity, Economy, Environment, Science, English, Mathematics, Reasoning, Computer knowledge, Mizo language/culture and specialist disciplines. GK/GS can remain a convenient **discovery grouping** over these areas, while exact GK/GS paper labels belong to exam schemes. Initially preserve the approved stored IDs through an explicit mapping; do not mass-rewrite historical classifications. Replace label-derived equivalence with reviewed mappings so a label rename cannot silently change meaning or break URLs.

One primary path is the default. Secondary paths are for genuinely tested additional knowledge; regions, source boards, years and module names use their own facets. Counts use distinct canonical IDs for learning coverage and appearance IDs for printed-paper coverage. Multi-tagged questions must not satisfy two required mock slots unless the scheme explicitly intends that: allocate each chosen question to one blueprint slot.

Examples:

| Question/task | Learning classification | Separate context |
|---|---|---|
| Constitutional role of the Election Commission | Polity → Constitutional bodies | India; static concept |
| Who occupied an office at the time of an exam? | Current Affairs discovery route, with a relevant reviewed Polity path | Exact office/jurisdiction and reference date; retain historical answer |
| River flowing through Mizoram | Geography → Rivers | Region: Mizoram; not automatically Current Affairs |
| Grammar question whose passage mentions climate | English → Grammar | Passage subject does not automatically justify Environment tagging |
| Essay on development | English/Writing → Essay when testing writing; an additional content path only when the rubric warrants it | Written format, word limit, marks and choice group |

Reuse the existing current-affairs entities, fact revisions and appearance-bound links. Store event/reference period, checked date and review-due date separately. “Current Affairs” as a topic and “answer may change over time” are related but not identical. An explicitly dated award result remains historically true; an undated “current minister” question needs a reference date. New facts must not replace old paper keys or historical scores.

**4. Daily interface and work sequence**

Use four primary destinations: **Work queue, Questions, Papers, Modules**. Put imports/PDFs inside Papers; put taxonomy maintenance, accounts and system tools under Manage. Existing bookmarked routes remain supported.

The cleanup screen should have a persistent scope bar: bank/provider → module → source paper/year, plus learning-path and issue filters. The main list should be compact, with selectable rows; selecting one opens the question and a source panel beside it. On smaller screens, use a full-width inspector with an obvious return to the same list.

Inside the inspector, show four clearly labelled modes: **Tags, Answer, Text/source, History**. Keep the original page/number, passages, figures and provenance visible. Offer Checked & next, Save & next, and Cannot verify; retain the existing distinction between an inspection, an admin decision and completed publication. A saved decision is not yet an applied correction.

Prioritise queues: invalid tags; reported wrong tags; missing topics in priority exam modules; unresolved source/options/key issues; time-sensitive items needing context; suspected repeated records. Provide named, saved scopes and durable resume positions. Show “why this item is here.” A subject-only item that is intentionally broad should be dismissible with a recorded reason, rather than returning forever as unfinished work.

Keep the current 20-item interactive batch limit initially. Improve the path picker, preview, keyboard operation, apply-and-continue, and per-item failure recovery before increasing batch size. Bulk replace-primary, add-related and remove-related remain distinct. Larger machine-assisted jobs should produce bounded staged proposals with resumable progress, never a blind retag of all search results.

Start with English and common GK/GS in the active MCS, UDC/Assistant and Group B modules. Preserve specialist subjects and Departmental/LDE source boundaries. Finishing 58k classifications manually, one form at a time, is not a realistic default workflow.

**5. Official scheme distinctions that the model must preserve**

Official PDFs were downloaded and relevant pages rendered for inspection. Upload folder/date is not the exam sitting or scheme effective date. Applicability still needs the recruitment-specific notice and any later amendment; do not apply a new version retroactively.

| Scheme inspected | Structure relevant to the app |
|---|---|
| MCS combined, 27 August 2025 | Prelims: GS and Aptitude, each 100 MCQs / 200 marks / 2 hours. Aptitude is qualifying at 33%; wrong answers lose one-third of assigned marks. GS topic counts are indicative. |
| Group B Non-Gazetted, 28 October 2026 | General route: English 100 marks, mixed written/MCQ, 3 hours; GK & Reasoning 200 marks, 2 hours. Its latter paper divides into GK 100, arithmetic 60 and reasoning 40. English includes writing as well as grammar, vocabulary and sentence formation. |
| Group B Gazetted combined, 17 July 2025 | English 100, Essay 100, GS I/II/III 200 each. English/Essay take 3 hours, GS papers 2 hours. GS I covers modern history/culture and current events; GS II polity/economy/geography; GS III science/technology, Mizoram and aptitude. |

Sources: [MCS 2025](https://mpsc.mizoram.gov.in/uploads/attachments/2025/08/d89bfbc71ea5cda75b0957627c877416/scheme-of-examination-for-mizoram-civil-services-combined-competitive-examination-2025.pdf), [Non-Gazetted 28 October 2026](https://mpsc.mizoram.gov.in/uploads/attachments/2026/11/32bc3ed03f920c30e06edaccfa44e6fe/syllabus-for-non-gazetted-posts-28102026.pdf), [Gazetted combined 2025](https://mpsc.mizoram.gov.in/uploads/attachments/2026/04/ee26522353e4d860ba5b28834fb35af9/scheme-of-examination-for-mizoram-group-b-gazetted-general-services-combined-competitive-examinations-2025.pdf).

The October 2026 Non-Gazetted notification explicitly supersedes May 2025. Its general-route interview is 37.5 marks; technical-route interview is 75. Its technical route has English, a 100-mark knowledge paper and two 200-mark technical papers. There is a source-label inconsistency: page 2 calls the technical knowledge paper General Knowledge; page 3's detailed heading says General Knowledge & Reasoning, but the listed allocation is the eight knowledge categories. Preserve the printed wording/evidence and flag this; do not invent extra arithmetic/reasoning marks. Keep recruitment-specific LDC/UDC/Assistant rules separate where applicable.

Original-paper mode should open immediately from a paper card and preserve section hierarchy, printed numbering, shared passages/figures, instructions such as “answer any two,” original option order and written questions. Add readiness indicators for source coverage, ordering, scheme mapping, answer evidence and scoring. “Original paper available,” “practice subset ready,” and “full simulation ready” are different states. Never silently omit unscored items and call the result a complete original paper.

**6. Delivery order and acceptance**

1. **Fix the cleanup path.** Repair retag links; expose topic/related-path filters; share the taxonomy display mapping; preserve source/list position. Acceptance: a fully tagged wrong question opens directly from answer review and can be corrected without losing context, including after refresh/save failure.
2. **Close the taxonomy and source gaps.** Add writing categories; explicit provider/corpus identity; current-affairs context; source-backed scheme revisions. Audit all other banks before registering them. Acceptance: the same concept is reusable across modules without becoming a copied question or an invented exam section.
3. **Run a representative cleanup pilot.** Label a few hundred diverse questions across English, GK/GS, Mizoram, science, technical, OCR and written formats. Measure primary-topic accuracy, unnecessary secondary tags and human correction time. Use errors to improve the catalogue/prompts before scaling.
4. **Make paper readiness and reuse operational.** Review duplicate candidates, preserve appearances and old IDs, then exercise complete paper rendering and simulation. Acceptance: shuffled options, two appearances in one paper, compensated questions, missing figures and written choice groups all retain their correct identity and treatment.
5. **Scale measured batches.** Track missing-topic coverage, unresolved semantic errors, publication failures, source coverage and time per accepted correction. Benchmark first/deep pages and combined filters on the real-sized corpus. Target sub-second common reads where practical; do not introduce a search cluster without measured need.

Changes affecting existing source records must retain current provenance, reviewer assignments, holds and attempt history. Use additive migrations and the existing guarded publication route. Keep identical question matching, similar-concept linking and presentation grouping as separate operations.

**7. AI model recommendation**

For implementation, my recommendation is **GPT-6.1 Sol in Codex at high reasoning** for the cross-layer work, with GPT-6 Astra as an optional reviewer for difficult schema/publication decisions. This is a task-specific recommendation, not a benchmark result for this repository. Official guidance identifies GPT-6.1 Sol for Codex coding and high reasoning for complex debugging/agentic work. [Code generation](https://developers.openai.com/api/docs/guides/code-generation), [reasoning guidance](https://developers.openai.com/api/docs/guides/reasoning).

For classifying the bank, benchmark the existing economical draft model against Sol on the labelled pilot. Choose by measured path accuracy, over-tagging and cost per accepted correction. Require controlled IDs, source evidence and an explicit unresolved result. Keep uncertain cases for review. A stronger model is useful for ambiguous questions; it is not a substitute for the source or evidence that an answer is official. No 80k-question model run was started.

**Verification performed:** fresh authoritative JSON aggregate inventory; read-only PostgreSQL counts/taxonomy inspection; source-level retag URL reproduction; existing `check-editorial-simplification.cjs` and `check-editorial-list.cjs` both passed; rendered official scheme PDFs. This was a review, not a deployment, full load test, full semantic content audit or authenticated visual QA.
