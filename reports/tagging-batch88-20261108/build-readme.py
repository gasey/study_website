"""Generate README.md for Batch 88."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
summary = json.load(open(out / "summary.json"))
validation = json.load(open(out / "validation.json"))

md = f"""# Tagging Batch 88: Technical Competitive Examinations for Recruitment to Assistant Engineer (Civil) Contract Basis under Trade & Commerce Dept (July 2016) — General English

## Summary
- **Batch ID**: 88
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
- **Paper ID**: `Old_Questions/Direct_2014-2018/4.AE (Civil) under Trade & Commerce 2016 General English.pdf`
- **Document ID**: `doc_8f107f918e95df4a78cb1eb6`
- **Source SHA256**: `874b26d40277792e342894b967d605c4b4d667c5240bc3d2c943b17409c95eb7`
- **Total Questions in Paper**: 20 MCQs (100 Marks total with conventional items)
- **Conventional Sections**: 80 Marks across 5 conventional items: Comprehension Q1 (20m), Précis Q2 (20m), Essay Q3 (20m), Word Pairs Q6 (10m), Idioms Sentences Q7 (10m)

## Topic Breakdown
| Topic / Subtopic | Count |
| :--- | :--- |
"""

for topic, count in sorted(summary['breakdown'].items(), key=lambda x: -x[1]):
    md += f"| `{topic}` | {count} |\n"

md += """
## Section Breakdown
1. **Q1–Q10**: Verb forms and tenses (Choose the correct verb) -> `english/grammar/tenses` (10)
2. **Q11–Q20**: One-word substitution / definitions -> `english/vocabulary/one-word-substitution` (10)

## Conventional / Written Section Defects
- **Q1 (Page 1)**: Comprehension 4 descriptive questions for 20 Marks. Recorded in `pending-written-intake.json`.
- **Q2 (Page 1)**: Précis writing into 1/3 with title for 20 Marks. Recorded in `pending-written-intake.json`.
- **Q3 (Page 2)**: Essay writing on one of three topics (Sustainable Energy / Waste management system / Industries for State development) for 20 Marks. Recorded in `pending-written-intake.json`.
- **Q6 (Page 3)**: Sentence making with 10 word pairs for 10 Marks. Recorded in `pending-written-intake.json`.
- **Q7 (Page 3)**: Explaining and sentence making with 5 idioms for 10 Marks. Recorded in `pending-written-intake.json`.

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 20 candidates tagged under policy `study-tagging-v1`.
"""

(out / "README.md").write_text(md)
print("Wrote README.md successfully.")
