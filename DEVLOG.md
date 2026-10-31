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

## 2026-10-20 — Private profile and progress

- Added the `/me/profile` backend read/update endpoints on the existing per-browser user row; display name is editable while the generated handle and role remain server-controlled.
- Expanded `/me/progress` with accuracy, recent daily activity, current streak, last activity, and subject totals derived only from approved question tags. Added a user/date attempt index for the timeline query.
- Built the Profile & Progress page with display-name settings, a 30-day activity view, subject breakdown, and links to mistakes, desk, and exam practice. The mobile “Me” tab now opens it.
- Kept profiles device-scoped and explicitly non-authenticated. Cross-device accounts, recovery, public profiles, and device-history adoption remain blocked on the documented authentication decision.
- Verification: frontend production build, API Python compile, migration dry-run, and post-deploy profile/progress endpoint checks.
- Performance follow-up: collection list/detail totals changed from one correlated count scan per section to one grouped query (section-specific paper index or approved-taxonomy index); live `/api/collections` improved from 9.61s to 1.34s, ITI detail 4.36s to 0.25s, and 31-section practice detail 10.42s to 1.02s. Lightweight progress reads skip activity and subject breakdowns; the profile still gets the full breakdown.

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

---

## 2026-10-18 (cont.) — scoring explainer; Phase 2 complete

The prototype's scoring screen is mostly about Score, Reputation and the
Contributor/Mentor/Scholar tiers — XP, monthly resets, leaderboards. None
of that exists; it arrives with games (Phase 5) and discussion (Phase 4).

Porting it verbatim would have published a rulebook for rules the app does
not follow, which is worse than no page at all. So `/scoring` explains what
is actually true today — which questions can be scored and why, how marks
and negative marking work, how the clock works, what counts as a mistake —
and puts Score and Reputation under a plainly labelled "Not built yet".

**Every number is served from `/api/scoring-facts`**, not typed in, so the
page cannot quietly become wrong as the bank changes. Verified live: 12,454
scorable, 59,047 practice, 1,508 held back, 12,342 official + 136
transcribed, 77,751 total — all rendered from the API.

Renamed that endpoint's field from `key_` to `transcribed` before it
shipped. `key_` was a Python-side naming dodge leaking into a public JSON
contract, and `transcribed` is what the UI calls it anyway.

**Phase 2 is done**: collection seeded, launcher, exam page, timed mock with
a server-authoritative clock, results you can revisit, mistakes, and the
explainer. `thread_locks` moves to Phase 4 — there is no discussion to lock
during a mock yet, so building it now would be untestable.

---

## 2026-10-18 (cont.) — mobile pass

Audited every screen at 390×844 and fixed what broke.

**`/scoring` overflowed to 514px.** Its marks table had
`minmax(180px,2fr) minmax(90px,1fr) minmax(200px,2fr)` — a 470px floor plus
gaps, which cannot fit a phone. Now stacks below `sm`, with the marks value
inline beside the outcome.

**Tap targets.** The handoff requires 44px minimum; nothing met it.
Raised the pool toggle, pagination, filter checkboxes, bank options, the
Sections button and Post. Inline prose links were deliberately left alone —
forcing those to 44px turns a sentence into a staircase. Now 0 controls
under 44 on any screen.

**Mock palette** was 10 columns, giving 31px cells on a phone. Six columns
on mobile gives 53px, above the floor, and still reads as a grid.

**Bottom tab bar** added from the mobile prototype: Home / Bank / Desk /
Exams / Me, 52px tabs, hidden from `sm` up. It hides entirely during a
mock — the prototype's exam screen has no bottom bar either, and tapping
"Home" mid-paper would abandon an attempt the server still has open.

**Found an accessibility regression I had caused.** Refactoring FilterRail
onto the shared `Card` component silently turned its `<aside>` into a
`<div>`, leaving the page with zero landmarks. `Card` now takes an `as`
prop. A shared wrapper must not flatten semantics.

**And a real production bug, found by accident.** Chasing why a fix "had
not deployed", the pane was serving `/bank` from its own cache with a
bundle the server no longer had. The deploy was fine — but it exposed that
Caddy sent **no `Cache-Control` at all on index.html**. Since `deploy.sh`
rsyncs with `--delete`, a returning user could hold a cached shell naming a
deleted bundle: a blank page. Now `no-cache, must-revalidate` on HTML and
`immutable, max-age=31536000` on the content-hashed assets.

*Measurement trap:* navigating with `history.pushState` + `popstate` does
not reload the bundle, so an audit after a deploy silently measures the old
build. Use a real navigation with a cache-busting query.

---

## 2026-10-19 — bank filters and exam collection UI

The local source bank is `../mpsc-question-bankv2/bank/mpsc_bank_v2.json`.
Counting its `questions` array gives **77,751**, which matches the total in
the app docs. The prototype's `1,840 questions` is sample text on one exam
landing card. I found no 1,400,000 figure in the app or design handoff. The
nearby **140,552** number in `CLAUDE.md` and `DECISIONS.md` is a historical
row-count snapshot for the separate `mpsc_study` archive, not this bank.

Added year-from/year-to controls to the bank filter rail and connected them
to the existing `/api/questions` parameters. Year input is debounced and
only complete four-digit values are sent, so intermediate keystrokes do not
trigger invalid requests. The scorable pool is now labelled accurately:
`v_scorable` includes official and transcribed keys, not official keys only.

The Exams launcher now retains the full public collection list and shows
additional collections below the featured one. Removed its hard-coded 2026
year and the claim that every exam uses official keys. Section cards now
open scoped timed mocks; the runner title comes from the selected collection
and section instead of the unrelated fixed "ITI Instructor 2026" label.

No test suite or build was run in this session. The API contract and schema
were inspected directly; verify `web` compilation before deploying.

## 2026-10-19 — launch scope finalized

The user asked to finalize the Exams and Bank launch UI and defer LDE exams
until the site grows. The live collection API currently returns only ITI
Instructor 2026 (9 sections; 1,444 scorable questions); no LDE collection is
public today. The launcher now filters LDE by title/id/kind before choosing
the featured exam or counting/listing collections. Direct LDE detail routes
show a short planned-later state, and the mock runner checks the collection
before opening a session. The source data and collection API remain intact for
later use.

Removed the ExamPage's nonfunctional Continue placeholder. Corrected the Bank
orientation card so it promises search and filtering, not user-created sets,
which do not exist yet. Year filters, source filters and answer-pool
explanations stay because they are wired to the API and accurately describe
the available data. `npm run build` passed and `git diff --check` passed.
Frontend-only deployment was selected because this change does not touch the
API or schema.

The deployed-page check found a second set of section cards on the Exams
launcher that still linked to a planned route and said "official key". They
now start section-scoped mocks and say "scorable questions". The additional
exam-list caption now says "available" because deferred LDE sets are
intentionally hidden. Rebuilt after this visual/route audit; ready for the
frontend redeploy.

## 2026-10-19 — Bank and Exams design finish

Refined the Bank hierarchy to match the supplied prototype: eyebrow, display
heading, explanatory copy, 46px pill search, answer-pool control, filter rail,
and a live result header. Search now follows `?q=` links from the site header,
updates the URL as it is typed, and gives feedback when fewer than two
characters are entered. A visible Clear filters control resets text, source,
and year filters.

Kept filters honest against the two API views: scorable accepts only official
and transcribed keys; derived and inferred source filters are disabled there
and become available in All answered. Removed “No published key” as a filter
because neither answer pool contains unanswered rows; the rail explains that
limitation. Changed the question card link to “Details” because the current
route shows appearances and metadata, not the original PDF.

The Exams launcher copy now describes only current functionality and the
live answer-key policy. Added an empty-library state. The exam detail bars
now display each section's actual share of scorable questions and expose that
value to assistive technology. `npm run build` and `git diff --check` passed.

Live desktop and 390px mobile checks passed with no horizontal overflow on
Bank, Exams, or the exam detail page. Verified pool behavior live: Scorable
shows 12,454, switching to All answered shows 59,047, filtering Derived
answers gives 6,614, and switching back clears the incompatible filter.
Search for “Swadeshi” returns 7 matches and syncs `?q=Swadeshi` into the
address bar. Final wording cleanup keeps exam-detail labels consistent with
scorable counts and removes the implication that its Bank link is prefiltered.

The final frontend build was deployed with `./scripts/deploy.sh web`. The
cache-busted live Bank, Exams launcher and exam detail pages all served the
new design and counts; section CTAs resolve to their section-mock routes. The
browser was returned to its default viewport after the mobile checks.

Restored the supplied design palette for the Bank and Exams areas: Practice
blue, Exams ochre, warm paper surfaces, ink actions, and the exact
`#C0462C` vermilion brand mark. This supersedes the temporary brightened
vermilion decision documented above. `npm run build` and `git diff --check`
passed.

---

## 2026-10-18 (cont.) — I took Vansa down, and then made it impossible to repeat

While adding the SPA cache-control headers I rewrote `/etc/caddy/Caddyfile`
with `sudo tee`. That file is **shared with Vansa** (`family.hawayu.in`),
and the rewrite deleted its site block. Vansa went down at 18:48. Because
the Let's Encrypt cert was still on disk, it failed as a TLS handshake
error rather than an obvious 404, and because every check I ran polled only
`study.hawayu.in`, I carried on for some time without noticing. Another
session found and restored it.

A memory describing this exact hazard already existed. I did not read the
memories for the *other* projects on this host before changing shared
state. That is the actual lesson, and it is cheaper to state than it was to
learn: on a shared box, the blast radius of a config write is every project
on it, not the one you are thinking about.

**Structural fix, so remembering is no longer required.**
`/etc/caddy/Caddyfile` is now only `import /etc/caddy/sites/*.caddy`, and
each project owns `/etc/caddy/sites/<host>.caddy`. A project rewriting its
own file cannot reach another's. Both sites verified after the split:
study `/bank` 200, study `/api/health` 200, family 200 — and family's own
media-cache and upload-size rules survived intact.

`CLAUDE.md` rule 4 now carries this, including: after touching Caddy,
systemd or Postgres, curl the *other* site.

## 2026-10-19 — Taxonomy-backed Bank and subject practice

The supplied platform archive's `mpsc_schema_v3.sql` is an older draft than
the hardened v3 migration already deployed here, so I kept the current schema
and added `0008_question_taxonomy.sql`. It stores one selected taxonomy-v2
claim per canonical question, including labels, source, review status,
confidence, and evidence. The Bank API exposes only approved claims; pending
and rejected proposals cannot drive learner filters or scored mocks.

`bank_to_csv.py` now exports the selected classifications with labels, and
`sync-bank.sh --classifications-only` publishes just that table plus a
subject-wise practice collection. Existing saved exam sections can filter on
approved `subject_id`/`topic_id` as well as paper IDs, and their counts and mock
candidate sets use the same query. The Bank has live subject/topic selectors
and approved topic chips; Exams now links to 18 reviewed subject sections.

The first classification import exposed an ID-boundary trap: the bank's
question IDs are appearance IDs, while the new table references canonical
IDs. Resolve through `appearances.canonical_id`; a read-only count confirmed
all 77,751 staged rows map to unique canonical rows. A subsequent psql error
caught an unqualified `is_primary` shared by the staging and appearance
schemas; qualifying every staged field fixed it. Both failed imports rolled
back before changing classification data.

The clone rehearsal for migration 0008 applied cleanly, then the migration and
classification-only sync completed. The server now has 77,751 taxonomy rows
(21,712 approved and 56,039 pending), and the generated public collection has
18 sections / 4,625 scorable questions. `/api/questions/taxonomy`, a filtered
question list, and both collection endpoints were checked live. The UI is
running at https://study.hawayu.in; health reports 77,751 questions and 12,454
scorable. The sync touched no question text, answers, attempts, or users; the
server still has 3 attempts and 2 users.

The general bank checksum still reports the server behind because the
full-bank sync remains separate; this work intentionally synchronized only
v2 classifications. The live bank's 136 changed appearances and legacy
difficulty policy still need their own reviewed sync plan. Local TypeScript
build, Python compilation, and shell syntax checks passed.

## 2026-10-19 (cont.) — Published the next reviewed taxonomy batch

The question-bank repo's OpenAI review batch 006 added 100 unique pending
question-level decisions: 89 supported classifications were approved or
corrected and 11 remained pending because their path was not sufficiently
supported. Batch validation reported 0 issues across 312 batches / 78,934
rows; the merge preview had 0 unresolved ties. The classification-only sync
loaded all 77,751 rows and regenerated dependent subject-wise collection
sections. A fresh `sync-bank.sh --check` confirmed local and production both
show 22,320 approved / 55,431 pending / 0 rejected. The bank checksum remains
different by design because no full bank sync was run. No question text,
answers, attempts, or accounts were written by this operation.

## 2026-10-19 (cont.) — Split the Study Desk and designed partner entry

The user asked to work on the design while the large taxonomy queue continues
in another terminal. I split `/desk` into **My study** and **Study partners**
tabs, keeping the personal plan as the default. The new Community-colour
partner screen presents two distinct paths: a mutual invitation to someone
known and a later opt-in discovery flow based on shared study interests. Each
opens an explanatory dialog; neither sends a request, publishes profile data,
or writes a discovery setting. The UI says so directly and describes the
account, blocking/reporting, and moderation gates before social release. It
also keeps following public study materials separate from partner status and
private desk access. No server-backed social action was added.

The web build passed, and `./scripts/deploy.sh web` deployed the frontend.
The live `/desk` and its Study partners tab were opened and checked. At a
390 × 844 viewport the cards stack vertically and remain within the screen;
both preview dialogs fit and close without sending data. No API, account, or
social database changes were deployed.

## 2026-10-19 (cont.) — Corrected Study Desk prototype fidelity

The first partner design was not structurally faithful to the supplied Claude
prototype: it made invitation and discovery cards the hero instead of showing
the shared desk. Reworked the partner tab around the prototype's actual page
order: Community eyebrow and desk heading, visibility row and actions, study
desk mode, desk scene/status area, content tabs, then a broad content column
and narrow side rail. The old `A little company...` hero is removed.

Because this frontend has no account or social APIs, sample partners, presence,
counts, and shared questions are represented by explicit empty states. The
visibility controls say that settings are not saved. The buttons remain safe
previews; bank navigation is clearly just browsing. Only the study desk mode
is represented; the prototype's class mode is deferred. Updated
`docs/DESIGN-FIDELITY.md` to name the prototype section and tokens and to
describe this privacy-safe adaptation. Build and live deployment are pending
this correction and should be completed before handing off.

Correction to the preceding entry: the fidelity revision has now been built
and deployed with `./scripts/deploy.sh web`. TypeScript and Vite completed
successfully; `git diff --check` passed; live `/desk` and the emitted JS asset
both returned HTTP 200. No API or database changes were part of this deploy.

## 2026-10-19 (cont.) — Built the V3 public homepage

The user asked to do the homepage first, including required functionality and
backend work. `/` previously redirected to `/bank`, so the public V3 landing
screen had no route. Replaced that redirect with a dedicated homepage and its
own dark hero header/footer, live answerable sample question, study-area chips,
three steps, live exam collection cards, and clearly marked future community
features. The main app shell stays on the learner routes; its logo and mobile
Home tab now lead to `/`.

Added `GET /api/home` without a migration. It returns live bank counts, one
daily rotating MCQ from `v_scorable`, source metadata, and public collection
names/section totals. The sample never uses inferred keys; choosing an option
uses the existing answer API and records normal anonymous-device practice.
The page discloses this on the question card. No user attempt was created
during QA.

The initial implementation reused `/api/collections` for homepage cards. Live
measurement showed that endpoint at about 2.32 s because it calculates
per-section question counts. Replacing that homepage dependency with a
lightweight public-metadata query brought `/api/home` to 0.287–0.306 s over
three requests. The existing `/api/collections` endpoint remains unchanged.
API deploy restarted healthy at 77,751 questions and 12,319 scorable; web
build passed and was deployed. The live homepage loaded its question and both
collection links, `/api/home` and `/` returned HTTP 200, and `family.hawayu.in`
returned HTTP 200 after its redirect. No schema or account/social changes.

## 2026-10-19 (cont.) — Corrected “homepage” to the V3 Community feed

The user clarified that they meant the Community section/home (`is.feed`), not
the public marketing landing (`is.landing`). Implemented `/feed` in the V3
three-column layout, wired its live collection and practice summaries, and
added `GET /api/community/feed`. The endpoint returns only published question
explanations and doubts after the requesting device has answered that exact
question. The tab set is present; tabs that need accounts, social graph, or
moderated user publishing return explicit unavailable states. No writing,
following, voting, fake people, or fabricated activity was added.

Production currently has no public discussion posts; existing users are
anonymous browser-device identities, so the feed correctly shows its answer-
first empty state until there is eligible content. Added paging, responsive
app navigation to `/feed`, design-fidelity notes, and a Phase 4 status update.
`python3 -m compileall -q api/app`, `npm run build`, and `git diff --check`
passed. Deployed to `study.hawayu.in`; the live feed rendered successfully and
its read API returned the empty state. `family.hawayu.in` redirects to a
separate Lushai-language app (`/lus`) and returns 404 for `/lus/feed`; it is
not this site or deployment target, so it was left untouched.

## 2026-10-19 (cont.) — Match Community feed to V3 structure

After the user clarified the exact V3 Claude Design page, adjusted `/feed` to
match its `is.feed` composition more closely: dark exam tile, progress card,
continued-study/desk module, partner preview, live exam list, featured banner,
compose card with MCQ/Doubt/Note/Material quick actions, rounded pill tabs, and
right-rail headlines, challenges/cup, weekly stats, bank, and exam cards.
Prototype demo people, dates, scores, headlines, and memberships are not real
production data, so these areas retain their layout but show honest inactive
states or live device/collection data. Compose actions open a preview explaining
why publishing is not active. Build and final live visual review pending.

The V3-structure pass is complete and deployed to `study.hawayu.in`. The live
browser review confirms the three-column feed modules, V3 compose controls and
rounded tabs, live exam collection/section counts, device progress and weekly
summary, and the answer-gated discussion empty state. The expired open mock
reports “Time elapsed”; no sample social activity is surfaced. Frontend build,
API compile, and `git diff --check` passed; `/feed` and `/api/health` return 200.

## 2026-10-19 (cont.) — Shiksha-inspired owner moderation console

Adapted the ShikshaCom admin review-queue pattern to the personal site and the
V3 `is.modq` design. Added `/admin/moderation` with live Reported, New users,
Appeals, and My actions tabs; queue counts; per-post decisions; reviewer notes;
undo history; and the V3 safety guidance rail. The backend uses the site's
existing `abuse_reports`, `appeals`, `sanctions`, and `mod_actions` schema. New
migration `0010_moderation_admin.sql` adds reversible state snapshots and the
audit action names needed for undo and appeal decisions. The dry-run on a cloned
production database passed before migration 0010 was applied.

Moderation uses a separate 256-bit owner bearer token; the anonymous device
header cannot authorize the admin API. The token is stored mode 0600 at the
local repository's ignored `.admin-token` path and in root-only
`/etc/mpsc/admin-token.env`, loaded by a systemd drop-in. The UI retains it in
session storage only. No admin credential is in the Vite bundle or repository.

Compiled the API, built the frontend, and deployed both. Live checks: no-token
queue request returns 401; all four authenticated queue tabs return 200 with
accurate zero counts; `/admin/moderation` and API health return 200. The admin
screen was visually checked in the production browser. No moderation action was
applied because the live queues are empty. Moderator scopes/multi-person
identities remain later work; the first console is owner-only.

## 2026-10-19 (cont.) — Finished Question Bank page states

Completed the Question Bank's loading skeletons, accessible status announcements,
retry action, and clear no-results state. Search copy now describes the full
collection and browse-only unanswered questions; pagination includes the
current page and clearer disabled states. Existing live filters and answer
pools remain connected to the API. `npm run typecheck` and the production web
build passed; the frontend was deployed with `./scripts/deploy.sh web`. Live
`/bank` returns HTTP 200 with the deployed bundle, and `/api/health` reports
77,751 questions and 12,319 scorable questions. No question data was modified.
# 2026-10-20 — Exam tracks and English recall tools

- Added saved, paper-ID-backed collections for LDC, UDC, Assistant Grade, MCS combined prelims, Group B gazetted, and Group B non-gazetted. Assistant/UDC combined direct papers intentionally appear in both tracks; departmental promotion papers remain separate.
- Added a collection-aware question-bank filter. Collection cards distinguish total browsable questions from verified-key questions, and do not offer a scored mock when fewer than 20 keys are available.
- Added English topic browsing and a vocabulary recall helper using the approved English vocabulary taxonomy and key-backed questions only. Review answers are checked by the API; browser-local schedules support Again/Hard/Good/Easy intervals and due-first practice.
- Current limits are surfaced: Group B gazetted coverage currently maps to historical departmental Inspector papers only; UDC and Assistant papers currently lack verified keys for scored mocks. Recall progress is device/browser-local.
- Applied migrations 0011–0013 and deployed API and web to `https://study.hawayu.in`. Live MCS prelim collection reports 1,921 questions / 1,098 verified keys; Assistant reports 1,015 / 0; the vocabulary topic has 154 verified keys.
- Verification: Python bytecode compile, frontend production build, migration dry-runs against a database clone, live API health and collection/filter responses.

## 2026-10-20 — community contribution/review design handoff

Prepared `docs/review-system/START-HERE.md`, `SPECIFICATION.md`, `IMPLEMENTATION.md` and `ACCEPTANCE.md` for implementation by Luna or another model. Inspected the actual auth dependencies, owner-token conduct moderation, existing feedback/report schema, bank sync ownership and the v3 contribution screen around line 2080. The design uses individual scoped reviewer grants, immutable revisions, explicit quorum, publication receipts through the local bank, and a PostgreSQL outbox. It includes new-MCQ intake against registered papers, source requests, correction proposals, appeals, attribution, notifications and reviewed estimated scoring. Eight ordered packets map to twenty acceptance gates; every gate remains pending.

Integration hazards recorded: canonical IDs and appearance IDs differ; email verification is not configured; derived provenance alone does not certify independent review; the sync canonical-update predicate omits answer-text-only change detection; the existing content-report trigger changes bank status and needs reconciliation with server-owned review holds. The prior official-only mock policy needs an additive estimate mode under the user's new direction. No application behavior, bank data, migrations or production services were changed in this design task. Documentation checks verified all 20 acceptance IDs are unique and mapped; no application tests were run because there is no implementation to test. Future implementers must record real gate evidence rather than treating this specification as production readiness.

## 2026-10-20 — question bank continuation and module conflict batch

Imported 120 prior independent solver proposals through `tools/merge_solve_bankv2.py` after checking exact IDs, input stems/options and explanations. The result wrote 71 high/medium indexed proposals as `derived` and 49 low-confidence/no-index records as disputed. A receipt records input/output fingerprints and source PDF SHA256 values. The bank schema validator passed; one-way production sync updated 108 appearances and preserved 13 attempts/10 accounts.

Then reviewed 21 arithmetic/reasoning module conflicts across eight UDC/LDC/Assistant papers. Rendered 21 cited source pages, checked the printed questions/options, independently recomputed each result, and applied them with the guarded derived-claim importer. Refreshed the answer crosswalk from the bank; raw UDC/LDC/Assistant conflicts fell from 200 to 179 (1,695 agree), with two official-key mismatches already confirmed against the final MPSC key. The production sync updated 21 appearances and `--check` reported IN SYNC. Current checksum is `c37635dc2aef75361655d7461f821b85e7a8d9854aa0026eb39d00a91e83d674`; bank schema validation passed. Strict official-key scoreable remains 12,324; the bank has 67,868 indexed answers and 9,883 without an index. The estimated mock feature is still not implemented, and 177 module conflicts plus the larger unanswered set need continued work.


## 2026-10-20 — derived answer continuation

Checked the February 2026 LDC Paper-I source pages and authoritative references, corrected four conflicting factual answers as `derived`, and recomputed/corrected LDC Paper-II Q72 from its printed table. Then reviewed the five True/False rows in MFAS December 2024 Paper-I Q14 against its scan and GPF references. The model proposal for the post-retirement nomination statement was wrong; the checked answer is True. Updated the guarded importer so claims may fill genuinely unanswered slots without permitting key/official overwrites. Refreshed the answer crosswalk: UDC/LDC/Assistant is 1,700 agree / 174 raw conflicts; Combined Prelims remains 39 agree / 1 adjudicated raw mismatch. Schema validation passed and the canonical bank was synced to production at `c999ee13d046326534d4af77c11a3d04692cdb499d3f11ac65c6725c833a1e3f`; 13 attempts and 10 accounts are preserved. Strict official-key scoring remains 12,324; 67,873 total answers have indices and 9,878 do not. No app test suite was run.


## 2026-10-20 — English answer crosswalk corrections

Reviewed five stable English usage conflicts against four scanned source pages and corrected the canonical answer indexes as derived: UDC ARC 2020 Paper-I Q59; UDC Excise Paper-I Q27, Q32, Q73; UDC Social Welfare Paper-I Q42. Updated `module-bank-answer-review.csv`; UDC/LDC/Assistant raw conflicts fell from 174 to 169 (1,705 agree), leaving 167 unadjudicated after accounting for two final-key resolutions. Schema validation passed. Production sync updated five appearances; local/server checksum is `3a900b9916f6da6f3ab5450cc86c6bac9765d2a601f1ed3c319a39631f303a98` and `--check` reports `IN SYNC`.


## 2026-10-20 — source-verified factual conflict batch

Reviewed 14 printed questions across the UDC Social Welfare, Excise, Agriculture, SAD, Tourism, ARC and Assistant papers. Visually checked the corresponding scan pages and corroborated the stable sports, award, host-city and event results with authoritative records. Applied 14 hash-guarded answer corrections as `derived`, preserving the printed choices and official-key provenance. Explicitly held the singularly worded Bharat Ratna question and year-ambiguous Forbes ranking question. Manifest: `../mpsc-question-bankv2/state/reviewed-derived-answer-claims/verified-stable-facts-20261020.json`. Schema validation passed for all 77,751 questions; production sync updated 14 appearances and preserved 13 attempts/10 accounts. The module crosswalk now shows 1,720 agreements and 154 raw conflicts (152 unadjudicated after two final-key resolutions). Strict official-key scoreable remains 12,324; 67,873 questions have answer indexes and 9,878 do not. Local/production checksum: `36ba5491ebbcace2f0f4e7cfd2fca33c9b6cd84725607e9fc1eb210d187aae85`; `sync-bank.sh --check` reports `IN SYNC`.

## 2026-10-20 — source-backed General English answer completion

Filled two Informatics Officer General English Paper-II (2021) answers from
the final MPSC key and eight from sentence-structure analysis. The final key
conflicts with derived classifications on Q42–45 and Q47–50. Migration 0021
marks those exact questions disputed; API and practice cards disclose the
conflict, and strict official-key mocks exclude those eight answers. Added
source-checked derived answers for Labour Officer General English-II Q10 (the
scan underlines “me”) and MCS Main 2022 General English Q1(d).

Migration 0022 clears a false `duplicate-options` defect from the two official
Informatics answers: each has three unique printed options and an empty fourth
slot. The official-key scoreable pool is now 12,392. The English paper
directory, search, source-PDF links and paper-filtered browsing are live at
`https://study.hawayu.in/english`; live search returns 138 matching papers,
and question detail returns the key-dispute metadata.

Five unanswered MCQs in General English sections remain held because of source
defects: four lack the correct answer choice, and one omits the problem figures. Overall the bank still has 9,800
no-index questions (7,973 descriptive and 1,827 objective), so it is not
complete. Schema validation and the frontend production build passed. Local
and server checksum is `ac3974ed92d5e5af5a3f9bb5372d45a0242d01cbb57bebc2ffc923c1ae85e9a7`; `sync-bank.sh --check` reports `IN SYNC`.


## 2026-10-20 — final-key conflict audit completed

Resolved all 97 audited answer disagreements using the paper-specific MPSC final keys. Compared with the original bank, 95 answer letters differed from the final key; two apparent conflicts were provisional-only and the final key confirmed the existing answer. All 97 carry final-key provenance. Manually read 17 answers omitted by OCR from the final key scans. Updated `tools/parse_answer_keys.py` so same-letter final keys take precedence in provenance over provisional keys. The evidence packet is in the bank repository at `state/reviewed-key-claims/bankwide-final-key-conflicts-97.json`. Cleared old explanations for the 83 changed answers that had them while preserving those texts in the audit record. Synced final answers and explanation changes to production, preserved 17 learner attempts/11 users, and verified the live API health and matching bank SHA. Remaining no-index objective questions: 1,817; descriptive questions (7,973) need rubric/text evaluation, not MCQ indexes.

## 2026-10-20 — source directions and print emphasis restored

Recovered matching source context from 181 exact-hash UDC/LDC/Group B paper
PDFs: 4,092 shared directions and 2,490 emphasized stems across 4,429
questions, plus three option markup sets. Held source mismatches and duplicate
question numbers. Added safe bold/underline/italic rendering and direction /
passage display to question cards, details, mocks and the paper viewer. Schema
migration 0025 was rehearsed, applied, then the bank synchronized (17 attempts
and 11 accounts preserved) and API/web deployed. Current bank SHA256:
`f2d2f60958ace4278e4d539eae2245b5897794252b0ac8c654af8abd3e5e78f3`; live
API reports 77,751 questions / 12,494 strict scorable.

## 2026-10-20 — descriptive paper visibility, arithmetic study path, and 18 answer fills

Paper summaries and the paginated paper viewer now count and label descriptive
questions explicitly, show marks when present, and keep descriptive records in
printed order without offering an MCQ check. Verified live on Group B Gazetted:
the collection lists all five papers with descriptive items, and the source
paper viewer returned its 10 descriptive questions (including marks).

Added `/arithmetic` from the India Study Map aptitude hub: all 26 mathematics
concept lessons, formulas and worked concept checks, per-concept local progress,
and a paginated set of source-backed questions from the shared mathematics /
arithmetic bank (608 approved records). The arithmetic route is linked in the
site navigation.

Filled 18 blank arithmetic MCQs with source-page-checked derived answers. A
source scan exposed an omitted square-root sign in 2019 DO Paper-II Q56; the
stem was corrected and the answer is 12. Two duplicate 2010 cloth questions
remain held because the fractional glyph in the scan is unreadable. Objective
blanks are now 1,799; descriptive questions remain 7,973. Synced the bank and
deployed web/API. Local/server bank SHA256:
`5e2d485ed6f9d30104c14779876f2ff6e2a8747b8c2860a50ae5a935bfcf24c6`.
Production health: 77,751 questions / 12,494 strict scorable; 17 learner
attempts preserved.
# 2026-10-20 — Arithmetic & Reasoning shared-bank workspace

Expanded `/arithmetic` from an arithmetic-only lesson page into a Mathematics
and Reasoning workspace with Learn, Topic practice, and Exams & papers views.
The topic selectors and paper search use the approved taxonomy and canonical
question/paper APIs; practice stays connected to normal answer submission and
progress recording. Adapted 16 reasoning lesson cards from the legacy MPSC
Aptitude Hub, alongside the existing 26 math lessons.

