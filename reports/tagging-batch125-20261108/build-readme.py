"""Generate README.md for Batch 125."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
summary = json.load(open(out / "summary.json"))
validation = json.load(open(out / "validation.json"))

md = f"""# Tagging Batch 125: MES (PHED) (2019) — General English

## Summary
- **Batch ID**: 125
- **Date**: 2026-11-08
- **Targets**: {summary['targets']} MCQs ({summary['unextracted_items_preserved']} conventional items preserved, {summary['conventional_marks_preserved']} conventional marks)
- **Completion**: {summary['completion']}
- **Live Changes**: {summary['live_changes']} (All {summary['targets']} candidates remain `pending`)
- **Actions**:
  - `retag`: {summary['actions']['retag']}
  - `keep`: {summary['actions']['keep']}
  - `hold`: {summary['actions']['hold']}
- **Verification**: {validation['source_fingerprints_verified']}/{summary['targets']} source fingerprints re-verified via repeatable-read Oracle readback ({validation['validated_at']}).

## Paper Details
- **Paper ID**: `Old_Questions/Direct_2019-2020/General English (PHE).pdf`
- **Document ID**: `{summary['papers'][0]['document_id']}`
- **Source SHA256**: `{summary['papers'][0]['sha256']}`
- **Total Marks in Paper**: 100 Marks (Questions 1–2: 35 Conventional Marks [Essay 20 Marks, Précis 15 Marks] + Questions 3–7: 65 Objective Marks [35 MCQs])
- **Subject Coverage**: General English (Synonyms, Antonyms, Idioms & Phrases, Prepositions, Verb Tenses, Contextual Vocabulary, Reading Comprehension Passage Analysis)

## Topic Breakdown
| Topic / Subtopic | Count |
| :--- | :--- |
"""

for topic, count in sorted(summary['breakdown'].items(), key=lambda x: -x[1]):
    md += f"| `{topic}` | {count} |\n"

md += """
## Section Breakdown
1. **Conventional Sections (Questions 1–2, 35 Marks)**:
   - Question 1: Essay composition on Human capital / Globalization / Religion and Politics (20 Marks) -> documented in `pending-written-intake.json`.
   - Question 2: Précis writing on money and duty of soldiers, doctors, clergymen (15 Marks) -> documented in `pending-written-intake.json`.
2. **Objective MCQs (Questions 3–7, 35 MCQs / 65 Marks)**:
   - **Q1–Q5 (Question 3)**: Synonyms / nearest in meaning (abominable, convivial, inhibit, candid, industrious) -> `english/vocabulary/synonyms` (5)
   - **Q6–Q10 (Question 4)**: Antonyms / opposite in meaning (bizarre, boon, frivolous, acquit, altruism) -> `english/vocabulary/antonyms` (5)
   - **Q11–Q15 (Question 5)**: Idioms and idiomatic phrases meaning (hand over fist, talk through one's hat, wet behind the ears, keep eyes peeled, hold your horses) -> `english/vocabulary/idioms-and-phrases` (5)
   - **Q16–Q25 (Question 6)**: Fill in the blanks with appropriate words:
     - Q16, Q17, Q19, Q21, Q22, Q23: Prepositions in context (sprang upon, devoted to, glanced at/through, comply with, intrude on, wonderful about) -> `english/grammar/prepositions` (6)
     - Q18: Verb aspect/tense (was having my bath) -> `english/grammar/tenses` (1)
     - Q20, Q24, Q25: Contextual word choice (eloquent, appropriate, showed) -> `english/vocabulary` (3)
   - **Q26–Q35 (Question 7)**: Reading comprehension passage on Indian agriculture, farmer distress, MSP, and APMC -> `english/comprehension` (10)

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 35 candidate records staged under policy `study-tagging-v1`.
- Complete verification against 5 rendered page images from source PDF.
"""

(out / "README.md").write_text(md)
print("Wrote README.md successfully.")
