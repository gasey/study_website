"""Generate README.md for Batch 95."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
summary = json.load(open(out / "summary.json"))
validation = json.load(open(out / "validation.json"))

md = f"""# Tagging Batch 95: Sericulture Extension Officer (2019) — General English Paper-II

## Summary
- **Batch ID**: 95
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
- **Paper ID**: `Old_Questions/Direct_2019-2020/SEO General English-II.pdf`
- **Document ID**: `doc_8b9654f42a144ef28a022335`
- **Source SHA256**: `1e9c74bdf10bd03b7dc250a5aaddbb974291091fd1b92ea763c34ce801ec9a87`
- **Total Questions in Paper**: 100 MCQs (100 Marks, 2 Hours duration)
- **Subject Coverage**: General English (Parts of Speech, Noun Classification, Prepositions, Adverb Types, Sentence Structures, Transformations, Clauses, Synonyms, Idioms & Phrases, Grammatical Completion)

## Topic Breakdown
| Topic / Subtopic | Count |
| :--- | :--- |
"""

for topic, count in sorted(summary['breakdown'].items(), key=lambda x: -x[1]):
    md += f"| `{topic}` | {count} |\n"

md += """
## Section Breakdown
1. **Q1–Q10**: Functional parts of speech identification (adverb, adjective, noun, pronoun, preposition, conjunction) -> `english/grammar` (10)
2. **Q11–Q20**: Noun classification (common, abstract, material, collective, proper, compound) -> `english/grammar` (10)
3. **Q21–Q31**: Prepositions in context -> `english/grammar/prepositions` (11)
4. **Q32–Q40**: Adverb classification by type (degree, frequency, manner, time, place) -> `english/grammar` (9)
5. **Q41–Q50**: Sentence structure classification (simple, compound, complex, compound-complex) -> `english/grammar` (10)
6. **Q51–Q60**: Sentence transformations (negative, interrogative, imperative, simple, compound) -> `english/grammar` (10)
7. **Q61–Q70**: Clause identification and classification (noun clause, adverb clause, adjective clause) -> `english/grammar` (10)
8. **Q71–Q80**: Synonyms / closest meaning (jealous, smart, essential, irrelevant, awful, interesting, new, weak, huge, excess) -> `english/vocabulary/synonyms` (10)
9. **Q81–Q90**: Idioms and idiomatic expressions (rank and file, under thumb, rain cats and dogs, cat on hot bricks, high spirits, bring to light, bolt from blue, cost arm and leg, daggers drawn, take to heels) -> `english/vocabulary/idioms-and-phrases` (10)
10. **Q91–Q100**: Grammatical sentence completion, auxiliary verbs, and determiners -> `english/grammar` (10)

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 100 candidate records staged under policy `study-tagging-v1`.
- Complete verification against 8 rendered page images from source PDF.
"""

(out / "README.md").write_text(md)
print("Wrote README.md successfully.")
