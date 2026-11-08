"""Generate README.md for Batch 107."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
summary = json.load(open(out / "summary.json"))
validation = json.load(open(out / "validation.json"))

md = f"""# Tagging Batch 107: Laboratory Assistant under Commerce & Industries (2019) — General English

## Summary
- **Batch ID**: 107
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
- **Paper ID**: `Old_Questions/Direct_2019-2020/General English (LA).pdf`
- **Document ID**: `doc_806b72a6a12be40f7b0f0a59`
- **Source SHA256**: `463c437db96e7b85dc629dfbafe1eb6280b271d5336f3c552089f257a3e782a5`
- **Total Questions in Paper**: 1 Conventional Essay Question (Section A, 20 Marks) + 80 MCQs (Section B, 80 Marks)
- **Subject Coverage**: General English (Parts of Speech, Communicative Concepts & Notions, Prepositions, Reading Comprehension Passages, Sentence Structure Analysis, Subject-Verb Agreement Concord, Sentence Types, Idioms & Phrases)

## Topic Breakdown
| Topic / Subtopic | Count |
| :--- | :--- |
"""

for topic, count in sorted(summary['breakdown'].items(), key=lambda x: -x[1]):
    md += f"| `{topic}` | {count} |\n"

md += """
## Section Breakdown
1. **Section A (Conventional, 20 Marks)**: Essay writing on Science and benefits / Importance of Education / Health is Wealth -> documented in `pending-written-intake.json`.
2. **Q1–Q10**: Parts of speech identification in context (pronoun, proper adjective, distributive adjective, collective noun, proper noun, adverb, interjection, abstract noun, preposition) -> `english/grammar/parts-of-speech` (10)
3. **Q11–Q20**: Communicative concepts and notions (possibility, obligation, command, polite request, frequency, willingness, wish/prayer, purpose, condition) -> `english/grammar` (10)
4. **Q21–Q28**: Preposition usage (since, over, into, with, by, among, on, off) -> `english/grammar/prepositions` (8)
5. **Q29–Q39**: Reading comprehension passage (Jawaharlal Nehru's historic address 'Tryst with Destiny') -> `english/comprehension` (11)
6. **Q40–Q48**: Sentence structure analysis (Simple, Compound, Complex) -> `english/grammar` (9)
7. **Q49–Q57**: Subject-verb agreement concord (was/were, takes place, do not agree, is/are at door, seems/seem, singular subjects, collective nouns, titles, fractions) -> `english/grammar/subject-verb-agreement` (9)
8. **Q58–Q66**: Sentence types (interrogative, assertive/declarative, imperative, exclamatory, optative) -> `english/grammar` (9)
9. **Q67–Q80**: Idioms and idiomatic expressions (hands are full, put on the market, at a stretch, goes to heart, come to grief, bag and baggage, old head on young shoulders, when pigs fly, tried hand, put good face, moved heaven and earth, man of straw, man of words, wolf in sheep's clothing) -> `english/vocabulary/idioms-and-phrases` (14)

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 80 candidate records staged under policy `study-tagging-v1`.
- Complete verification against 8 rendered page images from source PDF.
"""

(out / "README.md").write_text(md)
print("Wrote README.md successfully.")
