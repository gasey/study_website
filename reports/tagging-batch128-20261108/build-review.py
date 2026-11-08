"""Build review candidates and findings for Batch 128: Jr. Accounts Officer Paper-II (GK, Arithmetic & Reasoning) (Q1–Q50, 50 MCQs)."""
import json
from pathlib import Path
from collections import Counter

out = Path(__file__).resolve().parent
packet = json.load(open(out / "oracle-packet.json"))

def parse_path(path_str):
    parts = path_str.split("/")
    if len(parts) == 1:
        return {"subject_id": parts[0], "topic_id": None, "subtopic_id": None}
    elif len(parts) == 2:
        return {"subject_id": parts[0], "topic_id": path_str, "subtopic_id": None}
    elif len(parts) == 3:
        return {"subject_id": parts[0], "topic_id": f"{parts[0]}/{parts[1]}", "subtopic_id": path_str}
    raise ValueError(path_str)

def assign_tax(qnum, q):
    # Current Affairs
    if qnum in (1, 2, 3, 4):
        return 'general-studies/current-affairs', 'General studies current affairs: international notices, government initiatives (INTERPOL Silver Notice, Project Waterworth, TALASH programme, Yala glacier)'
    
    # History
    elif qnum in (5, 6, 7, 27, 28, 29):
        return 'general-studies/indian-history', 'General studies Indian history: ancient administration and colonial era policies (Subsidiary Alliance, Gupta administration, Anglo-Maratha Wars, Ilbert Bill, Vernacular Press Act 1878, Cripps Mission)'
    
    # Geography
    elif qnum in (8, 9, 10, 30, 31, 32):
        return 'general-studies/geography', 'General studies geography: physical and climatological geography (rainfall types, heat budget, ITCZ, cyclones, latitude lines, world plateaus)'
    
    # Polity
    elif qnum in (11, 12, 33, 34, 35, 36):
        return 'general-studies/indian-polity', 'General studies Indian polity: constitutional provisions and institutions (Fundamental Duties, Drafting Committee, Money Bills, Judicial Review, Tenth Schedule anti-defection, constitutional vs non-constitutional bodies)'
    
    # Economy
    elif qnum in (13, 14, 15, 37, 38):
        return 'general-studies/indian-economy', 'General studies Indian economy: macroeconomic concepts and international trade (GNP, HDI indicators, WTO Amber Box subsidies, Self Help Groups, dependency ratio)'
    
    # Environment
    elif qnum in (16, 39, 40, 41, 43):
        return 'general-studies/environment', 'General studies environment: ecological conservation and sustainability (Red Data Book, Brundtland Report, acid rain pollutants, biosphere reserves, wetlands & coral bleaching)'
    
    # Science
    elif qnum in (17, 42):
        return 'science/biology/ecology', 'Science biology ecology: interspecies relationships and environmental concentrations (amensalism, biomagnification)'
    elif qnum == 18:
        return 'science/physics/mechanics', 'Science physics mechanics: work, force, and energy (work done pushing against a rigid wall)'
    elif qnum == 19:
        return 'science/chemistry', 'Science chemistry: energy storage and chemical batteries (Lithium-ion vs lead-acid batteries)'
    elif qnum in (20, 44):
        return 'science/biology/human-physiology', 'Science biology human physiology: medical isotopes and central nervous system (Iodine-131, cerebellum balance)'
    elif qnum == 45:
        return 'science/physics/light', 'Science physics optics: wave scattering and light dispersion (Rayleigh scattering of blue sky)'
    elif qnum == 46:
        return 'science/biology/cell-biology', 'Science biology cell biology and genetics: chromosomes and RNA protein synthesis'
    
    # Mizoram
    elif qnum in (21, 22, 23, 24, 26, 47, 48, 49, 50):
        return 'general-studies/mizoram', 'General studies Mizoram: history, festivals, folklore, and administration (Zupui Ni, Operation Jericho, folklore, unification of Lushai Hills, Project Thaichhawninu, mythic world tree, Thingdim lam, Ram sem sap, 2nd Governor)'
    
    # Sports
    elif qnum == 25:
        return 'general-knowledge/sports', 'General knowledge sports: stadium venues and tournaments (Estadio Azteca FIFA World Cup)'
    
    else:
        raise ValueError(f"Unhandled question number: {qnum}")

pending_candidates = []
findings = []

