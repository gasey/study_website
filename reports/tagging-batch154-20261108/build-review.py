"""Build candidates, findings, summary for Batch 154 (LDC SW & WCD Paper-II)."""
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
    1: (make_primary("computer-science", "computer-science/computer-systems-and-architecture", None), "Computer generations: Vacuum tubes as core electronic component of first-generation computers."),
    2: (make_primary("computer-science", "computer-science/computer-systems-and-architecture", None), "CPU architecture: Control Unit (CU) function directing instruction flow and hardware operations."),
    3: (make_primary("computer-science", "computer-science/computer-systems-and-architecture", None), "Processor architecture: Instruction set as the complete vocabulary of machine-level commands."),
    4: (make_primary("computer-science", "computer-science/computer-systems-and-architecture", None), "Memory hierarchy: CPU registers and cache as fastest memory in system."),
    5: (make_primary("computer-science", "computer-science/computer-systems-and-architecture", None), "Storage hierarchy: Primary memory directly accessible to CPU without secondary controllers."),
    6: (make_primary("computer-science", "computer-science/computer-systems-and-architecture", None), "Peripherals: Projector classified as visual optical output display device."),
    7: (make_primary("computer-science", "computer-science/computer-systems-and-architecture", None), "Software types: Operating systems classified as fundamental system software."),
    8: (make_primary("computer-science", "computer-science/computer-systems-and-architecture", None), "Software classification: Firmware defined as permanent software programmed into read-only memory."),
    9: (make_primary("computer-science", "computer-science/computer-systems-and-architecture", None), "Computer types: Supercomputers designed for massive parallel computational tasks."),
    10: (make_primary("computer-science", "computer-science/computer-systems-and-architecture", None), "Cyber law: Information Technology Act 2000 Section 66 penalties for computer hacking."),
    11: (make_primary("computer-science", "computer-science/operating-systems", None), "Operating systems: Process management allocating CPU schedule and memory."),
    12: (make_primary("computer-science", "computer-science/operating-systems", None), "Desktop GUI: Desktop icon types and graphical shortcuts in Windows environment."),
    13: (make_primary("computer-science", "computer-science/operating-systems", None), "OS history: Major releases and version history of Microsoft Windows."),
    14: (make_primary("computer-science", "computer-science/operating-systems", None), "GUI shortcuts: Ctrl+A shortcut for universal file selection in directory."),
    15: (make_primary("computer-science", "computer-science/operating-systems", None), "File systems: Parent folder and child subfolder hierarchical directory structure."),
    16: (make_primary("computer-science", "computer-science/operating-systems", None), "File systems: File extension association determining application handling."),
    17: (make_primary("computer-science", "computer-science/operating-systems", None), "File management: Windows Recycle Bin temporary deleted file storage."),
    18: (make_primary("computer-science", "computer-science/operating-systems", None), "Storage management: Disk formatting preparing file system architecture."),
    19: (make_primary("computer-science", "computer-science/office-applications", None), "Word processing: Document layout and print view modes in MS Word."),
    20: (make_primary("computer-science", "computer-science/office-applications", None), "Word processing: Page margin configurations and ruler measurements."),
    21: (make_primary("computer-science", "computer-science/office-applications", None), "Word processing: Ribbon tabs and command grouping in modern office suite."),
    22: (make_primary("computer-science", "computer-science/office-applications", None), "Word processing: Table insertion, cell merging and table properties."),
    23: (make_primary("computer-science", "computer-science/office-applications", None), "Word processing: Proofing tools, spell check and grammar verification."),
    24: (make_primary("computer-science", "computer-science/office-applications", None), "Spreadsheets: Formula syntax and calculation operators in MS Excel."),
    25: (make_primary("computer-science", "computer-science/office-applications", None), "Spreadsheets: Chart types and visual data representations."),
    26: (make_primary("computer-science", "computer-science/office-applications", None), "Spreadsheets: Relative versus absolute cell addressing using dollar symbols."),
    27: (make_primary("computer-science", "computer-science/office-applications", None), "Spreadsheets: Standard mathematical and statistical functions (SUM, AVERAGE)."),
    28: (make_primary("computer-science", "computer-science/office-applications", None), "Spreadsheets: Sorting and filtering tabular records."),
    29: (make_primary("computer-science", "computer-science/office-applications", None), "Presentation software: Slide transition effects between slides in PowerPoint."),
    30: (make_primary("computer-science", "computer-science/office-applications", None), "Presentation software: Slide Sorter view for thumbnail slide reordering."),
    31: (make_primary("computer-science", "computer-science/office-applications", None), "Presentation software: Animation pane and custom object animations."),
    32: (make_primary("computer-science", "computer-science/office-applications", None), "Presentation software: Slide Master configuring uniform template design."),
    33: (make_primary("computer-science", "computer-science/office-applications", None), "Office tools: Standard print preview and printer page orientation settings."),
    34: (make_primary("computer-science", "computer-science/office-applications", None), "Office tools: Exporting documents to PDF format."),
    35: (make_primary("computer-science", "computer-science/office-applications", None), "Office tools: Header and footer insertion in multi-page documents."),
    36: (make_primary("computer-science", "computer-science/networking", None), "Networking basics: LAN, MAN, and WAN geographic network classifications."),
    37: (make_primary("computer-science", "computer-science/networking", None), "Network topology: Star, ring, bus and mesh physical network topologies."),
    38: (make_primary("computer-science", "computer-science/networking", None), "Internet tools: Web browser function rendering HTML and web content."),
    39: (make_primary("computer-science", "computer-science/networking", None), "Web search: Search engines indexing and indexing algorithms."),
    40: (make_primary("computer-science", "computer-science/networking", None), "Web architecture: Uniform Resource Locator (URL) component breakdown."),
    41: (make_primary("computer-science", "computer-science/networking", None), "Protocols: HTTP and HTTPS protocol standards for web communication."),
    42: (make_primary("computer-science", "computer-science/networking", None), "Protocols: SMTP and POP3/IMAP email transfer and retrieval protocols."),
    43: (make_primary("computer-science", "computer-science/networking", None), "Electronic mail: Email headers, CC, BCC, and attachment mechanics."),
    44: (make_primary("computer-science", "computer-science/networking", None), "Cloud computing: Cloud storage services and remote accessibility."),
    45: (make_primary("computer-science", "computer-science/networking", None), "Cybersecurity: Computer virus, worm, trojan horse malware definitions."),
    46: (make_primary("computer-science", "computer-science/networking", None), "Cybersecurity: Firewall protection filtering incoming and outgoing network traffic."),
    47: (make_primary("computer-science", "computer-science/networking", None), "Cybersecurity: Strong password criteria and authentication best practices."),
    48: (make_primary("computer-science", "computer-science/networking", None), "Web concepts: Cookies storing user session data in browser."),
    49: (make_primary("computer-science", "computer-science/networking", None), "Web concepts: Hyperlink navigation connecting hypertext documents."),
    50: (make_primary("computer-science", "computer-science/networking", None), "Internet infrastructure: Domain Name System (DNS) IP address resolution."),
    51: (make_primary("mathematics", "mathematics/arithmetic", None), "Number systems: Positioning of negative and positive rational numbers on number line."),
    52: (make_primary("mathematics", "mathematics/arithmetic", None), "Fractions: Subtracting fractions to achieve target difference (2/3 - x = 1/6)."),
    53: (make_primary("mathematics", "mathematics/arithmetic", None), "Rational numbers: Identifying intermediate rational numbers between given bounds."),
    54: (make_primary("mathematics", "mathematics/arithmetic", None), "Linear equations: Fractional difference algebraic word problem (3/5x - 2/7x = 44)."),
    55: (make_primary("mathematics", "mathematics/algebra", None), "Exponents: Exponential power multiplication and linear exponent equation."),
    56: (make_primary("mathematics", "mathematics/arithmetic", None), "Number properties: Prime factorisation to find least divisor yielding perfect square."),
    57: (make_primary("mathematics", "mathematics/arithmetic", None), "Number properties: Finding least four-digit perfect square (1024 = 32^2)."),
    58: (make_primary("mathematics", "mathematics/arithmetic", None), "Surds and radicals: Radical simplification and addition/subtraction (sqrt(50) + sqrt(8) - sqrt(18))."),
    59: (make_primary("mathematics", "mathematics/algebra", None), "Number algebra: Two-digit number relation where tens digit is twice unit digit."),
    60: (make_primary("mathematics", "mathematics/arithmetic", None), "Percentages: Unit conversion and percentage calculation (36 mm of 1.2 m)."),
    61: (make_primary("mathematics", "mathematics/arithmetic", None), "Percentages: Finding total population given percentage of subset (36% boys, girls count given)."),
    62: (make_primary("mathematics", "mathematics/arithmetic", None), "Profit and loss: Cost per unit versus selling price per unit determining profit/loss."),
    63: (make_primary("mathematics", "mathematics/arithmetic", None), "Commercial mathematics: Sales tax addition on marked retail price."),
    64: (make_primary("mathematics", "mathematics/arithmetic", None), "Commercial mathematics: Single equivalent discount for three successive discounts."),
    65: (make_primary("mathematics", "mathematics/arithmetic", None), "Commercial mathematics: Discount percentage applied to retail ticket price."),
    66: (make_primary("mathematics", "mathematics/arithmetic", None), "Interest: Difference between Compound Interest and Simple Interest for 2 years."),
    67: (make_primary("mathematics", "mathematics/arithmetic", None), "Ratio and proportion: Determining antecedent given ratio (2:5) and consequent (90)."),
    68: (make_primary("mathematics", "mathematics/arithmetic", None), "Ratio and proportion: Finding difference between numbers given ratio (3:7) and HCF (5)."),
    69: (make_primary("mathematics", "mathematics/arithmetic", None), "Ratio and proportion: Proportional division among four shares ABCD."),
    70: (make_primary("mathematics", "mathematics/arithmetic", None), "Ratio and proportion: Percentage of proportion component determining total."),
    71: (make_primary("mathematics", "mathematics/arithmetic", None), "Ratio and proportion: Difference of squares relation in integer ratio (4:5)."),
    72: (make_primary("mathematics", "mathematics/arithmetic", None), "Work and time: Equivalence between men and women work rates solving group completion time."),
    73: (make_primary("mathematics", "mathematics/arithmetic", None), "Work and time: Joint work completion time by two individuals."),
    74: (make_primary("mathematics", "mathematics/arithmetic", None), "Work and time: Inverse variation worker-days calculation."),
    75: (make_primary("mathematics", "mathematics/arithmetic", None), "Work and time: Fraction of work remaining after joint work for specific duration."),
    76: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/verbal-reasoning", None), "Verbal reasoning: Natural phenomenon analogy (Thunder : Rain :: Dark : Night)."),
    77: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/verbal-reasoning", None), "Verbal reasoning: Geometric component analogy (Arc : Circle :: Line : Rectangle)."),
    78: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/verbal-reasoning", None), "Deductive syllogism: Universal affirmative and universal negative statements evaluation."),
    79: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/verbal-reasoning", None), "Letter analogy: Letter triad shift pattern transformation (CKO:FNL :: DPQ:?)."),
    80: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/verbal-reasoning", None), "Coding-decoding: Word cipher transformation pattern (BASE -> GUCD)."),
    81: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/verbal-reasoning", None), "Non-verbal reasoning: Lateral reflection mirror image determination."),
    82: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/verbal-reasoning", None), "Linear ranking: Total strength determination from dual directional rank (7th top, 26th bottom)."),
    83: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/verbal-reasoning", None), "Linear arrangement: Relative separation position in row of 32 students."),
    84: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/verbal-reasoning", None), "Direction sense: Two-dimensional vector displacement and distance from starting point."),
    85: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/verbal-reasoning", None), "Non-verbal reasoning: Geometric rotational congruence identification."),
    86: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/verbal-reasoning", None), "Blood relations: Kinship identification (son of mother's brother = maternal cousin)."),
    87: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/numerical-ability", None), "Numerical puzzles: Missing number in geometric diagram pattern."),
    88: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/verbal-reasoning", None), "Alphabet manipulation: Forward letter shift and vowel counting in FANTASTIC."),
    89: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/verbal-reasoning", None), "Logical sequence: Ordering linguistic hierarchy (Letter, Word, Phrase, Sentence, Paragraph)."),
    90: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/verbal-reasoning", None), "Direction sense: Tracking facing orientation after cardinal turns."),
    91: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/verbal-reasoning", None), "Linear seating: Seating arrangement determining immediate right neighbour."),
    92: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/verbal-reasoning", None), "Linear seating: Determining person second from right end in line."),
    93: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/verbal-reasoning", None), "Linear seating: Determining median person in linear arrangement."),
    94: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/numerical-ability", None), "Clock problems: Angle between hour hand and minute hand at specific time."),
    95: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/numerical-ability", None), "Calendar arithmetic: Modulo 7 day calculation after 75 elapsed days."),
    96: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/verbal-reasoning", None), "Blood relations: Deductive family relationship puzzle determining relation of R to D."),
    97: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/verbal-reasoning", None), "Blood relations: Kinship relation of D to K."),
    98: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/verbal-reasoning", None), "Blood relations: Kinship relation of W to P."),
    99: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/verbal-reasoning", None), "Alphanumeric series: Conditional pattern search for letters preceding/succeeding specific symbols."),
    100: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/verbal-reasoning", None), "Alphanumeric series: Conditional pattern search for numbers meeting adjacent criteria.")
}

