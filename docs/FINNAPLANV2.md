# FINNAPLAN v2 — implementation guide: modules, subjects and the full bank

Written 23 November 2026. This is the **executable companion to
`FINNAPLAN.md` Part XI**. Part XI holds the reasoning and the measured evidence;
this file holds the order of work, the exact files, the gates and the rollback.
Where the two disagree, Part XI is the design authority and this file is wrong.

**Read before starting:** `CLAUDE.md`, `FINNAPLAN.md` §V.0 (standing gates),
§XI.1–§XI.2.2 (what already exists — most of this work is *not* new building),
§VII.16.1 (the measurement acceptance bar).

**Nothing in this guide is implemented.** Every phase below is unstarted.

---

## 0. The one-paragraph summary

The question bank is browsed through **modules**, and there are exactly two kinds:
**exam modules** defined by a paper list (the seven that exist) and **subject
modules** defined by a taxonomy path with no papers (none exist yet, except one
accidental precedent). Subject modules are cross-exam for free, because they are a
live query over the whole bank. There is **no merge engine** — the owner withdrew
it (§XI.2.1) and it was never needed. `/bank` stays, loses its nav entry, and shows
nothing until you choose a shelf. One facet endpoint serves both. That is the whole
change.

---

## 1. Preconditions

| | |
| --- | --- |
| Next migration number | **0140** — `0139_personal_vault.sql` was added 23 Nov and is committed (`b1d9ef1c`) |
| Migration tool | `scripts/migrate.sh` — applied migrations are **checksummed**; editing an applied file is an error (`migrate.sh:14`) |
| Rehearsal | every migration on a **disposable clone of a fresh production dump**, never on production first (§V.0) |
| Tests | `api/tests/` (231 `test_*.py` files), isolated PostgreSQL, never production fixtures |
| Web deploy | build **locally**, `scripts/deploy.sh`; never build on Oracle. `deploy.sh` rsyncs with `--delete` (`deploy.sh:19,46,56`) — confirm the exclude list before running |
| Bank authority | the only writable bank is Oracle `/srv/study/workshop/mpsc-question-bankv2`. **Nothing in this guide touches bank content** — it changes configuration, queries and UI only |
| Receipt | `DEVLOG.md` entry per phase, with honest limitations, before stopping |

### 1.1 Two naming facts that will cause a collision if ignored

1. **"Vault" is taken.** `0139_personal_vault.sql` + `api/app/routers/vault.py`
   (635 lines, mounted at `main.py:121-122`) ship the **Personal Question Vault** —
   a learner-owned store of saved and custom questions. Earlier drafts of Part XI
   used "vault" for the public corpus; that was corrected. **Do not reintroduce the
   word for `/bank`.**
2. **"Module" should stay out of learner copy.** It is the internal word for a
   `collections` row. Learners see *an exam*, *a subject*, *a set*.

### 1.2 Decisions required from the owner before any code

Neither is a refactor; both change policy. Do not infer either.

| # | Decision | Why it cannot be assumed |
| --- | --- | --- |
| **D1** | **Browse allowance.** Restate the free tier as *"a published module and its own four filters are free; `/bank` and ad-hoc filter combinations meter"* — instead of today's rule, which charges a search for any **two** of {topic, year, answer} against a limit of **three per IST day** (`services/browse_allowance.py:10-31`) | Under the new design the default path pre-sets a subject, so the simplification would **paywall its own happy path**. This changes what paying buys (§0.9.2) |
| **D2** | **Which subject modules to publish, and in what order.** Candidates: English, Arithmetic, Reasoning, General Knowledge / General Studies, Mizo | Each is a public surface with a route and a progress key. Publishing ten at once makes the §2 measurement meaningless |

---

## 2. Phase order

```
P1  V.26   Behaviour from data            migration 0140   ← gates everything
P2  —      Measurement                    none             ← gates P3
P3  V.28a  Publish subject modules        migration 0141
P4  V.27   One resolver + facet endpoint  none
P5  V.28b  Surfaces: /bank, filters, test-from-view
P6  V.28c  Home: flip the onboarding sequence
```

P1 → P2 → P3 is a hard chain. P4–P6 are independent of each other and of P3, and
P6 is independent of all of it — it can ship first if something stalls.

**Withdrawn before starting: V.25, the `collection_id[]` array parameter.** Two
module shapes removed the need for a browsable union (§XI.2.1). Its only surviving
item — retiring `group-b`'s hardcoded fan-out — moved to P5.

---