paper_id = "Old_Questions/Direct_2025-2027/Jr. Accounts Officer Paper-II (GK, Arithmetic & Reasoning) -Series A..pdf"

for item in packet["items"]:
    cid = item["canonical_id"]
    aid = item["appearance_id"]
    rec = item["snapshot"]["record"]
    qnum_int = int(rec["qnum"])
    q_text = rec["question"]
    fingerprint = item["source_fingerprint"]
    
    cur_cls = rec.get("classification") or {"subject_id": None, "topic_id": None, "subtopic_id": None}
    
    target_tax, rationale = assign_tax(qnum_int, q_text)
    parsed = parse_path(target_tax)
    action = "keep" if parsed == cur_cls else "retag"
    
    cand = {
        "canonical_id": cid,
        "appearance_id": aid,
        "paper_id": paper_id,
        "source_fingerprint": fingerprint,
        "review_status": "pending",
        "action": action,
        "current_primary": cur_cls,
        "proposed_primary": parsed,
        "confidence": 1.0,
        "rationale": rationale,
        "batch_id": 128,
        "policy": "study-tagging-v1"
    }
    pending_candidates.append(cand)
    
    findings.append({
        "qnum": str(qnum_int),
        "canonical_id": cid,
        "appearance_id": aid,
        "action": action,
        "current_taxonomy": cur_cls,
        "target_taxonomy": parsed,
        "rationale": rationale,
        "stem_excerpt": q_text[:80]
    })

findings.sort(key=lambda x: int(x["qnum"]))
pending_candidates.sort(key=lambda x: next(int(i["snapshot"]["record"]["qnum"]) for i in packet["items"] if i["appearance_id"] == x["appearance_id"]))

unextracted_items = []

(out / "pending-candidates.json").write_text(json.dumps(pending_candidates, ensure_ascii=False, indent=2) + "\n")
(out / "findings.json").write_text(json.dumps(findings, ensure_ascii=False, indent=2) + "\n")
(out / "pending-written-intake.json").write_text(json.dumps(unextracted_items, ensure_ascii=False, indent=2) + "\n")

tax_counts = Counter(
    (c["proposed_primary"]["subtopic_id"] or c["proposed_primary"]["topic_id"] or c["proposed_primary"]["subject_id"])
    for c in pending_candidates
)
action_counts = Counter(c["action"] for c in pending_candidates)

summary = {
    "batch": 128,
    "papers": [
        {
            "paper_id": paper_id,
            "paper_title": "General Competitive Examination for Recruitment to the Posts of Junior Accounts Officer (JAO) under Food, Civil Supplies & Consumer Affairs Department, July 2026 — Paper-II (GK, Arithmetic & Reasoning) (Series A) [Part 1: General Knowledge Q1–Q50]",
            "document_id": packet["documents"][0]["id"],
            "sha256": packet["documents"][0]["sha256"],
            "targets": 50
        }
    ],
    "targets": 50,
    "completion": "100% paper completion achieved for Jr. Accounts Officer July 2026 Paper-II (Series A) across Batch 14 (Q51–Q100 Arithmetic & Reasoning, 50 MCQs) and Batch 128 (Q1–Q50 General Knowledge & Science, 50 MCQs). Batch 128 covers: 9 Mizoram GK, 6 Indian History, 6 Indian Polity, 6 Geography, 5 Indian Economy, 5 Environment, 7 General Science [Biology, Physics, Chemistry], 4 Current Affairs, 1 Sports.",
    "actions": {
        "retag": action_counts["retag"],
        "keep": action_counts["keep"],
        "hold": 0
    },
    "unextracted_items_preserved": 0,
    "conventional_marks_preserved": 0,
    "breakdown": dict(sorted(tax_counts.items(), key=lambda x: -x[1])),
    "source_defects": [
        "Reclassified unrefined top-level labels (general-studies, law, mizo, economics, science) into precise granular subject, topic, and subtopic taxonomy nodes.",
        "Complements Batch 14 (which reviewed Q51–Q100 Arithmetic & Reasoning) to achieve 100% full-paper coverage of all 100 questions in JAO Paper-II with zero duplicate reviews."
    ],
    "all_pending": True,
    "live_changes": 0
}

(out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
print(f"Batch 128 built: {len(pending_candidates)} candidates ({action_counts['retag']} retags, {action_counts['keep']} keeps)")
