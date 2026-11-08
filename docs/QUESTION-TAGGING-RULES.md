# Question tagging and bank repair rules

Policy `study-tagging-v1`, 7 November 2026. This is the single current tagging
policy for study.hawayu.in, its question bank and every model preparing repairs.
The owner requested removal of conflicting old instructions, not deletion of
existing question tags. Historical records remain evidence, never instructions
to rerun old merges. Operational safeguards in `../CLAUDE.md` still apply.

## Read these in order

1. This policy: how to decide a tag and resolve uncertainty.
2. The current active `review_taxonomy` registry on Oracle: which IDs are legal.
   Its bank definition is
   `/srv/study/workshop/mpsc-question-bankv2/taxonomies/question-bank-v2.json`.
   Refresh and compare them before a repair run; a local recovery copy may lag.
3. [Model handoff](QUESTION-TAGGING-MODEL-PROMPT.md): required candidate records.
4. [Publication runbook](ORACLE-PAPER-WORKBENCH-RUNBOOK.md): how reviewed changes
   reach the bank and website. A taxonomy decision is not an answer decision.

The routing examples in `question-tagging-policy.json` are a machine-readable
companion to this policy. They contain real stored IDs, not display aliases.
Run `python3 scripts/check-tagging-policy.py --registry REPORT.json` against a
fresh registry export with a top-level `taxonomy` array. Validation establishes
legal paths only; a reviewer must still decide whether each question fits.

## 1. Keep these dimensions separate

| Dimension | Record | Never substitute |
| --- | --- | --- |
| Source | Exact paper, recruitment, year, booklet, appearance ID, printed question number and physical PDF page | Filename/upload date for verified exam identity |
| Printed paper/section | The original heading: General English, General Knowledge, General Studies I, etc. | A learning tag for the printed title |
| Primary learning path | One subject → topic → optional subtopic, based on the task being tested | Recruiting department, exam name or incidental words |
| Related learning paths | Additional knowledge explicitly tested; normally none | Alternative guesses, keyword matches or duplicate GK/GS aliases |
| Context | Region, language, time behaviour and reference period with evidence | Region/language as the subject merely because it appears in the question |
| Scheme and membership | Exact applicable scheme revision and reviewed module sources | One current scheme applied to every legacy paper |

English questions from LDC, UDC, Assistant and technical recruitments use the
same English taxonomy. Their original appearances keep them in the appropriate
exam views. A combined Assistant/UDC source may serve both modules; unrelated
separate sittings do not automatically acquire both memberships. Counts across
modules can overlap. Preserve canonical IDs, appearances and booklet order.

## 2. Decide the learning path from the task

Read the complete stem, instructions, ordered options, underlining, passage and
figures. Ask: **what must the learner know or do to answer this question?**

- Antonyms in a Mines paper: English → Vocabulary → Antonyms.
- A water-image puzzle in a Junior Engineer paper: Reasoning and Aptitude.
  The active registry currently has no suitable non-verbal topic. Keep the
  topic null with an explicit taxonomy-gap note; do not choose Circuits or
  Verbal Reasoning to make the record appear complete.
- A clause identified within an underlined phrase: English → Grammar.
  There is currently no active clause subtopic. Use a null subtopic; a phrase
  such as `english/grammar/clauses` is not a valid stored ID today.
- A passage about elections asking for a synonym: English → Vocabulary.
  Elections are passage context, not a second Polity/Current Affairs tag.
- A stable physics principle in a GK paper: Science → the supported topic.
  A specialist engineering design question belongs to its engineering subject.
- A written GS answer testing constitutional knowledge: the supported Polity
  path with its written type preserved. An English essay testing composition
  uses English → Writing → Essay writing. Read the task and marking context;
  the words “write an essay” alone cannot resolve every multidisciplinary case.

Use the narrowest **supported, active** path. A missing topic is a backlog item;
a missing subtopic is acceptable when none exists or none is justified.
Subject-only classification is intentional only when the task is genuinely
broad or the registry lacks a suitable topic, with a reason recorded. The app's
`broad_subject_intentional` resolution is available for such checked cases.
Do not mark every incomplete tag intentional to improve a completeness score.

