"""Generate README.md for Batch 110."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
summary = json.load(open(out / "summary.json"))
validation = json.load(open(out / "validation.json"))

md = f"""# Tagging Batch 110: Computer Operator under Election Deptt (2019) — General English

## Summary
- **Batch ID**: 110
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
- **Paper ID**: `Old_Questions/Direct_2019-2020/General English(Election).pdf`
- **Document ID**: `doc_8576449cb9ba5aa1982b5f25`
- **Source SHA256**: `d4b1b3ff73d273087be69d5fb38c3ee0d603a1d9426f53fc8e0ce9a0ff3bbbe6`
- **Total Questions in Paper**: 1 Conventional Essay Question (Section A, 20 Marks) + 80 MCQs (Section B, 80 Marks)
- **Subject Coverage**: General English (Idioms & Phrases, Reading Comprehension Passages, Parts of Speech, Sentence Structure Analysis, Clause Analysis, Grammatical Word Choice, Antonyms)

## Topic Breakdown
| Topic / Subtopic | Count |
| :--- | :--- |
"""

for topic, count in sorted(summary['breakdown'].items(), key=lambda x: -x[1]):
    md += f"| `{topic}` | {count} |\n"

md += """
## Section Breakdown
1. **Section A (Conventional, 20 Marks)**: Essay writing on Aung San Suu Kyi statement on democracy and negotiation of different views -> documented in `pending-written-intake.json`.
2. **Q1–Q16**: Idioms and phrases meaning (face the music, hand to mouth, sitting on fence, thick and thin, take exception, white elephant, spur of moment, Hobson's choice, snake in grass, etc.) -> `english/vocabulary/idioms-and-phrases` (16)
3. **Q17–Q32**: Reading comprehension passages:
   - Passage 1: Wildlife poaching and species extinction (Q17–Q22) -> `english/comprehension` (6)
   - Passage 2: Abraham Lincoln and emancipation of slavery (Q23–Q32) -> `english/comprehension` (10)
4. **Q33–Q48**: Functional parts of speech identification (any, before, his, after, yet, again, what, enough, place, that, round, above, till, on) -> `english/grammar/parts-of-speech` (16)
5. **Q49–Q56**: Sentence structure analysis (Simple, Compound, Complex) -> `english/grammar` (8)
6. **Q57–Q64**: Clause analysis (Noun clause, Adjective clause, Adverb clause) -> `english/grammar` (8)
7. **Q65–Q72**: Contextual grammar & concord:
   - Q65, Q69–Q72: Determiners, adjective forms, sensory verb complements, adverbs, and conditional conjunctions -> `english/grammar` (5)
   - Q66: Preposition with gerund complement (fond of playing) -> `english/grammar/prepositions` (1)
   - Q67–Q68: Subject-verb agreement concord (The cost of articles has risen / Neither food nor water was found) -> `english/grammar/subject-verb-agreement` (2)
8. **Q73–Q80**: Antonyms in context (vivacious, common, lethargic, enmity, frugal, relinquish, busy, perilous) -> `english/vocabulary/antonyms` (8)

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 80 candidate records staged under policy `study-tagging-v1`.
- Complete verification against 8 rendered page images from source PDF.
"""

(out / "README.md").write_text(md)
print("Wrote README.md successfully.")
