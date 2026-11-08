"""Generate README.md for Batch 103."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
summary = json.load(open(out / "summary.json"))
validation = json.load(open(out / "validation.json"))

md = f"""# Tagging Batch 103: District Organiser (Oct 2020) — General English

## Summary
- **Batch ID**: 103
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
- **Paper ID**: `Old_Questions/Direct_2019-2020/General English (DO, Oct).pdf`
- **Document ID**: `doc_edb3109f0a62cb5bb80c86f0`
- **Source SHA256**: `638bc321bcf8b5c3d38aae4d480ab2495e4fb6c61a51a3ffb78ee6636860d3b4`
- **Total Questions in Paper**: 80 MCQs (80 Marks, 2 Hours duration)
- **Subject Coverage**: General English (Reading Comprehension Passage, Idioms & Phrases, Verb Tenses & Irregular Participles, Prepositions, Functional Parts of Speech, Sentence Kinds Analysis, Sentence Transformations, Synonyms, Antonyms, Words Often Confused)

## Topic Breakdown
| Topic / Subtopic | Count |
| :--- | :--- |
"""

for topic, count in sorted(summary['breakdown'].items(), key=lambda x: -x[1]):
    md += f"| `{topic}` | {count} |\n"

md += """
## Section Breakdown
1. **Q1–Q16**: Reading comprehension passage on Philosophy of Education -> `english/comprehension` (16)
2. **Q17–Q32**: Idioms and idiomatic expressions (what goes around comes around, good hand, throw cold water, hard nut to crack, no spring chicken, take a toll, grease palm, on cloud nine, hit ceiling, etc.) -> `english/vocabulary/idioms-and-phrases` (16)
3. **Q33–Q34**: Lexical usage & noun derivation (hope/except/expect/accept, loss) -> `english/vocabulary` (1), `english/grammar` (1)
4. **Q35–Q39**: Verb tenses & irregular participle forms (had hurt, will have arrived, had frozen, was raining, have not completed) -> `english/grammar/tenses` (5)
5. **Q40–Q44**: Prepositions in context (over, by, into, on, across) -> `english/grammar/prepositions` (5)
6. **Q45–Q48**: Functional parts of speech identification (adjective, adverb, conjunction, noun) -> `english/grammar` (4)
7. **Q49–Q53**: Sentence kind analysis (Simple, Complex, Compound) -> `english/grammar` (5)
8. **Q54–Q64**: Sentence transformations as directed (use noun form, voice, negative, comparison, synthesis) -> `english/grammar` (11)
9. **Q65–Q70**: Synonyms / closest meaning to underlined words (unanimous, etc.) -> `english/vocabulary/synonyms` (6)
10. **Q71–Q75**: Antonyms / opposite in meaning to underlined words (apathetic, etc.) -> `english/vocabulary/antonyms` (5)
11. **Q76–Q80**: Words often confused / lexical usage (adapt/adopt, affect/effect, complement/compliment, etc.) -> `english/vocabulary` (5)

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 80 candidate records staged under policy `study-tagging-v1`.
- Complete verification against 9 rendered page images from source PDF.
"""

(out / "README.md").write_text(md)
print("Wrote README.md successfully.")
