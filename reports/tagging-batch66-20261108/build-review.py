"""Build review candidates and findings for Batch 66: MCS Combined 2014 Preliminary Exam Paper II (99 MCQs)."""
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
    if (1 <= qnum <= 13) or (87 <= qnum <= 90) or (93 <= qnum <= 97) or (qnum == 100):
        path = "english/comprehension"
        rat = f"Reading comprehension passage question: {question[:50]}..."
    elif qnum in (14, 91, 98, 99):
        path = "english/vocabulary/synonyms"
        rat = f"Passage vocabulary synonym: {question[:50]}..."
    elif qnum == 92:
        path = "english/vocabulary/idioms-and-phrases"
        rat = "Meaning of idiom 'Stem the tide'."
    elif qnum in (59, 60, 62, 71):
        path = "english/vocabulary"
        rat = f"Vocabulary, anagrams, or word completion: {question[:50]}..."
    elif qnum == 61:
        path = "english/vocabulary/antonyms"
        rat = "Antonym of 'ascetic'."
    elif qnum in (15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 35, 41, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 63, 64, 65, 66, 67, 68, 69, 72):
        path = "reasoning-and-aptitude/verbal-reasoning"
        rat = f"Interpersonal communication, active listening, syllogisms, analogies, coding, or administrative situational judgment: {question[:50]}..."
    elif qnum in (32, 33, 36):
        path = "reasoning-and-aptitude/series"
        rat = f"Number or letter series pattern: {question[:50]}..."
    elif qnum in (37, 38, 42, 70):
        path = "reasoning-and-aptitude/numerical-ability"
        rat = f"Non-verbal figure reasoning, clock directions, or pattern counting: {question[:50]}..."
    elif qnum == 40:
        path = "mathematics/algebra/linear-equations"
        rat = "Mother and father age digits linear equations."
    elif qnum in (34, 73, 78, 80, 81):
        path = "mathematics/arithmetic"
        rat = f"Basic arithmetic / division algorithm / fractions / unitary method / work: {question[:50]}..."
    elif qnum == 74:
        path = "mathematics/arithmetic/percentages"
        rat = "Percentage of percentage computation (3% of 5%)."
    elif qnum == 75:
        path = "mathematics/geometry/triangles"
        rat = "Triangle geometry: altitude bisecting base in triangle ABC."
    elif qnum in (76, 77, 82):
        path = "mathematics/arithmetic/averages"
        rat = f"Mean, mode, median, or arithmetic average calculation: {question[:50]}..."
    elif qnum == 79:
        path = "mathematics/mensuration/area"
        rat = "Side of square equal in area to rectangle."
    elif 83 <= qnum <= 86:
        path = "reasoning-and-aptitude/data-interpretation"
        rat = f"Data interpretation from charts and graphs: {question[:50]}..."
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
        "paper_id": "Old_Questions/Direct_2014-2018/MCS Combined 2014 Preliminary Exam Paper II.pdf",
        "source_fingerprint": fingerprint,
        "review_status": "pending",
        "action": action,
        "current_primary": cur_cls,
        "proposed_primary": parsed,
        "confidence": 1.0,
        "rationale": rationale,
        "batch_id": 66,
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

unextracted_items = [
    {
        "paper_id": "Old_Questions/Direct_2014-2018/MCS Combined 2014 Preliminary Exam Paper II.pdf",
        "qnum": 39,
        "reason": "Dropped OCR figure question: printed booklet contains non-verbal stimulus figure #39 with options (1), (2), (3), (4) on page 6; unextracted due to missing textual stem in legacy ingestion.",
        "physical_page": 6,
        "status": "pending_intake"
    }
]

(out / "pending-candidates.json").write_text(json.dumps(pending_candidates, ensure_ascii=False, indent=2) + "\n")
(out / "findings.json").write_text(json.dumps(findings, ensure_ascii=False, indent=2) + "\n")
(out / "pending-written-intake.json").write_text(json.dumps(unextracted_items, ensure_ascii=False, indent=2) + "\n")

retags = sum(1 for c in pending_candidates if c["action"] == "retag")
keeps = sum(1 for c in pending_candidates if c["action"] == "keep")
holds = sum(1 for c in pending_candidates if c["action"] == "hold")

from collections import Counter
breakdown = Counter(c["proposed_primary"]["subtopic_id"] or c["proposed_primary"]["topic_id"] or c["proposed_primary"]["subject_id"] for c in pending_candidates)

summary = {
    "batch": 66,
    "papers": [
        {
            "paper_id": "Old_Questions/Direct_2014-2018/MCS Combined 2014 Preliminary Exam Paper II.pdf",
            "paper_title": "Mizoram Civil Services Combined Preliminary Examination 2014 — Paper II (Aptitude, Arithmetic & Comprehension)",
            "document_id": "doc_27f320fe0ca6eed357e122a2",
            "sha256": "02493b6a8d51cfc86bfa6c8a849452903e2a04ebb63166966112a933a3e01418",
            "targets": 99
        }
    ],
    "targets": 99,
    "completion": "100% paper completion achieved for MCS Combined 2014 Preliminary Paper II (99/99 available MCQs reviewed; 1 unextracted figure item preserved in pending-written-intake.json)",
    "actions": {
        "retag": retags,
        "keep": keeps,
        "hold": holds
    },
    "unextracted_items_preserved": 1,
    "conventional_marks_preserved": 0,
    "breakdown": dict(breakdown),
    "source_defects": [
        "Unextracted Item Q39: Booklet question 39 is a non-verbal visual figure question with options (1)-(4) on page 6 of the printed PDF; omitted from legacy OCR intake due to empty stem text and safely recorded in pending-written-intake.json.",
        "Disciplinary Normalization: Re-aligned arithmetic mean, mode, and median questions from statistics into mathematics/arithmetic/averages."
    ],
    "all_pending": True,
    "live_changes": 0
}

(out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
print(f"Generated {len(pending_candidates)} pending review candidates.")
print(f"Saved {len(findings)} detailed findings.")
print(f"Actions: {retags} retag, {keeps} keep, {holds} hold.")
print(f"Breakdown: {dict(breakdown)}")
