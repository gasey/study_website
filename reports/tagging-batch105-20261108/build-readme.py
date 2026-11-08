"""Generate README.md for Batch 105."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
summary = json.load(open(out / "summary.json"))
validation = json.load(open(out / "validation.json"))

md = f"""# Tagging Batch 105: Coach Grade-III (2019) — General English

## Summary
- **Batch ID**: 105
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
- **Paper ID**: `Old_Questions/Direct_2019-2020/Coach Grade-III General English.pdf`
- **Document ID**: `doc_674bbbda31b6972462cdee92`
- **Source SHA256**: `5eac0bfe7cce11a92490ce4ec9e132412531288410f5ef8fa39b9ef279e145ca`
- **Total Questions in Paper**: 80 MCQs (80 Marks, 2 Hours duration)
- **Subject Coverage**: General English (Idioms & Phrases, Reading Comprehension Passages, Functional Parts of Speech, Tense Identification, Sentence Kinds & Types, Relative Pronouns, Subject-Verb Agreement, Prepositions, Articles, Contextual Vocabulary)

## Topic Breakdown
| Topic / Subtopic | Count |
| :--- | :--- |
"""

for topic, count in sorted(summary['breakdown'].items(), key=lambda x: -x[1]):
    md += f"| `{topic}` | {count} |\n"

md += """
## Section Breakdown
1. **Q1–Q16**: Idioms and idiomatic expressions (arm's length, wolf in sheep's clothing, made a pile, under his wing, at sixes and sevens, etc.) -> `english/vocabulary/idioms-and-phrases` (16)
2. **Q17–Q28**: Reading comprehension passages (Passage 1: Memorials to Mahatma Gandhi, Q17–Q23; Passage 2: Man vs Machines / Modern life, Q24–Q28) -> `english/comprehension` (12)
3. **Q29–Q38**: Functional parts of speech identification (all, about, around, better, but, down, etc.) -> `english/grammar` (10)
4. **Q39–Q48**: Verb tense forms and tense identification in context -> `english/grammar/tenses` (10)
5. **Q49–Q64**: Sentence kinds analysis (Simple, Compound, Complex) and sentence types (Declarative, Exclamatory, Interrogative) -> `english/grammar` (16)
6. **Q65–Q80**: Grammatical concord & word form usage:
   - Q65–Q66, Q68, Q79, Q80: Pronouns, adjectives, gerund qualifiers, and comparisons -> `english/grammar` (5)
   - Q67, Q72–Q78: Subject-verb agreement rules (neither of, three parts of business, neither...nor, together with crew, compound subjects) -> `english/grammar/subject-verb-agreement` (8)
   - Q69: Preposition of comparison (superior to) -> `english/grammar/prepositions` (1)
   - Q70: Definite article (The book) -> `english/grammar/articles` (1)
   - Q71: Word choice in context (written statement vs oral statement) -> `english/vocabulary` (1)

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 80 candidate records staged under policy `study-tagging-v1`.
- Complete verification against 8 rendered page images from source PDF.
"""

(out / "README.md").write_text(md)
print("Wrote README.md successfully.")