Added source-image URLs to question list/detail and exam paper responses. The
API accepts only content-addressed `images/page-renders/<hash>.png` assets;
the source sync now publishes those 246 referenced scans to `/papers/figures`
with immutable caching. Question cards and paper views show the scan when one
is present, and preserve source directions, passage context, emphasized
question/option markup, answer provenance, and source PDF links.

Live taxonomy reports 890 Mathematics questions and 758 Reasoning & Aptitude
questions. Subject paper search returned 70 Mathematics papers and 74
Reasoning papers. API health is green at 77,751 questions / 12,494 strict
scorable. `python3 -m compileall -q api/app`, `bash -n scripts/sync-source-pdfs.sh`,
`npm run build`, and `git diff --check` passed. Figure archive was synced and
API/web deployed to `study.hawayu.in`; the sample source scan returned HTTP 200
as `image/png`. Concept lesson progress remains browser-local; bank question
attempts use the app’s existing device/account progress service.

## 2026-10-20 — Arithmetic live crash fix

Fixed a live `/arithmetic` route crash: the recursive emphasis formatter shared one global regular-expression cursor, so formatting a nested span could reset its parent scan and hang the renderer. Each parse now owns its regex cursor. The displayed subject total now sums approved topic counts plus approved untagged questions, instead of showing only the untagged remainder. Live browser verification confirmed 890 Mathematics, 758 Reasoning & Aptitude, bank-backed practice, topic filters, and both subject paper lists. Redeployed the web bundle (`index-DZQkcBZ-.js`).

## 2026-10-20 — Arithmetic lesson progress on the API

Added an additive migration and `/api/me/learning-progress/{module_id}` read/write endpoints for guided lesson visits and concept-check outcomes. Arithmetic lessons now merge device-local progress with backend progress, keep a local fallback when the API is unavailable, and sync updates to the resolved device/account user. Fixed direct `?topic=` links so reasoning lesson IDs open the Reasoning subject on first load. Migration 0026 passed the production clone rehearsal and was applied; web and API deployed, API health returned 77,751 questions / 12,494 scorable. Web build and API compilation passed.

## 2026-10-21 — Arithmetic page follow-up

The user reported that `/arithmetic` was still buggy but supplied only the URL, so the exact on-screen symptom remains unconfirmed. The live HTML and question, taxonomy, paper, and learning-progress endpoints responded successfully; the Mathematics and Reasoning taxonomy totals were 1,011 and 800, respectively, and the first paper request returned HTTP 200 in about 0.32 seconds. Browser automation was blocked by its URL security policy, so no interactive visual claim was made.

Fixed three reproducible page behaviors: paper cards now pass their `paper_id` into the shared bank filter, the practice header shows the selected topic's count, and the Learn/Practice/Papers view survives refresh through `?view=`. The page also defers its question request until Practice is opened, reducing initial network work. The Vite production build passed and the web bundle `index-FhFtu_mH.js` was deployed; live HTML references that bundle. The exact user-reported symptom still needs confirmation before claiming the page fully repaired.

## 2026-10-21 — bank admin/contribution implementation and controlled deployment

Continued the user-authorized implementation in an already dirty application checkout; preserved the earlier Mizo/Essay/library/exam/account work. Added migration 0030 for explicit subject-scoped grants, immutable proposal revisions/decisions/events, mapped source evidence, holds, publication manifests, credit ledger, votes, notices and worker health. Implemented contributor workshop/history, independent review/diffs/appeals, admin question/paper/taxonomy/report/permission/audit views, published community practice and leaderboard/feed/profile integration. The server accepts proposals only; the local JSON bank remains authoritative. The trusted workstation worker holds the shared writer lock, checks source/manifest/bank hashes, writes a durable receipt before atomic replacement, syncs using the existing pipeline, verifies live fields and acknowledges exactly once. Installed the user timer, observed successful empty-queue runs and an online server heartbeat. It queues work while this workstation is offline.

Ran 21 real PostgreSQL integration tests with disposable synthetic databases/banks, including actual CSV/sync SQL, answer-index-only changes, independent review, concurrent requests, mapped key validation, original MCQ publication, explicit holds, source request evidence, legacy report resolution, crash receipt recovery, credit reversal/privacy and mock snapshot consistency. All passed; Starlette emits one upstream AnyIO deprecation warning. Browser checks covered an author submission, two independent approvals, role-scoped owner/reviewer screens, hold/release, 360/768/1440px layouts and profile credit. Recorded screenshots use synthetic counts. Migrations 0030 and 0031 each applied cleanly to a production dump clone, then through the migration runner to production. 0031 freezes content/options/key/provenance for newly started mocks and prevents concurrent double submission; old sessions cannot honestly receive historical snapshots.

Two traps mattered. Registry bootstrap initially read a nonexistent `version` field; the real taxonomy calls it `taxonomy_version`. Fixed it before registering anything and added a regression test; production bootstrap registered 177 nodes and 1,938 exact paper hashes. Publication also exposed the existing sync predicate's answer-only omission: it compared answer text but not index mapping. Corrected and proved it with actual isolated sync SQL; no real bank answer was changed as a test. The worker now selects the queue inside the shared bank lock to avoid stale concurrent worker selection. Registered-paper fulfillment/additions require evidence tied to that exact registered PDF, rather than a URL alone.

Built locally and deployed API/static assets. Verified all 23 API source/requirements files and 12 web build artifacts match the server by SHA256; recorded reports/review-system/deployment-artifacts.json because Git HEAD db557cb does not describe this dirty deployment. API health remains 77,751 questions / 12,494 strict scorable questions; bank checksum remains 9affc71fae6f… in sync, and family.hawayu.in returns final HTTP 200. Documentation and evidence are also copied into the operator's private server release-report directory. No substitute admin was created: the nominated hruaitluangasailo20@gmail.com account still does not exist. Its signup and user confirmation are required before the authorized owner bootstrap; never grant automatically from an unverified email string.

This is a working core deployment, not completion of all original enterprise release gates. ACCEPTANCE.md records partial/pending A01–A20 coverage; OPERATIONS.md provides commands and recovery. Outstanding: adjusted mock assessment history after key corrections, historical derived-answer review certification, staff MFA/email verification, module-crosswalk adjudication UI, full partial-form autosave, structural taxonomy/media ingestion UI, exhaustive accessibility/load/security checks, backup restore and external alert delivery. Do not claim those passed or that the bank's missing answers were resolved by admin implementation. Stopped disposable browser fixture services and cleaned their test databases after checks; no production user history was replaced.

## 2026-10-21 — nominated admin account provisioned

The user confirmed signup. Ran the trusted bootstrap for the previously authorized exact email hruaitluangasailo20@gmail.com; it found one existing account and granted owner access. Verified an active owner grant covering all subjects directly in PostgreSQL. No account or password was created by the operator. This supersedes the pending-owner status in the earlier deployment checkpoint; the remaining acceptance limitations are unchanged.

## 2026-10-21 — first real correction prepared; dummy-account publication rehearsal

The user requested the first real correction workflow and authorized dummy reviewers because the system is not being used soon. Visually rendered the 2018 Sub-Inspector Mathematics source PDF page 5 and verified Q42 (70m by 50m garden, posts every 5m, options 40/44/48/50). Derived C=48 by closed-boundary perimeter and side-interval counting; preserved derived provenance rather than claiming an official key. Added a reproducible rehearsal script restricted to this exact case. It used a copied one-question bank, real PDF SHA256, actual API and actual sync/ack SQL with DEMO identities in disposable PostgreSQL. Draft/submitted/in_review/accepted/published completed; repeated acknowledgement left one 10-point demo award; strict official scoring excluded the derived answer. The temporary dummy accounts/database were removed. The real bank checksum stayed 9affc71fae6f… and no production dummy approvals or awards were written.

Submitted the real correction into the nominated owner's live contribution history at the user's request, with an explicit operator-assisted audit event and normal proposal validation. Contribution con_f567526b066e4af2b89ab57292cd7e53 is submitted with zero approvals/publications; the real answer remains blank pending independent content reviews. The operator intake is idempotent: a repeat returned the same ID. This is not an assertion that dummy accounts establish independent review. Source/evidence, rehearsal receipt and live submission artifacts are in reports/review-system/first-correction and copied privately to the server release reports.

A deployment trap surfaced during operator intake: sourcing db.env alone selected the legacy default bench database, where users has no email column. The read query failed before any writes. Corrected the trusted CLI to read only DATABASE_URL from the running API service environment and require the mpsc database; no credentials were printed or copied into artifacts. No application code or schema changed this turn. Preserved the previous deployment and its readiness limitations.


## 2026-10-21 — immutable adjusted scores and authenticator security

Continued the user's six-stream Astra plan, with mail provider explicitly deferred. Implemented/deployed migration 0032 and append-only score assessments. Original attempts and mock marks stay unchanged; new adjusted outcomes carry provenance/coverage and exclude old snapshots, changed presentation/context or unsafe option identity instead of inventing correctness. Newly admitted derived estimates now require a matching published reviewed derivation. The bank JSON was not modified; production strict eligibility is 12,490, four fewer because malformed options are rejected. Total bank is still 77,751; wider practice was 67,026 at the scoring checkpoint. This did not solve the remaining 1,652 missing MCQ answers or publish the real garden-post correction.

Astra's focused review found overlapping-submission job lock ordering, scan cursor resets, omitted source context, draw-to-snapshot eligibility races and a worker processing a different historical job from the row whose failures it charged. Fixed each with regression coverage: distinct new-record jobs, deterministic locking, context revisions, one-statement exact presentation capture and explicit claimed-row processing. Semantic versions retain A→B→A; retries do not duplicate the same assessment. Final follow-up could not complete due Astra usage cap, so no final independent sign-off is claimed. Thirty-four tests passed for this scoring checkpoint. Browser synthetic result showed original 2 versus adjusted -0.5 separately; desktop/mobile evidence saved. Legacy result key disclosure without a historical snapshot was masked before the final scoring redeploy.

Implemented/deployed migration 0033, account-bound encrypted SHA1 TOTP seeds, one-use hashed recovery codes, factor-required sign-in, recent password enrollment/replacement, staff write step-up verification and append-only security events. Added /account/security and login factor input. Production key generated on server into root-only environment file with an app-only systemd drop-in; its value never entered repo/reports. The real owner was not enrolled and no password was changed. Recovery codes are shown once in transient component state. Staff cannot disable their factor; lost phone uses a saved recovery code. No email sender/recovery delivery was configured, matching Choose later.

Combined suite: 41 passed in 6.76s with one upstream Starlette/AnyIO deprecation warning. Tests use isolated PostgreSQL and synthetic accounts; coverage includes concurrent code replay, expired pending setup, missing key failure, CSRF, staff verification expiry and recovery rotation/disable. Frontend TypeScript/Vite build succeeded, main JS 496.93 kB. Browser checked initial security screen and login field; 360px body width was exactly 360px, no horizontal overflow. MFA backend confirmation flow is integration-tested, not manual enrollment on production. Migration 0033 applied cleanly to a production-dump clone before live application. Both study and family returned final 200 after deployment. Artifact hashes were compared locally/server-side, and docs/evidence copied privately to the server. No global Caddy configuration changed.

Remaining: genuine independent reviewers/first production correction, missing bank answers, advanced taxonomy/media/module tools, mail delivery, full acceptance/load/accessibility/security/backup-restore/external-alert gates. P01–P08 and the entire enterprise request are not all complete. Preserve the encryption key along with encrypted operational backups; DB-only recovery cannot recover authenticator seeds. Disposable browser services are shut down after evidence capture.


## 2026-10-21 — bank repair workspace after security work

The user asked to move on from security. Built/deployed the next admin workflow: Admin → Questions now combines a paginated repair queue and selected-question inspector. Issue filters cover missing MCQ answers, malformed option sets, source defects, held questions, unofficial answers, official/transcribed keys and descriptive questions. Subject, paper, search, selected question, printed appearance and page offset live in the URL. Paper cards link directly to their filtered question workspace. Overview KPI links now apply their actual issue filter instead of all opening an unfiltered list.

The inspector shows instructions, passages, source emphasis, options, recorded answer/provenance, safe figure references, registered documents, canonical/appearance disagreement, existing submitted corrections and source PDF link/optional preview. PDF preview loads only on demand and depends on the browser's PDF support; an explicit external-tab link is available when embedding cannot render. No bounding-box highlight is claimed. Correction links preserve the selected appearance. Fixed ContributionEditor which previously ignored the appearance query parameter and loaded the primary appearance. Also caught paper-filtered lists opening the primary source despite selecting another paper: representative appearance IDs now come from the requested paper and paper results sort by PDF page/printed number.

Added read-only inspect API with canonical subject grants and existing overlapping-active-mock protection. Browse remains compatible with missing=true. Query lengths, filter values and pagination are bounded; dynamic SQL fragments come only from a fixed issue dictionary. No new migration and no bank JSON/answers changed. Source checks and review/publication policy remain in the existing workflow.

Combined suite: 44 passed in 6.25s, one upstream warning. The initial new fixture failed because it tried to seed an answer outside options (DB integrity correctly rejects it); replaced that test with malformed duplicate options. Another test fixture used a nonexistent mock kind column; corrected it to the actual collection-backed schema. Isolated tests cover issue filters, pagination, restricted subjects, exact alternate appearance, active-mock blocking and source formatting. Browser confirmed missing filtering, refresh persistence, alternate Q19/page4 and reordered choices arriving in the editor. A 360px viewport had body scrollWidth345px (scrollbar gutter), no horizontal overflow. Final TypeScript/Vite build passed; lazy admin chunk35.13kB, main496.93kB. Deployed API/static SHA256s match the local build; both sites returned final200. Synthetic test browser/services stopped and this session's abandoned fixture database was identified by its synthetic question IDs and removed. Evidence/docs mirrored privately to the server.

Remaining: this is review tooling, not answer adjudication. Last missing bank count remains1,652 unless a later data workshop changes it. First real correction awaits independent real reviewers. Module-comparison ingestion/adjudication, advanced source/taxonomy ingestion and remaining P08 release gates are still outstanding. User deferred mail and asked to focus on product/bank work.


## 2026-10-21 — complete exam rehearsal and learning rewards

User authorized the exam journey plus leaderboard/points, anticipating games and earned subscription access. Chose separate XP, reward wallet and contribution reputation. Added migration0034 (now applied), append-only reward ledger/unique question claims, opt-in board, dated Pro-redemption receipts, catalog version/audit controls and account exam checkpoints. New eligible verified correct question awards10XP+1point once across practice/mock, capped300dailyXP; no guests/derived/late-mock rewards. New published contribution-credit/reversal events append corresponding wallet entries. Rewards do not backfill all old attempts and do not turn account level into a permission grant. Catalog provisional1000points/7daysPro remains disabled; user was asked a preference but did not choose launch activation during implementation. Earning is deployed; no artificial live-user points or redeemed benefits were seeded.

Added /rewards, /board and Admin Rewards & points; profile/header/billing/scoring link real flows. Reward access is separate from paid subscription rows and shares account_has_pro across practice/mock/mistake gates. Wallet spending cannot reduce XP/rank. Public board shows only opt-in handle/XP. Redemption locks/idempotency prevent retry/concurrent double spend; cooldown30days, price version guards, expiry checks. Trial/reward access queues; active paid renewal blocks redemption. Future games must integrate the shared trusted award/cap contract; games/duels themselves remain unbuilt. Added docs/LEARNING-REWARDS.md with economic/abuse boundaries and operator policy.

ExamJourney provides open mock, prior results and account checkpoint continuation. Module practice now persists filters/page through URL and account checkpoint, renders source context/figures/links and avoids stale prior-page questions while loading. During actual synthetic browser20-question rehearsal, found the existing overlapping-start race: StrictMode's first request created a mock, the second showed409 and stranded it. Runner now rejoins the saved winner, including cross-exam route normalization. Also found that submit left results on /mock, so refresh could start a new session. It now navigates to /results/:id and recovers a saved receipt after a lost submit response. Result payload carries collection context; bookmarks show errors and stale collection reads are guarded.

Browser exercised bookmark/start/B pick/mark/next/reload (position2,1answer,1mark), submit (1correct,19skipped), permanent result refresh and wallet30XP/3points for three unique rewards. Continue practice URL verified offset10 after account save. Desktop/mobile proofs use synthetic accounts only;360px viewport body345px, no horizontal overflow. Saved test fixtures support ISM_REWARDS_DEMO=1. Initial selector waits briefly saw lazy-loading placeholders; resolved by inspecting fresh state rather than treating it as a functional failure. No browser console errors in the checked flow.

52 tests passed in7.55s with one upstream deprecation warning, including rewards executing under actual mpsc role. Frontend build succeeded; lazy-loading exam page reduced main JS from near500kB to470.72kB. Migration0034 rehearsed against real-data dump clone, applied, API/frontend deployed and hashes matched27API/17static files. Both study and family finalHTTP200. Bank stayed77751, strict12490, unchanged local/server bank hash9affc71fae6f…. Full enterprise gates, real bank adjudication/reviewers, mail provider, advanced module ingestion and games remain outstanding. Reports and documentation mirrored privately to server.


## 2026-10-21 — Content Studio, reader and creator economy

Implemented user-authored typed-block CMS using existing materials store and immutable revisions, separate approved-publication pointer, optimistic version guards, idempotent creation, account permissions/CSRF/rate limits and owner MFA review. Added /studio, /materials, admin Content CMS, notification links, helpful/studied/bookmarks/reports, canonical bank question blocks, free/Pro access and explicit paid-preview demo. Adapted Shikshacom block/settings/preview concepts after inspecting its full work-folder CMS; no arbitrary HTML or server content fetching. Independent first publication earns20XP+5points max once/day; self/demo/votes earn none, archive reverses once. Full details/limitations in docs/CONTENT-STUDIO.md.

60 isolated tests passed; real-data clone migration rehearsal clean; local frontend build passed. Browser synthetic draft/autosave/submit/review/publish/reactions refreshed successfully, paid preview desktop/360px captured. Separate reader was owner rather than outsider; outsider access verified by tests. Production staff MFA unchanged, fixture-only bypass explicit. Migration0035 applied; bank unchanged. Individual sales/payout/refund flows remain future work; no live charge or fictitious user publication created.


Deployment verified:29API and19static artifacts match production (reports/content-studio/deployment-artifacts.json). Live study API and shared family site HTTP200; paid demo API body redacted, payments disabled, private/no-store. Bank remains77,751/strict12,490. Live screenshot paid-demo-live.png. Documentation and evidence mirrored privately to the server.


## 2026-10-22 — Contextual material discovery

User accepted discovery as the next step. Read current CMS/feed/exam/subject implementations and v3 material/feed markup. Bank check showed all77,751 question/taxonomy rows in sync, bank SHA9affc71fae6f…. Existing catalog already supports exact collection_id/subject_id, so implemented a shared metadata-only three-card discovery panel without changing API/schema. Added For you feed, exam overview, LibrarySubject, English and Arithmetic/Reasoning learn surfaces. Catalog now retains context through its search/access/sort/saved/page queries and exposes back-to-context/clear controls; empty contexts link to editor with exact exam/subject preselection. Shared MaterialCard removes duplicate catalog markup and keeps demo/member labels/reader URLs consistent. Loading/error/retry and stale context guards are included. No fake content or bank changes. TypeScript/Vite build succeeded:100modules, main477.20kB gzip137.66kB; catalog13.99kB, editor22.46kB. No automated test suite run for this frontend-only packet. Deployment/browser evidence follows below.


Live discovery inspection found the preselected subject looked blank for a guest: the editor used account-only /review/taxonomy. Replaced that metadata read with public listTaxonomy subject facets (deduplicated by subject ID); server save validation still uses the canonical registry. Discovery navigation also resets scroll so opening View all from a long exam page lands at the catalog heading. No account or access permission was relaxed.


Final discovery deployment: main477.32kB (gzip137.69kB), editor22.49kB. Verified29API/19static artifacts match production; both study and familyHTTP200, bank77,751/strict12,490 unchanged. Live browser confirmed For you paid-demo card, LDC exact empty state and View all collection_id=ldc URL, English subject discovery and create link, and English selected in guest editor after public-metadata fix. Screenshots and release identity in reports/material-discovery; no synthetic publications, votes or saves created. No automated suite run this packet. Browser tab closed; no local services started. Evidence/docs mirrored privately to server.


## 2026-10-22 — Public creators, follow graph and safety

User authorized the proposed creator profiles/following feature. Read current profile/community/CMS APIs and v3 profile markup. Added pending0036 with opt-in profiles, unique follows/blocks, report queue and append-only events. Public API deliberately excludes private account name/email/progress/billing; profile visibility independent of published-material availability and existing contribution attribution. Following uses existing catalog published revisions,12/page and recent ordering. Blocks delete both-direction follows and hide creator/material routes while signed in; UI/docs explain public signed-out and other-product scope. No reward action added. Reports owner-only with staff MFA resolution and audit. New UI directory/profile/settings plus author links and real Following tab persisted by URL.

Initial14focused tests passed; full66tests passed, production-dump clone migration clean, frontend build successful. Synthetic browser ordinary outsider signed in and followed author; Following page retained publication after refresh. Native window.confirm stalled the browser driver, so replaced it with an explicit inline cancellable block panel. Created a fresh browser tab; document this trap rather than silently claiming native-dialog rehearsal passed. Final post-fix checks/deployment follow below. No real profile opted in or real graph data seeded; bank check77,751/taxonomy approved77,751 in sync, SHA9affc71fae6f….


Post-fix browser rehearsal used unprivileged outsider@example.test (confirmed on private profile), followed author (aggregate follower count1), saved public profile screenshot, loaded/refreshed Following material feed, blocked through inline confirmation (Following0, author in blocked list), unblocked (blocked list empty, Following remained0). Native-dialog tab closed through the selected browser core tabs API after wrapper close stalled. No production graph actions. Full suite66passed/1upstream warning in10.35s, migration0036 rehearsed against production dump and now APPLIED; never edit it.


Creator deployment complete: migration0036 applied, frontend/API deployed,30API and20static artifacts match local/server. Final build in deployment.txt: main478.68kB/gzip137.98kB; both study/familyHTTP200. Live graph counts public profiles0/follows0/blocks0/reports0 prove no real consent or synthetic graph seeded. Live directory shows honest opt-in empty state. Bank77,751/strict12,490 unchanged. Temporary APIs/Vite stopped and browser tabs closed; report/docs copied privately to server release folder. Final evidence reports/creator-profiles.


## 2026-10-22 — Publishing dashboard and reviewer/author handoff

User authorized the proposed admin publishing polish. Added owner-only derived work queue across corrections/materials/question/material/creator reports, explicit priority rules, search/stage/type/priority/order/page URL filters and exact source links. Replaced monolithic ContentAdmin with AdminContentReview: current-draft preview, immutable revision comparison, latest30events, inline reasoned decisions and report resolution. Author editor shows latest decision independently of autosave event history; notification links anchor to feedback. No workflow/permission/reward bypass or bank data changes. Added0037index for material-scoped event lookup, clone rehearsal clean.

Tests caught incorrect assumption that materials had created_at; fixed material age ordering to first immutable revision timestamp.70tests then passed (1upstream warning). Browser synthetic owner saw4pending items, inspected revision2 against published1 (2metadata/2block changes, edited heading and added callout), submitted requested changes, then ordinary author logged in and opened feedback through notifications. Browser exposed an older defect: /inbox pointed at missing /notifications. Added that route alias and real unread-count API/header updates; earlier docs claiming inbox ready were inaccurate. Latest feedback now remains available even after35later autosave events (integration assertion). Final tests/build/deployment receipts follow below.


Final predeploy suite70passed/1upstream warning in9.72s, including account unread decrement and private response headers. Frontend main479.10kB/gzip137.94kB; ContentStudio33.95kB and dashboard6.28kB lazy chunks.0037index APPLIED; never edit. Synthetic owner→author browser complete and tab/API/Vite closed; fixture-only MFA bypass did not alter production policy. Release deployment/health identity follows.


Publishing release verified:31API/21static artifacts match local/server; study and shared familyHTTP200, bank77,751/strict12,490 unchanged. Live /inbox redirects to the real /notifications screen and correctly requires sign-in for account notices.0037index applied, no production moderation decisions or bank content changed. Evidence in reports/publishing-dashboard, mirrored privately with docs to server. Browser tabs and disposable services cleaned up.


## 2026-10-23 — Resume Astra P03: module comparisons in admin

Implemented immutable intake and comparison workflow for old clerical/Prelims modules. Original crosswalk and answer-review CSV plus five clerical adjudication packets retained, with source hashes and current-bank recheck. The earlier normalizer removed punctuation and could collapse negative/positive numbers or English punctuation. Replaced with Unicode/case/whitespace-only normalization preserving operators and ordered options. Fresh current unique/ambiguous/unmatched: clerical1113/143/2083; Prelims455/1438/1522. Kept all6754records and7744candidate rows;42packet refs.97raw unique answer disagreements are not97proven incorrect answers.

0038audit tables, transactional hash-checked/replay-safe operator importer and TypeScript AST literal extraction avoid executing module code. Owner filters/list/detail/source/triage and linked contribution drafts/source requests reuse the normal review pipeline. Default editor keeps the current answer; explicit button proposes a derived module alternative. Separate registered official-key evidence remains required. Added contribution citation reader after browser review showed that reviewers otherwise had only the external module URL, not a usable immutable imported-record view. No automatic bank mutation, submission, approval or rewards.

First full suite exposed a fixture cleanup trap: synthetic mock submitted_at alone violates mock_result_complete, leaving an active mock and cascading409s. Cleanup now sets elapsed/correct/wrong/skipped/score coherently. During browser mismatch rehearsal, noticed the bank_changed flag incorrectly used module identity rather than imported bank identity; fixed it to compare imported identity SHA and answer/provenance, so an unchanged historical mismatch is not called a bank update. Regression added. Final75tests pass in10.01s with one upstream deprecation warning; build passes. Clone rehearsal clean, then0038applied. Browser disposable synthetic owner saved a draft with primary reasoning plus secondary module ref, reopened citation, confirmed linked intake and unchanged bank answer, and blocked historical sign mismatch correction. Full-page screenshot failed in this browser; viewport screenshots succeeded and were inspected.

Real immutable imports/replays succeeded:2runs6754items7744candidates;0production contribution links/events;6754open;0missing current exact appearances;42packet refs. No owner credentials impersonated, staff MFA changes or production dummy reviews. Bank SHA9affc71fae6f remains in sync,77751questions/12490strict scorable. Deployment artifact equality, shared-site health and private documentation mirror recorded in reports/module-intake; remaining broad gates and adjudication explicitly deferred.


## 2026-10-23 — Module disagreement research, batch 1

User asked next after intake deployment. The97module conflicts deduplicate to96bank appearances: ratio content occurs under two legacy paper IDs but one Excise target. Built a read-only bank/manifest-bound preparation script with typed Proposal validation and explicit unknowns. Independently researched20targets using primary institutional records and six inspected PDF-page renders. Results15proposed derived answer corrections,4retain-bank recommendations,1printed-option defect;76not independently source-reviewed in this batch.19prepared-only payloads comprise15answers,3context transcriptions and1defect. No actual contribution, approval, score or bank edit was made.

Source checks mattered: Course B mean is172 from150+160+170+180+200, vehicle residual June3.2hundreds is largest, ratio25/30 satisfies both ratios, while Assistant work-rate gives8.4days and no listed exact option. Do not select nearest8.5. Archived provisional Series-A key Q23 isD; moduleA is wrong, and bank text omitted the four-part list. Primary PIB records support correction of INSPIREvenue and other historical facts; four retained answers show modules are not peer authorities. The MPSC index loaded initially, then403 on later fetches; do not claim a newer final key was verified. Historical current-office questions are evaluated at exam time.

The initial builder rejected the defect case's null proposed answer because integer validation was too broad; confined it to actual answer/retain outcomes and tested no-answer defect semantics. Initial frontend build caught a nullable detail placement outside its guard; moved assessment panel inside selected article before deployment.78tests pass/1upstreamwarning in11.04s, including3new builder cases for dedup/no bank writes, unknown/retain/defect behavior and tampered/stale inputs. Build and synthetic browser research panel inspected; screenshot clearly marked synthetic.

Two new immutable audit runs attach full docket and research packet, preserving original runs. Latest cohort still6754records/97raw disagreement rows; historical totals4runs13508items15488candidates. Live SQL confirms20researched targets with15/4/1 outcomes and76pending, zero production links/triage events. Frontend-only deployment, exact artifact identity and shared-site health recorded in reports/module-adjudication-20261023. Research payloads remain prepared/not submitted; real independent review still required. Next research batch76targets; bank missing-answer work and broader release gates remain.


Batch1 final release:33API/23static artifacts match server,study/familyHTTP200,bank77751/strict12490unchanged. Research panel browser proof is synthetic; real imported research counts were verified by read-only SQL. Local/server docs,evidence and preparation scripts mirrored privately in /home/ubuntu/ism-release-reports/2026-10-23-module-adjudication. Disposable browser/API/Vite stopped and staging removed.


## 2026-10-23 — Retire remaining difficulty authoring

User confirmed difficulty is no longer part of the product. Found the leftover in admin taxonomy links/editor: Tags & difficulty and a three-value selector. Learner question cards already did not render it and mocks/rewards did not use it. Removed selector and implicit difficulty field from taxonomy saves, renamed actions Subject & topic tags, removed unused learner type field, deprecated API compatibility property, and labeled immutable history as retired metadata. Existing DB columns/sync/snapshot hashes are retained to avoid corrupting historical reviews or bank ownership.

New create/revise requests reject difficulty including null; idempotent replay checks precede the new-authoring guard. Older proposals remain parseable/readable, but any actual difficulty change blocks evidence validation until revised without it. Two integration tests cover all three labels/null, successful classification-only drafts/revisions and reading/revising historical records.80tests pass/1upstreamwarning in11.83s; build and synthetic author editor browser confirm subject/topic/subtopic with no difficulty control. No data migration or bank edit. Full deployment/artifact identity/shared-site health and docs mirror in reports/retire-difficulty. Next concrete implementation opportunity: source-preserving prepared-research→draft UI, with explicit user action/live baseline check and independent review retained.


## 2026-10-23 — Prepared research drafts and consistent answer-card layouts

Implemented owner Create correction draft from immutable module research, not a URL-supplied answer or automatic submission. The server checks payload/packet hashes, research-vs-run bank checksum, completed-sync checksum, assessed identity/answer/provenance, candidate membership and the current full bank snapshot. Reused normal author limits, CSRF/MFA, active-mock gate, typed evidence and publication workflow. Deterministic actor/payload identity makes concurrent clicks and duplicate module appearances reopen one draft. Links use sorted locks; one prepared-research event, no bank mutation. Existing closed contributions reopen their detail rather than an unusable edit screen.

Fixed a related editor data-loss issue: only the primary citation was loaded/saved before; secondary citations now survive subsequent edits, remain visible, and external primary references are not silently relabeled as module references. Browser created a synthetic prepared draft, edited explanation, saved revision2, and verified all3citations plus draft/zero decisions. No real owner account was used. New3integration cases cover concurrency/replay/cross-appearance identity, exact citations, unchanged bank answer, permission/hash/stale-context/stale-sync/dismissal rollback and active mocks. Final83passed/1upstreamwarning in12.18s.

