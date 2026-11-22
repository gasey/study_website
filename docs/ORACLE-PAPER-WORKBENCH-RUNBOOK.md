# Oracle paper workbench and bank authority

## Current collection-performance recovery — 20 November 2026 IST

The empty-pins release changes only `app/routers/collections.py` and matching
`app/data/learning-economy-v2.json`. Current root-only backup: `/root/finna-empty-pins-backup-c8_khz6p`.
On Oracle, `sudo python3 /root/finna-empty-pins-backup-c8_khz6p/deploy.py --restore /root/finna-empty-pins-backup-c8_khz6p` validates the
released API/static/configuration/schema history and both prior preimages, then
restores the pair and restarts/health-checks only `ism-api`. It refuses newer drift
before stopping services. It preserves all database, mail, learner and payment history.
Recovery tests pass; production recovery has not been invoked. Never replay this
or older frozen deployment targets. Receipt: `reports/finna-empty-pins-20261120/README.md`.

Implemented 3 November 2026. This runbook supersedes the earlier local-publisher location. Workflow ownership remains unchanged: JSON owns exam content; PostgreSQL owns accounts, attempts, review decisions and workflow history.

## Everyday work

- Prepare a new source in `/paper-workbench`. Upload its original PDF (20 MB, up to 300 pages). Confirm the exam name/year from its pages, booklet and printed question count; the filename is not identity evidence.
- Extract selectable text, split clear numbered blocks, or transfer a selected block into an editable question. Scans can use local English Tesseract OCR. Equations, Mizo, tables and unusual layouts still need inspection. No generative AI runs during preparation or play.
- Choose MCQ or written format, preserve instructions/passages, inspect options and approved learning tags, and attach a crop from its actual source page when needed. Keyboard users can enter normalized crop coordinates.
- Save explicitly. Scratch text is a transfer aid, not a saved question. Saved draft versions are immutable; restoring creates a new version. Concurrent stale saves are rejected, and saving invalidates an earlier submission/approval. OCR jobs never overwrite manual question text.
- If the PDF is already registered and has no questions, choose **Use this empty
  original**, then save. This binds the exact original paper and current registration
  to the reviewed draft and adopts its existing exam name/year/paper subject. The
  publisher preserves the original paper row and document registration rather than
  creating an Uploaded alias. Multiple matching identities or a paper that already
  has questions require source resolution or the existing correction workflow.
  Changing the original link invalidates approval. Source/metadata changes or a
  competing extraction stop publication. No automatic module/assignment additions
  accompany this link; future publication populates the already selected source.
- An official answer requires the uploaded key, its document title, exact booklet mapping and physical key page. Human unofficial solutions stay labelled and do not enter official-key scoring.
- The owner can assign an existing account to this exact draft, or revoke that assignment. This grants no general bank or publishing role. Someone who has ever edited the draft cannot approve it. Four explicit inspection checks and an evidence note are required.
- The owner queues the current independently approved revision. The Oracle publisher rechecks roles, source hashes and review identity, appends the paper under the common bank lock, syncs it, and reads back source identity, question types, text/options/answers, context, figures, booklet and taxonomy before reporting publication. It registers both paper and key documents.
- A failed job retains its reason. Retry reuses a durable receipt and refuses a changed submission. Never change a bank hash or regenerate protection state to force a retry.

Existing UDC/Prelims review stays at `/editorial`. Solomon retains Prelims; Sangzel retains UDC. The protected 78-paper / 6,931-question membership was preserved. New papers do not silently join those frozen assignments or collection versions. A checklist or approved taxonomy is not final source/answer certification.

## Runtime

| Component | Location / service |
|---|---|
| Writable JSON bank | `/srv/study/workshop/mpsc-question-bankv2/bank/mpsc_bank_v2.json` |
| Operator scripts | `/srv/study/workshop/india-study-map-app/scripts` |
| API | `/srv/api`, `ism-api` |
| Private originals and page derivatives | `/srv/study/private/paper-workbench` |
| Browser source archive | `/srv/study/papers/source` and `/srv/study/papers/figures` |
| Document processing | `ism-paper-documents`, www-data, one leased job, bounded subprocesses, 1 GB memory / one core |
| Reviewed paper publication | `ism-paper-publisher`, privileged canonical bridge; does not parse PDFs as root |
| Existing correction publication | `ism-oracle-bank-review.timer` |
| Paired recovery snapshots | `ism-workshop-backup.timer`, daily, `/srv/study/backups/workshop` |
| Private copy on this computer | user `ism-oracle-recovery-pull.timer`, hourly / after startup, `~/.local/share/ism-oracle-recovery` |

The private workshop root is not web served. There is no new public admin service or port. No Caddy configuration was changed. Credentials remain in root-only existing environment files. Original source PDFs, figures, registered evidence, protection state, receipts, taxonomy and parser code were transferred; old local backup trees and unused parser caches remain local. The initial copy also retained some unused partial data on Oracle. The whole workshop occupies about 4.3 GB, with 79 GB free at cutover.

Document tools are Poppler, qpdf and Tesseract. Jobs cap PDF bytes/pages, output size, CPU, address space, open files and wall time. The document daemon runs as www-data with filesystem/network restrictions; bank publishing is separate. Graceful stop finishes the leased job before deployment replaces worker code. Deployment drains publishers and restores services even after a deployment failure. The bank lock serializes paper imports and ordinary reviewed corrections.

