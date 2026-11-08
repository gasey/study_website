"""Generate review candidates and findings for Batch 37.
Paper: Sub Inspector (UB) under Home Department (October, 2018) — Mathematics (100 MCQs)
Target: 100 MCQs.
All 100 currently untagged (subject=null, topic=null).
"""
import json
from pathlib import Path

batch_dir = Path(__file__).resolve().parent
packet = json.load(open(batch_dir / "oracle-packet.json"))

P = {
    1: ("Fractions (Fraction word problem: 7/9 read, 40 left)", "mathematics/arithmetic", "Fractional portion calculation; assign to Arithmetic topic."),
    2: ("Fractions (Cutting pieces from 11m rope: remaining length)", "mathematics/arithmetic", "Mixed number subtraction; assign to Arithmetic topic."),
    3: ("Square Roots (Least number subtracted from 7250 to get perfect square)", "mathematics/arithmetic", "Long division square root method; assign to Arithmetic topic."),
    4: ("Profit and Loss (Discount percentage: marked price 2700, offered at 2025)", "mathematics/arithmetic/profit-and-loss", "Discount percentage formula; assign to Profit and Loss subtopic."),
    5: ("Compound Interest (Amount on 10,000 for 2 years at 8% per annum)", "mathematics/arithmetic", "Annual compounding formula; assign to Arithmetic topic."),
    6: ("Algebraic Identities (x² + y² from x - y = 7 and xy = 9)", "mathematics/algebra/algebraic-expressions", "Standard identity (x-y)² + 2xy; assign to Algebraic Expressions subtopic."),
    7: ("Linear Equations (A + B - C + 100 = 350 with A=2B, B=2C)", "mathematics/algebra/linear-equations", "Single variable substitution equation; assign to Linear Equations subtopic."),
    8: ("Linear Equations (Simultaneous equations: 5 pens + 2 pencils = 85)", "mathematics/algebra/linear-equations", "Elimination method for linear system; assign to Linear Equations subtopic."),
    9: ("Geometry / Angles (Angle 36° more than its complement: x - (90-x) = 36)", "mathematics/geometry/lines-and-angles", "Complementary angles linear equation; assign to Lines and Angles subtopic."),
    10: ("Geometry / Triangles (Angles in ratio 2:3:7: smallest angle)", "mathematics/geometry/triangles", "Angle sum property of triangle (180°); assign to Triangles subtopic."),
    11: ("Geometry / Circles (Radius from circumference 66 cm: 2πr = 66)", "mathematics/geometry/circles", "Circumference of circle formula; assign to Circles subtopic."),
    12: ("Mensuration / Volume (Longest pole in 10×10×5m room: cuboid diagonal)", "mathematics/mensuration/volume", "Space diagonal of cuboid √(l²+b²+h²); assign to Volume subtopic."),
    13: ("Simple Interest (Time for 1250 to amount to 1400 at 6%)", "mathematics/arithmetic", "Simple interest duration formula; assign to Arithmetic topic."),
    14: ("Number Systems (Conversion of recurring decimal 0.3636... to p/q)", "mathematics/arithmetic", "Pure recurring decimal to fraction; assign to Arithmetic topic."),
    15: ("Percentages / Depreciation (Machine depreciation at 20% per annum)", "mathematics/arithmetic/percentages", "Annual compound depreciation formula; assign to Percentages subtopic."),
    16: ("Ratio and Proportion (Dividing 3645 in ratio 2:3:4: B's share)", "mathematics/arithmetic/ratio-and-proportion", "Proportional division of money; assign to Ratio and Proportion subtopic."),
    17: ("Mensuration / Area (Side of equilateral triangle from area 49√3 cm²)", "mathematics/mensuration/area", "Equilateral triangle area formula; assign to Area subtopic."),
    18: ("Mensuration / Volume (Air volume per person in 20×15×4.5m hall)", "mathematics/mensuration/volume", "Room volume divided by individual air quota; assign to Volume subtopic."),
    19: ("Mensuration / Volume (Number of bricks for 8m×6m×22.5cm wall)", "mathematics/mensuration/volume", "Volume of wall divided by volume of unit brick; assign to Volume subtopic."),
    20: ("Mensuration / Volume (Volume of cylindrical well: πr²h)", "mathematics/mensuration/volume", "Cylinder volume calculation; assign to Volume subtopic."),
    21: ("Averages (Mean weight of 6 boys is 48 kg: 6th boy weight)", "mathematics/arithmetic/averages", "Total sum from average minus 5 boys; assign to Averages subtopic."),
    22: ("Percentages (Town population increase at 5% per annum)", "mathematics/arithmetic/percentages", "Compound population growth formula; assign to Percentages subtopic."),
    23: ("Time, Speed & Distance (Walking in same/opposite directions: relative speed)", "mathematics/arithmetic", "Relative speed distance formula; assign to Arithmetic topic."),
    24: ("Time, Speed & Distance (Train 200m long at 80 km/hr passing pole/platform)", "mathematics/arithmetic", "Time = distance / speed with km/h to m/s conversion; assign to Arithmetic topic."),
    25: ("Time, Speed & Distance (Speed of sound: 1.32 km in 4 seconds)", "mathematics/arithmetic", "Basic speed = distance / time; assign to Arithmetic topic."),
    26: ("Time & Work (Man in 5 days, with son in 3 days -> son alone)", "mathematics/arithmetic", "Work rate subtraction formula; assign to Arithmetic topic."),
    27: ("Time & Work (A in 15 days, B in 20 days: 4 days together work left)", "mathematics/arithmetic", "Combined work done in given days; assign to Arithmetic topic."),
    28: ("Pipes & Cisterns (Pipe in 16 hours, leak causes 24 hours)", "mathematics/arithmetic", "Leak emptying rate formula; assign to Arithmetic topic."),
    29: ("Linear Equations (Two numbers diff 26, one is 3 times the other)", "mathematics/algebra/linear-equations", "Two-variable linear word problem; assign to Linear Equations subtopic."),
    30: ("Algebra / Progressions (105th term of AP 12, 17, 22...)", "mathematics/algebra", "Arithmetic progression nth term formula; assign to Algebra topic."),
    31: ("Algebra / Progressions (15th term from the end of AP 4, 9, 14... 254)", "mathematics/algebra", "AP term from reverse end formula; assign to Algebra topic."),
    32: ("Arithmetic / Sets (Venn diagram: 18 teachers English or Math)", "mathematics/arithmetic", "Two-set inclusion-exclusion formula; assign to Arithmetic topic."),
    33: ("Geometry / Triangles (Distance between tops of two vertical poles)", "mathematics/geometry/triangles", "Right-angled triangle Pythagoras theorem; assign to Triangles subtopic."),
    34: ("Mensuration / Area (Bus wheel radius 70cm: distance in revolutions)", "mathematics/mensuration/area", "Distance = revolutions × circumference; assign to Area subtopic."),
    35: ("Mensuration / Area (Area of circular ring: π(R² - r²))", "mathematics/mensuration/area", "Concentric circle ring area formula; assign to Area subtopic."),
    36: ("Geometry / Circles (Radius from circle area 616 cm²: πr² = 616)", "mathematics/geometry/circles", "Circle area to radius extraction; assign to Circles subtopic."),
    37: ("Mensuration / Volume (Cubes of side 2cm cut from 6cm cube: volume ratio)", "mathematics/mensuration/volume", "Cube volume division; assign to Volume subtopic."),
    38: ("Numerical Ability / Probability (Probability of prime number from balls 1 to 20)", "reasoning-and-aptitude/numerical-ability", "Prime number counting in sample space; assign to Numerical Ability topic."),
    39: ("Arithmetic / HCF & LCM (Bells tolling together: LCM of 3, 7, 12, 14 min)", "mathematics/arithmetic", "LCM application to periodic events; assign to Arithmetic topic."),
    40: ("Linear Equations (Boys 120 more than girls: total students)", "mathematics/algebra/linear-equations", "Simple single variable linear problem; assign to Linear Equations subtopic."),
    41: ("Ratio and Proportion (Ratio of bills 3:2, total ` 450)", "mathematics/arithmetic/ratio-and-proportion", "Proportional division; assign to Ratio and Proportion subtopic."),
    42: ("Mensuration / Area (Fencing perimeter of 70m×50m garden: posts count)", "mathematics/mensuration/area", "Perimeter spacing calculation; assign to Area subtopic."),
    43: ("Mensuration / Area (Flooring cost of 6m×4m room at unit rate)", "mathematics/mensuration/area", "Rectangular area and total cost; assign to Area subtopic."),
    44: ("Averages (Family of 7 avg age 18, head 60 excluded -> remaining avg)", "mathematics/arithmetic/averages", "Decomposed average calculation; assign to Averages subtopic."),
    45: ("Mensuration / Area (Perimeter of semicircular window of diameter 63cm)", "mathematics/mensuration/area", "Semicircle perimeter formula (πr + 2r); assign to Area subtopic."),
    46: ("Mensuration / Area (Diagonal path of 40m×30m rectangular hall)", "mathematics/mensuration/area", "Rectangle diagonal using Pythagoras; assign to Area subtopic."),
    47: ("Percentages (Discount 20% saves Rs 500: marked price)", "mathematics/arithmetic/percentages", "Base price from discount amount; assign to Percentages subtopic."),
    48: ("Reasoning / Mathematical Operations (Operator substitution BODMAS)", "reasoning-and-aptitude/numerical-ability", "Symbol interchange arithmetic; assign to Numerical Ability topic."),
    49: ("Reasoning / Mathematical Operations (Letter variable substitution)", "reasoning-and-aptitude/numerical-ability", "Alphabetical operator substitution; assign to Numerical Ability topic."),
    50: ("Profit and Loss (SP of 20 articles = CP of 21 articles)", "mathematics/arithmetic/profit-and-loss", "Article count equivalence profit percentage; assign to Profit and Loss subtopic."),
    51: ("Time & Work (Unitary method: 6 men in 20 days -> 8 men in ? days)", "mathematics/arithmetic", "Inverse proportion work formula (M1*D1 = M2*D2); assign to Arithmetic topic."),
    52: ("Time, Speed & Distance (Convert 60 km/h to m/s: 60 × 5/18)", "mathematics/arithmetic", "Speed unit conversion factor; assign to Arithmetic topic."),
    53: ("Time, Speed & Distance (Distance at 15 m/s in 20 minutes)", "mathematics/arithmetic", "Distance = speed × time with minute conversion; assign to Arithmetic topic."),
    54: ("Mensuration / Area (Area of square from diagonal 5.4 cm: d²/2)", "mathematics/mensuration/area", "Square diagonal area formula; assign to Area subtopic."),
    55: ("Time, Speed & Distance / Clock (Departure time: 6h 40m arrival at 9:00 PM)", "mathematics/arithmetic", "Time subtraction calculation; assign to Arithmetic topic."),
    56: ("Linear Equations (Ages of father 50 and son 5: ratio after n years)", "mathematics/algebra/linear-equations", "Age progression linear relation; assign to Linear Equations subtopic."),
    57: ("Linear Equations (Two digit number: ten's digit double unit's digit)", "mathematics/algebra/linear-equations", "Two-digit positional value equation; assign to Linear Equations subtopic."),
    58: ("Arithmetic / Sets (Survey of 1000 persons: three-set Venn diagram)", "mathematics/arithmetic", "Three-set Venn diagram calculation; assign to Arithmetic topic."),
    59: ("Algebra / Defined Operations (Binary operation: a * b = (a+5)²(b-7))", "mathematics/algebra", "Arbitrary algebraic operator evaluation; assign to Algebra topic."),
    60: ("Number Systems / Indices (Negative exponents simplification: (5⁻¹ × 3⁻²)⁻²)", "mathematics/arithmetic", "Laws of exponents; assign to Arithmetic topic."),
    61: ("Number Systems / Square Roots (Square root of decimal 0.00008281)", "mathematics/arithmetic", "Decimal square root evaluation; assign to Arithmetic topic."),
    62: ("Arithmetic / Square Roots (Square seating of 1089 students: √1089)", "mathematics/arithmetic", "Square root integer factorization; assign to Arithmetic topic."),
    63: ("Algebraic Identities (Find ab given a - b = 5 and a² + b² = 85)", "mathematics/algebra/algebraic-expressions", "Algebraic identity manipulation; assign to Algebraic Expressions subtopic."),
    64: ("Algebraic Identities (Find x⁴ + 1/x⁴ given x - 1/x = 3)", "mathematics/algebra/algebraic-expressions", "Successive squaring of reciprocal identity; assign to Algebraic Expressions subtopic."),
    65: ("Algebraic Identities (Find a² + b² + c² given a+b+c=14 and ab+bc+ac=25)", "mathematics/algebra/algebraic-expressions", "Three-variable identity (a+b+c)²; assign to Algebraic Expressions subtopic."),
    66: ("Algebraic Identities (Evaluate (a³ - b³)/(a² + ab + b²) = a - b)", "mathematics/algebra/algebraic-expressions", "Cubic identity cancellation; assign to Algebraic Expressions subtopic."),
    67: ("Percentages (Failed 42% English, 52% Math, 17% both: passing %)", "mathematics/arithmetic/percentages", "Venn diagram percentage intersection; assign to Percentages subtopic."),
    68: ("Linear Equations (2/3 of number is 20 less than number: x - 2x/3 = 20)", "mathematics/algebra/linear-equations", "Single variable fractional equation; assign to Linear Equations subtopic."),
    69: ("Time & Work (1 man or 2 women or 3 boys in 55 days)", "mathematics/arithmetic", "Equivalence work rate method; assign to Arithmetic topic."),
    70: ("Mensuration / Volume (Volume of metal in hemispherical bowl)", "mathematics/mensuration/volume", "Hollow hemisphere volume 2/3 π (R³ - r³); assign to Volume subtopic."),
    71: ("Percentages (Election votes percentage calculation)", "mathematics/arithmetic/percentages", "Vote fraction percentage; assign to Percentages subtopic."),
    72: ("Mensuration / Volume (Plane section of sphere: radius of cross section)", "mathematics/mensuration/volume", "Sphere plane section circle radius √(R² - d²); assign to Volume subtopic."),
    73: ("Profit and Loss (Successive discounts 8% and 12%: single discount)", "mathematics/arithmetic/profit-and-loss", "Successive discount formula; assign to Profit and Loss subtopic."),
    74: ("Arithmetic / Series (Sum of first 45 natural numbers: n(n+1)/2)", "mathematics/arithmetic", "Sum of natural numbers formula; assign to Arithmetic topic."),
    75: ("Percentages (Alloy composition: 10g copper in 50g total)", "mathematics/arithmetic/percentages", "Mass percentage in mixture; assign to Percentages subtopic."),
    76: ("Percentages / Mixtures (Impurity in sand-gravel mixture ratio 1:4)", "mathematics/arithmetic/percentages", "Weighted mixture percentage; assign to Percentages subtopic."),
    77: ("Profit and Loss (Profit equal to SP of chairs: gain percentage)", "mathematics/arithmetic/profit-and-loss", "Selling price profit equivalence; assign to Profit and Loss subtopic."),
    78: ("Pipes & Cisterns (Tap A fills in 8h, B empties in 10h: net fill time)", "mathematics/arithmetic", "Net fill rate 1/8 - 1/10; assign to Arithmetic topic."),
    79: ("Averages (Seven numbers: first 4 avg 4, last 4 avg 4 -> 4th number)", "mathematics/arithmetic/averages", "Overlapping subset average formula; assign to Averages subtopic."),
    80: ("Averages (Average of 100 items corrected for misread value)", "mathematics/arithmetic/averages", "Mean correction for recording error; assign to Averages subtopic."),
    81: ("Ratio and Proportion (Two numbers ratio 2:3, each decreased by 3)", "mathematics/arithmetic/ratio-and-proportion", "Proportion equation with constant subtraction; assign to Ratio and Proportion subtopic."),
    82: ("Ratio and Proportion (Partnership investments: A = 3B, B = 2/3 C)", "mathematics/arithmetic/ratio-and-proportion", "Partnership investment ratio chaining; assign to Ratio and Proportion subtopic."),
    83: ("Geometry / Trigonometry (Complementary angles evaluation: sin50/cos40)", "mathematics/geometry", "Trigonometric ratios of complementary angles; assign to Geometry topic."),
    84: ("Time, Speed & Distance (Time for 42 km/h car to cover 350 meters)", "mathematics/arithmetic", "Time = distance / speed with unit conversion; assign to Arithmetic topic."),
    85: ("Numerical Ability / Statistics (Empirical relation: Mode = 3 Median - 2 Mean)", "reasoning-and-aptitude/numerical-ability", "Empirical relationship among central tendencies; assign to Numerical Ability topic."),
    86: ("Algebra / Progressions (Number of terms in AP 3, 6, 9... 111)", "mathematics/algebra", "AP number of terms n = (l-a)/d + 1; assign to Algebra topic."),
    87: ("Linear Equations (Monthly budget expenditure and savings balance)", "mathematics/algebra/linear-equations", "Personal finance budget linear equation; assign to Linear Equations subtopic."),
    88: ("Mensuration / Volume (Planks of 5m×20cm×8cm stored in 18m×6m×4m space)", "mathematics/mensuration/volume", "Storage volume division; assign to Volume subtopic."),
    89: ("Mensuration / Volume (Total surface area of solid hemisphere: 3πr²)", "mathematics/mensuration/volume", "Solid hemisphere surface area formula; assign to Volume subtopic."),
    90: ("Mensuration / Volume (Melting three metallic spheres 3, 4, 5cm into single sphere)", "mathematics/mensuration/volume", "Volume conservation sum of cubes (3³+4³+5³ = 6³); assign to Volume subtopic."),
    91: ("Mensuration / Area (Area swept by 21cm minute hand in given minutes)", "mathematics/mensuration/area", "Sector area of clock face; assign to Area subtopic."),
    92: ("Mensuration / Area (Area of equilateral triangle of side 8cm: √3/4 s²)", "mathematics/mensuration/area", "Equilateral triangle area formula; assign to Area subtopic."),
    93: ("Mensuration / Volume (Cylinder volume 448π cm³ and height 7cm -> radius)", "mathematics/mensuration/volume", "Cylinder volume formula V = πr²h; assign to Volume subtopic."),
    94: ("Mensuration / Volume (Sphere volume ratio when radius is doubled: 2³ = 8)", "mathematics/mensuration/volume", "Cube scaling ratio in sphere volume; assign to Volume subtopic."),
    95: ("Number Systems / Surds (Solving radical equation for x)", "mathematics/arithmetic", "Radical equation evaluation; assign to Arithmetic topic."),
    96: ("Mensuration / Area (Isosceles triangle base 12cm, perimeter 32cm: area)", "mathematics/mensuration/area", "Isosceles triangle height and area; assign to Area subtopic."),
    97: ("Numerical Ability / Probability (Probability of face card from 52 cards)", "reasoning-and-aptitude/numerical-ability", "Standard playing card probability; assign to Numerical Ability topic."),
    98: ("Simple Interest (Rate for sum to double in 8 years: R = 100/T)", "mathematics/arithmetic", "Doubling time simple interest formula; assign to Arithmetic topic."),
    99: ("Number Systems / Remainder Theorem (Divisor remainder property: 221 leaves 18)", "mathematics/arithmetic", "Euclidean division remainder deduction; assign to Arithmetic topic."),
    100: ("Fractions (1/8th of train passengers children = 40 children -> total)", "mathematics/arithmetic", "Unitary fractional total extraction; assign to Arithmetic topic.")
}

assert len(P) == 100

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
        "batch_id": 37,
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

# Zero unextracted conventional items (100% MCQ paper)
unextracted_items = []
(batch_dir / "pending-written-intake.json").write_text(json.dumps(unextracted_items, indent=2) + "\n")

summary = {
    "batch": 37,
    "paper_id": "Old_Questions/Direct_2014-2018/3.Mathematics.pdf",
    "paper_title": "General Competitive Examinations for Recruitment to the Post of Sub Inspector (UB) under Home Department, Government of Mizoram (October, 2018) — Mathematics",
    "document_id": "doc_941aa0c516507942933a0ab1",
    "sha256": "7b2e6c54c18657b2b22b82ecfc19659343a921b3aae30c0bda7ec3ee22b5af87",
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