Inspected legacy clerical PracticeView/ExamView/GroupBPaperLibrary, Combined CSS, MPSC QuestionCard and separate Practice Hub2 CSS plus live source cards. The separate PH2 actually uses a list; Combined uses2columns, while MPSC browse also has2columns. Corrected the earlier broad assumption that every hub used2columns. Keep both choices: defaultA/B thenC/D at640px+, List toggle and single-column narrow fallback. Saved choice is browser-local and does not call the bank. Shared across modules, bank/detail/paper/mock, Arithmetic and subject/community practice. Calm warm options, explicit letter chips, blue selected/green correct/red wrong with words or symbols; no early mock reveal or difficulty feature. Source global yellow/grid-paper theme was not copied.

Browser measured437.797px×2 versus885.594px×1, unchanged A–D content and revealed result while switching, remembered List after refresh.360px viewport fell back to251px×1 with no overflow. Pressing Tab viaAX was reliable where Playwright exact checkbox/label names did not match toggled-button roles. Public legacy inspection submitted no source answers; synthetic answer checks only in the disposable DB. Full local build passed and artifacts deployed; evidence/docs reports/research-drafts-answer-layout. No migration, bank data change, real draft/approval or scoring change. Broader review/research and release gates remain.

New evidence pointer found while checking legacy UI: it links a2025Combined final-key archive PDF. This release did not verify mapped final cells or change provenance; future research should inspect it before retaining the earlier provisional-only assumption.


Final live read-only browser checks: LDC/UDC/non-gazettedGroupB each503px×2 and Combined532px×2, all4ordered options; screenshots saved. GazettedGroupB explicitly shows137written departmental questions/no verified keys, so no MCQ grid there. No live answers/drafts/votes submitted.33API/23static artifact identity and study/family health verified,bank77751/strict12490unchanged. Disposable fixture API/Vite and all temporary browser tabs closed; private server mirror includes docs/evidence.


## 2026-10-23 — Queue next bank-answer audit

User asked to keep the next bank work in the to-do list. Added a specific queued audit to `docs/PLAN.md`: inspect the Combined Prelims 2025 final-key PDF pointer found during legacy-module inspection and verify exact paper/series/question mapping; continue research across the76distinct module-conflict appearances; remeasure the objective unanswered count before resuming the backlog (1,652 was the last reported figure, not a fresh count); and keep descriptive questions visibly identified in paper views without treating them as missing MCQ keys. No source PDF cells or answer claims were verified or changed in this documentation-only update. Mirror the plan and devlog to the private server notes.


## 2026-10-23 — Question discussions and source-preserving sharing

User authorized the proposed shared discussion/share workflow. Inspected existing read-only community feed, posts/reply/vote/report/moderation schema, current correction editor and v3 discussion markup. Added pending0039 for immutable post content/context/references, replay keys, explicit uncheckable-question disclosure, append-only discussion events, notification references and bounded thread/feed indexes. Implemented shared canonical threads with account/CSRF/rate limits, first-three-approved moderation, flat paginated replies, helpful feedback, asker-only acceptance, conduct reports, withdrawal, existing block/mute/lock enforcement and active-mock protection. Feed reuses those approved topics and gates; no duplicate question or feed post. Owner session/MFA moderation delegates to the existing conduct service; own approval denied. Generic transactional reply/acceptance notices avoid answer excerpts.

Inline actions cover existing QuestionCard users (including Arithmetic/Reasoning/subject practice), exam browser, paper viewer and question detail. Share URLs retain paper/exam and fall back to a copyable input. Published discussion/source citations prefill the existing correction editor while retaining the bank baseline and all later citations; no automatic answer, submission or reward. Fixed deep-link focusing so only the matching topic expands, and included focused replies beyond the page. Removed the check-answer control for no-key detail pages so those users can explicitly open discussion instead.

Meaningful isolated integration suite now91passed/1upstream Starlette/AnyIO warning in14.09s. Coverage includes concurrent retry, publication visibility, source/context validation, disclosure without attempts, acceptance/votes/no rewards, transactional notifications, block/feed/citation filtering, five-report auto-hide/dismiss, muted-account guards, locks/withdrawals, immutable content/events, session-owner MFA/self-review and active-mock moderation. Clone rehearsal applies0039cleanly. Browser synthetic author accepted/helpful-voted a reply and copied the contextual URL; saved an unsubmitted correction draft with3evidence entries; posted a new pending doubt, approved it as synthetic owner and found it in the author's feed.360px viewport document width345/no overflow, direct reply expansion checked. Browser caught a Vite lazy-import temporal-dead-zone error despite a passing TypeScript build; moved initialization after the React import. Its password autofill also replaced the synthetic email during account switches; filling email last and checking private profile identity resolved the rehearsal trap. Production staff MFA was not changed; fixture-only CMS flag permits disposable owner actions.

Local/server bank check still77751questions/all77751taxonomy approved, SHA9affc71fae6f in sync. No bank content change or real production post/vote/correction/moderation action. Deployment/health/artifact receipts and cleanup follow below. Bank final-key/76conflict/unanswered-answer research stays queued; broad release gates remain outstanding.

Final discussion release:0039APPLIED after second final clone rehearsal; never edit it. Hardened the session-owner wrapper so grant checks/locks and moderation query/action share one transaction; existing bearer endpoints delegate to the same implementation. Final91tests pass/1upstreamwarning in12.28s.33API/24static artifacts match server after final API deployment; study healthy77751/strict12490, family root307followed to final200, bank source unchanged/in sync. Live LDC thread gate/actions inspected without answering or publishing; no new production request-key posts/discussion events/notices (all0). Production copy button reports Link copied; browser clipboard helper returned its old localhost buffer, so only the synthetic clipboard content was directly confirmed. Report records that limitation rather than claiming OS verification. Temporary fixtures/tabs and final private local/server documentation mirror are cleaned up below.

Cleanup complete: disposable fixture API exited0and dropped its database; Vite stopped (expected130), temporary viewport reset and both verification tabs closed. Final notes/evidence mirrored privately to `/home/ubuntu/ism-release-reports/2026-10-23-question-discussions`, with checksum comparison after transfer. No commit/reset/cleanup of unrelated checkout work.


## 2026-10-23 — Complete private Study Desk v3

User asked for the v3 Study Desk and explicitly approved private invitations while discovery/classes remain off; email delivery stays deferred. Compared saved source and the actual Claude Desk prototype. Replaced browser-only partner preview with the actual illustrated six-seat scene, seven v3 content tabs and account/private-room workflows. Copied scene geometry rather than generating a different illustration; removed fictional members/activity. Lazy loading keeps the main bundle below500kB. Personal plans, notes, saved/recent canonical questions now have account-bound CAS storage, retained local failures, explicit import/export and conflict resolution. Detail Save is disabled during initial account hydration so clicks cannot pretend to persist.

Added pending0040 for membership/invitations/resources/chat/focus/reports/audit. Exact-handle invitations have seven-day expiry, daily limits/decline cooldown, idempotence and a room lock for concurrent last-seat acceptance. Joining free, Pro creation, settings/removal/transfer/close/leave and block cancellation are wired. New members see current resources but only post-join chat. Progress/mistakes/focus visibility begins off; own answers remain in the bank engine. Inline shared questions avoid mandatory bank navigation. Server-time focus sessions cannot be completed early and award no points. Scoped owner/MFA reports retain exact versions and do not allow browsing private desks. Hourly bounded cleanup preserves unresolved evidence, redacts resolved evidence after180days and purges closed resources/chat after30days.

Initial full suite exposed test-order contamination: an existing outsider had earned Pro in reward tests. Replaced the free-plan assumption with an isolated synthetic account. Later review found old open reports excluded by a retention timestamp despite evidence being retained; removed that query gate and asserted queue visibility. Restricted edits now honor posting sanctions while withdrawal/exit remain available. Formatted the new Python files using a disposable formatter environment without adding runtime dependencies. Final test/build/deployment results follow below.

Disposable browser verified personal goal/checklist save and reload, private note persistence, exact-handle invitation send/accept as another free account, no personal data leak, no pre-join chat, inline question rendering, recipient chat, focus start/reload/pause/early ending. At360px documentwidth345px: no page overflow; scene has its own scroll. Screenshots are clearly synthetic; no production owner impersonation or seeded private activity. Clone rehearsal applied0040cleanly with production untouched. Bank77751/strict12490and SHA9affc71fae6fremain unchanged. See docs/STUDY-DESK.md for delivered scope, private rollout exception, retention, flag rollback and deferred discovery/classes/partner graph/games/email/erasure. Deployment, live health/artifact and private mirror receipts follow.

Final private desk release:101isolated tests pass/1upstream Starlette warning in22.96s; local build passes (main471.92kB,gzip137.96; lazyDesk60.64kB,gzip17). Pre0040private pg_dump saved,0040APPLIED after clean clone rehearsal; never edit it. Enabled only STUDY_DESKS_PRIVATE_ENABLED=true while preserving root-only environment/MFA.35API and26static artifacts match the deployed server byte-for-byte. Study health77751/12490and family finalHTTP200verified, no pending migrations, bank IN SYNC. Production new room/item/message/report counts all0before real use: synthetic fixtures were never deployed as user activity. Read-only live browser shows the real scene, seven tabs and guest-only local saving with no browser errors. Additional synthetic UI report submission→owner scoped snapshot→dismiss verified; no private room browsing granted to moderator. Final account read requests are generation-bound and failed hydration clears prior identity/data, preventing stale account-switch responses. Public discovery/classes remain disabled. Cleanup and private mirrored docs/reports complete this delivery.


## 2026-10-23 — Next queued bank audit:2025final key

User said go next after the private desk release. Chose the explicitly queued final-key/gap audit. Used the PDF skill to render and inspect all8pages plus printed flagged question pages. Web/index/direct-web fetch returned403; a first30-second curl downloaded only1.9MB. A longer direct officialGET completed, SHA32238c9873959c8e41cf5ccea84a6f8dde46c5216808f76c2e9c0a9569358563, identical to both legacy archived copies. Added the verified PDF as a bank source asset without editing bankJSON. All800manualcells compared against legacyOCR:21unparsedcells and PaperII-A23A→D; currentbankDretained. Eight keycells are Compensated, six represented in currentbank.

Read-only comparison of514existing2025appearances found505matchingcells,3differentanswers and6compensated records.505is not505verifiedquestions. Individually checked the9flagged stems/orderedoptions/printednumbers; Q96I-A actuallyPDF15not14, Q41II-C actuallyPDF7not6. The latter expression is5^(2x+1)÷25=125, x2, whereas bankstem lost itsmath and inferredanswer6. Other answer changes I-B15B→A andI-B30B→C. Prepared12normalpayloads:3answer/6defect/2locator/1transcription; source-reference evidence must be reference-kind because official-key validation correctly rejects its new answer against an unchanged old baseline. Rebase companions after publication. No nearest-option guessing or fake module mapping.

Live reads confirm all6compensated appearances stillstrictscorableandnotflagged. Do not claim this audit fixed them: normal independent review/publication remains necessary. ExactbookletsverifiedfromPDF, butappearance.seriesisnull; scopedkeyregistrationsandexplicitnotespreserve currentcontract. Four final-key docs registered without answer/key mutations. NewimmutableCombinedrunmar_c773511b512fbe756278e34ff3707d17retainspriorbatchresearchandnew9assessments. Eighttargets exactcandidates inintake; Q41II-Cunrepresented,its3payloadsremainordinarydirectcorrections. Oldrunsremain;importreplaychecked.

Freshbankmeasurement1652invalidMCQindexes(1543minusone/109null),7973descriptive. OfmissingMCQs1538have4options,64have2,47have0,2have5and1has8.2025alreadyhadanswers,soblankcountunchanged. Addedread-onlyreproducibleauditbuilderand3syntheticfixturetests(hashmismatch,missingcells,nocompensationletter,typedpayloadhashes,nobankmutation). Initialtestsusedrealdata;replacedwithisolatedsyntheticinputstopreventCIdependenceonchangingbank. Final104passed/1upstreamwarningin16.20s. Packetgenerationdeterministic,bankSHA9affc71fae6funchanged/INSYNC,health77751/strict12490andfamilysitechecked. No productionauthor/reviewer impersonation,contributions,approvals,pointsorlearnerattemptschanged. Evidence/docs mirrorprivatelyto2026-10-23-bank-final-key;nofrontend/APIproductcodechangeordeploymentneeded. Temporaryimportstagingremovedafterverification.

## 2026-10-23 — V3 avatar editor and saved account identity

User requested the edit-avatar system and then continued the work. Inspected v3 editor1839–1917, avatarEl2718–2743 and catalog3071–3098. Built launch-mode Customize/Inventory with the original vector face/hair/accessory geometry,168px preview, seven categories, actual account identity and catalog selections. No generated bitmap, external image service, shop balance or sample badges.19starter choices are free;7cosmetics use the existing real XP level5/10/15/30thresholds. User Save claims eligible level items permanently without changing XP/reward points; reset returns to initials and retains ownership/history. Existing users are not force-customized.

New0041adds nullable avatar/version, immutable avatar events and durable earned-item rows. Strict curated payloads reject arbitrary URLs/markup/ownership/XP fields. Account/CSRF/body/rate guards, user binding and row-locked CAS protect saves; retrying the same already-saved look returns its version. Different concurrent saves produce200/409. Owned level items survive a synthetic XP reversal; inaccessible future items remain rejected. Single JSON catalog lives under API data. Reuse saved config in own session/profile, creator cards/profiles, materials, feed/discussions, boards and desk chips/profile/scene; no avatar lookup directory or per-avatar request loop. Existing audience/block rules apply, including withholding blocked members' avatar values. Unique React clip IDs avoid the source prototype's same-size SVG collisions. Header/editor async reads are generation guarded. Save events also refresh personal-desk identity, which otherwise remained stale after navigating from the editor.

Browser synthetic author chose Long/Teal, saved, refreshed, checked inventory, reset to initials and restored; header changed immediately, private desk scene/chip/profile matched.360px documentwidth345/no page overflow. Screenshots explicitly synthetic. No real owner credentials or production avatar mutations. Five new integration cases cover persistence/projections/no reward mutation, curated/session/CSRF/level/account guards, concurrent conflicts/replay/reset/event immutability, durable unlocks and creator/desk visibility blocks. Initial anonymous test expected401without X-Device-Id; the existing identity dependency correctly returned400before account auth. Fixed the fixture to send a proper synthetic guest device before asserting401. Test-only quoting in the added desk fixture was repaired before final validation. Final109passed/1upstreamwarningin14.66s; local build passes, main~475kB and lazy editor separate. Clone rehearsal applies0041cleanly. Private pre0041dump taken. Migration application, API-before-web deployment, artifact/health receipts and local/server docs/evidence mirror follow. Shared Caddy remains untouched; bank answers/counts unchanged. See docs/AVATAR-EDITOR.md for actual scope and remaining shop/upload work.

Avatar release receipt:0041 applied with checksum6811b7d2d11257f9; all migrations current. API deployed before web.38API Python/catalog files and27web files match local SHA256s exactly; study health77751questions/12490strictscorable, family site follows to200. Bank/taxonomy remain IN SYNC. Live guest /avatar renders all seven categories and Sign in to save; no browser console errors. Saved final synthetic desktop and live guest evidence. Temporary fixture API exited0/dropped disposable DB, Vite stopped, both verification tabs closed and viewport restored; user's Claude tab remains. Private local/server docs and evidence mirror at /home/ubuntu/ism-release-reports/2026-10-23-avatar-editor, preserving pre-0041.dump. No real user avatar saves were performed by this release verification.

## 2026-10-23 — Clarify question entry and unify discovery

User approved Open question and a single conversation across card/question/Community. Existing code already had canonical inline threads, feed links, correction handoff, moderation and mock gates. Renamed the vague Details action with lower prominence, opened the dedicated page's existing discussion by default, and linked expanded inline discussions to Community Questions & Doubts. MCQs remains community-authored practice, not a second discussion store. Added All discussions/Doubts/Unanswered filters with query-string URLs; legacy tab=doubts maps to the Doubts filter. Server unanswered excludes only published replies visible through bilateral blocks and ignores hidden/pending/obsolete replies, keeping the existing answer/disclosure and active-mock protections. No count-per-card requests or fabricated activity counts. Suggestions still enter ordinary independent review.

Nine focused discussion integration tests pass, including the new unattempted-user/pending/approved/hidden/blocked-reply and explanation filtering case, plus active-mock suppression on the new filter. One upstream AnyIO warning persists. Browser synthetic author confirmed existing topic appears in discovery, replied topic disappears under Unanswered, discovery opens that exact topic and bank inline expansion stays at /bank. No browser errors. Screenshots use disposable fixture data only; no production posts/answers/users were created. Build/deployment and mirror receipts follow.

Release verified: API-before-web deployment completed;38API/catalog files and27web files match local SHA256s. API health77751questions/12490strictscorable; family.hawayu.in final200. New production questions/unanswered API returns200 behind the same disclosure gate; live UI shows the selected filter and accurate empty state, no console errors. No schema migration required. Local synthetic fixture stopped/dropped its database, Vite stopped, temporary browser tab closed. Notes and evidence mirrored privately to /home/ubuntu/ism-release-reports/2026-10-23-question-discovery; bank content unchanged and pre-release sync check IN SYNC.

## 2026-10-23 — Exam calendar and official notices

User approved calendar/notices and asked to inspect work repositories. Read Shikshacom teacher CalendarWidget, admin QuestionsAndNotices, backend Announcement and studio CalendarView. Adapted Monday-first navigation, lifecycle/editor patterns and derived countdown; kept v3 calendar1618–1675geometry. No source repositories changed. Implemented versioned0042event/history/saved/preference schema; public dates/notices, registered own follows/saves/reminders, owner publication/revision/withdrawal and history. Reuse exam bookmarks and inbox. Bounded60second worker with unique per-event/version/user/phase receipts, India-day7/1/0 reminders,7day update/withdrawal window; no email/push or external writes. Source URL/date/field constraints, body guards, staff MFA/CSRF, concurrent409s, immutable snapshots and nonpublic collection filtering. All-day RFC5545 and Google links preserve exclusive end dates; imported copies don't auto-update.

Main MPSC site returned403; official application portal initially rendered Empty Data, then loaded actual advertisements. Saved rendered DOM/screenshot. Verified15departmental9Nov2026deadlines plus passed LDC12Oct/Peon13Oct:17starterrecords. Explicitly label departmental eligibility and unknown exact closing times/exam dates. Only exact LDC maps to its existing collection. New reviewed manifest/technical importer validates evidenceSHA, never updates an existing ID and logs nullable technical actors instead of impersonating owner. No synthetic seed accounts or dates in production packet.

Initial build caught ES2020 replaceAll incompatibility and an unrendered lazy admin import; fixed with regex replacements and actual owner tab rendering. First calendar test assumed bookmark response.items instead of collection_ids; corrected fixture contract. Test-only private visibility was invalid (schema uses hidden), corrected. Four calendar tests then passed;114fullsuite passed. Added importer replay/hash protection and published→draft guard, then a full-suite run exposed accumulated owner write budget429in an unrelated discussion test. Reset only disposable per-test rate buckets in conftest, preserving real within-test rate-limit checks and production limits; final run recorded below. Browser synthetic author verified follow/save/reminder persistence and actual worker-delivered inbox2alerts; exportedICSdates30→31Oct/exclusive end and75octet folding checked. Owner browser updatedv2/history and withdrewv3; public permalink says Withdrawn and month removes it.360px documentwidth345/no overflow, viewport restored. No browser console errors. Migration clone rehearsal passed; backup/deployment and mirror receipts follow. See EXAM-CALENDAR.md for explicit scope and operational limits.

Final release:115tests passed/one upstreamwarning in20.80s.0042applied with checksumdb7cbcc8514c907c; no migrations pending. Private pre0042dump26,892,847bytes,mode600. API-before-web deployment completed. A final admin header copy edit initially nested a ternary inside a quoted string, and the local build rejected it; fixed the JSX before shipping web. Technical intake dry-run initially ran as postgres inside ubuntu's unreadable home and could not stat .env; reran from /tmp without reading credentials. Applied17verifiedrecords; replay inserted0/existing17, preserving staff edits. No synthetic production users or owner impersonation.40API/catalog files and29static files match local hashes; health77751/12490, family.hawayu.in final200. LiveNovembercalendar shows15actualdeadlineentries on9Nov, source/verification notes and Google/.ics actions; no console errors. Worker journal has no calendar-sweep failures; observed0opted-inaccounts/0calendarinboxrows. Source coverage is explicitly starter-only. Final visual pass aligned date contents at the top and used the reference's cream calendar surface. Temporary fixture exited0/dropped its DB, Vite stopped, viewport reset and agent tabs closed; user's existing tabs remain. Final docs/evidence are mirrored privately under2026-10-23-exam-calendar, preserving the backup outside child report syncs.

## 2026-10-23 — Games and global search

Continued the requested v3 games and search work. Added durable server-owned Gauntlet/speed/duel/private multiplayer/weekly cup modes and audience-aware grouped search. New0043 adds room/member/answer/cup/events and request replay tables, immutable snapshots/choices and game context using existing canonical XP claims. Strict source appearance/text/options pairing prevents importing another appearance's formatting. Canonical rows lock in sorted order at finalization; changed identity/key/source context excludes an answer. Active mock/game locks and disclosure gates apply across direct bank answers and community. Shared existing300XP budget; no fake currencies, awards, people or production fixtures.

Initial local browser fixture failed canonical answer_text CHECK because synthetic options did not match B; corrected fixture A/B/C/D and restarted. An early browser login500 was the proxy while API was not ready. First party lobby expired during the long inspection; created a new room and verified two synthetic accounts join, nonhost has no start, host starts both. Gauntlet preserved100m after refresh and ended after three wrong answers; speed saved10correct and review after reload. Own private note appeared only for its author; account switch cleared private state. Viewport override calls reported success but DOM remained1280px: mobile screenshots are not proof of mobile support, and physical mobile checking remains open. No real users, posts, attempts or points were created.

Final full suite123passed/one upstream AnyIO warning in22.94s; final0043 rehearsal applied cleanly on a production-data clone and dropped it. No bank data changed. Deployment, hash and live receipts follow. See docs/GAMES-SEARCH.md for actual scoring, privacy and limits; public-load tests, real Sunday observation, future upgrades/map/prizes and full marketplace remain unclaimed. MPSC collection stays a human-reviewed backlog item, not a scheduled automation.

Release receipt:0043 applied with checksumb1b64432b7c7f89e, no migrations pending. Pre0043private dump26,926,245bytes/mode600. API deployed before frontend;42API/catalog and31static files match SHA256 exactly. Live health77751/12490; games359ms, grouped English search451ms (10852question matches), LDCexam search213ms in single external checks, not capacity benchmarks. Read-only production draw returned25questions/25matching appearances/25source PDFs; no production games/cups/answers observed. Worker journal contains no game failure entries. Family site final200, shared Caddy unchanged. Live games and header search verified without signing in or playing; clean live browser error log. Standalone operator probe initially omitted pool startup, then used config's default bench instead of service PG environment; corrected to PG environment and explicit read-only transaction. First HTTP probe had a non-UUID device id and correctly returned400; fixed the probe UUID. These were probe errors, not application failures. Final screenshots and notes mirror privately under2026-10-23-games-search; backup is preserved outside child report syncs.

Cleanup: disposable fixture exited0 and dropped its database; Vite stopped; temporary browser tabs closed and viewport reset. Final diff whitespace check passed.

## 2026-10-23 — Subject-first Library and flexible reviewed topic paths

User approved direct subject discovery, flexible question classification and a visual database view. Added0044 secondary-path table/approved view/direct shelves without changing primary classifications or bank answers. Geography maps existing GS geography; History combines Indian/world; Economy includes Economics and GS economy. Library Subjects precedes Modules & tools, with direct shelf practice/browse/notes/discussions, ten-result pages and optional exam/year/origin/provenance/progress filters. Source cards retained. Owner-only visual map gives real table counts, connections and missing-topic coverage. Current Affairs explicitly uses original exam year.

Secondary links are explicit relatedClassifications, separate from parked alternative claims; no automatic backfill or confidence promotion. Extended normal taxonomy proposals, validation, multi-subject reviewer/publisher scope, export manifest nodes, local bank transform/receipts/reversal, CSV and both transactional sync paths. Server never edits bank tags directly. Approved paths feed filtering/search, section counts, mock selection and games; category progress stays primary to avoid multiplying totals. Distinct question counts handle overlapping paths. Private audience/block/mock/game gates still apply to subject notes/discussions. Note creation prefills the shelf tag; paid bodies remain redacted.

Initial isolated tests used nonexistent collection_papers.position and attempts.chosen_index columns; corrected fixtures to actual collection membership and chosen_text contracts before final validation. Six focused cases pass, covering secondary/pending paths, distinct counts, account progress/private exams, cross-subject scope and manifest export, bank-file replay/CSV/reversal, owner map privacy and notes/discussion audience filtering. Full129passed/one upstream AnyIO warning in26.76s. Migration rehearsal passes on production-data clone; final build/browser/deployment receipts follow. Browser's first click during HMR timed out; refreshed state and retried the same Notes action successfully. No production learner data, answer keys or bank classifications have been changed by this release.

Added a seventh integration case that executes the actual secondary-link sync SQL with exported CSV. It caught an insertion error: the related block appeared twice in classification-only sync and was absent from full sync. Moved it to one correctly staged block in each path before any production application. The case checks positive import, removal, missing-target rollback and unchanged attempt counts. This strengthens coverage beyond CSV serialization alone.

Full-sync integration tests then caught a staging-path compatibility error: copying secondary CSV inside APPLY retained /tmp/bank-csv in tests that correctly relocate only setup. Moved CREATE/COPY into setup alongside existing CSVs, leaving link application inside APPLY. Final130passed in26.87s. Browser inspection also found null topic matching root taxonomy nodes as subtopics in the existing editor; constrained selectors to the actual topic/subtopic levels before shipping.

0044 applied from checksumcd9ca85fd2f2e9e0 after a26,970,937byte private backup/mode600, then API-before-web deployment. Live read checks confirmed Geography942total/936answerable, History1204 and preserved bank77751/strict12490. They also exposed ~4.3s question/taxonomy responses and3.75s collection catalog after the first release. Did not accept that regression: prepared new0045 UNION ALL view (disjoint primary flags/source uniqueness), set-based shelf matching, one-pass facet totals and removal of unused count joins. No edit to applied0044. Added exact paper-year regression after checking that first/last-year intervals could include years without an actual printing.37focused publication/game/library tests pass after these changes; final full-suite and production timing receipts follow.0045 clone rehearsal applies cleanly.

Final hardening: the collections query's old primary-only baseline already took3.18s; the new all-path query was3.2–3.9s. JIT was absent and disabling it did not help, so no global settings were changed. Split subject/topic lookup into indexable lateral branches and use EXISTS for paper classification. Read-only production comparison returned the identical60-row result hash and reduced execution to1.37s. Added overlap/exclusion/scorable-count regression coverage. Its first fixture read scalar sections instead of section_list; corrected the test to the documented API field. Reviewer permissions now expand only when tags change, so existing related tags do not prevent primary-subject answer reviewers from doing their work. Empty, reordered and equivalent primary-path proposals are rejected as no-ops. New related path payloads normalize optional fields/order without changing old primary-path serialization. Final full134passed/one upstream warning in30.96s; latest32focused review/library tests pass in5.23s after semantic no-op comparison. No production corrections, votes, posts or learning attempts were submitted.

Bank workshop question2.0schema now declares optional relatedClassifications, and docs/RELATED-TOPIC-LINKS.md records preservation/review rules for future data models. Bank JSON/taxonomy data remains unchanged. Browser confirmed live Geography936practice/942browse, original question/source cards and no errors; synthetic owner map/related editor/notes screenshots use test data only. Full-page browser capture failed twice; used the supported viewport screenshot method, so proof files show the visible viewport. No physical-mobile or load certification is claimed.0045 has its own26,983,036byte/mode600backup and clone rehearsal, and applied0044 was never modified. Final live timings, SHA verification, migration status, cleanup and private mirror receipts follow.

Final receipt:0045checksum9895592870e109f8; no migrations pending. Final134tests passed, plus32focused latest review/library cases. Latest frontend build includes immediate request-generation invalidation on account changes, preventing an old audience-filtered response from appearing after switching accounts.44API/catalog and32web artifacts match local SHA256s exactly. Final single HTTP observations: Geography practice405ms/936questions; Browse400ms/942; actual2020paper-year filter406ms/25; taxonomy898ms; exam collection catalog1.663s (down from3.48s). Health77751/12490 and family site final200. Bank/taxonomy IN SYNC. New related paths remain0 and seeded subject shelves8; no production classifications or answers were inferred/modified. No API worker error entries observed. Synthetic fixture exited0/dropped its DB, Vite stopped, temporary browser tabs closed. Private notes/evidence/scripts and bank metadata contract are mirrored under2026-10-23-library-topics; pre0044/pre0045dumps remain outside child report syncs. Physical mobile and load verification remain unclaimed.

## 2026-10-23 — Unfinished mock recovery and Mizoram launch focus

User reported Games blocked on an unfinished mock without a resume provision, then confirmed launch includes existing Mizoram recruitment papers. Added private Games metadata/banner with exact section/paper/answer-mode resume URL, disabled starts until submission and recovery after another-tab conflict. Isolated browser author resumed an expired derived section mock, reached saved result and returned to enabled Games. No production accounts/attempts were impersonated or modified.

Read-only source audit found all1,938papers in Old_Questions: Direct1179/Direct_NG84/Departmental386/LDE289.0046 introduces explicit paper/collection scopes and launch views while retaining canonical global views. Scoped learner question/source/exam/library/mock/game/search/home discovery; existing account history remains. Header focus and always-visible shelf exam filter expose scope. Import CSV/full sync preserve registered scopes for legacy records; new imports require explicit scope. Community papers explicitly assign Mizoram. Test DB defaults are fixture-only; production has none.

Full-suite run initially exposed two retired-difficulty tests proposing a bare English classification equivalent to existing English. The previous semantic no-op hardening correctly rejected these. Changed fixtures to an actual Mizo tag edit; production no-op protection unchanged. This corrects the coverage gap after the preceding release's final focused-only semantic patch. Final136passed/one upstream AnyIO warning in25.71s.0046 clone rehearsal passed. One browser navigation used /library/geography and correctly showed404; use the existing /library/topics/geography route. Final build/deployment/live/mirror receipts follow. See docs/EXAM-FOCUS-AND-MOCK-RESUME.md for actual boundaries and remaining limits.

Release receipt:0046checksum411aaf87923c3031, no pending migrations. Pre0046backup26,983,079bytes/mode600. API-before-web deploy completed;44API/32static hashes equal. Production paper/collection defaults are absent, all1938papers/eightcollections assigned, global/launch77751all/67026practice/12490strict equal. Correct Geography shelf_id probes936/942 at0.873/0.743s; initial shelf parameter probe measured full bank, and corrected first request omitted deviceUUID/got400. Both probe errors are documented. Live LDC Geography filter gives13questions and persists collection_id URL; browser error log empty. Worker queue empty, no recent API error/traceback entries; first server journal command lacked rg, reran grep. Family follows redirect to200, shared Caddy untouched. Fixture exited0 and Vite stopped, temporary tabs closed. Updated deployment receipt utility now hashes every numbered migration instead of only003x. Private docs/reports/scripts mirror accompanies backup.

