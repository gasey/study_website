"""Generate README.md for Batch 140."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
summary = json.load(open(out / "summary.json"))
validation = json.load(open(out / "validation.json"))

md = f"""# Tagging Batch 140: Direct General English Papers Collection (2014–2018)

## Summary
- **Batch ID**: 140
- **Date**: 2026-11-08
- **Targets**: {summary['targets']} questions across 5 examination papers ({summary['unextracted_items_preserved']} conventional items preserved, {summary['conventional_marks_preserved']} conventional marks)
- **Completion**: {summary['completion']}
- **Live Changes**: {summary['live_changes']} (All {summary['targets']} candidates remain `pending`)
- **Actions**:
  - `retag`: {summary['actions']['retag']}
  - `keep`: {summary['actions']['keep']}
  - `hold`: {summary['actions']['hold']}
- **Verification**: {validation['source_fingerprints_verified']}/{summary['targets']} source fingerprints re-verified via repeatable-read Oracle readback ({validation['validated_at']}).

## Papers Included
"""

for p in summary["papers"]:
    md += f"- **`{p['paper_id']}`**: {p['targets']} targets (Document ID: `{p['document_id']}`, SHA256: `{p['sha256'][:16]}...`)\n"

md += """
## Topic Breakdown
| Topic / Subtopic | Count |
| :--- | :--- |
"""

for topic, count in sorted(summary['breakdown'].items(), key=lambda x: -x[1]):
    md += f"| `{topic}` | {count} |\n"

md += """
## Paper & Section Breakdown

1. **Assistant Divisional Accountant 2014 General English (`1. General English.pdf`, 5 items)**:
   - **Conventional Preserved**: Q1 Essay on Reading / Economy / Politics / Women (20 marks) and Q2 Précis on Peace and Human Instincts (10 marks).
   - **Q11, Q13, Q14, Q15**: Vocabulary word choice (gracious, assured, panacea, raise) -> `english/vocabulary` (4)
   - **Q12**: Prepositional connective (except that) -> `english/grammar` (1)

2. **CDPO 2016 General English Paper I Common (`1.CDPO under Social Welfare Department 2016 General English Paper I Common.pdf`, 3 items)**:
   - **Q1**: Essay on Child Labour / Status of Women / Drug Abuse -> `english/writing/essay` (1)
   - **Q3**: Official letter to Director, Social Welfare Department -> `english/writing/letter` (1)
   - **Q5**: Expansion of ideas (face is index of mind, uneasy lies head that wears crown) -> `english/writing/essay` (1)

3. **Junior Grade of MES 2015 General English Common (`2. Jr. Grade of MES 2015 General English (Common).pdf`, 1 item)**:
   - **Q1**: Essay on Same sex marriage / Social networking / Swachh Bharat Abhiyan -> `english/writing/essay` (1)

4. **Direct General English Paper 21 (`21. General English.pdf`, 5 items)**:
   - **Q1**: Essay in ~1000 words -> `english/writing/essay` (1)
   - **Q2**: Précis writing in ~one-third length -> `english/writing/precis` (1)
   - **Q3**: Reading comprehension -> `english/comprehension` (1)
   - **Q6**: Word pairs / homophones into sentences -> `english/vocabulary` (1)
   - **Q9**: Idioms and phrases -> `english/vocabulary/idioms-and-phrases` (1)

5. **Direct General English Paper 6 (`6.General English.pdf`, 6 items)**:
   - **Q1**: Essay writing in 800-900 words -> `english/writing/essay` (1)
   - **Q5 (5 items)**: Vocabulary word meanings (invidious, apotheosis, anarchy, fastidious, anomaly) -> `english/vocabulary` (5)

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 20 candidate records staged under policy `study-tagging-v1`.
- Complete verification against 17 rendered page images across 5 source PDFs.
"""

(out / "README.md").write_text(md)
print("Wrote README.md successfully.")
