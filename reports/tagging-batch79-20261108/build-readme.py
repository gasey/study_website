"""Generate README.md for Batch 79."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
summary = json.load(open(out / "summary.json"))
validation = json.load(open(out / "validation.json"))

md = f"""# Tagging Batch 79: General Competitive Examinations for Various Posts under MIMER (February, 2018) — General English Common Paper

## Summary
- **Batch ID**: 79
- **Date**: 2026-11-08
- **Targets**: {summary['targets']} MCQs ({summary['unextracted_items_preserved']} conventional item preserved)
- **Completion**: {summary['completion']}
- **Live Changes**: {summary['live_changes']} (All {summary['targets']} candidates remain `pending`)
- **Actions**:
  - `retag`: {summary['actions']['retag']}
  - `keep`: {summary['actions']['keep']}
  - `hold`: {summary['actions']['hold']}
- **Verification**: {validation['source_fingerprints_verified']}/{summary['targets']} source fingerprints re-verified via repeatable-read Oracle readback ({validation['validated_at']}).

## Paper Details
- **Paper ID**: `Old_Questions/Direct_2014-2018/1.General English Common Paper.pdf`
- **Document ID**: `doc_6df8aa9179998188151c7268`
- **Source SHA256**: `0a1d4899c9e5413e110cf900b777a163483b87fe48d0a4c28f62f3a695e1e755`
- **Total Questions in Paper**: 80 MCQs (Section B, 80 Marks)
- **Conventional Section**: Section A Essay (20 Marks) on Page 1

## Topic Breakdown
| Topic / Subtopic | Count |
| :--- | :--- |
"""

for topic, count in sorted(summary['breakdown'].items(), key=lambda x: -x[1]):
    md += f"| `{topic}` | {count} |\n"

md += """
## Section Breakdown
1. **Q1–Q12**: Reading comprehension passages (cleanliness and health) -> `english/comprehension` (12)
2. **Q13–Q28**: Idioms and phrases (identification and meanings) -> `english/vocabulary/idioms-and-phrases` (16)
3. **Q29–Q37**: Parts of speech identification -> `english/grammar/parts-of-speech` (9)
4. **Q38–Q48**: Fill in the blanks:
   - **Q38–Q40**: Verb form and tenses -> `english/grammar/tenses` (3)
   - **Q41**: Subject-verb agreement (police agreement) -> `english/grammar/subject-verb-agreement` (1)
   - **Q42, Q43, Q47**: Preposition selection -> `english/grammar/prepositions` (3)
   - **Q44, Q45**: Distributive pronoun / determiner usage -> `english/grammar` (2)
   - **Q46**: Adverb selection -> `english/grammar/parts-of-speech` (1)
   - **Q48**: Conjunction selection -> `english/grammar` (1)
5. **Q49–Q58**: Sentence structure & types:
   - **Q49–Q52**: Sentence structure (Simple, Compound, Complex) -> `english/grammar` (4)
   - **Q53–Q58**: Sentence functional classification (Affirmative, Negative, Interrogative, Exclamatory, Imperative) -> `english/grammar` (6)
6. **Q59–Q64**: Synthesis of sentences -> `english/grammar` (6)
7. **Q65–Q72**: One word substitution -> `english/vocabulary/one-word-substitution` (8)
8. **Q73–Q80**: Usage:
   - **Q73–Q78**: Prepositional phrases / appropriate prepositions -> `english/grammar/prepositions` (6)
   - **Q79–Q80**: Tenses and mood -> `english/grammar/tenses` (2)

## Conventional / Written Section Defect
- **Section A Q1 (Page 1)**: Essay writing on one of three topics (Child labour in India / Life in a big city / Use and abuse of social media) not more than 300 words for 20 Marks. Recorded in `pending-written-intake.json`.

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 80 candidates tagged under policy `study-tagging-v1`.
"""

(out / "README.md").write_text(md)
print("Wrote README.md successfully.")
