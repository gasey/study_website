# Execution checkpoint — 2026-10-21

User request: continue the remaining work following the saved Astra plan. Preserve the dirty checkout and unrelated changes. No OpenCode/Ollama. Mail provider explicitly deferred (Choose later).

## Completed current packets

- P06 adjusted scoring deployed. Applied migration 0032 must not be edited. Original scores remain immutable; separate assessments include exclusions and provenance. Exact source/context snapshots, reviewed-derived admission, durable bounded jobs and active-mock disclosure gates tested. Prior scoring suite 34 passed. Astra identified locking/cursor/context/admission defects that were fixed; final additional follow-up hit usage cap, so no final Astra approval is claimed.
- Staff/account TOTP MFA deployed. Applied migration 0033 must not be edited. Routes /api/auth/mfa, UI /account/security, factor input at login, one-use recovery, password/recent-login enrollment, encrypted account-bound seeds and staff verification within15min. Production flags confirmed loaded; /etc/mpsc/mfa.env root:root0600, separate app systemd drop-in. Never print/regenerate the existing key. Owner must enroll personally; no production account is enrolled yet. No owner password changed.
- 41 integration tests passed, one upstream warning. Frontend build succeeded. Migrations rehearsed on production dump clones. 26 API files/14 static artifacts hash-equal to production. Both sites finalHTTP200. Two workers online; zero parked failed assessment jobs at final check.
- Documentation/evidence in reports/review-system/{scoring,security}, mirrored privately to server /home/ubuntu/ism-release-reports/2026-10-21-review. DEVLOG/PLAN/DECISIONS/ACCEPTANCE/OPERATIONS updated.

## Remaining work

The full P01–P08/A01–A20 release is not complete. Bank has77,751 total, strict12,490, estimate12,490 and wider practice67,026 at scoring checkpoint. Four malformed-option rows excluded from strict scoring. Last missing MCQ count1,652. No bank JSON content changed. Real correction con_f567526b066e4af2b89ab57292cd7e53 remains submitted with zero approvals. Dummy votes stay isolated.

1. Owner enrolls their authenticator, saves recovery codes, nominates actual independent reviewer accounts. No fake production approvals.
2. Continue evidence-backed bank adjudication and first real reviewed publication.
3. Advanced taxonomy/media/module ingestion tools and remaining reviewer matrix.
4. P08 restore/rollback, load/accessibility/security matrix and external alerts. Database and MFA encryption key both need encrypted backup/restore rehearsal; not yet verified.
5. Email verification/recovery awaits provider choice; no sender configured. Lost phone uses recovery codes, lost both has no automatic bypass. Legacy bearer moderation is not claimed MFA-protected.

Disposable API/Vite services and browser tab were stopped after evidence capture. No new PR/commit created. Shared VM family site must be checked after any systemd/Postgres/API change; never rewrite global Caddyfile.


## Latest continuation — product/bank work, 2026-10-21

User said move on from security; do not interpret as authorization to disable existing protections. Deployed repair workspace at /admin/bank?tab=questions&issue=missing. New AdminQuestionWorkbench.tsx; expanded read-only bank_workspace browse/inspect APIs; ContributionEditor now honors exact appearance query parameter. No migration. Issue filters/source context, option ordering, figures, provenance, existing corrections, paper links and refreshable URL state implemented. Paper views pick their own appearance rather than the primary one.

44 tests pass; browser missing/refresh/alternate appearance→editor flow checked, desktop360px evidence saved; frontend build and both-site health passed. Latest artifact identity is reports/review-system/repair-workspace/deployment-artifacts.json, superseding earlier receipts. Local docs/evidence copied to private server report folder. Disposable browser/API/Vite closed. No actual bank answers or production votes changed. Next product work can address module comparison ingestion/adjudication and evidence-backed missing-answer proposals; actual independent reviewer dependency remains. Full release gates still incomplete.


## Latest: exam journey + rewards, 2026-10-21

