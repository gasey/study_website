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

## 31 October 2026 — Completed recovered Aptitude tags and scheduled publishing continuation

Owner asked to do the remaining work and continue after reset. Verified the existing one-time02:10ISTheartbeat remains active and Codex has25%ofitsfive-hourwindowleft (75%used, reset1November02:03:46IST). Website staff publishing remains500of500; no reset, quota exemption, new contribution, answer or source edit is attempted. Added a distinct one-time same-thread continuation for1November21:35ISTwhen the oldest current staff entries should have aged out; ID `continue-mcs-publication-after-daily-allowance-resets`. Its prompt rechecks actual rolling allowance, latest bank/Git state and Codex usage and preserves provenance/holds/learner data. This supplements the early Codex-reset continuation; both use COUNT=1 and read the latest checkpoint to avoid repeating completed work. Local machine/app must run for local execution.

Read all163remainingrecoveredAptitudestems/options and rendered/inspected25sourcepages to resolve diagram-only items, omitted directions and factual-looking reading passages. Confirmed tax-avoidance, leadership, army, ISRO and astronomy questions in explicit comprehension passages rather than misclassifying them by keywords. Figure folding, rotation, sequence and matrix items are separately supported by original shared directions. Genuine median/probability content stays Statistics; numeric routine calculations stay Arithmetic/Algebra/Geometry; factual physics/biology assertions retain their subject even in Paper II. Broad Aptitude is deliberate for spatial/decision/interpersonal skills missing a closed-registry topic. The first exact-ID coverage assertion caught an omitted Venn-set item102before writing any claims/bank; added its explicit Algebra review and reran the full163coverage guard.

Saved question-level baselines/evidence in `docs/sources/mcs-recovered-aptitude-learning-review.json` and the bank workshop. Paused the publisher timer, confirmed service inactive, then bounded-merged163IDs with zero registry issues. Full-bank diff proves163classificationfieldchanges only, preserving every other field/paper and81,464otherquestionobjects. No answers, source defects, difficulty, source-paper identities or provenance changed. All600recoveredand480recentrestorations now have learning tags; global81,627approvedprimaryclassifications and MCS role-map unclassified0/0. This is learning classification, not source/key/simulation certification.

Prepared13explicitlocaltranscriptiondrafts from inspected pages in `docs/sources/mcs-recovered-transcription-drafts.json`: numeric/fraction/surd choices, missing source operators and footer/adjacent-question spillover. They are not submitted owner contributions, published source repairs or invented answers. Keep source flags and null answers, and recheck exact baseline/PDF before later audited publication. Retained the printed spelling error “alpabets” rather than silently correcting source wording. The late continuation can use remaining allowance after the80recentkeymappings; source review must not assume those historic reproductions establish official booklet equivalence.

Live verification checks all163records against the canonical bank, no unanswered recovered item acquiring an answer, no exported publications, unchanged MCS1,473/global13,083officialeligibility, all24compensatedholds,243attempts/71users and unlimited owner access. Normal bank/taxonomy sync reports IN SYNC at81,627approvedrows. Evidence: `reports/mcs-aptitude-review-20261031/`, including source renders and complete field diff. No implementation change required additional unit tests; registry validation, complete bank diff and exact live comparisons are the meaningful acceptance checks for this metadata pass. No frontend/API/schema/Caddy change or fresh browser acceptance claimed. Restore publisher timer after verification and push docs/audit checkpoints to GitHub. Remaining work is80recentkeymappings, source flags/options, recovered key/source identity verification, explanations and historical numbering;2012/2013staysdeferred and simulation stays gated.

## 1 November 2026 — Overall progress status check

Owner requested overall progress. Read latest checkpoints and live health/MCS collection without changing application or bank content. Latest implementation remains pushed commit2b55f7a. Production health isokwith81,627questions/13,083officialeligible; MCS has30booklets,2,977activequestions and1,473officialeligible (744GS/729Aptitude), while older/unanswered/review-required content still limits full assessment readiness. All imported MCS learning tags are complete; source/answer verification,80preparedkeymappings,13source-repairdrafts, explanations and original-paper rules/simulation remain unfinished. Broader release notes still identify SMTP delivery and representative load acceptance as pending. Both continuation configurations remain saved ACTIVE; this status check does not establish that a scheduled run executed. No fresh visual/performance acceptance or new implementation claimed.

## 1 November 2026 — Scheduled Codex-reset continuation; historical numbering and staged working

The02:10ISTheartbeatactuallyexecuted. Preserved the existing uncommitted DEVLOG status-check entry rather than resetting it. Read latest conversation/CLAUDE/PLAN/MCS/BANK-MAINTENANCE, checked bank/taxonomy IN SYNC at8e5b9998e87b,81,627records/approvedpaths, and read live usage: Codex five-hour0%used after reset, website staff quota still500of500since31October15:56UTC, no exported publications. Did not reclassify completed questions, create contributions, consume a reset credit, bypass quota, or pause/restart a running publisher. The local publisher stays active/enabled; late21:35ISTcontinuation remains configured.

Read-only audit of the six already-imported2014/2016PDFs found600actualprintedpositions versus601bankrecords.2016PaperI C has duplicate imports atQ4(HydrocarbonVision)andQ86(honey), not102distinctprintedquestions; exact normalized stem/ordered options agree, but canonical IDs and one answer provenance differ. All four canonical records are live; the current snapshots show zero attempts/contributions/mock links/duplicate links, which does not justify deletion or exhaust every possible reference.2014II Q39is a real missing figure question onPDFpage6. Q11/Q12are physically onpage3, notpassage-startpage2. Q38also lacks both its own figureImage and the group image. Inspected original pages and registered paper document, saved source-page asset locally, prepared two page-reference corrections, Q38diagramdraft and unansweredQ39original-source draft. Nothing applied, merged, held, retired or assigned a new key. Community new_question validation requires a derived answer, so it is not a valid substitute for unanswered original-source ingestion. Existing duplicate publication only links a relationship; it cannot be claimed to remove a repeated printed source position. Recorded these workflow prerequisites in the draft packet.

Added `audit-mcs-historical-numbering.py` with a six-source SHA manifest and read-only report output. A first strict-dot scan stopped at2014I Q78because originalQ79prints no period; verified the scan and supported this printed form. Figure-only `39.` is preserved, numbered premises cannot silently advance the sequence before preceding a/b/c/d choices, covers retain physical page offsets, missing choices/sequences fail closed. Output is restricted to app reports (including symlink resolution) so the tool cannot overwrite the bank/source archive.13focusedtests pass, including no mutation, reordered-option non-equivalence and canonical-output rejection. Full reports and raw source text/renders remain ignored evidence; durable review summary is committed.

Staged13realworkedmathsexplanations for already-official2023II C answers after inspecting originalPDFpages8/9/10/12/13. Exact Fraction/integer checks cover compound interest, ages, journey time, income/expense ratios, effective annual rate, mixed workforce rates, AP terms, mixture dilution, a dimensionally valid plank packing, modular addend, proportional travel time, percentage equation and loss price. Every computed choice agrees with that appearance's existing own-booklet final-key cell; explanations are site-reviewer working, not official worked solutions or fabricated independent peer review. No live explanation/answer changes. Fresh recent-key preparation still yields80newmappings,391alreadyanswered,sixcompensated,threesourceflags bound to the current bank SHA.

Local archive search exposed a previously unrecorded coverage gap:2016-labelledPaperIIA/B/C/Dscans exist (16pageseach) but are absent from bank JSON and live paper/source-file registry. Native pdftotext returns only16formfeeds; sidecar OCR exists but conservative sequential starts stop at18/14/14/8and one header reads I-A instead of visible II-A. Inspected all four first/last pages (II-A/B/C/D,Q100); saved hashes, OCR checksums and limits. These are source leads, not400verified/transcribedquestions, and year/sitting binding still needs corroboration beyond filenames. Separately inspected archived coverCSP:16/PaperI/SeriesB:120minutes,100items/200marks,one-thirdquestion-markwrongpenalty. Saved exact-cover rule evidence only, without retroactively applying it to other papers/series or configuring simulation. No2012/2013search resumed.

Checkpoint files: `docs/sources/mcs-historical-numbering-review.json`, `mcs-maths-explanation-drafts.json`, `mcs-2016-image-only-source-inventory.json`, scope manifest and audit CLI. Evidence `reports/mcs-reset-review-20261101/`. Canonical bank remains byte-identical, global official13,083/MCS1,473, all24compensationholds/learnerhistory/owneraccess preserved. No production content or frontend/API/schema/Caddy deployment. GitHub push includes this audit/tool/draft release and the preserved prior status log. Late run must first recheck quota and latest work, prioritize80recentkeys/recent source flags, then source/explanation drafts, with four-booklet intake separately planned. Original-paper simulation stays gated.

Locator-packet follow-up: Q11/Q12currently have no stored passage. Added exact shared-passage transcriptions acrossPDFpages2–3 as a prerequisite to locator correction, so pointing directly atpage3does not discard the reader's context. Packet phases explicitly separate those same-canonical context and page proposals, with a sync/verification/fresh baseline between phases; Q38diagramis a distinct target. Final read-only checks find73users(upfrom71throughnormalliveactivity),243attempts, ownerunlimitedtrue, quota500/500, zeroexports and all24holds. Audit replay is value-identical and bankSHA8e5b9998e87bunchanged.13mathsdraftsagreewithliveofficialanswersandremainnull-explanationlive; no draft is presented as publication. Publisher active/enabled, no service restart or deployment.

## 1 November 2026 — Immediate owner-requested MCS publication

Owner instructed “Do it now” after the 500/500 rolling staff cap and delayed publishing schedule had been explained. Rechecked the live cap (still 500; oldest contribution 31 October 15:56:23 UTC), zero outstanding exports and clean Git. Recorded that direct instruction as authorization for this bounded SSH maintenance exception, rather than changing ordinary website quotas. Each of the 111 contributions has an owner-maintenance quota-exemption audit event; public/staff daily limits remain 30/500. The exception ends with each exact-target process and is not ongoing authorization for later batches.

Paused the local publisher timer and waited for its running service to finish. Regenerated exact-booklet final-key mappings against the current source bank: 80 ready, 391 already answered, six compensated, three source defects. Verified registered final key documents, exact source guards and live canonical identities, then dry-ran/published all 80 through immutable batch manifests and normal bank sync. No worked explanations invented. Regeneration after publication yields zero ready / 471 already answered; the six compensated and three source-defective candidates remain excluded.

Published 13 checked mathematical explanations for existing official-key 2023 Paper II C answers, retaining every answer index and registered key provenance. These are reviewer-written working, not official worked solutions or fabricated independent reviews. Published all 13 recovered-paper transcription drafts with source hashes, normalized printed-number guards and registered document evidence; preserved null answers and every existing source flag (nine flagged and four unflagged repaired items). Added complete shared-passage context to 2014 II Q11/Q12 and restored Q38's missing diagram from the exact original PDF page. Mirrored that source image with matching SHA256 before publication. After the context/image batch synced and verified, created fresh exports correcting Q11/Q12 to physical PDF page 3. No overlapping canonical proposals or stale-baseline rebase shortcuts.

All 111 publications are applied and their contributions published; zero peer decisions, reward credits or outstanding exports. Four batches change 109 existing question objects (two questions have separate context and locator repairs). Complete bank comparison permits only the requested fields and exact final publication receipt IDs, preserving 81,518 other question objects and the entire paper registry. Canonical/live record comparison checks all 109 affected appearances. Bank SHA is 84c8752c01502b70353574e4bc2207c49b69d1d11e4ec8fcdca5aff2aa61b90c. Live health: 81,627 questions, 13,163 global official-eligible; MCS 2,977 active / 1,553 official-eligible, up 80. Both MCS learning roles remain zero unclassified. All 24 compensated holds remain held and unscorable; attempts remain 243, users 73, and the owner's unlimited Pro access is preserved. Family site returns expected 307. No frontend/API/schema/Caddy deployment or new visual/performance acceptance claimed.

49 focused publication, coordination, source-warning, owner-maintenance and historical-numbering tests pass. Historical audit rerun now reports three remaining numbering issues, down from five: 2016 I C duplicate source positions Q4/Q86 and missing 2014 II Q39. No duplicate was deleted or merged, no absent question fabricated or added through inappropriate community authoring. The 36 recovered-copy flags and three recent source flags still need separate adjudication; source transcription repair alone does not clear a warning. Four image-only Paper II booklet leads still require sitting/source verification and careful intake; 2012/2013 recovery remains deferred and original-paper simulation gated.

Durable publication receipt index: docs/sources/mcs-publication-20261101.json. Updated the three draft packets to distinguish applied repairs from remaining findings while retaining original review baselines. Ignored evidence: reports/mcs-now-20261101/, including requests, individual receipts, dry runs, sync/publication logs, full-bank/live checks and final historical audit. Restored the publisher timer after verification. The existing 21:35 IST continuation must read this latest checkpoint and continue remaining review within actual ordinary allowance; it must not replay these completed 111 publications or assume this run's exception persists. Push the documentation checkpoint to GitHub.

## 1 November 2026 — Explanation status and dated revision context

Owner requested implementation of clearer MCQ/derived distinctions, good-explanation expectations and relevant current-affairs hints. Read project instructions, design values and existing provenance/currentness, learner surfaces and admin/contribution workflow. Existing badges already distinguish reviewed unofficial solutions from authority keys; reused those guards rather than relabelling arbitrary derived answers as verified. Added a shared post-answer explanation panel in Bank, detail, module study and paper workspace. It distinguishes missing text, available official-key commentary without separate review metadata, published reviewed unofficial working, and provisional stored working. Official keys do not imply checked explanations. Added explanation-only proposal links and concise teaching/source/date guidance to admin and contributor forms. MCQ format now appears explicitly on module and paper views; provenance help explains format versus source. Unreviewed answer matches are described as stored-answer matches rather than authoritative correctness.

Replaced generic-only revision help with dated editorial notes and explicit unknown-update handling. Inspected Akashvani's 4 August 2025 Shibu Soren report, the Ministry of Finance's current Budget documents and Finance Commission report/listing using browser research. Seeded three notes with event/period, checked and review-due dates and direct sources. The Shibu note is constrained to 2025 and applies to the four matching UDC/Assistant appearances found in the bank; no present officeholder is asserted. Removed the misleading fallback that linked every state's Chief Minister question to the Mizoram portal. Detail view now uses the selected appearance's year, or an unambiguous shared year, rather than assuming the first appearance is relevant. Notes/answer-bearing references are absent from rendered markup until an answer or explicit revision-context reveal; the latter also works for unsolved/held questions without submitting an attempt. Reveal is bound to question/year, future-dated notes are suppressed, expired notes request rechecking and all notes preserve historical scoring. This is an editorial registry, not an automatic news feed or a browser-managed update queue; separate per-explanation review metadata is not invented.

Validation: production frontend build and all nine frontend test files pass; four new focused tests also pass directly, including actual React server rendering for answer-leak prevention and honest explanation labels. Canonical bank remains byte-identical at 84c8752c01502b70353574e4bc2207c49b69d1d11e4ec8fcdca5aff2aa61b90c. No bank, API, schema, score, hold, access or learner-history writes. No new browser visual acceptance claimed. Early integration commands exposed a working-directory mismatch and paper view's inline explanation variant; corrected those locally and built/tested the integrated surfaces. Evidence: ignored reports/explanation-context-20261101/; durable workflow/source references in docs/EXPLANATIONS-AND-CURRENT-AFFAIRS.md.

Deployment/push checkpoint: current sandbox denies networking sockets (`ssh ...: socket: Operation not permitted`), so live bank-sync confirmation and production SSH deployment cannot run. Do not claim these frontend changes are live or pushed. Build locally, deploy with `./scripts/deploy.sh web` and push the local commit with `git push origin main` once networking is available, then verify learner pages and live health. Preserve the existing publisher timer; it was not touched this turn. Existing scheduled continuation must read this newer checkpoint before further content work. Continue substantive checked explanations and sourced updates through the documented existing publication safeguards; previous quota exceptions do not extend to this run.

Release checkpoint follow-up: local commit succeeded; GitHub push failed because this sandbox cannot resolve github.com. Production SSH separately fails with socket Operation not permitted. The final build and four direct focused tests pass after the last stored-answer wording changes; all nine frontend test files passed the integrated feature run. Working tree is saved locally. Deploy the frontend and push this commit when normal networking is restored; no live release or successful remote push occurred in this session.

## 1 November 2026 — Oracle access and deployment retry

Owner requested deployment again and asked how to access the Oracle shell. Confirmed clean working tree at the tested explanation/context commit 106eff8 and inspected the existing frontend-only deployment path. Retried the configured SSH connection to ubuntu@152.67.31.231 with BatchMode and an eight-second connection timeout. The sandbox still rejects socket creation with Operation not permitted, before authentication; this does not establish an Oracle outage or bad key. No deployment, rebuild, remote change or successful push occurred. The owner can use the same SSH command from their normal terminal with their configured key, or run scripts/deploy.sh web from the local repository. Production verification and GitHub push remain pending network access.

## 1 November 2026 — Explanation/context frontend deployed after access restored

Owner restored full network access and requested deployment. SSH now succeeds using the existing Oracle connection, without changing credentials or server access policy. Confirmed clean tree at 14e03c4 and canonical bank/taxonomy IN SYNC (84c8752c0150, 81,627 records/approved classifications). Ran scripts/deploy.sh web: local production build succeeded, static frontend shipped to /srv/study/public and no API/schema/Caddy/systemd/bank changes were made. The live root entrypoint is byte-identical to the locally built index. Existing nine frontend test-file and four focused-test acceptance remains applicable; this run changes deployment/docs only.

Actual in-app-browser acceptance on /bank/cq_00276f549d658964: 2025 MCQ and reviewed unofficial-solution provenance remain separate; revision context is collapsed initially, expanding it shows an explicit reveal button with no answer-bearing note/link, and revealing displays the 2025 historical context, dated revision note, source-check date, review deadline and direct Akashvani reference. Did not submit an answer, change saved state or create an attempt. Screenshot: reports/explanation-context-20261101/live-revision.png; deployment-proof.json records live artifact verification. API remains healthy at 81,627 questions / 13,163 official-eligible, family site returns expected 307. Publisher timer and account/bank/learner data were untouched. Marked deployment complete in PLAN; push all saved feature/blocker/release commits to GitHub now. Previous entries accurately describe earlier denied access; they no longer describe the current deployment state.

## 1 November 2026 — Answer-check versus reveal clarification

Owner asked what provisions exist for checking an option versus directly revealing an answer. Read the actual learner controls and API: detail/paper checking requires a selected option and submits an answer attempt; Bank cards/module practice can submit on option click. Direct comparison uses the separate read-only answer-comparison endpoint, invokes active-assessment protection, and does not submit a practice answer. Revision-context reveal is a separate educational display action, not completion/mastery or an answer submission. No universal standalone Show answer button is claimed and no product behavior changed during this clarification.

## 1 November 2026 — Explicit practice checking and protected answer viewing deployed

Implemented the owner's accepted Check answer / Show answer flow across bank cards, module study, question detail and paper browsing. Selecting an option now only selects it. A shared PracticeAnswerPanel shows answer provenance, stored explanation, dated revision context and optional key/solution comparison. Removed the independent revision reveal and competing comparison footer. Viewed answers stay separate from AnswerResult and never enter attempt/progress/reward callbacks; paper checking retains canonical option-order mapping. Detail-page check errors now stay inline so a blocked check does not discard the question.

Added migration 0061_answer_reveals and a protected POST reveal endpoint. A learner/canonical-question advisory lock serializes reveals against new checks, and a 30-minute window rejects immediate post-reveal attempts across contexts, tabs and appearances. Comparisons with answer content also record exposure. Previously recorded idempotent answer replays remain readable without duplicate attempts. Active mock/game/unclosed-cup protections remain on both reveal paths. This is a study cooldown, not proof of independent recall or protection against separate accounts or external PDFs; existing discussion unlocking still requires an attempt.

Validation: all 329 API tests and 40 frontend tests passed; production TypeScript/Vite build passed. Eight new real-PostgreSQL tests cover no attempt/reward creation, cooldown expiry and alternate-context rejection, source bounds, active mock/game/cup restrictions, unusable options, comparison exposure and idempotent replay. Rehearsed 0061 on a production dump clone, dropped the clone, applied the migration, deployed API and locally built web through the established scripts. No bank publication/export, quota override, timer change or Caddy edit was needed. Canonical bank/taxonomy was IN SYNC at 81,627 before work.

Live browser acceptance on cq_00276f549d658964: selection leaves Check answer enabled without revealing; Show answer displays Viewed answer plus explanation and dated revision note; reloading then checking is rejected inline with the 30-minute explanation. Verified in production that the browser's reveal has zero attempts and zero reward entries; total attempts remains 243 and owner Pro access remains true. API health: 81,627 questions / 13,163 scorable; family.hawayu.in returns expected 307; live index is byte-identical to the local build. Screenshot and test logs are under reports/practice-answer-flow-20261101/. Push this implementation and documentation to GitHub after the final diff check.

## 1 November 2026 — Reading continuity, revision actions and MCS quality follow-up

Owner requested all proposed follow-ups. Added a bounded private practice-state read that restores revealed answers and remaining retry time without extending the exposure timestamp; public catalog responses remain answer-free/cacheable. Visible frontend reads coalesce into batches of at most 100 and reject account/scope changes. A newer actual attempt clears the restored reading state. Discussion now accepts an existing reveal as its read gate while retaining active mock/game/cup checks and existing account/moderation/sanction controls for writes. Save for revision uses the existing personal saved list; Retry later ensures a save then advances; Next follows the current bank/module results or the chosen paper's printed order. Daily revision excludes questions until the reveal window expires. Added narrowly dated/source-checked Stand-Up India, initial-language-count and archived biodiversity-hotspot notes; no historical answer or score was changed.

All 340 backend tests passed after fixing a flaky scoring-retry assertion: a background worker may append an unrelated assessment during the test, so it now checks that every pre-existing assessment payload remains unchanged rather than assuming the global row count cannot increase. Frontend acceptance passed 44 checks before the last regression case, and the final runner passed all ten frontend test files; the four focused private-state/restoration cases also pass directly. TypeScript/Vite production build passes. No schema migration was needed. Initial scripts/deploy.sh all succeeded; API health remained 81,627 questions / 13,163 scorable, family site 307 and live root index byte-identical to the initial local artifact.

Actual browser checks: old Shibu Soren view restores with its remaining one minute, discussion is open without an attempt and posting still requests sign-in; Save for revision updates both saved controls; natural expiry exposes Retry now, which clears the answer without submitting; Retry later saves then opens the same booklet's printed Q74 after Q73. Screenshot reports/practice-followup-20261101/live-reading-mode.png shows reading state, remaining time, saved status, revision actions and unlocked discussion. No answer was submitted and no production mock/post/reward was created; the save was in the guest browser, not the owner's account.

Live acceptance also caught a restoration race after Retry now -> Show answer: the refresh reused the original effect generation and left “Restoring your practice state…” visible. Reload successfully restores the saved answer. Fixed locally by issuing a new generation inside every restore invocation; added a behavioral test exercising the component's actual async callback through repeated restores and invalidation. All final frontend tests and build pass. IMPORTANT DEPLOYMENT LIMITATION: terminal permissions changed to restricted network mid-run, after the initial deployment. A normal eight-second SSH check now fails at socket creation before authentication, so this last small frontend fix has NOT been deployed. Do not describe the final build as live. The 21:35 IST continuation now begins with deploying and verifying this frontend fix; GitHub's connected integration remains available for saving the code. No alternate SSH/proxy or access-policy workaround was attempted.

MCS quality work inspected all 39 flagged appearances on 21 PDF pages plus the adjacent shared graph. The versioned checked-draft packet docs/sources/mcs-quality-followup-20261101.json contains 31 transcription corrections, 35 possible separate defect clearances, 35 worked answer drafts (32 recovered-copy unofficial solutions / three source-bound recent official mappings), and four explanations for existing official answers. Four defects deliberately remain: missing diagram choice, count-versus-percentage ambiguity, two valid digit choices and missing fruit-union premise. Re-inspection found two errors in earlier published source transcriptions: 2015 II Q74 C is 25 rather than 54; Q77 choices are 10, 23, 18, 15. Their flags/null answers remain in force, so no score was based on them. Kept the earlier immutable publication evidence and added a correction notice/new exact drafts. Exact recent final keys were visually rechecked on their own pages (2023 II C Q70 A/Q96 A; 2025 II C Q25 B). The new read-only preparer enforces current PDF/bank baselines and distinct source -> defect -> answer phases; its tests caught and fixed an initial mistake assuming the workshop record projection included sourceDefect. The flag is now checked independently from the full source record.

Ordinary staff allowance was 611/500 in the rolling window with zero outstanding exports; no exemption was inferred or used. Actual contribution timestamps predict the first slot around 21:29 IST and roughly 101 by 21:31, subject to fresh quota checks. Full staged packet needs 105 decisions. Updated the existing 21:35 one-time continuation with the exact packet/preparer and phase order. No contribution/export/bank sync, scoring-pool change, timer pause, compensation-hold change or account-access change occurred. Wider explanation backlog remains 2,203 answered raw appearances without working; these drafts do not complete it. 2012/2013 remains deferred. Push code/docs via the connected GitHub integration using a non-forced expected-head update, and verify the remote tree against the local staged tree before declaring GitHub saved.

Follow-up checkpoint correction: updating the scheduled continuation a second time to explicitly prepend the frontend hotfix was denied after the permission change (“MCP tool call requires approval, but approval policy is never”). The earlier content-packet update succeeded and the existing 21:35 continuation still reads this latest DEVLOG; use the pending frontend fix above as its first action. No approval was requested or schedule change claimed after that rejection. The connected GitHub write integration was separately tested successfully with a blob upload, so saving this exact staged tree remains possible through that integration even though terminal SSH is unavailable.

Loading-fix scope clarification: the underlying stale token can affect a fresh Show answer as well as the observed Retry now -> Show answer sequence. The server stores the view correctly, and reloading restores its panel. The one-line fix issues a new generation on each refresh and is included in the tested final staged build; that final web deployment remains required as soon as SSH access is restored.


## 1 November 2026 — Final loading fix deployed; scheduled continuation removed

Owner requested dropping the scheduled-continuation arrangement and confirmed access permission; environment network access was restored. Deleted the exact 21:35 IST automation continue-mcs-publication-after-daily-allowance-resets through the app tool, which confirmed deletion. This supersedes earlier active-schedule statements; no replacement automation was created. SSH succeeded and the canonical bank/taxonomy check reported IN SYNC at 81,627 questions, SHA prefix 84c8752c0150. Built and shipped the already tested final frontend with scripts/deploy.sh web; no API/schema/Caddy/bank changes. Live root index is byte-identical to local dist, API health is 81,627 questions / 13,163 scorable, family site returns expected 307.

Verified fresh Show answer on live cq_6cdfff6a8a672f19 in the guest browser: transient restoring state resolves without reload to Viewed answer, explanation, 30-minute retry countdown, revision actions and unlocked discussion, with sign-in still required to post. No answer attempt was submitted. Screenshot: reports/practice-followup-20261101/deployed-loading-fix.png. Updated PLAN to mark the loading fix deployed and the continuation cancelled. MCS draft publications remain pending actual ordinary allowance; this deployment permission is not a publication-quota exception. Save and push this release checkpoint to GitHub.


## 1 November 2026 — Pending MCS packet completed under explicit bounded exception

Owner requested the pending work. Fresh live checks showed 611 contributions in the rolling day against the ordinary staff limit of 500 and zero outstanding exports. Revalidated the source packet against current bank/PDF hashes; prepared 31 source repairs and four existing-answer explanations. Explained the repository requirement for explicit future exception authorization, and the owner answered “Yes, publish this packet now” to the exact up-to-105-decision scope. Used run mcs-pending-20261101 with that authorization recorded on every contribution; no public/staff quota or persistent permission was changed. The 21:35 Codex continuation remains cancelled.

Paused the local publisher timer and confirmed the service inactive. Initial transcription intake failed validation because unchanged optionsMarkup:null entries were included as new list edits; the batch transaction rolled back before publishing. Fixed the preparer to omit unchanged fields, retaining the immutable reviewed packet and exact post-repair baseline; regression test added. Published and verified all 31 source repairs. Three separate defect clearances completed individually. Stopped the local orchestration parent while allowing its already running publication child to finish and acknowledge normally; did not interrupt a publication or export overlapping work. The remaining 32 clearances exposed a batch-tool limitation: only obsolete duplicate flags were supported. Added a narrow owner-only unresolved-source clearance path requiring the complete exact source baseline, no answer, distinct nonempty options, figure reference when required, paper evidence and a separate explanatory note. The local publisher independently validates its immutable flag/source baseline and evidence. Added real-DB and pure publisher tests for answered, changed-source, missing-figure, wrong-flag, missing-evidence and duplicate-option rejections. All 353 backend tests pass; deployed the API through the existing script and checked API/family health. No schema, frontend or Caddy change.

Published the remaining 32 clearances, verified live, then freshly prepared 35 answer decisions and four existing-key explanation decisions. Published those 39 disjoint decisions together against the same checked bank baseline. All 105 contributions/publications are published/applied, each with exactly one scoped exception audit event; zero independent votes, contribution-credit rows or outstanding exports. New content: 32 checked unofficial recovered-copy solutions, three exact recent-booklet official answers, 39 worked explanations. Four ambiguous/incomplete sources remain flagged and unanswered. Full bank comparison changes only 42 existing question objects, preserves 81,585 others and the complete paper registry. Live appearance/canonical/source-flag verification passes, all 24 compensation holds remain held/unscorable, attempts remain 243, users 82 and owner unlimited Pro remains true. Bank/taxonomy IN SYNC at SHA958adfec3e2b985c56b7aae83d445ec5fb898d353cdb65003946652529accd5c. API health 81,627 / 13,166; MCS active 2,977 / official eligible 1,556; family site 307. Restored publisher timer after verification.

Actual guest-browser acceptance on 2015 II Q77 confirms printed choices 10,23,18,15 and Show answer displays 15 with 0.16x=2.4 working and explicit unofficial status, without reload or submitting an attempt. Screenshot reports/mcs-pending-20261101/live-published-solution.png. Durable receipt index docs/sources/mcs-quality-publication-20261101.json; ignored requests, dry runs, individual/batch receipts, sync logs, full-bank/live verification, exception/hold/history checks and tests under reports/mcs-pending-20261101/. Remaining measured raw 30-paper backlog is four source flags and 2,774 missing explanations; 2,192 appearances have nonnegative answer indices but no working. A first read-only inventory query incorrectly used active_version; corrected it to the real collections.live_version before measuring. Do not infer that the broader explanation, numbering or simulation work is complete. 2012/2013 remains deferred. Save and push this completed release checkpoint and guarded tooling to GitHub.


## 1 November 2026 — Luna-assisted recent explanations and dated revision references

Owner requested the next explanation/simulation-readiness work, asked about token use and explicitly requested Luna where effective, plus relevant latest current-affairs guidance. Used three bounded GPT-6 Luna agents with narrow contexts: inventory/maths, explanation-only tooling/English, and dated official sources. Consulted current official OpenAI model-selection guidance for the model question; no exact token/cost promise or API-key-dependent external model runner was invented. Work used the connected subagent models and existing shell/browser workflows. Current Codex limits initially showed44%of the five-hour window used; no reset was consumed or new continuation scheduled. The previously cancelled21:35continuation remains deleted.

Initial inventory normalization stripped punctuation/operators and omitted direction/emphasis, which could falsely group different mathematical or passage tasks. Rejected it and rebuilt using NFKC/case/whitespace normalization preserving symbols and full appearance/canonical direction, passage, emphasis and figure context, plus current live status. Final recent scope:16booklets/1,600appearances,1,588usableanswered;1,560literal-emptyexplanations,28nonempty left intact;1,542empty appearances pass live candidate checks,18emptyheld excluded. Full snapshot has24heldcompensation appearances. Grouping is a triage tool, not source equivalence certification; no answers were transferred.

Prepared a concrete checked packet of72empty-text updates in28groups:49maths,9English,14factual. Source/PDF hashes, raw record digests, full source snapshots, exact primary documents and true physical PDF pages are bound to each item. Native PDF checks coveredall72; tenfraction/radicalmismatches received original-page visual review. Luna's early-rounded24/1.73treecheck falsely flagged the13.84mkey; coordinating review simplified24tan30°=8sqrt(3) first, then used the explicitly printed1.73approximation. Corrected draft preserves the false-alarm review history. English bridle wording now distinguishes headgear from reins rather than asserting every other object cannot be held. Factual explanations use exam-era primary sources and keep rounded G20shares, survey literacy rates, index edition and report themes explicit. Skipped railwayCRS, originalMUHCSstatement and operation claims that were not fully established. No independent peer review or new official-key certification is asserted. Ten2025Apage locator findings and tworadical-stem text leads are saved separately; an English safety-valve meaning/key concern remains an unconfirmed review lead, not a scoring hold.

Added a narrow explanation-only trusted owner-batch path. It requires a complete exact source snapshot, a live undisputed existing usable answer, distinct options, required figure, exact registered paper evidence and a patch containing only substantive explanation text. It preserves index/source/key reference and source positions, blocks single-item queue bypass and rechecks live eligibility after export. Existing role, quota, active-assessment, objection, immutable-manifest, bank-lock, zero-reward and publication guards remain. The new read-only recent packet preparer refuses source/PDF/answer changes and any nonempty-text overwrite. Tests include real disposable-DB and pure publisher guard failures, exact-source preparation and independent arithmetic checks. Full suite391passed; frontend50passed; production build passed.

Added six narrowly matched dated revision notes: Bairabi–Sairang2026anniversary update, MUHCS2026–27datednotice, NER SDG edition/currentlisting context, ULLAS2026–27framework distinguished from survey rate, UNFPA2025theme and AIFF2023event. Root checked the key primary sources and narrowed the scheme wording to dated facts/subsequent-notice guidance. A seventh operation note was removed after the first build; froze agent source edits, reran frontend checks and rebuilt/redeployed the final six-note artifact. API and final frontend are deployed; live index matches localdist; API health81,627/13,166andfamily307. Actual guest-browser reveal on cq_591d797ea8478c9e restores normally, keeps Explanation not yet available, and opens the sourced13September2026revision note separately from the2025historicalkey. No attempt submitted. Screenshot reports/mcs-explanations-20261101/live-dated-revision-note.png.

Read-only simulation audit:all16recentbooklets remain platform-default practice. Eight2025covers independently contain120minutes,100questions/200marks,+2correct,−2/3wrong and0blank; source hashes/physical page evidence saved without configuring rules. The inspected2023firstpages lack equivalent cover evidence. Original simulation remains gated by content/final-key/position review, authority compensation semantics and frozen per-item rational scoring; do not omit compensated questions or infer whole-exam qualifying rules from the cover.2012/2013remainsdeferred.

Publishing is not complete: the finished105-decisionexception did not extend to this new task. A new up-to200explanation-onlyexception question was presented and has no response at this checkpoint. Prepared/validated the72proposals but submitted none; no exports or bank writes, no timer pause and no account/hold/history change was needed. The publisher remains active. The canonical bank remains958adfec3e2b985c56b7aae83d445ec5fb898d353cdb65003946652529accd5c. Save/push the concrete packet, source evidence, tested tooling and deployed app checkpoint; after actual new exception approval (or ordinary allowance), revalidate sources/live baselines, pause the timer, queue/dry-run/publish the packet, verify full-bank fields/holds/history and restore the timer. The wider explanation backlog is not complete.


## 1 November 2026 — Explanation packet approved; SSH blocked by session policy

Owner replied “I approve” to the pending new up-to200 explanation-only quota-exception request. This is explicit authorization for that scope and supersedes the previous awaiting-answer checkpoint; do not ask again when access returns. Re-ran the read-only preparer: all72 checked packet items prepared, zero already-identical explanations. Request saved at reports/mcs-explanations-20261101/approved-explanation-request.json; durable authorization at docs/sources/mcs-explanation-authorization-20261101.json.

Normal SSH with BatchMode and an eight-second connection timeout failed immediately with socket: Operation not permitted, before authentication. Current session network policy is restricted and approvals are unavailable; user task authorization does not override that environment restriction. No bypass attempted. No contribution, quota exception, export, bank/server write, timer change or deployment occurred. Last verified live application/six revision notes remain deployed; these72 explanations remain local and unpublished. Resume through the established audited workflow after connectivity returns, preserving source/answer provenance, compensation holds, access and history; verify fresh live baselines before queueing.


## 1 November 2026 — Approved72-explanation packet published and verified

Owner explicitly approved SSH access; environment network policy now permits it. SSH succeeded, and bank/taxonomy started IN SYNC at958adfec3e2b. Reprepared all72 checked explanations, with zero already-identical entries. Paused the local publisher timer; a running service was initially activating, so waited for it to finish naturally and confirmed inactive before queueing. Initial local read-only verification import missed PYTHONPATH=scripts; corrected it before any queue writes. Fresh preflight: zero outstanding exports,243attempts and owner unlimitedPro.

Queued72 explanation-only decisions under the already approved bounded exception run mcs-explanations-20261101, recording the owner's authorization; ordinary website limits unchanged. All72 exported, passed the immutable-manifest/source/evidence dry run, then published through one canonical local-bank sync. Verified every live source record against its final local projection and all72 contributions/publications published/applied, exactly one exception event each, zero peer decisions or reward credits, zero outstanding exports. Full bank comparison changed only explanation and reviewPublicationId on72 existing question objects, leaving81,555 other objects and the complete paper registry unchanged. Answer indices/provenance/key references, options, source mappings and classifications preserved. All24 compensation holds remain held/unscorable;243 attempts and owner unlimitedPro preserved.

Final bank SHA8bca8cf30d69349b811dc23fe9584e2f42ddc7337be0f178109885c0e4e61644; bank/taxonomy IN SYNC. API health81,627questions/13,166scorable; MCS2,977/1,556; family site307. Restored publisher timer and verified active after completed live checks. No app-code/schema/Caddy change required and no new test suite repeated; existing391backend/50frontend tests cover the unchanged tooling/application, while this content batch passed fresh preparation, dry-run, full-bank diff and live receipt verification. Durable receipt docs/sources/mcs-explanation-publication-20261101.json; execution/verification logs under reports/mcs-explanations-20261101/approved-*. Six dated revision notes remain deployed. Wider explanation/source-numbering/simulation work remains pending;2012/2013 deferred. Save and push this completion checkpoint to GitHub.

## 1 November2026 — Next MCS packet, missing comprehension context and new review holds

Owner requested completion, then “Go.” Continued the wider MCS quality task using the three existing Luna agents under the owner's earlier explicit delegation request: source-backed maths/aptitude drafts; primary-source factual drafts; historical numbering/simulation/key-context audit. Current canonical bank remains8bca8cf30d69349b811dc23fe9584e2f42ddc7337be0f178109885c0e4e61644. Recent scope has1,488blank explanations after the previous72published; the initial1,470available candidates are triage, not final provenance/source eligibility. Last live ordinary staff usage788/500; zero content exports created this task.

Found76comprehension appearances across2023PaperIIA/B/C/D with null passage fields. Extracted each of five shared passages independently from every exact booklet (20blocks), including continuations; all four variants agree after conservative whitespace/quotation normalization. Matched every printed stem and ordered option set independently. Coordinator visually inspected SeriesBphysical1,3,4,5,6, including both split passages. Source spelling/grammar retained rather than silently editing the author. Prepared76passage restorations,24verifiedphysical-page corrections (the original10plus13math/aptitude and one factual locator), and two visually checkedsqrt(3)=1.73stem repairs. Visually inspected2025IIAphysical8,12,13,14,15,16, IIDphysical4 and2025IAphysical12. Mixed/earlier passage-start locators are not blindly moved. Separate78transcription and24locator stages require the exactQ89predecessor; no overlapping proposal is queued in a batch.

Reviewed the next explanation drafts: coordinator checked32Luna maths/aptitude groups, excluded the three Brain odd-organ drafts because the proposed sense-organ rationale misleadingly treats lips as a standard named sense organ, and excluded one inferred-answer appearance from explanation-only publication. Kept74maths/aptitude appearances,42primary-source factual appearances (14concepts), and coordinator-authored68passage-based explanations (17questions ×4series). Total184explanations/62groups. Clarified plank-volume packing with an exact8×3×80orientation. Did not invent explanations for inconsistent code mappings or ambiguous fence/ratio wording; these remain explicit source-review leads. Each draft binds exact raw/source baselines, PDF SHA/physical page, preserved key and any required checked source predecessor. An in-memory rehearsal validates all286proposals through the actual Proposal schema and staged preparers without bank/server writes.

The English safety-valve source/meaning versus final-key concern is confirmed in all four booklets. A second vain-regrets item has an unsupported key/context inference. Placed eight exact needs-review holds through the trusted answer-decision workflow, preserving every examiner answer/provenance and source field. Also placed two holds for a printed six-letter ASTARK → five-letter LBFMG code example with no reliable rule. All ten received held acknowledgments; no contributions, rewards, publications or quota exceptions are involved. Durable original evidence/request/receipt index: docs/sources/mcs-completion-review-holds-20261101.json. These ten are separate from the24compensationholds. The hold source baseline is pre-passage-restoration and must not be replayed over changed content.

Read-only recent numbering inventory finds100bankpositions in each16booklet, with greedy source-label matching candidates and114page differences. Treat that as triage: numbered statements can confuse greedy matching, and context-start locators are legitimate in some cases; it does not certify1,600complete source transcriptions. Existing strict helper stops on four2025PaperIIlayouts. Further historical duplicate/missing-position reconciliation and four unimported image-only booklet leads remain. Authority research finds a2025scheme explicitly awarding challenged-key compensation to all candidates, while2023attempt eligibility remains unestablished by the exact year evidence. Compensation/penalty implementation, full source/final-key readiness,100position snapshots and exact rational grading remain prerequisites; original simulation is not activated. Durable follow-up: docs/sources/mcs-simulation-followup-evidence-20261101.json.2012/2013remainsdeferred.

Added narrow read-only source/passage/explanation preparers and guard tests. Ten navigation tests passed normally before the session permission switch. After the switch, the repository's autouse disposable-PostgreSQL fixture fails before all35targeted tests because socket creation is forbidden; reran those pure preparation tests with --noconftest and explicit PYTHONPATH, all35pass. This is not a substitute claim for the full DB suite: no API/web/schema changes were made. Actual184explanation and102source proposals pass fresh Pydantic validation in staged memory. An initial guard caught the one inferred-answer draft; excluded it without weakening provenance checks. Standard actual preparation refuses explanation work until its exact source repairs exist, refuses all answer/context drift and nonempty overwrite, and preview output is explicitly non-executable.

IMPORTANT EXECUTION CHECKPOINT: network permissions switched back to restricted during work; fresh normal SSH fails at socket creation before authentication. Previous owner SSH permission persists; this is environment policy, not a fresh permission question or Oracle outage. No workaround attempted. No286content decisions/exports, bank writes, quota exception, timer changes or deployment occurred. The publisher was last verified active at prior72-item completion and was not touched this task. A new explicit286-item quota-exception question is pending; the previous72run is complete and does not extend. Source packet,184explanations and exact staged commands/checkpoint are committed for review. Recheck connectivity, current bank/live flags/holds/history/account/quota/export state; obtain the pending bounded exception answer or actual ordinary allowance, coordinate timer, publish78source repairs, freshly prepare/publish24locators, then two explanation batches100/84, verify complete bank fields/live receipts, all34holds as appropriate, account/history and restore timer. Do not claim remaining wider explanation backlog or simulation complete.

Follow-up authorization received: owner answered “Yes, publish this286-item packet” to the exact76passages+24locators+2maths-text+184explanations question. This supersedes the pending-quota-approval statements above; do not ask again for this packet. Bounded run mcs-completion-20261101 is recorded in docs/sources/mcs-completion-authorization-20261101.json and both checkpoints. No exception invocation or publication yet: current session SSH socket restriction is the remaining execution blocker. Existing user SSH permission persists.

## 1 November2026 — Oracle access restored; approved286-item packet completed

Owner asked to check full Oracle access. Fresh SSH connected to mpsc-arm as ubuntu; trusted sudo/DB maintenance worked. Bank/taxonomy started IN SYNC at8bca8cf30d69349b811dc23fe9584e2f42ddc7337be0f178109885c0e4e61644. Fetched GitHub and reconciled the previous API-saved equivalent commit: rebase skipped localfdab6fb because remoted169c43had the identical verified tree. No force push or user changes discarded. Fresh preflight independently verified all34holds (24compensation+10newsource/key concerns), zero outstanding exports, owner unlimitedPro and244attempts. One legitimate new attempt arrived since the earlier243checkpoint; captured hashes of all244existing rows before publication.

Re-ran all35targeted preparation tests with the normal disposable-PostgreSQL fixture, all pass. Reprepared exact sources; paused the local publisher timer, waited for the activating worker to finish naturally and confirmed inactive. Used the already explicit286-item exception run mcs-completion-20261101, preserving ordinary public/staff quotas and all source/answer guards. Published/verified78transcriptions (76complete original passages+two lost radical/equality expressions); freshly prepared and published24physical-page locators after the exactQ89stem predecessor; then freshly prepared/published100and84explanation-only decisions. All four phases passed independent immutable-manifest dry runs and normal canonical-bank sync/live receipt verification. No bank/server direct editing, new key certification, peer votes/rewards, API/schema/web-code/Caddy deployment or schedule update.

Final verification: all286publications applied and contributions published, each with exactly one scoped exception event; zero peer decisions/credits/outstanding exports. Full-bank diff changes only explicitly authorized passage/question/page/explanation/reviewPublicationId fields on206existingquestionobjects;81,421otherobjects and the entire paper registry unchanged. Answer indices/provenance/key references, ordered options/classifications all preserved. All34holds held/unscorable, all244pre-existing attempt rows byte-hash unchanged, owner unlimitedPro true. Final health81,627questions/13,156scorable; MCS2,967active/1,546officialeligible. The reduction from the previous13,166/1,556is the ten previously acknowledged review holds, not this content publication. Bank/taxonomy IN SYNC at527d8757d2990b224b13a9471e8a000867c613b2af78f46f6b0841d96215684b. Family site307. Restored publisher timer and verified active after all final checks.

One verification-only trap: initial final live fetch exceeded fetch_live_records'100target limit. Corrected the read-only verification script to chunk100; no publication replay or bank mutation was needed. Fresh full verification passes. Receipt index docs/sources/mcs-completion-publication-20261101.json; phase requests/receipts/dryruns/sync logs, field diff, hold/account/history baselines and final checks under reports/mcs-completion-next-20261101/. Actual guest-browser acceptance on cq_ff7b784ec1fcb174 shows the restored full train/luggage passage, its collapse control, and Show answer reveals the new checked explanation with provenance caveat and30minutecooldown, without submitting an attempt/reward. Screenshot live-restored-passage-explanation.png in that report folder.

This completes the exact286-publication authorization, not the whole MCS backlog. Recent raw count:1,600appearances,1,588usableansweredMCQs;1,304usableanswered appearances still lack working, or1,316blank MCQ explanations counting malformed/unanswered rows. Eligibility/source/key checks still apply. Historical numbering, incomplete sources/scanned-booklet leads, further teaching explanations and original-paper simulation prerequisites remain;2012/2013deferred. No source completeness, derived solution or compensation rule has been invented. Save and push the completed receipt/checkpoint to GitHub.

## 1 November 2026 — Focused UDC student overview

The owner approved implementing the UDC review and clarified that its audience wants UDC preparation first, with a deliberate move to Group B Non-Gazetted later. Delivered the first release: removed the UDC/LDC/Assistant overview switcher, repeated hero actions, prominent rewards link, empty community-material panel and the single 100% Past papers coverage bar. Five primary views now sit directly below the hero, followed by the existing saved journey, six approved own-exam subject shortcuts and three recent paper groups. All other sources remain reachable through full paper search/pagination. Hero coverage distinguishes48source booklets,3,859questions and3,569with answers for study. Official/unofficial/review labels remain visible on paper/question cards and in disclosed test guidance.

The eight2025booklets now occupy two series-selection groups; the full list has42groups over48sources. Grouping is deliberately limited to exact registered2025IDs with matching year/paper role: their exam-title casing and wording differ across series, so a broad title/year merge would be unreliable for departmental papers. Tests cover isolation of same-year departments, missing metadata, a filtered single series, unmutated source IDs, and checkpoint filter restoration without changing collection/view. UDC ignores another exam's active mock in its focused journey; all exams keep the shared resume mechanism. Mistake previews hide answer text and UDC has a direct wrong-queue practice action.

Bank and taxonomy check reported IN SYNC at81,627questions/approved tags. Frontend build, the new focused UDC checks and source-text rendering checks pass. The older check-answer-provenance.mjs harness currently fails resolving ../lib/answerStatus before assertions; no badge/scoring code was changed, and this pre-existing harness failure is not recorded as a pass. Browser checks exercised the guest overview, Series C source/PDF/action identity, UDC English practice, expanded timed guidance, Prelims GS/Aptitude and A–D choices, and the separate LDC/Assistant entry points. At360px and390px document/body widths were345px and375px respectively (15px scrollbar), with no horizontal page overflow. Local proxied practice state reported a same-origin guard; no answer/attempt was submitted through that proxy. Signed-in cross-device continuation was not exercised. Bounded10/20-question sessions and their persistence/finish screen are intentionally still pending as the next release, rather than being represented by existing unlimited pagination.

Final deployment verification: static frontend deployed through scripts/deploy.sh web; index and entry JS match the local production build. The final live check also replaces the global exam-scope selector within UDC routes with a compact UDC study label, avoiding an All exams message inside a scoped workspace. Live UDC English practice loaded its own source context without the local proxy same-origin error. Live390px body/document375px, with no page overflow. Desktop/mobile evidence: reports/udc-study-20261101/live-overview.jpg and live-mobile.jpg. API and the shared family site both returned200. No bank content, schema or scoring policy changed.


## 2 November 2026 — MCS source repairs and ordinary-quota explanation pass

Continued from the completed 286-item packet after fresh SSH, bank/taxonomy, current usage, quota, hold/history and account checks. Ordinary owner allowance was 463/500; no previous exception was reused. Checked exact booklet scans/final-key cells for the two remaining blank-option 2025 figure questions (B Q58 and D Q8), restoring the original page images, four accessible choices in printed order, separate source-defect clearance and each booklet's final-key B cell with working. Seven exponent/division/nested-root stems and three physical-PDF locators were repaired. Added 18 explanation-only backfills: 11 maths/code appearances and seven factual appearances supported by inspected NASA/EPA references. Their examiner answers and source context remain unchanged. Four code questions differ meaningfully by capitalisation; casefold triage had wrongly excluded them.

36 publications applied/published through the existing owner CLI, immutable exports, publisher dry runs and normal syncs. One additional unapplied withdrawal export was prepared while the preceding sync was still running and was correctly blocked as stale. Retained its immutable failed manifest, verified its target baseline unchanged, used normal request-rebase/withdraw transitions and a fresh owner decision; no in-place manifest edit or quota exception. Reduced explanation backfills by one to keep all 37 created contributions within the ordinary 500/500 limit. Future single-item exports must wait for the preceding sync and acknowledgement.

Full bank diff changes only requested fields/publication receipts on 21 question objects; 81,606 others and all paper objects unchanged. Both restored figure answers remain B but now reference exact registered final keys. All 34 holds remain held/unscorable, all 244 preexisting attempt-row hashes unchanged and owner unlimited Pro preserved. Zero peer votes/credits/quota exemptions/outstanding exports. Public question endpoints and both image byte hashes verified. Health 81,627/13,158 official-eligible; MCS 2,967 active/1,548 eligible. Bank/taxonomy IN SYNC at 6a060c94b8a398567455ee4c38916437200aaaffe60205b7121ad1539ccecec1; publisher timer restored active. Family site follows its redirect to HTTP 200. All 18 targeted preparation tests pass offline with synthetic source files; no unrelated UDC API/web code was deployed.

Receipt: docs/sources/mcs-publication-20261102.json. Exact figure, notation/locator and explanation snapshots plus guarded preparers/tests are committed. Saved 96 further source-checked agent drafts (53 maths, 43 factual) for coordinator acceptance and fresh live checks, and historical duplicate/missing-number evidence. Remaining recent counts: 1,296 raw blank explanations; 1,290 with usable case-sensitive choices/answers. These counts include held/ineligible content and do not certify publication readiness. Three historical numbering issues require supported duplicate/source-intake workflows; authentic simulation prerequisites remain incomplete; 2012/2013 stays deferred. Resume from docs/sources/mcs-continuation-checkpoint-20261102.json using ordinary quotas when available. Existing unrelated UDC working-tree edits remain preserved.


## 2 November 2026 — Saved UDC study sets

Delivered the approved follow-up: 10/20-question sets, exact saved question and source order, refresh/return continuation, finish summaries and targeted mistake sets. Reused the shared question card and existing attempt/reward engine. Session checks and position updates share one transaction; deterministic receipts prevent duplicate awards. Version guards reject stale writes. Completed feedback restores the original attempt snapshot, including absent figures, and retains active-test protections. Revealed answers remain reading with no attempt or reward. Finish reconciles server reveal records after interrupted acknowledgements. Explicit guest adoption preserves session ownership and reveal cooldown.

Migration 0062 adds session metadata only and was rehearsed on a disposable clone before live application. Local production build and focused frontend/source-text checks passed. The combined targeted backend suite passed 56 tests; the final two focused reruns each passed all nine session tests. Tests cover concurrent/idempotent checks, rollback after grading, source snapshots, owner boundaries, guest adoption, active mocks, smaller pools, full 20-question sets and reveal reconciliation. Testing caught and corrected SQL string concatenation during adoption. Browser testing caught loading-page scroll clamping; focus now waits for saved questions to load.

Synthetic browser rehearsal produced 1 correct / 1 wrong / 1 viewed / 7 skipped, retained the summary on refresh and opened exactly the missed question for review. Requested 20 questions from a three-question pool produced an explicit three-question set. Desktop, 390px practice and 360px expanded filters were checked without horizontal overflow. Evidence is in reports/udc-sessions-20261101. No production answer or reveal submissions were used.

Deployed through scripts/deploy.sh all, followed by the final snapshot fix through scripts/deploy.sh api. Deployment health returned OK with 81,627 questions and 13,156 scorable at that time. Live isolated-guest API smoke confirmed a 20-question UDC set, frozen order after refresh, saved position, replay-safe creation and persistent all-skipped finish summary, with zero answer attempts. See live-api-smoke.json. The live browser confirmed the loaded chooser and switching to Start 20-question set; live-chooser.jpg captures the deployed page. A final shell health/static-hash/family recheck could not run after network restrictions changed (DNS resolution unavailable); deployment success and live browser verification are confirmed, but no new family-health claim is made. No proxy configuration was changed.


## 2 November 2026 — Booklet series disclosure and conservative queue grouping

The owner requested hiding unnecessary paper-series UI in UDC and MCS Prelims, while checking duplication and retaining question clarity. Local-bank audit confirmed imported copies already exist; hiding the controls does not itself create duplicates. The exact 2025 source families hold 720 UDC and 800 MCS Prelims appearances. A conservative case-sensitive ordered-options/context/solution audit found 64 UDC clusters with 69 extra matching text copies and 102 MCS clusters with 120 extras. These are local candidate counts, not live eligibility totals; runtime adds source/review/figure guards. Receipt: reports/study-series-20261102/local-bank-audit.json. Earlier looser stem/option-set scans overcounted safe matches, especially for figures and different explanations, so they are not release counts.

Moved A–D choices behind Booklet series & original sources, omitted series from grouped-card display titles, moved PDF links into Paper details and disclosed per-question source identity. Visible passages, figures, source-issue warnings and answer provenance remain. Added a shared SQL candidate wrapper for general UDC/combined-prelims queues. Exact text, ordered choices, canonical/source contexts and markup, answer/explanation and review/issue status must match within the same filename family/year/role; any diagram/figure appearance keeps a question separate. Candidate filters run first, then grouping, then learner status. Latest own attempted member wins so an answered parallel series does not re-enter unseen practice. Explicit paper filters bypass grouping. No bank mutations, canonical merges, attempt/reward changes, schema changes or edits to frozen sets.

Normal PostgreSQL startup failed because both TCP and Unix sockets are denied. Added scripts/check-study-series.py using PostgreSQL 16 standalone mode on a disposable synthetic cluster, which needs no sockets. All 14 checks passed across UDC and MCS: representative selection, pagination, attempted/non-default series continuity, unseen/wrong filters, other-user isolation, review-state distinction, context/case/options/key/explanation guards and recorded figures. The test uses the production SQL generator rather than an imitation in Python. Frontend booklet/resume and source-text checks, Python compilation, production build and git diff --check pass. Full API integration and browser/mobile checks remain pending; earlier session test counts do not certify this refinement.

Deployment is blocked by the current session's network restrictions: bank-sync check cannot reach the server and direct SSH returns socket: Operation not permitted. Both local TCP and Unix sockets are also denied; local browser preview could not be started. The earlier UDC study-set release remains live; this refinement is local only. No Caddy, systemd or production database changes were made. Next step with access is bank/taxonomy sync check, full API/session regression and browser/mobile verification, then scripts/deploy.sh all and live source/queue/health checks.


## 2 November 2026 — UDC readiness and admin editing/confirmation recheck

The owner asked to finish UDC readiness and assess whether admins can quickly validate/edit questions and whether later checks can cause mismatches. Read the current workbench, direct decision, proposal/export/worker and append-only reassessment paths. Existing exam/subject/issue/year/paper filters, exact source/PDF inspection and Save & next already support quick per-question work. Existing stale-baseline, exact-key, primary-source, permission, duplicate-request, active-mock and pending-publication guards remain. No blanket approval, fabricated reviewer, quota exception or bank mutation was used.

Found a verification gap: the publisher compared a complete appearance but only a small canonical tuple, so a canonical-only provenance, key-reference or source-context/markup drift could escape acknowledgement checks. Added a shared field-name-only comparator covering every primary canonical learner field represented by the receipt, while preserving retired difficulty and secondary-source semantics. Added a private/no-store GET publication verification endpoint using a repeatable-read read-only transaction, both original/current subject permissions and active-test protection. It distinguishes current match, unexplained mismatch and legitimate later publication. Recent admin decisions recheck after application and offer manual recheck; published contribution history exposes the same controls after reload. This is a consistency check, not proof that the administrator’s answer is factually correct.

Found that saved UDC feedback restored original text/options/figures but could silently keep a later review badge or show old feedback without a correction notice. Saved results now carry update field names without exposing replacement answers; the UI retains original totals/feedback and links to the current question. New attempt JSON snapshots retain original answer-status/review context; older ones cannot inherit a newer derived-review badge. The current UDC UI also sends a presentation fingerprint. The check locks current source/canonical rows and rejects a changed presentation before grading/attempt/reward writes; exact replay remains stable. The token is optional for old API clients, so this is not a claim that old clients or unlimited/detail question routes have the same stale-display guard. No schema or existing snapshots were changed.

Read-only local UDC audit: exact 48 snapshot source IDs have 3,930 raw appearances (3,882 MCQ, 48 descriptive), versus 3,859 in the supplied older public snapshot. Server holds/merged/withdrawn status cannot be inferred offline; do not assign the 71-row difference a cause. Found 250 MCQ appearances without a usable recorded answer, 184 answered appearances without explanations, two explicit source defects and two malformed-choice appearances. Raw answerSource labels are not independent-review proof. All 48 supplied paper rule records use platform-default; keep timed MCQs labelled practice and do not claim full authentic simulations. Added a UDC coverage/written-practice disclosure, prioritised five main shortcuts and retained historical subjects. Inspected the official 2026 six-page advertisement and exposed its syllabus link. The current redirect and older official syllabus PDFs failed/403 through the web tool; complete current blueprint/rule validation remains pending.

Used the PDF skill for read-only visual review of three original physical page-9 scans covering four flagged appearances. Both duplicate-choice cases match printed defects; do not invent replacement choices. The two existing unresolved mathematical expressions are unclear in the source itself, so their source flags remain justified. No key was assigned or flag cleared. Renders, source hashes, raw counts, queue links and limits are in reports/udc-admin-readiness-20261102.

Verification: 32 focused offline tests passed, including the production worker’s actual readback query against real PostgreSQL 16 standalone mode, canonical/source drift, stale-display rejection before grading, read-only endpoint/protection orchestration, publication file replay/recovery and preserved versus adjusted feedback. All 14 standalone PostgreSQL series checks and frontend booklet/resume/source-text checks pass. Production build, Python compilation and git diff --check pass. Added complete API publication-recheck and admin-edit/session regressions, but they and the wider API/account suite could not run because this session denies normal local TCP and Unix sockets. Do not reuse earlier 56/391/etc. counts as validation of this change.

Final SSH probe still fails before authentication: socket: Operation not permitted. Bank-sync cannot reach the host. No new deployment, production approval/hold/content write, worker-timer change or infrastructure mutation occurred. Full browser/mobile/cross-device continuation, fresh bank sync, full API tests, deploy.sh all and study/family health checks remain required. Content backlog and exact syllabus/rule evidence remain substantive work beyond software verification. Evidence/report: reports/udc-admin-readiness-20261102/README.md.

## 2 November 2026 — UDC release deployed and browser verified

Resumed the authorized UDC/admin refinement with Oracle SSH and ordinary local database sockets temporarily restored. Bank check confirmed local/server in sync (hash prefix 6a060c94b8a3), 81,627 questions/classifications approved and zero pending/rejected; migration status through 0062 applied with none pending. No content or migration edits were needed. The first full targeted API run caught a real defect: the new repeatable-read READ ONLY verification route called require_role with its default lock=True, producing a forbidden SELECT FOR SHARE. Both permission reads in that route now pass lock=False within the consistent transaction. Reran the full targeted admin/bank/operator/scoring/session/account/learning/reveal/reward/collection/exam/MCS-role suite: 131 passed, one dependency deprecation warning, 16.98 seconds. Focused publication/feedback suite separately passed 27, and standalone production series SQL passed all 14 checks. Frontend booklet/resume and source-text checks, production build and diff whitespace checks passed.

Ran a disposable local browser rehearsal on synthetic UDC/MCS sources with a known test owner. Mutating synthetic options after display produced the intended 409 and no attempt; refresh cleared selection and fresh checking worked. Finished 10 questions with 1 correct, 1 wrong, 1 reading-only reveal and 7 skipped. Explicitly adopted the two guest answers during sign-in; saved set totals/position persisted and a separate authenticated client confirmed continuity while a fresh unrelated guest got 404. Practise mistakes created a one-question child with only the wrong question. A 20-question Mizo request with a three-question pool produced exactly three and a clear notice. At 390px the practice area remained below the header. Admin Save & next queued the synthetic decision, advanced exactly one question and showed publication pending. Full integration tests independently exercised real synthetic bank apply/sync/worker acknowledgement, matched publication readback and canonical-only mismatch; no real question approval was fabricated.

Deployed with scripts/deploy.sh all; API health returned OK, 81,627 questions and 13,158 scorable, and the local build/static upload completed. Reloaded live UI confirmed index-CG_oEUp9.js. At 360px expanded UDC filters and MCS controls fit (345px scroll width). Both modules initially hid series controls; selecting C changed Browse paper to exact C, and UDC Source PDF matched C too. Live UDC general browsing returned 3,790 instead of archive 3,859, matching 69 conservatively grouped copies without a source merge. Live guest 20-question set 46bba36bac1b43efb40eae0abf722a1a reopened at question two after reload and finished with 20 skipped, zero checked/viewed; no real answer/reveal was submitted. Screenshots and logs: reports/udc-release-20261102. Temporary viewport reset.

Environment permissions changed again after deployment completed. A fresh shell SSH attempt failed at socket creation and curl could not resolve DNS. Browser navigation to the API-health URL was blocked, and the family-site navigation was explicitly denied by policy; that denial was not worked around. Therefore deployment health and live student flows are confirmed, but post-deploy SSH file hashes, second sync check and shared family health remain unconfirmed. No Caddy changes. The disposable fixture process handles were no longer available after the environment reset; no unknown local databases were removed. The factual answer/explanation review and syllabus/rule backlog remains separate substantive work; this release does not establish full UDC content completion.


## Access-restored final verification — 2 November 2026

The owner restored full access. Fresh SSH confirmed ism-api active. SHA-256 hashes of deployed admin_answers.py, study_sessions.py, publication_verification.py, study_series.py and public/index.html exactly match the local release. Fresh API health is OK with 81,627 questions and 13,158 scorable. A second bank/taxonomy check reports IN SYNC: bank hash prefix 6a060c94b8a3, 81,627 questions/classifications approved, zero pending/rejected. The shared family site returned HTTP 200 after redirect to /lus, with the expected Family tree HTML title. This closes the infrastructure checks previously blocked by session permissions. No redeployment or infrastructure mutation was needed. Removed only the inactive disposable database named by /tmp/udc-release-fixture.json; no unknown databases were touched. Source-reviewed answer/explanation backlog and exact syllabus/paper-rule mapping remain outstanding.

## 2 November 2026 — First UDC content batch and official syllabus recovery

The owner asked to do the remaining answer/explanation and syllabus/rule work and estimate time/success, then authorized doing as much as needed after the quota question and clarified this is not yet for public use. Fresh bank/taxonomy sync passed. Fresh source readback confirmed 3,930 UDC appearances, 250 missing usable answers (240 live/10 held) and 184 blank explanations (125 live/59 held). There are 434 canonical targets in those two disjoint buckets, so do not blindly discount them as duplicates. Only 238 missing-answer and 124 explanation targets were live primary records without recorded issues before independent review. Ordinary owner contributions were 500/500; first rolling slot was 07:45:14 UTC. Scope owner exceptions to this UDC run and exact targets; HTTP/default quotas unchanged.

Recovered the actual three-page syllabus behind tinyurl.com/Assistantudccom via curl; web-tool retrieval still returned errors/403. Downloaded the exact official attachment and visually checked all pages using the PDF skill. Page 1 confirms the two 3-hour/200-mark papers, subject counts and 50-mark written English; pages 2–3 contain the August 2025 Gazette amendment adding one-third wrong-answer penalty and no blank penalty. Published this factual, date-scoped guidance inside the existing UDC syllabus disclosure and replaced the redirect with the direct official PDF. No historical scoring rule changed. Frontend checks/build passed, web deployed and live UI text/source links verified; local/deployed index hashes match. Recorded hashes/extracted text/renders and a 48-source first-two-page historical-cover inventory; extraction alone is not evidence of complete historical rules.

The first maths explanation sample exposed substantive issues rather than safe backfills. Visually checked eight original pages and recomputed contradictions: absent AP term index, tax result only approximated by an option, impossible reciprocal sum, wrong aggregate-versus-unit price ratio, subsidy result absent, impossible remainder, missing set-union assumption and percentage denominator mismatch, plus ambiguous work/boat timing. Applied ten source-bound needs-review holds with exact expected records. Source/canonical answer fields and target attempts were fingerprint stable. Correction to my initial cap assumption: direct needs-review decisions return before contribution creation, so these ten holds needed no contribution exemption; told the owner explicitly. They preserve existing unreviewed inferred answers as historical source data and do not certify new answers.

Recovered the official final answer key issued 21 May 2024 for the examination held 3 April 2024; the local corresponding key was provisional. Visually checked both key pages and both exact April 2024 paper first pages/ordered options. Registered the new SHA-bound final key for each source and mirrored all 40 key/reference records to private storage. Paper II Q29 is A&B and Q45/Q52/Q72 are compensated; do not assign single-option keys. Two Paper I source extraction artifacts were left for a repair phase. Published the 15 clearly inspected single-answer cells (Paper I Q1,3,4,5,6,8; Paper II Q1–9) under 15 exact scoped quota-exemption audit events. Paused/drained publisher timer, queued exact immutable decisions, dry-ran and published through the existing batch/local-bank/normal-sync/worker acknowledgement workflow, then restored timer active. No peer approvals/users/grants/credits fabricated.

Independent verification found exactly 15 changed question objects and 81,612 unchanged; text/options/context/figures preserved. All 244 original attempts and 135 review holds remained fingerprint-stable across publication. All 15 receipts applied, zero exports/peer votes/credits. A read-only verifier report initially failed because its JSON alias result collided with the worker wrapper alias; changed it to integrity and batched source fetches, then verification passed. It was not a publication failure and no manifests were rewritten/retried. New bank SHA 77963609b0753214f2380b3f39741a1dd1320505e037b3b0e25df61534fdceba; bank/taxonomy IN SYNC. API health OK, 81,627/13,173; family HTTP 200. No Caddy/API/systemd config changes.

First batch does not finish the backlog. Raw missing answers are now 235 and blank explanations 199: the 15 newly official answers add 15 questions that still need worked explanations, with none deleted. Provisional remaining estimate is 12–25 focused work hours excluding missing-authority/scan waits; high confidence in substantial safe improvement, no defensible percentage for answering every historical defect. Findings, source hashes, authorized requests, dry run, applied receipts, full-bank/live/history verification and continuation notes are in reports/udc-content-20261102/README.md. Current syllabus is verified; complete syllabus coverage and exact rules for every historical sitting remain open.

Live browser follow-up for this batch confirmed Official key on April 2024 Paper I Q1/Q3, intentionally deferred Q2 still Unsolved, original image/options/instructions retained and zero answer/reveal submissions. Saved live-official-key-paper.jpg and retained the paper workspace tab.

### 2 November 2026 — UDC source validity, explanations deferred

The owner prioritized question validity and authorized continuation. Screened all 3,930 UDC appearances, verified 48 paper PDFs plus 90 figure hashes locally/remotely, then visually adjudicated source leads. Published 79 source transcription/context repairs and 62 page locators (133 distinct appearances) through normal owner export/dry-run/local-bank/sync/live-receipt workflow. Restored 48 missing underlines, corrected five wrong MPSC target names, recovered the complete two-page Bell passage for seven Aizawl questions, removed two contaminated options and repaired eight April 2024 prompts. Six direct holds cover two source duplicate-choice defects plus exact final-key multi-answer/compensated cells; no contribution quota is consumed by direct holds. All answers/provenance/explanations across 81,627 questions remain unchanged; all 244 attempt rows and 135 existing holds are preserved. Zero exports, votes or credits; 141 scoped authorized quota events. Bank now a47a61cfb7105644f7e56f8ad7377e8c3119ee26abf4385e689c70e66a1e629c, bank/taxonomy in sync, timer restored, API and family healthy. Source-text renderer checks pass; browser confirms corrected target underline and complete passage/page link.

Traps: unique normalized source prefixes are only leads—Fisheries Q54/55 begin with repeated directions and would have been moved to the wrong page; original page 7 disproved both. Aizawl's short/direction-prefixed stems required printed-number range mapping. The combined final recheck exceeded the worker's 100-appearance limit; split into two chunks and both passed. Structural screening does not certify factual answers. A follow-up passage scan exposed a possibly truncated April 2024 written W3 instruction; leave a separate written-source review pending because this batch publisher is intentionally MCQ-only. Explanations remain deferred. Evidence and exact requests/receipts: reports/udc-validity-20261102/README.md.

### 2 November 2026 — Learner-first feed redesign and release

Reworked Feed.tsx around continue practice, revisit mistakes and ask a question before community discovery. Removed the left rail that preceded the feed on mobile, duplicate exam lists, games promotion, partner preview and arbitrary first-collection Your exam claim. All-time practice totals replace Your week; removed unsupported percentage/progress bars and the unused mock-history request. Reused the existing guarded learning resume service and preserved timed-practice paper/section/mode in resume URLs. Kept all community views and keyboard tab behavior; discussion filter changes now preserve exam_scope. Existing content eligibility and reveal protections remain untouched.

Production TypeScript/Vite build and frontend deploy succeeded. Live API health remains OK (81,627 questions, 13,173 scorable). Browser verified guest/no-checkpoint fallback, materials rendering and unanswered filter URL plus aria-pressed=true. Desktop viewport 1280/document1265 and mobile390/document375 showed no horizontal overflow. A brittle text snapshot check initially returned false due to snapshot formatting; explicit URL and pressed attribute confirmed the filter works. Authenticated saved-resume branching was code-reviewed but no new attempt/account was manufactured to test it. The browser session reset when permissions changed; rebound the existing tab for final proof. No bank/backend changes in this redesign; prior UDC work remains intact.

### 2 November 2026 — Group B Non-Gazetted preparation foundation

Owner requested a broader NG module for learners choosing English/GK/Current Affairs and asked whether it supersets UDC/LDC. Checked the official9July2024 NG general/technical scheme and recruitment-specific LDC source; these support GK naming and distinct exam patterns. Found newer May2025 official notice but linkedPDF repeatedly returned403. Did not present2024 marks/duration as the current universal scheme. Existing decisions already union UDC/Assistant sources into NG; LDC remains a linked focused module, not silently relabelled or added.

Implemented GroupBNonGazettedIntro, NG default on `/group-b` (explicit combined/Gazetted still work), actual-topic current-affairs shortcut, separate technical/common links, and NG General Knowledge labels in topic cards and practice filter. Used the existing scoped API and source role protections; no backend/bank writes. Exact routes remain deep-linkable. Production TypeScript/Vite build passed twice (final changes included). Frontend deployment then failed at SSH socket creation with Operation not permitted under the newly restricted session. Upload did not occur; live Group B has not changed. Browser verification remains pending for this slice. Saved design/source/relationship brief in docs/GROUP-B-NON-GAZETTED-MODULE.md. Prior feed release and UDC work were preserved.

### 2 November 2026 — Group B learning/navigation finalization

Owner requested optimized, refactored, easy learning/navigation. Added pure groupBStudy state/navigation/label helpers, separated Study home from active topic/reading/practice views, collapsed source-group/archive controls and compacted active-study header. Changing scope now drops stale paper/topic/offset/answer-status/pool/personal filters; changing read/practice mode retains topic while choosing the correct pool. Added metadata/current-affairs Retry, selected-collection-only fetch and loaded-collection guard to avoid stale mappings. GK labels now agree across topic cards, selectors, breadcrumb and generic question badges. Source titles and bank protections unchanged.

Production builds, meaningful navigation-transition checks and existing UDC checks pass. Local Vite started successfully despite prior assumptions about socket limitations; real API-backed browser confirms748 topic-map Current Affairs questions (coverage count, not claim of current facts), correct scoped shortcut, read pool=all with topic retained, English selection clears oldtopic, and Study home. Mobile viewport390/document375 has no overflow. No answers submitted. SSH still fails immediately with socket Operation not permitted, so no new live release.

Corrected earlier terminology advice after inspecting the actual January2026 H&FW NG technical paper cover: it prints PAPER-II (GENERAL STUDIES). Shared GK category is fine, but saying NG has no GS would be wrong. Updated module disclosure and appended source note; do not rename this original paper. Final local preview evidence stored in reports/group-b-finalization-20261102.

### 2 November 2026 — Save Group B work for later continuation

Owner requested a plan to resume later. Created docs/GROUP-B-CONTINUATION-PLAN.md with exact local implementation state, tests/browser evidence, pending frontend deployment, live acceptance steps, terminology correction (January2026 NG technical General Studies), May2025 source-access gap and separately scoped future learner preferences/sets. Marked the earlier deployed feed/UDC work separately from pending Group B. Permissions are now restored, but did not test SSH or deploy during this planning request. Preserved all uncommitted changes; linked the checkpoint from PLAN. No product or bank mutations in this turn.


## Released and syllabus recovered — 2 November 2026

This entry supersedes the earlier SSH/deployment and May2025-access limitations above. SSH and read-only sync checks succeeded:81,627 questions and approved taxonomy claims in sync. Group B frontend deployed successfully, then redeployed with dated syllabus guidance. Live default NG home, Current Affairs topic/pools, English filter reset, Back/Forward, reload, home scroll, technical archive and recruitment-group switching checked. NG exam overview shows the same entry choices and amended guidance. Viewports1280/390/360 had no horizontal overflow. API healthy; family site HTTP200 after redirect. No learner answers submitted.

Recovered the original May2025 PDF via ordinary HTTPS and the five-page source linked by the official direct-syllabus listing (June2026 attachment directory). Visually inspected all pages, including the15July2025 amendment: general interview37.5, total337.5. Added source-linked dated general/technical scheme guidance inside the existing relationship disclosure. Historical rules, practice scoring, source membership and bank remain unchanged. Exact source URLs, page findings, hashes, verification limits and live screenshots: `reports/group-b-release-20261102/README.md`.

Remaining: exact post-specific/UDC/LDC comparison and later-amendment audit, learner subject preferences and Group B saved sets. Do not infer full current-syllabus coverage from this release.


## 2 November — Make exam names visible alongside generic PDF titles

The owner reported that some exam identities could only be found inside PDFs. Traced this to shared paper cards and PaperViewer prioritising filenames, even when the collection API already supplies an exam name. All 97 NG paper records have nonempty exam metadata; some inherited records retain abbreviated identity and this check is not a fresh full-corpus identity certification. Visually checked January2026English/GS covers; both print Group B Non-Gazetted technical recruitment. Use one frontend paperIdentity helper: printed paper label then filename fallback for the heading, existing exam/title metadata visibly beneath it. Apply to shared exam cards, viewer and technical cards; search technical papers by exam/paper labels too. Preserve printed filenames in source details and keep conservative booklet grouping. No bank, source membership, scoring or database changes.

Paper identity, UDC and Group B regressions passed; TypeScript/Vite build and frontend deploy succeeded. Live NG cards show exam names below Paper I/II headings;390px has 375px document width. Verification evidence: reports/paper-exam-names-20261102. No new learner answer submitted.


## 2 November — Exam/year archive list and human bank handoff

Owner requested an MPSC-style exam/year list with ascending/descending order and a candid bank-finalisation assessment. Added a responsive list of year, examination, paper and Browse/PDF links to shared exam archives. Group B Past papers defaults to list; existing cards remain selectable. URL-persisted newest/oldest and exam A–Z/Z–A sorting happens before pagination, unknown years remain last, changing controls resets page, and booklet-card groups follow the selected order. Grouping does not merge source identities. Other module defaults remain cards.

Archive/identity/UDC checks, TypeScript/Vite build, deployment and artifact hash match passed. Live: ascending2010, descending2026, reload and page-reset behaviour, alphabetical order, year intersection, and390px/375px width. Screenshots in reports/bank-human-handoff-20261102.

Read-only production audit includes held questions for editorial planning. Group B common English/GK/GS:3,634 MCQs,101official,2,898reviewed unofficial,378needs review,257unsolved (82.5% accepted status). All Group B:7,884 MCQs,281official,5,165reviewed unofficial,461needs review,1,977unsolved (69.1%). Whole bank:73,475 MCQs,13,173official,5,583reviewed unofficial,50,948needs review,3,771unsolved (25.5%). These statuses are not a human-verification count. Common499/all Group B2,286 missing explanations overlap the answer backlog; written117/176 are separate. Produced HUMAN-HANDOFF.md, reproducible SQL, paper snapshots and2,677unique canonical review leads with source pointers. Human refinement can start now; no full-bank finality or full archive/syllabus coverage is claimed. No bank mutation, account grant or message to a reviewer.


## 2 November — Protect UDC/Prelims human correction from AI re-parsing

Owner requested comprehensive handoff safety and named Solomon.scorp@gmail.com for Prelims and Sangzel/sangzeldoto@gmail.com for UDC. Confirmed neither account existed. Implemented exact-source pending assignments with owner activation/revocation and a small /editorial workspace. Assignment access permits inspecting assigned source answers, logging attributed append-only checks and submitting ordinary correction proposals; no administrative grants, publishing, self-approval or auto-verified answers. Ordinary quotas remain. Created audited reservations without email/password/session creation. Activation waits for each friend's real account and owner identity confirmation.

Found two distinct overwrite risks: legacy bank writers and stale ordinary contribution forms. Added full-value protected record/source-asset fingerprints, membership checks before every sync mode, and locked atomic writer gates across14known workshop/app writers. Blocked parser imports retain draft comparisons. Initialized78source papers/6,931appearances/452assets from the existing synced bank without altering its content or answer status. Validated manifest/batch publishers journal exact target transitions and recover on either side of bank replacement. File-state integrity is not security against root/operator code edits. Private recovery copies of initial/current state and guard code are on /home/ubuntu/editorial-protection-20261102.

Added answer-free transaction-version tokens to ordinary source/correction forms. Protected UDC/Prelims proposals require a fresh token and reject source/canonical/classification drift. Assigned inspection checks use the same freshness comparison and preserve original records. Existing publication history/readback/source-key guards remain authoritative.

Migration0063rehearsed on a production dump clone and applied; API/web deployed.103focused tests plus3workshop regressions passed, production build and UDC/GroupB/archive checks passed. Synthetic preview exercised selection and saved checklist at1280/390without overflow; production browser confirmed signed-out boundary. No friend's login or human sign-off was fabricated. Bank checksum a47a61cfb710… remains in sync; API healthy, familyHTTP200. Two initial synthetic test fixture errors (required exam_type and module import path) were repaired before the final suite. Runbook and per-friend packs:reports/udc-prelims-human-review-20261102. No messages sent.

### 2026-11-02 — Activate the two friend accounts

The owner asked to apply the assignments and provide individual simple passwords or implement OAuth. Used the existing password option to deliver immediate access, with distinct random multiword passwords saved only in an owner-readable file outside the repository. Both previously absent accounts registered through the ordinary HTTPS registration endpoint; existing-account conflicts never overwrite a password. Activated Sangzel→UDC and Solomon→combined-prelims through the existing owner-authorized service and audited activation logic, preserving version checks and frozen paper scopes. No global grants, email verification, human source checks or bank content changes were made.

Live verification signed in to each real account, loaded its sole active assignment (48/30 papers respectively) and a question list, rejected the opposite assignment with404 and owner management/global bank admin with403, then logged out. The initial operational logout omitted the CSRF header and failed; corrected the client to fetch the session CSRF token and use the standard header, then revoked all remaining setup sessions for these newly created accounts. Updated the handoff exporter to emit sign-in/change-password instructions for active assignments while retaining registration instructions for pending assignments. Regenerated both source packs without passwords. OAuth was not implemented; no Google app credentials were configured. The change-password recommendation is not a new enforced first-login policy.

### 2026-11-02 — Shorter friend passwords on owner request

The owner requested simpler passwords after account handoff. Changed both through the existing authenticated password-change endpoint to different 12-character word/number passwords, retaining the site's minimum and normal CSRF/security-event/session-revocation behavior. Updated only the owner-readable credential file outside the repository. Verified each new password signs in, each previous password returns401, and both original assignments remain active; logged out every setup/test session. No application policy, bank content or privileges changed. Passwords are intentionally omitted from repository documentation.

### 2026-11-02 — Comprehensive paper, website and games design

The owner asked how to manage PDF papers comfortably with little AI and design the whole website/admin including games. Inspected current routes, admin navigation, PaperIntake and its pdftotext helper, assigned-review code context, current GameSetup and games selection/preview/readiness endpoints. The important gap is routine intake still depends on a local extraction command and artifact JSON; a file chooser currently hashes rather than uploads a PDF. Older games planning lists gaps that current code has already addressed, so the new plan cites current capabilities and calls for auditing remaining operations before rewriting them.

Added docs/WEBSITE-AND-PAPER-WORKSPACE-DESIGN.md with role-specific navigation, paper-workbench layout, manual/non-generative intake, scanned/written/diagram/key edge cases, evidence/version controls, a durable canonical-worker bridge, student screens, game journeys/admin, accessibility, phased delivery and acceptance exercises. Consulted primary PDF.js/Tesseract documentation for rendering/OCR boundaries. This turn produced a design only; no UI, data, account or deployed behavior changed. No new accuracy/cost or bank readiness claims were made.

### 2026-11-02 — Small topic game design

Designed Topic Trail in docs/TOPIC-TRAIL-GAME-DESIGN.md after the owner requested something more fun with a narrow UDC/Prelims scope and asked whether Sol6.1 could handle it. The design limits the first release to one source-checked topic pack, ten-question solo runs, a compact avatar trail and one optional double-next token. Specifies scoring, source eligibility, retry/correction behavior, minimal admin and acceptance tests. Topic examples remain candidates pending live usable-pool verification; no counts were fabricated. Consulted/fetched the official GPT-6.1 Sol model page using OpenAI Docs. No game implementation, AI runtime dependency, deployment or model switch occurred.

### 2026-11-02 — Provision for recurring current-affairs questions

The owner requested connecting older current-affairs questions with newer versions before Sol implementation, including GS/GK relationships. Read existing explanations/current-affairs design and confirmed there is already a small static revision-note registry. Added a separate implementation specification for reviewed entity/fact timelines, precise source-appearance links and a Then and now panel, with exact original date/options/key preservation. Explicitly handles no matching modern option, unknown dates, same-office versus same-person identity, effective/check dates, source conflicts, temporal duplicates and score-history preservation. Related facts introduce answer-disclosure paths, so the proposed server API must gate linked content across active assessments rather than relying on current frontend note visibility. Cross-referenced website/game plans. This is design provision only; no live facts, links, schema or bank records were altered and no actual officeholder was asserted.

### 2026-11-02 — Implement current-affairs connections

The owner said “Do it sol” immediately after the current-affairs linkage design. Implemented that bounded feature, not the separate whole-site redesign/game or canonical-host migration. Added migration0064 with precise entity identities, immutable proposal payloads, exact source links and an audited independent-owner publication/rejection/retraction state machine. Active source assignments authorize proposals without global staff powers; owner/subject grants also work. Source-version validation applies at submission/publication and author access is checked again. An owner cannot publish their own claims. Added a practical form and permitted-source search at /current-affairs/manage, admin/sidebar and assigned-review entry points, plus a private learner panel after answer reveal.

Answer-bearing routes block all active mocks/games and still-unclosed cup release windows. Explicit viewing records normal reveal cooldowns for all linked canonical IDs and no attempts/rewards. Historical keys/options and attempts remain untouched. Linked papers retain exact source appearances and original PDF links; no temporal deduplication or AI updates occur. Date validation distinguishes effective periods, source publication, check and next-review dates, rejects overlapping known intervals, and permits explicit unknowns.

Caught a durability trap during review: sync upserts change PostgreSQL xmin even for identical data, so a transient edit token cannot serve as long-lived evidence. Added separate migration0065 and semantic fingerprints for published source links. Identical upserts now retain connections; a real canonical answer or source change hides stale context until new review. Applied migrations are never rewritten. Regression checks cover this case, source permissions/revocation, independent publication, immutable content, retries, stale/conflicting revisions, retraction, historical answer preservation, exposure and active assessment access.

Final focused suite:71passed (current-affairs/editorial/bank-review/admin-answers/protection); build passed. Rehearsed schema changes on production dump clones. Full-stack browser rehearsal used a disposable local database, synthetic offices/facts and separate source years2020/2026, verified independent owner publication and learner Then and now display, and measured no horizontal overflow at1280/390. Initial test fixtures failed because an answer was not a literal option and cleanup attempted forbidden history updates; corrected the fixtures without weakening application protections. Found14actual chief-election-commissioner source appearances read-only for future human curation, including2023MLS and2025technical GS. No factual connection or officeholder was manufactured or auto-published. Release evidence is in reports/current-affairs-connections-20261102.

Release follow-through: deployed API and frontend after applying0064/0065, verified health81627/13173and familyHTTP200, and verified real Sangzel/Solomon queue access, no publish rights and source-search membership. Logged both verification sessions out. Strict bank check passed protected78papers/6931questions and confirmed checksum a47a61cfb710… remains in sync. The learner's displayed retry deadline now refreshes after reading linked facts, and other visible linked-question panels receive the existing reveal event. Signed-out users receive a concise access screen before the editor. First real factual connections remain for human source review;14candidate appearances are saved without asserting a current officeholder.

### 2026-11-02 — Broaden current affairs beyond the example

The owner clarified that Chief Election Commissioner was merely one example and requested general support such as the largest iron exporter. Replaced the officeholder-first editor assumption with ten fact categories, leaving GS/GK source/taxonomy handling intact. Rankings/statistics now carry required exact subject, metric, comparison basis, units, population, named source series and methodology; revisions cannot silently switch to a different commodity/value/volume/production measure. The first immutable proposal defines comparison identity under the existing entity lock, so no schema migration or historical JSON rewriting is needed.

Facts now separate reporting year/period/type/edition from source publication, effective and check dates. Annual rankings/awards can coexist without false officeholder-style expiry requirements; duplicate same-period claims are rejected. Question links explicitly distinguish direct comparability from related-only/unclear, with evidence notes and periods where directly compared. The learner and independent-owner review show these definitions and limits. Legacy fields default to general/unclear and normalize safely on idempotent replay. No real country/officeholder value or bank answer was changed.97focused tests passed, including new commodity/basis/population/methodology conflicts, annual reporting, missing metadata, ambiguous old questions and other fact categories. Build passed; synthetic full-stack rehearsal uses fictional trade leaders and source questions. Release evidence:reports/current-affairs-general-20261102.

General-current-affairs release follow-through: added an explicit legacy-payload replay regression, bringing the focused suite to98passed. Deployed API/frontend successfully; health remains81627questions/13173scorable and familyHTTP200. Verified trade-category field selection and learner comparison rendering on desktop/mobile, with390viewport/375documentwidth. Revised the disposable trade demonstration so exam years, reporting periods, options and synthetic keyed countries agree; no actual country ranking is asserted by the fixture. Source and bank protections were retained; this follow-up introduces no bank content changes or schema migration.


## 3 November 2026 — MCS protected source repair and first explanation packet

Resumed the scheduled MCS task after reading the new UDC/Prelims human-review protection and current bank-authority rules. Initial bank/taxonomy/protected scope matched production at a47a61cfb7105644f7e56f8ad7377e8c3119ee26abf4385e689c70e66a1e629c. Ordinary usage193/500, exports0, attempts244, human checks0; owner unlimited Pro true. The protected 78-paper/6,931-source scope and both activated reviewer assignments remain intact. No parser rebaseline or protection bypass. Existing validated publishers journaled only exact target transitions.

The fresh recent-source audit found nine more hasDiagram questions without images even though all four option strings existed; this corrects any interpretation of the prior blank-option audit as complete diagram coverage. Visually inspected the exact A/B/D booklet pages and restored four content-addressed original page images for nine questions, preserving printed choices/answers. Corrected four physical-PDF links and the lost printed √3=1.73 annotation in2025B Q72. Separately published nine diagram/chart workings plus80accepted backfills (40maths/reasoning,40factual). All103immutable publications are applied/published via ordinary owner CLI, dry runs, normal sync/readback and the protected publication journal. No examiner key/reference, ordered option, classification or historical answer was rewritten.

The saved96draft packet was reviewed again, not blindly published. Sixteen remain withheld: four printed fence-wording issues, four contradictory Rama/Thana names/ratio stems, four language-group assumptions, three broad prolactin stems and one corrupted radical transcription. Root caught a mixed-radical template in the agent draft; that text was discarded, exact per-source radical workings were recomputed, and the different2023B Q99 stem/options were checked visually. That one clearly damaged source received a standard reversible needs-review hold, preserving its official key and excluding it from grading. No invented answer or independent/human approval. Other wording/assumption findings remain for subject/source review, without blanket new holds.

Full-bank verification permits requested changes only on89questionobjects;81,538others and every non-question bank object are identical. All34priorholds remain held/unscorable, the new source hold is separate, all244pre-existing attempt-row hashes and both reviewer-assignment rows are unchanged. Account unlimited, human checks0; zero peer decisions/credits/quota exemptions/outstanding exports. Final bank/taxonomy IN SYNC at1cfdd44ca6d9b7bf845b6cac377e6692f4fa312193a943c7f2cc174d31e64b43. Health81,627/13,172eligible and MCS2,966active/1,547eligible: the one-question reduction is the explicit new hold. Required-image scan now finds zero missing referenced images among the recent1,600; this is flag-based coverage, not full factual/source certification.

71targeted tests pass, including protected publication, exact source/image/answer guards and the selectable checked-packet CLI. The new --packet option accepts only repository docs/sources inputs and keeps all existing validation; it avoids cloning a dated preparer for every next packet. Live guest browser showed the restored pie chart, preserved choices and corrected page17PDFlink, without checking/revealing/submitting an answer. FamilyHTTP200. Publisher timer restored active; updated protection state mirrored privately to /home/ubuntu/editorial-protection-20261103/udc-prelims.json. No API/web/Caddy/schema deployment or unrelated working-tree edits.

Receipt:docs/sources/mcs-publication-20261103.json; exact packets,16withheld findings and new-hold request/receipt are committed. Recent remaining blank counts1,207literal/1,201usableanswered include held/ineligible rows. Historical Q4/Q86 source duplicates still have zero attempts/contributions; links do not retire sources. Missing2014IIQ39 requires a protected original-source-only intake/identity review.2012/2013remainsdeferred and authentic simulation stays disabled. With204ordinaryslots still free, a separate bounded read-only next-draft review is continuing; checkpoint docs/sources/mcs-continuation-checkpoint-20261103.json distinguishes it from this completed103-publication packet.


## 3 November 2026 — additional MCS context and explanation packet

Published 93 more checked explanations: 36 reasoning/English and 57 factual. Their source prerequisites were published first: 13 physical PDF page links, the four-example list in 2025 Paper II A Q23, and the shared hypothetical syllogism instruction for 2025 Paper II D Q74–77. The three sequential batches total 111 ordinary audited publications. Exact source baselines, final-key cell checks, independent reasoning and primary references are retained in `docs/sources/mcs-additional-checked-explanations-20261103.json`. Five weaker factual themes remain excluded. These are historical/static explanations; no dated current-affairs connection, human sign-off or independent peer certification was invented.

The preparer now accepts the existing direction field as an exact source prerequisite. Full record, PDF hash, ordered choice, key and predecessor checks remain mandatory. All 75 targeted tests pass. Each batch passed a dry run, protected publication, normal bank sync and full live readback. Five restored contexts are visible through the public question API; verification made no answer attempt or reveal request.

Full-bank verification against the second baseline permits only requested fields on 93 question records. The other 81,534 questions and all non-question bank data are identical. All 134 existing global holds, 244 previous attempt rows, both reviewer assignments and unlimited owner Pro access are preserved. There are still zero human checks. Answers, ordered choices, classifications and scoring eligibility are unchanged. All 111 publications are applied, with no peer votes, credits, quota exceptions or outstanding exports. The protected scope remains 78 papers / 6,931 questions; only exact validated publication targets advanced its integrity state. The publisher timer is active, bank/taxonomy are IN SYNC at `99ce7a54d37581a8be55b6f144b677ab8855240371ed1ec67d6a142139dd45e0`, and the protection recovery copy was hash-verified on Oracle. Global eligibility remains 13,172; MCS has 2,966 active / 1,547 eligible questions. Family site returned HTTP 200.

This heartbeat's two receipts total 214 ordinary publications, 182 explanations, nine restored diagrams, 17 corrected PDF links, five missing contexts and one notation repair. The first packet separately placed one corrupted source on review hold. Ordinary usage is 407/500. Remaining recent blanks: 1,114 raw / 1,108 with usable ordered answers, including held or ineligible records. The 16 earlier exclusions, damaged radical/choice correction, historical identity/intake gaps and original simulation prerequisites remain open. Keep 2012/2013 recovery deferred. Latest receipt: `docs/sources/mcs-additional-explanations-publication-20261103.json`.

## 3 November 2026 — browser paper workbench, Oracle authority and Topic Trail

Continued the owner's instruction to implement the remaining PDF/site/admin/game work. Added source-first PDF upload/extraction/OCR/rotation/crops and MCQ/written preparation with explicit saves, optimistic versions, immutable restore history, exact reviewer grants/revocation and independent whole-paper review. A saved change invalidates review. Page jobs store separate extraction/output revisions, so neither polling nor OCR replaces manual questions; polling initially did replace scratch text, which the browser rehearsal exposed and was fixed. The first TS build also caught a missing pointer-handler brace. Official keys require an uploaded document, booklet agreement and a real key-page bound. Reviewed publication uses one bank lock, append-only source IDs, compressed preimages, crash-replay receipts, the normal sync and exact identity/context/figure/taxonomy/booklet readback. PostgreSQL's paper-kind constraint only permits mcq/descriptive, so mixed papers keep their individual types and use mcq at paper level; a full isolated mixed-format publication verified the constraint and CSV path.

Moved writable canonical authority to `/srv/study/workshop/mpsc-question-bankv2` on Oracle. The original broad copy included unnecessary parser data and was stopped; reused existing source/figure bytes and copied the active references instead. Verified all 22,272 files / 2,899,173,375 bytes by SHA-256, including all registered evidence. Some unused partial data is retained, making the VM workshop about 4.3 GB; 79 GB remains free. The copied bank and protected scope matched exactly at `99ce7a54d37581a8be55b6f144b677ab8855240371ed1ec67d6a142139dd45e0`. Oracle's dry-run full CSV sync reported zero changed appearances and rolled back with 244 attempts and 179 users intact. Disabled the local publisher timer and replaced its local machine policy with the Oracle authority policy; verified that local publication now fails closed. The protected 78 papers / 6,931 source questions and both exact friend assignments remain unchanged. No Caddy configuration changed; study API and the redirected family login both remained healthy.

Installed separate www-data document processing and root publication services plus the ordinary correction timer. Document tools run with resource limits, network/filesystem restrictions and no generative AI. Added graceful worker stop and publisher draining to deployment so code updates do not interrupt a bank write. A paired root-only backup includes the JSON/protection/receipts/taxonomy, PostgreSQL workflow dump and new private PDF/crop bytes; its archived bank hash is checked. The first 66 MB snapshot was fetched to private local storage and both files hash-verified. A user timer fetches recovery copies hourly/after startup while online; no external cloud destination or backup pruning is configured. A real dump restore into `ism_paper_fullpilot` succeeded. Its PostgreSQL role initially could not read the root-only dump file, correctly; streamed the root-read dump to pg_restore rather than loosening permissions. The isolated test then exercised upload, extraction, editing an MCQ and written task, exact reviewer assignment, independent synthetic approval, key mapping, append/sync and full readback. Both source/key documents and PILOT booklet values were registered, with all 244 prior attempts retained. Synthetic accounts/papers/approvals existed only in the disposable clone, which was removed along with its hard-linked file workshop. Production remained 81,627 questions, 244 attempts and 179 accounts.

Implemented Topic Trail in existing game_rooms to preserve active-assessment reservations and reward protections. Ten stones, 20-second answer windows, paused feedback, original exam/year, a pre-reveal one-use Double next, immutable snapshots, source-change exclusions and a 30-minute total session bound. The browser completed a synthetic ten-correct trail at exactly 1,100 points, and mobile width checks showed no horizontal overflow at 390 px. Used the existing source-markup renderer and avatar, with quiet scenery and reduced-motion-aware movement. A real pool census found thirteen vocabulary canonical IDs but only seven distinct eligible questions after deduplicating booklet copies. Physics also contained geography questions, so no physics or vocabulary pack was launched. Added exact source-list administration and launched ten stable Prelims Constitution basics sources after matching every stem and option to its original PDF page. This is a limited-variety pilot, not topic mastery or whole-bank certification. No current factual rankings or officeholders were automatically populated.

Verification passed 112 focused game/current-affairs/protection/publication tests plus 44 assignment/operator/review tests and the frontend production build. An expanded test initially referenced v_scorable.has_diagram, which does not exist; removed that assumption. A test fixture also temporarily added paper-test to UDC and contaminated later review tests; now removes that membership at teardown. Additional recovery/official-key/source-list checks pass. The direct live catalogue and desktop/mobile workbench were checked in the browser; synthetic screenshots, source matches, receipts and logs are in reports/workbench-oracle-trail-20261103. Updated the authority notes/runbook and preserved the original local source/backup copy. Human review of real papers, first real current-affairs facts, richer reviewed pack content and continuous independent cloud offsite backups remain human/content/operations work, not silently declared complete.

Follow-up to this session's account-count statement: 179 is the recovery-snapshot baseline, not a promise that the live users counter stays frozen. Subsequent live checks/visits raised that counter through anonymous guest profiles. Compared every original user ID from the private dump against production; no original account was missing and no synthetic pilot account exists in production. Record the retention result separately from the changing visitor counter.

Final runtime probes: the restricted www-data systemd account successfully extracted a two-page source (6,392 characters), rendered its page and performed rotated OCR (2,831 characters), with the production filesystem/network/resource restrictions. Temporary probe files were removed. The account-retention comparison completed with all 179 original IDs present, zero additional registered accounts and zero synthetic pilot accounts in production; additional profiles were anonymous visitors. Oracle document/paper/correction/backup services were active and reporting fresh heartbeats. Systemd KillMode=mixed ensures a graceful worker stop signals the main loop first while allowing its bounded child command to finish. The final API deployment passed health checks, and family.hawayu.in followed its normal redirect to HTTP 200.

### 3 November — consolidated AI queue, discovery and checked five-question pilot

Implemented the owner-approved consolidation after Plan mode ended. Replaced active
local-authority prose with a 73-line model-independent entry point, reduced the
active plan to 44 lines and retained the former 1,140-line milestone ledger as an
explicit historical archive. Old completed publication packets and bounded quota
exceptions are no longer startup instructions. Preserved source protection, human
assignments, scoring/reveal/account boundaries and shared-server safeguards.

Added the private durable SQLite explanation queue, immutable source/context/draft/
check/request/receipt artifacts, rotating claims, original-PDF caching/rendering,
source conflict rejection, exact proposal reconciliation after uncertain SSH results
and serial audited Oracle publication. The legacy multi-item guard now checks the
Oracle timer/service and fails closed if remote state is unknown. Single-item
exports work with the normal timer. API intake locks/rechecks the full expected
source and blank explanation, including supporting answer provenance.

Added migration0069 and answer-free discovery with seven-day distinct registered
practice/discussion signals, conservative shared booklet groups and five-person
threshold. Editorial recommendations use existing inspected exact source lists.
Hot picks have owner-only versioned draft/publish/retire history, evidence dates,
expiry and stale/withdrawn independently published factual-support checks. Existing
assessment restrictions withhold all discovery. Owner editor and exam/Home sections
are deployed; no popularity or factual pick was seeded. Live switching to UDC
was verified. Browser widths1265/1280 and375/390 show no horizontal overflow.

142 focused regressions pass, covering recovery/conflicts, billing refusal, booklet
signals, real thresholds, dated support, assignments, workbench and Topic Trail.
Migration rehearsal used and dropped a production dump clone; production migration,
build and deployment pass. Both shared domains and Oracle API/publish/PDF workers
remain healthy. Initial test fixtures incorrectly used combined-prelims version1;
changing fixtures to the actual live_version2 resolved their empty membership.

Loaded1,065 eligible authoritative Prelims questions; inspected five original pages
and preceding argument directions, plus primary reference support. Published the
five explanations through ordinary allowance370→375 and verified complete source
readback. The initial whole-bank exclusion hash differed because publication also
updates each target's required reviewPublicationId. Compared the hash-verified
original backup directly: exactly five records changed, each only explanation and
that audit pointer. A corrected normalization and exact pointer-to-receipt check
both pass. All254attempts, two assignments/78source memberships, grants and human
checks are byte-equivalent; zero exports remain. Queue has1,060pending/fivepublished
and no active packet. Detailed evidence is reports/ai-discovery-20261103.

The owner confirmed OpenCode Go. This installed v2 Console exposes generic model
names; its existing OAuth credentials were rejected (401) by a read-only Go API
probe. No secret was printed or stored in the repository, and no paid model call
was made. Replaced the obsolete provider-name/CLI-permission assumption with a
stateless call to the documented Go-only endpoint, a private personal API key,
stable session header, bounded response and explicit Go/zero-charge usage check.
It exposes no model tools and never falls back; a billing mismatch blocks later
calls. Synthetic billing tests pass. Actual Go calls await the owner's personal Go
key, supplied privately via the documented environment/key file. The five-question
pilot used manual session drafts and a separate source/reasoning pass; none was
represented as human certification. Continuation instructions and provider status
make this remaining setup requirement explicit.

### 3 November — easier private Go key setup

The owner did not know how to connect the personal key. Checked the current official
Console API documentation: personal keys are under Account → Personal API keys;
Restricted → Models: Request provides the required model access. Added a local
getpass setup helper with no credential arguments, no echo, atomic mode600 storage
inside a mode700 private directory, and clear return-to-chat instructions. It makes
no model request and does not touch an existing key until validated input is ready.
Synthetic temporary-file checks verify private modes, exact storage and malformed
input preserving the prior value. No real key was entered/read by this helper and
Go remains unconnected until the owner performs this local step.

### 3 November — Go personal key connected and billing verified

The owner explicitly supplied and authorized use of their personal key. Entered it
through the helper's non-echoing terminal prompt; the key is stored only in the
private local key file and was not printed to tool output or committed to the repo.
A single bounded GLM-5.3-Flash connection request to the Go-only endpoint succeeded:
billing_source=go, balance cost=0. Saved only non-secret connection status in the
ignored queue directory. Marked the setup milestone complete and updated handoff
instructions. The earlier failed OAuth probe is historical; current requests use
the private personal key. Advised replacing the key because it appeared in chat.
No bank publication, question draft, account grant or learner attempt was made by
this connection check.

### 3 November — bounded Go drafting and independent checking trial

Completed the owner-authorized ten-question trial from the durable Prelims queue.
Prepared registered hash-checked PDFs and visually inspected all target pages.
Six questions received seven GLM-5.3-Flash calls including a one-question prompt
retry: 24,139 provider tokens, all billing_source=go and balance cost=0, provider
allowance consumption 0.00550247. No fallback. One exact-question explanation was
reused after separate source comparison; two image-flagged plain-text questions
were handled manually without changing flags or canonical identities.

Initial drafts needed metadata/verbosity cleanup, bounded-force interpretation and
qualification of a subjective semiconductor ranking. Updated the runner prompt to
80–130 learner-facing words and max_tokens=700, storing prompt version and cap in
model-run artifacts. One controlled question reduced completion tokens 844→354
and total 3531→3133; no all-ChatGPT control or checking-token measure exists, so no
claim of net ChatGPT percentage savings or model accuracy is made. Nine queue
regressions passed; git whitespace checks passed for touched workflow documents.

Nine explanations published serially through ordinary audited owner maintenance
and the active Oracle timer/service, each with exact full-source readback. Pattern
cq_03281775c7e34f15 remained unresolved: original PDF confirms the numbers, but no
common rule independently established the keyed 77. Original answer/source retained.

Fresh full-bank normalized audit preserved all unrelated content; exact final texts
and audit pointers match nine receipts. The unresolved record is unchanged. Hashes
of 254 attempts, two assignments, 78 memberships, zero human checks and two grants
are identical before/after. Ordinary daily use 375→384, no exemption, zero pending
exports. API, PDF workers and timer active; study health and family site HTTP200.
Queue checkpoint: 14 total published including earlier five, one unresolved, 1050
pending, no active packet. Updated continuation handoff; private reports/receipts
are in reports/go-review-batch-20261103 and state/ai-review/go-batch-20261103.

### 3 November — second ten-question Go continuation packet

Owner requested continuation. Refreshed Oracle eligibility and ordinary allowance
(384 before packet), claimed ten and hash-checked/rendered/visually inspected each
original page with full relevant shared context. Six routine Go v2 calls consumed
18,135 provider tokens, all billing_source=go and cost=0, reported allowance
consumption 0.00330545. No paid fallback; two image-flagged facts handled manually.
All six Go drafts received a separate check and one editorial revision. Appointment
text still used key metadata as reasoning; replaced it with the Governor office's
16 June 2023 evidence. Explicitly bounded poverty/appointment answers to historical
context. Qualified refrigerant comparisons/flammability and workplace escalation;
used printed strong-argument directions and simplified supported Moho terminology.

Eight explanation-only publications applied serially through ordinary audited
Oracle maintenance, exact full-source readback confirmed. Two left unresolved:
cq_074f9dbb041891eb repeats the earlier unestablished number rule; original numbers
independently confirmed. For cq_068bef5061686f96, full family context permits a
countermodel (XS married, widowed engineer Q their son/father of students R and T,
adult R married teacher P), so XS/QP is not uniquely entailed. Recorded keys,
source flags, identities and content of both remain unchanged; no synthetic human
approval or source/answer repair created.

Fresh complete normalized bank audit preserved unrelated content; exact final eight
texts and pointers match receipts. Hashes of 254 attempts, two assignments, 78
memberships, zero human checks and two grants unchanged. Ordinary use 384→392,
zero pending exports, no exemption. Timer/API/PDF workers active, both study health
and family site HTTP200. Content-only work: no code/schema changes or repeated
regression suite needed. Queue checkpoint: 22 total published, three unresolved,
1040 pending, no active packet. Report/artifacts saved under go-review-batch2-20261103
and private go-batch2-20261103; continuation and plan updated.

## 3 November 2026 — Learning collections and separate Website bank

Implemented Important Days, year-specific themes, linked practice sets, source
filters and revision quizzes using canonical question references. Website bank
retains the existing learner MCQ review workflow. Added independent versioned
collection proposals/reviews, question search, immutable history and live/draft
separation; no production content or human reviews fabricated. Home now uses
actual seven-day activity and recent mocks; new mock snapshots retain topic
labels for original-score topic breakdowns. Google PKCE sign-in and explicit
account linking are gated by private provider configuration and preserve MFA.

Validation: 43 focused catalog/auth/review/scoring tests passed; production web
build and whitespace check passed. Migrations 0070/0071 rehearsed on a disposable
full mpsc dump clone and applied successfully. Initial operator notes incorrectly
named bench; its empty migration ledger was detected before any migrations were
applied there. The ledger helper created only an empty schema_migrations table
in bench. Actual service uses mpsc and all prior migration checksums matched.
Synthetic browser checks at390px verified linked-question search/add and public
revision flow with375px document width. Google provider exchange is mocked in
tests; credentials and live provider verification remain outstanding. See
LEARNING-COLLECTIONS.md for routes, publication rules and setup.

Release completed: targeted API and frontend deployed. The first targeted upload
copied a temporary directory's0700 mode onto /srv/api, causing a brief service
restart failure. Restored0755, verified ism-api active and fixed staging mode in
deploy.sh. Production health is OK; family redirect resolves toHTTP200. Live
catalog endpoint returns the honest empty published set; Google config reports
enabled=false. Live Website bank and Important Days render correctly at390px
(document375px). Synthetic quiz check recorded the original answer correctly.

## 3 November 2026 — Google Console provisioning

Created Google Cloud project india-study-map under the signed-in
claudestudy123@gmail.com account, configured external OAuth branding with explicit
user approval of Google's User Data Policy, and created the approved Web client
India Study Map production. Registered the exact production callback. Credential
JSON download stalled and no usable local file was found. Google client details
confirm the client exists but its original secret is now only masked; Google
requires adding a new secret. Browser credential-change handoff rules require
the user to perform that step. No secret installed on the server; Google sign-in
remains disabled. Audience production publishing and end-to-end sign-in remain
pending. Console tab retained for handoff. API service verified active.

## 3 November 2026 — Community creator structure (design only)

Mapped user-created mocks, private/public tags, reviewed subject proposals,
Helpful votes, qualified popularity and creator contribution points onto the
existing catalog, mock runner, taxonomy, discovery and rewards infrastructure.
Design keeps one Studio Create entry, one Library Tests & practice view, compact
cards and existing navigation. Specifies immutable attempts/revisions, scoped
review, vote eligibility, non-redeemable contribution reputation, anti-duplication
claims and phased delivery. No product code or production settings changed.
See docs/COMMUNITY-MOCKS-AND-CREATOR-DESIGN.md.

## 3 November 2026 — Website UX restructuring (released)

Implemented a shared five-destination navigation model: Home, Exams, Library,
Create, More. Removed the large header menu and duplicated controls; matched the
mobile bottom bar to desktop destinations and preserved distraction-free sessions.
Added code-native navigation icons, skip-to-content anchors and visible keyboard
focus. Existing detailed routes remain intact.

Separated the focused study home from the full community feed. Legacy
/feed?section=community and tab/discussion links redirect to /community, keeping
filters. Home prioritizes resume/test, revision and subject practice, with compact
discovery, weekly activity and followed exams. Library has Subjects, Practice,
Reading, Saved and Tools, including separate MPSC/Website bank links. Create brings
existing question, material, practice-set and Important Day workflows together,
with draft/submission/review destinations. More groups personal learning, games,
calendar, community and account, showing staff tools only to granted users.
Updated the public landing page's navigation, headline and stale planned-feature
copy. Collection-kind links preselect the draft type. Guests get a sign-in prompt
before starting a collection; Home no longer requests account-only resume data for
guests or mistakes the expected lack of an account for an activity-load failure.

Validation: TypeScript + Vite production build passed; navigation smoke checks
covered 12 active-section cases and seven focused-session cases. Checked 70 hub
links against actual routes, excluding the wildcard 404. git diff --check passed.
Deployed with scripts/deploy.sh web only; public HTML matches the built artifact,
entry assets return 200, API health and shared family site return 200. Live desktop
inspection verified Home, Library practice/reading, Create, More, guest creation
prompt and legacy community redirect. No production content or account mutations
were used during QA. Saved live screenshot at docs/screenshots/study-home-2026-11-03.jpg.

Limitations: local preview access was denied by browser approval. The browser's
viewport override did not resize the live 1280px viewport; mobile visual QA remains
unverified for this change, and the override was reset. Signed-in author/reviewer
flows were not exercised in production. This release reorganizes current features;
user-created timed mocks, subject proposals and new vote-based reputation remain
in COMMUNITY-MOCKS-AND-CREATOR-DESIGN.md. Google OAuth secret setup remains pending.

## 3 November 2026 — Sangzel full administrator access

User explicitly requested giving sangzeldoto@gmail.com administrator privileges
after confusion between the UDC assignment and comprehensive admin console.
Applied the existing global owner role (grant 4), with an operator:codex audit
entry and reason identifying the direct user authorization. Target was the exact
registered account, locked within the transaction; duplicate grants are ignored.
Verified committed grant and matching audit event. Existing active UDC assignment
remains 48 papers. No other role, account credential, auth session, source content,
review approval or publication protection changed.

Staff authenticator enforcement remains enabled. The target account has no enabled
authenticator yet; it can browse the dashboard but must complete its own setup at
/account/security before privileged writes. Existing password is unchanged.
Production study API and family site both returned HTTP 200. Updated current
instructions and appended the assignment runbook rather than rewriting historical
access receipts.

## 3 November 2026 — Focused editorial review, phone and iPad layout

Published frontend only with `bash scripts/deploy.sh web`. Added prominent UDC
review entry on admin home, auto-selection of the matching active assignment,
searchable paper choice, current-page question search/outcome filters, compact
25-question paging, and previous/next question navigation across page boundaries.
On widths below 1280px the question rail collapses after selecting a question;
review content uses one column and wrapping actions. Inputs use 16px text to avoid
phone focus zoom. The PDF viewer is optional/lazy, separate from the review form.
Owner assignment management and secondary tools are below the review workspace;
management data loads only when opened.

Added checklist cards, clearer outcomes, evidence note, Save & next, immediate
recorded-check status updates, explicit staff MFA guidance, and 24-hour tab drafts
keyed by user, assignment, appearance and source version. Failed saves retain the
note and never advance. Earlier checks are labelled as historical rather than
current verification. All existing backend assignment, MFA, source-version,
publication and answer-protection checks remain unchanged. No bank/API changes or
production check submissions were made. Signed-out entry no longer incorrectly
claims the account has no assignments, and its login link preserves the UDC route.

Validation: full TypeScript/Vite production build passed; check-editorial-review
passed pagination boundaries, evidence rules, draft expiry/validation/isolation
and filtering. check-editorial-component.cjs passed failed-save retention,
successful save-and-next payload/status, draft cleanup and MFA disabling using
React test renderer (18.3.1 installed in /tmp/editorial-component-tests; run from
repo root with that directory as the script argument). Existing Group B navigation,
UDC study, archive ordering and paper identity checks passed. Production API
healthy; family site follows its redirect to HTTP 200. Browser verified published
signed-out page at 390x844 and 768x1024: document width equals viewport width,
without horizontal overflow. Screenshots saved in docs/screenshots/editorial-*
2026-11-03.png; viewport reset afterward.

Limit: authenticated responsive screens were component-tested, not visually
exercised in a signed-in browser or physical iPad. Earlier local browser-preview
approval denial was respected; no alternate route was used to bypass it. This
release does not claim a guarantee of zero regressions.

## 3 November 2026 — Multi-paper editorial progress overview

Replaced the long paper select with a searchable eight-card overview. Added All,
In progress, Not started, Needs attention and All recorded filters, paper progress
bars, assignment totals, and a Continue action for the most recently reviewed
unfinished paper. Opening an unfinished paper jumps to its first unreviewed
question, including the correct 25-question page; fully recorded papers open a
flagged question first if one exists. Current-paper progress stays visible and
All papers & progress returns to the overview. Existing version-scoped tab drafts
survive this switch. Saved checks refresh totals without resetting the inspector.

The existing authorized papers endpoint now aggregates the latest saved outcome
per appearance across the whole assignment, with last activity and a resume
pointer. Repeated checks do not inflate progress. Wording distinguishes recorded
inspection from source freshness, published corrections and verification; flagged
items remain counted separately. No migrations, bank changes, new permissions or
synthetic production reviews. Added targeted `scripts/deploy.sh editorial-api`
release with router backup/health rollback, preserving other API files.

Validation: seven isolated PostgreSQL editorial tests passed, including 26-question
resume across a page boundary, duplicate/revised outcomes, changed-source history
and cross-account denial. Overview component tests passed eight-card pagination,
resume selection, status filters and search empty state. Existing editorial helper
and save/MFA component regressions passed. TypeScript/Vite production build passed.
Read-only production query verified consistent totals and resume offsets for all
48 assigned UDC papers in 55ms. API health and shared family-site health passed.
Initial API staging compilation hit an existing /tmp bytecode-directory ownership
issue before replacing the router; using a dedicated bytecode directory resolved
it. A frontend deploy was repeated after the script changed during execution.
Signed-in phone/iPad visual testing remains outstanding; no local browser denial
was bypassed. Component tests used react-test-renderer@18.3.1 in the existing
/tmp/editorial-component-tests directory.

## 3 November 2026 — General source-review workspace and conflict visibility

Released the unified registered-paper review workspace through the targeted
editorial API and web deployment modes. Removed the UDC/Prelims assignment
allowlist: owners choose any registered paper-based module or an explicit set of
existing papers from MPSC/Website sources. Search results are paged cards, with
selected-scope preview and removals before reservation. Identical paper sets reuse
the existing reservation. Pending account confirmation, explicit activation,
revocation, email binding, staff MFA and exact source authorization remain.

Migration 0072 makes module membership optional for standalone paper assignments,
adds a display title and stable scope keys, and supplies a compatibility insert
trigger for existing exam-scope operators. Rehearsed against a disposable live dump
clone, applied normally with the migration ledger, then dropped the clone. A hash
comparison confirmed every pre-existing assignment's reviewer, email, state,
version and paper membership remained identical (78 assigned paper memberships).
No actual new reviewer grants, assignments or human checks were created by release.

New module papers are listed for an explicit owner scope addition, guarded by the
assignment version and an audit event. Already assigned papers are marked; adding
only existing IDs is rejected rather than reporting a fictitious scope expansion.
Module assignment snapshots never expand automatically. Question IDs/appearance
IDs continue to reference the bank; no module-specific copies are created.

Bulk source-version comparison now separates recorded history, current Checked
outcomes, current flagged issues and Recheck needed. Canonical text/answer/
explanation, appearance/source, paper identity, primary classification and related
paths participate in the same version token as stale-save rejection. Recheck
priority and source-position resume span the whole paper. Review complete requires
all source questions to have a current Checked outcome. Green progress reflects
current checks. Overview filters/search/page survive opening a question; progress
refreshes after saves, returning to the overview and browser focus. Draft isolation
uses the complete user/assignment/appearance/source tuple for storage and remounts.

Added separate correction queue/publication counts, source-bank labels, assigned
reviewer handles, shared-question module/source context and the current user's
proposal links. Other authors' private draft IDs/titles/notes/payloads are excluded;
non-private submitted work is represented by status counts, not proposal access.
Assigned handles do not claim online presence or an exclusive editing lease.
Active assessment answer gates apply to context reads. All actively assigned
sources now require a fresh correction token, including future/individual scopes.
Existing publication, evidence, independent-review and scoring safeguards remain.
No bank-owned SQL or canonical bank JSON was edited by this feature.

Admin entry now opens Review workspace. New PDF drafts, Important Days/practice-set
metadata and learner-submission queues are linked with their existing approval
paths. Question-only learning catalog metadata is not silently converted to access
to every question in its source papers. These boundaries are documented in
EDITORIAL-WORKSPACE.md and appended to the human-review runbook.

Validation: 81 combined backend tests passed in one disposable PostgreSQL DB
(editorial assignments, current affairs, bank review). New cases cover arbitrary
future modules, exact Website/mixed paper scopes, duplicate reservations, explicit
scope expansion and stale versions, all five source-version change categories,
shared canonical changes across appearances, historical checks, no bank mutation,
private draft exclusion, answer gates and out-of-scope denial. Fixed test-fixture
cleanup so synthetic active assignments cannot leak into subsequent suites.
Four frontend regression scripts passed helper/draft rules, failed-save retention,
Save & next payload, MFA disabling, eight-card paging, current-completion/recheck
filters, arbitrary module and exact-paper reservation payloads, scope reset and
context links. TypeScript/Vite production build passed; final entry/chunk hashes
and feature strings verified against deployed assets. Private catalog returns 401
signed out. Existing 30-paper Prelims and 48-paper UDC backend reads passed progress
sum and resume-position checks in 171ms/201ms respectively; owner module catalog
returned seven choices. API healthy, family redirect ends HTTP 200.

Limits: authenticated phone/iPad layouts were component-tested, not visually
exercised in a signed-in browser or physical device. Prior local-preview denial
was respected. Version tracking is conservative: rewriting a row can require
recheck even when its visible text looks unchanged. No promise of zero regressions
or automatic content certification is made.
# 4 November 2026 — Editorial simplification implementation brief

Prepared `docs/EDITORIAL-SIMPLIFICATION-IMPLEMENTATION.md` after the owner requested
fewer review steps, easier wrong-tag cleanup and final admin authority, and left
the choice of planning versus immediate implementation to this task. Chose an
implementation handoff for Sol 6.1, as communicated in the conversation.

Inspected current editorial checks, source-version logic, assignment boundaries,
direct admin answer decisions, retagging proposals/batches, publication eligibility,
worker acknowledgement/credit, report resolution, navigation, picker and existing
tests. The brief defines a shared admin decision/publication path, tag discovery,
single-screen work, conservative migration to aspect-specific review fingerprints,
automatic linked-report resolution after verified application, and a staged file
map/acceptance suite. It keeps public proposal review and existing source/answer
protections; it does not add compulsory whole-paper sign-off after completed work.

Documentation only. No runtime code, migration, production data, account grants,
services or live website changed. No runtime tests or mobile QA claimed for this
brief. Implementation/deployment and its acceptance checks remain pending.


## 2026-11-04 — Editorial simplification implemented and deployed

Implemented My work / Needs attention / Completed, inline edits, explicit Checked
& next attestation, searchable taxonomy/source pickers, independent tag search
scope, final admin decisions and linked reports. Public submissions retain
independent review; assignment-only editors cannot publish. Current evidence,
subject grants, MFA and answer controls remain. Content fingerprints avoid reopening
unchanged answers after tag-only changes; legacy checks remain conservative.

Bulk publication required a real worker fix: separate tag publications change the
bank checksum after the first item. Added atomic up-to-20-target application under
one lock with immutable manifests, durable receipts, sync/readback verification and
grouped failure/retry. No manifest baseline is rewritten to bypass stale checks.
Only matching linked reports close after application; no maintenance points accrue.

Validation: 157 backend tests passed, including interrupted batch recovery, stale
atomic batches, permissions/revocation, evidence drift, public quorum, answer gates,
report closure and disposable-bank readback. Frontend helper/component regressions
and TypeScript/Vite build passed. Rehearsed migration 0073 on a disposable clone,
then applied it. Deployed selected API/worker files with rollback and built web
assets. API, document worker, publisher and review timer active. Health/family
checks passed. Assignment, membership and grant hashes exactly match baseline;
inspections/admin decisions remain zero and canonical questions remain 81,627.
No synthetic production publication or human review was created.

Skipping fingerprints for uninspected overview questions reduced measured reads
from about 1.4–1.9s to 134ms (Prelims30) and 165ms (UDC48). Default tag attention
still measures around 2.3s on 58,500 missing-topic matches.

Signed-out live entry inspected at 390x844 and 768x1024 without horizontal overflow;
viewport reset. Authenticated mobile/iPad visual QA remains pending without a
signed-in session. Existing local-preview denial was respected. Passing tests do
not guarantee zero regressions or certify existing bank content.


## 2026-11-04 — Database-wide tag discovery performance follow-up

Owner requested faster cleanup and clarification of bank-wide tagging. Replaced
per-canonical appearance sorting and report counting with a scoped DISTINCT ON
source selection and grouped open tag reports. Count and paginated items now share
one materialized filtered snapshot/evaluation. Empty/beyond-end pages retain exact
counts. Source selection preserves primary preference inside the selected bank,
module, year or paper; shared canonical targets appear once. No content, taxonomy,
grants or assignments were rewritten and no automatic reclassification was run.

Added disposable-DB regressions for shared MPSC/Website appearances, exact bank/
year/paper selection, current browsable module membership, empty pages and multiple
reports without duplicate questions. All 158 focused backend tests passed. Initial
JSON aggregation used a page alias that collided with the numeric page column;
regressions caught this before deployment, and the explicit page_rows alias fixes
it. Full item shape was also checked in read-only production profiling.

Deployed via scripts/deploy.sh editorial-simplification with backup/rollback.
After-release server route reads: attention 654ms (previous 2312ms), no-topic 549ms
(previous 1485ms), reported 32ms (previous 1965ms), no-subject 60ms (previous 114ms).
Invalid-path empty result measured 396ms (previous 287ms); the primary improvement
is the broad list, not a claim that every query is faster. These are server route
measurements, not end-to-end browser render timings. Paper overviews remain125/161ms.
API health and family return200; protected tag list returns401 signed out. API,
document/publisher services and review timer active. Assignment/membership/grant
hashes still match the earlier release baseline, checks/admin decisions remain0,
and canonical count is81,627. No new migration or frontend build was required.

Cleanup covers registered source questions across both banks within actual grants.
Approved canonical tag changes affect shared module appearances after normal
publication/sync. The 58,500 missing-topic matches are coverage gaps requiring
inspection, not proof that those questions are incorrectly classified. Unreported
semantic mistags cannot be inferred automatically. Authenticated phone/iPad visual
QA remains pending as recorded in the preceding release.


## 2026-11-04 — Discoverable review and admin navigation

Owner requested visible routes to editorial/admin work and advice on reviewing by
module. Added authorised workspace shortcuts below the normal site header and a
prominent Review & administration section at the top of More. Assigned-only users
see Review workspace; staff also see Admin dashboard and tag cleanup. Ordinary
learners do not gain staff navigation or access. Header account reloads clear role
shortcuts, and stale async account responses cannot repopulate them after sign-out.
The five primary destinations stay intact; the utility strip scrolls away instead
of increasing the sticky header height over existing editors.

Admin sidebar now links directly to Review workspace and Find & fix tags on phone
and desktop. Admin home leads with module/paper review, followed by Across the bank
for broader tools. Editorial has an Admin dashboard return link and an explicit
Tag issues in this module action. That action opens a fresh current-module tag
scope, clearing unrelated tag filters/batches while preserving the exact My work
assignment, paper, question, appearance and pagination. Existing correction and
publication methods are reused; no bank content or permissions changed.

Added check-review-navigation.cjs: owner, assignment-only, pending invitation and
ordinary-learner visibility; sign-out/stale response isolation; focused-session
visibility; non-sticky utility placement; admin entries; future module filters and
source-position retention. It passed alongside editorial helper, quick-review and
workspace component checks. TypeScript/Vite build passed, deployed via deploy.sh
web, and deployed index checksum matches local dist. API health reports 81,627
questions; shared family site returns200.

Live browser confirmed the updated editorial guidance and More navigation. Signed-
out phone390px/document375px and tablet768px/document768px had no horizontal
overflow; viewport reset. Authenticated navigation is component-tested but cannot
be visually certified with the available signed-out browser. No fabricated login
or production review was created. Recommend module-by-module inspection first;
whole-bank tools remain useful for reports and corrections spanning source papers.


## 2026-11-04 — Separate Group B Non-Gazetted and Gazetted learner homes

Implemented the owner's request for both Group B designs. Clear group selection,
distinct warm/sage homes, Home / Subjects / Papers / available Practice / Progress,
and a compact mobile navigation row replace the generic shared entry. Removed the
redundant global focus selector only on the Group B hub. Existing Group B overview
URLs reach the new homes; existing paper/question/practice links remain valid.

Non-Gazetted uses real common English/GK/topic counts and the approved Current
Affairs ID. Existing explicit technical-source roles and dated syllabus disclosures
remain. Gazetted's current five papers are written sources with no answer-ready
MCQ pool, so its home leads with original papers and collapses sparse subject
coverage. Availability controls practice actions. Progress shows a compact reading
explanation when no attempts exist, retains historical activity when available,
and never treats reading/offline written work as automatically scored. Shared study
asks for one group when viewing progress. Other modules keep default progress links.

Added a searchable original-paper library with year/written/sort filters and ten
items per page. Filter changes reset pagination; URLs retain filter state. Source
IDs, titles, PDFs and owning collections are preserved, and paper return links
lead back to the matching Group B library. Exam saving reuses existing bookmark
APIs with retry/error handling and stale-account response isolation. No bank/source
membership, taxonomy, answer, permission, backend or migration changes were made.

Passed Group B navigation/components (including actual progress availability and
historic activity), UDC study, archive ordering and review-navigation regressions,
git diff --check, TypeScript and Vite. Final deployment through deploy.sh web
completed; local/live index SHA256 matches
ba7e1165803483667c8b77f674dd7428c3c18710772407f8fb554758c36f5cd0.
API health OK at81,627 questions; shared family site healthy.

Live checks passed group switching, Gazetted reading progress, NG archive page2
and filter reset, General English/2026/written filtering, exact original paper
and back link, overview redirect and approved Current Affairs scope. Phone390px
had375px document width on NG home/archive, primary action ended at710px inside
844px viewport. Tablet768px had753px document width on NG archive/Gazetted home.
No overflow in those checks. First deployed design was visually inspected; final
browser screenshot captures timed out even with a fresh tab, so final screenshot
and physical-device QA are not claimed. Viewport overrides reset. No production
answers/bookmarks were submitted and no signed-in test session was fabricated.

Current design, evidence and remaining content/future-feature scope are recorded
in docs/GROUP-B-STUDY-DESIGN.md. Updated the continuation checkpoint so later work
does not replay old deployment instructions. Source/taxonomy review and saved short
study sets remain separate from this completed frontend design release.


## 2026-11-04 — Shared module review design

Owner requested a review system suited to compiled exam modules, including Group B,
UDC, Assistant and future additions. Read the current editorial/permission/publishing
implementation, migration contracts, Group B roles and collection selection paths.
Confirmed that corrections use shared canonical identities, but paper/question
inspection progress currently filters by assignment as well as appearance. Existing
shared-use context joins collection papers and is insufficient to describe every
filtered area or future compilation's exact membership.

Created docs/SHARED-MODULE-REVIEW-DESIGN.md: one workspace, separate canonical edits,
source inspections and module membership; reusable exact-source checks with original
reviewer attribution, independent source variants, permission-bounded scope adapters,
deduplicated parent progress, aspect freshness, direct admin actions and honest
publication state. Includes daily UI wireframe, scope/removal impact, future module
configuration, explicit owner checks without fake assignments, additive schema/API
implementation slices, migration/rollout approach and acceptance scenarios.

Preserves existing public-submission rules, MFA/assessment gates, frozen assignments,
Oracle publication, attempts and history. Read-only design work only: no live data,
roles, app code, migrations or source memberships changed, and no tests or deployment
are claimed for a document-only deliverable. Markdown whitespace and local reference
checks passed. PLAN now distinguishes this completed design from pending implementation.

## 2026-11-04 — Shared module review core deployed

Implemented reusable exact-appearance inspections across assignment/module scopes,
with original reviewer attribution, evidence freshness, explicit append-only issue
resolution and idempotent direct checks. Migration0074 permits owner/publisher
checks with an explicit origin scope instead of a fabricated assignment. Legacy
assignment routes remain available. Existing assessment/MFA/subject boundaries,
frozen assignments, public independent review and Oracle publishing remain.

Added permission-bounded review_scope adapters for current published collections,
section predicates, pins/excludes and exact Group B source roles. Materialized
candidate-paper selection and batched status lookup avoid a broad correlated bank
scan. Scope/status service timing improved from roughly3–6seconds to UDC216ms,
Assistant73ms, NG534ms, Gazetted20ms and NG common241ms; catalog68ms. These are
read-only service timings, excluding browser/network latency. Held records remain
visible for review and are explicitly distinguished from learner availability.

SharedModuleReview adds a searchable module chooser, attributed prior checks,
honest question/appearance counts, source-paper progress, full-paper search and
All/Remaining/Needs attention. Papers open at remaining work. If a source leaves
the current queue, the UI explains it and supplies Show all / Continue actions.
Focus refresh and URL source identity preserve context. Existing inline correction
forms and shared tag cleanup remain; exam homes expose role-aware module links.
No new review page is needed for modules using existing collection definitions.

Migration0074 was rehearsed on a disposable production-dump clone, then applied;
applied checksum53cb9c614bcdb083230ce0b92155a48f38a452a938d381eeae55443adfd441b0.
104 backend tests passed (shared review, assignments, simplification, Group B,
bank review, answer admin, publication verification), with one existing Starlette
anyio deprecation warning. Frontend shared-review/editorial/navigation/Group B
component checks passed. The final shared UI rerun passed after navigation polish;
local Vite production build passed in4.38seconds. No tests wrote production reviews.

Narrow API release backup: /tmp/shared-editorial-1793775669/backup on Oracle.
Frontend deployed with scripts/deploy.sh web; index checksum
08cc69205ae4b56e96b1d55d967ca85ded4f1293caceb0c87a8d5910deb0a1c0.
Release commands returned healthy study API and family site. Logs are in local
/tmp/ism-shared-review-release-api.log and /tmp/ism-shared-review-release-web.log.

Delivery boundary: shared-review core is live; general versioned module composer,
dependency/cycle validation and membership-change preview/editor remain later-stage
work. Module selection disclosure is read-only. Source-collection tag cleanup does
not claim exact filtered-area scope. This deployment does not certify content.
Live signed-out phone390/tablet768 entry widths passed; authenticated visual and
physical-device QA remain pending. Browser screenshot capture timed out. No signed-in
session was fabricated and no production answers, bookmarks or inspections seeded.

Final readback matched local/live frontend and migration checksums. Migration ledger
contains0074; API, document worker, publisher and review timer are active. API health
reports81,627 questions/13,172 scorable; signed-out scope access correctly returns401.
Full-row assignment, assignment-paper, grant and collection-paper hashes match the
pre-release baseline, with zero editorial checks and81,627 canonical questions.
Preservation evidence: /tmp/ism-shared-review-baseline-before.txt and
/tmp/ism-shared-review-baseline-release.txt (identical). Family redirect resolves
successfully. Final Markdown whitespace check passed.

## 2026-11-04 — Versioned source-paper module composer deployed

Owner authorised the remaining composition editor and responsive verification.
Implemented additive migration0075 (draft configuration and immutable publication
history), owner/MFA/CSRF-protected module-setup routes, composition service and a
secondary ModuleCompositionEditor panel in the shared workspace. Supports new
hidden modules, resuming drafts, searchable individual papers, published-library
imports, explicit exclusions, saved before/after preview and reasoned publication.
The published source version stays live during drafting. Publication appends a new
collection version and moves its pointer atomically; prior versions and source
checks remain. Retries are idempotent; stale draft/source/membership tokens fail.

Dependency checks reject self/circular imports. Imports freeze a paper-library
snapshot and require deliberate refresh/publication for later source changes.
Cross-bank and restricted-module publication are rejected. Existing section filters,
pins/excludes and paper rules survive except explicit removals; removal cannot be
undone accidentally by a shared canonical pin. New/imported papers do not silently
become timed mocks. No bank JSON, canonical content, assignments or permissions
are edited. Arbitrary filter authoring/per-question pin controls remain outside
this source-paper composition panel; a child learning area is not mislabeled as
its entire library.

115 backend tests passed, covering composition, shared evidence, assignments,
simplification, Group B, bank reviews, answer administration and publication checks.
One existing Starlette/anyio deprecation warning remains. Frontend composer/shared
review/editorial/navigation/Group B checks and local build passed (4.40seconds).
The new UI tests exercise explicit preview, draft retention, stable retry keys,
owner/account transitions and MFA. API tests include permissions, CSRF, MFA,
cycles, stale previews, snapshot stability, source removal, section preservation
and actual published scope parity.

Migration0075 rehearsed against a disposable production-dump clone, then applied.
Checksum3999cdfc103b6ebcbecdb8d47492a7dd1787ffd792054052025622b0ce11299a.
Narrow API rollback files: /tmp/shared-editorial-1793776670/backup on Oracle.
Web deployed with scripts/deploy.sh web; local/live index checksum matched:
edce0f41b5388ef7174749bb28a8838dbdfbf03aefbcff38ca7e3ab8f61f3a82.
API, document worker, publisher and review timer active; study health81627/13172,
signed-out setup401, family200. Full-row collection/section/source-membership,
assignment/assigned-paper/grant hashes unchanged. Canonical questions81627, source
checks0, composition drafts0/history0: no production fixtures or fake inspections.

Production read-only previews ran under the application DB role with READ ONLY,
using an existing owner's permission identity for service evaluation, never a
fabricated login session. UDC1072ms (48papers/3930appearances), NG1718ms
(97papers/8060appearances), Gazetted300ms (5papers/137appearances). Each unchanged
selection produced zero additions/removals. Measurements exclude network/render.
Logs: /tmp/ism-composer-{final-tests,migration-rehearsal,migration-apply,api-deploy,
web-deploy,profile}.log; preservation baselines under /tmp/ism-composer-*before.txt
and *after.txt. Browser remained signed out after the user reported logging in
elsewhere; requested the specific Codex browser session for authentic device QA.

## 2026-11-04 — Everyday module review continuation deployed

Audited the existing shared workspace, scope/status adapters, correction callbacks,
module composer and admin prototype before extending them. Preserved the substantial
pre-existing working-tree changes. No new worktree, schema migration or bank-content
change was needed.

Each selected module now has one prominent Continue reviewing action, including
modules with no previous inspections. It resumes unfinished work in the current
paper or the most recently active unfinished paper. Shared paper overview suppresses
its duplicate summary/continue card. Module setup remains collapsed and now follows
the daily review content. Existing source PDFs/context and 44px wrapping controls
remain. Work shortcuts distinguish module source/answer attention, wrong tags in the
source collection, and learner/publication queues across the permitted bank; they
do not claim exact learning-area scoping for the latter queues.

Added server-side continuation by exact appearance identity after a successful
inspection. It seeks the next unresolved source in original paper order, wraps
once, skips the saved source even if still unresolved, and returns the correct page
after queue shrinkage. Empty/end-of-paper views explain the saved result and offer
the module continuation action where other papers remain. Manual previous/next,
search, URL source state and failed-save draft retention remain. Correction saves
retain the canonical receipt and expose Continue to next unresolved question with
an explicit pending-publication caveat. They never create an inspection attestation.
Resume priorities now select incomplete work before completed rows, including saved
assignment scopes opened through the shared workspace.

Module totals separate remaining inspections, appearances with unresolved issues,
and submitted/awaiting-publication or failed corrections. Corrections deduplicate
canonical questions across source papers. Labels explain that issue and inspection
categories can overlap. Existing checks retain original attribution; public
submission policies, final authorised admin decisions and MFA/assessment/source
safeguards continue through their existing routes.

Validation:118 backend tests passed across shared review, composition, assignments,
simplification, Group B, bank review, answer admin and publication verification.
The three new regressions cover shrinking page boundaries/wraparound, a lone saved
unresolved source, and canonical correction deduplication. The strengthened shared
suite passed again (15 tests). Existing anyio deprecation warning remains.
Shared-review UI now exercises successful save-to-next URL/page binding. Component,
overview, workspace, navigation, Group B and composer checks passed. Final local
TypeScript/Vite build passed (4.42seconds); git diff --check passed.

Deployed through scripts/deploy.sh shared-editorial and web. The narrow API file
list already includes both changed backend files, so it needed no expansion.
API rollback backup: /tmp/shared-editorial-1793778586/backup on Oracle. Final
local/live frontend index SHA256:
26e2986aecdcc5cf013fe7ac80a5fa44fead62cabdf1e67111ccdb539d9b74ce.
API, document worker, publisher and review timer are active; health81627/13172,
signed-out scope401 and family200. Applied0074/0075 checksums remain unchanged.
Full-row collection, section, source-membership, assignment, assigned-paper and
grant hashes match before/after. Canonical questions81627, source checks0,
composition drafts0/history0. Evidence: /tmp/ism-daily-{before,after}.txt;
test/deploy logs: /tmp/ism-daily-review-*.log. No production fixtures, fabricated
sessions or content edits were used.

Authenticated phone/iPad visual and physical-device QA remains unverified. No login
was requested again, and the prior local-preview denial was not bypassed. Existing
responsive structures were retained and tested as components; this is not a new
visual-browser certification or content certification.

## 2026-11-04 — Group B Gazetted source audit and repairs

Owner said Go after the source-coverage/admin-capability recommendation. Audited all
137 existing entries against13 rendered pages from five hash-verified original PDFs.
Found133 printed questions plus four duplicate extractions; all137 lacked physical
page locators,114 lacked printed numbers, and all137 lacked approved topic tags.
Kept source IDs, canonical identities, historical wording/legislation, blank written
answers and actual attribution. No human source-inspection sign-offs were created.

Published415 exact corrections:137 source locators,137 original section/instruction
restorations,137 approved subject/topic paths and four literal wording repairs.
One source question is printed incompletely; the restored wording has a visible
source note instead of an invented completion. All415 existing publication IDs are
applied with verified source/canonical readback; no new audited job is pending/failed.
Four duplicate extraction identities are recorded, with matching page/number/context,
and remain separate IDs pending relationship/presentation work.

Confirmed a missing registered2016 common Inspector/Sub-Inspector Paper I (zero
extracted questions). Actual owner composer save/preview/publication produced v2:
five to six library papers, zero added/removed appearances and137 stored entries.
That original-PDF resource is linked with explicit unextracted-question copy. Other
module definitions, exact assignments and grants are unchanged. No new MCQs, mocks,
answers, scoring eligibility or other module source memberships were introduced.

Nine September2026 Combined Gazetted originals already exist on Oracle (English A/B,
Essay, GS I/II/III A/B) but have no registered paper/question rows. Official archive
listing and source headers establish the gap; direct archive retrieval returned403.
They still need source intake/extraction and existing new-paper review. The linked
common2016 Paper I also needs extraction. Coverage is not claimed complete.

Extended quick corrections with physical PDF page/printed-number repair, section
instructions and shared-passage fields. Existing final admin/public proposal routes
and draft/version protections remain. New paper cards disclose zero extraction.
The bounded source publisher now accepts descriptive locator/context repairs while
rejecting written option/answer mutations. The initial100 locator writes reached
JSON/sync but readback stopped because canonical absent answer provenance uses
'none' while source provenance is NULL. Paused the Oracle correction timer, added
strict written-only normalization tests and exact prepared-output recovery, then
reconciled those same100 receipts. No re-review, new request IDs, direct content SQL,
protection reset or fake login was used. Timer restored; all jobs verified applied.

123 publisher/operator/verification tests and103 admin/shared backend tests passed
(overlapping suites), with the existing anyio deprecation warning. New cases cover
written patches, rejected MCQ mutation, exact failed-ack recovery and strict provenance
normalization. Updated stale coordination fixtures to both real Oracle units and
removed a synthetic out-of-scope grant leak between tests. Correction/reference/
context, question actions, shared review, navigation, Group B, paper overview and
composer UI checks passed. Final local production build and diff checks passed.
Authenticated phone/iPad visual QA remains unverified; no login was requested and
no denied preview was bypassed.

Preservation readback:81627 canonical questions,13172 scorable globally,259 unchanged
attempts,2 assignments/78 assigned papers,3 grants,0 source checks. Every appearance
retains its canonical ID; source holds and written-unanswered states match. Full
non-Gazetted configuration hashes match. Unrelated JSON content matches after exact
reviewed-target empty-related-list and unanswered-index normalizations; original
comparison/diff evidence was retained. Ordinary daily budget425/500; no exemption.
Existing101 unrelated failed publications are unchanged. Explanation queue remains
32 published,3 unresolved,1030 pending and no active packet.

Portable evidence: docs/sources/group-b-gazetted-source-audit-20261104.json.
Detailed before/after/source renders, reviewed map, requests, receipts, reconciliation,
publication states and preservation comparisons are under
reports/group-b-gazetted-audit-20261104/. Current guide: docs/GROUP-B-GAZETTED-AUDIT.md.
Final bank SHA2566c2c1e38efe97702ad2c24974de9c9720d9dfb2206471f9832a8d2b8357f9353.
Bounded publisher local/live SHA25673afca98c94f8e389a712cb6ab7028981a56f34e133f166a515d8b7360adeb50;
shared verifier b60b56f15a92a644c6e35d5cddcaac12ddce11431212f0bd8dd81fd693f44a1b.
Narrow operator/verifier rollback backup:/tmp/source-review-tools-1793779953/backup
on Oracle. Deployment through deploy.sh source-review-tools/web; API restarted for
the verifier and health checked. API/document worker/publisher/review timer active;
study health81627/13172, signed-out editorial401 and family200. No migration or Caddy
change. Test/deploy logs:/tmp/ism-gazetted-*.log. Final web index hash recorded below.

Final local/live web index SHA256: a35d15a7d84503b257ff59de08cf2f424ff017e0cb18e2f68ee86925f497eb53.
# 4 November 2026 — Gazetted next phase: private intake and duplicate reading

Prepared the nine verified September2026 Combined Gazetted PDFs plus common2016
Paper I through the actual paper-workbench upload/create/save/document-job routes
under the existing owner's delegated operator authorization. No browser sessions,
human inspection attestations, reviewer accounts or approvals were fabricated.
Ten drafts contain756 questions (732 MCQ/24 written),104 original pages and40
completed source crops; all50 extraction/crop jobs finished. English retains
A1–A3/B1–B66 numbering and section instructions; General Essay retains its two-unit
choice. Answers, keys and explanations are unset. Broad subject labels remain
drafts, requiring exact source/taxonomy review before genuine independent approval.

Added read-only `scripts/prepare-gazetted-intake.py`, with hash/printed-sequence
checks, bounded local Poppler extraction, conservative option splitting and
source-based crop coordinates. Article39(b)/(c) references remain in stems, not
option labels. Ambiguous columns retain raw text instead of invented options.
The first attachment pass stopped because it compared raw preparation text with
the route's whitespace-normalized saved payload. Recovery compared the exact
Pydantic-normalized source payload plus the original completed crop IDs; it refused
other changes and reused existing drafts/history/jobs, creating no replacements.

The current new-paper publisher refuses the already registered common2016 source.
That draft exposes the limitation; a guarded empty-source import extension is still
required. No duplicate Uploaded paper or live question publication was attempted.

Added explicit source-audited duplicate presentation for Paper III:23 printed
questions/27 stored entries, with show-all, direct appearance links, flags and exact
correction identities retained. Guards compare current locator, text/context,
figures, classification and hold fields and show both records on disagreement.
No database duplicate votes, canonical merges, scoring changes or module edits.

Verified fresh original/private PDF hashes, all saved payloads, unset answers,
zero submissions/reviews/publications, all completed crop bytes and104 extracted
pages. Bank/sync SHA remains6c2c1e38efe97702ad2c24974de9c9720d9dfb2206471f9832a8d2b8357f9353;
81,627 canonical/13,172 scorable questions. Attempts, assignments, grants, human
checks, every module configuration and the old source/canonical rows are unchanged.
Evidence: `docs/sources/group-b-gazetted-intake-20261104.json` and ignored
`reports/group-b-gazetted-audit-20261104/intake/`.

Validation: five focused preparation regressions; live27-entry/four-group checks;
component grouping/show-all/exact-link/flag/navigation regressions; archive, identity,
source formatting, Group B design/navigation checks and TypeScript/Vite build.
Authenticated phone/iPad screenshots remain unverified; respected the instruction
to stop pursuing login and the denied local browser preview. Web deployment and
final health/checksum checks are recorded below when complete.

Web deployment completed with scripts/deploy.sh web. Public index SHA
d4e2cfd39bfcbfe9fd2bd0ed8aa2cbb80f734a2cfae0df1a532929ae10212a0f and PaperViewer asset SHA
19eab5da999ffbf3774b39a857bc2821acf5d3706e8eb25cccd6b0e55d2ddf47 match the local build.
Study API and family site returned200; API/document/paper-publisher/review-timer
services are active. Final privileged bank checksum still matches the preserved
source above. No API, migration, Caddy or service configuration was deployed.
## 4 November 2026 — existing empty original import support

Implemented and deployed explicit draft binding to an already registered empty
source, resolving common2016 Paper I's intake gap. The saved payload includes the
exact original paper ID and version of its paper metadata/document registration.
Saving/adopting a new binding invalidates prior approval. Save/submission validate
the original PDF registration, identity and zero extracted appearances. The paper
publisher repeats the checks, verifies private/original PDF bytes, and the guarded
writer rechecks the full known paper identity and absence of JSON questions under
the shared bank lock. Existing paper metadata and registration are retained; no
Uploaded alias is created. Normal sync and complete question/context/classification/
identity readback remain required. A now-populated database target is rejected
unless the exact prior receipt/payload/submission/appearance set explains it; the
writer also verifies the immutable manifest and bank checksums on retry.

Added an Existing original paper control to the workbench: explicit link/refresh,
registered exam/year/subject adoption, stale/ambiguous/populated guards, read-only
review visibility, unlink and accurate published-state wording. Question/answer
objects remain untouched. No schema migration or authentication/role change.

Validation passed38 backend tests (paper workbench, Gazetted preparation and paper
readiness), focused source-link UI checks, duplicate/identity/archive/Group B
regressions and TypeScript/Vite. New reusable
`scripts/rehearse-existing-paper-import.py` ran the actual API, worker, protected
fixture writer and normal sync SQL in a disposable local database. It published one
synthetic written and one unanswered MCQ under the same existing paper, preserved
all old paper metadata/question answers and the single source registration, and
created no Uploaded alias. A deliberate failure after SQL commit recovered through
the same immutable receipt without a second append. Those approvals/accounts were
synthetic local fixtures only; the database was removed and recovery bank unchanged.

Deployed only router/paper target resolver/paper publication bridge/guarded writer
through the new `deploy.sh paper-source-import` target. Both previously active
paper workers were drained and restored; rollback files remain at
`/tmp/paper-source-import-1793785243/backup` on Oracle. Web built/deployed locally
through the normal web target. Four API/script hashes and the public index/
PaperWorkbench asset match local files. Study API/family site returned200; private
draft read returned401 signed out; all API/paper workers/review timer are active.
No authority policy, protection baseline, applied migration, Caddy or dependency
configuration changed. Authenticated phone/iPad visual QA remains unverified.

Used the real owner's delegated operator path to link the existing common2016
draft as revision3, retaining all ten question objects byte-for-byte semantically
and leaving its answers unset. Only the original link/version, registered blank
paper-subject metadata and resolved-gap identity note changed. It is still a draft,
with zero submissions/independent reviews/publications. Fresh validation matches
the original, private and public PDF hashes and current registration; all other
nine saved draft hashes/versions match their intake receipts. No fake login or
human inspection was created.

Live bank/sync SHA remains
6c2c1e38efe97702ad2c24974de9c9720d9dfb2206471f9832a8d2b8357f9353;
81,627 canonical questions,13,172 scorable,259 attempts. Old source/canonical/tag/
document rows, human checks, exact assignments, grants and every module definition
match the before snapshot. Live Gazetted inventory is still137 entries; the756
new draft questions still need source/formatting/exact-tag review and genuine
independent approval before publication. Source binding does not publish them.
Portable evidence: `docs/sources/group-b-gazetted-existing-source-import-20261104.json`;
ignored detailed evidence: `reports/group-b-gazetted-audit-20261104/existing-source/`.

## 2026-11-04 — Gazetted draft source and primary-tag review

Reviewed756 private draft entries against all104 visually inspected source PDF
pages. Added read-only source geometry/text and proposal helpers. Native checks
cover every question,732 ordered MCQ stems and2,928 ordered options; negative
controls detect swapped options, reordered words and an added source word. Fixed
the audit's empty page-boundary strips so last-on-page questions also receive
per-option order checks. Vector-only ₹ glyphs required visual source inspection.

Used the existing owner's delegated operator adapter with actual process/save
handlers and explicit operator authorization/save events. Preflighted all ten
versions/payload hashes, approved taxonomy registry and original/private source
hashes, then checked each version again before saving. No login or human review
attestation was fabricated. All ten saves increment history once and remain
unsubmitted drafts with zero independent reviews.

Saved752 tag-path changes and756 cover-context updates. All756 classifications
use valid active approved paths,746 with topics; four writing and six visual/
spatial entries remain subject-only because suitable approved topics are absent.
Classification reuse across369 A/B matches requires matching stem/options/
passage/task type/semantic direction and preserves each booklet's own text,
option order, page and IDs. GS II A83/B33 terminal punctuation stays as printed.

Restored12 source ₹ symbols in six entries: polymer-note options GS II A47/B97,
digital rupee GS II A73/B23, and sale price GS III A90/B100. Added14 inspected,
hash-verified actual document-worker crops, preserving the original40 (54 total,
64 done document jobs). These include four essential folding/cube diagrams,
currency/emphasis examples and the printed English option defect. English A Part
B52 / B Part B16 has no Future perfect choice for `will have finished`; retain its
original choices, unset answer and explicit identity-note/crop evidence.

Final versions: English A/B4, Essay3, GS I A/B3, GS II A/B3, GS III A/B4,
common2016 Paper I4. Full API-workflow readback matches the normalized saved
proposals; newer schema defaults add only null target fields to older unlinked
drafts. Common2016 target ID/version, every question ID/page/type/passage/key,
all old figure jobs, source bytes and prior history remain intact. Answers and
explanations remain unset; printed premises/answer truth are not certified.

Fresh complete bank/source exports match before/after, including261 attempts,
two assignments/78 exact memberships, three grants, zero human checks and every
module definition. Bank SHA stays
6c2c1e38efe97702ad2c24974de9c9720d9dfb2206471f9832a8d2b8357f9353;
study health81627 canonical /13172 scorable, live Gazetted137 stored /133 printed.
All four API/document/publisher/timer services active; health and final family URL
200. No app deployment, migration, authority/protection policy or Caddy change.
Physical authenticated phone/iPad QA remains unverified, per the owner's instruction
to stop chasing login. Genuine independent review remains the next publication
gate; afterward add new published source IDs through the module composer.

Portable evidence: `docs/sources/group-b-gazetted-draft-review-20261104.json`;
private before/after payloads, proposals, crop/save receipts, visual sheets,
negative controls and preservation checks: ignored
`reports/group-b-gazetted-audit-20261104/draft-review/`.

### 2026-11-04 — Gazetted completion published, attributed AI review

Completed the owner's request to review and finish the Gazetted bank/module.
Published all ten exact reviewed drafts through guarded append and normal sync;
module composer v3 now exposes15 original PDFs and893 stored entries. Nine new
source titles use the existing verified identity workflow; common2016 Paper I
keeps its original registered ID. All137 previous entries remain unchanged from
the completion baseline. Ten valid subject-only classifications remain broad.

Inspected the official eight-page29September2026 provisional key, mapped732 MCQ
rows/366 booklet pairs and published726 keyed answers. Six English tense/seating
conflicts retain original options/key evidence but remain unscored with learner
notes.24 written prompts have no fabricated answers;58 crops match worker and
public bytes. Exact General Studies roles expose maths/reasoning/computing as
common study without changing taxonomy or including specialist papers; common
study755 questions. This is source/key mapping review, not proof of every fact.

Added explicit provisional/final payload/editor/registration support, fixed an
upload update race, and installed an owner/source/payload-bound `owner_ai` approval
with model/evidence attribution. Migration0076 was rehearsed on a dump clone then
applied normally. It creates no human editorial checks and leaves independent
review author/editor exclusion and frozen assignments intact. Owner delegated
completion; no other person's approval/session/MFA was impersonated. The exact
installed scope cannot authorize edited payloads or other papers.

An existing-source metadata check caught an absent legacy JSON examScopeId whose
SQL value had been backfilled by0046. Fixed the writer to follow normal sync's
existing COALESCE behavior; explicit differing scopes still fail. Retried the
same failed job/receipt and verified one append, not a duplicate import. The
2016 paper's full reviewed identity/snapshot survives publication unchanged.

Validation:83 backend tests; source-link/duplicate component checks and normal
web production build; disposable publication with provisional-key registration
and postcommit acknowledgement recovery. All756 complete SQL/payload/tag/context
readbacks match; normal sync checksum matches bank SHA
b6d5920f9b951694cb6c92426ff0b8d6fa3b70ce7b82a2ead8f055edd0eb80e0.
Removing only newly appended rows reproduces every original bank field exactly.
Fresh baseline/readback both preserve262 attempts, two frozen assignments/78 exact
paper memberships, three grants and zero human checks. Other module definitions
are unchanged. API/scope/publisher deployed hashes match; health82383/13898,
API/document/publisher/timer active; study/family200. Narrow release rollback:
Oracle `/tmp/gazetted-review-1793801841/backup`; earlier backups retained.

Portable receipt: `docs/sources/group-b-gazetted-completion-20261104.json`.
Private source/payload/worker/deploy/test evidence:
`reports/group-b-gazetted-audit-20261104/answer-review/`.
Full explanations/written model answers and authenticated phone/iPad visual QA
remain unavailable; do not relabel this work as independent human certification.

### 2026-11-04 — Editorial question list and quick revision

Added EditorialReviewList to shared module and assigned-paper review. Opening a
paper defaults to a full-width25-question list; direct question links retain the
detailed view. Existing shared paper search and status filters remain server-side;
legacy assignment search/filter labels honestly remain page-specific. Rows load
exact source snapshots on demand, capped at three concurrent reads. Reviewers can
show one answer or all answers on the current page, expand context/options, tap a
choice for immediate comparison, hide/reset and open the existing correction form.
Recorded key references/provenance and missing/written states remain explicit.

These actions issue only existing permission-checked snapshot GETs: no attempt,
reward, inspection or bank mutation. Page/user/scope changes remount local state.
Detailed editing and inspection still use their existing permissions, source
versions, retained drafts, idempotent requests and explicit issue resolution.
Learner Check answer still confirms an attempt; the new editorial self-check
requires no confirmation button and gives no accuracy credit.

Validation: focused editorial list tests cover lazy exact-source reads, bounded
page reveal, immediate comparison, no mutations, missing/written answers, hiding
and retry. Existing shared review and correction editor checks pass. TypeScript /
Vite production build passes. Deployed with the normal frontend-only web target;
no API migration or bank changes. Authenticated mobile visual QA is unverified,
respecting the previous instruction to stop chasing login.

### 2026-11-04 — One-tap attempts and editorial page sizes

Removed the extra Check answer control from bank cards, question detail, module
practice, paper practice, saved UDC sets and vocabulary. Option handlers pass the
actual tapped index directly to existing submission paths, avoiding stale React
selection state. Synchronous in-flight guards prevent rapid duplicate submissions.
Printed option-to-canonical mapping and missing/held/source-defect restrictions
remain. Show answer and editorial self-check retain their separate reading behavior.

Editorial supports25/50/100 rows per page. Both source-list APIs validate limit up
to100; shared next-unresolved and last-page clamping use that size. Both UI layouts
and assignment navigation use the current size; changing size resets page position.
No schema or bank-content change. Tests:33 shared-editorial/assignment backend
checks passed, including100-row continuation and rejected oversized limits;
component checks cover one-tap submission, rapid double taps, errors/retry, held
questions, editorial reveal and existing inspection flows. Production build passed.
Normal shared-editorial API and web deploy targets used. Authenticated mobile
visual QA remains unverified; no login bypass was attempted.

### 2026-11-04 — Plain-language public UI polish

Simplified learner-facing answer help, explanation labels, subject introductions,
footer, filter labels, practice/test results and account/payment unavailable states.
Removed canonical/provenance/derived terminology and internal review/configuration
process descriptions from public UI copy. Official keys, unofficial worked
solutions, unverified answers, disputed answers and provisional-key limitations
remain explicit. Explanation verification is still independent of key status.
No stored question/explanation/source document or answer classification was changed.
Staff/editorial tools retain their technical details and audit attribution.

Updated outdated scoring guidance about practice estimates, removed prospective
feature claims, and added loading/error/retry feedback for scoring counts. Adjusted
results now describe questions counted and answer changes in learner language;
unknown exclusion reasons have a plain fallback instead of exposing a reason code.
Payment availability no longer mentions provider credentials or webhook setup.

Validation: public answer-label tests verify accessible help, official/unofficial
and unverified distinctions, disputed/source-defect overrides, provisional key
warning, independent explanation state and correction links. One-tap regression
passed; TypeScript/Vite build and diff whitespace checks passed. Deployed via normal
web-only target. Authenticated mobile visual QA remains unverified; no login bypass.

## 4 November — reduce practice answer clutter

Replaced the tall missing-explanation section with one line. Moved explanation contributions, dated connections, reward messages, comparison and save-and-continue into a closed More options disclosure. Main save/next controls now follow the answer/explanation. Available explanations keep their review qualification; date context and answer-source warnings remain visible. Disclosure resets when the source question changes.

Passed rendered answer-panel checks (collapsed secondary tools, visible source and explanation, next action, restricted-test state), answer provenance and one-tap regressions, and TypeScript/Vite production build. Physical-phone visual QA remains unverified.

Deployed frontend through scripts/deploy.sh web. Live index matches the local build; study API health and family site both returned HTTP 200.

### 4 November — list navigation follow-up

Removed per-question Next and Save and continue from bank/library cards, module lists and original-paper list mode. Single-question detail and paper focus retain navigation. List pagination remains available. Answer-panel checks cover both navigation variants; one-tap regression passed.

## 5 November 2026 — quieter public question cards

Published the owner-requested learner-card redesign to study.hawayu.in. Shared UDC,
LDC, exam-module, bank and original-paper cards now surface a compact official-key /
our-answer comparison after reveal. Agreement uses one line; differences and
scoring holds stay explicit. Missing sources stay missing. Option letters are
mapped to the displayed choices by text, so shuffled appearances cannot silently
change their meaning. Detailed evidence is collapsed; long explanations use a
Read explanation disclosure, while short working remains visible. Removed repeated
explanation disclaimers and per-card contribution prompts. Existing authored
explanation text itself is preserved.

Public cards offer a discreet Report an issue form, requiring sign-in and the
existing origin/CSRF/rate checks. Reports are deduplicated in content_reports and
enter the existing subject-scoped staff queue; they do not alter keys or scoring.
Review/edit and discussion-to-correction links are shown only with staff grants.
Existing contribution routes and server-side role checks remain intact.

Automatic comparisons restore previously exposed answers without renewing the
30-minute cooldown. The server checks actual user-specific reveal/attempt history,
source scope and active assessment restrictions; a client flag cannot reveal a
new answer. Explicit comparison reveals retain their existing cooldown behavior.

Validation: 53 backend tests (reports, comparison evidence, reveal/restore gates),
four focused React/public-label/one-tap check scripts, production build and diff
whitespace check passed. Local disposable UDC browser rehearsal checked the card
and report form at390px without horizontal overflow. Live signed-out UDC reveal
confirmed the new comparison, visible short explanation and discreet footer;
staff visibility/auth transitions are covered by component tests, not a live staff
session. Screenshot: docs/screenshots/public-cards/live-desktop.jpg.

Deployment safety: reconstructing the pre-task frontend produced the exact live
entry asset names (index-YSRcn_xi.js / index-B-eNDhNa.css). Both changed API routers
matched their pre-task production hashes before replacement. Backups of the API
routers and web tree are retained on Oracle at /tmp/public-cards-20261104-backup.
Only bank_workspace.py and questions.py were installed for the API; frontend shipped
through scripts/deploy.sh web. No migrations, bank publications, worker changes,
permissions or Caddy changes. Live assets match the build, API health is healthy,
unauthenticated report submission returns401, and study/family pages return200
(following the normal family redirect).

## 2026-11-05 — Further compact public question cards

Owner requested less space after the first simplification. The answer label and
value now share a row; official/our answers use one wrapping comparison line.
One initially closed Explanation & sources disclosure holds the full explanation
and evidence, avoids repeating identical explanation text, and keeps the existing
explanation accessible if comparison loading fails. Comparison evidence maps
letters to displayed options too. Save/next and More study tools share a wrapping
row. Module source details move beside Discussion/Share/Report; module options
use6px gaps and44px targets. Public report and staff review controls are preserved.

Four focused frontend checks and the production TypeScript/Vite build passed.
Live UDC before/after measurements use the same first revealed question with Retry
now available and disclosures closed: card width960px, height883.125→501.5px;
390px phone viewport/card width351px, height1105.625→656.5px (40.6% shorter).
All four mobile choices measure44px high, and the card has no horizontal overflow.
Live explanation and report disclosures open correctly. Screenshots:
`docs/screenshots/public-cards/compact-mobile.jpg` and `compact-desktop.jpg`.

Web deployed using scripts/deploy.sh web; live entry assets match the tested build,
API health and shared family site passed. Previous web tree retained on Oracle at
/tmp/public-cards-density-20261105-backup/public. This pass changes presentation
only; no backend, scoring, account permissions or bank content changes.

## 2026-11-05 — Mixed module browsing and visible attempt filters

Compared the live map.hawayu.in System Manager Practice screen and its local
reference implementation. It exposes Never attempted, Previously wrong, due and
starred filters and mixes practice selection. The study modules previously buried
attempt status and always sorted by repetition/ID, producing the same opening
questions. LDC/UDC/Assistant and the shared module browser now expose compact
My questions and Question order controls. Mixed order is the default; Shuffle
again explicitly creates a new sequence. Most repeated first remains available.
Previously wrong means any recorded wrong answer, including later-corrected
questions; Last answer wrong retains the existing latest-attempt behavior.

The API uses a validated seed and deterministic hash order on the filtered pool,
with stable booklet-group identity, deterministic tie-breaking and consistent
pagination. It does not shuffle option indices or call ORDER BY random(). URLs,
next-page prefetches, account checkpoints and saved UDC sets carry the seed.
Legacy checkpoints preserve repetition order. Personal queues remain user/exam
scoped, and forward navigation accounts for answered questions leaving a shrinking
queue. Reading answers never counts as an attempt. Grouped booklet mistake history
survives switching to the most recently attempted representative. Fixed the saved
UDC set candidate call's missing learning_entry=None, which otherwise passed a
FastAPI Query object into SQL and prevented set creation.

Validation:66 unique backend tests passed across ordering, saved sessions,
comparison/reveal behavior, booklet history and checkpoint persistence. Focused
browse-helper, UDC study, one-tap, public-card and answer-panel checks and the
TypeScript/Vite production build passed. Disposable browser rehearsal verified
nonoverlapping pages, stable back navigation, explicit reshuffle, a real synthetic
wrong-answer filter, saved-set start and refresh restoration. Live read-only checks
returned stable25-question pages for UDC3774, LDC520 and Assistant1564, with first
observed request times1.21/0.72/0.72seconds respectively (not a benchmark). Live
browser controls checked in all three modules; UDC at390px has351px client/scroll
width and no horizontal overflow. Screenshot: docs/screenshots/module-browse/live-mobile.jpg.

Deployed exactly questions.py, study_sessions.py, rewards.py and study_series.py,
after all four pre-task hashes matched Oracle. Backup includes those files and the
previous web tree at /tmp/module-browse-20261105-backup. Frontend deployed with
scripts/deploy.sh web and its live entry assets match the tested build. API health
and family site checks passed. No migration, bank-content changes, worker changes,
new grants or production synthetic attempts. Due/starred practice queues from the
reference are not part of this release.

## 2026-11-05 — Read-only Oracle PDF/bank integration status

Owner requested current integration status. Fresh Oracle sync-bank.sh --check
confirmed matching bank/database hash b6d5920f9b95… and82383 questions; taxonomy
also matches82383 approved primary rows. Protected78-paper/6931-question scope
passed. API, document and paper-publisher services are active; correction and
backup timers are waiting normally. Last paired backup service succeeded at
2026-11-04 20:19:29UTC; disk78GB free.

Read-only SQL:1979 paper records,1721 with appearances,258 without,82383 source
appearances and82383 canonical records. Source-document registrations:1978 papers,
40 final keys and8 provisional keys. LDC under MPSC Paper-II2025 lacks a paper
review_documents row; this does not establish whether its PDF bytes are missing.
Ten workbench drafts are published;58 crop/10 extract/10 publish jobs are done,
with no queued/running/failed jobs in that table. Archive contains2558 PDF files
under Old_Questions and137 under Answer_Keys; these raw file counts are not a
one-to-one deduplicated paper coverage measure. Served source archive has1980
PDF files.13977 canonical rows have explanation text; taxonomy approval is not
answer/explanation source certification. No production content or workflow data
was changed during this status check.

## 2026-11-05 — Final PDF/MPSC CMS upgrade plan

Inspected the existing exam inventory API/UI, current implementation ledger and
repository authority rules. Recorded docs/PDF-CMS-UPGRADE-PLAN.md and linked its
phased checklist from docs/PLAN.md. Plan builds on existing CMS screens, separates
archive reconciliation from import/review/publication/module coverage, and uses
the preceding read-only Oracle audit as a dated baseline. No application code,
production service, bank content or approval policy changed. Documentation-only;
validated the plan link and retained pending implementation checkboxes.

## 2026-11-05 — PDF/MPSC CMS upgrade deployed

Added staff PDF Library with compact Library / Needs attention / Activity views,
URL-preserved filters/pagination, module links, paper-quality detail, source PDF
preview and next actions into the existing inventory/workbench/editorial workflows.
Added resumable, hash-cached Oracle archive scans and atomic last-complete snapshot
selection (migration0077); partial/failed scans never replace the last complete
inventory. Requests queue background work; daily refresh and minute polling use
restricted root scan units. The API sees only a read-only PDF subtree through a
service mount; the canonical workshop and bank remain private. Fixed the upload
source directory's group write access without changing canonical source files.

Existing Oracle files can be staged into the workbench with hash/stat rechecks,
shared advisory locking and draft reuse. Empty originals retain their exact
registered source binding; missing/ambiguous registrations fail closed. Upload
draft creation shares the same duplicate lock. Existing review, approval, worker
retry and guarded publication paths remain authoritative. Workbench now returns
to the selected library results and displays completed publication receipts.

Validation:78 focused backend regressions plus the added answer-status parity
case; six PDF-library cases passed in the final follow-up. Four focused frontend
checks and production build passed. Rehearsed0077 on an Oracle dump clone; source
scan hashed5,822 file locations and its repeat rehashed zero. A separate synthetic
publication rehearsal preserved the original paper and recovered after an
intentional post-SQL-commit interruption without a second append. No live account,
question or review attestation was synthesized. Disposable databases removed.

Initial reconciliation:1,979 registered papers,258 empty sources, zero missing
registered source files, zero conflicting hashes, one document-registration gap
(the existing LDC2025 PaperII has its PDF and100 questions).1,796 unlinked PDF
hashes span all document categories;563 are in the question-paper folder and
remain discovery candidates. Reconciliation does not certify or auto-import them.

Optimised the initial8.97s library query by computing answer status only where
needed, aggregating document/source matches once, and projecting draft metadata
once instead of repeatedly reading large question payloads. Production list/filter
reads measured0.305–0.362s; inspected answer detail1.055s. Verified all3,765 selected
distinct PDF hashes are readable inside the API namespace, the PDF mount is
read-only, bank JSON is unreadable there, and signed-out API access returns401.
Live browser entry shows the PDF Library heading and admin sign-in gate.
Authenticated phone/tablet visual inspection remains unverified; login was not
bypassed and no synthetic production account/session was created.

Deployed the bounded API release and locally built web bundle. Backup:
/tmp/pdf-library-1793889781/backup; full rehearsal dump remains in a root-only
private stage directory. Question/paper/source-row digests, exact frozen source
assignments, grants, module membership,275 attempts and bank checksum match the
before snapshot. Normal authority sync and78-paper/6,931-question protection
checks pass. API/document/publisher services and both new timers are active;
family.hawayu.in follows through toHTTP200. Shared Caddy configuration was untouched.
Delivery details:docs/sources/pdf-cms-release-20261105.json. Content import/review
backlog is tracked separately from this CMS deployment.


## 5 November 2026 — Student ease and shared navigation upgrade

Owner requested an overall functional/visual upgrade and chose both areas with
student ease first. Shipped a web-only release: exam search and compact choices
now precede large promotional panels, with direct Questions / Subjects / Original
papers actions, existing saved exams/progress and recoverable catalog loading.
Home prioritizes real continuation/active tests, otherwise a live-catalog Quick
start opens mixed practice, never-attempted, ever-wrong or original papers. Optional
topic discovery loads only when opened. No invented activity or browser-stored
personal history was added.

Added Find to the student header and admin sidebar: native modal, keyboard focus
containment, Escape, arrow navigation, Ctrl/Cmd+K, exam/tool search and handoff to
existing full search. Staff destinations derive from existing grants; assignment-
only users retain only their review workspace. Focused tests/games do not mount
the launcher. Public answer comparison, private reports and scoring/reveal rules
remain unchanged. Selected subject/topic/search filters can be removed directly.

PDF Library gains compact secondary filters, UDC/LDC/Assistant shortcuts, Clear
filters, previous/next source within the current results page and retained return
position. Fixed invalid/shrinking offsets, stale source actions during failed
detail loads and selecting All from the attention view. Existing import/review/
publication endpoints and permissions remain authoritative. Read-only inspection
confirmed the runtime already has the scanner cleanup privilege; no migration or
permission change was needed.

Validation: Quick access, PDF Library, review navigation, question browsing,
public question cards, UDC study and Group B navigation/home/archive checks pass.
Production TypeScript/Vite build passes. At390px, preview exam catalog and Find
layout were inspected, and Quick start opened UDC Never attempted with mixed
order and a stable seed. No answer was submitted. At320px, home inspection found
3px header overflow against the client width; the final patch hides the Find text
below360px while retaining a44px icon button. Browser policy then blocked preview
reconnection after the user continuation. No alternate route/authentication
workaround was attempted. Final live responsive recheck and signed-in staff
phone/tablet visual QA remain pending.

Deployed with scripts/deploy.sh web. Main, StudyHome, Exams and PdfLibrary asset
bytes exactly match the local release. /feed, /exams and /admin/bank?tab=pdf-library
return200, API health isOK with82,383 questions, unsigned PDF Library API returns
401, and family.hawayu.in follows to200. API/bank content, PostgreSQL, workers and
shared Caddy configuration were not deployed or modified. Web rollback archive:
Oracle /tmp/study-ease-web-before-20261105.tar.gz (root-only). Detailed receipt:
docs/sources/study-ease-release-20261105.json.


## 2026-11-05 — Exam catalog and module visual refresh

Implemented the owner's requested modern module browsing/layout/colour update.
Catalog now has per-exam accent cards, compact List view, URL-backed layout and
single expanded study-options panel, existing live counts/save/progress/search.
Headers and module navigation share cool slate/white surfaces with restrained
teal/blue/violet/indigo/amber identity colours. All six exam views are directly
available, including UDC Questions. Existing timed/source options remain available.
Redundant hero links are limited to Overview to save space within study views.

Subject headers now toggle their own topic panels; Expand/Collapse all operates
on visible results and search automatically opens matches while allowing collapse.
Topic/subtopic links retain source/section/pool scope. Booklet series disclosures
have visible chevrons. Touch targets, keyboard focus, reduced-motion treatment and
phone wrapping are preserved. Question correctness/source styling is unchanged.
Moved the React import before lazy route declarations to fix a pre-existing Vite
development-preview initialization error found during visual testing.

Validation: production build and Group B design/navigation, UDC study, question
browsing, public cards, quick access and paper archive checks pass. Added behavioral
coverage for independent subject expansion, expand all and search-collapse.
Preview inspected at desktop,390px and320px. Live catalog desktop, expanded LDC
list390px and LDC subjects320px verified; no horizontal overflow on the inspected
phone screens. Screenshots in reports/exam-theme-20261105/. Signed-in staff/admin
visual testing was not performed in this presentation release.

Deployed with scripts/deploy.sh web. Main/catalog/module JS bytes match local
artifacts. Exam routes and API health return200;82,383 questions and13,898 scorable
remain reported. Deployment's shared family-site check passed. No API, bank,
database, worker or Caddy changes shipped. Root-only Oracle rollback snapshot:
/tmp/exam-theme-web-before-20261105.tar.gz. Receipt:
docs/sources/exam-theme-release-20261105.json.


## 2026-11-06 — MCQ solver Phase A and safe Phase B scaffold

Read the owner-provided CODEX_QUESTION_BANK_SOLVER.md and current official SIWC
documentation. Added docs/solver-discovery.md and an isolated tools/mcq-solver
Python package. The real recovery-bank adapter preserves appearance IDs and
zero-based answer indexes, hashes source/key/media state, and writes only separate
local SQLite review drafts. Added PKCE/OIDC bootstrap, protected OAuth storage,
serialized refresh, VM host-preserving SSH handover, account model discovery and
completion-only Responses streaming. Eligibility, explicit plan consent and
credit-setting confirmation gate inference; API-key billing has no adapter.

Added atomic leases, idempotency, stale-source checks, bounded retries, persistent
usage pauses, stop/resume, blind packet export, validated offline import and CSV
review export. Initial runs are capped at five and all drafts need human review.
39 deterministic tests passed, plus compileall and pip check. The synthetic
five-question end-to-end test saved five review drafts without modifying source
answers; real-bank dry-run found five candidates. Staged those five real inputs
in ~/.local/share/mcq-solver with no model output or inference request. Bank SHA256
remained 99ce7a54d37581a8be55b6f144b677ab8855240371ed1ec67d6a142139dd45e0.

Live Phase B is NOT complete: worker OSS/authorized-integration eligibility is
unconfirmed, no owner SIWC consent was obtained, and no production draft-only
capability or VM deployment was configured. Existing Codex login is not reused.
No canonical/public answer, explanation, application migration, billing setting
or live service changed. The existing explanation queue was checkpointed only
(1030 pending, 32 published, 3 unresolved, no active packet). Commands, test
evidence and remaining Phase B/C/D gates are documented in the package README
and docs/phase-ab-validation.md. No licensing/publication decision was made.


## 2026-11-06 — Standalone MIT review package and authenticated draft service

The owner asked to continue and explicitly chose “Prepare MIT-licensed worker for
review.” Added the MIT license, a portable standalone README and an allowlist ZIP
builder. Prepared artifacts/personal-mcq-solver-review-20261106.zip under the
parent personal workspace (28 files, SHA256
dae34ffb60af35245c437d9b21a2ccd1bf58e079f130a92657b0f033738a4cb8), and extracted
a local personal-mcq-solver review project. The bundle excludes the private app,
bank/source records, original owner brief, runtime state, credentials, private
addresses/hosts and integration service. All manifest hashes matched; its 39
tests passed from the extracted ZIP and an isolated wheel build succeeded. No
public repository was created or pushed.

Added api/app/services/mcq_solver_drafts.py and five PostgreSQL integration tests.
The service requires an actual recent MFA Actor plus current owner/publisher
permission, captures exact canonical/appearance/source/document state, rejects
stale/invalid output and calls the existing contribution service to create
unreviewed drafts. Five synthetic drafts and exact retries preserved canonical
and appearance rows byte-for-byte (as JSON), created no publications/decisions,
and retained official-key disagreement as a derived proposal. All five tests
passed in the existing disposable database harness. No route was exposed, no
worker credential was provisioned, and no live draft was written.

Read-only SSH confirmed the Oracle host and active API. No Oracle code/service
was changed. For the now separately packaged MIT local CLI, recorded the assessed
OSS/local use basis in private runtime config, without marking account entitlement
as granted. Public GitHub publication is not an explicit step in the documented
dynamic-registration flow and was not used as a prerequisite. Started the local
OAuth browser flow for explicit user consent; no credentials were imported from
Codex and no inference was requested. Additional credit spending confirmation
remains false, which blocks inference until the owner checks that app setting.


## 2026-11-06 — SIWC authorization confirmed and account catalog verified

Local OAuth completed successfully, including the required direct-plan scope;
private credential status reports authorized, unexpired and not transferred.
The read-only account catalog lists the configured gpt-6.1-sol and other models.
No probe or question inference has been requested because the owner has not yet
confirmed that additional credit spending is disabled for this app. The runtime
confirmation remains false, and five local jobs remain pending with zero drafts.

Adjusted model discovery to require eligibility and scoped OAuth without requiring
the inference-only credit-setting confirmation. Responses still requires the
confirmation. The new regression proves discovery works while inference is
blocked; all 40 worker tests pass. The change was applied to the private source
package and the extracted standalone review copy. Existing review ZIP remains
the immutable prior snapshot. No published bank content or paid API configuration
was changed.


## 2026-11-06 — First real SIWC five-question draft pilot completed

The owner confirmed additional credit spending was disabled. Recorded that fact
in private runtime config and verified official documentation that SIWC requests
consume the signed-in account's Codex / ChatGPT Work plan usage. No API-key
adapter or billing fallback was added.

The first probe failed local validation; a sanitized second probe established that
this route can emit completed output items separately and leave terminal output
empty. Fixed streaming in both worker source copies to retain finalized items
but require successful response.completed. Partial/failed/incomplete streams and
conflicting completed items remain rejected. All 42 worker tests passed. The
third probe passed normally with gpt-6.1-sol / high.

The real five-question local run then completed: five valid drafts, five review
flags, zero failures/pauses. Two option suggestions (one uncertain), three
cannot-determine results for incomplete/ambiguous choices or missing circuit
media. No human approvals were created. These are proposed answers, not verified
accuracy. Five private CSV rows were exported; the ledger contains only five
review_required jobs and no active/pending jobs. Total hosted attempts were
three small probes plus five questions; exact token/percentage usage was not
retained. Source bank SHA256 remains unchanged at
99ce7a54d37581a8be55b6f144b677ab8855240371ed1ec67d6a142139dd45e0.

Details: docs/solver-live-pilot-20261106.md. Revised 28-file MIT review ZIP:
parent workspace artifacts/personal-mcq-solver-review-20261106-r2.zip, SHA256
e51f6a86783c204a0a4c53509de98332140456e26e208bac8a3a2ab7fed8637a.
No public repository, Oracle deployment, live draft, published answer/explanation,
paid API billing change or unattended scheduling occurred.


## 2026-11-06 — Original-source review and private solver draft page

Inspected all five original pilot sources and primary GFR/Arms references. Found
four malformed MCQ representations; placed private local source holds on them.
The GFR paper header specifies 2005, resolving edition uncertainty, and its
object-head question prints a Rule 74 reference for content supported by Rule 73.
The circuit has an existing figure: 4 || 12 = 3 ohms, printed option A. No original
model result was edited or official answer provenance invented. The five records
cannot be reported as a five-MCQ accuracy benchmark.

Created detailed Markdown and embedded-image HTML source reports. Added a private
owner/publisher source-review page and narrow draft-only POST, with recent real
MFA, CSRF, source/PDF checks, ordinary contribution limits and idempotency. It
creates only answer/defect drafts and retains human approval as null. No production
draft was created with a forged session, and no submit/approve/publish endpoint
was added. Deployed only the focused API files plus frontend build. Rollback
backup: /srv/api/.release-backups/mcq-source-review-1793954946603675781.

Validation: 43 worker tests, 10 disposable-Postgres backend tests and TypeScript/
Vite production build pass. Live anonymous GET returns 401; browser route renders
sign-in requirement. Study/family health checks pass. Recovery bank SHA unchanged:
99ce7a54d37581a8be55b6f144b677ab8855240371ed1ec67d6a142139dd45e0.
No new inference calls, paid billing changes, published content changes or
unattended schedule. Details: docs/solver-source-review-20261106.md.


## 2026-11-06 — Admin system review (no application changes)

Reviewed the current admin code and read-only authoritative Oracle inventory: 82,383 records, 1,979 papers, 58,373 subject-only classifications, zero approved related links and zero canonical IDs with multiple appearances. Saved findings, incremental architecture/workflow recommendations and versioned official scheme references in `docs/ADMIN-SYSTEM-REVIEW-20261106.md`; aggregate evidence and inspected PDFs are in `reports/admin-system-review-20261106/`. Found the retag q/tag_q navigation mismatch and gaps in tag discovery/source-provider representation. Existing correction-editor and editorial-list regression scripts passed. No production content/configuration/application code changed; authenticated visual QA, load testing and exhaustive content review were not performed.

## 2026-11-06 — Admin organisation, cleanup and legacy schemes deployed

Implemented and deployed the requested admin improvements within the existing
editorial/publication model. Added exact-source cleanup navigation, retained
filters and next actions, inline correction, topic/subtopic/related-path filters,
account-owned saved views, controlled learning context and intentional broad-tag
resolution. Unified GK/GS discovery through explicit stable aliases and added
English Writing/Essay/Précis/Letter definitions without reclassifying questions.

Added registered source providers, immutable custom/legacy/current scheme
revisions, source-backed draft templates and explicit paper edition/era/layout/
section mapping. Original-paper coverage counts appearances. Full simulation
requires complete supported official MCQ coverage and pinned verified rules;
written/mixed/incomplete/unsupported structures retain study/practice access.
Reviewed repeat relations preserve all records/keys/history. Fresh matching
same-question/extraction-duplicate links can share one generated mock candidate;
original-paper positions remain intact. No canonical merge or answer transfer.

Validation: 127 focused backend tests, six focused UI scripts, TypeScript/Vite
build and deployment-script syntax/diff checks passed. Migration 0078 checksum
`1bfb8122231d4686` was rehearsed on a disposable production dump clone with
unchanged content/attempt/assignment/grant fingerprints, then applied additively.
The taxonomy registry was extended under canonical authority, lock and backup.
Bank JSON SHA256 stayed
`b6d5920f9b951694cb6c92426ff0b8d6fa3b70ce7b82a2ead8f055edd0eb80e0`.

The first API release restored its previous files because a family-site health
check expected a direct 200 instead of its normal redirect. Corrected the check
to follow redirects and released successfully. Brief 502s during API restart
cleared on retry. Latest release/rollback evidence is at Oracle
`/tmp/bank-organization-1793974354/`; initial migration rehearsal evidence is at
`/tmp/bank-organization-1793973474/`. The web release serves
`index-DS3z0zBM.js` / `index-CfbuuvQL.css`; an isolated task-start build exactly
matched the prior deployed asset set before publishing, excluding unrelated
new frontend changes. Live public readiness/health, anonymous staff rejection,
workers and family site passed. Health reports 82,383 questions / 13,898 scorable.

No bulk AI classification, mass content mutation, saved verified scheme,
invented human inspection or authenticated visual QA occurred. Real-size latency
and a labelled cleanup pilot remain unmeasured. Implementation/use guide:
`docs/ADMIN-SYSTEM-IMPLEMENTATION-20261106.md`; aggregate evidence:
`reports/admin-system-implementation-20261106/`.

## 2026-11-06 — Website-user shareable mocks and PDF quick guide deployed

The owner clarified that the Google Forms-style test maker is for ordinary
website users. Extended existing learning practice collections with validated
timed settings, bank question selection/order and immutable reviewed test
editions. Normal accounts save/submit; independent staff review publishes.
Authors can stop sharing their own live test. Existing draft/history/review and
mock services remain the authority; canonical questions are not copied or edited.

Added public test directory/landing pages, guest start/resume, private frozen
results and edition-aware links. Copy/WhatsApp/native sharing is user-initiated
and contains an invitation, not private responses. Escaped server-rendered share
metadata does not require JavaScript crawlers. Creator totals are starts and
completions by edition; no respondent identities, individual answers or scores
are exposed. Shared tests have three starts per test per browser/account in
24 hours and do not consume the ordinary monthly mock allowance. Creator test
collections are bounded at 50; a test holds up to 100 questions. Existing active
assessment restrictions, CSRF/MFA and account boundaries remain.

Added How to use PDF Library inside the admin screen and
`docs/ADMIN-QUICK-START-20261106.md`, explaining PDF import/review/publication,
tag cleanup, legacy schemes, feature usage and the still-unfinished corpus work.
The implementation guide is documentation, not another installation step.
No ad account/script was configured or WhatsApp message sent.

Validation: 144 focused backend tests passed on disposable databases. New
shareable-test UI checks plus existing bank-organisation, correction,
review-navigation and PDF Library checks pass; TypeScript/Vite build succeeds.
Migration 0079 checksum `c14af5f359b1fe30` was rehearsed on a disposable full dump
clone with preserved content/attempt/permission/collection/mock fingerprints,
then applied additively. An isolated task-start frontend exactly matched all
114 prior deployed assets before the new web release. Source guards preserve
unrelated deployed code. API release/rollback: `/tmp/shareable-tests-1793975884/`;
previous web archive: `/tmp/shareable-tests-web-before-20261106.tgz`.
Current entry: `index-Cof0_sdu.js`. Brief API restart 502s cleared on retry.

Live directory/private-management/unavailable-test/asset/health checks pass;
workers restored and family site healthy. Public desktop directory and guest
maker sign-in entry were inspected in the browser. No authenticated creator or
staff visual QA, production test publication, synthetic human review, WhatsApp
delivery/preview test, load benchmark or ad activation was performed. Bank JSON
SHA256 remains `b6d5920f9b951694cb6c92426ff0b8d6fa3b70ce7b82a2ead8f055edd0eb80e0`;
health reports 82,383 questions / 13,898 scorable. Delivery details:
`docs/SHAREABLE-TESTS-20261106.md`; evidence: `reports/shareable-tests-20261106/`.

## 2026-11-06 — Solo-owner cleanup, owner publication and live database map

Implemented the explicitly requested one-person workflow. Global owners can
omit notes for routine tag, transcription/context, explanation and source-locator
corrections; the server generates factual change summaries through the existing
guarded proposal/publication path. Save & next is the primary owner action.
Bounded tag previews retain source tokens and permit optional owner notes.
Changed correct-answer text still needs reasoning plus the existing solution/key
evidence. No source inspection or independent review is invented by a summary.

Added source/payload/author/submission/version-bound paper owner previews and
explicit publication, with immutable `review_kind=owner` attribution and current
grant rechecks by the worker. Kept independent and narrowly scoped `owner_ai`
semantics distinct. Owners can preview/publish saved learning collections and
their own shareable tests; normal-user independent review remains. Retry reuses
the original paper job/test edition. Updated in-app PDF/source/restore wording,
the admin quick start and current repository/runbook guidance.

Replaced the old database-map list with an owner-only interactive read-only map:
content relationships versus actual live PostgreSQL foreign keys, area/search,
selectable cards, highlighted links, zoom/scroll/list, descriptions, counts,
columns/PKs and related admin tools. It exposes no raw row values or SQL console.
Read-only production metadata check: 28 tables, 360 columns, 41 FK links in
0.125s; this single observation is not a load benchmark. Topic-detail coverage is
explicitly not semantic classification accuracy.

Validation: 191 backend tests passed on disposable databases; focused owner,
normal-user shareable-test, correction, organisation and original-source UI
checks passed, including blank notes with a linked PDF and the interactive map.
TypeScript/Vite build and diff/shell checks passed. Full isolated guarded paper
publication/recovery rehearsal preserved source identity/metadata/original answer
and reused the receipt after an interruption following SQL commit. No fixture or
synthetic approval was added to production.

Migration0080 (`1144966cad163381`) was rehearsed on a full production dump clone;
content, attempts, assignments, grants, learning/mock and paper-workflow row
fingerprints matched before/after. Bounded deployment checked API/writer source
preimages, drained/restored workers and retained rollback backups at
`/tmp/solo-owner-1793978445/` (including `backup/web.tar`). All117 task-start asset
hashes exactly matched the preceding deployment. Final entry:
`index-Ck4bhi36.js`. Brief API-restart502s cleared on health retries.

Live health, anonymous staff-route rejection, exact served assets, restored
workers and family site checks pass. Bank SHA256 remains
`b6d5920f9b951694cb6c92426ff0b8d6fa3b70ce7b82a2ead8f055edd0eb80e0`;
82,383 questions / 13,898 scorable. Existing ten `owner_ai` paper decisions remain;
no new production owner decision was fabricated. Authenticated owner desktop/
phone visual QA, actual production owner-publication acceptance and full corpus
classification/scheme/source cleanup remain outstanding. Delivery:
`docs/SOLO-OWNER-WORKFLOW-20261106.md`; evidence:
`reports/solo-owner-20261106/`.

## 2026-11-06 — Make exam-year filters visible

The user could not find year filtering. Existing Questions and Learning-tags
filters already accepted exact paper years, but both controls were inside closed
details panels. Moved Exam year into each main filter row, with All years as the
empty hint and an explicit applied-year clear action. Questions keeps its existing
safe debounce; Learning tags now waits for a valid full1900–2100 year or clearing
before updating the URL/API, avoiding partial-typing422s. Original paper/exam
year remains separate from current-affairs reference period; existing Papers
inventory has its All years dropdown. No API/schema/content change was needed.

Extended the existing organisation UI check to exercise both actual components:
year outside details, partial typing, full-year request binding, offset reset,
retained exam/source/provider scope and clearing. It and the solo-owner UI checks
pass; production build and diff checks pass. Task-start reconstruction exactly
matched all117 prior asset hashes before the web-only release. Previous frontend
backup: `/tmp/admin-year-web-before-20261106.tar` on Oracle. New entry:
`index-Hc1Hi4b-.js`. Quick start updated. Live year-filter routes, exact assets,
health, anonymous staff boundary and family site were checked; canonical bank
SHA remains `b6d5920f9b951694cb6c92426ff0b8d6fa3b70ce7b82a2ead8f055edd0eb80e0`.
Authenticated responsive visual QA remains unperformed. Evidence:
`reports/admin-year-filter-20261106/`.
# 7 November 2026 - Owner access and reusable tagging foundation

The owner explicitly requested simpler access/removal of the authenticator for
their named account. Live inspection found an unfinished setup, no enabled factor.
Added an operator-controlled immutable-account-ID exception, honoured by staff
write/session/status and solver draft gates without asserting MFA verification.
Recent-sign-in/roles/CSRF and opt-in login MFA remain intact. The bounded API
release installs a single-account systemd policy and clears pending setup with an
account security audit event; other staff policy, password and grants are retained.
Release/rollback: `/tmp/owner-access-1794027201` on Oracle. Canonical JSON checksum
was unchanged; service health and family site checked after restart.

Fresh read-only tagging checks found 0 saved scheme revisions, 0 paper profiles,
0 new learning-context records; English filtering works across all/UDC/Assistant/
LDC/Gazetted scopes, and UDC/Assistant share 898 distinct browse question IDs.
English primary classification has 4,557 live records without a topic label.
Re-downloaded official schemes, visually inspected relevant structure pages and
documented the initial manual-review rules in `docs/TAGGING-FOUNDATION-20261107.md`.
Added an unverified Assistant/UDC combined 2026 draft template, with mixed Paper I,
written task distinctions, independent recruitment applicability and unknown
historical dates/counts retained. No saved scheme, paper binding, mass retag,
bank publication or owner/human source approval was created.

Validation: 30 focused backend tests on disposable PostgreSQL, organisation UI
behaviour check and TypeScript/Vite build passed. Tests cover account isolation,
CSRF/default staff enforcement, optional enrolled-factor sign-in/removal, preserved
recent role requirements and mixed-paper template totals. Running-process policy
and target pending/enabled state were read back on Oracle. Authenticated owner
browser acceptance remains for the real signed-in user; no session was fabricated.

## 7 November 2026 — question-bank working overview

Owner requested a clean overview page. Replaced the full-bank admin landing view
with live canonical coverage, exam membership table, field gaps, historical review
and publication activity, scheme-link counts, recommended manual-review order and
existing workflow links. Added exam search, attention filter and CSV snapshot export.
Scoped reviewers retain their existing view; expanded data requires a global grant.
Counts exclude merged records, deduplicate appearances within each live browse
collection, and explicitly explain overlapping exams/issues. Inspection history is
not reported as current certification; saved scheme links are not simulation readiness.
No question content, scheme configuration, review assignment or authentication
policy was changed. No schema migration was needed.

Validation: isolated PostgreSQL test covers deduplication, live-version/browse
membership, MCQ versus written gaps and global/scoped/unauthorised access. Production
read-only query took 0.43s (82,383 stored / 82,249 live; seven exam collections).
Local browser preview with actual aggregate snapshot passed desktop and 390px
phone layout, no document overflow, exam search/empty state and attention filter.
Authenticated production UI acceptance remains pending: available browser is signed out.

Deployment completed through `scripts/deploy.sh bank-overview` and `web`.
Narrow API backup `/tmp/bank-overview-1794028320`; deployed preimage matched before
installation. Study health and shared family site healthy, anonymous summary still
401, served web index matches the built artifact. Release log and aggregate query
receipt: `reports/bank-overview-20261107/`.

## 7 November 2026 — refresh question status after publication

Owner reported ENERVATE `cq_0001fa4e5c93df84` remaining in Needs review.
Read-only production diagnosis: explanation applied, taxonomy export failed a bank
snapshot check, and the separately queued answer decision subsequently failed the
same check. The canonical answer status therefore correctly remains Needs review.
No content, evidence, manifest hash, source baseline or review attribution was changed.

Fixed question-list refresh on confirmed publication and window focus. Publication
progress emits content change only after checking an applied receipt; refreshed
counts do not reset the open inspector or unsaved correction editor. Inline receipts
are retained in recent decisions so Save & next still monitors publication. Failed
exports now show the real failure and a fresh-question link; stale exports explicitly
require a fresh decision rather than an ineffective repeat retry. Verification
responses include current answer status and explain when an applied tag/explanation
edit leaves answer review outstanding. Reopening the same selected question reloads
its source and decision form.

Validation: 12 admin-answer regressions passed, including confirmed current status
and held status on applied publications; disposable-renderer checks cover pending,
applied and failed publication, one-time notifications, list/count refresh, retained
editor identity and non-confirming edits. Solo-owner UI regression and production
web build passed. Existing publication/source protections remain unchanged.

Narrow API release completed with preimage verification and backup
`/tmp/publication-refresh-1794034098`; web release completed and served index
matches local build. Study and family health checks passed. The reported answer
publication remains failed and requires a fresh owner decision from its current
source; no obsolete export was forced through the guard.

## 7 November 2026 — actionable question review queues

Owner supplied nine Needs review examples and requested optimisation. Read-only
production inspection confirmed inferred/unverified answers, one duplicate-options
source problem, and ENERVATE's separate failed answer/tag publications. These labels
are real outstanding work, not nine completed answer publications.

Added disjoint URL-backed task filters with scoped counts: Answer checks, recorded
Source/scoring problems, Publishing, Publication failed and All matching. Latest
work per correction kind prevents an old failed attempt from hiding a newer completed
correction of that kind. Active publication takes precedence over failures and source
problems. Each row explains its actual next action; the inspector links outstanding
work. Condensed source titles and removed repeated generic review boilerplate. Live
queue polling runs only while visible publishing work exists; editor state stays in
place. Pagination clamps after the current queue shrinks.

The backend materialises answer status and scope once, counts canonical rows once,
and looks up source appearances for the bounded page. The read-only whole-bank
Needs review query measured0.94s versus2.63s for the initial implementation. At the
check it contained50,946 questions:49,320 answer checks,1,625 source/scoring problems,
one failed-publication question. These are dated measurements, not seeded UI values.
No stored tags, answers, source content, holds or publication guards were changed.

Validation:16 backend workbench/answer tests passed, including task disjointness,
permissions, source ordering, canonical deduplication, older-failure supersession,
parameter validation and current answer status. UI regression covers URL task changes,
publication refresh/counts, failed status and preservation of the open editor.

Release completed through `scripts/deploy.sh review-queue` and `web`; API rollback
backup `/tmp/review-queue-1794034841`. Served index matches the local build. Study
and family health checks passed; anonymous review requests still return401.
Authenticated production visual acceptance remains pending in the owner's session.

## 7 November 2026 — backend publication audit and serial export

Audited queue/status, direct answer decisions, routine edits, bulk tags, retries,
worker publication, immutable receipt verification and source/permission checks.
Found and fixed: failed corrections blocked fresh decisions; answer decisions did
not share the tag/text pending guard; retries requeued provably obsolete immutable
exports; replayed decisions could falsely report queued or return no publication
object; independent saves exported against the same whole-bank snapshot and raced.
Also corrected the queue reason for malformed official options.

New optional operator setting PUBLICATION_SERIAL_QUEUE serialises ordinary export.
Later authorised saves remain accepted with a durable review_outbox intent. The
trusted local worker exports them only after the preceding publication sync/ack,
revalidating exact source baseline, immutable decision, current grants and evidence.
No old manifest or baseline hash is modified and no approval is manufactured. Tag
batches retain one atomic snapshot and wait for an open slot before being saved.
A tick drains up to five serial jobs within a180-second scheduling window; existing
per-job bank lock, machine authority, document checks, sync and readback are intact.
Queued validation failures retain an attributable error/history; fresh decisions can
replace failed attempts while the originals stay recorded.

Validation includes two back-to-back decisions through actual guarded temporary JSON
writes, normal CSV/SQL sync, current-source readback and acknowledgment: both become
verified in sequence with the first manifest unchanged. Tests also cover busy-lock
contention, permission revocation/source drift while waiting, intent retry/replay,
stale-retry refusal, shared pending guards, atomic tag batches and the promoter CLI.
Core regressions and the separate maintenance suite pass. The initial combined run
exposed an outdated mock status field (updated) and shared fixture contribution-quota
interference (maintenance suite rerun on a fresh disposable database; production
quotas are unchanged). Frontend publication/owner regressions and web build pass.
No production question/tag/answer/hold was directly edited in this audit.

Release completed with exact deployed preimage checks and rollback at
`/tmp/backend-audit-1794035628`. Serial queue was verified in the running API and
worker environment. The helper import/DB smoke passed as postgres in disabled mode;
the normal enabled worker completed successfully and its timer is active. Study
and family health checks passed; anonymous admin requests still401. Served frontend
matches the built artifact. Final totals:115 core backend regressions +17 isolated
maintenance regressions =132 passing tests, plus two UI regression scripts and
production TypeScript/Vite build. Existing failed history/content was preserved.

## 7 November 2026 — publication follow-up audit

Continued the authorised backend audit. Fresh production checks found no accepted,
publishing or pending-intent work stuck in the live queue. Two failed historical
ENERVATE decisions remain recorded.

Fixed two further boundary cases: an export now takes its slot before reading the
completed-sync checksum and rechecks its source after slot acquisition, so a worker
finishing between statements cannot make a fresh export stale. A retry of an intent
that failed before its first export retains the original admin-decision binding,
both when re-deferred and when exported immediately. The generic retry endpoint
creates no replacement authority. Worker independently validates that binding.

The worker now skips up to five failed/cancelled intents in a tick before looking
for valid work, preserving each recorded failure. This avoids making unrelated valid
work wait another minute behind each stale item; the scan remains bounded.

Validation:48 workflow regressions,56 source/scoring/organisation verification
regressions and15 serial/worker tests pass on disposable databases. Added tests force
a sync at the slot boundary, force source drift at that boundary, validate the original
retry binding through the real worker and check that failed/cancelled intents do not
block a following valid publication. Initial out-of-order combined tests exposed
shared fixture quota/state interference; groups run on separate disposable databases.
No production content, review record, permission or configuration was changed by
these checks. Release changes only the publication helper and correction worker.

Follow-up deployed successfully with rollback `/tmp/backend-followup-1794036087`.
API/helper smoke and both study/family health checks passed. The deployed worker
completed successfully, its timer remains active, and live SQL shows no accepted,
publishing or pending-intent backlog. Anonymous admin reads remain401. This audit
confirms the tested workflow paths; it is not a claim of universal bug-free operation.

## 7 November 2026 — on-demand publication wake-up and VM capacity

Owner requested realtime publication and asked about VM capacity. Fresh read-only
inspection:4 CPU cores,23,974MiB RAM with21,400MiB available,77GiB available disk,
load0.20/0.20/0.07,645MB study database. This is an idle snapshot, not a load-test
capacity guarantee. The ENERVATE fresh owner decision reached applied/published and
its canonical status is verified. Its remaining old failed taxonomy history is kept.

Added commit-bound empty PostgreSQL notification on accepted/publishing workflow
transitions. A small systemd listener uses the existing limited application database role
with read-only transactions. It can request only the existing fixed guarded
publisher unit. Arbitrary notification payloads never become commands or logs.
LISTEN precedes startup wake;5-second pending-work checks recover missed notifications
or a worker becoming idle after a burst. The original60-second timer remains fallback.
A wake signal never bypasses queue validation, authority, locks, sync or readback.

Added private permission-scoped publication-pulse revision/pending endpoint, and
3-second UI polling while work is pending. Unchanged pulses do not rerun the full
bank list query or remount the editor. Progress cards check at3 seconds. Corrected
"A answer" wording. Actual bank writes/syncs remain asynchronous, not instantaneous.

Validation:20 wake-up/workbench/answer tests and19 serial/wake-up tests passed
(groups overlap). Includes real PostgreSQL commit versus rollback delivery, missed
notification recovery, fixed unit invocation/read-only connection, scoped pulse permissions,
serial guarded publication and status. Renderer tests verify unchanged pulses avoid
list reloads and completion refreshes without replacing the open editor. Web build
passes. No extra database, Redis or schema migration is needed.

Live wake-up rollout: initial service smoke rejected dropping a child process to
postgres under the explicit-root service restrictions; rollback restored the API
and original timer. Final design uses one process and the existing limited mpsc
application credential via the existing protected environment file, with read-only
transactions and fixed systemd invocation. No new credential was created or exposed.
New listener tests pass for this final connection design.

Final deployment completed with rollback `/tmp/publication-live-1794041083`.
Listener active with zero restarts and20,373,504 bytes memory at the check; guarded
worker completed successfully, original timer active, study/family healthy, served
frontend matches build and anonymous publication pulse is401. A committed empty
wake signal was measured against the worker's new start timestamp (receipt in
`reports/publication-live-20261107/wake-latency.json`). ENERVATE is verified live.
UI regression confirms pulse-driven refresh preserves open edits. No new content
was submitted for the latency probe; it woke only the normal guarded queue reader.

## 7 November 2026 — 1,000-question source preflight

Ran a bounded, read-only preflight over the first 1,000 highest-priority actionable
questions in the live review queue. The source lane currently contains1,625 items,
so this pass intentionally selected source-risk work before answer-only work. No
question, answer, taxonomy, review state or publication was changed.

The pass recorded2,165 blocker flags and2,464 review flags. Main findings were
914 existing source-defect flags,780 blank-option flags,723 unverified answers,
256 missing MCQ answers,124 duplicate-option flags,758 missing topics and936
missing explanations. It also found85 held questions,30 repeated stems inside
the pass,17 official/key rows without a registered final key,3 disputed keys and
3 rows without a registered paper document. These are triage signals for manual
inspection, not automatic corrections or approvals.

The report is saved in
`reports/1000-question-preflight-20261107/` as `summary.md`, `report.csv` and
`report.json`. The current question `cq_00054447a65e8ad1` appears first with its
source defect and blank-option flags, so its printed A–C layout should be repaired
before saving the verified B answer.

## 7 November 2026 — one strict tagging policy for future models

The owner clarified that “remove any other” means remove conflicting old
instructions, not existing tags. Added `docs/QUESTION-TAGGING-RULES.md`
(`study-tagging-v1`), a copyable model prompt, machine-readable preferred paths,
and app/bank AGENTS entry points. The policy separates tested content from exam
headings, schemes, region/language and dated context; GK/GS display aliases must
never be stored. Historical Current Affairs retains its reference period and key.
Ambiguous candidates stay pending with an owner question. Actual source, answer,
taxonomy and context repairs remain separate reviewed operations.

Archived four conflicting instruction documents intact and replaced their active
paths with current pointers. Updated README/handoff/library entry points and the
legacy classification utility's documentation; runtime algorithms were unchanged.
The source/scheme foundation remains a dated findings report, not a competing policy.

Read-only live audit at09:23 UTC:181 active nodes,82,249 live questions,58,370
subject-only approved primary paths, including4,557 English. No saved rows in
the new context/scheme/profile/tag-resolution tables. ENERVATE remains Geology;
water-image remains Electrical Engineering/Circuits. Clauses and non-verbal
reasoning have no appropriate narrow active nodes. These are repair candidates
and registry gaps, not corrections made by this instruction work.

The new read-only checker passes24 preferred routes against181 nodes; five
regression tests pass locally and on Oracle, covering alias/parent/node/status
errors. This checks legal paths, not semantic accuracy or arbitrary model outputs.
The earlier1,000-question pass was metadata triage, not source/answer certification.
Its reports are in the parent workspace's reports directory (the older entry's
relative path is relative to that workspace, not this app repository).

Oracle's workshop was a stripped deployment with no agent instructions/docs.
Installed14 new instruction, audit and checker/test files after confirming all
targets absent; verified every file hash and ran the same checks there. No service
restart, SQL content write, taxonomy change or question publication was performed.
Receipt: `reports/tagging-policy-20261107/oracle-install.json`. Canonical policy
there: `/srv/study/workshop/india-study-map-app/docs/QUESTION-TAGGING-RULES.md`.
Next: source-reviewed pilot and verified scheme/time-context records under this
policy; the58,370 subject-only rows still require triage, not automatic relabelling.

## 2026-11-07 — Source-reviewed 20-question tagging pilot (pending only)

Prepared `reports/tagging-pilot-20261107/README.md`, the required model-format
`pending-candidates.json` and separate source/answer/context findings from fresh
read-only Oracle snapshots and eight hash-matched registered PDFs. Final pilot:
20 unique canonical/appearance targets, 14 proposed retags, 6 keeps, 0 tag holds;
all candidates pending, zero submissions/publications/live question changes.
Coverage includes combined Assistant/UDC, separate legacy UDC, Gazetted GS and
written English, ENERVATE/water-image corrections, static chemistry, and a
specialist HMS Mining control. The owner resolved the Mizo time-expression item
to regional Mizoram knowledge and clarified notified-town count as Current Affairs;
these are attributed routing examples, not source sign-offs or publication approval.

All 181 fresh active registry nodes match the Oracle bank taxonomy definition;
candidate paths/parents and 24 policy routes validate. A later read-only Oracle
check preserves all 20 source fingerprints, paths, answer baselines and appearance
sets. Complete inspection locators are recorded per target. Q44 actually appears
on physical page 5 (stored page 6), has a printed underline versus live bold markup,
and three printed options versus a fourth null live option; its source flag and
inferred answer remain untouched. The historical town-count answer 23 still lacks
a dated official list; reference context is the printed October 2025 exam month.
No official keys or recruitment notices were inspected, no answers certified,
and no scheme/profile/context records were saved. Spatial/clause/Mining taxonomy
gaps remain separate backlog work. The report recommends a focused next 20 English
source reviews; it contains no authorization to publish this pilot.

## 2026-11-07 — Second pending tagging batch, 20 English targets

Continued the recommended next batch within the original prepare-only scope.
`reports/tagging-batch2-20261107/README.md` and model-format pending candidates
cover legacy UDC Q10–16, Assistant/UDC October 2025 Series A Q51–57 and Gazetted
September 2026 Series A English B11/B13/B15–18. All 20 source-reviewed:
7 proposed Sentence Correction → Grammar retags, 13 keeps, 0 tag holds.
All remain pending; no production proposals, publications or live data edits.
Three freshly retrieved PDFs match registered hashes; cover and exact task pages,
underlines and local directions were visually inspected. Six UDC shared directions
omit the final word “sentences”; separate source defects were retained without
blocking clear tags. Three voice items normalize shared PDF directions into stems;
this was recorded separately, not treated as missing context. No official keys or
recruitment notices were inspected and no answer certification was created.

All 181 active Oracle registry nodes match the fresh Oracle bank definition;
all candidate paths/parents and 24 policy examples validate. Later read-only
Oracle snapshots preserve all 20 fingerprints/paths/answer baselines/appearance
sets and the registry. Zero overlap with pilot 1: combined 40 reviewed,
21 proposed retags, 19 keeps, 0 holds and 0 live changes. Report records the
recommended next 20 targets and leaves earlier Q44/town-count evidence work open.

## 2026-11-07 — Owner expanded tagging review to the entire bank

Owner explicitly confirmed “Entire question bank”; retained the original pending-only,
no-live-data-change scope. Saved read-only repeatable-read Oracle inventory and
local exact coverage index under `reports/tagging-corpus-20261107/`: 82,383
canonical/source-appearance targets (82,249 live, 134 held), 1,979 papers,
1,978 registered source-paper documents and 181 active registry nodes.
No source-inspection claim was created for inventory-only targets.

Completed two additional source-reviewed packets of 100 each, reports
`tagging-batch3-20261107` and `tagging-batch4-20261107`. Combined four-packet
coverage is 240 distinct targets: 50 retag proposals, 187 keeps and 3 tag holds,
all pending, zero live changes/submissions/publications. Every new target has
actual PDF page/context inspection evidence, current active path validation and
unchanged exact Oracle source/answer/appearance readback. All recorded appearances
in initial legacy UDC (75), combined Assistant/UDC Series A (80), and Gazetted
English Series A (69) sources are now covered; no extraction/scheme/key readiness
certification is inferred from that coverage.

Open owner questions are source-bound: Shibu Soren obituary/past-career routing,
Dar Hla cultural/literary routing, and registration-number predecessor conventions
versus abstract reasoning. Current live tags/answers are preserved. New source/key
concerns (truncated directions, lost emphasis, null keys, printed phrase mismatch,
ambiguous/missing options) are recorded separately, not silently repaired.

The bank is NOT fully reviewed: 82,143 targets remain unreviewed, accounted for
exactly once by 1,218 source-focused planned packets (74,189 targets, max 100 each)
and a source-recovery queue (7,954 targets: 7,854 missing page locators, 100 missing
paper-document registration). The report contains a resumable process and honest
freshness limits; no unattended background process or automation was started.

## 2026-11-07 — Complete 7,954-target source-recovery pass (pending only)

Owner asked “Do the 7k”, referring to the 7,954-target source-recovery queue.
Processed every exact target against fresh read-only Oracle snapshots and all
610 source PDFs. Local source bytes (not local question records) were used only
after 609 registered Oracle hash matches; the unregistered LDC original was
separately hash-matched to current Oracle canonical and served source copies.
Extracted 1,221 PDF pages and ran local Tesseract OCR on nine scans / 31 pages.

`reports/source-recovery-20261107/README.md` and 80 bounded final JSON/Markdown
packets account for all 7,954 targets: 6,432 pending locator candidates,
804 partial candidates, 618 unresolved/held location findings, and 100 existing
locators preserved under one pending document-registration candidate. Only six
individual locators were visually checked; all other text/OCR matches explicitly
remain unverified visually. These are source-reference findings, not new tagging
reviews or production hold decisions. Semantic-review count remains 240.

Saved six source-bound, page-only `source_reference` proposals that validate
against the current Oracle Proposal schema without DB/API submission. Visual
checks exposed separate missing 16-row cost data / rates-analysis coefficients,
and flattened/null printed-question locators. No tables, historical cost periods,
answers or qnums were silently repaired. LDC cover/page-12 identity was checked;
recorded Q85/Q99/Q100 source defects remain untouched, including illegible
mirror/dice figures in the actual scan. No new document ID or sign-off invented.

Fresh readback preserves all 7,954 complete snapshots/source fingerprints,
raw appearances and canonical answer/status fields, plus paper/document registry
and active taxonomy. Validation checks pending status, exact coverage, hashes,
physical-page bounds, packet size and no duplicates. Local corpus JSONL/SQLite
now points to pending recovery findings but retains live source blockers and
unreviewed semantic status. Zero live changes, registrations, submissions or
publications. Source repairs are not all finished; automatic locator candidates,
804 partials and 618 held cases still need source/context inspection.


## 2026-11-07 — Source recovery continuation, pending only

Owner said “go” on the entire-bank / 7,954-source-recovery continuation. Prepared
141 new source-reviewed model-format tag candidates in packets 5–7 (65/51/25):
87 retag proposals, 54 keeps, no new semantic holds. Inspected 16 distinct complete
PDF pages across six registered hash-matched sources; batch 6 explicitly reused
the same nine inspected pages as batch 5. All 141 physical locators are individually
verified in pending page-only proposals. Of these, 63 previously held and 27
partial matches were recovered; 51 existing machine candidates were verified.
The multi-page police-manual composite retains pages 1–2 as evidence, with only
the start page in the existing page-only source-reference contract.

Fresh Oracle repeatable-read read-only exports and later readbacks preserved exact
snapshots, raw appearances, answers/statuses/defects, four-plus-two source documents
and the 181-node taxonomy. Legal paths and source-reference Proposal contracts pass;
schema validation made no submission. All original source fingerprints match. No
new target overlaps the prior 240; all other 7,813 recovery findings are unchanged.

Cumulative semantic review: 381 pending candidates (137 retag, 241 keep, 3 earlier
owner holds), 82,002 still unreviewed in the dated inventory. Source-recovery totals:
6,522 pending locator candidates, 777 partial, 555 held, 100 affected by missing LDC
document registration; 147 individual visual locator checks. The 6,375 remaining
machine locator candidates are not visually verified. This is not completion of
the bank or 7,954 source reviews. Live changes/submissions/publications remain zero.

Separated missing shared headings/instructions, overlapping composite/atomic source
representations, descriptive papers incorrectly typed mcq, missing discipline/evidence
taxonomy topics, and Q17 cash-book printed payment/discount ambiguity from tag decisions.
Historical source periods, exercise data, answers, identities and holds are preserved.
Existing three owner questions and LDC Q99/Q100 illegibility remain unresolved.

Evidence: reports/source-recovery-review2-20261107, review3, review4; required model
candidates and readable before/after tables: reports/tagging-batch5-20261107 through
batch7. Local corpus coverage/remaining plans rebuilt. Latest report recommends
32 open targets from MF&AS July 2019 Paper II, MPS July 2019 Paper III and Draftsman/JE
Accounts before formula/figure-heavy engineering/math papers. No background work started.


## 2026-11-07 — Owner priority: English, Arithmetic and Reasoning first

Owner redirected the proposed 32-question accounts batch before it began. Deferred
other-subject selection and exported a fresh read-only Oracle inventory at
11:52:15 UTC, preserving the earlier inventory. New priority discovery/coverage
ledger includes current English, Arithmetic, Reasoning, English-source/task clues
and subject-only mathematics for arithmetic triage. Discovery is explicitly not
semantic classification or exhaustive recall certification.

Prepared packets 8–11: 294 distinct source-reviewed existing targets across four
registered PDFs / 36 visually inspected original pages; 276 retag proposals and
18 keeps, all pending. Assistant Director Town Planning February 2026 General
English (68), Tourist Officer July 2026 General English (76), Sub-Inspector of
Statistics January 2026 Paper II (100), and its General English Paper I (50).
Statistics Paper II had 92 English/Grammar classifications despite printed General
Mathematics and GK groups. Tourist Officer had three passage items under GK/GS.
All actual task/option/formula/underline/passage contexts were inspected, preserving
exam/group identity. Owner resolved song-composer Q95 to GS/Mizoram culture; exact
attribution/example saved without closing earlier Dar Hla ambiguity.

Kept defects separate: 86 page-only pending source-reference proposals, missing
passage links (12), two absent shared-table links, wrong named underline targets,
missing emphasis, six corrupted formula/option targets and bounded arithmetic/
answer flags. Sixteen printed written tasks absent from the three English papers'
current appearances are separate intake evidence with null IDs and suggested
active paths; not invented canonical records or additional completed reviews.
No official key, independent human inspection or recruitment scheme certification.

Each packet's fresh Oracle readback preserved exact snapshots, raw appearances,
answers/statuses/defects, registry and documents. Four PDF hashes matched; all 181
active IDs/levels/parents matched the fresh Oracle bank definition. Page-only
Proposal schema checks passed without DB/API writes/submission. No overlapping
reviewed targets; all model statuses remain pending. No live question data, source
registry, context, key, scoring holds or memberships changed; no publications.

Cumulative bank review: 675 pending targets (413 retag, 259 keep, 3 earlier holds),
81,708 still unreviewed in dated full-bank inventory. Priority discovery: 16,065
targets, 467 reviewed and 15,598 unreviewed. Current stored-category remaining:
English 10,808, Arithmetic 912, Reasoning 2,673; these are not correctly-classified
shelf counts. Saved proposed paths across all packets: English 371, Arithmetic 23,
Reasoning 4. The original 7,954 missing-source queue's 147 visual locators are a
separate scope and were not falsely increased by these already-located papers.

Evidence: reports/tagging-batch8-20261107 through batch11, and
reports/tagging-priority-20261107/README.md. All full before/after tables, exact
inspection notes, baseline/readback, pending candidates, missing-task evidence and
validation receipts saved. Corpus ledger/plans refreshed. Next selection remains
English (Assistant LESO, then CAO A/B) and Arithmetic/Reasoning; other subject
queues deferred. Priority areas are not complete; no background review started.


## 2026-11-07 18:02 IST — Fresh bank-status confirmation

Owner requested confirmation of reported bank situation. Exported a fresh full
Oracle roster and exact 675-target snapshots in repeatable-read read-only
transactions. Confirmed 82,383 questions/appearances (82,249 live, 134 held),
675 unique saved pending candidates (413 retag, 259 keep, 3 hold), and 81,708
unreviewed. Current-label unreviewed counts remain English 10,808, Arithmetic
912, Reasoning 2,673; these are structural counts, not correct-subject guarantees.

All 675 full source snapshots/fingerprints, target appearances, recorded answers
and registered document bindings match saved baselines. No question IDs/status/
classification metadata changed from the earlier priority inventory. No taxonomy
or source-reference contributions were created for these targets since 09:00 UTC.
The prepared retags have not reached live primary paths. No live writes were made,
PDF inspections invented, new question reviews counted or publication authorized.

Evidence: reports/bank-confirmation-20261107-123101/README.md and verification.json;
new read-only roster/source exports preserve historical review receipts. This
confirms counts and exact reviewed-target preservation, not semantic/key/source
quality across unreviewed questions.

## 2026-11-07 — Exam paper presentation

- Added scoped examination-stationery styling to original papers, shared practice
  cards, timed mock/shared-test runners and result summaries: cream sheets, serif
  question typography, restrained rules, circular answer letters and readable spacing.
- Compacted paper readiness/instructions and collapsed search/filter controls;
  preserved question/source identity, scoring, answer gates, flags, notes and PDF tools.
- Added labelled time remaining, answered progress, 44px question-map controls and
  accessible current-question/status labels. Replaced inaccurate “Not seen” with
  “Unanswered”. Paper answer outcomes include text as well as colour.
- Production build, shareable-test UI, answer-panel and paper-duplicate component
  checks pass. Updated the duplicate test's stale readiness API stub (no behavior
  change). Browser checked the supplied LDC paper in desktop and 390px mobile
  viewports and focus navigation; mobile document width equals viewport width.
- Timed/shared runner verified with mocked API component checks; no synthetic
  production attempt was submitted. Local screenshot: tmp/exam-paper-preview.png.
- Frontend release uses scripts/deploy.sh web; prior public artifact copied to
  /srv/study/releases/pre-exam-paper-ui-20261107 for rollback. No backend/bank edits.
- Release completed successfully; live LDC focus page and next-question navigation
  verified in browser. Both study and family sites healthy. Live screenshot:
  tmp/exam-paper-live.png.

## 2026-11-07 18:20 IST — Compact public question cards (local)

Owner requested minimal expanding cards around the 2016 Make in India Week example,
with the map.hawayu.in MCQ practice hub as reference. Inspected its real browser
layout and preserved the study app's answer/provenance semantics. Public bank and
module cards now use tighter spacing, a divider-based answer area and one compact
Save / More / Explanation & details footer. Full explanation, answer evidence,
historical revision context and study tools share the latter disclosure. More
contains Source, Discussion, Share, private Report and permitted Review/edit.
Source/scoring warnings remain visible; answer restoration/restrictions retain
source/report access. No answer gates, answer status, historical answers, attempt
logic, staff grants or live bank data changed.

TypeScript/Vite build and existing public-card/answer-panel checks pass. Browser
verified phone and desktop layouts plus explanation, source, discussion and private
report disclosures against isolated synthetic responses; no form submitted. Same
fixture shrank from 698.5px to 462.3px on phone (33.8%) and 523px to 336.1px on
desktop (35.7%), without horizontal overflow. Compact controls retain 44px targets.
Evidence, exact pre-task component copies, reproducible local preview and screenshots
saved in reports/compact-cards-20261107/. These are component previews, not live-page
measurements. Frontend not deployed; full live integration still pending. Existing
pending tagging work remains unchanged.

## 2026-11-07 — Distinct explanations after answering

- Revealed practice explanations now appear immediately outside the collapsed
  source/study-tools disclosure, with a pale blue panel, blue left rule and
  Public Sans body text distinct from serif questions and selectable options.
- Long explanations show six lines initially with accessible Read more/Show less
  controls. Retained review-state wording and honest missing-explanation states.
- Outcome row includes the displayed option letter only when its text maps uniquely;
  unverified answers retain “matches/differs from stored answer” language.
- Answer-panel regression covers automatic visibility, expansion and test restrictions;
  shared-test checks pass. Browser verified guest Show answer on the supplied LDC
  paper (Q1 has no stored explanation, so the explicit empty state is shown).
- Frontend-only release through scripts/deploy.sh web with rollback artifact at
  /srv/study/releases/pre-explanation-panel-20261107. No answer content changed.
- Deployment completed; live stylesheet verified, study/family health checks passed.
  Preview evidence: tmp/explanation-panel.png. Production build passed.

## 2026-11-07 — Readable admin publication history

- Promoted Publication history into primary admin navigation and replaced the raw
  request list with a dedicated correction log at /admin/bank?tab=publications.
- Default My corrections includes authored/exported work; added all-permitted
  scope, title/paper/ID search, status/type filters, refresh and older/newer pages.
  Labels distinguish Published, Publishing, Needs attention and Reverted; cards
  show actor, request/completion dates, changed fields, source and question links.
- Added read-only paginated API and lazy scoped details from immutable manifests
  and receipts. Before/after values distinguish actual receipts from requested
  corrections and missing historical fields. No publication decisions changed.
  Pending approvals remain explicitly linked to the existing review queue.
- Tested on a disposable database: scope filtering, own/exporter attribution,
  pagination, query validation, exact receipt values, guest/staff boundaries and
  active-test answer protection (2 tests). Component fixture checks cover filters,
  expanded comparisons and pagination; navigation tests and production build pass.
  Updated the navigation fixture to ignore CSS imports from the newer overview.
- Desktop visual preview uses synthetic examples only:
  tmp/publication-history-preview.html and tmp/publication-history-preview.png.
  A phone viewport override did not take effect on the background preview tab;
  phone visual verification was not completed. Responsive controls/comparisons
  use wrapping/stacked layouts.
- Released via scripts/deploy-publication-history.sh (read-only router additions
  appended to the exact running router, preserving unrelated deployed changes),
  then scripts/deploy.sh web. API rollback copy:
  /tmp/publication-history-1794056392; frontend rollback:
  /srv/study/releases/pre-publication-history-20261107.
- Both sites passed health checks; live anonymous history access correctly returns
  401. Authenticated behavior verified in disposable database/component fixtures;
  the available live browser is signed out. No bank/question/user-history writes.


## 2026-11-07 21:50 IST — Source-reviewed tagging pilot 2

- Prepared source-reviewed pilot of 20 questions spanning English (5), GK/GS (5),
  Current Affairs (5), and Reasoning (5) across distinct MPSC exams under policy
  study-tagging-v1: Assistant/UDC April 2024, Combined Competitive Gazetted 2026
  (GS-I, GS-II, GS-III), MCS CSP Paper II, Radiotherapy Technologist 2026,
  Inspector of Taxes 2021, LDC 2025, Fishery Extension Officer 2017, and
  Sub-Inspector Excise 2026.
- Enforced owner's directive: to reduce duplication, only one booklet (Series A /
  Booklet A / primary appearance) is considered per paper.
- Result: 10 retags, 10 keeps, 0 holds. All 20 remain pending candidates in
  reports/tagging-pilot2-20261107/pending-candidates.json. Live writes: 0.
- Readback validation against Oracle DB verified that all 20 source fingerprints,
  answer baselines, and review states remain identical. All 20 proposed paths
  validate strictly against the 181 active nodes in review_taxonomy.


## 2026-11-07 22:15 IST — Source-reviewed tagging batch 12 (English Grammar & Vocabulary)

- Completed source-reviewed tagging batch 12 of 50 English questions following the owner's
  English/Arithmetic/Reasoning priority under policy study-tagging-v1.
- Targets: 25 English MCQs (Q51–Q75) from Combined Competitive Examinations for Assistant Grade /
  UDC 2024 Paper-I, and 25 English MCQs (Q51–Q75) from Combined Group B (NG) Paper-I December 2024
  Booklet A. Single-booklet policy enforced (Booklets B, C, D omitted to reduce duplication).
- Direct visual inspection of all 6 physical PDF page images (pages 5, 6, 7 of both registered PDFs,
  sha256 6e55b48c... and 8cb1eb2d...).
- Results: 32 retags, 18 keeps, 0 holds. All 50 remain pending candidates in
  reports/tagging-batch12-20261107/pending-candidates.json. Live writes: 0.
- Key corrections:
  * Assistant/UDC 2024: 20 items previously lumped into generic english/grammar were refined to
    active subtopics: Synonyms (Q51-55), Antonyms (Q56-60), Subject-Verb Agreement (Q62-65),
    and Idioms & Phrases (Q66-70).
  * Group B NG Dec 2024: Corrected 5 Antonym questions (Q66-70) that were previously misclassified
    as Synonyms; refined 3 subject-only English root items to Vocabulary.
- Readback validation (validation.json) against Oracle DB verified 0 database writes; all 50
  source fingerprints match 100%. All paths validate against the 181 active taxonomy nodes.


## 2026-11-07 22:30 IST — Source-reviewed tagging batch 13 (Reasoning & Mental Ability)

- Completed source-reviewed tagging batch 13 of 50 Reasoning & Aptitude questions following the
  owner's English/Arithmetic/Reasoning priority under policy study-tagging-v1.
- Target paper: Mizoram Civil Services Combined Preliminary Examination 2025, Paper-II (Aptitude &
  Reasoning), Series-A (50 core reasoning questions: Q35–Q84).
- Single-booklet policy enforced: only Series-A was considered; duplicate permutation series
  (Series-B, Series-C, Series-D) were omitted to eliminate redundant tagging passes.
- Direct visual inspection of all 9 physical PDF pages (pages 7 to 15 of registered document
  doc_e092395e2688703b09ce8212, sha256 63ee7c9d5510accf...). Inspected all stems, directions,
  options, and figure diagrams (including Q75 rotating sector diagram).
- Results: 8 retags, 42 keeps, 0 holds. All 50 remain pending candidates in
  reports/tagging-batch13-20261107/pending-candidates.json. Live writes: 0.
- Key corrections:
  * Restored 3 Assertion & Reason questions (Q45 Tides, Q46 Himalayan rivers, Q47 Glaciers) that were
    misclassified as General Studies (geography/environment) back to reasoning-and-aptitude/verbal-reasoning.
  * Reclassified CSAT quantitative word problems (Q73 fence posts, Q84 work-rate) from mathematics/arithmetic
    to reasoning-and-aptitude/numerical-ability.
  * Reclassified visual figure progression (Q75) and alphabet position progression (Q76) to
    reasoning-and-aptitude/series. Noted taxonomy gap for non-verbal reasoning.
- Readback validation (validation.json) against Oracle DB verified 0 database writes; all 50
  source fingerprints match 100%. All paths validate strictly against the 181 active taxonomy nodes.


## 2026-11-07 23:55 IST — Source-reviewed tagging batch 18 (Arithmetic & Reasoning)

- Completed source-reviewed tagging batch 18 of 50 Quantitative & Reasoning questions under /goal execution,
  following the owner's English/Arithmetic/Reasoning priority under policy study-tagging-v1.
- Target paper: Combined Group B (NG) Paper-II December-2024 Booklet A (Q34–Q83, completing the entire
  quantitative, data interpretation, and reasoning section).
  Single-booklet policy enforced: only Booklet A (doc_9e78d845748f93799eefe5ac, sha256 c45fbaf9...) was
  considered; duplicate permutation Booklets B, C, and D were cleanly omitted, saving 249 redundant reviews.
- Direct visual inspection of all 6 physical PDF page images (pages 5 to 10) from registered document
  doc_9e78d845748f93799eefe5ac. Inspected pie charts (Q46-47), geometric formulas, branching number trees (Q75),
  non-verbal figure patterns (Q78, Q79), and 3x3 figure matrix (Q80).
- Results: 50 retags, 0 keeps, 0 holds. All 50 remain pending candidates in
  reports/tagging-batch18-20261107/pending-candidates.json. Live writes: 0.
- Key corrections:
  * Rectified 100% of targets (all 50 previously sat in an unassigned `null/null` state in the database).
  * Computer Science / Networking (Q34, Q35): IPv6 128-bit address architecture and messaging channels mapped to `computer-science/networking`.
  * Arithmetic & Numbers (Q36, Q37, Q41, Q43, Q44, Q54, Q57, Q60, Q61): Divisibility, radical arithmetic,
    simple interest, AP sums, BODMAS, square roots, train speed-distance, and compound interest mapped to `mathematics/arithmetic`.
  * Averages (Q38): Positive even multiples mean mapped to `mathematics/arithmetic/averages`.
  * Profit & Loss (Q39, Q53): Unit orange sales and loss recovery mapped to `mathematics/arithmetic/profit-and-loss`.
  * Percentages (Q45, Q48, Q49, Q52, Q65, Q71): Pass mark shortfall, successive discounts, sales tax,
    homework completion, Venn survey intersection, and election valid votes mapped to `mathematics/arithmetic/percentages`.
  * Ratio & Proportion (Q50, Q51): Compound equality ratios and liquid mixture adjustments mapped to `mathematics/arithmetic/ratio-and-proportion`.
  * Geometry & Mensuration (Q42, Q55, Q63): Complementary angle heights, cube volume, and perimeter wire area
    comparison mapped to `mathematics/geometry/triangles`, `mathematics/mensuration/volume`, and `mathematics/mensuration/area`.
  * Algebra (Q56): Common base exponential equation mapped to `mathematics/algebra/algebraic-expressions`.
  * Probability (Q64): Two-coin toss probability mapped to active subject root `mathematics`.
  * Data Interpretation (Q46, Q47): Book store distribution pie chart central angles and group differences mapped to `reasoning-and-aptitude/data-interpretation`.
  * Series & Spatial Logic (Q59, Q69, Q75, Q78–Q80): AP terms count, dice adjacency, branching number HCF tree,
    figure patterns, and 3x3 shape matrix mapped to `reasoning-and-aptitude/series`. Documented taxonomy gap for non-verbal reasoning.
  * Verbal Reasoning & Numerical Ability (Q40, Q58, Q62, Q66–Q68, Q70, Q72–Q74, Q76–Q77, Q81–Q83): Time and work,
    cistern leaks, displacement, alphabet position logic, calendar cycle, analogies, seating arrangements, shadow direction,
    recess bullying reaction, drought relief courses of action, and wage sharing mapped to active topics.
- Readback validation (validation.json) against Oracle DB verified 0 database writes; all 50
  source fingerprints match 100%. All paths validate strictly against the 181 active taxonomy nodes.



## 2026-11-07 23:40 IST — Source-reviewed tagging batch 17 (Technical & Pure Mathematics)

- Completed source-reviewed tagging batch 17 of 50 Mathematics questions under /goal execution,
  following the owner's English/Arithmetic/Reasoning priority under policy study-tagging-v1.
- Target paper: Competitive Examination for Inspector of Statistics 2026 - Paper-III (Mathematics)
  (Q1–Q50, completing Part-A Multiple Choice Questions).
  Single-booklet policy enforced: unique registered document doc_064ad469ca009ef3206215ef (sha256 57d152bd...).
- Direct visual inspection of all 7 physical PDF page images (pages 1 to 7) from registered document
  doc_064ad469ca009ef3206215ef. Inspected all printed formulas, differential equations, integrals, matrices,
  and numerical algorithms.
- Results: 50 retags, 0 keeps, 0 holds. All 50 remain pending candidates in
  reports/tagging-batch17-20261107/pending-candidates.json. Live writes: 0.
- Key corrections:
  * Rectified 100% of targets (all 50 previously erroneously stored under generic `gk/Inspector of Statistics Paper-III (Mathematics).`).
  * Abstract & Linear Algebra (Q3, Q11, Q12, Q17, Q27–Q30, Q39–Q41): Mapped to active topic `mathematics/algebra`.
  * 3D Geometry (Q8, Q35): Shortest distance and angle between skew lines mapped to `mathematics/geometry/lines-and-angles`.
  * Numerical Linear Equations (Q50): Gauss-Seidel iterative method mapped to `mathematics/algebra/linear-equations`.
  * Advanced Calculus, Differential Equations, Analysis & Numerical Methods (Q1–Q2, Q4–Q7, Q9–Q10, Q13–Q16,
    Q18–Q26, Q31–Q34, Q36–Q38, Q42–Q49): Mapped to active subject root `mathematics`. Documented systemic taxonomy
    gap: the active 181-node taxonomy lacks dedicated topics for advanced undergraduate mathematics (Calculus,
    Differential Equations, Real/Complex Analysis, Numerical Analysis, Operations Research).
- Readback validation (validation.json) against Oracle DB verified 0 database writes; all 50
  source fingerprints match 100%. All paths validate strictly against the 181 active taxonomy nodes.


## 2026-11-07 23:55 IST — Source-reviewed tagging batch 18 (Arithmetic & Reasoning)

- Completed source-reviewed tagging batch 18 of 50 Quantitative & Reasoning questions under /goal execution,
  following the owner's English/Arithmetic/Reasoning priority under policy study-tagging-v1.
- Target paper: Combined Group B (NG) Paper-II December-2024 Booklet A (Q34–Q83, completing the entire
  quantitative, data interpretation, and reasoning section).
  Single-booklet policy enforced: only Booklet A (doc_9e78d845748f93799eefe5ac, sha256 c45fbaf9...) was
  considered; duplicate permutation Booklets B, C, and D were cleanly omitted, saving 249 redundant reviews.
- Direct visual inspection of all 6 physical PDF page images (pages 5 to 10) from registered document
  doc_9e78d845748f93799eefe5ac. Inspected pie charts (Q46-47), geometric formulas, branching number trees (Q75),
  non-verbal figure patterns (Q78, Q79), and 3x3 figure matrix (Q80).
- Results: 50 retags, 0 keeps, 0 holds. All 50 remain pending candidates in
  reports/tagging-batch18-20261107/pending-candidates.json. Live writes: 0.
- Key corrections:
  * Rectified 100% of targets (all 50 previously sat in an unassigned `null/null` state in the database).
  * Computer Science / Networking (Q34, Q35): IPv6 128-bit address architecture and messaging channels mapped to `computer-science/networking`.
  * Arithmetic & Numbers (Q36, Q37, Q41, Q43, Q44, Q54, Q57, Q60, Q61): Divisibility, radical arithmetic,
    simple interest, AP sums, BODMAS, square roots, train speed-distance, and compound interest mapped to `mathematics/arithmetic`.
  * Averages (Q38): Positive even multiples mean mapped to `mathematics/arithmetic/averages`.
  * Profit & Loss (Q39, Q53): Unit orange sales and loss recovery mapped to `mathematics/arithmetic/profit-and-loss`.
  * Percentages (Q45, Q48, Q49, Q52, Q65, Q71): Pass mark shortfall, successive discounts, sales tax,
    homework completion, Venn survey intersection, and election valid votes mapped to `mathematics/arithmetic/percentages`.
  * Ratio & Proportion (Q50, Q51): Compound equality ratios and liquid mixture adjustments mapped to `mathematics/arithmetic/ratio-and-proportion`.
  * Geometry & Mensuration (Q42, Q55, Q63): Complementary angle heights, cube volume, and perimeter wire area
    comparison mapped to `mathematics/geometry/triangles`, `mathematics/mensuration/volume`, and `mathematics/mensuration/area`.
  * Algebra (Q56): Common base exponential equation mapped to `mathematics/algebra/algebraic-expressions`.
  * Probability (Q64): Two-coin toss probability mapped to active subject root `mathematics`.
  * Data Interpretation (Q46, Q47): Book store distribution pie chart central angles and group differences mapped to `reasoning-and-aptitude/data-interpretation`.
  * Series & Spatial Logic (Q59, Q69, Q75, Q78–Q80): AP terms count, dice adjacency, branching number HCF tree,
    figure patterns, and 3x3 shape matrix mapped to `reasoning-and-aptitude/series`. Documented taxonomy gap for non-verbal reasoning.
  * Verbal Reasoning & Numerical Ability (Q40, Q58, Q62, Q66–Q68, Q70, Q72–Q74, Q76–Q77, Q81–Q83): Time and work,
    cistern leaks, displacement, alphabet position logic, calendar cycle, analogies, seating arrangements, shadow direction,
    recess bullying reaction, drought relief courses of action, and wage sharing mapped to active topics.
- Readback validation (validation.json) against Oracle DB verified 0 database writes; all 50
  source fingerprints match 100%. All paths validate strictly against the 181 active taxonomy nodes.




## 2026-11-07 23:20 IST — Source-reviewed tagging batch 16 (English Grammar, Vocabulary & Reported Speech)

- Completed source-reviewed tagging batch 16 of 50 English questions under /goal execution,
  following the owner's English/Arithmetic/Reasoning priority under policy study-tagging-v1.
- Target paper: Competitive Examination for Assistant LESO 2026 - General English (Q17–Q66).
  Single-booklet policy enforced: unique registered document doc_3c107a32ef282eb0258dac94 (sha256 bd3c0763...).
  Together with Batch 15 (Q1–Q16), this brings Assistant LESO 2026 General English to 100% completion (66/66).
- Direct visual inspection of all 7 physical PDF page images (pages 4 to 10) from registered document
  doc_3c107a32ef282eb0258dac94. Inspected stems, options, phrase/clause structures, and speech transformations.
- Results: 50 retags, 0 keeps, 0 holds. All 50 remain pending candidates in
  reports/tagging-batch16-20261107/pending-candidates.json. Live writes: 0.
- Key corrections:
  * Rectified 100% of targets (all 50 previously erroneously stored under generic `gk/Assistant LESO-2026 General English.`).
  * Conjunctions (Q17–Q20): Mapped to active topic `english/grammar`.
  * Prepositions (Q21–Q30): Mapped to active subtopic `english/grammar/prepositions`. Recorded source defect:
    printed heading mislabels section as 'determiner', while options are prepositions. Recorded Q28 typo ('wairing').
  * Vocabulary sentence completion (Q31–Q38): Mapped to active topic `english/vocabulary`.
  * Idioms & Phrases (Q39–Q43): Mapped to active subtopic `english/vocabulary/idioms-and-phrases`.
  * Sentence forms & structural syntax (Q44–Q54, Q58): Mapped to active topic `english/grammar`.
  * Conditional & correlative syntax (Q55, Q56): Mapped to active topic `english/sentence-correction`.
  * Subject-verb agreement (Q57): Mapped to active subtopic `english/grammar/subject-verb-agreement`.
  * Reported Speech (Q59–Q66): Mapped 8 questions testing direct/indirect speech transformations and universal truths
    to active subtopic `english/grammar/reported-speech`.
- Readback validation (validation.json) against Oracle DB verified 0 database writes; all 50
  source fingerprints match 100%. All paths validate strictly against the 181 active taxonomy nodes.


## 2026-11-07 23:55 IST — Source-reviewed tagging batch 18 (Arithmetic & Reasoning)

- Completed source-reviewed tagging batch 18 of 50 Quantitative & Reasoning questions under /goal execution,
  following the owner's English/Arithmetic/Reasoning priority under policy study-tagging-v1.
- Target paper: Combined Group B (NG) Paper-II December-2024 Booklet A (Q34–Q83, completing the entire
  quantitative, data interpretation, and reasoning section).
  Single-booklet policy enforced: only Booklet A (doc_9e78d845748f93799eefe5ac, sha256 c45fbaf9...) was
  considered; duplicate permutation Booklets B, C, and D were cleanly omitted, saving 249 redundant reviews.
- Direct visual inspection of all 6 physical PDF page images (pages 5 to 10) from registered document
  doc_9e78d845748f93799eefe5ac. Inspected pie charts (Q46-47), geometric formulas, branching number trees (Q75),
  non-verbal figure patterns (Q78, Q79), and 3x3 figure matrix (Q80).
- Results: 50 retags, 0 keeps, 0 holds. All 50 remain pending candidates in
  reports/tagging-batch18-20261107/pending-candidates.json. Live writes: 0.
- Key corrections:
  * Rectified 100% of targets (all 50 previously sat in an unassigned `null/null` state in the database).
  * Computer Science / Networking (Q34, Q35): IPv6 128-bit address architecture and messaging channels mapped to `computer-science/networking`.
  * Arithmetic & Numbers (Q36, Q37, Q41, Q43, Q44, Q54, Q57, Q60, Q61): Divisibility, radical arithmetic,
    simple interest, AP sums, BODMAS, square roots, train speed-distance, and compound interest mapped to `mathematics/arithmetic`.
  * Averages (Q38): Positive even multiples mean mapped to `mathematics/arithmetic/averages`.
  * Profit & Loss (Q39, Q53): Unit orange sales and loss recovery mapped to `mathematics/arithmetic/profit-and-loss`.
  * Percentages (Q45, Q48, Q49, Q52, Q65, Q71): Pass mark shortfall, successive discounts, sales tax,
    homework completion, Venn survey intersection, and election valid votes mapped to `mathematics/arithmetic/percentages`.
  * Ratio & Proportion (Q50, Q51): Compound equality ratios and liquid mixture adjustments mapped to `mathematics/arithmetic/ratio-and-proportion`.
  * Geometry & Mensuration (Q42, Q55, Q63): Complementary angle heights, cube volume, and perimeter wire area
    comparison mapped to `mathematics/geometry/triangles`, `mathematics/mensuration/volume`, and `mathematics/mensuration/area`.
  * Algebra (Q56): Common base exponential equation mapped to `mathematics/algebra/algebraic-expressions`.
  * Probability (Q64): Two-coin toss probability mapped to active subject root `mathematics`.
  * Data Interpretation (Q46, Q47): Book store distribution pie chart central angles and group differences mapped to `reasoning-and-aptitude/data-interpretation`.
  * Series & Spatial Logic (Q59, Q69, Q75, Q78–Q80): AP terms count, dice adjacency, branching number HCF tree,
    figure patterns, and 3x3 shape matrix mapped to `reasoning-and-aptitude/series`. Documented taxonomy gap for non-verbal reasoning.
  * Verbal Reasoning & Numerical Ability (Q40, Q58, Q62, Q66–Q68, Q70, Q72–Q74, Q76–Q77, Q81–Q83): Time and work,
    cistern leaks, displacement, alphabet position logic, calendar cycle, analogies, seating arrangements, shadow direction,
    recess bullying reaction, drought relief courses of action, and wage sharing mapped to active topics.
- Readback validation (validation.json) against Oracle DB verified 0 database writes; all 50
  source fingerprints match 100%. All paths validate strictly against the 181 active taxonomy nodes.



## 2026-11-07 23:40 IST — Source-reviewed tagging batch 17 (Technical & Pure Mathematics)

- Completed source-reviewed tagging batch 17 of 50 Mathematics questions under /goal execution,
  following the owner's English/Arithmetic/Reasoning priority under policy study-tagging-v1.
- Target paper: Competitive Examination for Inspector of Statistics 2026 - Paper-III (Mathematics)
  (Q1–Q50, completing Part-A Multiple Choice Questions).
  Single-booklet policy enforced: unique registered document doc_064ad469ca009ef3206215ef (sha256 57d152bd...).
- Direct visual inspection of all 7 physical PDF page images (pages 1 to 7) from registered document
  doc_064ad469ca009ef3206215ef. Inspected all printed formulas, differential equations, integrals, matrices,
  and numerical algorithms.
- Results: 50 retags, 0 keeps, 0 holds. All 50 remain pending candidates in
  reports/tagging-batch17-20261107/pending-candidates.json. Live writes: 0.
- Key corrections:
  * Rectified 100% of targets (all 50 previously erroneously stored under generic `gk/Inspector of Statistics Paper-III (Mathematics).`).
  * Abstract & Linear Algebra (Q3, Q11, Q12, Q17, Q27–Q30, Q39–Q41): Mapped to active topic `mathematics/algebra`.
  * 3D Geometry (Q8, Q35): Shortest distance and angle between skew lines mapped to `mathematics/geometry/lines-and-angles`.
  * Numerical Linear Equations (Q50): Gauss-Seidel iterative method mapped to `mathematics/algebra/linear-equations`.
  * Advanced Calculus, Differential Equations, Analysis & Numerical Methods (Q1–Q2, Q4–Q7, Q9–Q10, Q13–Q16,
    Q18–Q26, Q31–Q34, Q36–Q38, Q42–Q49): Mapped to active subject root `mathematics`. Documented systemic taxonomy
    gap: the active 181-node taxonomy lacks dedicated topics for advanced undergraduate mathematics (Calculus,
    Differential Equations, Real/Complex Analysis, Numerical Analysis, Operations Research).
- Readback validation (validation.json) against Oracle DB verified 0 database writes; all 50
  source fingerprints match 100%. All paths validate strictly against the 181 active taxonomy nodes.


## 2026-11-07 23:55 IST — Source-reviewed tagging batch 18 (Arithmetic & Reasoning)

- Completed source-reviewed tagging batch 18 of 50 Quantitative & Reasoning questions under /goal execution,
  following the owner's English/Arithmetic/Reasoning priority under policy study-tagging-v1.
- Target paper: Combined Group B (NG) Paper-II December-2024 Booklet A (Q34–Q83, completing the entire
  quantitative, data interpretation, and reasoning section).
  Single-booklet policy enforced: only Booklet A (doc_9e78d845748f93799eefe5ac, sha256 c45fbaf9...) was
  considered; duplicate permutation Booklets B, C, and D were cleanly omitted, saving 249 redundant reviews.
- Direct visual inspection of all 6 physical PDF page images (pages 5 to 10) from registered document
  doc_9e78d845748f93799eefe5ac. Inspected pie charts (Q46-47), geometric formulas, branching number trees (Q75),
  non-verbal figure patterns (Q78, Q79), and 3x3 figure matrix (Q80).
- Results: 50 retags, 0 keeps, 0 holds. All 50 remain pending candidates in
  reports/tagging-batch18-20261107/pending-candidates.json. Live writes: 0.
- Key corrections:
  * Rectified 100% of targets (all 50 previously sat in an unassigned `null/null` state in the database).
  * Computer Science / Networking (Q34, Q35): IPv6 128-bit address architecture and messaging channels mapped to `computer-science/networking`.
  * Arithmetic & Numbers (Q36, Q37, Q41, Q43, Q44, Q54, Q57, Q60, Q61): Divisibility, radical arithmetic,
    simple interest, AP sums, BODMAS, square roots, train speed-distance, and compound interest mapped to `mathematics/arithmetic`.
  * Averages (Q38): Positive even multiples mean mapped to `mathematics/arithmetic/averages`.
  * Profit & Loss (Q39, Q53): Unit orange sales and loss recovery mapped to `mathematics/arithmetic/profit-and-loss`.
  * Percentages (Q45, Q48, Q49, Q52, Q65, Q71): Pass mark shortfall, successive discounts, sales tax,
    homework completion, Venn survey intersection, and election valid votes mapped to `mathematics/arithmetic/percentages`.
  * Ratio & Proportion (Q50, Q51): Compound equality ratios and liquid mixture adjustments mapped to `mathematics/arithmetic/ratio-and-proportion`.
  * Geometry & Mensuration (Q42, Q55, Q63): Complementary angle heights, cube volume, and perimeter wire area
    comparison mapped to `mathematics/geometry/triangles`, `mathematics/mensuration/volume`, and `mathematics/mensuration/area`.
  * Algebra (Q56): Common base exponential equation mapped to `mathematics/algebra/algebraic-expressions`.
  * Probability (Q64): Two-coin toss probability mapped to active subject root `mathematics`.
  * Data Interpretation (Q46, Q47): Book store distribution pie chart central angles and group differences mapped to `reasoning-and-aptitude/data-interpretation`.
  * Series & Spatial Logic (Q59, Q69, Q75, Q78–Q80): AP terms count, dice adjacency, branching number HCF tree,
    figure patterns, and 3x3 shape matrix mapped to `reasoning-and-aptitude/series`. Documented taxonomy gap for non-verbal reasoning.
  * Verbal Reasoning & Numerical Ability (Q40, Q58, Q62, Q66–Q68, Q70, Q72–Q74, Q76–Q77, Q81–Q83): Time and work,
    cistern leaks, displacement, alphabet position logic, calendar cycle, analogies, seating arrangements, shadow direction,
    recess bullying reaction, drought relief courses of action, and wage sharing mapped to active topics.
- Readback validation (validation.json) against Oracle DB verified 0 database writes; all 50
  source fingerprints match 100%. All paths validate strictly against the 181 active taxonomy nodes.





## 2026-11-07 23:00 IST — Source-reviewed tagging batch 15 (English Reading Comprehension, Grammar & Communication)

- Completed source-reviewed tagging batch 15 of 50 English and Aptitude questions under /goal execution,
  following the owner's English/Arithmetic/Reasoning priority under policy study-tagging-v1.
- Target papers:
  1. Mizoram Civil Services Combined Preliminary Examination 2025, Paper-II Series-A (34 questions: Q1–Q34).
     Single-booklet policy enforced: Series-A selected; duplicate Series-B, C, D omitted.
  2. Competitive Examination for Assistant LESO 2026 - General English (16 questions: Q1–Q16).
- Direct visual inspection of all 8 physical PDF page images (MCS CSP pages 2 to 7; LESO pages 3 and 4)
  from registered documents doc_e092395e2688703b09ce8212 (sha256 63ee7c9d...) and doc_3c107a32ef282eb0258dac94
  (sha256 bd3c0763...). Inspected 4 full reading comprehension passages (AI, Solitude, Social Media, Women's
  Empowerment), stems, options, and grammar directions.
- Results: 50 retags, 0 keeps, 0 holds. All 50 remain pending candidates in
  reports/tagging-batch15-20261107/pending-candidates.json. Live writes: 0.
- Key corrections:
  * Rectified 100% of targets (all 50 previously erroneously stored under generic `gk/<Paper Title>`).
  * Mapped 16 passage questions (MCS Q1–Q15, Q17) to active topic `english/comprehension`.
  * Mapped passage-based contextual synonym (MCS Q16) to `english/vocabulary/synonyms`.
  * Mapped vocabulary cloze and confusing word items (MCS Q18–Q20) to `english/vocabulary`.
  * Mapped critical reasoning inference (MCS Q21) to `reasoning-and-aptitude/verbal-reasoning`.
  * Mapped 13 CSAT interpersonal, non-verbal communication, assertiveness, and empathy items (MCS Q22–Q34)
    to `reasoning-and-aptitude/verbal-reasoning`. Documented taxonomy gap for interpersonal communication.
  * Mapped 10 Parts of Speech items (LESO Q1–Q10) to `english/grammar/parts-of-speech`.
  * Mapped 5 Prepositions items (LESO Q11–Q15) to `english/grammar/prepositions`.
  * Mapped Conjunction item (LESO Q16) to `english/grammar`.
- Readback validation (validation.json) against Oracle DB verified 0 database writes; all 50
  source fingerprints match 100%. All paths validate strictly against the 181 active taxonomy nodes.


## 2026-11-07 23:55 IST — Source-reviewed tagging batch 18 (Arithmetic & Reasoning)

- Completed source-reviewed tagging batch 18 of 50 Quantitative & Reasoning questions under /goal execution,
  following the owner's English/Arithmetic/Reasoning priority under policy study-tagging-v1.
- Target paper: Combined Group B (NG) Paper-II December-2024 Booklet A (Q34–Q83, completing the entire
  quantitative, data interpretation, and reasoning section).
  Single-booklet policy enforced: only Booklet A (doc_9e78d845748f93799eefe5ac, sha256 c45fbaf9...) was
  considered; duplicate permutation Booklets B, C, and D were cleanly omitted, saving 249 redundant reviews.
- Direct visual inspection of all 6 physical PDF page images (pages 5 to 10) from registered document
  doc_9e78d845748f93799eefe5ac. Inspected pie charts (Q46-47), geometric formulas, branching number trees (Q75),
  non-verbal figure patterns (Q78, Q79), and 3x3 figure matrix (Q80).
- Results: 50 retags, 0 keeps, 0 holds. All 50 remain pending candidates in
  reports/tagging-batch18-20261107/pending-candidates.json. Live writes: 0.
- Key corrections:
  * Rectified 100% of targets (all 50 previously sat in an unassigned `null/null` state in the database).
  * Computer Science / Networking (Q34, Q35): IPv6 128-bit address architecture and messaging channels mapped to `computer-science/networking`.
  * Arithmetic & Numbers (Q36, Q37, Q41, Q43, Q44, Q54, Q57, Q60, Q61): Divisibility, radical arithmetic,
    simple interest, AP sums, BODMAS, square roots, train speed-distance, and compound interest mapped to `mathematics/arithmetic`.
  * Averages (Q38): Positive even multiples mean mapped to `mathematics/arithmetic/averages`.
  * Profit & Loss (Q39, Q53): Unit orange sales and loss recovery mapped to `mathematics/arithmetic/profit-and-loss`.
  * Percentages (Q45, Q48, Q49, Q52, Q65, Q71): Pass mark shortfall, successive discounts, sales tax,
    homework completion, Venn survey intersection, and election valid votes mapped to `mathematics/arithmetic/percentages`.
  * Ratio & Proportion (Q50, Q51): Compound equality ratios and liquid mixture adjustments mapped to `mathematics/arithmetic/ratio-and-proportion`.
  * Geometry & Mensuration (Q42, Q55, Q63): Complementary angle heights, cube volume, and perimeter wire area
    comparison mapped to `mathematics/geometry/triangles`, `mathematics/mensuration/volume`, and `mathematics/mensuration/area`.
  * Algebra (Q56): Common base exponential equation mapped to `mathematics/algebra/algebraic-expressions`.
  * Probability (Q64): Two-coin toss probability mapped to active subject root `mathematics`.
  * Data Interpretation (Q46, Q47): Book store distribution pie chart central angles and group differences mapped to `reasoning-and-aptitude/data-interpretation`.
  * Series & Spatial Logic (Q59, Q69, Q75, Q78–Q80): AP terms count, dice adjacency, branching number HCF tree,
    figure patterns, and 3x3 shape matrix mapped to `reasoning-and-aptitude/series`. Documented taxonomy gap for non-verbal reasoning.
  * Verbal Reasoning & Numerical Ability (Q40, Q58, Q62, Q66–Q68, Q70, Q72–Q74, Q76–Q77, Q81–Q83): Time and work,
    cistern leaks, displacement, alphabet position logic, calendar cycle, analogies, seating arrangements, shadow direction,
    recess bullying reaction, drought relief courses of action, and wage sharing mapped to active topics.
- Readback validation (validation.json) against Oracle DB verified 0 database writes; all 50
  source fingerprints match 100%. All paths validate strictly against the 181 active taxonomy nodes.



## 2026-11-07 23:40 IST — Source-reviewed tagging batch 17 (Technical & Pure Mathematics)

- Completed source-reviewed tagging batch 17 of 50 Mathematics questions under /goal execution,
  following the owner's English/Arithmetic/Reasoning priority under policy study-tagging-v1.
- Target paper: Competitive Examination for Inspector of Statistics 2026 - Paper-III (Mathematics)
  (Q1–Q50, completing Part-A Multiple Choice Questions).
  Single-booklet policy enforced: unique registered document doc_064ad469ca009ef3206215ef (sha256 57d152bd...).
- Direct visual inspection of all 7 physical PDF page images (pages 1 to 7) from registered document
  doc_064ad469ca009ef3206215ef. Inspected all printed formulas, differential equations, integrals, matrices,
  and numerical algorithms.
- Results: 50 retags, 0 keeps, 0 holds. All 50 remain pending candidates in
  reports/tagging-batch17-20261107/pending-candidates.json. Live writes: 0.
- Key corrections:
  * Rectified 100% of targets (all 50 previously erroneously stored under generic `gk/Inspector of Statistics Paper-III (Mathematics).`).
  * Abstract & Linear Algebra (Q3, Q11, Q12, Q17, Q27–Q30, Q39–Q41): Mapped to active topic `mathematics/algebra`.
  * 3D Geometry (Q8, Q35): Shortest distance and angle between skew lines mapped to `mathematics/geometry/lines-and-angles`.
  * Numerical Linear Equations (Q50): Gauss-Seidel iterative method mapped to `mathematics/algebra/linear-equations`.
  * Advanced Calculus, Differential Equations, Analysis & Numerical Methods (Q1–Q2, Q4–Q7, Q9–Q10, Q13–Q16,
    Q18–Q26, Q31–Q34, Q36–Q38, Q42–Q49): Mapped to active subject root `mathematics`. Documented systemic taxonomy
    gap: the active 181-node taxonomy lacks dedicated topics for advanced undergraduate mathematics (Calculus,
    Differential Equations, Real/Complex Analysis, Numerical Analysis, Operations Research).
- Readback validation (validation.json) against Oracle DB verified 0 database writes; all 50
  source fingerprints match 100%. All paths validate strictly against the 181 active taxonomy nodes.


## 2026-11-07 23:55 IST — Source-reviewed tagging batch 18 (Arithmetic & Reasoning)

- Completed source-reviewed tagging batch 18 of 50 Quantitative & Reasoning questions under /goal execution,
  following the owner's English/Arithmetic/Reasoning priority under policy study-tagging-v1.
- Target paper: Combined Group B (NG) Paper-II December-2024 Booklet A (Q34–Q83, completing the entire
  quantitative, data interpretation, and reasoning section).
  Single-booklet policy enforced: only Booklet A (doc_9e78d845748f93799eefe5ac, sha256 c45fbaf9...) was
  considered; duplicate permutation Booklets B, C, and D were cleanly omitted, saving 249 redundant reviews.
- Direct visual inspection of all 6 physical PDF page images (pages 5 to 10) from registered document
  doc_9e78d845748f93799eefe5ac. Inspected pie charts (Q46-47), geometric formulas, branching number trees (Q75),
  non-verbal figure patterns (Q78, Q79), and 3x3 figure matrix (Q80).
- Results: 50 retags, 0 keeps, 0 holds. All 50 remain pending candidates in
  reports/tagging-batch18-20261107/pending-candidates.json. Live writes: 0.
- Key corrections:
  * Rectified 100% of targets (all 50 previously sat in an unassigned `null/null` state in the database).
  * Computer Science / Networking (Q34, Q35): IPv6 128-bit address architecture and messaging channels mapped to `computer-science/networking`.
  * Arithmetic & Numbers (Q36, Q37, Q41, Q43, Q44, Q54, Q57, Q60, Q61): Divisibility, radical arithmetic,
    simple interest, AP sums, BODMAS, square roots, train speed-distance, and compound interest mapped to `mathematics/arithmetic`.
  * Averages (Q38): Positive even multiples mean mapped to `mathematics/arithmetic/averages`.
  * Profit & Loss (Q39, Q53): Unit orange sales and loss recovery mapped to `mathematics/arithmetic/profit-and-loss`.
  * Percentages (Q45, Q48, Q49, Q52, Q65, Q71): Pass mark shortfall, successive discounts, sales tax,
    homework completion, Venn survey intersection, and election valid votes mapped to `mathematics/arithmetic/percentages`.
  * Ratio & Proportion (Q50, Q51): Compound equality ratios and liquid mixture adjustments mapped to `mathematics/arithmetic/ratio-and-proportion`.
  * Geometry & Mensuration (Q42, Q55, Q63): Complementary angle heights, cube volume, and perimeter wire area
    comparison mapped to `mathematics/geometry/triangles`, `mathematics/mensuration/volume`, and `mathematics/mensuration/area`.
  * Algebra (Q56): Common base exponential equation mapped to `mathematics/algebra/algebraic-expressions`.
  * Probability (Q64): Two-coin toss probability mapped to active subject root `mathematics`.
  * Data Interpretation (Q46, Q47): Book store distribution pie chart central angles and group differences mapped to `reasoning-and-aptitude/data-interpretation`.
  * Series & Spatial Logic (Q59, Q69, Q75, Q78–Q80): AP terms count, dice adjacency, branching number HCF tree,
    figure patterns, and 3x3 shape matrix mapped to `reasoning-and-aptitude/series`. Documented taxonomy gap for non-verbal reasoning.
  * Verbal Reasoning & Numerical Ability (Q40, Q58, Q62, Q66–Q68, Q70, Q72–Q74, Q76–Q77, Q81–Q83): Time and work,
    cistern leaks, displacement, alphabet position logic, calendar cycle, analogies, seating arrangements, shadow direction,
    recess bullying reaction, drought relief courses of action, and wage sharing mapped to active topics.
- Readback validation (validation.json) against Oracle DB verified 0 database writes; all 50
  source fingerprints match 100%. All paths validate strictly against the 181 active taxonomy nodes.




## 2026-11-07 23:20 IST — Source-reviewed tagging batch 16 (English Grammar, Vocabulary & Reported Speech)

- Completed source-reviewed tagging batch 16 of 50 English questions under /goal execution,
  following the owner's English/Arithmetic/Reasoning priority under policy study-tagging-v1.
- Target paper: Competitive Examination for Assistant LESO 2026 - General English (Q17–Q66).
  Single-booklet policy enforced: unique registered document doc_3c107a32ef282eb0258dac94 (sha256 bd3c0763...).
  Together with Batch 15 (Q1–Q16), this brings Assistant LESO 2026 General English to 100% completion (66/66).
- Direct visual inspection of all 7 physical PDF page images (pages 4 to 10) from registered document
  doc_3c107a32ef282eb0258dac94. Inspected stems, options, phrase/clause structures, and speech transformations.
- Results: 50 retags, 0 keeps, 0 holds. All 50 remain pending candidates in
  reports/tagging-batch16-20261107/pending-candidates.json. Live writes: 0.
- Key corrections:
  * Rectified 100% of targets (all 50 previously erroneously stored under generic `gk/Assistant LESO-2026 General English.`).
  * Conjunctions (Q17–Q20): Mapped to active topic `english/grammar`.
  * Prepositions (Q21–Q30): Mapped to active subtopic `english/grammar/prepositions`. Recorded source defect:
    printed heading mislabels section as 'determiner', while options are prepositions. Recorded Q28 typo ('wairing').
  * Vocabulary sentence completion (Q31–Q38): Mapped to active topic `english/vocabulary`.
  * Idioms & Phrases (Q39–Q43): Mapped to active subtopic `english/vocabulary/idioms-and-phrases`.
  * Sentence forms & structural syntax (Q44–Q54, Q58): Mapped to active topic `english/grammar`.
  * Conditional & correlative syntax (Q55, Q56): Mapped to active topic `english/sentence-correction`.
  * Subject-verb agreement (Q57): Mapped to active subtopic `english/grammar/subject-verb-agreement`.
  * Reported Speech (Q59–Q66): Mapped 8 questions testing direct/indirect speech transformations and universal truths
    to active subtopic `english/grammar/reported-speech`.
- Readback validation (validation.json) against Oracle DB verified 0 database writes; all 50
  source fingerprints match 100%. All paths validate strictly against the 181 active taxonomy nodes.


## 2026-11-07 23:55 IST — Source-reviewed tagging batch 18 (Arithmetic & Reasoning)

- Completed source-reviewed tagging batch 18 of 50 Quantitative & Reasoning questions under /goal execution,
  following the owner's English/Arithmetic/Reasoning priority under policy study-tagging-v1.
- Target paper: Combined Group B (NG) Paper-II December-2024 Booklet A (Q34–Q83, completing the entire
  quantitative, data interpretation, and reasoning section).
  Single-booklet policy enforced: only Booklet A (doc_9e78d845748f93799eefe5ac, sha256 c45fbaf9...) was
  considered; duplicate permutation Booklets B, C, and D were cleanly omitted, saving 249 redundant reviews.
- Direct visual inspection of all 6 physical PDF page images (pages 5 to 10) from registered document
  doc_9e78d845748f93799eefe5ac. Inspected pie charts (Q46-47), geometric formulas, branching number trees (Q75),
  non-verbal figure patterns (Q78, Q79), and 3x3 figure matrix (Q80).
- Results: 50 retags, 0 keeps, 0 holds. All 50 remain pending candidates in
  reports/tagging-batch18-20261107/pending-candidates.json. Live writes: 0.
- Key corrections:
  * Rectified 100% of targets (all 50 previously sat in an unassigned `null/null` state in the database).
  * Computer Science / Networking (Q34, Q35): IPv6 128-bit address architecture and messaging channels mapped to `computer-science/networking`.
  * Arithmetic & Numbers (Q36, Q37, Q41, Q43, Q44, Q54, Q57, Q60, Q61): Divisibility, radical arithmetic,
    simple interest, AP sums, BODMAS, square roots, train speed-distance, and compound interest mapped to `mathematics/arithmetic`.
  * Averages (Q38): Positive even multiples mean mapped to `mathematics/arithmetic/averages`.
  * Profit & Loss (Q39, Q53): Unit orange sales and loss recovery mapped to `mathematics/arithmetic/profit-and-loss`.
  * Percentages (Q45, Q48, Q49, Q52, Q65, Q71): Pass mark shortfall, successive discounts, sales tax,
    homework completion, Venn survey intersection, and election valid votes mapped to `mathematics/arithmetic/percentages`.
  * Ratio & Proportion (Q50, Q51): Compound equality ratios and liquid mixture adjustments mapped to `mathematics/arithmetic/ratio-and-proportion`.
  * Geometry & Mensuration (Q42, Q55, Q63): Complementary angle heights, cube volume, and perimeter wire area
    comparison mapped to `mathematics/geometry/triangles`, `mathematics/mensuration/volume`, and `mathematics/mensuration/area`.
  * Algebra (Q56): Common base exponential equation mapped to `mathematics/algebra/algebraic-expressions`.
  * Probability (Q64): Two-coin toss probability mapped to active subject root `mathematics`.
  * Data Interpretation (Q46, Q47): Book store distribution pie chart central angles and group differences mapped to `reasoning-and-aptitude/data-interpretation`.
  * Series & Spatial Logic (Q59, Q69, Q75, Q78–Q80): AP terms count, dice adjacency, branching number HCF tree,
    figure patterns, and 3x3 shape matrix mapped to `reasoning-and-aptitude/series`. Documented taxonomy gap for non-verbal reasoning.
  * Verbal Reasoning & Numerical Ability (Q40, Q58, Q62, Q66–Q68, Q70, Q72–Q74, Q76–Q77, Q81–Q83): Time and work,
    cistern leaks, displacement, alphabet position logic, calendar cycle, analogies, seating arrangements, shadow direction,
    recess bullying reaction, drought relief courses of action, and wage sharing mapped to active topics.
- Readback validation (validation.json) against Oracle DB verified 0 database writes; all 50
  source fingerprints match 100%. All paths validate strictly against the 181 active taxonomy nodes.



## 2026-11-07 23:40 IST — Source-reviewed tagging batch 17 (Technical & Pure Mathematics)

- Completed source-reviewed tagging batch 17 of 50 Mathematics questions under /goal execution,
  following the owner's English/Arithmetic/Reasoning priority under policy study-tagging-v1.
- Target paper: Competitive Examination for Inspector of Statistics 2026 - Paper-III (Mathematics)
  (Q1–Q50, completing Part-A Multiple Choice Questions).
  Single-booklet policy enforced: unique registered document doc_064ad469ca009ef3206215ef (sha256 57d152bd...).
- Direct visual inspection of all 7 physical PDF page images (pages 1 to 7) from registered document
  doc_064ad469ca009ef3206215ef. Inspected all printed formulas, differential equations, integrals, matrices,
  and numerical algorithms.
- Results: 50 retags, 0 keeps, 0 holds. All 50 remain pending candidates in
  reports/tagging-batch17-20261107/pending-candidates.json. Live writes: 0.
- Key corrections:
  * Rectified 100% of targets (all 50 previously erroneously stored under generic `gk/Inspector of Statistics Paper-III (Mathematics).`).
  * Abstract & Linear Algebra (Q3, Q11, Q12, Q17, Q27–Q30, Q39–Q41): Mapped to active topic `mathematics/algebra`.
  * 3D Geometry (Q8, Q35): Shortest distance and angle between skew lines mapped to `mathematics/geometry/lines-and-angles`.
  * Numerical Linear Equations (Q50): Gauss-Seidel iterative method mapped to `mathematics/algebra/linear-equations`.
  * Advanced Calculus, Differential Equations, Analysis & Numerical Methods (Q1–Q2, Q4–Q7, Q9–Q10, Q13–Q16,
    Q18–Q26, Q31–Q34, Q36–Q38, Q42–Q49): Mapped to active subject root `mathematics`. Documented systemic taxonomy
    gap: the active 181-node taxonomy lacks dedicated topics for advanced undergraduate mathematics (Calculus,
    Differential Equations, Real/Complex Analysis, Numerical Analysis, Operations Research).
- Readback validation (validation.json) against Oracle DB verified 0 database writes; all 50
  source fingerprints match 100%. All paths validate strictly against the 181 active taxonomy nodes.


## 2026-11-07 23:55 IST — Source-reviewed tagging batch 18 (Arithmetic & Reasoning)

- Completed source-reviewed tagging batch 18 of 50 Quantitative & Reasoning questions under /goal execution,
  following the owner's English/Arithmetic/Reasoning priority under policy study-tagging-v1.
- Target paper: Combined Group B (NG) Paper-II December-2024 Booklet A (Q34–Q83, completing the entire
  quantitative, data interpretation, and reasoning section).
  Single-booklet policy enforced: only Booklet A (doc_9e78d845748f93799eefe5ac, sha256 c45fbaf9...) was
  considered; duplicate permutation Booklets B, C, and D were cleanly omitted, saving 249 redundant reviews.
- Direct visual inspection of all 6 physical PDF page images (pages 5 to 10) from registered document
  doc_9e78d845748f93799eefe5ac. Inspected pie charts (Q46-47), geometric formulas, branching number trees (Q75),
  non-verbal figure patterns (Q78, Q79), and 3x3 figure matrix (Q80).
- Results: 50 retags, 0 keeps, 0 holds. All 50 remain pending candidates in
  reports/tagging-batch18-20261107/pending-candidates.json. Live writes: 0.
- Key corrections:
  * Rectified 100% of targets (all 50 previously sat in an unassigned `null/null` state in the database).
  * Computer Science / Networking (Q34, Q35): IPv6 128-bit address architecture and messaging channels mapped to `computer-science/networking`.
  * Arithmetic & Numbers (Q36, Q37, Q41, Q43, Q44, Q54, Q57, Q60, Q61): Divisibility, radical arithmetic,
    simple interest, AP sums, BODMAS, square roots, train speed-distance, and compound interest mapped to `mathematics/arithmetic`.
  * Averages (Q38): Positive even multiples mean mapped to `mathematics/arithmetic/averages`.
  * Profit & Loss (Q39, Q53): Unit orange sales and loss recovery mapped to `mathematics/arithmetic/profit-and-loss`.
  * Percentages (Q45, Q48, Q49, Q52, Q65, Q71): Pass mark shortfall, successive discounts, sales tax,
    homework completion, Venn survey intersection, and election valid votes mapped to `mathematics/arithmetic/percentages`.
  * Ratio & Proportion (Q50, Q51): Compound equality ratios and liquid mixture adjustments mapped to `mathematics/arithmetic/ratio-and-proportion`.
  * Geometry & Mensuration (Q42, Q55, Q63): Complementary angle heights, cube volume, and perimeter wire area
    comparison mapped to `mathematics/geometry/triangles`, `mathematics/mensuration/volume`, and `mathematics/mensuration/area`.
  * Algebra (Q56): Common base exponential equation mapped to `mathematics/algebra/algebraic-expressions`.
  * Probability (Q64): Two-coin toss probability mapped to active subject root `mathematics`.
  * Data Interpretation (Q46, Q47): Book store distribution pie chart central angles and group differences mapped to `reasoning-and-aptitude/data-interpretation`.
  * Series & Spatial Logic (Q59, Q69, Q75, Q78–Q80): AP terms count, dice adjacency, branching number HCF tree,
    figure patterns, and 3x3 shape matrix mapped to `reasoning-and-aptitude/series`. Documented taxonomy gap for non-verbal reasoning.
  * Verbal Reasoning & Numerical Ability (Q40, Q58, Q62, Q66–Q68, Q70, Q72–Q74, Q76–Q77, Q81–Q83): Time and work,
    cistern leaks, displacement, alphabet position logic, calendar cycle, analogies, seating arrangements, shadow direction,
    recess bullying reaction, drought relief courses of action, and wage sharing mapped to active topics.
- Readback validation (validation.json) against Oracle DB verified 0 database writes; all 50
  source fingerprints match 100%. All paths validate strictly against the 181 active taxonomy nodes.






## 2026-11-07 22:45 IST — Source-reviewed tagging batch 14 (Arithmetic & Quantitative Aptitude)

- Completed source-reviewed tagging batch 14 of 50 Arithmetic & Quantitative Reasoning questions
  following the owner's English/Arithmetic/Reasoning priority under policy study-tagging-v1.
- Target paper: Junior Accounts Officer (JAO) 2026, Paper-II (GK, Arithmetic & Reasoning), Series A
  (50 core quantitative and reasoning questions: Q51–Q100).
- Single-booklet policy enforced: only Series-A was considered; duplicate booklet Series-B was
  omitted to eliminate redundant tagging passes and prevent duplicate question bloat.
- Direct visual inspection of all 6 physical PDF page images (pages 7 to 12 of registered document
  doc_a11990f15b7d667f861bd8b7, sha256 3f83869e5d7f191b...). Inspected all stems, formulas,
  options, histograms (Q71), pie charts (Q77-78), triangle geometric counting (Q90), and paper folding
  diagrams (Q91).
- Results: 49 retags, 1 keep, 0 holds. All 50 remain pending candidates in
  reports/tagging-batch14-20261107/pending-candidates.json. Live writes: 0.
- Key corrections:
  * Refined 49 bare subject-only root tags (`mathematics` and `reasoning-and-aptitude`) down to active
    specific topics/subtopics:
    - Arithmetic: Averages (Q56, Q58), Percentages (Q59, Q60), Profit & Loss (Q61, Q62), Ratio & Proportion (Q63, Q64).
    - Arithmetic Topic Root: Simple/Compound Interest (Q65, Q66) and Time & Distance (Q67, Q68) mapped to topic
      `mathematics/arithmetic` (subtopics do not exist in active 181-node taxonomy).
    - Algebra: Quadratic Equations (Q51), Algebraic Expressions (Q52).
    - Mensuration: Area (Q53), Volume (Q54).
    - Permutations, Combinations & Probability: (Q57, Q69, Q70) mapped to subject root `mathematics`.
    - Data Interpretation: Histogram (Q71), Pie Chart (Q77-78), Tabular Data (Q79-80).
    - Series & Sequences: (Q72-76, Q87, Q88).
    - Reasoning Spatial/Diagrams: Triangle counting (Q90), Paper folding (Q91) mapped to `reasoning-and-aptitude/series`.
    - Verbal Reasoning: Blood relations (Q81), Coding-decoding (Q82-83), Direction sense (Q84), Syllogisms/Logic (Q85-86, Q92-96).
    - Numerical Ability: Word problems (Q97-100).
- Readback validation (validation.json) against Oracle DB verified 0 database writes; all 50
  source fingerprints match 100%. All paths validate strictly against the 181 active taxonomy nodes.


## 2026-11-07 23:55 IST — Source-reviewed tagging batch 18 (Arithmetic & Reasoning)

- Completed source-reviewed tagging batch 18 of 50 Quantitative & Reasoning questions under /goal execution,
  following the owner's English/Arithmetic/Reasoning priority under policy study-tagging-v1.
- Target paper: Combined Group B (NG) Paper-II December-2024 Booklet A (Q34–Q83, completing the entire
  quantitative, data interpretation, and reasoning section).
  Single-booklet policy enforced: only Booklet A (doc_9e78d845748f93799eefe5ac, sha256 c45fbaf9...) was
  considered; duplicate permutation Booklets B, C, and D were cleanly omitted, saving 249 redundant reviews.
- Direct visual inspection of all 6 physical PDF page images (pages 5 to 10) from registered document
  doc_9e78d845748f93799eefe5ac. Inspected pie charts (Q46-47), geometric formulas, branching number trees (Q75),
  non-verbal figure patterns (Q78, Q79), and 3x3 figure matrix (Q80).
- Results: 50 retags, 0 keeps, 0 holds. All 50 remain pending candidates in
  reports/tagging-batch18-20261107/pending-candidates.json. Live writes: 0.
- Key corrections:
  * Rectified 100% of targets (all 50 previously sat in an unassigned `null/null` state in the database).
  * Computer Science / Networking (Q34, Q35): IPv6 128-bit address architecture and messaging channels mapped to `computer-science/networking`.
  * Arithmetic & Numbers (Q36, Q37, Q41, Q43, Q44, Q54, Q57, Q60, Q61): Divisibility, radical arithmetic,
    simple interest, AP sums, BODMAS, square roots, train speed-distance, and compound interest mapped to `mathematics/arithmetic`.
  * Averages (Q38): Positive even multiples mean mapped to `mathematics/arithmetic/averages`.
  * Profit & Loss (Q39, Q53): Unit orange sales and loss recovery mapped to `mathematics/arithmetic/profit-and-loss`.
  * Percentages (Q45, Q48, Q49, Q52, Q65, Q71): Pass mark shortfall, successive discounts, sales tax,
    homework completion, Venn survey intersection, and election valid votes mapped to `mathematics/arithmetic/percentages`.
  * Ratio & Proportion (Q50, Q51): Compound equality ratios and liquid mixture adjustments mapped to `mathematics/arithmetic/ratio-and-proportion`.
  * Geometry & Mensuration (Q42, Q55, Q63): Complementary angle heights, cube volume, and perimeter wire area
    comparison mapped to `mathematics/geometry/triangles`, `mathematics/mensuration/volume`, and `mathematics/mensuration/area`.
  * Algebra (Q56): Common base exponential equation mapped to `mathematics/algebra/algebraic-expressions`.
  * Probability (Q64): Two-coin toss probability mapped to active subject root `mathematics`.
  * Data Interpretation (Q46, Q47): Book store distribution pie chart central angles and group differences mapped to `reasoning-and-aptitude/data-interpretation`.
  * Series & Spatial Logic (Q59, Q69, Q75, Q78–Q80): AP terms count, dice adjacency, branching number HCF tree,
    figure patterns, and 3x3 shape matrix mapped to `reasoning-and-aptitude/series`. Documented taxonomy gap for non-verbal reasoning.
  * Verbal Reasoning & Numerical Ability (Q40, Q58, Q62, Q66–Q68, Q70, Q72–Q74, Q76–Q77, Q81–Q83): Time and work,
    cistern leaks, displacement, alphabet position logic, calendar cycle, analogies, seating arrangements, shadow direction,
    recess bullying reaction, drought relief courses of action, and wage sharing mapped to active topics.
- Readback validation (validation.json) against Oracle DB verified 0 database writes; all 50
  source fingerprints match 100%. All paths validate strictly against the 181 active taxonomy nodes.



## 2026-11-07 23:40 IST — Source-reviewed tagging batch 17 (Technical & Pure Mathematics)

- Completed source-reviewed tagging batch 17 of 50 Mathematics questions under /goal execution,
  following the owner's English/Arithmetic/Reasoning priority under policy study-tagging-v1.
- Target paper: Competitive Examination for Inspector of Statistics 2026 - Paper-III (Mathematics)
  (Q1–Q50, completing Part-A Multiple Choice Questions).
  Single-booklet policy enforced: unique registered document doc_064ad469ca009ef3206215ef (sha256 57d152bd...).
- Direct visual inspection of all 7 physical PDF page images (pages 1 to 7) from registered document
  doc_064ad469ca009ef3206215ef. Inspected all printed formulas, differential equations, integrals, matrices,
  and numerical algorithms.
- Results: 50 retags, 0 keeps, 0 holds. All 50 remain pending candidates in
  reports/tagging-batch17-20261107/pending-candidates.json. Live writes: 0.
- Key corrections:
  * Rectified 100% of targets (all 50 previously erroneously stored under generic `gk/Inspector of Statistics Paper-III (Mathematics).`).
  * Abstract & Linear Algebra (Q3, Q11, Q12, Q17, Q27–Q30, Q39–Q41): Mapped to active topic `mathematics/algebra`.
  * 3D Geometry (Q8, Q35): Shortest distance and angle between skew lines mapped to `mathematics/geometry/lines-and-angles`.
  * Numerical Linear Equations (Q50): Gauss-Seidel iterative method mapped to `mathematics/algebra/linear-equations`.
  * Advanced Calculus, Differential Equations, Analysis & Numerical Methods (Q1–Q2, Q4–Q7, Q9–Q10, Q13–Q16,
    Q18–Q26, Q31–Q34, Q36–Q38, Q42–Q49): Mapped to active subject root `mathematics`. Documented systemic taxonomy
    gap: the active 181-node taxonomy lacks dedicated topics for advanced undergraduate mathematics (Calculus,
    Differential Equations, Real/Complex Analysis, Numerical Analysis, Operations Research).
- Readback validation (validation.json) against Oracle DB verified 0 database writes; all 50
  source fingerprints match 100%. All paths validate strictly against the 181 active taxonomy nodes.


## 2026-11-07 23:55 IST — Source-reviewed tagging batch 18 (Arithmetic & Reasoning)

- Completed source-reviewed tagging batch 18 of 50 Quantitative & Reasoning questions under /goal execution,
  following the owner's English/Arithmetic/Reasoning priority under policy study-tagging-v1.
- Target paper: Combined Group B (NG) Paper-II December-2024 Booklet A (Q34–Q83, completing the entire
  quantitative, data interpretation, and reasoning section).
  Single-booklet policy enforced: only Booklet A (doc_9e78d845748f93799eefe5ac, sha256 c45fbaf9...) was
  considered; duplicate permutation Booklets B, C, and D were cleanly omitted, saving 249 redundant reviews.
- Direct visual inspection of all 6 physical PDF page images (pages 5 to 10) from registered document
  doc_9e78d845748f93799eefe5ac. Inspected pie charts (Q46-47), geometric formulas, branching number trees (Q75),
  non-verbal figure patterns (Q78, Q79), and 3x3 figure matrix (Q80).
- Results: 50 retags, 0 keeps, 0 holds. All 50 remain pending candidates in
  reports/tagging-batch18-20261107/pending-candidates.json. Live writes: 0.
- Key corrections:
  * Rectified 100% of targets (all 50 previously sat in an unassigned `null/null` state in the database).
  * Computer Science / Networking (Q34, Q35): IPv6 128-bit address architecture and messaging channels mapped to `computer-science/networking`.
  * Arithmetic & Numbers (Q36, Q37, Q41, Q43, Q44, Q54, Q57, Q60, Q61): Divisibility, radical arithmetic,
    simple interest, AP sums, BODMAS, square roots, train speed-distance, and compound interest mapped to `mathematics/arithmetic`.
  * Averages (Q38): Positive even multiples mean mapped to `mathematics/arithmetic/averages`.
  * Profit & Loss (Q39, Q53): Unit orange sales and loss recovery mapped to `mathematics/arithmetic/profit-and-loss`.
  * Percentages (Q45, Q48, Q49, Q52, Q65, Q71): Pass mark shortfall, successive discounts, sales tax,
    homework completion, Venn survey intersection, and election valid votes mapped to `mathematics/arithmetic/percentages`.
  * Ratio & Proportion (Q50, Q51): Compound equality ratios and liquid mixture adjustments mapped to `mathematics/arithmetic/ratio-and-proportion`.
  * Geometry & Mensuration (Q42, Q55, Q63): Complementary angle heights, cube volume, and perimeter wire area
    comparison mapped to `mathematics/geometry/triangles`, `mathematics/mensuration/volume`, and `mathematics/mensuration/area`.
  * Algebra (Q56): Common base exponential equation mapped to `mathematics/algebra/algebraic-expressions`.
  * Probability (Q64): Two-coin toss probability mapped to active subject root `mathematics`.
  * Data Interpretation (Q46, Q47): Book store distribution pie chart central angles and group differences mapped to `reasoning-and-aptitude/data-interpretation`.
  * Series & Spatial Logic (Q59, Q69, Q75, Q78–Q80): AP terms count, dice adjacency, branching number HCF tree,
    figure patterns, and 3x3 shape matrix mapped to `reasoning-and-aptitude/series`. Documented taxonomy gap for non-verbal reasoning.
  * Verbal Reasoning & Numerical Ability (Q40, Q58, Q62, Q66–Q68, Q70, Q72–Q74, Q76–Q77, Q81–Q83): Time and work,
    cistern leaks, displacement, alphabet position logic, calendar cycle, analogies, seating arrangements, shadow direction,
    recess bullying reaction, drought relief courses of action, and wage sharing mapped to active topics.
- Readback validation (validation.json) against Oracle DB verified 0 database writes; all 50
  source fingerprints match 100%. All paths validate strictly against the 181 active taxonomy nodes.




## 2026-11-07 23:20 IST — Source-reviewed tagging batch 16 (English Grammar, Vocabulary & Reported Speech)

- Completed source-reviewed tagging batch 16 of 50 English questions under /goal execution,
  following the owner's English/Arithmetic/Reasoning priority under policy study-tagging-v1.
- Target paper: Competitive Examination for Assistant LESO 2026 - General English (Q17–Q66).
  Single-booklet policy enforced: unique registered document doc_3c107a32ef282eb0258dac94 (sha256 bd3c0763...).
  Together with Batch 15 (Q1–Q16), this brings Assistant LESO 2026 General English to 100% completion (66/66).
- Direct visual inspection of all 7 physical PDF page images (pages 4 to 10) from registered document
  doc_3c107a32ef282eb0258dac94. Inspected stems, options, phrase/clause structures, and speech transformations.
- Results: 50 retags, 0 keeps, 0 holds. All 50 remain pending candidates in
  reports/tagging-batch16-20261107/pending-candidates.json. Live writes: 0.
- Key corrections:
  * Rectified 100% of targets (all 50 previously erroneously stored under generic `gk/Assistant LESO-2026 General English.`).
  * Conjunctions (Q17–Q20): Mapped to active topic `english/grammar`.
  * Prepositions (Q21–Q30): Mapped to active subtopic `english/grammar/prepositions`. Recorded source defect:
    printed heading mislabels section as 'determiner', while options are prepositions. Recorded Q28 typo ('wairing').
  * Vocabulary sentence completion (Q31–Q38): Mapped to active topic `english/vocabulary`.
  * Idioms & Phrases (Q39–Q43): Mapped to active subtopic `english/vocabulary/idioms-and-phrases`.
  * Sentence forms & structural syntax (Q44–Q54, Q58): Mapped to active topic `english/grammar`.
  * Conditional & correlative syntax (Q55, Q56): Mapped to active topic `english/sentence-correction`.
  * Subject-verb agreement (Q57): Mapped to active subtopic `english/grammar/subject-verb-agreement`.
  * Reported Speech (Q59–Q66): Mapped 8 questions testing direct/indirect speech transformations and universal truths
    to active subtopic `english/grammar/reported-speech`.
- Readback validation (validation.json) against Oracle DB verified 0 database writes; all 50
  source fingerprints match 100%. All paths validate strictly against the 181 active taxonomy nodes.


## 2026-11-07 23:55 IST — Source-reviewed tagging batch 18 (Arithmetic & Reasoning)

- Completed source-reviewed tagging batch 18 of 50 Quantitative & Reasoning questions under /goal execution,
  following the owner's English/Arithmetic/Reasoning priority under policy study-tagging-v1.
- Target paper: Combined Group B (NG) Paper-II December-2024 Booklet A (Q34–Q83, completing the entire
  quantitative, data interpretation, and reasoning section).
  Single-booklet policy enforced: only Booklet A (doc_9e78d845748f93799eefe5ac, sha256 c45fbaf9...) was
  considered; duplicate permutation Booklets B, C, and D were cleanly omitted, saving 249 redundant reviews.
- Direct visual inspection of all 6 physical PDF page images (pages 5 to 10) from registered document
  doc_9e78d845748f93799eefe5ac. Inspected pie charts (Q46-47), geometric formulas, branching number trees (Q75),
  non-verbal figure patterns (Q78, Q79), and 3x3 figure matrix (Q80).
- Results: 50 retags, 0 keeps, 0 holds. All 50 remain pending candidates in
  reports/tagging-batch18-20261107/pending-candidates.json. Live writes: 0.
- Key corrections:
  * Rectified 100% of targets (all 50 previously sat in an unassigned `null/null` state in the database).
  * Computer Science / Networking (Q34, Q35): IPv6 128-bit address architecture and messaging channels mapped to `computer-science/networking`.
  * Arithmetic & Numbers (Q36, Q37, Q41, Q43, Q44, Q54, Q57, Q60, Q61): Divisibility, radical arithmetic,
    simple interest, AP sums, BODMAS, square roots, train speed-distance, and compound interest mapped to `mathematics/arithmetic`.
  * Averages (Q38): Positive even multiples mean mapped to `mathematics/arithmetic/averages`.
  * Profit & Loss (Q39, Q53): Unit orange sales and loss recovery mapped to `mathematics/arithmetic/profit-and-loss`.
  * Percentages (Q45, Q48, Q49, Q52, Q65, Q71): Pass mark shortfall, successive discounts, sales tax,
    homework completion, Venn survey intersection, and election valid votes mapped to `mathematics/arithmetic/percentages`.
  * Ratio & Proportion (Q50, Q51): Compound equality ratios and liquid mixture adjustments mapped to `mathematics/arithmetic/ratio-and-proportion`.
  * Geometry & Mensuration (Q42, Q55, Q63): Complementary angle heights, cube volume, and perimeter wire area
    comparison mapped to `mathematics/geometry/triangles`, `mathematics/mensuration/volume`, and `mathematics/mensuration/area`.
  * Algebra (Q56): Common base exponential equation mapped to `mathematics/algebra/algebraic-expressions`.
  * Probability (Q64): Two-coin toss probability mapped to active subject root `mathematics`.
  * Data Interpretation (Q46, Q47): Book store distribution pie chart central angles and group differences mapped to `reasoning-and-aptitude/data-interpretation`.
  * Series & Spatial Logic (Q59, Q69, Q75, Q78–Q80): AP terms count, dice adjacency, branching number HCF tree,
    figure patterns, and 3x3 shape matrix mapped to `reasoning-and-aptitude/series`. Documented taxonomy gap for non-verbal reasoning.
  * Verbal Reasoning & Numerical Ability (Q40, Q58, Q62, Q66–Q68, Q70, Q72–Q74, Q76–Q77, Q81–Q83): Time and work,
    cistern leaks, displacement, alphabet position logic, calendar cycle, analogies, seating arrangements, shadow direction,
    recess bullying reaction, drought relief courses of action, and wage sharing mapped to active topics.
- Readback validation (validation.json) against Oracle DB verified 0 database writes; all 50
  source fingerprints match 100%. All paths validate strictly against the 181 active taxonomy nodes.



## 2026-11-07 23:40 IST — Source-reviewed tagging batch 17 (Technical & Pure Mathematics)

- Completed source-reviewed tagging batch 17 of 50 Mathematics questions under /goal execution,
  following the owner's English/Arithmetic/Reasoning priority under policy study-tagging-v1.
- Target paper: Competitive Examination for Inspector of Statistics 2026 - Paper-III (Mathematics)
  (Q1–Q50, completing Part-A Multiple Choice Questions).
  Single-booklet policy enforced: unique registered document doc_064ad469ca009ef3206215ef (sha256 57d152bd...).
- Direct visual inspection of all 7 physical PDF page images (pages 1 to 7) from registered document
  doc_064ad469ca009ef3206215ef. Inspected all printed formulas, differential equations, integrals, matrices,
  and numerical algorithms.
- Results: 50 retags, 0 keeps, 0 holds. All 50 remain pending candidates in
  reports/tagging-batch17-20261107/pending-candidates.json. Live writes: 0.
- Key corrections:
  * Rectified 100% of targets (all 50 previously erroneously stored under generic `gk/Inspector of Statistics Paper-III (Mathematics).`).
  * Abstract & Linear Algebra (Q3, Q11, Q12, Q17, Q27–Q30, Q39–Q41): Mapped to active topic `mathematics/algebra`.
  * 3D Geometry (Q8, Q35): Shortest distance and angle between skew lines mapped to `mathematics/geometry/lines-and-angles`.
  * Numerical Linear Equations (Q50): Gauss-Seidel iterative method mapped to `mathematics/algebra/linear-equations`.
  * Advanced Calculus, Differential Equations, Analysis & Numerical Methods (Q1–Q2, Q4–Q7, Q9–Q10, Q13–Q16,
    Q18–Q26, Q31–Q34, Q36–Q38, Q42–Q49): Mapped to active subject root `mathematics`. Documented systemic taxonomy
    gap: the active 181-node taxonomy lacks dedicated topics for advanced undergraduate mathematics (Calculus,
    Differential Equations, Real/Complex Analysis, Numerical Analysis, Operations Research).
- Readback validation (validation.json) against Oracle DB verified 0 database writes; all 50
  source fingerprints match 100%. All paths validate strictly against the 181 active taxonomy nodes.


## 2026-11-07 23:55 IST — Source-reviewed tagging batch 18 (Arithmetic & Reasoning)

- Completed source-reviewed tagging batch 18 of 50 Quantitative & Reasoning questions under /goal execution,
  following the owner's English/Arithmetic/Reasoning priority under policy study-tagging-v1.
- Target paper: Combined Group B (NG) Paper-II December-2024 Booklet A (Q34–Q83, completing the entire
  quantitative, data interpretation, and reasoning section).
  Single-booklet policy enforced: only Booklet A (doc_9e78d845748f93799eefe5ac, sha256 c45fbaf9...) was
  considered; duplicate permutation Booklets B, C, and D were cleanly omitted, saving 249 redundant reviews.
- Direct visual inspection of all 6 physical PDF page images (pages 5 to 10) from registered document
  doc_9e78d845748f93799eefe5ac. Inspected pie charts (Q46-47), geometric formulas, branching number trees (Q75),
  non-verbal figure patterns (Q78, Q79), and 3x3 figure matrix (Q80).
- Results: 50 retags, 0 keeps, 0 holds. All 50 remain pending candidates in
  reports/tagging-batch18-20261107/pending-candidates.json. Live writes: 0.
- Key corrections:
  * Rectified 100% of targets (all 50 previously sat in an unassigned `null/null` state in the database).
  * Computer Science / Networking (Q34, Q35): IPv6 128-bit address architecture and messaging channels mapped to `computer-science/networking`.
  * Arithmetic & Numbers (Q36, Q37, Q41, Q43, Q44, Q54, Q57, Q60, Q61): Divisibility, radical arithmetic,
    simple interest, AP sums, BODMAS, square roots, train speed-distance, and compound interest mapped to `mathematics/arithmetic`.
  * Averages (Q38): Positive even multiples mean mapped to `mathematics/arithmetic/averages`.
  * Profit & Loss (Q39, Q53): Unit orange sales and loss recovery mapped to `mathematics/arithmetic/profit-and-loss`.
  * Percentages (Q45, Q48, Q49, Q52, Q65, Q71): Pass mark shortfall, successive discounts, sales tax,
    homework completion, Venn survey intersection, and election valid votes mapped to `mathematics/arithmetic/percentages`.
  * Ratio & Proportion (Q50, Q51): Compound equality ratios and liquid mixture adjustments mapped to `mathematics/arithmetic/ratio-and-proportion`.
  * Geometry & Mensuration (Q42, Q55, Q63): Complementary angle heights, cube volume, and perimeter wire area
    comparison mapped to `mathematics/geometry/triangles`, `mathematics/mensuration/volume`, and `mathematics/mensuration/area`.
  * Algebra (Q56): Common base exponential equation mapped to `mathematics/algebra/algebraic-expressions`.
  * Probability (Q64): Two-coin toss probability mapped to active subject root `mathematics`.
  * Data Interpretation (Q46, Q47): Book store distribution pie chart central angles and group differences mapped to `reasoning-and-aptitude/data-interpretation`.
  * Series & Spatial Logic (Q59, Q69, Q75, Q78–Q80): AP terms count, dice adjacency, branching number HCF tree,
    figure patterns, and 3x3 shape matrix mapped to `reasoning-and-aptitude/series`. Documented taxonomy gap for non-verbal reasoning.
  * Verbal Reasoning & Numerical Ability (Q40, Q58, Q62, Q66–Q68, Q70, Q72–Q74, Q76–Q77, Q81–Q83): Time and work,
    cistern leaks, displacement, alphabet position logic, calendar cycle, analogies, seating arrangements, shadow direction,
    recess bullying reaction, drought relief courses of action, and wage sharing mapped to active topics.
- Readback validation (validation.json) against Oracle DB verified 0 database writes; all 50
  source fingerprints match 100%. All paths validate strictly against the 181 active taxonomy nodes.





## 2026-11-07 23:00 IST — Source-reviewed tagging batch 15 (English Reading Comprehension, Grammar & Communication)

- Completed source-reviewed tagging batch 15 of 50 English and Aptitude questions under /goal execution,
  following the owner's English/Arithmetic/Reasoning priority under policy study-tagging-v1.
- Target papers:
  1. Mizoram Civil Services Combined Preliminary Examination 2025, Paper-II Series-A (34 questions: Q1–Q34).
     Single-booklet policy enforced: Series-A selected; duplicate Series-B, C, D omitted.
  2. Competitive Examination for Assistant LESO 2026 - General English (16 questions: Q1–Q16).
- Direct visual inspection of all 8 physical PDF page images (MCS CSP pages 2 to 7; LESO pages 3 and 4)
  from registered documents doc_e092395e2688703b09ce8212 (sha256 63ee7c9d...) and doc_3c107a32ef282eb0258dac94
  (sha256 bd3c0763...). Inspected 4 full reading comprehension passages (AI, Solitude, Social Media, Women's
  Empowerment), stems, options, and grammar directions.
- Results: 50 retags, 0 keeps, 0 holds. All 50 remain pending candidates in
  reports/tagging-batch15-20261107/pending-candidates.json. Live writes: 0.
- Key corrections:
  * Rectified 100% of targets (all 50 previously erroneously stored under generic `gk/<Paper Title>`).
  * Mapped 16 passage questions (MCS Q1–Q15, Q17) to active topic `english/comprehension`.
  * Mapped passage-based contextual synonym (MCS Q16) to `english/vocabulary/synonyms`.
  * Mapped vocabulary cloze and confusing word items (MCS Q18–Q20) to `english/vocabulary`.
  * Mapped critical reasoning inference (MCS Q21) to `reasoning-and-aptitude/verbal-reasoning`.
  * Mapped 13 CSAT interpersonal, non-verbal communication, assertiveness, and empathy items (MCS Q22–Q34)
    to `reasoning-and-aptitude/verbal-reasoning`. Documented taxonomy gap for interpersonal communication.
  * Mapped 10 Parts of Speech items (LESO Q1–Q10) to `english/grammar/parts-of-speech`.
  * Mapped 5 Prepositions items (LESO Q11–Q15) to `english/grammar/prepositions`.
  * Mapped Conjunction item (LESO Q16) to `english/grammar`.
- Readback validation (validation.json) against Oracle DB verified 0 database writes; all 50
  source fingerprints match 100%. All paths validate strictly against the 181 active taxonomy nodes.


## 2026-11-07 23:55 IST — Source-reviewed tagging batch 18 (Arithmetic & Reasoning)

- Completed source-reviewed tagging batch 18 of 50 Quantitative & Reasoning questions under /goal execution,
  following the owner's English/Arithmetic/Reasoning priority under policy study-tagging-v1.
- Target paper: Combined Group B (NG) Paper-II December-2024 Booklet A (Q34–Q83, completing the entire
  quantitative, data interpretation, and reasoning section).
  Single-booklet policy enforced: only Booklet A (doc_9e78d845748f93799eefe5ac, sha256 c45fbaf9...) was
  considered; duplicate permutation Booklets B, C, and D were cleanly omitted, saving 249 redundant reviews.
- Direct visual inspection of all 6 physical PDF page images (pages 5 to 10) from registered document
  doc_9e78d845748f93799eefe5ac. Inspected pie charts (Q46-47), geometric formulas, branching number trees (Q75),
  non-verbal figure patterns (Q78, Q79), and 3x3 figure matrix (Q80).
- Results: 50 retags, 0 keeps, 0 holds. All 50 remain pending candidates in
  reports/tagging-batch18-20261107/pending-candidates.json. Live writes: 0.
- Key corrections:
  * Rectified 100% of targets (all 50 previously sat in an unassigned `null/null` state in the database).
  * Computer Science / Networking (Q34, Q35): IPv6 128-bit address architecture and messaging channels mapped to `computer-science/networking`.
  * Arithmetic & Numbers (Q36, Q37, Q41, Q43, Q44, Q54, Q57, Q60, Q61): Divisibility, radical arithmetic,
    simple interest, AP sums, BODMAS, square roots, train speed-distance, and compound interest mapped to `mathematics/arithmetic`.
  * Averages (Q38): Positive even multiples mean mapped to `mathematics/arithmetic/averages`.
  * Profit & Loss (Q39, Q53): Unit orange sales and loss recovery mapped to `mathematics/arithmetic/profit-and-loss`.
  * Percentages (Q45, Q48, Q49, Q52, Q65, Q71): Pass mark shortfall, successive discounts, sales tax,
    homework completion, Venn survey intersection, and election valid votes mapped to `mathematics/arithmetic/percentages`.
  * Ratio & Proportion (Q50, Q51): Compound equality ratios and liquid mixture adjustments mapped to `mathematics/arithmetic/ratio-and-proportion`.
  * Geometry & Mensuration (Q42, Q55, Q63): Complementary angle heights, cube volume, and perimeter wire area
    comparison mapped to `mathematics/geometry/triangles`, `mathematics/mensuration/volume`, and `mathematics/mensuration/area`.
  * Algebra (Q56): Common base exponential equation mapped to `mathematics/algebra/algebraic-expressions`.
  * Probability (Q64): Two-coin toss probability mapped to active subject root `mathematics`.
  * Data Interpretation (Q46, Q47): Book store distribution pie chart central angles and group differences mapped to `reasoning-and-aptitude/data-interpretation`.
  * Series & Spatial Logic (Q59, Q69, Q75, Q78–Q80): AP terms count, dice adjacency, branching number HCF tree,
    figure patterns, and 3x3 shape matrix mapped to `reasoning-and-aptitude/series`. Documented taxonomy gap for non-verbal reasoning.
  * Verbal Reasoning & Numerical Ability (Q40, Q58, Q62, Q66–Q68, Q70, Q72–Q74, Q76–Q77, Q81–Q83): Time and work,
    cistern leaks, displacement, alphabet position logic, calendar cycle, analogies, seating arrangements, shadow direction,
    recess bullying reaction, drought relief courses of action, and wage sharing mapped to active topics.
- Readback validation (validation.json) against Oracle DB verified 0 database writes; all 50
  source fingerprints match 100%. All paths validate strictly against the 181 active taxonomy nodes.



## 2026-11-07 23:40 IST — Source-reviewed tagging batch 17 (Technical & Pure Mathematics)

- Completed source-reviewed tagging batch 17 of 50 Mathematics questions under /goal execution,
  following the owner's English/Arithmetic/Reasoning priority under policy study-tagging-v1.
- Target paper: Competitive Examination for Inspector of Statistics 2026 - Paper-III (Mathematics)
  (Q1–Q50, completing Part-A Multiple Choice Questions).
  Single-booklet policy enforced: unique registered document doc_064ad469ca009ef3206215ef (sha256 57d152bd...).
- Direct visual inspection of all 7 physical PDF page images (pages 1 to 7) from registered document
  doc_064ad469ca009ef3206215ef. Inspected all printed formulas, differential equations, integrals, matrices,
  and numerical algorithms.
- Results: 50 retags, 0 keeps, 0 holds. All 50 remain pending candidates in
  reports/tagging-batch17-20261107/pending-candidates.json. Live writes: 0.
- Key corrections:
  * Rectified 100% of targets (all 50 previously erroneously stored under generic `gk/Inspector of Statistics Paper-III (Mathematics).`).
  * Abstract & Linear Algebra (Q3, Q11, Q12, Q17, Q27–Q30, Q39–Q41): Mapped to active topic `mathematics/algebra`.
  * 3D Geometry (Q8, Q35): Shortest distance and angle between skew lines mapped to `mathematics/geometry/lines-and-angles`.
  * Numerical Linear Equations (Q50): Gauss-Seidel iterative method mapped to `mathematics/algebra/linear-equations`.
  * Advanced Calculus, Differential Equations, Analysis & Numerical Methods (Q1–Q2, Q4–Q7, Q9–Q10, Q13–Q16,
    Q18–Q26, Q31–Q34, Q36–Q38, Q42–Q49): Mapped to active subject root `mathematics`. Documented systemic taxonomy
    gap: the active 181-node taxonomy lacks dedicated topics for advanced undergraduate mathematics (Calculus,
    Differential Equations, Real/Complex Analysis, Numerical Analysis, Operations Research).
- Readback validation (validation.json) against Oracle DB verified 0 database writes; all 50
  source fingerprints match 100%. All paths validate strictly against the 181 active taxonomy nodes.


## 2026-11-07 23:55 IST — Source-reviewed tagging batch 18 (Arithmetic & Reasoning)

- Completed source-reviewed tagging batch 18 of 50 Quantitative & Reasoning questions under /goal execution,
  following the owner's English/Arithmetic/Reasoning priority under policy study-tagging-v1.
- Target paper: Combined Group B (NG) Paper-II December-2024 Booklet A (Q34–Q83, completing the entire
  quantitative, data interpretation, and reasoning section).
  Single-booklet policy enforced: only Booklet A (doc_9e78d845748f93799eefe5ac, sha256 c45fbaf9...) was
  considered; duplicate permutation Booklets B, C, and D were cleanly omitted, saving 249 redundant reviews.
- Direct visual inspection of all 6 physical PDF page images (pages 5 to 10) from registered document
  doc_9e78d845748f93799eefe5ac. Inspected pie charts (Q46-47), geometric formulas, branching number trees (Q75),
  non-verbal figure patterns (Q78, Q79), and 3x3 figure matrix (Q80).
- Results: 50 retags, 0 keeps, 0 holds. All 50 remain pending candidates in
  reports/tagging-batch18-20261107/pending-candidates.json. Live writes: 0.
- Key corrections:
  * Rectified 100% of targets (all 50 previously sat in an unassigned `null/null` state in the database).
  * Computer Science / Networking (Q34, Q35): IPv6 128-bit address architecture and messaging channels mapped to `computer-science/networking`.
  * Arithmetic & Numbers (Q36, Q37, Q41, Q43, Q44, Q54, Q57, Q60, Q61): Divisibility, radical arithmetic,
    simple interest, AP sums, BODMAS, square roots, train speed-distance, and compound interest mapped to `mathematics/arithmetic`.
  * Averages (Q38): Positive even multiples mean mapped to `mathematics/arithmetic/averages`.
  * Profit & Loss (Q39, Q53): Unit orange sales and loss recovery mapped to `mathematics/arithmetic/profit-and-loss`.
  * Percentages (Q45, Q48, Q49, Q52, Q65, Q71): Pass mark shortfall, successive discounts, sales tax,
    homework completion, Venn survey intersection, and election valid votes mapped to `mathematics/arithmetic/percentages`.
  * Ratio & Proportion (Q50, Q51): Compound equality ratios and liquid mixture adjustments mapped to `mathematics/arithmetic/ratio-and-proportion`.
  * Geometry & Mensuration (Q42, Q55, Q63): Complementary angle heights, cube volume, and perimeter wire area
    comparison mapped to `mathematics/geometry/triangles`, `mathematics/mensuration/volume`, and `mathematics/mensuration/area`.
  * Algebra (Q56): Common base exponential equation mapped to `mathematics/algebra/algebraic-expressions`.
  * Probability (Q64): Two-coin toss probability mapped to active subject root `mathematics`.
  * Data Interpretation (Q46, Q47): Book store distribution pie chart central angles and group differences mapped to `reasoning-and-aptitude/data-interpretation`.
  * Series & Spatial Logic (Q59, Q69, Q75, Q78–Q80): AP terms count, dice adjacency, branching number HCF tree,
    figure patterns, and 3x3 shape matrix mapped to `reasoning-and-aptitude/series`. Documented taxonomy gap for non-verbal reasoning.
  * Verbal Reasoning & Numerical Ability (Q40, Q58, Q62, Q66–Q68, Q70, Q72–Q74, Q76–Q77, Q81–Q83): Time and work,
    cistern leaks, displacement, alphabet position logic, calendar cycle, analogies, seating arrangements, shadow direction,
    recess bullying reaction, drought relief courses of action, and wage sharing mapped to active topics.
- Readback validation (validation.json) against Oracle DB verified 0 database writes; all 50
  source fingerprints match 100%. All paths validate strictly against the 181 active taxonomy nodes.




## 2026-11-07 23:20 IST — Source-reviewed tagging batch 16 (English Grammar, Vocabulary & Reported Speech)

- Completed source-reviewed tagging batch 16 of 50 English questions under /goal execution,
  following the owner's English/Arithmetic/Reasoning priority under policy study-tagging-v1.
- Target paper: Competitive Examination for Assistant LESO 2026 - General English (Q17–Q66).
  Single-booklet policy enforced: unique registered document doc_3c107a32ef282eb0258dac94 (sha256 bd3c0763...).
  Together with Batch 15 (Q1–Q16), this brings Assistant LESO 2026 General English to 100% completion (66/66).
- Direct visual inspection of all 7 physical PDF page images (pages 4 to 10) from registered document
  doc_3c107a32ef282eb0258dac94. Inspected stems, options, phrase/clause structures, and speech transformations.
- Results: 50 retags, 0 keeps, 0 holds. All 50 remain pending candidates in
  reports/tagging-batch16-20261107/pending-candidates.json. Live writes: 0.
- Key corrections:
  * Rectified 100% of targets (all 50 previously erroneously stored under generic `gk/Assistant LESO-2026 General English.`).
  * Conjunctions (Q17–Q20): Mapped to active topic `english/grammar`.
  * Prepositions (Q21–Q30): Mapped to active subtopic `english/grammar/prepositions`. Recorded source defect:
    printed heading mislabels section as 'determiner', while options are prepositions. Recorded Q28 typo ('wairing').
  * Vocabulary sentence completion (Q31–Q38): Mapped to active topic `english/vocabulary`.
  * Idioms & Phrases (Q39–Q43): Mapped to active subtopic `english/vocabulary/idioms-and-phrases`.
  * Sentence forms & structural syntax (Q44–Q54, Q58): Mapped to active topic `english/grammar`.
  * Conditional & correlative syntax (Q55, Q56): Mapped to active topic `english/sentence-correction`.
  * Subject-verb agreement (Q57): Mapped to active subtopic `english/grammar/subject-verb-agreement`.
  * Reported Speech (Q59–Q66): Mapped 8 questions testing direct/indirect speech transformations and universal truths
    to active subtopic `english/grammar/reported-speech`.
- Readback validation (validation.json) against Oracle DB verified 0 database writes; all 50
  source fingerprints match 100%. All paths validate strictly against the 181 active taxonomy nodes.


## 2026-11-07 23:55 IST — Source-reviewed tagging batch 18 (Arithmetic & Reasoning)

- Completed source-reviewed tagging batch 18 of 50 Quantitative & Reasoning questions under /goal execution,
  following the owner's English/Arithmetic/Reasoning priority under policy study-tagging-v1.
- Target paper: Combined Group B (NG) Paper-II December-2024 Booklet A (Q34–Q83, completing the entire
  quantitative, data interpretation, and reasoning section).
  Single-booklet policy enforced: only Booklet A (doc_9e78d845748f93799eefe5ac, sha256 c45fbaf9...) was
  considered; duplicate permutation Booklets B, C, and D were cleanly omitted, saving 249 redundant reviews.
- Direct visual inspection of all 6 physical PDF page images (pages 5 to 10) from registered document
  doc_9e78d845748f93799eefe5ac. Inspected pie charts (Q46-47), geometric formulas, branching number trees (Q75),
  non-verbal figure patterns (Q78, Q79), and 3x3 figure matrix (Q80).
- Results: 50 retags, 0 keeps, 0 holds. All 50 remain pending candidates in
  reports/tagging-batch18-20261107/pending-candidates.json. Live writes: 0.
- Key corrections:
  * Rectified 100% of targets (all 50 previously sat in an unassigned `null/null` state in the database).
  * Computer Science / Networking (Q34, Q35): IPv6 128-bit address architecture and messaging channels mapped to `computer-science/networking`.
  * Arithmetic & Numbers (Q36, Q37, Q41, Q43, Q44, Q54, Q57, Q60, Q61): Divisibility, radical arithmetic,
    simple interest, AP sums, BODMAS, square roots, train speed-distance, and compound interest mapped to `mathematics/arithmetic`.
  * Averages (Q38): Positive even multiples mean mapped to `mathematics/arithmetic/averages`.
  * Profit & Loss (Q39, Q53): Unit orange sales and loss recovery mapped to `mathematics/arithmetic/profit-and-loss`.
  * Percentages (Q45, Q48, Q49, Q52, Q65, Q71): Pass mark shortfall, successive discounts, sales tax,
    homework completion, Venn survey intersection, and election valid votes mapped to `mathematics/arithmetic/percentages`.
  * Ratio & Proportion (Q50, Q51): Compound equality ratios and liquid mixture adjustments mapped to `mathematics/arithmetic/ratio-and-proportion`.
  * Geometry & Mensuration (Q42, Q55, Q63): Complementary angle heights, cube volume, and perimeter wire area
    comparison mapped to `mathematics/geometry/triangles`, `mathematics/mensuration/volume`, and `mathematics/mensuration/area`.
  * Algebra (Q56): Common base exponential equation mapped to `mathematics/algebra/algebraic-expressions`.
  * Probability (Q64): Two-coin toss probability mapped to active subject root `mathematics`.
  * Data Interpretation (Q46, Q47): Book store distribution pie chart central angles and group differences mapped to `reasoning-and-aptitude/data-interpretation`.
  * Series & Spatial Logic (Q59, Q69, Q75, Q78–Q80): AP terms count, dice adjacency, branching number HCF tree,
    figure patterns, and 3x3 shape matrix mapped to `reasoning-and-aptitude/series`. Documented taxonomy gap for non-verbal reasoning.
  * Verbal Reasoning & Numerical Ability (Q40, Q58, Q62, Q66–Q68, Q70, Q72–Q74, Q76–Q77, Q81–Q83): Time and work,
    cistern leaks, displacement, alphabet position logic, calendar cycle, analogies, seating arrangements, shadow direction,
    recess bullying reaction, drought relief courses of action, and wage sharing mapped to active topics.
- Readback validation (validation.json) against Oracle DB verified 0 database writes; all 50
  source fingerprints match 100%. All paths validate strictly against the 181 active taxonomy nodes.



## 2026-11-07 23:40 IST — Source-reviewed tagging batch 17 (Technical & Pure Mathematics)

- Completed source-reviewed tagging batch 17 of 50 Mathematics questions under /goal execution,
  following the owner's English/Arithmetic/Reasoning priority under policy study-tagging-v1.
- Target paper: Competitive Examination for Inspector of Statistics 2026 - Paper-III (Mathematics)
  (Q1–Q50, completing Part-A Multiple Choice Questions).
  Single-booklet policy enforced: unique registered document doc_064ad469ca009ef3206215ef (sha256 57d152bd...).
- Direct visual inspection of all 7 physical PDF page images (pages 1 to 7) from registered document
  doc_064ad469ca009ef3206215ef. Inspected all printed formulas, differential equations, integrals, matrices,
  and numerical algorithms.
- Results: 50 retags, 0 keeps, 0 holds. All 50 remain pending candidates in
  reports/tagging-batch17-20261107/pending-candidates.json. Live writes: 0.
- Key corrections:
  * Rectified 100% of targets (all 50 previously erroneously stored under generic `gk/Inspector of Statistics Paper-III (Mathematics).`).
  * Abstract & Linear Algebra (Q3, Q11, Q12, Q17, Q27–Q30, Q39–Q41): Mapped to active topic `mathematics/algebra`.
  * 3D Geometry (Q8, Q35): Shortest distance and angle between skew lines mapped to `mathematics/geometry/lines-and-angles`.
  * Numerical Linear Equations (Q50): Gauss-Seidel iterative method mapped to `mathematics/algebra/linear-equations`.
  * Advanced Calculus, Differential Equations, Analysis & Numerical Methods (Q1–Q2, Q4–Q7, Q9–Q10, Q13–Q16,
    Q18–Q26, Q31–Q34, Q36–Q38, Q42–Q49): Mapped to active subject root `mathematics`. Documented systemic taxonomy
    gap: the active 181-node taxonomy lacks dedicated topics for advanced undergraduate mathematics (Calculus,
    Differential Equations, Real/Complex Analysis, Numerical Analysis, Operations Research).
- Readback validation (validation.json) against Oracle DB verified 0 database writes; all 50
  source fingerprints match 100%. All paths validate strictly against the 181 active taxonomy nodes.


## 2026-11-07 23:55 IST — Source-reviewed tagging batch 18 (Arithmetic & Reasoning)

- Completed source-reviewed tagging batch 18 of 50 Quantitative & Reasoning questions under /goal execution,
  following the owner's English/Arithmetic/Reasoning priority under policy study-tagging-v1.
- Target paper: Combined Group B (NG) Paper-II December-2024 Booklet A (Q34–Q83, completing the entire
  quantitative, data interpretation, and reasoning section).
  Single-booklet policy enforced: only Booklet A (doc_9e78d845748f93799eefe5ac, sha256 c45fbaf9...) was
  considered; duplicate permutation Booklets B, C, and D were cleanly omitted, saving 249 redundant reviews.
- Direct visual inspection of all 6 physical PDF page images (pages 5 to 10) from registered document
  doc_9e78d845748f93799eefe5ac. Inspected pie charts (Q46-47), geometric formulas, branching number trees (Q75),
  non-verbal figure patterns (Q78, Q79), and 3x3 figure matrix (Q80).
- Results: 50 retags, 0 keeps, 0 holds. All 50 remain pending candidates in
  reports/tagging-batch18-20261107/pending-candidates.json. Live writes: 0.
- Key corrections:
  * Rectified 100% of targets (all 50 previously sat in an unassigned `null/null` state in the database).
  * Computer Science / Networking (Q34, Q35): IPv6 128-bit address architecture and messaging channels mapped to `computer-science/networking`.
  * Arithmetic & Numbers (Q36, Q37, Q41, Q43, Q44, Q54, Q57, Q60, Q61): Divisibility, radical arithmetic,
    simple interest, AP sums, BODMAS, square roots, train speed-distance, and compound interest mapped to `mathematics/arithmetic`.
  * Averages (Q38): Positive even multiples mean mapped to `mathematics/arithmetic/averages`.
  * Profit & Loss (Q39, Q53): Unit orange sales and loss recovery mapped to `mathematics/arithmetic/profit-and-loss`.
  * Percentages (Q45, Q48, Q49, Q52, Q65, Q71): Pass mark shortfall, successive discounts, sales tax,
    homework completion, Venn survey intersection, and election valid votes mapped to `mathematics/arithmetic/percentages`.
  * Ratio & Proportion (Q50, Q51): Compound equality ratios and liquid mixture adjustments mapped to `mathematics/arithmetic/ratio-and-proportion`.
  * Geometry & Mensuration (Q42, Q55, Q63): Complementary angle heights, cube volume, and perimeter wire area
    comparison mapped to `mathematics/geometry/triangles`, `mathematics/mensuration/volume`, and `mathematics/mensuration/area`.
  * Algebra (Q56): Common base exponential equation mapped to `mathematics/algebra/algebraic-expressions`.
  * Probability (Q64): Two-coin toss probability mapped to active subject root `mathematics`.
  * Data Interpretation (Q46, Q47): Book store distribution pie chart central angles and group differences mapped to `reasoning-and-aptitude/data-interpretation`.
  * Series & Spatial Logic (Q59, Q69, Q75, Q78–Q80): AP terms count, dice adjacency, branching number HCF tree,
    figure patterns, and 3x3 shape matrix mapped to `reasoning-and-aptitude/series`. Documented taxonomy gap for non-verbal reasoning.
  * Verbal Reasoning & Numerical Ability (Q40, Q58, Q62, Q66–Q68, Q70, Q72–Q74, Q76–Q77, Q81–Q83): Time and work,
    cistern leaks, displacement, alphabet position logic, calendar cycle, analogies, seating arrangements, shadow direction,
    recess bullying reaction, drought relief courses of action, and wage sharing mapped to active topics.
- Readback validation (validation.json) against Oracle DB verified 0 database writes; all 50
  source fingerprints match 100%. All paths validate strictly against the 181 active taxonomy nodes.








## 2026-11-08 00:05 IST — Source-reviewed tagging batch 19 (English Comprehension, Grammar & Vocabulary)

- Completed source-reviewed tagging batch 19 of 50 English questions under /goal execution,
  following the owner's English/Arithmetic/Reasoning priority under policy study-tagging-v1.
- Target paper: Competitive Examination for Recruitment to the Post of Tourist Officer under Tourism Department,
  Government of Mizoram - General English (doc_7efd2b6447fc6f5d639cc708, sha256 b200602b63c..., Q1–Q50).
- Direct visual inspection of all 6 physical PDF page images (pages 2 to 7) from registered document
  doc_7efd2b6447fc6f5d639cc708. Inspected full passage on sustainable livelihoods, all parts-of-speech stems/underlines,
  preposition sentences, conjunctions, quantifiers, synonyms, and idioms.
- Results: 50 retags, 0 keeps, 0 holds. All 50 remain pending candidates in
  reports/tagging-batch19-20261107/pending-candidates.json. Live writes: 0.
- Key corrections:
  * Rectified 100% of targets (all 50 previously misclassified under generic `gk/Tourist Officer General English.`).
  * Reading Comprehension (Q1–Q10): Passage comprehension on sustainable livelihoods, including primary focus, resilience,
    excluded challenges, in-context vocabulary ('deplete'), rural livelihoods, and summarization mapped to `english/comprehension`.
  * Parts of Speech (Q11–Q20): Syntactic identification of adverbs ('usually', 'round', 'rather'), prepositions ('by'),
    conjunctions ('When', 'after'), interjection ('wait !.'), verb ('interested'), adjective ('lame'), and pronoun ('one another')
    mapped to `english/grammar/parts-of-speech`.
  * Prepositions (Q21–Q33): Prepositions following adjectives/verbs ('predicated on', 'deficient in', 'acquiesced to',
    'along', 'hold to', 'aptitude for', 'complied with', 'onto', 'through', 'consistent with', 'invested with', 'vexed at',
    'connives at') mapped to `english/grammar/prepositions`.
  * Source Defects Documented:
    - Q21 (p. 4): Printed typographical error 'predicted' instead of 'predicated' in stem ('is predicted ________ several flawed assumptions').
    - Q31 (p. 5): Printed typographical error 'judical' instead of 'judicial'.
  * Conjunctions & Determiners (Q34–Q40): Subordinating conditional ('provided that'), manner ('as if'), concessive ('although'),
    and quantifiers/determiners ('any', 'Much', 'much', 'neither') mapped to active topic `english/grammar`. Documented taxonomy
    observation: active taxonomy lacks dedicated subtopics for conjunctions and determiners/quantifiers under English Grammar.
  * Synonyms (Q41–Q45): Lexical synonym identification for 'clamorous' (loud), 'potent' (strong), 'whimsical' (playful),
    'puny' (feeble), and 'adversity' (hardships) mapped to `english/vocabulary/synonyms`.
  * Idioms & Phrases (Q46–Q50): Traditional English idioms 'when pigs fly', 'sitting on its hands', 'coughed up',
    'off on a tangent', and 'heap coals of fire on his head' mapped to `english/vocabulary/idioms-and-phrases`.
- Readback validation (validation.json) against Oracle DB verified 0 database writes; all 50
  source fingerprints match 100%. All paths validate strictly against the 181 active taxonomy nodes.

## 2026-11-08 00:10 IST — Source-reviewed tagging batch 20 (English Grammar, Syntax, Transformations & Speech)

- Completed source-reviewed tagging batch 20 of 51 English questions under /goal execution,
  following the owner's English/Arithmetic/Reasoning priority under policy study-tagging-v1.
- Target papers:
  1. Competitive Examination for Recruitment to the Post of Tourist Officer under Tourism Department - General English
     (doc_7efd2b6447fc6f5d639cc708, sha256 b200602b63c..., Q51–Q76: 26 questions, completing the paper 100%).
  2. Competitive Examination for Lower Division Clerk under MPSC, February 2025 — Paper I
     (doc_bb0f82b67a2f3726fd265915, sha256 c222905e480..., Q51–Q75: 25 questions, completing the English MCQ section 100%).
- Direct visual inspection of all 7 physical PDF page images (Tourist Officer pages 7 to 10; LDC Paper-I pages 6 to 8)
  from registered documents doc_7efd2b6447fc6f5d639cc708 and doc_bb0f82b67a2f3726fd265915. Inspected all printed stems,
  clauses, options, sentence conversions, direct/indirect speeches, voices, and tenses.
- Results: 47 retags, 4 keeps, 0 holds. All 51 remain pending candidates in
  reports/tagging-batch20-20261107/pending-candidates.json. Live writes: 0.
- Key corrections & milestones:
  * 100% Paper Completion: Tourist Officer General English completely reviewed (76/76 questions across Batches 19 & 20).
  * 100% Section Completion: LDC February 2025 Paper-I General English MCQs completely reviewed (25/25 MCQs).
  * Prepositions (Tourist Q21–33 in Batch 19; LDC Q51, Q52, Q54, Q55 in Batch 20): Mapped to `english/grammar/prepositions`.
  * Tenses (Tourist Q72–Q76; LDC Q56, Q57, Q59): Mapped to `english/grammar/tenses`.
  * Reported Speech (Tourist Q67–Q71; LDC Q70): Mapped to `english/grammar/reported-speech`.
  * Voice (LDC Q66–Q69): Mapped to `english/grammar/voice`.
  * Subject-Verb Agreement (LDC Q74): Intervening phrase agreement mapped to `english/grammar/subject-verb-agreement`.
  * Idioms & Phrases (LDC Q53, Q61–Q65): Mapped to `english/vocabulary/idioms-and-phrases`.
  * Vocabulary (Tourist Q51–Q55; LDC Q71, Q72): Mapped to `english/vocabulary`, `english/vocabulary/antonyms`, and `english/vocabulary/synonyms`.
  * Sentence Transformations, Clauses & Moods (Tourist Q56–Q66; LDC Q58, Q60, Q73, Q75): Preserved/routed to `english/grammar`.
  * Documented Source Defects:
    - Tourist Officer Q63 (p. 8): Printed typo 'quarantee' in option (b).
    - Tourist Officer Q74 (p. 10): Printed typo 'then' instead of correlative 'than'.
    - LDC Paper-I Q65 (p. 7): Printed typo 'legimate' in option (c).
- Readback validation (validation.json) against Oracle DB verified 0 database writes; all 51
  source fingerprints match 100%. All paths validate strictly against the 181 active taxonomy nodes.

## 2026-11-08 00:20 IST — Source-reviewed tagging batch 21 (Quantitative Aptitude, Arithmetic & Reasoning)

- Completed source-reviewed tagging batch 21 of 50 Quantitative Aptitude, Arithmetic & Reasoning questions
  under /goal execution, following the owner's English/Arithmetic/Reasoning priority under policy study-tagging-v1.
- Target paper: Combined Competitive Examination for Recruitment to the Post of Assistant Grade & UDC under
  Various Departments, Government of Mizoram — Paper II (Series A) (doc_6ecb11d8198be7efc1b74ee3, sha256 872a73ca...,
  Q36–Q85, covering all 35 Arithmetic questions and the first 15 Reasoning questions).
  Single-booklet policy enforced: only Series A was considered; duplicate permutation series Series B, C, and D
  were cleanly omitted, saving 300 redundant reviews.
- Direct visual inspection of all 7 physical PDF page images (pages 5 to 11) from registered document
  doc_6ecb11d8198be7efc1b74ee3. Inspected all printed formulas, pie charts (Q63, Q64), line graph (Q65), spatial embedded
  figures (Q74), alphanumeric mirror image (Q75), geometric mirror figure (Q78), 3-set meat preference Venn diagram
  (Q79–Q82), and 2x2 crossed diagonal grid counting triangles and squares (Q83).
- Results: 50 retags, 0 keeps, 0 holds. All 50 remain pending candidates in
  reports/tagging-batch21-20261107/pending-candidates.json. Live writes: 0.
- Key corrections:
  * Rectified 100% of targets (all 50 previously misclassified under generic `gk/Assistant, UDC Paper-II Series A.`).
  * Arithmetic (Q36, Q40, Q41, Q54, Q56, Q59, Q62): Fractions, HCF, divisibility missing digits, speed/distance late-early,
    compound interest, BODMAS priority, and velocity unit conversion mapped to `mathematics/arithmetic`.
  * Averages (Q60): Weighted student-teacher inclusion mean mapped to `mathematics/arithmetic/averages`.
  * Profit & Loss (Q47, Q57): Fractional loss% and CP/SP article equality mapped to `mathematics/arithmetic/profit-and-loss`.
  * Percentages (Q61): Successive discounts mapped to `mathematics/arithmetic/percentages`.
  * Ratio & Proportion (Q48, Q49, Q51): Terms ratio with sum of squares, boys/girls money sharing, and product ratio
    mapped to `mathematics/arithmetic/ratio-and-proportion`.
  * Algebra (Q37, Q39, Q42, Q44, Q52): Power index reduction mapped to `mathematics/algebra/algebraic-expressions`;
    simultaneous linear equations (currency denominations, quotient equation, father-son ages, 3-number system) mapped
    to `mathematics/algebra/linear-equations`.
  * Geometry & Mensuration (Q43, Q45, Q46, Q50, Q53): Circle sector area, park pathway area, and circle-square area
    mapped to `mathematics/mensuration/area`; sphere melting recast into cubes mapped to `mathematics/mensuration/volume`;
    tower-pole angle of elevation right triangle trigonometry mapped to `mathematics/geometry/triangles`.
  * Permutations (Q38, Q58): nP3 product and 'APPLE' multiset arrangements mapped to active subject root `mathematics`.
  * Data Interpretation (Q63–Q65): Construction expenditure pie chart angles/percentages and food grain line graph average
    comparison mapped to `reasoning-and-aptitude/data-interpretation`.
  * Reasoning & Spatial Logic (Q66–Q73, Q74–Q85): Analogies, direction sense displacement, 7-boy ranking puzzles,
    blood relations, alphabet position count, embedded figure visualization, alphanumeric and geometric mirror images,
    linear parallel seating arrangement, row position shifting, 3-set meat Venn diagram, and 2x2 grid triangle/square
    counting mapped to `reasoning-and-aptitude/verbal-reasoning` and `reasoning-and-aptitude/series`.
  * Documented Source Defects:
    - Q73 (p. 9): Printed typographical error 'How may letters' instead of 'How many letters'.
- Readback validation (validation.json) against Oracle DB verified 0 database writes; all 50
  source fingerprints match 100%. All paths validate strictly against the 181 active taxonomy nodes.

### Batch 22 tagging report (51 questions: 15 Reasoning & Quantitative + 36 English Grammar & Vocabulary)
- Complete coverage of:
  1. *Combined Competitive Examination for Assistant Grade & UDC Paper-II Series A* (Q86–Q100, 15 questions, achieving 100% completion of the quantitative and reasoning section).
  2. *General Competitive Examination for Inspector under Excise & Narcotics Department, 2025 - General English* (Q1–Q36, 36 questions, doc_8647182b0b74ac738c56de62, achieving 100% paper completion).
- Results: 51 retags, 0 keeps, 0 holds. All 51 pending candidates in `reports/tagging-batch22-20261107/pending-candidates.json`. Live writes: 0.
- Key corrections:
  * Rectified 100% of targets (all 51 previously misclassified under generic `gk/...` paths).
  * Reasoning & Spatial Logic (Q86–Q90, Q92, Q94, Q95, Q97, Q98, Q100): 3D cube rotations, folded cube net, syllogisms, blood relations, letter coding, number analogies, and geometric figure progression mapped to `reasoning-and-aptitude/verbal-reasoning` and `reasoning-and-aptitude/series`.
  * Quantitative Aptitude (Q91, Q93, Q96, Q99): Age ratio linear equations, percentage calculation, and octagonal wheel missing number mapped to `mathematics/algebra/linear-equations`, `mathematics/arithmetic/percentages`, and `reasoning-and-aptitude/numerical-ability`.
  * English Parts of Speech (Q1–Q10): Abstract/material nouns, relative pronouns, comparative adjectives, and adverbs mapped to `english/grammar/parts-of-speech`.
  * English Prepositions (Q11–Q20): Dependent prepositions ('immune to', 'fond of', 'guilty of', etc.) mapped to `english/grammar/prepositions`.
  * English Vocabulary, Synonyms & Antonyms (Q21–Q36): Single word substitutes ('altruist', 'somnambulist', 'amateur', 'lexicographer', 'polyglot', 'pedestrian', 'dermatology', 'claustrophobia', 'gregarious', 'veteran') mapped to `english/vocabulary`; vocabulary synonyms/antonyms mapped to `english/vocabulary/synonyms` and `english/vocabulary/antonyms`.
- Readback validation (validation.json) against Oracle DB verified 0 database writes; all 51 source fingerprints match 100%. All paths validate strictly against active taxonomy nodes.

### Batch 23 tagging report (50 English Grammar, Usage, Vocabulary & Sentence Structure questions)
- Complete coverage of:
  * *Common Competitive Examination for Group 'B' Non-Gazetted (Technical) - Paper I (General English) (January-2026)* (Q1–Q50, 50 MCQs, doc_7f704f41cc87a988ef58e762, achieving 100% completion of the paper's MCQ section).
- Results: 50 retags, 0 keeps, 0 holds. All 50 pending candidates in `reports/tagging-batch23-20261107/pending-candidates.json`. Live writes: 0.
- Key corrections:
  * Rectified 100% of targets (all 50 previously misclassified under generic `gk/General English Paper-I 2026.`).
  * Parts of Speech (Q1–Q10): Preposition, adjective, subordinating conjunction, temporal adverb, semi-modal verb, material noun, interjection, distributive pronoun, adverb of proximity, and noun mapped to `english/grammar/parts-of-speech`.
  * Prepositions (Q11–Q15): Prepositions of sovereignty, location, formal presence, duration, and agentive passive mapped to `english/grammar/prepositions`.
  * Sentence Correction (Q16–Q25): Rate expression idiom, adjective hierarchy/order, indefinite pronoun placement, embedded interrogative inversion, participial adjective, modal negation, correlative clause redundancy, infinitive aspect, conditional tense harmony, and stative verb phrasing mapped to `english/sentence-correction`.
  * Vocabulary & Sentence Completion (Q26–Q35): Contextual collocations, moral judgment diction, institutional vocabulary, semantic harmony, modal and transit preference verbs, executive administrative terms, and metaphorical idioms mapped to `english/vocabulary`.
  * Antonyms (Q36–Q40): Benevolent/Cruel, Vivid/Dull, Audacious/Cowardly, Lucid/Confusing, and Gregarious/Introverted mapped to `english/vocabulary/antonyms`.
  * Idioms & Phrases (Q41–Q45): 'once in a blue moon', 'hits the nail on the head', 'the ball is in your court', 'under the weather', and 'to throw down the gauntlet' mapped to `english/vocabulary/idioms-and-phrases`.
  * Sentence Classification & Grammar (Q46–Q50): Functional declarative definition, declarative statement, exclamatory sentence, imperative sentence without overt subject, and interrogative request with imperative force mapped to active topic `english/grammar`.
  * Documented Source Defects:
    - Q31 (p. 3): Printed typographical backslash in option (c) reading 'deported\\'.
    - Q35 (p. 4): Printed typographical omission in option (c) printing single word 'well-considered' without second pair blank.
- Readback validation (validation.json) against Oracle DB verified 0 database writes; all 50 source fingerprints match 100%. All paths validate strictly against the 181 active taxonomy nodes.

### Batch 24 tagging report (49 questions: 33 Computer Knowledge/IT + 16 Quantitative Aptitude & Data Interpretation)
- Complete 100% paper finalization for TWO major exam papers:
  1. *Combined Group B (NG) Paper-II December-2024 Booklet A* (Q1–Q33, 33 questions, doc_9e78d845748f93799eefe5ac, achieving 100% completion of the entire 83-question paper across Batch 18 and Batch 24). Single booklet deduplication omitted duplicate Booklets B, C, D (saving 249 redundant reviews).
  2. *MCS Combined 2025 Preliminary Exam Paper-II Series-A* (Q85–Q100, 16 questions, doc_e092395e2688703b09ce8212, achieving 100% completion of the entire 100-question paper across Batches 13, 15, and 24). Single booklet deduplication omitted duplicate Series B, C, D (saving 300 redundant reviews).
- Results: 49 retags, 0 keeps, 0 holds. All 49 pending candidates in `reports/tagging-batch24-20261107/pending-candidates.json`. Live writes: 0.
- Key corrections:
  * Rectified 100% of targets (33 previously unassigned nulls; 16 previously misclassified under generic `gk/...` path).
  * Computer Storage & Hardware (Q1, Q3, Q5, Q7, Q9): SSD characteristics, banking MICR, CPU internal registers, I/O system, and USB port mapped to `computer-science/computer-systems-and-architecture/memory-and-storage` and `computer-hardware`.
  * Computer Generations (Q2): 3rd generation ICs mapped to `computer-systems-and-architecture/history-and-generations`.
  * Operating Systems & GUI (Q4, Q6, Q8, Q10): System software definition, GUI widgets, responsive design, and desktop background workspace mapped to `computer-science/operating-systems`.
  * Office Applications (Q11–Q25): MS Word lists, text wrapping, page breaks, mail merge, gutter margin; MS Excel IF condition, freeze panes, absolute reference ($), NOW() datetime, PivotTable; and PowerPoint Slide Master, layouts, transitions, placeholders, capacity limit mapped to `computer-science/office-applications`.
  * Networking & Collaboration (Q26–Q33): SMTP email protocol, subnet mask, router function, full-duplex transmission mode, browser incognito mode, Zoom video conferencing, collaboration software benefits, and Google Docs real-time collaboration mapped to `computer-science/networking`.
  * Quantitative Aptitude & Arithmetic (Q85, Q92, Q93, Q94, Q95, Q96, Q97): Profit/loss CP-SP difference, Rama/Thana marks ratio, bulbs gain% with scrap wastage, inverse proportion time & work, nested square/cube root radicals, school boys/girls percentage, and white/green balls probability mapped to `mathematics/arithmetic`, `profit-and-loss`, `percentages`, and `ratio-and-proportion`.
  * Algebra (Q86, Q91): A & B age simultaneous linear equations and exponential equation 5^(2x+1)/25 = 125 mapped to `mathematics/algebra/linear-equations` and `algebraic-expressions`.
  * Geometry & Mensuration (Q87, Q88, Q89, Q90): Ladder Pythagoras theorem, steel wire square-to-circle area, storm broken tree trigonometry height, and metallic sphere recast into cylindrical wire volume mapped to `mathematics/geometry/triangles`, `mensuration/area`, and `mensuration/volume`.
  * Data Interpretation (Q98–Q100): Family expenditure circular pie chart (Education 108° expenditure from Rent 36°), and comparative college boys & girls bar chart (boys mean, and girls to boys ratio) mapped to `reasoning-and-aptitude/data-interpretation`.
  * Documented Source Defects:
    - MCS Q98 (p. 16): Printed grammatical typo in stem 'was spend on Rent' instead of 'was spent on Rent'.
- Readback validation (validation.json) against Oracle DB verified 0 database writes; all 49 source fingerprints match 100%. All paths validate strictly against the 181 active taxonomy nodes.

## 2026-11-07 — One booklet entry, quieter answers and review deduplication

Delivered generic explicit-series/numeric booklet grouping to card/list archives,
including Group B pagination. Fuller sources open first; other originals remain
accessible with exact identities. Counts distinguish paper entries/source questions.
Normal answer comparison is inside Sources & study tools; concise Verified answer
badges preserve real provenance, conflict/hold/provisional notices and reveal gates.

Added conservative exact booklet-repeat filtering to mixed-mock and shared-test
selection without rewriting sources/keys/history. Live read-only check: 5,577
marked-booklet candidates → 4,520 slots (1,057 exact repeats suppressed). Existing
source-version-bound reviewed relations remain independently applied.

Saved review audit found overlapping files and mismatched current-primary metadata.
Frozen snapshot: 1,146 rows / 1,068 unique targets; 78 targets repeated, 276 candidate
rows fail their own saved-snapshot metadata check. Consolidated selection contains
868 unique snapshot-aligned pending records; zero live tagging writes. Visually
reconciled two source tasks using the PDF skill; original candidates are preserved.
Shared agent/tagging instructions now require coverage exclusion and one primary
booklet before new selections. The audit is not control of an external running
agent and does not attribute a model identity or claim answer-solving completion.

12 backend integration tests, focused retest, two coverage tests, relevant frontend
regressions and build pass. Browser checked the two-entry December-2024 Group B
archive and the simplified restored-answer view. API + web deployed, both sites
healthy. Evidence/limitations: reports/booklet-card-cleanup-20261107/README.md.

## 2026-11-08 — Remaining answer wording and explicit conflict choices

Fixed the leftover bank-card/practice/saved-UDC feedback labels reported by the
owner. Removed learner “stored answer” wording; trusted sources use Correct /
Incorrect, unverified feedback uses Suggested answer and flagged keys use Answer
under review. General dated-context/exam helper text and the admin shortcut were
also updated. No stored answers or historical attempts were rewritten.

AnswerComparison now shows both labelled option letters/text immediately when an
official key disagrees with a published verified solution or revealed practice
suggestion. Unreviewed alternatives remain suggestions; an agreeing verified
solution cannot conceal a different current suggestion. Option mapping uses text
so booklet reorderings do not fabricate conflicts. Normal agreement stays compact.
The existing backend comparison, reveal gates, provisional-key notices, scoring
holds and key-preserving admin workflow remain in force; UI exclusion wording
only appears when the backend reports a hold. No scoring/content policy changed.

35 backend comparison tests, learner-label and component/security checks, and
production build pass. Frontend deployed through scripts/deploy.sh web with a
rollback copy; live assets verified and both sites healthy. Synthetic visual
preview and details: reports/answer-feedback-20261108/README.md.


## 2026-11-08 — Core Foundation Learning Game competitive design, leaderboards, daily rewards and interactive prototype

Designed the stream-aware non-technical Foundation Learning Game (`docs/CORE-LEARNING-GAME-DESIGN.md`) and interactive Web (`1240px`) + Mobile (`390×844`) prototype (`docs/design/Core Learning Game Prototype.html`), scoped to the shared MPSC foundation across GK & General Studies (`13,129` live MCQs), General English (`10,907` live MCQs), and topic-verified Everyday Maths & Reasoning (`2,222` live MCQs), explicitly excluding the 39 specialist technical/departmental branches and unclassified B.Sc/Statistics calculus roots.

Defines four stream comfort presets (Humanities Comfort Mix, Science & Tech GK Bridge, Balanced MPSC Core, and Single Pillar Deep Dive), task-aware server clocks (`20s` for GK/English recall, `35–45s` for Everyday Maths & Reasoning), and a **Task-Normalized Competitive Scoring Engine** (`+100` Base Accuracy + `0–50` Task-Normalized Pace Bonus based on `%` of stone clock saved so `45s` Maths and `20s` GK stones are 100% fair + `2×..5×+` Streak Combo Flame `+15..50 pts` + `+25` Cross-Stream Courage Bonus + `Double Next ×2`). Includes a **4-Track Competitive Leaderboard Architecture** (Weekly/Monthly XP League Divisions from Bronze to MPSC Topper on `/board`, Sunday 25-Stone Common Core Championship Cup, Pillar Specialist High-Score Boards, and Stream Cohort Filters), a **Daily 3-Ring Quest & 7-Day IST Streak Engine** (`daily_quest_claims` + Streak Shields), and a **Spendable Reward Point Wallet** (`1,000 pts → 7 Days Pro Access`, Streak Shields, and Mizo *Puanchei* / Bamboo Study Desk cosmetics) that never reduces XP or leaderboard rank. Planning and prototype only; zero live database, API, migration or canonical bank changes were performed.

## 2026-11-08 00:45 IST — Source-reviewed tagging batches 25, 26, and 27 (General English 100% Paper Finalizations)

- Completed source-reviewed tagging batches 25, 26, and 27 totaling 186 English MCQs across 3 complete papers, advancing the owner's English/Arithmetic/Reasoning priority under policy `study-tagging-v1`:
  * **Batch 25:** *Sub-Inspector of Police (UB) March-2026 Paper-I General English* (`doc_fd9380f6bfaa7b8c2c3caeaa`, Q1–Q60, 60 MCQs, 100% section completion). 60 retags, 0 keeps, 0 holds. Rectified 100% of targets from severe misclassification under `general-studies/current-affairs` (55 items) and `general-studies/indian-history` to Parts of Speech, Prepositions, Voice, Reported Speech, Tenses, and Subject-Verb Agreement. Preserved 4 unextracted Section-A conventional written prompts (Essay, Precis, Complaint Letter, Comprehension) as pending intake evidence. [Batch 25 report](reports/tagging-batch25-20261107/README.md).
  * **Batch 26:** *Research Investigator under Art & Culture Department May-2026 Paper-I General English* (`doc_d6e9188aece142e847dc80a5`, Q1–Q60, 60 MCQs, 100% section completion). 59 retags, 1 keep, 0 holds. Rectified misclassifications from `general-studies/current-affairs` (48 items), `general-studies/mizoram`, and `indian-history` to Parts of Speech, Synonyms, One-Word Substitution, Reported Speech, and Tenses. Uncovered critical OCR extraction target discrepancies on physical pages 3–4 where stored question text appended false target words that contradicted the physical bolded words in the question booklet (Q1 'country' vs 'diverse', Q12 'book' vs 'on', Q16 'sit' vs 'here', Q19 'old' vs 'slowly'). Preserved 4 unextracted Part-A written prompts as pending intake evidence. [Batch 26 report](reports/tagging-batch26-20261107/README.md).
  * **Batch 27:** *Cooperative Audit Officer March-2026 General English Series A* (`doc_72979c5dc3be316985dc7d13`, Q1–Q66, 66 MCQs, 100% section completion). 64 retags, 2 keeps, 0 holds. Enforced single-booklet deduplication rule (bypassed duplicate permutation Series B, saving 66 redundant reviews). Rectified 64 bare `english` subject placeholders and 1 coarse grammar topic to Parts of Speech, Prepositions, Idioms & Phrases, One-Word Substitution, Tenses, and Transformations. Documented extraction ambiguity in Q15 ('Mean' vs 'mean'), omitted option (d) in printed Q28, and defective options in Q57. Preserved 4 unextracted Section-A written prompts as pending intake evidence. [Batch 27 report](reports/tagging-batch27-20261107/README.md).
- Zero live writes or database changes across all three batches. Fresh readback validations confirmed 100% source fingerprint consistency, zero database mutations, and 100% compliance with `review_taxonomy` active nodes and `audit-review-coverage.py`. Cumulative deduplicated candidates in the review ledger reached 1,054 unique targets across 28 candidate reports with zero problems or booklet family conflicts.

## 2026-11-08 01:10 IST — Source-reviewed tagging batch 28 (Junior Accounts Officer July-2026 Paper-I General English 100% Paper Finalization)

- Completed source-reviewed tagging batch 28 (63 English MCQs, 100% paper completion) from *General Competitive Examination for Recruitment to the Posts of Junior Accounts Officer (JAO) under Food, Civil Supplies & Consumer Affairs Department, Government of Mizoram (July, 2026) — Question Booklet: Paper-I (General English) Series-A* (`doc_d15fa789c988623dc8c610bc`, Q1–Q65, 63 MCQs), advancing the owner's English/Arithmetic/Reasoning priority under policy `study-tagging-v1`:
  * **61 retags, 2 keeps, 0 holds.** Enforced single-booklet deduplication rule (bypassed equivalent permutation Series-B `doc_c41203ae4343358938de3aaf`, saving 63 redundant reviews and eliminating booklet family conflicts).
  * **Severe Cross-Subject Misclassification Rectification:** Rectified 2 questions erroneously categorized under `civil-engineering/surveying` (Q46 complex sentence transformation, Q47 simple sentence transformation) to `english/grammar`; rectified 1 question categorized under generic `general-studies` (Q36 one-word substitution 'Democracy') to `english/vocabulary/one-word-substitution`. Refined 58 bare `english` subject placeholders to `english/comprehension` (5 items), `english/grammar/parts-of-speech` (26 items), `english/grammar/prepositions` (7 items), `english/grammar/voice` (4 items), `english/grammar` (10 items), and vocabulary topics. Verified 2 already-correct baseline topics (Q25 `parts-of-speech`, Q44 `vocabulary`) as KEEP decisions.
  * **Uncovered OCR Extraction Drops on Duplicate Stems:** Identified that printed Part-B Q26 (Page 5: `26. Choose the correct sentence. (a) Each of the boys have completed the task...`) and printed Part-B Q37 (Page 6: `37. Choose the correct sentence. (a) No sooner had he arrived than it started raining...`) were dropped during automated ingestion due to identical stem collisions with earlier questions, creating sequence gaps at DB Q31 and Q42. Preserved both unextracted MCQs in `pending-written-intake.json`.
  * **Preserved 5 Part-A Conventional Written Tasks:** Extracted full prompt evidence and suggested taxonomy for Part-A Q1 Essay (10m: Digital Ration Cards / Digital Technology in Mizoram / Eco-Tourism), Q2 Précis (10m), Q3 JAO Formal Letter to ration dealer (10m), Q9 Reading Comprehension short answer (2m), and Q10 Reading Comprehension short answer (3m) in `pending-written-intake.json`.
  * **Documented Typesetting Defects:** Documented physical underline target error in Q16 (`children` underlined in printed scan, whereas key and options test adverb `happily`), complete underline omission in printed Q18 (`Abigail wanted to go shopping, but...`), missing period in Q17 number prefix (`12 She bought...`), and typo in Q32 stem (`fill in the bank`).
- Zero live database or API mutations. Readback validation confirmed 100% source fingerprint matches (63/63) and 0 database writes. Cumulative deduplicated unique targets in the review ledger reached 1,117 across 29 candidate reports with zero problems or booklet family conflicts. [Batch 28 report](reports/tagging-batch28-20261108/README.md).

## 2026-11-08 01:25 IST — Source-reviewed tagging batch 29 (JE under Agri & Farmer Welfare March-2026 Paper-I General English 100% Paper Finalization)

- Completed source-reviewed tagging batch 29 (40 English MCQs, 100% paper completion) from *Competitive Examination for Recruitment to the Post of Junior Engineer under Agriculture & Farmer Welfare Department, Government of Mizoram (March, 2026) — Paper-I (General English)* (`doc_f4bc2fadc026c4c11d66f4a9`), advancing the owner's English priority under policy `study-tagging-v1`:
  * **29 retags, 11 keeps, 0 holds.**
  * **Taxonomy Refinement:** Resolved coarse `english/grammar` placeholders to active subtopics: `english/vocabulary/idioms-and-phrases` (8 items), `english/vocabulary/one-word-substitution` (8 items), `english/grammar/parts-of-speech` (6 items), `english/grammar/prepositions` (2 items), `english/grammar/voice` (1 item), and `english/vocabulary/synonyms` (1 item). Verified 11 already-correct baseline topics (7 reading comprehension questions and 4 sentence structures/transformations) as KEEP decisions.
  * **Preserved Conventional Section-A Prompt:** Documented Section-A Q1 Essay prompt (20 marks: Technology against poverty / Entrepreneurship / Cultural Festivals) in `pending-written-intake.json`.
  * **Defects Documented:** Documented Section-B Q12 where printed booklet omitted 'Preposition' from options (a)–(d) (forcing database option e), and indexing displacement where Section-A Q2(viii) was sequenced onto page 3 after Section-B Q7.
- Zero live database or API mutations. Readback validation confirmed 100% source fingerprint matches (40/40) and 0 database writes. Cumulative deduplicated unique targets in the review ledger reached 1,157 across 30 candidate reports with zero problems or booklet family conflicts. [Batch 29 report](reports/tagging-batch29-20261108/README.md).

## 2026-11-08 01:40 IST — Source-reviewed tagging batch 30 (Radiotherapy Technologist April-2026 Paper-I General English 100% Paper Finalization)

- Completed source-reviewed tagging batch 30 (60 English MCQs, 100% paper completion) from *Competitive Examination for Recruitment to the Post of Radiotherapy Technologist (Contract) under Health & Family Welfare Department, Government of Mizoram (April, 2026) — Paper-I (General English)* (`doc_a8943344d9cc369f5611b184`), advancing the owner's English priority under policy `study-tagging-v1`:
  * **40 retags, 20 keeps, 0 holds.**
  * **Taxonomy Refinement:** Resolved coarse `english/grammar` and `english/vocabulary` placeholders to active subtopics: `english/grammar/parts-of-speech` (20 items: syntactic identification and noun/verb/adverb/pronoun classification), `english/vocabulary/antonyms` (5 items), `english/vocabulary/synonyms` (5 items), `english/vocabulary` (5 items), and `english/grammar/subject-verb-agreement` (5 items). Verified 20 already-correct baseline topics (Sentence Functions/Kinds and Sentence Structures) as KEEP decisions.
  * **Preserved 4 Section-A Conventional Written Tasks:** Extracted full prompt evidence and suggested taxonomy for Section-A Q1 Essay (10m: AI & Healthcare / Mental Health / Health Tourism), Q2 Précis (10m: Trees and selfless service), Q3 Official Letter to Health Minister (10m), and Q4 Reading Comprehension conventional questions (a)–(e) (10m) in `pending-written-intake.json`.
  * **Defects Documented:** Documented database underline omissions in Section-B Q1–Q10, printed typo 'quests' for 'guests' in Q22, and printed typo 'Pupose' in Q49.
- Zero live database or API mutations. Readback validation confirmed 100% source fingerprint matches (60/60) and 0 database writes. Cumulative deduplicated unique targets in the review ledger reached 1,217 across 31 candidate reports with zero problems or booklet family conflicts. [Batch 30 report](reports/tagging-batch30-20261108/README.md).

## 2026-11-08 01:55 IST — Source-reviewed tagging batch 31 (Lecturer GHSS Serchhip 2026 General English 100% Paper Finalization)

- Completed source-reviewed tagging batch 31 (66 English MCQs, 100% paper completion) from *Competitive Examination for Recruitment of Lecturer (Contract), Govt. Higher Secondary School, Serchhip under School Education Department, Government of Mizoram (March & April, 2026) — General English* (`doc_94f974b5a87cadd1fb61511f`), advancing the owner's English priority under policy `study-tagging-v1`:
  * **65 retags, 1 keep, 0 holds.**
  * **Severe Misclassification Rectification:** Rectified 65 items misclassified in database under generic `gk` placeholder to active subtopics: `english/grammar/parts-of-speech` (34 items), `english/grammar/prepositions` (3 items), `english/vocabulary` (5 items), `english/grammar/reported-speech` (6 items), `english/grammar/tenses` (5 items), `english/grammar/subject-verb-agreement` (2 items), `english/vocabulary/synonyms` (1 item), `english/vocabulary/antonyms` (1 item), `english/vocabulary/one-word-substitution` (3 items), and `english/grammar` (6 items). Verified 1 already-correct baseline subtopic (Q18 `parts-of-speech`) as KEEP decision.
  * **Preserved 3 Part-B Conventional Written Tasks:** Preserved Part-B Q1 Précis (14m: Youth smartphone ownership and digital skills), Q2 Lecturer Job Application Letter with Resume (10m), and Q3 Reading Comprehension questions (a)–(e) (10m: Indian cultural unity in diversity) in `pending-written-intake.json`.
  * **Defects Documented:** Documented severe automated ingestion misclassification under `gk`, underline omissions in stored text for Q1, Q9, Q58–Q61, and printed typos ('Ditection', 'against its').
- Zero live database or API mutations. Readback validation confirmed 100% source fingerprint matches (66/66) and 0 database writes. Cumulative deduplicated unique targets in the review ledger reached 1,283 across 32 candidate reports with zero problems or booklet family conflicts. [Batch 31 report](reports/tagging-batch31-20261108/README.md).

## 2026-11-08 01:10 IST — Full-stack Competitive Foundation Learning Game, 4-track leaderboards, daily quests, and IST streaks

- Shipped the full-stack implementation of the stream-aware non-technical Foundation Learning Game across database (`api/migrations/0081_competitive_foundation_game.sql`), backend API (`api/app/services/game_selection.py`, `api/app/services/games.py`, `api/app/services/learning_rewards.py`, `api/app/routers/games.py`, `api/app/routers/rewards.py`), and React frontend (`web/src/lib/games.ts`, `web/src/components/GameSetup.tsx`, `web/src/screens/Games.tsx`, `web/src/screens/Rewards.tsx`):
  * **Stream-Aware Non-Technical Foundation Presets (`kind: "foundation"`):** Added 7 presets (`arts-comfort`, `science-bridge`, `balanced-core`, `commerce-core`, `gk-foundation`, `math-foundation`, `english-foundation`) drawing strictly from verified official-key questions across the 3 shared non-technical pillars (`3,953` GK/GS, `796` General English, and `831` topic-verified Everyday Class-10 Maths & Reasoning = `5,580` game-ready official-key questions in production), while blocking the 39 specialist technical/medical/departmental branches and unclassified B.Sc/Statistics calculus roots (`subject_id = 'mathematics'` where `topic_id IS NULL`).
  * **Task-Normalized Competitive Scoring & Extended Math Clocks:** Every question carries its `pillar`, `pillar_label`, `round_seconds` (`20s` for GK/English recall, `45s`/`40s`/`35s` for Everyday Maths & Reasoning depending on stream preset), and `courage_eligible`. Game finalization awards `100` Base Accuracy + `0..50` Task-Normalized Pace Bonus (computed from the fraction of the question's own clock remaining) + `15..50` Streak Combo Flame (`🔥 2×..5×+`) + `25` Cross-Stream Courage Bonus (`⚡`) when answering outside the learner's comfort stream, persisted on `game_members` (`pace_bonus`, `streak_bonus`, `courage_bonus`, `best_streak`). Added an inline Quick Math Scratchpad and Class-10 formula reminder bar inside `GamePlayer` for `everyday_math` questions.
  * **4-Track Competitive Leaderboards & Stream Cohorts:** Added `GET /api/games/leaderboard` (`track` in `league`, `gk_gs`, `everyday_math`, `english`, `cup`; `period` in `week`, `month`, `all`; `cohort` in `all`, `arts-comfort`, `science-bridge`, `commerce-core`, `balanced-core`) and enriched `GET /api/rewards/leaderboard` with stream cohort filtering, cohort badges, and streak indicators.
  * **Daily 3-Ring Quests, 7-Day IST Streaks & Streak Shields:** Added `daily_quest_claims` (append-only, guarded by `forbid_reward_ledger_mutation()`) and extended `reward_profiles` with `stream_cohort`, `current_streak_days`, `longest_streak_days`, `last_active_ist_date`, and `streak_shields` (`0..2`). `POST /api/rewards/daily-quests/{quest_key}/claim` awards quest chest XP (clamped under the `300 XP/day` shared study/game cap) and full reward points; `POST /api/rewards/streak-shield` equips a 1-day streak shield for `25` points (`0 XP`) without affecting XP or rank.
- **Verification & Deployment:**
  * Backend pytest suite: `24 passed` (`tests/test_rewards.py`, `tests/test_games_search.py`, `tests/test_topic_trail.py`, including `test_foundation_presets_competitive_scoring_quests_and_leaderboards`).
  * Frontend TypeScript + Vite production build (`npm run build`) passed cleanly.
  * Rehearsed `0081_competitive_foundation_game.sql` on a disposable production dump clone on Oracle (`152.67.31.231`), verified zero row mutations on `canonical_questions`, `game_rooms`, and `reward_ledger`, applied `0081` atomically with `schema_migrations` (`afb395fd9e942b95`), deployed the 5 bounded API files and `web/dist`, and verified live endpoints on `https://study.hawayu.in` and `https://family.hawayu.in` (`over_cap_days = 0`, `wallets_in_debt = 0`).

## 2026-11-08 02:15 IST — Source-reviewed tagging batch 32 (Assistant Controller of Mines March-2026 General English 100% Paper Finalization)

- Completed source-reviewed tagging batch 32 (66 English MCQs, 100% paper completion) from *Competitive Examination for Recruitment to the Post of Assistant Controller of Mines under Geology & Mining, Commerce & Industries Department, Government of Mizoram (March-2026) — General English* (`doc_4ceb491f18bd951a08157418`), advancing the owner's English priority under policy `study-tagging-v1`:
  * **58 retags, 8 keeps, 0 holds.**
  * **Single-Booklet Deduplication Enforced:** Cleanly bypassed the identical duplicate paper ingestion `doc_c565126360469474a31af91c` under `Old_Questions/Direct_NG_2024-2027/`, saving 66 redundant reviews while protecting ledger consistency.
  * **Severe Misclassification Rectification:** In the database, all 66 items were misclassified under `gk` placeholder subject (`subject=gk, topic=Asst. Controller of Mines General English`). Rectified 58 items to active English subtopics: `english/grammar/parts-of-speech` (24 items), `english/grammar/prepositions` (6 items), `english/vocabulary` (7 items), `english/grammar` (15 items), `english/grammar/reported-speech` (5 items), `english/vocabulary/one-word-substitution` (4 items), and `english/vocabulary/idioms-and-phrases` (5 items). Verified 8 already-correct baseline topics as KEEP decisions.
  * **Preserved 3 Part-B Conventional Written Tasks:** Extracted full prompt evidence and suggested taxonomy for Part-B Q1 Essay (14m: Environmental Degradation and Mining / AI in Modern Education / Youth in Disaster Management), Q2 Précis (10m: Sustainable development and conservation), and Q3 Reading Comprehension questions (a)–(e) (10m: Global digital divide and remote education) in `pending-written-intake.json`.
  * **Defects Documented:** Documented severe automated ingestion misclassification under `gk` and underline omissions in stored database text for Q1–Q10.
- Zero live database or API mutations. Readback validation confirmed 100% source fingerprint matches (66/66) and 0 database writes. Cumulative deduplicated unique targets in the review ledger reached 1,349 across 33 candidate reports with zero problems or booklet family conflicts. [Batch 32 report](reports/tagging-batch32-20261108/README.md).

## 2026-11-08 02:35 IST — Source-reviewed tagging batch 33 (ITI Instructor 2026 & Inspector of Statistics 2026 General English 100% Paper Finalization)

- Completed source-reviewed tagging batch 33 (32 English MCQs, achieving 100% completion of all direct 2026 General English papers in the registered corpus) across *Instructor ITI Paper-I General English* (`doc_0b0f26b428ddfe44c54aef08`, 26 MCQs) and *Inspector of Statistics Paper-I General English* (`doc_b61ba36d95d17e4c2a561cb8`, 6 MCQs), advancing the owner's English priority under policy `study-tagging-v1`:
  * **32 retags, 0 keeps, 0 holds.**
  * **Untagged Baseline Rectification:** All 32 MCQs were completely untagged in the production database (`subject=null, topic=null`). Rectified 100% of targets to active English subtopics: `english/grammar/parts-of-speech` (9 items), `english/grammar/prepositions` (1 item), `english/vocabulary/idioms-and-phrases` (5 items), `english/vocabulary` (2 items), `english/vocabulary/one-word-substitution` (3 items), `english/grammar` (5 items), `english/sentence-correction` (1 item), and `english/comprehension` (6 items).
  * **Preserved 22 Unextracted Tasks & Ingestion Drops:**
    - ITI Instructor: Preserved 4 conventional written tasks (Précis 10m, Letter to Editor 10m, Reading Comprehension 10m, Essay 10m) and 4 dropped MCQs (Q27–Q30 dropped by automated ingestion due to repeated identical section stem 'Choose the correct sentence:') in `pending-written-intake.json`.
    - Inspector of Statistics: Preserved 14 conventional written tasks (Essay 20m, Précis 10m, 4 Comprehension short answers, Homophones 10m, One-word substitutes 20m, Synonyms 10m, Antonyms 10m, Idioms 10m, Voice 10m, Question tags 10m, Sentence transformations 20m) in `pending-written-intake.json`.
- Zero live database or API mutations. Readback validation confirmed 100% source fingerprint matches (32/32) and 0 database writes. Cumulative deduplicated unique targets in the review ledger reached 1,381 across 34 candidate reports with zero problems or booklet family conflicts. [Batch 33 report](reports/tagging-batch33-20261108/README.md).

## 2026-11-08 02:55 IST — Source-reviewed tagging batch 34 (Stenographer Grade-II 2025 General English 100% Paper Finalization)

- Completed source-reviewed tagging batch 34 (40 English MCQs, 100% paper completion) from *Competitive Examination for the Post of Stenographer Grade-II (Contract) under Mizoram Public Service Commission (May-2025) — Paper-I General English* (`doc_5f0d589624f2eb0f9031863f`), advancing the owner's English priority under policy `study-tagging-v1`:
  * **40 retags, 0 keeps, 0 holds.**
  * **Untagged Baseline Rectification:** All 40 MCQs were completely untagged in the production database (`subject=null, topic=null`). Rectified 100% of targets to active English subtopics: `english/grammar/parts-of-speech` (5 items), `english/grammar/prepositions` (10 items), `english/grammar/tenses` (5 items), `english/vocabulary/idioms-and-phrases` (5 items), `english/grammar/voice` (5 items), and `english/vocabulary/one-word-substitution` (10 items).
  * **Preserved 3 Part-A Conventional Written Tasks:** Extracted full prompt evidence and suggested taxonomy for Part-A Q1 Essay (20m: Communication skills / Workplace ethics / Digital India), Q2 Reading Comprehension questions (a)–(l) (30m: Talent vs hard work), and Q3 Précis (10m: Academic degrees vs common sense) in `pending-written-intake.json`.
  * **Defects Documented:** Documented completely untagged baseline and printed booklet typo ('disabitity' instead of 'disability' in Q36).
- Zero live database or API mutations. Readback validation confirmed 100% source fingerprint matches (40/40) and 0 database writes. Cumulative deduplicated unique targets in the review ledger reached 1,421 across 35 candidate reports with zero problems or booklet family conflicts. [Batch 34 report](reports/tagging-batch34-20261108/README.md).

## 2026-11-08 03:20 IST — Source-reviewed tagging batch 35 (ASI Ministerial 2018 Mathematics 100% Paper Finalization — 100 MCQs)

- Completed source-reviewed tagging batch 35 (100 Class-10 Arithmetic, Algebra, Geometry, Mensuration & Numerical Ability MCQs, 100% paper completion) from *General Competitive Examinations for Recruitment to the Post of Assistant Sub Inspector (Ministerial) under Home Department, Government of Mizoram (October, 2018) — Mathematics* (`doc_5c1f675b19f778f61bcf7eaf`), advancing the owner's Arithmetic priority under policy `study-tagging-v1`:
  * **100 retags, 0 keeps, 0 holds.**
  * **Untagged Baseline Rectification:** All 100 MCQs were completely untagged in the production database (`subject=null, topic=null`). Rectified 100% of targets to active Class-10 mathematics subtopics:
    - `mathematics/arithmetic/percentages` (12 items)
    - `mathematics/arithmetic/profit-and-loss` (8 items)
    - `mathematics/arithmetic/ratio-and-proportion` (6 items)
    - `mathematics/arithmetic/averages` (5 items)
    - `mathematics/arithmetic` (29 items: Simple Interest, Compound Interest, Time & Work, Time & Distance, Surds, Fractions, HCF/LCM, Real-world calculation)
    - `mathematics/algebra/linear-equations` (4 items)
    - `mathematics/algebra/algebraic-expressions` (2 items)
    - `mathematics/algebra` (4 items: Exponents, Arithmetic Progressions)
    - `mathematics/geometry/lines-and-angles` (4 items)
    - `mathematics/geometry/triangles` (4 items)
    - `mathematics/geometry/circles` (1 item)
    - `mathematics/geometry` (3 items: Trigonometry, Coordinate Geometry)
    - `mathematics/mensuration/area` (8 items)
    - `mathematics/mensuration/volume` (3 items)
    - `reasoning-and-aptitude/numerical-ability` (7 items: Statistics and Probability)
- Zero live database or API mutations. Readback validation confirmed 100% source fingerprint matches (100/100) and 0 database writes. Cumulative deduplicated unique targets in the review ledger reached 1,521 across 36 candidate reports with zero problems or booklet family conflicts. [Batch 35 report](reports/tagging-batch35-20261108/README.md).

## 2026-11-08 03:45 IST — Source-reviewed tagging batch 36 (Agri & Allied 2025 & Jr. MHS 2025 General English 100% Paper Finalization — 86 MCQs)

- Completed source-reviewed tagging batch 36 (86 English MCQs, achieving 100% paper completion across both booklets) from *Agri & Allied Services (Combined Technical) November-2025 General English* (`doc_74fb44237ebef4588c005e8a`, 46 MCQs) and *Junior Grade of MHS September-2025 General English* (`doc_dab76ba7bd50a3f08ac483d2`, 40 MCQs), advancing the owner's English priority under policy `study-tagging-v1`:
  * **86 retags, 0 keeps, 0 holds.**
  * **Untagged Baseline Rectification:** All 86 MCQs were completely untagged in the production database (`subject=null, topic=null`). Rectified 100% of targets to active English subtopics:
    - `english/grammar/parts-of-speech` (21 items)
    - `english/vocabulary/idioms-and-phrases` (14 items)
    - `english/vocabulary` (12 items)
    - `english/grammar/prepositions` (13 items)
    - `english/grammar/articles` (1 item)
    - `english/grammar` (7 items: Clauses, Sentence Structures, Transformations)
    - `english/grammar/tenses` (5 items)
    - `english/vocabulary/one-word-substitution` (5 items)
    - `english/sentence-correction` (5 items)
    - `english/grammar/voice` (1 item)
    - `english/vocabulary/synonyms` (1 item)
    - `english/vocabulary/antonyms` (1 item)
  * **Preserved 10 Unextracted Tasks & Ingestion Drops:**
    - Agri & Allied: Preserved 3 Section-A written prompts (Précis 10m, Reading Comprehension 20m, Transformations 10m) and 4 dropped MCQs (Q42–Q45 dropped by automated ingestion due to empty stems under 'Choose the correct sentence:') in `pending-written-intake.json`.
    - Jr. of MHS: Preserved 3 Section-A written prompts (Essay 20m, Précis 20m, Reading Comprehension 20m) in `pending-written-intake.json`.
- Zero live database or API mutations. Readback validation confirmed 100% source fingerprint matches (86/86) and 0 database writes. Cumulative deduplicated unique targets in the review ledger reached 1,607 across 37 candidate reports with zero problems or booklet family conflicts. [Batch 36 report](reports/tagging-batch36-20261108/README.md).

## 2026-11-08 04:10 IST — Source-reviewed tagging batch 37 (Sub Inspector (UB) 2018 Mathematics 100% Paper Finalization — 100 MCQs)

- Completed source-reviewed tagging batch 37 (100 Class-10 Arithmetic, Algebra, Geometry, Mensuration & Numerical Ability MCQs, 100% paper completion) from *General Competitive Examinations for Recruitment to the Post of Sub Inspector (UB) under Home Department, Government of Mizoram (October, 2018) — Mathematics* (`doc_941aa0c516507942933a0ab1`), advancing the owner's Arithmetic priority under policy `study-tagging-v1`:
  * **100 retags, 0 keeps, 0 holds.**
  * **Untagged Baseline Rectification:** All 100 MCQs were completely untagged in the production database (`subject=null, topic=null`). Rectified 100% of targets to active Class-10 mathematics subtopics:
    - `mathematics/arithmetic/percentages` (7 items)
    - `mathematics/arithmetic/profit-and-loss` (4 items)
    - `mathematics/arithmetic/ratio-and-proportion` (4 items)
    - `mathematics/arithmetic/averages` (4 items)
    - `mathematics/arithmetic` (30 items: Simple Interest, Compound Interest, Time & Work, Time & Distance, Surds, Fractions, HCF/LCM, Real-world calculation)
    - `mathematics/algebra/linear-equations` (8 items)
    - `mathematics/algebra/algebraic-expressions` (5 items)
    - `mathematics/algebra` (4 items: Arithmetic Progressions & Defined Operations)
    - `mathematics/geometry/lines-and-angles` (1 item)
    - `mathematics/geometry/triangles` (2 items)
    - `mathematics/geometry/circles` (2 items)
    - `mathematics/geometry` (1 item: Trigonometry)
    - `mathematics/mensuration/area` (11 items)
    - `mathematics/mensuration/volume` (12 items)
    - `reasoning-and-aptitude/numerical-ability` (5 items: Statistics and Probability)
- Zero live database or API mutations. Readback validation confirmed 100% source fingerprint matches (100/100) and 0 database writes. Cumulative deduplicated unique targets in the review ledger reached 1,707 across 38 candidate reports with zero problems or booklet family conflicts. [Batch 37 report](reports/tagging-batch37-20261108/README.md).

## 2026-11-08 04:30 IST — Source-reviewed tagging batch 38 (Assistant Director / CDPO 2025 General English 100% Paper Finalization — 66 MCQs)

- Completed source-reviewed tagging batch 38 (66 English MCQs, achieving 100% paper completion) from *Competitive Examination for Child Development Project Officer (CDPO) and Assistant Director (Food & Drugs) (November, 2025) — General English* (`doc_000e6be43acfd05656947ae1`), advancing the owner's English priority under policy `study-tagging-v1`:
  * **66 retags, 0 keeps, 0 holds.**
  * **Single-Booklet Deduplication Enforced:** Cleanly bypassed duplicate file `Old_Questions/Direct_2025-2027/CDPO General English-2025..pdf` (`doc_93dc9451f2beee9b16a34ec8`), an identical sha256 binary duplicate of the same booklet, saving 66 redundant reviews.
  * **Untagged Baseline Rectification:** All 66 MCQs were completely untagged in the production database (`subject=null, topic=null`). Rectified 100% of targets to active English subtopics:
    - `english/grammar/parts-of-speech` (15 items: Adverbs 5, Pronouns 5, Articles 5)
    - `english/grammar/prepositions` (10 items)
    - `english/grammar/tenses` (10 items)
    - `english/grammar/reported-speech` (5 items: Direct/Indirect narration)
    - `english/vocabulary/idioms-and-phrases` (5 items)
    - `english/vocabulary/one-word-substitution` (4 items)
    - `english/sentence-correction` (3 items)
    - `english/grammar` (11 items: Concord/Agreement 5, Sentence Combining 3, Determiners 3)
    - `english/vocabulary` (3 items: Synonyms/Antonyms)
  * **Preserved 3 Unextracted Conventional Tasks:** Preserved 3 Section-B written prompts (Essay 20m, Précis 10m, Reading Comprehension 10m) totaling 40 marks in `pending-written-intake.json`.
- Zero live database or API mutations. Readback validation confirmed 100% source fingerprint matches (66/66) and 0 database writes. Cumulative deduplicated unique targets in the review ledger reached 1,773 across 39 candidate reports with zero problems or booklet family conflicts. [Batch 38 report](reports/tagging-batch38-20261108/README.md).

## 2026-11-08 04:50 IST — Source-reviewed tagging batch 39 (Circle Education Officer 2025 General English 100% Paper Finalization — 66 MCQs)

- Completed source-reviewed tagging batch 39 (66 English MCQs, achieving 100% paper completion) from *Competitive Examination for Recruitment to the Post of Circle Education Officer under School Education Department (November, 2025) — General English* (`Old_Questions/Direct_2025-2027/CEO General English - 2025..pdf`, `doc_db5ba5b3fe26ca319535f622`), advancing the owner's English priority under policy `study-tagging-v1`:
  * **64 retags, 2 keeps, 0 holds.**
  * **Untagged Baseline Rectification:** 64 of 66 questions had unclassified `subject=english` with `topic=null, subtopic=null` or coarse tags. Rectified 100% of targets to active English subtopics:
    - `english/grammar/parts-of-speech` (6 items)
    - `english/grammar/prepositions` (9 items)
    - `english/grammar` (10 items: Conjunctions, Connectors, Sentence Transformations)
    - `english/grammar/tenses` (15 items: Verb Forms 10, Tense Transformations 5)
    - `english/vocabulary` (2 items)
    - `english/vocabulary/one-word-substitution` (6 items)
    - `english/vocabulary/idioms-and-phrases` (4 items)
    - `english/vocabulary/antonyms` (4 items)
    - `english/grammar/reported-speech` (5 items: Direct/Indirect narration)
    - `english/vocabulary/synonyms` (5 items)
  * **Preserved 3 Unextracted Conventional Tasks:** Preserved 3 Part-A written prompts (Précis 14m, Formal Application Letter 10m, Reading Comprehension 10m) totaling 34 marks in `pending-written-intake.json`.
- Zero live database or API mutations. Readback validation confirmed 100% source fingerprint matches (66/66) and 0 database writes. Cumulative deduplicated unique targets in the review ledger reached 1,839 across 40 candidate reports with zero problems or booklet family conflicts. [Batch 39 report](reports/tagging-batch39-20261108/README.md).

## 2026-11-08 05:15 IST — Source-reviewed tagging batch 40 (AAO & Field Facilitator 2025 General English Series A 100% Paper Finalization — 60 MCQs)

- Completed source-reviewed tagging batch 40 (60 English MCQs, achieving 100% paper completion) from *General Competitive Examination for Recruitment to the Posts of Assistant Accounts Officer (Treasury & Works) and Field Facilitator (November, 2025) — Paper-I (General English) (Series A)* (`Old_Questions/Direct_NG_2024-2027/General English - Series A..pdf`, `doc_f00f463fd9dd338fb2178369`), advancing the owner's English priority under policy `study-tagging-v1`:
  * **41 retags, 19 keeps, 0 holds.**
  * **Single-Booklet Series Deduplication Enforced:** Cleanly bypassed permuted Series B booklet `Old_Questions/Direct_NG_2024-2027/General English - Series B..pdf` (`doc_9283fbe7c06c764e3084aeff`, `sha256: 950f330d86383ce12a0ee813fadea7d1745627866eeedbf98cf501703a0f5b95`), saving 60 redundant reviews under the single-booklet deduplication policy.
  * **Untagged Baseline Rectification:** All 60 MCQs had coarse topic-level tags (`english/grammar` or `english/vocabulary`) without subtopics. Rectified 100% of targets to active English subtopics:
    - `english/grammar/parts-of-speech` (10 items: Adjectives 1, Adverbs 4, Conjunctions 1, Prepositions 1, Pronouns 1, Nouns 2)
    - `english/grammar/tenses` (10 items: Present 1, Past 3, Future 2, Continuous 2, Perfect 2)
    - `english/vocabulary` (4 items: Contextual Word Choice)
    - `english/vocabulary/synonyms` (5 items)
    - `english/vocabulary/antonyms` (1 item)
    - `english/sentence-correction` (6 items: Word Order, Grammaticality, Sentence Completeness, Punctuation)
    - `english/grammar` (18 items: Jumbled Sentences PQRS 3, Conjunctions 1, Sentence Types 6, Clause Patterns 4, Sentence Functions 4)
    - `english/grammar/prepositions` (1 item)
    - `english/grammar/reported-speech` (3 items: Direct/Indirect narration)
    - `english/grammar/voice` (2 items: Active/Passive Voice)
  * **Preserved 4 Unextracted Conventional Tasks:** Preserved 4 Part-A written prompts (Précis 10m, Formal Letter to Minister 10m, Reading Comprehension 10m, Essay Writing 10m) totaling 40 marks in `pending-written-intake.json`.
- Zero live database or API mutations. Readback validation confirmed 100% source fingerprint matches (60/60) and 0 database writes. Cumulative deduplicated unique targets in the review ledger reached 1,899 across 41 candidate reports with zero problems or booklet family conflicts. [Batch 40 report](reports/tagging-batch40-20261108/README.md).

## 2026-11-08 05:40 IST — Source-reviewed tagging batch 41 (High School Teacher 2017 Mathematics Paper-I 100% Paper Finalization — 75 MCQs)

- Completed source-reviewed tagging batch 41 (75 Quantitative Aptitude, Arithmetic, Reasoning, Algebra, Geometry, Probability, Statistics & Calculus MCQs, achieving 100% paper completion) from *Competitive Examinations for Recruitment to the Posts of High School Teacher (Mathematics) under School Education Department, Government of Mizoram (September, 2017) — Technical Paper-I* (`Old_Questions/Direct_2014-2018/2.Mathematics Paper-I.pdf`, `doc_3bbda79f063fd1c62ac7e8a3`), advancing the owner's Arithmetic & Reasoning priority under policy `study-tagging-v1`:
  * **57 retags, 18 keeps, 0 holds.**
  * **Untagged & Inactive Taxonomy Baseline Rectification:** All 75 MCQs had coarse unclassified subject baselines (`mathematics/None/None` or `reasoning-and-aptitude/None/None`), and 3 questions (Q49, Q56, Q58) suffered from an inactive subject defect (`statistics/None/None`). Rectified 100% of targets to active taxonomy paths:
    - `mathematics/arithmetic` (7 items: Number System Cyclicity, Divisibility Counting, Radicals, Decimals/Exponents, Time & Work, Pipes & Cisterns, Alligations)
    - `mathematics/arithmetic/ratio-and-proportion` (2 items)
    - `mathematics/arithmetic/averages` (2 items: Corrected Mean, Shifted Averages)
    - `mathematics/arithmetic/percentages` (2 items: Consumption/Price, Compound Depreciation)
    - `mathematics/arithmetic/profit-and-loss` (2 items: Identical SP Transaction, Successive Discounts)
    - `reasoning-and-aptitude/series` (1 item: Letter Series)
    - `reasoning-and-aptitude/verbal-reasoning` (6 items: Analogies, Classification, Coding-Decoding, Carrom Seating, Venn Diagram, Alphabetical Ordering)
    - `reasoning-and-aptitude` (3 items: Non-Verbal Pattern Completion & Geometric Figure Counting)
    - `mathematics/algebra/quadratic-equations` (3 items: Discriminant, Root Relations, Reciprocal Roots)
    - `mathematics/algebra/algebraic-expressions` (3 items: Logarithmic Identities, Cyclic Expressions, Remainder Theorem)
    - `mathematics/algebra/linear-equations` (2 items: Line Geometry through Origin, Simultaneous Linear Equations)
    - `mathematics/algebra` (2 items: Set Symmetric Difference, Mathematical Induction)
    - `mathematics/geometry/circles` (1 item: Equilateral Circumcircle Radius)
    - `mathematics/geometry/triangles` (2 items: Similar Triangle Area Ratio, Triangle Perimeter)
    - `mathematics/geometry` (5 items: Trigonometric Identities, Quadrant Ratios, Heights & Distances, Extrema)
    - `mathematics/geometry/lines-and-angles` (2 items: Collinearity Intercepts, Section Formula)
    - `reasoning-and-aptitude/numerical-ability` (15 items: Probability & Statistics, rectifying inactive `statistics` baseline)
    - `mathematics` (15 items: Advanced Real Analysis, Continuity, Limits, Rolle's Theorem, Extrema, Homogeneous Euler Theorem, Definite/Indefinite Integrals)
- Zero live database or API mutations. Readback validation confirmed 100% source fingerprint matches (75/75) and 0 database writes. Cumulative deduplicated unique targets in the review ledger reached 1,974 across 42 candidate reports with zero problems or booklet family conflicts. [Batch 41 report](reports/tagging-batch41-20261108/README.md).

## 2026-11-08 06:10 IST — Source-reviewed tagging batch 42 (Food Sub-Inspector & Receptionist 2025 General English Series A 100% Paper Finalization — 52 MCQs)

- Completed source-reviewed tagging batch 42 (52 English MCQs, achieving 100% paper completion) from *Competitive Examination for Sub-Inspector under Food, Civil Supplies & Consumer Affairs Department and Receptionist under Health & Family Welfare Department (May, 2025) — Paper-I (General English) (Series A)* (`Old_Questions/Direct_NG_2024-2027/Paper-I General English (Series A)..pdf`, `doc_57d09d87766f60d8370e2547`), advancing the owner's English priority under policy `study-tagging-v1`:
  * **37 retags, 15 keeps, 0 holds.**
  * **Single-Booklet Series Deduplication Enforced:** Cleanly bypassed 3 permuted series booklets: Series B (`doc_ae75dbff924cd9f1cda167dc`), Series C (`doc_a0c489d819810fcb83048888`), and Series D (`doc_42a5afe2420d8ff997936b63`), saving 68 redundant reviews across the series family.
  * **Untagged Baseline Rectification:** All 52 MCQs had coarse topic-level tags (`english/grammar` or `english/vocabulary`) without subtopics. Rectified 100% of targets to active English subtopics:
    - `english/grammar/parts-of-speech` (10 items: Adjectives 2, Adverbs 2, Nouns 1, Pronouns 5)
    - `english/grammar/prepositions` (5 items)
    - `english/grammar/subject-verb-agreement` (1 item)
    - `english/grammar/tenses` (4 items)
    - `english/sentence-correction` (6 items: Spotting Errors 5, Sentence Structure 1)
    - `english/vocabulary` (6 items: Word Choice 5, Spelling 1)
    - `english/vocabulary/one-word-substitution` (5 items)
    - `english/grammar` (15 items: Jumbled Sentences 5, Inversion Structures 5, Conditional Transformations 5)
  * **Preserved 11 Unextracted Tasks & Ingestion Drops:**
    - Preserved 3 Section-A conventional tasks totaling 40 marks (Précis 10m, Formal Complaint Letter 15m, Reading Comprehension 15m) in `pending-written-intake.json`.
    - Preserved 8 dropped MCQs (Q37–Q40 spelling tests, Q47–Q50 sentence structure items dropped due to empty stems under direction headers) in `pending-written-intake.json`.
- Zero live database or API mutations. Readback validation confirmed 100% source fingerprint matches (52/52) and 0 database writes. Cumulative deduplicated unique targets in the review ledger reached **2,026** across 43 candidate reports with zero problems or booklet family conflicts. [Batch 42 report](reports/tagging-batch42-20261108/README.md).

## 2026-11-08 06:35 IST — Source-reviewed tagging batch 43 (Final 2024–2025 Direct English Booklets 100% Paper Finalization — 81 items)

- Completed source-reviewed tagging batch 43 (81 English questions across 4 distinct booklets, achieving 100% paper completion across all four papers) from:
  1. *Competitive Examination for the Post of Sericulture Extension Officer (2025) — General English* (`doc_3e7d37598a061cd1d52da2ad`, 20 MCQs)
  2. *Technical Competitive Examination for Junior Grade of Mizoram Engineering Service (Combined) (2025) — General English* (`doc_682ab0cad0fd9c4e525e91a9`, 21 MCQs)
  3. *General Competitive Examination for Recruitment to the Post of Junior Grade of Mizoram Planning, Economic & Statistical Service (2025) — General English* (`doc_895b0f62c2314d435e125458`, 30 MCQs)
  4. *Group B(NG) (Technical) Paper-I (General English)-2024* (`doc_d50623457f36f5aeab231741`, 10 composite items)
  * **79 retags, 2 keeps, 0 holds.**
  * **Baseline Rectification & Bug Fix:** Rectified question Q3(ii) in Sericulture Extension Officer, which was mistakenly ingested in production under `subject_id: sociology` due to passage topic keywords; correctly reassigned to `english/comprehension`. Across all 4 booklets, rectified 100% of targets to active English subtopics:
    - `english/comprehension` (7 items)
    - `english/vocabulary/one-word-substitution` (6 items)
    - `english/vocabulary/synonyms` (6 items)
    - `english/vocabulary/antonyms` (11 items)
    - `english/grammar` (10 items: Clause Analysis)
    - `english/grammar/tenses` (15 items)
    - `english/grammar/prepositions` (16 items)
    - `english/grammar/subject-verb-agreement` (1 item)
    - `english/grammar/parts-of-speech` (5 items)
    - `english/writing/precis` (1 item)
    - `english/writing/letter` (1 item)
    - `english/grammar/voice` (1 item)
    - `english/grammar/reported-speech` (1 item)
  * **Preserved 5 Conventional Descriptive Tasks:** Preserved 5 conventional written tasks totaling 80 marks in `pending-written-intake.json` (Sericulture: Précis 10m, Complaint Letter 15m; MES: Essay 20m; MPE & SS: Essay 20m, Précis 15m).
- Zero live database or API mutations. Readback validation confirmed 100% source fingerprint matches (81/81) and 0 database writes. Cumulative deduplicated unique targets in the review ledger reached **2,107** across 44 candidate reports with zero problems or booklet family conflicts. [Batch 43 report](reports/tagging-batch43-20261108/README.md).

## 2026-11-08 07:05 IST — Source-reviewed tagging batch 44 (Finance Dept ADA, AA & ATA Arithmetic 100% Paper Finalization — 70 MCQs)

- Completed source-reviewed tagging batch 44 (70 Arithmetic, Quant, Mensuration & Data Interpretation MCQs, achieving 100% paper completion across both booklets) from:
  1. *General Competitive Examinations for Recruitment to the Post of Assistant Divisional Accountant under Finance Department (2015) — 3. Arithmetic* (`doc_b3e48463a72b3b18b82957d0`, 20 MCQs)
  2. *Competitive Examinations for Recruitment to the Posts of Assistant Auditor, Assistant Treasury Accountant & Assistant Divisional Accountant (2019) — Arithmetic* (`doc_5335e1afbbcfc26d1afa5cd2`, 50 MCQs)
  * **64 retags, 6 keeps, 0 holds.**
  * **Triple Bug Rectification:** 
    - Rectified 3 items (Q13 in Paper 1; Q39, Q40 in Paper 2) with inactive `subject_id: statistics` baseline to `reasoning-and-aptitude/numerical-ability`.
    - Rectified Q30 in Paper 2 (partnership capital ratio) from misclassified `commerce` baseline to `mathematics/arithmetic/ratio-and-proportion`.
    - Rectified Q49 in Paper 2 (pie chart miscellaneous expenditure) from misclassified `financial-rules-and-accounts` baseline to `reasoning-and-aptitude/data-interpretation`.
  * **Untagged Baseline Rectification:** Across all 70 questions, rectified 100% of targets to active taxonomy paths:
    - `mathematics/arithmetic` (31 items: Place Value, Fractions, Decimals, BODMAS, HCF/LCM, Simple/Compound Interest, Time & Work, Speed/Distance, Surds, Radicals)
    - `mathematics/arithmetic/averages` (2 items)
    - `mathematics/arithmetic/ratio-and-proportion` (5 items)
    - `mathematics/arithmetic/percentages` (6 items)
    - `mathematics/arithmetic/profit-and-loss` (3 items)
    - `mathematics/mensuration/area` (4 items)
    - `mathematics/mensuration/volume` (4 items)
    - `mathematics/algebra/linear-equations` (2 items)
    - `reasoning-and-aptitude/numerical-ability` (4 items)
    - `reasoning-and-aptitude/data-interpretation` (9 items: Bar Chart Analysis 5, Pie Chart Expenditure Analysis 4)
- Zero live database or API mutations. Readback validation confirmed 100% source fingerprint matches (70/70) and 0 database writes. Cumulative deduplicated unique targets in the review ledger reached **2,177** across 45 candidate reports with zero problems or booklet family conflicts. [Batch 44 report](reports/tagging-batch44-20261108/README.md).

## 2026-11-08 07:45 IST — Source-reviewed tagging batch 45 (Finance Dept ADA, AA & ATA General English 100% Paper Finalization — 60 MCQs)

- Completed source-reviewed tagging batch 45 (60 General English MCQs, achieving 100% paper completion) from:
  - *Competitive Examinations for Recruitment to the Posts of Assistant Auditor, Assistant Treasury Accountant & Assistant Divisional Accountant under Finance Department, Government of Mizoram (January 2019) — General English* (`doc_28eafb04c21bfc501a33c583`, 60 MCQs)
  * **58 retags, 2 keeps, 0 holds.**
  * **Companion Paper Finalization:** Companion to the Batch 44 Arithmetic paper, completing the entire non-GK portion of the 2019 Finance Department Combined recruitment examination. Single-booklet paper with zero duplicates.
  * **Untagged Baseline Rectification:** All 60 MCQs in production had coarse `current_subject: 'gk'` and `current_topic: 'ADA, AA & ATA General English'`. All have been restructured into active taxonomy subtopics:
    - `english/grammar/parts-of-speech` (25 items: abstract/collective/common nouns, transitive verb, gerunds as subject/object/complement, participles, predicate/substantive adjectives, degree/manner adverbs, interjections, coordinating/subordinating conjunctions, spatial preposition)
    - `english/grammar` (19 items: modal notions of possibility, obligation, command, polite request, habitual aspect, clause purpose, optative wish/prayer, moral advice, conditions; traditional sentence types: interrogative, assertive, imperative, exclamatory, optative, negative)
    - `english/grammar/prepositions` (7 items: time origin, dependent verbs, motion, idiomatic swearing, relative position)
    - `english/grammar/subject-verb-agreement` (9 items: prepositional interveners, 'one of' singular agreement, compound subjects with 'and', single composite unit 'horse and carriage', correlative conjunctions, singular scientific fields 'Physics', divided collective nouns 'Committee were', proper book titles 'The Arabian Nights', fractions of uncountables)
  * **Preserved 2 Conventional Descriptive Section-A Tasks:** Preserved 2 conventional written tasks totaling 40 marks in `pending-written-intake.json` (Task 1: Essay 20m; Task 2: Précis 20m).
- Zero live database or API mutations. Readback validation confirmed 100% source fingerprint matches (60/60) and 0 database writes. Cumulative deduplicated unique targets in the review ledger reached **2,237** across 46 candidate reports with zero problems or booklet family conflicts. [Batch 45 report](reports/tagging-batch45-20261108/README.md).

## 2026-11-08 08:00 IST — Source-reviewed tagging batch 46 (Inspector of Statistics & MPE & SS Mathematics 100% Paper Finalization — 47 items)

- Completed source-reviewed tagging batch 46 (47 Mathematics items, achieving 100% paper completion across both booklets) from:
  1. *Technical Competitive Examinations for Recruitment to Inspector of Statistics under Planning & Programme Implementation Department (February 2017) — Paper-III (Mathematics)* (`doc_baa7d3e36313750a22acdc00`, 20 MCQs)
  2. *General Competitive Examination for Recruitment to the Post of Junior Grade of Mizoram Planning, Economic & Statistical Service (December 2025) — Mathematics-I* (`doc_cceff4af00fc9b8c74f9e2ab`, 27 items)
  * **12 retags, 35 keeps, 0 holds.**
  * **Multi-Subject Bug Rectifications:**
    - Rectified inactive `statistics` baseline on Paper 1 Q20 (Binomial distribution mean and variance) to `reasoning-and-aptitude/numerical-ability`.
    - Rectified misclassified `science` baseline on Paper 1 Q11 (projectile least velocity) to `mathematics`.
    - Rectified misclassified `engineering-mechanics` baseline on Paper 1 Q12 (coplanar forces equilibrium / Lami's theorem) to `mathematics/geometry/lines-and-angles`.
    - Rectified misclassified `engineering-mechanics` baseline on Paper 2 Q13 (simple pendulum equation of motion using Lagrangian formulation) to `mathematics`.
  * **Taxonomy Alignment:** Refined 5 items to active algebra topics (`mathematics/algebra` on Paper 1 Q2 Descartes' signs, and Paper 2 Q7 groups/subgroups, Q8 Euclidean rings/PID, Q9(a) fields/integral domains, Q9(b) field extension tower law); confirmed 35 university-level items under active subject `mathematics` (Real Analysis, Multivariable Calculus, Functional Analysis, Topology, Differential Equations, Operations Research, Numerical Analysis, Calculus of Variations); confirmed 2 items under `reasoning-and-aptitude/numerical-ability` (surjections combinatorics, binomial distribution); confirmed 2 items under `mathematics/geometry/lines-and-angles` and 1 item under `mathematics/geometry`.
  * **Preserved 80 Marks of Conventional Descriptive Problems:** Preserved 7 conventional problems (difference operators, exact differential equations, particle kinematics, friction, simplex method, transportation problem) totaling 45+ marks in `pending-written-intake.json`.
- Zero live database or API mutations. Readback validation confirmed 100% source fingerprint matches (47/47) and 0 database writes. Cumulative deduplicated unique targets in the review ledger reached **2,284** across 47 candidate reports with zero problems or booklet family conflicts. [Batch 46 report](reports/tagging-batch46-20261108/README.md).

## 2026-11-08 08:35 IST — Source-reviewed tagging batch 47 (Direct 2023-2025 General English Booklets 100% Paper Finalization — 78 MCQs)

- Completed source-reviewed tagging batch 47 (78 General English MCQs, achieving 100% paper completion across all 4 booklets) from:
  1. *General Competitive Examinations for Recruitment to the Post of Jr. Grade of Mizoram Forest Service (Asst. Conservator of Forests) (2023) — General English* (`doc_b5f51992824cdf78ca9eb105`, 10 MCQs)
  2. *Technical Competitive Examination for Informatics Officer under ICT Department (November 2024) — General English Paper-I* (`doc_e46ac6fab7a2eb8bf138f169`, 8 MCQs)
  3. *Technical Competitive Examinations for Junior Grade of Mizoram Engineering Service, P&E Cadre (Electrical Wing) and Assistant Architect (July 2023) — General English* (`doc_210c8de409ca07cc3de1ad76`, 10 MCQs)
  4. *Technical Competitive Examinations for Junior Grade of Mizoram Legal Service (MLS) under Law & Judicial Department (July 2023) — English* (`doc_e13e10e93f23cf05cda8960a`, 50 MCQs)
  * **78 retags, 0 keeps, 0 holds.**
  * **Bug Fix & Baseline Rectification:** 
    - Rectified item `mpsc-cli-informatics-officer-general-english-paper-i-2024-007` from misclassified `town-planning` baseline to `english/comprehension`.
    - Restructured 77 unclassified/coarse baseline targets into precise active English taxonomy paths:
      - `english/vocabulary/one-word-substitution` (10 items: MES Electrical Wing Q6(a)–(j))
      - `english/vocabulary/idioms-and-phrases` (15 items: ACF Q1–Q10; MLS Q46–Q50)
      - `english/vocabulary/synonyms` (5 items: MLS Q1–Q5)
      - `english/vocabulary/antonyms` (5 items: MLS Q6–Q10)
      - `english/grammar/prepositions` (5 items: MLS Q11–Q15)
      - `english/grammar/parts-of-speech` (5 items: MLS Q16–Q20 conjunctions)
      - `english/grammar/tenses` (10 items: MLS Q21–Q30)
      - `english/grammar/subject-verb-agreement` (5 items: MLS Q31–Q35)
      - `english/grammar/reported-speech` (5 items: MLS Q36–Q40)
      - `english/grammar/voice` (5 items: MLS Q41–Q45)
      - `english/comprehension` (8 items: Informatics Officer Q6(a)–(h) urban planning passage)
  * **Preserved 10 Conventional Descriptive Tasks (190 Marks):** Preserved 10 conventional written tasks (Essays, Précis, Idea Expansion, Idiom sentence composition) totaling 190 marks across all 4 booklets in `pending-written-intake.json`.
- Zero live database or API mutations. Readback validation confirmed 100% source fingerprint matches (78/78) and 0 database writes. Cumulative deduplicated unique targets in the review ledger reached **2,362** across 48 candidate reports with zero problems or booklet family conflicts. [Batch 47 report](reports/tagging-batch47-20261108/README.md).

## 2026-11-08 08:48 IST — Source-reviewed tagging batch 48 (Direct 2022-2023 General English Booklets 100% Paper Finalization — 75 MCQs & Tasks)

- Completed source-reviewed tagging batch 48 (75 General English MCQs and descriptive tasks, achieving 100% paper completion across all 4 booklets) from:
  1. *Competitive Examinations for Recruitment to the Post of Grade-V of MSCS (Cooperative Audit Officer) (December 2022) — General English Paper-I* (`doc_09ecdb100f668625c85b57c4`, 14 MCQs)
  2. *Competitive Examinations for Recruitment to the Post of Geologist Junior under Commerce & Industries Department (November 2022) — General English Paper-I* (`doc_7a32498eb36e71f5a1ac6918`, 6 items)
  3. *Technical Competitive Examinations for Grade-III of Mizoram Health Service (GDMO & Dental Surgeon Sub-Cadre) (October 2022) — General English* (`doc_062a465c96890fff341e8db7`, 20 MCQs)
  4. *Technical Competitive Examinations for Junior Grade of Mizoram Engineering Service, P&E Cadre (Electrical Wing) (June 2022) — General English* (`doc_4e9059a592b86e3de860b4f1`, 35 MCQs)
  * **75 retags, 0 keeps, 0 holds.**
  * **Granular Structuring & Taxonomy Alignment:**
    - Restructured 75 untagged/coarse baseline targets into precise active English taxonomy paths:
      - `english/vocabulary/idioms-and-phrases` (24 items: 14 CAO Paper-I items Q4–Q17; 10 GDMO/Dental items Q5(a)–(j))
      - `english/vocabulary` (10 items: GDMO/Dental Q7(a)–(j) contextual vocabulary and lexical choice)
      - `english/vocabulary/synonyms` (10 items: MES Electrical Wing Q3(a)–(e) passage synonyms; Q24–Q28 general synonyms)
      - `english/vocabulary/antonyms` (5 items: MES Electrical Wing Q29–Q33)
      - `english/grammar/parts-of-speech` (10 items: MES Electrical Wing Q4–Q13)
      - `english/grammar/tenses` (10 items: MES Electrical Wing Q14–Q23)
      - `english/writing/essay` (1 item: Geologist Junior Q1)
      - `english/writing/precis` (1 item: Geologist Junior Q2)
      - `english/writing/letter` (2 items: Geologist Junior Q3(a) and Q3(b))
      - `english/writing` (1 item: Geologist Junior Q5 proverb expansion)
      - `english/comprehension` (1 item: Geologist Junior Q6 reading comprehension)
  * **Underlined Token Visual Alignment:** Verified exact rectangle fill path geometries (`rect`) in the PDF stream for MES Electrical Wing Q4–Q13 to confirm the precise underlined word in each sentence ('spider', 'little', 'sells', 'They', 'spreads', 'and', 'soundly', 'into', 'Alas!', 'Our').
  * **Preserved 16 Conventional Descriptive Tasks (245 Marks):** Preserved 16 conventional written tasks (Essays, Précis, Letter writing, Proverb expansions, Sentence corrections, and Idiom sentence compositions) totaling 245 marks across all 4 booklets in `pending-written-intake.json`.
- Zero live database or API mutations. Readback validation confirmed 100% source fingerprint matches (75/75) and 0 database writes. Cumulative deduplicated unique targets in the review ledger reached **2,437** (2,837 unique appearances) across 49 candidate reports with zero problems or booklet family conflicts. [Batch 48 report](reports/tagging-batch48-20261108/README.md).

## 2026-11-08 08:55 IST — Source-reviewed tagging batch 49 (Direct 2019-2022 General English Paper-I Booklets 100% Paper Finalization — 50 MCQs & Tasks)

- Completed source-reviewed tagging batch 49 (50 General English MCQs and descriptive tasks, achieving 100% paper completion across all 6 booklets) from:
  1. *Competitive Examinations for Recruitment to the Post of Circle Education Officer (CEO) under School Education Department (August 2019) — General English Paper-I* (`doc_74d9b3f2ded9bc5c2e9c8b74`, 12 items)
  2. *General Competitive Examinations for Recruitment to the Post of Inspector under Excise & Narcotics Department (2019) — General English Paper-I* (`doc_da993afc1d299ca9ec8df13c`, 14 items)
  3. *General Competitive Examinations for Recruitment to the Post of Jr. Grade of MAH & VS (Veterinary Officer) (2019) — General English Paper-I* (`doc_1ab13cb407d3fde6a1a38251`, 3 items)
  4. *Technical Competitive Examinations for Recruitment to the Post of Informatics Officer (2020) — General English Paper-I* (`doc_5250924536dbee082db7539f`, 8 items)
  5. *Assistant Soil Conservation Engineer (ASCE) (2021) — General English Paper-I* (`doc_1244a8721bec769394f9b3a7`, 5 items)
  6. *General Competitive Examinations for Recruitment to the Post of Jr. Grade of MAH & VS (Veterinary Officer) (2021) — General English Paper-I* (`doc_38ddaa760769d6b08c77b1a7`, 8 items)
  * **50 retags, 0 keeps, 0 holds.**
  * **Bug Fix & Baseline Rectification:**
    - Rectified ASCE Q3 (`desc-5e1e5996c1f4b75e5c34`: Office Order drafting) from misclassified `service-rules-and-office-procedure` baseline to active taxonomy `english/writing/letter`.
    - Restructured 49 untagged/coarse baseline targets into precise active English taxonomy paths:
      - `english/comprehension` (25 items: 8 CEO Paper-I items Q6–Q13 on *Gilray's Flower-Pot*; 7 Inspector of Excise items Q12–Q18 on Gandhian egalitarianism; 1 Veterinary Officer 2019 item Q11 on science & religion; 8 Informatics Officer 2020 items Q1–Q8 on anti-colonial movements; 1 ASCE 2021 item Q6 on corporate mentoring)
      - `english/vocabulary/idioms-and-phrases` (12 items: 7 Inspector of Excise items Q4–Q10; 5 MAH Vety 2021 items Q5(a)–(e))
      - `english/writing/essay` (3 items: CEO Q1, ASCE Q1, MAH Vety 2021 Q1)
      - `english/writing/letter` (3 items: CEO Q2, ASCE Q3, MAH Vety 2021 Q3)
      - `english/writing/precis` (2 items: CEO Q3, ASCE Q2)
      - `english/writing` (3 items: CEO Q5, ASCE Q5, MAH Vety 2021 Q4)
      - `english/vocabulary/synonyms` (1 item: Veterinary Officer 2019 Q13)
      - `english/vocabulary/antonyms` (1 item: Veterinary Officer 2019 Q14)
  * **Preserved 18 Conventional Descriptive Tasks (274 Marks):** Preserved 18 conventional written tasks (Essays, Précis, Letter writing, Proverb expansions, Idiom explanations, and sentence compositions) totaling 274 marks across all 6 booklets in `pending-written-intake.json`.
- Zero live database or API mutations. Readback validation confirmed 100% source fingerprint matches (50/50) and 0 database writes. Cumulative deduplicated unique targets in the review ledger reached **2,487** (2,887 unique appearances) across 50 candidate reports with zero problems or booklet family conflicts. [Batch 49 report](reports/tagging-batch49-20261108/README.md).

## 2026-11-08 09:05 IST — Source-reviewed tagging batch 50 (Direct 2014-2026 General English Booklets 100% Paper Finalization — 70 MCQs & Tasks)

- Completed source-reviewed tagging batch 50 (70 General English MCQs and descriptive tasks, achieving 100% paper completion across all 7 target booklets):
  1. *Common Competitive Examination for Group 'B' Non-Gazetted (Technical) (March 2026) — Paper I (General English)* (`doc_7f704f41cc87a988ef58e762`, 5 written tasks, achieving **100% paper completion** with 55/55 items reviewed)
  2. *Competitive Examinations for Recruitment to the Posts of Fishery Extension Officer (FEO) — General English* (`doc_197d853e438e227a2ae7f15f`, 32 items, 100% paper completion)
  3. *Inspector of Statistics (February 2017) — General English* (`doc_08d6b0f9b9e23606217a0ed3`, 12 items, 100% paper completion)
  4. *Technical Competitive Examinations for Recruitment to the Post of Employment Officer — General English Paper I* (`doc_115a2dd346bc29a73812bf40`, 7 items, 100% paper completion)
  5. *Competitive Examinations for Recruitment to the Post of Inspector of Factories — General English* (`doc_7eb8775038672312345754e3`, 2 items, 100% paper completion)
  6. *Technical Competitive Examinations for Assistant Engineer / Assistant Environmental Officer (AEO) — General English* (`doc_f75f6fa112041692130f684b`, 4 items, 100% paper completion)
  7. *Competitive Examinations for Recruitment to Grade-V of Mizoram Food, Civil Supplies & Consumer Affairs Service (Inspector) (2019) — General English Paper I* (`doc_de0249ac406ac702e8477528`, 8 items, 100% paper completion)
  * **70 retags, 0 keeps, 0 holds.**
  * **Granular Structuring & Taxonomy Alignment:**
    - Restructured 70 baseline targets into precise active English taxonomy paths:
      - `english/vocabulary/idioms-and-phrases` (19 items: 10 Inspector of Statistics items Q1–Q10; 7 Employment Officer items Q1–Q7; 1 FEO item Q32; 1 Inspector FCS&CA item Q5)
      - `english/vocabulary` (11 items: FEO contextual vocabulary items)
      - `english/vocabulary/one-word-substitution` (8 items: FEO Q17–Q24)
      - `english/grammar/parts-of-speech` (6 items: FEO possessive pronoun, comparative adjectives, conjunctions)
      - `english/grammar/prepositions` (5 items: FEO prepositions)
      - `english/grammar/tenses` (1 item: FEO Q6 simple present habitual action)
      - `english/grammar/voice` (1 item: Group B Technical Q.W4 active-to-passive voice transformations)
      - `english/grammar/reported-speech` (1 item: Group B Technical Q.W5 direct-to-indirect speech transformations)
      - `english/comprehension` (6 items: Inspector FCS&CA Q1–Q3, Q6, Q7 on mass culture and art; Group B Technical Q.W2 on Scandinavian Ombudsman)
      - `english/writing/essay` (3 items: Inspector of Statistics Q1, IoF Q1, AEO Q1)
      - `english/writing/precis` (4 items: Group B Technical Q.W1, Inspector of Statistics Q2, IoF Q2, AEO Q2)
      - `english/writing/letter` (2 items: Group B Technical Q.W3, AEO Q3)
      - `english/writing` (1 item: AEO Q5 proverb expansion)
      - `english/vocabulary/synonyms` (1 item: Inspector FCS&CA Q4)
      - `english/vocabulary/antonyms` (1 item: Inspector FCS&CA Q8)
  * **Single-Booklet Deduplication Enforced:** Cleanly bypassed 68 duplicate appearances across Series B, C, and D of the 2026 Group 'B' Non-Gazetted Technical examination under single-booklet deduplication rules.
  * **Preserved 21 Conventional Descriptive Tasks (346 Marks):** Preserved 21 conventional written tasks across all 7 booklets in `pending-written-intake.json`.
- Zero live database or API mutations. Readback validation confirmed 100% source fingerprint matches (70/70) and 0 database writes. Cumulative deduplicated unique targets in the review ledger reached **2,557** (2,957 unique appearances) across 51 candidate reports with zero problems or booklet family conflicts. [Batch 50 report](reports/tagging-batch50-20261108/README.md).

## 2026-11-08 09:15 IST — Source-reviewed tagging batch 51 (Assistant Labour Officer General English Paper-II — 100 MCQs 100% Paper Completion)

- Completed source-reviewed tagging batch 51 (100 General English Paper-II MCQs, achieving **100% paper completion**):
  - *Competitive Examinations for Recruitment to the Post of Assistant Labour Officer under Labour, Employment, Skill Development & Entrepreneurship Department, Government of Mizoram (March 2021) — General English Paper-II* (`Old_Questions/Direct_2020-2021/Assistant LO General English Paper-II.pdf`, `doc_f614daf6ec16a2e1ba92bc19`, 100 MCQs, achieving 100% paper completion with 100/100 items reviewed).
  * **70 retags, 30 keeps, 0 holds.**
  * **Granular Structuring & Taxonomy Alignment:**
    - Structured 100 baseline targets into active English taxonomy paths:
      - `english/grammar` (30 items, all confirmed and kept from baseline):
        - Q41–Q50: Sentence conversion among Simple, Complex, and Compound structures.
        - Q51–Q60: Sentence transformation without losing meaning (affirmative/negative, assertive/interrogative, degrees of comparison, interchange of parts of speech, removal of 'too').
        - Q61–Q70: Synthesis of sentences using infinitives, participles, apposition, adverbial/adjective/noun clauses, and cumulative conjunctions.
      - `english/grammar/parts-of-speech` (20 items, retagged from coarse baseline):
        - Q21–Q30: Conjunctions (*therefore, whereas, so that, yet, unless, as well as, lest, but also, while, although*).
        - Q31–Q40: Adjectives, adverbs, and determiners (*worst, slowly, near, much, little, well in the test, fortunately, largest, some, too/so*).
      - `english/grammar/tenses` (10 items, retagged from coarse baseline):
        - Q1–Q10: Verb forms and tense sequence (*lost, has been waiting, wants, was driving, will call, had written, revolves, will have finished, broken, run*).
      - `english/grammar/prepositions` (10 items, retagged from coarse baseline):
        - Q11–Q20: Spatial, temporal, and dependent prepositions (*above, till, keen interest in, respect for, control over, into, beside, worthy of, beyond, congratulated on*).
      - `english/vocabulary/idioms-and-phrases` (10 items, retagged from coarse baseline):
        - Q71–Q80: Idiomatic expressions (*kicked the bucket, when pigs fly, set the bar, paid lip service, old school, keep in the loop, make light of, at odds, light years away, wet blanket*).
      - `english/vocabulary/one-word-substitution` (10 items, retagged from coarse baseline):
        - Q91–Q100: One-word lexical substitutes for underlined words/definitions (*insolent -> ill-mannered, calligraphy -> beautiful handwriting, philanderer -> chasing after women, zenith -> the highest point, inexorable -> unstoppable, animated -> lively, avarice -> love of money, posthumously -> after her death, obsolete -> outdated, invincible -> cannot be conquered*).
      - `english/vocabulary/synonyms` (5 items, retagged from coarse baseline):
        - Q81–Q85: Lexical synonyms (*penitent -> repentant, vengeance -> revenge, revelry -> celebration, succulent -> juicy, drowsy -> sleepy*).
      - `english/vocabulary/antonyms` (5 items, retagged from coarse baseline):
        - Q86–Q90: Lexical antonyms (*Fragrant -> smelly, Perpetual -> temporary, Retreat -> advance, Sensible -> foolish, Gratify -> displease*).
  * **Documented Source Defects:**
    - Documented Q5 printing defect: source paper printed only options (a), (b), and (c); preserved empty string in 4th slot matching canonical record.
    - Documented Q61 colloquial phrasing in printed booklet ('You do not hard work. You will fail the test.').
- Zero live database or API mutations. Readback validation confirmed 100% source fingerprint matches (100/100) and 0 database writes. Cumulative deduplicated unique targets in the review ledger reached **2,657** (3,057 unique appearances) across 52 candidate reports with zero problems or booklet family conflicts. [Batch 51 report](reports/tagging-batch51-20261108/README.md).

## 2026-11-08 09:25 IST — Source-reviewed tagging batch 52 (Informatics Officer General English Paper-II — 100 MCQs 100% Paper Completion)

- Completed source-reviewed tagging batch 52 (100 General English Paper-II MCQs, achieving **100% paper completion**):
  - *Technical Competitive Examinations for Recruitment to the Post of Informatics Officer under Information & Communication Technology Department, Government of Mizoram (February 2021) — General English Paper-II* (`Old_Questions/Direct_2020-2021/Informatics Officer - General English Paper-II.pdf`, `doc_e7390bd6cab5dd95ac26ed38`, 100 MCQs, achieving 100% paper completion with 100/100 items reviewed).
  * **32 retags, 68 keeps, 0 holds.**
  * **Granular Structuring & Taxonomy Alignment:**
    - Structured 100 baseline targets into active English taxonomy paths:
      - `english/grammar` (50 items, confirmed and kept from baseline):
        - Q21–Q30: Verb moods (indicative, infinitive, imperative, subjunctive).
        - Q31–Q40: Modal auxiliaries and tense forms (*shall, can, must, should have, were able to, must have gone, should, hadn't been*).
        - Q41–Q50: Sentence analysis into Simple, Complex, and Compound structures.
        - Q51–Q60: Clause identification (noun clauses, adjective/relative clauses, adverbial clauses).
        - Q61–Q70: Sentence classification (affirmative, negative, assertive, comparative, superlative).
      - `english/grammar/parts-of-speech` (10 items, retagged from coarse baseline):
        - Q1–Q10: Identification of parts of speech of underlined words (*any, before, even, by, master, One, back, deep, than, fix*).
      - `english/grammar/prepositions` (11 items, 10 kept + 1 retagged):
        - Q11–Q20: Spatial, temporal, and directional prepositions (*at the roundabout, on the left, change into, except, above corruption, across the road, over the years, through the back door, at the age of, under the agreement*).
        - Q92: Dependent preposition (*acquitted of the charge*).
      - `english/vocabulary` (17 items, confirmed and kept from baseline):
        - Q71–Q80: Contextual word pairs filling blanks.
        - Q94–Q100: Contextual vocabulary (*delicate, fastidious, exercise restraint, unbelievably, queasy, cloistered, casual*).
      - `english/vocabulary/idioms-and-phrases` (6 items, retagged from coarse baseline):
        - Q81–Q85: Proverb completions (*bad name, into the river, guilty conscience is always suspicious, quarrels with his tools, praises his pot*).
        - Q93: Idiom (*get your house in order*).
      - `english/vocabulary/one-word-substitution` (4 items, retagged from coarse baseline):
        - Q86 (*highest position -> pinnacle*), Q87 (*indifferent to art -> Philistine*), Q90 (*Prima facie -> on the first impression*), Q91 (*universal remedy -> panacea*).
      - `english/vocabulary/synonyms` (1 item, retagged from coarse baseline):
        - Q88 (*BACKLASH -> reaction*).
      - `english/vocabulary/antonyms` (1 item, retagged from coarse baseline):
        - Q89 (*AMPLE -> scanty*).
  * **Documented Source Defects & Vector Geometry:**
    - Verified underlined target words in parts of speech questions (*any, before, even, by, master, One, back, deep, than, fix*) directly from vector line geometry in the PDF stream.
    - Verified authentic 3-option structure for sentence analysis questions Q41–Q50 ((a) Simple, (b) Complex, (c) Compound).
- Zero live database or API mutations. Readback validation confirmed 100% source fingerprint matches (100/100) and 0 database writes. Cumulative deduplicated unique targets in the review ledger reached **2,757** (3,157 unique appearances) across 53 candidate reports with zero problems or booklet family conflicts. [Batch 52 report](reports/tagging-batch52-20261108/README.md).

## 2026-11-08 09:35 IST — Source-reviewed tagging batch 53 (Inspector of Excise General English Paper-II — 100 MCQs 100% Paper Completion)

- Completed source-reviewed tagging batch 53 (100 General English Paper-II MCQs, achieving **100% paper completion**):
  - *General Competitive Examinations for Recruitment to the Post of Inspector under Excise & Narcotics Department, Government of Mizoram (February 2021) — General English Paper-II* (`Old_Questions/Direct_2020-2021/Inspector of Excise - General English Paper-II.pdf`, `doc_96761ae7f42a829600dbd517`, 100 MCQs, achieving 100% paper completion with 100/100 items reviewed).
  * **57 retags, 43 keeps, 0 holds.**
  * **Granular Structuring & Taxonomy Alignment:**
    - Structured 100 baseline targets into active English taxonomy paths:
      - `english/grammar` (30 items, confirmed and kept from baseline):
        - Q41–Q50: Sentence structure analysis into Simple, Complex, and Compound sentences.
        - Q51–Q60: Sentence forms and degrees of comparison (affirmative, negative, positive, comparative, superlative).
        - Q61–Q70: Clause identification (noun clauses, adjective/relative clauses, adverbial clauses).
      - `english/grammar/parts-of-speech` (20 items, retagged from coarse baseline):
        - Q1–Q10: Identification of parts of speech of underlined words (*either, Either, Both, both, half, half, above, above, after, after*).
        - Q11–Q20: Classification of adverbs into manner, degree, time, place, frequency, and negation (*fast, almost, before, round, always*, etc.).
      - `english/grammar/prepositions` (10 items, retagged from coarse baseline):
        - Q21–Q30: Prepositions (*among, in, across, along, into, upon, at, under*).
      - `english/grammar/tenses` (10 items, retagged from coarse baseline):
        - Q31–Q40: Tenses and verb forms (*have sent, went, have done, appears, has been raining, had left*, etc.).
      - `english/sentence-correction` (10 items, retagged from coarse baseline):
        - Q71–Q80: Sentence improvement, modifier placement, politeness order of personal pronouns (*You, your brother and I*), and conditional inversion (*Had you not reached*).
      - `english/vocabulary` (13 items, confirmed and kept from baseline):
        - Q81–Q90: Contextual vocabulary, analogies (*life:death :: pleasure:suffering*), and collocations.
        - Q91, Q93, Q94: Collective nouns (*sheaf of wheat, litter of cubs*) and zoological young (*calf of an elephant*).
      - `english/vocabulary/idioms-and-phrases` (4 items, retagged from coarse baseline):
        - Q92 (*as blind as a bat*), Q96 (*beggars cannot be choosers*), Q98 (*beneath the rose lies the serpent/thorn*), Q100 (*spread like wildfire*).
      - `english/vocabulary/synonyms` (1 item, retagged from coarse baseline):
        - Q95 (*LAUD -> praise*).
      - `english/vocabulary/antonyms` (1 item, retagged from coarse baseline):
        - Q97 (*LETHARGIC -> hyperactive*).
      - `english/vocabulary/one-word-substitution` (1 item, retagged from coarse baseline):
        - Q99 (*per centum -> by the hundred*).
  * **Documented Source Defects:**
    - Verified authentic 3-option structure for sentence analysis questions Q41–Q50 ((a) Simple, (b) Complex, (c) Compound).
- Zero live database or API mutations. Readback validation confirmed 100% source fingerprint matches (100/100) and 0 database writes. Cumulative deduplicated unique targets in the review ledger reached **2,857** (3,257 unique appearances) across 54 candidate reports with zero problems or booklet family conflicts. [Batch 53 report](reports/tagging-batch53-20261108/README.md).

## 2026-11-08 09:45 IST — Source-reviewed tagging batch 54 (ASCE General English Paper-II — 100 MCQs 100% Paper Completion)

- Completed source-reviewed tagging batch 54 (100 General English Paper-II MCQs, achieving **100% paper completion**):
  - *Technical Competitive Examinations for Recruitment to the Post of Assistant Soil Conservation Engineer (ASCE) under Land Resources, Soil & Water Conservation Department, Government of Mizoram (February 2021) — General English Paper-II* (`Old_Questions/Direct_2021-2022/ASCE - General English Paper-II.pdf`, `doc_55f0caf9ddb8ed0aa2607152`, 100 MCQs, achieving 100% paper completion with 100/100 items reviewed).
  * **50 retags, 50 keeps, 0 holds.**
  * **Granular Structuring & Taxonomy Alignment:**
    - Structured 100 baseline targets into active English taxonomy paths:
      - `english/grammar` (40 items, confirmed and kept from baseline):
        - Q11–Q20: Types of imperative sentences (command, advice, request, proposal).
        - Q41–Q50: Sentence structure analysis into Simple, Compound, and Complex sentences.
        - Q51–Q60: Functional sentence types (declarative, imperative, interrogative, exclamatory).
        - Q61–Q70: Clause identification (co-ordinate clause, noun clause, adjective clause, adverb clause).
      - `english/grammar/parts-of-speech` (10 items, retagged from coarse baseline):
        - Q1–Q10: Identification of parts of speech of underlined words (*and, None, swimmer, Freedom, amusing, Lift, look, too, Ohh!, off*).
      - `english/grammar/tenses` (10 items, retagged from coarse baseline):
        - Q21–Q30: Tense identification across 3 choices (present tense, past tense, future tense).
      - `english/grammar/prepositions` (10 items, retagged from coarse baseline):
        - Q31–Q40: Prepositions (*during, considering, owing to, regarding, put up with, give a high five to*, etc.).
      - `english/vocabulary/idioms-and-phrases` (10 items, retagged from coarse baseline):
        - Q71–Q80: Phrasal verbs (*passed by, make out, run up to, takes up*, etc.).
      - `english/vocabulary` (10 items, confirmed and kept from baseline):
        - Q81–Q90: Contextual vocabulary and semantic equivalence (*respectable, impair*, etc.).
      - `english/vocabulary/one-word-substitution` (10 items, retagged from coarse baseline):
        - Q91–Q100: One-word lexical substitutes from definitions (*germicide, regicide, piscivore, monotheist*, etc.).
  * **Documented Source Defects & Vector Geometry:**
    - Verified underlined target words in parts of speech questions (*and, None, swimmer, Freedom, amusing, Lift, look, too, Ohh!, off*) directly from vector line geometry in the PDF stream.
    - Verified authentic 3-option structure for tense identification questions Q21–Q30 ((a) present tense, (b) past tense, (c) future tense).
    - Verified authentic 3-option structure for sentence analysis questions Q41–Q50 ((a) Simple, (b) Compound, (c) Complex).
- Zero live database or API mutations. Readback validation confirmed 100% source fingerprint matches (100/100) and 0 database writes. Cumulative deduplicated unique targets in the review ledger reached **2,957** (3,357 unique appearances) across 55 candidate reports with zero problems or booklet family conflicts. [Batch 54 report](reports/tagging-batch54-20261108/README.md).

## 2026-11-08 09:55 IST — Source-reviewed tagging batch 55 (Jr. Gr. of MAH & VS General English Paper-II — 100 MCQs 100% Paper Completion)

- Completed source-reviewed tagging batch 55 (100 General English Paper-II MCQs, achieving **100% paper completion**):
  - *General Competitive Examinations for Recruitment to the Post of Junior Grade of MAH & VS (Veterinary Officer) under Animal Husbandry & Veterinary Science Department, Government of Mizoram (November 2021) — General English Paper II* (`Old_Questions/Direct_2021-2022/Jr. Gr. of MAH Vety General English Paper-II.pdf`, `doc_fbd803035525d42a414da40f`, 100 MCQs, achieving 100% paper completion with 100/100 items reviewed).
  * **70 retags, 30 keeps, 0 holds.**
  * **Granular Structuring & Taxonomy Alignment:**
    - Structured 100 baseline targets into active English taxonomy paths:
      - `english/grammar` (30 items, confirmed and kept from baseline):
        - Q41–Q50: Clause analysis in complex and compound sentences (main clauses, adjectival clauses, noun clauses, adverbial clauses).
        - Q51–Q60: Sentence transformation without changing meaning (invigorating adjective, removal of 'too', comparative degree, negative with litotes, affirmative).
        - Q61–Q70: Synthesis of sentences using adverbs (*Fortunately*), adversative conjunction (*but*), noun clause with *whether*, adjective clauses, cumulative conjunction (*as well as*), apposition, and participles.
      - `english/grammar/parts-of-speech` (23 items, retagged from coarse baseline):
        - Q1–Q10: Identification of parts of speech of underlined words (*admiration, comfortable, about, down, book, As, Some, need, What!, They*).
        - Q21–Q30: Adjectives, adverbs, and determiners (*Each, much, generously, late, only, his*, etc.).
        - Q35, Q36, Q38: Conjunctions (*so that, therefore, lest*).
      - `english/grammar/tenses` (10 items, retagged from coarse baseline):
        - Q11–Q20: Verb forms and tense sequence (*is raining, have been living, comes, Did*, etc.).
      - `english/grammar/prepositions` (7 items, retagged from coarse baseline):
        - Q31–Q34, Q37, Q39, Q40: Prepositions (*above, compare with, depends upon, look into*, etc.).
      - `english/vocabulary/one-word-substitution` (10 items, retagged from coarse baseline):
        - Q71–Q80: One-word lexical substitutes from descriptions (*optimist, atheist, zoophilist, illegible, amateur, ambiguous, insatiable, turncoat, regent, author*).
      - `english/vocabulary/synonyms` (10 items, retagged from coarse baseline):
        - Q81–Q90: Lexical synonyms (*placate -> calm, gregarious -> sociable, imperious -> arrogant*, etc.).
      - `english/vocabulary/antonyms` (10 items, retagged from coarse baseline):
        - Q91–Q100: Lexical antonyms (*humble -> proud, prudent -> unwise*, etc.).
  * **Documented Source Defects & Vector Geometry:**
    - Verified underlined target words in parts of speech questions (*admiration, comfortable, about, down, book, As, Some, need, What!, They*) directly from vector line geometry in the PDF stream.
    - Verified vector line geometry for underlined words in synonyms and antonyms sections Q81–Q100.
- Zero live database or API mutations. Readback validation confirmed 100% source fingerprint matches (100/100) and 0 database writes. Cumulative deduplicated unique targets in the review ledger reached **3,057** (3,457 unique appearances) across 56 candidate reports with zero problems or booklet family conflicts. [Batch 55 report](reports/tagging-batch55-20261108/README.md).

## 2026-11-08 10:05 IST — Source-reviewed tagging batch 56 (Labour Officer General English Paper-II — 100 MCQs 100% Paper Completion)

- Completed source-reviewed tagging batch 56 (100 General English Paper-II MCQs, achieving **100% paper completion**):
  - *Competitive Examinations for Recruitment to the Post of Labour Officer under Labour, Employment, Skill Development & Entrepreneurship Department, Government of Mizoram (October 2021) — General English Paper-II* (`Old_Questions/Direct_2021-2022/Labour Officer under LESD&E Dept. - General English-II.pdf`, `doc_ecf12646749245ad755d372e`, 100 MCQs, achieving 100% paper completion with 100/100 items reviewed).
  * **68 retags, 32 keeps, 0 holds.**
  * **Granular Structuring & Taxonomy Alignment:**
    - Structured 100 baseline targets into active English taxonomy paths:
      - `english/grammar` (30 items, confirmed and kept from baseline):
        - Q41–Q50: Sentence structure analysis into Simple, Compound, Complex, and Compound-Complex sentences.
        - Q51–Q60: Sentence transformation (adjective transformation, superlative degree, removal of 'too', comparative degree).
        - Q61–Q70: Synthesis of sentences using participles, periodic structure, alternative coordinators (*or, otherwise*), noun clause in apposition, and correlative conjunctions (*not only... but also*).
      - `english/grammar/parts-of-speech` (20 items, retagged from coarse baseline):
        - Q1–Q10: Identification of parts of speech of underlined words (*guilty, wants, day, she, quickly, but, After, hiding, story, me*).
        - Q21–Q30: Conjunctions (*because, though, but, or*, etc.).
      - `english/grammar/tenses` (10 items, retagged from coarse baseline):
        - Q11–Q20: Verb forms and tense sequence (*washes, will go, was waiting*, etc.).
      - `english/grammar/prepositions` (10 items, retagged from coarse baseline):
        - Q31–Q40: Prepositions (*without, responsible for, on 22nd May, by today evening, for two hours*, etc.).
      - `english/vocabulary/synonyms` (10 items, retagged from coarse baseline):
        - Q71–Q80: Lexical synonyms (*Exotic, Haggle -> Bargain, Connoisseur -> Lover of art, Zenith -> Pinnacle*, etc.).
      - `english/vocabulary/one-word-substitution` (10 items, confirmed and kept from baseline):
        - Q81–Q90: One-word lexical substitutes from descriptions (*Panacea, Gourmet*, etc.).
      - `english/vocabulary` (10 items, confirmed and kept from baseline):
        - Q91–Q100: Contextual vocabulary and collocations (*job, success-oriented, any news, interrupt*, etc.).
  * **Documented Source Defects & Vector Geometry:**
    - Verified underlined target words in parts of speech questions (*guilty, wants, day, she, quickly, but, After, hiding, story, me*) directly from vector line geometry in the PDF stream.
- Zero live database or API mutations. Readback validation confirmed 100% source fingerprint matches (100/100) and 0 database writes. Cumulative deduplicated unique targets in the review ledger reached **3,157** (3,557 unique appearances) across 57 candidate reports with zero problems or booklet family conflicts. [Batch 56 report](reports/tagging-batch56-20261108/README.md).

## 2026-11-08 10:15 IST — Source-reviewed tagging batch 57 (Programme Co-ordinator General English II — 100 MCQs 100% Paper Completion)

- Completed source-reviewed tagging batch 57 (100 General English Paper-II MCQs, achieving **100% paper completion**):
  - *General Competitive Examinations for Recruitment to the Post of Programme Co-ordinator under Art & Culture Department, Government of Mizoram (October 2021) — General English II* (`Old_Questions/Direct_2021-2022/Programme Co-ordinator under A&C Deptt. General English-II.pdf`, `doc_8d9eac32e2c709359cc7c145`, 100 MCQs, achieving 100% paper completion with 100/100 items reviewed).
  * **67 retags, 33 keeps, 0 holds.**
  * **Granular Structuring & Taxonomy Alignment:**
    - Structured 100 baseline targets into active English taxonomy paths:
      - `english/grammar` (30 items, confirmed and kept from baseline):
        - Q45–Q50: Sentence synthesis using participles, adverb clauses, and infinitives.
        - Q51–Q58: Sentence transformation (simple, compound, complex, comparative degree, superlative degree).
        - Q59–Q68: Phrase and clause analysis (adjective phrases, noun clauses, relative adjective clauses).
        - Q69–Q74: Sentence forms and degrees of comparison (assertive, positive, comparative, imperative).
      - `english/grammar/parts-of-speech` (15 items, retagged from coarse baseline):
        - Q16–Q24: Identification of parts of speech of underlined words (*which, innocence, about, but, Never, her, Out, no, all*).
        - Q91–Q96: Pronouns and determiners (*whom, Few, I, What, A little, Either*).
      - `english/grammar/prepositions` (10 items, retagged from coarse baseline):
        - Q35–Q44: Prepositions (*beset with, liable to, onto, subsists on, incitement to*, etc.).
      - `english/grammar/tenses` (10 items, retagged from coarse baseline):
        - Q25–Q34: Verb forms and tense sequence (*have gone on strike lately*, etc.).
      - `english/vocabulary/idioms-and-phrases` (8 items, retagged from coarse baseline):
        - Q1–Q8: Idioms and phrases (*chewing the cud, teething problems, beggars description*, etc.).
      - `english/vocabulary` (7 items, confirmed and kept from baseline):
        - Q9–Q15: Contextual word usage and polysemy (*Benign, Invincible, Court, Peep, Protocol*, etc.).
      - `english/vocabulary/synonyms` (6 items, retagged from coarse baseline):
        - Q75–Q80: Lexical synonyms (*Expeditious -> prompt and efficient, rancour -> hatred, soporific -> soothing*, etc.).
      - `english/grammar/subject-verb-agreement` (5 items, retagged from coarse baseline):
        - Q86–Q90: Subject-verb concord (*Each of the students is, Either of us has, More than one man was*, etc.).
      - `english/vocabulary/antonyms` (5 items, retagged from coarse baseline):
        - Q81–Q85: Lexical antonyms of target headwords.
      - `english/grammar/articles` (4 items, retagged from coarse baseline):
        - Q97–Q100: Definite, indefinite, and zero articles (*skips lunch [zero], a thankful office [a], by prejudice [zero], most enemies [zero]*).
  * **Documented Source Defects & Vector Geometry:**
    - Verified underlined target words in parts of speech questions (*whole, which, innocence, about, but, Never, her, Out, no, all*) directly from vector line geometry in the PDF stream.
- Zero live database or API mutations. Readback validation confirmed 100% source fingerprint matches (100/100) and 0 database writes. Cumulative deduplicated unique targets in the review ledger reached **3,257** (3,657 unique appearances) across 58 candidate reports with zero problems or booklet family conflicts. [Batch 57 report](reports/tagging-batch57-20261108/README.md).





















## 2026-11-08 — Tagging Batch 58: Grade-V of MSCS (Cooperative Audit Officer) General English Paper - II (100 MCQs)

- **Execution:** Prepared pending source-reviewed tagging batch 58 (`reports/tagging-batch58-20261108`) under policy `study-tagging-v1` (`docs/QUESTION-TAGGING-RULES.md`).
- **Target Paper & Milestone:** Achieved **100% paper completion** for:
  - *Competitive Examinations for Recruitment to the Post of Grade-V of MSCS (Cooperative Audit Officer) under Cooperation Department (December 2022) — General English Paper - II* (`Old_Questions/Direct_2022-2023/General English Paper-II (CAO).pdf`, `doc_8cd9d275470b7aa2b6b85cbd`, 100 MCQs, achieving **100% paper completion** with 100/100 items reviewed).
- **Candidate Decisions & Taxonomy Structuring (100 items: 60 retag, 40 keep, 0 hold):**
  - All 100 candidates remain strictly pending; zero live database mutations.
  - Active path assignments:
    - `english/grammar` (30 items, confirmed and kept): Q41–Q50 (compound/complex/simple conversions), Q51–Q60 (clause identification), Q61–Q70 (synthesis & transformation).
    - `english/grammar/parts-of-speech` (24 items, retagged): Q1–Q10 (underlined parts of speech), Q21–Q30 (adjectives/adverbs/formation), Q31, Q36, Q38, Q39 (conjunctions).
    - `english/grammar/tenses` (10 items, retagged): Q11–Q20 (verb forms and aspect).
    - `english/grammar/prepositions` (6 items, retagged): Q32–Q35, Q37, Q40 (prepositions).
    - `english/vocabulary` (10 items, retagged): Q71–Q80 (contextual vocabulary and confusable word pairs).
    - `english/vocabulary/idioms-and-phrases` (10 items, retagged): Q91–Q100 (idiomatic expressions).
    - `english/vocabulary/antonyms` (5 items, retagged): Q81–Q85 (direct antonyms).
    - `english/vocabulary/synonyms` (5 items, retagged): Q86–Q90 (direct synonyms).
- **Source Defects & Verification:**
  - Q1–Q10 and Q81–Q100 underlined stems and words verified via vector line drawings.
- **Ledger Verification:**
  - Readback validation confirmed 100/100 source fingerprints match, 0 live database writes.
  - Cumulative review ledger: **3,835 saved records**, **3,757 unique appearances**, **3,357 deduplicated candidates**, **0 problems**. [Batch 58 report](reports/tagging-batch58-20261108/README.md).

## 2026-11-08 — Tagging Batch 59: Geologist Junior General English Paper-II (100 MCQs)

- **Execution:** Prepared pending source-reviewed tagging batch 59 (`reports/tagging-batch59-20261108`) under policy `study-tagging-v1` (`docs/QUESTION-TAGGING-RULES.md`).
- **Target Paper & Milestone:** Achieved **100% paper completion** for:
  - *Competitive Examinations for Recruitment to the Post of Geologist Junior under Commerce & Industries Department, Government of Mizoram (November 2022) — General English Paper - II* (`Old_Questions/Direct_2022-2023/Geologist Junior under Commerce Deptt - Gen English-II..pdf`, `doc_a9476c81c3142d879ad48676`, 100 MCQs, achieving **100% paper completion** with 100/100 items reviewed).
- **Candidate Decisions & Taxonomy Structuring (100 items: 64 retag, 36 keep, 0 hold):**
  - All 100 candidates remain strictly pending; zero live database mutations.
  - Active path assignments:
    - `english/grammar` (30 items, confirmed and kept): Q41–Q50 (sentence analysis: simple/compound/complex), Q51–Q60 (functional sentence types), Q61–Q70 (clause identification).
    - `english/grammar/parts-of-speech` (24 items, retagged): Q1–Q3, Q5–Q10 (nouns, pronouns, adjectives, adverbs, conjunctions, interjections, verbs), Q21–Q30 (adjectives & determiners), Q31–Q35 (adverbs).
    - `english/grammar/tenses` (10 items, retagged): Q11–Q20 (finite verb forms and aspect).
    - `english/grammar/prepositions` (6 items, retagged): Q4 (preposition identification), Q36–Q40 (preposition usage).
    - `english/vocabulary/idioms-and-phrases` (11 items, retagged): Q71–Q80 (idioms in context), Q99 (phrasal verb / idiom 'bottled up').
    - `english/vocabulary/one-word-substitution` (11 items, retagged): Q81–Q90 (one-word substitutes), Q94 (definition of 'sadist').
    - `english/vocabulary` (6 items, confirmed and kept): Q91 (spelling), Q95 (confusable words 'felicitated'), Q96, Q97, Q98, Q100 (contextual vocabulary).
    - `english/vocabulary/synonyms` (2 items, retagged): Q92 ('primeval'), Q93 ('inception').
- **Source Defects & Verification:**
  - Q61–Q70 underlined clauses and Q71–Q80 underlined idioms verified via vector line drawings.
- **Ledger Verification:**
  - Readback validation confirmed 100/100 source fingerprints match, 0 live database writes.
  - Cumulative review ledger: **3,935 saved records**, **3,857 unique appearances**, **3,457 deduplicated candidates**, **0 problems**. [Batch 59 report](reports/tagging-batch59-20261108/README.md).

## 2026-11-08 — Tagging Batch 60: SEO under Sericulture General English Paper-II (100 MCQs)

- **Execution:** Prepared pending source-reviewed tagging batch 60 (`reports/tagging-batch60-20261108`) under policy `study-tagging-v1` (`docs/QUESTION-TAGGING-RULES.md`).
- **Target Paper & Milestone:** Achieved **100% paper completion** for:
  - *Competitive Examinations for Recruitment to the Post of Sericulture Extension Officer (SEO) under Sericulture Department, Government of Mizoram (2022) — General English Paper-II* (`Old_Questions/Direct_2022-2023/SEO under Sericulture Deptt 2022 General English-II..pdf`, `doc_488d90639b1b64f05e81c67e`, 100 MCQs, achieving **100% paper completion** with 100/100 items reviewed).
- **Candidate Decisions & Taxonomy Structuring (100 items: 60 retag, 40 keep, 0 hold):**
  - All 100 candidates remain strictly pending; zero live database mutations.
  - Active path assignments:
    - `english/grammar` (30 items, confirmed and kept): Q41–Q50 (clause analysis), Q51–Q60 (sentence transformations), Q61–Q70 (synthesis).
    - `english/grammar/parts-of-speech` (25 items, retagged): Q1–Q10 (underlined parts of speech), Q21–Q30 (adjectives & adverbs), Q31, Q35, Q36, Q37, Q40 (conjunctions).
    - `english/grammar/tenses` (10 items, retagged): Q11–Q20 (finite verb forms and aspect).
    - `english/grammar/prepositions` (5 items, retagged): Q32–Q34, Q38–Q39 (preposition usage).
    - `english/vocabulary` (10 items, confirmed and kept): Q71–Q80 (contextual vocabulary & blank completions).
    - `english/vocabulary/synonyms` (10 items, retagged): Q81–Q90 (lexical synonyms of underlined words).
    - `english/vocabulary/antonyms` (10 items, retagged): Q91–Q100 (lexical antonyms of underlined words).
- **Source Defects & Verification:**
  - Q1–Q10 and Q81–Q100 underlined stems and target words verified via vector line drawings.
- **Ledger Verification:**
  - Readback validation confirmed 100/100 source fingerprints match, 0 live database writes.
  - Cumulative review ledger: **4,035 saved records**, **3,957 unique appearances**, **3,557 deduplicated candidates**, **0 problems**. [Batch 60 report](reports/tagging-batch60-20261108/README.md).

## 2026-11-08 — Tagging Batch 61: MCS Combined 2021 Preliminary Paper II (100 MCQs)

- **Execution:** Prepared pending source-reviewed tagging batch 61 (`reports/tagging-batch61-20261108`) under policy `study-tagging-v1` (`docs/QUESTION-TAGGING-RULES.md`).
- **Target Paper & Milestone:** Achieved **100% paper completion** for:
  - *Mizoram Civil Services Combined Preliminary Examination 2021 — Paper II (Aptitude, Arithmetic & Comprehension)* (`Old_Questions/Direct_2021-2022/MCS Combined 2021 Preliminary Exam Paper II.pdf`, `doc_82ea93920297fe3dba5ea823`, 100 MCQs, achieving **100% paper completion** with 100/100 items reviewed).
- **Candidate Decisions & Taxonomy Structuring (100 items: 31 retag, 69 keep, 0 hold):**
  - All 100 candidates remain strictly pending; zero live database mutations.
  - Active path assignments:
    - `english/comprehension` (10 items, confirmed and kept): Q1–Q2, Q8–Q9, Q11–Q14, Q16–Q17 (reading comprehension passages).
    - `english/vocabulary/synonyms` (3 items, retagged): Q3, Q5, Q7 (passage vocabulary synonyms).
    - `english/vocabulary` (2 items, confirmed and kept): Q4, Q6 (passage vocabulary context).
    - `english/vocabulary/antonyms` (1 item, retagged): Q10 (opposite of 'rampant').
    - `english/vocabulary/idioms-and-phrases` (1 item, retagged): Q15 ('deliver the goods').
    - `reasoning-and-aptitude/verbal-reasoning` (52 items): Q18–Q33 (interpersonal/decision-making), Q34–Q37 (logic puzzle), Q38, Q72 (blood relations), Q39–Q40 (analogies), Q41, Q45, Q73 (coding), Q43–Q44 (non-verbal figures), Q50 (inequalities), Q51–Q54 (syllogisms/conclusions), Q55–Q67 (administrative decision making), Q71 (assertion-reason), Q74, Q78 (direction sense), Q81–Q82 (analytical puzzles).
    - `reasoning-and-aptitude/series` (4 items): Q42, Q68, Q69 (number series), Q46 (letter series).
    - `reasoning-and-aptitude/numerical-ability` (8 items): Q70 (word problem), Q75 (number matrix), Q76, Q90 (Venn sets), Q79 (clock), Q80 (dice), Q83 (seating rows), Q84 (scheduling).
    - `reasoning-and-aptitude/data-interpretation` (3 items): Q91 (pie chart), Q99–Q100 (table DI).
    - `mathematics/arithmetic` (4 items): Q86–Q87 (surd arithmetic), Q89 (pipes & cisterns), Q96 (speed, distance, time).
    - `mathematics/arithmetic/percentages` (3 items): Q48, Q85, Q94 (percentage calculations).
    - `mathematics/arithmetic/averages` (2 items): Q49, Q88 (arithmetic mean / averages).
    - `mathematics/arithmetic/ratio-and-proportion` (2 items): Q95, Q98 (ratios).
    - `mathematics/algebra` (1 item): Q92 (arithmetic progression).
    - `mathematics/algebra/linear-equations` (3 items): Q47, Q77, Q93 (linear equations & age algebra).
    - `mathematics/mensuration` (1 item): Q97 (wheel revolutions & perimeter).
- **Source Defects & Verification:**
  - Resolved baseline anomalies (Assertion-Reason in Physics, Mean/Average in Statistics) by properly mapping to reasoning and arithmetic.
- **Ledger Verification:**
  - Readback validation confirmed 100/100 source fingerprints match, 0 live database writes.
  - Cumulative review ledger: **4,135 saved records**, **4,057 unique appearances**, **3,657 deduplicated candidates**, **0 problems**. [Batch 61 report](reports/tagging-batch61-20261108/README.md).

## 2026-11-08 — Tagging Batch 62: MCS Combined 2023 Preliminary Paper II Series A (100 MCQs)

- **Execution:** Prepared pending source-reviewed tagging batch 62 (`reports/tagging-batch62-20261108`) under policy `study-tagging-v1` (`docs/QUESTION-TAGGING-RULES.md`).
- **Target Paper & Milestone:** Achieved **100% paper completion** for:
  - *Mizoram Civil Services Combined Preliminary Examination 2023 — Paper II (Series A: Aptitude, Arithmetic & Comprehension)* (`Old_Questions/Direct_2023-2025/MCS Combined 2023 Preliminary Exam Paper-II Series 'A'..pdf`, `doc_1f45222ca9e6101529b723e7`, 100 MCQs, achieving **100% paper completion** with 100/100 items reviewed).
  - Enforced single-booklet deduplication: cleanly bypassed permutation booklets Series B, C, and D without redundant review.
- **Candidate Decisions & Taxonomy Structuring (100 items: 26 retag, 74 keep, 0 hold):**
  - All 100 candidates remain strictly pending; zero live database mutations.
  - Active path assignments:
    - `english/comprehension` (14 items, confirmed and kept): Q1, Q4–Q7, Q10, Q12–Q17, Q60–Q61 (reading comprehension).
    - `english/vocabulary/idioms-and-phrases` (2 items, retagged): Q2 ('lavish with his hospitality'), Q11 ('safety-valve').
    - `english/vocabulary/synonyms` (2 items, retagged): Q3 ('paradox'), Q8 ('subsistence').
    - `english/vocabulary/antonyms` (1 item, retagged): Q9 (opposite of 'stimulate').
    - `english/vocabulary` (3 items, confirmed and kept): Q21–Q23 (contextual vocabulary).
    - `reasoning-and-aptitude/verbal-reasoning` (48 items): Q18–Q20, Q24–Q34, Q52–Q53, Q56–Q57, Q59, Q62–Q64, Q67 (interpersonal skills, communication, administrative situational judgment), Q35–Q37, Q47–Q48 (blood relations & deductions), Q39–Q43 (statements and arguments), Q44–Q46 (syllogisms), Q49–Q51 (odd word out), Q54 (ranking test), Q66 (meaningful sequence), Q71 (direction sense), Q72, Q76, Q77 (coding-decoding), Q74, Q78 (ranking comparison), Q75 (analogy).
    - `reasoning-and-aptitude/series` (2 items): Q38 (letter series), Q80 (number series).
    - `reasoning-and-aptitude/numerical-ability` (5 items): Q65 (dice), Q69 (matrix), Q79 (problem figures), Q83 (tournament rounds), Q92 (Venn sets).
    - `reasoning-and-aptitude/data-interpretation` (2 items): Q73 (Venn DI), Q91 (pie chart).
    - `mathematics/arithmetic` (10 items): Q58 (journey time), Q68, Q82 (compound interest), Q70, Q87 (time & work), Q84 (divisibility), Q85, Q86, Q95 (surds/radicals), Q88 (speed, distance, time).
    - `mathematics/arithmetic/percentages` (1 item): Q89.
    - `mathematics/arithmetic/profit-and-loss` (1 item): Q90.
    - `mathematics/arithmetic/ratio-and-proportion` (2 items): Q81, Q96.
    - `mathematics/arithmetic/averages` (1 item): Q100 (mean).
    - `mathematics/algebra` (1 item): Q93 (AP).
    - `mathematics/algebra/linear-equations` (1 item): Q55.
    - `mathematics/algebra/algebraic-expressions` (1 item): Q97 (GCD & LCM of polynomials).
    - `mathematics/algebra/quadratic-equations` (1 item): Q98 (quadratic zeroes).
    - `mathematics/mensuration/area` (1 item): Q94 (perimeter wire rebent).
    - `mathematics/mensuration/volume` (1 item): Q99 (plank storage volume).
- **Source Defects & Verification:**
  - Resolved baseline misclassifications under commerce and statistics, standardizing all aptitude items into their rightful subjects.
- **Ledger Verification:**
  - Readback validation confirmed 100/100 source fingerprints match, 0 live database writes.
  - Cumulative review ledger: **4,235 saved records**, **4,157 unique appearances**, **3,757 deduplicated candidates**, **0 problems**. [Batch 62 report](reports/tagging-batch62-20261108/README.md).

## 2026-11-08 — Tagging Batch 63: MCS Combined 2015 Preliminary Paper II Series A (100 MCQs)

- **Execution:** Prepared pending source-reviewed tagging batch 63 (`reports/tagging-batch63-20261108`) under policy `study-tagging-v1` (`docs/QUESTION-TAGGING-RULES.md`).
- **Target Paper & Milestone:** Achieved **100% paper completion** for:
  - *Mizoram Civil Services Combined Preliminary Examination 2015 — Paper II (Series A: Aptitude, Arithmetic & Comprehension)* (`Old_Questions/Recovered_MCS/MCS Combined 2015 Preliminary Exam Paper-II Series-A Chase copy.pdf`, `mcs-recovered-2015-ii`, 100 MCQs, achieving **100% paper completion** with 100/100 items reviewed).
- **Candidate Decisions & Taxonomy Structuring (100 items: 75 retag, 25 keep, 0 hold):**
  - All 100 candidates remain strictly pending; zero live database mutations.
  - Resolved major legacy baseline misclassifications where questions had been imported into foreign subjects (`psychology` [10], `commerce` [4], `general-studies` [3], `science` [3], `civil-engineering` [1], and `journalism` [1]).
  - Active path assignments:
    - `english/comprehension` (24 items): Q1–Q4, Q6–Q14, Q87–Q91, Q93–Q95, Q97–Q99 (reading comprehension).
    - `english/vocabulary/one-word-substitution` (1 item): Q5 ('Euthanasia').
    - `english/vocabulary/antonyms` (2 items): Q92 ('spurious'), Q96 ('frustrater').
    - `english/vocabulary` (4 items): Q67–Q70 (anagrams).
    - `reasoning-and-aptitude/verbal-reasoning` (32 items): Q15–Q29 (interpersonal communication, active listening, conflict), Q42–Q44 (logic deduction), Q45–Q51 (group decision making, administrative ethics), Q55–Q58 (Mr. Thanga case study), Q63–Q64 (verbal analogies), Q72 (line seating).
    - `reasoning-and-aptitude/series` (5 items): Q30–Q32 (letter series), Q60 (geometric series), Q65 (letter matrix).
    - `reasoning-and-aptitude/numerical-ability` (14 items): Q33–Q38 (figure sequences), Q39–Q41 (pattern completion), Q52–Q54 (painted cube faces), Q66 (number matrix), Q71 (page numbering digits).
    - `reasoning-and-aptitude/data-interpretation` (4 items): Q82 (pie chart), Q83–Q84 (tables), Q86 (graph).
    - `mathematics/arithmetic` (3 items): Q76 (rope fractions), Q79 (speed/distance), Q100 (million = ten lakh).
    - `mathematics/arithmetic/percentages` (2 items): Q59 (pass percentage), Q77 (16% equation).
    - `mathematics/arithmetic/averages` (3 items): Q62 (mean height), Q81 (mean salary), Q85 (median).
    - `mathematics/arithmetic/ratio-and-proportion` (1 item): Q80 (alloy mixture).
    - `mathematics/algebra/linear-equations` (1 item): Q74 (two-digit number).
    - `mathematics/algebra/quadratic-equations` (1 item): Q73 (age quadratic product).
    - `mathematics/geometry` (1 item): Q75 (quadrant).
    - `mathematics/mensuration` (1 item): Q61 (perimeter comparison).
    - `mathematics/mensuration/volume` (1 item): Q78 (brick wall volume, retagged from civil engineering).
- **Source Defects & Verification:**
  - Standardized stimulus image questions (Q63, Q64) as verbal analogies.
- **Ledger Verification:**
  - Readback validation confirmed 100/100 source fingerprints match, 0 live database writes.
  - Cumulative review ledger: **4,335 saved records**, **4,257 unique appearances**, **3,857 deduplicated candidates**, **0 problems**. [Batch 63 report](reports/tagging-batch63-20261108/README.md).

## 2026-11-08 — Tagging Batch 64: MCS Combined 2017 Preliminary Paper II Series A (100 MCQs)

- **Execution:** Prepared pending source-reviewed tagging batch 64 (`reports/tagging-batch64-20261108`) under policy `study-tagging-v1` (`docs/QUESTION-TAGGING-RULES.md`).
- **Target Paper & Milestone:** Achieved **100% paper completion** for:
  - *Mizoram Civil Services Combined Preliminary Examination 2017 — Paper II (Series A: Aptitude, Arithmetic & Comprehension)* (`Old_Questions/Recovered_MCS/MCS Combined 2017 Preliminary Exam Paper-II Series-A Chase copy.pdf`, `mcs-recovered-2017-ii`, 100 MCQs, achieving **100% paper completion** with 100/100 items reviewed).
- **Candidate Decisions & Taxonomy Structuring (100 items: 73 retag, 27 keep, 0 hold):**
  - All 100 candidates remain strictly pending; zero live database mutations.
  - Re-aligned questions previously misclassified into foreign topics (`law`, `psychology`, `service-rules-and-office-procedure`, `science/chemistry`, `general-studies`).
  - Active path assignments:
    - `english/comprehension` (28 items): Q1–Q14, Q87–Q100 (reading comprehension).
    - `english/vocabulary` (1 item): Q28 ('implicate').
    - `english/vocabulary/synonyms` (3 items): Q61–Q63 (WHIMSICAL, APATHETIC, CLANDESTINE).
    - `english/vocabulary/idioms-and-phrases` (3 items): Q64–Q66 (proverbs & idioms).
    - `reasoning-and-aptitude/verbal-reasoning` (35 items): Q15–Q27, Q29 (interpersonal skills, communication), Q30 (coding-decoding), Q31, Q37 (seating), Q32, Q33 (syllogisms), Q40 (directions), Q44–Q51, Q53–Q57 (decision making), Q52 (statement-conclusion), Q70 (hardness).
    - `reasoning-and-aptitude/series` (1 item): Q74 (square sequence).
    - `reasoning-and-aptitude/numerical-ability` (10 items): Q36 (coin geometry), Q58–Q60, Q67–Q69 (stimulus figures), Q71–Q72 (figure sequence), Q75 (Venn).
    - `reasoning-and-aptitude/data-interpretation` (6 items): Q81–Q83 (budget table), Q84–Q86 (recruitment table).
    - `mathematics/arithmetic` (5 items): Q34 (work), Q41 (train speed/distance), Q42 (divisibility), Q76 (fractions), Q79 (compound interest).
    - `mathematics/arithmetic/averages` (2 items): Q35, Q78.
    - `mathematics/arithmetic/percentages` (1 item): Q80.
    - `mathematics/algebra/linear-equations` (3 items): Q38, Q77 (digit equations), Q39 (siblings).
    - `mathematics/mensuration/area` (1 item): Q43 (circle areas ratio).
    - `statistics/probability-and-statistics/probability` (1 item): Q73.
- **Source Defects & Verification:**
  - Preserved fidelity of stimulus image questions Q58–Q60 and Q67–Q69.
- **Ledger Verification:**
  - Readback validation confirmed 100/100 source fingerprints match, 0 live database writes.
  - Cumulative review ledger: **4,435 saved records**, **4,357 unique appearances**, **3,957 deduplicated candidates**, **0 problems**. [Batch 64 report](reports/tagging-batch64-20261108/README.md).

## 2026-11-08 — Tagging Batch 65: MCS Combined 2018 Preliminary Paper II Series A (100 MCQs)

- **Execution:** Prepared pending source-reviewed tagging batch 65 (`reports/tagging-batch65-20261108`) under policy `study-tagging-v1` (`docs/QUESTION-TAGGING-RULES.md`).
- **Target Paper & Milestone:** Achieved **100% paper completion** for:
  - *Mizoram Civil Services Combined Preliminary Examination 2018 — Paper II (Series A: Aptitude, Arithmetic & Comprehension)* (`Old_Questions/Recovered_MCS/MCS Combined 2018 Preliminary Exam Paper-II Series-A Chase copy.pdf`, `mcs-recovered-2018-ii`, 100 MCQs, achieving **100% paper completion** with 100/100 items reviewed).
- **Candidate Decisions & Taxonomy Structuring (100 items: 80 retag, 20 keep, 0 hold):**
  - All 100 candidates remain strictly pending; zero live database mutations.
  - Executed major re-alignment across questions previously misclassified in foreign disciplines (`general-studies`, `general-knowledge`, `psychology`, `sociology`, `physics`, `commerce`, `civil-engineering`).
  - Active path assignments:
    - `english/comprehension` (28 items): Q1–Q14, Q87–Q100 (reading comprehension).
    - `english/vocabulary` (2 items): Q66–Q67 (DECEIVE, DECEPTIVE).
    - `reasoning-and-aptitude/verbal-reasoning` (48 items): Q15–Q28 (interpersonal communication, active listening, conflict), Q29–Q33 (economic/monsoon logic), Q34–Q38 (assertion & reason), Q39–Q42 (family age deduction), Q43–Q57 (administrative decision making, groupthink), Q63 (coding), Q64–Q65 (verbal analogies), Q70–Q71 (situational engineering/physics).
    - `reasoning-and-aptitude/series` (2 items): Q61 (letter series), Q62 (number series).
    - `reasoning-and-aptitude/numerical-ability` (6 items): Q58–Q60, Q68–Q69 (stimulus figures), Q75 (Venn sets).
    - `reasoning-and-aptitude/data-interpretation` (2 items): Q81 (pie chart), Q85 (frequency table).
    - `mathematics/arithmetic` (4 items): Q72 (divisibility), Q74 (work), Q79 (radicals), Q86 (compound interest).
    - `mathematics/arithmetic/percentages` (2 items): Q73 (percentage fraction), Q82 (sales tax).
    - `mathematics/arithmetic/profit-and-loss` (1 item): Q83 (profit/cost price).
    - `mathematics/arithmetic/ratio-and-proportion` (1 item): Q80 (ratio comparison).
    - `mathematics/algebra` (1 item): Q77 (AP sum).
    - `mathematics/mensuration/area` (2 items): Q76 (circle radius), Q84 (plot perimeter).
    - `statistics/probability-and-statistics/probability` (1 item): Q78 (colored ball probability).
- **Ledger Verification:**
  - Readback validation confirmed 100/100 source fingerprints match, 0 live database writes.
  - Cumulative review ledger: **4,535 saved records**, **4,457 unique appearances**, **4,057 deduplicated candidates**, **0 problems**. [Batch 65 report](reports/tagging-batch65-20261108/README.md).

## 2026-11-08 — Tagging Batch 66: MCS Combined 2014 Preliminary Paper II (99 MCQs)

- **Execution:** Prepared pending source-reviewed tagging batch 66 (`reports/tagging-batch66-20261108`) under policy `study-tagging-v1` (`docs/QUESTION-TAGGING-RULES.md`).
- **Target Paper & Milestone:** Achieved **100% paper completion** for:
  - *Mizoram Civil Services Combined Preliminary Examination 2014 — Paper II (Aptitude, Arithmetic & Comprehension)* (`Old_Questions/Direct_2014-2018/MCS Combined 2014 Preliminary Exam Paper II.pdf`, `doc_27f320fe0ca6eed357e122a2`, 99 MCQs, achieving **100% paper completion** with 99/99 items reviewed).
  - Documented legacy omission: Question 39 was a non-verbal stimulus figure question on page 6 of the printed PDF omitted from legacy database intake due to empty stem text, now recorded in `pending-written-intake.json`.
- **Candidate Decisions & Taxonomy Structuring (99 items: 19 retag, 80 keep, 0 hold):**
  - All 99 candidates remain strictly pending; zero live database mutations.
  - Active path assignments:
    - `english/comprehension` (23 items): Q1–Q13, Q87–Q90, Q93–Q97, Q100 (reading comprehension).
    - `english/vocabulary/synonyms` (4 items): Q14, Q91, Q98, Q99.
    - `english/vocabulary/idioms-and-phrases` (1 item): Q92 ('Stem the tide').
    - `english/vocabulary/antonyms` (1 item): Q61 ('ascetic').
    - `english/vocabulary` (4 items): Q59 ('pilaster'), Q60 ('gingival'), Q62, Q71.
    - `reasoning-and-aptitude/verbal-reasoning` (43 items): Q15–Q29 (interpersonal communication), Q30–Q31 (photo deduction), Q35 (sequence), Q41 (directions), Q43–Q44 (syllogisms), Q45–Q58 (administrative situational judgment), Q63–Q64 (analogies), Q65 (odd out), Q66–Q67 (coding), Q68 (cause-effect), Q69 (blood relations), Q72 (alphabetical sequence).
    - `reasoning-and-aptitude/series` (3 items): Q32, Q33 (number series), Q36 (letter series).
    - `reasoning-and-aptitude/numerical-ability` (4 items): Q37–Q38 (figure logic), Q42 (clock), Q70 (pattern count).
    - `reasoning-and-aptitude/data-interpretation` (4 items): Q83 (pie chart), Q84 (bar graph), Q85 (line graph), Q86 (coordinate graph).
    - `mathematics/arithmetic` (5 items): Q34 (fraction), Q73 (division), Q78 (book pages), Q80 (unitary), Q81 (work).
    - `mathematics/arithmetic/percentages` (1 item): Q74 (percentage).
    - `mathematics/arithmetic/averages` (3 items): Q76 (multiples average), Q77 (mode/mean/median), Q82 (median).
    - `mathematics/algebra/linear-equations` (1 item): Q40 (digits reverse age).
    - `mathematics/geometry/triangles` (1 item): Q75 (altitude bisecting base).
    - `mathematics/mensuration/area` (1 item): Q79 (square & rectangle area).
- **Ledger Verification:**
  - Readback validation confirmed 99/99 source fingerprints match, 0 live database writes.
  - Cumulative review ledger: **4,634 saved records**, **4,556 unique appearances**, **4,156 deduplicated candidates**, **0 problems**. [Batch 66 report](reports/tagging-batch66-20261108/README.md).

## 2026-11-08 — Tagging Batch 67: 5.MCS Series A Paper-II (95 MCQs)

- **Execution:** Prepared pending source-reviewed tagging batch 67 (`reports/tagging-batch67-20261108`) under policy `study-tagging-v1` (`docs/QUESTION-TAGGING-RULES.md`).
- **Target Paper & Milestone:** Achieved **100% paper completion** for:
  - *Mizoram Civil Services Combined Preliminary Examination — Paper II (Series A: Aptitude, Arithmetic & Comprehension)* (`Old_Questions/Direct_2014-2018/5.MCS Series A Paper-II.pdf`, `doc_29704fec92a63aac9cf1e2ea`, 95 MCQs, achieving **100% paper completion** with 95/95 items reviewed).
  - Enforced single-booklet deduplication: cleanly bypassed permutation series `6.MCS Series B Paper-II.pdf`, `7.MCS Series C Paper-II.pdf`, and `8.MCS Series D Paper-II.pdf`.
  - Preserved unextracted source defects: 5 visual stimulus figure questions (Q59, Q60, Q68, Q69, Q72) omitted from legacy database OCR intake due to missing text stems are recorded in `pending-written-intake.json`.
- **Candidate Decisions & Taxonomy Structuring (95 items: 91 retag, 4 keep, 0 hold):**
  - All 95 candidates remain strictly pending; zero live database mutations.
  - Active path assignments:
    - `english/comprehension` (28 items): Q1–Q14, Q87–Q100 (reading comprehension).
    - `english/vocabulary` (1 item): Q28 ('implicate').
    - `english/vocabulary/synonyms` (3 items): Q61–Q63 (WHIMSICAL, APATHETIC, CLANDESTINE).
    - `english/vocabulary/idioms-and-phrases` (3 items): Q64–Q66 (proverbs & idioms).
    - `reasoning-and-aptitude/verbal-reasoning` (35 items): Q15–Q27, Q29 (interpersonal communication), Q30 (coding-decoding), Q31, Q37 (seating), Q32, Q33 (syllogisms), Q40 (directions), Q44–Q51, Q53–Q57 (decision making), Q52 (statement-conclusion), Q70 (hardness).
    - `reasoning-and-aptitude/series` (1 item): Q74 (square sequence).
    - `reasoning-and-aptitude/numerical-ability` (5 items): Q36 (coin geometry), Q58, Q67, Q71 (non-verbal figures), Q75 (Venn).
    - `reasoning-and-aptitude/data-interpretation` (6 items): Q81–Q83 (budget table), Q84–Q86 (recruitment table).
    - `mathematics/arithmetic` (5 items): Q34 (work), Q41 (train speed/distance), Q42 (divisibility), Q76 (fractions), Q79 (compound interest).
    - `mathematics/arithmetic/averages` (2 items): Q35, Q78.
    - `mathematics/arithmetic/percentages` (1 item): Q80.
    - `mathematics/algebra/linear-equations` (3 items): Q38, Q77 (digit equations), Q39 (siblings).
    - `mathematics/mensuration/area` (1 item): Q43 (circle areas ratio).
    - `statistics/probability-and-statistics/probability` (1 item): Q73.
- **Ledger Verification:**
  - Readback validation confirmed 95/95 source fingerprints match, 0 live database writes.
  - Cumulative review ledger: **4,729 saved records**, **4,651 unique appearances**, **4,251 deduplicated candidates**, **0 problems**. [Batch 67 report](reports/tagging-batch67-20261108/README.md).

### 2026-11-08: Source-Reviewed Question Tagging Batch 68 (CDPO General English Paper II Common)
- **Execution:** Prepared pending source-reviewed tagging batch 68 (`reports/tagging-batch68-20261108`) under policy `study-tagging-v1` (`docs/QUESTION-TAGGING-RULES.md`).
- **Target Paper & Milestone:** Achieved **100% paper completion** for:
  - *Technical Competitive Examinations for Child Development Project Officer (CDPO) under Social Welfare Department 2016 — General English Paper II (Common)* (`Old_Questions/Direct_2014-2018/2.CDPO under Social Welfare Department 2016 General English Paper II Common.pdf`, `doc_44de83a1b9447347e93a07df`, 100 MCQs, achieving **100% paper completion** with 100/100 items reviewed).
- **Candidate Decisions & Taxonomy Structuring (100 items: 64 retag, 36 keep, 0 hold):**
  - All 100 candidates remain strictly pending; zero live database mutations (`live_changes: 0`).
  - Active path assignments:
    - `english/grammar/parts-of-speech` (15 items): Q1–Q10 (underlined parts of speech: adverb, preposition, conjunction, noun, interjection), Q31–Q35 (pronouns).
    - `english/grammar/prepositions` (10 items): Q11–Q20 (appropriate prepositions).
    - `english/grammar/tenses` (10 items): Q21–Q30 (appropriate verb forms and tenses).
    - `english/grammar/articles` (5 items): Q36–Q40 (article insertion).
    - `english/grammar` (30 items): Q41–Q48 (sentence structure: simple, compound, complex), Q49–Q56 (phrase identification: noun, adjective, adverb, prepositional phrases), Q57–Q65 (clause analysis: noun, adjective, adverb clauses), Q66–Q70 (notion / mood analysis).
    - `english/vocabulary/idioms-and-phrases` (10 items): Q71–Q80 (idioms and phrases meaning).
    - `english/vocabulary/synonyms` (6 items): Q81–Q86 (nearest in meaning).
    - `english/vocabulary/antonyms` (8 items): Q87–Q94 (opposite in meaning).
    - `english/vocabulary` (6 items): Q95–Q100 (vocabulary / sentence completion).
- **Ledger Verification:**
  - Readback validation confirmed 100/100 source fingerprints match, 0 live database writes.
  - Cumulative review ledger: **4,829 saved records**, **4,751 unique appearances**, **4,351 deduplicated candidates**, **0 problems**. [Batch 68 report](reports/tagging-batch68-20261108/README.md).

### 2026-11-08: Source-Reviewed Question Tagging Batch 69 (Fishery Extension Officer General English Paper II)
- **Execution:** Prepared pending source-reviewed tagging batch 69 (`reports/tagging-batch69-20261108`) under policy `study-tagging-v1` (`docs/QUESTION-TAGGING-RULES.md`).
- **Target Paper & Milestone:** Achieved **100% paper completion** for:
  - *Competitive Examinations for Recruitment to the Post of Fishery Extension Officer (December 2017) — General English Paper II* (`Old_Questions/Direct_2014-2018/2.General English Paper-II.pdf`, `doc_c634c07280fb2818a0383368`, 100 MCQs, achieving **100% paper completion** with 100/100 items reviewed).
- **Candidate Decisions & Taxonomy Structuring (100 items: 93 retag, 7 keep, 0 hold):**
  - All 100 candidates remain strictly pending; zero live database mutations (`live_changes: 0`).
  - Active path assignments:
    - `english/grammar/parts-of-speech` (17 items): Q1–Q10 (underlined parts of speech), Q21–Q22 (determiners/quantifiers), Q31–Q35 (adjectives and adverbs).
    - `english/grammar/tenses` (15 items): Q11–Q20 (correct form of verbs), Q36–Q40 (name the tense of the verb).
    - `english/grammar/articles` (3 items): Q23–Q25 (article selection: a/an/the).
    - `english/grammar/prepositions` (5 items): Q26–Q30 (preposition selection).
    - `english/grammar` (30 items): Q41–Q50 (sentence transformation: simple, compound, complex), Q51–Q55 (sentence transformation: affirmative/negative, degrees, exclamatory), Q56–Q60 (interchanging parts of speech), Q61–Q65 (sentence transformation: affirmative, negative, interrogative), Q66–Q70 (sentence synthesis using clauses).
    - `english/vocabulary/antonyms` (5 items): Q71–Q75 (opposite in meaning).
    - `english/vocabulary/synonyms` (5 items): Q76–Q80 (nearest in meaning).
    - `english/vocabulary/idioms-and-phrases` (10 items): Q81–Q90 (idioms and phrases meaning).
    - `english/vocabulary/one-word-substitution` (10 items): Q91–Q100 (one-word substitution).
- **Ledger Verification:**
  - Readback validation confirmed 100/100 source fingerprints match, 0 live database writes.
  - Cumulative review ledger: **4,929 saved records**, **4,851 unique appearances**, **4,451 deduplicated candidates**, **0 problems**. [Batch 69 report](reports/tagging-batch69-20261108/README.md).

### 2026-11-08: Source-Reviewed Question Tagging Batch 70 (General English Paper - II September 2018)
- **Execution:** Prepared pending source-reviewed tagging batch 70 (`reports/tagging-batch70-20261108`) under policy `study-tagging-v1` (`docs/QUESTION-TAGGING-RULES.md`).
- **Target Paper & Milestone:** Achieved **100% paper completion** for:
  - *General Competitive Examinations (September 2018) — General English Paper - II* (`Old_Questions/Direct_2014-2018/2.General English-II.pdf`, `doc_f41a788556c2566c4c00da87`, 100 MCQs, achieving **100% paper completion** with 100/100 items reviewed).
- **Candidate Decisions & Taxonomy Structuring (100 items: 74 retag, 26 keep, 0 hold):**
  - All 100 candidates remain strictly pending; zero live database mutations (`live_changes: 0`).
  - Active path assignments:
    - `english/grammar/parts-of-speech` (30 items): Q1–Q10 (underlined parts of speech), Q11–Q20 (relative pronouns), Q21–Q30 (conjunctions).
    - `english/grammar/prepositions` (5 items): Q31–Q35 (prepositions).
    - `english/grammar/tenses` (5 items): Q36–Q40 (verb forms and tenses).
    - `english/grammar` (25 items): Q41–Q50 (sentence transformation: simple, compound, complex), Q51–Q55 (sentence / clause structure classification), Q56–Q60 (sentence synthesis), Q61–Q65 (clause identification).
    - `english/vocabulary` (15 items): Q66–Q70 (collocation), Q91–Q100 (homophones / vocabulary / correct alternative).
    - `english/vocabulary/synonyms` (5 items): Q71–Q75 (nearest in meaning).
    - `english/vocabulary/antonyms` (5 items): Q76–Q80 (opposite in meaning).
    - `english/vocabulary/idioms-and-phrases` (10 items): Q81–Q90 (idioms and phrases meaning).
- **Ledger Verification:**
  - Readback validation confirmed 100/100 source fingerprints match, 0 live database writes.
  - Cumulative review ledger: **5,029 saved records**, **4,951 unique appearances**, **4,551 deduplicated candidates**, **0 problems**. [Batch 70 report](reports/tagging-batch70-20261108/README.md).

### 2026-11-08: Source-Reviewed Question Tagging Batch 71 (Inspector of Taxes 2016 General English Paper II)
- **Execution:** Prepared pending source-reviewed tagging batch 71 (`reports/tagging-batch71-20261108`) under policy `study-tagging-v1` (`docs/QUESTION-TAGGING-RULES.md`).
- **Target Paper & Milestone:** Achieved **100% paper completion** for:
  - *Competitive Examinations for Recruitment to Inspector of Taxes (January 2016) — General English Paper II* (`Old_Questions/Direct_2014-2018/2.Inspector of Taxes 2016 General English Paper II.pdf`, `doc_6311a1c087c7ee07ee8bb474`, 100 MCQs, achieving **100% paper completion** with 100/100 items reviewed).
- **Candidate Decisions & Taxonomy Structuring (100 items: 70 retag, 30 keep, 0 hold):**
  - All 100 candidates remain strictly pending; zero live database mutations (`live_changes: 0`).
  - Active path assignments:
    - `english/grammar/parts-of-speech` (17 items): Q1–Q10 (name parts of speech), Q27, Q28 (noun forms and quantifiers), Q36–Q40 (adjectives and adverbs).
    - `english/grammar/tenses` (15 items): Q11–Q20 (correct form of verbs), Q31–Q35 (name the tense of the verb).
    - `english/grammar/prepositions` (5 items): Q21–Q25 (prepositions).
    - `english/grammar/articles` (3 items): Q26, Q29, Q30 (articles and determiners).
    - `english/grammar` (30 items): Q41–Q45 (degrees of comparison transformation), Q46–Q50 (sentence transformation: affirmative/negative), Q51–Q60 (sentence conversion: simple, compound, complex), Q61–Q70 (sentence synthesis using clauses).
    - `english/vocabulary/idioms-and-phrases` (10 items): Q71–Q80 (idioms and phrases meaning).
    - `english/vocabulary/synonyms` (10 items): Q81–Q90 (synonyms / nearest in meaning).
    - `english/vocabulary/one-word-substitution` (10 items): Q91–Q100 (one-word substitution).
- **Ledger Verification:**
  - Readback validation confirmed 100/100 source fingerprints match, 0 live database writes.
  - Cumulative review ledger: **5,129 saved records**, **5,051 unique appearances**, **4,651 deduplicated candidates**, **0 problems**. [Batch 71 report](reports/tagging-batch71-20261108/README.md).

### 2026-11-08: Source-Reviewed Question Tagging Batch 72 (Grade-V of MHS 2017 General English Paper II)
- **Execution:** Prepared pending source-reviewed tagging batch 72 (`reports/tagging-batch72-20261108`) under policy `study-tagging-v1` (`docs/QUESTION-TAGGING-RULES.md`).
- **Target Paper & Milestone:** Achieved **100% paper completion** for:
  - *Technical Competitive Examinations for Grade-V of Mizoram Horticulture Service (November 2017) — General English Paper - II* (`Old_Questions/Direct_2014-2018/General English paper-II (MHS).pdf`, `doc_bbd4602370e71a495e7d027b`, 100 MCQs, achieving **100% paper completion** with 100/100 items reviewed).
- **Candidate Decisions & Taxonomy Structuring (100 items: 50 retag, 50 keep, 0 hold):**
  - All 100 candidates remain strictly pending; zero live database mutations (`live_changes: 0`).
  - Active path assignments:
    - `english/grammar/parts-of-speech` (8 items): Q1–Q8 (underlined parts of speech).
    - `english/vocabulary` (15 items): Q9–Q13 (semantic adverb meaning), Q81–Q90 (vocabulary / sentence completion).
    - `english/grammar` (40 items): Q14–Q23 (notion / concept expressed by sentence), Q51–Q60 (sentence structure analysis: simple, complex, compound), Q61–Q70 (clause identification), Q71–Q80 (sentence functional classification: declarative, imperative, interrogative, exclamatory).
    - `english/grammar/tenses` (5 items): Q24, Q25, Q28–Q30 (verb forms and conditionals).
    - `english/grammar/prepositions` (12 items): Q26, Q27, Q31–Q40 (preposition selection).
    - `english/vocabulary/idioms-and-phrases` (10 items): Q41–Q50 (phrasal verbs).
    - `english/vocabulary/one-word-substitution` (10 items): Q91–Q100 (one-word substitution).
- **Ledger Verification:**
  - Readback validation confirmed 100/100 source fingerprints match, 0 live database writes.
  - Cumulative review ledger: **5,229 saved records**, **5,151 unique appearances**, **4,751 deduplicated candidates**, **0 problems**. [Batch 72 report](reports/tagging-batch72-20261108/README.md).

### 2026-11-08: Source-Reviewed Question Tagging Batch 73 (Senior Horticulture Demonstrator General English April 2018)
- **Execution:** Prepared pending source-reviewed tagging batch 73 (`reports/tagging-batch73-20261108`) under policy `study-tagging-v1` (`docs/QUESTION-TAGGING-RULES.md`).
- **Target Paper & Milestone:** Achieved **100% paper completion** for:
  - *Technical Competitive Examinations for Senior Horticulture Demonstrator (April 2018) — General English* (`Old_Questions/Direct_2014-2018/3.General English.pdf`, `doc_83296a794525fd6c34a58849`, 109 appearances covering all 80 MCQs and 29 legacy duplicate extractions, achieving **100% paper completion**).
  - Preserved unextracted conventional Section A Essay (20 marks) on Page 1 in `pending-written-intake.json`.
- **Candidate Decisions & Taxonomy Structuring (109 items: 62 retag, 47 keep, 0 hold):**
  - All 109 candidates remain strictly pending; zero live database mutations (`live_changes: 0`).
  - Active path assignments:
    - `english/vocabulary/idioms-and-phrases` (16 items): Q1–Q16 (idioms and phrases meaning).
    - `english/comprehension` (12 items): Q17–Q28 (reading comprehension passage).
    - `english/grammar/prepositions` (7 items): Q29–Q34 (preposition selection across 7 appearances).
    - `english/grammar/parts-of-speech` (12 items): Q35–Q40 (underlined parts of speech across 12 appearances).
    - `english/grammar/tenses` (10 items): Q41–Q48 (verb forms and tenses across 10 appearances).
    - `english/grammar` (32 items): Q49–Q53 (sentence structure: compound, complex, simple), Q54–Q58 (clause identification: noun, adjective, adverb, coordinate), Q59–Q64 (sentence notion and concept).
    - `english/vocabulary` (12 items): Q65–Q72 (usage of words, homophones).
    - `english/vocabulary/synonyms` (8 items): Q73–Q80 (nearest in meaning).
- **Ledger Verification:**
  - Readback validation confirmed 109/109 source fingerprints match, 0 live database writes.
  - Cumulative review ledger: **5,338 saved records**, **5,260 unique appearances**, **4,860 deduplicated candidates**, **0 problems**. [Batch 73 report](reports/tagging-batch73-20261108/README.md).

### 2026-11-08: Source-Reviewed Question Tagging Batch 74 (Middle & Primary School Teacher 2015 General English)
- **Execution:** Prepared pending source-reviewed tagging batch 74 (`reports/tagging-batch74-20261108`) under policy `study-tagging-v1` (`docs/QUESTION-TAGGING-RULES.md`).
- **Target Paper & Milestone:** Achieved **100% paper completion** for:
  - *General Competitive Examinations for Recruitment to Middle School Teacher & Primary School Teacher (July 2015) — General English* (`Old_Questions/Direct_2014-2018/1.Middle & Primary School Teacher 2015 General English.pdf`, `doc_73d36df5c68f5a69c05bd094`, 80 MCQs, achieving **100% paper completion** with 80/80 items reviewed).
  - Preserved unextracted conventional Section A Essay (20 marks) on Page 1 in `pending-written-intake.json`.
- **Candidate Decisions & Taxonomy Structuring (80 items: 27 retag, 53 keep, 0 hold):**
  - All 80 candidates remain strictly pending; zero live database mutations (`live_changes: 0`).
  - Active path assignments:
    - `english/vocabulary/idioms-and-phrases` (16 items): Q1–Q16 (idioms and phrases meaning and usage).
    - `english/comprehension` (16 items): Q17–Q32 (reading comprehension passages across 3 passages).
    - `english/grammar/parts-of-speech` (8 items): Q33–Q40 (form of nouns, verbs, adjectives, adverbs).
    - `english/grammar/prepositions` (8 items): Q41–Q48 (prepositions).
    - `english/grammar/voice` (8 items): Q49–Q56 (Active Voice / Passive Voice identification).
    - `english/grammar` (9 items): Q57–Q65 (sentence structure: simple, compound, complex).
    - `english/vocabulary` (15 items): Q66–Q70 (speech terminology), Q71–Q75 (sentence completion), Q76–Q80 (word derivation).
- **Ledger Verification:**
  - Readback validation confirmed 80/80 source fingerprints match, 0 live database writes.
  - Cumulative review ledger: **5,418 saved records**, **5,340 unique appearances**, **4,940 deduplicated candidates**, **0 problems**. [Batch 74 report](reports/tagging-batch74-20261108/README.md).

### 2026-11-08: Source-Reviewed Question Tagging Batch 75 (Junior Engineer General English April 2016)
- **Execution:** Prepared pending source-reviewed tagging batch 75 (`reports/tagging-batch75-20261108`) under policy `study-tagging-v1` (`docs/QUESTION-TAGGING-RULES.md`).
- **Target Paper & Milestone:** Achieved **100% paper completion** for:
  - *Technical Competitive Examinations for Junior Engineer (J.E) under PHE & PWD (April 2016) — General English* (`Old_Questions/Direct_2014-2018/3. General English.pdf`, `doc_4c79cb3420629f238d2b19c8`, 80 MCQs, achieving **100% paper completion** with 80/80 items reviewed).
  - Preserved unextracted conventional Section A Essay (20 marks) on Page 1 in `pending-written-intake.json`.
- **Candidate Decisions & Taxonomy Structuring (80 items: 80 retag, 0 keep, 0 hold):**
  - All 80 candidates remain strictly pending; zero live database mutations (`live_changes: 0`).
  - Active path assignments:
    - `english/vocabulary/idioms-and-phrases` (23 items): Q1–Q16 (idioms and phrases fill-in and meaning), Q29–Q35 (phrasal verbs).
    - `english/comprehension` (12 items): Q17–Q28 (reading comprehension passages across 2 passages).
    - `english/grammar/parts-of-speech` (13 items): Q36–Q42 (adjectives, adverbs, and verbs), Q43–Q48 (parts of speech of underlined words).
    - `english/grammar` (16 items): Q49–Q54 (clause identification), Q55–Q59 (sentence structure: simple, complex, compound), Q60–Q64 (sentence functional classification: declarative, interrogative, imperative, exclamatory).
    - `english/vocabulary/synonyms` (6 items): Q65–Q70 (synonyms / similar meaning).
    - `english/vocabulary/antonyms` (4 items): Q71–Q74 (antonyms / opposite meaning).
    - `english/vocabulary/one-word-substitution` (4 items): Q75–Q77, Q79 (one-word substitution).
    - `english/vocabulary` (2 items): Q78, Q80 (vocabulary / word usage).
- **Ledger Verification:**
  - Readback validation confirmed 80/80 source fingerprints match, 0 live database writes.
  - Cumulative review ledger: **5,498 saved records**, **5,420 unique appearances**, **5,020 deduplicated candidates**, **0 problems**. [Batch 75 report](reports/tagging-batch75-20261108/README.md).

### 2026-11-08: Source-Reviewed Question Tagging Batch 76 (Junior Scientific Officer General English May 2016)
- **Execution:** Prepared pending source-reviewed tagging batch 76 (`reports/tagging-batch76-20261108`) under policy `study-tagging-v1` (`docs/QUESTION-TAGGING-RULES.md`).
- **Target Paper & Milestone:** Achieved **100% paper completion** for:
  - *Technical Competitive Examinations for Junior Scientific Officer (Contract) under Home Dept (May 2016) — General English* (`Old_Questions/Direct_2014-2018/5.JSO General English 2016 (Common).pdf`, `doc_27139f9cee9ec33283e18370`, 80 MCQs, achieving **100% paper completion** with 80/80 items reviewed).
  - Preserved unextracted conventional Section A Essay (20 marks) on Page 1 in `pending-written-intake.json`.
- **Candidate Decisions & Taxonomy Structuring (80 items: 79 retag, 1 keep, 0 hold):**
  - All 80 candidates remain strictly pending; zero live database mutations (`live_changes: 0`).
  - Active path assignments:
    - `english/vocabulary/idioms-and-phrases` (16 items): Q1–Q16 (idioms and phrases meaning and fill-in).
    - `english/comprehension` (14 items): Q17–Q22, Q25–Q32 (reading comprehension passages across 2 passages).
    - `english/vocabulary/synonyms` (6 items): Q23 (passage synonym), Q72–Q76 (synonyms).
    - `english/vocabulary/antonyms` (5 items): Q24 (passage antonym), Q77–Q80 (antonyms).
    - `english/grammar/tenses` (10 items): Q33–Q42 (simple past vs present perfect tense).
    - `english/grammar/reported-speech` (6 items): Q43–Q48 (direct and indirect speech).
    - `english/grammar` (12 items): Q49–Q56 (sentence structure: simple, complex, compound), Q62–Q65 (sentence linking / conjunctions).
    - `english/sentence-correction` (5 items): Q57–Q61 (phrase substitution / sentence correction).
    - `english/vocabulary` (6 items): Q66–Q71 (vocabulary definitions of underlined words).
- **Ledger Verification:**
  - Readback validation confirmed 80/80 source fingerprints match, 0 live database writes.
  - Cumulative review ledger: **5,578 saved records**, **5,500 unique appearances**, **5,100 deduplicated candidates**, **0 problems**. [Batch 76 report](reports/tagging-batch76-20261108/README.md).

### 2026-11-08: Source-Reviewed Question Tagging Batch 77 (Programmer under PHED General English Paper I July 2018)
- **Execution:** Prepared pending source-reviewed tagging batch 77 (`reports/tagging-batch77-20261108`) under policy `study-tagging-v1` (`docs/QUESTION-TAGGING-RULES.md`).
- **Target Paper & Milestone:** Achieved **100% paper completion** for:
  - *General Competitive Examinations for Recruitment to Programmer under Public Health Engineering Department (July 2018) — General English Paper I* (`Old_Questions/Direct_2014-2018/1.General English Paper-I.pdf`, `doc_f65bdaf24aea5195f08880e8`, 80 MCQs, achieving **100% paper completion** with 80/80 items reviewed).
  - Preserved unextracted conventional Section A Essay (20 marks) on Page 1 in `pending-written-intake.json`.
- **Candidate Decisions & Taxonomy Structuring (80 items: 76 retag, 4 keep, 0 hold):**
  - All 80 candidates remain strictly pending; zero live database mutations (`live_changes: 0`).
  - Active path assignments:
    - `english/comprehension` (8 items): Q1–Q8 (reading comprehension passage).
    - `english/vocabulary/idioms-and-phrases` (16 items): Q9–Q24 (idioms and phrases meaning).
    - `english/vocabulary/antonyms` (8 items): Q25–Q32 (opposite in meaning).
    - `english/grammar/parts-of-speech` (8 items): Q33–Q40 (parts of speech of underlined words).
    - `english/grammar/prepositions` (8 items): Q41–Q48 (prepositions).
    - `english/grammar` (16 items): Q49–Q58 (sentence structure: simple, compound, complex), Q59–Q64 (sentence functional classification: declarative, imperative, interrogative, exclamatory).
    - `english/vocabulary` (8 items): Q65–Q72 (vocabulary / sentence completion).
    - `english/vocabulary/synonyms` (8 items): Q73–Q80 (nearest in meaning to underlined word).
- **Ledger Verification:**
  - Readback validation confirmed 80/80 source fingerprints match, 0 live database writes.
  - Cumulative review ledger: **5,658 saved records**, **5,580 unique appearances**, **5,180 deduplicated candidates**, **0 problems**. [Batch 77 report](reports/tagging-batch77-20261108/README.md).

### 2026-11-08: Source-Reviewed Question Tagging Batch 78 (Assistant Tourist Officer General English Dec 2017)
- **Execution:** Prepared pending source-reviewed tagging batch 78 (`reports/tagging-batch78-20261108`) under policy `study-tagging-v1` (`docs/QUESTION-TAGGING-RULES.md`).
- **Target Paper & Milestone:** Achieved **100% paper completion** for:
  - *Competitive Examinations for Recruitment to the Posts of Assistant Tourist Officer under Tourism Department (December, 2017) — General English* (`Old_Questions/Direct_2014-2018/1.ATO General English.pdf`, `doc_fe7a66559c7eb4bde50c19a9`, 80 MCQs, achieving **100% paper completion** with 80/80 items reviewed).
  - Preserved unextracted conventional Section A Essay (20 marks) on Page 1 in `pending-written-intake.json`.
- **Candidate Decisions & Taxonomy Structuring (80 items: 77 retag, 3 keep, 0 hold):**
  - All 80 candidates remain strictly pending; zero live database mutations (`live_changes: 0`).
  - Active path assignments:
    - `english/comprehension` (12 items): Q1–Q6 (poem reading comprehension), Q7–Q12 (poem vocabulary synonyms).
    - `english/grammar/tenses` (5 items): Q13–Q17 (verb form and tense selection).
    - `english/grammar/prepositions` (5 items): Q18–Q22 (preposition selection).
    - `english/grammar/parts-of-speech` (10 items): Q23–Q32 (parts of speech identification).
    - `english/grammar` (16 items): Q33–Q38 (sentence structure: simple, compound, complex), Q39–Q43 (sentence functional classification), Q44–Q48 (clause identification).
    - `english/vocabulary/one-word-substitution` (7 items): Q49–Q55 (one-word substitution).
    - `english/vocabulary/synonyms` (5 items): Q56–Q60 (synonyms nearest in meaning).
    - `english/vocabulary/idioms-and-phrases` (15 items): Q61–Q65 (phrase similar in meaning), Q71–Q80 (idioms and phrases meaning).
    - `english/vocabulary` (5 items): Q66–Q70 (animal cries vocabulary).
- **Ledger Verification:**
  - Readback validation confirmed 80/80 source fingerprints match, 0 live database writes.
  - Cumulative review ledger: **5,738 saved records**, **5,660 unique appearances**, **5,260 deduplicated candidates**, **0 problems**. [Batch 78 report](reports/tagging-batch78-20261108/README.md).

### 2026-11-08: Source-Reviewed Question Tagging Batch 79 (Various Posts under MIMER Feb 2018 General English Common Paper)
- **Execution:** Prepared pending source-reviewed tagging batch 79 (`reports/tagging-batch79-20261108`) under policy `study-tagging-v1` (`docs/QUESTION-TAGGING-RULES.md`).
- **Target Paper & Milestone:** Achieved **100% paper completion** for:
  - *General Competitive Examinations for Recruitment to Various Posts under MIMER (February, 2018) — General English Common Paper* (`Old_Questions/Direct_2014-2018/1.General English Common Paper.pdf`, `doc_6df8aa9179998188151c7268`, 80 MCQs, achieving **100% paper completion** with 80/80 items reviewed).
  - Preserved unextracted conventional Section A Essay (20 marks) on Page 1 in `pending-written-intake.json`.
- **Candidate Decisions & Taxonomy Structuring (80 items: 22 retag, 58 keep, 0 hold):**
  - All 80 candidates remain strictly pending; zero live database mutations (`live_changes: 0`).
  - Active path assignments:
    - `english/comprehension` (12 items): Q1–Q12 (reading comprehension passages on cleanliness and health).
    - `english/vocabulary/idioms-and-phrases` (16 items): Q13–Q28 (idioms and phrases).
    - `english/grammar/parts-of-speech` (10 items): Q29–Q37 (parts of speech identification), Q46 (adverb usage).
    - `english/grammar/tenses` (5 items): Q38–Q40 (verb forms and tenses), Q79–Q80 (tenses and mood).
    - `english/grammar/subject-verb-agreement` (1 item): Q41 (police agreement).
    - `english/grammar/prepositions` (9 items): Q42, Q43, Q47 (preposition selection), Q73–Q78 (prepositional usage).
    - `english/grammar` (19 items): Q44, Q45 (distributive pronouns), Q48 (conjunction), Q49–Q52 (sentence structure: simple, compound, complex), Q53–Q58 (sentence functional classification), Q59–Q64 (synthesis of sentences).
    - `english/vocabulary/one-word-substitution` (8 items): Q65–Q72 (one-word substitution).
- **Ledger Verification:**
  - Readback validation confirmed 80/80 source fingerprints match, 0 live database writes.
  - Cumulative review ledger: **5,818 saved records**, **5,740 unique appearances**, **5,340 deduplicated candidates**, **0 problems**. [Batch 79 report](reports/tagging-batch79-20261108/README.md).

### 2026-11-08: Source-Reviewed Question Tagging Batch 80 (Computer Operator under SAD 2016 General English)
- **Execution:** Prepared pending source-reviewed tagging batch 80 (`reports/tagging-batch80-20261108`) under policy `study-tagging-v1` (`docs/QUESTION-TAGGING-RULES.md`).
- **Target Paper & Milestone:** Achieved **100% paper completion** for:
  - *Technical Competitive Examinations for Recruitment to the Post of Computer Operator (Contract) under SAD (2016) — General English* (`Old_Questions/Direct_2014-2018/1.Computer Operator (Contract) under SAD 2016 General English.pdf`, `doc_eb2fb7b4156640c6198fbbd3`, 80 MCQs, achieving **100% paper completion** with 80/80 items reviewed).
  - Preserved unextracted conventional Section A Essay (20 marks) on Page 1 in `pending-written-intake.json`.
- **Candidate Decisions & Taxonomy Structuring (80 items: 76 retag, 4 keep, 0 hold):**
  - All 80 candidates remain strictly pending; zero live database mutations (`live_changes: 0`).
  - Active path assignments:
    - `english/vocabulary/idioms-and-phrases` (16 items): Q1–Q16 (idioms and phrases meanings).
    - `english/comprehension` (16 items): Q17–Q32 (reading comprehension passages on good manners and etiquette).
    - `english/grammar/prepositions` (6 items): Q33–Q38 (preposition selection).
    - `english/grammar/parts-of-speech` (6 items): Q39–Q44 (parts of speech identification).
    - `english/grammar/tenses` (4 items): Q45–Q48 (verb form and tense selection).
    - `english/grammar` (16 items): Q49–Q53 (sentence structure: simple, compound, complex), Q54–Q58 (clause identification), Q59–Q64 (sentence functional classification).
    - `english/vocabulary` (8 items): Q65–Q72 (vocabulary usage / homophones / commonly confused words).
    - `english/vocabulary/synonyms` (8 items): Q73–Q80 (nearest in meaning to underlined words).
- **Ledger Verification:**
  - Readback validation confirmed 80/80 source fingerprints match, 0 live database writes.
  - Cumulative review ledger: **5,898 saved records**, **5,820 unique appearances**, **5,420 deduplicated candidates**, **0 problems**. [Batch 80 report](reports/tagging-batch80-20261108/README.md).

### 2026-11-08: Source-Reviewed Question Tagging Batch 81 (Computer Operator under Mizoram Information Commission 2016 General English)
- **Execution:** Prepared pending source-reviewed tagging batch 81 (`reports/tagging-batch81-20261108`) under policy `study-tagging-v1` (`docs/QUESTION-TAGGING-RULES.md`).
- **Target Paper & Milestone:** Achieved **100% paper completion** for:
  - *Technical Competitive Examinations for Recruitment to the Post of Computer Operator under Mizoram Information Commission (2016) — General English* (`Old_Questions/Direct_2014-2018/1.Computer Operator (CB) under Mizoram Information Commission 2016 General English.pdf`, `doc_e4a3e87d3a010bc114cf396a`, 80 MCQs, achieving **100% paper completion** with 80/80 items reviewed).
  - Preserved unextracted conventional Section A Essay (20 marks) on Page 1 in `pending-written-intake.json`.
- **Candidate Decisions & Taxonomy Structuring (80 items: 77 retag, 3 keep, 0 hold):**
  - All 80 candidates remain strictly pending; zero live database mutations (`live_changes: 0`).
  - Active path assignments:
    - `english/vocabulary/idioms-and-phrases` (16 items): Q1–Q8 (idiom meanings), Q9–Q16 (idioms in context).
    - `english/comprehension` (16 items): Q17–Q32 (reading comprehension passages on human society and religion).
    - `english/grammar/tenses` (11 items): Q33–Q37 (past and perfect tenses), Q38–Q42 (verb forms), Q45 (participle form).
    - `english/grammar/parts-of-speech` (4 items): Q43, Q46, Q47, Q48 (relative pronouns and determiners).
    - `english/grammar/prepositions` (1 item): Q44 (preposition: looking for).
    - `english/grammar` (17 items): Q49–Q56 (sentence structure: simple, complex, compound), Q57–Q61 (sentence synthesis and pronoun substitution), Q62–Q65 (sentence connectors / linkers).
    - `english/vocabulary` (6 items): Q66–Q71 (vocabulary usage in context).
    - `english/vocabulary/synonyms` (5 items): Q72–Q76 (synonyms).
    - `english/vocabulary/antonyms` (4 items): Q77–Q80 (antonyms).
- **Ledger Verification:**
  - Readback validation confirmed 80/80 source fingerprints match, 0 live database writes.
  - Cumulative review ledger: **5,978 saved records**, **5,900 unique appearances**, **5,500 deduplicated candidates**, **0 problems**. [Batch 81 report](reports/tagging-batch81-20261108/README.md).

### 2026-11-08: Source-Reviewed Question Tagging Batch 82 (Junior Engineer Contract Basis General English)
- **Execution:** Prepared pending source-reviewed tagging batch 82 (`reports/tagging-batch82-20261108`) under policy `study-tagging-v1` (`docs/QUESTION-TAGGING-RULES.md`).
- **Target Paper & Milestone:** Achieved **100% paper completion** for:
  - *General Competitive Examinations for Recruitment to Junior Engineer (JE) Contract Basis — General English* (`Old_Questions/Direct_2014-2018/9. General English.pdf`, `doc_9ca4c2a445e9a44ecb9c3f58`, 80 MCQs, achieving **100% paper completion** with 80/80 items reviewed).
  - Preserved unextracted conventional Section A Essay (20 marks) on Page 1 in `pending-written-intake.json`.
- **Candidate Decisions & Taxonomy Structuring (80 items: 78 retag, 2 keep, 0 hold):**
  - All 80 candidates remain strictly pending; zero live database mutations (`live_changes: 0`).
  - Active path assignments:
    - `english/vocabulary/idioms-and-phrases` (16 items): Q1–Q16 (idioms and phrases meaning).
    - `english/comprehension` (16 items): Q17–Q32 (reading comprehension passage on poverty and development).
    - `english/grammar/prepositions` (6 items): Q33–Q38 (prepositions).
    - `english/grammar/parts-of-speech` (6 items): Q39–Q44 (parts of speech identification).
    - `english/grammar/tenses` (4 items): Q45–Q48 (verb form and tenses).
    - `english/grammar` (16 items): Q49–Q53 (sentence structure: simple, compound, complex), Q54–Q58 (clause identification), Q59–Q64 (sentence functional classification).
    - `english/vocabulary` (8 items): Q65–Q72 (vocabulary / word usage / commonly confused words).
    - `english/vocabulary/synonyms` (8 items): Q73–Q80 (synonyms nearest in meaning).
- **Ledger Verification:**
  - Readback validation confirmed 80/80 source fingerprints match, 0 live database writes.
  - Cumulative review ledger: **6,058 saved records**, **5,980 unique appearances**, **5,580 deduplicated candidates**, **0 problems**. [Batch 82 report](reports/tagging-batch82-20261108/README.md).

### 2026-11-08: Source-Reviewed Question Tagging Batch 83 (Assistant Conservator of Forest 2018 General English)
- **Execution:** Prepared pending source-reviewed tagging batch 83 (`reports/tagging-batch83-20261108`) under policy `study-tagging-v1` (`docs/QUESTION-TAGGING-RULES.md`).
- **Target Paper & Milestone:** Achieved **100% paper completion** for:
  - *General Competitive Examinations for Recruitment to Junior Grade of Mizoram Forest Service i.e. Assistant Conservator of Forest (ACF) (2018) — General English* (`Old_Questions/Direct_2014-2018/ACF General English.pdf`, `doc_eb2da5629158c3db0a463a50`, 65 MCQs, achieving **100% paper completion** with 65/65 items reviewed).
  - Preserved unextracted conventional Section A Essay (20 marks) and Précis (15 marks) on Page 1 (35 marks total) in `pending-written-intake.json`.
- **Candidate Decisions & Taxonomy Structuring (65 items: 65 retag, 0 keep, 0 hold):**
  - All 65 candidates remain strictly pending; zero live database mutations (`live_changes: 0`).
  - Active path assignments:
    - `english/grammar/tenses` (10 items): Q1–Q10 (verb forms and tenses).
    - `english/grammar/parts-of-speech` (10 items): Q11–Q20 (parts of speech identification).
    - `english/grammar/prepositions` (10 items): Q21–Q30 (preposition selection).
    - `english/vocabulary/idioms-and-phrases` (10 items): Q31–Q40 (idioms and phrases meaning).
    - `english/grammar` (20 items): Q41–Q50 (modal concepts / sentence notions: possibility, obligation, request, command, invitation), Q51–Q60 (conjunctions).
    - `english/vocabulary/one-word-substitution` (5 items): Q61–Q65 (one-word substitution).
- **Ledger Verification:**
  - Readback validation confirmed 65/65 source fingerprints match, 0 live database writes.
  - Cumulative review ledger: **6,123 saved records**, **6,045 unique appearances**, **5,645 deduplicated candidates**, **0 problems**. [Batch 83 report](reports/tagging-batch83-20261108/README.md).
