"""Generate README.md for Batch 115."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
summary = json.load(open(out / "summary.json"))
validation = json.load(open(out / "validation.json"))

md = f"""# Tagging Batch 115: Junior Inspector of Cooperative Societies (2019) — General English

## Summary
- **Batch ID**: 115
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
- **Paper ID**: `Old_Questions/Direct_2019-2020/General English (JICS).pdf`
- **Document ID**: `doc_1d71fe43336214be3919fcda`
- **Source SHA256**: `0bed10fd00d7e2f49557b6f6341d37b60060938361099f662f3277d3f00109b8`
- **Total Questions in Paper**: 1 Conventional Essay Question (Section A, 20 Marks) + 80 MCQs (Section B, 80 Marks; Q6 dropped in legacy OCR)
- **Subject Coverage**: General English (Idioms & Proverbs, Reading Comprehension, Parts of Speech, Prepositions, Sentence Structure & Notions, Vocabulary Definitions, Homophones, Commonly Confused Words)

## Topic Breakdown
| Topic / Subtopic | Count |
| :--- | :--- |
"""

for topic, count in sorted(summary['breakdown'].items(), key=lambda x: -x[1]):
    md += f"| `{topic}` | {count} |\n"

md += """
## Section Breakdown
1. **Section A (Conventional, 20 Marks)**: Essay writing on Recycling / Mizo Language / Rainy Day -> documented in `pending-written-intake.json`.
2. **Q1–Q16 (excl. dropped Q6)**: Idioms and phrases:
   - Q1–Q5, Q7–Q8: Idiom meaning -> `english/vocabulary/idioms-and-phrases` (7)
   - Q9–Q16: Idioms fill in blanks -> `english/vocabulary/idioms-and-phrases` (8)
3. **Q17–Q28**: Reading comprehension passages (Passage 1: Q17–Q20; Passage 2: Q21–Q24; Passage 3: Q25–Q28) -> `english/comprehension` (12)
4. **Q29–Q40**: Form of nouns, verbs, adjectives, and adverbs -> `english/grammar/parts-of-speech` (12)
5. **Q41–Q48**: Prepositions in context -> `english/grammar/prepositions` (8)
6. **Q49–Q59**: Sentence structure analysis (simple, compound, complex), sentence types, and communicative notions -> `english/grammar` (11)
7. **Q60–Q64**: Word choice and idiomatic expressions:
   - Q60, Q61, Q64: Vocabulary in context (quiet, confident, waste) -> `english/vocabulary` (3)
   - Q62, Q63: Idiomatic phrases (in black and white, for good) -> `english/vocabulary/idioms-and-phrases` (2)
8. **Q65–Q70**: Homophones and proverbs:
   - Q65–Q68: Homophones / commonly confused words (effected/affected, principal/principle, soar/sore, raised/razed) -> `english/vocabulary` (4)
   - Q69–Q70: Proverb completions (Absence makes heart grow fonder / Home is where heart is) -> `english/vocabulary/idioms-and-phrases` (2)
9. **Q71–Q75**: Word definitions (pedantic, archaic, brine, thwart, tithe) -> `english/vocabulary` (5)
10. **Q76–Q80**: Commonly confused word pairs (human/humane, angel/angle, tampered/tempered, childish/childlike, lightning/lengthening) -> `english/vocabulary` (5)

## Defect Documentation
- **Q6 Legacy OCR Drop**: Short idiom question "6. To drive home (a) to find one’s root (b) to return to place to rest (c) back to original position (d) to emphasise" on physical page 2 was dropped during initial OCR database extraction. Documented in `findings.json` and `pending-written-intake.json`.

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 79 candidate records staged under policy `study-tagging-v1`.
- Complete verification against 8 rendered page images from source PDF.
"""

(out / "README.md").write_text(md)
print("Wrote README.md successfully.")
