"""Build review candidates and findings for Batch 91: AE/SDO 2012 General Aptitude Test (50 MCQs)."""
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
    if qnum in (1, 3, 4, 43, 49):
        return 'reasoning-and-aptitude/series', 'Reasoning: numerical, progression, and pattern series'
    elif qnum in (2, 5, 8, 9, 10, 11, 13, 15, 16):
        return 'mathematics/arithmetic', 'Arithmetic: squares, primes, probability, tournament combinations, speed/distance, handshakes, simple interest'
    elif qnum == 6:
        return 'mathematics/arithmetic/averages', 'Arithmetic: averages and mean sum'
    elif qnum == 12:
        return 'mathematics/arithmetic/percentages', 'Arithmetic: percentages and relative comparisons'
    elif qnum in (14, 21, 28, 31, 37, 38):
        return 'reasoning-and-aptitude/numerical-ability', 'Reasoning: numerical ability, operator substitution, leap year day counting, number sets'
    elif qnum in (7, 20, 22, 23, 24, 25, 26, 27, 29, 30, 32, 33, 34, 35, 36, 39, 40, 41, 42, 44):
        return 'reasoning-and-aptitude/verbal-reasoning', 'Reasoning: verbal reasoning, analogies, odd one out, coding-decoding, blood relations, direction sense, ranking, calendar logic'
    elif qnum in (45, 46, 47, 48, 50):
        return 'reasoning-and-aptitude', 'Reasoning: non-verbal reasoning (figure counting, dice positions, visual analogies/patterns)'
    elif qnum in (17, 18):
        return 'science/biology/human-physiology', 'Science: infectious disease pathology, epidemiology, and immunology (Hepatitis B, Swine Flu)'
    elif qnum == 19:
        return 'science/biology/ecology', 'Science: global warming mitigation limitations and ecological policy'
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
        "paper_id": "Old_Questions/Direct_2014-2018/3. General Aptitude Test.pdf",
        "source_fingerprint": fingerprint,
        "review_status": "pending",
        "action": action,
        "current_primary": cur_cls,
        "proposed_primary": parsed,
        "confidence": 1.0,
        "rationale": rationale,
        "batch_id": 91,
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
    "batch": 91,
    "papers": [
        {
            "paper_id": "Old_Questions/Direct_2014-2018/3. General Aptitude Test.pdf",
            "paper_title": "General Aptitude Test for Grade-V of Mizoram Engineering Service (AE/SDO)",
            "document_id": "doc_dd04f5d21970135ddf530d12",
            "sha256": "8acc79a97e3bcdbb7012096dfc16686eaa97dda1ef05eac7cb93a976a8ba5976",
            "targets": 50
        }
    ],
    "targets": 50,
    "completion": "100% paper completion achieved for MES Grade-V (AE/SDO) 2012 General Aptitude Test (50/50 MCQs reviewed: 20 Verbal Reasoning, 11 Arithmetic, 6 Numerical Ability, 5 Series, 5 Non-Verbal, 3 Science/Biology)",
    "actions": {
        "retag": action_counts["retag"],
        "keep": action_counts["keep"],
        "hold": 0
    },
    "unextracted_items_preserved": 0,
    "conventional_marks_preserved": 0,
    "breakdown": dict(sorted(tax_counts.items(), key=lambda x: -x[1])),
    "source_defects": [
        "Realigned legacy blanket gk classifications into precise reasoning, arithmetic, and science taxonomy.",
        "Verified all 50 MCQs against 8 rendered page images from source PDF."
    ],
    "all_pending": True,
    "live_changes": 0
}

(out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
print(f"Batch 91 built: {len(pending_candidates)} candidates ({action_counts['retag']} retags, {action_counts['keep']} keeps)")
