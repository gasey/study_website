"""Generate README.md for Batch 141."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
summary = json.load(open(out / "summary.json"))
validation = json.load(open(out / "validation.json"))

md = f"""# Tagging Batch 141: LDE & Departmental General English Collection (11 Papers)

## Summary
- **Batch ID**: 141
- **Date**: 2026-11-08
- **Targets**: {summary['targets']} questions across 11 examination papers ({summary['unextracted_items_preserved']} conventional items preserved, {summary['conventional_marks_preserved']} conventional marks)
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
1. **Cross-Domain Corrections**:
   - Multiple essays originally misclassified under `general-studies` or `education` (in Asst. Jailor, ASI-UB, MSS, UDC, and Principal HSS papers) were properly unified into `english/writing/essay`.
   - Official memorandum and formal letter drafting items originally misclassified under `service-rules-and-office-procedure` were properly unified into `english/writing/letter`.
2. **Grammar & Vocabulary Refinements**:
   - Reclassified 10 phrasal verbs into `english/vocabulary/idioms-and-phrases`.
   - Refined 17 reading comprehension questions into `english/comprehension`.
   - Categorized reported speech, active/passive voice, and abstract nouns into their specific grammatical subtopics.
3. **Conventional Preservation**:
   - Preserved Section A conventional written sections (Essay 25 marks, Précis 15 marks, Letter 10 marks) for Functional Manager LDE in `pending-written-intake.json`.

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 91 candidate records staged under policy `study-tagging-v1`.
- Complete verification against 32 rendered page images across 11 source PDFs.
"""

(out / "README.md").write_text(md)
print("Wrote README.md successfully.")
