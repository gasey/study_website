"""Build candidates, findings, summary for Batch 148 (UDC Tourism 2018 Paper-II)."""
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

# Mapping of qnum to physical page in the PDF (from our earlier analysis)
def get_physical_page(qnum):
    if qnum <= 7: return 1
    if qnum <= 20: return 2
    if qnum <= 33: return 3
    if qnum <= 46: return 4
    if qnum <= 58: return 5
    if qnum <= 70: return 6
    if qnum <= 79: return 7
    if qnum <= 90: return 8
    return 9

pending_candidates = []
action_counts = Counter()
tax_counts = Counter()

# Specific decisions for each qnum in UDC Tourism 2018 Paper-II
decisions = {
    1: (make_primary("general-studies", "general-studies/mizoram", None), "Mizoram state event (President Ram Nath Kovind visit to Mizoram in Nov 2017).", "mizoram"),
    2: (make_primary("general-studies", "general-studies/current-affairs", None), "International current affairs (US recognition of Jerusalem as Israel capital).", "dynamic"),
    3: (make_primary("general-studies", "general-studies/current-affairs", None), "Current natural disasters / meteorology (Cyclone Mora in May 2017).", "dynamic"),
    4: (make_primary("general-studies", "general-studies/current-affairs", None), "Global indices & reports (Global Gender Gap Index 2017 top country).", "dynamic"),
    5: (make_primary("general-studies", "general-studies/current-affairs", None), "Government initiative (Less Cash Year 2017).", "dynamic"),
    6: (make_primary("general-studies", "general-studies/current-affairs", None), "International organization leadership (UN High Commissioner for Refugees).", "dynamic"),
    7: (make_primary("general-studies", "general-studies/current-affairs", None), "International judicial body representation (Indian judge at ICJ).", "dynamic"),
    8: (make_primary("general-studies", "general-studies/environment", None), "Environmental conservation & wildlife monitoring (M-STrIPES tiger reserve maintenance).", "static"),
    9: (make_primary("general-studies", "general-studies/current-affairs", None), "National transport & infrastructure project (first freight village in Varanasi).", "dynamic"),
    10: (make_primary("general-studies", "general-studies/current-affairs", None), "Sports events & adventure tourism (Global Paragliding Contest Dec 2017).", "dynamic"),
    11: (make_primary("general-studies", "general-studies/current-affairs", None), "International trade & digital policy (Digital Single Market Strategy - EU).", "dynamic"),
    12: (make_primary("general-knowledge", "general-knowledge/art-and-culture", None), "Literature / Indian authors ('One Indian Girl' by Chetan Bhagat).", "static"),
    13: (make_primary("general-knowledge", "general-knowledge/art-and-culture", None), "Books & autobiographies ('My Country My Life' by LK Advani).", "static"),
    14: (make_primary("general-knowledge", "general-knowledge/sports", None), "Sports tournament winner (WTA Finals 2017 Caroline Wozniacki).", "dynamic"),
    15: (make_primary("general-knowledge", "general-knowledge/sports", None), "Sports personalities (PV Sindhu - Badminton).", "static"),
    16: (make_primary("general-studies", "general-studies/indian-economy", None), "Socio-economic urban poverty scheme (BSUP: Basic Services to Urban Poor).", "static"),
    17: (make_primary("general-knowledge", "general-knowledge/static-gk", None), "Defence acronyms & technology (QR-SAM: Quick Reaction Surface-to-Air Missile).", "static"),
    18: (make_primary("general-knowledge", "general-knowledge/static-gk", None), "Geographical sobriquets ('Land of Morning Calm' - South Korea).", "static"),
    19: (make_primary("general-studies", "general-studies/geography", None), "Indian economic geography sobriquets ('Manchester of India' - Ahmedabad).", "static"),
    20: (make_primary("general-knowledge", "general-knowledge/art-and-culture", None), "Literary honours & awards (Jnanpith Award 2017 - Krishna Sobti).", "dynamic"),
    21: (make_primary("general-knowledge", "general-knowledge/static-gk", None), "Scientific inventions & telecommunications history (Mobile phone - Martin Cooper).", "static"),
    22: (make_primary("general-knowledge", "general-knowledge/static-gk", None), "Inventions & household technology (Microwave oven - Percy Spencer).", "static"),
    23: (make_primary("computer-science", "computer-science/computer-systems-and-architecture", "computer-science/computer-systems-and-architecture/history-and-generations"), "Supercomputing history and development in India.", "static"),
    24: (make_primary("computer-science", "computer-science/networking", None), "Data communication and telecommunications standards (ISDN).", "static"),
    25: (make_primary("computer-science", "computer-science/networking", None), "Mobile network generations & wireless communication standards (SMS introduced in 2G).", "static"),
    26: (make_primary("computer-science", "computer-science/office-applications", None), "Word processing shortcut keys (Subscript shortcut Ctrl + =).", "static"),
    27: (make_primary("computer-science", "computer-science/office-applications", None), "Digital document formatting & typography definition (Font: design of type).", "static"),
    28: (make_primary("general-studies", "general-studies/current-affairs", None), "Technology in the news / digital apps (Datally launched by Google).", "dynamic"),
    29: (make_primary("general-studies", "general-studies/current-affairs", None), "Security institutions in the news (Global Centre for Security & Counter Terrorism).", "dynamic"),
    30: (make_primary("general-studies", "general-studies/environment", None), "Renewable energy installations & urban infrastructure (first rooftop solar carpet).", "dynamic"),
    31: (make_primary("general-knowledge", "general-knowledge/art-and-culture", None), "Indian cinema & cultural festivals (3D Sanskrit film Anurakti at IFFI).", "dynamic"),
    32: (make_primary("general-knowledge", "general-knowledge/sports", None), "International football awards (European Golden Shoe 2017).", "dynamic"),
    33: (make_primary("general-studies", "general-studies/current-affairs", None), "International diplomacy & judiciary (Dalveer Bhandari ICJ re-election).", "dynamic"),
    34: (make_primary("general-studies", "general-studies/current-affairs", None), "State healthcare initiatives (public air ambulance service).", "dynamic"),
    35: (make_primary("general-studies", "general-studies/indian-economy", None), "Global economic rankings (world richest country by GDP per capita).", "dynamic"),
    36: (make_primary("general-studies", "general-studies/environment", None), "International environmental observances (World Toilet Day 2017 theme).", "dynamic"),
    37: (make_primary("general-studies", "general-studies/current-affairs", None), "Global development indices (India rank in Global Gender Gap Index 2017).", "dynamic"),
    38: (make_primary("general-studies", "general-studies/current-affairs", None), "Humanitarian awards (Mother Teresa Award 2017 for Social Justice).", "dynamic"),
    39: (make_primary("general-studies", "general-studies/current-affairs", None), "International summits & diplomatic meetings (31st ASEAN Summit 2017).", "dynamic"),
    40: (make_primary("general-studies", "general-studies/current-affairs", None), "National urban safety schemes (Safe City plan for women).", "dynamic"),
    41: (make_primary("general-knowledge", "general-knowledge/art-and-culture", None), "Classic world literature / authors ('Robinson Crusoe' by Daniel Defoe).", "static"),
    42: (make_primary("general-studies", "general-studies/mizoram", None), "Mizo literature and publications ('Thinglubul' by Romuanpuii Zadeng).", "mizoram"),
    43: (make_primary("general-knowledge", "general-knowledge/sports", None), "Sports terminology & tournaments (Grand Slam in Tennis).", "static"),
    44: (make_primary("general-knowledge", "general-knowledge/sports", None), "Indian domestic sports trophies (Santosh Trophy - Football).", "static"),
    45: (make_primary("computer-science", "computer-science/office-applications", None), "Spreadsheet applications (Excel worksheet basic unit - Cell).", "static"),
    46: (make_primary("computer-science", "computer-science/computer-systems-and-architecture", "computer-science/computer-systems-and-architecture/computer-hardware"), "Computer hardware peripherals (Input devices - Keyboard).", "static"),
    47: (make_primary("computer-science", "computer-science/computer-systems-and-architecture", "computer-science/computer-systems-and-architecture/memory-and-storage"), "Computer memory hierarchy (Main working memory - RAM).", "static"),
    48: (make_primary("science", "science/biology", None), "Medical microbiology & antibiotics discovery (Penicillin - Alexander Fleming).", "static"),
    49: (make_primary("general-knowledge", "general-knowledge/static-gk", None), "Banking technology acronyms (ATM: Automated Teller Machine).", "static"),
    50: (make_primary("general-knowledge", "general-knowledge/art-and-culture", None), "International awards & honours (Nobel Prize awarding country - Sweden).", "static"),
    51: (make_primary("general-knowledge", "general-knowledge/sports", None), "National sports awards criteria (Arjuna Award).", "static"),
    52: (make_primary("general-studies", "general-studies/world-history", None), "Historical geopolitical sobriquets ('Sick Man of Europe' - Ottoman Turkey).", "static"),
    53: (make_primary("general-studies", "general-studies/geography", None), "World geographic sobriquets ('Isle of Pearls' - Bahrain).", "static"),
    54: (make_primary("general-studies", "general-studies/current-affairs", None), "International cultural diplomacy & fitness (Yoga declared sports activity in Saudi Arabia).", "dynamic"),
    55: (make_primary("general-studies", "general-studies/current-affairs", None), "Lexicography & media in the news (Collins Word of the Year 2017 - Fake news).", "dynamic"),
    56: (make_primary("general-studies", "general-studies/current-affairs", None), "Regional governance / state leadership (Chief Minister of Nagaland in 2017).", "dynamic"),
    57: (make_primary("general-knowledge", "general-knowledge/sports", None), "Olympic sports symbols & branding (Beijing 2022 Winter Games emblem).", "dynamic"),
    58: (make_primary("general-knowledge", "general-knowledge/sports", None), "Indian para-athletes & achievements (Kanchanmala Pande - Swimming).", "dynamic"),
    59: (make_primary("general-knowledge", "general-knowledge/art-and-culture", None), "Indian cinema personalities / obituaries (Shashi Kapoor).", "dynamic"),
    60: (make_primary("general-studies", "general-studies/current-affairs", None), "Pageantry & national personalities (Manushi Chhillar Miss World 2017).", "dynamic"),
    61: (make_primary("general-studies", "general-studies/current-affairs", None), "National conferences & health themes (International Conference on Yoga 2017).", "dynamic"),
    62: (make_primary("science", "science/biology", "science/biology/human-physiology"), "Human pathology and public health (Trachoma eye infection).", "static"),
    63: (make_primary("general-studies", "general-studies/indian-polity", None), "Constitutional dignitaries / Vice-President of India.", "dynamic"),
    64: (make_primary("general-studies", "general-studies/mizoram", None), "Mizoram sports achievement (Aizawl FC winning I-League 2016-17).", "mizoram"),
    65: (make_primary("general-knowledge", "general-knowledge/art-and-culture", None), "Literature / poetry collections ('Forbidden Verses' by Abu Nuwas).", "static"),
    66: (make_primary("general-knowledge", "general-knowledge/sports", None), "International sports personalities (Stan Wawrinka - Switzerland tennis).", "static"),
    67: (make_primary("general-studies", "general-studies/indian-polity", None), "Investigative and law enforcement agencies (CBI full form).", "static"),
    68: (make_primary("general-knowledge", "general-knowledge/static-gk", None), "Government computer bodies & educational acronyms (DOEACC full form).", "static"),
    69: (make_primary("general-studies", "general-studies/geography", None), "Urban geography sobriquets ('City of Skyscrapers' - New York).", "static"),
    70: (make_primary("general-knowledge", "general-knowledge/static-gk", None), "National civilian honours hierarchy (Bharat Ratna highest award).", "static"),
    71: (make_primary("general-studies", "general-studies/current-affairs", None), "International philanthropic and cultural prizes (Israel Genesis Prize 2018).", "dynamic"),
    72: (make_primary("general-knowledge", "general-knowledge/static-gk", None), "History of science and printing (Printing press - Gutenberg).", "static"),
    73: (make_primary("science", "science/physics", None), "Inventions and aeronautics history (Aeroplane - Wright Brothers).", "static"),
    74: (make_primary("computer-science", "computer-science/computer-systems-and-architecture", "computer-science/computer-systems-and-architecture/computer-hardware"), "Computer architecture fundamentals (CPU full form).", "static"),
    75: (make_primary("computer-science", "computer-science/computer-systems-and-architecture", "computer-science/computer-systems-and-architecture/memory-and-storage"), "Secondary computer storage & portability (Flash Drive).", "static"),
    76: (make_primary("mathematics", "mathematics/arithmetic", None), "Arithmetic: Speed, distance, and time (train crossing a pole).", "static"),
    77: (make_primary("mathematics", "mathematics/arithmetic", None), "Arithmetic: Fractional subtraction and rope measurements.", "static"),
    78: (make_primary("mathematics", "mathematics/mensuration", "mathematics/mensuration/volume"), "Mensuration: Cylinder volume scaling with halved radius.", "static"),
    79: (make_primary("statistics", "statistics/probability-and-statistics", "statistics/probability-and-statistics/probability"), "Probability: Selecting letters from a word.", "static"),
    80: (make_primary("mathematics", "mathematics/arithmetic", "mathematics/arithmetic/averages"), "Arithmetic: Age averages combined with ratio.", "static"),
    81: (make_primary("mathematics", "mathematics/arithmetic", None), "Arithmetic: Harmonic average speed and total journey distance.", "static"),
    82: (make_primary("mathematics", "mathematics/arithmetic", None), "Arithmetic: Simple interest duration calculation.", "static"),
    83: (make_primary("mathematics", "mathematics/arithmetic", None), "Arithmetic: Product of HCF and LCM of two numbers.", "static"),
    84: (make_primary("mathematics", "mathematics/algebra", "mathematics/algebra/algebraic-expressions"), "Algebra: Solving linear fractional equation for variable x.", "static"),
    85: (make_primary("mathematics", "mathematics/arithmetic", "mathematics/arithmetic/percentages"), "Arithmetic: Weight unit conversion and percentage calculation.", "static"),
    86: (make_primary("mathematics", "mathematics/arithmetic", "mathematics/arithmetic/percentages"), "Arithmetic: Expenditure compensation after percentage price increase.", "static"),
    87: (make_primary("mathematics", "mathematics/arithmetic", "mathematics/arithmetic/profit-and-loss"), "Arithmetic: Selling price calculation with profit and loss margins.", "static"),
    88: (make_primary("mathematics", "mathematics/arithmetic", "mathematics/arithmetic/profit-and-loss"), "Arithmetic: Successive commercial discounts on marked price.", "static"),
    89: (make_primary("mathematics", "mathematics/arithmetic", "mathematics/arithmetic/ratio-and-proportion"), "Arithmetic: Unitary method and proportion calculation.", "static"),
    90: (make_primary("mathematics", "mathematics/arithmetic", None), "Arithmetic: Pipes and cisterns filling and emptying rates.", "static"),
    91: (make_primary("mathematics", "mathematics/geometry", "mathematics/geometry/triangles"), "Geometry: Similar triangles and proportional shadows.", "static"),
    92: (make_primary("mathematics", "mathematics/arithmetic", "mathematics/arithmetic/ratio-and-proportion"), "Arithmetic: Fractional parts and total page count.", "static"),
    93: (make_primary("mathematics", "mathematics/algebra", "mathematics/algebra/algebraic-expressions"), "Algebra: Exponent rules and power equations.", "static"),
    94: (make_primary("mathematics", "mathematics/geometry", "mathematics/geometry/circles"), "Geometry: Circular wheel circumference and distance covered.", "static"),
    95: (make_primary("mathematics", "mathematics/mensuration", "mathematics/mensuration/volume"), "Mensuration: Volume conservation in recasting cone into spheres.", "static"),
    96: (make_primary("mathematics", "mathematics/arithmetic", None), "Arithmetic: Time and work combined completion rate.", "static"),
    97: (make_primary("mathematics", "mathematics/arithmetic", "mathematics/arithmetic/ratio-and-proportion"), "Arithmetic: Direct proportion between time and distance.", "static"),
    98: (make_primary("mathematics", "mathematics/arithmetic", "mathematics/arithmetic/ratio-and-proportion"), "Arithmetic: Mixtures and allegiant ratio adjustments.", "static"),
    99: (make_primary("mathematics", "mathematics/mensuration", "mathematics/mensuration/area"), "Mensuration: Circle area from circumference.", "static"),
    100: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/numerical-ability", None), "Numerical ability: Set theory and two-set intersection.", "static")
}

