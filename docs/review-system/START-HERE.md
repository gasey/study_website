# Handoff for Luna or another implementation model

The user requested a complete community contribution and review system for India Study Map. This directory is the design handoff, not a shipped feature.

Read:
1. `CLAUDE.md`, `docs/PLAN.md`, `docs/DECISIONS.md`, `docs/DESIGN-FIDELITY.md`.
2. `docs/review-system/SPECIFICATION.md` — required behavior, architecture, contracts and 20 acceptance gates.
3. `docs/review-system/IMPLEMENTATION.md` — ordered work packets and testing obligations.

The newest user direction allows reviewed derived answers for estimated tests. The spec defines a separate estimate mode and requires review evidence; do not bulk mark existing `derived` or `inferred` answers official or reviewed. Local JSON stays the bank authority. The server owns user submissions/reviews; accepted changes return through an exported, guarded publication workflow.

Copy this instruction into the implementation terminal:

> Implement the community contribution and review system in `india-study-map-app` using `docs/review-system/SPECIFICATION.md` and `IMPLEMENTATION.md`. Start by reading the project instructions and inspecting existing edits. Complete P01 through P08 in dependency order, with working end-to-end integrations and acceptance evidence. Preserve unrelated changes, old clients, user data and the local-bank/server-feedback ownership boundary. Do not modify production bank data as a test. Use explicit per-account review permissions and immutable revisions; no shared owner token for volunteer reviewers. Implement the Claude v3 contribution design with real state and APIs. Include reviewed derived answers in a clearly labeled estimated mock mode with score snapshots. Keep every acceptance gate pending until verified; record failures and deployment limitations honestly. Update DEVLOG.md and a resumable checkpoint after each packet. Ask for focused stronger-model review for security, scoring, migration or publication problems you cannot resolve, and supply the concrete diff and evidence. Do not claim production readiness until all specified release gates pass.

Current implementation status at handoff: no contribution-system code, migration or deployment was added in this design task. Existing moderation/account/bank functionality is described as reuse, not proof that this new system is implemented.

## Implementation checkpoint — 2026-10-21

The preceding paragraphs describe the original design handoff. Implementation has now begun shipping: migrations 0030/0031, the scoped review APIs, contributor/admin UI, local publication worker, source/taxonomy registry, credit/votes/notifications, legacy report queue and new-mock snapshots. Read **ACCEPTANCE.md** and **OPERATIONS.md** before continuing. The full P01–P08 definition of done is not passed; do not infer production readiness from a successful build or the passing integration suite.
