"""Generate README.md for Batch 92."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
summary = json.load(open(out / "summary.json"))
validation = json.load(open(out / "validation.json"))

md = f"""# Tagging Batch 92: Employment Officer under LE&IT Deptt (2019) — General English Paper-II

## Summary
- **Batch ID**: 92
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
- **Paper ID**: `Old_Questions/Direct_2019-2020/Employment Officer under LE&IT Deptt Gen English Paper-II.pdf`
- **Document ID**: `doc_400ac277d6d2656e9c6ca280`
- **Source SHA256**: `85a0297c01d54690922b247b4986513c603f509cf0b60d5f9aa0dba6f8cba2cd`
- **Total Questions in Paper**: 100 MCQs (100 Marks, 2 Hours duration)
- **Subject Coverage**: General English (Grammar, Prepositions, Tenses, Sentence Types, Comparison, Phrases, Clauses, Notions, Idioms, Synonyms, Antonyms, Vocabulary)

## Topic Breakdown
| Topic / Subtopic | Count |
| :--- | :--- |
"""

for topic, count in sorted(summary['breakdown'].items(), key=lambda x: -x[1]):
    md += f"| `{topic}` | {count} |\n"

md += """
## Section Breakdown
1. **Q1–Q10**: Parts of speech identification (verb, noun, adjective, adverb, conjunction, pronoun, interjection) -> `english/grammar` (10)
2. **Q11–Q15**: Preposition selection in context (behind, in, in, into, to) -> `english/grammar/prepositions` (5)
3. **Q16–Q20**: Conjunctions and sentence connectors -> `english/grammar` (5)
4. **Q21–Q30**: Verb forms and tenses (present, continuous, past, perfect, future) -> `english/grammar/tenses` (10)
5. **Q31–Q35**: Determiners and pronouns -> `english/grammar` (5)
6. **Q36–Q40**: Articles and determiners -> `english/grammar` (5)
7. **Q41–Q48**: Sentence structure analysis (simple, compound, complex, compound-complex) -> `english/grammar` (8)
8. **Q49–Q56**: Degrees of comparison (positive, comparative, superlative) -> `english/grammar` (8)
9. **Q57–Q61**: Phrase classification (noun, prepositional, adverbial, adjective phrase) -> `english/grammar` (5)
10. **Q62–Q65**: Clause classification (noun clause, adjective clause, adverb clause) -> `english/grammar` (4)
11. **Q66–Q70**: Sentence notions and communicative concepts (habitual, suggestion, certainty, command, ability) -> `english/grammar` (5)
12. **Q71–Q80**: Idioms and phrases meaning and usage -> `english/vocabulary/idioms-and-phrases` (10)
13. **Q81–Q86**: Synonyms / closest meaning -> `english/vocabulary/synonyms` (6)
14. **Q87–Q94**: Antonyms / opposite meaning -> `english/vocabulary/antonyms` (8)
15. **Q95–Q100**: Word choice and vocabulary fill in the blanks -> `english/vocabulary` (6)

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 100 candidate records staged under policy `study-tagging-v1`.
- Complete verification against 8 rendered page images from source PDF.
"""

(out / "README.md").write_text(md)
print("Wrote README.md successfully.")
