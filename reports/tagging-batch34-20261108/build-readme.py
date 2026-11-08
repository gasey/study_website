"""Generate README.md for Batch 34."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
packet = json.load(open(out / "oracle-packet.json"))
summary = json.load(open(out / "summary.json"))
findings = json.load(open(out / "findings.json"))
validation = json.load(open(out / "validation.json"))
written = json.load(open(out / "pending-written-intake.json"))

lines = [
    "# Pending source-reviewed tagging — Batch 34: Stenographer Grade-II (Contract) 2025 General English",
    "",
    "Policy: `study-tagging-v1`. **40 existing MCQ questions reviewed: 40 retag proposals, 0 keep decisions, 0 tag holds. 3 unextracted conventional written tasks preserved as separate pending intake evidence. All 40 remain pending. Zero live changes, submissions or publications.**",
    "",
    "## Target Paper Identity & 100% Paper Completion Milestone",
    "",
    "- **Target Paper:** *Competitive Examination for the Post of Stenographer Grade-II (Contract) under Mizoram Public Service Commission (May-2025) — Paper-I General English* (`Old_Questions/Direct_NG_2024-2027/Stenographer Grade-II (Contract) under MPSC - Paper-I (General English)..pdf`, `doc_5f0d589624f2eb0f9031863f`, `sha256: aa21fba8e0cae4d2ba59d2a0a32f23d67399eabcf54c885896eb329479f29699`).",
    "- **Coverage:** Complete 100% review of all 40 extracted Part-B MCQs (Q1–Q40 across physical PDF pages 3 to 6), achieving full paper completion.",
    "- **Untagged Baseline Rectification:** In the database, all 40 questions were completely untagged (`subject=null, topic=null`). Proposed active English taxonomy paths for 100% of targets: Parts of Speech (5 items), Prepositions (10 items), Tenses & Subjunctive (5 items), Idioms & Phrases (5 items), Active & Passive Voice (5 items), and One-Word Substitution (10 items).",
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
    "Direct visual inspection of all 6 rendered PNG page images (`paper-1-p1.png` to `paper-1-p6.png`) of `doc_5f0d589624f2eb0f9031863f`:",
    "- **Page 1 (`paper-1-p1.png`):** Inspected Paper cover and Part-A (Conventional Type, 60 Marks): Q1 Essay writing (20 marks: Communication skills in office work / Workplace ethics / Digital India) and Q2 Reading Comprehension passage on talent versus hard work (30 marks total across questions a–l).",
    "- **Page 2 (`paper-1-p2.png`):** Inspected Part-A Q2 continued questions (e–l: Thomas Edison perseverance, innate, surpassed, failure, rigid) and Q3 Précis writing (10 marks: Academic degrees vs common sense).",
    "- **Page 3 (`paper-1-p3.png`):** Inspected Part-B Multiple Choice Questions (40 Marks): Direction (Q1–5: Identify part of speech of underlined words) Q1–Q5 ('fast' as adverb, 'hard' as adjective, 'run' as noun, 'yourself' as pronoun, 'brave' as noun/substantive adjective) and Direction (Q6–15: Fill in with prepositions) Q6–Q11 ('on the recommendation of', 'versed in', 'abstained from', 'for lack of', 'inspired by', 'at 6:00 a.m.').",
    "- **Page 4 (`paper-1-p4.png`):** Inspected Q12–Q15 ('walk to the office', 'at work', 'in the classroom', 'how to play the piano'), Direction (Q16–20: Choose the correct tense of verbs) Q16–Q20 ('had finished', 'had left', 'scold', 'had', 'were'), and Direction (Q21–25: Meaning of idiom) Q21–Q22 ('Burning the midnight oil', 'Cutting corners').",
    "- **Page 5 (`paper-1-p5.png`):** Inspected Q23–Q25 ('Throw in the towel', 'A wild goose chase', 'Play devil's advocate') and Direction (Q26–30: Passive/Active voice) Q26–Q30 (modal passive 'should have been informed', active 'had served dinner', active 'are installing', active 'should have submitted', passive 'have been being given').",
    "- **Page 6 (`paper-1-p6.png`):** Inspected Direction (Q31–40: One-word substitution) Q31–Q40 (Claustrophobia, Cartographer, Elegy, Omnivore, Noctambulist, Autism, Lactose intolerance, Hypsophobia, Zealotry, Workaholic).",
    "",
    "## Documented Source, Extraction & Option Defects",
    "",
    "1. **Missing Part-A Conventional Written Tasks (Pages 1–2):** 3 prompts totaling 60 marks (Essay 20m, Reading Comprehension 30m, Précis 10m) preserved in `pending-written-intake.json`.",
    "2. **Completely Untagged Ingestion Baseline:** All 40 MCQs in Part-B had `subject=null, topic=null` in the production database, leaving them unclassified until this review.",
    "3. **Printed Booklet Typo:** Page 6 Q36 prints 'disabitity' instead of 'disability'."
])

(out / "README.md").write_text("\n".join(lines) + "\n")
print(f"Generated README.md ({len(lines)} lines).")