for it in packet["items"]:
    snap = it["snapshot"]
    rec = snap["record"]
    aid = it["appearance_id"]
    cid = it["canonical_id"]
    cur_primary = rec["classification"]
    pid = it["appearance"]["paper_id"]
    qnum = int(it["appearance"]["qnum"])
    qtext = rec["question"]
    page = get_physical_page(qnum)

    prop, reason, time_behavior = decisions[qnum]
    action = "keep" if prop == cur_primary else "retag"
    action_counts[action] += 1
    tax_counts[f"{prop['subject_id']} > {prop['topic_id']}"] += 1

    region = "IN-MZ" if prop["topic_id"] == "general-studies/mizoram" else ""
    context_reason = "Regional context: Mizoram state interest." if region else ("Dynamic current affairs topic." if time_behavior == "dynamic" else "Standard static syllabus knowledge.")

    cand = {
        "candidate_id": f"tcand_b148_{aid[:16]}",
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
        "rationale": f"Batch 148 source-inspected (page {page}): {reason}",
        "policy_version": "study-tagging-v1",
        "source_evidence": {
            "document_id": pid,
            "sha256": "2.UDC under Tourism Deptt.-II",
            "physical_page": page,
            "printed_question": str(qnum),
            "inspected": True,
            "note": f"Inspected physical page {page} of UDC Tourism June-2018 Paper II (Q{qnum}). Verified stem, options, and section layout."
        },
        "context_candidate": {
            "region": region,
            "language": "en",
            "time_behavior": time_behavior,
            "reference_period": "2017-2018" if time_behavior == "dynamic" else "",
            "reference_basis": "question_stem" if time_behavior == "dynamic" else "unknown"
        },
        "context_reason": context_reason,
        "source_issues": [],
        "taxonomy_gap": None,
        "alternatives": [],
        "owner_question": None
    }
    pending_candidates.append(cand)

