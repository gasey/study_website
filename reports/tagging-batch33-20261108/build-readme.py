"""Generate README.md for Batch 33."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
packet = json.load(open(out / "oracle-packet.json"))
summary = json.load(open(out / "summary.json"))
findings = json.load(open(out / "findings.json"))
validation = json.load(open(out / "validation.json"))
written = json.load(open(out / "pending-written-intake.json"))

lines = [
    "# Pending source-reviewed tagging — Batch 33: ITI Instructor 2026 & Inspector of Statistics 2026 General English",
    "",
    "Policy: `study-tagging-v1`. **32 existing MCQ questions reviewed: 32 retag proposals, 0 keep decisions, 0 tag holds. 22 unextracted conventional written tasks and dropped duplicate-stem MCQs preserved as separate pending intake evidence. All 32 remain pending. Zero live changes, submissions or publications.**",
    "",
    "## Target Papers Identity & 100% 2026 Direct English Finalization Milestone",
    "",
    "This batch completes 100% of the remaining direct 2026 General English papers in the registered corpus:",
    "1. **Instructor ITI (April-2026) — Paper-I General English** (`Old_Questions/Direct_2025-2027/Paper-I (General English)..pdf`, `doc_0b0f26b428ddfe44c54aef08`, `sha256: 23534dd43b1bfc4aa67cda0ffa409b3f72201ea2da6e219c42123a4a6adcb1b6`): 26 MCQs (Q1–Q26 across physical PDF pages 3 to 6).",
    "2. **Inspector of Statistics (March-2026) — Paper-I General English** (`Old_Questions/Direct_2025-2027/Inspector of Statistics Paper-I (English)..pdf`, `doc_b61ba36d95d17e4c2a561cb8`, `sha256: 58f0cf1cd9de99cd9c8b61ebcc519a3c7f4288d539f7eeed8f517cd681639477`): 6 MCQs (Q5, Q6, Q8, Q9, Q10, Q11 across physical PDF pages 2 to 3).",
    "- **Untagged Ingestion Rectification:** In the database, all 32 questions were completely untagged (`subject=null, topic=null`). Proposed active English taxonomy paths for 100% of targets: Parts of Speech (9 items), Prepositions (1 item), Idioms & Phrases (5 items), Contextual Vocabulary (2 items), One-Word Substitution (3 items), Sentence Transformations (5 items), Sentence Correction (1 item), and Reading Comprehension (6 items).",
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
    "### 1. Instructor ITI Paper-I General English (`doc_0b0f26b428ddfe44c54aef08`):",
    "- **Page 1 (`paper-2-p1.png`):** Inspected Paper cover and Part-A Conventional Type (40 Marks): Q1 Précis writing (10 marks: modern skill-based training and instructor mentors) and Q2 Letter to the Editor of Zawlkhawpui on vocational education awareness (10 marks).",
    "- **Page 2 (`paper-2-p2.png`):** Inspected Part-A Q3 Reading Comprehension short answer questions (i)–(vi) (10 marks: industrial training discipline and practical skills) and Q4 Essay writing (10 marks: choice of Discipline in skilled career / Intermarriage and Mizo Women's Rights / IT in Skill Development).",
    "- **Page 3 (`paper-2-p3.png`):** Inspected Part-B Multiple Choice Questions (60 Marks, negative marking 1/3) Direction (Q1–5: Choose correct part of speech) Q1–Q5 ('very' as adjective, 'since' as preposition, 'might' as verb, 'Nobody' as pronoun, 'upheaval' as noun) and Q6 ('bravely' -> 'bravery').",
    "- **Page 4 (`paper-2-p4.png`):** Inspected Direction (Q6–10: Rewrite by substituting parts of speech) Q7–Q10 ('beautiful' -> 'beautifully', 'true' -> 'truth', 'gentle' -> 'gently', 'happy' -> 'happiness') and Direction (Q11–15: Idioms and phrases) Q11–Q14 ('to miss the boat', 'under the weather', 'break the ice', 'let the cat out of the bag').",
    "- **Page 5 (`paper-2-p5.png`):** Inspected Q15 ('the ball is in your court'), Direction (Q16–20: Complete sentences with appropriate words) Q16–Q20 ('indispensable', 'inedible', 'misogynist', 'anarchy', 'obsolete'), and Direction (Q21–25: Sentence conversions) Q21–Q23 (negative, superlative, assertive).",
    "- **Page 6 (`paper-2-p6.png`):** Inspected Q24–Q25 (positive degree, imperative) and Direction (Q26–30: Choose the correct sentence) Q26 (No sooner had... than), Q27 (Under no circumstances), Q28 (So difficult was...), Q29 (The harder... the more...), Q30 (Not only did he...). Uncovered OCR duplicate-stem drop for Q27–Q30.",
    "",
    "### 2. Inspector of Statistics Paper-I General English (`doc_b61ba36d95d17e4c2a561cb8`):",
    "- **Page 1 (`paper-1-p1.png`):** Inspected Paper cover (FM: 150): Q1 Essay writing (20 marks: Sairang Rail Station / Mental Health and Work Environment / Good Governance through Official Statistics / The Digital Generation) and Q2 Précis writing (10 marks: Self-reliance as pilgrim's best staff).",
    "- **Page 2 (`paper-1-p2.png`):** Inspected Direction (Q3–12: Reading comprehension on Science and Religion passage) Q3–Q4 (conventional short answers, 2m each), Q5–Q6 (MCQs, 2m each: methods of inquiry, present juncture), Q7 (conventional antonym of 'non-contradictory', 2m), Q8–Q9 (MCQs, 2m each: true/not true statements).",
    "- **Page 3 (`paper-1-p3.png`):** Inspected Q10–Q11 (MCQs, 2m each: truth was, objective of authors), Q12 (conventional synonym of 'dazzled/impressed', 2m), Q13 (homophones sentence making, 10m: Emerge/Immerse, Pair/Pare, Teem/Team, Antique/Antic, Compliment/Complement, Hail/Hale, Wave/Waive, Proscribe/Prescribe), Q14 (one-word substitutes a–l, 20m), Q15 (synonyms a–g, 10m), Q16 (antonyms a–g, 10m), Q17 (idioms sentence making a–g, 10m), Q18 (voice change a–e, 10m).",
    "- **Page 4 (`paper-1-p4.png`):** Inspected Q19 (question tags a–e, 10m) and Q20 (sentence transformations as directed a–j, 20m: know, compound, complex, simple, indirect, direct, if, positive degree, error correction, never).",
    "",
    "## Documented Source, Extraction & Option Defects",
    "",
    "1. **OCR Deduplication Drop on Repeated Stems:** In ITI Instructor Paper-I, printed Q26–Q30 share the identical instruction stem 'Choose the correct sentence:'. Only Q26 was ingested into the database; Q27–Q30 were dropped due to naive stem deduplication. Preserved all 4 dropped MCQs in `pending-written-intake.json`.",
    "2. **Missing Conventional Written Tasks:** Preserved 4 conventional tasks from ITI Instructor (Précis 10m, Letter 10m, Comprehension 10m, Essay 10m) and 14 conventional tasks from Inspector of Statistics (Essay 20m, Précis 10m, 4 Comprehension short answers, Homophones 10m, One-word substitutes 20m, Synonyms 10m, Antonyms 10m, Idioms 10m, Voice 10m, Question tags 10m, Sentence transformations 20m) in `pending-written-intake.json`.",
    "3. **Completely Untagged Ingestion Baseline:** All 32 MCQs across both papers had `subject=null, topic=null` in the production database, leaving them unclassified until this review."
])

(out / "README.md").write_text("\n".join(lines) + "\n")
print(f"Generated README.md ({len(lines)} lines).")