## 3. GK and GS: one discovery family, exact stored IDs

GK and GS describe exam structures as well as learning areas. Those uses must
not be conflated. UDC/Assistant/LDC learning views show General Knowledge;
cross-exam discovery groups compatible paths under GK/GS. Original headings
are taken from the inspected source and its applicable edition.

Current preferred stored routes are:

| Learning topic | Stored subject | Stored topic |
| --- | --- | --- |
| Current Affairs | `general-studies` | `general-studies/current-affairs` |
| Indian History | `general-studies` | `general-studies/indian-history` |
| World History | `general-studies` | `general-studies/world-history` |
| Geography | `general-studies` | `general-studies/geography` |
| Indian Polity | `general-studies` | `general-studies/indian-polity` |
| Indian Economy | `general-studies` | `general-studies/indian-economy` |
| Environment | `general-studies` | `general-studies/environment` |
| Mizoram knowledge | `general-studies` | `general-studies/mizoram` |
| Art and Culture | `general-knowledge` | `general-knowledge/art-and-culture` |
| Sports | `general-knowledge` | `general-knowledge/sports` |
| Science in the news | `general-knowledge` | `general-knowledge/science-in-the-news` |
| Static GK, only when no more specific route fits | `general-knowledge` | `general-knowledge/static-gk` |

These paths were checked against the live registry on 7 November. An alias
entry in `api/app/data/learning-topic-aliases.json` does not establish that its
source ID is an active taxonomy node. For example,
`general-knowledge/current-affairs` is a compatibility mapping but was absent
from the active registry at this check. Never manufacture it from a paper's GK
heading. The valid Current Affairs route above still works inside UDC GK.

Never store `gk-gs`, `gk-gs:current-affairs` or `gk-gs:science` as a
classification. They are browsing projections. Do not create two stored copies
of one learning topic just to make it appear under both GK and GS. If the
registry later contains equivalent active variants, preserve a correct existing
path; new candidates follow the shared picker's resolver and the current policy
mapping. Any planned migration needs its own reviewed mapping and receipts.

Static GK is not a substitute for Geography, History, Polity, Culture or Sports.
Use it for a stable general fact that has no fitting specific active route and
explain that choice. Unknown facts remain unresolved. Existing “Other/General”
tags are not deleted by this policy.

## 4. Current Affairs and historical reference periods

Use Current Affairs when answering requires a dated event, appointment, award,
result, ranking, statistic or changing officeholder **as understood at the
question's reference period**. “Current” is relative to the original question,
not the date a model reviews it. An old current-affairs question remains useful
historical current affairs; never replace its key with today's fact.

Use a stable subject route when the actual test is a concept or established
historical fact. A year, politician's name or word such as “recent” in a quoted
passage is not sufficient by itself. A stable constitutional rule stays Polity;
a specific appointment normally uses Current Affairs; a historical reign stays
History. A question about a changing constitutional rule can need Polity plus
time context without becoming an appointment/news question.

| Task | Primary route | Additional context/link |
| --- | --- | --- |
| Winner of a named recent tournament edition | Current Affairs | Exact edition/date; Sports related path only when substantively useful and justified |
| Stable rule of a sport | Sports | Static context; no automatic Current Affairs link |
| Latest named space mission/launch | Current Affairs | Dated-event; Science in the news may be a justified related path |
| Scientific concept explicitly asked through a news development | Science in the news, or the precise Science topic if that is the actual test | Explain the primary choice; Current Affairs related path only if dated knowledge is also required |
| Ordinary physics or chemistry principle | Science topic | Static; news setting alone is not a second tag |
| Mizoram officeholder at a specified time | Current Affairs | Region Mizoram and reference period; not Mizo language |
| Mizoram-specific historical/cultural knowledge | Mizoram, or the more specific supported knowledge route | Explain the main learning objective; region Mizoram |
| Mizo grammar or literature | Mizo → Grammar/Literature | Language and region remain separate |

