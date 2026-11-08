"""Generate review candidates and findings for Batch 35.
Paper: Assistant Sub Inspector (Ministerial) under Home Department (October, 2018) — Mathematics (100 MCQs).
"""
import json
from pathlib import Path

batch_dir = Path(__file__).resolve().parent
packet = json.load(open(batch_dir / "oracle-packet.json"))

# We construct the 100 proposals dictionary mapped by question number (1 to 100)
# Then map by canonical_id / appearance_id
P = {
    1: ("Venn Diagram / Sets (Union, intersection: n(A∪B) = n(A) + n(B) - n(A∩B))", "mathematics/arithmetic", "Sets and basic group counts; assign to Arithmetic foundational topic."),
    2: ("Profit and Loss (Gain percentage: cost price ` 500, selling price ` 750)", "mathematics/arithmetic/profit-and-loss", "Basic gain percentage calculation; assign to Profit and Loss subtopic."),
    3: ("Profit and Loss (Selling price from cost price ` 1650 and gain 4%)", "mathematics/arithmetic/profit-and-loss", "Selling price determination; assign to Profit and Loss subtopic."),
    4: ("Profit and Loss (Discount percentage from marked price and selling price)", "mathematics/arithmetic/profit-and-loss", "Trade discount percentage; assign to Profit and Loss subtopic."),
    5: ("Ratio and Proportion (Compound ratio: a:b = 7:5, b:c = 10:13 -> a:c)", "mathematics/arithmetic/ratio-and-proportion", "Compound ratio chaining; assign to Ratio and Proportion subtopic."),
    6: ("Ratio and Proportion (Unitary method: 6 bowls cost ` 180, cost of 20 bowls)", "mathematics/arithmetic/ratio-and-proportion", "Direct proportion and unitary method; assign to Ratio and Proportion subtopic."),
    7: ("Ratio and Proportion (Terms of ratio: number added to 11:29)", "mathematics/arithmetic/ratio-and-proportion", "Ratio modification by added constant; assign to Ratio and Proportion subtopic."),
    8: ("Arithmetic / Rational Numbers (Fraction subtraction: 5/7 - x = -1)", "mathematics/arithmetic", "Rational number arithmetic; assign to Arithmetic topic."),
    9: ("Arithmetic / Roots (Cube root of 2744 = 14)", "mathematics/arithmetic", "Cube root evaluation; assign to Arithmetic topic."),
    10: ("Arithmetic / Surds (Simplification: √32 - √8 + √18)", "mathematics/arithmetic", "Radical surds simplification; assign to Arithmetic topic."),
    11: ("Arithmetic / Surds (Rationalization of denominator: 1/(9-√8))", "mathematics/arithmetic", "Surd rationalization; assign to Arithmetic topic."),
    12: ("Algebra / Exponents (Indices equation: 3^(2x+1) ÷ 9 = 27)", "mathematics/algebra", "Exponential equation; assign to Algebra topic."),
    13: ("Arithmetic / Fractions (Sum of squares of unit fractions)", "mathematics/arithmetic", "Fractional square summation; assign to Arithmetic topic."),
    14: ("Algebra / Algebraic Identities (Evaluation of x² + 1/x² given x + 1/x = 5)", "mathematics/algebra/algebraic-expressions", "Standard algebraic identity (a+b)²; assign to Algebraic Expressions subtopic."),
    15: ("Percentages (What percent of 80 is 16)", "mathematics/arithmetic/percentages", "Elementary percentage calculation; assign to Percentages subtopic."),
    16: ("Percentages (Percentage of a number: 12% is 15 -> 20% is ?)", "mathematics/arithmetic/percentages", "Proportional percentage calculation; assign to Percentages subtopic."),
    17: ("Percentages (Complementary percentage: 36% girls, boys count)", "mathematics/arithmetic/percentages", "Population percentage breakdown; assign to Percentages subtopic."),
    18: ("Profit and Loss (Sales tax on purchase price ` 4500 at 5%)", "mathematics/arithmetic/profit-and-loss", "Commercial sales tax calculation; assign to Profit and Loss subtopic."),
    19: ("Algebra / Linear Equations (Word problem: 2/3 of a number is 20 less)", "mathematics/algebra/linear-equations", "Single-variable linear equation; assign to Linear Equations subtopic."),
    20: ("Algebra / Linear Equations (Age word problem: Siami and mother)", "mathematics/algebra/linear-equations", "Age problem linear equation; assign to Linear Equations subtopic."),
    21: ("Arithmetic / Simple Interest (Time calculation: ` 500 to ` 1200 at 10%)", "mathematics/arithmetic", "Simple interest duration formula; assign to Arithmetic topic."),
    22: ("Arithmetic / Compound Interest (Half-yearly compounding on ` 6250 at 8%)", "mathematics/arithmetic", "Compound interest compounding formula; assign to Arithmetic topic."),
    23: ("Averages (Arithmetic mean of 2, 5, x, 8 is 6)", "mathematics/arithmetic/averages", "Mean of discrete observations; assign to Averages subtopic."),
    24: ("Numerical Ability / Statistics (Median of 8 raw numbers)", "reasoning-and-aptitude/numerical-ability", "Median calculation on ordered dataset; assign to Numerical Ability topic."),
    25: ("Averages (Property of mean when constant 5 is added to all items)", "mathematics/arithmetic/averages", "Arithmetic mean invariance under constant addition; assign to Averages subtopic."),
    26: ("Numerical Ability / Statistics (Mode of discrete frequency data)", "reasoning-and-aptitude/numerical-ability", "Mode determination; assign to Numerical Ability topic."),
    27: ("Numerical Ability / Statistics (Class mark of interval 120-140)", "reasoning-and-aptitude/numerical-ability", "Class mark midpoint calculation; assign to Numerical Ability topic."),
    28: ("Geometry / Angles (Complement of 2/3 of a right angle)", "mathematics/geometry/lines-and-angles", "Complementary angle relation; assign to Lines and Angles subtopic."),
    29: ("Arithmetic / Time, Speed & Distance (Conversion from m/s to km/hr)", "mathematics/arithmetic", "Unit conversion in speed; assign to Arithmetic topic."),
    30: ("Arithmetic / Time & Work (A and B together in 12 days, A alone in 20 days)", "mathematics/arithmetic", "Work rate combined equation; assign to Arithmetic topic."),
    31: ("Numerical Ability / Probability (Probability of a sure event = 1)", "reasoning-and-aptitude/numerical-ability", "Axiomatic probability of certain event; assign to Numerical Ability topic."),
    32: ("Numerical Ability / Probability (Probability of drawing red ball from bag)", "reasoning-and-aptitude/numerical-ability", "Classical probability from ball counts; assign to Numerical Ability topic."),
    33: ("Numerical Ability / Probability (Probability of face card from deck of 52)", "reasoning-and-aptitude/numerical-ability", "Standard card deck probability; assign to Numerical Ability topic."),
    34: ("Algebra / Progressions (Finding term where AP 72, 68, 64... becomes 0)", "mathematics/algebra", "Arithmetic progression nth term; assign to Algebra topic."),
    35: ("Algebra / Progressions (8th term from the end of AP 7, 10, ... 184)", "mathematics/algebra", "Reverse term calculation in AP; assign to Algebra topic."),
    36: ("Algebra / Progressions (Sum of first 10 terms of AP 2, 7, 12...)", "mathematics/algebra", "AP sum formula Sn = n/2(2a+(n-1)d); assign to Algebra topic."),
    37: ("Geometry / Trigonometry (Evaluation of cot²45° - sin²60° = x sin45°cos45°)", "mathematics/geometry", "Standard trigonometric angles substitution; assign to Geometry topic."),
    38: ("Geometry / Trigonometry (Angle of elevation from height and shadow length)", "mathematics/geometry", "Heights and distances trigonometric tangent ratio; assign to Geometry topic."),
    39: ("Geometry / Coordinate Geometry (Distance of point P(8,6) from origin)", "mathematics/geometry", "Distance formula in Cartesian plane; assign to Geometry topic."),
    40: ("Mensuration (Area of rectangular plot given perimeter 80m and breadth 16m)", "mathematics/mensuration/area", "Perimeter and area of rectangle; assign to Area subtopic."),
    41: ("Mensuration (Rebending circular wire of radius 28cm into square)", "mathematics/mensuration/area", "Circumference to perimeter equivalence; assign to Area subtopic."),
    42: ("Mensuration (Side of equilateral triangle from area 9√3 cm²)", "mathematics/mensuration/area", "Equilateral triangle area formula; assign to Area subtopic."),
    43: ("Mensuration (Volume of cube from lateral surface area 256 cm²)", "mathematics/mensuration/volume", "Cube surface area to volume relation; assign to Volume subtopic."),
    44: ("Mensuration (Number of smaller 2cm cubes cut from 6cm cube)", "mathematics/mensuration/volume", "Volume conservation in solid division; assign to Volume subtopic."),
    45: ("Geometry / Angles (Two complementary angles in ratio 2:3)", "mathematics/geometry/lines-and-angles", "Ratio-based complementary angles; assign to Lines and Angles subtopic."),
    46: ("Geometry / Triangles (Displacement using Pythagoras theorem: 15m west, 8m north)", "mathematics/geometry/triangles", "Pythagorean right triangle distance; assign to Triangles subtopic."),
    47: ("Ratio and Proportion (Proportion equation: 75:15 = x:7)", "mathematics/arithmetic/ratio-and-proportion", "Direct proportion product of extremes/means; assign to Ratio and Proportion subtopic."),
    48: ("Arithmetic / Order of Operations (BODMAS: 4 + 12÷2 + 7 - 5×6)", "mathematics/arithmetic", "BODMAS order of arithmetic operations; assign to Arithmetic topic."),
    49: ("Percentages (Population percentage increase: 50,000 to 52,000)", "mathematics/arithmetic/percentages", "Percentage increase on base value; assign to Percentages subtopic."),
    50: ("Geometry / Angles (Acute angle between clock hands at 2:00)", "mathematics/geometry/lines-and-angles", "Clock hand angle calculation (60°); assign to Lines and Angles subtopic."),
    51: ("Percentages (Percentage score: 320 out of 500 marks)", "mathematics/arithmetic/percentages", "Standard percentage mark calculation; assign to Percentages subtopic."),
    52: ("Algebra / Linear Equations (System of linear equations: x+y=46, x-y=12)", "mathematics/algebra/linear-equations", "Simultaneous linear equations; assign to Linear Equations subtopic."),
    53: ("Geometry / Circles (Radius from circumference 88 cm)", "mathematics/geometry/circles", "Circle circumference formula 2πr; assign to Circles subtopic."),
    54: ("Arithmetic / Time, Speed & Distance (Train crossing a post: 100m at 60 km/hr)", "mathematics/arithmetic", "Train passing a point object; assign to Arithmetic topic."),
    55: ("Arithmetic / Installments (Total paid on loan of 60,000 in three 22,000 installments)", "mathematics/arithmetic", "Commercial loan installment arithmetic; assign to Arithmetic topic."),
    56: ("Arithmetic / Elementary Logic (Cutting 20m rope into 2m pieces: cuts count)", "mathematics/arithmetic", "Number of cuts logic (n-1 cuts); assign to Arithmetic topic."),
    57: ("Algebra / Algebraic Identities (Evaluation of x²+y² given x-y=2 and xy=15)", "mathematics/algebra/algebraic-expressions", "Algebraic identity (x-y)² + 2xy; assign to Algebraic Expressions subtopic."),
    58: ("Geometry / Angles (Revolutions of minute hand in one day)", "mathematics/geometry/lines-and-angles", "Clock revolution count in 24 hours (24 revolutions); assign to Lines and Angles subtopic."),
    59: ("Geometry / Triangles (Third angle of triangle given 50° and 60°)", "mathematics/geometry/triangles", "Angle sum property of triangle (180°); assign to Triangles subtopic."),
    60: ("Percentages (Percentage decrease in price from ` 25 to ` 20)", "mathematics/arithmetic/percentages", "Percentage reduction on original price; assign to Percentages subtopic."),
    61: ("Ratio and Proportion (Combining ratios: a:b=3:4, b:c=6:5 -> a:b:c)", "mathematics/arithmetic/ratio-and-proportion", "Three-term continuous ratio combination; assign to Ratio and Proportion subtopic."),
    62: ("Profit and Loss (Successive discounts: 30% and 20% equivalent single discount)", "mathematics/arithmetic/profit-and-loss", "Successive discount formula; assign to Profit and Loss subtopic."),
    63: ("Percentages (Finding salary from 75% expenditure and ` 15,000 savings)", "mathematics/arithmetic/percentages", "Percentage savings complement (25% = 15,000); assign to Percentages subtopic."),
    64: ("Geometry / Triangles (Largest angle of triangle with angle ratio 1:2:3)", "mathematics/geometry/triangles", "Ratio-based triangle angle sum; assign to Triangles subtopic."),
    65: ("Averages (Mean age of 10 students)", "mathematics/arithmetic/averages", "Arithmetic mean of ungrouped dataset; assign to Averages subtopic."),
    66: ("Arithmetic / Time, Speed & Distance (Distance traveled at 75 km/hr in 20 minutes)", "mathematics/arithmetic", "Speed-time distance formula with minute conversion; assign to Arithmetic topic."),
    67: ("Arithmetic / Surds (Simplification of surd expression: √50, √20, etc.)", "mathematics/arithmetic", "Radical surds factoring; assign to Arithmetic topic."),
    68: ("Percentages (Percentage of 1 min 12 sec to 1 hour)", "mathematics/arithmetic/percentages", "Time unit normalization and percentage; assign to Percentages subtopic."),
    69: ("Percentages (Number exceeding 20% of itself by 40)", "mathematics/arithmetic/percentages", "Linear percentage equation; assign to Percentages subtopic."),
    70: ("Arithmetic / Time, Speed & Distance (Speed of sound distance: thunder after 2s)", "mathematics/arithmetic", "Distance = speed × time; assign to Arithmetic topic."),
    71: ("Arithmetic / Square Roots (Square arrangement of 1089 students: √1089)", "mathematics/arithmetic", "Square root application to grid seating; assign to Arithmetic topic."),
    72: ("Algebra / Linear Equations (Number equation: x/4 - 4 = 3)", "mathematics/algebra/linear-equations", "Fractional linear equation; assign to Linear Equations subtopic."),
    73: ("Arithmetic / Time & Work (Anand in 12 days, Binod twice as fast)", "mathematics/arithmetic", "Work efficiency ratio; assign to Arithmetic topic."),
    74: ("Percentages (5% of ` 100 + 100% of ` 5)", "mathematics/arithmetic/percentages", "Percentage commutative property calculation; assign to Percentages subtopic."),
    75: ("Percentages (Pass mark percentage: 178 marks, fails by 22, pass=40%)", "mathematics/arithmetic/percentages", "Pass threshold percentage equation; assign to Percentages subtopic."),
    76: ("Arithmetic / Pipes & Cisterns (Inlet in 5 hours, outlet in 8 hours)", "mathematics/arithmetic", "Net fill rate of conflicting pipes; assign to Arithmetic topic."),
    77: ("Ratio and Proportion (Map scale ratio: 1cm to 5km)", "mathematics/arithmetic/ratio-and-proportion", "Representative map scale ratio; assign to Ratio and Proportion subtopic."),
    78: ("Mensuration (Longest pole in rectangular room: cuboid diagonal)", "mathematics/mensuration/volume", "Space diagonal of cuboid √(l²+b²+h²); assign to Volume subtopic."),
    79: ("Mensuration (Area of square from diagonal 110m: d²/2)", "mathematics/mensuration/area", "Square area from diagonal formula; assign to Area subtopic."),
    80: ("Geometry / Triangles (Ladder against wall: Pythagoras theorem)", "mathematics/geometry/triangles", "Right-angled triangle height/base relation; assign to Triangles subtopic."),
    81: ("Arithmetic / Time, Speed & Distance (Opposite direction walking distance)", "mathematics/arithmetic", "Relative speed in opposite directions; assign to Arithmetic topic."),
    82: ("Percentages (Percentage of remainder: 38 students, 3 absent, 20% fail)", "mathematics/arithmetic/percentages", "Sub-population percentage calculation; assign to Percentages subtopic."),
    83: ("Profit and Loss (Cost price from selling price ` 660 and gain 10%)", "mathematics/arithmetic/profit-and-loss", "Cost price extraction formula; assign to Profit and Loss subtopic."),
    84: ("Arithmetic / Fractions & Decimals (Evaluation of √81 / 0.09)", "mathematics/arithmetic", "Square root and decimal division; assign to Arithmetic topic."),
    85: ("Averages (Three numbers average 7, first two average 4 -> third number)", "mathematics/arithmetic/averages", "Total sum from average decomposition; assign to Averages subtopic."),
    86: ("Arithmetic / Number Theory (Product of two numbers = HCF × LCM)", "mathematics/arithmetic", "Fundamental HCF-LCM product theorem; assign to Arithmetic topic."),
    87: ("Arithmetic / Time & Work (A, B and C individual and combined rates)", "mathematics/arithmetic", "Three-worker work rate equation; assign to Arithmetic topic."),
    88: ("Arithmetic / Real-World Arithmetic (Electricity meter consumption calculation)", "mathematics/arithmetic", "Meter unit difference and cost; assign to Arithmetic topic."),
    89: ("Arithmetic / Mixed Fractions (Simplification of mixed fractions)", "mathematics/arithmetic", "Mixed number arithmetic evaluation; assign to Arithmetic topic."),
    90: ("Arithmetic / Surds (Simplification of rational radical fraction)", "mathematics/arithmetic", "Identical numerator/denominator algebraic reduction; assign to Arithmetic topic."),
    91: ("Arithmetic / Surds (Radical identity equation: √18 + √14 = x - √84)", "mathematics/arithmetic", "Surd equation balancing; assign to Arithmetic topic."),
    92: ("Profit and Loss (Marked price before sales tax)", "mathematics/arithmetic/profit-and-loss", "Reverse sales tax deduction; assign to Profit and Loss subtopic."),
    93: ("Mensuration (Grazing area of horse tied at corner of rectangular field)", "mathematics/mensuration/area", "Quadrant sector area (πr²/4); assign to Area subtopic."),
    94: ("Averages (Average age increase with teacher included)", "mathematics/arithmetic/averages", "Weighted average increment; assign to Averages subtopic."),
    95: ("Mensuration (Floor carpet area and border path)", "mathematics/mensuration/area", "Area of rectangular floor; assign to Area subtopic."),
    96: ("Mensuration (Number of square tiles to pave rectangular floor)", "mathematics/mensuration/area", "Area division by unit tile size; assign to Area subtopic."),
    97: ("Mensuration (Comparison of area when 44cm wire is bent into circle vs square)", "mathematics/mensuration/area", "Isoperimetric area comparison; assign to Area subtopic."),
    98: ("Profit and Loss (Identical selling price with +10% gain and -10% loss -> overall loss)", "mathematics/arithmetic/profit-and-loss", "Standard dual-sale overall percentage loss (x²/100 %); assign to Profit and Loss subtopic."),
    99: ("Arithmetic / Square Numbers (Multiplier to make 396 a perfect square: prime factorization)", "mathematics/arithmetic", "Prime factorization to find unpaired factor; assign to Arithmetic topic."),
    100: ("Numerical Ability / Probability (Probability of getting exactly 2 heads in 3 coin tosses: 3/8)", "reasoning-and-aptitude/numerical-ability", "Binomial probability in 3 coin tosses; assign to Numerical Ability topic.")
}

