"""Generate README.md for Batch 81."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
summary = json.load(open(out / "summary.json"))
validation = json.load(open(out / "validation.json"))

md = f"""# Tagging Batch 81: Technical Competitive Examinations for Recruitment to Computer Operator under Mizoram Information Commission (2016) — General English

## Summary
- **Batch ID**: 81
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
- **Paper ID**: `Old_Questions/Direct_2014-2018/1.Computer Operator (CB) under Mizoram Information Commission 2016 General English.pdf`
- **Document ID**: `doc_e4a3e87d3a010bc114cf396a`
- **Source SHA256**: `1e269ab32908628c68ebca988ef4a4ec16b9b3c4f74d08a8047970d47321e06f`
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
1. **Q1–Q8**: Idioms and phrases meaning -> `english/vocabulary/idioms-and-phrases` (8)
2. **Q9–Q16**: Idioms and phrases fill in the blanks -> `english/vocabulary/idioms-and-phrases` (8)
3. **Q17–Q32**: Reading comprehension passages (3 passages) -> `english/comprehension` (16)
4. **Q33–Q37**: Past and perfect tenses -> `english/grammar/tenses` (5)
5. **Q38–Q42**: Correct form of verbs -> `english/grammar/tenses` (5)
6. **Q43–Q48**: Word or phrase usage:
   - **Q43, Q46, Q47, Q48**: Relative pronouns / determiners (what, which, only, whom) -> `english/grammar/parts-of-speech` (4)
   - **Q44**: Preposition selection (looking for) -> `english/grammar/prepositions` (1)
   - **Q45**: Participle / verb form (entering) -> `english/grammar/tenses` (1)
7. **Q49–Q56**: Sentence structure analysis (Simple, Complex, Compound) -> `english/grammar` (8)
8. **Q57–Q61**: Sentence synthesis / avoiding repetition / pronoun substitution -> `english/grammar` (5)
9. **Q62–Q65**: Linking sentences / conjunctions -> `english/grammar` (4)
10. **Q66–Q71**: Vocabulary usage in context -> `english/vocabulary` (6)
11. **Q72–Q76**: Synonyms / similar meaning -> `english/vocabulary/synonyms` (5)
12. **Q77–Q80**: Antonyms / opposite meaning -> `english/vocabulary/antonyms` (4)

## Conventional / Written Section Defect
- **Section A Q1 (Page 1)**: Essay writing on one of three topics (Uses and abuses of social media / The role of youth in nation building / Cleanliness is next to Godliness) 300 words for 20 Marks. Recorded in `pending-written-intake.json`.

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 80 candidates tagged under policy `study-tagging-v1`.
"""

(out / "README.md").write_text(md)
print("Wrote README.md successfully.")
