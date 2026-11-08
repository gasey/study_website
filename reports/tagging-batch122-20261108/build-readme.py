"""Generate README.md for Batch 122."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
summary = json.load(open(out / "summary.json"))
validation = json.load(open(out / "validation.json"))

md = f"""# Tagging Batch 122: Coach Grade-I under Sports & Youth Services (2019) — General English

## Summary
- **Batch ID**: 122
- **Date**: 2026-11-08
- **Targets**: {summary['targets']} appearances (80 official booklet MCQs + 6 duplicate OCR extractions; {summary['unextracted_items_preserved']} conventional items preserved, {summary['conventional_marks_preserved']} conventional marks)
- **Completion**: {summary['completion']}
- **Live Changes**: {summary['live_changes']} (All {summary['targets']} candidates remain `pending`)
- **Actions**:
  - `retag`: {summary['actions']['retag']}
  - `keep`: {summary['actions']['keep']}
  - `hold`: {summary['actions']['hold']}
- **Verification**: {validation['source_fingerprints_verified']}/{summary['targets']} source fingerprints re-verified via repeatable-read Oracle readback ({validation['validated_at']}).

## Paper Details
- **Paper ID**: `Old_Questions/Direct_2019-2020/Coach Grade-I General English.pdf`
- **Document ID**: `{summary['papers'][0]['document_id']}`
- **Source SHA256**: `{summary['papers'][0]['sha256']}`
- **Total Marks in Paper**: 100 Marks (Section A: 20 Conventional Marks [Essay 20 Marks] + Section B: 80 MCQs [80 Marks])
- **Subject Coverage**: General English (Reading Comprehension Passages, Sentence Structure Analysis, Clauses, Sentence Types, Contextual Vocabulary, Antonyms, One-Word Substitution, Parts of Speech, Prepositions, Verb Tenses & Forms, Idioms & Phrases)

## Topic Breakdown
| Topic / Subtopic | Count |
| :--- | :--- |
"""

for topic, count in sorted(summary['breakdown'].items(), key=lambda x: -x[1]):
    md += f"| `{topic}` | {count} |\n"

md += """
## Section Breakdown
1. **Section A (Conventional, 20 Marks)**: Essay writing on Child Labour / Save water, Save life / Importance of Sports (20 Marks) -> documented in `pending-written-intake.json`.
2. **Section B (MCQs, 80 Marks / 86 Appearances)**:
   - **Q1–Q7**: Passage 1 reading comprehension (Zoo animals and elephant/lion/monkey behavior) -> `english/comprehension` (7)
   - **Q8–Q12**: Passage 2 reading comprehension (Science, technological inventions, and human progress) -> `english/comprehension` (5)
   - **Q13–Q18**: Sentence structure analysis (Simple, Compound, Complex) -> `english/grammar` (6)
   - **Q19–Q23**: Clause analysis (Noun clause, Adjective clause, Adverb clause) -> `english/grammar` (5)
   - **Q24–Q28**: Sentence classification (Declarative, Imperative, Interrogative, Exclamatory) -> `english/grammar` (5)
   - **Q29–Q34**: Contextual word choice and lexical precision -> `english/vocabulary` (6)
   - **Q35–Q39**: Antonyms (Curtail, Bane, Gruesome, Hefty, Abhor) -> `english/vocabulary/antonyms` (10; 5 official items + 5 duplicate OCR extractions without prefix)
   - **Q40–Q44**: One-word substitution (Theology, Misanthrope, Polyandry, Numismatist, Omnipotent) -> `english/vocabulary/one-word-substitution` (5)
   - **Q45–Q51**: Functional parts of speech (adverb, adjective, conjunction, preposition, noun, verb) -> `english/grammar/parts-of-speech` (8; 7 official items + 1 duplicate extraction for Q46)
   - **Q52–Q58**: Appropriate prepositions in context (at, on, in, with, to, through) -> `english/grammar/prepositions` (7)
   - **Q59–Q64**: Appropriate forms of verbs and tense usage in context -> `english/grammar/tenses` (6)
   - **Q65–Q72**: Idioms and idiomatic phrases in bold -> `english/vocabulary/idioms-and-phrases` (8)
   - **Q73–Q80**: Idiomatic expressions and phrases meaning -> `english/vocabulary/idioms-and-phrases` (8)

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 86 candidate records staged under policy `study-tagging-v1`.
- Complete verification against 8 rendered page images from source PDF.
"""

(out / "README.md").write_text(md)
print("Wrote README.md successfully.")
