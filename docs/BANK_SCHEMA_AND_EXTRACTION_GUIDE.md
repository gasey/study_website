# India Study Map — Bank schema v3 and extraction guide

Instructions for a coding model (or a developer) working in `mpsc-question-bankv2`.
Read this whole file before writing code. Work in the numbered phases, in order. Each phase ends with acceptance checks; do not start the next phase until they pass.

---

## 0. Where things stand (verified 17 Oct 2026)

| What | Where | State |
|---|---|---|
| Bank | `bank/mpsc_bank_v2.json` (58 MB) | 1,938 papers · 77,751 questions (69,778 MCQ, 7,973 descriptive) |
| Schema | `db/mpsc_schema_v2.sql` | One `questions` row per **printed appearance**, tied to one `paper_id` |
| Pages | every MCQ has `page` | No position on the page (no bounding box) |
| Answers | 11,459 MCQs have no answer | `answer_source` ∈ key / official / derived / inferred / none |
| Explanations | empty on 77,733 rows | |
| Dedupe | `qb/dedupe.py` | Trigram Jaccard + SequenceMatcher, writes `duplicate_refs`. Links only; nothing merged |
| UDC/LDC study set | `bank/udc_ldc_module/FINAL_*_CLEAN.json` | 1,616 questions **copied** out of the bank, with answers and explanations added. Group B: 700 more |
| PDFs | `pdfs/Old_Questions/…` (~2 GB, local only) | `pdf_path` resolves for 1,938/1,938 papers |
| Page renders | `images/page-renders/` | Partial |

### The three problems this guide fixes
1. **Copies.** The UDC/LDC set holds its own copies of questions, so a fix in one place does not reach the other, and its 1,616 answers + explanations never flow back into the bank.
2. **No canonical question.** The same question printed in 2016, 2019 and 2025 is three unrelated rows. "Asked 3×" cannot be computed and discussion threads would split three ways.
3. **No position on the page.** The viewer can open the right page but cannot highlight the question.

---

## 1. Schema changes (`db/mpsc_schema_v3.sql`)

Do **not** edit v2 in place. Write v3 as a migration that keeps every v2 column.

### 1.1 Split "question" from "appearance"

```sql
-- One row per distinct question. This is what threads, reports,
-- explanations, attempts and collections point at.
CREATE TABLE canonical_questions (
    id              TEXT PRIMARY KEY,             -- 'cq_' + 12-char base32, never reused
    type            TEXT NOT NULL CHECK (type IN ('mcq','descriptive')),
    question        TEXT NOT NULL,                -- best transcription across appearances
    options         JSONB NOT NULL DEFAULT '[]',  -- in the order of the "primary" appearance
    answer_text     TEXT,                         -- the correct OPTION TEXT, not an index
    answer_source   TEXT CHECK (answer_source IN ('official','key','derived','inferred','none')),
    answer_key_ref  TEXT,
    subject TEXT, topic TEXT, topic_label TEXT, difficulty TEXT,
    concept_id      TEXT REFERENCES concepts(id) ON DELETE SET NULL,
    status          TEXT NOT NULL DEFAULT 'live'
                      CHECK (status IN ('live','held','withdrawn','merged')),
    merged_into     TEXT REFERENCES canonical_questions(id),
    times_asked     INTEGER NOT NULL DEFAULT 1,   -- maintained by trigger / rebuild
    first_year      INTEGER,
    last_year       INTEGER,
    fingerprint     JSONB,                        -- see §3.2
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- The existing v2 `questions` table becomes the appearance table.
ALTER TABLE questions RENAME TO appearances;
ALTER TABLE appearances
    ADD COLUMN canonical_id  TEXT REFERENCES canonical_questions(id),
    ADD COLUMN option_order  INTEGER[],           -- maps this printing's A–D to canonical order
    ADD COLUMN bbox          JSONB,               -- {"x0","y0","x1","y1"} in PDF points, page-relative
    ADD COLUMN bbox_source   TEXT CHECK (bbox_source IN ('text','ocr','manual')),
    ADD COLUMN series        TEXT;                -- booklet series A/B/C/D where printed
```

Rules:
- **Answers are stored as option text on the canonical row**, never as an index. Each appearance's index is derived through `option_order`. This is what makes reordered repeats safe.
- `times_asked` = count of distinct `(sitting_id)` among appearances, **not** count of rows. Series A/B/C/D of one sitting count once.
- A merged canonical row is never deleted: `status='merged'`, `merged_into` set. All foreign keys must follow `merged_into`.

### 1.2 Concepts (same fact, different question)

