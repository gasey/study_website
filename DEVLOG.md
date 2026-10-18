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
