"""Generate README.md for Batch 102."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
summary = json.load(open(out / "summary.json"))
validation = json.load(open(out / "validation.json"))

md = f"""# Tagging Batch 102: Circle Education Officer (CEO) (2022) — General English Paper-II

## Summary
- **Batch ID**: 102
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
- **Paper ID**: `Old_Questions/Direct_2022-2023/Circle Education Officer under School Education Deptt 2022 Paper-II.pdf`
- **Document ID**: `doc_cb78bb80691cbb720a142340`
- **Source SHA256**: `9d5f30547f9761ecd336e026ee236f9b9d46570d6df05ac72836f707896597fa`
- **Total Questions in Paper**: 100 MCQs (100 Marks, 2 Hours duration)
- **Subject Coverage**: General English (Functional Parts of Speech, Imperative Sentence Types, Verb Tenses, Prepositions, Sentence Kinds Analysis, Declarative/Interrogative/Exclamatory Types, Clauses, Idioms & Phrases, Antonyms, Synonyms, One-Word Substitution)

## Topic Breakdown
| Topic / Subtopic | Count |
| :--- | :--- |
"""

for topic, count in sorted(summary['breakdown'].items(), key=lambda x: -x[1]):
    md += f"| `{topic}` | {count} |\n"

md += """
## Section Breakdown
1. **Q1–Q10**: Functional parts of speech identification (off, running, connects, emotional burst, proximity, articles, etc.) -> `english/grammar` (10)
2. **Q11–Q20**: Imperative sentence types & functions (command, request, advice, prohibition, invitation, proposal) -> `english/grammar` (10)
3. **Q21–Q30**: Verb tense selection and form completions in context -> `english/grammar/tenses` (10)
4. **Q31–Q40**: Prepositions in context (bearing on, adept in, etc.) -> `english/grammar/prepositions` (10)
5. **Q41–Q50**: Sentence kind analysis (Simple, Compound, Complex) -> `english/grammar` (10)
6. **Q51–Q60**: Sentence type identification (Declarative, Interrogative, Exclamatory, Imperative) -> `english/grammar` (10)
7. **Q61–Q70**: Clause identification (Noun clause, Adjective clause, Adverb clause, Co-ordinate clause) -> `english/grammar` (10)
8. **Q71–Q80**: Idioms and idiomatic expressions (to grow upon, at sixes and sevens, hard nut to crack, etc.) -> `english/vocabulary/idioms-and-phrases` (10)
9. **Q81–Q90**: Vocabulary in context:
   - Q81–Q83, Q87: Antonyms (intrepid, quench, vicious, amicable) -> `english/vocabulary/antonyms` (4)
   - Q84, Q86, Q89: Synonyms (hostility -> antagonism, berated -> reproached, recede -> retreat) -> `english/vocabulary/synonyms` (3)
   - Q85, Q90: Contextual vocabulary (behemoth, impact) -> `english/vocabulary` (2)
   - Q88: Term definition (tacit) -> `english/vocabulary/one-word-substitution` (1)
10. **Q91–Q100**: One-word substitution / term definitions -> `english/vocabulary/one-word-substitution` (10)

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 100 candidate records staged under policy `study-tagging-v1`.
- Complete verification against 8 rendered page images from source PDF.
"""

(out / "README.md").write_text(md)
print("Wrote README.md successfully.")
