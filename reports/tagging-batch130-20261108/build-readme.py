"""Generate README.md for Batch 130."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
summary = json.load(open(out / "summary.json"))
validation = json.load(open(out / "validation.json"))

md = f"""# Tagging Batch 130: AAP 2020 General English & MES 2020 General English

## Summary
- **Batch ID**: 130
- **Date**: 2026-11-08
- **Targets**: {summary['targets']} MCQs ({summary['unextracted_items_preserved']} conventional items preserved, {summary['conventional_marks_preserved']} conventional marks across both papers)
- **Completion**: {summary['completion']}
- **Live Changes**: {summary['live_changes']} (All {summary['targets']} candidates remain `pending`)
- **Actions**:
  - `retag`: {summary['actions']['retag']}
  - `keep`: {summary['actions']['keep']}
  - `hold`: {summary['actions']['hold']}
- **Verification**: {validation['source_fingerprints_verified']}/{summary['targets']} source fingerprints re-verified via repeatable-read Oracle readback ({validation['validated_at']}).

## Papers Reviewed
1. **Assistant Public Prosecutor (AAP) under Lokayukta (Nov 2020) — General English**:
   - **Paper ID**: `Old_Questions/Direct_2019-2020/AAP General English.pdf`
   - **Document ID**: `{summary['papers'][0]['document_id']}`
   - **Source SHA256**: `{summary['papers'][0]['sha256']}`
   - **Targets**: 15 MCQs (80 conventional marks preserved in `pending-written-intake.json`)

2. **Junior Grade of MES under PWD (March 2020) — General English**:
   - **Paper ID**: `Old_Questions/Direct_2019-2020/MES General Englsih.pdf`
   - **Document ID**: `{summary['papers'][1]['document_id']}`
   - **Source SHA256**: `{summary['papers'][1]['sha256']}`
   - **Targets**: 20 MCQs (80 conventional marks preserved in `pending-written-intake.json`)

## Topic Breakdown
| Topic / Subtopic | Count |
| :--- | :--- |
"""

for topic, count in sorted(summary['breakdown'].items(), key=lambda x: -x[1]):
    md += f"| `{topic}` | {count} |\n"

md += """
## Section Breakdown
### Paper 1: AAP 2020 General English (15 MCQs + 7 Conventional Items)
- **Q7(a)–(e)**: Synonyms (frantic, humdrum, alacrity, attenuate, chimera) -> `english/vocabulary/synonyms` (5)
- **Q8(a)–(e)**: Antonyms (ameliorate, fecundity, plethora, continence, decrepit) -> `english/vocabulary/antonyms` (5)
- **Q10(a)–(e)**: Reading Comprehension on fate, human will, and responsibility -> `english/comprehension` (5)
- **Conventional Intake**: Essay (20 marks), Précis (10 marks), Letter Drafting (10 marks), Proverb Expansion (10 marks), Prepositions (10 marks), Verb Tenses (4 marks), Idioms Sentence Making (16 marks) -> preserved in `pending-written-intake.json` (80 marks).

### Paper 2: MES 2020 General English (20 MCQs + 5 Conventional Items)
- **Q1, Q3 (Booklet 4a, 4c)**: Prepositions (beside, for) -> `english/grammar/prepositions` (2)
- **Q2, Q4, Q5, Q6, Q9, Q10 (Booklet 4b, 4d, 4e, 4f, 4i, 4j)**: Subject-Verb Agreement (is, have, has, was, carries, believe) -> `english/grammar/subject-verb-agreement` (6)
- **Q7, Q8, Q11, Q12, Q14, Q15, Q16, Q20 (Booklet 4g, 4h, 5a, 5b, 5d, 5e, 5f, 5j)**: Confusing words and homophones (soar, proceeds, further, eligible, latest, loose, latter, last) -> `english/vocabulary` (8)
- **Q13, Q17, Q18, Q19 (Booklet 5c, 5g, 5h, 5i)**: Degrees of comparison and determiners (longer, interesting, nearest, many) -> `english/grammar` (4)
- **Conventional Intake**: Essay (20 marks), Descriptive Comprehension (20 marks), Précis (20 marks), Sentence Correction (10 marks), Idioms Sentence Making (10 marks) -> preserved in `pending-written-intake.json` (80 marks).

## Verification and Safety
- Zero live DB mutations (`live_changes: 0`).
- All 35 candidate records staged under policy `study-tagging-v1`.
- Complete verification against 4 rendered pages (AAP) and 3 rendered pages (MES) from source PDFs.
"""

(out / "README.md").write_text(md)
print("Wrote README.md successfully.")
