"""Generate README.md for Batch 112."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
summary = json.load(open(out / "summary.json"))
validation = json.load(open(out / "validation.json"))

md = f"""# Tagging Batch 112: Chemist-II Archives under Art & Culture (2020) — General English

## Summary
- **Batch ID**: 112
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
- **Paper ID**: `Old_Questions/Direct_2019-2020/Chemist-II General Englsih.pdf`
- **Document ID**: `doc_1dff52e0078028ff515ec920`
- **Source SHA256**: `9630966b6f6b4b486a63588e4e9a8f4c47864f1993437299a9cf5f1c24da5ec3`
- **Total Questions in Paper**: 1 Conventional Essay Question (Section A, 20 Marks) + 80 MCQs (Section B, 80 Marks)
- **Subject Coverage**: General English (Reading Comprehension Passage, Idioms & Phrases, Prepositions, Parts of Speech, Sentence Structure, Clauses, Communicative Notions, Sentence Combinations, One-Word Substitution, Synonyms, Antonyms, Animal Offspring Vocabulary)

## Topic Breakdown
| Topic / Subtopic | Count |
| :--- | :--- |
"""

for topic, count in sorted(summary['breakdown'].items(), key=lambda x: -x[1]):
    md += f"| `{topic}` | {count} |\n"

md += """
## Section Breakdown
1. **Section A (Conventional, 20 Marks)**: Essay writing on "The effects of plastic bags on the environment" and AMC plastic-free city initiative -> documented in `pending-written-intake.json`.
2. **Q1–Q12**: Reading comprehension passage analysis -> `english/comprehension` (12)
3. **Q13–Q28**: Idioms and idiomatic expressions meaning -> `english/vocabulary/idioms-and-phrases` (16)
4. **Q29–Q32**: Preposition usage in context -> `english/grammar/prepositions` (4)
5. **Q33–Q48**: Functional parts of speech identification -> `english/grammar/parts-of-speech` (16)
6. **Q49–Q52**: Sentence structure analysis (Simple, Compound, Complex) -> `english/grammar` (4)
7. **Q53–Q55**: Clause analysis (Noun clause, Adjective clause, Adverb clause) -> `english/grammar` (3)
8. **Q56–Q60**: Communicative concepts / notions (advice, request, probability, permission, ability) -> `english/grammar` (5)
9. **Q61–Q64**: Sentence synthesis and clause combinations -> `english/grammar` (4)
10. **Q65–Q72**: One-word substitution (plagiarism, archives, ambiguous, recluse, quarantine, anonymous, soliloquy, homicide) -> `english/vocabulary/one-word-substitution` (8)
11. **Q73–Q74**: Synonyms in context (apathy, sagacity) -> `english/vocabulary/synonyms` (2)
12. **Q75–Q76**: Antonyms in context (tranquil, ameliorate) -> `english/vocabulary/antonyms` (2)
13. **Q77–Q78**: Collective nouns (band/troupe of singers, swarm of bees/ants/flies) -> `english/grammar/parts-of-speech` (2)
14. **Q79–Q80**: Young ones of animals (horse -> foal, elephant -> calf) -> `english/vocabulary` (2)

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 80 candidate records staged under policy `study-tagging-v1`.
- Complete verification against 8 rendered page images from source PDF.
"""

(out / "README.md").write_text(md)
print("Wrote README.md successfully.")
