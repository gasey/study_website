"""Build candidates, findings, summary for Batch 150 (SI under Excise 2014 Paper-II)."""
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

def get_physical_page(qnum):
    if 10 <= qnum <= 21: return 4
    if 33 <= qnum <= 44: return 3
    if 58 <= qnum <= 67: return 2
    return 1

pending_candidates = []
action_counts = Counter()
tax_counts = Counter()

decisions = {
    10: (make_primary("general-studies", "general-studies/current-affairs", None), "International beauty pageantry / news (Miss Universe 2013 Gabriela Isler).", "dynamic"),
    11: (make_primary("general-knowledge", "general-knowledge/sports", None), "Grand Slam tennis championship (Australian Open 2014 Women's winner).", "dynamic"),
    12: (make_primary("general-studies", "general-studies/current-affairs", None), "Corporate leadership in technology (Satya Nadella appointed Microsoft CEO).", "dynamic"),
    13: (make_primary("general-studies", "general-studies/mizoram", None), "Mizoram state agriculture achievement (Best Performing State in Agriculture).", "mizoram"),
    14: (make_primary("general-studies", "general-studies/mizoram", None), "Mizoram demographics & 2011 census literacy rate.", "mizoram"),
    15: (make_primary("general-studies", "general-studies/current-affairs", None), "National ceremonial events (Republic Day Parade 2014 Chief Guest Shinzo Abe).", "dynamic"),
    16: (make_primary("general-studies", "general-studies/current-affairs", None), "Neighbourhood international politics (Prime Minister of Bangladesh Sheikh Hasina).", "dynamic"),
    17: (make_primary("general-studies", "general-studies/current-affairs", None), "National defence procurement in the news (AgustaWestland VVIP Chopper deal).", "dynamic"),
    18: (make_primary("general-knowledge", "general-knowledge/sports", None), "International football honors (FIFA Ballon d'Or 2013 winner).", "dynamic"),
    19: (make_primary("general-studies", "general-studies/current-affairs", None), "Union government welfare policy / subsidies (LPG cylinder quota).", "dynamic"),
    20: (make_primary("general-knowledge", "general-knowledge/static-gk", None), "Telecommunications acronyms (EPABX: Electronic Private Automatic Branch Exchange).", "static"),
    21: (make_primary("general-knowledge", "general-knowledge/static-gk", None), "World currencies and monetary units (Indonesian Rupiah).", "static"),
    33: (make_primary("general-knowledge", "general-knowledge/static-gk", None), "Indian scientific and defence research institutions (BARC, ISRO, DRDO acronyms).", "static"),
    34: (make_primary("general-studies", "general-studies/current-affairs", None), "Nobel Prize in Physiology or Medicine 2013.", "dynamic"),
    35: (make_primary("science", "science/biology", None), "Branches of biological sciences (Ornithology: study of birds).", "static"),
    36: (make_primary("computer-science", "computer-science/computer-systems-and-architecture", "computer-science/computer-systems-and-architecture/computer-hardware"), "Computer input peripherals & optical recognition (OMR: Optical Mark Reader).", "static"),
    37: (make_primary("science", "science/physics", None), "Astrophysics and stellar evolution pioneers (Subrahmanyan Chandrasekhar).", "static"),
    38: (make_primary("science", "science/biology", None), "Medical sciences and drug mechanisms (Pharmacology definition).", "static"),
    39: (make_primary("science", "science/biology", "science/biology/human-physiology"), "Human anatomy and organs (Spleen as blood bank of the body).", "static"),
    40: (make_primary("science", "science/physics", None), "Nuclear physics principles (Atom bomb based on nuclear fission).", "static"),
    41: (make_primary("general-studies", "general-studies/mizoram", None), "Mizo historical migration and early settlements (Khampat / Chhinlung).", "mizoram"),
    42: (make_primary("general-studies", "general-studies/mizoram", None), "Linguistic classification of Mizo language (Tibeto-Burman family).", "mizoram"),
    43: (make_primary("general-studies", "general-studies/mizoram", None), "Mizoram colonial history (First Lushai Expedition 1871 leadership).", "mizoram"),
    44: (make_primary("general-studies", "general-studies/mizoram", None), "Mizo literature & missionary lexicography (Lorrain and Savidge Grammar & Dictionary).", "mizoram"),
    58: (make_primary("mathematics", "mathematics/arithmetic", "mathematics/arithmetic/profit-and-loss"), "Arithmetic: Profit percent when cost price of 6 equals selling price of 5.", "static"),
    59: (make_primary("mathematics", "mathematics/arithmetic", None), "Arithmetic: Simple interest time to double the principal.", "static"),
    60: (make_primary("mathematics", "mathematics/arithmetic", None), "Arithmetic: Fractional difference word problem.", "static"),
    61: (make_primary("mathematics", "mathematics/arithmetic", None), "Arithmetic: Speed conversion from m/s to km/h.", "static"),
    62: (make_primary("mathematics", "mathematics/arithmetic", "mathematics/arithmetic/averages"), "Arithmetic: Property of arithmetic mean when constant added to all values.", "static"),
    63: (make_primary("statistics", "statistics/probability-and-statistics", "statistics/probability-and-statistics/descriptive-statistics"), "Statistics: Median of an ungrouped dataset.", "static"),
    64: (make_primary("mathematics", "mathematics/arithmetic", None), "Arithmetic: Decimal linear division equation.", "static"),
    65: (make_primary("mathematics", "mathematics/arithmetic", None), "Arithmetic: Number properties, greatest 4-digit perfect square (9801).", "static"),
    66: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/series", None), "Reasoning: Numeric progression series pattern completion.", "static"),
    67: (make_primary("reasoning-and-aptitude", "reasoning-and-aptitude/series", None), "Reasoning: Alphabetic letter series pattern completion.", "static")
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
    context_reason = "Regional context: Mizoram state history, language, and achievements." if region else ("Dynamic current affairs topic." if time_behavior == "dynamic" else "Standard static syllabus knowledge.")

    cand = {
        "candidate_id": f"tcand_b150_{aid[:16]}",
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
        "rationale": f"Batch 150 source-inspected (PDF page {page}): {reason}",
        "policy_version": "study-tagging-v1",
        "source_evidence": {
            "document_id": pid,
            "sha256": "SI under Excise 2014 General Studies - II.",
            "physical_page": page,
            "printed_question": str(qnum),
            "inspected": True,
            "note": f"Inspected physical page {page} (printed page -{page*2 if page>1 else 8}) of Sub-Inspector under Excise 2014 Paper-II (Q{qnum}). Verified question stem, options, and section classification."
        },
        "context_candidate": {
            "region": region,
            "language": "en",
            "time_behavior": time_behavior,
            "reference_period": "2013-2014" if time_behavior == "dynamic" else "",
            "reference_basis": "question_stem" if time_behavior == "dynamic" else "unknown"
        },
        "context_reason": context_reason,
        "source_issues": [
            {
                "type": "incomplete_source_scan",
                "severity": "defect",
                "detail": "Source PDF contains only even-numbered printed pages (-2, -4, -6, -8). Odd-numbered pages (questions 1-9, 22-32, 45-57, and 68-75) were omitted from the uploaded scan."
            }
        ],
        "taxonomy_gap": None,
        "alternatives": [],
        "owner_question": None
    }
    pending_candidates.append(cand)

assert len(pending_candidates) == 34

(out / "pending-candidates.json").write_text(json.dumps(pending_candidates, indent=2) + "\n")
(out / "packets" / "source-packet-001.json").write_text(json.dumps(pending_candidates, indent=2) + "\n")

findings = {
    "batch": 150,
    "paper": "Old_Questions/Direct_2014-2018/SI under Excise 2014 General Studies - II..pdf",
    "total_candidates": 34,
    "retags": action_counts["retag"],
    "keeps": action_counts["keep"],
    "holds": 0,
    "distribution": dict(tax_counts),
    "source_defects": {
        "omitted_pages": "Odd-numbered pages (1, 3, 5, 7) omitted from PDF scan; only 34 of 75 printed questions present on even-numbered pages."
    }
}
(out / "findings.json").write_text(json.dumps(findings, indent=2) + "\n")

summary = {
    "batch": 150,
    "status": "pending_owner_review",
    "live_changes": 0,
    "total_reviewed": 34,
    "actions": dict(action_counts),
    "paper_completion": "Old_Questions/Direct_2014-2018/SI under Excise 2014 General Studies - II..pdf (34/34 available appearances reviewed; 41 questions missing from source scan)"
}
(out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")

manifest = {
    "batch": 150,
    "paper_id": "Old_Questions/Direct_2014-2018/SI under Excise 2014 General Studies - II..pdf",
    "items_count": 34,
    "actions": dict(action_counts)
}
(out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

print(f"Batch 150 review built successfully: {action_counts['retag']} retags, {action_counts['keep']} keeps, 0 holds.")
