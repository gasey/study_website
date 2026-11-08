"""Generate README.md for Batch 30."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
packet = json.load(open(out / "oracle-packet.json"))
summary = json.load(open(out / "summary.json"))
findings = json.load(open(out / "findings.json"))
validation = json.load(open(out / "validation.json"))
written = json.load(open(out / "pending-written-intake.json"))

lines = [
    "# Pending source-reviewed tagging — Batch 30: Radiotherapy Technologist April-2026 Paper-I (General English)",
    "",
    "Policy: `study-tagging-v1`. **60 existing MCQ questions reviewed: 40 retag proposals, 20 keep decisions, 0 tag holds. 4 unextracted conventional written tasks preserved as separate pending intake evidence. All 60 remain pending. Zero live changes, submissions or publications.**",
    "",
    "## Target Paper Identity & 100% Paper Completion Milestone",
    "",
    "- **Paper:** *Competitive Examination for Recruitment to the Post of Radiotherapy Technologist (Contract) under Health & Family Welfare Department, Government of Mizoram (April, 2026) — Paper-I (General English)* (`Old_Questions/Direct_NG_2024-2027/Radiotherapy Technologist Paper-I (English)..pdf`, `doc_a8943344d9cc369f5611b184`, `sha256: 903c76b0e3d02375f6b015cd1ba7207d54515a44c42260ec22c070ce5ff96111`).",
    "- **Coverage:** Complete 100% review of all 60 extracted Section-B MCQs (Q1–Q60 across physical PDF pages 3 to 7), achieving full paper completion.",
    "- **Refinements & Keep Decisions:** Rectified 40 coarse or misclassified items into active taxonomy subtopics: Parts of Speech (20 items), Antonyms (5 items), Synonyms (5 items), Vocabulary (5 items), and Subject-Verb Agreement (5 items). Verified 20 already-correct baseline topics (Sentence functions/types and Clause structures) as KEEP decisions.",
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
    "Direct visual inspection of all 7 rendered PNG page images (`paper-1-p1.png` to `paper-1-p7.png`) of `doc_a8943344d9cc369f5611b184`:",
    "- **Page 1 (`paper-1-p1.png`):** Inspected Paper cover and Section-A Conventional Type (40 Marks) Q1 (Essay writing, 10 marks: AI in Healthcare / Psychology / Health Tourism) and Q2 (Précis writing, 10 marks: Trees and selfless service).",
    "- **Page 2 (`paper-1-p2.png`):** Inspected Section-A Q3 (Official letter to Health Minister on PHC doctors, 10 marks) and Q4(a)–(e) (Reading comprehension on science and religion, 10 marks).",
    "- **Page 3 (`paper-1-p3.png`):** Inspected Section-B Multiple Choice Questions (60 Marks) header and Direction (Q1–10: Identify parts of speech of underlined words) Q1–Q9 (while, among, so, yet, Hello!, emaciated, more, after, a few).",
    "- **Page 4 (`paper-1-p4.png`):** Inspected Q10 (one another), Direction (Q11–20: Identify parts of speech as directed) Q11–Q20 (bravery, afterthought, Shakespeare of India, jury, rice, wisdom, seems, beautifully, each, himself), and Q21 (colossal antonym).",
    "- **Page 5 (`paper-1-p5.png`):** Inspected Q22–Q25 (Antonyms: luscious, indolent, denounced, abundant), Direction (Q26–30: Synonyms) Q26–Q30 (bold, fragile, gregarious, still, eccentric), and Direction (Q31–35: Vocabulary fill in the blanks) Q31–Q33 (stiffer, felicitated, saw).",
    "- **Page 6 (`paper-1-p6.png`):** Inspected Q34–Q35 (astrologer, reprimanded), Direction (Q36–40: Subject-Verb Agreement) Q36–Q40 (have, is, has, was, is), and Direction (Q41–46: Sentence kinds by function) Q41–Q46 (Declarative, Exclamatory, Imperative, Imperative, Interrogative, Declarative).",
    "- **Page 7 (`paper-1-p7.png`):** Inspected Q47–Q50 (Imperative, Command, Request, Imperative) and Direction (Q51–60: Sentence structure) Q51–Q60 (Complex, Compound, Compound, Simple, Simple, Simple, Complex, Compound-Complex, Complex, Simple).",
    "",
    "## Documented Source, Extraction & Option Defects",
    "",
    "1. **Missing Section-A Conventional Written Tasks (Pages 1–2):** 4 prompts totaling 40 marks (Essay 10m, Précis 10m, Official Letter 10m, Reading Comprehension 10m) preserved in `pending-written-intake.json`.",
    "2. **Underline Omissions in Database Text:** Stored text for Section-B Q1–Q10 omits the underline markings present in the physical booklet.",
    "3. **Printed Typos:** Q22 printed stem typo 'quests' for 'guests'; Q49 printed option (a) typo 'Pupose' for 'Purpose'."
])

(out / "README.md").write_text("\n".join(lines) + "\n")
print(f"Generated README.md ({len(lines)} lines).")
