# Navigation redesign — 22 November 2026

Status: **Header fixed and building locally. Production is still serving the
broken version** — nothing here has been deployed. Deploy is the owner's call.

## 1. What went wrong, and whose fault it was

The V.14 implementation of §VII.3.3 deleted the four desktop mega-menus and
the quick rail, replaced the primary nav with six flat links, and moved every
other destination onto `/index`.

**That is a faithful implementation of what §VII.3.3 said.** The spec was
wrong. It conflated two different problems:

| Real problem | What the spec did | Result |
| --- | --- | --- |
| Seven hand-synced nav arrays that drift | Replaced them with one manifest | ✅ correct, keep it |
| Mega-menus were *organising* 33 destinations | Deleted the organisation too | ❌ flat list of 40 links |

The mega-menus were the only place in the product where a destination carried
a one-line description explaining what it was. Removing them did not remove
complexity — it removed the *explanation* of the complexity and moved the same
links to a page nobody visits.

Two further regressions the spec did not anticipate:

1. **The "My exam" chip was deleted.** §0.11 makes the chosen exam the
   site-wide lens, and that chip was its primary affordance — one click from
   anywhere to the thing the learner is actually preparing for. Deleting it
   contradicts an earlier decided section.
2. **A literal revert is impossible.** The same phase consolidated the route
   table from ~88 paths to 37. The old `MENUS` table points at `/feed`,
   `/more`, `/english`, `/arithmetic`, `/mizo`, `/stats`, `/website-bank`,
   `/practice-sets`, `/tests/make`, `/news`, `/important-days` — **eleven dead
   routes**. Restoring the old header would produce dropdowns full of 404s,
   which is worse than what shipped.

So the fix had to go forward, not back.

## 2. What is now done

### `web/src/lib/siteMap.ts`
- Added `NavMenu = 'exams' | 'practice' | 'guides' | 'community'` and an
  optional `menu` field on `Destination`.
- Tagged 16 destinations with the nav item whose dropdown they belong to.
- Added `menuFor(menu)`, which returns a menu's contents in manifest order,
  excluding the nav item's own destination (clicking the label already goes
  there).

### `web/src/components/Header.tsx`
- **Dropdowns restored, generated from the manifest.** A menu can no longer
  point at a route the manifest does not define — the exact failure mode of
  the hand-synced table it replaces.
- **Label stays a link; the chevron is a separate button.** Clicking "Exams"
  goes to `/exams`. Only the chevron opens the panel.
- **Click or ArrowDown to open, never hover.** The previous implementation had
  both hover *and* click, which fight each other; hover menus are unusable on
  touch and trap keyboard users.
- **Escape closes and returns focus to the trigger.** `aria-expanded` and
  `aria-controls` are set only while open.
- **"My exam" chip restored** in the quick rail, which otherwise stays deleted
  — Revise and Play now live under Practice, Atlas and Chronicle under Guides,
  so only the chip needed to survive.
- Single column per menu rather than three: with 37 routes there are 2–4 items
  per menu, and a three-column grid holding four links is pure chrome.

### Verified
- `npm run build` passes (412 modules).
- All 12 generated menu links resolve against `App.tsx`'s live route table.

```
EXAMS ▾      Question bank /bank · Exam calendar /calendar
PRACTICE ▾   Build a test /practice/build · Shared tests /tests · Revise /revise · Play /games
GUIDES ▾     Subjects & shelves /library · Atlas /atlas · Chronicle /chronicle
COMMUNITY ▾  From the community /materials · Create & contribute /create · Creators /creators
```

## 3. The guard that would have caught this in 30 seconds

Add as a test, not a habit:

```ts
// web/src/lib/siteMap.test.ts
it('every manifest path resolves to a declared route', () => {
  for (const d of SITE_MAP) expect(routeExists(d.path)).toBe(true)
})
it('every nav item with a menu has at least one live child', () => {
  for (const d of destinationsForSurface('nav'))
    if (d.menu) expect(menuFor(d.menu).length).toBeGreaterThan(0)
})
```

This is the structural fix. A manifest that can silently point at deleted
routes will point at deleted routes. **Model choice matters less than this
test.**

## 3b. Dead-link sweep — done

`npm run check:links` (`web/scripts/check-dead-links.cjs`, pure static
analysis, no renderer needed so it runs on this box unlike the 36 existing
`check-*.cjs`). It parses `App.tsx`'s route table, every `to=` / `href=` /
`navigate()` literal in `web/src`, and every `siteMap.ts` path, and exits 1 on
any target that resolves to no route.

**93 dead references across 39 paths → 0.** 75 links rewritten across 47 files:

