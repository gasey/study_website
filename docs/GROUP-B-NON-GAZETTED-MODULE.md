# Group B Non-Gazetted preparation hub

Owner intent: offer broader preparation while allowing students to study only English, GK or Current Affairs. Focused UDC, LDC and Assistant pages retain their own exam identity, scope and requirements.

## Terminology and sources

Use **Group B Non-Gazetted**, **General English**, **General Knowledge**, **Current Affairs**. Current Affairs is a focused GK topic; General Science also belongs in the GK preparation map when supported by the exact source role. Do not rename original paper titles or stored taxonomy IDs.

The official 9 July 2024 general scheme calls Paper II General Knowledge & Reasoning; its technical scheme uses General Knowledge. These are evidence for naming, not authority to apply the 2024 scheme to every later sitting. Official source: https://mpsc.mizoram.gov.in/uploads/attachments/2024/07/63f9bc05c3b756aaa90fbf045d0ae494/syllabuses-for-group-b-non-gazetted-posts.pdf

A newer notice is listed at https://mpsc.mizoram.gov.in/post/syllabus-for-non-gazetted-posts-may-2025 (created 4 June 2025). Its linked PDF returned HTTP 403 during this review; exact current marks/timings were deliberately not added. The recruitment-specific LDC syllabus at https://mpsc.mizoram.gov.in/uploads/attachments/2024/10/dca2fc038ab5dba958fcf2c57625c4b4/syllabus-for-direct-recruitment-to-ther-post-of-ldc-under-mizoram-public-service-commission.pdf illustrates why focused modules must preserve their separate schemes.

## Module relationship

This is a preparation umbrella, not a claim that one exam syllabus contains every other syllabus or that every associated post has the same statutory classification. Existing Group B NG collection membership includes explicitly added UDC/Assistant sources. LDC is linked as a related focused route; this release does not claim or manufacture LDC membership in the Group B source union. Computer, arithmetic, reasoning, written language, typing and technical requirements depend on the actual recruitment. Common English/GK practice alone is not full exam preparation.

## Implemented first slice

- `/group-b` defaults to Non-Gazetted. Explicit `collection=group-b` retains cross-group discovery; Gazetted remains selectable.
- NG overview and common-subject entry offer English, GK and Current Affairs choices, independent of technical papers.
- Current Affairs resolves its real approved topic ID from the scoped API map; no guessed topic links or fabricated coverage counts.
- NG topic cards and subject filter show General Knowledge; stored `gk-gs` identity remains compatible.
- Existing bank, source roles, question eligibility, attempts and answer protections remain unchanged.

Next stages: verify the May 2025 document and post-specific exceptions; review any further source-union expansion explicitly; add learner-selected subject combinations and bounded saved sets only with clear syllabus/source scope. Current Affairs here means historical questions, not a current news service.

## Final navigation pass — 2 November

Study home now contains the three focused choices; topic maps and question controls belong to their selected study view. Practice/read mode changes retain topic selection and deliberately change the answer pool. Changing recruitment or learning area discards incompatible paper, topic, search, page and personal filters. Original archives and recruitment selectors are disclosed only when requested. Only the selected collection metadata is loaded; stale source mappings cannot render while another collection loads. Failed metadata/current-affairs requests have Retry controls. Returning home scrolls to the beginning; active study uses a compact heading.

Terminology correction: the original January2026 Health & Family Welfare Group B Non-Gazetted technical examination explicitly prints **PAPER-II (GENERAL STUDIES)**. Confirmed from page1 of `../mpsc-question-bankv2/pdfs/Old_Questions/Direct_NG_2024-2027/General Studies Paper-II 2026..pdf`, consistent with the existing source-role manifest. Therefore GK is our shared discovery label, not a claim that NG never has a GS paper. The module disclosure now states this distinction.

Navigation transition checks and existing UDC regression checks pass. Local browser with real API-backed data verifies the current-affairs shortcut, GK breadcrumb, selected topic, mode switch and clearing filters on English selection. Mobile390px has document width375px. Deployment remains blocked by SSH socket Operation not permitted; local checks do not establish a live deployment.


## Released and syllabus recovered — 2 November 2026

This entry supersedes the earlier SSH/deployment and May2025-access limitations above. SSH and read-only sync checks succeeded:81,627 questions and approved taxonomy claims in sync. Group B frontend deployed successfully, then redeployed with dated syllabus guidance. Live default NG home, Current Affairs topic/pools, English filter reset, Back/Forward, reload, home scroll, technical archive and recruitment-group switching checked. NG exam overview shows the same entry choices and amended guidance. Viewports1280/390/360 had no horizontal overflow. API healthy; family site HTTP200 after redirect. No learner answers submitted.

Recovered the original May2025 PDF via ordinary HTTPS and the five-page source linked by the official direct-syllabus listing (June2026 attachment directory). Visually inspected all pages, including the15July2025 amendment: general interview37.5, total337.5. Added source-linked dated general/technical scheme guidance inside the existing relationship disclosure. Historical rules, practice scoring, source membership and bank remain unchanged. Exact source URLs, page findings, hashes, verification limits and live screenshots: `reports/group-b-release-20261102/README.md`.

Remaining: exact post-specific/UDC/LDC comparison and later-amendment audit, learner subject preferences and Group B saved sets. Do not infer full current-syllabus coverage from this release.
