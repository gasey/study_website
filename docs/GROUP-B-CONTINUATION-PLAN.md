> Current checkpoint — 4 November 2026: separate Non-Gazetted and Gazetted learner
> homes, searchable paper libraries, availability-aware study actions and scoped
> progress are deployed. See [the current design and verification record](GROUP-B-STUDY-DESIGN.md).
> The dated checkpoints below are historical; do not replay their deployment steps.
> Remaining content review and future saved study sets are separate work.

> Earlier checkpoint — 2 November2026: the Group B frontend is now deployed and live-checked. SSH/bank/taxonomy checks pass. May2025 source recovered; official consolidated copy includes July2025 interview amendment. Dated guidance is live. See reports/group-b-release-20261102/README.md and the release entry at the end of docs/PLAN.md. Resume at post-specific syllabus exceptions/future learner features, not deployment. The earlier checkpoint below records the pre-release state.

# Group B Non-Gazetted — continuation plan

Saved: 2 November 2026. This is the restart point for the next session.

## Goal and agreed product direction

Make Group B Non-Gazetted an easy preparation hub: choose English, General Knowledge or Current Affairs; study by topic; read questions or practise answers; move into a focused exam when appropriate. Technical papers are optional. Keep UDC, LDC and Assistant modules focused and preserve their individual schemes.

This is a preparation umbrella, not proof that all related posts share a classification or that one syllabus is a strict superset of the others. Existing NG source membership includes explicitly selected UDC/Assistant sources. LDC is currently a related link; its papers were not silently added to the NG pool.

## Exact checkpoint

### Already implemented and checked locally

- `/group-b` defaults to NG; explicit `collection=group-b` and Gazetted remain supported.
- Study home has English/GK/Current Affairs choices. Current Affairs resolves its actual approved topic from the scoped API.
- Separate Choose a topic / Read questions / Practise answers views; compact active-study heading.
- Recruitment-group selection and original-paper archives are collapsed secondary controls.
- One navigation helper resets incompatible filters on scope/subject changes. Read/practice switches retain topic, reset pagination/status and choose the appropriate answer pool.
- Only selected collection metadata loads; old source mappings cannot render during a collection change. Failed loads have Retry.
- GK labels agree across topic cards, selectors, breadcrumbs and generic question badges. Original paper titles remain intact.
- Production build, navigation regression checks and existing UDC checks passed. Local browser verified real API-backed Current Affairs → Read questions → English → Study home. No learner answers were submitted.
- Mobile viewport390/document375 and desktop1280/document1265 had no horizontal overflow.

### Deployment state

**Group B changes are not deployed.** The previous attempts failed at SSH socket creation before upload. Access was restored in the environment immediately before the owner asked for this plan; it has not been tested again and no deployment was attempted in this planning turn. Recheck access on resumption rather than assuming it is still blocked.

The earlier feed redesign and UDC repairs were deployed successfully in preceding work. Do not confuse those releases with the pending Group B frontend release.

### Important terminology correction

Do not say “Non-Gazetted has no General Studies.” The original January2026 Health & Family Welfare NG technical paper prints **PAPER-II (GENERAL STUDIES)**. The July2024 general scheme uses General Knowledge & Reasoning. GK is our shared learning-category label; original paper names and recruitment/year-specific schemes remain authoritative.

A May2025 official syllabus notice was found, but its PDF returned403. Do not apply the July2024 marks/timing scheme universally or label it the latest verified scheme.

## Resume in this order

### 1. Re-establish the checkpoint

- Read `CLAUDE.md`, `docs/PLAN.md`, `docs/DECISIONS.md`, `docs/DESIGN-FIDELITY.md`, then this file.
- Inspect `git status` and relevant diffs. There are extensive uncommitted UDC/admin/feed changes; preserve them. No commit, reset, migration or bank change is required for this release.
- Recheck SSH and `./scripts/sync-bank.sh --check` as required by repository guidance. Do not modify bank data as a side effect of a UI release.

### 2. Release and verify the existing Group B work first

Run from `/home/hruaia/workspace/projects/personal/india-study-map-app`:

```bash
node web/scripts/check-group-b-navigation.mjs
node web/scripts/check-udc-study.mjs
git diff --check
./scripts/deploy.sh web
```

The deployment script builds locally. Use frontend-only deployment; no API deployment or migration is needed for these changes.

Verify on the deployed site:

