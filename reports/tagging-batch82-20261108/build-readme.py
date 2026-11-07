"""Generate README.md for Batch 82."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
summary = json.load(open(out / "summary.json"))
validation = json.load(open(out / "validation.json"))

md = f"""# Tagging Batch 82: General Competitive Examinations for Recruitment to Junior Engineer (JE) Contract Basis — General English

## Summary
- **Batch ID**: 82
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
- **Paper ID**: `Old_Questions/Direct_2014-2018/9. General English.pdf`
- **Document ID**: `doc_9ca4c2a445e9a44ecb9c3f58`
- **Source SHA256**: `cd3ed237c62c91d18f972b20f04c0ec2e9e2b1ea7ebae008fcb063548981f429`
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
1. **Q1–Q16**: Idioms and phrases meaning -> `english/vocabulary/idioms-and-phrases` (16)
2. **Q17–Q32**: Reading comprehension passages (poverty and development) -> `english/comprehension` (16)
3. **Q33–Q38**: Prepositions -> `english/grammar/prepositions` (6)
4. **Q39–Q44**: Parts of speech identification -> `english/grammar/parts-of-speech` (6)
5. **Q45–Q48**: Verb form and tenses -> `english/grammar/tenses` (4)
6. **Q49–Q53**: Sentence structure classification (Simple, Compound, Complex) -> `english/grammar` (5)
7. **Q54–Q58**: Clause identification (Noun, Adverb, Adjective, Coordinate clause) -> `english/grammar` (5)
8. **Q59–Q64**: Sentence functional classification (Imperative, Exclamatory, Assertive, Affirmative, Negative) -> `english/grammar` (6)
9. **Q65–Q72**: Vocabulary / word usage / commonly confused words -> `english/vocabulary` (8)
10. **Q73–Q80**: Synonyms (nearest in meaning to underlined words) -> `english/vocabulary/synonyms` (8)

## Conventional / Written Section Defect
- **Section A Q1 (Page 1)**: Essay writing on one of three topics (Child labour in India / Life in a big city / Use and abuse of social media) in not more than 300 words for 20 Marks. Recorded in `pending-written-intake.json`.

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 80 candidates tagged under policy `study-tagging-v1`.
"""

(out / "README.md").write_text(md)
print("Wrote README.md successfully.")
