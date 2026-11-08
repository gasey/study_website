"""Generate README.md for Batch 119."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
summary = json.load(open(out / "summary.json"))
validation = json.load(open(out / "validation.json"))

md = f"""# Tagging Batch 119: CDPO & AD (Food & Drugs) (2025) — General English

## Summary
- **Batch ID**: 119
- **Date**: 2026-11-08
- **Targets**: {summary['targets']} MCQs ({summary['unextracted_items_preserved']} conventional items preserved, {summary['conventional_marks_preserved']} conventional marks)
- **Completion**: {summary['completion']}
- **Live Changes**: {summary['live_changes']} (All {summary['targets']} candidates remain `pending`)
- **Actions**:
  - `retag`: {summary['actions']['retag']}
  - `keep`: {summary['actions']['keep']}
  - `hold`: {summary['actions']['hold']}
- **Verification**: {validation['source_fingerprints_verified']}/{summary['targets']} source fingerprints re-verified via repeatable-read Oracle readback ({validation['validated_at']}).

## Paper Details
- **Paper ID**: `Old_Questions/Direct_2025-2027/CDPO General English-2025..pdf`
- **Document ID**: `{summary['papers'][0]['document_id']}`
- **Source SHA256**: `{summary['papers'][0]['sha256']}`
- **Total Marks in Paper**: 100 Marks (Section A: 34 Conventional Marks [Précis 14 Marks, Reading Comprehension 10 Marks, Formal Letter Drafting 10 Marks] + Section B: 66 MCQs [66 Marks])
- **Subject Coverage**: General English (Parts of Speech, Prepositions & Adverbs, Phrases & Clauses, Sentence Transformations, Reported Speech [Direct/Indirect], Contextual Vocabulary, One-Word Substitution, Sentence Correction [Spotting Errors], Verb Tenses, Conjunctions/Connectors, Idioms & Phrases)

## Topic Breakdown
| Topic / Subtopic | Count |
| :--- | :--- |
"""

for topic, count in sorted(summary['breakdown'].items(), key=lambda x: -x[1]):
    md += f"| `{topic}` | {count} |\n"

md += """
## Section Breakdown
1. **Section A (Conventional, 34 Marks)**:
   - Q1: Précis writing on verbal and non-verbal communication (14 Marks) -> documented in `pending-written-intake.json`.
   - Q2: Reading comprehension on industrial civilization and inventions (10 Marks) -> documented in `pending-written-intake.json`.
   - Q3: Formal letter drafting to Director W&CD regarding child malnutrition survey and supplement program budget (10 Marks) -> documented in `pending-written-intake.json`.
2. **Section B (MCQs, 66 Marks)**:
   - **Q1–Q10**: Functional parts of speech (though, uninclined, well, what, love, adore, himself, before, until, wish) -> `english/grammar/parts-of-speech` (10)
   - **Q11–Q20**: Appropriate prepositions and adverbs:
     - Q11, Q13, Q16, Q17, Q18, Q19, Q20: Prepositions (about, on, with, of, in/within, upon, of) -> `english/grammar/prepositions` (7)
     - Q12, Q14, Q15: Adverbs / conjunctive adverbs (ago, consequently, besides) -> `english/grammar/parts-of-speech` (3)
   - **Q21–Q26**: Phrases and clauses identification (noun clause, noun phrase, adjective clause, adjective phrase, adverb clause) -> `english/grammar` (6)
   - **Q27–Q31**: Sentence transformation (affirmative, assertive, negative, exclamatory) -> `english/grammar` (5)
   - **Q32–Q36**: Direct and indirect reported speech narration transformation -> `english/grammar/reported-speech` (5)
   - **Q37–Q43**: Contextual vocabulary & one-word substitution:
     - Q37, Q38, Q41, Q42: One-word substitution (teetotaler, ineligible, monarchy, bigot) -> `english/vocabulary/one-word-substitution` (4)
     - Q39, Q40, Q43: Contextual word choice (magnanimous, epitome, credible) -> `english/vocabulary` (3)
   - **Q44–Q46**: Sentence correction / spotting errors -> `english/sentence-correction` (3)
   - **Q47–Q56**: Verb tenses and aspects -> `english/grammar/tenses` (10)
   - **Q57–Q61**: Sentence connectors and conjunctions (hence, therefore, before, provided, if) -> `english/grammar/parts-of-speech` (5)
   - **Q62–Q66**: Idioms and idiomatic phrases meaning (a lone wolf, rule of thumb, close-fisted, up to one's elbows, hold one's tongue) -> `english/vocabulary/idioms-and-phrases` (5)

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 66 candidate records staged under policy `study-tagging-v1`.
- Complete verification against 9 rendered page images from source PDF.
"""

(out / "README.md").write_text(md)
print("Wrote README.md successfully.")
