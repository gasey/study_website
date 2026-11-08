"""Generate README.md for Batch 100."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
summary = json.load(open(out / "summary.json"))
validation = json.load(open(out / "validation.json"))

md = f"""# Tagging Batch 100: Geologist Junior (2019) — General English Paper-II

## Summary
- **Batch ID**: 100
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
- **Paper ID**: `Old_Questions/Direct_2019-2020/Geologist Junior General English Paper-II.pdf`
- **Document ID**: `doc_513e7d40a192db657479c727`
- **Source SHA256**: `3029dc62b718f75c7561667b8fa7671cbfe183f0353725e8dc921d06980e4bef`
- **Total Questions in Paper**: 100 MCQs (100 Marks, 2 Hours duration)
- **Subject Coverage**: General English (Functional Parts of Speech, Pronouns, Conjunctions, Prepositions, Tenses & Verb Forms, Sentence Transformations, Sentence Types Analysis, Sentence Synthesis, Clauses, Collocations, Synonyms, Antonyms, Idioms and Phrases, Homophones)

## Topic Breakdown
| Topic / Subtopic | Count |
| :--- | :--- |
"""

for topic, count in sorted(summary['breakdown'].items(), key=lambda x: -x[1]):
    md += f"| `{topic}` | {count} |\n"

md += """
## Section Breakdown
1. **Q1–Q10**: Functional parts of speech identification (over, dense, hastily, repeat, little, under, upon, before, around, throughout) -> `english/grammar` (10)
2. **Q11–Q20**: Pronouns identification & usage (whom, who, whose, which, that, each other, one another) -> `english/grammar` (10)
3. **Q21–Q30**: Conjunctions in context (than, although, because, unless, since, so that, whereas, yet) -> `english/grammar` (10)
4. **Q31–Q35**: Prepositions in context (on a diet, off the bridge, opposite, onto, across) -> `english/grammar/prepositions` (5)
5. **Q36–Q45**: Verb forms, tenses, and adverbs (have been waiting, died, reading, stir, working, fought, runs, stronger, quickly, admire) -> `english/grammar/tenses` (6), `english/grammar` (4)
6. **Q46–Q51**: Sentence transformation and connector integration -> `english/grammar` (6)
7. **Q52–Q56**: Sentence types analysis (Simple, Complex, Compound) -> `english/grammar` (5)
8. **Q57–Q61**: Sentence synthesis and clause combination -> `english/grammar` (5)
9. **Q62–Q66**: Clause analysis (Noun clause, Adverb clause, Adjective clause) -> `english/grammar` (5)
10. **Q67–Q71**: Lexical collocations in context (warm welcome, fatally wounded, urban legend, controversy surrounding, valuable asset) -> `english/vocabulary` (5)
11. **Q72–Q76**: Synonyms / closest meaning (writer, ask, coarse, ancient, amends) -> `english/vocabulary/synonyms` (5)
12. **Q77–Q86**: Antonyms / opposite meaning (arrogant, blunt, sparse, rigid, expand, arrive, jubilant, moderate, gargantuan, hastily) -> `english/vocabulary/antonyms` (10)
13. **Q87–Q96**: Idioms and idiomatic expressions (rank and file, at daggers drawn, cry for the moon, take to heels, in high spirits, house of cards, kick the bucket, close fisted, cock sure, cut and dried) -> `english/vocabulary/idioms-and-phrases` (10)
14. **Q97–Q100**: Sequence of tenses, passive verb, and homophones (arrive, rejected, principles, bored) -> `english/grammar/tenses` (1), `english/grammar` (1), `english/vocabulary` (2)

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 100 candidate records staged under policy `study-tagging-v1`.
- Complete verification against 8 rendered page images from source PDF.
"""

(out / "README.md").write_text(md)
print("Wrote README.md successfully.")
