"""Generate README.md for Batch 111."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
summary = json.load(open(out / "summary.json"))
validation = json.load(open(out / "validation.json"))

md = f"""# Tagging Batch 111: Soil Conservation Ranger (2019) — General English

## Summary
- **Batch ID**: 111
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
- **Paper ID**: `Old_Questions/Direct_2019-2020/General English(SCR).pdf`
- **Document ID**: `doc_1d7f6a73c1d1297e61502479`
- **Source SHA256**: `e287d942eb27ca00c8a5a5c68f123c52a0bc98867a059883641b9b00da589f3d`
- **Total Questions in Paper**: 1 Conventional Essay Question (Section A, 20 Marks) + 80 MCQs (Section B, 80 Marks)
- **Subject Coverage**: General English (Idioms & Phrases, Reading Comprehension, Synonyms, Antonyms, Parts of Speech, Verb Tenses, Prepositions, Sentence Structure Analysis, Sentence Types, Contextual Vocabulary)

## Topic Breakdown
| Topic / Subtopic | Count |
| :--- | :--- |
"""

for topic, count in sorted(summary['breakdown'].items(), key=lambda x: -x[1]):
    md += f"| `{topic}` | {count} |\n"

md += """
## Section Breakdown
1. **Section A (Conventional, 20 Marks)**: Essay writing on The Ideal Politician / Conservation of Forest Cover / Transparency in Administration -> documented in `pending-written-intake.json`.
2. **Q1–Q16**: Idioms in italics (green-eyed, sitting on fence, point blank, high and low, burning question, feather in cap, in offing, not cut out, gift of gab, on wane, in doldrums, make head or tail, foot the bill, pulling leg, put foot down, took to heels) -> `english/vocabulary/idioms-and-phrases` (16)
3. **Q17–Q21**: Reading comprehension passage -> `english/comprehension` (5)
4. **Q22–Q24**: Synonyms from passage context -> `english/vocabulary/synonyms` (3)
5. **Q25–Q28**: Antonyms from passage context -> `english/vocabulary/antonyms` (4)
6. **Q29–Q36**: Functional parts of speech identification -> `english/grammar/parts-of-speech` (8)
7. **Q37–Q42**: Verb forms and tenses in context -> `english/grammar/tenses` (6)
8. **Q43–Q48**: Prepositions in context -> `english/grammar/prepositions` (6)
9. **Q49–Q58**: Sentence structure analysis (Simple, Compound, Complex) -> `english/grammar` (10)
10. **Q59–Q64**: Sentence types (Declarative, Interrogative, Imperative, Exclamatory) -> `english/grammar` (6)
11. **Q65–Q74**: Word choice and vocabulary in sentence context (eruption, respectable, cursory, fair share, apprehend, impair, endowed, altercation, evoked, resemblance) -> `english/vocabulary` (10)
12. **Q75–Q80**: Idioms and phrases (cold feet, apple of discord, skeleton in cupboard, sail in same boat, red-letter day, at beck and call) -> `english/vocabulary/idioms-and-phrases` (6)

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 80 candidate records staged under policy `study-tagging-v1`.
- Complete verification against 8 rendered page images from source PDF.
"""

(out / "README.md").write_text(md)
print("Wrote README.md successfully.")
