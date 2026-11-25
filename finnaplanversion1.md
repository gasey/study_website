# Finna Plan — Version 1.0 (Production Readiness & Improvement Audit)

**Date:** 25 November 2026 (IST)  
**Scope Rule:** **V1.0 Feature Freeze.** This document tracks the hardening, audit, verification, and release readiness for **Production V1.0** across **Web (`https://study.hawayu.in`)**, **API (`/srv/api`)**, and **Mobile (`in.hawayu.finna`)**.  
**Operating Principle:** **Audit, harden, verify, and fix what already exists. No net-new features until V1.0 ships.** All new ideas stay frozen in Section 6.

---

## 1. Current V1.0 Surface Inventory

| Surface | Web (`study.hawayu.in`) | API (`/srv/api`) | Mobile (`in.hawayu.finna`) | Verified State |
| --- | --- | --- | --- | --- |
| Dual-section Navigation (Exams, Subjects, Guides) | Live | Live | Ready in code | 42 Web routes + mobile tab manifest sync passing |
| Question Browser (`Scroll \| Pages`, Checkpoints, Blind Re-Test, `MCQ \| Written`) | Live | Live | Ready in code | All unit & component tests passing |
| Source Provenance + Exact Concept Guide Chapter Redirect (81 Web / 80 Mobile routes) | Live | Live | Ready in code | 0 broken anchors (automated prebuild gate added) |
| 11 Editorial Concept Guides (107 chapters, 41 tables, 15 examples, 43 traps) | Live (bundled + DB merge) | Owner admin GET live (`401` unauth) | 11 bundled offline | Click `Sync 11` once in Web Admin for DB parity |
| Unified **Practice & Full-Paper Mock** (Untimed drills + 100-Q / full past papers) | Live | Live | Ready in code | Fixed 20-Q bug + `simulation=full` 422 crash |
| **Finna Quest RPG** (12-Floor Expedition, 3 Bosses, Campfire Shop, Endless, Daily 10-Q) | Live (`/games/quest`) | Uses live `/api/questions` & `/answer` | Ready in code (`/quest`) | Strict 8+1 allowlist + 429/network error recovery |
| Admin Console (39 sections, Guides Studio, Answer Conflicts) | Live | Live | N/A (Web-only) | 39/39 admin sections verified reachable |

---

## 2. P0 — Production Release Blockers

### P0.1 — Git Hygiene & Reproducible Commits
- [x] **`.gitignore` hardened in both repos:** Added `/state/answer-review/` to `finna/.gitignore` and `*.apk` / `*.aab` to `india-study-map-mobile/.gitignore` so private editorial receipts and 111 MB APK binaries are strictly excluded.
- [x] **Clean baseline commits created** in both `finna` and `india-study-map-mobile` (zero secrets, zero keystores, zero binary artifacts).

### P0.2 — API & Migration Audit + Controlled Deployment
- [x] Audited `api/migrations/0142_consolidate_exam_modules.sql` (confirmed already present on `/srv/api/migrations/`), `api/app/routers/collections.py`, `api/app/routers/guides.py`, and `api/app/services/publication_verification.py`.
- [x] **Caught & fixed a real regression during audit:** Uncommitted `publication_verification.py` allowed `explanation` patches on unanswered MCQs (failing 2 tests in `test_publication_verification.py`). Restored strict invariant (`'explanation'` blocked on unanswered MCQs) → **51/51 backend tests passed**.
- [x] Deployed Web + API cleanly via `./scripts/deploy.sh`:
  - Health: `{"status":"ok","questions":82383,"scorable":13376}`
  - `ism-api.service`: `active` · `/srv/api/ops-collector.py`: `OK`
  - `GET /api/guides` → `200`, `GET /api/guides/admin` (unauth) → `401`, `GET /api/guides/admin/polity-codex` (unauth) → `401`
  - `https://study.hawayu.in` (`200`) and `https://family.hawayu.in` (`307`) healthy.

### P0.3 — Sync All 11 Concept Guides into Live Postgres *(Owner Action — 1 Click)*
- [ ] Sign in as owner on Web Admin → `https://study.hawayu.in/admin/bank?tab=guides-studio` and tap **`↑ Sync 11 bundled guides to DB`**.
- [ ] Confirm `GET https://study.hawayu.in/api/guides` returns all 11 published guides. *(Note: both Web and Mobile already render all 11 immediately via bundled fallback even before this click.)*

### P0.4 — Fresh Signed Mobile Release Build & On-Device Smoke Pass
- [x] Rebuilt standalone signed `finna-beta.apk` (with all V1.0 upgrades: 11 offline guides, Unified Practice & Full-Paper Mock, Finna Quest RPG, and 429/network recovery) — *building / ready at `india-study-map-mobile/finna-beta.apk`*.
- [ ] Plug Android phone (`RZCX92XN9KT`) back in, install the refreshed `finna-beta.apk`, and complete a 5-minute unplugged smoke pass (Browse → Practice → Full-Paper Mock → Concept Guide deep-link → Finna Quest RPG).

