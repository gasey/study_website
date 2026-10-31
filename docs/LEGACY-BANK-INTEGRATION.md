# Legacy exam modules and the canonical bank

The platform’s `/bank`, exam collections, mocks, and learner attempts use one
canonical question ID. An exam track is a saved collection filter over that
bank; it does not copy question rows. A repeat printing can therefore share
one question while each `appearance` keeps its paper, printed number, option
order, and source evidence. Mocks and practice submit the canonical ID, and
the shared answer/provenance rules apply everywhere.

## What is connected today

The live app has six separate collections for LDC, UDC, Assistant Grade,
Combined Prelims, Group B Gazetted, and Group B Non-Gazetted. Their question
counts come from the live bank and their mocks draw from `v_scorable` only.
The server bank was synchronized from the documented local source on
2026-10-19; the sync preserved all 6 existing attempts. The current Combined
Prelims collection has 1,921 questions, 1,098 with official/key answers. LDC
has 349 questions (70 scorable); UDC has 2,194, Assistant 1,015, Group B
Gazetted 137, and Group B Non-Gazetted 1,425. UDC, Assistant, and Gazetted
currently have no keys that meet the strict official/key scoring rule, so
their mock actions remain unavailable until source-verified keys are added.

## Legacy app boundary

The older `india-study-map` website still bundles its own Combined Prelims
archive and UDC/LDC module bank, and stores their learning history under
module-specific browser keys. Those records are not automatically the same
as the canonical database rows. Never equate IDs based only on question
number, text similarity, or paper title; repeated questions and shuffled
options can silently attach the wrong source or answer.

`scripts/audit-legacy-bank-crosswalk.py` writes a conservative Combined
Prelims crosswalk. It accepts only normalized exact stem plus ordered-options
matches with one unique source appearance. Its canonical ID is the expected
ID from the normal bank-sync mapping; before using any row in a migration,
resolve the current `appearances.canonical_id` because a later reviewed merge
can redirect it. Current Combined Prelims audit: 422 unique exact matches,
1,475 ambiguous exact matches, and 1,518 with no exact match. The 3,339-row
legacy UDC/LDC/Assistant bank has 1,914 unique exact matches, 290 ambiguous
exact matches, and 1,135 with no exact match. The generated CSVs are audit
artifacts, not migrations. Ambiguous or absent matches must keep their legacy
record until the underlying paper/appearance has been reconciled in the local
bank source.

## Safe path to full convergence

1. Reconcile the older modules’ source papers into the local bank JSON as
   appearances, retaining original paper IDs, q-numbers, keys, answer-key
   references, and source defects.
2. Run the normal bank sync so each appearance receives its stable canonical
   ID. Do not write imported content directly to production Postgres.
3. Produce explicit old-ID → canonical-ID maps, including option-order maps;
   keep ambiguous rows pending for human review.
4. Move old module question loading to the canonical API. Keep each exam’s
   scoring rules, paper navigation, and local learning state keyed by its
   module, while storing question references as canonical IDs.
5. Retire bundled duplicate question content only after API coverage and
   progress migration have been checked against the legacy source manifests.

This yields one accuracy pipeline: a verified key correction, provenance
review, or classification update applies to every collection containing that
canonical question. Sharing the engine prevents drift; it does not itself
make an unverified answer correct.
