"""Generate README.md for Batch 136."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
summary = json.load(open(out / "summary.json"))
validation = json.load(open(out / "validation.json"))

md = f"""# Tagging Batch 136: UDC under ARCS Office, Cooperation Dept (January 2020) — Paper-I

## Summary
- **Batch ID**: 136
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
- **Paper ID**: `Old_Questions/Direct_2019-2020/UDC ARC Paper-I.pdf`
- **Document ID**: `{summary['papers'][0]['document_id']}`
- **Source SHA256**: `{summary['papers'][0]['sha256']}`
- **Total Marks in Paper**: 125 Marks (Section A: 50 Marks Conventional + Section B: 75 Marks MCQs)
- **Subject Coverage**: General English (Parts of Speech, Prepositions, Sentence Analysis, Subordinate Clauses, Word Choice & Vocabulary, One-Word Substitution, Sentence Improvement, Question Tags, Idioms & Phrases)

## Topic Breakdown
| Topic / Subtopic | Count |
| :--- | :--- |
"""

for topic, count in sorted(summary['breakdown'].items(), key=lambda x: -x[1]):
    md += f"| `{topic}` | {count} |\n"

md += """
## Section Breakdown
1. **SECTION - A Conventional Written Section (50 Marks preserved in `pending-written-intake.json`)**:
   - **Question 1 (25 marks)**: Essay Writing in ~500 words on solving the problem of educated unemployment -> `english/writing/essay`.
   - **Question 2 (25 marks)**: Précis Writing on the modern advertising industry, psychological tactics, brand rivalry, and consumer benefits -> `english/writing/precis`.

2. **SECTION - B Objective MCQ Section (75 Marks, 75 MCQs)**:
   - **Q1–Q9**: Parts of speech identification -> `english/grammar/parts-of-speech` (9)
   - **Q10–Q18**: Appropriate prepositions -> `english/grammar/prepositions` (9)
   - **Q19–Q27**: Sentence structure analysis (simple, compound, complex) -> `english/grammar` (9)
   - **Q28–Q35**: Subordinate clause analysis (noun, adjective, adverb clauses) -> `english/grammar` (8)
   - **Q36**: Phrasal verb (put in a brief appearance) -> `english/vocabulary/idioms-and-phrases` (1)
   - **Q37–Q43**: Contextual vocabulary & appropriate word choice -> `english/vocabulary` (7)
   - **Q44–Q51**: One-word substitution -> `english/vocabulary/one-word-substitution` (8)
   - **Q52–Q59**: Sentence improvement & error correction -> `english/grammar` (8)
   - **Q60–Q67**: Question tags -> `english/grammar` (8)
   - **Q68–Q75**: Idioms and phrases -> `english/vocabulary/idioms-and-phrases` (8)

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 75 candidate records staged under policy `study-tagging-v1`.
- Complete verification against 8 rendered page images from source PDF.
"""

(out / "README.md").write_text(md)
print("Wrote README.md successfully.")
