# Oracle paper workbench and bank authority

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
