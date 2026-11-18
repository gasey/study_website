# Finna Stats — current release and operations

Implemented 15 November 2026. Native app entry: Library → Stats. Local phone
preview: http://localhost:8089/stats. Website entry: Library → Stats, or https://study.hawayu.in/stats. Both surfaces
read the same production Stats API and published releases.

## Available now

- India indicators: nominal GDP, real GDP growth, GDP per capita, population,
  consumer-price inflation, life expectancy and infant mortality, using WDI.
- Global same-period comparisons (India plus up to three countries/economies),
  historical charts/exact-value tables, search, paged rankings and source panels.
- UNDP HDR 2025: HDI scores over 1990–2023 and publisher ranks for 2023.
- NITI State Health Index Round IV: reference year 2019–20, with the report's
  19 larger states, eight smaller states and seven UTs kept separate. Mizoram is
  pinned only within its eligible group. The report period is always visible.
- Economic Survey 2025–26: 17 chapter/part links, 107 searchable official
  appendix-table links, a source-checked opening-chapter brief and two cited
  first-advance-estimate figures (GDP/GVA growth). Documents open the official
  source. This release does not transcribe all appendix tables or summarize all
  chapters inside the app.
- Release selection, source/check timestamps, missing-data states, delayed-update
  notices and bounded public offline snapshots. Offline snapshots keep their
  original release and period; 404/authorization errors do not use stale fallback.

The passport-index entry explains that permitted publisher data access is still
needed. No passport ranks, subscription or assumed public API were fabricated.
WHO and MoSPI direct connectors, more indices, all-chapter reviewed briefs,
account-saved revision cards and Stats-specific practice are future extensions.
Current health measures use World Bank WDI. General learner bookmarks/practice
continue independently and were not changed by Stats.

## Automatic checks

`ism-stats-refresh.timer` runs daily at 02:10 India time, with up to 15 minutes
of jitter and catch-up after downtime. The oneshot service runs as `www-data`,
uses `/etc/mpsc/db.env`, and has a 20-minute timeout. Standard PGDATABASE/libpq
variables are respected; an explicit DATABASE_URL takes precedence. Credentials
stay in the private server environment.

The initial on-demand full service run encountered two transient World Bank
failures and correctly retained published data. Bounded retries now restart the
entire series with a smaller page size if the provider/CDN rejects the original
request. The subsequent full service run completed successfully: all seven WDI
series, HDI and three official catalogue checks. No duplicate releases were made.
See `../reports/stats-release-20261115/first-successful-refresh.txt`.

World Bank checks can publish validated, approved series automatically. Schema,
period, units/series mapping, country coverage, complete pagination and edition
consistency are checked. Large revisions, coverage loss, period regression or
methodology changes stage a pending release. Null future-year placeholders are
excluded; actual missing observations remain null. Regional/income aggregates
are excluded from country comparisons. Calculated ordering uses raw values and
explicit competition ranks and is labelled separately from publisher indices.

HDI changes stage for owner review. NITI/Survey/UNDP landing-page checks detect
changed report links and labels; they do not automatically produce reviewed
content or discover arbitrary new APIs. An unchanged URL whose file bytes change
is not reliably detected by the catalogue watcher alone. Recheck exact document
bytes/source hashes during the next report import. WHO Athena is retired and is
not used.

A changed Survey catalogue pauses its document buttons because stable government
URLs may be reused for a newer edition. Stored edition figures remain dated.
Updating the catalogue requires a source-checked code/content release; there is
no one-click owner catalogue-acknowledgement UI yet. This intentionally avoids
unfreezing old-edition links without confirming their targets.

## Review and import APIs

Stats owner endpoints use existing cookie identity, same-origin CSRF, explicit
owner grants and staff MFA policy. Learner mobile tokens cannot access them.

```text
GET  /api/stats/admin/releases
GET  /api/stats/admin/releases/{release_id}
POST /api/stats/admin/releases
POST /api/stats/admin/releases/{release_id}/decision
```

GET list includes source-watch health/change flags. Inspect the complete candidate
payload and its source before deciding. POST release accepts the strict
`ReleaseInput` schema from `api/app/services/stats.py`; payloads are capped at
4 MiB, use approved source domains, and cannot mix calendar and financial years.
Decision accepts `decision: publish|reject` and a descriptive note (10–2000 chars).
Every decision is immutable history. Initial report ingestion is attributed
`source-checked-bootstrap` after Codex source inspection; it is not represented as
an independent human or owner sign-off. Later submitted payloads cannot acquire
that attribution by claiming the same upstream hash.