## Maintenance

Use SSH through the existing operator account. For authoritative status, run on Oracle:

```sh
sudo bash -c 'cd /srv/study/workshop/india-study-map-app; ISM_DB_TRANSPORT=local ./scripts/sync-bank.sh --check'
sudo systemctl status ism-paper-documents ism-paper-publisher ism-oracle-bank-review.timer
sudo journalctl -u ism-paper-documents -u ism-paper-publisher -u ism-oracle-bank-review --since '1 hour ago'
```

Deploy from this checkout with `./scripts/deploy.sh api`, `web`, or `all`. Build only locally. Applied migrations 0066–0068 are immutable. Rehearse future migrations on a dump clone, then apply. After systemd/Postgres changes, check both study.hawayu.in and family.hawayu.in.

The 10 November paper-order change uses `./scripts/deploy.sh question-order`
for the question-list router only, followed by `web`. It checks the reviewed
router preimage, retains a rollback copy, and restores it if health checks fail.
It does not ship unrelated API or workshop changes or modify bank records.

For the empty-source import extension, `./scripts/deploy.sh paper-source-import`
ships only the paper-workbench router, target resolver, publication bridge and
guarded paper writer. It drains/restarts the previously active paper workers and
keeps an API/script rollback under `/tmp/paper-source-import-*/backup`. It requires
no migration, dependency installation, authority-policy change or baseline reset.
Deploy its source-link UI separately with the normal `web` target.

`api/.venv/bin/python scripts/rehearse-existing-paper-import.py --output /tmp/FRESH-DIRECTORY`
runs a disposable local rehearsal with synthetic accounts/approval, the actual
publisher and normal sync SQL. It verifies preserved original metadata, no Uploaded
alias, written/unanswered-MCQ readback, and recovery from an intentional interruption
after SQL commit. Only CSV transport paths and the disposable database name differ;
it never changes the canonical bank, policies, live accounts or human attestations.

The local authority policy intentionally points to the Oracle machine and path. Local guarded writes and real syncs fail closed; read-only checks can compare the recovery snapshot. A later Oracle publication makes this local snapshot stale, not authoritative. Do not re-enable `ism-bank-review.timer`, reset the policy, force a JSON overwrite or introduce a second writer. An AI/parser candidate must be reviewed against current Oracle source versions.

Publication pauses below 10 GB free. New per-publication backups are compressed. Existing backups are retained; no automatic pruning was introduced.

## Recovery

The daily root-only snapshot pairs a PostgreSQL custom dump with the canonical JSON, receipts, taxonomy, editorial protection state and private uploaded PDFs/crops. Its receipt contains file checksums. The job reopens the archived bank and verifies its hash; the local pull verifies both archive and dump after download. Downloads are read-only and use mode 700/600 storage. A powered-off computer cannot fetch a new snapshot; its timer retries when online. Continuous independent cloud offsite storage is not configured.

The immutable pre-cutover sources remain in the original local workshop; their 22,272-file checksum manifest was verified against Oracle. New workbench uploads and crop bytes are included in the paired archive. Preserve those source files alongside snapshots for disaster recovery. Older source assets are not redundantly re-archived every day.

A real restore of the first workflow dump into `ism_paper_fullpilot` passed. In that isolated clone, upload → extraction → mixed MCQ/written editing → exact reviewer assignment → independent approval → paper/key publication → full JSON sync → readback all passed. It preserved 244 existing attempts. The synthetic test database and workshop were then removed. No synthetic paper, key, sign-off or account was added to production.

For a disaster recovery: stop publishers, restore the database into a separate database first, restore bank/receipts/taxonomy/protection and private uploads, recover original assets from the verified source copy, and compare hashes/counts before switching. A different machine requires a deliberately verified authority-policy change; never copy an old machine fingerprint as a bypass. Rehearse the restored instance before enabling one canonical publisher. Never restore only JSON over newer learner/workflow data.

## Topic Trail

`/trail` launches one **Prelims · Constitution basics** pack: ten exact source IDs, all original stems/options matched to their PDF pages. It uses existing official-key eligibility, original years, immutable game snapshots, assessment reservations and reward claims. Ten stones, 20 seconds per question, paused feedback, one Double next before reveal, maximum 1,100 run points. It never rewrites historical keys or calls AI during play.

The owner tool at `/admin/topic-trail` supports approved topics and inspected exact source lists, current usable counts, versioned edits and pausing new starts. Identical questions from different booklets cannot inflate a trail pool. Broad taxonomy approval does not certify narrow topic membership: the live physics pool included geography, so it was not launched; vocabulary had only seven distinct eligible questions. The first ten-question pack is a pilot with limited variety, not a full syllabus or mastery claim. Add packs after source review and student feedback.

Historical/current affairs connections remain independently reviewed dated facts in `/current-affairs/manage`, with assessment withholding and unchanged original keys. The feature supports appointments, rankings, trade, production, statistics, schemes, awards, records and events; no current facts were automatically populated.

## Dated Gazetted owner-authorized AI completion

The owner delegated completion of the ten reviewed Gazetted papers on 4 November
2026. Migration 0076 adds an explicit approval kind, model and immutable evidence;
it does not relabel AI work as an independent person's inspection. The installed
`gazetted-owner-ai-review-20261104.json` scope binds one existing owner and exactly
ten source SHA/payload hashes. The owner-only `owner-ai-review` handler requires a
submitted current version and all four review checks. Publication checks the same
scope/evidence again. Normal independent approvals still reject the author or any
past editor. Future edits and other papers cannot reuse this approval.

