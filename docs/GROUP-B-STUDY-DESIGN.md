# Group B learner homes — 4 November 2026

Deployed at `/group-b?collection=group-b-non-gazetted` and
`/group-b?collection=group-b-gazetted`. This is the current learner-design
checkpoint; the older continuation plan retains historical release notes.

## Structure

- Two explicit group choices with separate titles and warm/sage home treatments.
  Shared study is optional and preserves each paper's source collection.
- Home, Subjects, Papers, Practice when available, and Progress. On phones the
  four/five navigation items fit one row; redundant global study-focus selection
  is omitted on the Group B hub.
- Non-Gazetted starts with English, GK and Current Affairs. Subject availability
  comes from the common-source API; Current Affairs resolves its approved topic
  ID. Technical papers use existing explicit roles, with no membership expansion.
- Gazetted leads with original papers and written preparation. Its current bank
  has no answer-ready MCQs. Sparse common-subject coverage is collapsed; empty
  practice routes give a paper-library action. Actual future availability drives
  the practice tab and actions without a second UI implementation.
- Paper library: text search, year, written-content filter, four sort choices and
  ten papers per page. Filters remain in the URL; changing them resets pagination.
  Exact source IDs, original titles, years and PDFs remain visible. Paper back
  links return to the corresponding Group B library.
- Existing exam bookmark service is reused, including errors and account-change
  isolation. Progress uses existing recorded attempts for one group at a time.
  A written-only group with no attempts gets a compact reading explanation instead
  of empty score charts. Historical activity remains visible if practice
  availability later changes. Written responses are not automatically graded.
- Existing Group B overview URLs redirect to the new homes. Existing paper,
  question, topic and practice deep links remain valid. UDC/LDC/Assistant keep
  their focused modules and current source memberships.

## Evidence and checks

Read-only release observations: Non-Gazetted 97 papers / 7,969 canonical questions;
Gazetted 5 papers / 137 canonical questions. These are observations, not seeded
counts or claims of syllabus coverage. Production UI reads current availability.
The existing dated syllabus guidance is retained; this release adds no universal
Gazetted scheme or new syllabus certification.

Passed: Group B navigation and component checks, actual progress-panel availability
and historical-activity checks, archive ordering, UDC study regressions, review
navigation/account-isolation checks, TypeScript/Vite production build and diff
whitespace checks. Web-only deployment through `scripts/deploy.sh web` succeeded;
public index checksum equals local dist, API health is OK, and the shared family
site is healthy. No migration, API deployment or bank publication was needed.

Live read-only browser verification covered distinct group switching, no empty
Gazetted MCQ actions, compact Gazetted progress, NG archive pagination and filter
reset, search/year/written filtering, exact original paper and return link,
legacy overview redirect and approved Current Affairs scope. No learner answers
or bookmarks were submitted for testing.

At 390px, document width was 375px on NG home/archive; the primary subject action
ended at y=710 within the 844px viewport. At 768px, NG archive and Gazetted home
had 753px document width. No horizontal overflow in those checks. Temporary
viewport overrides were reset. The first deployed design was visually inspected;
final screenshot capture repeatedly timed out, including in a fresh tab. The
final responsive checks use live DOM/AX measurements and interactions, not a
claim of complete final screenshot or physical-device QA. Account-specific
bookmark/progress variants were component-tested, not exercised by signing in.

## Remaining content and future features

This release does not fill taxonomy gaps, certify every source, or add missing
Gazetted recruitment papers. Continue content review module by module through the
existing editorial workflow. Saved short study sets and automatic written-work
tracking remain separate features; do not infer them from exam bookmarks or
existing MCQ attempt progress.

## Gazetted source audit follow-up — 4 November 2026

The later [source audit](GROUP-B-GAZETTED-AUDIT.md) repaired source locators,
instructions and tags across all137 existing entries. Four are duplicate
extractions of the133 numbered questions in those five PDFs. Source-library v2
also links the registered2016 common Paper I as an original PDF with zero extracted
questions: six originals, still137 entries and zero answer-ready MCQs. Nine verified
2026 Combined Gazetted PDFs remain pending source intake/extraction. The earlier
release observations above are historical, not complete/current coverage claims.
