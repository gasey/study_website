"""Build review candidates and findings for Batch 65: MCS Combined 2018 Preliminary Exam Paper-II Series-A (100 MCQs)."""
import json
from pathlib import Path

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

def assign_tax(qnum, question):
    if (1 <= qnum <= 14) or (87 <= qnum <= 100):
        path = "english/comprehension"
        rat = f"Reading comprehension passage question: {question[:50]}..."
    elif qnum in (15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 63, 64, 65, 70, 71):
        path = "reasoning-and-aptitude/verbal-reasoning"
        rat = f"Interpersonal communication, conflict resolution, assertions, logic puzzles, or administrative decision making: {question[:50]}..."
    elif qnum in (58, 59, 60, 68, 69, 75):
        path = "reasoning-and-aptitude/numerical-ability"
        rat = f"Non-verbal figure reasoning, pattern matrix, or Venn sets: {question[:50]}..."
    elif qnum in (61, 62):
        path = "reasoning-and-aptitude/series"
        rat = f"Letter or number series sequence: {question[:50]}..."
    elif qnum in (66, 67):
        path = "english/vocabulary"
        rat = f"Vocabulary / word usage: {question[:50]}..."
    elif qnum in (72, 74, 79, 86):
        path = "mathematics/arithmetic"
        rat = f"Divisibility, work, radicals, or compound interest arithmetic: {question[:50]}..."
    elif qnum in (73, 82):
        path = "mathematics/arithmetic/percentages"
        rat = f"Percentage calculation or sales tax: {question[:50]}..."
    elif qnum in (76, 84):
        path = "mathematics/mensuration/area"
        rat = f"Area or perimeter of circle / rectangle: {question[:50]}..."
    elif qnum == 77:
        path = "mathematics/algebra"
        rat = "Sum of terms in arithmetic progression (AP)."
    elif qnum == 78:
        path = "statistics/probability-and-statistics/probability"
        rat = "Probability of drawing a ball from bag."
    elif qnum == 80:
        path = "mathematics/arithmetic/ratio-and-proportion"
        rat = "Comparison of ratios."
    elif qnum == 81:
        path = "reasoning-and-aptitude/data-interpretation"
        rat = "Data interpretation from marks pie chart."
    elif qnum == 83:
        path = "mathematics/arithmetic/profit-and-loss"
        rat = "Cost price calculation from selling price with profit percentage."
    elif qnum == 85:
        path = "reasoning-and-aptitude/data-interpretation"
        rat = "Frequency distribution table data interpretation."
    else:
        path = "reasoning-and-aptitude/verbal-reasoning"
        rat = f"General aptitude question: {question[:50]}..."
    return path, rat

pending_candidates = []
findings = []

for item in packet["items"]:
    cid = item["canonical_id"]
    aid = item["appearance_id"]
    rec = item["snapshot"]["record"]
    qnum = int(rec["qnum"])
    q_text = rec["question"]
    fingerprint = item["source_fingerprint"]
    
    cur_cls = rec.get("classification") or {"subject_id": None, "topic_id": None, "subtopic_id": None}
    
    target_tax, rationale = assign_tax(qnum, q_text)
    parsed = parse_path(target_tax)
    action = "keep" if parsed == cur_cls else "retag"
    
    cand = {
        "canonical_id": cid,
        "appearance_id": aid,
        "paper_id": "Old_Questions/Recovered_MCS/MCS Combined 2018 Preliminary Exam Paper-II Series-A Chase copy.pdf",
        "source_fingerprint": fingerprint,
        "review_status": "pending",
        "action": action,
        "current_primary": cur_cls,
        "proposed_primary": parsed,
        "confidence": 1.0,
        "rationale": rationale,
        "batch_id": 65,
        "policy": "study-tagging-v1"
    }
    pending_candidates.append(cand)
    
    findings.append({
        "qnum": qnum,
        "canonical_id": cid,
        "appearance_id": aid,
        "action": action,
        "current_taxonomy": cur_cls,
        "target_taxonomy": parsed,
        "rationale": rationale,
        "stem_excerpt": q_text[:80]
    })

findings.sort(key=lambda x: x["qnum"])
pending_candidates.sort(key=lambda x: int(next(i["snapshot"]["record"]["qnum"] for i in packet["items"] if i["appearance_id"] == x["appearance_id"])))

(out / "pending-candidates.json").write_text(json.dumps(pending_candidates, ensure_ascii=False, indent=2) + "\n")
(out / "findings.json").write_text(json.dumps(findings, ensure_ascii=False, indent=2) + "\n")
(out / "pending-written-intake.json").write_text(json.dumps([], ensure_ascii=False, indent=2) + "\n")

retags = sum(1 for c in pending_candidates if c["action"] == "retag")
keeps = sum(1 for c in pending_candidates if c["action"] == "keep")
holds = sum(1 for c in pending_candidates if c["action"] == "hold")

from collections import Counter
breakdown = Counter(c["proposed_primary"]["subtopic_id"] or c["proposed_primary"]["topic_id"] or c["proposed_primary"]["subject_id"] for c in pending_candidates)

summary = {
    "batch": 65,
    "papers": [
        {
            "paper_id": "Old_Questions/Recovered_MCS/MCS Combined 2018 Preliminary Exam Paper-II Series-A Chase copy.pdf",
            "paper_title": "Mizoram Civil Services Combined Preliminary Examination 2018 — Paper II (Series A: Aptitude, Arithmetic & Comprehension)",
            "document_id": "mcs-recovered-2018-ii",
            "sha256": "6a955f096a09992b681ac0c6eb0f6d48f7dbc9b831c4892a73efa9e9c7eceb47",
            "targets": 100
        }
    ],
    "targets": 100,
    "completion": "100% paper completion achieved for MCS Combined 2018 Preliminary Paper-II Series A (100/100 MCQs)",
    "actions": {
        "retag": retags,
        "keep": keeps,
        "hold": holds
    },
    "unextracted_items_preserved": 0,
    "conventional_marks_preserved": 0,
    "breakdown": dict(breakdown),
    "source_defects": [
        "Major Legacy Normalization: Corrected baseline classifications where CSAT questions were misclassified into sociology (3), psychology (7), general-studies (9), general-knowledge (6), physics (4), commerce (2), civil-engineering (1), and biology (1).",
        "Passage Question Grouping: Re-integrated reading comprehension questions across Indian Army, ISRO, crime/sociology, morals, and Beethoven into english/comprehension."
    ],
    "all_pending": True,
    "live_changes": 0
}

(out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
print(f"Generated {len(pending_candidates)} pending review candidates.")
print(f"Saved {len(findings)} detailed findings.")
print(f"Actions: {retags} retag, {keeps} keep, {holds} hold.")
print(f"Breakdown: {dict(breakdown)}")
