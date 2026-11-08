"""Generate README.md for Batch 129."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
summary = json.load(open(out / "summary.json"))
validation = json.load(open(out / "validation.json"))

md = f"""# Tagging Batch 129: Museum Guide (February 2020) — General English

## Summary
- **Batch ID**: 129
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
- **Paper ID**: `Old_Questions/Direct_2019-2020/Museum Guide General Englsih.pdf`
- **Document ID**: `{summary['papers'][0]['document_id']}`
- **Source SHA256**: `{summary['papers'][0]['sha256']}`
- **Total Marks in Paper**: 100 Marks (Section A: 20 Marks Conventional + Section B: 50 Marks MCQs; 70 marks active in booklet)
- **Subject Coverage**: General English (Idioms & Phrases, Reading Comprehension, Parts of Speech, Sentence Analysis & Transformation, Subject-Verb Agreement, Synonyms)

## Topic Breakdown
| Topic / Subtopic | Count |
| :--- | :--- |
"""

for topic, count in sorted(summary['breakdown'].items(), key=lambda x: -x[1]):
    md += f"| `{topic}` | {count} |\n"

md += """
## Section Breakdown
1. **SECTION - A Conventional Written Section (20 Marks preserved in `pending-written-intake.json`)**:
   - **Question I (20 marks)**: Essay Writing in not less than 300 words choosing one of: (1) Country Life versus Town Life, (2) Choice of Professions, (3) Youth and Social Media -> `english/writing/essay`.

2. **SECTION - B Objective MCQ Section (50 Marks, 50 MCQs)**:
   - **Q1–Q10**: Idioms & Phrases (Hole and corner, Plough the sands, Raw deal, Scot-free, With a grain of salt, Wild-goose chase, Fair and square, Eat humble pie, Chew the cud, Blow hot and cold) -> `english/vocabulary/idioms-and-phrases` (10)
   - **Q11–Q20**: Reading Comprehension passage on the press, newspaper responsibility, freedom of speech, and sensationalism -> `english/comprehension` (10)
   - **Q21–Q30**: Identification of Parts of Speech (evidence, off, like, less, after, pleasing, etc.) -> `english/grammar/parts-of-speech` (10)
   - **Q31–Q35**: Sentence Analysis (simple, compound, and complex sentences) -> `english/grammar` (5)
   - **Q36–Q40**: Sentence Degrees and Forms (degrees of comparison, assertive, affirmative, and negative forms) -> `english/grammar` (5)
   - **Q41–Q45**: Subject-Verb Agreement & Determiners (either/neither, means sufficient, distributive subjects) -> `english/grammar/subject-verb-agreement` (5)
   - **Q46–Q50**: Contextual Synonyms (exonerated, clandestine, promulgate, segregation, ubiquitous) -> `english/vocabulary/synonyms` (5)

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 50 candidate records staged under policy `study-tagging-v1`.
- Complete verification against 6 rendered page images from source PDF.
"""

(out / "README.md").write_text(md)
print("Wrote README.md successfully.")