## 3. P1 — V.26: per-module behaviour becomes data (migration 0140)

**Why first:** a subject module crosses exams on day one and therefore inherits
nothing from the exam-id tuples that currently carry per-module behaviour. Publish
"all English" before this lands and the same UDC question appears **once per
printed series**, while `/exams/udc` shows it once. That is a visible, day-one
regression, and it is the reason P1 gates P3.

### 3.1 The five hardcoded exam ids

Four were listed in §XI.1.3. Tracing the creation path for P3 found a **fifth**,
and it is the one that matters most here:

| # | Branch | File | Decides |
| --- | --- | --- | --- |
| 1 | `CLERICAL_EXAMS = ('udc','ldc','assistant')` | `services/learning_taxonomy.py:6` | science folds into the GK/GS path |
| 2 | `GROUP_B_COLLECTIONS = (…gazetted, …non-gazetted)` | `services/group_b_study.py:16` | a hand-coded two-module merge |
| 3 | `grouped = collection_id in ('udc','combined-prelims')` | `routers/questions.py:321` | repeated series printings collapse to one row |
| 4 | `collection_id=='combined-prelims' and section_path=='papers'` | `routers/questions.py:216-217` | silently drops the section filter |
| 5 | **`if collection_id == "subject-wise-practice": SET LOCAL join_collapse_limit=1`** | `routers/collections.py:350` | **the planner hint that makes a wide taxonomy collection fast** |

#5 is the precedent and the warning in one line. A taxonomy-wide collection
**already exists in production** and already needed a planner hint to be usable —
and that hint is keyed to a literal id, so **every new subject module gets the slow
plan**. The comment above it says as much: *"This measured wide taxonomy collection
benefits from declared joins. Small exam counts keep the default plan."*

### 3.2 Migration 0140

```sql
BEGIN;
-- Per-module behaviour stops being an exam-id tuple in application code.
ALTER TABLE collections
  ADD COLUMN IF NOT EXISTS series_grouping    BOOLEAN NOT NULL DEFAULT false,
  ADD COLUMN IF NOT EXISTS science_projection BOOLEAN NOT NULL DEFAULT false;

UPDATE collections SET series_grouping    = true WHERE id IN ('udc','combined-prelims');
UPDATE collections SET science_projection = true WHERE id IN ('udc','ldc','assistant','combined-prelims');
COMMIT;
```

Additive, defaults false, no rewrite of an applied migration. Backfill mirrors
today's behaviour exactly, so the migration alone changes nothing observable —
which is the property that makes it safe to rehearse and ship ahead of the code.

**Do not** add a column for the planner hint. Derive it (§3.3 item 4): a section
with no `paper_ids` is a wide taxonomy section, whatever its id.

### 3.3 Code changes

1. `routers/questions.py:321` — `grouped` reads `collections.series_grouping` for
   the resolved module instead of the id tuple. The resolved value for a **set of
   modules** is the **union** (`bool_or`) of its members' flags: if any member
   collapses series printings, the view does too. This is the honest default —
   under-collapsing shows duplicates, over-collapsing hides nothing.
2. `services/learning_taxonomy.py:6` — `CLERICAL_EXAMS` is deleted; callers read
   `science_projection`. Keep the constant name only if a test fixture needs it,
   and then as a test fixture.
3. `routers/questions.py:216-217` — the `combined-prelims`/`papers` special case
   becomes a section-level property or is deleted. **Check live behaviour before
   deleting**: it exists because that module's v2 split (`0060:17-22`) made
   `section_path='papers'` meaningless for it.
4. `routers/collections.py:350` — the `join_collapse_limit` hint applies when the
   resolved sections include **any section without `paper_ids`**, not when the id
   equals `subject-wise-practice`.

### 3.4 Tests

- `collections.series_grouping=true` on a fixture module collapses printings;
  `false` does not. Both asserted on counts, not on absence of error.
- A new taxonomy-only fixture collection receives the planner hint.
- **A guard test asserting no exam id string literal appears in a conditional in
  `routers/questions.py`, `services/learning_taxonomy.py` or
  `routers/collections.py`.** This is the phase's real deliverable: §0.10 rule 1
  ("exam identity is data, never schema or code branches") becomes enforced rather
  than remembered. Model it on `web/scripts/check-admin-nav.cjs`, which found a
  fourth dead link that the plan's own list had missed.

### 3.5 Done when

The guard test passes, every existing collection test passes unchanged, and
`/exams/udc` returns byte-identical counts before and after.

### 3.6 Rollback

