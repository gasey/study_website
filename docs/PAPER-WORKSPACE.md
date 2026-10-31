# Paper workspace

All exam paper routes share Paper, Focus and Question + PDF views. Printed question numbers, option order, directions, passages and source appearances remain authoritative. Search covers the loaded whole paper, including options and passages; Q73 jumps to that printed number. Loading and partial failure are explicit. The question map supports type, answer coverage, learning subject and visit-status filters.

UDC, LDC and Assistant display General Knowledge for shared GK/GS classifications. Science remains independently filterable and included in clerical GK. These are display/filter projections, not bank retagging.

Question + PDF lazily loads a local PDF.js worker, fonts and rendering assets. It opens the recorded source page, supports page navigation and zoom, and returns to the selected question's page. Missing page mappings are disclosed; there is no fabricated question bounding-box highlighting. Canvas pages have a descriptive accessible label and the searchable question transcription remains alongside them. Original PDF links remain available.

Flags and scratchpads last only during this workspace visit; refresh, leaving the workspace or account changes can clear them. They are not saved notes. Checked answers and picks use source appearance identity. Printed choices map back to canonical options; pending submits disable repeat actions. Written questions are not automatically scored. Existing official/reviewed practice eligibility and provenance remain visible under paper details.

Question data loads progressively in batches of 100; Paper mode renders 30 cards at a time. Completion follows actual appearance batches rather than a canonical-question count that may undercount repeated appearances. PDF code is only downloaded when needed. There are no API or schema changes in this release.

Validation and release evidence: `reports/paper-workspace-20261030/STATUS.md`.
