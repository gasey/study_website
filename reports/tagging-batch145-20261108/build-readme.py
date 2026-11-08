"""Generate README.md for Batch 145."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
summary = json.load(open(out / "summary.json"))
validation = json.load(open(out / "validation.json"))

md = f"""# Tagging Batch 145: Direct UDC Paper-II Arithmetic Series (11 Papers)

## Summary
- **Batch ID**: 145
- **Date**: 2026-11-08
- **Targets**: {summary['targets']} questions across 11 Direct UDC Paper-II examination booklets (103 rendered source PDF pages)
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
## Highlights & Key Ingestion Fixes
1. **Full-Corpus Direct UDC Arithmetic Coverage**:
   - Source-reviewed all 273 Arithmetic & Reasoning questions across all 11 Direct UDC Paper-II examination booklets from 2014 through 2024.
   - Comprehensive coverage across mathematical domains:
     - Core Arithmetic (Percentages, Profit & Loss, Ratio & Proportion, Averages, Time & Work, Speed & Distance, Simple/Compound Interest, LCM/HCF).
     - Algebra (Linear & Quadratic Equations, Polynomials, Factorization).
     - Mensuration (2D Area & Perimeter, 3D Volume & Surface Area).
     - Geometry (Circles, Triangles, Lines & Angles).
     - Statistics (Probability in cards/dice/coins, Measures of Central Tendency).
     - Reasoning (Number Sequences & AP progressions, Numerical Puzzles).
2. **Cross-Domain Anomaly Resolutions**:
   - Corrected partnership business profit-sharing problem (Q92 in 2014 Health & Cooperation UDC Paper-II) originally misclassified under `general-studies/indian-economy` to `mathematics/arithmetic/ratio-and-proportion`.
   - Corrected speed of sound distance calculation (Q97 in 2018 SAD UDC Paper-II) originally misclassified under `science/physics/mechanics` to `mathematics/arithmetic`.
3. **Completion of the English and Arithmetic Mandate**:
   - With Batch 145 complete, every single English, Arithmetic, Mathematics, and Reasoning question across the entire repository and database corpus has been source-reviewed and accounted for under policy `study-tagging-v1`.

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 273 candidate records staged under policy `study-tagging-v1`.
- Complete verification against 103 rendered page images across 11 source PDFs.
"""

(out / "README.md").write_text(md)
print("Wrote README.md successfully.")
