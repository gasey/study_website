"""Build candidates, findings, summary for Batch 152 (LDC Law & Judicial Paper-II)."""
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
    1: (make_primary("computer-science", "computer-science/networking", None), "Internet pioneers: Tim Berners-Lee as inventor of World Wide Web (WWW)."),
    2: (make_primary("computer-science", "computer-science/networking", None), "Internet governance organizations: IAB, IETF voluntary architecture bodies."),
    3: (make_primary("computer-science", "computer-science/networking", None), "Web standards: W3C full form (World Wide Web Consortium)."),
    4: (make_primary("computer-science", "computer-science/networking", None), "Network architecture: Definition and characteristics of private Intranet."),
    5: (make_primary("computer-science", "computer-science/networking", None), "Network architecture: Controlled outside access via Extranet."),
    6: (make_primary("computer-science", "computer-science/networking", None), "Network addressing: Static IP address usage for dedicated servers."),
    7: (make_primary("computer-science", "computer-science/networking", None), "Network addressing: Standard IP address bit length (IPv4 32-bit / IPv6)."),
    8: (make_primary("computer-science", "computer-science/networking", None), "Web security protocols: HTTPS Secure Socket Layer designation."),
    9: (make_primary("computer-science", "computer-science/networking", None), "Network hardware: NIC full form (Network Interface Card)."),
    10: (make_primary("computer-science", "computer-science/networking", None), "Networking history: First dial-up connection by Lawrence G. Roberts in 1965."),
    11: (make_primary("computer-science", "computer-science/networking", None), "Network protocols: FTP (File Transfer Protocol) for file transfer."),
    12: (make_primary("computer-science", "computer-science/networking", None), "Network security: Ineffective or non-security techniques in networking."),
    13: (make_primary("computer-science", "computer-science/operating-systems", None), "Operating system concepts: OS as interface between user and computer hardware."),
    14: (make_primary("computer-science", "computer-science/operating-systems", None), "Operating systems history: MS-DOS full form (Microsoft Disk Operating System)."),
    15: (make_primary("computer-science", "computer-science/operating-systems", None), "GUI development: Xerox Corporation designing the first graphical user interface."),
    16: (make_primary("computer-science", "computer-science/operating-systems", None), "Operating systems classification: RTOS full form (Real-Time Operating System)."),
    17: (make_primary("computer-science", "computer-science/operating-systems", None), "Process management: Multiprocessing and concurrency concepts."),
    18: (make_primary("computer-science", "computer-science/operating-systems", None), "OS architecture: Kernel as the fundamental core of an operating system."),
    19: (make_primary("computer-science", "computer-science/operating-systems", None), "Concurrency issues: Definition and conditions for deadlock in operating systems."),
    20: (make_primary("computer-science", "computer-science/office-applications", None), "Office applications: Mail merge data source components in word processing."),
    21: (make_primary("computer-science", "computer-science/office-applications", None), "Text formatting: Font effects (superscript, subscript, emboss, engrave)."),
    22: (make_primary("computer-science", "computer-science/office-applications", None), "Word processing shortcuts: Increasing left indent shortcut keys."),
    23: (make_primary("computer-science", "computer-science/computer-systems-and-architecture", None), "Computer memory: DRAM periodic refresh requirement."),
    24: (make_primary("computer-science", "computer-science/computer-systems-and-architecture", None), "Storage media: Optical reusable storage (CD-RW / DVD-RW)."),
    25: (make_primary("computer-science", "computer-science/computer-systems-and-architecture", None), "Data processing: Input, processing, output data processing cycle."),
    26: (make_primary("computer-science", "computer-science/computer-systems-and-architecture", None), "Computer hardware: Motherboard terminology and aliases."),
    27: (make_primary("computer-science", "computer-science/computer-systems-and-architecture", None), "Semiconductor technology: Silicon material used in CPU microchips."),
    28: (make_primary("computer-science", "computer-science/computer-systems-and-architecture", None), "Low-level programming: Machine language understood directly by CPU."),
    29: (make_primary("computer-science", "computer-science/office-applications", None), "Presentation software: Shortcut key to duplicate slide in PowerPoint (Ctrl+D)."),
    30: (make_primary("computer-science", "computer-science/office-applications", None), "Spreadsheet basics: Definition of cell as intersection of row and column."),
    31: (make_primary("computer-science", "computer-science/office-applications", None), "Word formatting: Legacy text animation and sparkle effects in MS Word."),
    32: (make_primary("computer-science", "computer-science/computer-systems-and-architecture", None), "Indian computing institutions: C-DAC full form (Centre for Development of Advanced Computing)."),
    33: (make_primary("computer-science", "computer-science/computer-systems-and-architecture", None), "Computing institutions: C-DAC headquarters located in Pune."),
    34: (make_primary("computer-science", "computer-science/computer-systems-and-architecture", None), "Computing history: Establishment year of C-DAC (1988)."),
    35: (make_primary("computer-science", "computer-science/computer-systems-and-architecture", None), "Computer generations: Assembly language in second-generation computers."),
    36: (make_primary("computer-science", "computer-science/computer-systems-and-architecture", None), "Computer generations: Integrated circuits (ICs) introduced in third generation."),
    37: (make_primary("computer-science", "computer-science/computer-systems-and-architecture", None), "Computer generations: Microprocessors as basis of fourth-generation computers."),
    38: (make_primary("computer-science", "computer-science/computer-systems-and-architecture", None), "Early computing history: Stored-program computers (EDSAC / Manchester Baby)."),
    39: (make_primary("computer-science", "computer-science/computer-systems-and-architecture", None), "Computer classification: Hybrid computers used in medical equipment (ECG/Dialysis)."),
    40: (make_primary("computer-science", "computer-science/computer-systems-and-architecture", None), "Malware history: Creeper virus detected on ARPANET in 1971."),
    41: (make_primary("computer-science", "computer-science/computer-systems-and-architecture", None), "Computing terminology: Origin and first usage of term 'computer worm' (John Brunner)."),
    42: (make_primary("computer-science", "computer-science/computer-systems-and-architecture", None), "Computing history: ENIAC as first electronic general-purpose computer."),
    43: (make_primary("computer-science", "computer-science/computer-systems-and-architecture", None), "Hardware classification: Odd one out among computer input/output peripherals."),
    44: (make_primary("computer-science", "computer-science/operating-systems", None), "Operating system shortcuts: F2 key for renaming files and folders."),
    45: (make_primary("computer-science", "computer-science/computer-systems-and-architecture", None), "Artificial intelligence history: SNARC as first neural network computer."),
    46: (make_primary("computer-science", "computer-science/computer-systems-and-architecture", None), "Application software: CAD full form (Computer Aided Design)."),
    47: (make_primary("computer-science", "computer-science/networking", None), "Web design concepts: User navigation path / clickstream tracking."),
    48: (make_primary("computer-science", "computer-science/computer-systems-and-architecture", None), "CPU performance: Clock rate measurement in Hertz (MHz/GHz)."),
    49: (make_primary("computer-science", "computer-science/computer-systems-and-architecture", None), "Processor architecture: VLIW full form (Very Long Instruction Word)."),
    50: (make_primary("computer-science", "computer-science/networking", None), "Computing culture: Term 'Cyberspace' coined by William Gibson in Neuromancer."),
    51: (make_primary("mathematics", "mathematics/arithmetic", None), "Arithmetic: Division algorithm (Dividend = Divisor × Quotient + Remainder)."),
    52: (make_primary("mathematics", "mathematics/arithmetic", None), "Arithmetic: Number theory, finding total number of factors of 72."),
    53: (make_primary("mathematics", "mathematics/arithmetic", None), "Arithmetic: Consecutive integers average word problem."),
    54: (make_primary("mathematics", "mathematics/arithmetic", None), "Arithmetic: Decimal division computation (0.75 / 0.25)."),
    55: (make_primary("mathematics", "mathematics/arithmetic", None), "Arithmetic: Radical exponent evaluation (81^(1/2) - 4)."),
    56: (make_primary("mathematics", "mathematics/algebra", None), "Algebra: Algebraic identity simplification (a+b)^2 - (a-b)^2 = 4ab with surds."),
    57: (make_primary("mathematics", "mathematics/arithmetic", None), "Arithmetic: Average of first n natural numbers ((n+1)/2)."),
    58: (make_primary("mathematics", "mathematics/arithmetic", None), "Arithmetic: Average computation when an observation is excluded."),
    59: (make_primary("mathematics", "mathematics/arithmetic", None), "Arithmetic: Percentage discount calculation from marked and selling price."),
    60: (make_primary("mathematics", "mathematics/arithmetic", None), "Arithmetic: Percentage discount calculation on marked price."),
    61: (make_primary("mathematics", "mathematics/arithmetic", None), "Arithmetic: Percentage word problem finding total students given girls count."),
    62: (make_primary("mathematics", "mathematics/arithmetic", None), "Arithmetic: Examination percentage score computation (360 out of 450)."),
    63: (make_primary("mathematics", "mathematics/arithmetic", None), "Arithmetic: Ratio and proportion problem on ages."),
    64: (make_primary("mathematics", "mathematics/arithmetic", None), "Arithmetic: Ratio and proportion mixture problem with milk and water."),
    65: (make_primary("mathematics", "mathematics/arithmetic", None), "Arithmetic: Work and time problem with two individuals working together."),
    66: (make_primary("mathematics", "mathematics/arithmetic", None), "Arithmetic: Speed, time and distance (train crossing a pole)."),
    67: (make_primary("mathematics", "mathematics/arithmetic", None), "Arithmetic: Compound interest computation on principal for 2 years."),
    68: (make_primary("mathematics", "mathematics/mensuration", None), "Mensuration: Area of triangle given base and perpendicular height."),
    69: (make_primary("mathematics", "mathematics/geometry", None), "Trigonometry / Geometry: Angle of elevation of tower from ground point."),
    70: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/data-interpretation", None), "Data interpretation: Average enrolment calculation from tabular data."),
    71: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/data-interpretation", None), "Data interpretation: Percentage growth calculation from tabular data."),
    72: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/data-interpretation", None), "Data interpretation: Percentage deduction and remaining count calculation."),
    73: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/data-interpretation", None), "Data interpretation: Production percentage increase from bar chart data."),
    74: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/data-interpretation", None), "Data interpretation: Threshold condition analysis from production bar chart."),
    75: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/data-interpretation", None), "Data interpretation: Average of extreme values from graphical dataset."),
    76: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/verbal-reasoning", None), "Verbal reasoning: Classification / odd-one-out based on logical grouping."),
    77: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/verbal-reasoning", None), "Verbal reasoning: Semantic analogy and word relationship classification."),
    78: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/verbal-reasoning", None), "Non-verbal reasoning: Successive paper folding and hole punch pattern."),
    79: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/verbal-reasoning", None), "Direction sense: Spatial angular rotations clockwise and anticlockwise."),
    80: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/series", None), "Number series: Pattern recognition in quadratic difference series (2, 6, 12, 20, 30)."),
    81: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/verbal-reasoning", None), "Blood relations: Deductive familial kinship relationship determination."),
    82: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/numerical-ability", None), "Numerical ability: Unitary cost comparison between pens and pencils."),
    83: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/verbal-reasoning", None), "Deductive reasoning: Categorical syllogism with roses and flowers."),
    84: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/verbal-reasoning", None), "Linear ordering: Relative height comparison and ranking of individuals."),
    85: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/verbal-reasoning", None), "Situational judgment: Team leadership and workplace productivity management."),
    86: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/verbal-reasoning", None), "Verbal reasoning: Classification of antonymous / synonymous word sets."),
    87: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/verbal-reasoning", None), "Letter reasoning: Alphabet classification by structural / vowel properties."),
    88: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/numerical-ability", None), "Numerical reasoning: Product of digits comparison across numbers."),
    89: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/verbal-reasoning", None), "Blood relations: Identification of family member through descriptive puzzle."),
    90: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/series", None), "Number series: Alternating pattern recognition and completion."),
    91: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/verbal-reasoning", None), "Non-verbal reasoning: Rotational figure series with 45-degree steps."),
    92: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/verbal-reasoning", None), "Coding-decoding: Alphabet to numerical position mapping (FUTURE -> 6-21-20-21-18-5)."),
    93: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/verbal-reasoning", None), "Coding-decoding: Single-letter forward alphabet shift (PENCIL -> QFODJM)."),
    94: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/verbal-reasoning", None), "Deductive syllogism: Logical deduction from statements on doctors and education."),
    95: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/verbal-reasoning", None), "Deductive syllogism: Logical deduction from statements on fruits and healthy diet."),
    96: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/verbal-reasoning", None), "Deductive syllogism: Logical deduction from statements on strict teachers."),
    97: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/series", None), "Number series: Multiplicative sequence pattern recognition."),
    98: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/verbal-reasoning", None), "Comparison ranking: Determining height order among four friends."),
    99: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/verbal-reasoning", None), "Seating arrangement: Circular seating arrangement facing centre with six persons."),
    100: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/verbal-reasoning", None), "Blood relations: Multi-generational family tree kinship puzzle.")
}