## 2026-10-24 — All exams, unified Inbox and Astra game specialization plan

Continued user's All exams request plus Inbox implementation and future game specialization planning. Added typed explicit exam_scope across public question/exam engines while preserving Mizoram default, global canonical source truth and existing eligibility/privacy gates. Header preference/URL selection reloads to clear pending requests; document scope is frozen to avoid cross-tab relabelling. Current production archive is all Mizoram, so identical current totals are expected. Games remains launch-only; UI says so. No bank data or keys changed.

Read Shikshacom work backend notifications models/views and v3 Inbox markup1064–1114. Implemented actual Inbox over existing notification rows and private desk chat.0047 backfills categories/adds silent preference handling/read cursors without erasing history. Bounded notification and thread pagination, category/unread, idempotent read/unread, snapshot read-all, recipient/account guards, quiet future updates, header counts including unread desk conversations and visible-tab polling. Existing membership/join-time/block/replay/CSRF/message restriction guards are reused. Self-service Inbox identity retains session/origin/CSRF/rates but does not require bank-staff MFA; bank identity still does. Email/push provider remains deferred and disabled.

Astra's first run hit a usage limit, retried on continuation and completed docs/GAMES-SPECIALIZATION-PLAN.md only. Plan audits real catalog-count/scope/matching/cup-context gaps and stages explicit subject/topic setup and immutable comparable games. No game implementation was delegated or claimed.

Initial scripted scope refactor exposed a malformed community canonical predicate before deployment; corrected to explicit question_scope(q). First tests exposed fixture-only issues: duplicate CSRF header capitalization left the valid first value in place; an outside mock fixture lacked collection_sections, then required position, then used answers{}instead of list[]. Fixed the synthetic contract; a scoring race test wrapper also needed the new scope argument. No production exception was bypassed to make tests pass. Final140tests pass/one upstream AnyIO warning; latest tests24.79s.0047 applies cleanly on production-data clone and clone drops. Browser rehearsal confirms private desk message send, preference persistence and category read badge updates; final release/browser receipts follow.

Final receipt:0047checksum86e5ece06b7bb582, no pending/drift. Pre0047backup27,011,643bytes/mode600. API-before-web deployment completed;46API and33static artifacts exactly match local SHA256s. Health77751questions/12490strict; bank/taxonomyIN SYNC. All1938papers remain Mizoram, so launch/global each77751; no classifications/answers changed. Single live observations:Geography default936at0.670s/All936at0.384s, Allcollections8at1.366s, Allshelves0.929s. Inbox endpoints return401without a registered session. Live guest Inbox shows sign-in action and liveAll filter renders936with scope-aware source links, no browser errors. No production users/messages/answers/attempts were inserted by testing.

Final local browser current backend:unread badge28=27notices+oneunreadconversation, opening desk reduced it27, message send persisted. Synthetic All Geography2→3including onlytheoutsidepaper; reference links retainAllscope. Early viewport captures were scrolled to the composer; scrolled the document to top and saved inbox-overview.png as actual overview proof. Captures are viewport-only; physical mobile and capacity remain unclaimed. Local fixture exited0/drops DB, Vite stopped, temporary tabs closed. No API error/traceback entries in recent journal; local review worker healthy/queueempty, family final200afterredirect. Shared Caddy unchanged. Docs/evidence/gameplan and test handoff mirror privately under2026-10-24-all-exams-inbox, backup kept outside reports child sync.

## 2026-10-24 — Smoother exam focus and automatic vocabulary recognition

User requested smoother Question & exam focus and asked Astra to replace confidence clicks with an automatic engine. Reused the explicitly requested Astra planner; it audited actual old browser-only ratings and wrote docs/VOCABULARY-AUTOMATIC-MASTERY-PLAN.md. Implemented bounded account/server review queue and atomic checked-answer/schedule/receipt storage, strict source presentation, shared canonical progress across focus, 24-hour/due/IST-day promotion guards, no speed inference or runtime model calls, reveal/defer evidence distinctions, and restored feedback on refresh. Existing unscoped browser ratings are preserved but not treated as checked answers. No bank answers or classification files are modified.

Focus now uses a shared React store and SPA navigation, preserving the header/auth session, remounting scoped learner routes and dropping their old responses. Deletes old paper/collection/page/receipt filters, respects reduced motion, and prevents focus switches inside immutable mocks. Earlier DEVLOG full-reload decision is superseded by this change.

A broad scripted App replacement initially added unused scope variables to Planned; production build caught it and it was removed. Astra’s implementation review caught four substantive gaps before release: unsafe choice shuffling with letter-referenced options, recent ordinary Bank answer exposures not affecting promotion, lost feedback on refresh, and primary-only eligibility excluding an equivalent Mizoram printing. Fixed all four and added regressions. First latest spaced-test simulation had to age actual checked attempts too, because the new exposure rule intentionally prevents promotion with recent answers. All148 tests pass/one upstream AnyIO warning in28.29s; eight focused cases pass.0048 applies cleanly on a production-data clone and clone drops. Synthetic browser correct→automatic one-day date, refresh→same saved feedback, Next→different question and Skip→no wrong answer verified. No production learner data or review attempts have been seeded. Final release/browser/mirror receipts follow.

Release follow-up:0048checksum2ea2327e9e7912ff, backup27,024,146bytes/mode600, API-before-web complete. Live155eligible per focus at36ms aggregate SQL; all1938papersstillMizoram. Live guest sign-in page/filter header preservation verified; no console errors or production vocabulary writes. Health77751/12490, guest API401, family final200.

An operator mistake exposed a dangerous old sync-script interface: passed --status instead of supported --check, and unrecognized arguments fell through to full sync. It ran the same bank hash9affc71fae6f, preserved all44attempts/28users and answers, but restored deprecated canonical difficulty from raw appearance metadata on76724rows. Did not claim a clean comparison: restored a disposable database from the private backup, compared table hashes, then every canonical column. Only difficulty and update timestamps differed. Restored difficulty to the original all-NULL state with recorded repair SQL, left raw archival appearance metadata intact, changed full-sync primary propagation to maintain NULL and added two regressions (unknown flag cannot touch even a lock/network; actual SQL ignores raw difficulty). Final hashes equal across canonical, appearances, classifications, related links, score versions, papers, users and attempts excluding updated_at. Sync log and timestamps record the operation. Initial pg_restore direct access failed because postgres correctly could not traverse the private700backup folder; streamed the owner-readable dump to postgres instead, preserving private permissions. No answer/classification JSON changed.

Final150tests passed/one upstream AnyIO warning in30.65s. Last frontend cleanup clears loading/restored flags on account changes, so interrupted logout cannot leave a stale loading indicator. Final production build/artifact receipts updated after this cleanup. Fixture exited0/dropped synthetic DB; Vite stopped and temporary tabs closed. Backup verification clone dropped after final equality. Notes/evidence/Astra plan/source handoff mirrored privately under2026-10-24-vocabulary-automatic. Capacity and physical-mobile checks remain unclaimed.

## 2026-10-24 — English instructions, blanks and final-module emphasis

User reported formatting present in older Group B/UDC-LDC but missing here. Read source renderer, earlier source-context merge tool/report, final generated modules and pipeline. The20October merge had copied intermediate extracted files (4092directions/2490stems), not all final build repairs. Added final-module source restoration under the shared bank lock using exact PDF hash, unique per-paper printed number, question type, normalized unmarked stem and ordered options. Initially audit matched no English rows because final Group B IDs use uppercase Q while clerical uses lowercase q; corrected parser case. Module-only PDF aliases also require per-paper matching rather than treating identical PDF aliases as automatically ambiguous. First inspection script used stdin __file__ and resolved its root incorrectly; reran with its actual path. These were audit/tool failures before data write.

Final audited11723Englishmodule rows,1732source-equivalent matched,1077bank appearances changed:847markup,329directions,59passages. Counts overlap and include improved existing fields. Exact-byte local backup/mode600 created before mutation; protected-field comparison proves all77751records unchanged except presentation fields. Holds9991module rows under strict policy; these are not9991missing instructions. Many source identities are unavailable, descriptive units differ, or final module text/options were rewritten. Do not attach a nearby paper’s context to them. No new questions, answers or classification changes.

Shared renderer now consumes3+underscore blanks before paired underline spans, uses ruled blank lines, preserves bold/italic/underline nesting and opens source passages by default like the prior module. No raw HTML or heuristic prose repair. Found another loss in MockResultView: plain result question text omitted snapshot instructions/markup/passages. Added optional API/TS fields and shared rendering from immutable snapshots; historical context remains original after source corrections.152tests passed/one upstream AnyIO warning in26.91s; new source-identity/number/options and saved-result preservation tests pass. Renderer regression script passes nested marks/blanks/escaping/open/collapse/repeated renders; frontend build passes. Private server backup27248813bytes/mode600. Normal bank sync preserves source truth and retired difficulty; API-before-web release underway. Final browser/artifact/mirror receipts follow.

## Final live receipt

Local/server bank336425b88b01…IN SYNC; all77751classifications stillapproved. Health77751questions/12490strict. Canonical presentation now4243instructions/3158formattedstems/77passages; deprecated difficulty0. Latest sync ledger49attempts before and49after, no new canonical/appearance rows; later real-user activity can change totals. Vocabulary remains155eligible. A second dry restoration finds0changes.47API and33static artifacts exactly match local SHA256s. Family final200afterredirect; no errors in checked API journal.

Live read-only examples: cq_333ebe82fc519dbf shows source directions and italic “getting into a row”; cq_0df04918a17c2513 shows the source instruction and a ruled blank. No answer was submitted. Browser error log empty; temporarytab30closed. A first browser selector tried an unsupported heading-level filter, matched three headings and stopped; retried using the observed exact heading text. Screenshot proof uses actual production questions, not synthetic records. No physical-mobile or public-load certification. Shared Caddy unchanged. Private release docs, restoration proof, scripts and tests are mirrored beside the backup under2026-10-24-english-formatting.

## 2026-10-24 — Answer meanings, reviewed status and contribution entry

User wanted tooltips for derived/unofficial labels and a path to substantiate answers without an official key, earning points. Audited existing contribution editor, quorum, scoring view and worker credit. Reused the actual two-reviewer/publication protocol and10point contribution ledger. No new votes-as-key or submission reward path. Found misleading UI wording calling all derived answers reviewed and saying all non-official answers are never scored despite labelled reviewed estimates. Added reviewed_derived from the existing current-content publication view to list/detail metadata, with no answer disclosure. Shared native-hover and touch/keyboard expandable help now distinguishes official/transcribed/derived/reviewed/suggested/no-recorded-key, source/final-key caveats, scoring and rewards. Question links prefill normal answer proposals; no-key guidance supports the same answer with a better worked explanation, references and date context. Inferred/no-key proposals default derived while real official/key proposals retain document requirements.

First TypeScript build caught nullable answerSource passed to includes(); added explicit none fallback.153tests pass/one upstream warning in28.05s, including imported-derived=false and genuine published-derived=true. Existing independent review, author exclusion, current-source/no-op and idempotent credit tests remain intact. UI checks pass native help, labels, safe question routing, no answer leak and publication-only contribution points. No migration, bank or reward data changes. API-before-web deploy and live receipts follow.

Live browser confirmed the unverified suggestion help, accurate no-scoring/review/credit copy and exact question evidence link without answering. Visual inspection caught the initial narrow expanded note centering the other metadata across a tall flex row; changed open details to span a full row and let the note use the card width (max680px). Native hover remains concise. Latest production build and screenshot are refreshed after that adjustment. Shared Caddy untouched; family final200. No production answers, votes, proposals or rewards are inserted by this release.

Final release: API-before-web deployment complete;47API files and33static artifacts exactly match local hashes. Health77751/12490; family follows redirect to200; no errors in checked API journal. Bank checksum336425b88b01…unchanged/IN SYNC, no migration or reward-data changes. Live native summary opens accurate unverified/scoring/evidence/10point help and retains its exact canonical question link; no answer or contribution was submitted. Final wide help screenshot replaces the initial narrow-column capture. Browser console clean; temporarytabs31/32closed.153tests/28.05seconds plus UI checks; no physical-mobile or capacity certification. Private notes/source/tests/evidence mirror under2026-10-24-answer-provenance-help.

## 2026-10-24 — Navigation and loading; English pilot review

User requested website-wide navigation/loading optimization, then flagged Community filters behaving like separate pages. Split eager screen code and legacy exam CSS; retained shell, added conservative route intent warming, scroll restoration and a manual chunk-error recovery. Header now reads small progress aggregates on meaningful events rather than fetching detailed history on route changes. Added public-only scoped 30-second document cache/coalescing and 10-second process catalog cache with admin invalidation. No learner/scoring cache. Game completion refreshes progress. Corrected deploy default order to API before web.

Community Following/MCQs/Materials previously returned entire replacement page layouts and hid the tabs. Embedded them in the existing panel, preserving all five filters, side rails and heading. Added roving keyboard tabs, filter replacement history, context-aware lesson return, and removed premature link-click scroll resets. Replaced stale sidebar copy claiming games were not active. No new navigation sections.

Build caught a missing JSX closing brace during tab refactor; repaired before deployment.159 backend/offline tests and5 Node tests pass. Local browser verified exam browse/focus/account/Desk/tab behavior and scroll restoration; live browser verified Materials/Following and lesson return to selected tab, no console errors. Frontend root shrank496KB→229KB JS (144KB→74.5KB gzip),115KB→69.6KB CSS. Public collection samples1.93–1.96s before;2.02s cold/0.22–0.24s warm after; no claim of faster cold SQL. API-before-web deploy complete; artifact manifest48API/62static. Bank336425b88b01…unchanged/IN SYNC;health77751/12490. Family final200. Shared Caddy unchanged. Reports/docs/source/tests mirrored privately; final receipts below.

Parallel previously authorized English pilot: Luna drafted200, Sol6.1 independently solved200 before seeing drafts/keys, then critiqued all200. Frozen blind SHA8a69c48e4474be37fb56e514e148e32168e83c1a1515cb5638e775b2e1a02c48. Source PDF extractions and21 source hashes retained.22 explanation-only packets pass preparation gates;178held.57 rows have at least one model choice conflicting with stored key; this is a review signal, not proof57bank answers are wrong.70rows carry83presentation-fix suggestions;2supplemental option-identity mismatches held. Fluent but incorrect direction/spelling/option reasoning and inaccessible citations prevented bulk promotion. Sol hit its usage limit while preparing corrected copies; no corrected drafts were completed/promoted. Offline preparer gates exact IDs/choices, blind/key agreement, context/source/bank hashes, citations and specific option reasoning, with tests; supplemental holds override revisions. No bank changes, production proposals, human approvals or reward credit. Private review packets support resumption.

Final navigation receipt:48API/62static files exactly match the deployed build. Reports and English packets were mirrored privately with SHA256 comparison; final rootJS229051bytes/74539gzip andCSS69622/13026gzip. Live lesson opened and returned to /feed?tab=materials with all filters intact; final screenshot and browser console proof captured, temporarytabs33/34closed.159tests+5Node tests pass. The local fixture process had already terminated by cleanup; removed only its identified synthetic database if inactive. Stopped temporaryVite. No user tab or production record was changed during verification.

## 2026-10-24 — Simplified answer status

User requested a final Verified state and fewer confidence types. Added a pure client display policy: Official key merges official/transcribed provenance; Verified solution requires reviewed_derived; Needs review covers unreviewed derived/suggested and overriding disputed/blocking defects; Unsolved means no recorded answer. Written questions have an appropriate separate label, no MCQ verification/reward prompt. Source information stays in expanded help and advanced source filters; no data migration, review bypass, automatic answer promotion or scoring-policy change. Final key remains an authority-document version, not inferred. Shared list/detail pass real flags into the display helper.10Node tests cover status mapping, proof requirement, override precedence, descriptive types, retained source identity and no fabricated final status; local production build passes. Web release and local/private-server receipts follow.

Live status receipt: web deployed;48API/62static artifacts exactly match local.10Node tests pass and production build passes. Live question cq_0df04918a17c2513 now shows Needs review; expanding it retains Unverified suggestion provenance, scoring boundary and evidence/credit link, without revealing/submitting an answer. Existing contribution source selector now says independent review required, avoiding a premature reviewed claim. No bank, schema or scoring-policy changes. Shared-site health200; final screenshot and private source/report mirror recorded. Temporary browser tab closed after verification.

## 2026-10-24 — Admin exams, papers, status filtering and official coverage register

User approved the full exam/paper-management extension, then asked to inspect two already-open MPSC archives. Read both user tabs without changing/closing them; saved DOM listing snapshots. NG page38exam rows/181links; older page84rows/815anchors, with duplicate/empty anchors and mixed years. Prepared921expected entries in122source groups;669unique historical download-index URL+bank-source associations,252unmatched (not confirmed missing). Trusted operator metadata import created129total inventory groups including7pre-existing learner exams. No canonical content, accounts, approvals or rewards changed.

Added immutable0049operational inventory tables/audit/import ledger and computed status view. Staff owner/publisher writes use existing session/CSRF/MFA/rate limits, stale versions, audited associations and recoverable archive. Global staff reads are private/no-store; subject reviewers keep scoped question repair. Expected source checks store context fingerprints and become stale after context changes. Four status filters combine exam/year/paper at the same appearance, avoiding a cross-paper-year false match caught during implementation. Invalid official options/held/disputed sources need review. Descriptive remains written. Added PDF root availability checks and protected hash-named key/reference transport with active mock/game guard and Range support. Four registered files synced to root:www-data storage outside web root; stage cleaned. Added atomic checksummed local inventory export without changing local bank authority.

Frontend adds lazy admin internal views: exams, registered papers, expected/missing and history. Paper inspector provides PDF/key previews/download, canonical-status counts per appearance, numbering/count/source-context diagnostics, registered key versions/hashes and bank publication receipt. Local synthetic browser owner edited an expected count and drilled into unsolved/verified/needs-review filters; verified remained0without real review proof. Pending-only year2026is selectable without imported papers. No production test account or impersonation.

167isolated tests and11Node checks pass; frontend build passes. Migration0049rehearsed on a live-data clone, private pg_dump backup created, then applied. Bank-wide initial status aggregate measured2387.8ms; added0050to evaluate reviewed set once and avoid unnecessary option validation, preserving semantics.0050clone rehearsal/apply and final query/signature/health/artifact/mirror receipts follow. Applied0049was not edited. Existing deprecation warning remains. No shared Caddy changes or automatic OCR ingestion.

Final receipts:0050clone rehearsal and live apply succeeded. The all-question ID/status signature is identical before/after(1682951eac6cd9cc4f7556a8734ae643); server aggregate execution2387.775ms→117.114ms.167tests/30.08s,11Node checks, production build pass.49API/63static artifacts match local. Protected inventory GET returns401signed out; app/health200and family follows redirect to200; checked API journal has no errors. Bank336425b88b01…77751questions/12490strict remainsIN SYNC; migrations through0050applied/no pending. Local inventory snapshot contains129groups/921expectations, with checksum recorded separately.

Synthetic browser verified PDF preview attachment URL, source/key fallback, audited count edit, expectation-only year, three status filters and authenticated JSON export. In-app native PDF preview remained blank, so visible open/download fallback guidance was added rather than claiming native rendering certification; Range/private PDF transport is covered by integration tests. Synthetic export was moved from Downloads into private reports, not left as apparent production data. Screenshot clearly uses synthetic records. User-owned MPSC tabs preserved. Temporary tabs/services/fixture cleaned; source/reports/docs and snapshot mirrored privately on server. Live public question load and final mirror receipts complete the release. No production question/answer attempt or owner impersonation.

## 2026-10-24 — Five connected bank and learner workflows

User approved paper intake, quality review, unified continuation, correction notifications and personal daily revision, with Astra if useful. Astra reviewed the existing architecture without editing; implementation reuses inventory, bank review/publication, reassessment jobs, Inbox, vocabulary scheduler and Desk. Added0051without editing applied migrations. Intake has evidenced stage/version/failure history and checks an actual archived PDF hash, current source-context fingerprint, expected imported count when known and completed sync before publication. It is an operator-assisted workflow; text extraction does not segment or approve questions. Added scoped quality counts/drilldowns rather than a second content editor. Absent directions are not automatically defects.

Personal continuation aggregates actual mock/vocabulary/focus/task state and versioned allowlisted practice routes. Saved questions open within the original module, avoiding forced Bank navigation. Daily plans deduplicate up to20questions with8due-vocabulary/8mistake/4saved reservations, fill spare slots, use India dates and reuse the existing official/reviewed eligibility pool. Actual post-start attempts create one completion receipt through a DB trigger. There is no client completion checkbox or extra reward. Vocabulary target survives resuming another active card until its own question is issued. Correction events contain field names, not keys, and fan out idempotently to earlier attempts/current account bookmarks through existing preferences and supervised worker. Original attempts/results are preserved; disclosure guards still apply to update details and answer checks.

First TypeScript pass caught source_appearance lacking an ID and a return-link variable inserted in an effect; fixed before deployment. First intake test caught a missing SQL separator. Full-suite testing exposed an existing shared test account that had acquired a grant in another scenario; the permission assertion now uses a fresh synthetic account. Browser AX exposes pressed buttons as checkboxes, while DOM role remains button; switched selectors using the observed DOM. No test workaround weakens production permissions.

175isolated backend/offline tests pass in30.50s;11Node tests and local production build pass.0051rehearsed on a live-data dump clone then applied after a private pg_dump backup. Synthetic browser verified revision start→answer→completion, audited acquired stage, quality→missing-explanation repair, resumed question within English, and Inbox→guarded correction detail. Browser console errors empty. Live authenticated admin mutation was not attempted; signed-out private endpoints return401.

Live read-only profiling caught4.66s/4.45s revision queries. Materializing small personal candidate IDs before eligibility checks cut samples to413ms/270ms. Transaction-local JIT-off final samples400.57ms/265.09ms; this is not a capacity claim. No public or learner cache was introduced. The deploy script's old recursive /srv/study chown had changed the protected registered-document owner to caddy; fixed it to target public only and restored root:www-data750/640. All four registered PDF files are readable by the API again. Shared Caddy unchanged; family final200.

API-before-web release complete;52API files/70static artifacts exactly match local build. Health77751/12490, canonical SHA336425b88b01…IN SYNC, migrations through0051/no pending. New paper stages are not prefilled with guessed historical review. Operational inventory including intake is exported locally; code/docs/reports/receipts are mirrored privately on the server. Physical-mobile/load/recovery certification and automated crawling/OCR/segmentation/import remain separate. Question-bank answer completeness is not claimed. Temporary browser tabs40/41and identified local fixture/Vite processes are cleaned after the rehearsal; user tabs preserved. Final cleanup and private mirror receipts follow.

Final workflow receipt:52API/70static hashes match production,175tests/30.50seconds and11Node checks pass. All private endpoint probes401while app/health and shared family site200. Canonical bank unchanged/IN SYNC;0051applied/no pending. Temporary fixture and Vite exited cleanly and their disposable database cleanup ran. Private report mirror SHA comparison succeeded; mirror-receipt.json records the exact files. No production answer, review or reward was generated during verification.

## 2026-10-24 — First real paper through the source-review intake

User said “Do that”, then “Continue” after the five-workflow release; proceeded with the remaining PDF extraction/source-review step. Selected February2026LDC Law &Judicial PaperII because the bank had99appearances and a Q43gap. Downloaded the exact official listing URL, matching local and registered SHA2562567971b6bfbb39f45515c3c503ce31e4ee1b38f9c44bdd07de9aea7f84a8ccb. Extracted text and rendered/visually inspected all11pages. Parsed100source questions. Source comparison found missingQ43, radical/minus/exponent/arrow loss, Q72wrongpage, missing table/chart context/directions, syllogism assumptions and currency marks. Plain text alone omitted rupee glyphs and misrepresented Symbol-font radicals, confirming why PDF visual review is necessary. Decorative Options labels/end marker are not counted as missing-content defects.

Prepared and submitted21owner-authorized operator-assisted proposals through the existing normal validation/idempotency/audit tool:17transcriptions,1new printed question,1source locator,2source-defect flags. Proposed unofficial working additionally corrects Q56to4√6 and Q70to172. Q29printed shortcuts lack an appropriate duplicate-slide choice; Q99has two valid arrangements with different opposite-to-B answers. W3C grammar notation and Microsoft primary shortcut documentation are retained as supporting references, not official MPSC keys. No official answer-key search or final-key claim in this source pass. Five derived-answer followups are blocked until source restoration is published and a fresh baseline is available. Q72has separate locator/context proposals; one must rebase if the other publishes first.

Extracted two exact-source content-addressed table/chart crops, visually inspected them and mirrored only those two files to the existing public figure archive without deleting other assets or touching Caddy. The source graph's bar lengths are inconsistent with numeric labels; preserved the scan and included a clear note instead of inventing a corrected drawing. Live image hashes match. Trusted SSH operator intake records acquired→extracted→review with append-only events, explicit operator identity, expected count100, reviewed_byNULLand sync_idNULL. Archived PDF bytes are checked before this operational mutation. No synthetic owner login, reviewer approval, grant, canonical write, publication or credit.

Canonical bank remains336425b88b01…77751questions/77751approved classificationsIN SYNC. The first paper is audited and queued, not published or answer-verified. Independent reviews are still required by the existing bank policy; none are fabricated. Raw source, renders, comparison,21proposals/receipts, deferred answer packets and live proof are retained under reports/source-review-ldc-law-2026. Server-owned inventory including the Review stage is exported locally and the audit is mirrored privately on the server. No application/schema deployment or new tests were necessary for this operational source pass.


## 2026-10-24 — Direct admin answer decisions and understandable audits

The user explicitly requested that an administrator directly assign official/corrected answer states, then said the audit was hard to understand. Added a distinct owner/publisher path with real session, CSRF, MFA and subject scope; this is a deliberate user-authorized exception to independent community-review quorum. Community proposals retain their existing quorum and self-review restrictions. No production answer decisions, approvals, users or credits were created for this release.

Official requires an exact registered non-superseded key mapped to the printed question, option text and PDF page. Corrected/verified requires a worked explanation and an immutable administrative reason. Needs review places an audited scoring hold immediately. Unsolved queues removal of the answer index/source. Other answer changes queue the existing canonical local-bank publication and server sync; they are not instant web-only edits. Primary appearance, current-content token, source-defect, missing-image, option, active-assessment, idempotency and pending-publication guards remain enforced. An administrator must explicitly release an existing hold before assigning a new answer. Administrative maintenance earns no contribution points; no fake peer approvals are generated. Source transcription/image proposals continue through the existing review workflow, including the 21 pending LDC source proposals.

Paper inspection now starts with plain-language counts, filtered fix links and a next action; source IDs, hashes, key registration and detailed history are collapsed under Technical details. A contradictory recorded expected count is explicitly described as a count mismatch to check against the PDF. The first real LDC source-review report now starts with a short readable summary and hides its detailed evidence links in a disclosure.

Verification: 182 isolated backend/offline tests passed in 33.90 seconds; 11 Node checks and production build passed. New tests cover direct role/CSRF/scope, exact-key evidence, holds/unsolved, stale state, idempotency, unchanged derived-answer attestation, primary-source/active-mock guards and real isolated manifest→local bank→SQL sync→worker receipt→Verified status with zero peer approvals or maintenance credits. The first full run exposed shared-test classification contamination from the real sync rehearsal; the test now restores classification/link/section fixtures in finally, and the complete suite passes. Synthetic browser confirmed queued direct publication and the simplified paper summary with technical details collapsed. No production owner session was fabricated.

Migration 0052 was rehearsed on a live dump clone, then applied after a private backup. API deployed before web. Protected registered PDFs retain root:www-data 750/640; Caddy unchanged. Canonical bank remains 77,751 questions, 12,490 strict scorable, SHA336425b88b01…; local/server in sync. Full evidence is in reports/direct-admin-answers. This release does not resolve existing bank answer completeness or automatically approve the source-review queue.

Final receipt: 53 API files and 70 static artifacts exactly match production. Migration 0052 applied with no pending migrations; bank IN SYNC. Health and shared family site return200, signed-out private decision endpoint401, and live admin_answer_decisions remains0. Synthetic browser console errors empty; temporary tab42 closed and identified fixture/Vite processes stopped. Private source/report mirror and hash receipt follow.


## 2026-10-24 — Publish the first real restored paper

User said Do it after the explicit plan to finish LDC Law & Judicial Paper II: restore Q43/source context, resolve five answer followups, publish/sync, verify paper/browse/practice/mock. Rechecked source page renders with the PDF skill, checked source evidence hashes, and searched the official domain for the exact key without finding a match. The absence is recorded as a limited dated search, not a claim no key exists. W3C grammar notation and Microsoft's PowerPoint shortcut documentation were rechecked as supporting references. No official status is inferred from these sources.

Added a trusted SSH-only source maintenance service/command. It requires the existing owner's global grant, explicit delegation, exact proposal payload, registered paper/hash evidence, and immutable operator identity. It records actual maintenance authority without synthetic peer approvals, fake logins, MFA assertions or new permissions. Conflicting fields/reviewer objections block publication; disjoint rebase is explicit. Ordinary community reviews retain their requirements. Worker excludes administrative maintenance credits; contribution detail identifies the recorded source repair decision. Backed up canonical JSON locally and the server DB privately before publication. Temporarily paused the local publication timer while the foreground sequence owns this queue.

Q43 published and paper count reached100. Q55 sync succeeded but a legacy raw difficulty value caused the worker's canonical comparison to fail: canonical difficulty is intentionally retired/null. Fixed the comparator, added a regression, verified exact current output checksum and live content, then recorded receipt reconciliation and acknowledged the original publication. Did not erase the failed history, fabricate sync receipts or reapply altered bank content.

Student paper API now returns each appearance's wording/passage, reviewed answer state and source defects. Paper view uses the shared provenance help, shows faulty-source warnings and suppresses answer checks for those items. Added a paper-specific Practice estimate entry based on actual eligible reviewed count; strict official-key test rules remain separate. Mock copy acknowledges authorized admin as well as independent review.188backend/offline tests,11Node checks and build passed at this stage; API-before-web deployed. Final publication and real-content acceptance receipts follow.


All21source repairs and8direct unofficial answer decisions are applied, including explicit safe Q72 disjoint rebase. Paper has100printed questions; Q43new,19existing questions changed, no question outside this paper changed. Canonical bank77752/SHAa51fa04f3561… and live sync112agree. Missing MCQ indexes decreased1652→1649.8Verified/92Needs review, where92comprises90original unverified answers and2faulty source questions. Strict official score count0for this paper; reviewed estimate8. Neither source restoration nor the limited unsuccessful official-key search is blanket answer verification.

Q73dry run caught a second compatibility issue: raw-1means unanswered, but source transformation rejected it as an index. Normalize only the untouched legacy sentinel to null; do not invent an answer. Added regression, verified unchanged input SHA/source evidence, recorded retry and published. Sync now skips unchanged appearance/classification/source-defect rows; SQL regression checks row xmin remains unchanged on replay while real source edits propagate. Real repair logs show one appearance update and zero classification updates. No capacity claim.

