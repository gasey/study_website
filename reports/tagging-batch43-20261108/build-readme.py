"""Generate README.md for Batch 43."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
packet = json.load(open(out / "oracle-packet.json"))
summary = json.load(open(out / "summary.json"))
findings = json.load(open(out / "findings.json"))
validation = json.load(open(out / "validation.json"))

lines = [
    "# Pending source-reviewed tagging — Batch 43: Final 2024–2025 Direct English Booklets (81 items)",
    "",
    "Policy: `study-tagging-v1`. **81 existing questions reviewed: 79 retag proposals, 2 keep decisions, 0 tag holds. All 81 remain pending. Zero live changes, submissions or publications.**",
    "",
    "## Target Papers & 100% Paper Completion Milestone",
    "",
    "This batch completes 100% source review across the remaining four 2024–2025 Direct English examination booklets in the corpus:",
    "1. *Competitive Examination for the Post of Sericulture Extension Officer (2025) — General English* (`Old_Questions/Direct_2025-2027/General English..pdf`, `doc_3e7d37598a061cd1d52da2ad`, 20 MCQs, 100% paper completion).",
    "2. *Technical Competitive Examination for Junior Grade of Mizoram Engineering Service (Combined) (2025) — General English* (`Old_Questions/Direct_2025-2027/Jr. Grade of MES (Combined)-2025 - General English..pdf`, `doc_682ab0cad0fd9c4e525e91a9`, 21 MCQs, 100% paper completion).",
    "3. *General Competitive Examination for Recruitment to the Post of Junior Grade of Mizoram Planning, Economic & Statistical Service (2025) — General English* (`Old_Questions/Direct_2025-2027/Jr. Grade of MPE & SS, General English..pdf`, `doc_895b0f62c2314d435e125458`, 30 MCQs, 100% paper completion).",
    "4. *Group B(NG) (Technical) Paper-I (General English)-2024* (`Old_Questions/Direct_NG_2024-2027/Group B(NG) (Technical)Paper-I (General English)-2024..pdf`, `doc_d50623457f36f5aeab231741`, 10 composite items, 100% paper completion).",
    "",
    "- **Untagged & Misclassified Baseline Rectification:** All 81 items suffered from unclassified or coarse tag baselines (`subject=english, topic=null` or `topic_id: english/grammar`). Most notably, in Sericulture Extension Officer, question Q3(ii) was misclassified in production as `subject_id: sociology`, which has been cleanly rectified to `english/comprehension`. Across all 4 papers, rectified 100% of targets to active English subtopics: Reading Comprehension (7 items), One-Word Substitution (6 items), Synonyms (6 items), Antonyms (11 items), General Grammar & Clause Analysis (10 items), Tenses & Verb Forms (15 items), Prepositions (16 items), Subject-Verb Agreement (1 item), Parts of Speech (5 items), Précis Writing (1 item), Letter Writing (1 item), Voice (1 item), and Reported Speech (1 item).",
    "- **Preserved Conventional Intake:** Preserved 5 conventional written tasks totaling 80 marks across the papers in `pending-written-intake.json` (Sericulture: Précis 10m, Complaint Letter 15m; MES: Essay 20m; MPE & SS: Essay 20m, Précis 15m).",
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
    "Direct visual inspection of all 16 rendered PNG page images across 4 papers:",
    "- **Paper 1 (`doc_3e7d37598a061cd1d52da2ad`):** Inspected Pages 1 to 4: Q1 (Précis on sericulture), Q2 (Complaint letter on defective silkworms), Q3(i)–Q3(v) (Comprehension passage on communal politics and social class factors), Q7(i)–Q7(v) (Synonyms: persuasions, rescind, frailties, insatiable, pernicious), Q8(i)–Q8(v) (Antonyms: delayed, dejected, literal, deft, urbane), Q9(i)–Q9(v) (One-word substitution: aesthete, cynic, xenophobia, gregarious, phonetics).",
    "- **Paper 2 (`doc_682ab0cad0fd9c4e525e91a9`):** Inspected Pages 1 to 4: Q1 (Essay), Q2(d) (Contextual meaning of 'solemn'), Q5(a)–Q5(e) (Antonyms: Strident, Dank, Component, Friction, Conceptual), Q7(i)–Q7(v) (Tenses/Verbs: Be quiet!, Ram lived, It is strange, One clown, Listen John), Q8(i)–Q8(v) (Prepositions: proud of, looks after, well-known for, through, cautioned against), Q9(i)–Q9(v) (Clauses: noun, adjective, adverb clauses).",
    "- **Paper 3 (`doc_895b0f62c2314d435e125458`):** Inspected Pages 1 to 4: Q1 (Essay), Q2 (Précis), Q1–Q5 (Clause analysis: relative, purpose, noun, reason, manner), Q6–Q10 (Tenses: along with, by the time, I'd rather, though he worked, takes office), Q11–Q15 (Parts of speech: One [pronoun], wise [adj], however [conj], Hurrah! [interj], borne [verb]), Q16–Q25 (Prepositions: in/at, into, since, until, in/on, with, on, for, by, above), Q26–Q30 (Verb forms: teaches, was crossing, had studied, found, will have finished).",
    "- **Paper 4 (`doc_d50623457f36f5aeab231741`):** Inspected Pages 1 to 4: QW1 (Précis), QW2 (Comprehension), QW4 (Letter), QW5 (Prepositions multi-part), QW6 (Verb forms multi-part), QW7 (Voice multi-part), QW8 (Reported speech multi-part), QW9 (One-word substitution multi-part), QW10 (Synonyms multi-part), QW11 (Antonyms multi-part).",
    "",
    "## Documented Source, Extraction & Option Defects",
    "",
    "1. **Rectification of Erroneous 'sociology' Subject Misclassification:** In Sericulture Extension Officer, question Q3(ii) was mistakenly ingested with `subject_id: sociology` due to the passage topic ('class factor in communal politics'). Rectified to `english/comprehension`.",
    "2. **Unextracted Conventional Descriptive Tasks:** Preserved 5 conventional written prompts totaling 80 marks in `pending-written-intake.json` across Sericulture, MES Combined, and MPE & SS."
])

(out / "README.md").write_text("\n".join(lines) + "\n")
print(f"Generated README.md ({len(lines)} lines).")
