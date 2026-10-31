# English source presentation restoration

24 October 2026. User reported missing instructions, blanks and emphasis compared with the previous Group B / UDC-LDC modules.

## What changed

The older restoration read intermediate `tools/udc-ldc-build/extracted` files. The final generated modules contain later source repairs and passages not represented there. Extended the safe TypeScript literal exporter to both clerical and Group B generated arrays; no module code is executed. `scripts/restore-module-source-context.py` compares final English rows to the local authoritative bank using identical PDF SHA256, unique printed question number per paper, equivalent unmarked stem and ordered options, and compatible question type. Identical PDF aliases are handled independently; different sources/options/text and ambiguous numbering are retained in the audit report. Module IDs use both lower-case q001 and upper-case Q5; both are now parsed.

11,723 English module rows audited;1,732 source-verified equivalent module rows;1,077 bank appearances updated. Fields:847questionMarkup,329direction,59passage; fields overlap. These include restored and improved existing fields, not1,235new questions. Blank-run length changes alone do not overwrite existing markup, and empty module fields do not erase existing bank context. No stems, options, answer indexes/provenance, classification, paper identities or other bank fields are edited. Full before/after comparison across77,751records confirms this. Exact-byte local backup is retained with mode600; server has a private pre-release dump. Bank file updates are serialized with the publication lock and replaced atomically.

The shared React renderer now scans blanks before emphasis, renders underscore runs as visible ruled answer spaces, preserves nested italic/bold/underline markers and trailing text, and opens reading passages by default. Explicit collapsed mode remains available. It renders React nodes, never raw source HTML. No guessed grammar, typography or mathematical repair is applied to plain text.

Mock results now carry direction, question_markup and passage from the immutable test snapshot into immediate and revisited review pages. A later bank correction cannot substitute new instructions into an old result. Legacy results with no context snapshot leave those fields absent. Scoring, disclosure protection, marks and stored answers are unchanged.

## Evidence and boundaries

-152backend tests pass, one upstream AnyIO warning,26.91seconds. New tests reject wrong PDF identity, duplicate printed numbers and reordered options, and check context through API, mock display, submission and saved result after a later context edit.
-Renderer regression script verifies visible separate blanks, nested emphasis, default-open passages, explicit collapse, HTML escaping and repeat-render stability.
-Production build passes; API is shipped before web. Bank sync is the normal transactional local-to-server authority; canonical difficulty remains NULL.
-9,991 module rows could not meet this strict matching policy (8,034 lack available source identity/unique number;1,957 fail paper/number/stem/options identity). This is an audit backlog, not a count of9,991broken or missing bank questions. Some are absent source PDFs, combined descriptive tasks or rewritten module questions/options. Their formatting is not guessed or attached to a similarly worded question. No new module question corpus was imported in this release.
-Old immutable mocks keep the original presentation they actually displayed. Existing vocabulary receipts remain historical; changed source context invalidates unanswered tokens through existing version guards.

Evidence: reports/english-source-formatting. Live checks, artifact equality and mirror receipts follow below. No production practice answers or synthetic accounts are used for browser verification.

## Final live receipt

Local/server bank336425b88b01…IN SYNC; all77751classifications stillapproved. Health77751questions/12490strict. Canonical presentation now4243instructions/3158formattedstems/77passages; deprecated difficulty0. Latest sync ledger49attempts before and49after, no new canonical/appearance rows; later real-user activity can change totals. Vocabulary remains155eligible. A second dry restoration finds0changes.47API and33static artifacts exactly match local SHA256s. Family final200afterredirect; no errors in checked API journal.

Live read-only examples: cq_333ebe82fc519dbf shows source directions and italic “getting into a row”; cq_0df04918a17c2513 shows the source instruction and a ruled blank. No answer was submitted. Browser error log empty; temporarytab30closed. A first browser selector tried an unsupported heading-level filter, matched three headings and stopped; retried using the observed exact heading text. Screenshot proof uses actual production questions, not synthetic records. No physical-mobile or public-load certification. Shared Caddy unchanged. Private release docs, restoration proof, scripts and tests are mirrored beside the backup under2026-10-24-english-formatting.
