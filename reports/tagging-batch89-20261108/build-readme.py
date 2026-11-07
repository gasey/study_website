"""Generate README.md for Batch 89."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
summary = json.load(open(out / "summary.json"))
validation = json.load(open(out / "validation.json"))

md = f"""# Tagging Batch 89: Combined Services / Departmental Examinations (CSM: 17) — General English

## Summary
- **Batch ID**: 89
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
- **Paper ID**: `Old_Questions/Direct_2014-2018/13.General English.pdf`
- **Document ID**: `doc_eb2bb5df817e94df40f1a4e7`
- **Source SHA256**: `27621b4231413956bf3a07c12662c8ce12046e7f722c3e164f9b2d35e80fa9fa`
- **Total Questions in Paper**: 10 MCQs (Question 9 a–j, 10 Marks; 95 Marks conventional written sections)
- **Conventional Sections**: 95 Marks across 9 conventional items: Essay Q1 (20m), Précis Q2 (15m), Comprehension Q3 (15m), Grammar Q4 (10m), Prepositions Q5 (5m), Connectors Q6 (5m), Voice Q7 (10m), Word Pairs Q8 (10m), Articles Q10 (5m)

## Topic Breakdown
| Topic / Subtopic | Count |
| :--- | :--- |
"""

for topic, count in sorted(summary['breakdown'].items(), key=lambda x: -x[1]):
    md += f"| `{topic}` | {count} |\n"

md += """
## Section Breakdown
1. **Q9(a)–(e), Q9(h)**: One-word substitution / term definitions (etymologist, domicile, acquaintance, articulate, posthumous, epitaph) -> `english/vocabulary/one-word-substitution` (6)
2. **Q9(f), Q9(g)**: Collective nouns (lions: pride, cars: fleet) -> `english/vocabulary` (2)
3. **Q9(i), Q9(j)**: Vocabulary / relationships / figures of speech (niece, oxymoron) -> `english/vocabulary` (2)

## Conventional / Written Section Defects
- **Q1 (Page 1)**: Short essay writing on one of four topics for 20 Marks. Recorded in `pending-written-intake.json`.
- **Q2 (Page 1)**: Précis writing on courage for 15 Marks. Recorded in `pending-written-intake.json`.
- **Q3 (Page 2)**: Comprehension questions on art and beauty for 15 Marks. Recorded in `pending-written-intake.json`.
- **Q4 (Page 2)**: Grammar correction and composition for 10 Marks. Recorded in `pending-written-intake.json`.
- **Q5 (Page 3)**: Preposition fill-in-blanks for 5 Marks. Recorded in `pending-written-intake.json`.
- **Q6 (Page 3)**: Connectors fill-in-blanks for 5 Marks. Recorded in `pending-written-intake.json`.
- **Q7 (Page 3)**: Voice transformation for 10 Marks. Recorded in `pending-written-intake.json`.
- **Q8 (Page 3)**: Word pairs sentence making for 10 Marks. Recorded in `pending-written-intake.json`.
- **Q10 (Page 4)**: Articles insertion for 5 Marks. Recorded in `pending-written-intake.json`.

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 10 candidates tagged under policy `study-tagging-v1`.
"""

(out / "README.md").write_text(md)
print("Wrote README.md successfully.")