The columns are additive with safe defaults; reverting the code restores the
tuples. No data loss path.

---

## 4. P2 — Measurement (no migration, no code)

**This is a gate, not a chore.** §XI.2.2 predicted that a taxonomy-only module is
the expensive one; §3.1 #5 shows it has already happened once.

### 4.1 What to run

On a **fresh production dump clone**, reusing the existing harness pattern
(`scripts/benchmark-collection-order.py` — read-only, clones into a temp database,
writes a timed report):

1. `EXPLAIN (ANALYZE, BUFFERS)` on
   `GET /api/questions?collection_id=subject-wise-practice` — paginated, cold and
   warm — and on the same query with the planner hint removed, to establish what
   the hint is worth.
2. A cold `GET /api/collections`. `_section_stats` resolves **every** live section
   of every public collection in one grouped query (`collections.py:18-21,77-87`),
   and each taxonomy-only section contributes a whole-bank scan.
3. The same two with **one** hypothetical extra subject module seeded on the clone.

### 4.2 Record

A dated directory under `reports/` with the clone's dump SHA, the queries, and
before/after timings — the format §VII.16.1 requires and these scripts already
produce.

### 4.3 Kill criteria

- If a cold `/api/collections` degrades materially per added subject module,
  **P3 publishes one module, not a set**, and P4 is promoted ahead of the rest.
- If the taxonomy branch needs its own index or a materialised membership, that is
  P4's work and it is far cheaper to know now than after ten modules are public.
- **Do not publish a second subject module on an unmeasured plan.**

---

## 5. P3 — V.28a: publish the subject modules (migration 0141)

### 5.1 The editor cannot do this — use a seed migration

Part XI §XI.2.1 said "publish through the existing editor." **That is wrong and is
corrected here.** `POST /api/module-composition/create` requires a `source_module`
and seeds the draft as `{papers:[], modules:[source], excluded_papers:[]}`
(`routers/module_composition.py:43-57`), and `Selection` has **no taxonomy field at
all** (`services/module_composition.py:13-17`). The editor composes **paper
libraries**; a subject module has no papers. Worse, its preview is a paper diff
(`added_papers` / `removed_papers`, `module_composition.py:147-152`), which reports
nothing meaningful about a whole-bank taxonomy predicate.

So: a seed migration, following `0011_exam_tracks.sql`'s precedent exactly. It is
reviewable as SQL, it is versioned, and the row count is small and fixed.

### 5.2 Row shape, per subject

```sql
INSERT INTO collections (id,title,kind,route,visibility,position,live_version,exam_scope_id)
VALUES ('subject-english','English','practice','/subjects/english','public',30,1,'mizoram-recruitment');

INSERT INTO collection_sections (collection_id,version,path,title,position,formats,query,pins,excludes)
VALUES ('subject-english',1,'all','All English questions',0,'{}',
        '{"subject_id":"english"}'::jsonb,'{}','{}');
```

Notes, each of which is load-bearing:

- `kind='practice'` — permitted by `0002_schema_v3.sql:417` and **never yet
  seeded**. A subject module is not an exam, and `kind='exam'` would put it in
  `bank_exam_catalog` (`0049:31`) and in the saved-exam picker, where it does not
  belong.
- **`subject_id` must be a real id from the approved registry** (`review_taxonomy`,
  `0030:19-23`, `level='subject'`, `active=true`). Verify each id against the live
  registry in the same session you write the migration — do not copy ids from this
  document or from §VII.18.4.
- **No `paper_ids` key.** Its presence switches the resolver to branch 1
  (`collections.py:29-44`) and the module stops being cross-exam. This is the
  single most likely mistake in this phase.
- `visibility='public'`. `'pro'` is a valid value and is **not** what D1 decided.
- `/subjects/:id` must exist as a route and render the same component as
  `/exams/:id` (§VII.18.8: one hero, one tab row, one filter card, one result line).

### 5.3 Checks before and after publishing each module

- `GET /api/questions?collection_id=subject-english` total equals
  `GET /api/questions?subject_id=english` total **in the same scope and pool**. If
  they differ, the section query is wrong, not the count.
- The same UDC question appears **once**, not once per series printing (this is
  what P1 bought).
- Counts are consistent with `GET /api/collections`' section stats for that module.
- An untagged question does not vanish from its own paper: subject modules add a
  lens, they never remove a question from `/bank` or from its paper
  (§0.11.4, §XI.11).

### 5.4 Honest limitation to record in the DEVLOG