Keyed payloads must explicitly choose `provisional` or `final`. The publisher
registers and reads back that edition; conflicting existing key metadata fails
closed. The shared editor clears the edition when replacing a key PDF. For the
September 2026 Gazetted exam the inspected eight-page official key is provisional;
726 entries use it and six source/key conflicts remain unanswered with visible
notes. Written prompts have no fabricated model answers.

The empty-source writer follows normal sync's legacy scope behavior: an absent
JSON examScopeId preserves the reviewed SQL backfill. Explicit JSON scope values
and every other identity field must still match. The target snapshot is rechecked
before and after normal sync; no original paper row is rewritten.

Deploy this bounded release with `./scripts/deploy.sh gazetted-review` after the
rehearsed 0076 migration. It includes source-bound General Studies learning roles,
the exact scope and the guarded writer. Source titles use the existing identity
handler; membership uses the existing versioned module composer. The portable
completion receipt records module v3 and the unchanged outside-module state.

Use `--owner-ai-provisional-key` with the disposable rehearsal script to exercise
attributed approval, provisional key registration, publication/sync and recovery
from a lost acknowledgement after SQL commit. Synthetic accounts stay in its
throwaway database. This release does not authorize expanding the installed scope.

## PDF Library — 5 November2026

The staff entry `/admin/bank?tab=pdf-library` reconciles canonical PDFs, served
sources, private uploads and registered evidence against paper IDs and drafts.
Scans write only the PostgreSQL discovery index. The last complete generation
remains visible after interruption or failure. Identical hashes group byte copies,
not paper identities. Recorded exam expectations and learner module membership
remain separate. The Library exposes direct next actions and receipts; ingestion
and content certification retain the existing workbench/review/publisher gates.

`ism-pdf-library.timer` checks queued/running scans each minute. The daily
`ism-pdf-library-refresh.timer` requests a scan at21:15UTC. A stopped scan resumes
its running generation; unchanged size/mtime/ctime reuses a cached hash. File/hash
changes invalidate intake. Scan errors retain the previous snapshot and put
operator details in the service journal. See `systemctl status` / `journalctl -u`
for both matching services; never reset content protections to clear a scan error.

API drop-in `ism-api.service.d/pdf-library.conf` bind-mounts only the canonical
`pdfs` subtree read-only at `/srv/study/private/pdf-library/archive`, configured
through `PDF_LIBRARY_ARCHIVE_ROOT`. The private canonical bank and its parent
permissions remain unchanged. The upload source directory is root:www-data2770;
new uploads retain content-addressed private file permissions. Root scan workers
use the ordinary mpsc database role and a read-only filesystem service sandbox.

Deploy with `./scripts/deploy.sh pdf-library`, then `./scripts/deploy.sh web`. The
release script checks the inspected source preimages (or identical current
payload), checks/applies only0077, backs up affected files and installs the units.
Changed preimages require inspection before a future update. Rehearse new schema
on a disposable dump clone first; `scripts/rehearse-pdf-library.py` refuses a DB
name outside the `ism_pdf_cms_rehearsal_` prefix. It reads source files and writes
only that disposable discovery index.

On release failure the script restores API/service files and upload-directory
permissions; additive index tables remain. For a later manual rollback stop both
new timers/services, restore affected API/drop-in files from the release backup,
reload systemd and restart API. Restore the previous library navigation/workbench
frontend source and rebuild/deploy web. Do not drop workflow or bank tables.
After service changes verify both study.hawayu.in and family.hawayu.in, the read-only
PDF mount, normal bank sync and exact source/permission/module preservation.

## Explicit owner decisions (6 November 2026)

Global owners can preview a saved paper and explicitly publish it themselves.
`owner-preview` validates the same source/layout/key conditions as submission;
`owner-publish` binds the inspected source SHA, payload, author, submission and
preview version in an immutable `review_kind=owner` decision. The worker rechecks
current owner permission and exact evidence before guarded JSON publication.
Independent and narrowly scoped `owner_ai` records keep their distinct meanings.
No checkbox is checked automatically and an agent must not invent an inspection.

Deploy this feature with `bash scripts/deploy.sh solo-owner`, then `web`. The
bounded release checks API and bank-writer preimages, rehearses migration0080 on
a disposable full production dump, compares content/attempt/grant/workflow
fingerprints, drains publishers, and backs up API plus `paper_bank_store.py`.
It applies only the unapplied numbered migration with its checksum atomically.
Restore both tar backups on rollback and restart API/workers; keep the additive
schema. Do not roll back content or recreate source-protection baselines.

Routine owner edits use generated factual change summaries with optional notes.
Answer/key reasoning, source hashes, scoring holds, publication receipts and
protected assignments are still enforced. Learning tests have an explicit owner
preview/publication path; ordinary user proposals retain independent review.

## Serial correction export — 7 November 2026

