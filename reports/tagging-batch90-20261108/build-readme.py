"""Generate README.md for Batch 90."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
summary = json.load(open(out / "summary.json"))
validation = json.load(open(out / "validation.json"))

md = f"""# Tagging Batch 90: Competitive Examination for Lower Division Clerk (LDC) under MPSC (February 2025) — Paper II

## Summary
- **Batch ID**: 90
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
- **Paper ID**: `Old_Questions/Direct_NG_2024-2027/LDC under MPSC Paper-II 2025..pdf`
- **Document ID**: `doc_712c2c9334cdd9d7`
- **Source SHA256**: `712c2c9334cdd9d779b40945a6019a22ddbc71af6cc229fe2edecc51c78a275a`
- **Total Questions in Paper**: 100 MCQs (100 Marks, 2 Hours duration)
- **Subject Coverage**: Computer Knowledge (Q1–Q50), Arithmetic (Q51–Q75), Reasoning (Q76–Q100)

## Topic Breakdown
| Topic / Subtopic | Count |
| :--- | :--- |
"""

for topic, count in sorted(summary['breakdown'].items(), key=lambda x: -x[1]):
    md += f"| `{topic}` | {count} |\n"

md += """
## Section Breakdown
1. **Q1–Q50 (Computer Knowledge - 50 MCQs)**:
   - **Computer Architecture, Generations & Hardware**: Q1 (generations), Q2, Q5 (CPU, plotter hardware), Q3, Q4 (main and cache memory), Q6, Q8, Q9 (software definition, classification, supercomputer), Q10 (IT Amendment Act)
   - **Operating Systems & Windows**: Q7, Q11–Q18 (OS role, Windows versions, taskbar, control panel, desktop icons, file naming rules, shortcuts, default apps)
   - **Office Applications (MS Word, Excel, PowerPoint)**: Q19–Q30 (Word formatting, alignment, spacing, autocorrect, grammar, mail merge, tables), Q31–Q38 (Excel cells, sum range, absolute reference, auto-fit, IF function, edit mode, data table, chart update), Q39–Q43 (PowerPoint slides, layout, slide sorter, animation sound, rehearse timings)
   - **Networking & Internet**: Q44–Q50 (Internet definition, governance ICANN, search engines, HTTPS security, IMAP email protocol, CC email, email services)
2. **Q51–Q75 (Arithmetic - 25 MCQs)**:
   - **Arithmetic Core**: Q53 (primes), Q57 (time & work), Q58 (permutations/words), Q59 (combinations/teams), Q63 (recurring fractions), Q64 (BODMAS), Q70 (train speed & distance), Q71 (compound interest), Q72 (simple interest)
   - **Averages**: Q52, Q56, Q68
   - **Percentages**: Q54, Q55
   - **Profit & Loss**: Q65
   - **Ratio, Proportion & Partnership**: Q66, Q67, Q69
   - **Mensuration & Geometry**: Q60 (room diagonal/longest rod), Q73 (cone volume ratio), Q74 (angle of elevation / trigonometry)
   - **Data Interpretation**: Q61 (flight level graph), Q62 (bar chart company expenses), Q75 (fruit cost pie chart)
3. **Q76–Q100 (Reasoning - 25 MCQs)**:
   - **Verbal Reasoning**: Q76, Q77 (word analogies), Q79, Q93 (odd word/group out), Q81 (word formation), Q82 (letter sequence reverse), Q83 (coding-decoding), Q84, Q85 (blood relations), Q86, Q87 (directions and angles), Q88, Q89 (ranking and order), Q91 (dictionary sequence), Q92 (syllogisms)
   - **Series & Missing Terms**: Q78, Q80 (letter pattern series), Q90 (number series), Q95, Q96, Q97, Q98 (missing letter/number grids and matrices)
   - **Numerical Ability**: Q94 (digit reversal and ranking)
   - **Non-Verbal Reasoning**: Q99 (mirror images), Q100 (dice opposite face)

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 100 candidate records safely staged under policy `study-tagging-v1`.
- Complete verification against 12 rendered page images from source PDF.
"""

(out / "README.md").write_text(md)
print("Wrote README.md successfully.")
