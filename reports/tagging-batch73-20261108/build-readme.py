"""Generate README.md for Batch 73."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
summary = json.load(open(out / "summary.json"))
validation = json.load(open(out / "validation.json"))

md = f"""# Tagging Batch 73: Technical Competitive Examinations for Senior Horticulture Demonstrator (April 2018) — General English

## Summary
- **Batch ID**: 73
- **Date**: 2026-11-08
- **Targets**: {summary['targets']} Appearances ({summary['unextracted_items_preserved']} conventional item preserved)
- **Completion**: {summary['completion']}
- **Live Changes**: {summary['live_changes']} (All {summary['targets']} candidates remain `pending`)
- **Actions**:
  - `retag`: {summary['actions']['retag']}
  - `keep`: {summary['actions']['keep']}
  - `hold`: {summary['actions']['hold']}
- **Verification**: {validation['source_fingerprints_verified']}/{summary['targets']} source fingerprints re-verified via repeatable-read Oracle readback ({validation['validated_at']}).

## Paper Details
- **Paper ID**: `Old_Questions/Direct_2014-2018/3.General English.pdf`
- **Document ID**: `doc_83296a794525fd6c34a58849`
- **Source SHA256**: `cd686973b1e79f802c33c1838962828c46709f1a4ffc53bdfe03d005c646f998`
- **Total Physical MCQs in Booklet**: 80 MCQs (Section B, 80 Marks)
- **Total Appearances in Database**: 109 Appearances (due to 29 legacy duplicate extractions across page boundaries)
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
2. **Q17–Q28**: Reading comprehension passage -> `english/comprehension` (12)
3. **Q29–Q34**: Prepositions -> `english/grammar/prepositions` (7 appearances including 1 duplicate)
4. **Q35–Q40**: Parts of speech identification -> `english/grammar/parts-of-speech` (12 appearances including 6 duplicates)
5. **Q41–Q48**: Verb forms and tenses -> `english/grammar/tenses` (10 appearances including 2 duplicates)
6. **Q49–Q53**: Sentence structure analysis (Compound, Complex, Simple) -> `english/grammar` (10 appearances including 5 duplicates)
7. **Q54–Q58**: Clause identification (Noun, Adjective, Adverb, Coordinate) -> `english/grammar` (10 appearances including 5 duplicates)
8. **Q59–Q64**: Sentence notion and concept -> `english/grammar` (12 appearances including 6 duplicates)
9. **Q65–Q72**: Usage of words / homophones -> `english/vocabulary` (12 appearances including 4 duplicates)
10. **Q73–Q80**: Synonyms / nearest in meaning -> `english/vocabulary/synonyms` (8)

## Conventional / Written Section Defect
- **Section A Q1 (Page 1)**: Essay writing on one of three topics (The value of sports and athletics / Environmental Pollution / Cleanliness is next to Godliness) for 20 Marks. Recorded in `pending-written-intake.json`.

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 109 candidates tagged under policy `study-tagging-v1`.
"""

(out / "README.md").write_text(md)
print("Wrote README.md successfully.")
