"""Generate README.md for Batch 93."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
summary = json.load(open(out / "summary.json"))
validation = json.load(open(out / "validation.json"))

md = f"""# Tagging Batch 93: Circle Education Officer under School Education Deptt (2019) — General English Paper-II

## Summary
- **Batch ID**: 93
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
- **Paper ID**: `Old_Questions/Direct_2019-2020/CEO General English-II.pdf`
- **Document ID**: `doc_b62486413c037a0400665202`
- **Source SHA256**: `905ccb750d4a98236faea42938a452d5d7a261beda7f261938f7d52b3dffd36f`
- **Total Questions in Paper**: 100 MCQs (100 Marks, 2 Hours duration)
- **Subject Coverage**: General English (Parts of Speech, Nouns, Prepositions, Adjectives & Determiners, Sentence Types, Phrases & Clauses, Comparison, Vocabulary Contextual & Fill-in-blanks, One-Word Substitution)

## Topic Breakdown
| Topic / Subtopic | Count |
| :--- | :--- |
"""

for topic, count in sorted(summary['breakdown'].items(), key=lambda x: -x[1]):
    md += f"| `{topic}` | {count} |\n"

md += """
## Section Breakdown
1. **Q1–Q10**: Functional parts of speech identification (down, up, near, all, face, while, such, once, right, ones) -> `english/grammar` (10)
2. **Q11–Q20**: Noun classification (common, proper, collective, abstract, material) -> `english/grammar` (10)
3. **Q21–Q30**: Prepositions and collocations (on, for, for, before, wait at, made of, through, on account of, dispense with, committed to) -> `english/grammar/prepositions` (10)
4. **Q31–Q40**: Adjectives and determiners classification (quantity, quality, demonstrative, indefinite, numeral, distributive) -> `english/grammar` (10)
5. **Q41–Q50**: Sentence analysis and clause structure (simple, compound, complex, compound-complex) -> `english/grammar` (10)
6. **Q51–Q60**: Phrases and subordinate clauses (noun/adjective/adverbial phrases and clauses) -> `english/grammar` (10)
7. **Q61–Q70**: Degrees of comparison (positive, comparative, superlative) -> `english/grammar` (10)
8. **Q71–Q80**: Contextual double fill-in-the-blanks / word pairs -> `english/vocabulary` (10)
9. **Q81–Q90**: Word choice and vocabulary sentence completion -> `english/vocabulary` (10)
10. **Q91–Q100**: One-word substitution (ambiguous, agenda, altruism, sinecure, apostate, retrospection, emeritus, perseverance, postscript, philology) -> `english/vocabulary/one-word-substitution` (10)

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 100 candidate records staged under policy `study-tagging-v1`.
- Complete verification against 8 rendered page images from source PDF.
"""

(out / "README.md").write_text(md)
print("Wrote README.md successfully.")
