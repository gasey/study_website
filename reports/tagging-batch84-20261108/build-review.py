"""Build review candidates and findings for Batch 84: Stenographer Grade-II (Contract) 2015 General English (50 MCQs)."""
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
    if 1 <= qnum <= 8:
        path = "english/vocabulary/idioms-and-phrases"
        rat = f"Meaning of idiom / phrase: {question[:50]}..."
    elif 9 <= qnum <= 14:
        path = "english/comprehension"
        rat = f"Reading comprehension passage question: {question[:50]}..."
    elif qnum in (15, 20, 22, 23, 24):
        path = "english/grammar/prepositions"
        rat = f"Preposition selection: {question[:50]}..."
    elif qnum in (16, 17, 18, 19, 21):
        path = "english/grammar/parts-of-speech"
        rat = f"Parts of Speech identification (adjectives, adverbs, degrees of comparison): {question[:50]}..."
    elif 25 <= qnum <= 30:
        path = "english/grammar"
        rat = f"Sentence notion / concept expressed: {question[:50]}..."
    elif 31 <= qnum <= 36:
        path = "english/grammar"
        rat = f"Sentence structure classification (Simple, Compound, Complex): {question[:50]}..."
    elif 37 <= qnum <= 42:
        path = "english/grammar"
        rat = f"Clause identification (Noun, Adverb, Adjective clause): {question[:50]}..."
    elif qnum in (46, 48):
        path = "english/vocabulary/idioms-and-phrases"
        rat = f"Idiom / phrase in context (took to their heels, smells a rat): {question[:50]}..."
    elif qnum == 47:
        path = "english/vocabulary/one-word-substitution"
        rat = f"One word substitution / definition (pompous words): {question[:50]}..."
    elif qnum in (43, 44, 45, 49, 50):
        path = "english/vocabulary"
        rat = f"Vocabulary / word usage / word choice in context: {question[:50]}..."
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
        "paper_id": "Old_Questions/Direct_2014-2018/1.STENOGRAPHER GRADE-II (CONTRACT) UNDER DP&AR (SSW),2015General English.pdf",
        "source_fingerprint": fingerprint,
        "review_status": "pending",
        "action": action,
        "current_primary": cur_cls,
        "proposed_primary": parsed,
        "confidence": 1.0,
        "rationale": rationale,
        "batch_id": 84,
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
        "paper_id": "Old_Questions/Direct_2014-2018/1.STENOGRAPHER GRADE-II (CONTRACT) UNDER DP&AR (SSW),2015General English.pdf",
        "qnum": "Section A Q1",
        "reason": "Conventional written essay: 'Write an essay on any one of the following topics in not more than 300 words (20 Marks): (a) Social media and its impact on society (b) Role and significance of NGO’s in Mizoram (c) Crime against women in India'. Conventional section omitted from MCQ database ingestion.",
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
    "batch": 84,
    "papers": [
        {
            "paper_id": "Old_Questions/Direct_2014-2018/1.STENOGRAPHER GRADE-II (CONTRACT) UNDER DP&AR (SSW),2015General English.pdf",
            "paper_title": "Written Examinations for Recruitment to Stenographer Grade-II (Contract) under DP&AR (May 2015) — General English",
            "document_id": "doc_e4ea50d99042b325203308ec",
            "sha256": "0916398a402f44709d22cbe2857ce79f83ea032488a0862590740a6b7e09ea9d",
            "targets": 50
        }
    ],
    "targets": 50,
    "completion": "100% paper completion achieved for Stenographer Grade-II (Contract) 2015 General English (50/50 MCQs reviewed; 20-mark conventional Section A essay preserved in pending-written-intake.json)",
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
