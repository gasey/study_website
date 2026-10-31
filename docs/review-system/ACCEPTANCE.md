# Review system acceptance evidence

Checkpoint: 2026-10-21. The contribution/admin workflow is implemented and deployed; full specification readiness is **not established**. Twenty-one passing automated tests do not mean all twenty release gates passed.

## Executed evidence

- `api/.venv/bin/python -m pytest api/tests -q`: **21 passed** on isolated local PostgreSQL; one upstream Starlette/AnyIO deprecation warning. See `reports/review-system/integration-tests.txt`.
- Fixture: five synthetic account/session identities, one original synthetic question/appearance and temporary original-MCQ additions, plus empty paper metadata required by historical migrations. All migrations apply from scratch; temporary databases are dropped. No real bank content is used as test input or altered.
- Full correction chain: API draft → submit → two independent reviewers → export → temporary bank write → actual CSV converter and sync SQL → live field verification → actual acknowledgement SQL → exactly one award/notification. Reviewed reversal follows the same path, restores the answer and appends a credit reversal exactly once.
- Full original-MCQ chain: same publication pipeline; stable appearance ID on replay, one 25-credit award, original community practice excluded from strict official scoring. Self-votes rejected, duplicate votes deduplicated, votes award no points, attribution opt-out removes the author from the leaderboard.
- Concurrency: same-key creation, simultaneous review decisions, and simultaneous mock submissions. One valid effect, stale contender gets 409.
- New mocks: real start/resume/submit/result endpoints retain original question/options/key after the canonical bank changes; immutable snapshot trigger rejects edits. Pre-existing sessions have an explicitly documented fallback.
- Browser: localhost author saved/submitted a correction; reviewer1 and reviewer2 independently approved it; owner dashboard, question search, explicit hold/release, source pane, role-sensitive controls and empty states inspected. Responsive views checked at 360/768/1440px. Screenshots in `reports/review-system/` use synthetic data and must not be presented as production counts.
- Live read checks: contribution page, admin sign-in gate, empty public leaderboard/feed projections; unauthenticated private queue returns 401. API health has 77,751 questions and 12,494 strict scorable questions. Shared family.hawayu.in returns final HTTP 200.
- Migrations 0030 and 0031 each rehearsed on a complete production dump clone, then applied through migrate.sh. The clone was dropped; user tables were not replaced.
- Bootstrap: 177 taxonomy nodes and 1,938 exact paper SHA256 registrations. No official keys were invented or promoted by this operation.
- Local user worker timer enabled, successful empty-queue run and server heartbeat `online`; queue waits while the workstation is offline.

## Release gates

