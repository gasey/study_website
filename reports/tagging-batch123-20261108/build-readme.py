"""Generate README.md for Batch 123."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
summary = json.load(open(out / "summary.json"))
validation = json.load(open(out / "validation.json"))

md = f"""# Tagging Batch 123: Assistant under MPSC (2019) — Paper-I

## Summary
- **Batch ID**: 123
- **Date**: 2026-11-08
- **Targets**: {summary['targets']} items (75 objective MCQs + 2 conventional written items; {summary['unextracted_items_preserved']} conventional items preserved, {summary['conventional_marks_preserved']} conventional marks)
- **Completion**: {summary['completion']}
- **Live Changes**: {summary['live_changes']} (All {summary['targets']} candidates remain `pending`)
- **Actions**:
  - `retag`: {summary['actions']['retag']}
  - `keep`: {summary['actions']['keep']}
  - `hold`: {summary['actions']['hold']}
- **Verification**: {validation['source_fingerprints_verified']}/{summary['targets']} source fingerprints re-verified via repeatable-read Oracle readback ({validation['validated_at']}).

## Paper Details
- **Paper ID**: `Old_Questions/Direct_2019-2020/Asst. Grade under MPSC Paper-1.pdf`
- **Document ID**: `{summary['papers'][0]['document_id']}`
- **Source SHA256**: `{summary['papers'][0]['sha256']}`
- **Total Marks in Paper**: 125 Marks (Section A: 50 Conventional Marks [Essay 25 Marks, Précis 25 Marks] + Section B: 75 MCQs [75 Marks])
- **Subject Coverage**: General English (Essay Writing, Précis Writing, Parts of Speech, Sentence Classification, Verb Tenses & Forms, Prepositions, Connecting Words / Conjunctions, Adjectives, Question Tags)

## Topic Breakdown
| Topic / Subtopic | Count |
| :--- | :--- |
"""

for topic, count in sorted(summary['breakdown'].items(), key=lambda x: -x[1]):
    md += f"| `{topic}` | {count} |\n"

md += """
## Section Breakdown
1. **Section A (Conventional, 50 Marks)**:
   - **W1**: Essay composition on technology enslavement / role of newspapers / festivals in Mizoram (not less than 350 words, 25 Marks) -> `english/writing/essay` (1)
   - **W2**: Précis writing on trees and noble character of good men (one third length with title, 25 Marks) -> `english/writing/precis` (1)
2. **Section B (MCQs, 75 Marks)**:
   - **Q1–Q10**: Functional parts of speech identification (verb, conjunction, adjective, noun, adverb, pronoun, preposition) -> `english/grammar/parts-of-speech` (10)
   - **Q11–Q20**: Sentence classification (declarative, interrogative, imperative, exclamatory, simple, compound, complex) -> `english/grammar` (10)
   - **Q21–Q30**: Verb tenses and aspects identification (simple past, present continuous, past perfect, future continuous, present perfect, etc.) -> `english/grammar/tenses` (10)
   - **Q31–Q40**: Appropriate prepositions in context (at, on, in, by, with, for, into, of) -> `english/grammar/prepositions` (10)
   - **Q41–Q50**: Verb forms and agreement in context (went, has lived, was reading, had finished, will go, etc.) -> `english/grammar/tenses` (10)
   - **Q51–Q60**: Connecting words / conjunctions (because, although, unless, but, if, so that) -> `english/grammar/parts-of-speech` (10)
   - **Q61–Q70**: Suitable adjective selection and usage in context -> `english/grammar/parts-of-speech` (10)
   - **Q71–Q75**: Question tags mechanics (doesn't she, can she, have they, etc.) -> `english/grammar` (5)

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 77 candidate records staged under policy `study-tagging-v1`.
- Complete verification against 8 rendered page images from source PDF.
"""

(out / "README.md").write_text(md)
print("Wrote README.md successfully.")
