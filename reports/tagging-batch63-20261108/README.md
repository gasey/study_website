# Pending source-reviewed tagging — Batch 63: MCS Combined 2015 Preliminary Paper II Series A (100 MCQs)

Policy: `study-tagging-v1`. **100 existing questions reviewed: 75 retag proposals, 25 keep decisions, 0 tag holds. All 100 remain pending. Zero live changes, submissions or publications.**

## Target Paper & 100% Paper Completion Milestone

This batch achieves **100% paper completion** for the 100-MCQ MCS Combined Preliminary Paper-II examination (2015 Chase Academy copy):
- *Mizoram Civil Services Combined Preliminary Examination 2015 — Paper II (Series A: Aptitude, Arithmetic & Comprehension)* (`Old_Questions/Recovered_MCS/MCS Combined 2015 Preliminary Exam Paper-II Series-A Chase copy.pdf`, `mcs-recovered-2015-ii`, 100 MCQs, achieving **100% paper completion** with 100/100 items reviewed).

## Granular Structuring & Major Baseline Normalization

This batch executes a major cleanup of legacy imports where questions had been misclassified into foreign disciplines (psychology, commerce, general studies, civil engineering, and journalism):
- `english/comprehension` (24 items):
  - Q1–Q4, Q6–Q14, Q87–Q91, Q93–Q95, Q97–Q99: Reading comprehension passages on coastal exploration, terminal care, scientific method/Darwin, Gandhiji in England, poverty/satisfaction, urban sociology, and astronomy.
- `english/vocabulary/one-word-substitution` (1 item):
  - Q5: Lexical definition of 'Euthanasia'.
- `english/vocabulary/antonyms` (2 items):
  - Q92 ('spurious' -> genuine), Q96 ('frustrater' -> promoter).
- `english/vocabulary` (4 items):
  - Q67–Q70: Anagrams / unscrambled words (*SURPRISE, VALIANT, DILIGENT, DISASTER*).
- `reasoning-and-aptitude/verbal-reasoning` (32 items):
  - Q15–Q29: Interpersonal communication, active listening, feedback, cross-cultural adaptation, conflict resolution.
  - Q42–Q44: Analytical logic and deduction puzzles (painting crew, temperature variations, pizza sharing).
  - Q45–Q51: Group decision-making, rational choice model, electronic brainstorming, and ethical administrative judgment.
  - Q55–Q58: Industrial case study and managerial problem solving (Mr. Thanga night shift).
  - Q63–Q64: Verbal analogies from stimulus visual cards.
  - Q72: Five girls standing in a row facing east.
- `reasoning-and-aptitude/series` (5 items):
  - Q30–Q32: Letter series (AZ, CX, FU...; DKY, FJW...; BXJ, ETL...).
  - Q60: Geometric number series (8, 12, 24, 60, 180).
  - Q65: Letter matrix series.
- `reasoning-and-aptitude/numerical-ability` (14 items):
  - Q33–Q38: Non-verbal figure sequences and matrix patterns.
  - Q39–Q41: Incomplete pattern completion.
  - Q52–Q54: Painted cube face counting (blue faces, two colored faces, no colored faces).
  - Q66: Number matrix puzzle.
  - Q71: Digits used in book page numbering.
- `reasoning-and-aptitude/data-interpretation` (4 items):
  - Q82: Central government expenditure pie chart.
  - Q83: Fruit hamper distribution table.
  - Q84: Subject teacher performance table.
  - Q86: Pupil assessment line graph.
- `mathematics/arithmetic` (3 items):
  - Q76: Fractional rope subtraction.
  - Q79: Speed, distance, and time (overtaking runners).
  - Q100: Number system terminology ('A million' = ten lakh).
- `mathematics/arithmetic/percentages` (2 items):
  - Q59: Passing percentage calculation.
  - Q77: 16% of a number.
- `mathematics/arithmetic/averages` (3 items):
  - Q62: Combined average height of students.
  - Q81: Group mean salary with new member.
  - Q85: Frequency distribution median.
- `mathematics/arithmetic/ratio-and-proportion` (1 item):
  - Q80: Copper and zinc alloy mixture ratio.
- `mathematics/algebra/linear-equations` (1 item):
  - Q74: Two-digit number digit relations.
- `mathematics/algebra/quadratic-equations` (1 item):
  - Q73: Siama's age quadratic product equation.
- `mathematics/geometry` (1 item):
  - Q75: Coordinate quadrant of (-2, 3).
- `mathematics/mensuration` (1 item):
  - Q61: Perimeter comparison of geometric shapes.
- `mathematics/mensuration/volume` (1 item):
  - Q78: Brick volume and wall construction dimensions.

## Validation Summary

- Target appearances verified: 100/100
- Live changes: 0
- Candidates status: `all_pending`
- Taxonomy validity: `100%_active_paths_and_parents`
- Audit verification: `True`

```json
{
  "batch": 63,
  "papers": [
    {
      "paper_id": "Old_Questions/Recovered_MCS/MCS Combined 2015 Preliminary Exam Paper-II Series-A Chase copy.pdf",
      "paper_title": "Mizoram Civil Services Combined Preliminary Examination 2015 \u2014 Paper II (Series A: Aptitude, Arithmetic & Comprehension)",
      "document_id": "mcs-recovered-2015-ii",
      "sha256": "0a54d3113f97d0f4c1e6cff7333b1fb8eec3d95a39268d679bf076f9c603fd8a",
      "targets": 100
    }
  ],
  "targets": 100,
  "completion": "100% paper completion achieved for MCS Combined 2015 Preliminary Paper-II Series A (100/100 MCQs)",
  "actions": {
    "retag": 75,
    "keep": 25,
    "hold": 0
  },
  "unextracted_items_preserved": 0,
  "conventional_marks_preserved": 0,
  "breakdown": {
    "english/comprehension": 24,
    "english/vocabulary/one-word-substitution": 1,
    "reasoning-and-aptitude/verbal-reasoning": 32,
    "reasoning-and-aptitude/series": 5,
    "reasoning-and-aptitude/numerical-ability": 14,
    "mathematics/arithmetic/percentages": 2,
    "mathematics/mensuration": 1,
    "mathematics/arithmetic/averages": 3,
    "english/vocabulary": 4,
    "mathematics/algebra/quadratic-equations": 1,
    "mathematics/algebra/linear-equations": 1,
    "mathematics/geometry": 1,
    "mathematics/arithmetic": 3,
    "mathematics/mensuration/volume": 1,
    "mathematics/arithmetic/ratio-and-proportion": 1,
    "reasoning-and-aptitude/data-interpretation": 4,
    "english/vocabulary/antonyms": 2
  },
  "source_defects": [
    "Major Baseline Cleanup: Realigned legacy classification where CSAT questions were misclassified under psychology (10), commerce (4), science (3), general-studies (3), civil-engineering (1), and journalism (1).",
    "Q63, Q64 Visual Analogies: Verbal analogy questions with source-scanned stimulus diagrams properly tagged to reasoning-and-aptitude/verbal-reasoning."
  ],
  "all_pending": true,
  "live_changes": 0
}
```
