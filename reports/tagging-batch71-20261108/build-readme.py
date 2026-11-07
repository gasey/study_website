"""Generate README.md for Batch 71."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
summary = json.load(open(out / "summary.json"))
validation = json.load(open(out / "validation.json"))

md = f"""# Tagging Batch 71: Competitive Examinations for Recruitment to Inspector of Taxes (January 2016) — General English Paper II

## Summary
- **Batch ID**: 71
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
- **Paper ID**: `Old_Questions/Direct_2014-2018/2.Inspector of Taxes 2016 General English Paper II.pdf`
- **Document ID**: `doc_6311a1c087c7ee07ee8bb474`
- **Source SHA256**: `3edabb880e1e80444b92afde84387c637b3dd01398aafc71bd8a8053efeb6d1c`
- **Total Questions in Paper**: 100 MCQs

## Topic Breakdown
| Topic / Subtopic | Count |
| :--- | :--- |
"""

for topic, count in sorted(summary['breakdown'].items(), key=lambda x: -x[1]):
    md += f"| `{topic}` | {count} |\n"

md += """
## Section Breakdown
1. **Q1–Q10**: Name the Part of Speech of underlined words -> `english/grammar/parts-of-speech` (10)
2. **Q11–Q20**: Correct form of verbs / tense selection -> `english/grammar/tenses` (10)
3. **Q21–Q25**: Preposition selection -> `english/grammar/prepositions` (5)
4. **Q26, Q29, Q30**: Article and determiner selection -> `english/grammar/articles` (3)
5. **Q27, Q28**: Noun forms and quantifiers -> `english/grammar/parts-of-speech` (2)
6. **Q31–Q35**: Name the tense of the verb -> `english/grammar/tenses` (5)
7. **Q36–Q40**: Adjectives and adverbs -> `english/grammar/parts-of-speech` (5)
8. **Q41–Q45**: Degrees of comparison transformation -> `english/grammar` (5)
9. **Q46–Q50**: Sentence transformation (affirmative, negative, etc.) -> `english/grammar` (5)
10. **Q51–Q60**: Sentence conversion (Simple, Compound, Complex) -> `english/grammar` (10)
11. **Q61–Q70**: Sentence synthesis using clauses (noun, adjective, adverbial) -> `english/grammar` (10)
12. **Q71–Q80**: Idioms and phrases meaning -> `english/vocabulary/idioms-and-phrases` (10)
13. **Q81–Q90**: Synonyms -> `english/vocabulary/synonyms` (10)
14. **Q91–Q100**: One-word substitution -> `english/vocabulary/one-word-substitution` (10)

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 100 candidates tagged under policy `study-tagging-v1`.
"""

(out / "README.md").write_text(md)
print("Wrote README.md successfully.")
