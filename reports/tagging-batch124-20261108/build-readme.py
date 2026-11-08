"""Generate README.md for Batch 124."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
summary = json.load(open(out / "summary.json"))
validation = json.load(open(out / "validation.json"))

md = f"""# Tagging Batch 124: Tutor under H&FW (MCON) (2019) — General English

## Summary
- **Batch ID**: 124
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
- **Paper ID**: `Old_Questions/Direct_2019-2020/General English (Tutor, MCON).pdf`
- **Document ID**: `{summary['papers'][0]['document_id']}`
- **Source SHA256**: `{summary['papers'][0]['sha256']}`
- **Total Marks in Paper**: 100 Marks (Questions 1–5: 60 Conventional Marks [Essay 20 Marks, Précis 10 Marks, Application Letter 10 Marks, Proverb Expansion 10 Marks, Reading Comprehension 10 Marks] + Questions 6–45: 40 MCQs [40 Marks])
- **Subject Coverage**: General English (Parts of Speech Identification, Subject-Verb Agreement, Phrasal Verbs, Idioms and Expressions)

## Topic Breakdown
| Topic / Subtopic | Count |
| :--- | :--- |
"""

for topic, count in sorted(summary['breakdown'].items(), key=lambda x: -x[1]):
    md += f"| `{topic}` | {count} |\n"

md += """
## Section Breakdown
1. **Conventional Sections (Questions 1–5, 60 Marks)**:
   - Q1: Essay writing on Health is Wealth / Personal habits / Saving the environment (20 Marks) -> documented in `pending-written-intake.json`.
   - Q2: Précis writing on effects of travel on the mind (10 Marks) -> documented in `pending-written-intake.json`.
   - Q3: Formal letter to Director of Education applying for teacher appointment (10 Marks) -> documented in `pending-written-intake.json`.
   - Q4: Paragraph expansion on proverb 'Where there's a will there's a way' (10 Marks) -> documented in `pending-written-intake.json`.
   - Q5: Reading comprehension passage on Football in India with 5 sub-questions (10 Marks) -> documented in `pending-written-intake.json`.
2. **Objective MCQs (Questions 6–45, 40 Marks)**:
   - **Q6–Q19**: Functional parts of speech identification (noun, pronoun, adjective, adverb, preposition, verb, conjunction) -> `english/grammar/parts-of-speech` (14)
   - **Q20–Q29**: Subject-verb agreement rules (singular/plural verbs with collective, compound, disjunctive, and distributive subjects) -> `english/grammar/subject-verb-agreement` (10)
   - **Q30–Q45**: Phrasal verbs and idioms meaning (run up, saw through, takes after, worked upon, takes up, go by, looks down upon, hear me out, hot water, smell a rat, stands well with, at a stretch, goes to heart, come to grief, when pigs fly, keeps a good table) -> `english/vocabulary/idioms-and-phrases` (16)

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 40 candidate records staged under policy `study-tagging-v1`.
- Complete verification against 5 rendered page images from source PDF.
"""

(out / "README.md").write_text(md)
print("Wrote README.md successfully.")