`PUBLICATION_SERIAL_QUEUE=true` is operator-managed for both ism-api and
ism-oracle-bank-review. Ordinary saves behind an active export remain accepted and
store a publication-intent in review_outbox. With the bank lock held, the worker runs
`/srv/api/promote-publication-queue.py` as the PostgreSQL operator. It checks the
original approved revision, current permissions/evidence and exact current source
before creating a new immutable manifest against the latest completed sync. It
never rewrites an old manifest, baseline or review. Stale source/permission changes
fail with recorded reasons. Bulk tags wait for a free export slot and keep their
atomic batch path. Known obsolete exports cannot be repeatedly retried; reopen the
current source and save a fresh decision. Failed history remains available.

Deploy with `scripts/deploy.sh backend-audit`; this bounded release verifies
preimages, drains the existing correction worker, saves rollback files, updates
only listed API/worker files and the two queue-setting drop-ins, verifies API and
helper imports/DB access, then restores the timer. No migration, dependency change,
shared Caddy edit or content repair is involved. Disable the serial queue only after
its publication-intents are finished or explicitly reconciled; otherwise accepted
jobs will wait for the new worker to be restored.

The follow-up `scripts/deploy.sh backend-followup` updates only bank_publication.py
and bank-review-worker.py, with fresh preimage checks, publisher drain, rollback and
health/helper checks. Slot acquisition precedes checksum capture; source is checked
again at that boundary. Pre-export retries retain their original admin binding.
A bounded five-intent scan skips terminal intent failures without dropping history.

## On-demand publisher wake-up — 7 November 2026

`ism-publication-wakeup.service` listens for the empty `ism_bank_publication`
PostgreSQL signal sent when accepted/publishing changes commit. It uses the existing
limited application database credential with read-only transactions and only calls
`systemctl start --no-block ism-oracle-bank-review.service`. It ignores payloads,
uses fixed tokens/commands, restarts after disconnect, and checks for pending work
at5-second intervals to recover missed wakes. The existing publisher and60-second
timer remain authoritative and keep all guards. Stopping the wake-up service falls
back to the timer. No schema changes or credentials in files are added.

`deploy.sh publication-live` checks exact API preimages, drains the publisher,
backs up files, installs the listener/unit and API changes, verifies notification
wake-up and both sites, and restores the timer. The UI uses a cheap scoped progress
pulse at3-second intervals while pending; it reloads the bank list only on changes.

## Mobile learner companion — 15 November 2026

The bounded `scripts/deploy.sh mobile-companion` target released six exact API
files with preimage checks and rollback copies. It changes learner native access,
owned authoring/session tools and deferred Razorpay setup only; no bank, migration,
Caddy or publisher operation is performed. The frozen successful receipt is in
`reports/mobile-release-20261115/receipt.json`. Its preimages intentionally stop
an accidental repeat over a newer deployment; do not replace them to silence a
mismatch. A future release needs fresh reviewed preimages and a new receipt.

Live checkout remains disabled. Later payment activation follows
`docs/RAZORPAY-LATER.md`, with test credentials and a separate staging database
first. Password/MFA/reviewer decisions remain in their existing protected flows.

A separate one-file `mobile-credit` follow-up fixes the native Points summary
without delegating cookie/staff identity. Its frozen preimage and separate
`credit-followup.json` receipt preserve the initial release evidence.

## Stats — 15 November 2026

Stats uses independent 0084 tables and a daily `ism-stats-refresh.timer`; source
imports never mutate the bank. See `FINNA-STATS-OPERATIONS.md` and the frozen
`../reports/stats-release-20261115/` receipts. The migration passed a production
clone rehearsal. The bounded resume corrected the job's libpq database selection
and preserved applied-migration checksums. Future deployments need new preimages;
do not replay frozen targets or apply unrelated pending 0083 to update Stats.

## Owner billing controls — 16 November 2026

The bounded `scripts/deploy-owner-billing.py` release installed billing, auth, me
and rewards router changes plus migration0089 after a full-dump clone rehearsal.
It checks exact source preimages, records the migration checksum and saves paired
API/web/database rollback data under `/root/finna-owner-billing-suy2t3ca`.
Frontend deploy used the standard web target. No bank files, Caddy or systemd unit
files changed. Old provider price references remain historical. Do not replay the
fixed-preimage installer over newer code; create a fresh bounded release instead.
The server checkout flag remains false. See ACCOUNTS-BILLING.md for owner controls.

## Finnaplan V.5 release and recovery — 17 November 2026

V.5 is deployed through the bounded `scripts/deploy.sh finnaplan-v5` target;
0097 is applied/immutable, next free0098. Evidence and exact frozen hashes are in
`reports/finnaplan-v5-recovery-20261117/README.md`. Do not replay frozen installers
over later releases or deploy the whole dirty API checkout.

Private paired recovery data: `/root/finna-v5-backup-olyz_k9b`, including prior
API/static/database plus the released API/dependency/static snapshots. Ordinary
recovery must preserve new purchases, moderation-aware bio reads and closed-account
identity/credential/entitlement guards. Use the frozen `recover.py` in that backup
with the backup directory as its sole argument, as root. It validates artifact and
SQL-guard preimages, drains publishers, pauses new V.5 writes and pairs the current
safe API with prior static. It retains additive schema/history and verifies both
sites. Data export, sign-out, calendar deletion/feed revocation and owner moderation
remain available. Rehearse a bounded forward repair before resuming writes.
Never restore V.4 validators/readers or a full database dump over subsequent
learner history as routine rollback. Catalog and paid checkout remain disabled.

