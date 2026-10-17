# Handoff: India Study Map (MPSC exam prep platform)

## Overview
India Study Map is a learning platform for MPSC exam prep. It combines a question bank, per-question community discussion, user-made study materials, games, an exam calendar and paid plans. It should feel like a social feed, but the focus stays on questions, exams and community.

Three surfaces:
1. **Learner app (desktop)** – `India Study Map v3.dc.html`
2. **Learner app (mobile, 390 × 844)** – `India Study Map Mobile.dc.html` (renders the v3 app at phone width; bottom bar: Home, Bank, Desk, Exams, Me)
3. **Admin Console** – `Admin Console.dc.html` (bank browser, corrections, duplicates, moderators, plans, flags, settings)

Plus `Color System.dc.html` (colour rules), `db/mpsc_schema_v3.sql` and `docs/BANK_SCHEMA_AND_EXTRACTION_GUIDE.md`.

## About the Design Files
The `.dc.html` files are **design references built in HTML**: prototypes that show intended look and behaviour. They are not production code. Recreate them in the target codebase's environment (React/Next.js, React Native, etc.) using its own patterns. If no codebase exists yet, a reasonable choice is Next.js + TypeScript + Postgres (the schema is Postgres-flavoured SQL).

To view: open any `.dc.html` in a browser with `support.js` alongside it. All styling is inline; logic lives in the `<script data-dc-script>` class at the bottom of each file (a React-class-like `renderVals()` that returns data and handlers to the template). Mock data in those classes shows the intended content shape.

## Fidelity
**High-fidelity.** Colours, type, spacing and copy are final. Match them closely. Copy in the files is the intended copy.

## Information architecture (learner app)
Navigation keys (keep these as i18n keys; labels changed, keys did not):
`nav.landing, nav.onboard, nav.feed, nav.bank, nav.exam, nav.modules ("Exams & tools"), nav.calendar, nav.games, nav.duel, nav.board, nav.results, nav.mistakes, nav.scoring, nav.create, nav.contribute, nav.market, nav.news, nav.inbox, nav.search, nav.profile, nav.avatar, nav.account, nav.pricing, nav.partner, nav.modq` (moderation queue).
Internal routes also include `material`, `module`, `checkout`, `processing`, `pay`.

"Exams & tools" = **Exams** (exam sets / modules) and **Tools** (Study Map, Timeline, etc.).

## Screens / Views

### Feed (Home)
Social feed of doubts, materials, duel invites, calendar items, cup results and map challenges. One area colour per card (see tokens). White cards on neutral background.

### Question bank & question detail
- Filters, search, provenance labels on every question (source paper, year, printing).
- Launch modules: **Combined Prelims** and **UDC/LDC**.
- Planned: repeat badge **"Asked 3×"**, filter and sort by repeat count (needs dedup, see guide).
- **Discussion is hidden until the user answers.** Locked during live mocks (`thread_locks`).
- Thread sections: **Explanations** (top one pinned), **Doubts** (with accepted answer, shown with ✓), **Error reports** by type: wrong key, typo/OCR, outdated, ambiguous, duplicate.
- Error-report rule: at **3+ independent reports** the question is hidden from mocks until fixed; after a fix, affected attempts are re-scored and reporters get **+10 XP**.
- Original paper viewer: page image with the question region highlighted (`page_images` with coordinates).

### Mocks / exam
Timed paper, results, mistakes review, scoring explainer.

### Study materials & Create
- Anyone can create: notes, flashcards, question sets, mind maps, timelines, charts, diagrams, map pins, formula sheets, mock tests.
- `/` slash-command block editor (Notion-like).
- No review step, no creator dashboard. Materials live on the author's profile; ranked by helpful votes and "marked studied" count.
- **Impact** (score improvement of studiers) shown only once **50 people** mark it studied.

### Study desks / class desks
Group spaces (Community area). Class plan desks for coaching classes.

### Games
Gauntlet Run, speed round, duels (1v1 challenge), weekly cup (placings award coins), Locate-on-map.

### Rewards
XP with daily limits, levels, coins (from cup placings), leaderboards, contribution points. Avatar customisation (spend coins).

### Exam calendar
MPSC dates, mock openings.

### Pricing & checkout
Plans: **Free / Pro / Class**. Payment via UPI and Razorpay. Flow: pricing → checkout → pay → processing → result.

### Profile, inbox, search, account
Profile shows user's materials, contributions, level, avatar.

### Moderation (nav.modq, inside the learner app for moderators)
Four tabs: **Reported, New users, Appeals, My actions**.
- Moderators handle **conduct only**: spam, harassment, answer leaks, copyright. Content accuracy is handled by error reports, not mods.
- Each moderator covers **1–3 exams**, **6-month terms** (`moderators`, `moderator_scopes`).
- Escalation over a rolling **90 days**: warning → 24h mute → 7d mute → suspension (`sanctions`, `mod_actions`, `appeals`).

### Mobile
Same app at 390px. Top bar trimmed; bottom tab bar Home / Bank / Desk / Exams / Me. Min hit target 44px. **Not finished:** full reflow and contrast pass on every screen.

### Admin Console tabs
`overview, bank (Browse / Corrections), browser, editor, builder, dupes, homepage, roles, plans, flags, settings`.
- **Bank browser:** filters, papers table, questions table, PDF pane with highlighted question region.
- **Corrections:** data quality issues (open error reports, missing keys, OCR problems).
- **Dupes:** duplicate review queue (`dupe_candidates`) – human confirms near-duplicates and "same concept" links.
- **Builder:** Module Maker – an exam/module is a saved filter set over bank questions (`collections`, `collection_sections`, `collection_papers`, `question_collections`). Designed, not built.
- **Roles / Moderators:** assign moderators and scopes.

