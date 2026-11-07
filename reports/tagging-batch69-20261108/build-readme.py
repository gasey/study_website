"""Generate README.md for Batch 69."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
summary = json.load(open(out / "summary.json"))
validation = json.load(open(out / "validation.json"))

md = f"""# Tagging Batch 69: Competitive Examinations for Recruitment to Fishery Extension Officer (December 2017) — General English Paper II

## Summary
- **Batch ID**: 69
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
- **Paper ID**: `Old_Questions/Direct_2014-2018/2.General English Paper-II.pdf`
- **Document ID**: `doc_c634c07280fb2818a0383368`
- **Source SHA256**: `f39d66ec194bbd64918208fa0084f91337a4a55fadb62994c59865dd43820fd3`
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
2. **Q11–Q20**: Correct form of verbs / tense selection -> `english/grammar/tenses` (10)
3. **Q21–Q22**: Determiners and quantifiers -> `english/grammar/parts-of-speech` (2)
4. **Q23–Q25**: Articles (a/an/the) -> `english/grammar/articles` (3)
5. **Q26–Q30**: Prepositions -> `english/grammar/prepositions` (5)
6. **Q31–Q35**: Adjectives and adverbs -> `english/grammar/parts-of-speech` (5)
7. **Q36–Q40**: Name the tense of the verb -> `english/grammar/tenses` (5)
8. **Q41–Q50**: Sentence transformation (Simple, Compound, Complex) -> `english/grammar` (10)
9. **Q51–Q55**: Sentence transformation (affirmative/negative, degrees, exclamatory/assertive) -> `english/grammar` (5)
10. **Q56–Q60**: Interchanging parts of speech -> `english/grammar` (5)
11. **Q61–Q65**: Sentence transformation (affirmative, negative, interrogative) -> `english/grammar` (5)
12. **Q66–Q70**: Sentence synthesis using clauses (noun, adjective, adverbial) -> `english/grammar` (5)
13. **Q71–Q75**: Antonyms -> `english/vocabulary/antonyms` (5)
14. **Q76–Q80**: Synonyms -> `english/vocabulary/synonyms` (5)
15. **Q81–Q90**: Idioms and phrases -> `english/vocabulary/idioms-and-phrases` (10)
16. **Q91–Q100**: One-word substitution -> `english/vocabulary/one-word-substitution` (10)

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 100 candidates tagged under policy `study-tagging-v1`.
"""

(out / "README.md").write_text(md)
print("Wrote README.md successfully.")
