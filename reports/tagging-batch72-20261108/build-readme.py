"""Generate README.md for Batch 72."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
summary = json.load(open(out / "summary.json"))
validation = json.load(open(out / "validation.json"))

md = f"""# Tagging Batch 72: Technical Competitive Examinations for Grade-V of Mizoram Horticulture Service (November 2017) — General English Paper - II

## Summary
- **Batch ID**: 72
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
- **Paper ID**: `Old_Questions/Direct_2014-2018/General English paper-II (MHS).pdf`
- **Document ID**: `doc_bbd4602370e71a495e7d027b`
- **Source SHA256**: `3c06fc1ef3650753af81984338b62a8274cf5c1d17c27729c09fb9ee12831c70`
- **Total Questions in Paper**: 100 MCQs

## Topic Breakdown
| Topic / Subtopic | Count |
| :--- | :--- |
"""

for topic, count in sorted(summary['breakdown'].items(), key=lambda x: -x[1]):
    md += f"| `{topic}` | {count} |\n"

md += """
## Section Breakdown
1. **Q1–Q8**: Parts of speech identification (underlined words) -> `english/grammar/parts-of-speech` (8)
2. **Q9–Q13**: Semantic meaning of adverbs and statements -> `english/vocabulary` (5)
3. **Q14–Q23**: Notion and concept expressed by sentence -> `english/grammar` (10)
4. **Q24, Q25, Q28–Q30**: Verb forms and conditionals -> `english/grammar/tenses` (5)
5. **Q26, Q27, Q31–Q40**: Preposition selection -> `english/grammar/prepositions` (12)
6. **Q41–Q50**: Phrasal verbs -> `english/vocabulary/idioms-and-phrases` (10)
7. **Q51–Q60**: Sentence structure analysis (Simple, Complex, Compound) -> `english/grammar` (10)
8. **Q61–Q70**: Clause identification (noun, adverb, adjective, coordinate) -> `english/grammar` (10)
9. **Q71–Q80**: Sentence functional classification (Declarative, Imperative, Interrogative, Exclamatory) -> `english/grammar` (10)
10. **Q81–Q90**: Vocabulary / sentence completion -> `english/vocabulary` (10)
11. **Q91–Q100**: One-word substitution -> `english/vocabulary/one-word-substitution` (10)

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 100 candidates tagged under policy `study-tagging-v1`.
"""

(out / "README.md").write_text(md)
print("Wrote README.md successfully.")
