"""Generate README.md for Batch 39."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
packet = json.load(open(out / "oracle-packet.json"))
summary = json.load(open(out / "summary.json"))
findings = json.load(open(out / "findings.json"))
validation = json.load(open(out / "validation.json"))

lines = [
    "# Pending source-reviewed tagging — Batch 39: Circle Education Officer 2025 General English (66 MCQs)",
    "",
    "Policy: `study-tagging-v1`. **66 existing MCQ questions reviewed: 64 retag proposals, 2 keep decisions, 0 tag holds. All 66 remain pending. Zero live changes, submissions or publications.**",
    "",
    "## Target Paper Identity & 100% Paper Completion Milestone",
    "",
    "- **Target Paper:** *Competitive Examination for Recruitment to the Post of Circle Education Officer under School Education Department, Government of Mizoram (November, 2025) — General English* (`Old_Questions/Direct_2025-2027/CEO General English - 2025..pdf`, `doc_db5ba5b3fe26ca319535f622`, `sha256: a3b617a9b67098ab26fcb4798a8d0d931136c363c524da23a789a27d602b6b92`).",
    "- **Coverage:** Complete 100% review of all 66 extracted MCQs (Q1–Q66 across physical PDF pages 3 to 9), achieving full paper completion.",
    "- **Untagged Baseline Rectification:** In the database, 64 of 66 questions had `subject=english` with `topic=null, subtopic=null` or coarse tags. Rectified 100% of targets to standard General English grammar and vocabulary subtopics: Parts of Speech (6 items), Prepositions (9 items), General Grammar / Conjunctions / Transformations (10 items), Tenses & Verb Forms (15 items), General Vocabulary (2 items), One-Word Substitution (6 items), Idioms and Phrases (4 items), Antonyms (4 items), Reported Speech (5 items), and Synonyms (5 items).",
    "- **Preserved Conventional Intake:** Preserved 3 unextracted Part-A conventional tasks totaling 34 marks from Pages 1 and 2 in `pending-written-intake.json` (Précis Writing 14 marks, Formal Application Letter 10 marks, Reading Comprehension 10 marks).",
    f"- **Fresh Oracle read-only export:** `{packet['exported_at']}`. Readback validation (`{validation['validated_at']}`) confirmed 100% source fingerprint consistency, zero live mutations, and 100% compliance with active taxonomy nodes.",
    "",
    "## Before / after table",
    "",
    "| # | Source context | Tested skill | Before | Proposed after | Decision & rationale |",
    "| :---: | :--- | :--- | :--- | :--- | :--- |"
]

for idx, f in enumerate(findings, 1):
    ctx = f"{f['printed_question']} (p. {f['physical_page']})"
    lines.append(
        f"| {idx} | {ctx} | {f['tested_skill']} | `{f['current_path']}` | `{f['proposed_path']}` | **{f['action']}** — {f['rationale']} |"
    )

lines.extend([
    "",
    "## Totals & Summary Breakdown",
    "",
    f"- **Total existing questions reviewed:** {summary['targets']}",
    f"- **Retag candidates proposed:** {summary['actions'].get('retag', 0)}",
    f"- **Keep decisions:** {summary['actions'].get('keep', 0)}",
    f"- **Holds:** {summary['actions'].get('hold', 0)}",
    f"- **Unextracted written items preserved:** {summary['unextracted_items_preserved']}",
    "- **Live database writes:** 0 (strictly read-only)",
    "",
    "### Breakdown by Proposed Taxonomy Path",
    ""
])

for path, count in sorted(summary["breakdown"].items()):
    lines.append(f"- `{path}`: {count} questions")

lines.extend([
    "",
    "## Physical Element Inspection Evidence",
    "",
    "Direct visual inspection of all 9 rendered PNG page images (`paper-1-p1.png` to `paper-1-p9.png`) of `doc_db5ba5b3fe26ca319535f622`:",
    "- **Page 1 (`paper-1-p1.png`):** Inspected Paper cover and Part-A conventional tasks: Q1 Précis of reading passage (14 marks) and Q2 Formal application for Lecturer in Social Science (10 marks).",
    "- **Page 2 (`paper-1-p2.png`):** Inspected Q3 Reading Comprehension passage on Mrs. Drover's shut-up house with sub-questions (i) to (v) (10 marks).",
    "- **Page 3 (`paper-1-p3.png`):** Inspected Part-B OMR section header (66 Marks) and Q1–Q11: Q1–Q5 (Parts of speech of underlined words: 'happiness' [noun], 'must' [verb], 'almost' [adverb], 'among' [preposition], 'for' [conjunction]), Q6–Q11 (Prepositions / Conjunctions: Q6 'beside', Q7 'in March', Q8 'in a month', Q9 'since we last spoke', Q10 'but', Q11 'or').",
    "- **Page 4 (`paper-1-p4.png`):** Inspected Q12–Q23: Q12–Q15 (Prepositions: Q12 'prefer coffee to tea', Q13 'excited about', Q14 'insisted on', Q15 'recovering from'), Q16–Q23 (Tenses / Verb forms: Q16 'was shaking / fell', Q17 'has been working', Q18 'rises', Q19 'remembered', Q20 'Who took / has taken', Q21 'will be running', Q22 'wants', Q23 'received').",
    "- **Page 5 (`paper-1-p5.png`):** Inspected Q24–Q33: Q24–Q25 (Tenses: Q24 'was examining', Q25 'landed'), Q26–Q27 (Vocabulary: Q26 'eminent', Q27 'cite'), Q28–Q33 (One-Word Substitution: Q28 'mercenary', Q29 'philanderer', Q30 'polygyny', Q31 'astronomer', Q32 'anatomy', Q33 'pessimist').",
    "- **Page 6 (`paper-1-p6.png`):** Inspected Q34–Q43: Q34–Q37 (Idioms: Q34 'To bury the hatchet', Q35 'A fair weather friend', Q36 'To throw dust in one's eyes', Q37 'A wild goose chase'), Q38–Q41 (Antonyms: Q38 'admire', Q39 'contrary', Q40 'repulsive', Q41 'demolish'), Q42–Q43 (Tense transformations: Q42 'Future Perfect Continuous', Q43 'Past Continuous').",
    "- **Page 7 (`paper-1-p7.png`):** Inspected Q44–Q51: Q44–Q46 (Tense transformations: Q44 'Present Indefinite', Q45 'Past Perfect', Q46 'Future Indefinite'), Q47–Q51 (Reported speech direct/indirect narration: Q47 'raining since morning', Q48 'soldiers were marching', Q49 'did not enjoy the concert', Q50 'Why are you sketching', Q51 'saw a rabbit here').",
    "- **Page 8 (`paper-1-p8.png`):** Inspected Q52–Q61: Q52–Q56 (Connectors / Prepositions: Q52 'whom', Q53 'although', Q54 'since', Q55 'whether', Q56 'despite'), Q57–Q61 (Synonyms: Q57 'eloquence', Q58 'feeble', Q59 'incongruous', Q60 'nonchalant', Q61 'despise').",
    "- **Page 9 (`paper-1-p9.png`):** Inspected Q62–Q66 (Sentence transformations: Q62 'Everybody is present' -> negative, Q63 'No one can deny' -> assertive, Q64 'It was a lovely day' -> exclamatory, Q65 'It is useless to cry over spilt milk' -> interrogative, Q66 'Isn't the building red in colour?' -> negative statement).",
    "",
    "## Documented Source, Extraction & Option Defects",
    "",
    "1. **Unextracted Part-A Conventional Tasks:** Pages 1 and 2 contain 3 conventional written tasks (Précis 14 marks, Formal Application 10 marks, Reading Comprehension 10 marks) totaling 34 marks, which were not ingested into the MCQ database. Preserved in `pending-written-intake.json`.",
    "2. **100% Extracted MCQ Fidelity:** All 66 MCQs printed in Part-B (Pages 3 to 9) were present and numbered consecutively in the database without sequence gaps."
])

(out / "README.md").write_text("\n".join(lines) + "\n")
print(f"Generated README.md ({len(lines)} lines).")
