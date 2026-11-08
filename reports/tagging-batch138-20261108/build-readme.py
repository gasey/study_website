"""Generate README.md for Batch 138."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
summary = json.load(open(out / "summary.json"))
validation = json.load(open(out / "validation.json"))

md = f"""# Tagging Batch 138: UDC under Fisheries Department (April 2021) — Paper-I

## Summary
- **Batch ID**: 138
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
- **Paper ID**: `Old_Questions/Direct_2021-2022/UDC Direct under Fisheries Deptt - Paper-I.pdf`
- **Document ID**: `{summary['papers'][0]['document_id']}`
- **Source SHA256**: `{summary['papers'][0]['sha256']}`
- **Total Marks in Paper**: 125 Marks (Section A: 50 Marks Conventional + Section B: 75 Marks MCQs)
- **Subject Coverage**: General English (Prepositions, Tenses, Voice, Parts of Speech, Idioms & Phrases, One-Word Substitution, Antonyms, Sentence Analysis, Clauses, Transformations)

## Topic Breakdown
| Topic / Subtopic | Count |
| :--- | :--- |
"""

for topic, count in sorted(summary['breakdown'].items(), key=lambda x: -x[1]):
    md += f"| `{topic}` | {count} |\n"

md += """
## Section Breakdown
1. **SECTION - A Conventional Written Section (50 Marks preserved in `pending-written-intake.json`)**:
   - **Question 1 (25 marks)**: Précis Writing on modern boredom, employee motivation, and diversifying interests/service -> `english/writing/precis`.
   - **Question 2 (25 marks)**: Essay Writing in ~500 words on Environment vs Growth / Discipline in Life / Women Empowerment -> `english/writing/essay`.

2. **SECTION - B Objective MCQ Section (75 Marks, 75 MCQs)**:
   - **Q1–Q8**: Prepositions and prepositional collocations -> `english/grammar/prepositions` (8)
   - **Q9–Q14**: Tenses and verb forms -> `english/grammar/tenses` (6)
   - **Q15–Q19**: Active and Passive Voice -> `english/grammar/voice` (5)
   - **Q20–Q25**: Parts of speech identification -> `english/grammar/parts-of-speech` (6)
   - **Q26–Q33**: Idioms and phrases -> `english/vocabulary/idioms-and-phrases` (8)
   - **Q34–Q40**: One-word substitution -> `english/vocabulary/one-word-substitution` (7)
   - **Q41–Q45**: Antonyms -> `english/vocabulary/antonyms` (5)
   - **Q46–Q50**: Sentence completion & usage -> `english/grammar` (5)
   - **Q51–Q56**: Sentence structure analysis (simple, compound, complex) -> `english/grammar` (6)
   - **Q57–Q62**: Subordinate clause analysis (noun, adjective, adverb) -> `english/grammar` (6)
   - **Q63–Q75**: Sentence transformation (participles, simple/complex/compound, direct/indirect) -> `english/grammar` (13)

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 75 candidate records staged under policy `study-tagging-v1`.
- Complete verification against 8 rendered page images from source PDF.
"""

(out / "README.md").write_text(md)
print("Wrote README.md successfully.")
