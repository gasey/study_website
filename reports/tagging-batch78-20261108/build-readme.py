"""Generate README.md for Batch 78."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
summary = json.load(open(out / "summary.json"))
validation = json.load(open(out / "validation.json"))

md = f"""# Tagging Batch 78: Competitive Examinations for Recruitment to Assistant Tourist Officer under Tourism Department (December, 2017) — General English

## Summary
- **Batch ID**: 78
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
- **Paper ID**: `Old_Questions/Direct_2014-2018/1.ATO General English.pdf`
- **Document ID**: `doc_fe7a66559c7eb4bde50c19a9`
- **Source SHA256**: `83366651554541d5c8eb8223f2dbb761de9b3182d01864aefdfb7219e649c2a5`
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
1. **Q1–Q6**: Reading comprehension passage (poem) -> `english/comprehension` (6)
2. **Q7–Q12**: Reading comprehension passage vocabulary (synonyms in context) -> `english/comprehension` (6)
3. **Q13–Q17**: Verb form and tense selection -> `english/grammar/tenses` (5)
4. **Q18–Q22**: Preposition selection -> `english/grammar/prepositions` (5)
5. **Q23–Q32**: Parts of speech identification -> `english/grammar/parts-of-speech` (10)
6. **Q33–Q38**: Sentence structure (Simple, Compound, Complex) -> `english/grammar` (6)
7. **Q39–Q43**: Sentence functional classification (Affirmative, Assertive, Interrogative, Negative) -> `english/grammar` (5)
8. **Q44–Q48**: Clause identification (Adjective, Adverb, Noun clause) -> `english/grammar` (5)
9. **Q49–Q55**: One word substitution -> `english/vocabulary/one-word-substitution` (7)
10. **Q56–Q60**: Synonyms -> `english/vocabulary/synonyms` (5)
11. **Q61–Q65**: Idioms & phrases / phrase similar in meaning -> `english/vocabulary/idioms-and-phrases` (5)
12. **Q66–Q70**: Animal cries / vocabulary -> `english/vocabulary` (5)
13. **Q71–Q80**: Idioms & phrases meaning -> `english/vocabulary/idioms-and-phrases` (10)

## Conventional / Written Section Defect
- **Section A Q1 (Page 1)**: Essay writing on one of three topics (Problems and Pleasures of City Life / Economical importance of Tourism in India / My Idea of Success) not more than 300 words for 20 Marks. Recorded in `pending-written-intake.json`.

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 80 candidates tagged under policy `study-tagging-v1`.
"""

(out / "README.md").write_text(md)
print("Wrote README.md successfully.")