- `/group-b` opens NG Study home; `/exams/group-b-non-gazetted` shows the same focused entry choices.
- English, GK and Current Affairs links work. Current Affairs keeps its real topic ID and NG collection scope.
- Read/practice switching preserves topic and changes pool correctly. Switching subject/recruitment clears stale paper/topic/offset/personal filters.
- Browser Back/Forward, reload and a copied deep link preserve the selected learning view.
- Explicit Gazetted and combined-source routes still work. Original technical papers remain separate and accessible.
- Retry/loading/empty states do not show stale content. No unsupported coverage or mastery claims.
- Mobile360/390px and desktop: no horizontal overflow, usable controls, home scroll reset, source controls tucked away.
- UDC/LDC/Assistant links remain focused; no unintended source expansion.
- Confirm study API health and shared family site health after relevant server operations. Do not edit Caddy.
- Save live desktop/mobile screenshots and record the release in DEVLOG/PLAN. Existing screenshots are local previews only.

### 3. Finish the syllabus/terminology audit

- Retrieve the May2025 official PDF or an authoritative government copy; inspect general/technical schemes and subsequent amendments.
- Compare against the January2026 technical paper and specific UDC/LDC/Assistant schemes. Record exact source/date/post exceptions.
- Keep current-affairs historical questions distinct from present-day news. Preserve original wording and answer provenance.
- Review whether related-exam links satisfy the learning umbrella or whether more source membership is needed. Any expansion requires explicit paper/source-role review; do not union every LDC or technical question by keyword.

### 4. Learner enhancements after the release, if continuing product work

These are **not implemented yet**; keep them separate from release completion:

- Let students choose one or several common subjects and remember that preference. Use real available coverage, with a clear way to change focus.
- Add saved short study sets/continuation for Group B using the existing study engine only after verifying NG collection/filter support. Preserve source context, holds, answer provenance, immutable feedback and stale-question protection.
- Add targeted mistakes/revision within the selected scope. Avoid claiming syllabus completion or exam readiness from raw practice accuracy.
- Consider series-copy grouping only with the existing conservative identity guards. Do not delete bank records or rewrite historical attempts.

## Files to resume from

- `web/src/screens/GroupBStudy.tsx` — hub, view flow, scoped source metadata and technical archive.
- `web/src/components/GroupBNonGazettedIntro.tsx` — English/GK/Current Affairs cards and scheme relationship disclosure.
- `web/src/lib/groupBStudy.ts` — route parsing, filter transitions and display labels.
- `web/scripts/check-group-b-navigation.mjs` — scope/filter transition regressions.
- `web/src/components/ExamStudyTopics.tsx` — topic cards and scoped links.
- `web/src/screens/ModuleStudy.tsx` — shared practice/read UI; also contains earlier UDC work, so edit narrowly.
- `web/src/screens/ExamPage.tsx` — NG overview entry; also contains earlier UDC work.
- `web/src/lib/questionLabels.ts` — exam-aware fallback labels.
- `api/app/services/group_b_study.py` and `api/app/data/group-b-paper-roles.json` — existing eligibility/source-role authority; not changed by this UI slice.

## Evidence and source references

- Product/source notes: `docs/GROUP-B-NON-GAZETTED-MODULE.md`.
- Local screenshots: `reports/group-b-finalization-20261102/desktop.png` and `mobile.png`.
- Last build output: `/tmp/group-b-final-build.log` (temporary; may disappear).
- May2025 notice: https://mpsc.mizoram.gov.in/post/syllabus-for-non-gazetted-posts-may-2025
- Its linked PDF: https://mpsc.mizoram.gov.in/uploads/attachments/2025/06/22527d97ccb5918d986d0d1355be0323/syllabus-for-non-gazetted-posts-may-2025.pdf
- January2026 original cover: `../mpsc-question-bankv2/pdfs/Old_Questions/Direct_NG_2024-2027/General Studies Paper-II 2026..pdf`, page1.

## Completion bar

The current navigation release is complete only after deployment and live checks. Full syllabus coverage, factual certification of the bank, saved Group B sets and multi-subject personalization are separate unfinished work. UDC content validity work also has its own checkpoint; explanations remain deferred by the owner's earlier instruction.

Suggested restart instruction: “Continue from docs/GROUP-B-CONTINUATION-PLAN.md. Verify and deploy the existing Group B module first, then continue the syllabus audit without expanding bank scope automatically.”
