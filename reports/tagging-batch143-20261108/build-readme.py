"""Generate README.md for Batch 143."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
summary = json.load(open(out / "summary.json"))
validation = json.load(open(out / "validation.json"))

md = f"""# Tagging Batch 143: Remaining Direct General English Papers & Stray Intake (4 Papers)

## Summary
- **Batch ID**: 143
- **Date**: 2026-11-08
- **Targets**: {summary['targets']} questions across 4 Direct General English examination papers ({summary['unextracted_items_preserved']} conventional items preserved, {summary['conventional_marks_preserved']} conventional marks)
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
1. **Direct General English Papers Reviewed**:
   - `Genral Enlish..pdf` (SI under Excise 2014): 7 MCQs source-reviewed across parts of speech (nouns/adjectives), subject-verb agreement (Everyone was), prepositions (prefer ... to), comparative degrees (more useful than), and idioms/phrasal verbs (for sale, keep up with).
   - `General Englsih Paper-I (EO).pdf` (Employment Officer Paper I): 6 MCQs on English idioms and phrases (Hard-pressed, loggerheads, throw down the glove, shoot one's bolt, carry one's point, drive home).
2. **Conventional Written Sections Intake**:
   - Preserved Section A conventional written items (Précis 25 marks, Letter 25 marks) for Group B Gazetted General English (`768a298...`) in `pending-written-intake.json`.
   - Preserved Section B conventional written items (Essay 25 marks, Précis 15 marks, Reading Comprehension 10 marks) for LDC Paper-I 2025 in `pending-written-intake.json`.
3. **Typographical Paper Titles Documented**:
   - Source filenames `Genral Enlish..pdf` and `General Englsih Paper-I (EO).pdf` contain legacy typographical errors, correctly identified and mapped.

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 18 candidate records staged under policy `study-tagging-v1`.
- Complete verification against 26 rendered page images across 4 source PDFs.
"""

(out / "README.md").write_text(md)
print("Wrote README.md successfully.")