| Gate | Status | Evidence / remaining requirement |
|---|---|---|
| A01 | Partial | API/editor/history and original-MCQ workflows implemented. Valid drafts durable; incomplete form autosave and every-kind browser matrix outstanding. |
| A02 | Partial | Device forgery, CSRF/origin, ownership, subject scopes, self-review, revoked approvals tested. Full expired-session/role matrix and staff MFA outstanding. |
| A03 | Partial | Optimistic locking, duplicate create/review races, exactly-once effects tested. Exhaustive approve/withdraw race matrix outstanding. |
| A04 | Partial | Immutable revisions/decisions, stale edits and quorum invalidation implemented/tested. Appeal/lease recovery browser matrix outstanding. |
| A05 | Partial | Positive registered-key mapping and mismatched hash/series/number/answer rejection tested. Human verification of actual official key content remains necessary; module comparison ingestion outstanding. |
| A06 | Partial | Whitelisted patches, option remapping, registered paper evidence, taxonomy hierarchy, unsafe paths and stable new-question replay covered. Every-kind image/source browser matrix outstanding. |
| A07 | Partial | Real sync SQL answer-only update, field/hash verification, replay and drift stop tested on synthetic bank. First real approved production publication awaits owner/review accounts. |
| A08 | Partial | Prepared receipt recovery and repeat sync/ack/credit/notice verified. Process kill injection at all stages and full outage recovery outstanding. |
| A09 | Partial | Strict official/key scoring retained; community questions separate; defects blocked. Historical derived eligibility predates this protocol and is not automatically certified reviewed. |
| A10 | Partial | New mock content/key snapshots and original-result consistency tested. Historical reconstruction impossible; adjusted assessment history not implemented. |
| A11 | Partial | Explicit holds, sync preservation and no automatic report-count holds implemented. Historical adjusted denominator handling outstanding. |
| A12 | Partial | Reviewed answer compensation and append-only credit reversal tested; attribution opt-out implemented. Duplicate/source relation reversal requires operator audit; reassessment outstanding. |
| A13 | Partial | Warm-paper/admin-sidebar design and responsive/browser evidence. Comprehensive keyboard/screen-reader/contrast and every error state audit outstanding. |
| A14 | Partial | Body size, strict fields, URL/path validation, CSRF/IDOR, private baseline redaction and active-mock gates tested. Full penetration/secret-log audit outstanding. |
| A15 | Pending | Paginated lists and indexed queries implemented; specified load targets/backpressure not measured. |
| A16 | Partial | Full clone rehearsal and fresh-schema tests pass; API/static deploy healthy. Rollback/disaster restore rehearsal outstanding. |
| A17 | Partial | Durable notices, private history, net-credit opt-out, published feed and active-mock gates covered. Every privacy/browser combination outstanding. |
| A18 | Partial | Worker timer/logs/heartbeat installed. External alerts, backup restore timing and capacity measurements outstanding. |
| A19 | Partial | Source registration/evidence gate, published fulfillment and reviewed duplicate relation implemented. Complete terminal-state UI verification and relationship reversal outstanding. |
| A20 | Partial | Synthetic contributor → independent reviewers → actual file/sync/receipt → learner workflow tested in separate integration cases. Full production sequence and corrected adjusted result outstanding. |

## Deployment identity

The checkout was already dirty, with prior production features not committed. Do not identify this as clean Git revision db557cb. `reports/review-system/deployment-artifacts.json` records SHA256 for deployed API/static artifacts and the local worker/schema/test sources. The deployment used scripts/deploy.sh (local build, rsync), not a server-side build.

The nominated owner email has no account yet. No substitute account was granted access, and no password was created. Account creation plus user confirmation is needed before the explicitly authorized owner bootstrap. See OPERATIONS.md for the exact command, recovery procedure and remaining constraints.

### Owner access update — 2026-10-21

The user confirmed account creation after deployment. Bootstrap granted the nominated exact account owner access, and an active all-subject owner grant was verified in PostgreSQL. This supersedes the pending-owner note above; it does not mark the outstanding acceptance gates passed.


## Scoring and MFA evidence — 2026-10-21

This checkpoint supersedes the earlier statements that adjusted scoring and staff MFA were unimplemented. Migrations 0032 and 0033 are applied to mpsc and must not be edited. The nominated owner grant exists, but the owner must enroll their own authenticator before making staff changes.

- Combined isolated PostgreSQL suite: **41 passed**, one upstream Starlette/AnyIO deprecation warning; command and output in reports/review-system/security/integration-tests.txt. Scoring-only prior checkpoint: 34 passed.
- Scoring regression coverage: changed/absent/reordered keys/options, legacy snapshots, denominator exclusions, original immutability, strict vs reviewed-derived eligibility, source-context proof, active mock disclosure protection, overlapping submissions, job cursor/claim behavior and semantic replay. Synthetic browser demo showed original 2 marks beside adjusted -0.5; screenshots in reports/review-system/scoring.
- MFA regression coverage: RFC6238 SHA1 test vector, account-bound encryption, password/CSRF guards, pending expiration, fail-closed missing configuration, rate limiting, staff enrollment/15-minute verification, login factor requirement, recovery rotation/disable and concurrent recovery-code one-use. No live owner MFA enrollment was performed.
- Browser checked login optional factor input and account-security status/password setup affordance; desktop/mobile screenshots saved without real secrets. Actual QR/confirm/recovery backend flow covered by integration tests; it was not manually completed for the real owner.
- Migration 0033 rehearsed against a production-data dump clone, then applied. Frontend TypeScript/Vite build passed. API/static hashes match production in reports/review-system/security/deployment-artifacts.json. Both hosted sites returned final HTTP 200; API reported 77,751 questions and 12,490 strict eligible.

