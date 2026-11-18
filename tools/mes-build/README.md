# MES module and future exam modules

The web guide is `/exams/mes` in `india-study-map-app`; the native guide is `/mes` and opens from Exams.
Both render the same versioned catalog and use the same platform-neutral contract
in `web/src/lib/examGuides.ts`. The platform screens accept an `ExamGuide` prop, so
future exams can use their own catalog rather than copying MES-specific UI.

## Sources and boundaries

`syllabus-source.json` contains the 21 technical syllabus papers (79 units) from
Schedule I of Gazette Ex-507/2013. Running headers were removed and obvious OCR
spacing in headings repaired; descriptions retain the source's syllabus wording.
Common-paper study prompts are authored study aids, based on the English breakdown
and GS scope in Schedule I, rather than official questions or model answers.

`archive-source.json` pins 159 unique official PDF URLs and their official archive
sitting labels from the seven direct-recruitment pages listed in its sources.
The catalog covers 2012, 2014, 2015, 2018–2020 and 2022–2025. It does not imply that
every possible sitting or every branch has papers for every year.

The official syllabus directory linked the 2013 competitive regulations on
12 November 2026. No replacement competitive-exam scheme was verified. The
January 2012 P&E sitting is a separate **observed archive format**, with English I,
English II and aptitude marks/durations checked against original covers. It has
no claimed full legacy syllabus, technical marking breakdown, total or interview
score. Departmental regulations are a different examination and are not mixed in.

Papers from 2014 onward are **inferred** matches to the 2013 scheme based on sitting
year; both UIs disclose that inference. The official sitting label, rather than
the filename, controls the year: several official October 2025 URLs contain 2024.
Computer papers under the P&E Electrical Wing remain Computer Science papers;
cadre names are not subject labels. Common papers belong to each selected branch.

Original booklets are the past-paper reading experience. The web app reuses its
existing lazy PDF.js reader for 144 exact URL-to-source-file matches already hosted
in the source archive. The remaining 15 booklets open their official external PDF.
Native opens the official PDF. No PDF was copied into a new public directory.
The old archive also advertises a Mechanical 2015 Paper II URL ending in `.pdff`;
that exact official URL returns HTTP 404, so it is not counted as an available paper.
The misspelled 2020 `Englsih` source is displayed under General English, and the
2012 English I/II papers retain their separate paper numbers. This module
does not import, solve or relabel questions in the existing question bank.

Both platforms use the existing module views: Overview, Browse, Subjects, Papers,
Practice and Progress. Web reuses the LDC/Prelims `ExamOverview` header, tab styles
and paper cards while retaining the scheme dropdown and branch rail. Subjects
contains the syllabus checklist; Practice includes source-paper MCQs and syllabus
recall. Old `tab=Syllabus`, `tab=Past papers` and `tab=Recall` links still resolve.

Browse and Practice query existing questions using the exact decoded source-paper
ID from `readerUrl`, restricted to the selected scheme and branch. An external-only
PDF never triggers a bank query. Empty/untranscribed papers keep their PDF fallback.
The web Browse bar reuses the standard exam filter styles: paper type, source,
subject, topic, answer/study status and search, with year/pool/layout controls in
More filters. Subject/topic choices are approved bank taxonomy labels from the
existing taxonomy endpoint; global facet counts are not claimed as paper counts.
Every question request still includes the exact source ID. Paper type/year filter
the selected branch's source catalog, and Reset keeps the branch and scheme.

Question cards and normal answer APIs retain existing eligibility, source/reveal
gates and answer history. No unpublished MES collection ID is sent for answers;
this frontend guide does not publish a backend exam collection or a scored mock.
Progress is the device-local syllabus checklist, not a fabricated MES score or
server aggregate. Recall remains self-assessed and does not award an exam score.

## Rebuild and sync

From `india-study-map-app`:

```sh
python3 tools/mes-build/build.py
python3 tools/mes-build/build.py --check
node web/scripts/check-mes-module.cjs
node web/scripts/check-exam-overview.cjs ../india-study-map/web
cd web
npm run typecheck
npm run build
```

From `india-study-map-mobile` (Node 22+):

```sh
npm run exam-guides:sync
npm run exam-guides:check
npm run typecheck
npm run lint
npm test
```

The sync script copies only the shared contract and MES catalog; it never updates
native UI or touches the question-bank database. Counts are guarded so a changed
input cannot silently remove source material.

## Adding an exam or revising a scheme

The study catalog is presentation data. It does not replace the existing
**Modules & schemes → Exam schemes** admin workflow or certify a scheme revision
for full simulation. See `docs/ADMIN-SYSTEM-IMPLEMENTATION-20261106.md`. Scoring,
source inspection, pinned historical revisions, marking rules and paper readiness
stay under that existing backend authority. Never turn a source-linked guide into
a verified or eligible mock by changing a frontend JSON field.


1. Create a new catalog with a stable module ID, branch IDs and scheme IDs.
   Keep branch names separate from recruiting departments and cadres.
2. Record official sources, checked dates and the scheme's verification status.
   Do not call a scheme current because its PDF was uploaded recently.
3. Give each scheme its own paper definitions, formats, marks, durations, syllabus
   units, branch support and sources. Use `null` for unknown marks/durations.
   Never reuse current marks to fill an unverified historical pattern.
4. Preserve old versions. A revision gets a new scheme ID and new syllabus paper
   IDs; do not overwrite the old syllabus or silently migrate learner progress.
5. Assign each archived paper explicitly, using `schemeBasis: 'source'` only when
   verified. Mark year-based assignments `inferred`; leave `schemeId: null` and
   `schemeBasis: 'unknown'` if uncertain. An unknown paper must receive a review
   view before it is exposed by scheme-filtered screens; do not force a guess.
6. Run `guideProblems()` and regression tests for branch leakage, old/new format
   differences, unresolved references and progress separation. Include the new
   catalog in the mobile sync allowlist and add the platform routes/launchers.
7. Use `ExamGuidePage` on web and `ExamGuideScreen` on native. Set source links
   and generic metadata from the catalog, retain the six existing module views,
   and verify the actual UI on each. Use the shared source-paper helper for bank
   queries; never fall back to an unscoped bank query when a PDF is unlinked.

Progress keys include module + scheme + branch + paper + unit. Web uses the existing Study Desk identity to scope its local checklist; native
uses the existing account-scoped device storage. They do not
claim cross-device/cloud sync. No new scheme may inherit old progress by default.