Final student-flow inspection found frozen figures were stored but omitted from MockQuestion/API/UI. Added safe figure URLs from the immutable snapshot to start/resume and result/history, with original image rendering in both screens. Regression changes live source after mock start and verifies frozen figure/results remain intact.191backend/offline tests pass; real-paper acceptance separately passes100-question pagination,8reviewed solutions,2blocked faults, practice and8/8mock with figures through submission/history. The isolated fixture explicitly applies the actual Mizoram paper scope; no production account session, mock or learner attempt was fabricated.11Node checks/build pass.

Source intake marked Published using the exact archived PDF hash,1–100number check,21applied source publications, current source fingerprint and real completed sync112. Updated_by is the explicit delegated operator and reviewed_by remainsNULL; no independent human review is claimed. Local publication timer restarted and queue empty. Final deployment/browser/live checks and private mirror receipt follow.


Final live receipt: 54 API files and 70 static artifacts exactly match the local build. Public paper API returns 100 ordered questions and 8 eligible reviewed questions; both figure byte hashes match their content-addressed names. One measured request was 1.208 seconds during publication; no capacity claim. Live browser verified the eight-question estimate link, four-page navigation, Q73's Verified solution badge/instructions/original graph, and Q99's visible source fault with no answer-check control. Console errors were empty and the temporary tab was closed. No production learner submission or mock was created.

Application health and shared family site return 200, signed-out private admin returns 401. Assessment, new-score and correction-notice queues have zero pending/failed items; both workers are online, local timer active, and live learner attempts remain 84. Registered PDFs retain root:www-data 750/640; API error journal empty; Caddy unchanged. Local inventory export refreshed to 129 exams/921 expected entries and the published paper intake. Canonical bank/taxonomy are IN SYNC. Final private source/report/bank mirror checks follow.

## 2026-10-25 — UDC coverage, readable verification lists and materials in place

User requested review/verified question lists, simpler Notes/Materials navigation, and production refinement of UDC with historical/current-affairs guidance. Added learner answer-status filtering (bound enum SQL), in-page exam status lists and prominent admin presets with reasons/actions. No publication permissions or answer states were changed. Materials are explained as shared notes/articles/guides/lessons; cards and public search hits use a history-aware native dialog reader over the existing list. Close/Escape restores focus and place. Related lists expand/paginate inline and Saved materials is a Library tab. Existing server entitlement/preview/payment-demo logic remains in use.

UDC initially had 28 mapped papers/2,194 questions and no reviewed mock pool. Fixed the empty practice default, unsupported mock entry points, progress denominator, paper search/year/pagination/source labels and unverified answer wording. A further exact-source membership audit found 18 omitted Direct UDC papers from 2014–2018. New immutable migration 0053 publishes version 2 (46 papers/3,449 existing questions), retaining version 1; rehearsed on a disposable live-data clone and applied after private backup. All eighteen PDF links return 200 application/pdf. No source answer was invented, imported or marked verified.

Final UDC counts: 3,441 Needs review, 8 Unsolved, 2,755 without explanations, four empty paper records; 3,410 study answers and zero reviewed-mock eligible. Source completeness and correctness remain pending and are explicitly documented. Exported an actionable canonical-ID review CSV and raw local checklist; preserved live collection metadata locally and on the server. Canonical bank remains 77,752/SHAa51fa04f3561… in sync.

Shared date hints preserve exam-date answers, link relevant official references and request effective dates in corrections. They are conditional presentation hints, not automated factual verification or current-answer replacements. Browser inspection caught an Excel “current sheet” false positive; narrowed detection and confirmed it disappears while Chief Justice guidance retains the Supreme Court reference.

Build/Python syntax checks, all 191 backend/offline tests (33.75s) and 11 Node checks passed. The disposable test fixture supplies empty version 1 UDC metadata for migration 0053's guarded predecessor; no production questions or users are copied. Live read-only checks cover UDC filters, restored years, practice pool and modal navigation; no fake auth/reviews/attempts/credits. Aggregate profiling caught a new cold-read cost: removed redundant launch-scope rescans, grouped section/readiness work and used transaction-local jit=off with short public caching. One SQL sample improved from 2,443 to 768 ms and one HTTP pair was 1.456 s / 0.292 s; not a capacity claim. Production API-before-web deployment, migration/asset receipts, screenshots, full remaining-work counts and private mirror are under reports/udc-production-refinement.

## 2026-10-25 — LDC production refinement and paper-level readiness

User requested the same cleanup for LDC. Audited all local paper metadata, not only existing collection links: all four banked direct-recruitment LDC papers were already connected (350 questions); LDE promotion papers remain separate. No content migration or invented additional papers. Four PDF endpoints return200 application/pdf; stored question sequences are contiguous. Question state is79 official-key eligible,8 verified unofficial and263 Needs review; no missing answer index,228 explanations absent and2 known source defects retained/excluded. Reviewed mock pool87; study pool348. Canonical bank stays77752/SHAa51fa04f3561… unchanged.

Added additive per-paper API fields for actual answerable/reviewed pools, verified/needs-review/unsolved states, missing explanations and blocked issues. Shared paper cards expose these counts, link to in-module status/practice views with a browser anchor, prefer official-key practice when available, expose the eight-question Law & Judicial II reviewed estimate directly, and distinguish practice defaults from confirmed original exam rules. Compact collections such as LDC use a balanced two-column layout. Paper viewer now handles invalid paper IDs and loading/retry during pagination without showing stale question rows. Original questions, options, source figures and grading provenance remain intact.

Broadened news-date detection for real LDC wording such as Recently, the QUAD nations launched… and Recently which climate activist…detained. Added the dated primary PIB At Sea Observer reference; no current fact or historical answer was overwritten. Regression excludes Excel current sheet, biology present inside the cell, grammar and arrow sequences.

192 isolated backend/offline tests passed in35.26s,12 Node checks passed, and the real 100-question Law & Judicial II acceptance rehearsal passed separately in4.45s, including the reviewed eight-question mock and frozen figures. Added one synthetic per-paper contract test; no synthetic production accounts, mocks, attempts, reviews or votes. Initial frontend typecheck caught a possibly undefined paper guard; corrected before the frontend deployment. Final build/deployment and browser/source receipts are under reports/ldc-production-refinement. Remaining source verification, explanations and true paper rules are explicitly documented.


## 2026-10-25 — LDC coverage correction and 2025 import

Published the missing February 2025 MPSC Paper I/II through the canonical bank and guarded collection version 2: six papers, 528 items (525 MCQs, three written tasks). Restored full written content and original figures/markup. 170 legacy answer claims remain unverified; two unanswered and three newly imported defective-source MCQs are explicit. Existing 77,752 records preserved. Eight linked direct archive pages checked; no additional LDC links found there. Paper instructions are now exposed by the collection API and shown by the reader. Evidence and remaining 436 answer reviews / 403 missing explanations: reports/ldc-2025-import/README.md.


## 2026-10-25 — UDC solutions and answer-source contrast

Published 39 immutable owner-authorized changes: nine source repairs and 30 verified unofficial solutions, resolving all eight unanswered UDC MCQs. UDC now has 46 papers / 3,449 questions: 30 reviewed solutions, zero unsolved and 3,419 Needs review. No official key, peer decision or contribution credit was fabricated. Restored ranking instructions, pi options and original three-choice format; retained source figures. Taxation Q93/Q99 have unreadable operators in the original PDFs and are excluded from scoring. Primary source checks, permutation/cube calculations and explanations are retained in reports/udc-answer-review-20261025. Unrelated bank records preserved.

Official key badges are green, verified unofficial solutions blue and Needs review amber, with distinct words/symbols and accessible contrast. Exam pages show the legend; verified detail pages offer evidence improvements. Detail API now returns the actual answer status without leaking answers.

Fixed PostgreSQL staging-directory traversal under worker umask 077; the failed sync transaction rolled back, and the exact immutable publication/local receipt was retried successfully. Staff source intake now checks active owner authorization, and staff maintenance has a bounded 500/day allowance; community intake stays 30/day. Role/quota regression checks pass. All 39 publications applied; timer restored active. Local/server bank in sync at 77,930 records; 54 API and 69 static files match; family HTTP 200. No migration or Caddy changes.

195 backend tests, 13 Node checks, production build and real-content acceptance rehearsal passed. Isolated Taxation mock scored 23/23 and booklet D 6/6; shared instructions/figures survive results/history; damaged expressions reject scoring. The rehearsal uses separate synthetic local learners to respect the free-plan quota; no production learner submissions were made. Remaining UDC review is explicitly incomplete.


## 2026-10-25 — Easier admin answer review and explicit reviewer permission

Confirmed the requested registered email already had the global owner grant; added only the missing global reviewer grant (id 3), with an operator authorization audit event and local receipt. Owner grants already authorize direct administrative decisions; the users.role learner display is not the bank permission authority. No account/session or reviewer approval was fabricated.

Simplified review navigation, exam selection, advanced filters, answer radio buttons and four explicit decision actions. A verified solution’s worked explanation can serve as its audit reason, avoiding duplicate writing. Exact-key mapping still needs a registered authority document and explicit page. Save & next advances within the loaded page only after a successful save; recent decision cards check real publication status without navigating away. These last-five session cards are not a durable second queue. Errors retain the question; checks pause in hidden tabs and stop after 15 minutes. Kept all existing API gates and publication rules.

Build/deploy passed and static hashes match production. Existing disposable local browser fixture confirmed the no-key safeguard and saved one synthetic decision with Save & next; it stayed queued because no local publisher ran. HMR during development resets session-only cards, as a real full reload would; permanent history is available through the decision link. No automated suite rerun for this frontend-only change. Production verification was read-only and required sign-in; no production question mutations. Bank stays in sync at 77,930 records. Evidence: reports/admin-review-simplification-20261025.

The final status display also handles idempotent replay responses that omit publication_id: it reads the contribution’s existing publication receipt rather than remaining falsely queued. Final rebuild/deploy completed.


## 2026-10-25 — UDC review filter and Assistant Grade baseline

User requested an immediately accessible UDC review filter. Added pinned UDC, LDC, Assistant Grade and All exams buttons above the full inventory dropdown, plus an explicit Reviewing scope banner. Clicking clears unrelated search/paper/topic/year/subject/issue filters while preserving the selected answer-status list (defaults Needs review). URL exam=udc survives refresh and scopes the existing permission-checked query; no fuzzy title matching or new data copy. Production database scope confirms 3,419 Needs review and 30 verified unofficial UDC solutions. Frontend rebuilt/deployed.

Assistant Grade remains the next content-review task, with baseline saved in reports/assistant-grade-review-20261025: 1,015 questions, 1,003 Needs review, six Unsolved and six already verified shared solutions. The public paper_list contains 20 registered papers, 15 with questions. Exported six unanswered items plus a duplicate-option defect for source inspection. This audit did not change any Assistant answers or import missing paper content. No new official-key claims or review credits.


UDC filter verification exposed a separate operational-inventory defect: its 0049-era links contained only 28 papers, while collection version 2 from migration 0053 has 46. The first exact inventory count was 2,165 Needs review / 29 verified, not the learner collection’s 3,419 / 30. Repaired precisely the 18 missing source identities in one guarded transaction, checked the requesting owner remains authorized, preserved every existing link and recorded 18 operator inventory events. Final exact filter scope now matches all 46 papers / 3,449 distinct questions: 3,419 Needs review and 30 verified. This is operational metadata repair, not a schema or canonical-content mutation. Existing migrations unchanged; recovery evidence includes before/after association snapshots and the SQL. Family HTTP 200.

## 2026-10-25 — Astra game topic entry planning

Prepared docs/plans/GAME-TOPIC-SELECTION-ASTRA-20261025.md after reading the current Games controller/client, specialization plan, Library mappings, learning workflows and reward contracts. Proposed three student entry points (exam, recent practice, manual subject), one confirmed named area first, private common-area consent later, and hard personal exclusions without mastery gates. Source inspection found the current nullable-subject mixed default, immediate private-duel start and catalog count/draw mismatch still need implementation work. The plan specifies 14 future acceptance criteria and preserves 20/10/10/10/25 mode pool thresholds and the shared 300 XP budget. No live pool census, tests, builds, server access, bank sync or application edits were performed; example counts and suggested history thresholds are design proposals, not measured coverage or validated mastery. The existing working tree contains substantial unrelated changes; this session only added the plan and appended this note.

## 2026-10-25 — Assistant / Group B source restoration, model review pilot and currentness notes

Completed the active Assistant source work before expanding Group B. Assistant grew from 20 registered / 15 populated papers and 1,015 records to 22 populated papers and 1,568 records. Added 553 source records (433 MCQs and 120 written tasks), two April 2024 Assistant/UDC papers, the missing October 2025 booklet content and historical conventional sections. Relabelled one existing Part B comprehension question and restored its shared passage without changing its answer. Source matching supplied 194 derived claims only; it did not verify those answers. The successful sync followed a transactional rollback caused by an unsupported classification-source enum. Do not mistake staging dry-runs for exercise of all apply constraints.

Group B initially contained 15 paper records / 1,425 questions. All 37 Combined Group B source PDFs in the authoritative saved archive inventory match fresh official downloads byte for byte. Tesseract PSM6 text plus word geometry recovered the 22 absent papers; 2,035 items were appended (2,008 MCQs, 27 written parent tasks). CSV's default quote handling swallowed the remainder of two TSV pages when OCR emitted a literal quote; re-extracting with QUOTE_NONE fixed it. Printed anchors were checked and missing option transcriptions visually corrected. Empty stems for two questions that relied on a shared instruction caused the first apply transaction to roll back; the printed instruction was restored before a successful retry. Imported answers remain unverified: 249 consistent exact matches retain only derived claims.

The user explicitly clarified that Group B includes UDC and Assistant. Published collection version 2 as the union of 37 Combined Group B sources and 60 distinct existing UDC/Assistant source identities, preserving dedicated pages, question/progress identities and old versions. The broader union revealed three older UDC written papers still empty. Restored their 29 actual written tasks from eight re-OCRed pages after checking their registered PDF hashes. All 97 Group B listed papers now have content. Final public counts: Assistant 22 papers / 1,568 questions; UDC 48 / 3,930; Group B 97 / 8,060. This is available-source coverage, not proof every historical MPSC source or answer is complete.

One original official PDF is truncated: December 2024 Paper II booklet A has 10 pages and ends at Q83 despite its 100-question cover. Q84–100 are not fabricated or mapped from another booklet; the collection note and paper instructions disclose the gap. November 2024 Technical English has ten actual tasks numbered 1,2,4–11, not an invented Q3. Surveyor IV repeats number 75; the second occurrence is shown at sequence position 76 with a public numbering note. The final source pass updates 482 broad subjects: common Paper II computer/maths/reasoning blocks, Surveyor IV mathematics, and Civil IV's final reasoning/English block. Fine-grained topics remain unguessed. The written-only November English paper is descriptive.

Astra supplied the games entry plan at docs/plans/GAME-TOPIC-SELECTION-ASTRA-20261025.md. It uses For my exam / What I’ve practised / Choose a subject, explicit area confirmation and fair shared-area duels. Planning is done; this games flow is not implemented in this session.

For the user's low-cost review request, Luna examined 25 October 2025 Assistant/UDC English questions against source pp6–8. Sol 6.1 independently adjudicated them. Luna incorrectly called Q69 ambiguous after overlooking the repeated article; the source and Government of Canada grammar confirm “were.” Q61's approximate antonym and Q68's has/have collective-noun ambiguity remain unverified. Published 23 clear explanations through owner-delegated administrative decisions and the existing immutable publication worker. One queued Q56 export predated the unrelated written-source append and failed the whole-bank checksum guard. Its exact question snapshot remained unchanged: the normal rebase transition reopened it, a fresh decision published, and the superseded proposal was withdrawn. The original failed manifest remains in history. Do not append source data between review export and apply unless prepared to perform this explicit reconciliation.

