# UDC and Prelims human review

Live workspace: https://study.hawayu.in/editorial

Owner-requested assignments, 2 November 2026:

| Person | Account email | Exam | Fixed source scope |
|---|---|---|---|
| Sangzel | sangzeldoto@gmail.com | UDC | 48 papers / 3,930 source appearances |
| Solomon | solomon.scorp@gmail.com | MCS Prelims | 30 papers / 3,001 source appearances |

Both reservations are pending because the emails were not registered when provisioned. Each friend creates their own account, then the owner opens **Assigned paper review → Manage reviewer assignments**, confirms the account identity and activates the reservation. Activation is deliberately separate from email matching: a reservation does not grant access to an account that later claims that email automatically. The owner can revoke access from the same page. No email message was sent, no password was created, and no admin/publisher/reviewer role was granted.

An active assignment grants answer-bearing source inspection for its exact registered paper IDs and lets the user submit ordinary correction proposals. It does not permit reading other reviewers' private proposals, approving changes, releasing holds, managing accounts or publishing. The active mock/game answer gate still applies. Authors cannot approve their own proposals; normal evidence/quorum/publication rules remain in force. Assignment checks do not grant XP or contribution credit.

## Friend workflow

1. Sign in at `/editorial`, choose the assigned exam, paper and question.
2. Open the original PDF. Check prompt, shared context, underlining, options, figures and printed numbering. Check the answer and teaching explanation separately; written tasks require full passage/subquestion and marking-guidance review.
3. Save **Checked** only after all four checklist items have been inspected, with a concrete evidence note. Otherwise use **Needs correction** or **Cannot verify**. This creates an attributed, append-only human inspection record; it does not promote a solution to official or verified status.
4. Choose **Propose a correction** for text, options, answer, explanation, source locator or classification edits. Review the diff and submit it. Follow the proposal in `/contribute`. The contribution process, not a checklist tick, changes the bank after publication.
5. If the source changes while editing, the save rejects the stale form. Preserve the note locally, reopen the current question and compare again. Historical checks remain visible as earlier checks and must not be interpreted as a current sign-off after later corrections.
6. Work paper by paper. Tell the owner which source was checked and list unresolved items. Question and appearance IDs are shared across modules where applicable: do not create a duplicate bank for each reviewer.

Existing ordinary contribution quotas remain in force. An assignment does not silently grant the 500/day administrative shortcut or the prior owner-only quota exemption. If the workflow reaches a limit, the owner should review the workload and use an explicitly designed audited policy rather than sharing accounts.

Shareable owner-held packs and live source indexes are in `reports/udc-prelims-human-review-20261102/`. These exports contain question/source pointers and flags, without recorded answers. They become stale; the live source is authoritative for a new correction.

## Protection against AI re-parsing

The current UDC/Prelims source list and content are frozen as an integrity baseline, not marked human-verified. The mandatory local protection policy is `scripts/editorial-protection-policy.json`; state is `../mpsc-question-bankv2/state/editorial-protection/udc-prelims.json`. It covers question/paper IDs and complete record values, referenced passage/figure/sitting metadata, and hashes of original PDFs and figure assets. The initial baseline covers 78 papers, 6,931 questions and 452 referenced assets. The remote collection membership is checked before sync.

Fourteen known canonical-bank writer tools now use a common locked, atomic write gate. A changed protected record is rejected and its comparison retained under `../mpsc-question-bankv2/state/parser-drafts/`. AI extraction can continue into candidate files. It cannot automatically update handed-off content through those tools. The same check runs before every bank sync mode, including dry-run/classification-only/alternate-bank sync, so a raw file write that bypasses a tool cannot silently reach students through the normal sync path. `--check` is also strict: a failed integrity check must be investigated, not treated as permission to reset the baseline.

Existing validated publication paths can advance protection only for their exact validated target IDs. The publisher checks manifest/source/bank versions, journals the exact protected transition before replacing the bank, and commits it after replacement. Prepared publication receipts and protection journals support recovery on either side of the write boundary. Unrelated/stale targets cannot be used to absorb parser changes into a new baseline.

The ordinary correction editor additionally sends an answer-free source-version token. UDC/Prelims create/revise requests require the token and reject changed source/canonical/tag versions. This closes the gap where an old form could otherwise create a new proposal against a source the reviewer never saw. Existing proposal revision/version and publication checks remain in force.

### Commands for operators

```bash
./scripts/sync-bank.sh --check
python3 scripts/editorial_protection.py check \
  --bank ../mpsc-question-bankv2/bank/mpsc_bank_v2.json --remote-scope
python3 scripts/editorial_protection.py stage \
  --bank ../mpsc-question-bankv2/bank/mpsc_bank_v2.json \
  --candidate /absolute/path/to/new-ai-candidate.json \
  --output /absolute/path/to/staging/comparison.json
```

A staging artifact is not an approval or a publication manifest. Inspect each proposed change in the existing correction workflow. If the candidate adds missing questions to an already assigned paper or changes paper/source identity, prepare a separate source-intake/identity review. There is no automatic rebaseline/force-sync switch. Newly registered papers require deliberate assignment/protection-scope expansion; the source list is not silently expanded while friends are reviewing it.

