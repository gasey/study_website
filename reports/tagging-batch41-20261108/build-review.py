"""Build review packet and findings for Batch 41: High School Teacher Mathematics Paper-I (75 MCQs)."""
import json
from pathlib import Path

batch_dir = Path(__file__).resolve().parent
packet = json.load(open(batch_dir / "oracle-packet.json"))

def parse_path(path_str):
    parts = path_str.split("/")
    if len(parts) == 1:
        return {"subject_id": parts[0], "topic_id": None, "subtopic_id": None}
    elif len(parts) == 2:
        return {"subject_id": parts[0], "topic_id": path_str, "subtopic_id": None}
    elif len(parts) == 3:
        return {"subject_id": parts[0], "topic_id": f"{parts[0]}/{parts[1]}", "subtopic_id": path_str}
    raise ValueError(path_str)

# Map qnum (1-indexed) to metadata: (page, skill, path_str, action, rationale)
specs = {
    # Page 1: Q1-Q6
    1: (1, "Number System (Unit Digit)", "mathematics/arithmetic", "retag", "Calculates cyclicity of powers of 7 (7^105 mod 4) to find unit digit."),
    2: (1, "Divisibility & Counting", "mathematics/arithmetic", "retag", "Calculates count of multiples of 7 between 100 and 300 using arithmetic progression."),
    3: (1, "Square Roots & Radicals", "mathematics/arithmetic", "retag", "Evaluates nested square roots √(50 + 31) = √81 = 9."),
    4: (1, "Ratio & Proportion", "mathematics/arithmetic/ratio-and-proportion", "retag", "Evaluates rational expression (x² + y²)/(x² - y²) from given ratio x/y = 1/3."),
    5: (1, "Averages & Corrected Mean", "mathematics/arithmetic/averages", "retag", "Computes corrected arithmetic mean adjusting for misread observations (32, 12 vs 23, 11)."),
    6: (1, "Averages (Weighted & Shifted)", "mathematics/arithmetic/averages", "retag", "Sets up linear system for average age of Zumba class members before and after attrition/addition."),
    # Page 2: Q7-Q15
    7: (2, "Exponents & Simplification", "mathematics/arithmetic", "retag", "Simplifies powers of 0.8: (0.8^2)^2 ÷ (0.8^3)^3 * (0.8)^4 to solve for exponent."),
    8: (2, "Time & Work", "mathematics/arithmetic", "retag", "Computes work rate equivalence between men and women to find combined completion time."),
    9: (2, "Pipes & Cisterns", "mathematics/arithmetic", "retag", "Calculates net emptying rate of two opposing pipes when cistern is 3/4 full."),
    10: (2, "Mixtures & Alligations", "mathematics/arithmetic", "retag", "Calculates volume of water required to dilute 40L milk from Rs 3.50/L to Rs 2.00/L."),
    11: (2, "Percentages (Price & Consumption)", "mathematics/arithmetic/percentages", "retag", "Calculates original price of rice given 20% reduction enables purchasing 3.5 kg more."),
    12: (2, "Profit & Loss (Overall Transaction)", "mathematics/arithmetic/profit-and-loss", "retag", "Calculates net percentage loss when two identical selling price items are sold at +20% and -20%."),
    13: (2, "Profit & Loss (Successive Discounts)", "mathematics/arithmetic/profit-and-loss", "retag", "Calculates additional discount percentage to bring price down from list minus initial discount."),
    14: (2, "Ratio & Proportion", "mathematics/arithmetic/ratio-and-proportion", "retag", "Solves for constant term k added to both terms of ratio 3:5 to make 5:6."),
    15: (2, "Percentages (Compound Depreciation)", "mathematics/arithmetic/percentages", "retag", "Calculates depreciated value of machine after 2 years at 7% per annum compound rate."),
    # Page 3: Q16-Q22
    16: (3, "Letter Series", "reasoning-and-aptitude/series", "retag", "Identifies increasing alphabetical step difference sequence GH, JL, NQ, SW, YD -> EJ."),
    17: (3, "Verbal Analogy", "reasoning-and-aptitude/verbal-reasoning", "retag", "Tests manufacturing venue analogy: Newspaper : Press : : Cloth : Mill."),
    18: (3, "Odd One Out / Classification", "reasoning-and-aptitude/verbal-reasoning", "retag", "Identifies month with different day count (30 vs 31 days)."),
    19: (3, "Coding-Decoding", "reasoning-and-aptitude/verbal-reasoning", "retag", "Decodes pattern shift from ROAST -> PQYUR to encode SLOPPY."),
    20: (3, "Direction & Seating Arrangement", "reasoning-and-aptitude/verbal-reasoning", "retag", "Deduces facing directions and seating of partners P,R and S,Q playing carrom."),
    21: (3, "Venn Diagram Logic", "reasoning-and-aptitude/verbal-reasoning", "retag", "Interprets overlapping regions representing youth, employed, and educated subsets."),
    22: (3, "Non-Verbal (Figure Counting)", "reasoning-and-aptitude", "keep", "Confirms exact active subject for geometric triangle counting in composite figure."),
    # Page 4: Q23-Q26
    23: (4, "Non-Verbal (Figure Matrix)", "reasoning-and-aptitude", "keep", "Confirms exact active subject for non-verbal pattern matrix completion."),
    24: (4, "Non-Verbal (Pattern Completion)", "reasoning-and-aptitude", "keep", "Confirms exact active subject for embedded quadrant pattern completion."),
    25: (4, "Alphabetical Sequence Test", "reasoning-and-aptitude/verbal-reasoning", "retag", "Determines unchanged letter positions when BRAKES is sorted alphabetically."),
    26: (4, "Quadratic Equations (Discriminant)", "mathematics/algebra/quadratic-equations", "retag", "Finds parameter k for which quadratic equation has equal/real roots."),
    # Page 5: Q27-Q34
    27: (5, "Quadratic Equations (Root Relations)", "mathematics/algebra/quadratic-equations", "retag", "Solves parameter p when one root is the square of the other (α, α²)."),
    28: (5, "Quadratic Equations (Reciprocal Roots)", "mathematics/algebra/quadratic-equations", "retag", "Uses product of roots c/a = 1 to find k when roots are reciprocals."),
    29: (5, "Logarithmic Identities", "mathematics/algebra/algebraic-expressions", "retag", "Evaluates cyclic sum 1/(1+x) + 1/(1+y) + 1/(1+z) using base change logarithmic rules."),
    30: (5, "Linear Equations (Geometry of Lines)", "mathematics/algebra/linear-equations", "retag", "Identifies geometric property of linear equation ax + by = 0 passing through origin."),
    31: (5, "Set Theory (Symmetric Difference)", "mathematics/algebra", "retag", "Identifies set symmetric difference identity (A ∪ B) - (A ∩ B) = (A - B) ∪ (B - A)."),
    32: (5, "Logarithmic Equations", "mathematics/algebra/algebraic-expressions", "retag", "Evaluates x^x·y^y·z^z using logarithmic symmetry parameterization."),
    33: (5, "Mathematical Induction", "mathematics/algebra", "retag", "Evaluates base cases and induction validity for inequality 2^n > n!."),
    34: (5, "Polynomials & Remainder Theorem", "mathematics/algebra/algebraic-expressions", "retag", "Applies Polynomial Remainder Theorem: remainder of f(x) divided by (ax - b) is f(b/a)."),
    # Page 6: Q35-Q43
    35: (6, "Circles & Circumcircle", "mathematics/geometry/circles", "retag", "Calculates circumradius R = a/√3 for equilateral triangle of side 2√3 cm."),
    36: (6, "Similar Triangles & Area Ratio", "mathematics/geometry/triangles", "retag", "Applies theorem that ratio of areas of similar triangles equals square of side ratios (16:81)."),
    37: (6, "Trigonometric Identities", "mathematics/geometry", "retag", "Simplifies secθ + tan³θ·cosecθ into (1 + tan²θ)^(3/2) to express in parameter e."),
    38: (6, "Trigonometric Ratios in Quadrants", "mathematics/geometry", "retag", "Evaluates double angle and linear trigonometric expression in third quadrant with tanA = 4/3."),
    39: (6, "Heights & Distances", "mathematics/geometry", "retag", "Computes tower height from complementary angles of elevation at distances a and b (h = √ab)."),
    40: (6, "Heights & Distances", "mathematics/geometry", "retag", "Calculates speed of approaching boat from depression angles over uniform time interval."),
    41: (6, "Coordinate Geometry (Collinearity)", "mathematics/geometry/lines-and-angles", "retag", "Applies collinearity condition on intercept points (a,0), (0,b), (1,1) -> 1/a + 1/b = 1."),
    42: (6, "Coordinate Geometry (Section Formula)", "mathematics/geometry/lines-and-angles", "retag", "Computes internal division coordinates of line segment between given endpoints."),
    43: (6, "Coordinate Geometry (Perimeter of Triangle)", "mathematics/geometry/triangles", "retag", "Calculates perimeter of right triangle formed by coordinates (0,0), (1,0), (0,1)."),
    # Page 7: Q44-Q51
    44: (7, "Linear Equations (Simultaneous)", "mathematics/algebra/linear-equations", "retag", "Solves simultaneous linear equations 3x - 5y = -8 and 3x + 5y = 32 to evaluate p - q."),
    45: (7, "Trigonometry (Extrema)", "mathematics/geometry", "retag", "Finds minimum value of sin²θ + cos⁴θ using quadratic in sin²θ or cos²θ."),
    46: (7, "Probability (Conditional)", "reasoning-and-aptitude/numerical-ability", "retag", "Evaluates conditional probability P(B / A^c ∪ B) using set probability laws."),
    47: (7, "Probability (Mutually Exclusive Events)", "reasoning-and-aptitude/numerical-ability", "retag", "Identifies property P(E₁ ∩ E₂) = 0 and additive rule for mutually exclusive events."),
    48: (7, "Probability (Independent Events)", "reasoning-and-aptitude/numerical-ability", "retag", "Calculates probability of occurrence of at least one event among 8 independent events."),
    49: (7, "Statistics (Normal Distribution)", "reasoning-and-aptitude/numerical-ability", "retag", "Rectifies inactive 'statistics' baseline: identifies mean = median = mode symmetry in normal distribution."),
    50: (7, "Probability (Set Operations)", "reasoning-and-aptitude/numerical-ability", "retag", "Evaluates probability of intersection of union and complements (null event = 0)."),
    51: (7, "Statistics (Binomial Distribution)", "reasoning-and-aptitude/numerical-ability", "retag", "Determines bounds on standard deviation √(npq) given mean np = 25."),
    # Page 8: Q52-Q58
    52: (8, "Probability (Binomial / Combinations)", "reasoning-and-aptitude/numerical-ability", "retag", "Calculates probability of exactly 1 girl among 3 children: 3/8."),
    53: (8, "Probability (Complementary Conditional)", "reasoning-and-aptitude/numerical-ability", "retag", "Evaluates conditional probability of complements P(Ā/B̄)."),
    54: (8, "Probability (Binomial Distribution)", "reasoning-and-aptitude/numerical-ability", "retag", "Solves parameter p in B(5,p) equating P(X=2) and P(X=3) -> p = 1/2."),
    55: (8, "Probability (Combinations & Tickets)", "reasoning-and-aptitude/numerical-ability", "retag", "Calculates probability of drawing specific ticket numbers from 1 to 50."),
    56: (8, "Statistics (Regression Coefficients)", "reasoning-and-aptitude/numerical-ability", "retag", "Rectifies inactive 'statistics' baseline: relates regression coefficients to correlation r = √(b_yx · b_xy)."),
    57: (8, "Statistics (Standard Deviation Shift)", "reasoning-and-aptitude/numerical-ability", "retag", "Evaluates effect of additive and scalar constant modifications on standard deviation."),
    58: (8, "Statistics (Regression Lines)", "reasoning-and-aptitude/numerical-ability", "retag", "Rectifies inactive 'statistics' baseline: deduces correlation r = ±1 when regression lines coincide."),
    # Page 9: Q59-Q65
    59: (9, "Statistics (Bivariate Regression)", "reasoning-and-aptitude/numerical-ability", "retag", "Calculates correlation coefficient and variance of y from regression lines and variance of x."),
    60: (9, "Statistics (Bivariate Regression)", "reasoning-and-aptitude/numerical-ability", "retag", "Identifies means (x̄, ȳ) as intersection point of regression lines."),
    61: (9, "Calculus & Analysis (Strictly Increasing)", "mathematics", "keep", "Confirms top-level mathematics subject for monotonicity condition f'(x) = a > 0."),
    62: (9, "Calculus & Analysis (Curves & Tangents)", "mathematics", "keep", "Confirms top-level mathematics subject for vertical tangent / inflection behavior of y = x^(1/5)."),
    63: (9, "Calculus & Analysis (Limits)", "mathematics", "keep", "Confirms top-level mathematics subject for limit evaluation using L'Hopital's rule lim(x->0) (a^x-1)/(√(1+x)-1) = 2 ln a."),
    64: (9, "Calculus & Analysis (Continuity & Differentiability)", "mathematics", "keep", "Confirms top-level mathematics subject for differentiability of piecewise function x²/|x|."),
    65: (9, "Calculus & Analysis (Mean Value Theorems)", "mathematics", "keep", "Confirms top-level mathematics subject for Cauchy's Mean Value Theorem applicability."),
    # Page 10: Q66-Q72
    66: (10, "Calculus & Analysis (Extrema & Derivatives)", "mathematics", "keep", "Confirms top-level mathematics subject for determining parameters α, β from stationary points."),
    67: (10, "Calculus & Analysis (Rolle's Theorem)", "mathematics", "keep", "Confirms top-level mathematics subject for solving parameters b, c where Rolle's point c = 4/3."),
    68: (10, "Calculus & Analysis (Implicit Differentiation)", "mathematics", "keep", "Confirms top-level mathematics subject for second derivative of homogenous conic section."),
    69: (10, "Calculus & Analysis (Local Extrema)", "mathematics", "keep", "Confirms top-level mathematics subject for finding local maximum of cubic polynomial."),
    70: (10, "Calculus & Analysis (Derivative of Modulus)", "mathematics", "keep", "Confirms top-level mathematics subject for evaluating derivative of 3|2+x| at x = -3."),
    71: (10, "Calculus & Analysis (Partial Derivatives)", "mathematics", "keep", "Confirms top-level mathematics subject for homogeneous Euler theorem on u = √(x²+y²+z²)."),
    72: (10, "Calculus & Analysis (Partial Derivatives / Euler's Theorem)", "mathematics", "keep", "Confirms top-level mathematics subject for Euler's Theorem on homogeneous functions."),
    # Page 11: Q73-Q75
    73: (11, "Calculus & Analysis (Indefinite Integration)", "mathematics", "keep", "Confirms top-level mathematics subject for substitution integral ∫ 2^(2^x)·2^x dx."),
    74: (11, "Calculus & Analysis (Definite Integrals)", "mathematics", "keep", "Confirms top-level mathematics subject for integral of odd function composition over symmetric interval."),
    75: (11, "Calculus & Analysis (Integrals with Modulus)", "mathematics", "keep", "Confirms top-level mathematics subject for definite integral of signum step |x+2|/(x+2) over [-1, 1].")
}

