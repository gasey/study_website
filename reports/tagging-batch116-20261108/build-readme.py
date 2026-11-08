"""Generate README.md for Batch 116."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
summary = json.load(open(out / "summary.json"))
validation = json.load(open(out / "validation.json"))

md = f"""# Tagging Batch 116: Computer Operator under AH&Vety (2019) — General English

## Summary
- **Batch ID**: 116
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
- **Paper ID**: `Old_Questions/Direct_2019-2020/General English(AH&Vety).pdf`
- **Document ID**: `doc_1dbdb293efaa53fe5973dcf2`
- **Source SHA256**: `b5cafde327751068a17c2be07241599377d3c80b87497fd46b2fa372dcef254b`
- **Total Questions in Paper**: 1 Conventional Essay Question (Section A, 20 Marks) + 80 MCQs (Section B, 80 Marks)
- **Subject Coverage**: General English (Reading Comprehension Passage, Verb Tenses, Parts of Speech, Sentence Structure, Clauses, Contextual Vocabulary, One-Word Substitution, Idioms & Phrases)

## Topic Breakdown
| Topic / Subtopic | Count |
| :--- | :--- |
"""

for topic, count in sorted(summary['breakdown'].items(), key=lambda x: -x[1]):
    md += f"| `{topic}` | {count} |\n"

md += """
## Section Breakdown
1. **Section A (Conventional, 20 Marks)**: Essay writing on Electronic Media vs Print Media / State of Education in Mizoram / Role of YMA -> documented in `pending-written-intake.json`.
2. **Q1–Q10**: Reading comprehension passage analysis -> `english/comprehension` (10)
3. **Q11–Q18**: Verb tense forms and reported speech (was hanged, lay, have been residing, has passed, would come, sank, had come, gave) -> `english/grammar/tenses` (8)
4. **Q19–Q27**: Functional parts of speech identification (nouns, verbs, adjectives, adverbs, prepositions, conjunctions) -> `english/grammar/parts-of-speech` (9)
5. **Q28–Q36**: Sentence structure analysis (Simple, Compound, Complex) -> `english/grammar` (9)
6. **Q37–Q45**: Clause analysis (Noun clause, Adjective/Relative clause, Adverb clause) -> `english/grammar` (9; includes Q44)
7. **Q46–Q54**: Vocabulary in context & tenses:
   - Q46–Q53: Contextual word choice (weigh, allow, revenged, notorious, crimes, incident, admitted, entered) -> `english/vocabulary` (8)
   - Q54: Simple past tense (arrived yesterday) -> `english/grammar/tenses` (1)
8. **Q55–Q62**: One-word substitution and scientific terms (Chemistry, crematory, misanthropist, etc.) -> `english/vocabulary/one-word-substitution` (8)
9. **Q63–Q80**: Idioms and idiomatic expressions usage and meaning (ups and downs, odds and ends, turn up nose, eager beaver, heart and soul, gift of the gab, etc.) -> `english/vocabulary/idioms-and-phrases` (18)

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 80 candidate records staged under policy `study-tagging-v1`.
- Complete verification against 8 rendered page images from source PDF.
"""

(out / "README.md").write_text(md)
print("Wrote README.md successfully.")
