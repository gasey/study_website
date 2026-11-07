"""Build review candidates and findings for Batch 61: MCS Combined 2021 Preliminary Exam Paper II (100 MCQs)."""
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
    if qnum in (1, 2, 8, 9, 11, 12, 13, 14, 16, 17):
        path = "english/comprehension"
        rat = f"Reading comprehension passage question: {question[:50]}..."
    elif qnum in (3, 5, 7):
        path = "english/vocabulary/synonyms"
        rat = f"Passage vocabulary synonym: {question[:50]}..."
    elif qnum in (4, 6):
        path = "english/vocabulary"
        rat = f"Passage vocabulary context: {question[:50]}..."
    elif qnum == 10:
        path = "english/vocabulary/antonyms"
        rat = "Passage vocabulary antonym: opposite meaning to 'rampant'."
    elif qnum == 15:
        path = "english/vocabulary/idioms-and-phrases"
        rat = "Idiom from passage: meaning of 'deliver the goods'."
    elif 18 <= qnum <= 33:
        path = "reasoning-and-aptitude/verbal-reasoning"
        rat = f"Interpersonal skills, communication, and decision making: {question[:50]}..."
    elif qnum in (34, 35, 36, 37):
        path = "reasoning-and-aptitude/verbal-reasoning"
        rat = f"Logical deduction and grouping puzzle: {question[:50]}..."
    elif qnum in (38, 72):
        path = "reasoning-and-aptitude/verbal-reasoning"
        rat = f"Blood relations reasoning: {question[:50]}..."
    elif qnum in (39, 40):
        path = "reasoning-and-aptitude/verbal-reasoning"
        rat = f"Verbal analogy: {question[:50]}..."
    elif qnum in (41, 45, 73):
        path = "reasoning-and-aptitude/verbal-reasoning"
        rat = f"Coding-decoding pattern: {question[:50]}..."
    elif qnum in (42, 46, 68, 69):
        path = "reasoning-and-aptitude/series"
        rat = f"Number or letter series pattern: {question[:50]}..."
    elif qnum in (43, 44):
        path = "reasoning-and-aptitude/verbal-reasoning"
        rat = f"Non-verbal figure classification: {question[:50]}..."
    elif qnum in (47, 77, 93):
        path = "mathematics/algebra/linear-equations"
        rat = f"Linear equation and age algebra problem: {question[:50]}..."
    elif qnum in (48, 85, 94):
        path = "mathematics/arithmetic/percentages"
        rat = f"Percentage calculation and variation: {question[:50]}..."
    elif qnum in (49, 88):
        path = "mathematics/arithmetic/averages"
        rat = f"Average and arithmetic mean computation: {question[:50]}..."
    elif qnum in (50, 51, 52, 53, 54):
        path = "reasoning-and-aptitude/verbal-reasoning"
        rat = f"Logical reasoning, inequalities, syllogisms, or cause-and-effect: {question[:50]}..."
    elif 55 <= qnum <= 67:
        path = "reasoning-and-aptitude/verbal-reasoning"
        rat = f"Administrative decision making, situational judgment, and problem solving: {question[:50]}..."
    elif qnum in (70, 75, 76, 79, 80, 83, 84, 90):
        path = "reasoning-and-aptitude/numerical-ability"
        rat = f"Numerical ability, word problems, clock/dice or Venn sets: {question[:50]}..."
    elif qnum == 71:
        path = "reasoning-and-aptitude/verbal-reasoning"
        rat = "Assertion and Reason logical analysis."
    elif qnum in (74, 78):
        path = "reasoning-and-aptitude/verbal-reasoning"
        rat = f"Direction and distance spatial reasoning: {question[:50]}..."
    elif qnum in (81, 82):
        path = "reasoning-and-aptitude/verbal-reasoning"
        rat = f"Analytical arrangement puzzle: {question[:50]}..."
    elif qnum in (86, 87):
        path = "mathematics/arithmetic"
        rat = f"Basic arithmetic simplification: {question[:50]}..."
    elif qnum == 89:
        path = "mathematics/arithmetic"
        rat = "Time and work / pipes and cisterns arithmetic."
    elif qnum in (91, 99, 100):
        path = "reasoning-and-aptitude/data-interpretation"
        rat = f"Data interpretation from charts/tables: {question[:50]}..."
    elif qnum == 92:
        path = "mathematics/algebra"
        rat = "Arithmetic progression (AP) sequences."
    elif qnum in (95, 98):
        path = "mathematics/arithmetic/ratio-and-proportion"
        rat = f"Ratio and proportion problem: {question[:50]}..."
    elif qnum == 96:
        path = "mathematics/arithmetic"
        rat = "Speed, distance, and time arithmetic."
    elif qnum == 97:
        path = "mathematics/mensuration"
        rat = "Mensuration: distance covered by wheel revolutions."
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
        "paper_id": "Old_Questions/Direct_2021-2022/MCS Combined 2021 Preliminary Exam Paper II.pdf",
        "source_fingerprint": fingerprint,
        "review_status": "pending",
        "action": action,
        "current_primary": cur_cls,
        "proposed_primary": parsed,
        "confidence": 1.0,
        "rationale": rationale,
        "batch_id": 61,
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
    "batch": 61,
    "papers": [
        {
            "paper_id": "Old_Questions/Direct_2021-2022/MCS Combined 2021 Preliminary Exam Paper II.pdf",
            "paper_title": "Mizoram Civil Service Combined Preliminary Examination 2021 — Paper II (Aptitude, Arithmetic & Comprehension)",
            "document_id": "doc_82ea93920297fe3dba5ea823",
            "sha256": "9df024ceae83bb6183df0bf513aeb6354d8fa0cf1871ce9fd22455094c91784d",
            "targets": 100
        }
    ],
    "targets": 100,
    "completion": "100% paper completion achieved for MCS Combined 2021 Preliminary Paper II (100/100 MCQs)",
    "actions": {
        "retag": retags,
        "keep": keeps,
        "hold": holds
    },
    "unextracted_items_preserved": 0,
    "conventional_marks_preserved": 0,
    "breakdown": dict(breakdown),
    "source_defects": [
        "Q71 Misclassified to Physics: An assertion-reason logic question was misclassified into science/physics in legacy baseline; retagged to reasoning-and-aptitude/verbal-reasoning.",
        "Q49, Q88 Misclassified to Statistics: Standard arithmetic mean/average problems were tagged to statistics in legacy baseline; retagged to mathematics/arithmetic/averages."
    ],
    "all_pending": True,
    "live_changes": 0
}

(out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
print(f"Generated {len(pending_candidates)} pending review candidates.")
print(f"Saved {len(findings)} detailed findings.")
print(f"Actions: {retags} retag, {keeps} keep, {holds} hold.")
print(f"Breakdown: {dict(breakdown)}")
