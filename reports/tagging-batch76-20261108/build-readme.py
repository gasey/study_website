"""Generate README.md for Batch 76."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
summary = json.load(open(out / "summary.json"))
validation = json.load(open(out / "validation.json"))

md = f"""# Tagging Batch 76: Technical Competitive Examinations for Junior Scientific Officer (Contract) under Home Dept (May 2016) — General English

## Summary
- **Batch ID**: 76
- **Date**: 2026-11-08
- **Targets**: {summary['targets']} MCQs ({summary['unextracted_items_preserved']} conventional item preserved)
- **Completion**: {summary['completion']}
- **Live Changes**: {summary['live_changes']} (All {summary['targets']} candidates remain `pending`)
- **Actions**:
  - `retag`: {summary['actions']['retag']}
  - `keep`: {summary['actions']['keep']}
  - `hold`: {summary['actions']['hold']}
- **Verification**: {validation['source_fingerprints_verified']}/{summary['targets']} source fingerprints re-verified via repeatable-read Oracle readback ({validation['validated_at']}).

## Paper Details
- **Paper ID**: `Old_Questions/Direct_2014-2018/5.JSO General English 2016 (Common).pdf`
- **Document ID**: `doc_27139f9cee9ec33283e18370`
- **Source SHA256**: `4483dcd4583a9ca4ba61995ee0aa470761e7016acd13f8b9ec5432b026febb98`
- **Total Questions in Paper**: 80 MCQs (Section B, 80 Marks)
- **Conventional Section**: Section A Essay (20 Marks) on Page 1

## Topic Breakdown
| Topic / Subtopic | Count |
| :--- | :--- |
"""

for topic, count in sorted(summary['breakdown'].items(), key=lambda x: -x[1]):
    md += f"| `{topic}` | {count} |\n"

md += """
## Section Breakdown
1. **Q1–Q16**: Idioms and phrases (meaning and fill-in) -> `english/vocabulary/idioms-and-phrases` (16)
2. **Q17–Q22, Q25–Q32**: Reading comprehension passages (Passage 1 & Passage 2) -> `english/comprehension` (14)
3. **Q23**: Passage vocabulary synonym (tranquil) -> `english/vocabulary/synonyms` (1)
4. **Q24**: Passage vocabulary antonym (insidious) -> `english/vocabulary/antonyms` (1)
5. **Q33–Q42**: Simple past vs present perfect tense -> `english/grammar/tenses` (10)
6. **Q43–Q48**: Direct and indirect speech -> `english/grammar/reported-speech` (6)
7. **Q49–Q56**: Sentence structure analysis (Simple, Complex, Compound) -> `english/grammar` (8)
8. **Q57–Q61**: Phrase substitution / sentence correction -> `english/sentence-correction` (5)
9. **Q62–Q65**: Sentence linking / conjunctions -> `english/grammar` (4)
10. **Q66–Q71**: Vocabulary definitions of underlined words -> `english/vocabulary` (6)
11. **Q72–Q76**: Synonyms -> `english/vocabulary/synonyms` (5)
12. **Q77–Q80**: Antonyms -> `english/vocabulary/antonyms` (4)

## Conventional / Written Section Defect
- **Section A Q1 (Page 1)**: Essay writing on one of four topics (Does travel help promote understanding... / Information technology in Mizoram / Education in national development / Love looks not with the eyes) for 20 Marks. Recorded in `pending-written-intake.json`.

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 80 candidates tagged under policy `study-tagging-v1`.
"""

(out / "README.md").write_text(md)
print("Wrote README.md successfully.")
