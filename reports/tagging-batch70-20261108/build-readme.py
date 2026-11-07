"""Generate README.md for Batch 70."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
summary = json.load(open(out / "summary.json"))
validation = json.load(open(out / "validation.json"))

md = f"""# Tagging Batch 70: General Competitive Examinations (September 2018) — General English Paper - II

## Summary
- **Batch ID**: 70
- **Date**: 2026-11-08
- **Targets**: {summary['targets']} MCQs
- **Completion**: {summary['completion']}
- **Live Changes**: {summary['live_changes']} (All {summary['targets']} candidates remain `pending`)
- **Actions**:
  - `retag`: {summary['actions']['retag']}
  - `keep`: {summary['actions']['keep']}
  - `hold`: {summary['actions']['hold']}
- **Verification**: {validation['source_fingerprints_verified']}/{summary['targets']} source fingerprints re-verified via repeatable-read Oracle readback ({validation['validated_at']}).

## Paper Details
- **Paper ID**: `Old_Questions/Direct_2014-2018/2.General English-II.pdf`
- **Document ID**: `doc_f41a788556c2566c4c00da87`
- **Source SHA256**: `eca292bd3eabc70ae7e3aae4bb485f33a61327bc593fd77796045ca76687c5e0`
- **Total Questions in Paper**: 100 MCQs

## Topic Breakdown
| Topic / Subtopic | Count |
| :--- | :--- |
"""

for topic, count in sorted(summary['breakdown'].items(), key=lambda x: -x[1]):
    md += f"| `{topic}` | {count} |\n"

md += """
## Section Breakdown
1. **Q1–Q10**: Identify parts of speech of underlined words -> `english/grammar/parts-of-speech` (10)
2. **Q11–Q20**: Relative pronoun selection -> `english/grammar/parts-of-speech` (10)
3. **Q21–Q30**: Conjunction selection -> `english/grammar/parts-of-speech` (10)
4. **Q31–Q35**: Preposition selection -> `english/grammar/prepositions` (5)
5. **Q36–Q40**: Verb forms and tense selection -> `english/grammar/tenses` (5)
6. **Q41–Q50**: Sentence transformation (Simple, Compound, Complex) -> `english/grammar` (10)
7. **Q51–Q55**: Sentence / clause structure classification -> `english/grammar` (5)
8. **Q56–Q60**: Sentence synthesis as directed in brackets -> `english/grammar` (5)
9. **Q61–Q65**: Clause identification (adverb, noun, adjective, coordinate) -> `english/grammar` (5)
10. **Q66–Q70**: Collocation selection -> `english/vocabulary` (5)
11. **Q71–Q75**: Synonyms -> `english/vocabulary/synonyms` (5)
12. **Q76–Q80**: Antonyms -> `english/vocabulary/antonyms` (5)
13. **Q81–Q90**: Idioms and phrases -> `english/vocabulary/idioms-and-phrases` (10)
14. **Q91–Q100**: Homophones / vocabulary / correct alternative -> `english/vocabulary` (10)

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 100 candidates tagged under policy `study-tagging-v1`.
"""

(out / "README.md").write_text(md)
print("Wrote README.md successfully.")
