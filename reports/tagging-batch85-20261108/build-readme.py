"""Generate README.md for Batch 85."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
summary = json.load(open(out / "summary.json"))
validation = json.load(open(out / "validation.json"))

md = f"""# Tagging Batch 85: Technical Competitive Examinations for Recruitment to X-Ray Technician & Laboratory Technician (February, 2017) — General English

## Summary
- **Batch ID**: 85
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
- **Paper ID**: `Old_Questions/Direct_2014-2018/1.General English.pdf`
- **Document ID**: `doc_6e026ce1a2e737c020d2d3a3`
- **Source SHA256**: `23ee0f540a5a848074d2fe94326f29eeea63a0336ae56bc5e4a81ba6d8fbf4da`
- **Total Questions in Paper**: 46 MCQs (Section B, 80 Marks total with conventional items)
- **Conventional Section**: Question 1 Essay (20 Marks) on Page 1 and Question 2(f) Passage Title (1 Mark) on Page 2 (21 Marks total)

## Topic Breakdown
| Topic / Subtopic | Count |
| :--- | :--- |
"""

for topic, count in sorted(summary['breakdown'].items(), key=lambda x: -x[1]):
    md += f"| `{topic}` | {count} |\n"

md += """
## Section Breakdown
1. **Q1–Q5**: Reading comprehension passage -> `english/comprehension` (5)
2. **Q6–Q13**: Idioms and phrases meaning -> `english/vocabulary/idioms-and-phrases` (8)
3. **Q14–Q23**: Parts of speech identification -> `english/grammar/parts-of-speech` (10)
4. **Q24–Q31**: Preposition fill in the blanks -> `english/grammar/prepositions` (8)
5. **Q32–Q36**: Sentence structure analysis (Simple, Compound, Complex) -> `english/grammar` (5)
6. **Q37–Q41**: Sentence correction / phrase replacement -> `english/sentence-correction` (5)
7. **Q42–Q46**: Sentence transformation (into Compound, Complex, Simple) -> `english/grammar` (5)

## Conventional / Written Section Defect
- **Q1 (Page 1)**: Essay writing on one of four topics (Advantages and Disadvantages of Mobile Phones / Problems faced by the Public due to Demonitisation / Preservation of Wildlife / Awareness on Health Issues is a must for the Public) for 20 Marks. Recorded in `pending-written-intake.json`.
- **Q2(f) (Page 2)**: Supply a suitable title to the passage for 1 Mark. Recorded in `pending-written-intake.json`.

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 46 candidates tagged under policy `study-tagging-v1`.
"""

(out / "README.md").write_text(md)
print("Wrote README.md successfully.")