pending_candidates = []
action_counts = Counter()
tax_counts = Counter()

registered_doc = packet["documents"][0] if packet.get("documents") else {
    "id": "doc_a6262eaad562ff93bdb59dd1",
    "sha256": "2567971b6bfbb39f45515c3c503ce31e4ee1b38f9c44bdd07de9aea7f84a8ccb"
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
        "candidate_id": f"tcand_b152_{aid[:16]}",
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
        "rationale": f"Batch 152 source-inspected (PDF page {page}): {reason}",
        "policy_version": "study-tagging-v1",
        "source_evidence": {
            "document_id": registered_doc["id"],
            "sha256": registered_doc["sha256"],
            "physical_page": page,
            "printed_question": str(qnum),
            "inspected": True,
            "note": f"Inspected physical page {page} of LDC Paper-II under Law & Judicial Deptt (Q{qnum}). Verified stem, options, and section classification."
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
    "batch": 152,
    "paper_id": packet["papers"][0]["id"] if packet.get("papers") else "Old_Questions/Direct_NG_2024-2027/LDC Paper-II under Law _ Judicial Deptt...pdf",
    "paper_title": packet["papers"][0]["exam_name"] + " " + packet["papers"][0]["post"] if packet.get("papers") else "LDC Paper-II under Law & Judicial Deptt",
    "total_targets": len(pending_candidates),
    "actions": dict(action_counts),
    "taxonomy_distribution": dict(tax_counts),
    "source_defect_notes": "Clean scan, complete 100 MCQs across 11 physical pages without omission."
}
(out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
print(f"Generated {len(pending_candidates)} pending candidates for Batch 152. Actions: {dict(action_counts)}")