User authorized full exam journey and leaderboard/point system with future games/earned subscriptions. Migration0034 applied; NEVER edit it. Read docs/LEARNING-REWARDS.md for complete new policy/contracts. Deployed /rewards,/board, Admin Rewards & points, exam continuation/account checkpoint, source-aware practice and mock start/submit refresh fixes.52tests pass; actual mpsc trigger execution covered. Browser20Q mock answer/mark/position persisted on reload; permanent saved result refreshed; account checkpoint retained offset10. Points10XP+1 per unique verified answer,300dailyXP cap, no retroactive guest/old-history backfill; published contribution credit/reversal integration. Pro1000point/7day offer is provisional/disabled, no user response activated it. Separate entitlement does not rewrite paid billing.

Latest artifact/evidence is reports/learning-rewards (27API/17static); mirrored server report folder. Both sites healthy, bank unchanged. Games themselves remain unbuilt; extend trusted controller/shared award limits, never client /award. Full release gates, bank answer work, real reviewers, module ingestion and deferred mail remain. Stop this turn's synthetic browser/API/Vite after proofs. Current browser fixture printed score-d9e3e33ac1; disposable only, never production data.


## Latest: Content Studio — 2026-10-21

Implemented user CMS and material reader/admin review; migration0035 APPLIED, never edit. See docs/CONTENT-STUDIO.md for architecture, route/contracts, rewards and exact future-payment limits.60tests pass, clone migration clean, local build/browser synthetic workflow successful. New private evidence reports/content-studio. Shikshacom fuller work-folder CMS inspected and composition/settings/preview patterns adapted. User-author first independently approved publication20XP+5points max1/day; archive compensates, no self/demo/vote awards. Pro gates actual entitlements; individual paid preview has no checkout/payouts. Bank untouched. Staff MFA production remains enforced; synthetic fixture bypass only. Outstanding broad release gates, missing answers, real independent reviewers, deferred mail, games and payment-marketplace work remain.


Deployment verified:29API and19static artifacts match production (reports/content-studio/deployment-artifacts.json). Live study API and shared family site HTTP200; paid demo API body redacted, payments disabled, private/no-store. Bank remains77,751/strict12,490. Live screenshot paid-demo-live.png. Documentation and evidence mirrored privately to the server.


Final discovery deployment: main477.32kB (gzip137.69kB), editor22.49kB. Verified29API/19static artifacts match production; both study and familyHTTP200, bank77,751/strict12,490 unchanged. Live browser confirmed For you paid-demo card, LDC exact empty state and View all collection_id=ldc URL, English subject discovery and create link, and English selected in guest editor after public-metadata fix. Screenshots and release identity in reports/material-discovery; no synthetic publications, votes or saves created. No automated suite run this packet. Browser tab closed; no local services started. Evidence/docs mirrored privately to server.


Post-fix browser rehearsal used unprivileged outsider@example.test (confirmed on private profile), followed author (aggregate follower count1), saved public profile screenshot, loaded/refreshed Following material feed, blocked through inline confirmation (Following0, author in blocked list), unblocked (blocked list empty, Following remained0). Native-dialog tab closed through the selected browser core tabs API after wrapper close stalled. No production graph actions. Full suite66passed/1upstream warning in10.35s, migration0036 rehearsed against production dump and now APPLIED; never edit it.


Creator deployment complete: migration0036 applied, frontend/API deployed,30API and20static artifacts match local/server. Final build in deployment.txt: main478.68kB/gzip137.98kB; both study/familyHTTP200. Live graph counts public profiles0/follows0/blocks0/reports0 prove no real consent or synthetic graph seeded. Live directory shows honest opt-in empty state. Bank77,751/strict12,490 unchanged. Temporary APIs/Vite stopped and browser tabs closed; report/docs copied privately to server release folder. Final evidence reports/creator-profiles.


Final predeploy suite70passed/1upstream warning in9.72s, including account unread decrement and private response headers. Frontend main479.10kB/gzip137.94kB; ContentStudio33.95kB and dashboard6.28kB lazy chunks.0037index APPLIED; never edit. Synthetic owner→author browser complete and tab/API/Vite closed; fixture-only MFA bypass did not alter production policy. Release deployment/health identity follows.


Publishing release verified:31API/21static artifacts match local/server; study and shared familyHTTP200, bank77,751/strict12,490 unchanged. Live /inbox redirects to the real /notifications screen and correctly requires sign-in for account notices.0037index applied, no production moderation decisions or bank content changed. Evidence in reports/publishing-dashboard, mirrored privately with docs to server. Browser tabs and disposable services cleaned up.


