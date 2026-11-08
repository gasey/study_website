"""Generate README.md for Batch 120."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
summary = json.load(open(out / "summary.json"))
validation = json.load(open(out / "validation.json"))

md = f"""# Tagging Batch 120: Assistant Controller of Mines (March-2026) — General English

## Summary
- **Batch ID**: 120
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
- **Paper ID**: `Old_Questions/Direct_NG_2024-2027/Asistant Controller of Mines March-2026 General English..pdf`
- **Document ID**: `{summary['papers'][0]['document_id']}`
- **Source SHA256**: `{summary['papers'][0]['sha256']}`
- **Total Marks in Paper**: 100 Marks (Part A: 34 Conventional Marks [Précis 14 Marks, Official Letter Drafting 10 Marks, Reading Comprehension 10 Marks] + Part B: 66 MCQs [66 Marks])
- **Subject Coverage**: General English (Parts of Speech Identification, Conjunctions & Prepositions, Word Conversions across Parts of Speech, Sentence Functions & Types, Phrases & Clauses, Reported Speech [Direct/Indirect Narration], Contextual Vocabulary, One-Word Substitution, Idioms & Phrases)

## Topic Breakdown
| Topic / Subtopic | Count |
| :--- | :--- |
"""

for topic, count in sorted(summary['breakdown'].items(), key=lambda x: -x[1]):
    md += f"| `{topic}` | {count} |\n"

md += """
## Section Breakdown
1. **Part A (Conventional, 34 Marks)**:
   - Q1: Précis writing on social media tourism and Instatourism (14 Marks) -> documented in `pending-written-intake.json`.
   - Q2: Official letter drafting from Assistant Controller of Mines to Director regarding illegal mineral extraction in Siaha (10 Marks) -> documented in `pending-written-intake.json`.
   - Q3: Reading comprehension on Jeff Bezos's Princeton 2010 speech ('Cleverness is a gift, kindness is a choice') with 4 sub-questions (10 Marks) -> documented in `pending-written-intake.json`.
2. **Part B (MCQs, 66 Marks)**:
   - **Q1–Q10**: Functional parts of speech identification (pronoun, noun, adverb, verb, adjective, preposition, conjunction, interjection) -> `english/grammar/parts-of-speech` (10)
   - **Q11–Q16**: Contextual word choice and semantic precision (alleviate, steadfast, momentous, catalyst, inconsistent, mislead) -> `english/vocabulary` (6)
   - **Q17–Q26**: Conjunctions & prepositions:
     - Q17, Q18, Q21, Q22, Q26: Prepositions (beside, on, over, among, below) -> `english/grammar/prepositions` (5)
     - Q19, Q20, Q23, Q24, Q25: Conjunctions (yet, since, though, or, if) -> `english/grammar/parts-of-speech` (5)
   - **Q27–Q36**: Word formation and conversion across parts of speech (bravery, arrived, unlucky, easily, laughter, sweet, firmly, loneliness, wrong, proud) -> `english/grammar/parts-of-speech` (10)
   - **Q37–Q41**: Sentence structure and communicative function (imperative, complex, compound, assertive, optative) -> `english/grammar` (5)
   - **Q42–Q46**: Phrase and clause identification (adjective phrase, noun phrase, adverb phrase, adverb clause, adjective clause) -> `english/grammar` (5)
   - **Q47–Q51**: Direct and indirect speech narration conversion (imperative commands, negative advice, past assertive) -> `english/grammar/reported-speech` (5)
   - **Q52–Q56**: Phrase and clause identification in complex sentences (adverb clause, noun phrase, adjective clause, adverb phrase, noun clause) -> `english/grammar` (5)
   - **Q57–Q61**: One-word substitution and descriptive terms (nepotism, philanthropist, ephemeral, eclectic, fastidious) -> `english/vocabulary/one-word-substitution` (5)
   - **Q62–Q66**: Idioms and idiomatic phrases meaning (barking up the wrong tree, rite of passage, end in smoke, harp on same string, give oneself airs) -> `english/vocabulary/idioms-and-phrases` (5)

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 66 candidate records staged under policy `study-tagging-v1`.
- Complete verification against 10 rendered page images from source PDF.
"""

(out / "README.md").write_text(md)
print("Wrote README.md successfully.")
