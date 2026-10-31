# Admin exams, papers and coverage

24 October 2026. Entry: `/admin/bank?tab=exams`; existing `tab=papers` opens the registered-paper view.

## Delivered workflow

One admin workspace contains Exams, All registered papers, Expected / missing, and Change history. Filter by exam, year and title/source filename. Exam cards show registered/expected/unmatched counts. Every bank paper remains available, including unassigned archive papers. Admin inventory associations organize coverage only; they do not silently change learner collection selection.

Paper detail provides source PDF open/download/optional preview; printed and distinct question counts; Official key, Verified solution, Needs review, Unsolved and Written question totals; links to the matching repair list; directions/passages present, flagged figures lacking images and empty stems; observed numbering gaps/duplicates/non-standard numbering; expected-count comparisons; registered paper/key/reference documents with actual provisional/final/superseded metadata and SHA256; correction stages and latest bank-sync receipt. Numbering gaps are candidates for inspection, not proof of loss. Missing directions are not automatically defects.

Question repair combines status, exam, paper, year, primary subject and approved topic filters, plus existing issue filters. Exam/year/paper constraints must match the same appearance. The representative source is selected from that intersection. Subject permission limits remain enforced. Counts are canonical statuses, with paper cards counting their appearances; shared questions are not duplicated in account history.

## Status and safety contract

`v_bank_answer_status` derives the four answer statuses plus written type. It never writes or approves an answer. Held/disputed/blocking defective MCQs need review. Missing MCQ answers are unsolved. Official/key candidates require valid options for the official status. Verified solutions require the existing current-content reviewed-publication view. An imported derived label is insufficient. Legacy API `verified` keeps its official/key meaning; `answer_status` is separate. Public list/detail responses expose no answer text.

Global owner/publisher grants can manage inventory. Global staff can read; subject-only reviewers retain their scoped question repair workspace. Existing session, CSRF, staff-MFA policy, write-rate limit and body limit apply. Inventory responses are private/no-store. Registered private PDFs require staff access and enforce overlapping mock/game answer protection. Public source PDFs remain existing public archive files.

## Expected register

Create an exam and record paper title, year/booklet, confirmed question count (including written questions), reference/listing and PDF URLs, evidence note and optional registered-paper association. Only HTTPS references without credentials are accepted; the server does not fetch supplied URLs. All metadata writes have audit records. Optimistic versions reject stale edits. Archiving preserves history and can be reversed through Archived expectations. An association cannot be removed while an active expected entry depends on it.

A source-context check is an explicit staff action, not an automatic import label. It stores a paper-context fingerprint. Subsequent question/options/instruction/passage/figure/page/source-path changes make the check stale. Counting a registered expectation is not a certification that the paper or answers are complete.

## MPSC listing intake

Captured the two user-open pages through read-only browser DOM:

- https://mpsc.mizoram.gov.in/page/old-question-ng
- https://mpsc.mizoram.gov.in/page/Old%20Question%20Paper-17-08-21-17-08-22

Preserved raw snapshots and hashes under `reports/admin-exam-inventory`. The importer deduplicates duplicate anchors within each listed exam; the same PDF appearing in different exam groups remains an expectation in each context. Blank-link exam entries remain unmatched. Group labels and source links are preserved, without trusting page headings as an exact date range.

Prepared921 expectations in122 source listing groups.669 have unique historical download-index URL plus bank-source-path associations;252 remain unmatched. This is association evidence, not remote PDF content verification and not a claim252PDFs are missing. The seven pre-existing learner exam collections remain distinct; the admin catalog totals129groups after this import. These two pages are not a complete census of every MPSC archive page.

`python3 scripts/import-mpsc-paper-inventory.py --snapshots reports/admin-exam-inventory/mpsc-browser-listings.json --bank ../mpsc-question-bankv2/bank/mpsc_bank_v2.json --download-index ../mpsc-question-bankv2/state/index.csv.bak-20260926 --output reports/admin-exam-inventory/mpsc-import-manifest.json`

Review the manifest; add `--apply` for trusted operator intake. This imports operational metadata only. Atomic idempotent manifests preserve manual changes on replay, never create users/reviewer approvals or change question content. Re-import does not silently relink an existing expectation; resolve new associations explicitly.

## Sources and local export

`python3 scripts/sync-registered-documents.py` copies only registered key/reference PDFs whose local bytes match their stored SHA256. Storage is `/srv/study/registered-documents`, root-owned and API-group readable, outside the static web root. Four existing registered key files were synced. Unavailable files remain explicitly unavailable; no fabricated link/version is added. Existing public paper paths are checked against `/srv/study/papers/source`; external URLs remain unchecked.

Use the authenticated Export inventory JSON link, or `python3 scripts/export-bank-inventory.py` for a trusted read-only SSH snapshot to `../mpsc-question-bankv2/state/admin-inventory/latest.json`. The snapshot is atomic and checksummed. Inventory metadata is server-owned; canonical questions remain local-bank-owned. Refresh this export after later metadata edits; no recurring export job was created. Question changes continue through review → local worker → bank sync → receipt. User attempts and progress are never imported over the bank.

## Acceptance and limits

Migrations0049and0050 are additive and rehearsed against production clones;0049introduces the inventory and0050optimizes the same status rules. Full isolated API/offline tests, frontend build and Node status/cache tests pass. Synthetic browser rehearsal covers exam→paper→status drilldown, source metadata, audited expected-count edit, zero verified results for unreviewed data, and expected-only year filtering. Source-context freshness, archived restoration, optimistic conflict, permissions/CSRF, replay-preserved edits, PDF Range/private headers and active-mock protection are integration-tested.

Manual identity/content review remains required for252unmatched entries, inconsistent official labels and numbering candidates. No automatic OCR/AI extraction, bulk answer approval, new final-key registration UI or complete outside-page census is claimed. Other archive pages can be captured using the same evidence format. This release does not grant a production-capacity or physical-device certification.

## Final receipt

167isolated tests and11Node checks pass;49API/63static artifacts match deployed hashes. Migration status through0050has no pending entries. The full ID/status signature is unchanged by0050; server aggregate execution improved2387.775→117.114ms. Root JS remains about229KB. Health77751questions/12490strict and bank336425b88b01…unchanged/IN SYNC. Authenticated inventory ownership was rehearsed in an isolated fixture, not by impersonating the real owner in production; unauthenticated live inventory requests return401. Native embedded PDF rendering was unavailable in the in-app rehearsal; open/download fallback remains available, and private Range transport is integration-tested.
