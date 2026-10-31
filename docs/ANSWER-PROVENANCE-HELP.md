# Answer provenance and evidence contributions

24 October 2026. User requested explanations of derived/unofficial labels and a way to strengthen answers, including when the authority has not published a key.

## Learner behavior

All Bank/Library question cards and detail pages use one provenance component. Hover shows a concise native tooltip; click/tap/keyboard opens a full-row in-flow help panel, avoiding clipped floating panels. It explains provenance, scoring boundaries, evidence submission and contribution credit. No answer text is included in help or metadata.

The learner-facing labels were simplified on 24 October 2026:

| Label | Rule | Scoring meaning |
|---|---|---|
| Official key | Existing official/key provenance; no overriding dispute/blocking source defect | Eligible strict official-key questions only |
| Verified solution | Derived with current reviewed publication; no overriding dispute/blocking source defect | Eligible labelled estimates; remains unofficial |
| Needs review | Unreviewed derived/inferred, or disputed/blocking defective item | Does not grant scoring eligibility |
| Unsolved | No recorded answer | Browse/contribute; not proof no official key exists |

Written questions show Written question rather than Unsolved; an MCQ index does not apply. Expandable source details retain official versus transcribed versus derived versus inferred provenance. Bank source filters are explicitly advanced source details, separate from verification. Source flags override a trusted-looking badge. No trust percentages or AI-consensus promotion.

Final key is an authority document version, not a synonym for Verified solution. The simplified badge does not invent final-key metadata. The legacy API verified boolean still means official/key and is unchanged; it must not be repurposed as proof of human review. The client display helper cannot grant review approval, publication or eligibility.
A question-specific Submit evidence or a worked solution link opens the existing answer proposal editor. Non-official MCQs also have an always-visible Help verify action. The editor explains a step-by-step solution, reliable references, alternative options and date-sensitive facts; retaining the same answer while meaningfully improving the explanation is valid. It defaults new inferred/unkeyed answer proposals to derived rather than submitting unsupported inferred provenance.

Two independent authorized reviewers are required for answer proposals, excluding the author. Changes to official/key answers also require a senior reviewer. Publishing and the bank worker retain immutable source/current-content checks and local-bank authority. No-key solutions do not become official by agreement, votes or a confidence label.

## Existing credit and scoring reused

Eligible published answer improvements earn 10 contribution points through the existing idempotent publication ledger. Drafts, submissions, upvotes and unchanged/no-op proposals do not mint publication credit. Reversions/duplicate-source requests retain existing exceptions and ledger behavior. Contribution points are separate from study XP and spendable reward balances; this UI does not promise cash or subscription redemption.

No new reward, voting, answer approval or scoring bypass was added. Imported derived answers are not relabelled reviewed. The API reviewed_derived boolean uses v_reviewed_answer_publications for both paginated lists and detail. Official status remains separate, and source-content changes can invalidate derived eligibility. Review counts, points and official-key status are never supplied by the browser.

## Validation

153 backend/integration tests pass, one upstream AnyIO warning, 28.05 seconds. Added assertions prove imported derived answers are not reviewed and a genuine applied publication is reviewed. Existing tests cover independent reviews, stale sources, no-op rejection, publication receipts and idempotent/reversed credit. UI regression checks verify accessible help, distinct provenance, safe question links, no answer leakage and publication-only point wording. Production build passes. Initial build caught nullable answerSource in the editor includes() check; normalized null to none without changing stored provenance. No schema/bank/reward/account data is changed by this release.

Live/browser/artifact/mirror receipts follow after deployment. Manual evidence quality and availability of independent human reviewers remain necessary; no automatic truth guarantee or AI consensus is claimed.

Final release: API-before-web deployment complete;47API files and33static artifacts exactly match local hashes. Health77751/12490; family follows redirect to200; no errors in checked API journal. Bank checksum336425b88b01…unchanged/IN SYNC, no migration or reward-data changes. Live native summary opens accurate unverified/scoring/evidence/10point help and retains its exact canonical question link; no answer or contribution was submitted. Final wide help screenshot replaces the initial narrow-column capture. Browser console clean; temporarytabs31/32closed.153tests/28.05seconds plus UI checks; no physical-mobile or capacity certification. Private notes/source/tests/evidence mirror under2026-10-24-answer-provenance-help.
