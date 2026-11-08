"""Generate README.md for Batch 104."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
summary = json.load(open(out / "summary.json"))
validation = json.load(open(out / "validation.json"))

md = f"""# Tagging Batch 104: District Organiser (March 2020) — General English

## Summary
- **Batch ID**: 104
- **Date**: 2026-11-08
- **Targets**: {summary['targets']} MCQs ({summary['unextracted_items_preserved']} conventional items preserved)
- **Completion**: {summary['completion']}
- **Live Changes**: {summary['live_changes']} (All {summary['targets']} candidates remain `pending`)
- **Actions**:
  - `retag`: {summary['actions']['retag']}
  - `keep`: {summary['actions']['keep']}
  - `hold`: {summary['actions']['hold']}
- **Verification**: {validation['source_fingerprints_verified']}/{summary['targets']} source fingerprints re-verified via repeatable-read Oracle readback ({validation['validated_at']}).

## Paper Details
- **Paper ID**: `Old_Questions/Direct_2019-2020/General English(DO, March).pdf`
- **Document ID**: `doc_cbc152761905acf953b683b6`
- **Source SHA256**: `bc1610c7b7238f7f185cacaa2d1ada237a04f8361ba54f2f8529761dafc09786`
- **Total Questions in Paper**: 80 MCQs (80 Marks, 2 Hours duration)
- **Subject Coverage**: General English (Idioms & Phrases, Reading Comprehension Passage, Antonyms, Functional Parts of Speech, Verb Tenses, Prepositions, Sentence Kinds Analysis, Sentence Types, Lexical Usage, Synonyms)

## Topic Breakdown
| Topic / Subtopic | Count |
| :--- | :--- |
"""

for topic, count in sorted(summary['breakdown'].items(), key=lambda x: -x[1]):
    md += f"| `{topic}` | {count} |\n"

md += """
## Section Breakdown
1. **Q1–Q16**: Idioms and idiomatic expressions (give a wide berth, flesh creep, rub wrong way, gets on nerves, high and dry, burn candle at both ends, speak volumes, etc.) -> `english/vocabulary/idioms-and-phrases` (16)
2. **Q17–Q23**: Reading comprehension passage on an extravagant man and money -> `english/comprehension` (7)
3. **Q24–Q28**: Antonyms / opposite meaning to words from passage (admired, extravagant, despised, careful, popularity) -> `english/vocabulary/antonyms` (5)
4. **Q29–Q36**: Functional parts of speech identification (still, off, round, better, but, etc.) -> `english/grammar` (8)
5. **Q37–Q42**: Verb tense selection and form completions in context (moves, has gone, went, had started, etc.) -> `english/grammar/tenses` (6)
6. **Q43–Q48**: Prepositions in context (on diet, by, in, into, etc.) -> `english/grammar/prepositions` (6)
7. **Q49–Q58**: Sentence kind analysis (Simple, Compound, Complex) -> `english/grammar` (10)
8. **Q59–Q64**: Sentence type identification (Affirmative, Negative, Interrogative, Exclamatory, Imperative, Assertive) -> `english/grammar` (6)
9. **Q65–Q74**: Lexical selection, similes, and phrasal verbs:
   - Q65, Q67, Q74: Similes, idioms, and phrasal verbs (firm as a rock, fair share, taken after) -> `english/vocabulary/idioms-and-phrases` (3)
   - Q66, Q68–Q73: Contextual vocabulary (scalded, dispersed, wince, exercise restraint, sumptuous, averted, neglected) -> `english/vocabulary` (7)
10. **Q75–Q80**: Synonyms / nearest in meaning to underlined words (vigilant, etc.) -> `english/vocabulary/synonyms` (6)

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 80 candidate records staged under policy `study-tagging-v1`.
- Complete verification against 8 rendered page images from source PDF.
"""

(out / "README.md").write_text(md)
print("Wrote README.md successfully.")
