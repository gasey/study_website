# Pending source-reviewed tagging — Batch 66: MCS Combined 2014 Preliminary Paper II (99 MCQs)

Policy: `study-tagging-v1`. **99 existing questions reviewed: 19 retag proposals, 80 keep decisions, 0 tag holds. All 99 remain pending. Zero live changes, submissions or publications.**

## Target Paper & 100% Paper Completion Milestone

This batch achieves **100% paper completion** for the 99 available MCQs in the MCS Combined Preliminary Paper-II examination (2014):
- *Mizoram Civil Services Combined Preliminary Examination 2014 — Paper II (Aptitude, Arithmetic & Comprehension)* (`Old_Questions/Direct_2014-2018/MCS Combined 2014 Preliminary Exam Paper II.pdf`, `doc_27f320fe0ca6eed357e122a2`, 99 MCQs, achieving **100% paper completion** with 99/99 items reviewed).
- **Source Intake Defect Preserved**: Q39 was a non-verbal stimulus figure question on page 6 of the printed PDF booklet with options (1)-(4) that had been omitted from legacy OCR database ingestion due to empty stem text. It has been safely preserved in `pending-written-intake.json` for future re-intake.

## Granular Structuring & Taxonomy Alignment

All 99 items were structured into active English, Mathematics, and Reasoning taxonomy paths:
- `english/comprehension` (23 items):
  - Q1–Q13: Reading comprehension passages on acquiring knowledge, leisure time, feminist movement, and national objectives.
  - Q87–Q90: Reading comprehension passages on civilized society, rights, and duties.
  - Q93–Q97, Q100: Reading comprehension passages on talented Indians studying in America, brain bank, and 21st-century leadership.
- `english/vocabulary/synonyms` (4 items):
  - Q14 ('vigour'), Q91 ('talent'), Q98 ('cohesive'), Q99 ('moral').
- `english/vocabulary/idioms-and-phrases` (1 item):
  - Q92: Idiomatic expression 'Stem the tide'.
- `english/vocabulary/antonyms` (1 item):
  - Q61: Antonym of 'ascetic'.
- `english/vocabulary` (4 items):
  - Q59 ('pilaster'), Q60 ('gingival'), Q62 (word completion), Q71 (anagram / jumbled letters).
- `reasoning-and-aptitude/verbal-reasoning` (43 items):
  - Q15–Q29: Interpersonal skills, communication channels, non-verbal cues, descriptive communication, active listening, and critical feedback.
  - Q30–Q31: Group photo position deduction.
  - Q35: Meaningful word and sentence arrangement.
  - Q41: Direction sense test.
  - Q43–Q44: Syllogisms.
  - Q45–Q58: Administrative problem solving, situational judgment, and public leadership ethics.
  - Q63–Q64: Verbal analogies (Antiseptic : Germs :: Antidote : ?; Shirt : Button :: Shoe : ?).
  - Q65: Odd one out.
  - Q66–Q67: Coding-decoding.
  - Q68: Cause and effect reasoning.
  - Q69: Blood relations deduction.
  - Q72: Dictionary alphabetical order sequence.
- `reasoning-and-aptitude/series` (3 items):
  - Q32: Number difference series (120, 99, 80, 63, 48...).
  - Q33: Digit deletion series (589654237, 89654237...).
  - Q36: Letter analogy/series (ZRYQ : ...).
- `reasoning-and-aptitude/numerical-ability` (4 items):
  - Q37–Q38: Non-verbal figure fitting and odd-one-out.
  - Q42: Clock direction orientation.
  - Q70: Number pattern count of 3s.
- `reasoning-and-aptitude/data-interpretation` (4 items):
  - Q83: Monthly expenses pie chart.
  - Q84: Foodgrain production bar graph.
  - Q85: Patient temperature line graph.
  - Q86: Coordinate line graph intersection.
- `mathematics/arithmetic` (5 items):
  - Q34: Number fraction equation.
  - Q73: Division algorithm and remainder arithmetic.
  - Q78: Book page fraction.
  - Q80: Unitary method (juice cans in cartons).
  - Q81: Time and work (X and Y comparative rates).
- `mathematics/arithmetic/percentages` (1 item):
  - Q74: Percentage computation (3% of 5%).
- `mathematics/arithmetic/averages` (3 items):
  - Q76: Average of first five multiples of 3.
  - Q77: Empirical relationship between mean, median, and mode.
  - Q82: Median computation of numerical data.
- `mathematics/algebra/linear-equations` (1 item):
  - Q40: Two-digit age reversal linear equations.
- `mathematics/geometry/triangles` (1 item):
  - Q75: Triangle ABC altitude bisecting base.
- `mathematics/mensuration/area` (1 item):
  - Q79: Square area equal to rectangle area.

## Validation Summary

- Target appearances verified: 99/99
- Live changes: 0
- Candidates status: `all_pending`
- Taxonomy validity: `100%_active_paths_and_parents`
- Audit verification: `True`

```json
{
  "batch": 66,
  "papers": [
    {
      "paper_id": "Old_Questions/Direct_2014-2018/MCS Combined 2014 Preliminary Exam Paper II.pdf",
      "paper_title": "Mizoram Civil Services Combined Preliminary Examination 2014 \u2014 Paper II (Aptitude, Arithmetic & Comprehension)",
      "document_id": "doc_27f320fe0ca6eed357e122a2",
      "sha256": "02493b6a8d51cfc86bfa6c8a849452903e2a04ebb63166966112a933a3e01418",
      "targets": 99
    }
  ],
  "targets": 99,
  "completion": "100% paper completion achieved for MCS Combined 2014 Preliminary Paper II (99/99 available MCQs reviewed; 1 unextracted figure item preserved in pending-written-intake.json)",
  "actions": {
    "retag": 19,
    "keep": 80,
    "hold": 0
  },
  "unextracted_items_preserved": 1,
  "conventional_marks_preserved": 0,
  "breakdown": {
    "english/comprehension": 23,
    "english/vocabulary/synonyms": 4,
    "reasoning-and-aptitude/verbal-reasoning": 43,
    "reasoning-and-aptitude/series": 3,
    "mathematics/arithmetic": 5,
    "reasoning-and-aptitude/numerical-ability": 4,
    "mathematics/algebra/linear-equations": 1,
    "english/vocabulary": 4,
    "english/vocabulary/antonyms": 1,
    "mathematics/arithmetic/percentages": 1,
    "mathematics/geometry/triangles": 1,
    "mathematics/arithmetic/averages": 3,
    "mathematics/mensuration/area": 1,
    "reasoning-and-aptitude/data-interpretation": 4,
    "english/vocabulary/idioms-and-phrases": 1
  },
  "source_defects": [
    "Unextracted Item Q39: Booklet question 39 is a non-verbal visual figure question with options (1)-(4) on page 6 of the printed PDF; omitted from legacy OCR intake due to empty stem text and safely recorded in pending-written-intake.json.",
    "Disciplinary Normalization: Re-aligned arithmetic mean, mode, and median questions from statistics into mathematics/arithmetic/averages."
  ],
  "all_pending": true,
  "live_changes": 0
}
```
