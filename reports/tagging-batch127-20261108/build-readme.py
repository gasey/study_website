"""Generate README.md for Batch 127."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
summary = json.load(open(out / "summary.json"))
validation = json.load(open(out / "validation.json"))

md = f"""# Tagging Batch 127: Circle Officer (April 2026) — Paper-I (Series A)

## Summary
- **Batch ID**: 127
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
- **Paper ID**: `Old_Questions/Direct_2025-2027/Circle Officer April-2026 Paper-I (Series A)..pdf`
- **Document ID**: `{summary['papers'][0]['document_id']}`
- **Source SHA256**: `{summary['papers'][0]['sha256']}`
- **Total Marks in Paper**: 100 Marks (Part A: 40 Marks Conventional + Part B: 60 Marks MCQs)
- **Subject Coverage**: General English (Parts of Speech, Prepositions, Antonyms, Idioms & Phrases, One-Word Substitution, Clauses & Sentence Structure, Reported Speech, Sentence Transformation, Sentence Correction)

## Topic Breakdown
| Topic / Subtopic | Count |
| :--- | :--- |
"""

for topic, count in sorted(summary['breakdown'].items(), key=lambda x: -x[1]):
    md += f"| `{topic}` | {count} |\n"

md += """
## Section Breakdown
1. **PART-A Conventional Written Section (40 Marks preserved in `pending-written-intake.json`)**:
   - **Question 1 (10 marks)**: Essay Writing choosing one of: (a) The role of NGOs in community development, (b) Minimum Government, Maximum Governance, (c) Challenges faced by working women in modern society -> `english/writing/essay`.
   - **Question 2 (10 marks)**: Précis Writing on urbanisation, rural development, and bridging developmental gaps -> `english/writing/precis`.
   - **Question 3 (10 marks)**: Formal Letter Drafting to Mayor of Aizawl Municipal Corporation on rising burglary in localities -> `english/writing/letter`.
   - **Question 4 (10 marks)**: Reading Comprehension passage on youth, social media influence, mental health, and cyberbullying with 4 descriptive questions (8 marks) and 2 vocabulary MCQs (2 marks) -> `english/comprehension`.

2. **PART-B Objective MCQ Section (60 Marks, 60 MCQs)**:
   - **Q1–Q10**: Identification of Parts of Speech (still, better, most, right, since, near, but, fast, heavens, such) -> `english/grammar/parts-of-speech` (10)
   - **Q11–Q20**: Appropriate Prepositions (fawning upon, lost to, lying at hand, limit to, elated with joy at, talks to/like, passion for, cured of, acquitted of, committed to) -> `english/grammar/prepositions` (10)
   - **Q21–Q30**: Antonyms (senility, warily, grumpy, vicious, vanity, sturdy, intently, gradually, abstemious, mendacious) -> `english/vocabulary/antonyms` (10)
   - **Q31–Q35**: Idioms and Phrases (Go abegging, Tread on one's toe, A damp squib, Bore the palm, A jack of all trades) -> `english/vocabulary/idioms-and-phrases` (5)
   - **Q36–Q40**: One-word Substitution (sceptic, omniscient, epitaph, amnesty, expatriate) -> `english/vocabulary/one-word-substitution` (5)
   - **Q41–Q45**: Clause identification (adjective clause, adverb clause, noun clause, conditional clause) -> `english/grammar` (5)
   - **Q46–Q50**: Reported Speech / Narration (direct to indirect and indirect to direct conversions) -> `english/grammar/reported-speech` (5)
   - **Q51–Q58**: Sentence Transformation (interrogative, affirmative, exclamatory, negative, simple, complex, and compound sentences) -> `english/grammar` (8)
   - **Q59–Q60**: Sentence Correction (pronoun order "My brother and I", subjunctive suggestion "I suggested that he apply") -> `english/sentence-correction` (2)

## Deduplication Note
- `Circle Officer April-2026 Paper-I (Series B)..pdf` (`doc_377910aec4160662181961c8`) is a duplicate question series permutation of Series A. Under single-booklet deduplication policy, Series A represents the canonical family review; Series B requires no separate review, avoiding duplicate family conflicts.

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 60 candidate records staged under policy `study-tagging-v1`.
- Complete verification against 8 rendered page images from source PDF.
"""

(out / "README.md").write_text(md)
print("Wrote README.md successfully.")
