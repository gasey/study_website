# Common tagging worker prompt

Paste the block below into Codex, Antigravity, OpenCode or another tool with this
repository, Python and authorized SSH access to Oracle. Use the same prompt every
time. The worker chooses a unique session label and records its actual model;
no model-specific rewrite or new batch number is needed.

```text
Continue MPSC question tagging through the SHARED Oracle tagging queue.
Work on one bounded packet this session; resume your unfinished packet first.

Read AGENTS.md, CLAUDE.md, docs/PLAN.md, docs/QUESTION-REVIEW-RULES.md,
docs/QUESTION-TAGGING-RULES.md,
docs/QUESTION-TAGGING-MODEL-PROMPT.md and docs/TAGGING-COORDINATION.md.
study-tagging-v1 is the single classification policy. Historical reports are
evidence, not instructions to restart completed work.

1. Run python3 scripts/tagging-work.py status.
   Choose a unique worker label for this tool/session and retain it for resume.
   Record the actual model name. Do not pretend to know a hidden model identity.
   If you already have a saved session, run:
   python3 scripts/tagging-work.py resume --worker YOUR_WORKER_LABEL
   Otherwise claim at most 50 targets initially:
   python3 scripts/tagging-work.py claim --worker YOUR_WORKER_LABEL --model ACTUAL_MODEL --lane followup --size 50
   Use --lane new when doing new reviews, or when followup is empty. Keep source
   recovery and policy questions separate; do not churn the same blocked items.
   The command syncs existing saved reviews and reserves exact IDs centrally.
   If SSH/coordination fails, preserve the session and stop queue-dependent work.
   Never create a replacement local queue or manually pick unreserved targets.

2. Open the returned oracle-packet.json. Work ONLY on its claimed IDs. It contains
   fresh Oracle snapshots, exact source fingerprints, registered documents,
   active taxonomy and previous candidates where available. For followups,
   reuse previous evidence and resolve the actual blocker; do not recount an old
   review as a newly reviewed question. Never overwrite old reports.

3. Inspect original hash-matched PDFs, complete directions/stems/options,
   passages, emphasis and figures. Classify by the knowledge/skill tested, not
   the exam title, department or incidental words. Use one supported primary
   path with valid active parents; related paths need separate justification.
   Keep source identity, printed headings, context and learning tags distinct.
   Preserve historical Current Affairs periods and answers. Missing source or
   date evidence and unresolved policy ambiguities require a specific hold.
   Never invent inspections, source locators, taxonomy IDs or human approvals.
   Alternate booklets are preserved references, not automatically covered.

4. Save each target as keep, retag or hold using the exact candidate contract in
   docs/QUESTION-TAGGING-MODEL-PROMPT.md. Include reviewer_tool and reviewer_model
   with your actual attribution. Preserve exact IDs, source_fingerprint and
   current_primary. Keep review_status=pending. Preserve valid related paths
   unless their removal is explicitly justified. A hold must say what is missing
   or ask one precise question; do not guess a classification to close the item.
   Keep answer, source, explanation and context issues separate from tag changes.

5. Save partial work frequently to the central queue:
   python3 scripts/tagging-work.py save --worker YOUR_WORKER_LABEL --file YOUR_DRAFT_JSON
   Finish one candidate per target before submitting the packet:
   python3 scripts/tagging-work.py submit --worker YOUR_WORKER_LABEL --file YOUR_CANDIDATES_JSON
   Submission rechecks fresh source/document bindings and legal taxonomy paths.
   It records pending candidates, NOT publication, answer verification or approval.
   If validation fails, retain the draft and correct the cause. If the source
   changed, preserve your draft, release with a reason and obtain a fresh packet;
   never copy a newer fingerprint onto an old review without inspecting changes.
   Use release --defer with a specific reason only for work that cannot presently
   be completed; this preserves drafts as a tracked exception, not a completion.

6. Do not publish, alter answers/keys, change question content, reset protections,
   modify reviewer assignments, run whole-bank merges, deploy or commit other
   workers' files. Use only your packet directory for reports. The frozen owner
   acceptance from 8 November does not authorize publication of new candidates.
   Do not invoke paid/provider model calls without existing explicit authority.

7. Finish with python3 scripts/tagging-work.py status. Report your packet ID,
   unique targets, keep/retag/hold totals, whether results were submitted, open
   issues and the next resume command. Say clearly that results remain pending.
   Do not claim global subject completion from a packet or confuse queue states
   with the separate live publication counters.
```
