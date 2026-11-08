"""Generate README.md for Batch 36."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
packet = json.load(open(out / "oracle-packet.json"))
summary = json.load(open(out / "summary.json"))
findings = json.load(open(out / "findings.json"))
validation = json.load(open(out / "validation.json"))
written = json.load(open(out / "pending-written-intake.json"))

lines = [
    "# Pending source-reviewed tagging — Batch 36: Agri & Allied 2025 & Jr. of MHS 2025 General English (86 MCQs)",
    "",
    "Policy: `study-tagging-v1`. **86 existing MCQ questions reviewed: 86 retag proposals, 0 keep decisions, 0 tag holds. 10 unextracted conventional written tasks and dropped duplicate-stem MCQs preserved as separate pending intake evidence. All 86 remain pending. Zero live changes, submissions or publications.**",
    "",
    "## Target Papers Identity & 100% Paper Completion Milestone",
    "",
    "1. **Agri & Allied Services (Combined Technical) (November-2025) — General English** (`Old_Questions/Direct_2025-2027/Agri&Allied General English 2025..pdf`, `doc_74fb44237ebef4588c005e8a`, `sha256: 896a3876c120fae7600dcea6bfb9745a6082af38464edb7addb9002e0c80aa5a`): 46 MCQs (Q1–Q41, Q46–Q50 across physical PDF pages 4 to 8).",
    "2. **Junior Grade of Mizoram Health Services (Combined) (September-2025) — General English** (`Old_Questions/Direct_2025-2027/General English - Jr. of MHS, 2025..pdf`, `doc_dab76ba7bd50a3f08ac483d2`, `sha256: e506b03f45c1244ccbe4c7ff6ce8363764835848bb22687bf8a4f91187d90367`): 40 MCQs (Q1–Q40 across physical PDF pages 4 to 7).",
    "- **Untagged Baseline Rectification:** In the database, all 86 questions were completely untagged (`subject=null, topic=null`). Proposed active English taxonomy paths for 100% of targets: Parts of Speech (21 items), Prepositions (13 items), Idioms & Phrases (14 items), Contextual Vocabulary & Homophones (12 items), Sentence Transformations & Clauses (7 items), Tenses (5 items), Sentence Correction (5 items), One-Word Substitution (5 items), Active & Passive Voice (1 item), Articles (1 item), Synonyms (1 item), and Antonyms (1 item).",
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
    "### 1. Agri & Allied Services General English (`doc_74fb44237ebef4588c005e8a`):",
    "- **Page 1 (`paper-1-p1.png`):** Inspected Paper cover and Section-A Conventional Type (50 Marks) Q1 Précis writing (10 marks: Morality as spiritual and ethical compass of society).",
    "- **Page 2 (`paper-1-p2.png`):** Inspected Section-A Q2 Reading Comprehension passage on economic inequality (20 marks: questions a to f).",
    "- **Page 3 (`paper-1-p3.png`):** Inspected Section-A Q4 Sentence transformations as directed (10 marks: Complex, Simple, Compound, Voice change).",
    "- **Page 4 (`paper-1-p4.png`):** Inspected Section-B Multiple Choice Questions (50 Marks, negative marking 1/3) Direction (Q1–10: Identify parts of speech) Q1–Q8 ('tasted' as verb, 'always' as adverb, 'although' as conjunction, 'quite' as adverb, 'that' as demonstrative adjective, 'courage' as noun, 'costly' as adjective, 'very' as adverb).",
    "- **Page 5 (`paper-1-p5.png`):** Inspected Q9–Q10 ('least' as adverb, 'who' as relative pronoun), Direction (Q11–15: Idioms and phrases) Q11–Q15 (Where ignorance is bliss, heteronym, a white elephant, all greek to me, break a leg), and Direction (Q16–20: Choose the appropriate words) Q16–Q19 ('patience', 'bane', 'complemented', 'tiptoed').",
    "- **Page 6 (`paper-1-p6.png`):** Inspected Q20 ('dismayed'), Direction (Q21–25: Connectors) Q21–Q25 ('prefer to', 'besides', 'while', 'despite', 'or else'), and Direction (Q26–30: Prepositions) Q26–Q30 ('walked into', 'acquitted of', 'besides studying', 'triumphs over', 'sparing of').",
    "- **Page 7 (`paper-1-p7.png`):** Inspected Direction (Q31–35: Adjectives) Q31–Q35 (the most charming, much rain, the little food, the greatest villain, adjective of quantity), Direction (Q36–40: Determiners) Q36–Q40 (possessive adjective, many vacations, the head, sufficient evidence, each of us), and Q41 (Sentence structure).",
    "- **Page 8 (`paper-1-p8.png`):** Inspected Direction (Q41–45: Choose the correct sentence) Q42–Q45 (uncovered OCR dropped empty stems) and Direction (Q46–50: Type of clause) Q46–Q50 (adverb clause of reason, noun clause, adverb clause of place, noun clause, noun clause).",
    "",
    "### 2. Junior Grade of Mizoram Health Services General English (`doc_dab76ba7bd50a3f08ac483d2`):",
    "- **Page 1 (`paper-2-p1.png`):** Inspected Paper cover and Section-A (60 Marks): Q1 Essay writing (20 marks: Family role / Physical & mental health / Hospital acquired infection) and Q2 Précis writing (20 marks: John Ruskin passage on money vs work).",
    "- **Page 2 (`paper-2-p2.png`):** Inspected Section-A Direction (Q3–12: Reading comprehension passage on forming independent opinions).",
    "- **Page 3 (`paper-2-p3.png`):** Inspected Section-A Q6–Q12 reading comprehension questions.",
    "- **Page 4 (`paper-2-p4.png`):** Inspected Section-B Multiple Choice Questions (40 Marks): Direction (Q1–5: Verb tenses) Q1–Q5 ('rains', 'has been looking', 'will be waiting', 'were playing', 'am writing') and Direction (Q6–10: Prepositions) Q6–Q10 ('above us', 'out of the window', 'under the blankets', 'no money on me', 'glanced at').",
    "- **Page 5 (`paper-2-p5.png`):** Inspected Direction (Q11–15: Idioms) Q11–Q15 (act together, snowed under, stick to guns, reach majority, two to tango) and Direction (Q16–20: One-word substitution) Q16–Q20 (Conscientious, Articulate, Epitaph, Amnesia, Altruist).",
    "- **Page 6 (`paper-2-p6.png`):** Inspected Direction (Q21–25: Idioms in sentences) Q21–Q25 (in the offing, bird's eye view, dropping like flies, cut teeth on, taken wind out of sails), Direction (Q26–30: Choose grammatically correct sentence) Q26–Q30 (fair-weather friend, divided between two, stories that have, outright, different from), and Direction (Q31–35: Homophones) Q31–Q32 (their, sale).",
    "- **Page 7 (`paper-2-p7.png`):** Inspected Q33–Q35 (route, site, chords), Q36 (compound sentence), Q37 (passive voice), Q38 (Indifferent synonym), Q39 (Generous antonym), and Q40 (affect/effect).",
    "",
    "## Documented Source, Extraction & Option Defects",
    "",
    "1. **OCR Deduplication Drop on Repeated Stems:** In Agri & Allied General English Section-B, printed Q41–Q45 share the instruction 'Choose the correct sentence:'. Because Q42–Q45 had empty stems, automated ingestion dropped Q42–Q45, creating sequence gaps in the database. Preserved all 4 dropped MCQs in `pending-written-intake.json`.",
    "2. **Missing Conventional Written Tasks:** Preserved 3 Section-A tasks from Agri & Allied (Précis 10m, Reading Comprehension 20m, Sentence Transformations 10m) and 3 Section-A tasks from Jr. of MHS (Essay 20m, Précis 20m, Reading Comprehension 20m) in `pending-written-intake.json`.",
    "3. **Completely Untagged Ingestion Baseline:** All 86 MCQs across both papers had `subject=null, topic=null` in the production database, leaving them unclassified until this review."
])

(out / "README.md").write_text("\n".join(lines) + "\n")
print(f"Generated README.md ({len(lines)} lines).")