2026-10-23 P03 initial module intake shipped:0038APPLIED,75tests/build pass; synthetic browser draft/link/citation proof, strict punctuation-preserving current identity plus retained historical candidates. Both real manifests imported/replayed:6754items7744candidates42packet refs, zero production links/triage events and no missing current exact appearances.97raw unique answer disagreements are evidence, not adjudicated errors. Bank remains77751/strict12490; no answers or real proposals changed. Scope/commands/limits docs/MODULE-COMPARISON-INTAKE.md. Broader release gates, source fulfillment and independent bank adjudication remain.


Module intake final deployment verified:33API/23static artifacts match production. Study/familyHTTP200; guest intake401. Full suite75passed/1upstreamwarning; no migrations pending. Canonical bank and strict-scorable counts unchanged. Evidence and documentation privately mirrored to /home/ubuntu/ism-release-reports/2026-10-23-module-intake.


2026-10-23 research batch1:97conflict module rows→96bank targets.20researched:15propose answer/4retain bank/1option defect,76unassessed.19typed payloads prepared only (15answer/3context/1defect), no production drafts/submission/approval/bank writes. New latest runs mar_777ff96d432e9c6c3c109524abc4e4cc and mar_ae39b2fe708119a52a6376257c0a4556 attach research; original runs preserved. Latest6754items, historical13508/4runs,zero linked contributions/triage events.78tests/build/synthetic browser pass. Source packet, hashes, PDFs renders and next-work docket reports/module-adjudication-20261023/README.md. Next research76; independent real reviewers remain needed for publication.


Batch1 final release:33API/23static artifacts match server,study/familyHTTP200,bank77751/strict12490unchanged. Research panel browser proof is synthetic; real imported research counts were verified by read-only SQL. Local/server docs,evidence and preparation scripts mirrored privately in /home/ubuntu/ism-release-reports/2026-10-23-module-adjudication. Disposable browser/API/Vite stopped and staging removed.


2026-10-23 user retired difficulty entirely. Removed admin/editor controls and implicit taxonomy difficulty patch. New API create/revise rejects the field; old histories parse and idempotent replays remain valid, but old proposals changing difficulty require revision. Compatibility data/snapshots retained, not exposed as product tags.80tests/build/synthetic browser pass. Evidence reports/retire-difficulty. Next implementation can make prepared research create user-reviewed drafts with all sources and baseline guards; no autoapprovals.


2026-10-23 prepared research→draft implementation complete:owner action validates packet/live baseline, creates one actor-owned draft across retries/concurrency/duplicate appearances, retains all citations on revision and uses unchanged independent review.83tests/build/synthetic browser pass. Answer cards now share persisted2×2/List, default2columns640px+, narrow1column, stableA–D and explicit state colours/markers across module/bank/paper/mock/detail/subject/Arithmetic. Source clerical/Combined/PH2 inspected; PH2list not2column. No bank edits, real drafts or migrations. Reports/research-drafts-answer-layout.


Release identity verified33API/23static files equal production,Study API healthy77751/strict12490,familyHTTP200. LiveLDC andCombined2-column option geometry verified read-only; GazettedGroupB remains the explicitly labeled written departmental coverage with no MCQ options. Production prepared-research events/module links remain0; synthetic drafts only. Final docs/evidence mirror and cleanup follow.


Final live read-only browser checks: LDC/UDC/non-gazettedGroupB each503px×2 and Combined532px×2, all4ordered options; screenshots saved. GazettedGroupB explicitly shows137written departmental questions/no verified keys, so no MCQ grid there. No live answers/drafts/votes submitted.33API/23static artifact identity and study/family health verified,bank77751/strict12490unchanged. Disposable fixture API/Vite and all temporary browser tabs closed; private server mirror includes docs/evidence.


## 2026-10-23 — Discussion/share packet deployed

0039applied after dump-clone rehearsal. Shared inline question discussions, source-context links, accepted/helpful replies, moderated feed projection, correction citations, conduct/block/sanction controls and transactional inbox notices deployed.91tests pass; synthetic workflow/mobile browser evidence and production artifact/bank/health receipts in reports/question-discussions. No real production posts/reviews/votes or bank edits; all bank-answer research remains queued in PLAN. Real independent reviewer provisioning, mail provider and remaining P08 gates still outstanding.
