"""Generate README.md for Batch 139."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
summary = json.load(open(out / "summary.json"))
validation = json.load(open(out / "validation.json"))

md = f"""# Tagging Batch 139: MCS Mains General English Collection (2014, 2022, 2023, 2025)

## Summary
- **Batch ID**: 139
- **Date**: 2026-11-08
- **Targets**: {summary['targets']} questions across 4 MCS Main examinations ({summary['unextracted_items_preserved']} conventional items preserved, {summary['conventional_marks_preserved']} conventional marks)
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
## Paper & Question Breakdown

### 1. MCS Main 2014 General English (`doc_45e5a25777a2fbc67bbc54e5`, 7 items)
- **Conventional Preserved**: Q1 Essay Writing (20 marks) on FIFA World Cup / Mizoram Economy / IT Transformation; Q2 Précis Writing (15 marks) on Indian theatre and cinema.
- **Q4(g)(i)–(ii)**: Grammar determiners (`some`/`any`) and adverbs (`still`/`yet`) -> `english/grammar` (2)
- **Q8(a)–(d)**: Homophones (`stationary`/`stationery`, `descent`/`dissent`, `council`/`counsel`, `precede`/`proceed`) -> `english/vocabulary` (4)
- **Q8(e)**: Modals (`Can`/`May`) -> `english/grammar` (1)

### 2. MCS Main 2022 General English (`doc_fc219fb86b2a1c5f010dc87a`, 7 items)
- **Conventional Preserved**: Q2 Précis Writing (15 marks) on citizen character and national strength; Q3 Formal Letter Writing (10 marks) to Local Council Chairman.
- **Q1a, 1b, 1d, 1e, 1f, 1g**: Reading comprehension passage on password fatigue, SSO software, and biometrics -> `english/comprehension` (6)
- **Q1c**: Synonym in context (`mitigate` -> `lessen`) -> `english/vocabulary/synonyms` (1)

### 3. MCS Main 2023 General English (`doc_47386efa3f8ad958fe3a67be`, 5 items)
- **Q1**: Reading comprehension questions on William Hazlitt passage on journey and solitude -> `english/comprehension` (1)
- **Q2**: Précis writing on knowledge is power and education history -> `english/writing/precis` (1)
- **Q3**: Formal letter writing to Local Council on drainage system -> `english/writing/letter` (1)
- **Q6**: Sentence transformations (10 grammatical conversions) -> `english/grammar` (1)
- **Q9**: Expansion of ideas (short essays on proverbs) -> `english/writing/essay` (1)

### 4. MCS Main 2025 General English (`doc_b546f1a2adc30b19a5ef6076`, 2 items)
- **Conventional Preserved**: Q1 Short Essays (2x50 = 100 marks) on 5 contemporary topics; Q4 Précis Writing (20 marks); Q5 Formal Letter Writing (15 marks) to AMC.
- **Q1–Q2**: Reading comprehension on adolescent peer pressure and contextual vocabulary -> `english/comprehension` (2)

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 21 candidate records staged under policy `study-tagging-v1`.
- Complete verification against 18 rendered page images across 4 source PDFs.
"""

(out / "README.md").write_text(md)
print("Wrote README.md successfully.")
