# Solo-owner workflow and database map — 6 November 2026

The owner can clean routine questions without a compulsory typed reason and
publish their own prepared papers or learning tests without a second person.
The system records an attributable owner decision. Independent review remains
available, and ordinary website-user submissions retain independent approval.
This implements the requested workflow; it does not certify the whole bank.

Usage: [admin quick start](ADMIN-QUICK-START-20261106.md).

## Daily work

1. Open [Learning tags](https://study.hawayu.in/admin/bank?tab=retag), choose one
   source paper or saved issue scope and inspect the exact question/source.
2. Correct primary/related tags, wording/context, explanation or source locator.
   The global owner's note is optional. Use **Save & next**; the server generates
   a factual change summary and preserves the normal publication receipt.
3. For up to 20 similar tag fixes, preview once and apply. The optional note does
   not replace checking exceptions in the preview.
4. For a prepared paper, save, **Preview publication**, inspect its source/counts,
   then **Publish this saved paper as owner**. The explicit click records your
   source/options/figures/answer-evidence/explanation-availability confirmation.
5. For a test, **Preview owner publication**, inspect its questions/settings and
   **Publish test as owner**. A dirty/new draft is saved first and its exact saved
   version is published. Use the existing sharing controls afterwards.

The optional independent-paper-review controls are collapsed for owners. Existing
reviewer assignments and review history remain accessible. Learning collections
also expose explicit owner publication for saved content.

Reasons/evidence remain for substantive answer changes, key provenance, scoring
holds, verified scheme applicability and other source assertions. Stale-source
checks, assessment restrictions, staff MFA/CSRF, protected UDC/Prelims assignments,
bank authority/locking and publication/readback verification remain enforced.
No production question was corrected or approved merely to demonstrate the UI.

## Database map

Open [Database map](https://study.hawayu.in/admin/bank?tab=database), linked from
the admin header. Select **Content flow** for editorial relationships or
**Tables & foreign keys** for actual PostgreSQL constraints. Filter by question
bank, modules/tests or editing/publication; search, zoom, scroll or choose List.
Select cards to inspect descriptions, live counts, columns/primary keys and exact
join columns. Follow a connected table or open its associated tool.

The owner-only endpoint reads 28 curated content/workflow tables. Live verification
found 360 columns and 41 foreign-key links; the read-only server query took about
0.125 seconds. This is a single diagnostic observation, not a load benchmark.
Rule-based/JSON selections are labelled editorial relationships rather than fake
foreign keys. Rows are different units: appearances, canonical questions, test
editions and attempts must not be added as one question count. The coverage meter
measures approved primary-path detail, not semantic classification accuracy.

The map exposes counts/schema metadata, not row values. Account, credential and
billing tables are excluded. It offers no SQL console or raw database editing.

## Implementation and verification

- Routine edits reuse existing proposal validation, source bindings, immutable
  history and guarded publication. Automatic summaries describe actual fields
  changed; they never invent inspection or independent-review evidence. A stable
  retry key reuses the original baseline, even after publication.
- Owner paper decisions bind source SHA, payload, author, submission and preview
  version. Edited previews fail; workers recheck the current owner grant and
  matching evidence. Attribution is `owner`, distinct from `independent` and the
  earlier narrowly scoped `owner_ai` exception.
- Owner learning-test decisions validate existing eligibility and freeze immutable
  editions. Retry does not create another edition. Ordinary self-review remains
  prohibited in the independent flow.
- Additive migration0080 extends the paper decision constraint; it rewrites no
  historical decision or content row. Checksum: `1144966cad163381`.
- 191 backend tests passed on disposable databases. Focused interface checks cover
  routine notes/linked PDF evidence, Save & next, changed-answer boundaries,
  source-bound paper previews, owner tests, normal-user tests, source linking,
  cleanup/organisation and the read-only map. TypeScript/Vite build passed.
- A complete isolated paper publication exercised the actual guarded writer,
  normal sync SQL/readback and retry after interruption following SQL commit.
  Existing source identity, metadata and original answer were preserved; retry
  reused its receipt without appending twice. The fixture was never production.
- Migration rehearsal used a full production dump clone and compared content,
  attempt, assignment, grant, collection, mock and paper-workflow fingerprints.
  All compared rows were unchanged. All 117 task-start frontend asset hashes
  matched the deployed build before replacement.

The bounded API release/rollback directory is `/tmp/solo-owner-1793978445` on
Oracle. It backs up the changed API files and bank writer, and `backup/web.tar`
holds the prior frontend. Deploy through `scripts/deploy.sh solo-owner` and `web`;
do not replace unrelated dirty source. Publication workers were drained/restored.
Health, staff-route anonymous rejection, exact assets and the family site passed.
Canonical bank SHA256 remains
`b6d5920f9b951694cb6c92426ff0b8d6fa3b70ce7b82a2ead8f055edd0eb80e0`.

Evidence: `reports/solo-owner-20261106/`. Authenticated owner desktop/phone visual
QA, an actual owner-authored production publication, full bank classification
cleanup and real-traffic/load evaluation remain outstanding. No synthetic
production approval, WhatsApp delivery or ad activation was performed.
