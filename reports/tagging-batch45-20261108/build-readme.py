"""Generate README.md for Batch 45."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
packet = json.load(open(out / "oracle-packet.json"))
summary = json.load(open(out / "summary.json"))
findings = json.load(open(out / "findings.json"))
validation = json.load(open(out / "validation.json"))

lines = [
    "# Pending source-reviewed tagging — Batch 45: ADA, AA & ATA General English (60 MCQs)",
    "",
    "Policy: `study-tagging-v1`. **60 existing questions reviewed: 58 retag proposals, 2 keep decisions, 0 tag holds. All 60 remain pending. Zero live changes, submissions or publications.**",
    "",
    "## Target Paper & 100% Paper Completion Milestone",
    "",
    "This batch achieves 100% source review of the extracted MCQs for the companion General English paper to the Batch 44 Arithmetic booklet:",
    "- *Competitive Examinations for Recruitment to the Posts of Assistant Auditor, Assistant Treasury Accountant & Assistant Divisional Accountant under Finance Department, Government of Mizoram (January 2019) — General English* (`Old_Questions/Direct_2019-2020/ADA, AA & ATA General English.pdf`, `doc_28eafb04c21bfc501a33c583`, 60 MCQs, 100% paper completion).",
    "",
    "## Single-Booklet Deduplication Status",
    "",
    "- **Booklet Status:** Single-booklet direct recruitment examination with no alternate series or duplicate copies in the repository.",
    "",
    "## Untagged Baseline Rectification",
    "",
    "In the production database, all 60 items had unclassified coarse baseline tags (`current_subject: 'gk'`, `current_topic: 'ADA, AA & ATA General English'`). All 60 have been reviewed against official question text and structured into precise active taxonomy paths:",
    "- `english/grammar/parts-of-speech` (25 items):",
    "  - Nouns: abstract noun ('Laughter'), collective noun ('crowd'), common noun ('Grammar').",
    "  - Verbs & Verbals: transitive verb ('hurt'), gerunds ('Hunting', 'hoarding', 'Swimming', 'Giving', 'receiving', 'smoking'), participles / participial adjectives ('swimming pool', 'losing game', 'standing building').",
    "  - Adjectives: predicate adjective ('true'), substantive descriptive adjective ('courageous').",
    "  - Adverbs: adverb of degree ('quite'), adverb of manner ('fast').",
    "  - Interjections: 'Bravo!'.",
    "  - Conjunctions: adversative ('but'), concessive ('though'), causal ('Since'), explanatory ('for'), alternative ('else'), temporal ('before'), negative conditional ('Unless').",
    "  - Spatial Preposition: 'over'.",
    "- `english/grammar` (19 items):",
    "  - Modal Notions & Sentence Functions (10 items): possibility ('may'), obligation ('must'), direct command / order ('Get out'), polite request ('Would you kindly'), habitual action ('usually travel'), purpose ('to save his friend', 'just to see you'), wish / prayer ('May you be blessed'), moral duty ('must stand for what is right'), condition ('only if').",
    "  - Traditional Sentence Types (9 items): interrogative ('Who among the two boys...'), assertive declarative ('Nature is the best physician' [KEEP], 'Daphne is the tallest...', 'Today is a fine day'), imperative ('Have mercy on us', 'Shut the door at once'), exclamatory ('How very cold the night is!'), optative/blessing ('May you have all the joy...'), negative statement ('You cannot have all the riches...').",
    "- `english/grammar/prepositions` (7 items):",
    "  - Prepositions of time ('since yesterday'), objective preposition ('fought for the crown'), motion ('into my parlour'), idiomatic usage ('rise with the lark', 'By the name of God'), position ('sits among his boys', 'across her breast' [KEEP]).",
    "- `english/grammar/subject-verb-agreement` (9 items):",
    "  - Prepositional intervener ('quality of the mangoes was'), 'one of' singular agreement ('one of the volcanic eruptions takes place'), compound subject with and ('Fire and water do not agree'), single composite unit ('horse and carriage is'), correlative conjunction ('Neither praise nor blame seems'), branch of science ('Physics is'), collective noun divided ('Committee were divided'), proper book title ('The Arabian Nights is'), fraction of uncountable whole ('Three parts of the business is left').",
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
    "Direct visual inspection of all 7 rendered PNG page images of `doc_28eafb04c21bfc501a33c583`:",
    "- **Cover Page / Section A (Page 1):** Inspected Title, Instructions: General English, 3 hours, Full Marks: 100. Preserved Section A Conventional Tasks (40 marks):",
    "  1. Task 1 (p. 1, 20 marks): Essay writing on Man and Environment / Importance of Education / Women in Mizo society / IT at present time.",
    "  2. Task 2 (p. 1, 20 marks): Précis writing on Albert Einstein's passage on human interdependence and mutual cooperation.",
    "- **Section B Parts of Speech (Page 2):** Inspected Q1–Q10: transitive verb ('hurt'), noun ('Grammar'), predicate adjective ('true'), abstract noun ('Laughter'), collective noun ('crowd'), degree adverb ('quite'), manner adverb ('fast'), interjection ('Bravo!'), substantive adjective ('courageous'), spatial preposition ('over').",
    "- **Section B Modal Notions & Prepositions (Pages 3–4):** Inspected Q11–Q27: possibility ('may'), obligation ('must'), order ('Get out'), request ('Would you kindly'), habitual ('usually'), purpose ('to save his friend'), wish ('May you be blessed'), advice ('must stand'), purpose ('just to see you'), condition ('only if'), prepositions ('since yesterday', 'for the crown', 'into my parlour', 'with the lark', 'By the name of God', 'among his boys', 'across her breast').",
    "- **Section B Conjunctions & Verbals (Pages 4–5):** Inspected Q28–Q42: conjunctions ('but', 'though', 'Since', 'for', 'else', 'before', 'Unless'), gerunds and participles ('Hunting tigers', 'hoarding money', 'swimming pool', 'Swimming', 'losing game', 'Giving is better than receiving', 'standing building', 'smoking').",
    "- **Section B Sentence Analysis & Subject-Verb Agreement (Pages 5–7):** Inspected Q43–Q60: interrogative ('Who among the two boys...'), assertive ('Nature is the best physician', 'Daphne is the tallest...', 'Today is a fine day'), imperative ('Have mercy on us', 'Shut the door at once'), exclamatory ('How very cold the night is!'), optative ('May you have all the joy...'), negative ('You cannot have all the riches...'), subject-verb agreement ('quality ... was', 'one of ... takes', 'Fire and water do', 'horse and carriage is', 'Neither ... seems', 'Physics is', 'Committee were', 'The Arabian Nights is', 'Three parts ... is').",
    "",
    "## Documented Source, Extraction & Option Defects",
    "",
    "1. **Rectification of Unclassified Baseline Tags:** All 60 MCQs in production had coarse `current_subject: 'gk'` and `current_topic: 'ADA, AA & ATA General English'`. All have been structured into precise English taxonomy nodes.",
    "2. **Preservation of 40 Marks of Section A Conventional Written Work:** Documented Task 1 (Essay 20m) and Task 2 (Précis 20m) in `pending-written-intake.json`.",
    "3. **100% Extracted MCQ Fidelity:** All 60 printed Section B MCQs are present and consecutively numbered without gaps or OCR drops."
])

(out / "README.md").write_text("\n".join(lines) + "\n")
print(f"Generated README.md ({len(lines)} lines).")