There is no dedicated owner-review frontend in this release. Use the protected
APIs with the ordinary owner session. Never paste session cookies into scripts or
repository files. Source registry/catalogue changes are normal code deployments.

## Server checks and recovery

```bash
sudo systemctl status ism-stats-refresh.timer
sudo systemctl status ism-stats-refresh.service
sudo journalctl -u ism-stats-refresh.service -n 30 --no-pager
sudo systemctl start ism-stats-refresh.service
```

A failed import is recorded per metric and exits nonzero for service visibility;
last good published values remain available. `stats_checks.succeeded_at` advances
only on successful validated ingestion, not on a failed attempt. `stats_import_runs`
retains bounded errors. Pending/rejected releases never enter public responses.

New numbered migration 0084 creates only independent Stats tables and grants.
It was rehearsed on a fresh production dump clone with the existing bank identity
fingerprint unchanged. Unrelated 0083 remains unapplied on production. Applied
0084 is immutable. Source rollback keeps its additive tables/receipts for recovery.
No bank content, publisher, assessment state, Caddy or payment configuration was
changed. Both study.hawayu.in and family.hawayu.in passed health checks.

Four frozen receipts record the successful bounded API source releases. The
first attempted installation passed its clone rehearsal, then rolled source back
when the new job used a development default database. The audited resume reused
0084 after checking its exact checksum and rehearsal evidence. Runtime selection
was corrected to match the shared libpq environment. No broad API checkout sync
or unrelated migration replay was used.

Do not rerun the frozen `deploy-stats*.sh` targets after their preimages change.
Prepare a fresh bounded manifest and new receipt for future edits. Inspect the
receipts under `../reports/stats-release-20261115/`; they preserve the exact remote
source hashes and rollback directories. Migration DDL must use a new migration
for future schema changes.

## Validation and remaining release limits

- 49 API tests (24 Stats + 25 existing mobile companion); disposable PostgreSQL.
- 52 existing/new component checks plus three focused offline-cache checks (55 unique component/cache tests).
- 29 domain checks; mobile lint/typecheck and Android/iOS/web exports passed.
- Actual 390×844 browser QA: Library entry, India values, India/China common-year
  comparison, HDI publisher ties/India pin, separate NITI groups, Survey table
  search and estimate labels. Temporary viewport reset after verification.
- Service full refresh and live public readback receipts preserved. Razorpay
  checkout remains disabled.

Exports are not signed device binaries. Existing Expo sign-in/project ownership
and physical-device QA prerequisites remain separate. No new APK/IPA, App Store
submission or physical-device test is claimed here.

Final follow-up: rankings now request the same release ID as their detail view,
including when Latest is selected. This prevents a background publication from
mixing two releases on one screen. Three offline-cache regression tests passed.
The local temporary import database and development API/Metro servers were
removed/stopped after live verification; the8089 preview remains running against
the deployed public Stats API.


## Website extension — 15 November 2026

The public website now includes `/stats`, metric history/comparisons and rankings,
Economic Survey chapters/figures/searchable appendix links, and source/update
explanations. Entry points: Library modules, Subjects menu, More, and Quick Find.
Phone navigation keeps Stats within Library. The website follows the supplied
Finna tokens, including light/dark themes and the 1320px desktop shell.

Rankings are pinned to the metric response's exact release, including when the
selector says Latest. Comparisons retain a common reference year and at most four
places. Historical HDI scores do not acquire invented publisher ranks. Survey
catalogue changes pause every edition-sensitive document link. Public GETs omit
account credentials; a bounded 24-entry, 24-hour browser cache retains snapshot
periods/dates during transient failures. Missing/authorization responses do not
use stale fallback. This is cached data access, not a service-worker offline app.

Validation: production TypeScript/Vite build; focused Stats component/helper,
cache, request-race and failure checks; existing Quick Access and Review Navigation
regressions. Browser checks used live API data at desktop and nominal 390px phone
width, including HDI country/year changes, appendix search, light/dark rendering,
and no page-level horizontal overflow. Web artifacts were built locally and shipped
with `scripts/deploy.sh web`; no API/schema/bank/Caddy changes. Saved rollback:
`/srv/study/backups/stats-web-20261115/public`. Deployment/readback evidence:
`../reports/stats-web-20261115/`.

The automation and content limitations above still apply. A recent successful
source check does not certify the newest possible report edition. Daily scheduling
is enabled and the full service was tested successfully; its first scheduled daily
trigger had not occurred when the 15 November website work was verified.