If two primary routes remain equally plausible after source inspection, write
the alternatives and one precise question for the owner. Continue other clear
items. A model's confidence or another model's agreement cannot settle a policy
ambiguity. Record the owner's resolution with a new policy version/example.

Use the existing context fields, with these exact values:

- `time_behavior`: `static`, `dated-event`, `changes-over-time`, or `unknown`.
- `reference_period`: the printed period, or verified exam-date context when
  the question says “present/current”. Never invent a day from a year.
- `reference_basis`: `printed`, `exam-date`, `reviewed-source`, or `unknown`.
- `region`: `mizoram`, `india`, `international`, `other`, or empty when unknown;
  specify `region_detail` where useful. This is the scope tested, not the exam venue.
- `language`: `en`, `lus`, `hi`, `other`, or empty when unknown; use source evidence.
- `source_url`, `checked_on`, `review_due`: inspected evidence and dates only.
  Reviewing an item today does not change its historical reference period.

For Current Affairs candidates, require a known reference period and basis
before treating the tagging/context repair as complete. If missing, keep a
pending candidate and ask for the source date/context. Other changing facts also
need their relevant period even when their primary tag is Law, Economy or Science.
Never invent a final key, source URL, precise date or inspection claim.

Context is saved through the existing source/version-bound organization workflow;
it is not an extra field to slip into a taxonomy proposal. The current context
table holds one record per canonical question, tied to one appearance. When
repeat appearances imply different periods, document that conflict and escalate;
do not overwrite one period with another or claim every appearance is covered.
New current-fact explanations/connections use the separate current-affairs workflow.

### Owner-resolved regional-culture example — 7 November 2026

For Sub-Inspector of Statistics January 2026 Paper II Q95, “Who composed the song
‘Hmanah kaisar lal lian’?”, the owner explicitly chose **GS → Mizoram culture**
over Mizo → Literature in this chat. Use `general-studies/mizoram` for this exact
composer-attribution candidate, retaining the English task language, Mizo song
context and original exam identity. This is an attributed routing decision, not
a source/key sign-off. The separate Dar Hla repertory question remains unresolved.
Evidence: [exact owner resolution](../reports/tagging-batch10-20261107/owner-resolution.json).

## 5. Related tags, ambiguity and source defects

Start with one primary path and zero related paths. Add a related path only if
you can explain the additional tested knowledge in a sentence. The backend
allows at most 12; that is a ceiling, not a target. Reject duplicate paths and
primary/related copies of the same GK/GS discovery topic. Alternative model
claims in `classifications` are not related tags; approved related paths belong
in `relatedClassifications` through their ordinary publication workflow.

If source content is incomplete, inspect the original. Missing underlining,
figures, options or instructions can change the task. Record separate source,
answer and taxonomy findings; a correct tag never clears a source defect or
certifies an answer. A source issue does not prevent preparing an independently
clear taxonomy candidate, but it does prevent pretending the whole item is done.
For Q44, English → Grammar is already appropriate; restoring its underline,
three printed options and verifying its answer are separate repairs.

Use `hold` in a candidate report to mean “do not submit this proposed tag yet”.
It is not a command to create or release a scoring hold in production. Preserve
the current live tag while an alternative is unresolved. If no active path fits,
save the supported broader path or null candidate, the taxonomy gap and the
owner question. New taxonomy nodes require a separate versioned registry change.

## 6. Repair sequence and definition of done

1. Export a bounded current Oracle packet with exact canonical/appearance IDs,
   source fingerprint, current primary/related paths, instructions, options and
   necessary source evidence. Do not use the local recovery bank as current data.
2. Inspect each target. Keep source defects, answer problems, context gaps and
   tag decisions in separate fields. Generate a maximum of 100 pending candidates
   per packet; this is planning size, not permission to publish 100 at once.
3. For each item choose keep, retag or hold, with a specific content rationale.
   Use real active parent/child IDs. All model candidates remain pending.
4. Review each proposed change against its source. Batch only items supporting
   the same intended correction; the admin tag preview accepts at most 20.
   Owner decisions and independent-review decisions retain their actual attribution.
