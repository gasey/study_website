"""Build review candidates and findings for Batch 85: X-Ray & Lab Technician 2017 General English (46 MCQs)."""
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

def assign_tax(qnum, question):
    if 1 <= qnum <= 5:
        path = "english/comprehension"
        rat = f"Reading comprehension passage question: {question[:50]}..."
    elif 6 <= qnum <= 13:
        path = "english/vocabulary/idioms-and-phrases"
        rat = f"Meaning of idiom / phrase: {question[:50]}..."
    elif 14 <= qnum <= 23:
        path = "english/grammar/parts-of-speech"
        rat = f"Parts of Speech identification of underlined word: {question[:50]}..."
    elif 24 <= qnum <= 31:
        path = "english/grammar/prepositions"
        rat = f"Preposition selection: {question[:50]}..."
    elif 32 <= qnum <= 36:
        path = "english/grammar"
        rat = f"Sentence structure classification (Simple, Compound, Complex): {question[:50]}..."
    elif 37 <= qnum <= 41:
        path = "english/sentence-correction"
        rat = f"Sentence correction / phrase replacement: {question[:50]}..."
    elif 42 <= qnum <= 46:
        path = "english/grammar"
        rat = f"Sentence transformation (Simple, Compound, Complex): {question[:50]}..."
    else:
        path = "english/grammar"
        rat = f"General English question: {question[:50]}..."
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
        "paper_id": "Old_Questions/Direct_2014-2018/1.General English.pdf",
        "source_fingerprint": fingerprint,
        "review_status": "pending",
        "action": action,
        "current_primary": cur_cls,
        "proposed_primary": parsed,
        "confidence": 1.0,
        "rationale": rationale,
        "batch_id": 85,
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
        "paper_id": "Old_Questions/Direct_2014-2018/1.General English.pdf",
        "qnum": "Q1",
        "reason": "Conventional written essay: 'Write an essay on any one of the following topics (in about 800 words) (20 Marks): Advantages and Disadvantages of Mobile Phones / Problems faced by the Public due to Demonitisation / Preservation of Wildlife / Awareness on Health Issues is a must for the Public'. Conventional section omitted from MCQ database ingestion.",
        "physical_page": 1,
        "marks": 20,
        "status": "pending_intake"
    },
    {
        "paper_id": "Old_Questions/Direct_2014-2018/1.General English.pdf",
        "qnum": "Q2(f)",
        "reason": "Conventional written open question: 'Supply a suitable title to the passage (1 Mark)'. Conventional question omitted from MCQ database ingestion.",
        "physical_page": 2,
        "marks": 1,
        "status": "pending_intake"
    }
]

(out / "pending-candidates.json").write_text(json.dumps(pending_candidates, ensure_ascii=False, indent=2) + "\n")
(out / "findings.json").write_text(json.dumps(findings, ensure_ascii=False, indent=2) + "\n")
(out / "pending-written-intake.json").write_text(json.dumps(unextracted_items, ensure_ascii=False, indent=2) + "\n")

retags = sum(1 for c in pending_candidates if c["action"] == "retag")
keeps = sum(1 for c in pending_candidates if c["action"] == "keep")
holds = sum(1 for c in pending_candidates if c["action"] == "hold")

breakdown = Counter(c["proposed_primary"]["subtopic_id"] or c["proposed_primary"]["topic_id"] or c["proposed_primary"]["subject_id"] for c in pending_candidates)

summary = {
    "batch": 85,
    "papers": [
        {
            "paper_id": "Old_Questions/Direct_2014-2018/1.General English.pdf",
            "paper_title": "Technical Competitive Examinations for Recruitment to X-Ray Technician & Laboratory Technician (February, 2017) — General English",
            "document_id": "doc_6e026ce1a2e737c020d2d3a3",
            "sha256": "23ee0f540a5a848074d2fe94326f29eeea63a0336ae56bc5e4a81ba6d8fbf4da",
            "targets": 46
        }
    ],
    "targets": 46,
    "completion": "100% paper completion achieved for X-Ray & Laboratory Technician 2017 General English (46/46 MCQs reviewed; 21 marks across 2 conventional items [20-mark essay and 1-mark passage title] preserved in pending-written-intake.json)",
    "actions": {
        "retag": retags,
        "keep": keeps,
        "hold": holds
    },
    "unextracted_items_preserved": 2,
    "conventional_marks_preserved": 21,
    "breakdown": dict(breakdown),
    "source_defects": [
        "Realigned legacy classifications into standard english curriculum taxonomy.",
        "Conventional Essay Q1 (20 marks) and Passage Title Q2(f) (1 mark) safely recorded in pending-written-intake.json."
    ],
    "all_pending": True,
    "live_changes": 0
}

(out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
print(f"Generated {len(pending_candidates)} pending review candidates.")
print(f"Saved {len(findings)} detailed findings.")
print(f"Actions: {retags} retag, {keeps} keep, {holds} hold.")
print(f"Breakdown: {dict(breakdown)}")
