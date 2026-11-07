"""Generate README.md for Batch 77."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
summary = json.load(open(out / "summary.json"))
validation = json.load(open(out / "validation.json"))

md = f"""# Tagging Batch 77: General Competitive Examinations for Programmer under PHED (July 2018) — General English Paper I

## Summary
- **Batch ID**: 77
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
- **Paper ID**: `Old_Questions/Direct_2014-2018/1.General English Paper-I.pdf`
- **Document ID**: `doc_f65bdaf24aea5195f08880e8`
- **Source SHA256**: `d3cac5fa03c6944b09f4d5361b5b21d9b22e1e4d82f1923f8a7e08a2f4537376`
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
1. **Q1–Q8**: Reading comprehension passage -> `english/comprehension` (8)
2. **Q9–Q24**: Idiomatic phrases meaning -> `english/vocabulary/idioms-and-phrases` (16)
3. **Q25–Q32**: Antonyms -> `english/vocabulary/antonyms` (8)
4. **Q33–Q40**: Parts of speech identification -> `english/grammar/parts-of-speech` (8)
5. **Q41–Q48**: Prepositions -> `english/grammar/prepositions` (8)
6. **Q49–Q58**: Sentence structure (Simple, Compound, Complex) -> `english/grammar` (10)
7. **Q59–Q64**: Sentence type (Declarative, Imperative, Interrogative, Exclamatory) -> `english/grammar` (6)
8. **Q65–Q72**: Sentence completion / vocabulary -> `english/vocabulary` (8)
9. **Q73–Q80**: Synonyms -> `english/vocabulary/synonyms` (8)

## Conventional / Written Section Defect
- **Section A Q1 (Page 1)**: Essay writing on one of three topics (Freedom of the press / Skilling the youth of Mizoram / Conservation of natural resources) for 20 Marks. Recorded in `pending-written-intake.json`.

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 80 candidates tagged under policy `study-tagging-v1`.
"""

(out / "README.md").write_text(md)
print("Wrote README.md successfully.")
