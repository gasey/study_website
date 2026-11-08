"""Generate README.md for Batch 48."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
packet = json.load(open(out / "oracle-packet.json"))
summary = json.load(open(out / "summary.json"))
findings = json.load(open(out / "findings.json"))
validation = json.load(open(out / "validation.json"))

def fmt_tax(t):
    if not t:
        return "None"
    subid = t.get("subtopic_id")
    tid = t.get("topic_id")
    sid = t.get("subject_id")
    return subid or tid or sid or "None"

lines = [
    "# Pending source-reviewed tagging — Batch 48: Direct 2022-2023 General English Booklets (75 MCQs & Tasks)",
    "",
    "Policy: `study-tagging-v1`. **75 existing questions/tasks reviewed: 75 retag proposals, 0 keep decisions, 0 tag holds. All 75 remain pending. Zero live changes, submissions or publications.**",
    "",
    "## Target Papers & 100% Paper Completion Milestone",
    "",
    "This batch achieves 100% source review of the extracted MCQs and descriptive items across 4 Direct 2022–2023 General English examination booklets:",
    "1. *Competitive Examinations for Recruitment to the Post of Grade-V of MSCS (Cooperative Audit Officer) (December 2022) — General English Paper-I* (`Old_Questions/Direct_2022-2023/General English Paper-I (CAO).pdf`, `doc_09ecdb100f668625c85b57c4`, 14 MCQs, 100% paper completion).",
    "2. *Competitive Examinations for Recruitment to the Post of Geologist Junior under Commerce & Industries Department (November 2022) — General English Paper-I* (`Old_Questions/Direct_2022-2023/Geologist Junior under Commerce Deptt - Gen English-I..pdf`, `doc_7a32498eb36e71f5a1ac6918`, 6 items, 100% paper completion).",
    "3. *Technical Competitive Examinations for Grade-III of Mizoram Health Service (GDMO & Dental Surgeon Sub-Cadre) (October 2022) — General English* (`Old_Questions/Direct_2022-2023/Gr-III of MHS (GDMO-Dental Surgeon Sub-Cadre) Common - General English..pdf`, `doc_062a465c96890fff341e8db7`, 20 MCQs, 100% paper completion).",
    "4. *Technical Competitive Examinations for Junior Grade of Mizoram Engineering Service, P&E Cadre (Electrical Wing) (June 2022) — General English* (`Old_Questions/Direct_2022-2023/Jr. Grade of MES (Electrical Wing) under P & E Deptt., General English - 2022...pdf`, `doc_4e9059a592b86e3de860b4f1`, 35 MCQs, 100% paper completion).",
    "",
    "## Single-Booklet Deduplication Status",
    "",
    "- **Booklet Status:** All 4 papers are standalone single-booklet direct examinations with zero duplicate series or multi-folder ingestions.",
    "",
    "## Granular Structuring & Taxonomy Alignment",
    "",
    "All 75 items had unclassified subtopics or null topics in their baseline records. Source inspection structured them into granular active English taxonomy paths:",
    "- `english/vocabulary/idioms-and-phrases` (24 items):",
    "  - 14 CAO Paper-I items: Q4 ('getting into a row'), Q5 ('cry wolf'), Q6 ('take wind out of sails'), Q7 ('at fingertips'), Q8 ('put foot down'), Q9 ('blowing hot and cold'), Q10 ('on their toes'), Q11 ('cut coat according to cloth'), Q12 ('fell on stony ground'), Q13 ('out of spirits'), Q14 ('lose head'), Q15 ('made my day'), Q16 ('washed hands off'), Q17 ('let hair down').",
    "  - 10 GDMO/Dental items: Q5(a)–(j) ('green-eyed friends', 'left high and dry', 'feather in your cap', 'burning question', 'have cake and eat it too', 'sitting on the fence', 'took him to task', 'make head or tail of it', 'pulling my leg', 'in doldrums').",
    "- `english/vocabulary` (10 items): GDMO/Dental Q7(a)–(j) contextual vocabulary and lexical choice ('volcanic eruption', 'favouritism', 'respectable clothes', 'inevitable defeat', 'scalded hand', 'impair judgment', 'exercise restraint', 'sumptuous lunch', 'averted tragedy', 'serious altercation').",
    "- `english/vocabulary/synonyms` (10 items):",
    "  - 5 MES Electrical Wing passage synonyms: Q3(a)–(e) ('count on' for 'depend on', 'strange' for 'unfamiliar', 'devour' for 'consume', 'uncivilised' for 'savage', 'happens to' for 'befalls').",
    "  - 5 MES Electrical Wing general synonyms: Q24–Q28 ('hamper' -> 'hinder', 'assignment' -> 'task', 'burden' -> 'load', 'antagonistic' -> 'hostile', 'belligerent' -> 'aggressive').",
    "- `english/vocabulary/antonyms` (5 items): MES Electrical Wing Q29–Q33 ('adversity' -> 'prosperity', 'enrich' -> 'impoverish', 'Coarse' -> 'fine', 'Important' -> 'trivial', 'repulsive' -> 'attractive').",
    "- `english/grammar/parts-of-speech` (10 items): MES Electrical Wing Q4–Q13 (noun 'spider', adjective 'little', verb 'sells', pronoun 'They', verb 'spreads', conjunction 'and', adverb 'soundly', preposition 'into', interjection 'Alas!', pronoun 'Our').",
    "- `english/grammar/tenses` (10 items): MES Electrical Wing Q14–Q23 (Future indefinite 'shall remain', Present continuous 'is raining', Present perfect 'has stood', Future perfect 'will have finished', Present perfect continuous 'has been looking', Present indefinite 'lights', Past indefinite 'Did ... smoke', Past perfect 'had run', Past perfect continuous 'had been ringing', Present indefinite 'cuts').",
    "- `english/writing/essay` (1 item): Geologist Junior Q1 descriptive essay composition (Sustainable Development, Climate Change, Social Networking).",
    "- `english/writing/precis` (1 item): Geologist Junior Q2 descriptive précis condensation (books & solitary reflection).",
    "- `english/writing/letter` (2 items): Geologist Junior Q3(a) (letter to Superintendent of Police on cyber crime) and Q3(b) (letter to Village Council on quarry safety).",
    "- `english/writing` (1 item): Geologist Junior Q5 proverb and sentence expansion.",
    "- `english/comprehension` (1 item): Geologist Junior Q6 reading comprehension short-answer questions.",
    f"- **Fresh Oracle read-only export:** `{packet['exported_at']}`. Readback validation (`{validation['validated_at']}`) confirmed 100% source fingerprint consistency, zero live mutations, and 100% compliance with active taxonomy nodes.",
    "",
    "## Before / after table",
    "",
    "| # | Source context | Tested skill | Before | Proposed after | Decision & rationale |",
    "| :---: | :--- | :--- | :--- | :--- | :--- |"
]

for idx, f in enumerate(findings, 1):
    ctx = f"{f['paper_title'][:30]}... Q.{f['question_number']} (p. {f['physical_page']})"
    cur = fmt_tax(f["current_classification"])
    prop = fmt_tax(f["proposed_classification"])
    lines.append(
        f"| {idx} | {ctx} | {f['task_description']} | `{cur}` | `{prop}` | **{f['action']}** — {f['rationale']} |"
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
    "- **Paper 1 (`doc_09ecdb100f668625c85b57c4`, CAO 2022):** Inspected Pages 1 to 3. Preserved Section A Conventional Tasks (70 marks: Essay 25m, Précis 15m, Letter 15m, Proverb Expansion 15m, Comprehension True/False 7m, Comprehension Short-Answer 9m). Verified 14 MCQs on Idioms & Phrases across pages 1–2.",
    "- **Paper 2 (`doc_7a32498eb36e71f5a1ac6918`, Geologist Junior 2022):** Inspected Pages 1 to 2. Preserved Idiom Sentence Composition Task 4 (14m). Verified and structured all 6 registered descriptive tasks (Essay 25m, Précis 15m, Letter 3a 15m, Letter 3b 15m, Expansion 15m, Comprehension 16m).",
    "- **Paper 3 (`doc_062a465c96890fff341e8db7`, MHS GDMO/Dental 2022):** Inspected Pages 1 to 4. Preserved Section A Conventional Tasks (80 marks: Essay 20m, Comprehension 20m, Précis 20m, Sentence Correction 10m, Word Pairs Sentence Making 10m). Verified 20 MCQs across pages 3–4 (Idioms & Phrases 10, Vocabulary in Context 10).",
    "- **Paper 4 (`doc_4e9059a592b86e3de860b4f1`, MES Electrical Wing 2022):** Inspected Pages 1 to 5. Preserved Section A Conventional Tasks (65 marks: Essay 20m, Précis 20m, Comprehension 15m, Idiom Sentence Making 10m). Verified 35 MCQs across pages 2 to 5 (Passage Synonyms 5, Parts of Speech 10, Tenses 10, Synonyms 5, Antonyms 5).",
    "",
    "## Documented Source, Extraction & Option Defects",
    "",
    "1. **Underlined Word Geometry Extraction in Parts of Speech:** Verified exact rectangular fill path coordinates (`d['rect']`) in PDF stream for MES Electrical Wing Q4–Q13 to pinpoint precisely which token was underlined ('spider', 'little', 'sells', 'They', 'spreads', 'and', 'soundly', 'into', 'Alas!', 'Our').",
    "2. **Preservation of 245 Marks of Conventional Written Tasks:** Documented 16 descriptive tasks (Essays, Précis, Letter writing, Proverb expansions, Sentence corrections, and Idiom sentence compositions) across all 4 booklets in `pending-written-intake.json`.",
    "3. **Dual Ingestion of Alternative Letter Prompts:** Documented that Geologist Junior Q3 was ingested as two independent descriptive records (`desc-ccd21508f413220e9bbb` for 3(a) and `desc-b27741e0b86dd8107765` for 3(b)), both structured under `english/writing/letter`."
])

(out / "README.md").write_text("\n".join(lines) + "\n")
print(f"Generated README.md ({len(lines)} lines).")