A02, A09–A12, A16 and A20 now have additional evidence, not blanket pass status. Adjusted history exists; new estimates require a matching reviewed published answer. Four malformed-option rows no longer enter the strict pool. Historical sessions without snapshots are explicitly excluded from adjusted scoring. Bank-wide missing answers, first real independently approved publication, complete privacy/browser/race matrix, full load/accessibility/penetration testing, mail delivery, backup restoration and external alert delivery remain outstanding. A model code review is not an answer-key review vote. Astra found several scoring races and context gaps that were fixed; its final follow-up hit its usage limit, so final independent approval is not claimed.


## Repair workspace checkpoint — 2026-10-21

Read-only admin repair queue/inspector deployed; 44 combined tests pass. Added tests exercise every new issue selector, missing=true compatibility, subject restrictions, pagination, exact alternate-paper appearance, instructions/emphasis/source URL and active-mock answer disclosure protection. No schema migration or bank answer mutation. Browser verified missing filter and refresh, selected alternate Q19/page4 with option order C/A/B/D, then correction editor preselected C.B for that exact appearance. Desktop and360px screenshots and local/server artifact hashes are in reports/review-system/repair-workspace. No horizontal overflow measured at360px.

This improves A01/A06/A13/A14 evidence without declaring complete gates. Source PDF link/iframe integration exists, but the in-app browser did not visibly render the fixture PDF body; native embedding depends on browser PDF support and the UI supplies an external-tab link. No source bounding-box highlight or module comparison importer/adjudication UI is claimed. Actual missing answers were not resolved by this tooling packet.


## Learning rewards and exam journey — 2026-10-21

Migration0034 adds an independent XP/reward ledger, unique question claims, opt-in leaderboard, versioned owner reward catalog, immutable Pro redemption receipts and account exam checkpoints.52combined integration tests pass, including actual mpsc-role trigger execution and redemption concurrency/retry/expiry/effective-access reads. No bank content or real publication votes changed. New contribution-credit/reversal events feed reward ledger; existing contribution reputation is still distinct.

Browser synthetic20-question exam journey exercised bookmark/start/select/mark/save-next/reload/submit/permanent-result-refresh, exposing and fixing initialization race/result-URL bugs. Account Continue link retained page offset10. Desktop/mobile wallet/board/result proofs live under reports/learning-rewards, alongside exact artifact hashes. Main initial JS reduced to470.72kB by lazy exam loading.0034clone rehearsal and deployment passed; both sites returned200.

Redemption success is isolated integration evidence, not a production transaction. The provisional1000points→7days offer is disabled pending launch review. Future games/controllers, comprehensive abuse/privacy/load/failure/payment-scheduling matrices and the pre-existing full review-system release gates are not all complete. Earned activity XP does not certify answer-key correctness or exam rank.


## CMS packet — 2026-10-21

60 combined tests pass including8CMS tests; revision/idempotency/concurrent votes/redaction/review/reward/reversal/role privileges covered. Real-data clone migration and local build clean. Synthetic browser create→autosave→submit→owner publication→reader reactions persisted on refresh; desktop/360px paid-preview evidence recorded. Browser separate reader was owner; unprivileged redaction is an integration assertion. This does not close all P08 enterprise gates or bank adjudication. See ../CONTENT-STUDIO.md and reports/content-studio.


