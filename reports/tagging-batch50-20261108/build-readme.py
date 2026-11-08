"""Generate README.md for Batch 50."""
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
    "# Pending source-reviewed tagging — Batch 50: Direct 2014-2026 General English Booklets (70 MCQs & Tasks)",
    "",
    "Policy: `study-tagging-v1`. **70 existing questions/tasks reviewed: 70 retag proposals, 0 keep decisions, 0 tag holds. All 70 remain pending. Zero live changes, submissions or publications.**",
    "",
    "## Target Papers & 100% Paper Completion Milestone",
    "",
    "This batch achieves 100% source review of the extracted MCQs and descriptive items across 7 General English examination booklets, finalizing several multi-year series:",
    "1. *Common Competitive Examination for Group 'B' Non-Gazetted (Technical) (March 2026) — Paper I (General English)* (`Old_Questions/Direct_NG_2024-2027/General English Paper-I 2026..pdf`, `doc_7f704f41cc87a988ef58e762`, 5 written tasks, achieving **100% paper completion** with 55/55 items reviewed).",
    "2. *Competitive Examinations for Recruitment to the Posts of Fishery Extension Officer (FEO) — General English* (`Old_Questions/Direct_2014-2018/1.General English Paper-I (FEO).pdf`, `doc_197d853e438e227a2ae7f15f`, 32 items, 100% paper completion).",
    "3. *Inspector of Statistics (February 2017) — General English* (`Old_Questions/Direct_2014-2018/Inspector of Statistics- General English- 2017..pdf`, `doc_08d6b0f9b9e23606217a0ed3`, 12 items, 100% paper completion).",
    "4. *Technical Competitive Examinations for Recruitment to the Post of Employment Officer — General English Paper I* (`Old_Questions/Direct_2019-2020/Employment Officer under LE&IT Deptt Gen English Paper-I.pdf`, `doc_115a2dd346bc29a73812bf40`, 7 items, 100% paper completion).",
    "5. *Competitive Examinations for Recruitment to the Post of Inspector of Factories — General English* (`Old_Questions/Direct_2019-2020/General English (IoF).pdf`, `doc_7eb8775038672312345754e3`, 2 items, 100% paper completion).",
    "6. *Technical Competitive Examinations for Assistant Engineer / Assistant Environmental Officer (AEO) — General English* (`Old_Questions/Direct_2019-2020/General English(AEO).pdf`, `doc_f75f6fa112041692130f684b`, 4 items, 100% paper completion).",
    "7. *Competitive Examinations for Recruitment to Grade-V of Mizoram Food, Civil Supplies & Consumer Affairs Service (Inspector) (2019) — General English Paper I* (`Old_Questions/Direct_2019-2020/Inspector under F,CS & CA Dept-2019, General English Paper I.pdf`, `doc_de0249ac406ac702e8477528`, 8 items, 100% paper completion).",
    "",
    "## Single-Booklet Deduplication Status",
    "",
    "- **Deduplication Enforced:** `Direct_NG_2024-2027/General English Paper-I 2026..pdf` was source-reviewed as the primary booklet (Series A), while its sibling permutation booklets (`Paper-I General English (Series B)..pdf`, `Series C`, and `Series D`, totaling 68 appearances) were cleanly bypassed under single-booklet deduplication rules, avoiding redundant reviews.",
    "",
    "## Granular Structuring & Taxonomy Alignment",
    "",
    "All 70 items were structured into active English taxonomy paths:",
    "- `english/vocabulary/idioms-and-phrases` (19 items):",
    "  - 10 Inspector of Statistics items: Q1–Q10 (*snap one's fingers, French leave, Adam's ale, sum and substance, moot point, fits and starts, queer fish, pell-mell, hole-and-corner, elbow grease*).",
    "  - 7 Employment Officer items: Q1–Q7 (*hard-pressed, all at sea, at loggerheads, throw down the glove, shoot one's bolt, carry one's point, drive home*).",
    "  - 1 FEO item: Q32 (*knows no bounds*).",
    "  - 1 Inspector FCS&CA item: Q5 (*desert island*).",
    "- `english/vocabulary` (11 items): FEO contextual vocabulary items (*terribly, professionalism, hard, death, burdensome, defusing, plunged, series, craving, negligible, illegible*).",
    "- `english/vocabulary/one-word-substitution` (8 items): FEO Q17–Q24 (*piracy, pro bono, nepotism, autocracy, behemoth, trolling, metamorphosis, exodus*).",
    "- `english/grammar/parts-of-speech` (6 items): FEO possessive pronoun *theirs*, comparative adjective *cheaper*, Latin comparative *superior/preferable*, conjunctions *although* and *since*, conjunctive adverb *therefore*.",
    "- `english/grammar/prepositions` (5 items): FEO prepositions *beside*, *above*, *look into*, *ran into*, *cared about*.",
    "- `english/grammar/tenses` (1 item): FEO Q6 simple present habitual action (*goes*).",
    "- `english/grammar/voice` (1 item): Group B Technical Q.W4 active-to-passive transformations across 5 sentences.",
    "- `english/grammar/reported-speech` (1 item): Group B Technical Q.W5 direct-to-indirect speech transformations across 5 sentences.",
    "- `english/comprehension` (6 items): Inspector FCS&CA reading comprehension items Q1–Q3, Q6, Q7 on mass culture, abstract art, and bourgeoisie, plus Group B Technical Q.W2 on Scandinavian Ombudsman institution.",
    "- `english/writing/essay` (3 items): Inspector of Statistics Q1, IoF Q1, AEO Q1 descriptive essays.",
    "- `english/writing/precis` (4 items): Group B Technical Q.W1 (Internet addiction), Inspector of Statistics Q2, IoF Q2, AEO Q2 précis condensation.",
    "- `english/writing/letter` (2 items): Group B Technical Q.W3 (letter to Editor on misleading ads) and AEO Q3 (Finance Department Circular drafting).",
    "- `english/writing` (1 item): AEO Q5 proverb expansion.",
    "- `english/vocabulary/synonyms` (1 item): Inspector FCS&CA Q4 (*apologist -> defender*).",
    "- `english/vocabulary/antonyms` (1 item): Inspector FCS&CA Q8 (*hypocrisy -> sincerity*).",
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
    "Direct visual inspection of rendered PNG page images across all 7 papers (23 pages total):",
    "- **Paper 1 (`doc_197d853e438e227a2ae7f15f`, FEO):** Inspected Pages 1 to 4. Preserved Section A Conventional Tasks (60 marks: Essay 25m, Précis 15m, Letter 20m). Verified 32 MCQs across pages 2 to 4 (Vocabulary 11, Parts of Speech 6, Prepositions 5, Tenses 1, One-Word Substitution 8, Idioms 1).",
    "- **Paper 2 (`doc_08d6b0f9b9e23606217a0ed3`, Inspector of Statistics):** Inspected Pages 1 to 4. Preserved Conventional Tasks (40 marks: Letter 15m, Expansion 15m, Idiom Sentences 10m). Verified 2 descriptive tasks (Essay 25m, Précis 15m) and 10 MCQs on Idioms & Phrases.",
    "- **Paper 3 (`doc_115a2dd346bc29a73812bf40`, Employment Officer):** Inspected Pages 1 to 3. Preserved Section A Conventional Tasks (86 marks: Essay 25m, Précis 15m, Letter 15m, Expansion 15m, Comprehension 16m). Verified 7 MCQs on Idioms & Phrases.",
    "- **Paper 4 (`doc_7eb8775038672312345754e3`, IoF):** Inspected Pages 1 to 3. Preserved Section A Conventional Tasks (60 marks: Letter 15m, Idiom Sentences 15m, Expansion 15m, Comprehension 15m). Verified 2 descriptive tasks (Essay 25m, Précis 15m).",
    "- **Paper 5 (`doc_f75f6fa112041692130f684b`, AEO):** Inspected Pages 1 to 3. Preserved Conventional Tasks (30 marks: Idiom Sentences 14m, Comprehension 16m). Verified 4 descriptive tasks (Essay 25m, Précis 15m, Circular Drafting 15m, Expansion 15m).",
    "- **Paper 6 (`doc_de0249ac406ac702e8477528`, Inspector FCS&CA):** Inspected Pages 1 to 4. Preserved Conventional Tasks (70 marks: Essay 25m, Précis 15m, Letter 15m, Expansion 15m). Verified 8 MCQs on modern art, bourgeoisie, synonyms, and antonyms.",
    "- **Paper 7 (`doc_7f704f41cc87a988ef58e762`, Group B Technical 2026):** Inspected Pages 6 and 7. Verified and structured all 5 written tasks W1–W5 (Précis 10m, Ombudsman Comprehension 15m, Letter 15m, Voice 5m, Speech 5m), finalizing the paper to 100% completion (55 of 55 items).",
    "",
    "## Documented Source, Extraction & Option Defects",
    "",
    "1. **Single-Booklet Permutation Bypassing:** Cleanly bypassed 68 duplicate appearances across Series B, C, and D of the 2026 Group 'B' Non-Gazetted Technical examination, maintaining single-booklet deduplication integrity.",
    "2. **Preservation of 346 Marks of Conventional Written Tasks:** Documented 21 descriptive tasks across all 7 booklets in `pending-written-intake.json`.",
    "3. **Paper Finalization:** Brought Group 'B' Non-Gazetted Technical Paper-I to 100% completion (55/55 items) by source-reviewing the 5 written items W1–W5."
])

(out / "README.md").write_text("\n".join(lines) + "\n")
print(f"Generated README.md ({len(lines)} lines).")
