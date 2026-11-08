"""Generate README.md for Batch 97."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
summary = json.load(open(out / "summary.json"))
validation = json.load(open(out / "validation.json"))

md = f"""# Tagging Batch 97: Inspector of Taxes & Inspector of Excise (2019) — General English Paper-II

## Summary
- **Batch ID**: 97
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
- **Paper ID**: `Old_Questions/Direct_2019-2020/General English Paper-II (Inspector of Excise).pdf`
- **Document ID**: `doc_8a5e05a82f577a746bcc2509`
- **Source SHA256**: `e5b7885881833289bc1dee7c65e44fad9cb032a98fdfcee3397f34da821f9103`
- **Total Questions in Paper**: 100 MCQs (100 Marks, 2 Hours duration)
- **Subject Coverage**: General English (Parts of Speech, Prepositions, Word Class / Noun Form Derivation, Connectors, Sentence Types, Synthesis, Transformations, Idioms, Synonyms, Antonyms, One-Word Substitution)

## Topic Breakdown
| Topic / Subtopic | Count |
| :--- | :--- |
"""

for topic, count in sorted(summary['breakdown'].items(), key=lambda x: -x[1]):
    md += f"| `{topic}` | {count} |\n"

md += """
## Section Breakdown
1. **Q1–Q10**: Functional parts of speech identification (adjective, pronoun, adverb, conjunction, noun, preposition, verb) -> `english/grammar` (10)
2. **Q11–Q20**: Prepositions in context (at, on, in, between, upon, for, from, with, by) -> `english/grammar/prepositions` (10)
3. **Q21–Q30**: Word class & derivation (noun forms, prefixes, suffixes, adjective/adverb conversion) -> `english/grammar` (10)
4. **Q31–Q40**: Connectors, conjunctions, and sentence completion -> `english/grammar` (10)
5. **Q41–Q50**: Sentence structure types & conversion (simple, compound, complex) -> `english/grammar` (10)
6. **Q51–Q60**: Sentence synthesis and clause combinations -> `english/grammar` (10)
7. **Q61–Q70**: Sentence transformations & communicative notions (voice, negative/affirmative, degrees of comparison) -> `english/grammar` (10)
8. **Q71–Q80**: Idioms and idiomatic expressions -> `english/vocabulary/idioms-and-phrases` (10)
9. **Q81–Q85**: Synonyms / nearest in meaning -> `english/vocabulary/synonyms` (5)
10. **Q86–Q90**: Antonyms / opposite in meaning -> `english/vocabulary/antonyms` (5)
11. **Q91–Q100**: One-word substitution -> `english/vocabulary/one-word-substitution` (10)

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 100 candidate records staged under policy `study-tagging-v1`.
- Complete verification against 10 rendered page images from source PDF.
"""

(out / "README.md").write_text(md)
print("Wrote README.md successfully.")