## Interactions & Behavior
- Answer-before-discuss gate on every question.
- Thread lock while a live mock containing the question is open.
- Auto-hide at 3 reports; re-score on fix; +10 XP to each reporter of a confirmed issue.
- XP daily caps (see scoring screen for values).
- Material ranking = helpful votes + studied count; Impact appears at ≥50 studied.
- Hover/active states are in the files as `style-hover` / `style-active` attributes.
- Animations (avatar idle): `ism-breathe` (translateY 0 → -2.5px, loop), `ism-write` (rotate 0 → -5deg), `ism-steam`. Keyframes are in the v3 `<helmet>`.

## State / Data
Use `db/mpsc_schema_v3.sql` as the starting schema (written, **untested**). It keeps all v2 data and adds: `concepts, canonical_questions, dupe_candidates, page_images, users, posts, post_votes, content_reports, abuse_reports, collections, collection_sections, collection_papers, materials, material_votes, moderators, moderator_scopes, question_collections, thread_locks, mod_actions, sanctions, appeals`.

Key model: **one canonical question, many appearances** (each printing in a paper links to its master). Discussion, reports and repeat counts hang off the canonical question.

Extraction/dedup plan is in `docs/BANK_SCHEMA_AND_EXTRACTION_GUIDE.md`:
- Phase 1 migration – mechanical.
- Phase 2 exact + reordered-option merges; near-duplicates via embeddings go to human review.
- Phase 3 match copied questions back to bank originals; "same concept" links and answer conflicts need a human.
- **11,459 MCQs have no answer key** – flagged for review; do not infer answers with a model.

Page images: render source PDFs with `pdftoppm` → WebP, store in Cloudflare R2, record coordinates in `page_images`.

## Design Tokens

### Type
- Display / headings: **Newsreader** (500–600), Georgia fallback
- UI / body: **Public Sans** (400/500/600)
- Labels, metadata, codes: **IBM Plex Mono** (400/500), usually 10–11px, uppercase, letter-spacing .06–.1em
- Original-paper rendering: Times New Roman

### Neutrals
- Page background (warm paper): `#F4EFE4` (mobile canvas `#E9E1D2`)
- Card: `#FFFFFF` in app (Color System doc uses `#FBF8F1`)
- Ink (text, primary buttons): `#1D1B18`
- Secondary text: `#49443B`; muted: `#6B6457`; placeholder `#7A7366`
- Hairlines: `#E4DBC9`, `#DCD3C2`
- Brand mark only (vermilion): `#C0462C`

### Area colours (mid / soft tint / dark ink)
- Practice – `#2D5BD0` / `#E3E9F8` / `#1F44A6` – bank, MCQs, mocks, games, duels, cup
- Learn – `#7B45B8` / `#EEE6F7` / `#5E2F98` – materials, all block types
- Map – `#0E8287` / `#DCEFEF` / `#08605F` – Study Map, map pins, Locate
- Community – `#B23A9A` / `#F5E1F0` / `#86226F` – feed, doubts, explanations, desks, profiles
- Exams – `#B26B00` / `#F7EAD0` / `#7E4A00` – calendar, modules, papers, viewer, repeats
- Rewards – `#8A8A12` / `#ECEDCF` / `#545A06` – XP, coins, levels, leaderboards

### States (always with a symbol)
- Correct ✓ – `#2E7D46` / `#DCEFE1` / `#1F6234`
- Wrong × – `#C0392B` / `#F8DEDA` / `#9E2A1F`
- Needs attention ! – `#1D1B18` / `#EDE5D4` / `#1D1B18`

### Colour rules
1. A colour names an area, never a state.
2. Buttons and primary actions are ink. Vermilion is the brand mark only.
3. Text in an area colour uses its dark ink value; mid tone only for dots, bars, borders, swatches.
4. One area colour per card (a material in the feed is violet).
5. Nav shows each area's colour as a small dot, so the menu is the legend.

### Shape
- Card radius 10px; chips/pills 999px; small panels 8px.
- Borders: 1px hairline; emphasis borders 1px ink.

## Assets
- Fonts: Google Fonts (Newsreader, Public Sans, IBM Plex Mono).
- Image placeholders use `image-slot.js`; real images (avatars, paper scans) to be supplied.
- No icon set dependency; symbols are text glyphs (✓ × !).

## Open work (not designed or not wired)
- Study Map (interactive India map linked to questions + Locate game) exists in the user's codebase but isn't wired to the UI.
- Module Maker – designed in Admin › Builder, unbuilt.
- Page image pipeline (pdftoppm → WebP → R2).
- Three-tier dedup (exact, shuffled options, embeddings) and the "Asked N×" badge/filter/sort.
- Mobile reflow + contrast audit across all screens.
- Schema has not been run; test the migration first.

## Files
- `India Study Map v3.dc.html` – desktop learner app (all screens)
- `India Study Map Mobile.dc.html` – phone frames
- `Admin Console.dc.html` – admin tools
- `Color System.dc.html` – colour key
- `db/mpsc_schema_v3.sql` – schema
- `docs/BANK_SCHEMA_AND_EXTRACTION_GUIDE.md` – migration and dedup guide
- `support.js`, `image-slot.js` – needed only to open the HTML references