```sql
CREATE TABLE concepts (
    id     TEXT PRIMARY KEY,
    label  TEXT NOT NULL,            -- e.g. "Joint sitting of Parliament (Art. 108)"
    subject TEXT, topic TEXT
);
```
Concept links are made only by a reviewer (see §4). They never change answers or counts.

### 1.3 Duplicate review queue

```sql
CREATE TABLE dupe_candidates (
    id           BIGSERIAL PRIMARY KEY,
    a_id         TEXT NOT NULL REFERENCES canonical_questions(id),
    b_id         TEXT NOT NULL REFERENCES canonical_questions(id),
    tier         TEXT NOT NULL CHECK (tier IN ('exact','reordered','near','concept')),
    similarity   NUMERIC NOT NULL,
    checks       JSONB NOT NULL,     -- results of every guard in §3.3
    blocked      BOOLEAN NOT NULL,   -- true if any guard failed
    decision     TEXT CHECK (decision IN ('merge','concept','different')),
    decided_by   TEXT, decided_at TIMESTAMPTZ,
    UNIQUE (a_id, b_id)
);
```

### 1.4 Pages

```sql
CREATE TABLE page_images (
    paper_id  TEXT REFERENCES papers(id) ON DELETE CASCADE,
    page      INTEGER,
    url       TEXT NOT NULL,        -- object-storage key, e.g. pages/{paper_id}/{page}.webp
    width_px  INTEGER, height_px INTEGER,
    pdf_w_pt  NUMERIC, pdf_h_pt NUMERIC,   -- needed to scale bbox to pixels
    PRIMARY KEY (paper_id, page)
);
```

### 1.5 Community tables (point at canonical ids only)

```sql
CREATE TABLE posts (                         -- discussion on a question
    id BIGSERIAL PRIMARY KEY,
    canonical_id TEXT NOT NULL REFERENCES canonical_questions(id),
    kind TEXT NOT NULL CHECK (kind IN ('explanation','doubt','reply')),
    parent_id BIGINT REFERENCES posts(id),
    author_id TEXT NOT NULL, body TEXT NOT NULL,
    pinned BOOLEAN NOT NULL DEFAULT false, accepted BOOLEAN NOT NULL DEFAULT false,
    before_fix BOOLEAN NOT NULL DEFAULT false,   -- set when the key changes after posting
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE content_reports (               -- errors in the question itself
    id BIGSERIAL PRIMARY KEY,
    canonical_id TEXT NOT NULL REFERENCES canonical_questions(id),
    kind TEXT NOT NULL CHECK (kind IN ('wrong_key','typo_ocr','outdated','ambiguous','duplicate')),
    reporter_id TEXT NOT NULL, note TEXT,
    evidence_page INTEGER, evidence_paper TEXT,
    status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open','confirmed','fixed','rejected')),
    UNIQUE (canonical_id, kind, reporter_id)     -- "I see this too" = one row per person
);
CREATE TABLE abuse_reports (                 -- conduct only, kept separate on purpose
    id BIGSERIAL PRIMARY KEY, post_id BIGINT REFERENCES posts(id),
    reason TEXT NOT NULL CHECK (reason IN ('spam','harassment','answer_leak','copyright','other')),
    reporter_id TEXT NOT NULL, UNIQUE (post_id, reporter_id)
);
```

### 1.6 Collections (what the app currently calls "modules")

A collection holds **no questions of its own**. It is a tree of sections, each a saved query plus pins and exclusions.

```sql
CREATE TABLE collections (
    id TEXT PRIMARY KEY, title TEXT NOT NULL, kind TEXT CHECK (kind IN ('exam','tool','practice')),
    live_version INTEGER, draft_version INTEGER
);
CREATE TABLE collection_sections (
    collection_id TEXT REFERENCES collections(id) ON DELETE CASCADE,
    version INTEGER NOT NULL, path TEXT NOT NULL,      -- 'gk/polity'
    title TEXT NOT NULL, position INTEGER NOT NULL,
    query JSONB NOT NULL,                               -- {"subject":"gk","topic":"polity","year_gte":2016}
    pins TEXT[] NOT NULL DEFAULT '{}',                  -- canonical ids forced in, in order
    excludes TEXT[] NOT NULL DEFAULT '{}',
    PRIMARY KEY (collection_id, version, path)
);
```

