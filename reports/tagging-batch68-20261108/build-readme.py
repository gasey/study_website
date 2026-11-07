"""Generate README.md for Batch 68."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
summary = json.load(open(out / "summary.json"))
validation = json.load(open(out / "validation.json"))

md = f"""# Tagging Batch 68: Technical Competitive Examinations for Child Development Project Officer (CDPO) under Social Welfare Department 2016 — General English Paper II (Common)

## Summary
- **Batch ID**: 68
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
- **Paper ID**: `Old_Questions/Direct_2014-2018/2.CDPO under Social Welfare Department 2016 General English Paper II Common.pdf`
- **Document ID**: `doc_44de83a1b9447347e93a07df`
- **Source SHA256**: `d025377b53766146d02a37782626e72cc0f484b0e144dce43943bb76e740c934`
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
2. **Q11–Q20**: Choose the appropriate preposition -> `english/grammar/prepositions` (10)
3. **Q21–Q30**: Fill in the blanks with appropriate forms of verbs -> `english/grammar/tenses` (10)
4. **Q31–Q35**: Fill in the blanks with suitable pronouns -> `english/grammar/parts-of-speech` (5)
5. **Q36–Q40**: Insert appropriate articles -> `english/grammar/articles` (5)
6. **Q41–Q48**: Analyze sentences (Simple, Compound, Complex) -> `english/grammar` (8)
7. **Q49–Q56**: Identify phrases (Noun, Adjective, Adverb, Prepositional) -> `english/grammar` (8)
8. **Q57–Q65**: Pick the correct clause (Noun, Adjective, Adverb) -> `english/grammar` (9)
9. **Q66–Q70**: Sentence notion and mood -> `english/grammar` (5)
10. **Q71–Q80**: Idioms and phrases -> `english/vocabulary/idioms-and-phrases` (10)
11. **Q81–Q86**: Synonyms / nearest in meaning -> `english/vocabulary/synonyms` (6)
12. **Q87–Q94**: Antonyms / opposite in meaning -> `english/vocabulary/antonyms` (8)
13. **Q95–Q100**: Vocabulary / sentence completion -> `english/vocabulary` (6)

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 100 candidates tagged under policy `study-tagging-v1`.
"""

(out / "README.md").write_text(md)
print("Wrote README.md successfully.")