### P0.5 — Auth, Allowances & Free-Tier Guardrail Verification
- [x] Verified unauthenticated access to `/api/guides/admin*` strictly returns `401`.
- [x] **Caught & fixed real Quest UX bug:** Both Web (`QuestGame.tsx`) and Mobile (`quest.tsx`) previously swallowed `catch` errors silently on `/api/questions/{id}/answer`. Added explicit `battleError` recovery banner that pauses the countdown timer, explains HTTP 429 free daily allowance or 4G drops clearly, and offers 1-tap `Resume` or `View Debrief →`.

---

## 3. P1 — Improvement & Reliability Audit

### P1.1 — Automated Build & Quality Gates
- [x] Added [`web/scripts/check-guides-and-quest.mjs`](file:///home/hruaia/workspace/projects/personal/finna/web/scripts/check-guides-and-quest.mjs) to `web/package.json` `prebuild` — every future Web build automatically verifies:
  - All **11 guides** & **81 question-to-chapter routes** match real anchors in `guides-seed.json`
  - **0 stray LaTeX** tokens (`\frac`, `\sqrt`, `\Delta`, etc.)
  - **0 raw HTML** (`dangerouslySetInnerHTML`) in `Guides.tsx`, `GuidesStudio.tsx`, `QuestGame.tsx`, `Practice.tsx`, and `AnswerConflictsAdmin.tsx`.
- [x] Added **3 new unit tests** in `india-study-map-mobile/tests/quest-game.test.ts` verifying strict exclusion of Radiology, Nursing, Dental, Engineering & Accounts, deterministic Daily seed, Boss floors (4/8/12), and WhatsApp share cards.
- [x] Verified full automated pass counts:
  - **API:** `51 passed, 0 failed` (`test_part7_v15_v17`, `test_exam_scope_drift`, `test_publication_verification`)
  - **Web:** `tsc -b`, `check-dead-links` (42 routes), `check-admin-nav` (39 sections), `check-guides-and-quest` (11 guides / 81 routes), `vite build` clean (`6.75s`)
  - **Mobile:** `tsc --noEmit` (0 errors), **44/44** unit tests, **39/39** component tests (`AnswerIsolation`, `QuestionCard`, `QuestionPosition`, `HomeNavigation`).

### P1.2 — Security & Performance Hygiene
- [x] Confirmed zero secrets, keystores, or raw HTML injection across new Web & Mobile screens.
- [x] Confirmed lazy code-splitting: `QuestGame` (`12.4 kB` gzip), `guides-seed` (`83.0 kB` gzip), `Practice` (`5.5 kB` gzip), `Guides` (`5.9 kB` gzip).
- [ ] Run manual 4G / 360px mobile browser spot-check on `/practice`, `/exams/udc`, `/guides/maths-and-arithmetic`, and `/games/quest`.

---

## 4. P2 — Question Bank & Data Quality Audit (Ongoing Post-Gate Hygiene)

### P2.1 — Taxonomy Mis-Tag Spot Audit
- [x] Sampled 160 live practice questions across `computer-science` (80) and `general-studies` (80):
  - Outlier rate is low (~0.6% — 1 clear outlier spotted: `cq_24d18a97aa21300b`, a sustainable-development action plan question currently tagged under `computer-science/networking`).
- [ ] Re-tag `cq_24d18a97aa21300b` (and any future spotted outliers) cleanly via Web Admin → `/admin/bank?tab=retagging`.

### P2.2 — High-Value Explanation Coverage
- [ ] Continue filling the ~12,608 verified MCQs lacking explanations via `/admin/bank` Authoring Console (`no-explanation` queue + 20-target grouped batch publishing).

### P2.3 — Paper Metadata & Deduplication
- [ ] Gradually enrich `duration_minutes`, `marks_correct`, and `marks_wrong` on flagship papers (`udc`, `ldc`, `combined-prelims`, `assistant`) as official notices are confirmed.

---

## 5. V1.0 Go-Live Acceptance Gate

- [x] **P0.1** Git clean, `.gitignore` hardened, baseline committed across both repos.
- [x] **P0.2** API & Web audited, regression fixed, deployed cleanly (`study.hawayu.in` `200`, `family.hawayu.in` `307`, `ism-api` active).
- [x] **P0.5 & P1** Automated Web/API/Mobile gates green, Quest 429/offline recovery fixed, security/HTML audit clean.
- [ ] **P0.3** Owner taps `↑ Sync 11 bundled guides to DB` in Web Admin (`/admin/bank?tab=guides-studio`).
- [ ] **P0.4** Install freshly built `finna-beta.apk` on Android device & run 5-min unplugged smoke test.

---

## 6. Post-V1.0 Backlog (Frozen — Do NOT Build Until V1.0 Ships)

1. **Finna Quest v2:** Server-synced Quest profiles & weekly Quest leaderboards, illustrated Boss sprites, co-op / friend raid rooms, and achievement badges linked to Finna Rewards.
2. **Admin Guide Pinning:** Optional per-question `guide_anchor` override field in Admin.
3. **Additional Concept Guides:** Native-speaker-reviewed Mizo Grammar & Literature guide, Service Rules & Accounts handbook, and optional technical stream primers.
4. **Paperless Question Spine (V.21):** Deferred until owner needs original questions without printed source papers.
5. **Store Distribution & Growth:** Google Play Store production rollout, iOS TestFlight build, and automated weekly digest notifications.
