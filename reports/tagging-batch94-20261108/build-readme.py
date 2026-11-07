"""Generate README.md for Batch 94."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
summary = json.load(open(out / "summary.json"))
validation = json.load(open(out / "validation.json"))

md = f"""# Tagging Batch 94: Tourist Officer under Tourism Deptt (2019) — General English Paper-II

## Summary
- **Batch ID**: 94
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
- **Paper ID**: `Old_Questions/Direct_2019-2020/T.O General English Paper-II.pdf`
- **Document ID**: `doc_91a4e2e762e15e99c2db9bc7`
- **Source SHA256**: `4f8b865c093b1c831caa7cdfb303e6c46de8db7b07f58d4ea8337a739d13fd4a`
- **Total Questions in Paper**: 100 MCQs (100 Marks, 2 Hours duration)
- **Subject Coverage**: General English (Parts of Speech, Tenses, Prepositions, Connectors, Adjectives & Determiners, Transformations, Sentence Types, Synthesis, Idioms, Synonyms, Antonyms, One-Word Substitution)

## Topic Breakdown
| Topic / Subtopic | Count |
| :--- | :--- |
"""

for topic, count in sorted(summary['breakdown'].items(), key=lambda x: -x[1]):
    md += f"| `{topic}` | {count} |\n"

md += """
## Section Breakdown
1. **Q1–Q10**: Functional parts of speech identification (pronoun, verb, noun, adjective, conjunction, numeral, adverb, preposition) -> `english/grammar` (10)
2. **Q11–Q20**: Verb forms, aspects, and tenses -> `english/grammar/tenses` (10)
3. **Q21–Q23, Q26, Q27, Q29**: Prepositions in context (across, over, by, with, into, among) -> `english/grammar/prepositions` (6)
4. **Q24, Q25, Q28, Q30**: Conjunctions and sentence connectors (yet, unless, lest, so that) -> `english/grammar` (4)
5. **Q31–Q40**: Adjectives, determiners, and adverbs (whole, gratefully, best, every, nearest, almost, too, apart, better, little) -> `english/grammar` (10)
6. **Q41–Q50**: Sentence transformations (interrogative, degree conversion, affirmative, negative, assertive, adverb form) -> `english/grammar` (10)
7. **Q51–Q60**: Sentence type conversions (simple, compound, complex) -> `english/grammar` (10)
8. **Q61–Q70**: Sentence synthesis and clause combining -> `english/grammar` (10)
9. **Q71–Q80**: Idioms and phrases meaning (call it a day, bent out of shape, break the ice, hold tongue, at drop of hat, piece of cake, throw caution to wind, well-off, pass over, take to heels) -> `english/vocabulary/idioms-and-phrases` (10)
10. **Q81–Q85**: Synonyms / closest meaning (sorrow, insolent, perpetual, yearn, contrary) -> `english/vocabulary/synonyms` (5)
11. **Q86–Q90**: Antonyms / opposite meaning (precede, magnify, confess, lenient, advance) -> `english/vocabulary/antonyms` (5)
12. **Q91–Q100**: One-word substitution (anarchy, edible, teetotaller, insatiable, obnoxious, indefatigable, posthumously, virtuoso, impregnable, nepotism) -> `english/vocabulary/one-word-substitution` (10)

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 100 candidate records staged under policy `study-tagging-v1`.
- Complete verification against 10 rendered page images from source PDF.
"""

(out / "README.md").write_text(md)
print("Wrote README.md successfully.")
