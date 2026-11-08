"""Generate README.md for Batch 101."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
summary = json.load(open(out / "summary.json"))
validation = json.load(open(out / "validation.json"))

md = f"""# Tagging Batch 101: Forest Ranger (2019) — General English Paper-II

## Summary
- **Batch ID**: 101
- **Date**: 2026-11-08
- **Targets**: {summary['targets']} MCQs ({summary['unextracted_items_preserved']} conventional/dropped items preserved)
- **Completion**: {summary['completion']}
- **Live Changes**: {summary['live_changes']} (All {summary['targets']} candidates remain `pending`)
- **Actions**:
  - `retag`: {summary['actions']['retag']}
  - `keep`: {summary['actions']['keep']}
  - `hold`: {summary['actions']['hold']}
- **Verification**: {validation['source_fingerprints_verified']}/{summary['targets']} source fingerprints re-verified via repeatable-read Oracle readback ({validation['validated_at']}).

## Paper Details
- **Paper ID**: `Old_Questions/Direct_2019-2020/General English-II (FR).pdf`
- **Document ID**: `doc_bead3bb71835fdb97283f30a`
- **Source SHA256**: `b9df0cd7beee835d6078ef0da0432abf058a86f5584f0d76f572a172ea069437`
- **Total Questions in Paper**: 100 MCQs (98 extracted in appearances table, 2 legacy drops documented)
- **Subject Coverage**: General English (Functional Parts of Speech, Tenses, Determiners, Modals, Clauses, Sentence Types Analysis, Sentence Completion, Synonyms, Sentence Improvement, One-Word Substitution)

## Topic Breakdown
| Topic / Subtopic | Count |
| :--- | :--- |
"""

for topic, count in sorted(summary['breakdown'].items(), key=lambda x: -x[1]):
    md += f"| `{topic}` | {count} |\n"

md += """
## Section Breakdown
1. **Q1–Q10**: Functional parts of speech identification (yet, all, much, near, only, but, like, since, well) -> `english/grammar` (10)
2. **Q11–Q20**: Verb tenses in context (am wearing, had been trying, has lived, arrived, etc.) -> `english/grammar/tenses` (10)
3. **Q21–Q30**: Determiners & quantifiers (fewer, lesser, each, every, much, many, any) -> `english/grammar` (10)
4. **Q31–Q40**: Modal auxiliaries (could, can, may, might, should, would, ought to, must) -> `english/grammar` (10)
5. **Q41–Q50**: Clause identification (Noun clause, Adjective clause, Adverb clause) -> `english/grammar` (10)
6. **Q51–Q60**: Sentence types analysis (Simple, Complex, Compound) -> `english/grammar` (10)
7. **Q61–Q70**: Sentence completion & connectors (8 extracted: Q61–Q65, Q68–Q70; Q66 & Q67 omitted by legacy parser) -> `english/grammar` (8)
8. **Q71–Q80**: Synonyms / closest meaning (infructuous, recondite, mitigate, innocuous, abjure, ephemeral, clandestine, loquacious, supercilious, recalcitrant) -> `english/vocabulary/synonyms` (10)
9. **Q81–Q90**: Sentence correction / phrase improvement -> `english/sentence-correction` (10)
10. **Q91–Q100**: One-word substitution / term definitions -> `english/vocabulary/one-word-substitution` (10)

## Defect Ledger & Legacy Omissions
- **Q66**: Short stem `66. I think` with options `(a) today it is Wednesday (b) today is Wednesday (c) that today was Wednesday (d) today be Wednesday` dropped during original OCR ingestion. Documented in `pending-written-intake.json`.
- **Q67**: Short stem `67. He said` with options `(a) that yesterday he gone downtown (b) he go downtown yesterday (c) he goes downtown yesterday (d) he went downtown yesterday` dropped during original OCR ingestion. Documented in `pending-written-intake.json`.

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 98 candidate records staged under policy `study-tagging-v1`.
- Complete verification against 8 rendered page images from source PDF.
"""

(out / "README.md").write_text(md)
print("Wrote README.md successfully.")
