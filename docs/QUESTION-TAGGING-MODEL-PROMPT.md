# Copyable instructions for any tagging model

Read [QUESTION-TAGGING-RULES.md](QUESTION-TAGGING-RULES.md), policy
`study-tagging-v1`, before processing a packet. This handoff is a candidate
contract; it creates no bank changes or approvals.

> Classify each question by the knowledge or skill actually tested. Read the
> complete supplied source context, including directions, emphasis, options and
> images. Use only the supplied current active taxonomy IDs with valid parents.
> Keep the printed exam/paper/section identity separate from the learning path.
> Use exactly one proposed primary path when supported and only justified related
> paths. Never store browsing aliases such as gk-gs. Do not infer learning tags
> from department or paper title alone. Apply study-tagging-v1 to GK, GS, Current
> Affairs, Science, English and regional knowledge. For dated/changing facts,
> record the reference period and its evidence; preserve historical answers.
> If information is missing or policy choices remain ambiguous, return hold,
> alternatives and one precise owner question. Continue clear items. Do not
> invent tags, citations, source inspections, human reviews or answers. All
> results remain pending candidates. Do not change content or publish anything
> merely because this prompt asks for classification.

Return one record per supplied canonical/appearance target with these fields:

```json
{
  "policy_version": "study-tagging-v1",
  "canonical_id": "exact ID from packet",
  "appearance_id": "exact appearance from packet",
  "source_fingerprint": "unchanged fingerprint from packet",
  "action": "keep | retag | hold",
  "review_status": "pending",
  "current_primary": "copy the exact current path object or null",
  "proposed_primary": {
    "subject_id": "active stored subject ID",
    "topic_id": null,
    "subtopic_id": null
  },
  "proposed_related": [],
  "tested_skill": "What must the learner know or do?",
  "rationale": "Why this path follows from this particular question",
  "source_evidence": {
    "document_id": null,
    "sha256": null,
    "physical_page": null,
    "printed_question": null,
    "inspected": false,
    "note": "Describe only evidence actually examined"
  },
  "context_candidate": {
    "region": "",
    "language": "",
    "time_behavior": "unknown",
    "reference_period": "",
    "reference_basis": "unknown"
  },
  "context_reason": "Evidence supporting time/region/language, or missing information",
  "source_issues": [],
  "taxonomy_gap": null,
  "alternatives": [],
  "owner_question": null
}
```

The placeholders above describe fields, not valid production values. For `hold`,
`proposed_primary` can be null; preserve the actual current path in the report.
For `keep`, reproduce current primary and related paths exactly. For `retag`,
provide the complete intended related list and explain every addition/removal.
Do not remove a valid existing related path incidentally. A topic-null result
requires a specific broad-topic or missing-taxonomy explanation.

Every proposed related path needs its own rationale in the enclosing rationale
or a clearly labelled audit note. Missing source evidence stays null/false;
it must never be auto-filled from a default. A known reference year may be used
without inventing a day. Current Affairs without a supported reference period
remains held for clarification/context work.

This report is not an API request. A reviewed taxonomy proposal uses the existing
`kind=taxonomy`, `patch.classification` and `patch.relatedClassifications` contract,
source evidence and fresh baseline. Context goes through the organization workflow.
Do not add this report's extra fields to bank JSON or claim its `pending` state is
a production review record. Include packet totals and an exceptions list for the
owner. A later model must reread the policy, registry and current source version;
changing models does not create an independent human sign-off.

Before selecting targets, run `python3 scripts/audit-review-coverage.py --output
/tmp/study-review-coverage.json` from the app checkout. Exclude existing appearance
and canonical IDs and select one primary booklet per established paper. Follow
section 9 of QUESTION-TAGGING-RULES.md for intentional re-reviews, alternate-source
coverage, exact candidate baselines and bound reconciliation. Never claim a
pending tagging proposal solves or publishes the question's answer.
