# Group B common subjects and technical papers

Decision and implementation, 28 October 2026.

The learner entry `/group-b` opens **Group B — English & GK/GS**. Common
subjects are the first view. English and General Knowledge & Studies can be
selected independently. Technical papers have a separate view, searchable
paper list and topic/practice routes. The source-group selector supports both
Group B collections together or either collection independently. Entry links
appear on `/exams` and both existing Group B exam pages. Complete archives
remain accessible, including mixed papers, departmental papers and unmapped
subjects. Existing exam mocks retain their original scope and are not offered
as common-subject mocks on the new route.

## Classification and selection contract

- Classify by content: subject, topic, subtopic. Preserve original question,
  paper title, recruitment, year, exam group and source appearance separately.
- General Knowledge and General Studies are one learning category on this
  route. Existing stable taxonomy IDs remain valid; the virtual `gk-gs`
  subject maps their primary paths to one card and retains original topic IDs.
- Common English requires an approved primary English classification.
- Common GK/GS requires an approved primary General Knowledge or General
  Studies classification. General Science additionally requires an explicit
  GK/GS role for the source paper, so specialist science is not selected just
  because its subject says Science.
- Technical question practice requires an explicit technical paper role and
  an approved primary classification outside English/GK/GS. Other subjects
  are not implicitly technical. Approved related tags remain available but
  cannot promote specialist primary content into common practice.
- Missing/pending tags and unassigned paper roles remain available in complete
  archives; they are not inferred from broad recruitment names or paper numbers
  at request time. A role never grants syllabus equivalence across recruitments.
- Preserve distinct canonical IDs and each source appearance. Queries use
  distinct IDs/EXISTS; do not add overlapping topic counts to claim a total.
  Automatic deduplication is outside this change.
- Technical/non-technical is recruitment context, independent of a paper's
  learning role: a technical recruitment's English paper is common English.
- No difficulty labels or new scoring policy. Browse, practice, official-key
  and reviewed-answer restrictions use the existing question pools.

## Explicit source-role manifest

`api/app/data/group-b-paper-roles.json` is versioned application configuration,
not bank question content. Version `2026-10-28.2` lists 52 exact source-paper
IDs already present in the non-gazetted collection: two General English,
25 General Knowledge/Studies (including mixed papers), and 25 technical
papers. The original 29 entries use explicit inventory designations; the
23 additional GK/common entries were reviewed against local source PDFs
and all 75 candidate science question stems. Of these, 74 are eligible.
Bounded mixed-paper roles carry `qnum_from` and `qnum_to`: General Knowledge
questions 1-75 are eligible, while arithmetic questions beginning at 76
remain outside common science. The same appearance-level bound controls
both membership and the displayed source. Non-numeric and oversized question
numbers do not match bounded roles. These are reviewed exact entries, not a
runtime filename classifier. Future paper assignments need their own source
check and manifest version. They do not retag any canonical question.

Historical Gazetted coverage currently consists of departmental Inspector
papers. Its page explicitly explains the limited coverage; technical and
common direct-recruitment availability is not fabricated. The manifest can
add verified gazetted and non-technical recruitment paper contexts later.
General-science questions in further historical mixed papers still need a
reviewed source role before entering common science practice. Two possible
classification defects found during the source audit are recorded as pending
independent review; this release does not change canonical tags or answers.

## API and progress

`GET /api/questions?collection_id=group-b&study_area=common` selects the union
of the live, public, browsable Group B collection papers. `study_area` also
accepts `english`, `gk-gs`, or `technical`; a specific real Group B collection
can replace the virtual ID. Other collection IDs are rejected. Area selection
is always intersected with answer pools, paper/topic and personal filters.
`GET /api/collections/{group-b-or-real-id}/study-topics?study_area=...` uses
the same membership rule and primary paths; the shared virtual subject does
not alter the underlying registry. Existing endpoints without an area retain
their original behavior. `GET /api/collections/group-b/study-config` exposes
the public versioned source-role entries.

Displayed source appearances stay within the selected Group B group and
paper where selected. Answers save against the actual source collection and
paper rather than a fictitious `group-b` collection. Answered/unseen/wrong
filters cover those actual collections. Account practice continuation saves
the shared route and its area, source, topic, mode and offset filters through
the existing global checkpoint workflow. No database migration or bank sync
is needed for this application-level change.

## Verification

Isolated PostgreSQL tests cover mixed papers, common/technical science,
pending tags, secondary-tag contamination, distinct counts for repeated
appearances, shared GK/GS subject filtering, selected source appearances,
source subsets, invalid area/collection pairs and actual-collection progress.
Library-topic and learning-workflow regression tests run with these cases.
Live acceptance results and UI evidence belong in
`reports/group-b-common-20261028/`.

## Source titles versus learning topics

Keep original GK or GS wording in optional, explicitly reviewed appearance.paper_label. Show the approved topic on question cards; broad GK/GS fallback is a learning grouping. Never infer paper titles from question tags. Nine source covers currently carry reviewed labels; additional covers need inspection before adding labels.
