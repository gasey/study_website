"""Build review packet and findings for Batch 44: ADA, AA & ATA Arithmetic (70 MCQs)."""
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

# Proposals mapped by (paper_id, qnum)
proposals = {
    # --- PAPER 1: Assistant Divisional Accountant 2015 - 3. Arithmetic.pdf (20 MCQs) ---
    ("Old_Questions/Direct_2014-2018/3. Arithmetic.pdf", 1): (1, "Place & Face Value", "mathematics/arithmetic", "retag", "Calculates sum of place value (800) and face value (8) of digit 8 in 46891."),
    ("Old_Questions/Direct_2014-2018/3. Arithmetic.pdf", 2): (1, "Fractions & Proportions", "mathematics/arithmetic", "retag", "Computes total school strength from fraction of boys (5/8) and given number of girls (240)."),
    ("Old_Questions/Direct_2014-2018/3. Arithmetic.pdf", 3): (1, "Highest Common Factor (HCF)", "mathematics/arithmetic", "retag", "Finds common prime factors among four prime factor products to compute HCF."),
    ("Old_Questions/Direct_2014-2018/3. Arithmetic.pdf", 4): (1, "Fractions & Decimals", "mathematics/arithmetic", "retag", "Converts terminating decimal 0.36 into simplified vulgar fraction (9/25)."),
    ("Old_Questions/Direct_2014-2018/3. Arithmetic.pdf", 5): (1, "Simplification & Order of Operations", "mathematics/arithmetic", "retag", "Evaluates consecutive division 783 ÷ 9 ÷ 0.75 = 116."),
    ("Old_Questions/Direct_2014-2018/3. Arithmetic.pdf", 6): (1, "Radicals & Surds", "mathematics/arithmetic", "retag", "Evaluates decimal square root approximation for √154."),
    ("Old_Questions/Direct_2014-2018/3. Arithmetic.pdf", 7): (2, "Averages (Odd Numbers)", "mathematics/arithmetic/averages", "keep", "Confirms exact active subtopic for average of first 5 odd numbers (1,3,5,7,9 = 5)."),
    ("Old_Questions/Direct_2014-2018/3. Arithmetic.pdf", 8): (2, "Mean Proportional", "mathematics/arithmetic/ratio-and-proportion", "keep", "Confirms exact active subtopic for geometric mean proportional √(8 * 50) = 20."),
    ("Old_Questions/Direct_2014-2018/3. Arithmetic.pdf", 9): (2, "Square Roots in Practical Application", "mathematics/arithmetic", "retag", "Calculates square root of seating capacity where number of rows equals number of chairs per row."),
    ("Old_Questions/Direct_2014-2018/3. Arithmetic.pdf", 10): (2, "Fractions (Multiplicative Inverse)", "mathematics/arithmetic", "retag", "Identifies reciprocal / multiplicative inverse of rational number 3/2 -> 2/3."),
    ("Old_Questions/Direct_2014-2018/3. Arithmetic.pdf", 11): (2, "Fractions Division", "mathematics/arithmetic", "retag", "Solves linear equation (33/8) / x = 11/2 -> x = 3/4."),
    ("Old_Questions/Direct_2014-2018/3. Arithmetic.pdf", 12): (2, "Unitary Method", "mathematics/arithmetic", "retag", "Applies unitary method to calculate price of 36 books from cost of 15 books."),
    ("Old_Questions/Direct_2014-2018/3. Arithmetic.pdf", 13): (3, "Probability (Die Roll)", "reasoning-and-aptitude/numerical-ability", "retag", "Rectifies inactive 'statistics' baseline: calculates probability of even number on a single die roll (3/6 = 1/2)."),
    ("Old_Questions/Direct_2014-2018/3. Arithmetic.pdf", 14): (3, "Speed Unit Conversion", "mathematics/arithmetic", "retag", "Converts speed 40 m/s to km/h (40 * 18/5 = 144 km/h)."),
    ("Old_Questions/Direct_2014-2018/3. Arithmetic.pdf", 15): (3, "Time & Work", "mathematics/arithmetic", "retag", "Calculates combined work rate of A (15 days) and B (20 days)."),
    ("Old_Questions/Direct_2014-2018/3. Arithmetic.pdf", 16): (3, "Mensuration (Rectangle Area & Perimeter)", "mathematics/mensuration/area", "keep", "Confirms exact active subtopic for finding width and perimeter of rectangular plot from area 462 and length 28."),
    ("Old_Questions/Direct_2014-2018/3. Arithmetic.pdf", 17): (3, "Speed, Distance & Time", "mathematics/arithmetic", "retag", "Computes speed of sound from distance 1.34 km and time lag."),
    ("Old_Questions/Direct_2014-2018/3. Arithmetic.pdf", 18): (4, "Percentages (Unit Comparison)", "mathematics/arithmetic/percentages", "keep", "Confirms exact active subtopic for percentage calculation of 875g relative to 10,000g."),
    ("Old_Questions/Direct_2014-2018/3. Arithmetic.pdf", 19): (4, "Square Root Digit Identification", "mathematics/arithmetic", "retag", "Finds ten's place digit in square root of 15876 (√15876 = 126 -> ten's place is 2)."),
    ("Old_Questions/Direct_2014-2018/3. Arithmetic.pdf", 20): (4, "Mensuration (Cubic Volume)", "mathematics/mensuration/volume", "keep", "Confirms exact active subtopic for number of 2cm cubes cut from 6cm cube (6³/2³ = 27)."),

    # --- PAPER 2: ADA, AA & ATA Arithmetic 2019-2020 (50 MCQs) ---
    ("Old_Questions/Direct_2019-2020/ADA, AA & ATA Arithmatic.pdf", 1): (1, "Decimal Representation", "mathematics/arithmetic", "retag", "Identifies fractional decimal notation of 15 thousandths (0.015)."),
    ("Old_Questions/Direct_2019-2020/ADA, AA & ATA Arithmatic.pdf", 2): (1, "Decimal Ordering", "mathematics/arithmetic", "retag", "Arranges decimal numbers in descending magnitude order."),
    ("Old_Questions/Direct_2019-2020/ADA, AA & ATA Arithmatic.pdf", 3): (1, "BODMAS with Mixed Fractions", "mathematics/arithmetic", "retag", "Evaluates complex arithmetic expression with mixed fractions and order of operations."),
    ("Old_Questions/Direct_2019-2020/ADA, AA & ATA Arithmatic.pdf", 4): (1, "HCF & LCM Product Property", "mathematics/arithmetic", "retag", "Applies property: Product of two numbers = HCF * LCM."),
    ("Old_Questions/Direct_2019-2020/ADA, AA & ATA Arithmatic.pdf", 5): (2, "Linear Equation in One Variable", "mathematics/arithmetic", "retag", "Solves linear decimal/fraction equation for variable x."),
    ("Old_Questions/Direct_2019-2020/ADA, AA & ATA Arithmatic.pdf", 6): (2, "Percentage Comparison", "mathematics/arithmetic/percentages", "retag", "Calculates reciprocal percentage excess when A is 20% below B (20/80 = 25%)."),
    ("Old_Questions/Direct_2019-2020/ADA, AA & ATA Arithmatic.pdf", 7): (3, "Examination Percentages", "mathematics/arithmetic/percentages", "retag", "Computes total candidates given 80% pass and number of failing candidates."),
    ("Old_Questions/Direct_2019-2020/ADA, AA & ATA Arithmatic.pdf", 8): (3, "Profit & Loss (SP Equivalent)", "mathematics/arithmetic/profit-and-loss", "retag", "Calculates percentage gain when gain equals selling price of 11 articles out of 44 sold."),
    ("Old_Questions/Direct_2019-2020/ADA, AA & ATA Arithmatic.pdf", 9): (2, "Weighted Averages", "mathematics/arithmetic/averages", "retag", "Computes combined average marks of two classes with 40 and 50 students."),
    ("Old_Questions/Direct_2019-2020/ADA, AA & ATA Arithmatic.pdf", 10): (1, "Simple Interest & Calendar Days", "mathematics/arithmetic", "retag", "Calculates simple interest over exact calendar days between June and August."),
    ("Old_Questions/Direct_2019-2020/ADA, AA & ATA Arithmatic.pdf", 11): (1, "Two-Set Venn Percentage Overlap", "mathematics/arithmetic/percentages", "retag", "Calculates pass percentage in both subjects given individual failure counts and set union."),
    ("Old_Questions/Direct_2019-2020/ADA, AA & ATA Arithmatic.pdf", 12): (2, "Successive Percentage Expenditure", "mathematics/arithmetic/percentages", "retag", "Computes original bonus amount from sequential fractional/percentage expenditures."),
    ("Old_Questions/Direct_2019-2020/ADA, AA & ATA Arithmatic.pdf", 13): (2, "Time & Work (Pair Work)", "mathematics/arithmetic", "retag", "Calculates individual completion times from pairwise work rates (A+B, B+C, C+A)."),
    ("Old_Questions/Direct_2019-2020/ADA, AA & ATA Arithmatic.pdf", 14): (4, "Ratio & Proportion", "mathematics/arithmetic/ratio-and-proportion", "retag", "Finds original numbers in ratio 3:5 when 18 is added to first term."),
    ("Old_Questions/Direct_2019-2020/ADA, AA & ATA Arithmatic.pdf", 15): (4, "Mixtures & Alligations", "mathematics/arithmetic/ratio-and-proportion", "retag", "Calculates quantity of water added to alter ratio in milk-water mixture."),
    ("Old_Questions/Direct_2019-2020/ADA, AA & ATA Arithmatic.pdf", 16): (4, "Linear Equations (Age Problem)", "mathematics/algebra/linear-equations", "retag", "Solves linear system for father and son ages based on past and present relations."),
    ("Old_Questions/Direct_2019-2020/ADA, AA & ATA Arithmatic.pdf", 17): (4, "Speed, Distance & Train Crossing", "mathematics/arithmetic", "retag", "Calculates time for train of given length and speed to cross a 0.5 km bridge."),
    ("Old_Questions/Direct_2019-2020/ADA, AA & ATA Arithmatic.pdf", 18): (2, "Compound Depreciation", "mathematics/arithmetic/percentages", "keep", "Confirms exact active subtopic for auction vehicle depreciation over annual rate."),
    ("Old_Questions/Direct_2019-2020/ADA, AA & ATA Arithmatic.pdf", 19): (4, "Compound Ratios", "mathematics/arithmetic/ratio-and-proportion", "retag", "Compounds ratios a:b = 3:5 and b:c = 7:8 to evaluate 2a:3b:7c."),
    ("Old_Questions/Direct_2019-2020/ADA, AA & ATA Arithmatic.pdf", 20): (2, "Fractions of Time & Travel", "mathematics/arithmetic", "retag", "Compares flight durations in mixed hours to compute travel difference."),
    ("Old_Questions/Direct_2019-2020/ADA, AA & ATA Arithmatic.pdf", 21): (4, "Profit & Loss (Loss to Gain)", "mathematics/arithmetic/profit-and-loss", "retag", "Finds target selling price for desired profit percentage starting from 10% loss selling price."),
    ("Old_Questions/Direct_2019-2020/ADA, AA & ATA Arithmatic.pdf", 22): (2, "Compound Interest Rate", "mathematics/arithmetic", "retag", "Finds compound interest rate per annum where 64 amounts to 125 in 3 years (cube root 5/4 -> 25%)."),
    ("Old_Questions/Direct_2019-2020/ADA, AA & ATA Arithmatic.pdf", 23): (2, "Prime Factorization & Perfect Cubes", "mathematics/arithmetic", "retag", "Finds smallest divisor to make 72000 a perfect cube via prime factor grouping."),
    ("Old_Questions/Direct_2019-2020/ADA, AA & ATA Arithmatic.pdf", 24): (5, "Mensuration (Cube Surface Area)", "mathematics/mensuration/volume", "retag", "Computes edge length from volume 2197 cm³ (a = 13) and evaluates total surface area 6a²."),
    ("Old_Questions/Direct_2019-2020/ADA, AA & ATA Arithmatic.pdf", 25): (2, "Relative Speed & Motion", "mathematics/arithmetic", "retag", "Solves relative speed meeting problem for two travellers moving towards each other."),
    ("Old_Questions/Direct_2019-2020/ADA, AA & ATA Arithmatic.pdf", 26): (5, "Scientific Notation", "mathematics/arithmetic", "retag", "Converts scientific notation 3.123 * 10^5 to standard decimal form (312300)."),
    ("Old_Questions/Direct_2019-2020/ADA, AA & ATA Arithmatic.pdf", 27): (5, "Successive Trade Discounts", "mathematics/arithmetic/profit-and-loss", "retag", "Evaluates net price after successive discounts of 10%, 20%, and cash discount."),
    ("Old_Questions/Direct_2019-2020/ADA, AA & ATA Arithmatic.pdf", 28): (5, "Mensuration (Wheel Revolutions)", "mathematics/mensuration/area", "retag", "Calculates total distance from wheel diameter 1.26m and 500 revolutions (distance = 500 * πd)."),
    ("Old_Questions/Direct_2019-2020/ADA, AA & ATA Arithmatic.pdf", 29): (5, "Simultaneous Linear Equations", "mathematics/algebra/linear-equations", "retag", "Solves simultaneous money exchange puzzle for initial amounts of Fela and Rama."),
    ("Old_Questions/Direct_2019-2020/ADA, AA & ATA Arithmatic.pdf", 30): (2, "Partnership Capital & Profit", "mathematics/arithmetic/ratio-and-proportion", "retag", "Rectifies misclassified 'commerce' baseline: divides partnership profit in ratio of capital investments."),
    ("Old_Questions/Direct_2019-2020/ADA, AA & ATA Arithmatic.pdf", 31): (5, "Mensuration (Melting Sphere to Cylinder)", "mathematics/mensuration/volume", "retag", "Equates volume of 48cm diameter sphere to cylinder volume to find wire/cylinder length."),
    ("Old_Questions/Direct_2019-2020/ADA, AA & ATA Arithmatic.pdf", 32): (2, "Probability (Colored Balls)", "reasoning-and-aptitude/numerical-ability", "retag", "Computes classical probability of drawing specified colored balls from urn."),
    ("Old_Questions/Direct_2019-2020/ADA, AA & ATA Arithmatic.pdf", 33): (5, "Perfect Squares (Least Subtraction)", "mathematics/arithmetic", "retag", "Uses long division square root algorithm to find remainder subtracted to obtain perfect square."),
    ("Old_Questions/Direct_2019-2020/ADA, AA & ATA Arithmatic.pdf", 34): (6, "Surds Simplification", "mathematics/arithmetic", "retag", "Simplifies radical expression (√98 + √72 - √50) / √18 = (7√2 + 6√2 - 5√2) / 3√2 = 8/3."),
    ("Old_Questions/Direct_2019-2020/ADA, AA & ATA Arithmatic.pdf", 35): (2, "Mensuration (Hemisphere to Sphere)", "mathematics/mensuration/volume", "retag", "Equates hemisphere volume (2/3 πr³) to recast sphere volume (4/3 πR³) to find new radius."),
    ("Old_Questions/Direct_2019-2020/ADA, AA & ATA Arithmatic.pdf", 36): (6, "Mensuration (Field Survey Area)", "mathematics/mensuration/area", "retag", "Calculates polygon field area by summing trapezoids and right triangles along survey baseline."),
    ("Old_Questions/Direct_2019-2020/ADA, AA & ATA Arithmatic.pdf", 37): (6, "Mensuration (Surrounding Path Area)", "mathematics/mensuration/area", "retag", "Calculates path area around 40m x 30m field with uniform 2m border."),
    ("Old_Questions/Direct_2019-2020/ADA, AA & ATA Arithmatic.pdf", 38): (6, "Pipes & Cisterns (Tap & Leak)", "mathematics/arithmetic", "retag", "Computes net filling time combining inlet tap and outlet leak."),
    ("Old_Questions/Direct_2019-2020/ADA, AA & ATA Arithmatic.pdf", 39): (6, "Statistics (Empirical Mode Formula)", "reasoning-and-aptitude/numerical-ability", "retag", "Rectifies inactive 'statistics' baseline: applies empirical relation Mode = 3 Median - 2 Mean."),
    ("Old_Questions/Direct_2019-2020/ADA, AA & ATA Arithmatic.pdf", 40): (2, "Statistics (Mode of Discrete Series)", "reasoning-and-aptitude/numerical-ability", "retag", "Rectifies inactive 'statistics' baseline: finds most frequently occurring observation in discrete data set."),
    ("Old_Questions/Direct_2019-2020/ADA, AA & ATA Arithmatic.pdf", 41): (7, "Unitary Fuel Consumption", "mathematics/arithmetic", "retag", "Calculates fuel needed for specified travel distance from known rate 5L for 70km."),
    ("Old_Questions/Direct_2019-2020/ADA, AA & ATA Arithmatic.pdf", 42): (7, "Data Interpretation (Bar Chart Sum)", "reasoning-and-aptitude/data-interpretation", "retag", "Reads bar graph to compute total food grains production across years 2000 and 2001."),
    ("Old_Questions/Direct_2019-2020/ADA, AA & ATA Arithmatic.pdf", 43): (7, "Data Interpretation (Bar Chart Difference)", "reasoning-and-aptitude/data-interpretation", "retag", "Calculates difference in production between highest and lowest years from bar chart."),
    ("Old_Questions/Direct_2019-2020/ADA, AA & ATA Arithmatic.pdf", 44): (7, "Data Interpretation (Percentage Growth)", "reasoning-and-aptitude/data-interpretation", "retag", "Computes percentage growth in production from 2003 to 2004 from bar chart data."),
    ("Old_Questions/Direct_2019-2020/ADA, AA & ATA Arithmatic.pdf", 45): (2, "Data Interpretation (Production Ratio)", "reasoning-and-aptitude/data-interpretation", "retag", "Calculates ratio of production figures in 2002 versus 2003 from bar chart data."),
    ("Old_Questions/Direct_2019-2020/ADA, AA & ATA Arithmatic.pdf", 46): (7, "Data Interpretation (Multi-Year Average)", "reasoning-and-aptitude/data-interpretation", "retag", "Computes 6-year average yearly production across period 2000-2005 from bar graph data."),
    ("Old_Questions/Direct_2019-2020/ADA, AA & ATA Arithmatic.pdf", 47): (8, "Data Interpretation (Pie Chart Sum)", "reasoning-and-aptitude/data-interpretation", "retag", "Computes combined family expenditure on Food and Clothing from pie chart sector angles/percentages."),
    ("Old_Questions/Direct_2019-2020/ADA, AA & ATA Arithmatic.pdf", 48): (8, "Data Interpretation (Pie Chart Excess)", "reasoning-and-aptitude/data-interpretation", "retag", "Computes difference between Education and Clothing expenditures from pie chart data."),
    ("Old_Questions/Direct_2019-2020/ADA, AA & ATA Arithmatic.pdf", 49): (8, "Data Interpretation (Pie Chart Amount)", "reasoning-and-aptitude/data-interpretation", "retag", "Rectifies misclassified 'financial-rules-and-accounts' baseline: computes miscellaneous expenditure from pie chart."),
    ("Old_Questions/Direct_2019-2020/ADA, AA & ATA Arithmatic.pdf", 50): (2, "Data Interpretation (Pie Chart Savings)", "reasoning-and-aptitude/data-interpretation", "retag", "Evaluates net monthly family savings sector from pie chart income distribution.")
}

