# Mizoram launch focus and unfinished mock recovery

## Implemented

The learner launch scope is **MPSC & Mizoram recruitment exams**, including the current LDC/UDC, Group B, Combined Prelims, LDE and departmental archive. Subject names describe knowledge (including world geography), not the geographical source of the exam.

Migration 0046 registers paper and collection `exam_scope_id` metadata. Existing Old_Questions archive papers are explicitly assigned to `mizoram-recruitment`; current collections are assigned to the same launch scope. A read-only preflight counted 1,938 archive papers: Direct 1,179; Direct_NG 84; Departmental 386; LDE 289. No current papers were outside that archive.

`launch_question_ids` derives distinct canonical IDs from assigned paper appearances. `v_launch_all`, `v_launch_practice`, `v_launch_scorable` and `v_launch_mock_practice` wrap the existing canonical eligibility views. Public question lists/details/answering, taxonomy, paper directories, exam collections, subject shelves, new mocks, Games, question search, home and scoring facts use these pools. Source choices are restricted to assigned papers. Community question discovery uses the same scope. Canonical global views and owner review tools remain available for future systems; account history and existing assessment records are retained. This is a discovery/pool boundary, not an authorization boundary for all content. People, notes and desks keep their existing audience rules.

Header shows the launch focus; subject shelves expose the exam filter without opening More filters. No outside-exam switch is exposed yet.

Games returns only the signed-in user's unfinished mock metadata and a server-generated resume URL. It preserves collection, paper or section and derived-practice mode. A proactive banner links directly to it; new-game/join actions remain disabled until submission. A mock created in another tab is discovered when a game start is rejected. Expired sessions can open through the same link and use the existing automatic submission flow. No answers or question snapshots are exposed in Games metadata.

## Imports and future expansion

Production paper/collection scope columns have **no default**. New unassigned or `outside-mizoram` papers remain out of learner launch pools. New bank paper records may set `examScopeId` to `mizoram-recruitment` or `outside-mizoram`. CSV and full sync carry that field. Legacy imports without the field preserve an existing registered scope through COALESCE; to exclude a registered paper assign `outside-mizoram` explicitly. Missing scope does not silently enrol a new import. Community-reviewed paper creation explicitly uses the Mizoram scope. Adding an exam system later requires explicit metadata and a product filter; it does not require question duplication.

Disposable test databases give legacy synthetic paper/collection factories a Mizoram default. This is fixture setup only; the production migration deliberately has none.

## Acceptance evidence

- 136 API/integration tests passed, including outside/unassigned exclusion, global engine preservation, scope assignment without copying, mixed-scope collection paper lists and private mock resume metadata.
- Isolated browser account resumed an expired synthetic section mock in derived-practice mode, reached its saved result and returned to Games with the banner gone and play buttons enabled. No real user attempt was created or submitted.
- Local browser screenshots are viewport evidence, not mobile or load certification.
- Migration rehearsed on a disposable production-data clone. Deployment/live receipts are in `reports/mock-resume`.

Limitations: no public outside-scope selector or generic scope management editor yet; scope must be explicitly assigned by import/operator workflow. Hidden/retired collection recovery and physical mobile/load certification are not newly verified here. This release does not solve missing bank answers or change classifications.

## Deployment result

0046 applied with checksum411aaf87923c3031; no migration drift/pending.44API and32static artifact hashes match. Production scope columns have no defaults;1938papers/eightcollections assigned. Live canonical/launch counts match:77751all/67026practice/12490strict. Geography remains936practice/942browse; LDCfilter13questions. Single request times0.7–0.9s for Geography,2.0scollections,0.6sgames; no capacity guarantee. Shared family site200after redirect. Private report mirror includes backup and browser evidence.
