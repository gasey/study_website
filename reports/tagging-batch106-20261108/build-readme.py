"""Generate README.md for Batch 106."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
summary = json.load(open(out / "summary.json"))
validation = json.load(open(out / "validation.json"))

md = f"""# Tagging Batch 106: Deputy Store Officer under Home Deptt (2019) — General English

## Summary
- **Batch ID**: 106
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
- **Paper ID**: `Old_Questions/Direct_2019-2020/General English (DSO).pdf`
- **Document ID**: `doc_ffe3a81602eb0cbf3c6feb22`
- **Source SHA256**: `acea57eec5dc79b940989ee577881c19b35bc4568e3df31cc59c02d13778a6ff`
- **Total Questions in Paper**: 1 Conventional Essay Question (Section A, 20 Marks) + 80 MCQs (Section B, 80 Marks)
- **Subject Coverage**: General English (Idioms & Phrases, Reading Comprehension Passages, Parts of Speech, Prepositions, Verb Tenses, Sentence Structure, Clauses, Communicative Notions, One-Word Substitution, Synonyms)

## Topic Breakdown
| Topic / Subtopic | Count |
| :--- | :--- |
"""

for topic, count in sorted(summary['breakdown'].items(), key=lambda x: -x[1]):
    md += f"| `{topic}` | {count} |\n"

md += """
## Section Breakdown
1. **Section A (Conventional, 20 Marks)**: Essay writing on Brain Drain / Social Media / Cleanliness / Water Scarcity -> documented in `pending-written-intake.json`.
2. **Q1–Q16**: Idioms and idiomatic expressions (bury the hatchet, kick the bucket, babe in the woods, cut corners, hit the sack, etc.) -> `english/vocabulary/idioms-and-phrases` (16)
3. **Q17–Q22**: Reading comprehension passage 1 (Vincent van Gogh's life and art) -> `english/comprehension` (6)
4. **Q23–Q28**: Reading comprehension passage 2 (Ferdinand Magellan's circumnavigation voyage) -> `english/comprehension` (6; corrected from erroneous legacy `general-knowledge` tagging)
5. **Q29–Q34**: Parts of speech identification in context (not, rotten, conveyed, themselves, where, and) -> `english/grammar/parts-of-speech` (6)
6. **Q35–Q40**: Preposition usage (among, off, behind, of, against, among) -> `english/grammar/prepositions` (6)
7. **Q41–Q48**: Verb tense forms and fill-in-the-blank verbs -> `english/grammar/tenses` (8)
8. **Q49–Q53**: Sentence structure analysis (Simple, Compound, Complex) -> `english/grammar` (5)
9. **Q54–Q58**: Clause analysis (Noun clause, Adjective clause, Adverb clause, Coordinate clause) -> `english/grammar` (5)
10. **Q59–Q64**: Communicative functions / notions (request, command, exclamation, statement, etc.) -> `english/grammar` (6)
11. **Q65–Q72**: One-word substitution for descriptions and definitions (anomaly, polygamy, pseudonym, arcane, maelstrom, pariah, plethora, quaint) -> `english/vocabulary/one-word-substitution` (8)
12. **Q73–Q80**: Synonyms in context (acceptable, alluring, atrocious, ample, brilliant, harmony, exhilaration, vexed) -> `english/vocabulary/synonyms` (8)

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 80 candidate records staged under policy `study-tagging-v1`.
- Complete verification against 8 rendered page images from source PDF.
"""

(out / "README.md").write_text(md)
print("Wrote README.md successfully.")
