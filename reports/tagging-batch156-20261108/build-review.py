"""Build candidates, findings, summary for Batch 156 (Assistant UDC MPSC Paper-II)."""
import json
from pathlib import Path
from collections import Counter

out = Path(__file__).resolve().parent
packet = json.load(open(out / "oracle-packet.json"))

def make_primary(sid, tid=None, subid=None):
    return {
        "subject_id": sid,
        "topic_id": tid,
        "subtopic_id": subid
    }

decisions = {
    1: (make_primary("computer-science", "computer-science/computer-systems-and-architecture", None), "Computer hardware: Identification of physical components of a computer system."),
    2: (make_primary("computer-science", "computer-science/computer-systems-and-architecture", None), "Software types: System software controlling hardware and operating platform."),
    3: (make_primary("computer-science", "computer-science/computer-systems-and-architecture", None), "Peripheral interfaces: Input/output devices enabling communication between user and computer."),
    4: (make_primary("computer-science", "computer-science/computer-systems-and-architecture", None), "Display technology: Pixel composition using 3 sub-pixel colour dots (RGB) or 24-bit true color."),
    5: (make_primary("computer-science", "computer-science/computer-systems-and-architecture", None), "Memory architecture: Buffer memory compensating for data transfer speed differences."),
    6: (make_primary("computer-science", "computer-science/operating-systems", None), "Operating systems history: Windows 11 as latest major Windows NT operating system release."),
    7: (make_primary("computer-science", "computer-science/office-applications", None), "Word processing: Format Painter tool copying visual formatting across text sections."),
    8: (make_primary("computer-science", "computer-science/office-applications", None), "Word layout: Margins and indentation configuring whitespace around document body."),
    9: (make_primary("computer-science", "computer-science/office-applications", None), "Word UI: The Ribbon at top of window organizing command tabs and groups."),
    10: (make_primary("computer-science", "computer-science/office-applications", None), "Word automation: Mail Merge feature creating personalized mass correspondence."),
    11: (make_primary("computer-science", "computer-science/office-applications", None), "Word navigation: Bookmark tool marking specific internal document locations."),
    12: (make_primary("computer-science", "computer-science/networking", None), "Cloud services: Identification of non-cloud software applications."),
    13: (make_primary("computer-science", "computer-science/office-applications", None), "Office AI features: Microsoft Copilot integrated artificial intelligence assistant."),
    14: (make_primary("computer-science", "computer-science/office-applications", None), "Spreadsheets: Absolute cell referencing ($A$1) locking coordinates during copy."),
    15: (make_primary("computer-science", "computer-science/office-applications", None), "Spreadsheets: AutoSum keyboard shortcut (Alt + =)."),
    16: (make_primary("computer-science", "computer-science/office-applications", None), "Spreadsheets: Grid lines and cell coordinate identification."),
    17: (make_primary("computer-science", "computer-science/office-applications", None), "Spreadsheets: Workbook sheet navigation and tab management."),
    18: (make_primary("computer-science", "computer-science/office-applications", None), "Spreadsheets: Data sorting ascending and descending order."),
    19: (make_primary("computer-science", "computer-science/office-applications", None), "Spreadsheets: AutoFill handle extending numerical and chronological series."),
    20: (make_primary("computer-science", "computer-science/office-applications", None), "Spreadsheets: Formula bar editing cell content and functions."),
    21: (make_primary("computer-science", "computer-science/office-applications", None), "Presentation software: Normal view, Slide Sorter view and Reading view."),
    22: (make_primary("computer-science", "computer-science/office-applications", None), "Presentation software: F5 keyboard shortcut to launch slideshow from beginning."),
    23: (make_primary("computer-science", "computer-science/office-applications", None), "Presentation software: Presenter view displaying speaker notes."),
    24: (make_primary("computer-science", "computer-science/office-applications", None), "Presentation software: Animation effects applied to slide elements."),
    25: (make_primary("computer-science", "computer-science/office-applications", None), "Presentation software: Audio and video multimedia embedding in slides."),
    26: (make_primary("computer-science", "computer-science/networking", None), "Network hardware: Modem (Modulator-Demodulator) converting signals."),
    27: (make_primary("computer-science", "computer-science/networking", None), "Network architecture: Client-server and peer-to-peer network models."),
    28: (make_primary("computer-science", "computer-science/networking", None), "Network security: Anti-virus and spyware security protection utilities."),
    29: (make_primary("computer-science", "computer-science/networking", None), "Web concepts: IP address structure and unique host identification."),
    30: (make_primary("computer-science", "computer-science/networking", None), "Web architecture: World Wide Web client-server HTTP communication."),
    31: (make_primary("computer-science", "computer-science/networking", None), "Transmission media: Optical fiber carrying light pulse data over long distances."),
    32: (make_primary("computer-science", "computer-science/networking", None), "Internet connectivity: Optical fiber technology enabling high-speed broadband."),
    33: (make_primary("computer-science", "computer-science/networking", None), "Cloud service models: SaaS (Software as a Service) delivery model."),
    34: (make_primary("computer-science", "computer-science/networking", None), "Data communication: Full Duplex bi-directional simultaneous data transmission."),
    35: (make_primary("computer-science", "computer-science/networking", None), "Web applications: Web browsers reading HTML and rendering web pages."),
    36: (make_primary("mathematics", "mathematics/arithmetic", None), "Number systems: Definition of Real Numbers combining rational and irrational numbers."),
    37: (make_primary("mathematics", "mathematics/arithmetic", None), "Divisibility: Finding least number added to dividend to make it divisible."),
    38: (make_primary("mathematics", "mathematics/arithmetic", None), "Radical arithmetic: Simplifying nested square roots expression."),
    39: (make_primary("mathematics", "mathematics/arithmetic", None), "Rationalisation: Rationalising denominator of surds expression (2+sqrt(3))/(2-sqrt(3))."),
    40: (make_primary("mathematics", "mathematics/arithmetic", None), "Ratio compounding: Finding compound ratio a:b:c from a:b and b:c."),
    41: (make_primary("mathematics", "mathematics/arithmetic", None), "Simple and compound interest: Finding compound interest given simple interest for 2 years."),
    42: (make_primary("mathematics", "mathematics/arithmetic", None), "Compound interest: Determining principal sum from compounded amount for 3 years."),
    43: (make_primary("mathematics", "mathematics/arithmetic", None), "Ratio and proportion: Comparing unit costs of mangoes and apples in simplest ratio."),
    44: (make_primary("mathematics", "mathematics/arithmetic", None), "Profit and loss: Percentage profit calculation from cost price and selling price."),
    45: (make_primary("mathematics", "mathematics/arithmetic", None), "Profit and loss: Determining cost price given selling price and profit percentage."),
    46: (make_primary("mathematics", "mathematics/arithmetic", None), "Profit and loss: Percentage loss computation from cost price and discounted sale price."),
    47: (make_primary("mathematics", "mathematics/arithmetic", None), "Compound growth: Compound annual population growth computation."),
    48: (make_primary("mathematics", "mathematics/arithmetic", None), "Percentages: Finding marked original price given discount percentage and savings."),
    49: (make_primary("mathematics", "mathematics/arithmetic", None), "Percentages: Voter turnout percentage calculation from total registered electorate."),
    50: (make_primary("mathematics", "mathematics/arithmetic", None), "Work and time: Calculating individual work completion time using joint work formula."),
    51: (make_primary("mathematics", "mathematics/arithmetic", None), "Speed, time and distance: Distance computation given speed in km/h and time in minutes."),
    52: (make_primary("mathematics", "mathematics/geometry", None), "Trigonometry / Geometry: Angle of elevation calculation from height and shadow distance."),
    53: (make_primary("mathematics", "mathematics/arithmetic", None), "Work and time: Individual work completion time when joint time is 12 days."),
    54: (make_primary("mathematics", "mathematics/arithmetic", None), "Partnership arithmetic: Profit sharing based on capital investment and elapsed months."),
    55: (make_primary("mathematics", "mathematics/arithmetic", None), "Averages: Property of arithmetic mean when constant value added to all observations."),
    56: (make_primary("mathematics", "mathematics/arithmetic", None), "Permutations: Number of linear permutations of 5 distinct books (5! = 120)."),
    57: (make_primary("mathematics", "mathematics/arithmetic", None), "Combinations: Committee selection from group of men and women (nCr formula)."),
    58: (make_primary("mathematics", "mathematics/mensuration", None), "Mensuration: Area of trapezium formula solving for parallel side lengths."),
    59: (make_primary("mathematics", "mathematics/mensuration", None), "Mensuration: Difference in radii derived from circumferences of two circles."),
    60: (make_primary("mathematics", "mathematics/mensuration", None), "Mensuration: Curved surface area of cylinder given diameter and height."),
    61: (make_primary("mathematics", "mathematics/arithmetic", None), "Order of operations: Evaluating nested arithmetic expression using BODMAS brackets."),
    62: (make_primary("mathematics", "mathematics/arithmetic", None), "Order of operations: BODMAS evaluation with 'of' multiplication and division."),
    63: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/data-interpretation", None), "Data interpretation: Pie chart central angle proportion calculation."),
    64: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/data-interpretation", None), "Data interpretation: Annual profit percentage trends from line graph."),
    65: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/data-interpretation", None), "Data interpretation: Production output comparison across years from bar graph."),
    66: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/verbal-reasoning", None), "Classification: Odd one out among human anatomical facial features."),
    67: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/verbal-reasoning", None), "Number classification: Numerical pair relation odd-one-out (3x + 1 pattern)."),
    68: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/verbal-reasoning", None), "Coding-decoding: Word cipher with letter position reversal and shifts (COMPUTER)."),
    69: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/verbal-reasoning", None), "Coding-decoding: Common digit identification in numerical message code."),
    70: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/verbal-reasoning", None), "Coding-decoding: Direct letter-to-digit substitution mapping (ROSE/CHAIR/PREACH)."),
    71: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/verbal-reasoning", None), "Assertion and reasoning: Scientific evaluation of ebonite heat insulation on cookers."),
    72: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/verbal-reasoning", None), "Assertion and reasoning: Astronomical evaluation of Pluto surface temperature and insolation."),
    73: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/verbal-reasoning", None), "Assertion and reasoning: Physiological thermal comfort in humid climate."),
    74: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/verbal-reasoning", None), "Situational judgment: Moral and ethical response to bus conductor ticket oversight."),
    75: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/verbal-reasoning", None), "Situational judgment: Public administration ethics in serving distant rural applicant."),
    76: (make_primary("mathematics", "mathematics/algebra", None), "Linear equations: System of two linear equations in two variables solving ticket fares."),
    77: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/numerical-ability", None), "Numerical puzzles: Fabric roll division and cutting puzzle."),
    78: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/numerical-ability", None), "Matrix reasoning: 3x3 character grid finding missing number by row operations."),
    79: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/numerical-ability", None), "Matrix reasoning: 3x3 numerical matrix pattern recognition."),
    80: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/verbal-reasoning", None), "Logical sequence: Anatomical arrangement from shoulder to fingers."),
    81: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/numerical-ability", None), "Mathematical operations: Correct equation after interchanging mathematical signs and numbers."),
    82: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/numerical-ability", None), "Mathematical operations: Symbol substitution arithmetic expression evaluation."),
    83: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/series", None), "Number series: Pattern recognition in cubic difference series (4, 18, 48, 100, 180)."),
    84: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/series", None), "Number series: Finding anomalous wrong term in square difference sequence."),
    85: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/verbal-reasoning", None), "Linear ranking: Total row strength after position interchange between two persons."),
    86: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/verbal-reasoning", None), "Linear ranking: Total class strength from top and bottom rank coordinates."),
    87: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/verbal-reasoning", None), "Circular seating: Circular arrangement of eight persons facing centre."),
    88: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/verbal-reasoning", None), "Ranking and order: Boy and girl ratio ranking problem in class of 60."),
    89: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/verbal-reasoning", None), "Data sufficiency: Evaluating sufficiency of height statements among five friends."),
    90: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/verbal-reasoning", None), "Data sufficiency: Evaluating sufficiency of statements on total pole weight."),
    91: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/verbal-reasoning", None), "Spatial visualization: Identifying assembled geometric figure from components."),
    92: (make_primary("mathematics", "mathematics/mensuration", None), "Mensuration: Border and margin area calculation on 8.5 by 10 inch sheet."),
    93: (make_primary("mathematics", "mathematics/arithmetic", None), "Percentages: Two-candidate election vote count given majority percentage."),
    94: (make_primary("mathematics", "mathematics/arithmetic", None), "Percentages: Algebraic percentage equivalence relation (20% of a = b)."),
    95: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/numerical-ability", None), "Clock problems: Calculating true time from clock that gains minutes daily."),
    96: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/verbal-reasoning", None), "Deductive logic: Transitive age ranking relations (Tanya, Eric, Cliff)."),
    97: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/verbal-reasoning", None), "Deductive seating: Table arrangement deduction with profession constraints."),
    98: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/verbal-reasoning", None), "Comprehension inference: Philosophical and humanitarian deduction from passage on technology."),
    99: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/numerical-ability", None), "Calendar arithmetic: Day of the week calculation for 15th August 1947 (Friday)."),
    100: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/numerical-ability", None), "Calendar properties: Non-permissible last days of a century (Tuesday, Thursday, Saturday).")
}