assert len(P) == 100

# Parse path into subject, topic, subtopic
def parse_path(path_str):
    parts = path_str.split("/")
    if len(parts) == 1:
        return {"subject_id": parts[0], "topic_id": None, "subtopic_id": None}
    elif len(parts) == 2:
        return {"subject_id": parts[0], "topic_id": path_str, "subtopic_id": None}
    elif len(parts) == 3:
        return {"subject_id": parts[0], "topic_id": f"{parts[0]}/{parts[1]}", "subtopic_id": path_str}
    raise ValueError(path_str)

candidates = []
findings = []
breakdown = {}

for item in packet["items"]:
    aid = item["appearance_id"]
    cid = item["canonical_id"]
    qnum = int(item["appearance"]["qnum"])
    page = item["appearance"]["page"]
    
    skill, path_str, rat = P[qnum]
    proposed_tax = parse_path(path_str)
    
    breakdown[path_str] = breakdown.get(path_str, 0) + 1
    
    c_rec = {
        "canonical_id": cid,
        "appearance_id": aid,
        "source_fingerprint": item["source_fingerprint"],
        "review_status": "pending",
        "action": "retag",
        "current_primary": item["snapshot"]["record"]["classification"],
        "proposed_primary": proposed_tax,
        "rationale": rat,
        "batch_id": 35,
        "policy": "study-tagging-v1"
    }
    candidates.append(c_rec)
    
    findings.append({
        "canonical_id": cid,
        "appearance_id": aid,
        "printed_question": f"Q{qnum}",
        "physical_page": page,
        "tested_skill": skill,
        "action": "retag",
        "current_path": (item["snapshot"]["record"]["classification"]["subject_id"] or "null") if item["snapshot"]["record"]["classification"] else "null",
        "proposed_path": path_str,
        "rationale": rat
    })