## Recovery and limits

- Back up the protection state along with the canonical bank and review receipts. Initial/current snapshots were mirrored privately to `/home/ubuntu/editorial-protection-20261102/` on the deployment host; this is a recovery copy, not an independently updated authority.
- Missing policy/state, mismatched asset hashes, changed source membership or unexpected record hashes fail closed. Restore the exact reviewed state or reconcile the precise pending publication; do not initialise from an already changed bank.
- For a publisher crash, use its existing receipt/batch replay path. Protection accepts only its exact journaled transition, not an arbitrary new bank. Check live publication readback before acknowledging.
- Do not edit production bank-owned SQL columns directly. The local bank is still the authority for question content. The assignment/check tables are server-owned workflow records, not part of bank sync.
- These are integrity controls for the supported workflow. They cannot prevent someone with filesystem/root access from deliberately modifying code, policy/state, or production SQL. They also do not establish factual correctness, complete archive coverage, or complete human sign-off.

## Verification

The release rehearsed migration 0063 against a production dump clone, then applied it normally. Backend tests use disposable PostgreSQL with synthetic accounts/sources. They cover pending and out-of-scope access, owner-only activation, absent-account rejection, revocation, stale proposal/check rejection, attribution and append-only history, no publishing authority, and no answer/provenance mutation from checklist saves. File tests cover stale imports, changed/deleted/renamed records, asset changes, missing state, draft retention, validated manifest publication and interruption recovery. Browser verification of the active workspace uses loopback-only synthetic responses; production verification covers the signed-out access boundary and API/site health. No friend's login or human source sign-off was fabricated.

## Account activation — 2 November follow-up

The owner explicitly requested applying both assignments with individual passwords or OAuth. Created the two previously absent accounts through the ordinary public registration endpoint, using different randomly generated word-based passwords, and activated their existing assignments through the owner-authorized activation service. Sangzel (`sangzeldoto@gmail.com`) now has active UDC access (48 papers); Solomon (`solomon.scorp@gmail.com`) has active combined-prelims access (30 papers). No password reset of an existing account, email verification claim, global review grant, or publishing grant was made. Google sign-in was not implemented in this follow-up.

Live password logins, assigned paper/question lists, denial of the other assignment, and denial of owner management/global bank administration all passed. All setup/test sessions were revoked after verification. Friends should use `/login?next=%2Feditorial` and change their starting passwords at `/account/security`; this is an instruction, not an enforced first-login password-change gate. Their source packs now reflect active accounts and contain no passwords. Private credentials are held outside the repository in an owner-only local file. No email invitation was sent and no human inspection/check was recorded by account setup.

## 3 November: Oracle publishing and new-paper preparation

The publishing worker now runs on Oracle; leaving this computer switched on is no longer needed for approved corrections to publish. Existing assignments remain unchanged: Sangzel reviews UDC and Solomon reviews Prelims, covering the same 78 protected papers. The bank is still awaiting their real inspection/sign-offs; this migration is infrastructure verification, not factual certification.

For an additional PDF, the owner uses `/paper-workbench`, then assigns its exact draft if needed. That assignment is separate from existing frozen source access. OCR/extraction cannot overwrite manually prepared questions. Saving invalidates an earlier approval, and an independent person who has not edited the draft must inspect it. Only the owner can queue publication. Original keys, unofficial human solutions and missing answers remain distinct. See `ORACLE-PAPER-WORKBENCH-RUNBOOK.md` for the complete procedure and recovery safeguards.

## 3 November: explicit Sangzel administrator promotion

The website owner explicitly requested full administrator privileges for
sangzeldoto@gmail.com in the implementation chat. Applied global owner grant 4
through an operator-assisted, audited account-data transaction. The grant records
operator:codex as the actor and the explicit request as its reason; no browser
session or human reviewer identity was impersonated. Readback confirms the active
grant and audit event. Sangzel can now open /admin/bank and the comprehensive owner
sections. This supersedes the earlier statements that Sangzel has assignment-only
access; Solomon's access is unchanged.

Sangzel's active UDC assignment still contains 48 papers. No source data,
inspection checks, approvals or publisher protection rules changed. Production
staff MFA is required; this account has not enabled an authenticator, so Sangzel
must set it up at /account/security before privileged changes. Existing password
and sessions were not changed. Study API and family site both returned HTTP 200.

## General review workspace — 3 November follow-up

The assigned-paper interface now supports any registered paper-based module and
explicit sets of registered papers from either bank. Existing Sangzel and Solomon
memberships are preserved. New papers require an owner's explicit, versioned scope
addition. The overview separates saved history, current checks, flagged issues and
source versions requiring recheck. Review complete requires every question to have
a current Checked outcome; checklist completion never publishes a correction.

The context panel shows assigned reviewer handles and non-private correction
status counts, plus links to the current user's proposals. Shared questions retain
their original IDs. Other authors' private draft details remain inaccessible.
See EDITORIAL-WORKSPACE.md for scope, progress and other review-queue boundaries.
