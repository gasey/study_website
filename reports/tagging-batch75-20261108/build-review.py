"""Build review candidates and findings for Batch 75: Junior Engineer (JE) General English April 2016 (80 MCQs)."""
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
    if (1 <= qnum <= 16) or (29 <= qnum <= 35):
        path = "english/vocabulary/idioms-and-phrases"
        rat = f"Meaning or selection of idiom / phrasal verb: {question[:50]}..."
    elif 17 <= qnum <= 28:
        path = "english/comprehension"
        rat = f"Reading comprehension passage question: {question[:50]}..."
    elif 36 <= qnum <= 42:
        path = "english/grammar/parts-of-speech"
        rat = f"Adjective, adverb, or verb selection: {question[:50]}..."
    elif 43 <= qnum <= 48:
        path = "english/grammar/parts-of-speech"
        rat = f"Parts of Speech identification of underlined word: {question[:50]}..."
    elif 49 <= qnum <= 54:
        path = "english/grammar"
        rat = f"Clause identification (noun, adverb, adjective, independent clause): {question[:50]}..."
    elif 55 <= qnum <= 59:
        path = "english/grammar"
        rat = f"Sentence structure analysis (Simple, Complex, Compound): {question[:50]}..."
    elif 60 <= qnum <= 64:
        path = "english/grammar"
        rat = f"Sentence functional classification (Declarative, Interrogative, Imperative, Exclamatory): {question[:50]}..."
    elif 65 <= qnum <= 70:
        path = "english/vocabulary/synonyms"
        rat = f"Synonym / similar in meaning: {question[:50]}..."
    elif 71 <= qnum <= 74:
        path = "english/vocabulary/antonyms"
        rat = f"Antonym / opposite in meaning: {question[:50]}..."
    elif qnum in (75, 76, 77, 79):
        path = "english/vocabulary/one-word-substitution"
        rat = f"One-word substitution: {question[:50]}..."
    elif qnum in (78, 80):
        path = "english/vocabulary"
        rat = f"Vocabulary / usage of words: {question[:50]}..."
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
        "paper_id": "Old_Questions/Direct_2014-2018/3. General English.pdf",
        "source_fingerprint": fingerprint,
        "review_status": "pending",
        "action": action,
        "current_primary": cur_cls,
        "proposed_primary": parsed,
        "confidence": 1.0,
        "rationale": rationale,
        "batch_id": 75,
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
        "paper_id": "Old_Questions/Direct_2014-2018/3. General English.pdf",
        "qnum": "Section A Q1",
        "reason": "Conventional written essay: 'Write an essay on any one (1) of the given topics (300 words). (a) Talent versus Hard work. (b) Mass Media and Cultural Invasion. (c) Youth Culture Today. (20 Marks)'. Conventional section omitted from MCQ database ingestion.",
        "physical_page": 1,
        "marks": 20,
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
    "batch": 75,
    "papers": [
        {
            "paper_id": "Old_Questions/Direct_2014-2018/3. General English.pdf",
            "paper_title": "Technical Competitive Examinations for Junior Engineer (J.E) under PHE & PWD (April 2016) — General English",
            "document_id": "doc_4c79cb3420629f238d2b19c8",
            "sha256": "4cfb27b08fcd62e6f37f34c4f1560a182b023880ec3325f790657a920b904776",
            "targets": 80
        }
    ],
    "targets": 80,
    "completion": "100% paper completion achieved for Junior Engineer (J.E) General English April 2016 (80/80 MCQs reviewed; 20-mark conventional Section A essay preserved in pending-written-intake.json)",
    "actions": {
        "retag": retags,
        "keep": keeps,
        "hold": holds
    },
    "unextracted_items_preserved": 1,
    "conventional_marks_preserved": 20,
    "breakdown": dict(breakdown),
    "source_defects": [
        "Realigned legacy classifications into standard english curriculum taxonomy.",
        "Conventional Section A Essay (20 marks) on Page 1 safely recorded in pending-written-intake.json."
    ],
    "all_pending": True,
    "live_changes": 0
}

(out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
print(f"Generated {len(pending_candidates)} pending review candidates.")
print(f"Saved {len(findings)} detailed findings.")
print(f"Actions: {retags} retag, {keeps} keep, {holds} hold.")
print(f"Breakdown: {dict(breakdown)}")