(batch_dir / "pending-candidates.json").write_text(json.dumps(candidates, indent=2) + "\n")
(batch_dir / "findings.json").write_text(json.dumps(findings, indent=2) + "\n")

# This paper has zero unextracted conventional prompts (all 100 MCQs extracted in DB)
unextracted_items = []
(batch_dir / "pending-written-intake.json").write_text(json.dumps(unextracted_items, indent=2) + "\n")

summary = {
    "batch": 35,
    "paper_id": "Old_Questions/Direct_2014-2018/14..pdf",
    "paper_title": "General Competitive Examinations for Recruitment to the Post of Assistant Sub Inspector (Ministerial) under Home Department (October, 2018) — Mathematics",
    "document_id": "doc_5c1f675b19f778f61bcf7eaf",
    "sha256": "fea1083e5718886fdf40c49c71a39626b9a897931c8901eb0d5c0e18ddbc7c21",
    "targets": 100,
    "completion": "100% of paper's questions reviewed",
    "actions": {
        "retag": 100,
        "keep": 0
    },
    "unextracted_items_preserved": 0,
    "breakdown": breakdown,
    "all_pending": True,
    "live_changes": 0
}

(batch_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
print(f"Generated {len(candidates)} pending review candidates.")
print(f"Saved {len(findings)} detailed findings.")
print(f"Saved summary.json: {json.dumps(summary, indent=2)}")
