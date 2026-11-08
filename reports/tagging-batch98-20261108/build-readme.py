"""Generate README.md for Batch 98."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
summary = json.load(open(out / "summary.json"))
validation = json.load(open(out / "validation.json"))

md = f"""# Tagging Batch 98: Geologist Junior (Nov 2020) — General English Paper-II

## Summary
- **Batch ID**: 98
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
- **Paper ID**: `Old_Questions/Direct_2019-2020/Geologist Junior General Englsih Paper-II Nov.pdf`
- **Document ID**: `doc_a05a7fb9038cb7ec16c28f3b`
- **Source SHA256**: `22cfe81d805b8ba6306fbeefd815623c024bb4bd545206b389a42ee7932fd0d2`
- **Total Questions in Paper**: 100 MCQs (100 Marks, 2 Hours duration)
- **Subject Coverage**: General English (Idioms & Phrases, Tenses, Subject-Verb Agreement, Prepositions, Voice, Reported Speech, Sentence Types, Synthesis, Transformations, Synonyms, Verbal Analogies, Sentence Correction, Cloze Reading Comprehension)

## Topic Breakdown
| Topic / Subtopic | Count |
| :--- | :--- |
"""

for topic, count in sorted(summary['breakdown'].items(), key=lambda x: -x[1]):
    md += f"| `{topic}` | {count} |\n"

md += """
## Section Breakdown
1. **Q1–Q10**: Idioms and idiomatic expressions (gave a hand, got rid of, burned herself out, up to date, wheel and deal, chickened out, put the bite on, have kittens, leaving for, up to her ears) -> `english/vocabulary/idioms-and-phrases` (10)
2. **Q11–Q20**: Tense forms, subject-verb agreement, and verb grammar (goes, do, have been learning, was waiting, is, are not, driving, would, had practiced, were) -> `english/grammar/tenses` (5), `english/grammar/subject-verb-agreement` (2), `english/grammar` (3)
3. **Q21–Q30**: Prepositions & conjunctions/determiners (because of, such, neither...nor, as if, so that, from, to, of, like, of) -> `english/grammar/prepositions` (6), `english/grammar` (4)
4. **Q31–Q35**: Voice transformation (active to passive) -> `english/grammar/voice` (5)
5. **Q36–Q40**: Speech transformation (direct to indirect and reverse) -> `english/grammar/reported-speech` (5)
6. **Q41–Q50**: Sentence kind identification (Simple, Complex, Compound) -> `english/grammar` (10)
7. **Q51–Q60**: Sentence synthesis and clause combinations -> `english/grammar` (10)
8. **Q61–Q70**: Sentence transformation and communicative substitution -> `english/grammar` (10)
9. **Q71–Q75**: Synonyms / nearest in meaning (temperance, empirically, misogynism, propensity, garrulous) -> `english/vocabulary/synonyms` (5)
10. **Q76–Q80**: Verbal analogies and word relationships (raise/raze, collision/collusion, ballad/ballet, amity/enmity, a lot/allot) -> `english/vocabulary` (5)
11. **Q81–Q90**: Sentence correction / phrase improvement (prefer riding to walking, used to hard work, hardly had he entered, cooler than that of, cope with, was running, advice, room, pulled down, cross-purposes) -> `english/sentence-correction` (10)
12. **Q91–Q100**: Cloze test reading passage blanks completion -> `english/comprehension` (10)

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 100 candidate records staged under policy `study-tagging-v1`.
- Complete verification against 9 rendered page images from source PDF.
"""

(out / "README.md").write_text(md)
print("Wrote README.md successfully.")
