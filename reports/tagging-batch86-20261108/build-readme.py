"""Generate README.md for Batch 86."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
summary = json.load(open(out / "summary.json"))
validation = json.load(open(out / "validation.json"))

md = f"""# Tagging Batch 86: Technical Competitive Examinations for Recruitment to Librarian under Health & Family Welfare Department — General English

## Summary
- **Batch ID**: 86
- **Date**: 2026-11-08
- **Targets**: {summary['targets']} MCQs ({summary['unextracted_items_preserved']} conventional item preserved)
- **Completion**: {summary['completion']}
- **Live Changes**: {summary['live_changes']} (All {summary['targets']} candidates remain `pending`)
- **Actions**:
  - `retag`: {summary['actions']['retag']}
  - `keep`: {summary['actions']['keep']}
  - `hold`: {summary['actions']['hold']}
- **Verification**: {validation['source_fingerprints_verified']}/{summary['targets']} source fingerprints re-verified via repeatable-read Oracle readback ({validation['validated_at']}).

## Paper Details
- **Paper ID**: `Old_Questions/Direct_2014-2018/general-english-under-hfw-deptt.pdf`
- **Document ID**: `doc_eb2bb6d43e5c94e8a4d45be7`
- **Source SHA256**: `a949bd058450b694b293817f7724213d2df807e3240e53a2bb617db08e1ec6b6`
- **Total Questions in Paper**: 40 MCQs (Section B, 80 Marks / 40 questions)
- **Conventional Section**: Section A Essay (20 Marks) on Page 1

## Topic Breakdown
| Topic / Subtopic | Count |
| :--- | :--- |
"""

for topic, count in sorted(summary['breakdown'].items(), key=lambda x: -x[1]):
    md += f"| `{topic}` | {count} |\n"

md += """
## Section Breakdown
1. **Q1–Q8**: Idioms and phrases meaning -> `english/vocabulary/idioms-and-phrases` (8)
2. **Q9–Q14**: Reading comprehension passage (food, cloth and population situation in India) -> `english/comprehension` (6)
3. **Q15–Q19**: Preposition selection -> `english/grammar/prepositions` (5)
4. **Q20–Q24**: Word & phrase selection:
   - **Q20, Q21**: Verb form / subjunctive (if I were, hanged for murder) -> `english/grammar/tenses` (2)
   - **Q22**: Distributive pronoun (either of these two books) -> `english/grammar` (1)
   - **Q23**: Vocabulary (approached the bank) -> `english/vocabulary` (1)
   - **Q24**: Phrasal verb (turned over) -> `english/vocabulary/idioms-and-phrases` (1)
5. **Q25–Q29**: Sentence notion / concept expressed -> `english/grammar` (5)
6. **Q30–Q35**: Sentence structure analysis (Simple, Compound, Complex) -> `english/grammar` (6)
7. **Q36–Q40**: Clause identification (Noun, Adverb, Adjective clause) -> `english/grammar` (5)

## Conventional / Written Section Defect
- **Section A Q1 (Page 1)**: Essay writing on one of three topics (Environmental Pollution / Health is Wealth / Misuse of Mobile Phones) in not more than 300 words for 20 Marks. Recorded in `pending-written-intake.json`.

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 40 candidates tagged under policy `study-tagging-v1`.
"""

(out / "README.md").write_text(md)
print("Wrote README.md successfully.")
