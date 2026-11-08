# India Study Map — current working instructions

These instructions apply to every human or model working in this repository.
Historical logs explain past work; they do not authorize new operations.

## Start here

Read this file and `docs/PLAN.md`. For AI question work also read
`docs/AI-QUESTION-REVIEW-HANDOFF.md` and run its checkpoint command.
Read the relevant specialist runbook before operating that subsystem.
For tagging, classification, extraction labels or bank repairs, first read
`docs/QUESTION-TAGGING-RULES.md`. It is the single current tagging policy and
supersedes conflicting older classification handoffs. Use its model prompt and
fresh active registry IDs; unresolved semantic choices go to the owner.
For screens, consult `docs/DESIGN-FIDELITY.md` and the prototypes in `docs/design/`;
prototype markup takes precedence over its summary README. Record implementation
results and limitations in `DEVLOG.md` before stopping. Do not rewrite historical
receipts, decisions or applied migrations.

## One authority

The only writable bank is Oracle:
`/srv/study/workshop/mpsc-question-bankv2`. Its sibling app contains publisher
scripts; the API runs at `/srv/api`. Connect with `ssh ubuntu@152.67.31.231`.
This developer checkout's bank is a read-only recovery snapshot.

Bank content changes go through reviewed proposals, guarded JSON publication and
normal database sync. Never repair production bank content with SQL, bypass the
machine-bound authority policy, regenerate protection baselines to clear errors,
or enable the retired local publisher. Oracle's `ism-oracle-bank-review.timer`
handles ordinary corrections. The whole-paper publisher shares its bank lock.
Workflow/user data belongs to PostgreSQL and is never imported from bank JSON.
Use fresh authoritative checks rather than counts in historical documents.

## Review ownership

Parser/OCR output and AI drafts remain staged. Human edits invalidate stale drafts;
recheck exact sources at submission and publication. Preserve keys, provenance,
source identities, holds, attempts and immutable review history. AI agreement is
not source verification or an independent human sign-off.

On 4 November 2026, after asking Codex to finish the Gazetted review/publication,
the owner clarified "i dont understand...i just want it to be solved". The ten
exact source/payload/owner bindings in
`api/app/data/gazetted-owner-ai-review-20261104.json` therefore have a narrowly
scoped, explicitly attributed `owner_ai` approval path. Its immutable evidence
records AI-assisted source/key review and owner authorization, never a separate
person's inspection. Any edit invalidates that AI scope. This grants no authority to expand the scope,
alter frozen UDC/Prelims assignments, bypass MFA, or overwrite keys/history.
See `docs/sources/group-b-gazetted-completion-20261104.json` for the completed
publication and module receipt. Official 2026 keys remain **provisional**; the six
conflicting entries are unscored.

On 6 November 2026 the owner explicitly requested the solo-owner workflow.
Global owners may now make their own source-bound paper/learning-test publication
decisions through the admin preview and explicit publish controls. Attribute these
as `owner`, never as independent human or AI review. Routine owner corrections
and bounded bulk tags may omit a note; the server records a factual change summary.
Answer/key changes retain evidence requirements. Stale-source checks, guarded
publication/readback, holds, staff MFA and protected UDC/Prelims assignments still
apply. Ordinary user submissions retain independent review. Implementing this
workflow does not authorize an agent to claim source inspections it did not make.

Solomon reviews Prelims; Sangzel reviews UDC, through exact existing assignments.
On 3 November 2026 the website owner explicitly granted Sangzel
(sangzeldoto@gmail.com) the global owner/admin role. Solomon remains assignment-only.
Staff MFA remains required for admin changes. UDC/Prelims source protection stays
in force. Read `docs/HUMAN-REVIEW-UDC-PRELIMS.md` for those assignments and checks.
On 7 November 2026 the owner explicitly requested removing the authenticator
requirement for hruaitluangasailo20@gmail.com. The operator-managed
`STAFF_MFA_EXEMPT_USER_IDS` policy permits this exact immutable account ID to use
staff tools without MFA. Its unfinished setup was cleared; no active factor was
removed, MFA verification fabricated, password changed or role granted. Other
staff retain the existing MFA requirement. An optional enrolled factor still
protects sign-in. This account exception does not waive source protection,
evidence, stale-source checks or publication attribution.
Explanation backfill is explanation-only; source and answer repairs use their
separate existing workflows. Use ordinary allowance; past bounded quota exceptions
are historical and do not authorize a new exemption.

