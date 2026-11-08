"""Generate README.md for Batch 114."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
summary = json.load(open(out / "summary.json"))
validation = json.load(open(out / "validation.json"))

md = f"""# Tagging Batch 114: Junior Engineer PHED (2019) — General English

## Summary
- **Batch ID**: 114
- **Date**: 2026-11-08
- **Targets**: {summary['targets']} MCQs ({summary['unextracted_items_preserved']} defects/items preserved)
- **Completion**: {summary['completion']}
- **Live Changes**: {summary['live_changes']} (All {summary['targets']} candidates remain `pending`)
- **Actions**:
  - `retag`: {summary['actions']['retag']}
  - `keep`: {summary['actions']['keep']}
  - `hold`: {summary['actions']['hold']}
- **Verification**: {validation['source_fingerprints_verified']}/{summary['targets']} source fingerprints re-verified via repeatable-read Oracle readback ({validation['validated_at']}).

## Paper Details
- **Paper ID**: `Old_Questions/Direct_2019-2020/General English (JE).pdf`
- **Document ID**: `doc_dd7ee5b1f64f43405f6399c0`
- **Source SHA256**: `a5b36688166e3545b73d2ff90df9857dff6599b45dbf620614e26cf81d589f89`
- **Total Questions in Paper**: 1 Conventional Essay Question (Section A, 20 Marks) + 79 MCQs (Section B, 79 Marks; Q26 omitted in printed booklet)
- **Subject Coverage**: General English (Idioms & Phrases, Reading Comprehension, Parts of Speech, Prepositions, Verb Tenses, Sentence Structure, Clauses, Communicative Notions, One-Word Substitution, Commonly Confused Words, Synonyms)

## Topic Breakdown
| Topic / Subtopic | Count |
| :--- | :--- |
"""

for topic, count in sorted(summary['breakdown'].items(), key=lambda x: -x[1]):
    md += f"| `{topic}` | {count} |\n"

md += """
## Section Breakdown
1. **Section A (Conventional, 20 Marks)**: Essay writing on Smartphone / New Aizawl City / Swachh Bharat Abhiyan -> documented in `pending-written-intake.json`.
2. **Q1–Q16**: Idioms and phrases meaning -> `english/vocabulary/idioms-and-phrases` (16)
3. **Q17–Q28 (excl. omitted Q26)**: Reading comprehension passages (Passage 1: Q17–Q20; Passage 2: Q21–Q25, Q27–Q28 on Mewar kingdom) -> `english/comprehension` (11)
4. **Q29–Q34**: Functional parts of speech identification (noun, pronoun, adjective, verb, adverb, preposition/conjunction) -> `english/grammar/parts-of-speech` (6)
5. **Q35–Q40**: Prepositions in context -> `english/grammar/prepositions` (6)
6. **Q41–Q48**: Verb tense forms in context -> `english/grammar/tenses` (8)
7. **Q49–Q53**: Sentence structure analysis (Simple, Compound, Complex) -> `english/grammar` (5)
8. **Q54–Q58**: Clause analysis (Noun clause, Adjective clause, Adverb clause, Coordinate clause) -> `english/grammar` (5)
9. **Q59–Q64**: Communicative functions and speech acts / notions -> `english/grammar` (6)
10. **Q65–Q72**: Vocabulary, one-word substitutions and commonly confused words:
    - Q65–Q67, Q71–Q72: One-word substitution (ambidextrous, anonymous, omnipotent, epitaph, polygamy) -> `english/vocabulary/one-word-substitution` (5)
    - Q68–Q70: Commonly confused words (adopt/adept, effect/affect, precede/proceed) -> `english/vocabulary` (3)
11. **Q73–Q80**: Synonyms in context (industrious, immaculate, puerility, judicious, arduous, insatiable, eventually, integrity) -> `english/vocabulary/synonyms` (8)

## Booklet Defect Documentation
- **Q26 Misprint**: In the official printed question paper, the numbering jumped directly from `25.` to `27.` on Physical Page 4. Question 26 was omitted by the exam paper setter. Fully documented in `findings.json` and `pending-written-intake.json`.

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 79 candidate records staged under policy `study-tagging-v1`.
- Complete verification against 8 rendered page images from source PDF.
"""

(out / "README.md").write_text(md)
print("Wrote README.md successfully.")
