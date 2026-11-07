"""Generate README.md for Batch 84."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
summary = json.load(open(out / "summary.json"))
validation = json.load(open(out / "validation.json"))

md = f"""# Tagging Batch 84: Written Examinations for Recruitment to Stenographer Grade-II (Contract) under DP&AR (May 2015) — General English

## Summary
- **Batch ID**: 84
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
- **Paper ID**: `Old_Questions/Direct_2014-2018/1.STENOGRAPHER GRADE-II (CONTRACT) UNDER DP&AR (SSW),2015General English.pdf`
- **Document ID**: `doc_e4ea50d99042b325203308ec`
- **Source SHA256**: `0916398a402f44709d22cbe2857ce79f83ea032488a0862590740a6b7e09ea9d`
- **Total Questions in Paper**: 50 MCQs (Section B, 80 Marks / 50 questions)
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
2. **Q9–Q14**: Reading comprehension passage (cement tile manufacturing crisis) -> `english/comprehension` (6)
3. **Q15–Q24**: Parts of speech fill in the blanks:
   - **Q15, Q20, Q22, Q23, Q24**: Prepositions -> `english/grammar/prepositions` (5)
   - **Q16, Q17, Q18, Q19, Q21**: Adjectives, adverbs, degrees of comparison -> `english/grammar/parts-of-speech` (5)
4. **Q25–Q30**: Sentence notion / concept expressed -> `english/grammar` (6)
5. **Q31–Q36**: Sentence structure analysis (Simple, Compound, Complex) -> `english/grammar` (6)
6. **Q37–Q42**: Clause identification (Noun, Adverb, Adjective clause) -> `english/grammar` (6)
7. **Q43–Q50**: Word choice & vocabulary in context:
   - **Q43, Q44, Q45, Q49, Q50**: Word choice / vocabulary -> `english/vocabulary` (5)
   - **Q46, Q48**: Idioms in context (took to their heels, smells a rat) -> `english/vocabulary/idioms-and-phrases` (2)
   - **Q47**: One word substitution definition -> `english/vocabulary/one-word-substitution` (1)

## Conventional / Written Section Defect
- **Section A Q1 (Page 1)**: Essay writing on one of three topics (Social media and its impact on society / Role and significance of NGO’s in Mizoram / Crime against women in India) in not more than 300 words for 20 Marks. Recorded in `pending-written-intake.json`.

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 50 candidates tagged under policy `study-tagging-v1`.
"""

(out / "README.md").write_text(md)
print("Wrote README.md successfully.")