A subject module is **exactly as good as the tagging**. 19.2% of approved
classifications carry a subject with no topic (§VIII.4.2, measured 23 Nov), so
subject-level browse is solid and topic-level narrowing inside a subject module is
thinner. Say so in the receipt; do not describe a subject module as complete
coverage of its subject.

---

## 6. P4 — V.27: one resolver, one facet endpoint

### 6.1 One resolver

The three-key membership contract — and it is only three keys, `paper_ids`,
`subject_id`, `topic_id` — is written **six times in five files**:

```
routers/collections.py:22-75            the section resolver
routers/questions.py:183-215            the browse CTE (same job, different SQL)
routers/questions.py:218-237            the section_path filter (again)
services/module_composition.py:135-140  the publish preview
services/review_scope.py:51-64          the review scope
services/atlas_context.py:55-56         the atlas binding
```

Extract one `services/selector.py` emitting the resolved-id CTE. Keep
`exam_scope.py`'s discipline unchanged: internal literals only, client text never
interpolated (§VIII.3.1). **Do not add query keys in this phase** — the DDL comment
at `0002_schema_v3.sql:433` advertises `year_gte` and `times_asked_gte`, neither of
which exists, and two of its four keys are spelled differently from the implemented
ones. Fix the duplication first; add keys never, or later.

**Done when** the three-key SQL appears in one file and every caller cites it.

### 6.2 One facet endpoint

Today there are two facet sources and neither can narrow to a selection:
`/questions/taxonomy` keys on `pool + exam_scope + learning` only
(`questions.py:448-453`), and `/collections/{id}/study-topics` narrows to one
collection and one `section_path` (`collections.py:168-181`). So `Bank.tsx:74-88`
fires **one list request per year** to draw its year rail and
`Bank.tsx:83` suppresses the rail when the combination would consume allowance.
The file admits it: *"the bank has no year facet"*, *"No facet endpoint exists"*
(`Bank.tsx:27,74-75`).

- Generalise `study-topics` into `/api/questions/facets`, taking the same selector
  the list takes; keep the old route as an alias, because **mobile depends on it**
  (`src/app/questions.tsx:106-116`).
- Return counts for the **next** choice only — subjects until one is chosen, then
  topics — plus a year histogram and an `unclassified` count.
- **Never offer a value that returns zero** (§VII.18.4).
- Cache keys stay bounded: facet only the **structural** dimensions (`modules`,
  `papers`, `subject`, `section_path`). Free text and per-user status are not
  faceted. `public_catalog` already keys exactly this way.
- The year histogram is cheap: `canonical_questions.first_year` / `last_year` are
  maintained by `refresh_cq_counts()` (`0002:222+`).

**Done when** the year rail is one request and facet latency is measured on the
clone before and after. If the faceted call is slower than the six requests it
replaces, it does not ship (§VII.16.1).

---

## 7. P5 — V.28b: the surfaces

1. **`/bank` becomes chooser-first.** Zero questions on arrival; choose exam ·
   subject · paper · year first; keep **every** filter the API supports; remove its
   nav entry (§VII.18.4). It is reached from a module, a search, or `/index`.
2. **Modules show four filters, faceted**: subject, year, paper/section, and your
   status — default **`ever_wrong`**, not `wrong`. `me.py:358-378` gates mistakes
   on the *latest* attempt being wrong, so a question missed three times and
   guessed right once vanishes from revision; `ever_wrong` (`questions.py:267`) is
   the honest default and the column already exists.
3. **Retire the dead filters from the UI, not from the API**: `repeats_only` and
   `order='repeated'` are hardcoded off (`Bank.tsx:26,189` `REPEATS_READY=false`;
   `FilterRail`'s permanently-disabled checkbox) because `times_asked` is still 1
   on every row. Remove the controls; keep the parameters for when the dedupe job
   runs.
4. **"Test everything in this view"** passes the **selector** to the builder, not
   100 ids, and freezes the resolved snapshot at creation — mock snapshots are
   already immutable (`0031`) and `shared-tests` already exists as a `kind='tool'`
   collection (`0079:26`). Scoring eligibility is untouched: a timed run still
   scores only the verified pool, per question (§0.10 rule 4).
5. **Retire `group-b`'s hardcoded fan-out** (the one surviving item of the
   withdrawn V.25). Publish one combined Group B module — this *is* a paper-library
   merge, so here the existing editor is the right tool — then delete
   `GROUP_B_COLLECTIONS` (`services/group_b_study.py:16`) and the 422 branch at
   `questions.py:182`.