| Dead | Now | Count |
| --- | --- | --- |
| `/editorial`(+query) | `/admin/bank?tab=editorial` | 14 |
| `/rewards` | `/profile/rewards` | 12 |
| `/contribute`, `/contribute/new` | `/create/submissions`, `/create/new` | 15 |
| `/feed`, `/feed?tab=…` | `/home`, `/community/questions`, `/community?tab=following` | 7 |
| `/avatar` | `/profile/avatar` | 3 |
| `/paper-workbench` | `/admin/bank?tab=workbench` | 3 |
| `/current-affairs/manage`, `/current-affairs/automation` | `/admin/bank?tab=current-affairs`, `…?tab=ca-automation` | 5 |
| `/board` | `/profile/rewards` | 3 |
| `/learning/manage` | `/admin/bank?tab=learning` | 2 |
| `/trail`, `/trail/:id` | `/games?mode=trail`, `/games/:id?mode=trail` | 3 |
| `/english`, `/essay`, `/group-b`, `/website-bank`, `/practice-sets`, `/admin/atlas/bindings` | per §VII.14 | 8 |

### Two functional regressions found, not just dead links

1. **Topic Trail was unreachable.** `Games.tsx` navigates to `/trail/{id}`
   after creating a trail; that route was deleted, so creating a trail landed
   on the 404 page. `TopicTrail` now routes under `/games/:id?mode=trail` —
   it reads the same `id` param, and §0.12 already said Topic Trail belongs in
   the one Play hub.
2. **Stats was deleted, not demoted.** §VII.14 said *"Demote to a view — a tab
   on Home."* V.14 removed `/stats` without building the tab, orphaning
   `Stats.tsx`, `lib/stats.ts`, `stats-types.ts` and `styles/stats.css` —
   **while the API stays live and the mobile app still ships the whole Stats
   section** (`stats/index`, `stats/metric/[id]`, `stats/sources`,
   `stats/survey/[edition]`). Route restored and re-added to the manifest, with
   a comment, until the demotion is actually built. **Owner decision:** finish
   the demotion, or keep `/stats` as a destination.

Seven other screens are orphaned *intentionally* per §VII.14 — `English`,
`Arithmetic`, `Mizo`, `Essay`, `Mistakes`, `Vocabulary`, `LearningBoard`. Their
links now point at the consolidated destinations, but the screen files are dead
code and should be deleted once the replacements are confirmed equivalent.

## 4. Remaining work

Ordered by value. Each row names the model and effort I would give it, with
the reasoning in §5.

| # | Task | Files | Model · effort |
| --- | --- | --- | --- |
| 1 | The two manifest tests above | `siteMap.test.ts` (new) | Sonnet · low |
| 2 | Audit `/index` against the manifest — it should list destinations, not duplicate the menus. Sections in `SECTION_ORDER`, one line each, no cards. | `SiteIndex.tsx` | Sonnet · medium |
| 3 | Check the phone tab bar still reads from `destinationsForSurface('tabs')` and that `mobileTitle()` covers all 37 routes (it was written for 88) | `navigation.ts`, `BottomBar.tsx` | Sonnet · medium |
| 4 | `Footer.tsx` and `quickAccess.ts` — confirm neither re-hardcodes paths | both | Sonnet · low |
| 5 | Decide Desk vs Practice for the fifth phone tab (§VII.18.8) — needs a product call, not an implementation | — | **owner** |
| 6 | Dead-route sweep: any `<Link to=...>` in `web/src` whose path is not in the route table | all | Sonnet · medium |
| 7 | §VII.18 loop work — personal history on the card, `study_status` on `/bank`, the return block | many | **Opus · high** |

### Task 6 is worth doing immediately

The route table lost ~50 paths. The menus were the visible casualty; there are
almost certainly `<Link>`s elsewhere in 140 components pointing at the same
dead routes. One grep-and-fix pass, mechanical, high value.

```bash
grep -rno 'to="/[a-z0-9/-]*"' web/src --include=*.tsx | sort -u
```

## 5. Which model, and at what effort

The useful split is not "Sonnet vs Opus" in general. It is **which tasks
tolerate literal spec-following** — because this failure was not a capability
failure. The spec said delete the mega-menus; the mega-menus were deleted.

**Use Sonnet 5 at medium effort** for work where the spec is precise and
bounded and the failure mode is visible in a build or a test:
- rendering from a manifest, wiring a query param, adding a field to a type
- mechanical sweeps (task 6), test authoring (task 1)
- anything where "did it do what I asked" is checkable by running something

Raise to **high** when a migration is involved, because an applied migration
cannot be edited.

**Use Opus at high effort** for work where faithfully following the spec can
still produce the wrong outcome:
- any change to deployed navigation, auth, scoring eligibility, or the bank's
  integrity guards
- anything requiring reconciliation across the 7,000-line FINNAPLAN, where
  §VII.3.3 and §0.11 can contradict each other and the newer section is not
  automatically right
- §VII.18's loop work (task 7), which touches the question card on every
  surface and needs a measurement against §VII.16's acceptance bar
- writing the spec in the first place

**Use `xhigh`/`max` sparingly** — for adversarial review of something already
built (the §VII.6.2 conflict adjudication, a migration rehearsal), not for
authoring.

### The three rules that would have prevented this

1. **Run the build and check the output.** Not "it should compile" — run it.
2. **When a spec says delete something, ask what that something was doing.**
   The mega-menus were carrying the blurbs. Nothing else was.
3. **A spec written before a refactor is stale after it.** §VII.3.3 was
   written against an 88-route site and executed against a 37-route one. The
   implementer is entitled to say "this no longer applies" — and should.

Rule 3 is the one to put in `CLAUDE.md`.
