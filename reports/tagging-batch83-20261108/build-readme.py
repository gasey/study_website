"""Generate README.md for Batch 83."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
summary = json.load(open(out / "summary.json"))
validation = json.load(open(out / "validation.json"))

md = f"""# Tagging Batch 83: General Competitive Examinations for Junior Grade of Mizoram Forest Service (ACF) (2018) — General English

## Summary
- **Batch ID**: 83
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
- **Paper ID**: `Old_Questions/Direct_2014-2018/ACF General English.pdf`
- **Document ID**: `doc_eb2da5629158c3db0a463a50`
- **Source SHA256**: `6278bf717fc23659a5d13ba5863d047b744d08a54d6fa069502b4dbe5a539eb8`
- **Total Questions in Paper**: 65 MCQs (Section B, 65 Marks)
- **Conventional Section**: Section A Essay (20 Marks) and Précis (15 Marks) on Page 1 (35 Marks total)

## Topic Breakdown
| Topic / Subtopic | Count |
| :--- | :--- |
"""

for topic, count in sorted(summary['breakdown'].items(), key=lambda x: -x[1]):
    md += f"| `{topic}` | {count} |\n"

md += """
## Section Breakdown
1. **Q1–Q10**: Verb forms and tenses -> `english/grammar/tenses` (10)
2. **Q11–Q20**: Parts of speech identification -> `english/grammar/parts-of-speech` (10)
3. **Q21–Q30**: Preposition selection -> `english/grammar/prepositions` (10)
4. **Q31–Q40**: Idioms and phrases meaning -> `english/vocabulary/idioms-and-phrases` (10)
5. **Q41–Q50**: Sentence notions and modal concepts (possibility, obligation, request, command, invitation) -> `english/grammar` (10)
6. **Q51–Q60**: Conjunction selection -> `english/grammar` (10)
7. **Q61–Q65**: One word substitution -> `english/vocabulary/one-word-substitution` (5)

## Conventional / Written Section Defect
- **Section A Q I (Page 1)**: Essay writing on one of three topics (Conservation of the flora and fauna in Mizoram / Impact of technology in Society / Environmental Problems and its Solutions) for 20 Marks. Recorded in `pending-written-intake.json`.
- **Section A Q II (Page 1)**: Précis writing on technology and human alienation for 15 Marks. Recorded in `pending-written-intake.json`.

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 65 candidates tagged under policy `study-tagging-v1`.
"""

(out / "README.md").write_text(md)
print("Wrote README.md successfully.")