6. **Close the web/mobile filter divergence while here.** The API accepts 24
   parameters (`questions.py:66-93`); web sends 11 (`Bank.tsx:50`); mobile sends a
   *different* 10 including `section_path`, `subtopic_id` and `answer_status`
   (`src/lib/domain.ts:1-13`). After this phase the learner-facing set is four on
   both clients and the full set exists once, on `/bank`.

---

## 8. P6 — V.28c: Home's exam choice (independent, shippable first)

Both choices are already built with the right cardinalities — save many exams with
exactly one primary (`user_exam_bookmarks` + unique index `user_one_primary_exam`,
`0092:159`), and up to five focus subjects (`user_focus_subjects`,
`position BETWEEN 0 AND 4`, `0092:23-27`). **Keep one primary.** The work is
sequence, not structure:

1. Remove the gate. The optional 10-question check-in link is conditioned on
   `plan.exam?.is_primary` (`TodayCard.tsx:33`), so the best exam-suggestion signal
   in the product is only offered *after* the choice it should inform.
2. Widen the suggestion. `OnboardingSuggestions.tsx:9-17` already derives **focus
   subjects** from the check-in result and offers to save them. Have it suggest the
   **exam** the same way, in one confirmable line.
3. Give the `Primary exam` select something to choose on — papers, questions, saved
   target date. Bare titles cannot distinguish LDC from UDC from Assistant, which
   share most of a syllabus.
4. Pre-set scope stays visible and removable — *"Showing LDC · change"* — never
   silent (§0.11.4).

Also correct in `FINNAPLAN.md`: §VIII.3.2 and §V.7 list the `is_primary` saved-exam
flag as deferred to exam #2. **It shipped in migration 0092.** The deferral row is
stale (noted in §XI.12.1).

---

## 9. Not doing, and why

| | |
| --- | --- |
| A merge engine, `collection_id[]`, deterministic merge ids, "save this view" | Withdrawn by §XI.2.1. Two module shapes removed the need |
| A learner-facing merge builder | One exam body, seven modules, 25 accounts that have ever answered a question (§IX.2). The merges worth having are nameable |
| Making merges follow their sources live | A background job and a cache-invalidation model. Instead: list, in the editor, which published merges are behind their sources |
| New `collection_sections.query` keys | Six implementations in five files. §VIII.3.2 already deferred the exam key |
| A second browse code path | `/bank`, a module and a merge are one resolver, one card, one list (§XI.11) |
| Anything that hides a question | The lens is not a wall (§0.11). Modules add a view; they never remove a question from its paper |

---

## 10. Verification checklist

Run per phase, and record the output in the `DEVLOG.md` receipt.

```bash
# P1 — no exam ids left in browse conditionals
grep -rn "'udc'\|'ldc'\|'assistant'\|'combined-prelims'\|subject-wise-practice" \
  api/app/routers/questions.py api/app/routers/collections.py \
  api/app/services/learning_taxonomy.py

# P3 — a subject module agrees with the raw filter it stands for
curl -s '…/api/questions?collection_id=subject-english&limit=1' | jq .total
curl -s '…/api/questions?subject_id=english&limit=1'            | jq .total

# P4 — the three-key contract exists once
grep -rln "paper_ids" api/app | sort

# P5 — the dead filters are gone from the UI, kept in the API
grep -rn "REPEATS_READY\|repeats_only" web/src
grep -rn "repeats_only" api/app/routers/questions.py

# P5 — the hand-coded merge is gone
grep -rn "GROUP_B_COLLECTIONS" api/app
```

Plus, every phase: isolated-PostgreSQL tests green, local `npm run build` clean,
both `study.hawayu.in` and `family.hawayu.in` verified after any Caddy, systemd or
PostgreSQL change, and a dated `reports/` directory for anything measured.

---

## 11. Acceptance for the whole guide

- A **subject module** behaves identically to an exam module on series grouping,
  science projection and scoring eligibility — the same UDC question appears once
  in "all English", not once per printing.
- A taxonomy-defined module's browse and catalog latency is measured and recorded
  **before** a second one is published.
- The three-key membership SQL exists in one file, cited by every caller.
- Zero exam-id literals in browse conditionals, asserted by a test.
- `/bank` renders no question until something is chosen; every filter the API
  supports is reachable there and nowhere else.
- No learner on the default path consumes browse allowance by using a module's own
  four filters (requires **D1**).
- A learner reaches *"my twice-wrong English, across every exam it was ever asked
  in"* in three taps from Home, and turns it into a test in one more.
