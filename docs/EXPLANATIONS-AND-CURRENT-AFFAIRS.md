# Explanations and current-affairs context

Current policy: [Question review rules](QUESTION-REVIEW-RULES.md), including the
historical-answer + dated-update requirement, and [Public answer language](PUBLIC-ANSWER-LANGUAGE.md).
The release notes below are historical: their old empty-explanation labels and
future-work statements do not override current policy or deployed features.
The existing dated-fact editor is `/current-affairs/manage`; use its current
permissions and revision workflow. No automatic current-fact population is implied.

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

Answer-bearing revision notes and reference links render inside the shared answer panel after a successful check or protected Show answer request. There is no independent revision reveal; source-held and unanswered items retain evidence comparison instead. An expired note remains clearly dated and marked “Recheck due”; it is not presented as verified current information. Unknown updates say no question-specific update was checked. This is an editorial workflow, not an automatic news feed or automatic answer rewrite.

Maintainers add/review a note after checking its source, then run the frontend tests/build and deploy the frontend. Learners can propose dates/sources through Suggest correction; existing server proposal/publication safeguards remain in force. A full browser-managed current-affairs editorial queue and separate per-explanation review metadata are future work, not features claimed by this release.

## Sources inspected on 1 November 2026

- Shibu Soren: Akashvani, 4 August 2025, https://newsonair.gov.in/former-jharkhand-cm-shibu-soren-passes-away/ — identifies the former Jharkhand Chief Minister and event date. Supports the existing 2025 example's context; no current officeholder is asserted.
- Finance Commission: Ministry of Finance report, https://www.indiabudget.gov.in/doc/16fcvol1.pdf — award period 1 April 2026 to 31 March 2031; official report listing also inspected at https://fincomindia.nic.in/ .
- Union Budget: Ministry of Finance, https://www.indiabudget.gov.in/ — 2026–2027 documents and separate Budget/Revised/Actuals context. No numerical budget answer is transferred between years.

Source check dates are editorial records. They never imply an official examination answer key or independent peer approval.


## Practice checking and viewing (2026-11-01)

Bank cards, question details, module study and paper browsing use explicit selection followed by **Check answer**. **Show answer** calls the protected POST reveal endpoint and displays **Viewed answer**, with no attempt, accuracy entry, quota consumption or reward. The shared panel orders the stored answer/provenance, explanation, revision note and optional key/solution comparison. Revision notes have no independent reveal control.

`answer_reveals` stores only the most recent view per learner and canonical question. Revealing a usable answer or answer comparison starts a 30-minute review window across tabs and paper appearances. The answer endpoint rejects new attempts during that window, including alternative context values; idempotent replay of an already recorded attempt remains safe. Later attempts retain existing provenance and reward eligibility checks. This is a practical study cooldown, not proof of independent recall or protection against separate accounts/external PDFs. No existing learner attempt is rewritten.

Direct reveals and comparisons retain active mock/game/cup protection. Unusable/held questions retain source-evidence comparison, without presenting a checkable answer. GET comparison remains compatible with the existing client but now records answer exposure; it is private and not cacheable. Revision-note content is editorial frontend content, not a secret answer store.

## Reading continuity and revision actions (1 November follow-up)

A private, bounded practice-state read restores prior answer views after reload without renewing their cooldown. It checks exam scope, source paper, active mock/game/cup restrictions and newer attempts before returning an answer. The frontend batches visible cards in groups of at most 100 and keeps no persistent answer cache. Check/show exposure unlocks discussion reading; normal account, moderation, sanction and active-assessment gates still apply to discussion writes.

The answer panel displays the remaining retry minutes and offers Retry now once the server window expires. Save for revision uses the existing personal saved list. Retry later ensures the question is saved, then advances in the current results or printed paper order. Existing daily revision excludes revealed questions until their cooldown expires; viewing/saving/advancing never creates attempt history or rewards. Guest saves stay local to their browser, while registered saves follow the existing account sync/conflict handling.

Added narrowly matched MCS revision references: 2016 Stand-Up India (Ministry of Finance release, 22 July 2025); the 2015 original-language-count question (Government of India release, 18 December 2024); and 2017 biodiversity hotspots (EC JRC catalog of the explicitly archived 2016.1 dataset). These notes distinguish the source date/version and historical wording; no undated claim of current scheme terms or global designations is made.


## Recent MCS explanation and revision pass — 1 November

Added six narrowly year/topic-matched notes for the 2025 Bairabi–Sairang question (September 2026 railway update), MUHCS (dated2026–27notice), NER District SDG Index (edition-specific ranking and checked listing), ULLAS (2026–27framework, not a new Mizoram literacy rate), UNFPA's2025report and the2023Hero Tri-Nation event. Sources, exact stem matches and limitations are saved in `docs/sources/mcs-current-affairs-context-20261101.json`. Actual browser acceptance shows the dated railway update after protected answer reveal. No historical answer, explanation verification or present-day status is inferred from a newer note. Operation Black Forest was omitted from this note pass; the inspected retrospective material was not used to establish an exam-era answer.

The first checked explanation packet is `docs/sources/mcs-explanation-batch-20261101.json`:72empty-text appearances in28groups (49maths,9English,14factual). Luna drafts were checked against source pages, calculations and primary references by the coordinating operator. This is one delegated operator workflow, not independent peer approval. Source-text matching preserves punctuation, mathematical operators, directions, passages and emphasis; a question/choice multiset alone is not enough to assume equivalent context. No nonempty explanation is overwritten. The packet is prepared, not published, pending a new bounded quota-exception answer; the earlier105-decisionexception ended.

