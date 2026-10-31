# Original paper PDFs

The canonical bank stores the PDF-relative source path on each paper. Question
appearances add the printed page, so the API returns a source URL for every
appearance and the UI opens the paper at that page.

## Storage and retrieval

- The 1,938 source PDFs referenced by the current bank are mirrored to
  `/srv/study/papers/source/Old_Questions/...` on the study host (about 665 MB).
- Caddy serves them at `/papers/source/Old_Questions/...` with byte-range
  requests and a one-day cache. This keeps PDF bytes out of PostgreSQL and out
  of the frontend build/deploy directory.
- `papers.pdf_url` remains available for explicitly curated external or object
  storage URLs. Otherwise the API builds a safe archive URL from `source_file`.
- `appearances.page` controls the `#page=N` fragment in question source links.

## Sync after changing the bank

From this repository, run:

```sh
./scripts/sync-source-pdfs.sh --dry-run
./scripts/sync-source-pdfs.sh
```

The sync refuses to publish if any bank paper has a missing PDF, unsafe path,
or duplicate source path. It syncs only bank-referenced PDFs; OCR text and other
working files are not published.