## V.12 operations dashboard — 18 November 2026

The owner reads `/admin/ops`; `/api/admin/ops` requires a current owner cookie,
uses read-only RR SQL and sends private/no-store. Native credentials are excluded.
`/ops-runbook.html` is a public, generic investigation guide; it contains no live
telemetry or credentials. The detailed release is
`../reports/finnaplan-v12-ops-20261118/README.md`.

This slice changes four API readers/helpers/registration files and static assets.
It does not install heartbeat writers or systemd collectors. Mail/mastery use
existing receipts; assessment’s legacy health is separate. Missing assessment /
desk/calendar/game cycle receipts and timer/backup/disk collection show unknown.
Use existing systemd status/journals and verified paired-backup receipts through
approved server access. Do not infer backup restoration from a timer result.

Future collection must use real per-cycle outcomes, preserve last success after
failure, and report host disk/verified backup independently. Attach timer outcome
collection to each actual job; do not fabricate backfilled successful executions.
Modifying game/mastery/mail reward-bound sources requires new economy evidence;
never rewrite old proof artifacts to accept new writer hashes. Implement retention
and genuine monthly restore receipts separately. The seven-day-green gate remains.

Private release backup: `/root/finna-v12-ops-backup-52_pa_zk`. Its `deploy.py
--restore <backup>` validates every installed API/schema/static hash before
restoring prior read helpers, registration and static. Existing writers,0109and
history remain. Disposable recovery passes; no production recovery was invoked.
Never replay this or an older frozen target after another release. Both sites
returned200 after deploy. Current source/proof hashes and exact readbacks are in
`release-scope.json` / `release.json`; no database migration was needed.

## V.12 worker cycles and host collectors — 18 November 2026

Supersedes the earlier dashboard-only collection-pending note. Actual assessment,
desk/calendar/game cycles and mastery failures use the existing shared heartbeat
table. Success commits with work; post-rollback failures preserve prior last_ok.
Disk and paired-backup probes are written by root-owned `/srv/api/ops-collector.py`
through local peer PostgreSQL access. No credentials or public endpoint is added.

`finna-ops-host.timer` runs the oneshot every five minutes. Read status/journal for
this service if disk/backup collection is stale (>15minutes) or fails. Available
disk below10GiB needs attention. The newest real paired backup must have no
INCOMPLETE marker, matching archive/dump digests and a readable dump index. Changed
file identities/metadata invalidate the private `/run/finna-ops/backup-verified.json`
cache. Corrupt/newer incomplete backups do not fall back silently. Backup last_ok
is the actual backup creation time; older than48hours is stale. This verification
does not prove a successful monthly restore or offsite continuity.

Only `finna-ops.conf` is added to the bank-review, workshop-backup and stats service
drop-in folders. ExecStopPost reads actual result and normal-zero-exit evidence;
collector failure is ignored by the original job but becomes stale dashboard data.
Base units, existing drop-ins, schedules and authorities are untouched. No original
job is started by deploy; first natural daily results can remain unknown. Check
real unit journals rather than inventing successful historical receipts.

Guarded release:`scripts/deploy.sh finnaplan-v12-workers`. Full evidence is in
`../reports/finnaplan-v12-workers-20261118/README.md`; private backup:`/root/finna-v12-workers-backup-9r_rlztk`.
Its exact-source restore refuses later API/static/unit/collector drift, disables
only the new host timer, removes this collector/drop-ins and restores matching
prior API/economy evidence/static. Existing base units, schema/history and
heartbeat rows remain. Disposable recovery passes; production recovery not invoked.
Both sites200 after release. Never replay a frozen target over later work.

Installed server systemd behavior is tested with isolated transient success/failure
services. No new real publication/backup/stats run or false timer receipt is used.
Next account viewer/retention/site notice and monthly restore/checklist work are
separate; the genuine healthy-week gate still needs elapsed operation.

### Final collector timing classification — 18 November 2026

Host verification/peer persistence can take longer than100ms. Timer outcome state
comes from the collector's structured result, with freshness/future-time checks;
it does not use the in-process stamp tolerance to reject a real successful job.
This read-only follow-up changes only ops.py. Current worker/host/bank-review
observations and disk/backup probes are healthy; first backup/stats hook outcomes
wait for their real next runs. A natural bank review outcome already verifies its
post-command flow. No original job was manually run for proof.

Latest guarded reader target:`finnaplan-v12-collector-time`;backup:`/root/finna-v12-collector-time-backup-5atf23ce`.
It preserves all installed units,collector,economy-bound sources,schema and static.
Its exact-source restore only restores the prior classifier. The older worker
operator refuses the newer API hash; never replay it over this update. Read the
correction report before recovery. Bothsites200;ledger46→46;no production restore.


## V.12 read-only account support — 18 November 2026

Global owners use `/admin/users` to search an exact email or literal handle prefix
(minimum3characters). Existing staff MFA policy applies to these private reads,
including the already configured exact immutable-account exception. Scoped owners
and native bearer credentials do not gain access. Select one of the first20matches;
narrow the handle when more exist. Refresh replaces the snapshot and an outage
stays an error. Active/scheduled access receipts cap at50each; ledger shows latest20.
Cap days cover30ISTdates including today. Last activity comes from actual sign-in,
security and attempt receipts, never a generic last_login field. Routine browsing
is not monitored. No answer/desk content, credentials, device IDs, ledger item
notes or block identities are exposed. Use linked existing billing/moderation
consoles for changes; their ordinary MFA/CSRF/audit controls remain authoritative.

