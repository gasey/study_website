# Current Affairs Connections — historical questions and dated updates

2 November 2026 · Implementation provision for the website redesign and Topic Trail. Proposed, not deployed.

## Purpose

When an old paper asks “Who is currently the Chief Election Commissioner?”, preserve the original printed options, original answer evidence and exam-date meaning of “currently”. Let learners open related later questions and dated updates about the same office. A newer officeholder missing from old options is normally a time-context difference, not a reason to rewrite that paper.

This extends docs/EXPLANATIONS-AND-CURRENT-AFFAIRS.md. The site already has a small frontend revision-note registry; this design adds an editorially managed timeline and explicit question connections. Existing notes are source leads for migration, not automatically trusted database facts.

## Learner experience

After permitted answer reveal, a compact “Then and now” panel shows:

1. **In this paper:** exam/sitting, the question's reference date if known, historical answer and its original provenance. If reference date or evidence is unresolved, say so.
2. **Latest checked update:** the relevant fact, effective period, primary source and date checked. Use “Latest checked” rather than implying live accuracy. When due, show “Recheck due”; if absent, “No dated update has been checked yet”.
3. **Asked again:** confirmed related papers, sorted newest/oldest with exam/year and an explanation of the relationship. Each opens its own unchanged question and options.
4. **Study the concept:** link to the approved GS/GK topic, such as Election Commission roles and constitutional provisions, when there is actual reviewed material to link.

Example is hypothetical, with no assertion about a real officeholder or actual repeated paper:

```
Old exam: Who is currently the Chief Election Commissioner?
Original options and historical key remain as printed.

Then and now
• At this exam's reference date: [historically supported answer]
• Latest checked: [separately sourced officeholder], effective from [date]
• Asked again: [linked later paper, only if a real question is confirmed]
• Related concept: Election Commission — appointment and functions
```

An old question in a current-affairs study list gets “Historical · answer for YEAR”. The heading must not silently redefine it as a question about today. Different options in a later paper remain attached to that later source appearance.

## GS/GK and Current Affairs relationship

Current Affairs is a time-sensitive way to explore knowledge, not a reason to move every question into a single broad subject. Preserve original paper names (GS, GK, General Studies or General Knowledge) and approved classification paths. A question may have reviewed primary/related classifications under existing taxonomy rules.

Use a separate subject-of-fact entity to connect questions across exam labels: e.g. Election Commission of India → Chief Election Commissioner. The entity links the changing officeholder fact and static constitutional concepts while keeping them distinct. Do not create another competing taxonomy or infer an exact learning topic from a broad GS/GK label.

Keep Chief Election Commissioner distinct from other Election Commissioners, State Election Commissioners and foreign offices. Country/jurisdiction, institution, office, metric and edition are identity fields, not optional search decoration. Person-name matching alone is inadequate.

## Minimal storage contract

Use additive tables and reviewed relations; never add a mutable “current_answer” column to canonical_questions.

| Record | Required meaning |
| --- | --- |
| Entity | Stable ID, type, precise name, aliases, jurisdiction, parent institution and editorial status |
| Fact revision | Entity, predicate (e.g. officeholder), value, effective-from/to with precision/unknown markers, source URLs/document/page, source publication date, checked date, review-due date, reviewer and revision state |
| Question context | Canonical and source appearance IDs, entity/predicate, reference date or interval and evidence/basis, relation type, author/reviewer and source version |
| Question relation | Explicit typed edge: same changing fact / same concept / later question / revised statistic; ordered endpoints and evidence. Related does not mean duplicate. |

Store effective dates separately from when an editor learned or checked the fact. Never invent a day for a year-only date. Preserve prior revisions and retractions. Temporal overlaps, gaps, conflicting sources or unclear historical wording produce an unresolved status, not an automatic choice of the newest row. An acting appointment and a permanent appointment may need different scoped predicates.

Facts about budgets, rankings, population, awards and schemes require period/edition/unit/geography where relevant. Do not apply the officeholder model naively to every numerical fact. Capture an explicit source reference date in the stem ahead of exam date; where the stem is vague, editor-confirmed exam-date interpretation is labelled as such. Unknown sitting dates remain unknown.

Question links use exact source appearances because the same canonical wording can recur at different times. Never merge temporal duplicates or reuse a canonical answer merely because the stems match. An existing incorrectly merged temporal question must go through source-identity repair and ordinary correction review.

## Admin workflow

