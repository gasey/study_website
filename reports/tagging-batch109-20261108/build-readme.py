"""Generate README.md for Batch 109."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
summary = json.load(open(out / "summary.json"))
validation = json.load(open(out / "validation.json"))

md = f"""# Tagging Batch 109: Surveyor-I under Land Revenue & Settlement (2019) — General English

## Summary
- **Batch ID**: 109
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
- **Paper ID**: `Old_Questions/Direct_2019-2020/General English (Surveyor-I).pdf`
- **Document ID**: `doc_a011a84f3eb731f4571d7a3d`
- **Source SHA256**: `4f4fd42e4f7403c7370a256e99cb3ffb846fffe928b9fb6c4839d3c509aa0fba`
- **Total Questions in Paper**: 1 Conventional Essay Question (Section A, 20 Marks) + 80 MCQs (Section B, 80 Marks)
- **Subject Coverage**: General English (Idioms & Phrases, Reading Comprehension Passages, Parts of Speech Form, Prepositions, Sentence Types & Communicative Notions, Sentence Structure & Degrees of Comparison, Contextual Vocabulary, Word Choice)

## Topic Breakdown
| Topic / Subtopic | Count |
| :--- | :--- |
"""

for topic, count in sorted(summary['breakdown'].items(), key=lambda x: -x[1]):
    md += f"| `{topic}` | {count} |\n"

md += """
## Section Breakdown
1. **Section A (Conventional, 20 Marks)**: Essay writing on Educated Unemployed / Communal Harmony / Hazard of Mobile Phones -> documented in `pending-written-intake.json`.
2. **Q1–Q8**: Idioms and phrases meaning (Scot free, few and far between, next to nothing, by fits and starts, behind the scenes, by leaps and bounds, better half, black and blue) -> `english/vocabulary/idioms-and-phrases` (8)
3. **Q9–Q16**: Idioms and phrases completion (barking up wrong tree, don't put all eggs in one basket, beat a dead horse, drop of a hat, make hay while sun shines, under weather, riding high horse/gravy train, maggot in meat) -> `english/vocabulary/idioms-and-phrases` (8)
4. **Q17–Q32**: Reading comprehension passages:
   - Passage 1: Martin Luther King Jr.'s "I Have a Dream" address (Q17–Q22) -> `english/comprehension` (6)
   - Passage 2: Rabindranath Tagore on English literature and Indian thought (Q23–Q27) -> `english/comprehension` (5)
   - Passage 3: Plato, freewill, and cognitive capacity (Q28–Q32) -> `english/comprehension` (5)
5. **Q33–Q40**: Parts of speech forms in context (nouns, verbs, adjectives, adverbs) -> `english/grammar/parts-of-speech` (8)
6. **Q41–Q48**: Preposition usage (by, between/among, by/on, in, into, on, till, into) -> `english/grammar/prepositions` (8)
7. **Q49–Q56**: Sentence types and communicative notions (declarative, exclamatory, negative, interrogative, advice, imperative) -> `english/grammar` (8)
8. **Q57–Q65**: Sentence structure (simple, compound, complex) and degrees of comparison (positive, comparative, superlative) -> `english/grammar` (9)
9. **Q66–Q70**: Contextual vocabulary meaning (grief/sob, upset, ambiguity, inebriated, indefatigable) -> `english/vocabulary` (5)
10. **Q71–Q75**: Word choice in sentence context (inquisitive, meddle, eyelashes, gradually, traffic light) -> `english/vocabulary` (5)
11. **Q76–Q80**: Appropriate form and vocabulary selection (tradition, broadcast, lecture, grudges, thoughtful) -> `english/vocabulary` (5)

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 80 candidate records staged under policy `study-tagging-v1`.
- Complete verification against 10 rendered page images from source PDF.
"""

(out / "README.md").write_text(md)
print("Wrote README.md successfully.")