candidates = []
findings = []

breakdown = {}
action_counts = {"retag": 0, "keep": 0}

for idx, it in enumerate(packet["items"], 1):
    qnum = idx
    page, skill, path_str, action, rationale = specs[qnum]
    proposed_tax = parse_path(path_str)
    
    cur_class = it["snapshot"]["record"]["classification"]
    cur_sub = cur_class.get("subject_id")
    cur_top = cur_class.get("topic_id")
    cur_subtop = cur_class.get("subtopic_id")
    
    if cur_subtop:
        cur_path = cur_subtop
    elif cur_top:
        cur_path = cur_top
    elif cur_sub:
        cur_path = cur_sub
    else:
        cur_path = "untagged"
    
    prop_path = path_str
    
    breakdown[prop_path] = breakdown.get(prop_path, 0) + 1
    action_counts[action] = action_counts.get(action, 0) + 1
    
    cand = {
        "canonical_id": it["canonical_id"],
        "appearance_id": it["appearance_id"],
        "paper_id": it["appearance"]["paper_id"],
        "source_fingerprint": it["source_fingerprint"],
        "review_status": "pending",
        "action": action,
        "current_primary": cur_class,
        "proposed_primary": proposed_tax,
        "rationale": rationale,
        "batch_id": 41,
        "policy": "study-tagging-v1"
    }
    candidates.append(cand)
    
    finding = {
        "index": idx,
        "canonical_id": it["canonical_id"],
        "appearance_id": it["appearance_id"],
        "printed_question": f"Q{idx}",
        "physical_page": page,
        "tested_skill": skill,
        "current_path": cur_path,
        "proposed_path": prop_path,
        "action": action,
        "rationale": rationale
    }
    findings.append(finding)

assert len(candidates) == 75
assert len(findings) == 75

(batch_dir / "pending-candidates.json").write_text(json.dumps(candidates, indent=2) + "\n")
(batch_dir / "findings.json").write_text(json.dumps(findings, indent=2) + "\n")

summary = {
    "batch": 41,
    "paper_id": "Old_Questions/Direct_2014-2018/2.Mathematics Paper-I.pdf",
    "paper_title": "Competitive Examinations for Recruitment to the Posts of High School Teacher (Mathematics) (September, 2017) — Technical Paper-I",
    "document_id": "doc_3bbda79f063fd1c62ac7e8a3",
    "sha256": "401c946be44fd24deabfc9cb51398970d6dadfc4aa99c467d23c60b73dc51798",
    "targets": 75,
    "completion": "100% of extracted MCQs reviewed",
    "actions": action_counts,
    "unextracted_items_preserved": 0,
    "breakdown": breakdown,
    "all_pending": True,
    "live_changes": 0
}

(batch_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
print(f"Generated {len(candidates)} pending review candidates.")
print(f"Saved {len(findings)} detailed findings.")
print(f"Saved summary.json:\n{json.dumps(summary, indent=2)}")
