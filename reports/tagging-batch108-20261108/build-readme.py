"""Generate README.md for Batch 108."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
summary = json.load(open(out / "summary.json"))
validation = json.load(open(out / "validation.json"))

md = f"""# Tagging Batch 108: Librarian under H&FW Lunglei (2019) — General English

## Summary
- **Batch ID**: 108
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
- **Paper ID**: `Old_Questions/Direct_2019-2020/General English (Lib.-Lunglei).pdf`
- **Document ID**: `doc_a19e5d4cb2fc1385f9bc1ec3`
- **Source SHA256**: `0d8c1d3fbdd43fdfb03cbfa4a4d6f78810c950fc1b016259020468307ba892e6`
- **Total Questions in Paper**: 1 Conventional Essay Question (Section A, 20 Marks) + 80 MCQs (Section B, 80 Marks)
- **Subject Coverage**: General English (Parts of Speech, Tenses, Pronouns, Articles, Sentence Structure, Sentence Types & Notions, Idioms & Phrases, Word Choice in Context, Reading Comprehension Passages, Synonyms)

## Topic Breakdown
| Topic / Subtopic | Count |
| :--- | :--- |
"""

for topic, count in sorted(summary['breakdown'].items(), key=lambda x: -x[1]):
    md += f"| `{topic}` | {count} |\n"

md += """
## Section Breakdown
1. **Section A (Conventional, 20 Marks)**: Essay writing on Memorable Book / Aizawl a Better Place / Smart Phones in Student Life -> documented in `pending-written-intake.json`.
2. **Q1–Q10**: Parts of speech identification in context (preposition, adverb, conjunction, collective noun, indefinite pronoun, interjection, noun, adjective, adverb, conjunction) -> `english/grammar/parts-of-speech` (10)
3. **Q11–Q15**: Verb forms and tenses in context (drinks, have been playing, had caught, is growing, saw) -> `english/grammar/tenses` (5)
4. **Q16–Q20**: Pronoun selection in context (one's, whom, Each, what, that) -> `english/grammar/parts-of-speech` (5)
5. **Q21–Q25**: Article determination and zero article (elected chairman, a university, a white, an S.D.O., The English) -> `english/grammar/articles` (5)
6. **Q26–Q35**: Sentence structure analysis (Simple, Compound, Complex) -> `english/grammar` (10)
7. **Q36–Q40**: Sentence types and communicative notions (interrogative, declarative, assertive, imperative, request) -> `english/grammar` (5)
8. **Q41–Q56**: Idioms and idiomatic expressions (at sixes and sevens, wrong side of sixty, white feather, cross-purposes, for good, turned corner, blow own trumpet, piece of cake, under weather, sitting on fence, leave no stone unturned, etc.) -> `english/vocabulary/idioms-and-phrases` (16)
9. **Q57–Q62**: Word choice and vocabulary in context (fatally, accused, alienated, adequate, acquisition, common) -> `english/vocabulary` (6)
10. **Q63–Q74**: Reading comprehension passages (Passage 1: Information and knowledge, Q63–Q67; Passage 2: Science and religion, Q68–Q74) -> `english/comprehension` (12)
11. **Q75–Q80**: Synonyms in context (mitigate, empathy, monotonous, scrupulous, deteriorating, impromptu) -> `english/vocabulary/synonyms` (6)

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 80 candidate records staged under policy `study-tagging-v1`.
- Complete verification against 8 rendered page images from source PDF.
"""

(out / "README.md").write_text(md)
print("Wrote README.md successfully.")
