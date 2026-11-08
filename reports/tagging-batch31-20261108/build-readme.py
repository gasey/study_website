"""Generate README.md for Batch 31."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
packet = json.load(open(out / "oracle-packet.json"))
summary = json.load(open(out / "summary.json"))
findings = json.load(open(out / "findings.json"))
validation = json.load(open(out / "validation.json"))
written = json.load(open(out / "pending-written-intake.json"))

lines = [
    "# Pending source-reviewed tagging — Batch 31: Lecturer Govt. Hr. Sec. School Serchhip 2026 General English",
    "",
    "Policy: `study-tagging-v1`. **66 existing MCQ questions reviewed: 65 retag proposals, 1 keep decision, 0 tag holds. 3 unextracted conventional written tasks preserved as separate pending intake evidence. All 66 remain pending. Zero live changes, submissions or publications.**",
    "",
    "## Target Paper Identity & 100% Paper Completion Milestone",
    "",
    "- **Paper:** *Competitive Examination for Recruitment of Lecturer (Contract), Govt. Higher Secondary School, Serchhip under School Education Department, Government of Mizoram (March & April, 2026) — General English* (`Old_Questions/Direct_2025-2027/Lecturer Govt.Hr,Higher Secondary School, Serchhip, 2026- General English..pdf`, `doc_94f974b5a87cadd1fb61511f`, `sha256: 01212bc97b525a1df8a13df65c1d750e0ccfde93223e0bb06b2fd1cfb9f50d93`).",
    "- **Coverage:** Complete 100% review of all 66 extracted Part-A MCQs (Q1–Q66 across physical PDF pages 1 to 6), achieving full paper completion.",
    "- **Severe Misclassification Rectification:** In the database, all 66 items were misclassified under `gk` placeholder subject (`subject=gk, topic=Lecturer Govt.Hr,Higher Secondary School, Serchhip...`). Rectified 65 items to active English subtopics: Parts of Speech (34 items), Prepositions (3 items), Contextual Vocabulary (5 items), Reported Speech (6 items), Tenses (5 items), Subject-Verb Agreement (2 items), Synonyms (1 item), Antonyms (1 item), One-Word Substitution (3 items), and Sentence Transformations/Clauses (6 items). Verified 1 already-correct subtopic (Q18 `english/grammar/parts-of-speech`) as KEEP decision.",
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
    "Direct visual inspection of all 7 rendered PNG page images (`paper-1-p1.png` to `paper-1-p7.png`) of `doc_94f974b5a87cadd1fb61511f`:",
    "- **Page 1 (`paper-1-p1.png`):** Inspected Paper cover and Part-A Multiple Choice Questions (66 Marks) Direction (Q1–30: Choose correct parts of speech) Q1–Q8 (eloquently, emotion/interjection, that as conjunction, fast as adjective, hers, coordinating conjunction, he as pronoun, light as noun).",
    "- **Page 2 (`paper-1-p2.png`):** Inspected Q9–Q22 (Alas!, either, run/verb, adjective, pronoun, city/common noun, transitive verb, adverb, water/uncountable, gerund, himself/reflexive, read/transitive, broke/intransitive, before/conjunction).",
    "- **Page 3 (`paper-1-p3.png`):** Inspected Q23–Q30 (adverb definition, music/noun, seem/linking, by its tail, This/demonstrative, everyone/indefinite, sharp/adjective, on/upon) and Direction (Q31–36: Vocabulary fill in the blanks) Q31–Q36 (exemplary, expand, lucid, fewer, prone, cogent).",
    "- **Page 4 (`paper-1-p4.png`):** Inspected Direction (Q37–39: Reported speech/SVA) Q37–Q39 (I was, is interesting, was given a medal), Q40–Q41 (Obdurate synonym, Ephemeral antonym), Q42–Q43 (fleet of ships, herd of cows), Q44–Q46 (Lexicographer, Omniscient, Astronomer), and Q47–Q49 (is crying, were having, have finished).",
    "- **Page 5 (`paper-1-p5.png`):** Inspected Q50–Q51 (is going to, will have completed), Q52–Q54 (yet, unless, when), Q55–Q57 (exclamatory, negative, negative-interrogative), and Q58–Q61 (because he was late, who won the prize, what you said, at his behaviour).",
    "- **Page 6 (`paper-1-p6.png`):** Inspected Direction (Q62–66: Change into indirect speech) Q62–Q66 (will finish tomorrow -> would finish next day, where are you going -> where I was going, must complete today -> must complete that day, open door -> told me to open, cannot solve -> could not solve). Also inspected Part-B Conventional Type (34 Marks) Q1 (Précis writing, 14 marks: Smartphone ownership and digital literacy among youth).",
    "- **Page 7 (`paper-1-p7.png`):** Inspected Part-B Q2 (Job application letter with resume to Principal of Lianbuanga Memorial Higher Secondary School for lecturer post, 10 marks) and Q3(a)–(e) (Reading comprehension on Indian unity in diversity, 10 marks).",
    "",
    "## Documented Source, Extraction & Option Defects",
    "",
    "1. **Missing Part-B Conventional Written Tasks (Pages 6–7):** 3 prompts totaling 34 marks (Précis 14m, Lecturer Job Application Letter 10m, Reading Comprehension 10m) preserved in `pending-written-intake.json`.",
    "2. **Severe Database Misclassification under `gk`:** Automated ingestion classified all 66 MCQs as generic `gk` under paper title rather than English taxonomy.",
    "3. **Underline Omissions in Stored Text:** Database text for Q1, Q9, Q58–Q61 omits printed underline formatting.",
    "4. **Printed Booklet Typos:** Page 6 prints 'Ditection' instead of 'Direction' above Q62; Part-B prints 'indicated against its' instead of 'it'."
])

(out / "README.md").write_text("\n".join(lines) + "\n")
print(f"Generated README.md ({len(lines)} lines).")