5. Submit reviewed taxonomy changes through the current admin/guarded Oracle
   publisher. Save context separately through its existing endpoint/UI. Recheck
   source versions. Do not rerun old whole-bank classification merges, edit SQL
   content, reset protection baselines, or bypass frozen assignments.
6. Wait for applied publication and read back the exact primary/related paths.
   Verify All English or the applicable learning shelf and the original exam
   view. “Saved”, “Publishing”, a checklist and registry validation are not done.
7. Report unique targets, reviewed/changed/held counts, exact receipts, source
   issues still open, and context/scheme work remaining. Avoid double-counting
   overlapping related tags or exam membership.

The first pilot should cover a combined Assistant/UDC source, a separate legacy
clerical source, Gazetted GS and English/written tasks. Check Current Affairs,
static knowledge, science/news, language versus region, and specialist content.
General source schemes must be verified against their own recruitment notices;
never infer scheme applicability from a learning tag.

## 7. Current evidence and limits

[Live audit](../reports/tagging-policy-20261107/live-audit.json), 7 November:
181 active taxonomy nodes; 82,249 live questions with an approved primary subject;
58,370 approved subject-only rows, including 4,557 English rows. These are
structural counts, not proof of semantic accuracy. There are zero saved records
in the new question-context, scheme-revision, paper-profile and broad-tag-resolution
tables. Existing collections, paper identities and older current-affairs systems
are separate and are not counted by those zeros.

ENERVATE is still classified Geology; the water-image item is still Electrical
Engineering → Circuits. They are concrete cleanup candidates, not corrections
published by this policy update. The previous 1,000-question pass checked stored
metadata and options; it did not visually verify 1,000 PDFs or solve 1,000 answers.

This release cleans up instructions and validates the policy's example paths.
It does not recertify the corpus. API validation enforces legal paths and workflow
guards; semantic routing and full time-context coverage still require review.

## Supersession

This document replaces tagging decisions and operational directions in older
classification handoffs, the legacy scalar-tag chunk instructions and historical
local-publisher guidance. Archived originals retain their dated evidence. Schema
definitions, active registry IDs, source protections and immutable publication
receipts remain authoritative for their respective roles. Never interpret this
policy as permission to change those safeguards or the original paper identities.

## 9. One booklet and one saved review target

For simultaneous work by different tools/models, use the central packet claims
in [TAGGING-COORDINATION.md](TAGGING-COORDINATION.md) and the common
[worker prompt](TAGGING-WORKER-PROMPT.md). The claim command incorporates the
coverage audit and fresh Oracle export; reserve IDs before inspecting new targets.
Local audit exclusions alone cannot prevent two simultaneous selections. This is
workflow coordination under the same classification policy, not a new tagging
rule or publication authorization.

Before choosing any new tagging packet, run:

```bash
python3 scripts/audit-review-coverage.py --output /tmp/study-review-coverage.json
```

Exclude the output's `already_reviewed_appearance_ids` and
`already_reviewed_canonical_ids` from new selections, including keep decisions.
An intentional re-review must name the earlier candidate and explain why it is
being superseded; it does not increase unique reviewed coverage. Reuse the saved
source inspection rather than drafting a second proposal for the same target.

For an established exam/year/paper with A/B/C/D or 1/2 booklet permutations, select
one primary booklet (normally A or 1; prefer a complete registered copy). Keep
alternate PDFs and exact printed-number/key mappings as source references. A
booklet label or similar filename is not proof that all questions, passages,
figures and keys are identical. Check for variant-only content before recording
another booklet as covered. Never transfer an option letter between booklets.

Every candidate's `current_primary` and `source_fingerprint` must match its own
saved Oracle snapshot, then be checked against fresh Oracle state before any
submission. A generic GK placeholder copied from an old local bank is not a
current baseline. `audit-review-coverage.py` quarantines mismatched candidate
metadata from its consolidated selection; this is a metadata check, not a new
source inspection. Preserve original reports. Reconciliations must bind the exact
proposal signatures; changed proposals reopen the conflict. Prepared tagging work
is neither answer solving nor proof of publication.