Release: `reports/finnaplan-v12-users-20261118/`. Bounded target
`scripts/deploy.sh finnaplan-v12-users` is frozen and installed; never replay it.
Backup `/root/finna-v12-users-backup-8eqzsmv9` contains exact prior reader/static
recovery. Its `deploy.py --restore <backup>` refuses newer API/schema/static or
collector/unit drift, then restores the prior pair while preserving all history,
writers and installed collectors. Disposable recovery passes; production recovery
was not invoked. Final248-table clone and actual-mpsc reads pass;ledger46→46,
bothsites200. No SQL migration;0109immutable,next0110.68economy-bound sources
and13collector/unit paths unchanged. Mail/checkout stay off. Retention/site notice,
monthly restore receipt and the actual seven-day-green gate remain separate work.


## V.12 monthly maintenance checklist (deployed, 18 November 2026)

The monthly checklist is run by a human and receipted in DEVLOG. The dashboard
and agent audits supply evidence; neither substitutes for human sign-off. Check:
actual paired restore, dependency/CVE reports, TLS and **both** sites, slow-query
history, economy diagnostics, moderation backlog, disk/log rotation and every
worker/collector. Missing data and open advisories stay open. The18November
agent-assisted audit is reports/finnaplan-v12-maintenance-20261118/MONTHLY-CHECKLIST.md;
its slow-query review is unavailable because duration logging is disabled and
its dependency reports contain findings. No whole-checklist/green-week claim.

The source-bound actual paired restore already completed against the17November
backup (232archived tables/124944files). It used an isolated database and private
files, compared the restored bank checksum under read-only mpsc, then removed
temporary resources before writing the actual operational receipt. This does not
certify current248-table migration contents, offsite storage or original source
PDF completeness. Failed restores preserve last success and expose attention.
The maintenance release installed the verified tool; use:
`sudo /srv/api/.venv/bin/python /srv/api/restore-rehearsal.py --run`.
The tool checks disk headroom and holds a private lock, never switches databases,
promotes bank files, starts publishers or overwrites source assets. Receipts live
in /srv/study/backups/restore-rehearsals; the dashboard warns at40days.

Hourly account retention uses500-row transient batches/20empty guests,
5s statements/1s lock waits and real count heartbeats. Current credentials remain;
expired credential creation times survive as account activity metadata, with no
cleanup-time fabricated activity. Durable attempts, reward/billing/adoption/replay
receipts never expire. Generated guest credentials must have expired over12months
ago; registered/closed/non-default/profile/access state or linked data protects
the account, including alternate/composite/future FKs and legacy actor IDs.

The owner site notice is plain text in Operations, optional expiry explicitly in
IST. Owner/MFA/CSRF/version checks and immutable owner account events apply.
Reload on a version conflict; Clear hides the banner and keeps audit history.
Public web pages refresh each minute and at expiry. These notice/admin endpoints
remain outside the native allowlist and advertised capabilities; old apps get403,
with explicit test_mobile_companion coverage. No device certification is implied.

Release target finnaplan-v12-maintenance is frozen and installed; never replay it.
Backup /root/finna-v12-maintenance-backup-n3jzh49v contains its exact pair and
database safety snapshot.0110is applied/immutable; next0111. Its bounded recovery
keeps0110 and all database history, the account viewer reader for retained activity,
and the verified restore tool/collectors; other API/static return to their prior
pair. Newer API/schema/static/tool/unit drift refuses recovery. Never replay an
older frozen deployment or restore a database dump over later activity.


## Python dependency release — 18 November 2026

Reports:reports/finnaplan-v12-dependencies-20261118/. FastAPI0.163.2/Starlette1.10.0
and three required pure-Python dependencies installed from exactly five fixed
SHA256-bound local wheels. No Oracle network resolution or API/static/schema /
provider/collector changes. Actual installed versions match the clean dated scan;
npm advisories and slow-query logging are separate open findings.1324full checks,
81focused/2supplemental recovery checks,249-table preservation and live checks pass.
The target finnaplan-v12-dependencies is frozen; never replay it. Backup
/root/finna-v12-dependencies-backup-afhwfwbb holds the old whole environment and
requirements pair. Its deploy.py --restore <backup> refuses newer code/static /
schema/environment/requirements/collector/restore-tool drift, swaps back the exact
old environment and requirements, and preserves all database history. No production
recovery invoked.0110remains immutable,next0111. Bothsites200;ledger46→46.


## Slow-query logging — 18 November 2026

Duration logging now uses1000ms; normal/error bind parameters are suppressed0.
log_statement remains none; existing stderr /var/log/postgresql/postgresql-16-main.log
mode0640 and weekly10-file rotation unchanged. The three settings in PostgreSQL16
postgresql.auto.conf were applied with reload only; API PID and PostgreSQL start
were unchanged. Real read-only mpsc probe1102.161ms was found with its bind canary
absent; no raw SQL/values are exported to reports. Read private logs for monthly
query review; collection starts today, never claim earlier records existed.
Sources and five operator checks:reports/finnaplan-v12-query-logging-20261118/.
Bounded target finnaplan-v12-query-logging is frozen; do not replay it. Backup
/root/finna-v12-query-logging-backup-9_m32fsh holds the prior private auto configuration
and operator/scope. deploy.py --restore <backup> refuses runtime/configuration /
rotation drift, resets only those three keys and verifies the exact prior file;
no database/history restore or service restart. Production recovery not invoked.
Bothsites200;all8workers healthy;integrity0;ledger46→46.0110immutable,next0111.