### 1.7 Study materials (user-created)
```sql
CREATE TABLE materials (id TEXT PRIMARY KEY, author_id TEXT NOT NULL, title TEXT NOT NULL,
  tags TEXT[], blocks JSONB NOT NULL, published_at TIMESTAMPTZ,
  helpful INTEGER NOT NULL DEFAULT 0, studied INTEGER NOT NULL DEFAULT 0);
CREATE TABLE material_votes (material_id TEXT, user_id TEXT, studied BOOLEAN NOT NULL,
  PRIMARY KEY (material_id, user_id));
```
`blocks` is an ordered array of `{type, ...}` with type ∈ h, p, callout, mcq, cards, chart, timeline, mind, diagram, map, formula, mock. A `mock` block stores canonical ids, not copies.

### Phase 1 acceptance
- [ ] v3 migration runs on an empty DB and on a v2 dump without data loss (row count of `appearances` = 77,751).
- [ ] Every v2 CHECK still holds (`answer_in_range`, `compensated_has_no_answer`).
- [ ] No table outside `appearances` references `appearances.id` except `page_images` lookups and bbox.

---

## 2. Backfill canonical rows (no merging yet)

1. Create exactly **one canonical row per appearance**. `times_asked = 1`. Set `appearances.canonical_id`.
2. Copy `answer_index` → `answer_text = options[answer_index]` when not NULL.
3. Compute `fingerprint` (§3.2) for every canonical row.

### Phase 2 acceptance
- [ ] 77,751 canonical rows, 77,751 appearances, all linked.
- [ ] For every MCQ with an answer: `options[answer_index] == answer_text`.

---

## 3. Find repeats

### 3.1 Normalisation (`match_text` already exists in `qb/model.py`; extend it)
- NFC, casefold, collapse whitespace (existing).
- Strip leading numbering `^\(?\d+[\).]` and option letters `^\(?[a-d][\).]`.
- Normalise quotes, dashes, `°`, `−` (U+2212) → `-`.
- **Do not** strip `not`, `except`, `incorrect`, `false`, or any digit.

### 3.2 Fingerprint (store on the canonical row)
```json
{
  "stem": "<normalised stem>",
  "option_set": ["<normalised option>", "... sorted"],
  "answer": "<normalised answer text or null>",
  "negation": true,            // stem contains not|except|incorrect|false|wrong
  "numbers": ["15", "2003"],   // every number in stem + options, sorted
  "minhash": "<64 hashes>"     // for candidate generation at 77k scale
}
```

### 3.3 Tiers and guards

| Tier | Rule | Action |
|---|---|---|
| **exact** | stem equal AND option_set equal AND answer equal (or both null) | auto-merge |
| **reordered** | stem similarity ≥ 0.92 AND option_set equal AND answer equal | auto-merge, record `option_order` |
| **near** | stem similarity 0.80–0.95, option_set overlap ≥ 3 of 4 | review queue |
| **concept** | embedding cosine ≥ 0.85, different option sets | review queue, never merge |

Guards — if **any** fails, set `blocked = true`; a blocked pair can only be resolved as `concept` or `different`:
1. `answer` texts differ (when both known).
2. `negation` differs.
3. `numbers` differ.
4. Both appearances are from the **same sitting** (that is a series variant, handled in §3.5, not a repeat).

Similarity = `SequenceMatcher` ratio on normalised stems, as in `qb/dedupe.py`. Reuse its prefix-filter for candidates; replace the all-pairs fallback with MinHash LSH (`datasketch`, 128 perms, threshold 0.6) if it is too slow at 77k.

### 3.4 Merge procedure (one transaction)
1. Keep the canonical row whose primary appearance has the best `answer_source` (official > key > derived > inferred > none), then the most recent year.
2. Point every appearance of the loser at the winner; compute `option_order` for each.
3. Re-point posts, content_reports, attempts, collection pins/excludes, material mock blocks.
4. Loser: `status='merged'`, `merged_into=winner`.
5. Recompute `times_asked`, `first_year`, `last_year`.
6. If the winner's answer changed: mark existing posts `before_fix = true` and enqueue re-scoring of attempts.

### 3.5 Booklet series
Series A/B/C/D of one sitting are the same paper reshuffled. Merge their appearances into one canonical row per question, but they count **once** toward `times_asked`.

### Phase 3 acceptance
- [ ] Unit tests with these fixed pairs pass:
  - same stem, same options, same order → exact merge
  - same stem, options A↔D swapped, same answer text → reordered merge, `option_order` correct
  - "Which is a Fundamental Duty…" vs "Which is NOT a Fundamental Duty…" → blocked (negation)
  - "…15% of the Lok Sabha" vs "…10% of the Lok Sabha" → blocked (numbers)
  - Q6 LDC 2025 "40° C or F" vs printed "−40°" → near, blocked (numbers), goes to review
