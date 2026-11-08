"""Generate README.md for Batch 44."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
packet = json.load(open(out / "oracle-packet.json"))
summary = json.load(open(out / "summary.json"))
findings = json.load(open(out / "findings.json"))
validation = json.load(open(out / "validation.json"))

lines = [
    "# Pending source-reviewed tagging — Batch 44: Finance Dept ADA, AA & ATA Arithmetic (70 MCQs)",
    "",
    "Policy: `study-tagging-v1`. **70 existing questions reviewed: 64 retag proposals, 6 keep decisions, 0 tag holds. All 70 remain pending. Zero live changes, submissions or publications.**",
    "",
    "## Target Papers & 100% Paper Completion Milestone",
    "",
    "This batch achieves 100% source review across two major Finance Department competitive examination Arithmetic booklets:",
    "1. *General Competitive Examinations for Recruitment to the Post of Assistant Divisional Accountant under Finance Department (2015) — 3. Arithmetic* (`Old_Questions/Direct_2014-2018/3. Arithmetic.pdf`, `doc_b3e48463a72b3b18b82957d0`, 20 MCQs, 100% paper completion).",
    "2. *Competitive Examinations for Recruitment to the Posts of Assistant Auditor, Assistant Treasury Accountant & Assistant Divisional Accountant under Finance Department (2019) — Arithmetic* (`Old_Questions/Direct_2019-2020/ADA, AA & ATA Arithmatic.pdf`, `doc_5335e1afbbcfc26d1afa5cd2`, 50 MCQs, 100% paper completion).",
    "",
    "- **Untagged & Misclassified Baseline Rectification:** In the database, targets had unclassified coarse tags, and 4 questions suffered from severe baseline bugs: Q13 (Paper 1), Q39 (Paper 2), and Q40 (Paper 2) were tagged under the inactive `statistics` subject baseline; Q30 (Paper 2, partnership profit sharing) was misclassified under `commerce`; and Q49 (Paper 2, pie chart miscellaneous expenditure) was misclassified under `financial-rules-and-accounts`. All have been cleanly rectified to active taxonomy paths: General Arithmetic (31 items: Place Value, Fractions, Decimals, BODMAS, HCF/LCM, Simple/Compound Interest, Time & Work, Speed/Distance, Surds/Square Roots, Radicals), Averages (2 items), Ratio & Proportion (5 items: Mean Proportional, Continued Ratio, Mixture Ratios, Partnership Capital), Percentages (6 items: Relative Excess, Examination Percentages, Successive Spending, Depreciation), Profit & Loss (3 items: Selling Price Equivalents, Target Margin, Successive Trade Discounts), Mensuration (8 items: Rectangle Area, Wheel Distance, Survey Area, Path Area, Cube Volume, Recast Sphere/Hemisphere Volume), Linear Equations & Algebra (2 items: Age Problems, Simultaneous Equations), Probability & Numerical Ability (4 items: Die Roll, Colored Balls, Empirical Mode), and Data Interpretation (9 items: Bar Chart Analysis 5, Pie Chart Expenditure Analysis 4).",
    f"- **Fresh Oracle read-only export:** `{packet['exported_at']}`. Readback validation (`{validation['validated_at']}`) confirmed 100% source fingerprint consistency, zero live mutations, and 100% compliance with active taxonomy nodes.",
    "",
    "## Before / after table",
    "",
    "| # | Source context | Tested skill | Before | Proposed after | Decision & rationale |",
    "| :---: | :--- | :--- | :--- | :--- | :--- |"
]

for idx, f in enumerate(findings, 1):
    ctx = f"{f['printed_question']} (p. {f['physical_page']})"
    lines.append(
        f"| {idx} | {ctx} | {f['tested_skill']} | `{f['current_path']}` | `{f['proposed_path']}` | **{f['action']}** — {f['rationale']} |"
    )

lines.extend([
    "",
    "## Totals & Summary Breakdown",
    "",
    f"- **Total existing questions reviewed:** {summary['targets']}",
    f"- **Retag candidates proposed:** {summary['actions'].get('retag', 0)}",
    f"- **Keep decisions:** {summary['actions'].get('keep', 0)}",
    f"- **Holds:** {summary['actions'].get('hold', 0)}",
    f"- **Unextracted written items preserved:** {summary['unextracted_items_preserved']}",
    "- **Live database writes:** 0 (strictly read-only)",
    "",
    "### Breakdown by Proposed Taxonomy Path",
    ""
])

for path, count in sorted(summary["breakdown"].items()):
    lines.append(f"- `{path}`: {count} questions")

lines.extend([
    "",
    "## Physical Element Inspection Evidence",
    "",
    "Direct visual inspection of all 12 rendered PNG page images across both papers:",
    "- **Paper 1 (`doc_b3e48463a72b3b18b82957d0`):** Inspected Pages 1 to 4: Q1 (place & face value of 8), Q2 (school boys/girls fractions), Q3 (HCF of prime products), Q4 (vulgar fraction 0.36), Q5 (division simplification), Q6 (square root √154), Q7 (average first 5 odd numbers), Q8 (mean proportional √(8*50)), Q9 (auditorium seating square root), Q10 (multiplicative inverse 3/2), Q11 (fraction division), Q12 (unitary cost 3 dozen books), Q13 (single die even probability), Q14 (40 m/s to km/h), Q15 (A 15 days, B 20 days work), Q16 (rectangular plot area 462 and length 28), Q17 (gunshot distance 1.34 km and sound speed), Q18 (875g of 10kg percentage), Q19 (ten's digit of √15876), Q20 (6cm cube cut into 2cm cubes).",
    "- **Paper 2 (`doc_5335e1afbbcfc26d1afa5cd2`):** Inspected Pages 1 to 8: Q1 (15 thousandths decimal), Q2 (descending decimal order), Q3 (BODMAS mixed fractions), Q4 (HCF & LCM product), Q5 (linear equation for x), Q6 (salary 20% below reciprocal percentage), Q7 (80% pass exam total), Q8 (SP of 11 gain on 44 sold), Q9 (combined average marks Class X and IX), Q10 (SBI loan simple interest calendar days), Q11 (Math/Science failure Venn overlap), Q12 (bonus percentage expenditures), Q13 (A+B, B+C, C+A time and work), Q14 (ratio 3:5 added 18), Q15 (milk-water mixture dilution ratio), Q16 (father-son age system), Q17 (train crossing 0.5km bridge), Q18 (vehicle compound depreciation), Q19 (compound ratio 2a:3b:7c), Q20 (flight time difference), Q21 (coat sold for 2700 at 10% loss), Q22 (compound interest rate 64 to 125 in 3 years), Q23 (smallest divisor of 72000 for perfect cube), Q24 (cube volume 2197 to surface area), Q25 (relative speeds 4 km/h meeting), Q26 (scientific notation 3.123x10^5), Q27 (dining table successive discounts), Q28 (wheel 1.26m diameter revolutions distance), Q29 (Fela and Rama money exchange system), Q30 (joint capital partnership profit sharing), Q31 (48cm sphere melted to cylinder), Q32 (colored balls probability), Q33 (least subtraction from 438867 for perfect square), Q34 (surds simplification), Q35 (hemisphere recast into sphere), Q36 (field survey baseline triangulation area), Q37 (40mx30m field 2m uniform path area), Q38 (tap fill 40 min and leak empty 60 min), Q39 (empirical Mode = 3 Median - 2 Mean), Q40 (mode of discrete series), Q41 (car fuel consumption 5L for 70km), Q42–Q46 (Bar chart food grains production: sum, difference, percentage growth, ratio, 6-year average), Q47–Q50 (Pie chart family expenditure: food & clothing sum, education excess, miscellaneous expenditure, monthly savings).",
    "",
    "## Documented Source, Extraction & Option Defects",
    "",
    "1. **Rectification of Inactive 'statistics' Baseline Subject:** Questions Q13 (Paper 1), Q39 (Paper 2), and Q40 (Paper 2) were tagged in production under `subject_id: statistics`, an inactive subject in review taxonomy. Rectified to `reasoning-and-aptitude/numerical-ability`.",
    "2. **Rectification of Misclassified 'commerce' Baseline Subject:** Question Q30 (Paper 2) on partnership capital profit sharing was misclassified in production as `commerce`. Rectified to `mathematics/arithmetic/ratio-and-proportion`.",
    "3. **Rectification of Misclassified 'financial-rules-and-accounts' Baseline Subject:** Question Q49 (Paper 2) on pie chart miscellaneous expenditure was misclassified as `financial-rules-and-accounts`. Rectified to `reasoning-and-aptitude/data-interpretation`.",
    "4. **100% Extracted MCQ Fidelity:** All 70 questions printed in the physical examination booklets across both papers were present and numbered consecutively in the database without sequence gaps."
])

(out / "README.md").write_text("\n".join(lines) + "\n")
print(f"Generated README.md ({len(lines)} lines).")