## Frontend build dependency release — 18 November 2026

Vite6.4.6/esbuild0.25.12/selector-parser6.1.6 are local build-tool updates; browser
runtime package versions and source markup unchanged. Runtime-only npm audit0;
one unpatched picomatch advisory accounts for11build-graph package-chain findings.
No blanket clean/risk acceptance claim.348built/3344served hashes,2996retained
chunks,17route/2entry asset checks and real-mpsc verification pass. API PID/schema /
code/environment/logging/rotation/collector files fixed;8workers healthy,bothsites200,
ledger46→46. Exact scoped target finnaplan-v12-build-dependencies is frozen; never
replay it. Backup /root/finna-v12-build-dependencies-backup-vjq_0cd7 holds prior
static contents. Its deploy.py --restore <backup> refuses newer protected state,
restores prior HTML/assets and retains new immutable chunks for already-open tabs.
No service restart or database/history rollback; production recovery not invoked.
Initial actual duration-log review found1operational probe+14other entries,max4.5s.
Investigate their normalized query shapes privately; no bind values exported.
Reports:reports/finnaplan-v12-build-dependencies-20261118/ and query-logging report.


## Bounded question-detail lookup — 18 November 2026

The observed4.5s derived-detail lookup now reuses question_readiness helpers with
bounded reviewed-publication probes. All83,383canonical readiness/reviewed flags
match the authoritative view; cloned derived SQL3–4ms,live five HTTPdetails19–30ms.
Every other question-router AST node/answer writer unchanged; helper newly bound
in the73-file evidence set.1335full/156compatibility/2supplemental recovery checks
and final249-table preservation pass. All8workers healthy,integrity0,ledger46→46,
bothsites200. No migration/source-key/award/visibility change;0110immutable,next0111.
Reports:reports/finnaplan-v12-query-performance-20261118/. Frozen target
finnaplan-v12-query-performance must never be replayed. Backup /root/finna-v12-query-performance-backup-scpanrxd contains exact prior /
released3-file reader/evidence pair. deploy.py --restore <backup> refuses newer
API/static/environment/schema/configuration/collector drift, restores only that
pair, restarts only API and preserves all DB/history. No production recovery.
Later query analysis must exclude benchmark-clone databases from primary traffic.
Collection counts~1–1.6s are separate shapes; no all-query performance claim.

## Opt-in review digest — 19 November 2026

Growth-only production bundle reconstructs the552 frozen frontend source hashes
and adds the preference component/route; Desk/Atlas remain at their prior release.
Only0120 is applied.0110/0120 checksums are immutable,0111–0119 remain local/unapplied,
0121 next unreserved. Default subscribers/outbox/delivery rows were0 on readback.
API/study/family/recovery healthy; ledger46→46,25integrity counters0,76 runtime
bindings reconcile. Natural backup/statistics jobs now have actual healthy receipts;
that does not certify a full healthy operations week or monthly human sign-off.

The initial scoped deploy used `scripts/deploy.sh review-digest --check` then
`review-digest`; the two-file consent-throttle correction used
`review-digest-withdrawal`. Do not replay frozen installers against newer state.
Current root-only recovery backup: `/root/finna-digest-backup-dqul4iva`.
For an intentional matching-scope withdrawal:

```sh
ssh ubuntu@152.67.31.231 'sudo python3 /root/finna-digest-backup-dqul4iva/deploy.py --restore /root/finna-digest-backup-dqul4iva'
```

This refuses source/static/credential drift, keeps the compatible API/shared mail
capacity reader, retains0120 and all histories, disables only reminder sending,
and restores the exact prior static view. The unsubscribe API survives that static
restoration. Existing security mail stays enabled; credentials are preserved.
Never restore the older capacity reader after digest reservations exist. No bank,
workshop, Caddy, systemd unit or provider credentials were changed by this release.
Read both sites and recovery availability after a deliberate restart/withdrawal.

Feature availability is REVIEW_DIGEST_ENABLED in the existing private environment;
subscriptions are separate, prospective, verified-email-bound consent records.
Do not subscribe accounts for a test or force an evening-window send. The initial
real recovery email was a separately approved owner test, not digest consent.
Reports: `finna-review-digest-production-20261119` and
`finna-review-digest-withdrawal-20261119`; exact production source archives exclude
credentials. Actual first opted-in digest/DKIM presentation remains a natural-use
proof, not a claim from the fake SMTP sink.


## Referral access staging — 19 November 2026

Referral access is local code behind `REFERRAL_REWARDS_ENABLED=false`, with the
shared legal/recovery/live-checkout/reconciliation gates still required. It has
no production deploy target. Do not deploy the entire dirty API/static tree or
apply the draft migrations to exercise it. See [referral operation](FINNA-REFERRALS.md).
Draft0121 is reserved;0122 is next unreserved.0111–0119 remain local drafts;
applied0110 and0120 remain immutable. The live baseline is the digest/withdrawal
release above. Preserve its existing source-bound recovery backup.

