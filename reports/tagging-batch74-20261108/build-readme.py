"""Generate README.md for Batch 74."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
summary = json.load(open(out / "summary.json"))
validation = json.load(open(out / "validation.json"))

md = f"""# Tagging Batch 74: General Competitive Examinations for Middle & Primary School Teacher (July 2015) — General English

## Summary
- **Batch ID**: 74
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
- **Paper ID**: `Old_Questions/Direct_2014-2018/1.Middle & Primary School Teacher 2015 General English.pdf`
- **Document ID**: `doc_73d36df5c68f5a69c05bd094`
- **Source SHA256**: `16f3dc314a198ff2efc0cdfd90c620a339e7467dec80eafe2e84f93dbb02cd19`
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
1. **Q1–Q16**: Idioms and phrases (meaning and fill-in) -> `english/vocabulary/idioms-and-phrases` (16)
2. **Q17–Q32**: Reading comprehension passages (Passage 1: Q17–Q22, Passage 2: Q23–Q27, Passage 3: Q28–Q32) -> `english/comprehension` (16)
3. **Q33–Q40**: Form of nouns, verbs, adjectives, adverbs -> `english/grammar/parts-of-speech` (8)
4. **Q41–Q48**: Prepositions -> `english/grammar/prepositions` (8)
5. **Q49–Q56**: Voice identification (Active Voice / Passive Voice) -> `english/grammar/voice` (8)
6. **Q57–Q65**: Sentence structure (Simple, Compound, Complex) -> `english/grammar` (9)
7. **Q66–Q70**: Speech and dialogue terms / vocabulary -> `english/vocabulary` (5)
8. **Q71–Q75**: Sentence completion -> `english/vocabulary` (5)
9. **Q76–Q80**: Word derivation / vocabulary -> `english/vocabulary` (5)

## Conventional / Written Section Defect
- **Section A Q1 (Page 1)**: Essay writing on one of three topics (Population Problem in India / Development of Tourism in Mizoram / Dignity of Labour) for 20 Marks. Recorded in `pending-written-intake.json`.

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 80 candidates tagged under policy `study-tagging-v1`.
"""

(out / "README.md").write_text(md)
print("Wrote README.md successfully.")