On 8 November 2026 the owner explicitly authorized confirmation/publication of
the saved approximately 10k AI tagging reviews: “do it we should trust atleast one
model no”. The exact 10,686-target scope is frozen at SHA256
`1ff1a8623c4edeec94ec29b0eff0c2357106d7cd5aa07a7cc94353971f692409` in
`reports/owner-taxonomy-publication-20261108/frozen.json`. Its completion ledger
records 6,945 published taxonomy corrections, 3,365 confirmed unchanged and 376
blocked. Attribution is owner-delegated AI taxonomy acceptance, without independent
human checks, answer verification or paper approvals. It does not authorize new
future batches. Original pending candidate reports remain historical inputs;
read the completion ledger and current live state before continuing. The scoped
operator run does not consume the normal browser maintenance allowance; ordinary
staff limits and all source/permission/publication protections still apply.

On 8 November 2026, after the final Batch 1632 reconciliation at commit
`75eea6a532d4a68d801a54e16e134906c1f44040`, the owner explicitly instructed
"merge it and publish it" for the 78,049 saved unique tagging candidates. The new
`owner-taxonomy-final-20261108` run excludes 9,925 matching source-bound live
completions and freezes 68,124 outstanding targets at SHA256
`2d9737104889f1f512412463ef403cb7abf0f130bc0ec507b438f855c40f5855`.
Publication is complete, including four disjoint metadata/context supplements and
a separate 24-target policy reconciliation within the same authorized question IDs.
Final source-bound outcomes: 58,197 published corrections, 19,594 confirmed unchanged,
258 blocked, zero stale; 4,334 bank questions have no saved review in this pass.
Both full-bank proof runs passed, preserving text/options/answers, provenance and
paper identities. These are owner-delegated AI taxonomy acceptances, not independent
human review or answer verification. Consult
`reports/owner-taxonomy-final-20261108/README.md` and its immutable evidence before
continuing; never replay old pending files or extend authority to future batches.

## Product and implementation

- Use approved subject/topic/subtopic classifications. Difficulty labels are retired.
- Use existing scoring eligibility and answer-status views. Never promote an AI
  inference to an official key or silently change a historical answer.
- Preserve assessment restrictions, answer reveal gates and account boundaries.
- Keep question/source IDs; presentation grouping is not a canonical merge.
- Popular means observed learner activity; Hot topics require dated reviewed picks.
  Use honest empty states instead of invented activity or predictions.
- Make schema changes with new numbered migrations in `api/migrations/`; never edit
  an applied migration. Rehearse migrations on a disposable dump clone.
- Build frontend artifacts locally and deploy with `scripts/deploy.sh`. Never build
  on Oracle. Avoid `ORDER BY random()`; use existing indexed selection helpers.
- Never rewrite shared `/etc/caddy/Caddyfile`. After Caddy, systemd or PostgreSQL
  changes, verify both study.hawayu.in and family.hawayu.in.

## Runbooks and layout

- `docs/ORACLE-PAPER-WORKBENCH-RUNBOOK.md`: maintenance, deployment, PDF workers,
  guarded paper publication and paired backup/recovery.
- `docs/AI-QUESTION-REVIEW-HANDOFF.md`: serial queue, subscriptions and resumable AI
  explanation checks/publication. This is the continuation entry point.
- `docs/DECISIONS.md`: historical reasons; current guidance above supersedes obsolete
  physical locations, counts and completed task instructions.
- `web/`: React/Vite/TypeScript; `api/`: FastAPI/psycopg; `scripts/`: operators.

Run web locally with `cd web && npm run dev`; its default API proxy is production.
Use a disposable database for tests, never production fixtures or synthetic reviews.
Secrets stay in private credential storage, never repository files or tool output.
