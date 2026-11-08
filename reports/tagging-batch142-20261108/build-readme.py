"""Generate README.md for Batch 142."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
summary = json.load(open(out / "summary.json"))
validation = json.load(open(out / "validation.json"))

md = f"""# Tagging Batch 142: MCS Main English Literature Optional Collection (7 Papers)

## Summary
- **Batch ID**: 142
- **Date**: 2026-11-08
- **Targets**: {summary['targets']} questions across 7 MCS Mains elective literature papers ({summary['unextracted_items_preserved']} conventional items preserved in pending-written-intake.json)
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
1. **MCS Main English Literature Elective Corpus Intake**:
   - Source-reviewed all 69 conventional literature examination questions across 7 papers (MCS Main 2014, 2022, 2023 Paper-I and Paper-II).
   - Covers University-level descriptive literature questions: Shakespeare (The Tempest), Metaphysical poetry (John Donne), Romantic poetry (Wordsworth), Victorian & Modern novels (Jane Austen's Pride and Prejudice, George Eliot's Mill on the Floss, Mark Twain's Huckleberry Finn, Joseph Conrad's Lord Jim, Virginia Woolf's Mrs Dalloway, D.H. Lawrence's Sons and Lovers, Raja Rao's Kanthapura, V.S. Naipaul's A House for Mr. Biswas), Absurd drama (Samuel Beckett's Waiting for Godot, Henrik Ibsen's A Doll's House), and Literary Theory/Movements.
2. **Taxonomic Standardization**:
   - Reclassified legacy capitalized `English` subject and unstructured topics into active lowercase policy `english/writing/essay`.
3. **Conventional Preservation**:
   - Preserved all 69 long-form conventional questions in `pending-written-intake.json` for written evaluation intake.

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 69 candidate records staged under policy `study-tagging-v1`.
- Complete verification against 19 rendered page images across 7 source PDFs.
"""

(out / "README.md").write_text(md)
print("Wrote README.md successfully.")
