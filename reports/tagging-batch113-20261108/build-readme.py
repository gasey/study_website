"""Generate README.md for Batch 113."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
summary = json.load(open(out / "summary.json"))
validation = json.load(open(out / "validation.json"))

md = f"""# Tagging Batch 113: Junior Engineer Agriculture (2020) — General English

## Summary
- **Batch ID**: 113
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
- **Paper ID**: `Old_Questions/Departmental_2019-2020/JE General English..pdf`
- **Document ID**: `doc_b9d99723ec0d6b0559ebf04f`
- **Source SHA256**: `62f46c2bc0540cae1837bc9d91f42d25032906b3bc5b4da66ebaa8f107d6124d`
- **Total Questions in Paper**: 1 Conventional Essay Question (Section A, 20 Marks) + 80 MCQs (Section B, 80 Marks)
- **Subject Coverage**: General English (Idioms & Phrases, Reading Comprehension Passages, Parts of Speech, Sentence Structure, Clauses, Synthesis, Transformations, Prepositions, Sentence Correction, Term Definitions)

## Topic Breakdown
| Topic / Subtopic | Count |
| :--- | :--- |
"""

for topic, count in sorted(summary['breakdown'].items(), key=lambda x: -x[1]):
    md += f"| `{topic}` | {count} |\n"

md += """
## Section Breakdown
1. **Section A (Conventional, 20 Marks)**: Essay writing on Plastic Ban / Conservation of Resources / Be the Change / Sustainable Agriculture -> documented in `pending-written-intake.json`.
2. **Q1–Q16**: Idioms and phrases meaning -> `english/vocabulary/idioms-and-phrases` (16)
3. **Q17–Q32**: Reading comprehension passages (Passage 1: Q17–Q24; Passage 2: Q25–Q32) -> `english/comprehension` (16)
4. **Q33–Q40**: Contextual usage, prepositions, tenses, and concord:
   - Q33: affect vs effect -> `english/vocabulary` (1)
   - Q34, Q37–Q40: Preposition usage -> `english/grammar/prepositions` (5)
   - Q35: Past participle verb form -> `english/grammar/tenses` (1)
   - Q36: Subject-verb agreement (Six months is) -> `english/grammar/subject-verb-agreement` (1)
5. **Q41–Q50**: Functional parts of speech identification -> `english/grammar/parts-of-speech` (10)
6. **Q51–Q54**: Sentence structure analysis (Simple, Compound, Complex) -> `english/grammar` (4)
7. **Q55–Q58**: Clause analysis (Noun clause, Adjective clause, Adverb clause) -> `english/grammar` (4)
8. **Q59–Q62**: Sentence synthesis and clause combinations -> `english/grammar` (4)
9. **Q63–Q66**: Sentence transformations (Assertive, Interrogative, Affirmative, Imperative) -> `english/grammar` (4)
10. **Q67–Q72**: Case, response additions, tags, and agreement (larger than me, So do I, tag question, Each has [agreement], Whom, except him) -> `english/grammar` (5) & `english/grammar/subject-verb-agreement` (1)
11. **Q73–Q76**: Sentence correction and grammatical improvement (luggage, some advice, quality is, setting affects) -> `english/sentence-correction` (4)
12. **Q77–Q80**: One-word substitution and term definitions (lexicographer, teetotaller, florist, speleology) -> `english/vocabulary/one-word-substitution` (4)

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 80 candidate records staged under policy `study-tagging-v1`.
- Complete verification against 8 rendered page images from source PDF.
"""

(out / "README.md").write_text(md)
print("Wrote README.md successfully.")