Add “Current affairs connections” under Questions/Review:

- Find a question and mark it time-sensitive, with a reason and reference-date evidence.
- Select an existing precise entity or propose a new one.
- See candidate earlier/later questions from aliases, existing tags and text search; confirm the relationship manually.
- Attach an inspected primary source and enter a dated fact/update. Preview “In this paper” and “Latest checked” together.
- Submit for independent editorial review under explicit permissions, then publish the dated context through an audited context-publication path.
- Work queues: unlinked questions, missing historical context, unresolved dates, conflicting facts, recheck due, and changed source questions.

Assignments to a source paper can permit a friend to suggest links and sources, but do not grant publishing authority for shared entity facts. A fact update potentially affects many papers: show the affected list and validate the revision before publication. Current-app note maintenance remains available until the new workflow is released.

Start with manual curation. Deterministic alias/topic searches can find candidates; they cannot certify semantic equivalence or current truth. Later source monitoring may flag an official page change for review but must not silently replace a fact. AI extraction is optional draft assistance and never sets historical keys or verified-current status.

## Scoring, publication and answer protection

- Historical keys, options, explanations, attempts, rewards and game results are not rewritten by timeline updates.
- If the old key was wrong even for its reference date, use the existing correction/dispute workflow, not the timeline as a workaround.
- A newly authored “as of DATE” practice question is a separate labelled item with its own evidence and review; it is not an official past-paper question or automatically eligible for scored games.
- Topic Trail and other scored modes continue to use their strict official/key source pool. Do not turn an old question into a new scored question by swapping an option.
- Related content can disclose an active answer even when its question ID differs. New timeline/detail/search endpoints must apply answer-bearing access checks across linked entity/fact groups during active mocks/games/cups; until that exists, withhold timeline payloads during active assessments.
- Protected content must be served through authorized endpoints after permitted reveal, not embedded in public frontend bundles. Existing frontend notes are editorial public content; their current UI visibility is not a general secrecy guarantee.
- Avoid revealing answer values in search snippets, notification text, preload responses or relation labels before authorization. Existing source PDFs remain externally accessible study material; these controls do not claim prevention of all external assistance.
- During assessment creation, avoid selecting several linked questions that directly reveal each other's answers where the linkage is known. Freeze source/context versions and preserve shared exclusions and original results.

Timeline content is server-owned editorial context with immutable revisions; canonical bank changes still use the protected publication workflow. Source-version checks invalidate stale question-context proposals. Periodic recheck deadlines change display status; they do not certify that a fact remained true until the deadline.

## Small first release

Pilot one entity family: Election Commission offices, only with a handful of real source-checked historical questions and inspected dated evidence. Do not fabricate a recent repeat when none is found. Implement entity/fact revisions, exact question links, one protected learner panel and a manual editor queue. Add budget/award/ranking-specific schemas only after the officeholder workflow is usable.

Acceptance cases:

1. A former officeholder remains the historical answer even when no old option matches the latest checked fact.
2. A later real question shows its own choices/key and links back without either being merged or rescored.
3. Unknown exam date, source conflict, effective-date boundary and expired update display uncertainty correctly.
4. GS and GK source questions connect through the same precise entity without taxonomy/source-title rewriting.
5. New fact publication leaves historical content hashes, attempts and scoring unchanged.
6. Wrong-jurisdiction offices and same-name persons are not auto-linked.
7. Unpublished/retracted updates stay out of learner payloads; reviewer permission, stale writes and audit history hold.
8. Active assessment access cannot reveal linked answer-bearing updates through new UI/API/search paths.
9. Duplicate refresh/retry cannot publish twice; the current panel can be traced to its exact source/revision.

The basic curated version is a moderate feature. Reliable automatic monitoring and large-scale temporal duplicate repair are substantially harder and outside the first release. Sol can implement the bounded version after a real source inventory and tests. No content migration or factual update is implied by this design document.

## Scope correction and implemented general categories

The owner clarified on2November that the election office was illustrative, not the product's scope. The implementation now supports ten fact categories and structured measurement/period metadata, including trade, production, statistical/index rankings, schemes, awards, records and events. The office-only pilot suggestion above is superseded as a product limitation. Human curation can start in any category; facts still need source inspection and independent publication. See EXPLANATIONS-AND-CURRENT-AFFAIRS.md for the actual general schema contract and compatibility behavior. No actual exporter ranking or other current fact is inferred from this design.
