"""Generate README.md for Batch 118."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
summary = json.load(open(out / "summary.json"))
validation = json.load(open(out / "validation.json"))

md = f"""# Tagging Batch 118: Translator under Art & Culture (2019) — General English

## Summary
- **Batch ID**: 118
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
- **Paper ID**: `Old_Questions/Direct_2019-2020/General English (Translator).pdf`
- **Document ID**: `{summary['papers'][0]['document_id']}`
- **Source SHA256**: `{summary['papers'][0]['sha256']}`
- **Total Marks in Paper**: 100 Marks (Section A: 42 Conventional Marks [Essay 20 Marks, Précis 10 Marks, Verse Paraphrase 6 Marks, Mizo-to-English Translation 6 Marks] + Section B: 58 MCQs [58 Marks])
- **Subject Coverage**: General English (Idioms & Phrases, Parts of Speech, Clauses, Sentence Analysis, Voice Transformation, Subject-Verb Agreement, Predicate Adjectives, Comparison, Contextual Vocabulary, One-Word Substitution)

## Topic Breakdown
| Topic / Subtopic | Count |
| :--- | :--- |
"""

for topic, count in sorted(summary['breakdown'].items(), key=lambda x: -x[1]):
    md += f"| `{topic}` | {count} |\n"

md += """
## Section Breakdown
1. **Section A (Conventional, 42 Marks)**:
   - Q1: Essay on 'Strong cultural values keep one rooted in modern times' (20 Marks) -> documented in `pending-written-intake.json`.
   - Q2: Summary/précis of Jawaharlal Nehru's letter to Indira (10 Marks) -> documented in `pending-written-intake.json`.
   - Q3: Verse paraphrase of 'The glories of our blood and state...' (6 Marks) -> documented in `pending-written-intake.json`.
   - Q4: Translation of Mizo passage into English (6 Marks) -> documented in `pending-written-intake.json`.
2. **Section B (MCQs, 58 Marks)**:
   - **Q1–Q8**: Idioms and phrases meaning (hit upon, backed up, come off, losing ground, far cry, came to grief, fast life, bone of contention) -> `english/vocabulary/idioms-and-phrases` (8)
   - **Q9–Q16**: Idioms and phrases usage in sentences (beggars description, harp on same string, followed suit, moved heaven and earth, sixes and sevens, threw cold water, wrong side of sixty, sum and substance) -> `english/vocabulary/idioms-and-phrases` (8)
   - **Q17–Q26**: Parts of speech identification (preposition, pronoun, conjunction, verb, adverb, adjective, noun) -> `english/grammar/parts-of-speech` (10)
   - **Q27–Q32**: Clause analysis (adverb clause, adjective/relative clause, noun clause) -> `english/grammar` (6)
   - **Q33–Q37**: Sentence analysis (simple, compound, complex) -> `english/grammar` (5)
   - **Q38–Q42**: Active and passive voice transformation -> `english/grammar/voice` (5)
   - **Q43–Q58**: Suitable word selection and mechanics:
     - Q43: Compound singular subject agreement (My friend and mentor has arrived) -> `english/grammar/subject-verb-agreement` (1)
     - Q44: Linking verbs & predicate adjectives (smells sweet) -> `english/grammar` (1)
     - Q45: Degrees of comparison (wisest of all) -> `english/grammar` (1)
     - Q46: Verb form (laid the book) -> `english/grammar/tenses` (1)
     - Q47: Adverb modifier (too good to be true) -> `english/grammar` (1)
     - Q48: Conditional conjunction (unless) -> `english/grammar/parts-of-speech` (1)
     - Q49: Prepositional phrase (on behalf of) -> `english/grammar/prepositions` (1)
     - Q50–Q53: Contextual word choice (adapt, prescribe, admittance, petition) -> `english/vocabulary` (4)
     - Q54: One-word substitution (Ambidexterous) -> `english/vocabulary/one-word-substitution` (1)
     - Q55–Q56: Contextual nouns (consignment, catalogue) -> `english/vocabulary` (2)
     - Q57–Q58: One-word substitution (colleague, Ethnology) -> `english/vocabulary/one-word-substitution` (2)

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 58 candidate records staged under policy `study-tagging-v1`.
- Complete verification against 7 rendered page images from source PDF.
"""

(out / "README.md").write_text(md)
print("Wrote README.md successfully.")
