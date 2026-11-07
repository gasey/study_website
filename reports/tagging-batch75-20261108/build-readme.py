"""Generate README.md for Batch 75."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
summary = json.load(open(out / "summary.json"))
validation = json.load(open(out / "validation.json"))

md = f"""# Tagging Batch 75: Technical Competitive Examinations for Junior Engineer (J.E) under PHE & PWD (April 2016) — General English

## Summary
- **Batch ID**: 75
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
- **Paper ID**: `Old_Questions/Direct_2014-2018/3. General English.pdf`
- **Document ID**: `doc_4c79cb3420629f238d2b19c8`
- **Source SHA256**: `4cfb27b08fcd62e6f37f34c4f1560a182b023880ec3325f790657a920b904776`
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
1. **Q1–Q16**: Idioms and phrases (fill-in and meaning) -> `english/vocabulary/idioms-and-phrases` (16)
2. **Q17–Q28**: Reading comprehension passages (Passage 1: Q17–Q22, Passage 2: Q23–Q28) -> `english/comprehension` (12)
3. **Q29–Q35**: Phrasal verbs -> `english/vocabulary/idioms-and-phrases` (7)
4. **Q36–Q42**: Adjectives, adverbs, and verbs -> `english/grammar/parts-of-speech` (7)
5. **Q43–Q48**: Parts of speech identification of underlined words -> `english/grammar/parts-of-speech` (6)
6. **Q49–Q54**: Clause identification (noun, adverb, adjective, independent) -> `english/grammar` (6)
7. **Q55–Q59**: Sentence structure (Simple, Complex, Compound) -> `english/grammar` (5)
8. **Q60–Q64**: Sentence functional classification (Declarative, Interrogative, Imperative, Exclamatory) -> `english/grammar` (5)
9. **Q65–Q70**: Synonyms -> `english/vocabulary/synonyms` (6)
10. **Q71–Q74**: Antonyms -> `english/vocabulary/antonyms` (4)
11. **Q75–Q77, Q79**: One-word substitution -> `english/vocabulary/one-word-substitution` (4)
12. **Q78, Q80**: Word usage / vocabulary -> `english/vocabulary` (2)

## Conventional / Written Section Defect
- **Section A Q1 (Page 1)**: Essay writing on one of three topics (Talent versus Hard work / Mass Media and Cultural Invasion / Youth Culture Today) for 20 Marks. Recorded in `pending-written-intake.json`.

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 80 candidates tagged under policy `study-tagging-v1`.
"""

(out / "README.md").write_text(md)
print("Wrote README.md successfully.")