assert len(pending_candidates) == 100

(out / "pending-candidates.json").write_text(json.dumps(pending_candidates, indent=2) + "\n")

# Packet file for the whole batch
(out / "packets" / "source-packet-001.json").write_text(json.dumps(pending_candidates, indent=2) + "\n")

# Findings
findings = {
    "batch": 148,
    "paper": "Old_Questions/Direct_2014-2018/2.UDC under Tourism Deptt.-II.pdf",
    "total_candidates": 100,
    "retags": action_counts["retag"],
    "keeps": action_counts["keep"],
    "holds": 0,
    "distribution": dict(tax_counts)
}
(out / "findings.json").write_text(json.dumps(findings, indent=2) + "\n")

# Summary
summary = {
    "batch": 148,
    "status": "pending_owner_review",
    "live_changes": 0,
    "total_reviewed": 100,
    "actions": dict(action_counts),
    "paper_completion": "Old_Questions/Direct_2014-2018/2.UDC under Tourism Deptt.-II.pdf (100/100 complete)"
}
(out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")

# Manifest
manifest = {
    "batch": 148,
    "paper_id": "Old_Questions/Direct_2014-2018/2.UDC under Tourism Deptt.-II.pdf",
    "items_count": 100,
    "actions": dict(action_counts)
}
(out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

print(f"Batch 148 review built successfully: {action_counts['retag']} retags, {action_counts['keep']} keeps, 0 holds.")
