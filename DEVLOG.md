# Devlog

Append-only. Newest entry at the bottom. One entry per working session:
what changed, what was measured, what broke, what is next. Write down the
things that cost time — the trap you hit is worth more to the next session
than the feature you shipped.

---

## 2026-10-18 — infrastructure and project setup

**Server.** Oracle Cloud Always Free, Ampere A1, 4 OCPU / 24 GB, Mumbai
(`ap-mumbai-1`, single AD). Reserved IP `152.67.31.231`. The instance took
11 retries over ~45 minutes to land — `Out of host capacity` is the normal
state in Mumbai, and a retry loop is the answer. `~/oci/retry-launch.sh` on
the dev machine still works if the box ever needs rebuilding.

Installed: PostgreSQL 16.15 (tuned: `shared_buffers 6GB`,
`effective_cache_size 18GB`, `random_page_cost 1.1`, localhost only),
Redis 7.0.15, Caddy 2.11.7, Python 3.12.3, fail2ban, unattended-upgrades.

*Trap:* Oracle's Ubuntu images block 80/443 in iptables even when the VCN
security list allows them. Had to insert ACCEPT rules above the catch-all
REJECT and persist them. Cloud-side rules alone do nothing.

*Trap:* adding `log { output file /var/log/caddy/… }` to the Caddyfile makes
Caddy fail to reload with "permission denied" — the packaged unit sets
`ProtectSystem=full`, so `/var` is read-only no matter who owns the
directory. Logs go to journald.

**HTTPS.** https://study.hawayu.in live with a Let's Encrypt certificate,
HTTP 308s to HTTPS. Apex and `www` still point at Vercel and were left alone.

*Trap:* the DNS record appeared to be "propagating" for an hour. It had never
been saved — the zone serial at the authoritative nameserver was still three
days old. Querying the authoritative server directly settles this in seconds;
a cached resolver cannot tell you the difference between slow and absent.

**Schema v3 reviewed, fixed and tested.** Two different copies existed — a
472-line one and a 624-line one inside the design zip. The zip is
authoritative. Nine defects found, all tagged `[R-n]` in
`../mpsc-question-bankv2/db/mpsc_schema_v3.sql`. The two that mattered:

- `v_scorable` admitted all 40,675 model-inferred answers into mocks and
  duels, contradicting the project's own extraction guide.
- Section 14 quoted every function body with a bare `$` instead of `$$`, so
  the entire moderation block failed with a syntax error and none of its
  seven tables were created. Verified by running it.

**Measured on the real bank** (77,751 questions, not synthetic):

| | |
|---|---|
| COPY whole bank in | 3.8 s |
| v3 migration incl. backfill | 29 s |
| DB size after migration | 282 MB |
| point lookup / 20 scorable / FTS | 0.81 / 0.11 / 0.07–0.51 ms |
| 50 concurrent quiz clients | **5,379 tps**, 9.3 ms latency |
| bulk insert 50,000 attempts | 1.1 s |

Conclusion: performance is not a constraint for this workload. The earlier
worry about free-tier disk I/O throttling writes was wrong. The only slow
things are `ORDER BY random()` (19.8 ms, avoidable) and trigram similarity
(244 ms, batch-only).

**Project set up.** `india-study-map-app` with `web/` and `api/`. Milestone 1
is a vertical slice: Bank → Question detail, deployed.

*Next:* FastAPI service against the `bench` database.

---

## 2026-10-18 (later) — scaffold + API

**Repo split settled.** `mpsc-question-bankv2` stays as the data workshop
(2 GB of PDFs, raw JSON, OCR, parsers). The app owns what the app runs on:
`api/migrations/` now holds the schema, `docs/design/` holds the handoff, and
bankv2 keeps a `db/README.md` pointer. One copy of v3 only — two copies
already existed once and the review nearly landed on the stale one.