candidates = []
findings = []

breakdown = {}
action_counts = {"retag": 0, "keep": 0}

for it in packet["items"]:
    pid = it["appearance"]["paper_id"]
    qn = int(it["appearance"]["qnum"])
    page, skill, path_str, action, rationale = proposals[(pid, qn)]
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
        "batch_id": 44,
        "policy": "study-tagging-v1"
    }
    candidates.append(cand)
    
    finding = {
        "index": len(candidates),
        "canonical_id": it["canonical_id"],
        "appearance_id": it["appearance_id"],
        "printed_question": f"Q{qn}",
        "physical_page": page,
        "tested_skill": skill,
        "current_path": cur_path,
        "proposed_path": prop_path,
        "action": action,
        "rationale": rationale
    }
    findings.append(finding)

assert len(candidates) == 70
assert len(findings) == 70

(batch_dir / "pending-candidates.json").write_text(json.dumps(candidates, indent=2) + "\n")
(batch_dir / "findings.json").write_text(json.dumps(findings, indent=2) + "\n")

summary = {
    "batch": 44,
    "papers": [
        {
            "paper_id": "Old_Questions/Direct_2014-2018/3. Arithmetic.pdf",
            "paper_title": "General Competitive Examinations for Recruitment to the Post of Assistant Divisional Accountant under Finance Department (2015) — 3. Arithmetic",
            "document_id": "doc_b3e48463a72b3b18b82957d0",
            "sha256": "225158f85ab7992b85d5b2e4513a95839d847c9a7b2d68d0e9ad1a648903aae7",
            "targets": 20
        },
        {
            "paper_id": "Old_Questions/Direct_2019-2020/ADA, AA & ATA Arithmatic.pdf",
            "paper_title": "Competitive Examinations for Recruitment to the Posts of Assistant Auditor, Assistant Treasury Accountant & Assistant Divisional Accountant (2019) — Arithmetic",
            "document_id": "doc_5335e1afbbcfc26d1afa5cd2",
            "sha256": "cc5fbb2e46228b2451671d75413f55f4b399170ba01e6077bacb76ed51eb2c2f",
            "targets": 50
        }
    ],
    "targets": 70,
    "completion": "100% of extracted MCQs reviewed across both Finance Department Arithmetic booklets",
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
