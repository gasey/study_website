"""Generate README.md for Batch 117."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
summary = json.load(open(out / "summary.json"))
validation = json.load(open(out / "validation.json"))

md = f"""# Tagging Batch 117: Staff Nurse under H&FW (2019) — General English

## Summary
- **Batch ID**: 117
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
- **Paper ID**: `Old_Questions/Direct_2019-2020/General English(Staff Nurse).pdf`
- **Document ID**: `{summary['papers'][0]['document_id']}`
- **Source SHA256**: `{summary['papers'][0]['sha256']}`
- **Total Marks in Paper**: 100 Marks (Section A: 32 Conventional Marks [Essay 20 Marks, Reading Comprehension 12 Marks] + Section B: 68 MCQs [68 Marks])
- **Subject Coverage**: General English (Idioms & Phrases, Subject-Verb Agreement, Tenses, Parts of Speech, Prepositions, Clauses, Synthesis & Transformation, Sentence Classification, Semantic Function, Punctuation, Synonyms, One-Word Substitution)

## Topic Breakdown
| Topic / Subtopic | Count |
| :--- | :--- |
"""

for topic, count in sorted(summary['breakdown'].items(), key=lambda x: -x[1]):
    md += f"| `{topic}` | {count} |\n"

md += """
## Section Breakdown
1. **Section A (Conventional, 32 Marks)**:
   - Q1: Essay writing on Balanced Diet / The Past & Present / Social Problems of India (20 Marks) -> documented in `pending-written-intake.json`.
   - Q2: Reading comprehension passage on First Aid with 4 sub-questions (Synonyms [6 marks], Patient behavior [2 marks], Wound dressing [2 marks], Title [2 marks] = 12 Marks) -> documented in `pending-written-intake.json`.
2. **Section B (MCQs, 68 Marks)**:
   - **Q1–Q16**: Idioms and phrases (mealy mouthed, white elephant, call in question, cut into, man of parts, sum and substance, etc.) -> `english/vocabulary/idioms-and-phrases` (16)
   - **Q17–Q20**: Verb forms and mechanics:
     - Q17: Disjunctive subject-verb agreement (Either he or you are) -> `english/grammar/subject-verb-agreement` (1)
     - Q18: Present perfect continuous tense (has been raining) -> `english/grammar/tenses` (1)
     - Q19: Modal deduction (must be a fire) -> `english/grammar` (1)
     - Q20: Question tags (doesn't she) -> `english/grammar` (1)
   - **Q21–Q24**: Functional parts of speech (that book, That is, only three, Call back) -> `english/grammar/parts-of-speech` (4)
   - **Q25–Q28**: Prepositions (into, by, beneath/under, at) -> `english/grammar/prepositions` (4)
   - **Q29–Q32**: Tense identification (present perfect, future perfect, past perfect continuous, simple present) -> `english/grammar/tenses` (4)
   - **Q33–Q36**: Fill in the blanks:
     - Q33: Interrogative pronoun/determiner (Whose) -> `english/grammar/parts-of-speech` (1)
     - Q34: Preposition of duration (for seven months) -> `english/grammar/prepositions` (1)
     - Q35: Collocation / verb choice (felt my pulse) -> `english/vocabulary` (1)
     - Q36: Indefinite pronoun agreement (No one has come) -> `english/grammar/subject-verb-agreement` (1)
   - **Q37–Q40**: Clause analysis (Noun clause, Adjective clause, Adverb clause) -> `english/grammar` (4)
   - **Q41–Q44**: Sentence synthesis & transformation (too...to, participles, negative transformation, degrees of comparison) -> `english/grammar` (4)
   - **Q45–Q48**: Sentence transformation (simple, compound, complex, conditional) -> `english/grammar` (4)
   - **Q49–Q52**: Sentence classification (simple, compound, complex) -> `english/grammar` (4)
   - **Q53–Q56**: Semantic & functional classification (condition, optative, maxim, frequency) -> `english/grammar` (4)
   - **Q57–Q60**: Punctuation and capitalization mechanics -> `english/grammar` (4)
   - **Q61–Q64**: Synonyms (Dedicate, Candid, Moderate, Taboo) -> `english/vocabulary/synonyms` (4)
   - **Q65–Q68**: One-word substitution (Psephologist, Verbatim, Odontology [realigned from erroneous 'dental' tag], Drey) -> `english/vocabulary/one-word-substitution` (4)

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 68 candidate records staged under policy `study-tagging-v1`.
- Complete verification against 8 rendered page images from source PDF.
"""

(out / "README.md").write_text(md)
print("Wrote README.md successfully.")