Readiness and source-reference findings are separate: `docs/plans/MCS-ORIGINAL-SIMULATION-READINESS-20261101.md` records the current practice configuration and 2025 cover evidence; ten page locators, two radical-stem repair leads and a meaning/key review lead remain unpublished. Do not change source mapping or scoring as a side effect of an explanation update.

## Browser-managed connections — 2 November 2026

The first current-affairs connections workflow now lives at `/current-affairs/manage`, also linked from Assigned paper review and the admin navigation. Reviewers search only their permitted source questions, identify an exact office/institution, jurisdiction and fact type, enter dated facts with HTTPS source/document references, and attach exact source appearances with historical context and reference-date evidence. Unknown dates remain unknown. Overlapping known fact periods, future source checks and stale question tokens are rejected. The first version requires manual identity/source review; it has no automatic news feed, alias merger or generative processing.

Submission records immutable proposals. An independent owner can publish, reject or retract with an audited rationale; an owner cannot publish their own claims. Replacements carry the current entity version and replace the full linked-source set. Previously published revisions remain in history. Authors must retain their source permissions at publication. Exact-paper assignments allow friends to propose within their scopes without granting global factual publication rights. The owner sees all proposals, while each author sees their own. There is bounded pagination.

The shared practice answer panel offers “Then and now · Asked again” after normal answer checking/viewing. Signed-in readers explicitly request the protected dated payload. It lists historical context, effective/check/review dates, source links and related papers newest first. Expired facts are marked Recheck due. It does not assert that the latest stored fact is necessarily current today. Bank-owned questions, options, provenance, scoring and existing attempts are never changed by context publication. Correcting a wrong historical key still uses ordinary bank correction.

All new answer-bearing/manage/search routes withhold content during any active mock/game or an unclosed weekly cup answer-release window. Viewing published connections records the normal 30-minute answer-review exposure for all linked canonical questions, without creating attempts or rewards. Timeline payloads are fetched from private no-store endpoints rather than embedded in the public bundle. Existing static note registry behavior is unchanged; these new guards do not certify prevention of external access to PDFs or previously public notes.

Migrations0064/0065 add the editorial records and immutable source links. Transient edit tokens still reject stale proposals. Durable source fingerprints let published connections survive byte-identical sync upserts while withholding a connection after real question/key/context/classification changes. Missing historical fingerprints are not backfilled as if they were reviewed. A new inspected proposal is required. Source evidence points to exact appearances; this workflow does not automatically repair temporal questions that were incorrectly merged earlier.

Production begins with no automatic migration of the static notes and no invented officeholder facts. A read-only inventory found14Chief Election Commissioner source candidates; these remain unconfirmed candidates in `reports/current-affairs-connections-20261102/source-candidates.json`. A reviewer must inspect and submit actual dates/links before they appear in the new learner panel. Automated acceptance and browser rehearsal use synthetic accounts, facts and source questions only.

## General current-affairs categories — 2 November follow-up

The owner clarified that officeholders were only an example. The editor now offers General changing fact, Appointments, Trade exporters/importers, Production/resources, Statistics/rates/quantities, Reports/indices/rankings, Schemes/policies, Awards/sporting editions, Records/firsts/largest/longest, and Events/summits/discoveries. The default is general rather than officeholder. These are editorial fact types, not a replacement for GS/GK source labels or approved subject/topic classifications.

Rankings/statistics require a comparison definition: exact subject/commodity, measured metric, value/volume/rate/count/index basis, unit/currency/price basis, comparison population, source/report series and methodology. A connection for iron ore exports by tonnage must not be replaced with one for iron-and-steel exports by monetary value, production, another population or changed methodology. The immutable first proposal fixes the comparison identity; use a separately named connection and mark the relation appropriately when definitions differ. Independent reviewers see the complete definition before publishing. This is a structural check and human editorial contract, not automatic interpretation of commodity codes or unit conversions.

Each fact can record a reporting-period label, period type, start/end and edition separately from effective, publication, checked and review-due dates. Measured facts require an explicit period label, including an honest unknown label when necessary. Successive annual rankings and award editions can coexist without fictitious expiry dates; officeholder/general/scheme validity intervals still reject overlapping claims. Duplicate claims for the same period/type/edition require resolution. Learner ordering uses recorded reporting/effective dates and displays the actual period; it does not infer today's ranking from the most recently published report.

Every exact source-question link can state Comparable / Related topic only / Unclear, with its asked period and a comparison note. Measured links require the note, and directly comparable links require the period asked. A vague old question saying only “iron” can stay related with an explicit warning about ambiguous commodity/value/volume meaning. The learner panel displays these limits rather than implying all linked questions ask the same fact.

The additive fields live in the existing immutable JSON payloads. Older records default to general and unconfirmed comparison; their content is not rewritten or auto-classified. Idempotent retries normalize omitted legacy defaults. No new database migration is required. All independent-publication, exact-source, historical-answer, exposure/cup and bank-sync protections remain in force. The follow-up suite passed97focused backend checks; preview values for trade leaders are synthetic, not actual country rankings.
