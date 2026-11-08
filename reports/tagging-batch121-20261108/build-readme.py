"""Generate README.md for Batch 121."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
summary = json.load(open(out / "summary.json"))
validation = json.load(open(out / "validation.json"))

md = f"""# Tagging Batch 121: Employment Officer under LE&IT (2019) — General English Paper-II

## Summary
- **Batch ID**: 121
- **Date**: 2026-11-08
- **Targets**: {summary['targets']} MCQs ({summary['unextracted_items_preserved']} conventional items preserved, {summary['conventional_marks_preserved']} conventional marks)
- **Completion**: {summary['completion']}
- **Live Changes**: {summary['live_changes']} (All {summary['targets']} candidates remain `pending`)
- **Actions**:
  - `retag`: {summary['actions']['retag']}
  - `keep`: {summary['actions']['keep']}
  - `hold`: {summary['actions']['hold']}
- **Verification**: {validation['source_fingerprints_verified']}/{summary['targets']} source fingerprints re-verified via repeatable-read Oracle readback ({validation['validated_at']}).

## Paper Details
- **Paper ID**: `Old_Questions/Direct_2019-2020/General Englsih Paper-II (EO).pdf`
- **Document ID**: `{summary['papers'][0]['document_id']}`
- **Source SHA256**: `{summary['papers'][0]['sha256']}`
- **Total Marks in Paper**: 100 Marks (100 Objective MCQs, 1 mark each)
- **Subject Coverage**: General English (Parts of Speech, Prepositions, Conjunctions, Verb Tenses & Forms, Pronouns, Articles, Sentence Structure Analysis, Degrees of Comparison, Phrases, Clauses, Communicative Notions, Idioms & Phrases, Synonyms, Antonyms, Contextual Vocabulary)

## Topic Breakdown
| Topic / Subtopic | Count |
| :--- | :--- |
"""

for topic, count in sorted(summary['breakdown'].items(), key=lambda x: -x[1]):
    md += f"| `{topic}` | {count} |\n"

md += """
## Section Breakdown
1. **Q1–Q10**: Functional parts of speech identification (verb, noun, adjective, adverb, conjunction, pronoun, interjection) -> `english/grammar/parts-of-speech` (10)
2. **Q11–Q15**: Prepositions in context (behind, in, in, into, to) -> `english/grammar/prepositions` (5)
3. **Q16–Q20**: Conjunctions (but, neither, nevertheless, moreover, on the other hand) -> `english/grammar/parts-of-speech` (5)
4. **Q21–Q30**: Appropriate forms of verbs & tenses (has written, were, had left, was raining, will have completed, etc.) -> `english/grammar/tenses` (10)
5. **Q31–Q35**: Suitable pronouns (relative, reflexive, demonstrative, indefinite) -> `english/grammar/parts-of-speech` (5)
6. **Q36–Q40**: Definite, indefinite, and zero articles -> `english/grammar/articles` (5)
7. **Q41–Q48**: Sentence structure analysis (Simple, Compound, Complex) -> `english/grammar` (8)
8. **Q49–Q56**: Degrees of comparison (Positive, Comparative, Superlative) -> `english/grammar` (8)
9. **Q57–Q61**: Phrase structure identification (Adjective phrase, Noun phrase, Adverb phrase) -> `english/grammar` (5)
10. **Q62–Q65**: Clause analysis (Adverb clause, Adjective clause, Noun clause) -> `english/grammar` (4)
11. **Q66–Q70**: Communicative notions expressed by sentences (Supposition, Concession, Purpose, Condition, Result) -> `english/grammar` (5)
12. **Q71–Q80**: Idioms and idiomatic phrases meaning (gift of the gab, spill the beans, burn the midnight oil, dark horse, turn a deaf ear, etc.) -> `english/vocabulary/idioms-and-phrases` (10)
13. **Q81–Q86**: Synonyms / nearest in meaning (abundant, benevolent, frugal, obstinate, candid, transient) -> `english/vocabulary/synonyms` (6)
14. **Q87–Q94**: Antonyms / opposite in meaning (hostile, obscure, artificial, expand, genuine, rigid, despair, transparent) -> `english/vocabulary/antonyms` (8)
15. **Q95–Q100**: Contextual word choice and distinctions (discredit, renounced, rewarded, inevitable, erosion, unanimous) -> `english/vocabulary` (6)

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 100 candidate records staged under policy `study-tagging-v1`.
- Complete verification against 8 rendered page images from source PDF.
"""

(out / "README.md").write_text(md)
print("Wrote README.md successfully.")