**web/** Vite + React 18 + TS + Tailwind. Pinned to React 18 / Vite 5: npm
10.8.2's peer resolver crashes on the React 19 / Vite 8 tree
(`Cannot read properties of null (reading 'edgesOut')`), and 18/5 is what
india-study-map already runs, so ported components work unchanged. Tokens
verified in the browser by computed CSS, not by eye — `#F4EFE4`, `#1D1B18`,
all six area colours, three fonts loading.

*Note:* screenshots time out in this browser pane. Verify with the
accessibility tree and `getComputedStyle` instead; it is more precise anyway.

**api/** FastAPI + psycopg3 async pool, deployed as `ism-api.service` running
as www-data, behind Caddy at `/api/*`. `PGPASSWORD` comes from
`EnvironmentFile=/etc/mpsc/db.env`, and `DATABASE_URL` omits the password, so
the secret is in neither the unit file nor `ps` output.

Production database `mpsc` loaded and migrated: 77,751 canonical / 12,454
scorable / 59,047 practice. Migration took 19 s.

**The answer gate is enforced server-side.** No GET response carries
`answer_text` — verified by grepping 50 list items and a detail response, 0
occurrences. The key is revealed only by `POST /api/questions/{id}/answer`,
which grades by comparing option *text*, not index. Shipping the answer with
the question would have made the gate decorative.

Live: `https://study.hawayu.in/api/health` → 77,751 questions.

*Next:* Bank screen against this API.

---

## 2026-10-18 (cont.) — milestone 1 shipped, and bank sync

**Bank screen and Question detail are live** at https://study.hawayu.in.
Real data: 12,454 scorable / 59,047 practice, provenance tag on every card,
pool toggle, debounced full-text search, pagination. Detail has the
answer-before-reveal gate and the appearances list.

`scripts/deploy.sh [web|api|all]` builds locally and rsyncs artifacts; the
API half waits for `/api/health` and dumps journal output if it does not come
back. Caddy serves the SPA with `try_files {path} /index.html`, so deep links
like `/bank/<id>` return 200.

**Unresolved — colour verification.** The option buttons carry the right
classes (`border-correct bg-correct-soft` after a reveal) and the generated
CSS rules are correct, but `getComputedStyle` in this browser pane reports
the *pre-change* colours. A freshly created probe element — `div` and
`button` alike — with the identical classes computes correctly, and removing
`transition-colors` changes nothing. Behaviour is verified (aria-pressed, the
`×`/`✓` markers, the POST, disabled state); colours need a human to look at
the page in a real browser. Screenshots time out in this pane too, which
points at the pane rather than the CSS.

**scripts/sync-bank.sh** — local bank JSON is the source of truth, the server
DB is derived (DECISIONS.md #5). One transaction, `--dry-run` first.

*Trap:* the v3 migration leaves `appearances.canonical_id` NOT NULL with an
FK. `INSERT ... ON CONFLICT DO UPDATE` does **not** rescue a NOT NULL
violation — the proposed row is validated before the conflict is detected —
so the canonical row has to be created before its appearance, not after. The
first run failed on exactly this and rolled back whole, which is the argument
for the single transaction.

Verified round-trip: edited a question in a *copy* of the bank → synced →
marker visible via the live API → re-synced from the real file → gone.
Seeded attempts stayed at 3 through every cycle, and the real bank file was
never written to.

*Next:* milestone 2 — auth, and recording attempts for real.

---

## 2026-10-18 (cont.) — milestone 2: attempts without accounts

Progress now records, with no login. Client generates a UUID into
`localStorage` and sends `X-Device-Id`; the API creates a `users` row per
device so `attempts.user_id` is a real FK from day one. Answering records the
attempt with `chosen_text` — the text, not the index, so a later key
correction can re-score it. `GET /api/me/progress` returns answered/correct/
distinct counts and the header shows them.

Rejects a missing or malformed header with 400 rather than inventing a guest
identity, so a client bug is loud instead of silently splitting progress
across phantom users.

Verified against the live API: 400 on no header, 400 on a non-UUID, attempts
recorded, progress correct, and a second device sees zeroes — devices are
isolated.

*Caught a near-miss:* the second test answer returned `correct: true` when a
wrong one was expected. It was not a grading bug — index 3 genuinely is that
question's key. Re-tested with indices 0 and 1, both `false`. Worth noting
because "the test looked wrong" nearly became "the code is wrong".

`/api/me/progress` sits in its own router rather than under `/api/questions`,
where it was first written — two segments do not collide with
`/{question_id}`, but it was the wrong shape for a user resource.

*Next:* practice mode drawing from `v_practice` with unverified answers
labelled, then mocks.

---

## 2026-10-18 (cont.) — the design was not actually being followed

The deployed Bank screen looked bland and the user called it out. They were
right, and the framing in the earlier entry ("design tokens ported") was
generous to the point of misleading. What had been ported were colours and
fonts; the *layouts* were invented. The prototype is 3,500 lines of specific
composition and copy, and almost none of it had been read.

**Root cause: built from the handoff README instead of the prototype.** The
README's token summary disagrees with the actual markup in several places:

| | README | markup |
|---|---|---|
| card radius | 10px | 14px |
| option radius | 8px | 6px |
| correct state | `#2E7D46`/`#DCEFE1` | `#3D7344`/`#E3ECDD` |
| wrong state | `#C0392B`/`#F8DEDA` | `#B0412A`/`#F5E1D8` |
| option resting bg | `#FFFFFF` | `#FBF8F1` |
| state indicator | `✓ × !` | words: "Correct"/"Answer"/"Your pick" |

Everything extracted is now in `docs/DESIGN-FIDELITY.md`, and `CLAUDE.md`
says to read it before building a screen. **The markup is authoritative; the
README is a summary.**

Also missed entirely: the prototype answers questions **inline on the bank
list** ("Tap an option to check it"), with the explanation revealed under the
card. The detail page is for the original-paper view, not for answering.

Bank card now matches, verified against the live site: radius 14px, padding
20px 22px, option radius 6px on `#FBF8F1`/`#DCD3C2`, stem Newsreader 21px at
line-height 28.35px (= 21 × 1.35), outlined provenance pill, solid dark
repeat badge, "View original ↗" in `#33609E`.

**Resolves the earlier unexplained CSS reading.** Computed styles in this
browser pane are correct for classes present at *first render*, and stale for
classes React swaps in after a *state change* — which is exactly why the
post-reveal option colours read as unchanged while a freshly created probe
with the same classes read correctly. Not a CSS bug and not a React bug: do
not trust `getComputedStyle` here for post-interaction styling, verify the
className instead and have a human look at the page.

Still not ported: the filter rail, topic chips (our `subject` is NULL until
classification), discussion counts (milestone 4), and the other 24 screens.

*Next:* the filter rail, then the remaining screens one at a time, each
extracted from the prototype first.

---

## 2026-10-18 (cont.) — filter rail

Ported from the prototype (line 390): white card, 14px radius, 16px padding,
`flex 1 1 220px` capped at 260px, groups headed by a mono 11px label with a
1px ink underline, 14px checkbox squares at 3px radius filling solid ink.
Layout is the prototype's `gap:40px` with the list at `flex 999 1 520px`.

API gained `source` (repeatable) and `repeats_only`. `source` is whitelisted
against the enum before it reaches the query — a CHECK constraint is not a
sanitiser. A bogus value returns 422.

Verified live: switching to the practice pool and ticking "Unverified" took
the count 12,454 → 39,961, exactly the `inferred` total, and every card on
screen read "Unverified".

**Two filters are deliberately inert, and say so on screen:**

- *Topic* — `subject`/`topic` are NULL on every row until classification runs.
- *Repeats* — measured `max(times_asked) = 1` across all 77,751 rows, and
  zero canonicals have more than one appearance. Repeats only exist once the
  dedupe job merges duplicate printings, and it has not run. The filter was
  built, found to match nothing, and replaced with an explanation rather than
  left as a control that silently returns an empty list.

*Pane note, again:* `computer` clicks intermittently fail to reach React
here — a pool toggle and a checkbox both no-opped. `dispatchEvent(new
MouseEvent('click', {bubbles:true}))` works, one interaction per tool call so
React re-renders between them. Two clicks in a single call also fails: the
second lands before the re-render.

---

## 2026-10-18 (cont.) — surveyed the prototype, rewrote the plan

Mapped every screen instead of guessing. Screens are gated by
`<sc-if value="{{ is.<name> }}">` at column 0 — that is the switch, not the
`showX` flags, which are sub-sections. Markup ends at line 2283 where the
script block starts; measuring the last screen to EOF overstates it badly
(`contribute` looked like 1,420 lines, is 203).

**28 screens, 2,206 lines of markup**, plus the 147 KB Admin Console.
Largest: partner 274, contribute 203, feed 194, bank 162, profile 114,
material 101. Smallest: account 16, onboard 23, search 23.

Size is a poor proxy for effort — `exam` is 45 lines but needs a
server-authoritative timer and thread locking, while `partner` is 274 lines
of mostly static layout. The plan is ordered by dependency, not by size.

`docs/PLAN.md` rewritten as the authoritative feature-by-feature plan: phase
0 data prerequisites, then foundations, exams/mocks, accounts, community,
games, moderation, money, admin, mobile. Every screen carries its prototype
line reference so the next session can jump straight to the markup.

**Phase 0 is the real critical path and it is not engineering.** Subject
classification, dedupe, page images and the 11,459 missing keys each block a
feature the design treats as central, and none of them is unblocked by more
frontend. Three controls already ship as explanations because of this.

---

## 2026-10-18 (cont.) — migrations, and Phase 0 deferred

**Redis is installed and entirely unused** — 0 keys, the only client was a
`redis-cli` probe, ~1 MB resident. It is there for Phase 5 (game rooms,
presence, leaderboards shared across uvicorn workers). FastAPI does not
touch it and does not need to; Postgres covers everything at this scale.

**Phase 0 deferred by decision.** Classification, dedupe, page images and
the missing keys are no longer treated as the critical path. Build against
the 12,454 official-key questions and improve the bank later. Where a
control cannot be honest on today's data it ships as an explanation, which
two filters already do.

**Numbered migrations, because the schema will keep moving.**
`api/migrations/NNNN_name.sql` + `scripts/migrate.sh`. The old
`mpsc_schema_v2/v3.sql` became `0001`/`0002` and were baselined into a
`schema_migrations` ledger without re-running.

Two things worth knowing about the runner:

*`createdb -T` cannot be used for dry runs.* It needs exclusive access to
the template, and the API's pool holds connections — the first attempt died
with "source database is being accessed by other users". Taking the API down
to rehearse a migration is the wrong trade, so `--dry-run` restores a
`pg_dump` into a throwaway clone instead. ~15 s on the current 282 MB, site
stays up, and real data is included so backfills rehearse honestly.

*Applied migrations are checksummed and may not be edited.* Verified by
tampering with an applied file: the runner refuses and says to write a new
one. An edited migration means the repo and the server disagree about what
the schema is, silently.

First real migration, `0003_attempt_stats`: index on `attempts(canonical_id)`
plus `v_question_stats` and `v_option_picks`. These back the option-vote
bars the prototype shows (`opts()` takes a `votes` argument, line 2603) and
give a real difficulty signal, which the imported `difficulty` column never
did — it was a default `'medium'` on 96% of rows. Views rather than counter
columns: aggregates are milliseconds here, and a counter is one more thing
to keep honest when attempts are re-scored after a key fix.

---

## 2026-10-18 (cont.) — component library and the real app shell

`web/src/components/ui.tsx` holds the primitives every screen composes:
PillButton, OutlinePill, Chip, CountBadge, Checkbox, GroupTitle, Card,
NotYet, Avatar. FilterRail was refactored onto them, which is the point —
re-deriving padding and radii per screen is exactly how a design drifts.

**Header rebuilt from markup line 34, and it caught an invention.** The
earlier header put the six coloured area dots next to the wordmark. They are
not in the header at all — they belong to the landing hero and the footer
mark. There is now a comment in `Header.tsx` saying so, because it is the
kind of thing that gets "restored" by someone tidying up.

The real header: wordmark in Newsreader 22px, a `Sections ▾` pill that opens
a full-width mega-menu, quick nav underlined on the active route
(`underline-offset 6px`, `thickness 2px`), pill search on `#F7F3EA`, inbox
with a count badge, ink `Post` button, avatar with a level badge tucked
`-14px` into it.

Verified live: 0 dots in the header, menu grid resolves to 4×268px from
`auto-fit minmax(240px,1fr)`, shadow is exactly
`rgba(29,27,24,0.12) 0 18px 40px`, footer is `#14130F` on `#CFC7B8`.

Dismiss-on-outside-click and Escape were added to the menu — a full-width
overlay that only closes via its own button is a trap.

**Planned routes now name their phase.** The shell links to 13 screens that
do not exist. Rather than a bare 404, each renders a card saying which phase
owns it and pointing at `docs/PLAN.md`. Honest about what is designed versus
built, and it makes the shell navigable for review.

---

## 2026-10-18 (cont.) — a second corpus exists on the old server

`ssh shiksha-dev` (134.209.154.122, DigitalOcean blr1) runs `mpsc-api.service`
against a Postgres database `mpsc_study` holding **140,552 questions across
3,764 papers** — plus 168 `question_corrections`, 296 comments and a
208-row audit log that exist nowhere else.

Compared both corpora by normalised question text:

| | rows | distinct |
|---|---|---|
| old server | 140,552 | 90,619 |
| our bank | 77,751 | 71,987 |

overlap 64,129 · **only on old 26,490** · only in ours 7,858.

**Neither is a superset**, and the "140k" figure is a raw row count — the old
database carries roughly 50,000 internal duplicate texts, which is precisely
what the dedupe job is meant to collapse.

**Do not treat its answers as keys.** `mpsc_study.questions` has no
`answer_source`. 64,706 rows carry an `answer_index` with no record of where
it came from; `source` is only a label and `verified_by`/`key_disputed` are
empty on every row. Importing those as `official` would silently destroy the
one guarantee the product rests on — that `v_scorable` contains only
genuinely keyed questions. Anything harvested comes in as `inferred` at best.

It does not fix classification either: 138,355 of 140,552 rows are
`subject = 'gk'` — the same placeholder, at 98%.

Worth having: the ~26,490 unseen questions and **70,839 explanations** (our
bank has explanations on about 18 rows).

**Also corrected a misconception I had been carrying all session:** MPSC here
is the **Mizoram** Public Service Commission, not Maharashtra. Every exam
name reads "Government of Mizoram" and the design's footer is "Aizawl". It
changed nothing about the Mumbai region choice, but it had been stated wrong.

No merge attempted. Harvesting is a data decision with real downside, and
anything taken goes into the local bank JSON first, never into the server
database directly.

---

## 2026-10-18 (cont.) — harvest tooling, and the sync topology

Settled how the three stores relate (DECISIONS #7). Not a triangle:

```
shiksha-dev  ──import──▶  local bank JSON  ──sync-bank.sh──▶  Oracle VM
 (archive)                 (source of truth)                  (derived)
```

shiksha-dev can be demoted to an archive because it has no users: its nginx
log is 113 distinct IPs of vulnerability scanners, and its newest data is
~11 days old and was written by us.

**Chased down an apparent compromise and cleared it.** Webshell probes
(`wp_filemanager.php`, `opsh.php`, `BDKR28WP.php`) were returning **200**
rather than 404, which reads alarming. It is the SPA catch-all serving
index.html for unknown paths: the box has no PHP binary, no PHP packages, no
PHP services and no `.php` files on disk. Checked rather than assumed in
either direction — a 200 on a webshell path deserves five minutes.

`scripts/harvest_old_server.py` is report-only by default. Measured:
**8,655 explanations** to fill on questions we already hold, and **26,006
unseen questions** (77,751 → 103,757). It backs the bank up before writing,
and enforces DECISIONS #7: harvested answers land as `inferred`, never
`official`, because `mpsc_study` records no provenance at all; harvested
subjects are discarded since 98% are the placeholder `'gk'`; and a local row
is only ever modified to fill an *empty* explanation.

*Trap:* dumping JSON out of Postgres over ssh needs base64. `COPY ... TO`
uses text format and escapes backslashes and tabs, which corrupts embedded
JSON (`Expecting ',' delimiter` at char 5896), and `-At` still has to
survive newlines inside question text.

Also: `api.map.hawayu.in` resolves to the old droplet, so the domain
currently straddles both boxes.

No harvest performed — writing to the source-of-truth bank is the user's call.

---

## 2026-10-18 (cont.) — recording sync state so parallel work is safe

Migration `0004_sync_log` adds two tables. `sync_log` records every
`sync-bank.sh` run: the sha256 of the bank JSON it carried, the question
count, and the attempt count before and after — so "did that sync eat my
data?" is answered from a table instead of from memory. A CHECK makes
`attempts_after < attempts_before` unstorable.

`bank_feedback` is the reverse channel. The server never edits bank content
directly; it raises a proposal, which is exported, applied to the local
JSON, and returns through the normal sync. One authority for bank content,
work still possible on both sides. That closes the open tension flagged in
DECISIONS #5.

`./scripts/sync-bank.sh --check` now answers "is the server running the bank
in front of me?" — both checksums, IN SYNC or SERVER IS BEHIND, and how many
proposals are waiting. Verified both ways: identical bank reports IN SYNC;
one edited question in a copy reports BEHIND.

*Two bugs in that check, both from shell field-splitting:*
`psql -F' '` looked fine until the timestamp — which contains a space —
shifted every later field, so the feedback count was reading `04:44` and the
"open proposals" line printed when there were none. Switching to `-F'\t'`
was worse: inside the quoted ssh command `\t` survives as a literal
backslash-t, nothing split at all, and the comparison silently reported
BEHIND while displaying matching checksums. Settled on `|`, which cannot
occur in a checksum, a count or a timestamp.

The first fix looked right in the output and was wrong; the second looked
wrong in the output and was wrong differently. Worth checking both branches
of a status command, not just the one you expect.

Also corrected stale paths in `CLAUDE.md` — it still pointed at
`../mpsc-question-bankv2/db/` for the schema and `../mpsc-question-bankv2/design/`
for the prototypes, both of which moved into this repo, and told the reader
to run the dev server on :5173 with `uv`. A read-this-first file that lies
is worse than no file.

---

## 2026-10-18 (cont.) — the harvest, and two bugs it exposed

Harvested explanations from shiksha-dev. Net result: **18 → 275 real
explanations**. I had claimed the old server held 70,839. It does not, and
the gap is instructive.

**Bug 1 — the query had no ORDER BY.** mpsc_study holds ~50k duplicate
question texts and the dedup keeps whichever copy Postgres returns first,
which without an ORDER BY is arbitrary. Two identical runs reported 8,655
and 8,801. Ordering rows that *have* an explanation first made the harvest
both reproducible and maximal — the count jumped to 34,199.

**Bug 2 — sync-bank.sh never propagated `explanation` to canonical.** 43,018
landed in `appearances` and 18 reached `canonical_questions`, which is the
table the API reads, so none of it was visible. Any bank-owned column added
to the appearances upsert must also appear in the canonical propagate SET
*and* in its change-detection WHERE, or it silently stops halfway.

**And then the real problem: almost all of it was junk.** Of 43,018
harvested explanations, **42,742 were the literal string
`[OCR extraction from Old_Questions]`** — the old pipeline wrote a marker
into that column, not prose. 275 were real.

I had quoted "70,839 explanations" from a `COUNT(*)` on a non-null column
and never looked at the values. Then I shipped them live, where the API
served `[OCR extraction from Old_Questions]` to a user as an explanation.
The harvester now filters placeholders, the junk has been stripped from
both bank and server, and all 18 original explanations were verified intact
against the pristine 2026-10-16 backup.

**The lesson is cheap to state and was expensive here: a COUNT(*) on a
column tells you how many rows are non-null, not how many are useful.**
Sample the values before quoting the number, and certainly before writing
them to production.

---

## 2026-10-18 (cont.) — first exam collection

`0005_seed_iti_collection` seeds **ITI Instructor 2026**: 9 sections, 16
papers, 1,446 questions with an official key. The collections tables were
empty, so nothing in Phase 2 could be built against real data.

Chosen on the data, not preference. UDC/LDC is the natural first exam and
has 92 papers in the bank — **none of them keyed**. ITI Instructor is the
best-keyed exam there is. Structure: Paper-I General English, Paper-II
General Knowledge, then Technical Paper-I and II across seven trades (COPA,
Electrician, Electronics Mechanic, Wireman, Baker & Confectioner, Carpenter,
Workshop Calculation & Science).

*Trap worth recording:* grouping these by `exam_name` undercounts badly —
the same exam is stored under two different casings, so an earlier query
reported 7 papers / 584 scorable when the truth is 16 / 1,446. Match
`ILIKE`, not `=`.

*And a second:* my first generator derived the trade by parsing parentheses
out of the filename. The names are inconsistent enough ("Paper-IV (Technical
Paper-IV) (Wireman)", "Paper-III-Technical Paper-I (Carpenter)") that single
trades split across two sections — `electrician` and `electrician-i`,
`copa` and `paper-iv-copa-i`, with Wireman becoming `general` and `v`. The
generator now matches a known trade list by keyword, ordered so "Electronics
Mechanic" is tested before "Electrician", and it exits non-zero if any paper
fails to match rather than silently dropping it.

Sections filter by `paper_id` because `subject` is NULL everywhere until
classification runs; they can gain subject filters later without touching
the seed.

---

## 2026-10-18 (cont.) — Exams & tools launcher

`/exams` is live, driven by the seeded collection rather than mock data.
`GET /api/collections` and `/api/collections/{id}` return sections with
their paper and question counts, **counted from `v_scorable`** — a
collection can never advertise questions that mocks are not allowed to
score.

Ported from markup line 526: "Library" eyebrow in `#7E4A00`, the clamped
display heading, the two orientation cards (`#F7EAD0` "you are here" and the
white bank card), the near-black flagship panel at `#14130F` with its
`#2A2723` stats rail, and the module card grid.

Verified live: hero `rgb(20,19,15)`, stats rail `1,444 / 9 / 7 / 2026`,
both section groups, nine section cards.

The prototype hard-codes MPSC Combined Prelims as the flagship; we show
whichever collection sorts first by position, which today is the only one.

*Note to self about verification:* my check reported the "Library" eyebrow
missing. It was there — `innerText` returns the CSS-`uppercase` form, so a
case-sensitive match for "Library" fails against "LIBRARY". The test was
wrong, not the page. Worth remembering before "fixing" something that
already works.

---

## 2026-10-18 (cont.) — mock sessions, with the clock on the server

`0006_mock_sessions` plus `/api/mocks`. The property that matters: **the
client never owns the clock.** `started_at` is written server-side at start,
elapsed time is computed server-side at submit, and nothing the client sends
influences either. Verified by backdating a session ten minutes in the
database: the submit reported `elapsed 600s` against a 60s limit and flagged
`late: true`.

Late submissions are **recorded, not rejected** — a slow network should not
destroy an attempt, but the result has to say it was late.

The question set is frozen into `question_ids` at start, so resume works, a
bank re-sync cannot change a paper mid-attempt, and the order shown is the
order scored. Questions are drawn with `random.sample` in Python and fetched
by primary key; `ORDER BY random()` stays banned.

Verified live: answers never appear in the start or resume payload
(`answer_text leaked: False`), a second concurrent mock is refused (409,
enforced by a partial unique index), resubmission is refused (409), another
device submitting someone else's mock gets 404, and scoring with negative
marking is exact — 1 correct × 2 minus 4 wrong × 0.5 = 0.0.

**Found a systemic bug on the way.** The app role had been granted on *all
tables* once, which covers only the tables existing at that moment. 0006
added `mock_sessions` and the API died in production with
`permission denied for table mock_sessions` on the first request to touch
it. Every future migration that adds a table would have done the same.
`0007_grants` adds `ALTER DEFAULT PRIVILEGES`, so anything created by
`postgres` in `public` is usable by `mpsc` without a follow-up grant.

---

## 2026-10-18 (cont.) — the timed paper

`MockRunner.tsx`, ported from prototype line 579. Sticky `#1D1B18` bar with
the countdown and Submit, question area, and the palette grid at 10 columns.

Verified live against the prototype's own state colours: an answered cell is
`#1D1B18`/`#F4EFE4`, the current question carries the `#B0412A` border,
unseen is transparent on `#CFC5B2`. Options use `#EDE5D4` on `#1D1B18` when
selected, with the 26px letter circle inverting.

Ran a paper end to end: picked one option, submitted, got
`0 correct · 1 wrong · 19 skipped · 00:53 taken` and 20 review cards showing
the key beside the pick. **Answers appeared only after submit** — the
start and resume payloads contain no key at all.

Three behaviours worth noting:

*Resume on reload.* The server allows one open mock per device, so a reload
must rejoin rather than 409. The screen asks `/mocks/current` first and only
starts a new paper if there is none.

*Auto-submit at zero.* An abandoned tab would otherwise leave an open
session forever, and that session blocks the device from starting another.

*The countdown is cosmetic and says so in the file.* Stopping it in a
debugger buys nothing: the server recorded `started_at` and recomputes
elapsed on submit. Proven earlier by backdating a session ten minutes.

---

## 2026-10-18 (cont.) — results you can revisit, and mistakes

`/results/:mockId` and `/mistakes`, closing most of Phase 2.

Past results are **rebuilt from `mock_sessions` + `attempts`, not stored a
second time**. The review query uses `unnest(question_ids) WITH ORDINALITY`
LEFT JOINed to attempts — a LEFT JOIN specifically, because a skipped
question has no attempt row and would otherwise vanish from its own review.
Verified: a 6-question paper returns 6 rows.

`MockResultView` is shared between the runner (straight after submit) and
the standalone screen, so the two cannot drift apart.

**"Mistake" means the LATEST attempt was wrong**, not that a wrong attempt
exists. `DISTINCT ON (canonical_id) ... ORDER BY at DESC` then filtering on
`NOT correct`. Showing questions the learner has since got right would waste
their time and understate progress. Verified live: answered one of five
mistakes correctly in practice and the list went 5 → 4 with that question
gone.

Also fixed "1 marks" — visible on every single-mark result.

Phase 2 now has one item left: the scoring explainer. `thread_locks` during
a live mock belongs with discussion in Phase 4, since there are no threads
to lock yet.

---

## 2026-10-18 (cont.) — the palette, measured

Audited the palette with actual contrast maths rather than opinion. Two
findings.

**The system's rules are empirically sound.** Every `dark` area variant
passes AA on the warm paper (6.39–7.84), and the rule "text uses dark, mid
tone only for dots and bars" turns out to be load-bearing: as text, map
scores 4.01, exams 3.67 and rewards 3.20 — three of six areas are
unreadable at mid tone. Whoever wrote that rule had measured it.

**One real collision.** Brand vermilion `#C0462C` was RGB-distance 23 from
the wrong-answer state `#B0412A`, in a system whose central rule is that a
colour names an area and never a state. Every other pair is 73–96 apart.
Fixed to `{ DEFAULT: '#D9461C', dark: '#962F15' }` — distance now 60,
saturation 0.77 → 0.87, and the split exists because the prototype uses
vermilion as `color:` in several places while the old value was already
under AA for text at 4.41. DECISIONS #8.

The saturation increase is also what the user wanted, and it is defensible:
Valdez & Mehrabian (1994) give `Arousal = −0.31·Brightness + 0.60·Saturation`,
so saturation dominates, and learning-environment studies find reading
comprehension higher under vivid than pale colour on *difficult* material.
Yerkes–Dodson caps it — arousal/performance is curvilinear and a learner
sits here for hours — so the shape is **calm reading surface, vivid
accents**. The paper and body ink are unchanged.

Logged `placeholder #7A7366` at 4.10, under AA, as a known issue left for a
design pass rather than patched per-component.
