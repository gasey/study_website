# Content Studio and reader materials

Implemented 2026-10-21. Migration 0035_content_studio is applied; never edit it after deployment.

## User flows

- `/studio`: registered creator drafts, submitted work, decisions and published materials.
- `/studio/new`, `/studio/:id`: metadata/settings inspector, typed blocks, reorder/duplicate/remove, reader preview, explicit first save then debounced autosave, revision history and export-on-error recovery.
- `/materials`: search, access/saved filters, recent/helpful sort and pagination.
- `/materials/:id`: helpful upvote, studied status, account bookmark, report and access-controlled reader.
- `/materials/cms-paid-demo?preview=true`: clearly labeled paid-content demo with public excerpt and example price. Preview mode hides full blocks even for an owner.
- `/admin/bank?tab=content`: all-subject owner queue, exact draft inspection, publish/request changes/archive/restore and report resolution. Existing staff MFA applies to writes.
- `/notifications`: author decisions link back to the studio material.

## Storage and publishing

Reuse materials/material_votes as the single material store. Immutable material_revisions hold validated documents; materials has independent current-draft and approved published-revision pointers. Editing a published item does not expose its new draft. Submitting does not publish it. Owner publication validates the exact current revision and expected lock version. Stale changes return409. Create uses an account-bound idempotency key; mismatched retry payloads return409. Append-only material_events record actions. Author/reviewer access is checked server-side. Every mutation has same-origin CSRF and an atomic40/minute account budget; CMS bodies use the existing bounded request guard.

Canonical question blocks reference bank IDs and use the existing question renderer and answer/progress engine; materials do not fork question answers. Validate exam and subject IDs against registries. Block types: heading, paragraph, callout, quote, list, table, image, link, question. Text/rows/items/block counts and metadata lengths are bounded. Text is rendered through safe React components, not arbitrary HTML or scripts. Links/images require HTTPS with hostname and no credentials. Images are remote URL references with alt text, lazy loading and no-referrer; file uploads/storage/transforms are not implemented.

Catalog SQL excludes blocks. Reader responses for unauthorized accounts contain an empty blocks array and public preview only, with private,no-store caching. Free content is public; Pro content uses the existing actual account entitlement checker; paid-preview has no individual purchase entitlement and remains locked except author/owner inspection. Never introduce client-only body hiding or trust browser purchase flags. Existing zero materials were observed before migration; only the user-requested team demo was seeded, with no fake user activity or login.

## Reactions, moderation and economy

One helpful/studied record and bookmark per account/material. Authors cannot upvote or mark their own work studied. Full access is required for helpful/studied; previews can be saved/reported. Reports require a reason/note and are owner-resolved with audit. Helpful count supports discovery; votes award no points. Only published revisions appear publicly, and archive immediately removes them.

An independently reviewed first publication can earn20XP +5points, maximum one publication per account per India calendar day. Self-publication, paid demos and repeated publication do not earn. A persistent claim and shared reward lock prevent retry/race awards. Archive appends a compensating reversal once; restoring/re-publishing never earns again. Existing wallet debt/reversal policy applies. These creator entries integrate the existing opt-in leaderboard and wallet; points do not grant publication permission. Future games must continue using trusted server controllers and existing award limits.

## Future paid content

Pro membership gating works now. Individual paid-content checkout, seller onboarding, revenue share, payouts, tax/refund/dispute handling and seller entitlement receipts are not implemented. The example price is demo-only, no purchase button charges money. Build those as a separate verified payment/entitlement workflow with webhook idempotency, refund revocation and audit before activation. Existing Razorpay subscriptions are unchanged. The earned-Pro catalog remains disabled pending launch economics review.

## Design and Shikshacom adaptation

Read Claude v3 material/create sections and the fuller Shikshacom CMS in `/home/hruaia/workspace/projects/work/Admin-dashboard/src/blogBlocks/schema.js`, `pages/content/blocks/BlockCanvas.jsx`, `pages/content/ContentStudioHome.jsx`, `pages/content/BlogEditor.jsx`, plus `/home/hruaia/workspace/projects/shiksha-backend/content/models.py`. Adapted typed block composition, reorder/duplicate/delete, metadata/settings inspector and reader preview to this React TypeScript/FastAPI stack. This is not a wholesale TipTap/raw-HTML/Django copy. Warm paper cards, Newsreader headings, monospace labels, pill actions and gold callouts follow v3. Additional operational screens extend that system.

## Acceptance evidence and limits

60 combined isolated integration tests passed (one upstream warning), including8CMS tests covering validation, access redaction, idempotency, stale versions, immutable history, canonical references, concurrent duplicate votes, reviewer transitions, actual database role privileges, notifications, creator award cap and archive reversals. Migration rehearsed against a production dump clone without taking down the live API. Local TypeScript/Vite build passed.

Browser rehearsal used synthetic localhost accounts: create/save/autosave revision2, submit, separate owner review/publish, reader helpful/studied/save persistence, paid preview, desktop and360px layouts. The separate reader was the owner, not an unprivileged outsider; unprivileged access is covered by integration tests. Screenshots in reports/content-studio are synthetic, not production activity. ISM_CMS_DEMO=1 disables staff MFA only for the disposable local fixture; production enforcement is unchanged. No real owner password/MFA changed. No bank questions/keys/classifications changed by this packet.

This packet does not close every enterprise acceptance gate: live multi-user load, full accessibility/security matrices, restore drills, real independent bank reviewers, missing-answer adjudication, deferred mail delivery and advanced ingestion remain tracked separately. Deployment artifact identity and final health receipt are recorded under reports/content-studio.


## Contextual discovery — 2026-10-22

Published materials now surface in the For you community feed, exam overview, subject practice landing, English and the Arithmetic/Reasoning learn view. Shared MaterialDiscovery/MaterialCard use the existing catalog with sort=helpful and limit=3; no extra bank query or full-body response. Exam/subject IDs are exact filters, never inferred from title keywords. Context changes discard stale results; each panel has bounded loading/error/retry/empty states. View all retains collection_id/subject_id in catalog URLs alongside search/access/saved/sort/pagination; Browse all materials clears context and resets offset. Empty-state creator links prefill the existing editor exam/subject fields, still validated server-side. No unrelated fallback materials are shown for an empty context. Paid demos are labeled and force the existing preview reader. No new migration, publishing policy, awards or production content seeded.


Live discovery inspection found the preselected subject looked blank for a guest: the editor used account-only /review/taxonomy. Replaced that metadata read with public listTaxonomy subject facets (deduplicated by subject ID); server save validation still uses the canonical registry. Discovery navigation also resets scroll so opening View all from a long exam page lands at the catalog heading. No account or access permission was relaxed.