- [ ] After auto-merge: no canonical row has two appearances from the same sitting unless they are different series.
- [ ] Report: counts per tier, merges done, candidates queued, `times_asked` histogram. Write to `bank/REPEATS_REPORT.md`.

---

## 4. Fold the UDC/LDC copies back into the bank

For each row in `bank/udc_ldc_module/FINAL_*_CLEAN.json` and `group_b/*`:
1. **Match** to an appearance, stopping at the first hit:
   a. `paperId` + question number parsed from `id` suffix (`…-may-2025-006` → paper, Q6).
   b. `stem_hash` equal to an appearance's `stem_hash`.
   c. fingerprint exact/reordered (§3.3) against canonical rows.
   d. otherwise → `bank/udc_ldc_unmatched.json` for a human. **Do not create new canonical rows automatically.**
2. **Carry back** onto the canonical row:
   - `explanation` → a `posts` row, `kind='explanation'`, `author_id='team'`, `pinned=true`. Never overwrite an existing pinned explanation.
   - `answerIndex` → only if the bank has no answer. Convert to text via the module row's own `options`. Set `answer_source='derived'` (these were solved, not published). Never overwrite `official` or `key`.
   - If both have an answer and they disagree: do not change either. Write the pair to `bank/udc_ldc_conflicts.json`.
   - `topic`, `topicLabel`, `difficulty` → only where the bank's are NULL.
3. Build the UDC/LDC **collection** from the matched canonical ids, one section per subject/topic as in `MODULE_SUMMARY.json`. Use `pins` to keep the original order.
4. After this phase the `FINAL_*_CLEAN.json` files are read-only archives.

### Phase 4 acceptance
- [ ] matched + unmatched = 1,616 (+700 Group B).
- [ ] Zero `official`/`key` answers changed (diff before/after).
- [ ] Conflicts file exists even if empty.

---

## 5. Question positions on the page (for the original-paper viewer)

For each appearance with `page`:
1. Open `pdf_path` with **pdfplumber**. Get words with coordinates for that page.
2. Find the line starting with the printed question number (`^\s*{qnum}[\.\)]`). The box runs from that line's top to the top of the next question number's line (or page bottom), full text-column width.
3. Verify: the box text must contain ≥ 70 % of the stem's normalised trigrams. If not, `bbox = NULL`.
4. Scanned PDFs (no text layer): run **Tesseract** (`--psm 4`) on the page render to get word boxes, same steps, `bbox_source='ocr'`.
5. Two-column papers: detect by a gap in word x-positions > 15 % of page width; search each column separately.

Render pages once: `pdftoppm -r 110 -png` → convert to WebP q=70 → upload to `pages/{paper_id}/{page}.webp`. Fill `page_images`.

Storage: Cloudflare R2 (free tier covers ~2 GB, no egress charge) or DigitalOcean Spaces. Never commit PDFs or page images to git.

### Phase 5 acceptance
- [ ] bbox found for ≥ 90 % of text-layer MCQs; report the rest by paper.
- [ ] Spot-check 30 random appearances by drawing the box on the render and saving to `data/logs/bbox_check/` for a human to look at.

---

## 6. What a model can and cannot do here

**Safe to automate** (deterministic, checkable): the migration, backfill, fingerprints, exact and reordered merges, the guard checks, UDC/LDC matching steps a–c, bbox extraction, page rendering, all reports.

**Must go to a person** (the admin review queues already designed in the Admin Console):
- every `near` and `concept` pair
- every unmatched UDC/LDC row and every answer conflict
- every `content_report` before a key changes
- answers for the 11,459 unanswered MCQs. A model may *suggest* an answer with a cited source into the review queue, stored as `answer_source='inferred'`; it may never write `official` or `key`.

If you are the model doing this work: do not invent answers, do not merge on judgement, do not delete rows. When unsure, write to a review file and move on.

---

## 7. Naming: "module"

Today "module" covers two different things: exam sets (UDC/LDC, Combined Prelims, JSO) and tools (Study Map, Timeline, Flashcards). Learners also don't search for "module"; they search for their exam.

Recommendation:
- **User-facing:** call the exam ones **Exams** ("UDC / LDC exam", "Combined Prelims exam"). Put Study Map, Timeline, Mind Maps, Quick Revision under **Tools**.
- **Admin and code:** `collection` (as in §1.6), with `kind` = exam / tool / practice. The Admin "Module builder" becomes "Collection builder".
- Avoid "course": it implies a teacher and videos, which this is not.
