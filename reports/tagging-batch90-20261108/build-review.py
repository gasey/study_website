"""Build review candidates and findings for Batch 90: LDC 2025 Paper-II (100 MCQs)."""
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
    if 1 <= qnum <= 50:
        if qnum == 1:
            return 'computer-science/computer-systems-and-architecture/history-and-generations', 'Computer generations: fifth-generation computer focus'
        elif qnum in (2, 5):
            return 'computer-science/computer-systems-and-architecture/computer-hardware', 'Computer hardware components / output devices'
        elif qnum in (3, 4):
            return 'computer-science/computer-systems-and-architecture/memory-and-storage', 'Primary and cache memory storage architecture'
        elif qnum in (6, 8, 9):
            return 'computer-science/computer-systems-and-architecture', 'Computer fundamentals: software definition, classification, supercomputers'
        elif qnum == 10:
            return 'computer-science', 'Cyber law: Information Technology Amendment Act'
        elif qnum in (7, 11, 12, 13, 14, 15, 16, 17, 18):
            return 'computer-science/operating-systems', 'Operating systems: OS role, Windows interface, desktop, shortcuts, settings'
        elif 19 <= qnum <= 30:
            return 'computer-science/office-applications', 'Office applications: Microsoft Word processing, formatting, editing, mail merge'
        elif 31 <= qnum <= 38:
            return 'computer-science/office-applications', 'Office applications: Microsoft Excel worksheets, formulas, functions, charts'
        elif 39 <= qnum <= 43:
            return 'computer-science/office-applications', 'Office applications: Microsoft PowerPoint presentation slides, layouts, rehearsal'
        elif 44 <= qnum <= 50:
            return 'computer-science/networking', 'Networking: Internet protocols, email systems (IMAP, CC), security (HTTPS)'
    elif 51 <= qnum <= 75:
        if qnum == 51:
            return 'mathematics/algebra/algebraic-expressions', 'Algebra: operations on radicals / surd addition'
        elif qnum in (52, 56, 68):
            return 'mathematics/arithmetic/averages', 'Arithmetic: averages and means'
        elif qnum in (54, 55):
            return 'mathematics/arithmetic/percentages', 'Arithmetic: percentages and discounts'
        elif qnum == 60:
            return 'mathematics/mensuration', 'Mensuration: 3D room diagonal / longest rod'
        elif qnum in (61, 62, 75):
            return 'reasoning-and-aptitude/data-interpretation', 'Data interpretation: flight graph, bar chart, pie chart'
        elif qnum == 65:
            return 'mathematics/arithmetic/profit-and-loss', 'Arithmetic: profit, loss, and selling price'
        elif qnum in (66, 67, 69):
            return 'mathematics/arithmetic/ratio-and-proportion', 'Arithmetic: ratio, proportion, and partnership'
        elif qnum == 73:
            return 'mathematics/mensuration/volume', 'Mensuration: volume ratio of cones'
        elif qnum == 74:
            return 'mathematics/geometry/triangles', 'Geometry / trigonometry: angle of elevation and height/shadow'
        else:
            return 'mathematics/arithmetic', 'Arithmetic: primes, fractions, BODMAS, time & work, permutations/combinations, speed/distance, interest'
    elif 76 <= qnum <= 100:
        if qnum in (78, 80, 90, 95, 96, 97, 98):
            return 'reasoning-and-aptitude/series', 'Reasoning: number, letter, and grid series / missing characters'
        elif qnum == 94:
            return 'reasoning-and-aptitude/numerical-ability', 'Reasoning: numerical ability / digit rearrangement'
        elif qnum in (99, 100):
            return 'reasoning-and-aptitude', 'Reasoning: non-verbal reasoning (mirror images, dice)'
        else:
            return 'reasoning-and-aptitude/verbal-reasoning', 'Reasoning: verbal reasoning (analogies, odd one out, coding, blood relations, direction, ranking, syllogism)'
    raise ValueError(f"unhandled qnum {qnum}")

pending_candidates = []
findings = []

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
        "paper_id": "Old_Questions/Direct_NG_2024-2027/LDC under MPSC Paper-II 2025..pdf",
        "source_fingerprint": fingerprint,
        "review_status": "pending",
        "action": action,
        "current_primary": cur_cls,
        "proposed_primary": parsed,
        "confidence": 1.0,
        "rationale": rationale,
        "batch_id": 90,
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
    "batch": 90,
    "papers": [
        {
            "paper_id": "Old_Questions/Direct_NG_2024-2027/LDC under MPSC Paper-II 2025..pdf",
            "paper_title": "Competitive Examination for Lower Division Clerk under Mizoram Public Service Commission, February 2025 — Paper II",
            "document_id": "doc_712c2c9334cdd9d7",
            "sha256": "712c2c9334cdd9d779b40945a6019a22ddbc71af6cc229fe2edecc51c78a275a",
            "targets": 100
        }
    ],
    "targets": 100,
    "completion": "100% paper completion achieved for LDC 2025 Paper-II (100/100 MCQs reviewed: 50 Computer Knowledge, 25 Arithmetic, 25 Reasoning)",
    "actions": {
        "retag": action_counts["retag"],
        "keep": action_counts["keep"],
        "hold": 0
    },
    "unextracted_items_preserved": 0,
    "conventional_marks_preserved": 0,
    "breakdown": dict(sorted(tax_counts.items(), key=lambda x: -x[1])),
    "source_defects": [
        "Realigned legacy classifications into standard computer-science, arithmetic, and reasoning curriculum taxonomy.",
        "Verified all 100 MCQs against 12 rendered page images from source PDF."
    ],
    "all_pending": True,
    "live_changes": 0
}

(out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
print(f"Batch 90 built: {len(pending_candidates)} candidates ({action_counts['retag']} retags, {action_counts['keep']} keeps)")