## Creator packet — 2026-10-22

66combined tests pass, including6new profile/graph cases: private-by-default response contract, repeated/concurrent follow uniqueness, no relationship rewards, hidden-profile feeds, bidirectional blocks/catalog/direct-reader filtering, report ownership/resolve and actual mpsc table grants/immutable audit. Clone migration0036 clean and applied. Unprivileged synthetic browser follow/feed refresh/block/unblock inspected with screenshots in reports/creator-profiles. This does not complete universal cross-product blocking or broader P08 release gates. See ../CREATOR-PROFILES.md.


## Publishing workflow polish — 2026-10-22

70combined tests pass: unified owner-only work filters/order/priority/totals, exact report selectors, immutable revision comparison sources, author feedback after35later autosaves, unrelated-account rejection and unread notification decrement/private caching. Frontend build passed. Browser owner queue→revision comparison→request changes→separate ordinary author→notification→feedback editor verified synthetically; screenshots reports/publishing-dashboard.0037clone/live index clean. Wider enterprise gates and bank adjudication remain; see ../PUBLISHING-DASHBOARD.md.


## P03 initial module intake — 2026-10-23

75combined tests pass, including5module cases: manifest integrity/replay and mpsc grants; conservative punctuation identity; immutable history; owner and linked-author permissions; filters/empty totals; explicit ambiguous membership; historical mismatch versus actual bank update; draft/source-request reference links/idempotency; official provenance rejection; optimistic triage and active mock withholding; old Evidence serialization compatibility. Local frontend build passes. Disposable browser confirms explicit module proposal, retained baseline, primary reasoning plus secondary reference, citation reader and linked intake.0038clone/live clean; real6754-row import and replay verified without bank writes or production contributions. See ../MODULE-COMPARISON-INTAKE.md for limits.


## Module research preparation — 2026-10-23

78combined tests pass,1upstreamwarning.3new preparation tests prove repeated module rows yield one answer payload, old immutable refs survive, bank bytes stay unchanged, packets/payloads hash consistently, unknown/retain records create no answer proposals, defect proposals contain no fabricated answer index, and duplicate/stale identity/tampered manifests reject. Real packet:20researched targets,15answer+3context+1defect payloads prepared only;76unassessed. New immutable imports preserve4historical runs; SQL verifies latest6754rows,zero production links/events. Build passes; synthetic browser panel and source link inspected. These are not human approvals or published corrections.


## Prepared module draft release — 2026-10-23

83tests pass/1upstreamwarning. Prepared draft tests prove original source preservation, actor-scoped concurrent/replayed/cross-appearance uniqueness, unchanged bank answer, only draft/zero independent decisions, membership/hash/role/packet-bank/active-mock/stale-context guards and dismissed-intake rollback. Synthetic browser create→prefilled editor→revision2 kept3evidence records. Learner browser verifies fixed-order2×2/List, persisted List on refresh, correct/wrong/selected states and360px single-column/no overflow. Build passes. No real owner publication rehearsal or completeP08claim.


## 2026-10-23 — Question discussions

91 isolated tests pass (one upstream Starlette/AnyIO deprecation warning), including correction-draft citation handoff without submission/bank mutation, account/CSRF/gating, concurrent replay, first-post visibility, paper identity, acceptance/feedback/no rewards, generic notification idempotency, conduct threshold/dismissal, sanctions/blocks/locks/withdrawal, immutable records and staff owner MFA/self-review/mock protection. Browser synthetic author→reply→accept/helpful→correction draft with3evidence→new pending post→owner moderation→author feed succeeded;360px no horizontal overflow. Applied0039after clone rehearsal; migration is immutable. Local/server API/static hashes verified, study API healthy and shared family redirect followed to its final page. No production discussion posts/events/notices were seeded; bank unchanged. Evidence in reports/question-discussions. These checks do not complete the broader P08 gates.