pending_candidates = []
action_counts = Counter()
tax_counts = Counter()

registered_doc = packet["documents"][0] if packet.get("documents") else {
    "id": "doc_676fef38b446a6f195ca1ef0",
    "sha256": "3cb49a4e3fa3878b66e3b5e43a9926d70cb6eb883b631d871bc541a7741d7f19"
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
        "candidate_id": f"tcand_b154_{aid[:16]}",
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
        "rationale": f"Batch 154 source-inspected (PDF page {page}): {reason}",
        "policy_version": "study-tagging-v1",
        "source_evidence": {
            "document_id": registered_doc["id"],
            "sha256": registered_doc["sha256"],
            "physical_page": page,
            "printed_question": str(qnum),
            "inspected": True,
            "note": f"Inspected physical page {page} of LDC under SW, WCD Paper-II (Q{qnum}). Verified stem, options, and section classification."
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
    "batch": 154,
    "paper_id": packet["papers"][0]["id"] if packet.get("papers") else "Old_Questions/Direct_NG_2024-2027/LDC under SW, WCD Paper-II..pdf",
    "paper_title": packet["papers"][0]["exam_name"] + " " + packet["papers"][0]["post"] if packet.get("papers") else "LDC under SW, WCD Paper-II",
    "total_targets": len(pending_candidates),
    "actions": dict(action_counts),
    "taxonomy_distribution": dict(tax_counts),
    "source_defect_notes": "Clean scan, complete 100 MCQs across 18 physical pages without omission."
}
(out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
print(f"Generated {len(pending_candidates)} pending candidates for Batch 154. Actions: {dict(action_counts)}")
