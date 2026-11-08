"""Generate README.md for Batch 144."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
summary = json.load(open(out / "summary.json"))
validation = json.load(open(out / "validation.json"))

md = f"""# Tagging Batch 144: Mizoram Legal Service 2016 Aptitude & English Vocabulary + Deduplication Register

## Summary
- **Batch ID**: 144
- **Date**: 2026-11-08
- **Targets**: {summary['targets']} questions in Mizoram Legal Service 2016 GK & Aptitude Test
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
1. **Mizoram Legal Service 2016 Aptitude & Vocabulary Partitioning**:
   - Source-reviewed Questions 81-100 in `5.Jr. Administrative Grade and Sr. Grade of Mizoram Legal Service 2016 GK & Aptitute Test (Common).pdf`.
   - Partitioned into 9 Verbal Reasoning questions (logical reasoning and analogical classification), 6 Vocabulary Synonyms (Obnoxious, Liberty, Flaunt, Degrade, Persuade, Crave), 3 Arithmetic and Ratio problems (unitary method, speed-distance-time, time-and-work), 1 One-Word Substitution (Agoraphobia), and 1 Proverb/Idiom.
2. **Series Permutation Deduplication Ledger**:
   - Formally catalogued and documented secondary permutation booklets: CAO March-2026 Series B (66 items, duplicate of Series A from Batch 120), Jr. Accounts Officer Paper-I Series B (63 items, duplicate of Series A from Batch 114), Jr. Accounts Officer Paper-II Series B (4 items, duplicate of Series A from Batches 14 & 128), Direct NG General English Series B/C/D, and Uploaded Group B Gazetted Series B.
   - Under single-booklet deduplication policy, all secondary permutation series are safely bypassed without double-counting or database clutter.
3. **Geology Paper-III Misnomer Defect Register**:
   - Formally registered defect for `Geologist Junior General English Paper-III.pdf` (96 items) and `Geologist Junior General Englsih Paper-III Nov.pdf` (99 items). Source PDF visual examination proves these are Technical Geology Paper-III exams (Structural Geology, Stratigraphy, Petrology) mislabeled by original uploaders.

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 20 candidate records staged under policy `study-tagging-v1`.
- Complete verification against 9 rendered page images from source PDF.
"""

(out / "README.md").write_text(md)
print("Wrote README.md successfully.")
