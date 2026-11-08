"""Generate README.md for Batch 134."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
summary = json.load(open(out / "summary.json"))
validation = json.load(open(out / "validation.json"))

md = f"""# Tagging Batch 134: UDC under Secretariat Administration Department (February 2018) — Paper-I

## Summary
- **Batch ID**: 134
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
- **Paper ID**: `Old_Questions/Direct_2014-2018/1.UDC under SAD Paper-I.pdf`
- **Document ID**: `{summary['papers'][0]['document_id']}`
- **Source SHA256**: `{summary['papers'][0]['sha256']}`
- **Total Marks in Paper**: 125 Marks (Section A: 50 Marks Conventional + Section B: 75 Marks MCQs)
- **Subject Coverage**: General English (Parts of Speech, Clauses, Sentence Analysis, Concepts & Speech Acts, Phrasal Verbs & Idioms, One-Word Substitution, Prepositions, Tenses & Verb Forms)

## Topic Breakdown
| Topic / Subtopic | Count |
| :--- | :--- |
"""

for topic, count in sorted(summary['breakdown'].items(), key=lambda x: -x[1]):
    md += f"| `{topic}` | {count} |\n"

md += """
## Section Breakdown
1. **SECTION - A Conventional Written Section (50 Marks preserved in `pending-written-intake.json`)**:
   - **Question 1 (25 marks)**: Essay Writing in ~500 words on "Moral values should be made as a compulsory subject in schools" -> `english/writing/essay`.
   - **Question 2 (25 marks)**: Précis Writing on Lord Chesterfield's letter to his son on expenses and virtues -> `english/writing/precis`.

2. **SECTION - B Objective MCQ Section (75 Marks, 75 MCQs)**:
   - **Q1–Q8**: Parts of speech identification -> `english/grammar/parts-of-speech` (8)
   - **Q9–Q16**: Clause analysis (noun, adjective, adverb, co-ordinate clauses) -> `english/grammar` (8)
   - **Q17–Q24**: Sentence structure analysis (simple, compound, complex) -> `english/grammar` (8)
   - **Q25–Q32**: Functional concepts and speech acts (possibility, polite request, determination, simultaneous action, regret, promise) -> `english/grammar` (8)
   - **Q33–Q40**: Phrasal verbs (put down, assured of, gives off, took to their heels, worn out, etc.) -> `english/vocabulary/idioms-and-phrases` (8)
   - **Q41–Q48**: One-word substitution (germicide, linguist, turncoat, revel, filicide, articulate, verbose, litter) -> `english/vocabulary/one-word-substitution` (8)
   - **Q49–Q57**: Prepositions and prepositional collocations -> `english/grammar/prepositions` (9)
   - **Q58–Q66**: Idioms and phrases (snap fingers at, maiden speech, apple of discord, elbow room, etc.) -> `english/vocabulary/idioms-and-phrases` (9)
   - **Q67–Q75**: Verb forms, tenses, subject-verb agreement, and conditionals -> `english/grammar/tenses` (9)

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 75 candidate records staged under policy `study-tagging-v1`.
- Complete verification against 8 rendered page images from source PDF.
"""

(out / "README.md").write_text(md)
print("Wrote README.md successfully.")
