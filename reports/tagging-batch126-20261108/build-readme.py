"""Generate README.md for Batch 126."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
summary = json.load(open(out / "summary.json"))
validation = json.load(open(out / "validation.json"))

md = f"""# Tagging Batch 126: Stenographer Grade-II (Contract) (May 2025) — Paper-II

## Summary
- **Batch ID**: 126
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
- **Paper ID**: `Old_Questions/Direct_NG_2024-2027/Stenographer Grade-II (Contract) under MPSC - Paper-II..pdf`
- **Document ID**: `{summary['papers'][0]['document_id']}`
- **Source SHA256**: `{summary['papers'][0]['sha256']}`
- **Total Marks in Paper**: 100 Marks (100 Objective MCQs, 1 mark each)
- **Subject Coverage**: General Studies, Current Affairs, Arithmetic (Averages, Percentages, Speed/Distance, Ratio & Proportion, Profit & Loss), and Reasoning & Aptitude (Series, Ranking, Direction Sense, Coding-Decoding)

## Topic Breakdown
| Topic / Subtopic | Count |
| :--- | :--- |
"""

for topic, count in sorted(summary['breakdown'].items(), key=lambda x: -x[1]):
    md += f"| `{topic}` | {count} |\n"

md += """
## Section Breakdown
1. **General Studies & Current Affairs (Q1–Q75, 75 MCQs)**:
   - **Q1–Q10, Q12, Q14, Q16–Q19, Q21–Q23, Q25–Q27, Q29–Q32, Q34–Q36, Q39–Q51, Q53–Q55, Q57–Q60, Q63–Q64, Q67–Q70, Q72–Q75**: National and international current affairs, government schemes, bilateral relations, summits, and awards -> `general-studies/current-affairs` (58)
   - **Q1, Q4, Q13, Q24, Q33, Q56, Q61, Q62, Q66, Q71**: Domestic and international sports championships, tournaments, medals, and venues -> `general-knowledge/sports` (10)
   - **Q20, Q52, Q65**: Constitutional provisions (Right to Know, Census Union subject under Art 246, President's Rule under Art 356) -> `general-studies/indian-polity` (3)
   - **Q11, Q28**: Geography: National parks and wildlife sanctuaries in India -> `general-studies/geography` (2)
   - **Q37, Q38**: Archaeological discoveries and UNESCO Memory of the World classical texts -> `general-knowledge/art-and-culture` (2)
2. **Arithmetic (Q76–Q88, 13 MCQs)**:
   - **Q76–Q77**: Averages in context -> `mathematics/arithmetic/averages` (2)
   - **Q78–Q79**: Percentages and successive percentage change -> `mathematics/arithmetic/percentages` (2)
   - **Q80–Q81**: Speed, distance, time, and train length problems -> `mathematics/arithmetic` (2)
   - **Q82–Q84**: Ratios, proportions, and mixture problems -> `mathematics/arithmetic/ratio-and-proportion` (3)
   - **Q85–Q88**: Profit and loss, discounts, and percentage gain/loss -> `mathematics/arithmetic/profit-and-loss` (4)
3. **Reasoning & Aptitude (Q89–Q100, 12 MCQs)**:
   - **Q89, Q90, Q92, Q93**: Number series completion and sequence patterns -> `reasoning-and-aptitude/series` (4)
   - **Q91, Q94–Q100**: Verbal and analytical reasoning (coding-decoding, linear ranking and order, alphabet position values, direction sense) -> `reasoning-and-aptitude/verbal-reasoning` (8)

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 100 candidate records staged under policy `study-tagging-v1`.
- Complete verification against 9 rendered page images from source PDF.
"""

(out / "README.md").write_text(md)
print("Wrote README.md successfully.")