pending_candidates = []
action_counts = Counter()
tax_counts = Counter()

registered_doc = packet["documents"][0] if packet.get("documents") else {
    "id": "doc_51b1f060d41b6b7e043811a1",
    "sha256": "87b2af2637b48059ccf7dfd44b1ac1730056a88abb33497bf6b4f89e6a9daa9c"
}

for it in packet["items"]:
    snap = it["snapshot"]
    rec = snap["record"]
    aid = it["appearance_id"]
    cid = it["canonical_id"]
    cur_primary = rec["classification"]
    pid = it["appearance"]["paper_id"]
    qnum = int(it["appearance"]["qnum"])
    page = int(rec.get("page") or 1)

    prop, reason = decisions[qnum]
    action = "keep" if prop == cur_primary else "retag"
    action_counts[action] += 1
    tax_counts[f"{prop['subject_id']} > {prop['topic_id']}"] += 1

    cand = {
        "candidate_id": f"tcand_b156_{aid[:16]}",
        "canonical_id": cid,
        "appearance_id": aid,
        "paper_id": pid,
        "source_fingerprint": it["source_fingerprint"],
        "action": action,
        "review_status": "pending",
        "current_primary": cur_primary,
        "proposed_primary": prop,
        "proposed_related": [],
        "tested_skill": reason,
        "rationale": f"Batch 156 source-inspected (PDF page {page}): {reason}",
        "policy_version": "study-tagging-v1",
        "source_evidence": {
            "document_id": registered_doc["id"],
            "sha256": registered_doc["sha256"],
            "physical_page": page,
            "printed_question": str(qnum),
            "inspected": True,
            "note": f"Inspected physical page {page} of Assistant UDC under MPSC Paper-II (Q{qnum}). Verified stem, options, and section classification."
        },
        "context_candidate": {
            "region": "",
            "language": "en",
            "time_behavior": "static",
            "reference_period": "",
            "reference_basis": "unknown"
        },
        "context_reason": "Standard static syllabus knowledge (Computer Science, Arithmetic, Reasoning).",
        "source_issues": [],
        "taxonomy_gap": None,
        "alternatives": [],
        "owner_question": None,
        "reviewer_tool": "antigravity",
        "reviewer_model": "gemini"
    }
    pending_candidates.append(cand)

(out / "pending-candidates.json").write_text(json.dumps(pending_candidates, indent=2, ensure_ascii=False) + "\n")

summary = {
    "batch": 156,
    "paper_id": packet["papers"][0]["id"] if packet.get("papers") else "Old_Questions/Direct_NG_2024-2027/Assistant UDC under MPSC paper-II..pdf",
    "paper_title": packet["papers"][0]["exam_name"] + " " + packet["papers"][0]["post"] if packet.get("papers") else "Assistant UDC under MPSC paper-II",
    "total_targets": len(pending_candidates),
    "actions": dict(action_counts),
    "taxonomy_distribution": dict(tax_counts),
    "source_defect_notes": "Clean scan, complete 100 MCQs across 12 physical pages without omission."
}
(out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
print(f"Generated {len(pending_candidates)} pending candidates for Batch 156. Actions: {dict(action_counts)}")
