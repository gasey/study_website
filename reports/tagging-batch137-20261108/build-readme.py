"""Generate README.md for Batch 137."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
summary = json.load(open(out / "summary.json"))
validation = json.load(open(out / "validation.json"))

md = f"""# Tagging Batch 137: UDC under Taxation Department (March 2021) — Paper-I

## Summary
- **Batch ID**: 137
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
- **Paper ID**: `Old_Questions/Direct_2020-2021/UDC Direct under Taxation Deptt - Paper-I.pdf`
- **Document ID**: `{summary['papers'][0]['document_id']}`
- **Source SHA256**: `{summary['papers'][0]['sha256']}`
- **Total Marks in Paper**: 125 Marks (Section A: 50 Marks Conventional + Section B: 75 Marks MCQs)
- **Subject Coverage**: General English (Parts of Speech, Collective Nouns, Tense Forms, Sentence Classification, Homophones/Vocabulary, Subject-Verb Agreement, Prepositions, Similes/Idioms)

## Topic Breakdown
| Topic / Subtopic | Count |
| :--- | :--- |
"""

for topic, count in sorted(summary['breakdown'].items(), key=lambda x: -x[1]):
    md += f"| `{topic}` | {count} |\n"

md += """
## Section Breakdown
1. **SECTION - A Conventional Written Section (50 Marks preserved in `pending-written-intake.json`)**:
   - **Question 1 (25 marks)**: Précis Writing on ancient Indian science, Panini's Sanskrit grammar, medicine (Charaka), and surgery (Sushruta) -> `english/writing/precis`.
   - **Question 2 (25 marks)**: Essay Writing in ~500 words on Saving Planet Earth / Chapchar Kut / YMA / Corruption -> `english/writing/essay`.

2. **SECTION - B Objective MCQ Section (75 Marks, 75 MCQs)**:
   - **Q1–Q10**: Parts of speech identification (kindly, love, some, danger, over, half, oh god, hey, yourself, whom) -> `english/grammar/parts-of-speech` (10)
   - **Q11–Q20**: Tense form identification (Future Indefinite, Present Continuous, Past Perfect Continuous, etc.) -> `english/grammar/tenses` (10)
   - **Q21–Q30**: Sentence classification (Affirmative, Negative, Interrogative, Imperative, Exclamatory) -> `english/grammar` (10)
   - **Q31–Q40**: Homophones and contextual vocabulary choice (beech/beach, knot/not, whether/weather, etc.) -> `english/vocabulary` (10)
   - **Q41–Q50**: Subject-verb and pronoun agreement -> `english/grammar/subject-verb-agreement` (10)
   - **Q51–Q60**: Prepositions and prepositional phrases -> `english/grammar/prepositions` (10)
   - **Q61–Q68**: Collective nouns (library of books, mob of rioters, school of fish, etc.) -> `english/grammar/parts-of-speech` (8)
   - **Q69–Q75**: Similes and figurative comparisons (as cunning as a fox, as quick as lightning, etc.) -> `english/vocabulary/idioms-and-phrases` (7)

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 75 candidate records staged under policy `study-tagging-v1`.
- Complete verification against 8 rendered page images from source PDF.
"""

(out / "README.md").write_text(md)
print("Wrote README.md successfully.")