Oracle has a legacy `postgres` default ACL granting new tables CRUD to `mpsc`.
New feature migrations must explicitly revoke inherited excess privileges before
adding their intended grants, and rehearse the resulting effective permissions
on a fresh production dump clone. Draft0121 does this for all referral tables.
Do not infer production privileges solely from a clean local test schema.

Private legal-page drafts live in [FINNA-LEGAL-DRAFTS.md](FINNA-LEGAL-DRAFTS.md).
They are unpublished and contain unresolved operator/support/refund and other
owner decisions. They do not satisfy the legal or provider-launch gate.

## Adaptive collection-count release — 19 November 2026

A three-file reader/evidence release retains indexed readiness below50k IDs and
uses authoritative bulk readiness above that threshold. Exact counts/eligibility,
section membership/source scope/held-paper semantics, DTOs, cache policy, writers
and all applied migrations are unchanged. Clone detail16–23% faster; subject-wise
live HTTP7213ms remains slow. No all-query performance claim.
1602backend tests,537/328compatibility,105/77bindings,25integrity and5recovery checks
pass. Fresh analyzed252-table clone preserves all original values and68 outputs.
All8workers, both sites/API/recovery healthy; ledger46→46. Static3470,source310,
private environment/schema unchanged; no new emails or synthetic learner activity.
Receipts:reports/finna-collection-counts-adaptive-20261119/ and
reports/finna-collection-adaptive-production-20261119/. The collection-adaptive
deploy target is frozen; never replay the completed release.

Current paired recovery, root-only on Oracle:

```sh
ssh ubuntu@152.67.31.231 'sudo python3 /root/finna-collection-adaptive-backup-xlky5zb3/deploy.py --restore /root/finna-collection-adaptive-backup-xlky5zb3'
```

The operator guards the exact released API/static/protected configuration/schema
history and three prior preimages before stopping API. It restores only those
three files and restarts/health-checks the API, preserving attempts, ledger, grants,
consent, recovery history, all tables and mail configuration. Newer unrelated drift
refuses before service changes. Restore this pair before considering the older
digest-withdrawal recovery; never splice evidence/source versions or roll back
database history. Healthy-week/legal/payment/native/content/human gates stay open.


## Subject-wise count join-order release — 19 November 2026

Two-file reader/evidence pair. Only subject-wise-practice's detail transaction
uses SET LOCAL join_collapse_limit=1; the aggregate uses prepare=False to prevent
shared prepared plans crossing IDs. Other IDs retain default join settings. Paper/
section reads and SQL/DTO/source/cache/scoring/writers stay unchanged. No schema,
global setting, stats object, private/mail configuration or bank change.
1716full tests,641/432compatibility,105/77bindings,25integrity,62proposal/5recovery
checks pass. Fresh analyzed252-table clone preserves values and68 outputs; target
23–40% faster. Live subject HTTP7213→4484ms; both checked payload hashes identical
to prior release. All8workers/sites/API/recovery healthy; ledger46→46.
Receipts:reports/finna-subject-count-order-staged-20261119/ and
reports/finna-subject-count-order-production-20261119/.
Do not replay the completed subject-count-order deploy target.

Current root-only paired recovery:

```sh
ssh ubuntu@152.67.31.231 'sudo python3 /root/finna-subject-count-order-backup-0vhv3tic/deploy.py --restore /root/finna-subject-count-order-backup-0vhv3tic'
```

The exact source/static/protected configuration/schema-history and prior preimages
are checked before API stops. Restore only these two files; retain all attempts,
ledger/grants/consent/recovery/audit/database history and mail settings. Drift
refuses before service changes; restart follows atomic-write failure. Restore this
pair before considering older adaptive recovery. Never splice source/evidence or
roll back database history. Actual healthy-week/legal/payment/content/native/PDF/
human/volume gates remain; synthetic calibration is not an operations week.

## Section-count investigation — 19 November 2026

No release or recovery change. Planner settings and flattened taxonomy alternatives
were rejected after two analyzed production-dump clones:72 alternative comparisons
preserve counts/all252 original table values per clone, but performance regresses
or gives no useful gain. Both exact clones/dumps/stages were removed. See
reports/finna-section-count-plans-20261119/ and
reports/finna-section-count-flat-20261119/. Current recovery stays the preceding
subject-count-order pair at /root/finna-subject-count-order-backup-0vhv3tic.
Never deploy the rejected probes or replay completed earlier release targets.


## Local restore privacy preflight — 20 November 2026

The installed monthly paired-restore tool above is unchanged. Successful dump/
archive readback does not establish that old credentials, closures, restrictions
or withdrawals are current. The local `scripts/check-restore-privacy.py --run`
provides a separate read-only comparison against an independently current reference,
with candidate credential/mail quarantine and immutable delivery-history comparison.
It is not installed or integrated into the production rehearsal, never repairs
state and always denies promotion authorization. Missing staged privacy schema is
an error; do not run it on the current production database as a supported candidate.
Follow [the private procedure](FINNA-PRIVACY-OPERATIONS.md#restoring-without-reopening-old-access)
for required environment names, isolation, currentness, reconciliation and limits.
All 107 scoped synthetic PostgreSQL/workflow checks pass; no production connection,
new timer, backup prune, service restart, mail or payment was performed.
[Evidence](../reports/finna-restore-privacy-preflight-20261120/README.md).
