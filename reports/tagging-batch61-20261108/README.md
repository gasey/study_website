# Pending source-reviewed tagging — Batch 61: MCS Combined 2021 Preliminary Paper II (100 MCQs)

Policy: `study-tagging-v1`. **100 existing questions reviewed: 31 retag proposals, 69 keep decisions, 0 tag holds. All 100 remain pending. Zero live changes, submissions or publications.**

## Target Paper & 100% Paper Completion Milestone

This batch achieves **100% paper completion** for the 100-MCQ MCS Combined Preliminary Paper-II examination (Aptitude, Arithmetic & Comprehension):
- *Mizoram Civil Services Combined Preliminary Examination 2021 — Paper II (Aptitude, Arithmetic & Comprehension)* (`Old_Questions/Direct_2021-2022/MCS Combined 2021 Preliminary Exam Paper II.pdf`, `doc_82ea93920297fe3dba5ea823`, 100 MCQs, achieving **100% paper completion** with 100/100 items reviewed).

## Granular Structuring & Taxonomy Alignment

All 100 items were structured into active English, Mathematics, and Reasoning taxonomy paths:
- `english/comprehension` (10 items, confirmed and kept from baseline):
  - Q1–Q2, Q8–Q9, Q11–Q14, Q16–Q17: Reading comprehension passages on Magellan, legal administration, and hummingbirds.
- `english/vocabulary/synonyms` (3 items, retagged from coarse baseline):
  - Q3 ('precipice'), Q5 ('skirmish'), Q7 ('stalemate').
- `english/vocabulary` (2 items, confirmed and kept from baseline):
  - Q4, Q6: Contextual vocabulary and blank completion from passages.
- `english/vocabulary/antonyms` (1 item, retagged from coarse baseline):
  - Q10: Opposite meaning to 'rampant'.
- `english/vocabulary/idioms-and-phrases` (1 item, retagged from coarse baseline):
  - Q15: Idiom 'deliver the goods'.
- `reasoning-and-aptitude/verbal-reasoning` (52 items):
  - Q18–Q33: Interpersonal skills, communication, resilience, and emotional intelligence.
  - Q34–Q37: Logical deduction and sports grouping puzzle.
  - Q38, Q72: Blood relations reasoning.
  - Q39–Q40: Verbal analogies.
  - Q41, Q45, Q73: Coding-decoding patterns.
  - Q43, Q44: Non-verbal figure odd-one-out.
  - Q50: Comparison of inequalities.
  - Q51–Q54: Syllogisms, statement-conclusion, cause-effect, and statement-arguments.
  - Q55–Q67: Administrative decision-making, ethical dilemmas, and situational problem solving.
  - Q71: Assertion and reason logic (retagged from incorrect science/physics baseline).
  - Q74, Q78: Direction sense and spatial orientation.
  - Q81–Q82: Analytical seating and ranking arrangement.
- `reasoning-and-aptitude/series` (4 items):
  - Q42, Q68, Q69: Number series and missing/wrong number identification.
  - Q46: Letter series pattern.
- `reasoning-and-aptitude/numerical-ability` (8 items):
  - Q70: Tree distribution word problem.
  - Q75: Number matrix puzzle.
  - Q76, Q90: Venn diagram set problems.
  - Q79: Clock gain/loss time problem.
  - Q80: Dice pattern identification.
  - Q83: Seating rows arrangement.
  - Q84: Shift scheduling time problem.
- `reasoning-and-aptitude/data-interpretation` (3 items):
  - Q91: Pie chart expenditure analysis.
  - Q99–Q100: Table data interpretation (college pass/appearance ratios and averages).
- `mathematics/arithmetic` (4 items):
  - Q86–Q87: Radical and surd arithmetic simplification.
  - Q89: Pipes and cisterns / rate of work.
  - Q96: Speed, distance, and time.
- `mathematics/arithmetic/percentages` (3 items):
  - Q48: Purchasing power and price increase percentage.
  - Q85: Ratio to percentage conversion.
  - Q94: Salary percentage increment.
- `mathematics/arithmetic/averages` (2 items):
  - Q49, Q88: Corrected arithmetic mean / average calculation (retagged from statistics).
- `mathematics/arithmetic/ratio-and-proportion` (2 items):
  - Q95: Unitary method and table costs.
  - Q98: Ratio of ages.
- `mathematics/algebra` (1 item):
  - Q92: Arithmetic progression (AP) term calculation.
- `mathematics/algebra/linear-equations` (3 items):
  - Q47, Q77: Age algebra word problems.
  - Q93: Linear equation in one unknown.
- `mathematics/mensuration` (1 item):
  - Q97: Perimeter and wheel revolution distance.

## Visual Source & Defect Analysis

- **Cross-Disciplinary Normalization**: Corrected baseline anomalies where Assertion-Reason was tagged under Physics (Q71) and Mean/Averages were tagged under Statistics (Q49, Q88).
- **Source Booklet Verification**: Verified exact alignment against printed 14-page booklet.

## Validation Summary

- Target appearances verified: 100/100
- Live changes: 0
- Candidates status: `all_pending`
- Taxonomy validity: `100%_active_paths_and_parents`
- Audit verification: `True`

```json
{
  "batch": 61,
  "papers": [
    {
      "paper_id": "Old_Questions/Direct_2021-2022/MCS Combined 2021 Preliminary Exam Paper II.pdf",
      "paper_title": "Mizoram Civil Service Combined Preliminary Examination 2021 \u2014 Paper II (Aptitude, Arithmetic & Comprehension)",
      "document_id": "doc_82ea93920297fe3dba5ea823",
      "sha256": "9df024ceae83bb6183df0bf513aeb6354d8fa0cf1871ce9fd22455094c91784d",
      "targets": 100
    }
  ],
  "targets": 100,
  "completion": "100% paper completion achieved for MCS Combined 2021 Preliminary Paper II (100/100 MCQs)",
  "actions": {
    "retag": 31,
    "keep": 69,
    "hold": 0
  },
  "unextracted_items_preserved": 0,
  "conventional_marks_preserved": 0,
  "breakdown": {
    "english/comprehension": 10,
    "english/vocabulary/synonyms": 3,
    "english/vocabulary": 2,
    "english/vocabulary/antonyms": 1,
    "english/vocabulary/idioms-and-phrases": 1,
    "reasoning-and-aptitude/verbal-reasoning": 52,
    "reasoning-and-aptitude/series": 4,
    "mathematics/algebra/linear-equations": 3,
    "mathematics/arithmetic/percentages": 3,
    "mathematics/arithmetic/averages": 2,
    "reasoning-and-aptitude/numerical-ability": 8,
    "mathematics/arithmetic": 4,
    "reasoning-and-aptitude/data-interpretation": 3,
    "mathematics/algebra": 1,
    "mathematics/arithmetic/ratio-and-proportion": 2,
    "mathematics/mensuration": 1
  },
  "source_defects": [
    "Q71 Misclassified to Physics: An assertion-reason logic question was misclassified into science/physics in legacy baseline; retagged to reasoning-and-aptitude/verbal-reasoning.",
    "Q49, Q88 Misclassified to Statistics: Standard arithmetic mean/average problems were tagged to statistics in legacy baseline; retagged to mathematics/arithmetic/averages."
  ],
  "all_pending": true,
  "live_changes": 0
}
```