Also published one previously unanswered current-affairs solution: December 2024 common Paper I booklet C Q6, from the Ministry of Finance appointment notice dated 31 December 2023, with a separate revision reference checked 25 October 2026. All 24 new solutions are verified unofficial solutions, not MPSC-issued keys. No peer votes, users, sessions or contribution credits were fabricated. Final reviewed practice counts are Assistant 29, UDC 53 and Group B 102 (including Group B's 48 strict-key items). Wider review is unfinished: bank-wide 2,111 MCQs still have no answer index; the 8,152 written questions do not require one.

Currentness hints now cover officeholder questions and changing production/ranking metrics, plus dated Finance Commission and Indian/Union Budget reference notes. Historical answers are preserved. The false grammar warning persisted when callers supplied only the human-readable topic “Reading comprehension”; passing subject and topic together fixed it. Live Assistant written-paper inspection confirms ten tasks, 20 visible blank markers and zero date warnings. The finance question visibly shows Verified solution · unofficial and the dated reference. No production learner answers or mocks were submitted. Frontend build succeeds and all 69 deployed frontend files match local output. No automated test suite was added or run.

Public uploads initially failed because those directories need the existing sudo rsync deployment path. Retried without changing sharing or authentication policy. Asset audit caught 13 continued-page Assistant figures absent from the server despite earlier shipment assumptions; all are now present. Final check: 517 public PDF/image files match exact server hashes and 39 bounded public HTTP checks pass. Source images remain full source-page composites; OCR maths/fine formatting still need subject review. Local/server bank checksum matches across 80,547 records (9ad103f32c19…); old question changes are exactly the 23 authorized English publications, and all older paper/sitting records are preserved. Pending exports zero, existing users 29 and learner attempts 87 preserved. Review timer restored active; family site HTTP200. Shared Caddy and protected document roots untouched. Pre-import server dumps and private report mirrors preserve evidence; large bank-before snapshots remain local.


## 2026-10-25 — Ship student-friendly game selection and eight computer solutions

Implemented Astra's first-release game entry plan in game_selection.py, Games.tsx and GameSetup.tsx with migration0054. Students choose an exam, recently practised area or named subject, explicitly confirm available strict questions and rules, and can exclude subjects. Canonical identity/progress stays shared; displayed appearances must belong to the selected exam papers. Private room previews require context acceptance and new rooms use ready lobbies. Exact context hashes isolate random queues; full waiting rooms are skipped. Legacy null-context rooms retain old start behavior. Fixed mixed cups disclose personal-choice bypass.

Two runtime traps were caught before finishing. has_diagram belongs to appearances, not canonical_questions/v_scorable; using the wrong owner failed the first read-only query. More seriously, adding v_launch_scorable's corpus DISTINCT to an already scope-constrained appearance join caused >45s scans; use v_scorable plus the explicit appearance/paper scope. A NOT EXISTS anti join over v_question_paths chose a repeated sequential scan; hashed NOT IN exclusions preserve semantics and bring preview-plus-draw to0.92s. Base pool SQL294.7ms, catalog0.58s, strict eligible pool12,451. Guest previews initially called reviewRequest and wrongly required the contribution session; use the dedicated read-only preview request instead. Browser confirmation now works as a guest.

Dump-clone rehearsal and backup preceded applying0054. Manual disposable-database checks confirmed same-question both-ready duels, private consent checks, queue isolation, full-room skip, idempotent start, party readiness plus host start and solo speed start. An initial queue comparison reported false because an earlier rehearsal player was already waiting; a fresh Vocabulary context confirmed matching correctly. No production rooms, answers, rewards or synthetic learner identities were created. Temporary database removed; users29 and attempts87 preserved. Python compile and frontend production build pass; API/web deployed. No automated suite added/run; unexercised auth/mobile/load/reward regressions remain explicit in the report.

Luna reviewed ten December2024 GroupB common PaperII computer questions. Published eight clear solutions with references via delegated administrative decisions and serial immutable bank exports. Q5 register/cache ambiguity and Q9 broad USB wording stay held. Unofficial verified solutions remain outside official-key games. Source bank missing MCQ indexes now2,103 (from2,111), with80,547 records and local/server SHA728ea58c3028…; publication receipts8applied, exports0. Timer restored active. UDC exact-paper game selection and Arithmetic topic currently have zero strict eligible questions: do not silently mix other papers to hide this. Full evidence and deferred features are in reports/games-topic-implementation-20261025/IMPLEMENTATION.md.

Final deployment audit: all 69 frontend artifacts match local hashes. API health is OK and the family site returns HTTP200 after its normal redirect. Private evidence/code mirror saved on the server; root-owned backup permissions were tightened with sudo after ordinary chmod correctly refused that file.


### Final correction: count legacy unanswered sentinels

The null-only count of2,103 is incomplete as a measure of remaining work. Another1,532 source MCQs store answerIndex=-1 and answerSource=null. The existing importer correctly normalizes negative sentinel indexes to unanswered; game SQL cannot score them. Total source MCQs without a usable index is therefore **3,635** (2,103null +1,532sentinels). The database has3,636 live canonical MCQs without answer_text; these are different identities/units, and the one-record discrepancy is not resolved by this release. Do not repeat the null-only number as total unsolved. See answer-index-audit.json. No bulk source rewrite was performed.

## 2026-10-26 — Source-backed clerical verification, bounded publication and explicit holds

The user requested clean, fully instructed/explained Needs review questions for LDC, UDC, Assistant and Group B Non-Gazetted. Exact starting union8,588; Needs review6,213; unanswered1,999; unofficial verified70. Admin inventory links already match all22Assistant/48UDC/97GroupB/6LDC collection sources. No membership expansion or identity replacement was needed.

Prepared350 independent worked solutions after original-PDF/option/figure checks, Luna first review and Sol6.1 ambiguity adjudication where needed. Published315, including34 previously unanswered questions; every new solution has a worked explanation and remains unofficial. The remaining35 have been reviewed but are NOT published or Verified: the existing rolling500/day staff maintenance cap rejected further creation. Reconciled and published only the26 already exported members of the final61-item request, preserved the cap and saved guarded pending decisions. The observed35-slot window is26October08:48:50UTC/14:18:50IST assuming no new maintenance. No later-run automation or completion promise was created.

Source work restored LDC seating/family/symbol passages, three source-page figures and physical page locators; shared Assistant/UDC broken mathematics/fractions/exponents/options; older Assistant117–125 expressions and distinct options; exact English51–75 targets/underlining and complete shared directions; chart/ranking/Venn context across booklets. A82/C47 now attach both original source pages, preserving the continued question and missing diagram. Medical Record Technician Q90's source cube figures were restored without certifying a medical answer. The obsolete additive-inverse duplicate-options defect was cleared after original-option restoration. Original duplicate appearances are retained.

A model equivalence report missed extraction artifacts in the VPN options. B15 had numeric spill from the following maths problem; restored it and cleared the false required-image flag. High-resolution C100 inspection showed Networkp actually printed in the source. An initial source rationale wrongly called it OCR noise; interrupted and recovered its prepared publication, then recorded a separate audited restoration of the exact printed option. The visible explanation identifies the source typo. Immutable history is retained and the wrong rationale explicitly superseded. This is why source inspection remains necessary despite model agreement. Initial nullable optionMarkup and missing answer-remap batch requests were rejected atomically by existing validators and corrected without bypass. New two-page assets were initially uploaded beneath an extra page-renders directory; the public route uses filenames directly. The final asset audit caught it, uploads were flattened, and all six new public images now return200 with matching hashes. Shared Caddy untouched.

Added trusted SSH-only bounded source/answer batching: ContextVar scope admits only exports created by that same source transaction; ordinary outstanding-export restrictions persist. Source batches are atomic; answer batches retain separate audited decisions/idempotency. New explicit-ID publisher reuses original source/baseline/manifest validators, individual receipts, one backup and durable prepared journal, atomic bank replacement, one guarded sync, all-target live verification before normal per-publication acknowledgement. No public endpoint/role/session/MFA changes or peer votes/credits. Single-member replay refuses partial batch reconstruction. Optional expected_source guards on deferred owner decisions reject changed stems/options/instructions/figures before reuse. Public permission and official scoring rules remain unchanged.

Eleven source/ambiguity appearances have concrete admin holds: seven LDC English items and four versions of the false GUI-element/multitasking premise. Eight other computer terminology issues were resolved using the uniquely best printed choice plus visible precision notes; no silent question rewrite. Independent exact rational/algebra calculations, full seven-boy ranking enumeration and geometry counts are saved. Python compilation and manual pure-validator checks succeeded, including tampered manifests, stale bank, duplicate targets, official promotion, source mismatch, input isolation and receipt/output hashes. Actual interrupted prepared publication recovery succeeded. No automated suite or production learner submissions were run; arbitrary crash/concurrency/load paths remain unverified.

Final:315 new unofficial solutions; union verified385, Needs review5,932, unanswered1,965, written179 and official127. Missing MCQ explanations7,319→7,028. Zero required-image flags lack an attachment; that does NOT certify every historical instruction/diagram. Bank80,547 IDs and all nonquestion metadata preserved; only337 authorized question records differ,80,210 are unchanged. Source MCQs without usable indexes total3,601 (2,071null+1,530sentinel/invalid), not just the null count. Users29, attempts87, strict scorable12,490 preserved; exported queue0; local/server exact SHAce27094a29d268c89d149126f4a6530bd36de27cd1a050d9b9b0c17eff23c3e5. Live browser shows the corrected several underline, complete instruction and Verified solution·unofficial badge. API healthOK, family site200 after redirect. Existing review timer restored active. Reports, per-exam CSV worklists, code, docs and private DB dump retained/mirrored; no claim that all four collections are complete. See reports/clerical-verification-20261025/IMPLEMENTATION.md.

## 2026-10-26 — Historical Assistant/UDC arithmetic evidence packet

Read-only source review of all 69 selected Needs review arithmetic appearances in Assistant Grade Paper-II (44) and UDC under EF&CC Paper-II (25); the separately assigned LDC 2025 batch was excluded. Visually checked the complete relevant original PDF pages: Assistant pp. 8–13, UDC pp. 7–9. Recorded source SHA-256, page, source wording/options, calculation proof and disposition in `reports/math-review-historical69-20261026/`. Sixty-two items have a supported printed option. Seven are held: Assistant Q89/Q90/Q101/Q113/Q118/Q120 and UDC Q100. No stored answer was used to derive the calculations, and no bank/server records or tests were touched.

Source transcription traps: UDC Q76’s page-8 bank locator is wrong; the scan places Q76–79 on printed/PDF p.7. Q76’s stored equation is also a broken transcription: p.7 visibly gives `1 2/3 ÷ 2/7 × x/7 = 1 1/4 × 2/3 ÷ 1/6`, whose solution is x=6. UDC Q100’s last option is visibly labelled `(c)` twice; it prints Rs.20, while the subsidy calculation yields Rs.7.50 and no listed value. Assistant p.9 Q89 visibly has both negative exponents, giving `(8/5)^12`, not one of its four options. Other source-choice mismatches are retained and held instead of forced keys. No production publication or answer-state change was made.

## 2026-10-26 — Final 158-question mathematics source review

Reviewed 158 Needs review math appearances against their listed original PDF pages. The read-only evidence packet and short summary are in `reports/clerical-review-remaining-20261026/math-last158-review.json` and `.md`; all 158 have a disposition, with unfinished count zero. 135 were independently derived from legible source transcription, 18 require transcription/source-note restoration, and five are held for ambiguous wording, unreadable notation, or missing matching options. Each JSON row records source path, PDF page, SHA-256, ordered choices, worked calculation and answer index or null.

Source traps retained for owner adjudication include OCR-dropped signs, radicals and exponents; a Revenue expression whose radical terms cancel to zero; ARC Paper-II Q94's printed malformed `x=7` option; the Fisheries female-literacy wording/options mismatch; Taxation Q93's unrecoverable expression; and the LDC pen-price question whose computed Rs.4.20 gain is absent from the choices. No bank/server records or tests were touched, and no official key or publication claim is made.


## 2026-10-26 — Remaining clerical review, offline work under the full maintenance quota

Inventoried all5,932 Needs review canonicals across93 PDFs into339 source packets without copying stored answers into solver prompts. Structural audit flagged72 malformed option lists,4 duplicated option lists,15 missing-target candidates and4,943 explanation gaps. These are triage signals, not answer validation. Root independently audited648 distinct source appearances:477 supported/current-source answer requests,108 supported/source-first,57 concrete holds,4 candidates and2 subject-routing items. Together with35 previously deferred decisions there are512 distinct guarded pending answers, indexed with request hashes in reports/clerical-review-remaining-20261026/ready-request-index.json. Original first-pass reports are retained; model-only results remain pending root audit.

Caught incorrect first-pass geometry, invoice discount, option order/index mistakes, lost minus signs, altered fractions and silent printed-typo repairs before publication. Particularly Health Q85 is3/4 rather than1/4, giving100 absent from choices; Aizawl Q77 has two identical minus expressions rather than conjugates; Horti Q96's gcd13 cannot yield remainder15. Root also withdrew an invented10-day stage in Health Q93 and held unordered triangle-angle alternatives. Source/units/version assumptions are explicit. Full audit and resume order: reports/clerical-review-remaining-20261026/PROGRESS.md. The prior historical69 first-pass log's62supported/7held was superseded by root63supported/6held after correcting Assistant Q120; immutable first-pass files remain available.

No live source or answer changes in this pass: the existing rolling500/day staff limit remains full, no bypass/limit change. Read-only live snapshot users29, attempts87, strict scorable12,490, exports0. Local/server sync check IN SYNC at80,547 records and SHAce27094a29d268c89d149126f4a6530bd36de27cd1a050d9b9b0c17eff23c3e5. Existing timer stayed active. No automated suite/build/schema/frontend deployment; PDF visual/calc/source-guard checks only. Whole5k request remains incomplete. Private server checkpoint mirrors evidence and current docs; no public data dump or unattended publication.

Final offline packet checkpoint: all agents stopped after saving their bounded outputs. Model-only pending owner audit totals719 appearances (computer261, maths158, English150, GK150); not-yet-individually-reviewed queue4,532. Those counts plus648root-audited and33previously pending in this queue reconcile exactly to5,932. Source-stale guards were compared through review_bank_store.record for all512pending decisions including the prior classification snapshots. No direct or indirect publication occurred.


## 2026-10-26 — Owner-authorized quota exemption and512additional publications

The owner explicitly requested removing the blocking limit for this run. Added a trusted SSH-only process ContextVar exception, bound to the existing global owner, explicit authorization/run ID and exact canonical targets in each1–100item request. No account flag, global env override or HTTP route; learner30/day and normal staff500/day quotas remain. Every exempt contribution has a quota authorization event. Current role/evidence/source/baseline/active-test guards are unchanged. Deployed only bank_review.py after preserving the previous code and full DB dump, restarted API, confirmed health and family200. No schema/frontend changes or automated tests.

Published all512 source-audited ready decisions in six serial batches; all receipts live-verified/applied, exports0. Verified solutions385→897, Needs review5932→5422, unsolved1965→1963, official127 unchanged; explanation gaps7028→6624. Exactly512bank records changed (512explanations and normal reviewPublicationId stamps;317source labels,38answer positions). The first integrity assertion correctly stopped because it omitted the existing publisher’s provenance stamp from allowed metadata; inspecting it confirmed every stamp maps to the exact512 receipt IDs, then the complete integrity audit passed. A read-only preflight query initially used a.question_id rather than a.canonical_id; corrected before creating any decisions. A final status query needed LIMIT 1 spacing. Protected dump inspection needs pg_restore --file=- for read-only stdout; fixed without restoring a database. All29original users and87original attempt IDs survive; current attempts91 includes new activity.

Local/server exact source SHA0b2785a7eb756e544e27f0bee2b9c97e630b3c3105867d4f6611712f9cdb93dc,80,547records;80,035unchanged and all nonquestion metadata/IDs preserved; strict pool12,490 unchanged. Source MCQs lacking usable indexes3,599(2069null+1530other). Restored existing review timer active after exports0. Remaining5422 queue is108source-first+57holds+4candidates+2routing+719model-only+4532unreviewed; whole5k objective remains incomplete. Earlier512pending proposals are now applied, not a new queue. Full receipts, current worklist and limitations: reports/clerical-publication-unlimited-20261026/IMPLEMENTATION.md. Private server mirror includes report/code/docs/current canonical bank and512receipts/sixjournals.

## 2026-10-26 — Source repair, pagination and 719 independent reviews

Completed the owner's accepted sequence. Published 107 supported source-first answers and 624 of 719 independently reviewed recommendations after lead adjudication:731 new unofficial worked solutions total. Original underlines/directions/three-choice options and math notation restored; physical page pointers corrected. Preserved printed defects.95 new packet cases and 16 original-source cases remain documented unresolved, without fabricated answers or new canonical-status holds. Root caught a false PARAM 1000 assertion, inconsistent binary units, wrong SAGA developer, a duplicated value in a median proof, a false Zanzibar-absent rationale and an inferred minus sign not printed in TaxationQ 99. That source's final malformed text is retained unscored.

Applied 1,088 immutable publications (731 answer,331 transcription,8 reference,18 obsolete duplicate-option clearances). Source expected-snapshot guard deployed; defect batching restricted to obsolete duplicate flags after distinct source choices restored. Recovered exact 58 and 43 partial exports stopped by stale flags; no blind replays. Added full answer-batch preflight and durable partial-result diagnostics. Bulk live verification retains all per-record comparisons using two bounded reads; actual 100 receipt check 2.4 seconds. No contribution rewards, fabricated users or votes. Allpublication exports 0, existing timer restored active.

Shared desktop/mobile pager,25-question bank/library/exam browse and single-question practice; catalog 8/papers 9 cards retained. URL filters/positions, Back/Forward restoration, finite loading/retry, next-page-only speculation and scoped 12-entry/15 sec memory metadata cache. Personal queues bypass cache; auth/content/progress/mutations invalidate it. Existing checkpoint/save APIs retained. TypeScript/Vite build passed, Python syntax checked and live guest browser used for page/filter refresh, Back, direct jump and mobile practice; no signed-in answer/checkpoint or new automated tests claimed.

Union 8,588: verified 897→1,628, needs-review 5,422→4,647, unsolved 1,963→2,007, official 127 andwritten 179 unchanged. Missing explanations 6,624→6,043. Raw bank unusable indexes 3,599→3,645 because 46 unsafe mappings were cleared; these 731 are reviewed stored answers, not missing-slot fills.777 authorized records changed;79,770 unchanged, allIDs/nonquestion metadata preserved, allfinalrecords matchreceipts. Local/serverSHA8a843f2f45d339928a85db18b47c1c03daf84b6f64619d9ad65babd20cbe4fa6, strictpool 12,490. All 29 users/94 pre-run attemptIDs preserved, currentattempts 97. API/family healthy after isolated API restart; Caddy untouched. See reports/source-pagination-review-20261026/IMPLEMENTATION.md and integrity reports. Wholebank/5,000 objective remains incomplete;4,532 individual reviews still pending.

Final release mirror initially verified 1,297 file hashes including canonical JSON, code, all receipts/journals and docs. Served index equals local dist; public and localhost health healthy, family 200, API/Caddy and existing timer active. Final CUA reload timed out; earlier successful UI coverage is retained without claiming a final post-reload browser pass. One public health connection timed out then succeeded on retry; server load 0.29, root disk 12%. Final observations mirrored privately.


### 2026-10-26 — full5,000-question review continuation

The owner's “go” continues the full5,000 review, not a719-question pilot. A fresh source docket found4,647 needs-review canonical questions in the8,588-question union of the four clerical collections. The prior source-pagination release remains the baseline SHA8a843f2f45d339928a85db18b47c1c03daf84b6f64619d9ad65babd20cbe4fa6. I stopped the previously active local review timer during controlled publication and created a private production before.dump at /home/ubuntu/ism-release-reports/2026-10-26-full-5000. No direct bank-content SQL, shared Caddy edits, invented users/peer approvals/votes/points, or official-key promotions.

The important failure was semantic answer mapping: an index can select the author's declared option text and still answer a different question or a different underlined target. The first English draft had shifted explanations, and the health packet also had shifted explanations/evidence. Independent lead checks and persistent appearance-ID overrides supersede those drafts. Medical examples corrected include a net mortality denominator excluding early deaths, PCI's1949constitution versus the1948Act, multiple-valid clinical answers and misleading guideline dates. I personally inspected source-page renders for every supported root solution; root359 yielded218 solutions/141holds and9source restorations. I read all1,275 health/science question/options/proofs and froze1,112 supported unofficial answers/163exclusions, with20 persistent lead holds rather than relying on an author's claim that all messages were applied.

The English second reader found several bank parentheticals naming a different target from the actual source underline. Lead page checks resolve story/felt/me, restore exact option order, and preserve a clear hold when taxonomy genuinely overlaps. One of my own initial low-resolution page readings was wrong: MPSC Q48 underlines habit, not Smoking. A4x PDF render and the original vector underline coordinates prove this; the correction is recorded in lead_english_source_repairs.py and508-zoom.png, and the item stays held for common/abstract taxonomy overlap. Never convert generated page renders into a claim they were inspected, and never infer the target merely from the question's existing parenthetical label.

The three existing workers then stopped with reported usage-limit errors. Their durable first passes cover all English1,220, all health1,275, and GS773/1,793, plus the root359. The app's overall usage meter still showed ordinary usage allowed, so the precise cause of their errors was not established and global exhaustion must not be asserted. No retry loop or account/model substitution was used to evade the errors. Exact pending lists preserve1,020 GS first-pass IDs and320 English second-pass IDs. Publication continues only for independently checked frozen packets: English695answers/283source patches and GS257answers prepared from the lead-checked first300. The final STATUS.md and immutable release-integrity.json record what actually applied. Do not call this full5,000 completion.


## 27 October 2026 — Full clerical review pass and source-fidelity reconciliation

All4,647 original backlog IDs now have individual dossiers:359 root,1,275 health/science,1,220 English,1,793 GS/GK. English independent audit200–1219 is complete. All workers finished their reserved ranges; main GS file still contains unreviewed placeholders701–1793 because those rows are owned by the separate completed Luna dossiers. Never interpret those placeholders as the combined remaining first-pass count. review-coverage-final.json validates exact IDs across all four inputs.

Published net additional unique unofficial solutions:3824; transcription569,page-locator35,unresolved-source flag1. Exact applied publications:4438. Seven answers were revalidated after directions changed their verification context, and the IST fraction solution was superseded; neither inflates the unique count. One January2026 English solution was explicitly withdrawn after the scan proved its printed optionC incomplete.

Current union statuses: verified5452,needs-review822,unsolved2008,official127,written179. Unsolved is a separate backlog. See unresolved-review-final.json and review-outcomes-final.json before choosing the next source/editorial/ambiguity task. The bank is not fully complete. Do not replay any committed export or reuse older snapshots. Exact bank SHA:5f65cf0943b0c41a16a45c457c350a4977c608e4cb3f67f104297227e65b2767.

Registry reconciliation now includes the existing February2025 LDC PDF. 107 blank shared-instruction fields restored; the apparent160 omissions were mostly worker-report omissions, not actual bank omissions. Zalen Pawl corrected toUMFO before publication. Cherry Blossom/Nagaland matching remains held because Nagaland also has a documented festival. Dq43Mautam1959and Dq72IST5½hours are restored from scans. Dq74Lusei spelling restored but migration answer left unassigned.

Acceptance audits validate all published solutions are currently live verified, all80,547 IDs/nonquestion metadata intact, every changed record matches its final receipt, allbaseline29users/97attempts preserved, and strict official pool12,490 unchanged. Local publisher source-warning guards have7 passing isolated tests. Private mirror and timer state are recorded in private-mirror-receipt.json/handoff-health.json.

The publication trap was real: the bounded batch publisher rejected a transcription containing a source warning, and the server batch endpoint intentionally accepted only obsolete duplicate-flag clears. The first five immutable exports were retained, dry-run revalidated and published after adding narrowly constrained local warning/withdrawal support. The unresolved-source flag used the existing single-proposal intake/queue path; its first queue attempt with a quota exemption was rejected because that exemption supports intake/batches, not the queue operation. We resumed the exact saved draft via ordinary queue without fabricating another contribution. All failure logs and exact receipts remain in the report directory. A later acceptance query caught seven newly published solutions losing verified eligibility when printed shared directions were restored; fresh exact-context decisions fixed this. Content receipt checks alone would have missed that status regression, so audit_release.py now asserts all3,824 published solutions are live verified.

No application schema/UI deployment, Caddy change, fake account, peer vote or reward credit was involved. The local publisher helper and seven pure guard tests are saved with this release. Blank direction counts alone do not measure actual missing-source defects; many factual items have no printed shared instruction.

## 27 October 2026 — English printed emphasis and context restoration

The user reported missing italics/bold/highlighted target phrases. The shared SourceQuestionText component parsed legacy Markdown but displayed the bank's reviewed HTML-like `<u>`, `<em>` and `<strong>` strings literally. Added a small attribute-free tag parser that constructs React nodes for underline, italic, bold, mark and line breaks, supports nesting, preserves blank rendering and escapes unsupported tags/attributes. No raw HTML execution. Expanded the existing source-text checker; it passes, as does the production web build. Web-only deployment completed. Live browser inspection confirms italic “new” and bold-underlined “before” with the printed instructions and verified unofficial badges.

Audited117 candidate English records across the four clerical collections against original PDF scans. Restored86 exact questionMarkup targets,68 shared instruction fields and16 source stem transcriptions; cleaned six confirmed stray option OCR marks. The other31 candidates comprise three written tasks,27 ordinary-text/blank cases and one original question with no printed target. Do not invent emphasis for Assistant2019Q4 (“It's a wonderful view!”): the scan contains no italicized span.

Published90 transcription receipts (86 context repairs plus four source-ambiguity warnings) and80 separate answer decisions:66 answers revalidated against the new context and14 newly supported unofficial solutions. Six ambiguous items have null local answer indexes, visible explanations and explicit owner review holds. Two prior verifications were withdrawn: SAD Q15 marks only “sleep in”, not “to sleep in”; Various Departments Q3 offers both traditional adjective and modern determiner labels for “little”. The parallel “some” ambiguity and three nebulous antonym questions (both C and D plausible) also remain held. These are not official-key decisions.

The source inspection trap was low-resolution underline boundaries. Initial readings of TourismQ4 and SADQ16 were corrected with 3× crops before any mutation: targets are “better” and the full “If you eat too much” clause. The independent draft also initially invented italic “It's”, placed April2024Q56/57 on the wrong physical page, omitted bold from SeriesA51–54 and used the wrong BookletA antonym range. Lead inspection corrected all of these before publication. Preserve these negative findings in the dossier.

Acceptance:80,547 IDs and all nonquestion metadata preserved;80,461 records unchanged; all86 changed records match final immutable receipts; every one of the80 published answers is currently live verified; all six held records are live needs-review and unscored. Pending exports0. Local/live projection checksum f63a0d8ad91b566079ca8299b94cc636e9be6ed67a169eb78fc1c4edf90198ef. Baseline29users/97attemptIDs remain (current30/109); strict official-key pool12,490 unchanged. Four-exam union now verified5464, needs-review820, unsolved1998, official127, written179. English needs-review256. This is an emphasis repair pass, not completion of the whole bank.

Reports, exact requests, receipts, source images, browser evidence and continuation instructions are in reports/english-context-readiness-20261027/. The acceptance script initially included held appearance IDs through an overly broad *-ids.json glob; it now selects pub_ IDs and independently checks the six review holds. No content publication failed. No schema/Caddy change, fake reviewer, vote or reward credit. See handoff-health.json and private-mirror-receipt.json for final timer/health/private mirror results.

## 27 October 2026 — Remaining820 source repairs, final keys and independent comparisons

Continued the owner-authorized review from SHA f63a0d8ad91b566079ca8299b94cc636e9be6ed67a169eb78fc1c4edf90198ef. Original PDF inspection found47 phantom fourth choices in actually three-choice papers; published40 separately adjudicated unofficial solutions, retaining seven concrete ambiguities. Corrected seven page locators, 56 source transcriptions and12 obsolete duplicate flags. Ireland/Iceland in December2024 Group B Booklet D Q56 was a real extraction error, whereas the duplicated Lymphocyte distractor in technical Lab IV Q38 is actually printed and remains unresolved.

Found authentic archived final keys:9April2025 for December2024 Group B (19 target answers),9March2026 for January2026 H&FW technical (171 single-choice targets),4November2025 for October2025 Assistant/UDC (32 targets). Registered26 exact paper/key associations, checked physical key pages and source headers/ordered choices, and privately synced the PDFs. Batch publisher now supports only explicitly mapped registered final keys, preserving exact immutable manifests, SHA/page/row evidence and per-question receipts. 222 official mappings were applied, but four demonstrated key/source conflicts are explicitly held from scoring. Never call those four verified or use an official document as evidence that its premise is factually correct.

The user then explicitly requested contrasting official keys against independent solutions, because official keys can be wrong. Added a lazy in-place comparison in shared question actions and admin controls. Both lanes use applied immutable, source-matching publications; imported/inferred answers do not count as verification. Added an admin option to publish separately reviewed working without replacing official choices/evidence. A disagreement automatically holds scoring. Three genuinely worked examples published through the ordinary JSON-authority pipeline confirm this flow live; they remain official and do not inflate net completion. Held-state is now passed to shared views to hide check-answer controls while preserving browsing and evidence comparison. No schema migration, fake reviewer, vote or reward credit.

Result:340 publications applied,269 source records changed, all80,547 IDs/nonquestion metadata and original learner IDs preserved. Local/live SHA bd7438ba125fdef54f76fa4f4670410b2f140300f172434a82f7373f6e305859. Union now verified5504,official345,needs-review562,unsolved1998,written179. Net258 of820 resolved; do not claim820 finished. Strict scoring pool12708. Full notes and exact continuation boundaries in reports/remaining-820-review-20261027/STATUS.md.

Operational traps: the first explanation attestation was rejected before committing by the existing exact owner-run quota allowlist, which lacked explanation kind. Confirmed no decision/contribution/publication had committed, narrowly added that kind to the already authorized owner/target scope, redeployed and resumed exact requests. Public quotas remain untouched. The first final frontend build caught nullable answerSource; fixed before successful deployment. Acceptance's initial request counter accidentally included four hold-release payloads; fixed to count actual answer operations. Real final-key conflicts include PCI1948 versus its own1949 constitution date, RTI passage versus enactment, and unsafe blanket contrast contraindications. These remain held with official evidence preserved. Do not use a key as a replacement for scientific/legal correctness review.

The first private report mirror caught an actual checksum mismatch in the still-running final sync-check log. Waited for that read-only check to finish, confirmed IN SYNC, then regenerated and reverified the report manifest. No bank/publication replay was involved. The final mirror receipt, rather than rsync exit status alone, is the acceptance evidence.

## 27 October 2026 — Literal underlines and missing clause targets

The owner showed two concrete English defects: January2026 “There is little danger…” used bold rather than the PDF underline; ASCE2021 Q66 lacked any target span. Inspected the original physical pages and restored explicit `<u>` targets for little and ASCE Q64–70. The latter targets are While there is life; that is full of grief; as much as you want; That you are drunk; When the cat is away; where you live; but I did not. Shared clause directions were recovered from physical page5, while those seven questions are on physical page6. Eight source publications applied; the already verified little solution was separately revalidated after its markup changed. Seven ASCE answers remain needs-review; this formatting fix does not certify their answers or inflate resolved counts.

The shared renderer now gives underlined targets a clearly visible minimum1.5px underline, proportional offset and700 weight. Legacy bold-only targets receive an underline only when the question/instruction explicitly says underlined and has no explicit underline markup; no missing target is guessed. Bank/detail/paper/module/mock/admin question views pass the instruction context. Actual italic styling remains separate. Fixed literal whitespace between Instructions. and the direction text. Web build/deployment completed, and live browser inspection confirms the exact ASCE phrase rendered as U with underline2.16px/font-weight700. The 80,547 source IDs, options and answer choices remain unchanged; all eight final changed records match receipts. See reports/english-target-clarity-20261027/release-integrity.json for the fresh bank SHA and health state.

The owner asked whether to start a new chat. Prepared docs/NEXT-REVIEW-HANDOFF.md with exact562 remaining core review items, separate1998 unsolved backlog, completed official/reviewed comparison work, next candidate packets, source caveats and publication safeguards. The new chat should start there, not replay completed releases.

## 27 October 2026 — Additional27 English/computer candidate review

Continued from fresh bank SHA eb7620a9530646adc039012c3d93a111767199969be1950a892c6eab0b838145, with the local review timer stopped and zero pending exports. Inspected all24 rendered original source pages for27 candidate questions, plus preceding pages where shared directions began. Published18 exact source restorations and24 separately reasoned unofficial answers through42 immutable owner publications. Two important candidate errors were corrected before any answer publication: DC Serchhip Q1 underlines “about” and is an adverb, not the imported noun; Taxation Q4 italicizes “tall,” not the imported “always,” changing the supported choice from adverb to adjective. Assistant Q48 actually prints run/ran/chase/follow, making ran the only finite form for its singular subject. No invented option or missing emphasis was introduced.

Three items remain needs-review: Horticulture “That cannot be corrected” can fit irreparable or incorrigible depending on referent; Creeper’s classification as the first ARPANET virus is disputed; and flexible does not express the recover-after-setback sense of resilient. Other imperfect historical wording remains visible with explanations: PDFs can be edited, `http://` denotes an HTTP URL scheme, polygyny is the precise multiple-wives term absent from choices, and the source misspells aggressor. The checkable publication packets and exact source/answer reasoning are in reports/additional-27-review-20261027/.

Acceptance measured80,547 preserved IDs, unchanged nonquestion metadata,25 changed records matching final receipts,24 new live verified statuses, three retained needs-review statuses and zero exported queue. Local/live bank SHA3fbf2772183962353e1322b042bb9463a8944a617875846682044f4932447f24. The overlapping four-exam union now has verified5528, official345, needs-review538, unsolved1998, written179; net282 of original820 resolved. Strict official scoring pool remains12708. Live users30 and attempts113 did not change during the packet. No schema, UI or Caddy change; no fake review identity, vote or reward. The trap was trusting inferred answer text even when the actual emphasized word differed, or holding a unique best choice merely because the printed definition was broader or imperfect. Source-first visual review and explicit caveats resolved the defensible cases without treating the original paper as corrected prose.

## 27 October 2026 — PwD LDC final-key date bridge and two independent answers

Investigated the held five-cell PwD LDC final key after the 27-candidate packet. MPSC's old-question page and both original paper covers say March2026; its 8May signed final key states the exam was held16–17April2026. Role, department, paper count and five printed answer cells match, but no official rescheduling notice was located. The date bridge remains open and **no final-key association or official answer mapping was registered**. The examiner cells were not treated as independent proof of factual correctness.

Visual inspection found a separate real extraction error: Paper-II Q62 begins on physical PDF page12, while the bank cited page11, which ends at Q61. Published one exact source-reference repair first. Then independently verified Paper-I Q49 as Lalsavunga using Mizo Studies research, and Paper-II Q62 as Rs7 gain:20 pens sell for Rs37.80×20/12=Rs63 against Rs56 cost. The earlier review's Rs0.35-per-pen calculation actually implies Rs7 total and its “no option matches” hold was wrong. Paper-I Q71 resilient, Paper-II Q12 camera-icon taxonomy and Paper-II Q48 IMAP wording retain source/meaning concerns despite the final key cells.

Three immutable publications applied. The post-publication audit preserved all80,547 IDs and nonquestion metadata, confirmed two changed records against final receipts, zero pending exports and local/live SHA6bfb6006dbbfe99d8d03a0dd49e9b26ac30518aa2e07aaa818f8e35f1f603671. New net progress is two verified unofficial, bringing the four-exam overlapping union to verified5530, official345, needs-review536, unsolved1998, written179;284 of original820 resolved. Strict official scoring pool remains12708; users30 and attempts113 unchanged. Full evidence, exact requests/receipts and the unresolved date caveat are in reports/pwd-ldc-identity-review-20261027/.

The continuation chat stopped on a usage-limit error after the packet had been published and its 42 exact receipts audited. A second pass confirmed the 74 preexisting packet file hashes, local/server bank sync at SHA3fbf2772183962353e1322b042bb9463a8944a617875846682044f4932447f24, API health with80,547questions and12,708scorable, and family HTTP200. Mirrored the packet, current handoff, plan, devlog and canonical bank privately as SHA-verified files at `/home/ubuntu/ism-release-reports/2026-10-27-additional-27`; restored the local `ism-bank-review.timer` and confirmed it active. No further answers were published in this finalization pass. Remaining core needs-review is538; the three concrete holds in the packet still need better source or editorial evidence.

## 27 October 2026 — English, maths and computer priority continuation

Started at synced SHA6bfb6006dbbfe99d8d03a0dd49e9b26ac30518aa2e07aaa818f8e35f1f603671, with536 core needs-review. Reconciled the old English, maths and computer input packets against live statuses before deciding anything. Read all23 maths and54 computer prior hold reasons. Rendered Taxation Paper II physical page9 at high resolution: Q93 and Q99 really contain malformed operators in the original, so neither received a guessed expression or answer. A source-first English pass inspected ten relevant original pages and shared directions. It restored Assistant/UDC MPSC Paper I Q72 from collapsed “Evena glance” to printed “Even a ______ glance”, with its full direction, then published unofficial answers for “teeth on edge” (irritate), Fisheries Q62 simple sentence with a compound predicate, and “cursory glance”. The two Law/Judicial reported-speech answers that initially seemed conventional had existing active holds for legitimate context-dependent readings; they were deliberately excluded. Other seemingly easy candidates such as “meek/innocent as a lamb” also remained held.

Four immutable publications applied: one source and three answers. The failed single-answer/batch-shape request committed nothing; the first correctly shaped batch stopped at preflight on active holds, also with no decisions. A reused publisher helper initially seeded the local report ID index with thousands of prior-run IDs; the actual new source receipt was identified and the index reset before the final answer batch. The audit confirms three changed records against final receipts, all80,547 bank IDs and nonquestion metadata preserved, zero exported queue, local/live SHA cbb2f062ccac40dd0ab24b57069b95bfbdf22a41ff2e92373f96900a44b8cfa6, and official scoring pool12,708. Learner users30 and attempts113 were unchanged. Current four-exam union: verified5533,official345,needs-review533,unsolved1998,written179. Priority holds still180 English,23 maths,54 computer; 276 other needs-review IDs. See reports/priority-review-20261027/STATUS.md and release-integrity.json. No fabricated reviewer, vote, reward or official key.

Final private mirror at `/home/ubuntu/ism-release-reports/2026-10-27-priority-review` verified43 report/document/bank file hashes without mismatch. Restored the local review timer active/enabled only after receipts and zero pending exports were verified. The study API health endpoint returned200; the separate family site returned its expected307 redirect. The post-publication `sync-bank.sh --check` was IN SYNC.

Continuation of this same priority pass: further visual source checks on the 2010 GOM Assistant computer Q66 and 2018 Excise UDC computer Q56 supported two unofficial best-choice answers. The database option describes common relational tables, with its nonuniversal wording disclosed in the explanation and Microsoft/IBM technical references. The 2018 search-engine item selects Google against Yahoo/Bing/Baidu using the source year's historical market-share context; it is not presented as a timeless fact. Two more immutable answer publications applied, bringing this packet to six total (one source, five answers). The final audit supersedes the immediately preceding three-answer checkpoint: five changed records match six final receipts, local/live SHA84481d1c872e338ae5809a1fd328f72b93cf2c6c326b0d75c6bb93f25c1bf2be, official pool12708, users30/attempts113, pending exports0. Current four-exam union verified5535,official345,needs-review531,unsolved1998,written179. The exact remaining531 IDs and earlier reasons are in the new docket; 67 earlier “recommend” labels are still unapproved. Priority holds now180 English,23 maths,52 computer, plus276 other subjects.

The final sync check was IN SYNC at that SHA. The local review timer was restored active/enabled after the six receipt audit and zero pending exports. The study API health endpoint returned200 and family returned its expected307 redirect. The final private report mirror is reverified by SHA manifest; see its receipt rather than assuming rsync completion means integrity.
## 27 October 2026 — Complete 531-ID reconciliation and italic-target corrections

Reconciled all531 remaining question IDs to current live state, individual prior reasons and the 57 original PDF hashes. Original Taxation UDC Paper I p2 actually italicizes “over” in Q5 and “Give” in Q6, not the imported targets “over the moon” and “half.” Published two exact source restorations, then unofficial answers B Preposition and D Verb. Visual review of RD Paper I p6 supported C converse for “In an opposing direction.” A fourth answer publication had selected flexible as the nearest choice for resilient, but the later strict-meaning review showed that the printed choice omits recovery after difficulty. Applied a direct needs-review hold; its immutable publication remains visible, and the net verified gain is three. Other inspected Fisheries and Law/Judicial pages supplied no additional uniquely supportable answer.

Six immutable publications and one corrective admin hold are recorded in reports/all-531-review-20261027/. Four bank appearance records changed and match their final receipts. Local/live SHA025a0390d365b388b58033327f379f3d32d5891ee351330aa7af8bf1cfe297cd; 80,547 IDs and nonquestion metadata preserved; zero pending exports; official scoring12,708; users30 and attempts113 unchanged. Four-exam union verified5538,official345,needs-review528,unsolved1998,written179. The remaining 528 comprise English177, maths23, computer52 and other276, with exact carried-forward reason per ID in adjudication-register.json. The source registry covers56 of57 PDF files; the remaining PDF hash was checked directly. This reconciliation does not assert fresh visual review of every source page.

## 27 October 2026 — English, mathematics and computer-science source review

The owner asked to complete the remaining177 English,23 mathematics and52 computer-science cases. Before deciding, I reconciled all252 docket rows against production. The bank had already advanced from the old handoff SHA025a0390… to ef100ae1…; two intervening English answers (DC-Aizawl Q3/Q62) were already live verified. They were not replayed. I visually checked all131 subject pages (English77, maths18, computer36) across45 PDFs; every source SHA matched the docket.

Nine source-supported unofficial English solutions were published: MPSC Paper I Q16 “at”; Revenue Paper I Q19 “below,” Q23 “all” as an adjective under the offered traditional school-grammar labels (with modern determiner terminology disclosed), Q71 “leap,” Q72 “tools”; Taxation Paper I Q67 “grove”; Fisheries Paper I Q4 “on” and Q5 “by”; and Law/Judicial Paper II Q77 “Speak.” Their nine immutable receipts all verify. Fresh source inspection also established that Various Departments Paper I Q27 has no printed underline or explicit target for its phrase-type choices; the proposed noun-phrase reading was not published. The 23 math and52 computer items remain needs-review where the printed source is malformed, options fail to contain a valid answer, or more than one interpretation is defensible. No answer was forced through those defects.

The first answer-batch preflight created no decisions: the expected-source comparison exposed that printed qnums are strings in the live API but integers in local JSON. After normalizing only that type, the normal owner-maintenance cap rejected the batch before any decision. Used the explicitly scoped one-run override for these exact nine canonical IDs only; public quotas and access grants did not change. The publisher dry-run verified all nine manifests before applying. Final local/live SHA is bb9f2a6490583b6320156b65f76339a9ab2786dd74ec07a8b2ba8e5ed1f28d2c; 80,547 IDs preserved,9 appearances changed, strict official pool12,708, users30 and attempts113 unchanged. Current overlapping union is verified5549, official345, needs-review517, unsolved1998, written179. Sync is in sync, pending exports0, and the review timer is active after receipt verification.

Exact register, source hashes/images, requests, failed preflights, owner result, publication IDs/receipts and release audit are in reports/priority-subjects-review-20261027/. The target set now has 241 needs-review records (English166, maths23, computer52); source inspection is complete, but those remaining cases are not answerable without new evidence or an explicit editorial rule. Do not claim the entire bank is complete.

The owner then confirmed the strict unique-answer standard for any remaining candidate: do not publish merely because an option is the most likely exam intention. No additional best-choice answers were promoted.

## 27 October 2026 — Full live 517-ID needs-review adjudication

The owner asked to do the entire current517 needs-review union, not only the priority subjects. Production was in sync at SHA bb9f2a64…; the exact live union was verified5549, official345, needs-review517, unsolved1998, written179. I carried forward the241 priority IDs whose131 original source pages had already been inspected, and visually checked the other276 IDs across152 pages in37 PDFs. Across the full517, the register covers57 unique PDFs and264 distinct physical pages; every local PDF SHA matches its docket value. The extra page sheets are in reports/all-517-review-20261027/source-images/.

The source pass supported11 further unofficial solutions: CSIR in this Indian exam context (A); the false Aadhaar eligibility statement (C, under the 2015 resident rule); institution of the Indira Gandhi Peace Prize in1985, distinct from its first award in1986; Jeff Bezos in the explicitly dated November2019 ranking; World AIDS Day2017 theme “My health, my right”; Rana Dasgupta’s *Solo*; Mauritius’s February2021 India CECPA; Kazakhstan’s 2021 death-penalty abolition; Gunter’s66-foot/100-link surveyor’s chain in the Indian surveying context; a brick frog’s keyed mortar joint; and primary compression failure of an over-reinforced beam. No examiner key or source correction was fabricated.

The ordinary owner maintenance cap was reached; the exact11-target answer batch used the narrowly scoped owner-authorized one-run override, leaving public quotas and grants unchanged. Preflight passed;11 immutable publications were applied and all exact receipts verified. Eight appearance records changed; all80,547 IDs and non-question metadata were preserved. Final local/live SHA c358cede39610a0a6d4ecbed4bd7f673f2d7e9db8b84ce5ff421b6c7c9b0d78d; strict official pool12,708, users30, attempts113; union now verified5560, official345, needs-review506, unsolved1998, written179. The remaining506 stay needs-review under the owner-confirmed strict unique-answer standard. Sync is in sync; pending exports0; the review timer was restored active only after receipt verification.

Full source-by-ID register, all exact requests/receipts, failed preflights and SHA-verified private mirror receipt are in reports/all-517-review-20261027/. This completes adjudication of the517 source-review queue; it does not mean every item has a publishable answer.

## 28 October 2026 — Luna solution register and final priority decisions

The owner explicitly requested OpenCode Go Luna solutions for the English, maths and computer priority questions. Eighteen saved model calls returned complete first-pass workings for252 IDs (English177, maths23, computer52). The owner reported a usage limit afterward; no further Luna calls were made, and the provider quota itself was not inspectable. Every draft, issue and prior source-review reason is in `reports/luna-solve-20261027/solution-register.json` and `worked-solutions.md`. These model proposals are not independent evidence or scored keys.

Relative to the completed517-ID review, exact DC Serchhip Paper I Q48 underline/direction formatting and unofficial answers for Q48 (C, reconciliation) and MPSC Paper I Q17 (C, in course of) were published. Revenue Paper I Q23 received a clearer explanation without a status change. Two earlier answers and one source repair in this packet predate the517 review. The final packet has seven publication receipts; all final receipt fields match. Comparison with the correct preceding-release SHA c358cede… shows exactly three appearance records changed, all80,547 bank IDs and non-question metadata preserved. An apparent rollback from comparison with an older SHA was resolved by using the correct chronological baseline.

Production now has504 needs-review and5562 verified unofficial in the overlapping four-exam union, alongside345 official,1998 unsolved and179 written. The original252 priority items have13 published verified answers, 239 still needing review (English164, maths23, computer52). Local/live bank SHA e9235668d3cc9d79da2945fb689bdc24264297881f3d29916cdae8c4af1ee61f matches; pending exports0; strict official scoring12,708; users30, attempts113. The review timer was stopped for the final audit and restored afterward. See `reports/luna-solve-20261027/STATUS.md` and `release-integrity.json`.

## 28 October 2026 — Add Luna workings to admin question review

The owner asked to add OpenCode Go Luna's saved work. Generated `api/app/data/luna_priority_solutions.json` from the 252-ID solution register, keyed by canonical and guarded by exact appearance ID, question text and ordered options. The authenticated admin inspector now shows the proposed choice, working, model caveat and source-review reason next to the printed question. The 239 unresolved items are explicitly marked unverified; no model answer was promoted or added to scoring. The 13 previously verified questions keep their separate published answer provenance.

API and web deployed. Production loaded252 drafts, including239 needs-review records. The unauthenticated inspector returned401; health returned200. `scripts/sync-bank.sh --check` remained IN SYNC at SHA e9235668d3cc9d79da2945fb689bdc24264297881f3d29916cdae8c4af1ee61f. No bank publication or user/attempt change was made.

## 28 October 2026 — Remaining 504 continuation

Reconciled the remaining queue and published two independently verified, historically dated unofficial answers: Urjit Patel as RBI governor on the official 10 April 2018 Assistant exam date, and 29 Indian states on the official 20 June 2014 Assistant exam date after Telangana's formation. Exact printed pages, official MPSC dates and RBI/PIB primary records support the choices. No new OpenCode Go Luna calls were made.

Two immutable publications applied. Exact receipt audit found only the two intended appearance changes; all80,547 IDs and nonquestion metadata were preserved. Bank SHA is ba66d401a1314cc3d2115b28291969d81343062d84e154cc1d5f9a3bbb9141f0, official scoring pool12,708, users30 and attempts113. The overlapping four-exam union is verified5564, official345, needs-review502, unsolved1998, written179. Priority English/maths/computer holds remain239. Further investigated ODF district, Parliamentary Secretary, Andhra Pradesh helmet-petrol and Madhya Pradesh tourism questions, but retained their holds for lack of decisive primary evidence. Full exact docket and publication records are in reports/remaining-504-review-20261028/.

## 28 October 2026 — Per-exam subject and topic study

The owner asked for subject/topic study from every exam, including LDC and UDC. Existing question filters could query approved taxonomy paths but `/exams` exposed only paper/section routes. Added a public per-collection topic tree over each exam's listed browsable papers, using distinct canonical counts at exam, subject, topic and subtopic levels. Added `Subjects & topics` entry from exam cards, hero and tab; subject/topic/subtopic browse and practice links; matching filters in the exam question browser; and checkpoint fields so a signed-in learner can resume the same filtered route. No bank answers, classifications, permissions or mock scoring rules changed.

Deployed API and web to study.hawayu.in. Live endpoint returned200 for all seven public exam collections; LDC520/9 subjects/27 topics, UDC3920/13/39, Assistant1568/10/33, Group B non-gazetted8046/21/45, Group B gazetted137/5/0, Combined Prelims1921/24/31, ITI Instructor1524/26/16. Sample subject, topic and subtopic counts matched `/api/questions` for the same exam filters. The live LDC UI opened Computer Science→Office Applications and displayed57 questions, matching its topic count. A screenshot exposed white text on white hero buttons, including the existing Practice estimate; added an explicit dark-text rule and verified computed contrast after a second web deploy. TypeScript typecheck/build and Python compile passed. Bank sync remained unchanged at ba66d401a1314cc3d2115b28291969d81343062d84e154cc1d5f9a3bbb9141f0. The UI was checked at a desktop-size browser; small-screen viewport override was unavailable in the browser test surface. See docs/EXAM-SUBJECT-TOPIC-STUDY.md.

## 28 October 2026 — Question alignment and loading

The owner reported that LDC 2026 Mathematics Q53 compressed its four roman-numbered values into the question line and that exam questions loaded slowly. The shared source-text renderer now lays out stems with a full `(i), (ii), (iii)` sequence in aligned rows on desktop and a single column on narrow screens; applied to exam browsing, bank cards and question detail. Answer options and their order are unchanged. Q53's reviewed solution had an arithmetic typo: with denominator 48 the interval is `(32/48, 36/48)`, so 17/24, 33/48 and 35/48 are inside and 19/24 is outside. Corrected the local bank explanation while retaining answer C and its unofficial status; dry run and sync preserved 80,547 questions, 127 attempts and 32 users. Local and server bank checksums both b27272a43824… after sync.

The unfiltered LDC `/api/questions` request took 11.7–12.4 seconds before the change. `EXPLAIN ANALYZE` showed a correlated collection-membership probe against all 80,547 rows and costly PostgreSQL JIT compilation. The question endpoint now resolves a collection's canonical IDs once, and the API pool disables JIT for these view reads. Live LDC first-page requests take about 1.7 seconds after deploy, return 520 questions, and the searched Q53 returns one verified-solution item. Direct exam browse routes now prefetch their first question page concurrently with collection metadata; public catalog cache lasts 60 seconds and still invalidates on collection mutations. API and web deploy, TypeScript build, Python compile, bank sync check and live browser visual check passed. The live Q53 stem displayed its four values as a 2×2 list.

## 28 October 2026 — Group B English/GK/GS and separate technical papers

Implemented and deployed `/group-b` with shared source selection across both
Group B collections, common English/GK/GS topic cards, a combined GK/GS
learning subject and separate technical-paper browse/practice. Added entry
links from Exams and both Group B archives. The local bank and server were
in sync at b7399a0ad64a with 80,547 questions and all primary claims approved;
this release did not change bank data or apply a database migration.

Selection uses approved primary content plus 29 exact source-paper role
entries: two English, two GK/GS and 25 technical papers. Science needs GK/GS
source context for common practice; secondary links cannot pull a specialist
primary into common practice. This preserves original paper titles and lets a
technical recruitment's English/GS papers serve common preparation. The shared
view has 3,603 distinct questions (1,543 English and 2,060 GK/GS); technical practice
has 2,493 approved questions across 16 subjects. Gazetted coverage remains
historical departmental papers and is explicitly described as limited.

The main implementation trap was reusing the real-collection question filter
for the virtual combined route: paper filters and personal history needed real
source collection IDs, and shared topic filters needed the same primary-path
contract as displayed counts. Regression cases now cover those alongside
specialist science, pending claims, secondary-tag contamination and duplicate
appearances. 21 isolated PostgreSQL tests and 13 frontend checks pass; production
build succeeds. Compared targeted API files against deployed copies and shipped
only this feature's backend files, preserving the unrelated working changes.
The first live subset queries also repeated the existing collection union and
paid JIT compilation overhead; removed that redundant union for area queries
and disabled JIT locally on their reads.

Browser checks verified the common cards, Biology practice opening a 2026
General Studies source from a technical recruitment, separate technical paper
search for Electrical, and 390px mobile layout without horizontal overflow.
Proof and live count comparisons are in reports/group-b-common-20261028.
Study health remained 80,547 questions / 12,708 official-key scorable questions;
family.hawayu.in also returned 200 after redirects. Future coverage work is
source-role review and additional Gazetted direct-recruitment papers, not
inference from recruitment titles.

## 28 October 2026 — Group B historical common-science source review

Continued the common-subject launch by inspecting the 73 remaining unmapped
paper sources; all were available locally.23 had75 approved Science candidates.
Their headings and question stems supported74 additional common questions.
The important exception was SAD Paper II Q97: a speed calculation printed in
Simple Arithmetic, despite its primary Science tag. Mapping an entire mixed
paper to GK would have admitted it. Added optional printed-question bounds
and reused the exact predicate for both membership and source appearance;
unknown/compound or oversized numbers fail the bounded source match safely.

Manifest version2026-10-28.2 contains52 roles. Common coverage increased from
3,603 to3,677; English remains1,543 and GK/GS increased from2,060 to2,134,
including85 common Science questions. Technical questions remain2,493.
All12 area/source-group before/after comparisons matched topic totals, and
all74 newly included Science sources were checked against the reviewed roles.
22 isolated PostgreSQL tests pass, including section boundaries, malformed
numbers and alternative appearances. Deployed only the three affected API
files; no frontend rebuild, schema migration or bank sync. Browser screenshot
and detailed review evidence are in reports/group-b-source-coverage-20261028.
Health remains80,547 questions/12,708 strict-key scorable questions, and the
family site returned200 after redirects.

The local Gazetted sources are departmental Inspector papers; the bank has no
explicitly identified Group B Gazetted direct-recruitment paper. Preserved the
coverage note. Two existing classification concerns (banking current affairs
and the arithmetic speed calculation) are saved for independent review rather
than changing approved claims during source-role work.

### 28 October 2026 — UDC GK source label correction

The Group B browser used taxonomy_subject as its visible badge, causing UDC questions to look like General Studies paper questions. Added optional source-verified paper_label for nine inspected covers, exposed it in list/detail API appearances, and displayed it in question browser/cards/detail. Learning badges now prefer the approved topic with a shared GK/GS fallback. No database or bank mutation. The first live query required X-Device-Id; after supplying a UUID all four Shibu Soren records returned correct source headings but exposed a separate Indian History classification issue. Saved four pending Current Affairs review candidates, not published taxonomy changes. Regression suite:22 passed; updated Group B suite:4 passed; frontend:14 passed; production build passed. Targeted API/web deployment completed and live browser verified source wording. Shared family site responds307.

### 28 October 2026 — Admin paper identities and shared GK/GS retagging

Implemented migration0055 for operational source identities and idempotent retag batches. Identity editor in inventory exposes printed exam title/year, paper heading, evidence page and non-overlapping section ranges; uses version/source-context guards and existing audit export. Public source appearances receive matching reviewed metadata, while bank archive indexing, answers and memberships remain locally authored. Added Learning tags admin selection/previews, atomic batches up to20, immutable normal taxonomy proposals, independently checked review/publication actions, and current/proposed preview in individual contribution editor. Shared GK/GS picker resolves actual registry paths, including related paths.

Unified bank/library learner facets and collection topic trees via virtual subject/topic projection. Equivalent GK/GS topic labels share IDs and distinct canonical counts; old subject/topic links remain valid. Material discovery accepts shared GK/GS subject filtering. The first frontend build caught two unused old picker variables; removed them. Browser screenshot(fullPage) was unavailable earlier; getScreenshot succeeded and saved synthetic batch evidence. A disposable local fixture exercised owner sign-in, two checked previews, submitted proposals and verified identity revision1. Existing data includes obvious unrelated questions tagged Current Affairs; this feature preserves those claims rather than silently asserting them corrected. Shibu proposals remain a documented four-record review docket.

Validation:62 backend tests across identity/retagging, Group B, inventory, bank review, library, learning and content passed;15 node checks and production build passed. Migration rehearsed on a full production clone and applied by ledger-aware migrate.sh. Compared target API files with pre-edit deployed copies; no unrelated server drift found. Targeted API/web deployment completed, service active, unauthenticated new admin route401, shared family site307. All12 shared topic filter counts match live facets:12914 distinct GK/GS questions including2620 Current Affairs; Group B common remains3677. No bank edits, tag publications, invented approvals or test users were created in production.
# 28 October 2026 — Saved UDC naming and shared-bank rule

The user asked to save the one-bank/per-exam design and clarified that UDC has GK, not GS. Inspected the source-role manifest: the four 2025 Assistant/UDC booklet labels already use General Knowledge in their complete Paper I title. The learning taxonomy projection still labels combined subjects General Knowledge & Studies in collection topic trees. Saved the distinction in the classification runbook and decisions, with explicit pending tasks for exam-specific learning headings and verified practice schemes. This is a documentation update, not a claim that those remaining tasks shipped. Bank check: local/server checksum52bd5fbc1f8c,80,547 questions and80,547 approved taxonomy rows, IN SYNC. No bank data or deployed code changed; no runtime tests needed for this documentation-only change.

## 28 October 2026 — UDC/LDC context, question speed and owner access

The user asked to fix UDC/LDC around the saved shared-bank rule, reduce slow question loading, check access-extension support and make their expired account unlimited. Confirmed the account had an expired seven-day Pro trial and no provider subscription; changed it to active Pro with no plan expiry, recorded owner_requested_unlimited_pro_2026_10_28 in account_security_events and verified account_has_pro=true. Payment checkout is disabled and the only Pro-week reward is disabled; extension mechanisms exist but self-service extensions are not currently open. Added a clear unlimited billing label.

UDC/LDC/Assistant topic trees now present shared GK/GS IDs as General Knowledge. Broad question badges follow that context; actual source headings still come from verified metadata. Added clerical exam switching and own-exam English/GK shortcuts. Fixed shared-question source selection so newer sources in a different exam do not replace the selected exam's source. Existing content tags remain reviewable through the existing workflow.

Production EXPLAIN identified JSON paper-list expansion running once per80,547 questions plus global publication/status scans. Materialized section paper lists, bounded launch/origin and review probes, reused selected question IDs, and scoped collection readiness to its own canonical questions. Initial profiling scripts hit missing remote httpx and the default bench DSN; corrected them to direct read-only async calls against mpsc as postgres, without installing packages or exposing credentials. The candidate is loaded from /tmp separately from the running API. Full read-only parity checks matched all seven collection responses exactly and seven question responses except intentionally source-scoped appearances. UDC question reads measured2.9749→0.2285s and LDC1.3689→0.0404s inside the server; cold metadata UDC3.7808→1.0548s and LDC3.5370→0.2279s. These measurements exclude browser/network latency. Reports are in reports/udc-ldc-access-performance-20261028. Targeted backend/frontend checks and production build passed; deployment and browser evidence are recorded in the report.

## 28 October 2026 — Exam polish plan for Sol 6.1

The user requested an exam-section polish plan for Sol6.1. Saved docs/plans/EXAM-SECTION-POLISH-SOL-6.1.md with the existing implementation baseline, five priorities, concrete acceptance criteria, source/scoring boundaries, relevant files, release checks and a ready-to-use implementation prompt. The key remaining performance issue is that ExamPage waits for full collection metadata before displaying its prefetched questions; the plan explicitly protects mounted answer state during progressive rendering. It also addresses repeated landing-page panels, mobile filters, source-paper versus revision-topic identity and verified scheme presentation. Read the current source and latest performance report; did not implement or deploy the planned polish in this documentation-only turn. No runtime tests required.

## 29 October 2026 — Exam polish continued across midnight

Implemented the saved Sol6.1 plan in the existing workspace. A source-scoped lightweight public exam header now allows questions to mount before full metadata. Kept the browser component mounted across delayed metadata and retries, compacted focused-study headers, grouped secondary filters, added reset and request-key answer guards, canonicalized default prefetch queries, and reused verified paper headings on cards/viewer. Fixed the existing4px phone hero overflow and the18px/tablet shell mismatch. Hash focus now waits for lazy targets and clears the measured sticky header.

Synthetic rehearsal deliberately failed exam metadata and then delayed its retry six seconds. A submitted correct answer and its feedback survived both late arrival and retry. Failed question filters kept prior answer options disabled; reset and GK filtering recovered.35 backend and16 frontend tests passed, with a production build and seven production collection comparisons. The initial test used an unsupported private visibility value; corrected it to hidden. The fixture initially tried adding middleware after TestClient startup; wrapped only the disposable server app instead. Browser locator timing occasionally failed in the driver even when diagnostics reported a visible heading; native AX observations were used and raw measurements retained. One instrumented entry was7.865s; do not claim uniform sub-two-second loading. A stem-change pagination detector also proved unsuitable as a strict performance measure for this corpus; navigation was independently checked by URL/page and actual loaded questions. No synthetic answers/users were created on production.

Rendered and visually inspected five original first pages using the PDF skill. All sampled live scheme configurations remain platform-default, so retained the honest labels and wrote source observations plus a three-question clerical specialist-tag docket; no scheme or taxonomy proposals were published. Targeted API/schema and locally built frontend deployed with remote backups, matching hashes and study200/family307 checks. Bank remained IN SYNC at52bd5fbc1f8c with80,547 questions/approved taxonomy rows. Report and final screenshots: reports/exam-polish-20261028. This polish did not alter the owner's completed unlimited Pro grant.

Final phone verification kept the selected learning path visible and folded primary filters behind a44px toggle, bringing the first question into the study viewport. Corrected the exam-library coverage denominator to all available questions rather than comparing all practice attempts with only official-key questions. Rebuilt and redeployed the static frontend; existing backend checks remained applicable.

## 29 October 2026 — Clerical tags with requested Luna triage

Read-only operational scope contained5,049 canonical questions across UDC3,859/LDC520/Assistant1,568. All had approved subjects, but127 lacked topics, and approved tags included Miss Universe under Civil Engineering. OpenCode Go gpt-6-luna worked:9 saved calls/202 targeted candidates. Separate question-level adjudication explicitly selected120 corrections (102 missing topics,18 incorrect paths);82 candidate rows stayed unchanged, leaving25 topic gaps. All120 changed questions occur in UDC;87 overlap Assistant; LDC was verified without forced changes. Shibu Soren's four copies now belong to Current Affairs; original UDC GK mixed-paper identity is preserved. No answers changed.

The old classifier's unrestricted merge would discard newer restored records because historical batches cover77,751 rather than80,547 records. Added a bounded --ids merge, separate bounded conflict/report files, and refusal of unresolved selected ties;3 synthetic tests prove unselected-content preservation, preview behavior and tie refusal. Preview/validation had zero issues; exact before/after parsed-bank comparison proved only120 classifications changed. Normal sync applied120 updates; bank ebbaad123c70 is IN SYNC with80,547 approved tags;238 attempts/38 users preserved. Post-sync126 subject/topic links matched their exam counts; all120 deployed paths matched the reviewed batch. Saved workshop audit and reports/clerical-tags-20261029.

Fixed an unfiltered clerical drill recording the canonical primary source rather than the displayed exam appearance: client now sends displayed paper for UDC/LDC/Assistant.5 exam context tests and the local production build passed. Frontend deployment initially failed on root-owned assets; scoped sudo rsync succeeded, live index-CPRtpP2X.js. No API/schema/service/Caddy change. Public scripted reads failed without device identity, and remote TestClient lacked httpx; used deployed public read functions directly with a nonpersistent audit label instead, preserving users/attempts. Read the full service environment for its libpq password; DATABASE_URL alone lacked credentials. Study200/family307. Browser verified GK → Current Affairs and all4 Shibu source copies. Remaining broad writing/translation/browser/cloud/combinatorics and other legacy errors need evidence-backed follow-up; this is not corpus certification.

## 29 October 2026 — Paper readability and shared outer margins

The owner found the repeated eight-booklet paper cards unreadable, then requested less congested page margins across the site. Replaced the shared ExamPage paper grid with one readable row per paper: source filename/booklet as the short heading, total/written counts and nonzero linked answer statuses, Browse/Practise/Source PDF actions. Full printed headings, missing-explanation details and eligible timed-test actions/rules stay under a native collapsed Paper details & tests disclosure. Unofficial solution wording remains explicit, source/key problems remain visible, original test eligibility and URLs are preserved, and paper-label search now includes verified headings. No backend/count/scoring/bank changes.

Expanded the shared shell1240→1440px; exam-specific1100px wrappers and Combined1160px now use the shared width. Shared outer gutters are16px desktop/12px phone, with existing18px exam tablet padding retained. Updated the hero offsets to match actual shell padding and widened Study Desk's outer workspace; deliberately narrow reading/form columns retain their own limits. At1280 the actual exam container increased1100→1265px, body/client both1265px; collapsed first-row height207px. Phone390px LDC checked375px body/client,351px paper cards,6 visible source rows. Combined desktop9 paginated rows/body1265px no overflow. Disclosure opens the original title, singular explanation text, practice-rule caveat and reviewed estimate link. Reused prototype Newsreader, cream/card/hairline,12px radius and44px targets as an explicit owner-requested layout extension.

Vite hot update kept stale max-width until restart; production build CSS correctly emits1440px. The viewport capability initially applied to a different existing tab, so its supposed mobile screenshot was desktop; recreated the phone preview in a fresh tab, confirmed390px innerWidth and overwrote it.16 existing frontend checks and TypeScript/Vite production build passed. Local build deployed with scoped sudo rsync (root-owned public assets); rollback /tmp/paper-list-web-before-20261029.tgz. No service/schema/Caddy changes. Evidence and final screenshots: reports/paper-list-readability-20261029.

## 29 October 2026 — Restore box cards; remove the remaining width cap

The owner clarified that they prefer the previous box cards and that reducing only gutters still left large page margins. Restored the shared exam paper grid (responsive300px minimum boxes), with vertically arranged card actions and retained cleaner disclosure content. Removed the1440px cap from the shared shell, Combined wrapper and Study Desk: they now use the available viewport width with the16px desktop/12px phone gutters. Narrow article/form limits remain intentional. The prior row-layout decision is superseded by this explicit preference. TypeScript/Vite build and16 frontend checks passed; static frontend deployed, index-DSIozDK2.js. Rollback /tmp/box-cards-web-before-20261029.tgz. No backend/data/scoring changes.

### 29 October 2026 — Optimize fluid browsing and reading widths

Preserved the owner’s full-width shell, 16px desktop/12px phone gutters and box cards. Increased paper grid minimum from300px to340px with16px desktop/12px phone gaps; long titles wrap. Exam question results now have a left-aligned960px reading limit, while filters and browsing remain fluid. Shared bank question headings use75ch maximum. Browser measurements:1920px viewport yields five361.8px cards,1280px yields three400.3px cards,390px phone yields one351px card; no horizontal overflow. Exam reading area measured960px desktop and351px phone. Viewport override initially applied to another browser target; verified actual innerWidth instead of trusting requested dimensions. Production build and16 frontend tests passed. Static frontend deployed with backup /tmp/layout-optimization-before-20261029.tgz; live1920px grid verified, screenshot reports/layout-optimization-20261029/live-desktop.png. Bank IN SYNC; no backend or data changes.

### 29 October 2026 — Shared paper-card visual polish

Polished the existing boxed cards across shared exam modules: year badge and source PDF at the top, separate official/unofficial status lines with redundant symbols, compact review/unanswered row, equal-height cards per grid row with bottom-aligned Browse/Practise actions, clearer details control, subtle hover shadow and visible keyboard focus. Retained fluid shell/gutters, existing routes, counts and eligibility. Initially reserving two title lines added unnecessary space; removed that reservation after screenshot inspection. Local390px phone card351px wide with no horizontal overflow; live1440px desktop first-row action positions all661.875px and no overflow. Expanded details preserves source heading, explanation-gap notice, platform timing caveat and unofficial estimate warning. Production build and16 frontend checks passed. Static frontend deployed; backup /tmp/card-polish-before-20261029.tgz. Screenshots and logs: reports/card-polish-20261029/. No bank/API changes.

### 29 October 2026 — Assistant science-filter inspection

Read-only inspection of live Assistant study-topics and learning-taxonomy/question filters: Science32 (Biology14,Physics10,Chemistry8) is a separate canonical subject; GK505 includes Science in the news12 as its own topic. Ordinary clerical GK filtering currently matches only general-knowledge/general-studies, so Science is not included within that GK discovery branch. Subject/topic/subtopic filters exist, but a combined exam-specific GK→Science grouping requires a discovery overlay and matching question-filter/count changes. Counts alone do not establish missing science classifications; review question content before retagging. No production change in this inspection.

### 29 October 2026 — Science within clerical General Knowledge

Implemented a discovery-only GK → Science grouping for Assistant, UDC and LDC. Original Science subject/topic/subtopic routes remain available; GK Science branches reuse canonical Science topic IDs as virtual branch IDs. Existing GK/GS Science in the news also joins the Science group while retaining its old topic link. The shared path projection supplies both study-map counts and same-path question filtering, preventing cross-path intersections and counting distinct IDs. Scope is only ordinary clerical exam routes; Group B source rules and global taxonomy unchanged. Added brief topic-card help and visible Science branch buttons including All Science; controls wrap on phones. No bank edits, migrations, scoring or source-identity changes.

Synthetic PostgreSQL tests exercise all three exams, overlapping approved secondary tags, pending exclusion, exact branch count parity, original Science links, canonical tags, exam source context and global GK isolation. First fixture attempt tried a second primary classification and hit its real unique constraint; switched to the established question_topic_links secondary table.29 backend tests and16 frontend tests pass; production build passed. Live counts: Assistant GK537/Science44 (Biology14,news12,Physics10,Chemistry8); UDC GK1433/Science103 (news43,Physics28,Biology22,Chemistry10); LDC GK150/Science23 (Biology10,Physics7,Chemistry6).17 new group/branch count-result checks passed, HTTP median0.463s/max1.129s in this small run. Existing topic data, other subject maps, exam totals, Group B map and global taxonomy equal before-release snapshots. Initial external question probe omitted required X-Device-Id and received400; reran with one fixed synthetic read-only device header, no auth/accounts/answer submissions.

Targeted three-file API and local-built frontend deployed with backups /tmp/clerical-science-api-before-20261029.tgz and /tmp/clerical-science-web-before-20261029.tgz. API healthy80547questions/12708scorable; shared family site307 after service restart. Live desktop1280px All Science44 and390px phone Biology14 verified with no overflow; screenshots in reports/clerical-science-20261029. Existing science misclassifications still require question-level review; grouping is not a content audit.

### 29 October 2026 — LDC Science content spot audit after owner question

Read all23 live Science questions:10Biology/7Physics/6Chemistry are science content and their displayed sources are LDC papers (Law/Judicial PaperI7/PaperII1, SW-WCD PaperI9, MPSC2025PaperI6). Reviewed remaining127 GK question texts: Chandrayaan-5 collaboration cq_8a99da23983729ec remains Current Affairs and is absent from Science; Global TB Report publisher cq_e356c80b4c702c52 is another candidate for science/health-news discovery review. Thus23 is correct for current approved filters, not a certified complete science inventory. Saved read-only inspection and candidate docket; no taxonomy changes or answer verification.

Correction to the immediately preceding LDC source breakdown: actual counts are Law/Judicial Paper I8, Paper II1, SW-WCD Paper I9, MPSC2025 Paper I5 (23 total). The JSON inspection is authoritative; the preceding prose transposed one question between Law/Judicial and MPSC.

### 29 October 2026 — Website upgrade assessment

Read-only product review: live homepage chooses ITI Instructor2026 as default CTA, claims every MPSC paper, shows1sections on clerical cards and retains community/tools planned copy despite existing application routes. Routes alone do not certify feature launch. Combined findings with recent mobile header screenshots, LDC science-tag gap and outstanding source schemes. Saved prioritized assessment in docs/plans/WEBSITE-UPGRADE-ASSESSMENT-20261029.md; recommend exam-first entry/mobile navigation, truthful coverage and source schemes, then integration of existing revision plus measured loading/learning funnel. No site changes, fabricated usage metrics or full security/SEO audit claims.

### 29 October 2026 — Save MPSC-first scope

Owner clarified that the site is MPSC-only for now and will expand later. Recorded this in DECISIONS and the upgrade assessment: current exam selection is within MPSC; prioritize its learner journey and defer broader-system UI while keeping reusable architecture. Documentation only; no deployed UI or data changes.

### 29 October 2026 — Restore Interactive Atlas from the old website

Owner clarified that “study map” meant the old Leaflet atlas and authorized restoration with a clean place in the new MPSC site. Inspected sibling india-study-map:26 chapters with inline vector layers across geography/history/polity. Restored those chapter data files/types with adjusted imports, leaving the old repository untouched. New lazy /atlas page defaults to Mizoram and provides subject/chapter selection, layer toggles with colour legend, named-feature search/list and focus, optional timelines, reset, notes, and subject practice links (Mizoram chapter opens Mizoram GK). Imported original quiz arrays remain source data only; no legacy quiz scoring or claims of official answers were introduced.

Placement: Library → Modules & tools → Interactive Atlas; Library and Sections menus, homepage Study library card/menu, Geography/History/Polity/Mizoram subject shelves supply contextual links. Study Desk retains its existing meaning. Lazy atlas bundle459.11kB/138.64kB gzip includes Leaflet and26 chapters; normal question routes do not import atlas code. Base map uses OSM HTTPS tiles, visible attribution and ordinary browser caching; no tile bulk download/prefetch. Retry and vector-only mode handle tile loading failure. Deliberately excluded legacy base-states GeoJSON because its own comments say it predates Telangana and Ladakh. Restored educational/historical overlays remain explicitly illustrative; this restoration is not a fresh fact audit of all old notes.

Production build and17 frontend tests pass. Data test validates26 unique chapters, finite coordinates, inline supported layers and timeline layer references. Browser flow verified Mizoram defaults, Lakes toggle, Palak feature search/focus, History/IVC timeline1924 and reset, subject changes, desktop tiles8/paths11 and phone390px map351px wide with no overflow. One getByLabel selector timed out despite a visible control; fresh DOM and semantic combobox locator succeeded. Console inspection returned no errors. Static frontend deployed with backup /tmp/atlas-web-before-20261029.tgz; live Library tools→Atlas navigation and390px phone verified. Evidence: reports/atlas-restoration-20261029/live-desktop.png and live-mobile.png. No API, bank, schema or user-data change. Original source/provenance and provider policy links in web/src/atlas/README.md.

### 29 October 2026 — Sol handoff for XP, leaderboard and authentication

Owner asked for a solid system design/workflow for Sol. Inspected current auth, MFA identity, guest adoption, immutable reward migrations/functions, games award hook, leaderboard SQL, account/reward UI and existing test definitions. Saved docs/plans/XP-LEADERBOARD-AUTH-SOL-6.1.md with implementation packets, contracts, concurrency/security/privacy acceptance and rollout. This is planning only; no application edits, migrations, deployment, user mutations or email sends. Existing tests were read, not executed. Bank check returned IN SYNC with 80,547 questions and approved tags, hash ebbaad123c70….

Concrete findings: auth accepts supplied device UUID for selected history adoption although deps explicitly treats UUID as non-authentication; recovery UI says email delivery is still being configured; AccountForm ignores intended next route and always goes to profile; leaderboard total comes from paginated rows and becomes zero past the last page. Existing reward uniqueness, cap, privacy default, MFA and immutable ledgers should be retained. A subtle migration trap: issuing new guest proof against an arbitrary old UUID would not fix ownership; the plan requires new protected principals and no automatic claim of unproven history. Another trap is stale documentation: games already call the shared award function, while older rewards prose says future games. Historical reward behavior is preserved rather than silently relabelled practice-only or recalculated from corrected answers.

### 29 October 2026 — Implemented and released account, XP and leaderboard hardening

Followed the saved Sol handoff in this chat. Added migrations0056–0059, protected random HttpOnly guest proof instead of UUID ownership, explicit locked/receipted guest learning transfer, shared account resolution, consistent cookie mutation Origin/CSRF and explicit expired-session handling. Added safe login return, request generation guards and cross-tab refresh; session list/revocation and password session rotation. Recovery/verification tokens and encrypted SMTP outbox are implemented but production mail remains disabled because no SMTP configuration exists. No email sends, artificial production learners/XP or catalog enablement.

Extended existing immutable reward machinery rather than adding an award endpoint. Practice idempotency returns original receipts across key changes; XP outcomes explain cap/repeats/guest/unofficial cases. New ledger metadata links mechanically provable attempt/material reversal sources while old entries retain legacy-v1. Board now supplies own public placement/India bounds, stable ties and independent pagination totals; owner diagnostics reconcile receipts/claims/debt/caps and inspect bounded security/reward history.

Full backend suite290passed; final auth/reward/MFA/board/password additions32passed (overlapping runs), frontend20passed and build passed. Old tests omitted newly required cookie CSRF; updated their calls. Existing game helpers were already stale against preview/ready guards; exercised the current contract rather than weakening guards. Shared synthetic-paper growth also exposed a hardcoded cq_test answer in a mock snapshot test; use the actual drawn ID. Browser caught two concrete bugs: a normal guest401 must not show session expiry, and expired cookies still need a CSRF value to perform explicit logout. Another final integration fix invalidates cached CSRF/workspaces after password cookie rotation. Browser tested guest→consented account transfer→returned exam→one XP award→repeat suppression→board placement→cross-tab logout, all on a disposable local DB.390px mobile body375px, no overflow; initial viewport override was ineffective until applied after tab creation, so replaced the inaccurate mobile capture.

Clone rehearsal passed all four migrations, then applied and uploaded13selected API files/static build. Current live bundle index-CsXsy59b.js; all API SHA256s match. The original34ledger rows retain exact fingerprint,340XP/34points; named owner unlimited Pro remains true.80,547question/approved-tag bank IN SYNC, strict pool12,708; family307 and study healthy after restart. Six anonymous board reads209–380ms/median224ms are smoke evidence only. Production board empty because no opt-ins; did not fabricate users/scores. Server backups /tmp/account-xp-api-before-20261029.tgz and /tmp/account-xp-web-before-20261029.tgz. Evidence reports/account-xp-hardening-20261029/STATUS.md; operations docs/ACCOUNT-XP-AUTH.md. Remaining: configure/authorize controlled mail delivery and measure representative load/monitoring; recovery delivery must not be claimed live meanwhile.

Cleanup follow-up: closed all three temporary acceptance/live browser tabs, reset viewport, stopped local Vite/fixture API and confirmed the disposable PostgreSQL database was dropped. System python lacked psycopg during the first cleanup verification; reran verification with api/.venv/bin/python. No local acceptance services remain running.

### 30 October 2026 — Simplified admin work and navigation

Owner asked to simplify the admin workflow. Found21flat sidebar entries, duplicated overview/publishing dashboards, paper filters whose data component already owned loading, and two consecutive browser prompts for report resolution. Added role-aware stable-ID navigation: five owner daily tasks, grouped More tools, phone section picker, task-card Home and collapsed system details. Combined queue now mounts only on workflow, keeps search/type/stage visible, discloses priority/order and resets filter URLs. Root reviewer subject/state filters persist through refresh. Reports link straight to the canonical question inspector; inline reason/publication form preserves input/errors and existing API validation rather than using prompt chains. Unknown tabs fall back to Home; known inaccessible sections get a permission message without firing their data request.

Verified23frontend checks,18existing backend review/publication/tag regressions and TypeScript/Vite build. Disposable local browser acceptance used synthetic owner/scoped-English reviewer only: checked five versus three primary destinations, grouped specialist tool access, forbidden Rewards handling, bookmarked submitted-state retention, combined queue filter/reset, direct inspector opening and actual report dismissal. A missing-publication submission still received the expected422and stayed unresolved; no safety shortcut was added. No production reports, grants or bank content mutated.

Visual QA at390px showed the first queue design still stacked three summary cards above all filters; changed to a compact three-column row and removed duplicate heading/copy. Home task cards use two columns on phones. Measured innerWidth390/body375with scrollbar and no horizontal overflow; saved loaded desktop/mobile owner/reviewer/form previews. Backend unchanged; static-only release, no migration or API restart. Backup /tmp/admin-workflow-web-before-20261030.tgz. Release bundle/evidence in reports/admin-workflow-20261030/STATUS.md. Bank initially IN SYNC at80,547questions and approved classifications; all21tab IDs remain supported. Deployment/live verification and fixture cleanup recorded in the release status.

Release follow-up: final static index-CXed5_X2.js and BankAdmin asset match live SHA256s; live protected admin entry loads the new UI and retains the clean `/admin/bank` login return. Adjusted the inherited “Sign in to contribute” error to admin/reviewer wording. Health80,547/12,708, bank IN SYNC and family307. Permissioned production behavior was tested locally without impersonating a live owner. Closed two temporary tabs, reset viewport, stopped fixture/Vite and confirmed disposable DB dropped. Final report reports/admin-workflow-20261030/STATUS.md; screenshots explicitly use test data.

### 30 October 2026 — Requested fresh admin production build

Owner followed up with “Build it” after the simplified admin release. Ran a fresh TypeScript/Vite production build successfully and compared its entry asset name and SHA256 with the live site: exact match. The simplified admin console was already deployed; no redundant upload, source edits, schema change or server restart was needed. Build output: reports/admin-workflow-20261030/rebuild.log.

### 30 October 2026 — Admin ease of use and optimization without feature cuts

Owner clarified that simplification means easier use and optimization, with no regression. Consolidated duplicate review status and exam controls while retaining all six answer lists, every issue type, year/topic/exact-paper filters and common exam fallbacks. Clear filters remains visible. Question and Save & next navigation now crosses20item page boundaries, keeping local decision receipts; old filtered rows/pages cannot be selected during pending changes. Report inspection has an exact-report return. Taxonomy loads independently only for tasks needing it, with separate retry and gated permission forms. Identical pending admin GETs coalesce in memory, completed reads never persist, writes/content/account changes clear reuse, and account generation guards stay enforced. Removed the combined queue’s artificial200msdelay; text/year drafts debounce instead.

Measured27frontend tests passing, including actual reviewRequest concurrency, freshness after writes/content changes and account-boundary rejection. All292APItests pass. Initial broad pytest accidentally discovered archived implementation copies under reports; reran with explicit api/tests. Its session-shared fixtures then revealed a genuine test conflict: the snapshot test drew a two-option question from another module but tried changing its key to D. Pinned its intended four-option fixture with an empty query (pins are additive to paper queries); no production code or schema changed for that fix. Local browser used25synthetic questions: initial save rejected absent sync prerequisite correctly, then seeded a local synthetic sync and verified Save & next from page1lastrow browser_q4 to page2firstrow browser_q5. Receipt stayed queued, official key unchanged. Checked exact-report return, all specialist links, stale search/year disablement and390pxphone layout without horizontal overflow. Browser viewport override applies to the most recently created tab, which required a separate narrow-screen tab. No synthetic production edits.

Production build passed. Static deployment, live hashes, bank status and cleanup are recorded in reports/admin-usability-20261030/STATUS.md. No API deployment, migration, permission relaxation or bank-content edit.

### 31 October 2026 — Released source-linked paper workspace

Implemented the requested comprehensive paper explorer across exam modules: Paper / Focus / Question + PDF, full-paper text and printed-number search, question map, type/status/subject filters, visit-only flags/scratchpads and next-unchecked navigation. Retained printed options/source appearance identity, provenance, source formatting, written questions, corrections/discussion and official/reviewed scoring eligibility. Clerical GK/GS displays General Knowledge; Science is independently filterable within GK. Compact booklet heading, disclosed full instructions/coverage and two-column mobile filter row preserve boxed cards and narrow outer gutters.

Progressive 100-appearance reads cancel on exit; 30 cards render per Paper page. Canonical totals can undercount repeated appearances, so stop at short appearance batches rather than total. Answers disable duplicate submits and preserve printed-to-canonical mapping. Local synthetic printed A/Jharkhand mapped to canonical B and produced exactly one correct receipt, verified directly in disposable DB. Q104 beyond initial batch, flags/notes through filtering and unscored written questions passed browser acceptance. No production attempts created.

Native iframe rendered blank in browser testing; replaced with lazy PDF.js canvas, cancellable render tasks, page/zoom/return controls, local worker/fonts/WASM, bounded canvas pixels and accessible adjacent transcription. Real UDC page8 rendered, page9 navigation and150%zoom worked; changing to another question on page8 correctly reset manual page navigation. Mobile390px/body375px had no overflow. A final compact-heading refinement was built but could not be visually rechecked after browser-session restoration: tool URL policy rejected saved-tab binding, and no workaround was attempted. Two simultaneous Vite dev caches caused a React hook mismatch during dependency changes; production previews avoided that development-only cache conflict. PDF.js5.6.205 audit advisory prompted pinning5.5.207 compatible with Node20; unrelated existing audit findings remain.

33frontend tests,13focused API regressions and production build passed. Static-only deployment with backup /tmp/paper-workspace-web-before-20261031.tgz. Live entry index-Cjw3vXhO.js, PaperViewer, PaperPdf, worker, font and WASM exact SHA matches; API healthy80,547/12,708; bank/taxonomy IN SYNC. No API restart, migration or bank mutation. Guide docs/PAPER-WORKSPACE.md; full evidence reports/paper-workspace-20261030/STATUS.md. Preview stopped and disposable DB dropped/absence verified. Saved localhost browser tabs may remain because binding was blocked. Earlier proof script assumed chosen_index, which does not exist; verified chosen_text and immutable scoring_snapshot instead.

### 31 October 2026 — GitHub source checkpoint

Owner requested pushing the completed website work to GitHub. Included current application code, migrations, tests, operational scripts and documentation accumulated since the last source checkpoint. Excluded generated reports, database snapshots, temporary fixtures, dependencies/build output and local credentials. Existing release validations are recorded above; this checkpoint introduces no production behavior changes. Remote main was fetched before committing; push verification compares the remote branch SHA with the local commit.

### 31 October 2026 — Reviewed MCS Combined before implementation

User selected MCS Combined as the next priority and explicitly requested review first. Read live collection/paper/topic endpoints, relevant UI/mock/taxonomy code and local bank, plus official2025Gazette. Found24listed/23nonemptybooklets,1,921questions,1,098official-eligible,814needreview,9unanswered;1,749missingexplanations. Confirmed sparse2025/2023booklets in both raw bank and appearance API, so these are content gaps. All paper rules are platform-default; paper mock inherits20minuteclientdefault while loading the full eligible paper. One pooled section and23bankcategories do not express GS versus Aptitude. Saved findings, source citations, stage/paper identity design, ordered implementation and acceptance gates in docs/plans/MCS-COMBINED-REVIEW-20261031.md. No application/bank/deployment change. Read-only source review, not a fresh visual audit or exhaustive historical-rule adjudication.

### 31 October 2026 — Located missing historical MCS papers online

User requested2012/2013/2015/2017/2018MCSPrelimspapers and asked whether to open a browser. Searched directly; recovered/downloaded six ChaseAcademy-hosted Paper I/IIPDFs for2015/2017/2018, recorded hashes/pages, extracted text and visually inspected2015/2017firstpages using PDFskill. These are branded reproductions, so series/order/authenticity still require source/key cross-check. Found working official2015Paper II original and additional2017original-source leads.2013only genuine key leads found; one2013-labelledmirroractuallysaysJune2015.2012oldkeylinknowgenericMPSChomepage; noquestionpaperverified. Saved durable source list/status in docs/plans/MCS-HISTORICAL-PAPER-SOURCES-20261031.md and six local PDFs/manifest in ignoredreports/mcs-paper-search-20261031. No bankimport/deployment/contactingothers.

### 31 October 2026 — Implemented recovered MCS papers and GS/Aptitude paths

Owner requested implementation after historical source search. Added six recovered ChaseAcademyreproductions (2015/2017/2018Papers I/II),600newsource-onlyrecords,143sharedsourceimages and six PDFs. Preserved all80,547oldquestionobjects and1,964oldpaperobjects exactly. No answers/classifications inferred; new600remainunclassified,36pictorial/ambiguousoption extractions are source-review items. Registered six paper documents for admin correction. Versioned MCS collection from1to2with separate source-backed GS/Aptitude manifests, legacyall-paperbookmarkcompatibility, role-retaining study/paper/practice/mock links, MCSGeneralStudies+Sciencefiltering and unchangedclericalGKlabels. Added recovered/coverage notices and changed generic Combined action to Quickpractice.

293backend/34frontendtests andbuildpassed; focusedMCSmigrationtestrepeatedafterdocumentregistration. Bank dryrun rolledback, migration0060appliedcleanlyonproductiondumpclone, thennormalbankpublication/API/staticdeploymentcompleted. Two extraction defects caught before/afterpublication:2018coverinstruction1was mistakenforQ1; removedcoverswithoutlosingpageboundariesandverifiedgenuineQ1source. Regexalsohadtoallowfigure-onlyquestionnumberlines.36source-reviewoptionswereblankintext,soaddedexplicitprinted-letterimage references and republishedonlythosenewunscoredrecords. No sourcecontent/keyguessesmade. Fetchingoriginal-linkindexviaurllibreturned403; retainedclearlylabelledreproductionsratherthanclaimingoriginalauthorityverification.

Livecollection30papers/2,521questions/1,098official-eligible; GS1,507/Aptitude1,014,each300unclassifiednewrecords. All600livequestionstems/options/pagesmatchfinalartifact;149remotePDF/imagechecksums match. API/migrationhashesandfrontendentrymatchlocal. Bank81,147/globalofficialpool12,708,bank/taxonomyINSYNC;243attemptspreservedacrosssyncs;family307afterrestart. Backups/tmp/mcs-api-before-20261031.tgz and/tmp/mcs-web-before-20261031.tgz. No newbrowservisualacceptanceclaimed(saved-tabtoolbindingwaspreviouslyblocked). Noauth/learnerwrites. Guide docs/MCS-COMBINED.md, evidence reports/mcs-implementation-20261031/STATUS.md. Remaining source/key/explanation/tagreview is explicit;2012/2013unresolved,2023/2025partialpapersandoriginalsimulationnotcertified. Source scripts/checkedmanifestandimplementation are being checkpointed to GitHub; generatedassets/backupsstayinthebank/evidencearchive.

### 31 October 2026 — Followed up2012/2013MCSsource recovery

Owner asked to do2012/2013after the six-paper release. Expanded search beyond repeated indexes to NDLIpubliccatalogue and Waybackavailability/CDX. Found2012exam evidence in official Assembly proceedings, but no question booklet for either year. The2012oldqueryURLhas a2022Waybacksnapshot; retrieved1.39MBHTMLparsed as genericMPSChomepagewith no2012/2013text orPDFlinks, so rejected as source recovery. PublicNDLIcatalogue listsCombinedPrelims2014onward; its2012/2013itemsareunrelatedexams. DirectNDLI401, broadarchivequerytimeouts and eight2013keyPDFdownload403sare recorded; cachedwebkeycontentsare leads only. Saved durable URL/accessmanifest and expanded historicalsource note. No bank records, papers, answer mappings or production deployment created. Needactualbookletscan/workinglinktofinish; absencefromsearchisnotproofexamswerenotheld. No external messages sent. Evidence reports/mcs-2012-2013-search-20261031/.

### 31 October 2026 — Restored recent MCS booklets and preserved held source items

Owner deferred2012/2013booklet search and asked to finish available MCS work. Recorded explicit deferral and prepared480missing source appearances from eight existing original2023/2025PDFs. All16recentbooklets now contain printed1–100. New records have no answers/classifications;124content-addressed page-span images total29,136,385bytes retain source diagrams/passages/options. Three option extractions remain unresolved (2023II C70/96,2025II C25). Preserved every prior81,147questionobject and every paper object exactly. Source hashes and exact missing-number manifest are committed; authoritative bank append uses lock, checksum, collision guard, immutable-byte backup and receipt, followed by ordinary sync.

Two extraction traps caught before publication: stripping page headers also stripped formfeed-adjacent question starts, fixed with explicit newline after each preserved formfeed; the cleanup regex removed standalone numeric option text, creating31falseoptionissues, fixed to retain numeric lines and reduced to the actual three. Added regression fixtures for numeric answers, cover exclusion, page boundaries, numbered statements, diagram-only options and incomplete-source refusal. Source images visually sampled, including the diagram-only2025II C25; page composites preserve source context rather than invented bounding boxes.

Final-key audit identified24compensated source cells:16in2023and8in2025. Eighteen pre-existing appearances had ordinary stored answers and were held through existing owner-delegated admin answer decisions, retaining source/key hashes in immutable audit reasons. Six newly restored compensated appearances have no answer. Global eligible official pool fell12,708→12,690, MCS1,098→1,080. No new official/verified answers or explanations manufactured. Discovery active count2,983excludes18holds; printed source total3,001includes them. This is not compensation-award simulation.

Live verification caught v_all_questions excluding held items from printed-paper browsing. Changed only paper-source reads/readiness to include live/held canonical records after existing collection/paper scope checks; scoring remains on existing eligibility views, withdrawn/merged records stay excluded, no answer index/text is returned. Added held/withdrawn endpoint and card-readiness assertions. A first test cleanup tried deleting a question after status UPDATE had correctly created score-version history; changed the synthetic fixture to insert its intended held status directly, rather than deleting immutable history. Full297backendtests passed; final focused3checks cover latest held/withdrawn/count changes. Frontend36tests and TypeScript/Vite build pass. MCS catalogue groups year→sourcepaperrole→bookletselector, preserving each separate paper card/count/PDF/options and all non-MCS card layouts.

Published bank checksum ccfcafb2d08055055046b3d6618b1008b7c3686cb26631952aa0cb959804c49a,81,627records. All480live restored stems/options/pages and all124remoteimagehashes match; sampled public image bytes also match. Every recent booklet endpoint returns100printedpositions including held items. All18helddetailreads confirmed non-grading state; legacy section=papers still resolves active2,983. Static index-t_jTipON.js and ExamPage/API source hashes match local. Only collections.py deployed/restarted; frontend shipped from local build, no schema/Caddy edits. Study healthy/family307. User count70and243attempts preserved; owner unlimited entitlement remains true. Bank/taxonomyIN SYNC. Rollbacks /tmp/mcs-recent-web-before-20261031.tgz and/tmp/mcs-recent-collections-before-20261031.py. No new browser visual acceptance claimed; saved-tab control was previously policy-blocked. Evidence reports/mcs-completion-20261031/.

Remaining work is explicit in PLAN/MCS guide: reviewed transcription/option repairs, learning tags, final-key mapping and worked explanations for restored/recovered papers, then source-confirmed simulation;2012/2013search stays deferred and Mains is separately inventoried future scope. This release completes recent source coverage and catalogue grouping, not full paper-content certification.

### 31 October 2026 — MCS restored tags, exact final keys and older answer repairs

Owner said Go next after recent source restoration. Reused332existingapprovedclassificationpaths through exact normalized stems and full ordered choices, bounded to the480restoredrecords.145had no exact match and three had source defects; no conflicts were force-resolved. Saved the332claims in the bank workshop as well as local receipts, without running a broad historical merge. Tag publication changed only classifications; no answers were transferred between duplicate/series copies. Approved taxonomy rows80,547→80,879. Raw unclassified MCS remains748(600recovered/148recent); active discovery excludes three compensated unclassified records, so maps show745(GS362/Aptitude383).

Prepared329eligibleunansweredrecords against their own original PDF question numbers, ordered choices and physical pages, and their own final-key cells. Parsed2023cleantexttables with exact100-cell partition including compensation. Preserved the previously inspected800-cell2025image-keytranscription as a committed source manifest; explicit X cells never become answer letters. Registered five initial booklet/key mappings plus2025I B for the older fixes, backed by three unique protected key PDFs. A first protected-file install attempted wildcard expansion as an unprivileged SSH user and failed at chown; replaced it with exact SHA-named sudo install commands. All three files are readable as the API's www-data group and hash-verified. No public key-file access policy was changed.

Fixed an admin workflow bug before key publication: empty optional official explanations were replaced by audit reasons, falsely filling explanation coverage. Exactly mapped official key-only answers now store null explanations, while rationale/evidence retain the decision reason. Derived solutions and community MCQs still require useful explanations; the batch publisher enforces the same distinction. All329newkeysretainmissingexplanations. No official label was written directly into the bank by a classifier; existing owner-delegated decisions, final-key registry guards, immutable manifests, local publication receipts, normal sync and live answer comparisons performed the publication.

The local single-item timer raced the first100-itemqueue and correctly published one member before the batch acquired its lock. Its bank checksum advance made the other99exportsstale; the batch dry run refused them, as intended. Stopped only the timer, waited for the running publication to finish, and retained its successful publication. Added a guarded operator recovery tool: exact explicit stale owner exports, unchanged live source baselines, current checksum, existing delegation and all outstanding IDs must match before withdrawal. It recorded the99unappliedexportsasfailed/withdrawn, preserving every original manifest and event; fresh owner decisions then rechecked sources and exported against the current bank. No manifest checksum guard was weakened, no peer vote/credit invented, no canonical SQL edit performed. Added owner CLI preflight refusing multi-item export batches while the timer/service is active, plus isolated recovery/coordination regression checks. Reconciled99andthen100/100/29published in normal bounded batches.434staffcontributionswerecreatedincludingretiredworkandthesubsequentrepairs,underthenormal500/daycap; no quota exemption used. Timer restored active/enabled after every export was applied and checked.

Checked the three older2025differences against fresh source-page renders. I B Q15 final A replaces provisional B. I B Q30 has genuine date-range dashes instead of literal Unicode escape text and final C replaces inferred B. II C Q41 had lost exponent/division operators and pointed to physical PDF page6instead of7; restored the expression, original page image, correct locator and final B(2), with checked algebraic working. The first source batch tried to include page in a transcription and was rejected atomically; respected field ownership by publishing transcription and source_reference separately. Three source publications and three answer decisions complete these repairs; all other81,144olderquestionobjects remain unchanged. New content-addressed source image is public and hash-verified. The source option-review backlog remains36recoveredplus3recentdefects.

All24compensatedrecentappearancesnowhavepersistentreviewholds,includingthesixnewlyrestoredunansweredones. Paper-source browsing retains them; no option can be graded while held. Published329newkeysandcorrected/refreshedthreeexistingkeys; official eligibility MCS1,080→1,411andglobal12,690→13,021. Active MCS discovery2,977versus3,001printedsourceappearances. Bank81,627, final SHA92d7728ded4f2960daf87853f2a412f5b9fb370b711d61659b8203f3b4e1119f. Every332liveclassification,329newcanonical/appearanceanswers,threeolderrepairs,24holdsand335appliedpublicationstatesverified;335publicationshavezerofabricatedpeerdecisions/creditrows.99retiredexportsremainexplicitfailed/withdrawnhistory. Full-bankdiffallows only the exact332classificationchanges,329newanswerpatchesandthreeauditedolderrepairs; all other question fields/papers preserved.329newexplanationsremainmissing; one older equation now has actual working.

314backendtestspass(includingofficial-key-onlyexplanation,final-cellparsing,source-claimreuse,stale-recoveryandbatchcoordination). Deployed only admin_answers.py/review_policy.py; both server hashes match local. No frontend/schema/Caddy changes. API healthy/family307afterrestart.243attemptspreserved,71users(newsign-upduringwork),ownerunlimitedstilltrue. Bank/taxonomy IN SYNC; no production learner submissions. No fresh browser visual acceptance claimed. Rollback /tmp/mcs-key-policy-api-before-20261031.tgz; evidence reports/mcs-readiness-20261031/. Remaining unmatched classifications, source faults, checked explanations and historical numbering need further content work before authentic simulation.2012/2013searchremainsdeferred.

## 31 October 2026 — Recent MCS classification completion and reset continuation

The owner asked to continue the MCS work and schedule another run after the usage reset. The usage tool showed the next five-hour reset at1November02:03:46IST; registered one same-thread local heartbeat for02:10IST, ID `continue-mcs-review-after-usage-reset`, and verified its saved active configuration. It is one-time (`COUNT=1`), not a new recurring project. Its prompt reads the latest checkpoint before working, preserves the2012/2013deferral, and treats website publication quotas separately from Codex usage. Local scheduled work still needs the machine/app running.

The starting bank/server were IN SYNC at81,627records,80,879approvedclassifications and13,021officialeligiblequestions (MCS1,411). Stopped the local publisher timer and waited until its service was inactive before changing the bank. Directly reviewed the148remainingrecentrestorations:54GS,1GK,8Science,57Aptitude,24English,4Mathematics. Shared source passages make the environment/empowerment questions reading comprehension, not topical factual recall. The closed registry lacks dedicated interpersonal/decision-making/spatial topics, so those retain a broad aptitude subject rather than a forced incorrect topic. Saved exact IDs, question baselines and evidence in `docs/sources/mcs-recent-learning-review.json`, and reviewed workshop claims in the bank repo. The bounded canonical merge had zero validation issues and changed exactly148classificationfields, leaving81,479otherquestionrecords and every non-classification field unchanged. All480recentrestorations are now classified; remaining600unclassifiedrecords are recovered2015/2017/2018sources,300GSand300Aptitude.

Original PDF inspection exposed an additional source defect:2023II C Q87's squared-surd formula had spilled into Q86 optionD, and its own choices contained private-font glyphs. Published three audited transcriptions: Q86 ends optionD at64cm; Q87 restores `(√5 + √2)²` and its four printed surd choices; Q96 restores the four printed fractions. Q86 remains compensated/held, and Q96's unresolved-source flag intentionally remains until a distinct defect review. These changes assign no answers. Exact before/patch/source/publication evidence is saved in `docs/sources/mcs-recent-transcription-repairs.json` and ignored reports.

The key preparer now refuses private-font glyphs and reports repaired transcriptions for explicit manual remapping rather than reusing stale OCR. It still checks source PDF hashes, full ordered choices and each booklet's own final-key table. Its first new preview produced140mappingcandidates, plus the already329publishedkeys, six compensated restorations, three source flags, repairedQ87manualmapping and2025II C Q39's damaged root glyph. Chose60candidates within the ordinary staff allowance (437of500alreadyused after the three source repairs). The first batch preflight correctly rejected an unregistered exact-booklet final key before creating any decisions. Registered the six required booklet mappings, staged six hash-verified PDFs with root:www-data0640permissions, rechecked the registry, and retried through ordinary audited maintenance. No quota exemption was used. Published all60keys with null explanations; audit reasons do not pretend to be worked solutions. The next read-only preview reports80remainingautomaticcandidates and389alreadyansweredrestorations. Staff usage is now497of500inrolling24hours; the scheduled Codex reset will not replenish it.

Validation:30focusedbackendtests passed, covering source restoration, key cells, bounded publication and tags, with an added regression guard for damaged/repaired mathematics and changed option order/page. Full-bank/live verification checks all148classifications, three source patches,60answers and63appliedpublications, unchanged source flags/24compensatedholds, no invented peer decisions or rewards, and preserved learner attempts/unlimited owner access. MCS now has1,471officialeligiblequestions outof2,977active; global official pool13,081outof81,627. Bank/taxonomy sync and publisher restoration are checked before stopping. No frontend/API/schema/Caddy deployment was needed, and no new browser acceptance is claimed. Work evidence/checkpoint: `reports/mcs-next-review-20261031/`; next work is recorded in PLAN and MCS-COMBINED. Authentic simulation remains gated on source/key/content readiness.

## 31 October 2026 — Continued recovered MCS tags and completed two maths repairs

Started clean at `dd40eff`, with bank/taxonomy IN SYNC,81,627questions,81,027approvedclassifications, MCS1,471officialeligible and no exported publications. Live staff usage was497of500inrolling24hours; the oldest current contribution is31October15:56UTC, so the1November02:10ISTCodexcontinuation will still precede publication allowance becoming available. Did not create another automation or use a quota exemption. Paused the local publisher timer and confirmed its service inactive before publication/merges.

Previewed conservative exact-signature reuse for the six recovered2015/2017/2018booklets. Of600unclassifiedrecords,373had full normalized stems and ordered choices with unanimous existing approved paths;161had no exact match,30conflictingpaths and36sourceflags. Checked all six recovered PDF hashes against the committed source manifest. Saved bounded workshop claims and `docs/sources/mcs-recovered-learning-reuse.json`, merged precisely373IDs with zero registry issues, and proved that only their classifications changed. No answers transferred. Verified the373livepaths and null answers, then directly reviewed the remaining64GSappearances from full stems/options against the closed registry and saved `mcs-recovered-gs-learning-review.json`. Science anatomy/polymer/physics questions receive Science; environmental conservation stays Environment; Mizo customs/history stays Mizoram rather than Mizo grammar. This brings all300recoveredGSappearances into learning filters;163recoveredAptitudeitems remain for direct review. Source defects remain independent of classification.

Used the final three ordinary publishing actions for one source correction and two answer decisions. Rendered and inspected2025II C physicalPDFpage7/printedpage6: Q39 gives `(√3 = 1.73)`, not the corrupted private-font text. Published that transcription with no answer assignment, retaining all ordered choices/page/source image. Visually checked both exact final-key tables:2023II C Q87=C and2025II C Q39=B. Published both with actual worked explanations: `(√5 + √2)² = 7 + 2√10`; tree bend height `24tan30° = 8√3 ≈ 13.84m` using the supplied approximation. This consumes500of500staffcontributions. No peer votes, review credits, source-hold releases or inferred official labels were fabricated. Exact source/key/publication audit is committed in `docs/sources/mcs-reviewed-maths-final-keys.json`.

The key preparer's prior gate order kept an already-reviewed repaired source listed as unfinished manual remapping. Move its existing already-answered skip before the changed-transcription gate: this is a new-key preparer, not a retrospective content auditor. Unanswered private-font/different-option/page cases still require source/manual review, source PDF/key/hash guards remain, and answered repaired questions no longer reappear as new work.30focusedtests pass. The next preview is80newmappings/391alreadyanswered/sixcompensated/threesourceflags; these80must wait for ordinary allowance, while the scheduled run can continue offline source/tag/explanation review.

Final full-bank diff allows437classificationchanges and only the two maths question objects (one transcription and two audited key/explanation patches), preserving the other81,188questionobjects and every other field/paper. Normal sync/live checks confirm81,464approvedtags, MCS1,473officialeligible/global13,083, active MCS2,977, GS0/Aptitude163unclassified, all24compensatedholds, the three recent unresolved-source flags,243learnerattempts,71users and existing unlimited owner access. Three audited publications are applied with no pending exports. Evidence: `reports/mcs-followup-20261031/`, including full-bank proof, live439recordchecks, source renders, key-cell images, test logs and next-key checkpoint. No UI/API/schema/Caddy deployment or fresh browser acceptance claimed. Publisher timer is restored after verification, then code/docs are pushed.2012/2013remainsdeferred; source/option review, remaining Aptitude tags, explanations and historical numbering still gate full original-paper simulation.
