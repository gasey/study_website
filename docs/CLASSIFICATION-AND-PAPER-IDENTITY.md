# Paper identity and learning classification

The source tells us where a question was printed. Its content determines where learners study it. Store and review these independently.

## Saved product rule: one bank, separate exam identities

Use one shared question bank across exams. Each exam supplies its own paper/section names, syllabus scope, source appearances and practice scheme. Reuse common English and knowledge questions across technical and non-technical Group B preparation; keep specialist papers separately selectable.

For UDC, the knowledge component is **General Knowledge (GK)**, not General Studies. Do not introduce a GS paper or section into UDC because a question has a legacy `general-studies` classification. Preserve the complete verified printed title of mixed papers, including English and other components. The combined **GK/GS** label belongs to cross-exam learning discovery; an exam-specific UDC knowledge heading should read **General Knowledge**. Verify future paper editions against their own sources rather than guessing their headings.

Implementation status on 28 October 2026: shared discovery, separate source identities, reviewed UDC cover labels and admin retagging are implemented. Collection topic trees still use the shared GK/GS projection; exam-specific learning headings and complete per-exam practice schemes require a follow-up. Source identity edits alone do not configure those schemes or change exam membership.

| Information | Example | Owner / workflow |
| --- | --- | --- |
| Recruitment and source PDF | Assistant Grade & UDC, booklet B | Existing bank paper and exam membership |
| Printed cover wording | Paper I · General Knowledge, General English… | Admin inventory → Paper identity & printed sections |
| Printed section | General Knowledge, Q1–75 | Verified section title and numeric range on that paper |
| Learning subject and topic | GK/GS → Current Affairs | Individual contribution or admin Learning tags batch |
| Technical content | Medicine → Dialysis | Content classification; specialist paper mapping remains explicit |

## Record source identity once

Open **Admin → Exams & coverage → a registered paper**. Inspect its original PDF. Record the printed examination title, printed examination year, full paper title and cover/heading evidence page. Add section titles and question ranges only where numbering is unambiguous. Leave sections empty when numbering restarts or its boundaries cannot be established. Confirm source inspection and save verification notes.

The editor previews the source label and keeps every previous value in inventory audit history. Saves require a global owner/publisher grant, normal CSRF and staff MFA. The current version and source context must match the opened form. A later source-context change is flagged for reinspection. A replaced source reference no longer receives that identity overlay. The import's archive year and collection membership remain bank metadata; the identity year is the year printed on the source. Source identity edits update learner source labels, not archive indexing or recruitment membership.

The nine previously inspected cover headings remain as fallback labels until an admin identity is recorded. An unverified paper does not acquire an official GK or GS title from its tags or filename.

## Retag a question or a selected batch

Open **Admin → Learning tags**, search text or an exact canonical ID, and optionally enter from a paper's identity editor. Choose up to 20 questions across result pages. Select a learning subject, topic and optional subtopic; enter a rationale and content evidence. Preview the selection, compare current and proposed paths, open the original sources, and tick each question that has been checked. Unchecked questions are excluded.

Submission creates ordinary immutable taxonomy contributions. The complete batch is rejected if any selected baseline changed or any path is invalid or unchanged. Retrying the same request does not create duplicate proposals. Existing related paths remain, except a related path identical to the new primary path is removed from the related list.

An independent reviewer can inspect a batch, check each revision, and approve checked revisions. The author cannot approve their own proposals. A publisher can queue checked approved revisions through the existing bank worker. Decisions and publications retain per-question history, current permission checks, conflict checks and recovery. A partial multi-action failure reports the completed count and refreshes the remaining statuses. No bulk action invents independent approvals.

Global owner/publisher permission is required to submit a batch. Global reviewers can review batches; subject-scoped reviewers continue through individual contributions. The existing contribution editor also has a current/proposed tag preview and the same shared GK/GS picker, alongside the original source PDF.

## GK/GS learning rules

- Learner bank filters, shared topic trees and the library show **General Knowledge & Studies (GK/GS)**.
- Equivalent topic names under the two old subjects are combined. Counts use distinct canonical IDs, including when both paths occur on one question.
- Stored `general-knowledge` and `general-studies` paths remain compatible with existing bank revisions, publications and old URLs. The picker chooses a valid stored path automatically and exposes its exact ID under Stored taxonomy reference.
- Related paths follow the same approval process. Pending classifications are excluded from learning discovery.
- Paper headings never decide a question's content topic. A recent-death/officeholder question is usually Current Affairs; a stable historical event belongs in History. Read the actual wording and exam date.
- General English stays a shared learning subject across technical and non-technical recruitments. Specialist technical questions retain their own content subjects and explicitly mapped source papers.
- Science joins the Group B common area only through the existing reviewed GK/GS source rules. Group B membership and source-context protections remain in force.

Shared topic IDs such as `gk-gs:current-affairs` are discovery aliases. They are never written into bank classifications or submitted as review taxonomy node IDs. Existing subtopic IDs are preserved.

## Current data cleanup

The four Shibu Soren questions are listed in `reports/gk-source-labels-20261028/taxonomy-review.json`. They have not been automatically retagged. Open `/admin/bank?tab=retag&q=Shibu%20Soren`, review their wording and propose GK/GS → Current Affairs.

The existing approved corpus has further incorrect classifications. The new controls do not certify those old tags. Record and review individual content corrections rather than relabeling every GK/GS paper wholesale.

## Follow-up implemented: clerical exam learning headings

UDC, LDC and Assistant now present the shared knowledge learning category as **General Knowledge** in their topic maps and question-browser subject controls. A question with no narrower topic uses the same contextual badge. Cross-exam discovery continues to show GK/GS. Clerical exam pages have English/GK shortcuts and navigation between the three exam collections. Source selection stays within the active exam even when a canonical question appears in several exams. This does not certify existing topic tags or invent official syllabus sections: printed paper identities and configured paper test rules remain source-based.

## 29 October 2026 — First clerical cleanup published

The previously pending four Shibu Soren copies and three Civil Engineering candidates were separately reviewed and corrected as part of120 taxonomy-only corrections. Their older dockets now contain dated resolution links; retained original status text is historical.102 missing topics were supplied, leaving25 broad entries. See reports/clerical-tags-20261029/STATUS.md. Luna generates recommendations; a separate explicit content review chooses corrections through the bank workshop workflow. Community contributions still require independent account decisions, and author self-approval remains prohibited. Never run an unrestricted historical classification merge against newer restored bank records; use the reviewed exact-ID bounded merge and inspect the complete bank diff before sync.

### 29 October 2026 — Science inside clerical GK

Assistant, UDC and LDC expose General Knowledge → Science with canonical Science topics as branch choices (Physics/Chemistry/Biology as available). Existing GK Science in the news also appears there and retains its original topic. The separate Science subject supports deeper canonical subtopics and old links. These are overlapping discovery routes over distinct canonical question IDs, not additional stored classifications. Ordinary clerical question filters use the same projected path as map counts. Other exams and Group B retain their previous rules. Broader Science retagging needs evidence-based review of question wording; a small tag count does not prove how many are missing.
