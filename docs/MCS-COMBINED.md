# MCS Combined Prelims

The module `/exams/combined-prelims` separates Paper I (General Studies) and Paper II (Aptitude Tests) using source-paper membership. The same canonical bank and approved topic tags remain shared with other exams. Topic links, paper lists, practice and quick mocks retain the selected paper role. Existing `section=papers` bookmarks still resolve to the all-paper pool. Clerical modules retain General Knowledge; MCS displays General Studies, with Science independently available inside GS.

The 31 October 2026 release adds six Chase Academy-hosted recovered reproductions: Papers I/II for 2015, 2017 and 2018, each indexed as100questions. Their original host label is Series A; original-booklet/final-key reconciliation is pending. They are labelled recovered copies with provisional searchable transcription, source images and PDF links. Thirty-six questions have unresolved extraction of printed options, often pictorial; they remain source-review items. Textless choices explicitly direct the learner to the corresponding printed source image. No answer or verified classification was inferred for these600records. The six papers support source browsing; answer practice and scored tests remain unavailable until valid answers are published.

The paper catalogue has30listedbooklets/2,521questions, of which1,098retain eligible official keys. The total bank is81,147questions; the global official scoring pool remains12,708. The six recovered PDFs and143content-addressed source images are mirrored in the existing archive. Six paper documents are registered for subsequent admin source review. Existing questions, answers, attempts and historical collection version1remain intact.

Cards identify recent booklets with fewer than100availablequestions and distinguish recovered copies. The module uses “Quick practice” and generic platform paper sets use “Timed practice.” This release does not claim source-confirmed original exam simulation. Existing partial2023/2025booklets still need restoration.2012/2013questionbooklets remain unresolved. Mains is a separate future inventory.

## Import and review workflow

`prepare-recovered-mcs-papers.py --manifest manifest.json --output output-dir` prepares provisional source records and images. The manifest supplies each PDF's year, Roman paper number, local file, source URL and SHA256. Matching `.txt` layout extraction may exist beside each PDF; otherwise preparation invokes Poppler. Preparation verifies the PDF checksum, excludes cover instructions from question detection, requires printed positions1–100, preserves PDF page mapping, and never attaches an answer. Source images carry passages, figures, equations and option drawings that text extraction can lose. Images are intentionally shared by page span; they are not inferred question bounding boxes.

`import-recovered-mcs-papers.py artifact.json --receipt receipt.json` validates600records/sixpapers and source assets, then reports a dry run. `--apply` appends to the authoritative local bank under its lock, with a bank backup/receipt, and refuses IDs already imported. Use the normal bank sync afterwards. Never edit published migration0060or imported rows by rerunning the append command; corrections use the existing bank review/publication workflow.

Next review priorities: verify original source and booklet order; repair36option transcriptions; reconcile matching final keys including compensation/cancellations; add checked explanations and learning tags. A source image or a100-record extraction count alone does not establish a fully verified paper.

Evidence: ignored `reports/mcs-implementation-20261031/STATUS.md`, bank receipts, migration rehearsal, tests and live-check.json. Historical links: docs/plans/MCS-HISTORICAL-PAPER-SOURCES-20261031.md.

The checked six-source manifest is committed at `docs/sources/mcs-recovered-prelims.json`. Preparation can extract layout text with Poppler when a sidecar is absent. It requires PyMuPDF/Pillow for the source previews; the original PDFs are owned by the separate bank archive.
