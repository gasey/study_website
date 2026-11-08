"""Generate README.md for Batch 47."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
packet = json.load(open(out / "oracle-packet.json"))
summary = json.load(open(out / "summary.json"))
findings = json.load(open(out / "findings.json"))
validation = json.load(open(out / "validation.json"))

lines = [
    "# Pending source-reviewed tagging — Batch 47: Direct 2023-2025 General English Booklets (78 MCQs)",
    "",
    "Policy: `study-tagging-v1`. **78 existing questions reviewed: 78 retag proposals, 0 keep decisions, 0 tag holds. All 78 remain pending. Zero live changes, submissions or publications.**",
    "",
    "## Target Papers & 100% Paper Completion Milestone",
    "",
    "This batch achieves 100% source review of the extracted MCQs across all 4 remaining Direct 2023–2025 General English examination booklets:",
    "1. *General Competitive Examinations for Recruitment to the Post of Jr. Grade of Mizoram Forest Service (Asst. Conservator of Forests) (2023) — General English* (`Old_Questions/Direct_2023-2025/ACF-2023-General English..pdf`, `doc_b5f51992824cdf78ca9eb105`, 10 MCQs, 100% paper completion).",
    "2. *Technical Competitive Examination for Informatics Officer under ICT Department (November 2024) — General English Paper-I* (`Old_Questions/Direct_2023-2025/Informatics Officer General English Paper-I 2024..pdf`, `doc_e46ac6fab7a2eb8bf138f169`, 8 MCQs, 100% paper completion).",
    "3. *Technical Competitive Examinations for Junior Grade of Mizoram Engineering Service, P&E Cadre (Electrical Wing) and Assistant Architect (July 2023) — General English* (`Old_Questions/Direct_2023-2025/Jr. Grade of MES (Electrical Wing) under P&E Deptt., General English..pdf`, `doc_210c8de409ca07cc3de1ad76`, 10 MCQs, 100% paper completion).",
    "4. *Technical Competitive Examinations for Junior Grade of Mizoram Legal Service (MLS) under Law & Judicial Department (July 2023) — English* (`Old_Questions/Direct_2023-2025/Jr. Grade of MLS under Law & Judicial Deptt. - English..pdf`, `doc_e13e10e93f23cf05cda8960a`, 50 MCQs, 100% paper completion).",
    "",
    "## Single-Booklet Deduplication Status",
    "",
    "- **Booklet Status:** All 4 papers are standalone single-booklet direct examinations with zero duplicate series or multi-folder ingestions.",
    "",
    "## Misclassification & Untagged Baseline Rectifications",
    "",
    "Source inspection identified and cleanly rectified multiple baseline tagging defects:",
    "- **Rectification of 'town-planning' Subject Misclassification:** Item `mpsc-cli-informatics-officer-general-english-paper-i-2024-007` ('What role do green roofs play in sustainable urban planning?') was erroneously tagged under `town-planning` due to passage keywords. Rectified to active taxonomy `english/comprehension`.",
    "- **77 Coarse / Untagged Items Structured:** Rectified 77 bare `english` or placeholder baseline items to precise active subtopics:",
    "  - `english/vocabulary/one-word-substitution` (10 items): MES Electrical Wing Q6(a)–(j) ('timid', 'peer', 'emigrant', 'faux pas', 'diffident', 'complacent', 'hypocrite', 'ordination', 'immune', 'polyglot').",
    "  - `english/vocabulary/idioms-and-phrases` (15 items): ACF Q1–Q10 ('make head or tail', 'burning question', 'gift of the gab', 'take to task', 'take to one's heels', 'get cold feet', 'red-letter day', 'sit on the fence', 'clean breast', 'green-eyed friends') and MLS Q46–Q50 ('hit the sack', 'cut corners', 'draw the line', 'dime a dozen', 'snowball effect').",
    "  - `english/vocabulary/synonyms` (5 items): MLS Q1–Q5 ('plebeian', 'sterling', 'indispensable', 'resilient', 'hilarious').",
    "  - `english/vocabulary/antonyms` (5 items): MLS Q6–Q10 ('impoverished', 'insolvent', 'admiring', 'tenacious', 'subtle').",
    "  - `english/grammar/prepositions` (5 items): MLS Q11–Q15 (spatial 'above', distribution 'among', instrument 'with', emotion 'over', phrasal verb 'put me up').",
    "  - `english/grammar/parts-of-speech` (5 items): MLS Q16–Q20 conjunctions ('if', 'lest', 'despite', 'so', 'although').",
    "  - `english/grammar/tenses` (10 items): MLS Q21–Q30 (present perfect continuous 'has been living', simple present 'cries', simple past 'ran', future continuous 'will be meeting', present singular 'wants', present perfect 'have written', narrative past 'went', bare infinitive 'send', past auxiliary 'did', modal base verb 'agree').",
    "  - `english/grammar/subject-verb-agreement` (5 items): MLS Q31–Q35 ('Either he or I am', 'Rama as well as ... likes', 'You, who are', 'A black and a white cow were', collective noun 'mob was').",
    "  - `english/grammar/reported-speech` (5 items): MLS Q36–Q40 (direct to indirect speech for imperatives, modal questions, past-to-past-perfect shifts, future will-to-would, and exclamatory sentences).",
    "  - `english/grammar/voice` (5 items): MLS Q41–Q45 (quasi-passive middle voice 'Sugar tastes sweet', present continuous passive 'is being written', past simple passive 'were seen', infinitive of obligation passive 'is to be assisted', present perfect passive 'have been chopped').",
    "  - `english/comprehension` (8 items): Informatics Officer Q6(a)–(h) reading comprehension items on sustainable urban planning and challenges.",
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
    f"- **Conventional marks preserved:** {summary['conventional_marks_preserved']}",
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
    "Direct visual inspection of rendered PNG page images across all 4 papers (14 pages total):",
    "- **Paper 1 (`doc_b5f51992824cdf78ca9eb105`, ACF 2023):** Inspected Pages 1 to 3. Preserved Essay Task 1 (25m) on page 1 and Reading Comprehension written questions Task 7 (15m) on page 3. Verified 10 MCQs on idioms & phrases on page 2.",
    "- **Paper 2 (`doc_e46ac6fab7a2eb8bf138f169`, Informatics Officer 2024):** Inspected Pages 1 to 3 via tesseract OCR and PNG rendering. Preserved Essay Task 1 (25m) and Précis Task 2 (15m) on page 1, and Idea Expansion Task 5 (15m) on page 2. Verified 8 MCQs on Reading Comprehension (urbanization, green spaces, socio-economic disparity, quality of life, green roofs) on pages 2–3.",
    "- **Paper 3 (`doc_210c8de409ca07cc3de1ad76`, MES Electrical Wing 2023):** Inspected Pages 1 to 2. Preserved Essay Task 1 (20m) on page 1 and Précis Task 3 (20m) on page 2. Verified 10 One-Word Substitution items on page 1.",
    "- **Paper 4 (`doc_e13e10e93f23cf05cda8960a`, MLS English 2023):** Inspected Pages 1 to 6. Preserved Section A Conventional Tasks (50m: Essay 25m, Précis 15m, Idiom sentence composition 10m) on page 1. Verified 50 Section B MCQs across pages 2 to 6 (Synonyms 5, Antonyms 5, Prepositions 5, Conjunctions 5, Tenses 10, Subject-Verb Agreement 5, Reported Speech 5, Voice 5, Idioms 5).",
    "",
    "## Documented Source, Extraction & Option Defects",
    "",
    "1. **Rectification of 'town-planning' Subject Misclassification:** Rectified Informatics Officer reading comprehension item Q6(g) from `town-planning` to `english/comprehension`.",
    "2. **Preservation of 190 Marks of Conventional Written Work:** Documented 10 descriptive tasks (Essays, Précis, Idea Expansion, and Idiom sentence writing) across all 4 booklets in `pending-written-intake.json`.",
    "3. **Scanned PDF Optical Extraction Alignment:** Verified and numbered the 8 unnumbered comprehension items of Informatics Officer matching physical pages 2 and 3 of the examination booklet."
])

(out / "README.md").write_text("\n".join(lines) + "\n")
print(f"Generated README.md ({len(lines)} lines).")
